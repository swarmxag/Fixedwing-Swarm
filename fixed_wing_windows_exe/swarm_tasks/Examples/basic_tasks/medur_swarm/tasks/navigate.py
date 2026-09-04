"""'grid_path_planning' (pre-computes a Bezier grid, keeping only whatever
side effects BezierCurve's own methods perform -- its result is otherwise
unused, same as the original) and 'navigate' (fly the whole swarm through
one shared Bezier grid in lockstep, in whichever `ind`-th point the
slowest bot hasn't reached yet)."""

import csv
import time

import locatePosition
from bezier_curve import BezierCurve
from swarm_tasks.simulation import simulation as sim
from swarm_tasks.simulation import visualizer as viz

from medur_swarm import config, state
from medur_swarm.uav.guidance import (
    _drive_vehicle_towards,
    advance_bot_with_uav_pacing,
    pursuit_target_with_avoidance,
)
from medur_swarm.uav.telemetry import live_gps_plot_points, print_sim_vs_real_latlon
from medur_swarm.communication.dispatch import check_for_new_command


def run_grid_path_planning_command(data):
    if not data.startswith(b"grid_path_planning"):
        return
    decoded_index = data.decode(
        "utf-8"
    )  # Assuming utf-8 encoding, adjust if needed
    f, center_lat, center_lon, num_uavs, grid_space, coverage_area = (
        decoded_index.split(",")
    )
    curve = BezierCurve(
        state.origin,
        float(center_lat),
        float(center_lon),
        int(num_uavs),
        int(grid_space),
        int(coverage_area),
    )
    val = curve.GridFormation()
    path = curve.generate_bezier_curve()


def run_navigate_command(data):
    if not (data.startswith(b"navigate") or state.start_flag):
        return
    print("data", data)
    decoded_index = data.decode(
        "utf-8"
    )  # Assuming utf-8 encoding, adjust if needed
    f, center_lat, center_lon, num_uavs, grid_space, coverage_area = (
        decoded_index.split(",")
    )
    curve = BezierCurve(
        state.origin,
        float(center_lat),
        float(center_lon),
        int(num_uavs),
        int(grid_space),
        int(coverage_area),
    )
    val = curve.GridFormation()
    path = curve.generate_bezier_curve()
    multiple_goals = path
    if state.master_flag:
        # time.sleep(0.1)
        state.start_flag = True
        state.uav_home_pos = []
        state.index = "data"
        for vehicle in state.vehicles:
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            state.uav_home_pos.append((x / 2, y / 2))
    state.s = sim.Simulation(
        state.uav_home_pos, num_bots=len(state.pos_array), env_name=state.file_name
    )
    gui = viz.Gui(state.s)

    state.index = "data"

    for b in state.s.swarm:
        state.search_flag = False
        all_bot_reach_flag = False
        bot_array = [0] * state.num_bots
        ind = 0
        my_seq = state.last_seq
        diverted_indexes = set()
        while 1:
            if not state.start_flag:
                state.start_flag = False
                break
            time.sleep(config.SLEEP_TIMES.get(state.num_bots))
            check_for_new_command(my_seq)
            bot_array = [0] * state.num_bots
            for i, b in enumerate(state.s.swarm):
                if i in state.active_goal_tasks:
                    diverted_indexes.add(i)
                if i in diverted_indexes:
                    continue
                current_position = [b.x, b.y]
                if state.skip_wp_flag:
                    with open(csv_path, "a") as csvfile:
                        print("next_wp", state.next_wp)
                        state.next_wp = int(state.next_wp) - 1
                        state.start_return_csv_flag = True
                        fieldnames = ["waypoint"]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerow({"waypoint": state.next_wp})
                        state.goal_path_csv_array.append(state.next_wp)
                        print("goal_path_csv_array", state.goal_path_csv_array)
                        state.goal_path_csv_array_flag = True
                    for x, c in enumerate(state.s.swarm):
                        state.goal_table[x] = state.next_wp
                    print("goal_table", state.goal_table)
                    state.skip_wp_flag = False
                    ind = state.goal_table[i]

                goal = multiple_goals[ind]
                advance_bot_with_uav_pacing(i, b, goal, label="navigate")
                dx = abs(goal[0] - current_position[0])
                dy = abs(goal[1] - current_position[1])
                if dx <= 1 and dy <= 1:
                    bot_array[i] = 1
                if any(element == 1 for element in bot_array):
                    if ind == len(multiple_goals) - 1:
                        print("all_bot_reach_flag", all_bot_reach_flag)
                        all_bot_reach_flag = True
                        break
                    else:
                        ind += 1
                        print("ind", ind, multiple_goals[ind])

                if all_bot_reach_flag == True:
                    with open(csv_path, "a") as csvfile:
                        state.start_return_csv_flag = True
                        fieldnames = ["waypoint"]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerow(
                            {"waypoint": multiple_goals.index(goal)}
                        )
                        print(
                            "multiple_goals.index(goal)",
                            multiple_goals.index(goal),
                        )
                        state.goal_path_csv_array.append(multiple_goals.index(goal))
                        print("goal_path_csv_array", state.goal_path_csv_array)
                        state.goal_path_csv_array_flag = True
                    all_bot_reach_flag = False
                    bot_array = [0] * state.num_bots
                    if ind == len(multiple_goals) - 1:
                        print("Break")
                        state.start_flag = False
                        break
                # Pursuit point ahead of the bot's own heading, corrected
                # for real UAV-to-UAV separation -- same guidance
                # goal/search/split use, instead of the bot's raw position.
                _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))

            if gui is not None:
                gui.show_goals([multiple_goals[ind]] * len(state.s.swarm))
                gui.show_planned_path([multiple_goals] * len(state.s.swarm))
                gui.show_gps_positions(live_gps_plot_points())
                gui.update()
                print_sim_vs_real_latlon(
                    [
                        i
                        for i in range(len(state.s.swarm))
                        if i not in diverted_indexes
                    ],
                    label="navigate",
                )

            if state.index == b"stop":
                print(
                    "start_flag",
                    state.start_flag,
                    "circle_formation_flag",
                    state.circle_formation_flag,
                )
                state.start_flag = False
                state.circle_formation_flag = False
                if gui is not None:
                    gui.close()
                break
