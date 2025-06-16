# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib.resources
import logging

from abc import abstractmethod
from dataclasses import dataclass

from typing import List

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.schema import schema_files
from qc_opendrive.base import models, utils

import xmlschema
from lxml import etree

from qc_opendrive.checks.basic import (
    valid_xml_document,
    root_tag_is_opendrive,
    fileheader_is_present,
    version_is_defined,
)

CHECKER_ID = "check_asam_xodr_xml_valid_schema"
CHECKER_DESCRIPTION = "Input xml file must be valid according to the schema."
CHECKER_PRECONDITIONS = {
    valid_xml_document.CHECKER_ID,
    root_tag_is_opendrive.CHECKER_ID,
    fileheader_is_present.CHECKER_ID,
    version_is_defined.CHECKER_ID,
}
RULE_UID = "asam.net:xodr:1.0.0:xml.valid_schema"


class SchemaValidator:

    @dataclass
    class SchemaError:
        message: str
        line: int
        column: int
        xpath: str

    def __init__(
        self, checker_data: models.CheckerData, checker_bundle_name, checker_id, rule_id
    ):
        """Initialize the schema validator"""
        self.checker_bundle_name = checker_bundle_name
        self.checker_id = checker_id
        self.rule_id = rule_id
        self.checker_data = checker_data
        self.schema_version = checker_data.schema_version
        self.xml_file = checker_data.config.get_config_param("InputFile")
        self.xsd_file = schema_files.SCHEMA_FILES.get(self.schema_version)
        self.schema_file = (
            str(
                importlib.resources.files("qc_opendrive.schema").joinpath(self.xsd_file)
            )
            if self.xsd_file
            else None
        )

    def raise_issues(self) -> None:
        """Raise issues based on the schema validation results"""
        if self.xsd_file is None:
            self.checker_data.result.set_checker_status(
                checker_bundle_name=self.checker_bundle_name,
                checker_id=self.checker_id,
                status=StatusType.SKIPPED,
            )

            self.checker_data.result.add_checker_summary(
                self.checker_bundle_name,
                self.checker_id,
                f"Cannot find the schema file for ASAM OpenDrive version {self.schema_version}.",
            )
            return

        # Get all errors with their severity
        errors_with_severities = self._get_schema_errors()

        # Iterate over all errors and raise them as issues
        for error, severity in errors_with_severities:

            # Skip errors with no severity
            if not severity:
                continue

            # Create an issue for each error
            issue_id = self.checker_data.result.register_issue(
                checker_bundle_name=self.checker_bundle_name,
                checker_id=self.checker_id,
                description="Issue flagging when input file does not follow its version schema",
                level=severity,
                rule_uid=self.rule_id,
            )

            self.checker_data.result.add_file_location(
                checker_bundle_name=self.checker_bundle_name,
                checker_id=self.checker_id,
                issue_id=issue_id,
                row=error.line,
                column=error.column,
                description=error.message,
            )

    def _get_schema_errors(self) -> List[tuple[SchemaError, IssueSeverity | None]]:
        """Check if input xml tree is valid against the input schema file (.xsd). Expects self.schema_file to be set.

        Returns:
            List[tuple[SchemaError, IssueSeverity]]: List of errors found during the validation, with their severity
        """

        split_result = self.schema_version.split(".")
        major = utils.to_int(split_result[0])
        minor = utils.to_int(split_result[1])
        errors_with_severity = []

        if major is None or minor is None:
            return False, errors_with_severity

        # use LXML for XSD 1.0 with better error level -> OpenDRIVE 1.7 and lower
        if major <= 1 and minor <= 7:
            schema = etree.XMLSchema(etree.parse(self.schema_file))
            xml_tree = etree.parse(self.xml_file)
            schema.validate(xml_tree)
            for error in schema.error_log:
                schema_error = SchemaValidator.SchemaError(
                    message=error.message,
                    line=error.line,
                    column=error.column,
                    xpath=error.path,
                )
                errors_with_severity.append(
                    (schema_error, self._get_error_severity(schema_error))
                )
        else:  # use xmlschema to support XSD schema 1.1 -> OpenDRIVE 1.8 and higher
            schema = xmlschema.XMLSchema11(self.schema_file)
            # Iterate over all validation errors
            xml_doc = etree.parse(self.xml_file)
            for error in schema.iter_errors(xml_doc):
                schema_error = SchemaValidator.SchemaError(
                    message=error.reason,
                    line=error.sourceline,
                    column=0,
                    xpath=error.path,
                )
                errors_with_severity.append(
                    (schema_error, self._get_error_severity(schema_error))
                )

        return errors_with_severity

    @abstractmethod
    def _get_error_severity(self, schema_error: SchemaError) -> IssueSeverity | None:
        """Get the severity of the error based on the schema_error. Severity of None means no issue should be raised.

        Args:
            schema_error (SchemaError): Error to check

        Returns:
            IssueSeverity: Severity of the error
        """
        return IssueSeverity.ERROR  # Always return error, can be overriden if needed


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if input file is valid according to OpenDRIVE schema

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/86
    """
    logging.info("Executing valid_schema check")

    # Initialize the validator logic (can be overriden if needed)
    schema_validator = SchemaValidator(
        checker_data=checker_data,
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        rule_id=RULE_UID,
    )

    # Validate the schema by the defined logic
    schema_validator.raise_issues()
