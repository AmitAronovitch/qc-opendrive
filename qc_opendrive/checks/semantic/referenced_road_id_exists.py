import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_id_exists"
CHECKER_DESCRIPTION = "Referenced road id must exist."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "me.net:xodr:1.4.0:roads.id.exists"


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if all road ids referenced by roads and junctions have a road element with that id.

    Args:
        checker_data: The data needed to perform the check.
    """
    logging.info(f"Executing {RULE_UID}")

    # Collect all declared roads
    roads = utils.get_roads(checker_data.input_file_xml_root)

    # Collect all declared road ids
    declared_road_ids: set[str] = {
        road.get("id") for road in roads if road.get("id") is not None
    }

    # Collect all junctions (since those reference roads as well)
    junctions = utils.get_junctions(checker_data.input_file_xml_root)

    # Collect all declared junction ids
    declared_junction_ids: set[str] = {
        junction.get("id") for junction in junctions if junction.get("id") is not None
    }

    # Iterate over all roads, checking the referenced road ids (if any)
    for road in roads:
        _check_referenced_road_id_in_road(
            checker_data=checker_data,
            road=road,
            declared_road_ids=declared_road_ids,
            declared_junction_ids=declared_junction_ids,
        )

    # Iterate over all junctions, checking the referenced road ids (if any)
    for junction in junctions:
        _check_referenced_road_id_in_junction(checker_data, junction, declared_road_ids)


def _check_referenced_road_id_in_junction(
    checker_data: models.CheckerData,
    junction: etree._Element,
    declared_road_ids: set[str],
) -> None:
    """
    Check if the road id referenced by the junction exists.

    Args:
        checker_data: The data needed to perform the check.
        junction: The junction to check.
        declared_road_ids: The set of declared (existing) road ids.
    """
    # Find all junction connections
    connections = utils.get_connections_from_junction(junction)

    # Check each connection
    for connection in connections:
        incoming_road_id = connection.get("incomingRoad")
        connecting_road_id = connection.get("connectingRoad")

        if incoming_road_id is not None and incoming_road_id not in declared_road_ids:
            _raise_connection_issue(checker_data, connection, "incomingRoad")
        if (
            connecting_road_id is not None
            and connecting_road_id not in declared_road_ids
        ):
            _raise_connection_issue(checker_data, connection, "connectingRoad")


def _raise_issue(
    checker_data: models.CheckerData, issue_element: etree._Element, msg: str
) -> None:
    """
    Raises an issue for a an element, using the passed msg.

    Args:
        checker_data: The data needed to perform the check
        issue_element: The element to raise the issue for.
        msg: The message to use.
    """
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=msg,
        level=IssueSeverity.WARNING,
        rule_uid=RULE_UID,
    )

    # Add xml location
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(issue_element),
        description=msg,
    )

    # Add file location
    checker_data.result.add_file_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        row=issue_element.sourceline,
        column=0,
        description=msg,
    )


def _raise_connection_issue(
    checker_data: models.CheckerData, connection: etree._Element, road_type: str
) -> None:
    """
    Raise an issue for a connection element within a junction.

    Args:
        checker_data: The data needed to perform the check.
        connection: The referenced connection element.
        road_type: The declared road type (incomingRoad/connectingRoad).
    """
    # Create issue
    _raise_issue(
        checker_data, connection, msg=f"Referenced {road_type} does not exist."
    )


def _raise_road_or_junction_issue(
    checker_data: models.CheckerData,
    issue_element: etree._Element,
    linkage_tag: models.LinkageTag,
) -> None:
    """
    Raise an issue for a road element.

    Args:
        issue_element: The referenced road/junction element.
        linkage_tag: The linkage tag of the road element (successor/predecessor).
    """
    # Create issue
    _raise_issue(
        checker_data,
        issue_element,
        msg=f"Referenced {linkage_tag.name} {issue_element.get('elementType')} id does not exist.",
    )


def _check_referenced_road_id_in_road(
    checker_data: models.CheckerData,
    road: etree._Element,
    declared_road_ids: set[str],
    declared_junction_ids: set[str],
) -> None:
    """
    Check if the road id referenced by the road exists.

    Args:
        checker_data: The data needed to perform the check.
        road: The road to check.
        declared_road_ids: The set of declared (existing) road ids.
    """
    # Fetch the successor and predecessor elements (could be either roads or junctions)
    successor = road.find(".//link/successor")
    predecessor = road.find(".//link/predecessor")

    # Extract successor and predecessor road ids, if any
    successor_id = (
        (successor.get("elementId"), successor.get("elementType"))
        if successor is not None
        else None
    )
    predecessor_id = (
        (predecessor.get("elementId"), predecessor.get("elementType"))
        if predecessor is not None
        else None
    )

    if successor_id is not None:
        # Check if the successor road id exists
        if (successor_id[1] == "road") and (successor_id[0] not in declared_road_ids):
            _raise_road_or_junction_issue(checker_data, successor, "successor")

        # Check if the successor junction id exists
        if (successor_id[1] == "junction") and (
            successor_id[0] not in declared_junction_ids
        ):
            _raise_road_or_junction_issue(checker_data, successor, "successor")

    if predecessor_id is not None:
        # Check if the predecessor road id exists
        if (predecessor_id[1] == "road") and (
            predecessor_id[0] not in declared_road_ids
        ):
            _raise_road_or_junction_issue(checker_data, predecessor, "predecessor")

        # Check if the predecessor junction id exists
        if (predecessor_id[1] == "junction") and (
            predecessor_id[0] not in declared_junction_ids
        ):
            _raise_road_or_junction_issue(checker_data, predecessor, "predecessor")
