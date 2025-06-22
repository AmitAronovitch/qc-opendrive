import logging

from lxml import etree

from qc_baselib import IssueSeverity
from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_geometry_connected_roads_connect_reference_lines"
CHECKER_DESCRIPTION = "When roads connect as successors/predecessors their reference lines must connect as well."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:road.geometry.referece_lines_connect_along_paired_roads"
TOLERANCE_THRESHOLD = 0.001


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.geometry.referece_lines_connect_along_paired_roads

    Description: When roads connect as successors/predecessors their reference lines must connect as well.

    Severity: ERROR

    Version range: [1.4.0, )
    """
    logging.info(f"Executing {CHECKER_ID}.")

    road_id_to_road = utils.get_road_id_map(checker_data.input_file_xml_root)

    # Iterate over all roads, testing successors and predecessors for reference-line connection
    for road in road_id_to_road.values():

        # Check the roads reference-line connection with its successors
        road_successor = utils.get_road_linkage(
            road=road, linkage_tag=models.LinkageTag.SUCCESSOR
        )
        if road_successor:
            road_successor = road_id_to_road.get(road_successor.id)

            # Check the connection only if the road is not a connecting road within a junction
            if road_successor is not None and not utils.road_belongs_to_junction(
                road_successor
            ):
                _check_road_connection(
                    checker_data, road_successor, road, models.LinkageTag.SUCCESSOR
                )

        # Check the connection to the predecessor only if the road is not a connecting road within a junction
        if not utils.road_belongs_to_junction(road):
            road_predecessor = utils.get_road_linkage(
                road=road, linkage_tag=models.LinkageTag.PREDECESSOR
            )
            if road_predecessor:
                road_predecessor = road_id_to_road.get(road_predecessor.id)
                if road_predecessor is not None:
                    _check_road_connection(
                        checker_data,
                        road_predecessor,
                        road,
                        models.LinkageTag.PREDECESSOR,
                    )


def _check_road_connection(checker_data, road_1, road_2, linkage_tag) -> None:
    """
    Check if the reference lines of two roads connect.

    Args:
        checker_data: The data needed to perform the check.
        road_1: The first road to check.
        road_2: The second road to check.
        linkage_tag: The linkage tag that connects the two roads
    """
    # Collect the reference line ends of the two roads
    r1_reference_ends = (
        utils.get_start_point_xyz_from_road_reference_line(road_1),
        utils.get_end_point_xyz_from_road_reference_line(road_1),
    )
    r2_reference_ends = (
        utils.get_start_point_xyz_from_road_reference_line(road_2),
        utils.get_end_point_xyz_from_road_reference_line(road_2),
    )

    # Calculate all distances between the reference line ends of the two roads
    distances = [
        utils.euclidean_distance(p1, p2)
        for p2 in r2_reference_ends
        for p1 in r1_reference_ends
    ]

    # Raise an issue if the minimum distance is greater than the tolerance threshold
    if min(distances) > TOLERANCE_THRESHOLD:
        _raise_issue(checker_data, road_1, road_2, linkage_tag)


def _raise_issue(
    checker_data,
    road_1: etree._Element,
    road_2: etree._Element,
    linkage_tag: models.LinkageTag,
) -> None:
    """
    Raise an issue for a road that does not connect to another road.

    Args:
        checker_data: The data needed to perform the check.
        road_1: The first road to check.
        road_2: The second road to check.
        linkage_tag: The linkage tag that connects the two roads (2nd road to first, so a PREDECESSOR tag
            means that road_2 is the predecessor of road_1).
    """
    # Construct the msg to report
    r1_name = f'{road_1.get("id")}{" (Connecting)" if utils.road_belongs_to_junction(road_1) else ""}'
    r2_name = f'{road_2.get("id")}{" (Connecting)" if utils.road_belongs_to_junction(road_2) else ""}'
    msg = f"reference line does not connect for road {r2_name} and its {linkage_tag.name} road {r1_name}."

    # Cinstruct an issue
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=msg,
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )

    # Add xml location
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(road_2),
        description=msg,
    )

    # Add file location
    checker_data.result.add_file_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        row=road_2.sourceline,
        column=0,
        description=msg,
    )
