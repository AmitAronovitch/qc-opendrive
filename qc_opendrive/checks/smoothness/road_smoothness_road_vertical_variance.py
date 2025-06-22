import logging
from collections.abc import Callable

from lxml import etree
import numpy as np

from qc_baselib import IssueSeverity
from qc_opendrive import constants
from qc_opendrive.base import utils, models
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_smoothness_vertical_variance"
CHECKER_DESCRIPTION = "The central elevations of the roads vary in a suspicious way"
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "mobileye.com:xodr:1.4.0:road_smoothness_vertical_variance"

DEFAULT_MAX_VERTICAL_ROAD_GAP = 150.0


class RoadHeigtIssueRaiser:
    def __init__(self, checker_data: models.CheckerData):
        self.root = checker_data.input_file_xml_root
        self.result = checker_data.result
        self.common_args = dict(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
        )

    def register_issue(self, description: str) -> dict:
        issue_id = self.result.register_issue(
            description=description,
            level=IssueSeverity.WARNING,
            rule_uid=RULE_UID,
            **self.common_args,
        )
        return dict(issue_id=issue_id, **self.common_args)

    def road_xml_refs(self, road: etree._ElementTree) -> tuple[etree._ElementTree, str]:
        elevation_profile = road.find("elevationProfile")
        xml_object = road if elevation_profile is None else elevation_profile
        return xml_object, self.root.getpath(xml_object)

    @staticmethod
    def road_middle_point(road: etree._ElementTree) -> models.Point3D:
        mid_s = utils.get_road_length(road) / 2.0
        return utils.get_point_xyz_from_road_reference_line(road, mid_s)

    def add_road_locations(
        self, issue_args: dict, road: etree._ElementTree, description: str
    ):
        xml_object, xpath = self.road_xml_refs(road)
        self.result.add_xml_location(xpath=xpath, description=description, **issue_args)
        self.result.add_file_location(
            row=xml_object.sourceline, column=0, description=description, **issue_args
        )

        inertial_point = self.road_middle_point(road)
        self.result.add_inertial_location(
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description=description + " (road midpoint)",
            **issue_args,
        )

    def raise_empty_elevation_issue(
        self, road: etree._ElementTree, road_desc: str
    ) -> None:
        issue_args = self.register_issue(
            "Should not have roads with null elevation in a map that has non-zero elevations"
        )
        self.add_road_locations(issue_args, road, road_desc)

    def raise_elevation_gap_issue(
        self, low_road: etree._ElementTree, high_road: etree._ElementTree, gap: float
    ) -> None:
        issue_args = self.register_issue(
            f"Should not have large gaps between elevations of different roads ({gap=})"
        )
        self.add_road_locations(issue_args, low_road, "lower road")
        self.add_road_locations(issue_args, high_road, "higher road")


def _is_empty_elevations(road: etree._ElementTree) -> bool:
    elevations = utils.get_road_elevations(road)
    return all(
        utils.are_same_equations(elevation, utils.ZERO_OFFSET_POLY3)
        for elevation in elevations
    )


def _check_partly_empty_elevations(
    road_id_map: dict[int, etree._ElementTree],
    raise_issue: Callable[[etree._ElementTree, str], None],
) -> None:
    non_empty_ids, empty_ids = tuple(set() for _ in range(2))
    for road_id, road in road_id_map.items():
        if _is_empty_elevations(road):
            empty_ids.add(road_id)
        else:
            non_empty_ids.add(road_id)

    if non_empty_ids and empty_ids:
        logging.debug(
            f"{len(empty_ids)} roads with null elevation, and {len(non_empty_ids)} nonempty ones"
        )
        non_empty_id = next(iter(non_empty_ids))
        raise_issue(road_id_map[non_empty_id], "nonzero elevation road")
        for empty_id in empty_ids:
            raise_issue(road_id_map[empty_id], "null elevation road")


def _road_middle_elevation(road: etree._ElementTree) -> float:
    mid_s = utils.get_road_length(road) / 2.0
    elevation = utils.get_elevation_from_road_by_s(road, mid_s)
    return utils.calculate_elevation_value(elevation, mid_s)


def _check_mid_elevation_gaps(
    road_id_map: dict[int, etree._ElementTree],
    max_gap: float,
    raise_issue: Callable[[etree._ElementTree, etree._ElementTree, float], None],
) -> None:
    roads = list(road_id_map.values())
    mid_elevations = np.array([_road_middle_elevation(road) for road in roads])

    elevation_inds = np.argsort(mid_elevations)
    sorted_z = mid_elevations[elevation_inds]
    gaps = sorted_z[1:] - sorted_z[:-1]
    large_gaps = np.nonzero(gaps > max_gap)[0]
    if len(large_gaps) > 0:
        logging.debug(f"{len(large_gaps)} gaps found")
        for gap_ind in large_gaps:
            gap = gaps[gap_ind]
            low_road, high_road = (
                roads[ind] for ind in elevation_inds[gap_ind : gap_ind + 2]
            )
            raise_issue(low_road, high_road, gap)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road_smoothness_vertical_variance

    Description: High variance between elevation profiles of different roads may indicate
    problems in the map generation process, and can cause issues in automatic terrain
    generation software used for importing the map to a high resolution simulator.
    This rule is tested by two checks. A specific test for roads with null elevations in
    maps that also contain roads with non-zero elevation, and also a test for large gaps
    in the sorted list of road mid-point elevations.

    Severity: WARNING

    Version range: [1.4.0, )

    Remark:
        - Check is disabled when the map does not have more than one road.
        - The mid-elevation gaps check can be relaxed (or effectively disabled) by
          increasing the `maxVerticalRoadGap` parameter (may be useful in maps that
          have very steep and long roads).

    More info at
        - Not available yet.
    """
    logging.info("Executing road_smoothness_vertical_variance check.")

    # raised_issue_xpaths = set()
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    if len(road_id_map) < 2:
        logging.debug("road_smoothness_vertical_variance skipped (one road only)")
        return

    issuer = RoadHeigtIssueRaiser(checker_data)
    _check_partly_empty_elevations(road_id_map, issuer.raise_empty_elevation_issue)

    config_max_gap = checker_data.config.get_checker_param(
        constants.BUNDLE_NAME, CHECKER_ID, "maxVerticalRoadGap"
    )
    max_vertical_road_gap = (
        DEFAULT_MAX_VERTICAL_ROAD_GAP
        if config_max_gap is None
        else float(config_max_gap)
    )
    _check_mid_elevation_gaps(
        road_id_map, max_vertical_road_gap, issuer.raise_elevation_gap_issue
    )
