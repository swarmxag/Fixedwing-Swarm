"""'split' command: auto-groups a UAV list around given center points
(AutoSplitMission). Owns the CSV-waypoint flight engine shared with
'specificsplit' ("Split Search", see specific_split.py) -- both commands
converge on run_split_or_specific_split_command below.
"""

import csv
import json
import math
import time

import locatePosition
from dronekit import LocationGlobalRelative
from mission_paths import uav_path_csv
from groupsplitauto import AutoSplitMission
from swarm_tasks.simulation import simulation as sim
from swarm_tasks.simulation import visualizer as viz

import swarm_tasks

from medur_swarm import config, state
from medur_swarm.uav.management import remove_vehicle
from medur_swarm.utils import (
    allocate_drones,
    read_specific_line,
    selected_swarm_indexes,
)
from medur_swarm.uav.guidance import (
    advance_bot_with_uav_pacing,
    real_uav_avoidance_vector,
    signed_uav_lead,
    uav_reached_waypoint,
)
from medur_swarm.uav.telemetry import live_gps_plot_points, print_sim_vs_real_latlon
from medur_swarm.tasks.runner import assign_mission_tasks, synchronize_mission_topology
from medur_swarm.communication.dispatch import check_for_new_command
from medur_swarm.tasks import specific_split


def lookahead_point(x, y, theta, distance=10):
    lx = x + distance * math.cos(theta)
    ly = y + distance * math.sin(theta)
    return (lx, ly)


def compute_lookahead_target(x, y, theta, rx, ry, distance, min_lead=None):
    """See tasks/search.py's copy of this function for the full rationale
    -- same pursuit-point algorithm, shared verbatim rather than imported
    across task modules to keep each mission module self-contained.

    tx,ty = the point handed to the real vehicle: a fixed point on the
    bot's heading line, distance ahead of the bot, that the vehicle
    closes on -- never a point that runs away from it, and never one
    that falls behind it.
    """
    if min_lead is None:
        min_lead = distance * 0.5

    # Signed distance of vehicle along the bot's current heading
    along = (rx - x) * math.cos(theta) + (ry - y) * math.sin(theta)

    target_along = max(distance, along + min_lead)

    return lookahead_point(x, y, theta, target_along)


def start_split_mission(decoded_index):
    """Parses a 'split,...' command and registers it as a background
    mission task for whichever UAV subset it targets, without touching
    the foreground dispatch loop. Only used for the concurrent-intercept
    path (split arriving while something else is already running) -- a
    fresh top-level split dispatch still uses its own foreground loop
    (run_split_or_specific_split_command), unchanged."""
    msg_parts = decoded_index.split("_")
    selected_uav_ids = [int(u) for u in json.loads(msg_parts[2])]
    grid_space = json.loads(msg_parts[3])
    coverage_area = json.loads(msg_parts[4])
    center_lat_lon_array = json.loads(msg_parts[1])
    if not selected_uav_ids or not set(selected_uav_ids).issubset(set(state.pos_array)):
        print(
            "[concurrent split] rejected: GCS selection",
            set(selected_uav_ids),
            "not a subset of connected pos_array",
            set(state.pos_array),
        )
        return False
    split = AutoSplitMission(
        origin=state.origin,
        center_lat_lons=center_lat_lon_array,
        drone_list=selected_uav_ids,
        grid_spacing=int(grid_space),
        coverage_area=int(coverage_area),
    )
    split.GroupSplitting(
        center_lat_lons=center_lat_lon_array,
        num_of_drones=len(selected_uav_ids),
        grid_spacing=int(grid_space),
        coverage_area=int(coverage_area),
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


def handle_concurrent_split_command(command_data):
    if not (
        command_data.startswith(b"split") or command_data.startswith(b"specificsplit")
    ):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        if decoded_index.startswith("specificsplit"):
            return specific_split.start_specific_split_mission(decoded_index)
        return start_split_mission(decoded_index)
    except Exception as e:
        print("[concurrent split] failed", e)
        return False


def run_split_or_specific_split_command(data):
    """The foreground 'split'/'specificsplit' dispatch-loop handler.

    Returns True when the calling loop must `continue` immediately (the
    original code's inline `continue` on a rejected UAV subset, or on a
    specificsplit parse/GroupSplitting exception) -- False/None otherwise,
    letting the caller fall through to whatever dispatch block comes next.

    Note the asymmetry, preserved exactly from the original: a plain
    'split' parse/GroupSplitting exception is swallowed *without*
    aborting the iteration (unlike specificsplit's identical-looking
    except block, which does abort) -- so a first-ever failed 'split'
    falls through to the shared movement-loop setup below with
    selected_uav_ids never assigned, which raises and is caught by
    main.py's own per-iteration exception handler, exactly as it would
    have in the original single-file script.
    """
    if not (data.startswith(b"split") or data.startswith(b"specificsplit")):
        return
    if data.startswith(b"specificsplit"):
        selected_uav_ids = specific_split.parse_and_start_foreground(
            data.decode("utf-8")
        )
        if selected_uav_ids is None:
            return True
    if data.startswith(b"split"):
        try:
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            msg_parts = decoded_index.split("_")
            print("msg_parts", msg_parts, len(msg_parts))
            f = msg_parts[0]  # First coordinate pair
            # msg_parts[2] is the operator's actual UAV-id selection from the
            # GCS (not just a headcount) -- honored below, gated as a
            # subset of the swarm computer's own live pos_array.
            selected_uav_ids = [int(u) for u in json.loads(msg_parts[2])]
            grid_space = msg_parts[3]
            grid_space = json.loads(grid_space)
            coverage_area = msg_parts[4]
            coverage_area = json.loads(coverage_area)
            center_lat_lon_array = msg_parts[1]  # All other coordinates
            center_lat_lon_array = json.loads(center_lat_lon_array)
            if not selected_uav_ids or not set(selected_uav_ids).issubset(
                set(state.pos_array)
            ):
                print(
                    "[split] rejected: GCS selection",
                    set(selected_uav_ids),
                    "not a subset of connected pos_array",
                    set(state.pos_array),
                )
                return True
            else:
                split = AutoSplitMission(
                    origin=state.origin,
                    center_lat_lons=center_lat_lon_array,
                    drone_list=selected_uav_ids,
                    grid_spacing=int(grid_space),
                    coverage_area=int(coverage_area),
                )
                isDone = split.GroupSplitting(
                    center_lat_lons=center_lat_lon_array,
                    num_of_drones=len(selected_uav_ids),
                    grid_spacing=int(grid_space),
                    coverage_area=int(coverage_area),
                )
        except Exception as e:
            print("Exception", e)

    _run_split_movement(selected_uav_ids)


def _run_split_movement(selected_uav_ids):
    state.split_flag = True
    state.split_flag_val = 0
    state.search_step = 1
    state.all_uav_csv_grid_array = [0] * len(state.pos_array)
    state.grid_path_array = [0] * len(state.pos_array)
    num_lines = [0] * len(state.pos_array)
    state.pop_flag_arr = [1] * len(state.pos_array)
    state.removed_uav_grid = []
    state.removed_grid_path_length = []
    state.uncovered_area_points = []
    state.uncovered_area_filename = []
    state.removed_grid_path_array_flag = False
    state.removed_grid_path_array = [0] * len(state.pos_array)
    state.removed_grid_filename = [0] * len(state.pos_array)
    state.removed_grid_path_array_start_val = [0] * len(state.pos_array)
    state.checkall_removed_grid_path_array_start_val = [0] * len(state.pos_array)
    state.remove_bot_flag = False
    state.remove_bot_array = []
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    selected_index_set = set(selected_indexes)
    print(
        "[split] selected_uav_ids",
        selected_uav_ids,
        "selected_indexes",
        selected_indexes,
    )
    gui = None
    if state.master_flag:
        state.index = "data"
        state.uav_home_pos = []
        for vehicle in state.vehicles:
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            state.uav_home_pos.append((x / 2, y / 2))
        swarm_tasks.utils.robot.DEFAULT_SIZE = 0.4
        state.s = sim.Simulation(
            state.uav_home_pos, num_bots=state.num_bots, env_name=state.file_name
        )
        gui = viz.Gui(state.s)

    print("Group Splitting Started")
    f = ""
    num_lines = [0] * len(state.pos_array)
    print("num_lines", num_lines)
    state.goal_bot_num = 0
    goal_position = []
    state.grid_path_array = [0] * len(state.pos_array)
    print("split_flag_val", state.split_flag_val)
    planned_paths_by_bot = [None] * len(state.pos_array)
    if state.split_flag_val == 0:
        state.split_flag_val += 1
        csv_file_paths = []
        # Both plain split (AutoSplitMission.drone_list=selected_uav_ids) and
        # specific_split (uav_array) only write per-drone files for the
        # selected subset -- so only build/open a file for each selected
        # bot_index (real UAV id via pos_array[bot_index]), never the
        # full pos_array, or an unselected UAV's missing file would
        # crash this open().
        for path_slot, bot_index in enumerate(selected_indexes):
            uav_id = state.pos_array[bot_index]
            csv_path = uav_path_csv(uav_id)
            csv_file_paths.append(csv_path)
            reader = csv.reader(open(csv_path))
            rows = list(reader)
            num_lines[bot_index] = len(rows)
            # Whole planned route cached once here (not every tick)
            # purely for the show_planned_path() overlay below.
            try:
                planned_paths_by_bot[bot_index] = [
                    (float(row[0]), float(row[1])) for row in rows
                ]
            except Exception as e:
                print("[planned-path] failed to parse for bot", bot_index, e)
        print("csv_file_paths", csv_file_paths, num_lines)
    state.removed_grid_path_array_index = 0
    my_seq = state.last_seq
    print("grid_path_array", state.grid_path_array)
    current_goals = [None] * len(state.pos_array)
    diverted_indexes = set()
    # Tell apply_different_heights this loop owns these bots' movement (covers
    # both plain 'split' and 'specificsplit', which converge here), so a
    # concurrent 'different' only re-targets their altitude -- picked up by the
    # simple_goto below next tick -- instead of spawning an altitude task that
    # would divert them out of the split for good.
    state.foreground_mission_indexes = set(selected_indexes)
    while 1:
        time.sleep(config.SLEEP_TIMES.get(state.num_bots))
        check_for_new_command(my_seq)
        if state.vehicle_lost_flag:
            state.vehicle_lost_flag = True
            x = remove_vehicle()
            print(x)
        if state.remove_bot_flag:
            for m in sorted(set(state.remove_bot_array), reverse=True):
                if 0 <= m < len(state.all_uav_csv_grid_array):
                    state.removed_uav_grid.append(state.all_uav_csv_grid_array[m])
                if 0 <= m < len(state.grid_path_array):
                    state.removed_grid_path_length.append(state.grid_path_array[m])
        selected_indexes = synchronize_mission_topology(
            selected_indexes,
            csv_file_paths,
            state.all_uav_csv_grid_array,
            state.grid_path_array,
            num_lines,
            current_goals,
            planned_paths_by_bot,
        )
        selected_index_set = set(selected_indexes)
        # Keep the "this loop owns these bots" set aligned after any add/remove.
        state.foreground_mission_indexes = set(selected_indexes)

        if state.search_step == 1:
            for path_slot, bot_index in enumerate(selected_indexes):
                if path_slot >= len(csv_file_paths) or bot_index >= len(
                    state.all_uav_csv_grid_array
                ):
                    print(
                        "[split] skipped stale path assignment",
                        path_slot,
                        bot_index,
                    )
                    continue
                state.all_uav_csv_grid_array[bot_index] = csv_file_paths[path_slot]
            print("all_uav_csv_grid_array", state.all_uav_csv_grid_array)
            state.search_step += 1
        for i, b in enumerate(state.s.swarm):
            if i not in selected_index_set:
                continue
            if i in state.active_goal_tasks:
                diverted_indexes.add(i)
            if i in diverted_indexes:
                continue
            if len(state.checkall_removed_grid_path_array_start_val) == len(
                state.pos_array
            ):
                if all(
                    c == 1 for c in state.checkall_removed_grid_path_array_start_val
                ):
                    state.landing_flag = True
            else:
                # print("length oflen(checkall_removed_grid_path_array_start_val",len(checkall_removed_grid_path_array_start_val))
                pass
            if (
                all(
                    state.grid_path_array[x] >= int(num_lines[x])
                    for x in selected_indexes
                )
                and state.removed_grid_path_length != []
                and not state.removed_grid_path_array_flag
            ):
                print("removed_grid_path_length", state.removed_grid_path_length)
                allocation, remaining_points_list = allocate_drones(
                    int(num_lines[i]),
                    state.removed_grid_path_length,
                    len(selected_indexes),
                )
                print(
                    "allocation,remaining_points_list",
                    allocation,
                    remaining_points_list,
                )
                for x, v in enumerate(remaining_points_list):
                    print("x", x)
                    if state.removed_grid_path_length[x] == 1:
                        start_index = state.removed_grid_path_length[x]
                    else:
                        start_index = state.removed_grid_path_length[x] - 1
                    print("start_index", start_index)
                    print("JJJ", allocation[x])
                    if (allocation[x] == 0) and state.removed_grid_path_length[
                        x
                    ] != int(num_lines[i]):
                        state.uncovered_area_points.append(
                            state.removed_grid_path_length[x]
                        )
                        state.uncovered_area_filename.append(state.removed_uav_grid[x])
                        print(
                            "uncovered_area_points",
                            x,
                            v,
                            state.uncovered_area_points,
                            state.uncovered_area_filename,
                        )
                        continue
                    elif allocation[x] == 0:
                        continue
                    add_points = math.ceil(
                        remaining_points_list[x] / allocation[x]
                    )
                    print("add_points", math.ceil(add_points))
                    end_index = start_index + add_points + 1
                    print("end_index", math.ceil(end_index))
                    for m in range(allocation[x]):
                        print(
                            "removed_grid_path_array_index",
                            state.removed_grid_path_array_index,
                        )
                        if m != 0:
                            end_index += add_points
                        if end_index > int(num_lines[i]):
                            end_index = int(num_lines[i])
                        state.removed_grid_path_array[
                            state.removed_grid_path_array_index
                        ] = (start_index, end_index)
                        state.removed_grid_path_array_start_val[
                            state.removed_grid_path_array_index
                        ] = start_index
                        state.removed_grid_filename[state.removed_grid_path_array_index] = (
                            state.removed_uav_grid[x]
                        )
                        print(
                            "removed_grid_path_array",
                            state.removed_grid_path_array,
                            state.removed_grid_path_array_start_val,
                            state.removed_grid_filename,
                        )
                        start_index = end_index
                        state.removed_grid_path_array_index += 1
                print(
                    "removed_grid_path_array!!!!!",
                    state.removed_grid_path_array,
                    state.removed_grid_path_array_start_val,
                    state.removed_grid_filename,
                )
                state.removed_grid_path_array_flag = True

            if (
                all(
                    state.grid_path_array[x] >= int(num_lines[x])
                    for x in selected_indexes
                )
                and not state.removed_grid_path_length != []
            ):
                state.landing_flag = True
            if state.removed_grid_path_array_flag:
                if state.removed_grid_path_array_start_val[i] == 0:
                    state.checkall_removed_grid_path_array_start_val[i] = 1
                    print(
                        "checkall_removed_grid_path_array_start_val",
                        state.checkall_removed_grid_path_array_start_val,
                    )
                    continue
                if (
                    state.removed_grid_path_array_start_val[i]
                    == state.removed_grid_path_array[i][1]
                ):
                    state.checkall_removed_grid_path_array_start_val[i] = 1
                    if state.uncovered_area_points != []:
                        print("uncovered_area_points", state.uncovered_area_points)
                        for u, uncovered_area_point in enumerate(
                            state.uncovered_area_points
                        ):
                            state.removed_grid_path_array[i] = (
                                uncovered_area_point,
                                int(num_lines[i]) + 1,
                            )
                            print(
                                "removed_grid_path_array",
                                state.removed_grid_path_array,
                            )
                            state.removed_grid_path_array_start_val[i] = (
                                state.uncovered_area_points[u]
                            )
                            state.removed_grid_filename[i] = state.uncovered_area_filename[
                                u
                            ]
                            state.removed_grid_path_array[i] = (
                                state.uncovered_area_points[u],
                                int(num_lines[i]),
                            )
                            print(
                                "removed_grid_path_array_start_val",
                                state.removed_grid_path_array_start_val,
                                state.removed_grid_filename,
                            )
                            state.checkall_removed_grid_path_array_start_val[i] = 0
                            state.uncovered_area_points.pop(u)
                            state.uncovered_area_filename.pop(u)
                    else:
                        continue
            if (
                state.grid_path_array[i] >= int(num_lines[i])
                and not state.removed_grid_path_array_flag
            ):
                continue
            if state.removed_grid_path_array_flag:
                goal_lat_lon = read_specific_line(
                    state.removed_grid_filename[i],
                    state.removed_grid_path_array_start_val[i],
                )
            else:
                goal_lat_lon = read_specific_line(
                    state.all_uav_csv_grid_array[i], state.grid_path_array[i]
                )
            x, y, isCurve = (
                goal_lat_lon[0][0],
                goal_lat_lon[0][1],
                goal_lat_lon[0][2],
            )
            goal = (x, y)
            current_goals[i] = goal
            current_position = [b.x, b.y]
            dx = abs(goal[0] - current_position[0])
            dy = abs(goal[1] - current_position[1])
            is_curve = str(isCurve).strip().lower() == "true"
            next_goal = None
            is_final = False
            try:
                if state.removed_grid_path_array_flag:
                    next_index = state.removed_grid_path_array_start_val[i] + 1
                    is_final = next_index >= state.removed_grid_path_array[i][1]
                    if not is_final:
                        next_row = read_specific_line(
                            state.removed_grid_filename[i], next_index
                        )
                        next_goal = (next_row[0][0], next_row[0][1])
                else:
                    next_index = state.grid_path_array[i] + 1
                    is_final = next_index >= int(num_lines[i])
                    if not is_final:
                        next_row = read_specific_line(
                            state.all_uav_csv_grid_array[i], next_index
                        )
                        next_goal = (next_row[0][0], next_row[0][1])
            except Exception as e:
                print("[split] next point read failed", i, e)
            reached_split_waypoint, split_goal_distance = uav_reached_waypoint(
                i,
                b,
                goal,
                sim_radius=5,
                next_goal=next_goal,
                is_curve=is_curve,
                is_final=is_final,
            )
            # If the bot has already arrived at `goal`, pacing it toward
            # that same point again pulls with ~zero magnitude and it goes
            # fully static -- and a static bot means a static pursuit
            # target (compute_lookahead_target is anchored on the bot's
            # own x/y/heading), which risks the real aircraft closing in
            # on a fixed point and orbiting it while a lead-cap hold keeps
            # the CSV index from advancing. Pacing toward next_goal instead
            # keeps the bot -- and therefore the pursuit target -- moving,
            # without touching grid_path_array[i] itself; that still only
            # advances once the lead cap below allows it.
            already_at_goal = abs(goal[0] - b.x) <= 5 and abs(goal[1] - b.y) <= 5
            pacing_target = next_goal if (already_at_goal and next_goal is not None) else goal
            dis, step_size = advance_bot_with_uav_pacing(
                i, b, pacing_target, label="split"
            )
            if reached_split_waypoint:
                if split_goal_distance is not None:
                    print(
                        f"[uav-flyby] bot {i}: switching split point at "
                        f"{split_goal_distance:.1f} m"
                    )
                if (
                    state.grid_path_array[i] >= int(num_lines[i])
                    and not state.removed_grid_path_array_flag
                ):
                    continue
                signed_lead = signed_uav_lead(i, b)
                uav_is_ahead = signed_lead is not None and signed_lead > 0
                if dis > config.UAV_MAX_VIRTUAL_LEAD_M and not uav_is_ahead:
                    # Real aircraft is too far BEHIND to commit to a new
                    # point yet -- hold the index here (the bot still
                    # tracks this same point; only advancing to the NEXT
                    # one is paused) so the lead can't keep growing
                    # unbounded the way it did with pacing alone. Never
                    # holds just because `dis` is large when the UAV is
                    # actually ahead -- that's not lagging.
                    if config.BOT_SYNC_DEBUG:
                        print(
                            f"[lead-cap] bot={i} holding at current split point -- "
                            f"dis={dis:.1f}m exceeds "
                            f"UAV_MAX_VIRTUAL_LEAD_M={config.UAV_MAX_VIRTUAL_LEAD_M:.0f}m"
                        )
                elif (
                    state.grid_path_array[i] >= int(num_lines[i])
                    and state.removed_grid_path_array_flag
                ):
                    state.removed_grid_path_array_start_val[i] += 1
                    print(
                        "removed_grid_path_array_start_val",
                        state.removed_grid_path_array_start_val,
                    )
                else:
                    state.grid_path_array[i] += 1
                    print("grid_path_array", state.grid_path_array)
            if state.master_flag:
                # Pursuit point: a fixed distance ahead of the bot along its
                # own heading, that the real UAV closes on -- never a point
                # that runs away from it, and never one that falls behind
                # it (see compute_lookahead_target's docstring above). Only
                # once the UAV has actually overtaken that anchor does the
                # target get pushed further out, by min_lead.
                lat_v, lon_v = (
                    state.vehicles[i].location.global_relative_frame.lat,
                    state.vehicles[i].location.global_relative_frame.lon,
                )
                rx, ry = locatePosition.geoToCart(
                    state.origin, config.END_DISTANCE, [lat_v, lon_v]
                )
                tx, ty = compute_lookahead_target(
                    b.x, b.y, b.theta, rx / 2, ry / 2, distance=720
                )
                # Collision avoidance: nudge the target away from every
                # OTHER real UAV's live GPS position within range. Computed
                # straight from telemetry (real_uav_avoidance_vector), not
                # from the simulated bots' own separation.
                avoid_x, avoid_y = real_uav_avoidance_vector(i)
                tx += avoid_x
                ty += avoid_y
                state.uav_lookahead_points[i] = (tx, ty)
                lat, lon = locatePosition.cartToGeo(
                    state.origin, config.END_DISTANCE, [tx * 2, ty * 2]
                )
                if state.same_alt_flag:
                    point1 = LocationGlobalRelative(lat, lon, state.same_height)
                else:
                    point1 = LocationGlobalRelative(
                        lat, lon, state.different_height[i]
                    )
                state.vehicles[i].simple_goto(point1)

        state.s.time_elapsed += 1
        if state.master_flag and gui is not None:
            gps_pts = live_gps_plot_points()
            gui.show_goals(current_goals)
            gui.show_planned_path(planned_paths_by_bot)
            gui.show_gps_positions(gps_pts)
            gui.show_lookahead(
                [state.uav_lookahead_points.get(k) for k in range(len(state.s.swarm))],
                gps_pts,
            )
            gui.update()
            print_sim_vs_real_latlon(selected_indexes, label="split")

        if state.index == b"stop":
            state.split_flag = False
            state.foreground_mission_indexes = set()
            if state.master_flag and gui is not None:
                gui.close()
            break
