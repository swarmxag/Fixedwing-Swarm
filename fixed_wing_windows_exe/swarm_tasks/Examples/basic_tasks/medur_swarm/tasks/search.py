"""'search' command: BezierCurveMultiple grid-search coverage, flown by
whichever UAV subset the operator selected (or the whole connected fleet)."""

import csv
import math
import os
import time

import locatePosition
from dronekit import LocationGlobalRelative
from bezier_curve_multiple import BezierCurveMultiple
from mission_paths import uav_path_csv
from swarm_tasks.simulation import simulation as sim
from swarm_tasks.simulation import visualizer as viz

import swarm_tasks

from medur_swarm import config, state
from medur_swarm.utils import (
    allocate_drones,
    parse_selected_uav_ids,
    read_origin,
    read_specific_line,
    selected_swarm_indexes,
)
from medur_swarm.uav.guidance import (
    advance_bot_with_uav_pacing,
    real_uav_avoidance_vector,
    signed_uav_lead,
    uav_reached_waypoint,
)
from medur_swarm.uav.telemetry import live_gps_plot_points
from medur_swarm.uav.management import remove_vehicle
from medur_swarm.tasks.runner import assign_mission_tasks, synchronize_mission_topology
from medur_swarm.communication.dispatch import check_for_new_command


def lookahead_point(x, y, theta, distance=10):
    lx = x + distance * math.cos(theta)
    ly = y + distance * math.sin(theta)
    return (lx, ly)


def compute_lookahead_target(x, y, theta, rx, ry, distance, min_lead=None):
    """
    tx,ty = the point handed to the real vehicle: a fixed point on the
    bot's heading line, distance ahead of the bot, that the vehicle
    closes on -- never a point that runs away from it, and never one
    that falls behind it.

    x,y,theta -- bot pose (sim frame)
    rx,ry     -- vehicle's live position (sim frame, same units as x,y)
    distance  -- lookahead distance ahead of the BOT, sim units
    min_lead  -- once the vehicle has passed the bot-anchored target,
                 how far ahead of the vehicle to keep it instead.
                 Defaults to half distance.

    along is the vehicle's signed progress along the bot's heading:
    >0 means it has already passed the bot going that way. Anchoring
    the target to that progress (target_along = along + distance) is
    what misbehaves once the vehicle gets ahead -- the target then
    advances by exactly as much as the vehicle does, so the vehicle
    chases a carrot it can never reach and keeps building lead on the
    bot. Behind, the same formula is self-stabilising (the gap grows,
    giving a far target and a gentle straight-line pursuit), which is
    why only the "ahead" case shows the problem.

    So along is used here purely as a floor, not as the anchor: the
    target normally sits at a FIXED distance ahead of the bot, so a
    vehicle that is ahead actually closes on it and bleeds off its
    lead. Only when the vehicle has genuinely overflown that point
    does the target get pushed out, and then just by min_lead -- far
    enough to avoid commanding a reversal a fixed-wing can't fly.
    """
    if min_lead is None:
        min_lead = distance * 0.5

    # Signed distance of vehicle along the bot's current heading
    along = (rx - x) * math.cos(theta) + (ry - y) * math.sin(theta)

    target_along = max(distance, along + min_lead)

    return lookahead_point(x, y, theta, target_along)


def return_distance(loiter_radius):
    """Calculates the return distance based on the loiter radius."""
    return (loiter_radius / 2) + 100


def start_search_mission(decoded_index):
    """Parses a 'search,...' command and registers it as a background
    mission task for whichever UAV subset it targets, without touching
    the foreground dispatch loop. Only used for the concurrent-intercept
    path (search arriving while something else is already running) --
    a fresh top-level search dispatch still uses its own foreground loop,
    unchanged."""
    msg_parts = decoded_index.split(",", 6)
    selected_uav_raw = msg_parts[6] if len(msg_parts) > 6 else None
    f, center_lat, center_lon, num_uavs, grid_space, coverage_area = msg_parts[:6]
    selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
    if not selected_uav_ids:
        return False
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    effective_num_uavs = max(1, len(selected_indexes))
    curve = BezierCurveMultiple(
        state.origin,
        float(center_lat),
        float(center_lon),
        effective_num_uavs,
        int(grid_space),
        int(coverage_area),
        uav_ids=selected_uav_ids,
    )
    curve.GridFormation()
    curve.generate_bezier_curve()
    csv_paths_by_index = {}
    for path_slot, bot_index in enumerate(selected_indexes):
        csv_paths_by_index[bot_index] = uav_path_csv(selected_uav_ids[path_slot])
    assign_mission_tasks(csv_paths_by_index, "search")
    print(
        "[concurrent search] accepted during running mission",
        selected_uav_ids,
        selected_indexes,
    )
    return True


def handle_concurrent_search_command(command_data):
    if not command_data.startswith(b"search"):
        return False
    try:
        return start_search_mission(command_data.decode("utf-8"))
    except Exception as e:
        print("[concurrent search] failed", e)
        return False


def run_search_command(data):
    """The foreground 'search' dispatch-loop handler. Never signals an
    outer-loop abort -- its own inner while loop only exits via an
    internal `break` (on stop), then falls through exactly like the
    original inline block did."""
    if not (data.startswith(b"search") or state.search_flag):
        return
    print("data", data)
    decoded_index = data.decode("utf-8")  # Assuming utf-8 encoding, adjust if needed
    print("decoded_index", decoded_index)
    msg_parts = decoded_index.split(",", 6)
    selected_uav_raw = msg_parts[6] if len(msg_parts) > 6 else None
    f, center_lat, center_lon, num_uavs, grid_space, coverage_area = msg_parts[:6]
    selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    selected_index_set = set(selected_indexes)
    # A bot can still have an active_goal_tasks entry from an earlier
    # goal command (still en route, or already looping forever as a
    # guided_circle) -- without clearing it here, this fresh search
    # would see it below and mark the bot "diverted" before it's
    # ever given a single search waypoint, silently ceding control
    # to the stale task instead of actually starting the search.
    with state.active_goal_tasks_lock:
        for i in selected_indexes:
            state.active_goal_tasks.pop(i, None)
    effective_num_uavs = max(
        1, len(selected_indexes) if selected_uav_ids else int(num_uavs)
    )
    print(
        "[search] selected_uav_ids",
        selected_uav_ids,
        "selected_indexes",
        selected_indexes,
    )
    # Whole-swarm search (no explicit subset) targets every connected
    # UAV in pos_array order -- same order effective_num_uavs falls
    # back to num_uavs (== len(pos_array)) for, so the two line up.
    ids_for_curve = (
        selected_uav_ids if selected_uav_ids else state.pos_array[:effective_num_uavs]
    )
    curve = BezierCurveMultiple(
        state.origin,
        float(center_lat),
        float(center_lon),
        effective_num_uavs,
        int(grid_space),
        int(coverage_area),
        uav_ids=ids_for_curve,
    )
    val = curve.GridFormation()
    path = curve.generate_bezier_curve()
    state.search_step = 1
    gui = None
    if state.master_flag:
        state.index = "data"
        state.uav_home_pos = []
        for vehicle in state.vehicles:
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(
                state.origin, config.END_DISTANCE, [lat, lon]
            )
            state.uav_home_pos.append((x / 2, y / 2))
        swarm_tasks.utils.robot.DEFAULT_SIZE = 0.4
        # Search-only bot speed bump (+0.5 over the global default set in
        # main.py) -- not applied to goal/split, only here.
        swarm_tasks.utils.robot.MAX_SPEED = 3.0
        state.s = sim.Simulation(
            state.uav_home_pos, num_bots=state.num_bots, env_name=state.file_name
        )
        gui = viz.Gui(state.s)

    print("Search Started")
    state.search_flag_val = 0
    f = ""
    num_lines = [0] * len(state.pos_array)
    goal_position = []
    cwd = os.getcwd()
    print("search_flag_val", state.search_flag_val)
    state.grid_path_array = [0] * len(state.pos_array)
    # A previous split/search may have left this module-level list at
    # a different fleet size. Start each mission in the current
    # topology, rather than waiting for the first removal to expose it.
    state.all_uav_csv_grid_array = [0] * len(state.pos_array)
    if state.search_flag_val == 0:
        state.search_flag_val += 1
        csv_file_paths = []
        for i in range(1, effective_num_uavs + 1):
            csv_file_paths.append(uav_path_csv(ids_for_curve[i - 1]))
        print("csv_file_paths", csv_file_paths)
    state.removed_grid_path_array_index = 0
    print("grid_path_array", state.grid_path_array)
    current_goals = [None] * len(state.pos_array)
    planned_paths_by_bot = [None] * len(state.pos_array)
    my_seq = state.last_seq
    diverted_indexes = set()
    # Tell apply_different_heights this loop owns these bots' movement, so a
    # concurrent 'different' only re-targets their altitude (picked up by the
    # simple_goto below next tick) instead of spawning an altitude task that
    # would divert them out of the search for good.
    state.foreground_mission_indexes = set(selected_indexes)
    state.origin = read_origin(config.RECTANGLES_PATH)
    while 1:
        if state.num_bots == 10:
            time.sleep(0.1)
        elif state.num_bots == 9:
            time.sleep(0.1)
        elif state.num_bots == 8:
            time.sleep(0.11)
        elif state.num_bots == 7:
            time.sleep(0.11)
        elif state.num_bots == 6:
            time.sleep(0.12)  # verified
        elif state.num_bots == 5:
            time.sleep(0.12)  # verified
        elif state.num_bots == 4:
            time.sleep(0.123)
        elif state.num_bots == 3:
            time.sleep(0.125)
        elif state.num_bots == 2:
            time.sleep(0.13)
        elif state.num_bots == 1:
            time.sleep(0.13)
        check_for_new_command(my_seq)
        if state.vehicle_lost_flag:
            state.vehicle_lost_flag = True
            x = remove_vehicle()
            print(x)
        if state.remove_bot_flag:
            # Preserve progress for redistribution before compacting
            # the foreground mission arrays below.
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
                        "[search] skipped stale path assignment",
                        path_slot,
                        bot_index,
                    )
                    continue
                state.all_uav_csv_grid_array[bot_index] = csv_file_paths[path_slot]
                # Read once here (not every tick), per bot -- both the
                # line count used for THIS bot's own grid_path_array
                # bounds check below, and the whole planned route for
                # the show_planned_path() overlay. Per-bot matters: a
                # concurrent redirect (search re-targeting a UAV
                # subset while this mission is still running, see
                # start_search_mission()) overwrites just that
                # subset's csv files with a differently-sized grid --
                # a single num_lines shared across every bot (read
                # from whichever one file) would silently go wrong
                # for every OTHER, unrelated bot still reading its
                # own file, causing an out-of-range
                # read_specific_line() the moment that bot's
                # grid_path_array outpaces the now-wrong shared bound.
                try:
                    with open(state.all_uav_csv_grid_array[bot_index], "rt") as f:
                        rows = list(csv.reader(f))
                    num_lines[bot_index] = len(rows)
                    planned_paths_by_bot[bot_index] = [
                        (float(row[0]), float(row[1])) for row in rows
                    ]
                except Exception as e:
                    print("[planned-path] failed to read for bot", bot_index, e)
            print(
                "all_uav_csv_grid_array",
                state.all_uav_csv_grid_array,
                "num_lines",
                num_lines,
            )
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
                    add_points = math.ceil(remaining_points_list[x] / allocation[x])
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
                        state.removed_grid_filename[
                            state.removed_grid_path_array_index
                        ] = state.removed_uav_grid[x]
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
                            state.removed_grid_filename[i] = (
                                state.uncovered_area_filename[u]
                            )
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
            # print(f"CSV goal for bot {i}: {goal}, bot pos: {b.x:.1f}, {b.y:.1f}, ratio: {goal[0]/b.x:.2f}")
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
                print("[search] next point read failed", i, e)
            # If the bot has already arrived at `goal`, pacing it toward
            # that same point again pulls with ~zero magnitude and it goes
            # fully static -- and a static bot means a static pursuit
            # target (compute_lookahead_target is anchored on the bot's
            # own x/y/heading), which risks the real aircraft closing in
            # on a fixed point and orbiting it while a lead-cap hold keeps
            # the CSV index from advancing (see the [lead-cap] flight log
            # that surfaced this). Pacing toward next_goal instead keeps
            # the bot -- and therefore the pursuit target -- moving,
            # without touching grid_path_array[i] itself; that still only
            # advances once uav_reached_waypoint/the lead cap below allow
            # it.
            already_at_goal = abs(goal[0] - b.x) <= 15 and abs(goal[1] - b.y) <= 15
            pacing_target = (
                next_goal if (already_at_goal and next_goal is not None) else goal
            )
            dis, step_size = advance_bot_with_uav_pacing(
                i, b, pacing_target, label="search"
            )
            current_position = [b.x, b.y]
            dx = abs(goal[0] - current_position[0])
            dy = abs(goal[1] - current_position[1])
            reached_search_waypoint, uav_goal_distance = uav_reached_waypoint(
                i,
                b,
                goal,
                sim_radius=15,
                next_goal=next_goal,
                is_curve=is_curve,
                is_final=is_final,
            )
            if reached_search_waypoint:
                if config.BOT_SYNC_DEBUG:
                    print(
                        f"[waypoint-advance] label=search bot={i} "
                        f"index={state.grid_path_array[i]}->{state.grid_path_array[i] + 1} "
                        f"bot=({b.x:.2f},{b.y:.2f}) goal=({goal[0]:.2f},{goal[1]:.2f})"
                    )
                if uav_goal_distance is not None:
                    print(
                        f"[uav-flyby] bot {i}: switching search point at "
                        f"{uav_goal_distance:.1f} m"
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
                    # actually ahead -- that's not lagging, and holding
                    # for it would only stall the mission's own progress
                    # bookkeeping while the aircraft has already moved on.
                    if config.BOT_SYNC_DEBUG:
                        print(
                            f"[lead-cap] bot={i} holding at current search point -- "
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
                # OTHER real UAV's live GPS position within range. This is
                # computed straight from telemetry (real_uav_avoidance_vector),
                # not from the simulated bots' own separation, so it stays
                # meaningful even once each aircraft's target is being paced
                # individually and the bots and their real aircraft are no
                # longer necessarily close together.
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
                    point1 = LocationGlobalRelative(lat, lon, state.different_height[i])
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

        if state.index == b"stop":
            state.search_flag = False
            state.foreground_mission_indexes = set()
            if state.master_flag and gui is not None:
                gui.close()
            break
