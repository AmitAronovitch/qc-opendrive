import logging

from abc import abstractmethod

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models
from qc_opendrive.checks.schema.valid_schema import SchemaValidator


from qc_opendrive.checks.basic import (
    valid_xml_document,
    root_tag_is_opendrive,
    fileheader_is_present,
    version_is_defined,
)

CHECKER_ID = "me_check_asam_xodr_xml_valid_schema"
CHECKER_DESCRIPTION = "Input xml file must be valid according to the schema, filtered by ME needs, but some elements will raise only warnings and not errors."
CHECKER_PRECONDITIONS = {
    valid_xml_document.CHECKER_ID,
    root_tag_is_opendrive.CHECKER_ID,
    fileheader_is_present.CHECKER_ID,
    version_is_defined.CHECKER_ID,
}
RULE_UID = "asam.net:xodr:1.0.0:xml.me_valid_schema"


class MESchemaValidator(SchemaValidator):
    EPSILON = 1e-6

    @abstractmethod
    def _get_error_severity(
        self, schema_error: SchemaValidator.SchemaError
    ) -> IssueSeverity:
        """Get the severity of the error based on the error message

        Args:
            schema_error (SchemaError): Error to check

        Returns:
            IssueSeverity: Severity of the error
        """
        # Find the element that raised the error
        elements = self.checker_data.input_file_xml_root.xpath(schema_error.xpath)

        # Iterate over all elements, raise an error at the first one that doesnt match an ignore rule
        for element in elements:

            # Ignore trafficIsland as fillType errors
            if (
                element.get("fillType") == "trafficIsland"
                and "trafficIsland" in schema_error.message
                and "trafficIsland" in schema_error.message
            ):
                continue

            # Ignore object lengths of 0 errors
            if (
                element.tag == "object"
                and schema_error.message.startswith(
                    "Element 'object', attribute 'length': [facet 'minExclusive'] The value "
                )
                and schema_error.message.endswith(" must be greater than '0.0'.")
            ):

                length = element.get("length")
                if length is not None and float(length) == 0:
                    continue

            # Ignore lines with sOffsets that are negative but very close to 0
            if (
                element.tag == "line"
                and schema_error.message.startswith(
                    "Element 'line', attribute 'sOffset': [facet 'minInclusive'] The value "
                )
                and schema_error.message.endswith(
                    " is less than the minimum value allowed ('0.0')."
                )
            ):

                sOffset = element.get("sOffset")
                if sOffset is not None and float(sOffset) > -abs(
                    MESchemaValidator.EPSILON
                ):
                    continue

            # Ignore userData elements (when not in a junction, or when the junction has children of type 'connection')
            if element.tag == "userData":

                # Get the parent element
                parent_element = element.getparent()

                # Ignore all userData elements that are not children of a junction element
                if parent_element.tag != "junction":
                    continue

                # Ignore userData elements that are children of junction elements that have children of type 'connection'
                sibling_elements = [
                    c
                    for c in element.getparent().getchildren()
                    if c.tag == "connection"
                ]
                if sibling_elements:
                    continue

            # If we got this far - this error isnt filtered out
            return IssueSeverity.ERROR

        return None  # Always return None (implement if needed)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if input file is valid according to OpenDRIVE schema, but with
    some issues raised as warnings instead of errors and some other issues filtered-out by ME needs.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/86
    """
    logging.info(f"Executing {CHECKER_ID}")

    # Initialize the validator logic (can be overriden if needed)
    schema_validator = MESchemaValidator(
        checker_data=checker_data,
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        rule_id=RULE_UID,
    )

    # Validate the schema by the defined logic
    schema_validator.raise_issues()
