import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_junction_id_exists"
CHECKER_DESCRIPTION = "Referenced junction id must exist."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "mobileye.com:xodr:1.4.0:junctions.id.exists"


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if all junction ids referenced by roads have a junction
    element with that id.

    Args:
        checker_data: The data needed to perform the check.
    """
    logging.info(f"Executing {RULE_UID}")

    # Collect all declared junctions
    junctions = utils.get_junctions(checker_data.input_file_xml_root)

    # Collect all declared junction ids
    declared_junction_ids: set[str] = {
        junction.get("id") for junction in junctions if junction.get("id") is not None
    }

    # Collect all roads
    roads: list[etree._ElementTree] = utils.get_roads(checker_data.input_file_xml_root)

    # Iterate over all roads, checking the referenced junction ids (if any)
    for road in roads:
        _check_referenced_junction_id_in_road(checker_data, road, declared_junction_ids)


def _check_referenced_junction_id_in_road(
    checker_data: models.CheckerData,
    road: etree._Element,
    declared_junction_ids: set[str],
) -> None:
    """
    Check if the junction id referenced by the road exists.

    Args:
        checker_data: The data needed to perform the check.
        road: The road element to check.
        declared_junction_ids: The set of declared (existing) junction ids.
    """
    junction_id = road.get("junction", "-1")
    if junction_id != "-1" and junction_id not in declared_junction_ids:
        msg = "Referenced junction does not exist."
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            description=msg,
            level=IssueSeverity.WARNING,
            rule_uid=RULE_UID,
        )

        checker_data.result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            xpath=checker_data.input_file_xml_root.getpath(road),
            description=msg,
        )

        checker_data.result.add_file_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            row=road.sourceline,
            column=0,
            description=msg,
        )
