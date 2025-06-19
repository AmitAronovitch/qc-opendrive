# Changes in ASAM bundle

* Support for ignoring preconditions
* Replaced the `valid_schema` checker with `me_valid_schema`, suppressing some specific errors
* New checkers

TODO:

+ link checker descriptions to sections in the standard.

# Added checkers & rules

## Reference line connectivity

name: `connected_roads_connect_reference_lines` (ERROR)

Geometric distance between edges of roads connected (by `successor`/`predecessor` links) must be
smaller than threshold.

If one of the roads is a junction connecting road, then continuity is not checked.

## Gaps in between elevation profiles of roads

name: `road_smoothness_road_vertical_variance` (WARNING)

High variance between elevation profiles of different roads may indicate problems in the map
generation process, and can cause issues in automatic terrain generation software used for
importing the map to a high resolution simulator.

## Junction References

name: `referenced_junction_id_exists` (WARNING)

Verifies that the ids (other than -1) referenced in the `junction` attribute of roads actually exist.

## Road References

name: `referenced_road_id_exists` (WARNING)

Verifies that the road *and junction* ids referenced in:

 + `successor`/`predecessor` links in roads.
 + `incomingRoad`/`connectingRoad` attribs of junction connections.

Actually exist.

## Incoming roads number

name: `junctions_incoming_roads_number`

Junctions must contain at least 2 incoming roads (INFORMATION)

## Lanes connnect with conflicting driving directions

name: `lanes_connect_with_reversed_direction` (WARNING)

# General information

## Preconditions and checker run order

The checkers are run in pre-defined order. Most of them have preconditions, and checks are skipped
if any of their preconditions did not finish successfuly.

### Basic checks

In this category, each checker depends on all previous ones, in this order

1. `valid_xml_document`
2. `root_tag_is_opendrive`
3. `fileheader_is_present`
4. `root_tag_is_opendrive`

### XML schema

Original `valid_schema` is available in the code, but was explicitly replaced with `me_valid_schema`
in preconditions of all checks that depend on it.

5. `me_valid_schema`

All checks in categories below this one have this (as well as 1-4) as preconditions (1-5 is `basic_preconditions`).

### Semantic

+ `road_lane_level_true_one_side`
+ `road_lane_access_no_mix_of_deny_or_allow`
+ `road_lane_link_lanes_across_lane_sections`
+ `road_linkage_is_junction_needed`
+ `road_lane_link_zero_width_at_start`
+ `road_lane_link_zero_width_at_end`
+ `road_lane_link_new_lane_appear`
+ `junctions_connection_connect_road_no_incoming_road`
+ `junctions_connection_one_connection_element`
+ `junctions_connection_one_link_to_incoming`
+ `junctions_connection_start_along_linkage`
+ `junctions_connection_end_opposite_linkage`

### Geometry

+ `road_geometry_parampoly3_length_match`
+ `road_lane_border_overlap_with_inner_lanes`
+ `road_geometry_parampoly3_arclength_range`
+ `road_geometry_parampoly3_normalized_range`

### Performance

+ `performance_avoid_redundant_info`

### Smoothness

+ `lane_smoothness_contact_point_no_horizontal_gaps`

### ME Added

**Geometry**:

1. `connected_roads_connect_reference_lines`: Used as preconditin by [6.].

**Smoothness**:

2. `road_smoothness_road_vertical_variance`

**Semantic**:

3. `referenced_junction_id_exists`
4. `referenced_road_id_exists`
5. `junctions_incoming_roads_number`
6. `lanes_connect_with_reversed_direction`: This one has [1.] as precondition.
