import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions
from qc_opendrive.checks.geometry import connected_roads_connect_reference_lines

CHECKER_ID = "check_asam_xodr_lanes_connect_with_reversed_direction"
CHECKER_DESCRIPTION = "Lanes should connect with reversed direction. This is just a warning, not a spec violation"
CHECKER_PRECONDITIONS = set([connected_roads_connect_reference_lines]) | basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "me.net:xodr:1.4.0:connected_lanes.direction.reversed"
TOLERANCE_THRESHOLD = 0.001


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to warn if connected lanes (across different roads) have reversed traffic directions.

    Args:
        checker_data: The data needed to perform the check.
    """
    logging.info(f"Executing {RULE_UID}")
    
    # Get all roads
    roads_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    # Get all junctions
    junctions_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    # Iterate over all roads, checking lane connections for each road
    for road_id, road in roads_id_map.items():
        _check_road_lanes(checker_data, road, junctions_id_map, roads_id_map)
        

def _check_road_lanes(checker_data: models.CheckerData, 
                      road: etree._Element, 
                      junctions_id_map: dict[str, etree._Element],
                      roads_id_map: dict[str, etree._Element]) -> None:
    """
    Check if the lanes of the road connect to a lane from another road with a reversed 
    traffic direction (reference line directions are reversed while the lane id signs 
    are identical or reference line directions match but the lane id signs are opposite).

    Args:
        checker_data: The data needed to perform the check.
        road: The road element to check.
        junctions_id_map: A map of junction IDs to junction elements.
        roads_id_map: A map of road IDs to road elements.
    """
    # Get all of the road's lanes from the last lane section
    lane_sections = utils.get_lane_sections(road)
    lanes = utils.get_lanes(lane_sections[-1])

    # Iterate over all lanes
    for lane in lanes:

        # Find the connections for each lane
        connected_lanes_with_roads: tuple[etree._Element, etree._Element] = \
            _get_connected_lanes_with_roads(lane, road, junctions_id_map, roads_id_map)

        # If we have any connections, check the reference line directions versus the reference line directions of the current lane
        for connected_lane, connected_road in connected_lanes_with_roads:

            # Get the sign match between the lane IDs
            signs_reversed = (int(lane.get('id')) ^ int(connected_lane.get('id'))) < 0

            # Get the reference line direction match
            reference_line_direction_reversed = _is_reference_line_direction_reversed(road, connected_road)

            # If there is a mismatch in only one value - traffic directions with collide
            if signs_reversed ^ reference_line_direction_reversed:
                _raise_issue(checker_data, lane, connected_lane, road, connected_road)


def _get_connected_lanes_with_roads(lane: etree._Element, 
                                    road: etree._Element, 
                                    junctions_id_map: dict[str, etree._Element],
                                    roads_id_map: dict[str, etree._Element]) \
                                        -> list[tuple[etree._Element, etree._Element]]:
    """
    Get the connected lanes and their containing roads for the given lane and road.

    Args:
        lane: The lane element to get the connected lanes for.
        road: The road element containing the lane.
        junctions_id_map: A map of junction IDs to junction elements.
        roads_id_map: A map of road IDs to road elements.

    Returns:
        A list of tuples where each tuple contains the connected lane and its road.
    """
    connected_lanes_with_roads = []

    # Get the road's successor and predecessor road IDs
    successor_road_id = utils.get_successor_road_id(road)
    successor_road = roads_id_map.get(successor_road_id)
    
    # If the lane has a link element - add the connected lane
    if successor_road is not None and \
        (linked_lane := utils.get_lane_link_element(lane, 
                                                    successor_road_id, 
                                                    models.LinkageTag.SUCCESSOR)) is not None:
        connected_lanes_with_roads.append((linked_lane, successor_road))

    # Get the road's successor junction
    successor_junction_id = utils.get_linked_junction_id(road, models.LinkageTag.SUCCESSOR)
    successor_junction = junctions_id_map.get(successor_junction_id, None)

    # We have a connected junction - check its connections to our road and lane
    if successor_junction is not None:
        junction_connections = utils.get_connections_from_junction(successor_junction)

        # Keep only the junction connections where the incoming road has the same id as our road
        junction_connections = [jc for jc in junction_connections if jc.get('incomingRoad') == road.get('id')]

        # Get the lane links that match out lane id for each junction connection
        junction_connections_with_lane_links = \
            [(jc, [ll for ll in utils.get_lane_links_from_connection(jc) if ll.get('from') == lane.get('id')]) \
             for jc in junction_connections]

        # Iterate over the junction connections with lane links and add a connected lane for every remaining link
        for junction_connection_with_lane_links in junction_connections_with_lane_links:

            # Iterate over all remaining links in the connection
            for lane_link in junction_connection_with_lane_links[1]:

                # Get the connected road element
                connected_road = roads_id_map.get(int(junction_connection_with_lane_links[0].get('connectingRoad')))

                # Get the lane_section-0 for the connected road
                connected_lane_sections = utils.get_lane_sections(connected_road)

                if connected_lane_sections:

                    # Leave only connected lanes that match our connection-to link
                    connected_lanes = [l for l in utils.get_lanes(connected_lane_sections[0]) if l.get('id') == lane_link.get('to')]

                    if connected_lanes: 
                        # We have a connected lane matching the linked id - add it with its connecting road
                        connected_lanes_with_roads.append((connected_lanes[0], connected_road))

    return connected_lanes_with_roads


def _is_reference_line_direction_reversed(road: etree._Element, connected_road: etree._Element) -> bool:
    """
    Check if the reference line directions of the given roads are reversed.

    Args:
        road: The road element to check.
        connected_road: The road element to compare reference lines with.

    Returns:
        True if the reference line directions are reversed, False otherwise.
    """
    # Directions will be reversed if the two reference lines share an ending point or a starting point
    road_start_end = (utils.get_start_point_xyz_from_road_reference_line(road),
                      utils.get_end_point_xyz_from_road_reference_line(road))
    connected_road_start_end = (utils.get_start_point_xyz_from_road_reference_line(connected_road),
                                utils.get_end_point_xyz_from_road_reference_line(connected_road))
    return \
        utils.euclidean_distance(road_start_end[1], connected_road_start_end[1]) < TOLERANCE_THRESHOLD or \
        utils.euclidean_distance(road_start_end[0], connected_road_start_end[0]) < TOLERANCE_THRESHOLD


def _raise_issue(checker_data: models.CheckerData, lane: etree._Element, connected_lane: etree._Element, 
                 road: etree._Element, connected_road: etree._Element) -> None:
    """
    Raise an issue for the lanes that connect with reversed traffic directions.
    
    Args:
        checker_data: The data needed to perform the check.
        lane: The lane element being checked.
        connected_lane: The lane element that the lane being checked connected to, with a reversed traffic direction.
        road: The road element of the lane being checked.
        connected_road: The road element containing the connected lane with the reversed traffic direction.
    """
    # Construct the msg and the element to report
    msg = f'lane {lane.get("id")} of road {road.get("id")} connects to lane {connected_lane.get("id")} of road {connected_road.get("id")} with a reversed traffic direction'

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
        xpath=checker_data.input_file_xml_root.getpath(lane),
        description=msg,
    )

    # Add file location
    checker_data.result.add_file_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        row=lane.sourceline,
        column=0,
        description=msg,
    )
