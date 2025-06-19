import logging

from typing import List, Dict, Optional, Set
from lxml import etree
from scipy.spatial import distance

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import utils, models
from qc_opendrive import basic_preconditions


CHECKER_ID = "check_asam_xodr_road_smoothness_vertical_variance"
CHECKER_DESCRIPTION = "The variance of roads' cental height is suspiciosly high."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road_smoothness_vertical_variance"


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:lane_smoothness.contact_point_no_horizontal_gaps

    Description: Two connected drivable lanes shall have no horizontal gaps.
    There is no gap between two connected lanes in s-direction if the x,y values
    of the contact points of the two connected lanes match. There shall be no
    plan view gaps in its reference line geometry definition

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        - Only lanes of drivable types would be checked.
        - The rule will trigger one issue for each logical link. If lanes are
        connected as successor and predecessor, the rule will trigger 2 issues
        for the given connection.

    More info at
        - Not available yet.
    """
    logging.info("Executing road_smoothness_vertical_variance check.")

    raised_issue_xpaths = set()
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    for road in road_id_map.values():
        pass
