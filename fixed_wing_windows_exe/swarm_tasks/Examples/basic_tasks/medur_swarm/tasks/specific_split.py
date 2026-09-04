"""'specificsplit' command ("Split Search"): the operator assigns specific
UAV groups to specific center points (SpecificSplitMission), as opposed to
plain 'split' which auto-groups a UAV list around center points
(AutoSplitMission, see split.py). Both converge on the same CSV-waypoint
flight engine, which split.py owns (run_split_or_specific_split_command)."""

import json

from mission_paths import uav_path_csv
from groupsplitspecific import SpecificSplitMission

from medur_swarm import state
from medur_swarm.utils import selected_swarm_indexes
from medur_swarm.tasks.runner import assign_mission_tasks


def start_specific_split_mission(decoded_index):
    """Parses a 'specificsplit,...' command and registers it as a
    background mission task for whichever UAV subset it targets, without
    touching the foreground dispatch loop. Only used for the
    concurrent-intercept path (a specificsplit arriving while something
    else is already running) -- a fresh top-level specificsplit dispatch
    still uses its own foreground loop (run_split_or_specific_split_command
    in split.py), unchanged."""
    msg_parts = decoded_index.split("_")
    center_lat_lon_array = json.loads(msg_parts[1])
    uav_array = json.loads(msg_parts[2])
    grid_space = json.loads(msg_parts[3])
    coverage_area = json.loads(msg_parts[4])
    assigned_uav_ids = [int(u) for group in uav_array for u in group]
    if not assigned_uav_ids or not set(assigned_uav_ids).issubset(set(state.pos_array)):
        print(
            "[concurrent specificsplit] rejected: group assignment",
            set(assigned_uav_ids),
            "not a subset of connected pos_array",
            set(state.pos_array),
        )
        return False
    selected_uav_ids = assigned_uav_ids
    split = SpecificSplitMission(
        origin=state.origin,
        center_lat_lons=center_lat_lon_array,
        drone_array=uav_array,
        grid_spacing=grid_space,
        coverage_area=coverage_area,
    )
    split.GroupSplitting(
        center_lat_lons=center_lat_lon_array,
        drone_array=uav_array,
        grid_spacing=grid_space,
        coverage_area=coverage_area,
    )
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    csv_paths_by_index = {}
    for bot_index in selected_indexes:
        uav_id = state.pos_array[bot_index]
        csv_paths_by_index[bot_index] = uav_path_csv(uav_id)
    assign_mission_tasks(csv_paths_by_index, "split")
    print(
        "[concurrent split] accepted during running mission",
        selected_uav_ids,
        selected_indexes,
    )
    return True


def parse_and_start_foreground(decoded_index):
    """The 'specificsplit' half of the foreground split/specificsplit
    dispatch block. Returns the resolved selected_uav_ids on success, or
    None if the command was rejected/failed to parse -- in either case
    the caller (split.run_split_or_specific_split_command) must abort the
    whole dispatch-loop iteration immediately, matching the original
    inline `continue` on both the subset-rejection and the except branch.
    """
    try:
        msg_parts = decoded_index.split("_")
        print("msg_parts", msg_parts)
        f = msg_parts[0]  # First coordinate pair
        center_lat_lon_array = msg_parts[1]  # All other coordinates
        center_lat_lon_array = json.loads(center_lat_lon_array)
        print("center_lat_lon_array", center_lat_lon_array)
        uav_array = msg_parts[2]
        uav_array = json.loads(uav_array)
        grid_space = msg_parts[3]
        grid_space = json.loads(grid_space)
        print("grid_space", grid_space)
        coverage_area = msg_parts[4]
        coverage_area = json.loads(coverage_area)
        print("coverage_area", coverage_area)
        # Subset gate: assigned UAVs must be a non-empty subset of
        # the currently-connected pos_array -- they no longer have
        # to cover every connected UAV, so some can be left out
        # for a separate command. selected_uav_ids/selected_indexes
        # (set below) gate the shared csv_file_paths/movement-loop
        # code further down so only these indexes are touched.
        assigned_uav_ids = [int(u) for group in uav_array for u in group]
        if not assigned_uav_ids or not set(assigned_uav_ids).issubset(
            set(state.pos_array)
        ):
            print(
                "[specificsplit] rejected: group assignment",
                set(assigned_uav_ids),
                "not a subset of connected pos_array",
                set(state.pos_array),
            )
            return None
        else:
            selected_uav_ids = assigned_uav_ids
            split = SpecificSplitMission(
                origin=state.origin,
                center_lat_lons=center_lat_lon_array,
                drone_array=uav_array,
                grid_spacing=grid_space,
                coverage_area=coverage_area,
            )
            isDone = split.GroupSplitting(
                center_lat_lons=center_lat_lon_array,
                drone_array=uav_array,
                grid_spacing=grid_space,
                coverage_area=coverage_area,
            )
            return selected_uav_ids
    except Exception as e:
        print("Exception", e)
        return None
