# Checker bundle: xodrMEBundle

* Build version:  v1.0.0-rc.1
* Description:    OpenDrive checker bundle

## Parameters

* InputFile
* resultFile

## Checkers

### check_asam_xodr_xml_valid_xml_document

* Description: The input file must be a valid XML document.
* Addressed rules:
  * asam.net:xodr:1.0.0:xml.valid_xml_document

### check_asam_xodr_xml_root_tag_is_opendrive

* Description: The root element of a valid XML document must be OpenSCENARIO.
* Addressed rules:
  * asam.net:xodr:1.0.0:xml.root_tag_is_opendrive

### check_asam_xodr_xml_fileheader_is_present

* Description: Below the root element a tag with FileHeader must be defined.
* Addressed rules:
  * asam.net:xodr:1.0.0:xml.fileheader_is_present

### check_asam_xodr_xml_version_is_defined

* Description: The FileHeader tag must have the attributes revMajor and revMinor and of type unsignedShort.
* Addressed rules:
  * asam.net:xodr:1.0.0:xml.version_is_defined

### check_asam_xodr_xml_me_valid_schema

* Description: Input xml file must be valid according to the schema, filtered by ME needs, but some elements will raise only warnings and not errors.
* Addressed rules:
  * asam.net:xodr:1.0.0:xml.me_valid_schema

### check_asam_xodr_road_lane_level_true_one_side

* Description: Check if there is any @Level=False after being True until the lane border.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.lane.level_true_one_side

### check_asam_xodr_road_lane_access_no_mix_of_deny_or_allow

* Description: Check if there is mixed content on access rules for the same sOffset on lanes.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.lane.access.no_mix_of_deny_or_allow

### check_asam_xodr_road_lane_link_lanes_across_lane_sections

* Description: Lanes that continues across the lane sections shall be connected in both directions.
* Addressed rules:
  * asam.net:xodr:1.4.0:road.lane.link.lanes_across_lane_sections

### check_asam_xodr_road_linkage_is_junction_needed

* Description: Two roads shall only be linked directly, if the linkage is clear. If the relationship to successor or predecessor is ambiguous, junctions shall be used.
* Addressed rules:
  * asam.net:xodr:1.4.0:road.linkage.is_junction_needed

### check_asam_xodr_road_lane_link_zero_width_at_start

* Description: Lanes that have a width of zero at the beginning of the lane section shall have no predecessor element.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start

### check_asam_xodr_road_lane_link_zero_width_at_end

* Description: Lanes that have a width of zero at the end of the lane section shall have no successor element.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end

### check_asam_xodr_road_lane_link_new_lane_appear

* Description: If a new lane appears besides, only the continuing lane shall be connected to the original lane, not the appearing lane.
* Addressed rules:
  * asam.net:xodr:1.4.0:road.lane.link.new_lane_appear

### check_asam_xodr_junctions_connection_connect_road_no_incoming_road

* Description: Connecting roads shall not be incoming roads.
* Addressed rules:
  * asam.net:xodr:1.4.0:junctions.connection.connect_road_no_incoming_road

### check_asam_xodr_junctions_connection_one_connection_element

* Description: Each connecting road shall be represented by exactly one element. A connecting road may contain as many lanes as required.
* Addressed rules:
  * asam.net:xodr:1.7.0:junctions.connection.one_connection_element

### check_asam_xodr_junctions_connection_one_link_to_incoming

* Description: Each connecting road shall be associated with at most one <connection> element per incoming road. A connecting road shall only have the <laneLink> element for that direction.
* Addressed rules:
  * asam.net:xodr:1.8.0:junctions.connection.one_link_to_incoming

### check_asam_xodr_junctions_connection_start_along_linkage

* Description: The value "start" shall be used to indicate that the connecting road runs along the linkage indicated in the element.
* Addressed rules:
  * asam.net:xodr:1.7.0:junctions.connection.start_along_linkage

### check_asam_xodr_junctions_connection_end_opposite_linkage

* Description: The value "end" shall be used to indicate that the connecting road runs along the opposite direction of the linkage indicated in the element.
* Addressed rules:
  * asam.net:xodr:1.7.0:junctions.connection.end_opposite_linkage

### check_asam_xodr_road_geometry_parampoly3_length_match

* Description: The actual curve length, as determined by numerical integration over the parameter range, should match '@Length'.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.geometry.parampoly3.length_match

### check_asam_xodr_road_lane_border_overlap_with_inner_lanes

* Description: Lane borders shall not intersect inner lanes.
* Addressed rules:
  * asam.net:xodr:1.4.0:road.lane.border.overlap_with_inner_lanes

### check_asam_xodr_road_geometry_parampoly3_arclength_range

* Description: If @prange='arcLength', p shall be chosen in [0, @Length from geometry].
* Addressed rules:
  * asam.net:xodr:1.7.0:road.geometry.parampoly3.arclength_range

### check_asam_xodr_road_geometry_parampoly3_normalized_range

* Description: If @prange='normalized', p shall be chosen in [0, 1].
* Addressed rules:
  * asam.net:xodr:1.7.0:road.geometry.parampoly3.normalized_range

### check_asam_xodr_performance_avoid_redundant_info

* Description: Redundant elements should be avoided.
* Addressed rules:
  * asam.net:xodr:1.7.0:performance.avoid_redundant_info

### check_asam_xodr_lane_smoothness_contact_point_no_horizontal_gaps

* Description: Two connected drivable lanes shall have no horizontal gaps.
* Addressed rules:
  * asam.net:xodr:1.7.0:lane_smoothness.contact_point_no_horizontal_gaps

### check_asam_xodr_road_geometry_connected_roads_connect_reference_lines

* Description: When roads connect as successors/predecessors their reference lines must connect as well.
* Addressed rules:
  * mobileye.com:xodr:1.4.0:road.geometry.referece_lines_connect_along_paired_roads

### check_asam_xodr_road_smoothness_vertical_variance

* Description: The central elevations of the roads vary in a suspicious way
* Addressed rules:
  * mobileye.com:xodr:1.4.0:road_smoothness_vertical_variance

### check_asam_xodr_junction_id_exists

* Description: Referenced junction id must exist.
* Addressed rules:
  * mobileye.com:xodr:1.4.0:junctions.id.exists

### check_asam_xodr_road_id_exists

* Description: Referenced road id must exist.
* Addressed rules:
  * mobileye.com:xodr:1.4.0:roads.id.exists

### check_asam_xodr_junction_incoming_roads_number

* Description: Junctions must have at least 2 incoming road (recommended).
* Addressed rules:
  * mobileye.com:xodr:1.4.0:junctions.incoming_roads_number

### check_asam_xodr_lanes_connect_with_reversed_direction

* Description: Lanes should connect with reversed direction. This is just a warning, not a spec violation
* Addressed rules:
  * mobileye.com:xodr:1.4.0:connected_lanes.direction.reversed
