import logging

from lxml import etree

from qc_baselib import IssueSeverity
from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_geometry_connected_roads_connect_reference_lines"
CHECKER_DESCRIPTION = ("When roads connect as successors/predecessors their reference lines must connect as well.")
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

        # Check if the road is a connecting road
        road_is_a_connecting_road = (junction := road.get('junction')) is not None and int(junction) != -1

        # Skip the road if it is a connecting road (perhaps only predecessors need to be skipped in this case...)
        if road_is_a_connecting_road:
            continue

        # Check the roads reference-line connection with its successors
        road_successor = utils.get_road_linkage(road=road, linkage_tag=models.LinkageTag.SUCCESSOR)
        if road_successor:
            road_successor = road_id_to_road.get(road_successor.id)
            _check_road_connection(checker_data, road_successor, road, models.LinkageTag.SUCCESSOR)

        # Check the roads reference-line connection with its predecessors
        road_predecessor = utils.get_road_linkage(road=road, linkage_tag=models.LinkageTag.PREDECESSOR)
        if road_predecessor:
            road_predecessor = road_id_to_road.get(road_predecessor.id)
            _check_road_connection(checker_data, road_predecessor, road, models.LinkageTag.PREDECESSOR)

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
    r1_reference_ends = (utils.get_start_point_xyz_from_road_reference_line(road_1),
                         utils.get_end_point_xyz_from_road_reference_line(road_1))
    r2_reference_ends = (utils.get_start_point_xyz_from_road_reference_line(road_2),
                         utils.get_end_point_xyz_from_road_reference_line(road_2))
    
    # Calculate all distances between the reference line ends of the two roads
    distances = [utils.euclidean_distance(p1, p2) for p2 in r2_reference_ends for p1 in r1_reference_ends] 

    # Raise an issue if the minimum distance is greater than the tolerance threshold
    if min(distances) > TOLERANCE_THRESHOLD:
        _raise_issue(checker_data, road_1, road_2, linkage_tag)


def _raise_issue(checker_data, road_1: etree._Element, road_2: etree._Element, linkage_tag: models.LinkageTag) -> None:
    # Construct the msg and the element to report
    msg = f'reference line does not connect for {linkage_tag.name} road {road_1.get("id")} and road {road_2.get("id")}.'

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
        