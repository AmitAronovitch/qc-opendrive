import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_junction_incoming_roads_number"
CHECKER_DESCRIPTION = "Junctions must have at least 2 incoming road (recommended)."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "me.net:xodr:1.4.0:junctions.incoming_roads_number"


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if all junctions have at least 2 incoming roads.

    Args:
        checker_data: The data needed to perform the check.
    """
    logging.info(f"Executing {RULE_UID}")

    # Collect all declared junctions
    junctions = utils.get_junctions(checker_data.input_file_xml_root)

    # Iterate over all junctions, checking the number of incoming roads
    for junction in junctions:
        _check_junction_incoming_roads(checker_data, junction)


def _check_junction_incoming_roads(checker_data: models.CheckerData, junction: etree._Element) -> None:
    """
    Check if the junction contains at least 2 incoming roads.

    Args:
        checker_data: The data needed to perform the check.
        junction: The junction element to check.
    """
    connections = utils.get_connections_from_junction(junction)
    incoming_roads = set([c.get('incomingRoad', None) for c in connections])
    if len(incoming_roads) < 2:
        msg = "Junction does not contain at least 2 incoming roads."
        issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    description=msg,
                    level=IssueSeverity.INFORMATION,
                    rule_uid=RULE_UID)
        
        checker_data.result.add_xml_location(
             checker_bundle_name=constants.BUNDLE_NAME,
             checker_id=CHECKER_ID,
             issue_id=issue_id,
             xpath=checker_data.input_file_xml_root.getpath(junction),
             description=msg)
        
        checker_data.result.add_file_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            row=junction.sourceline,
            column=0,
            description=msg)

