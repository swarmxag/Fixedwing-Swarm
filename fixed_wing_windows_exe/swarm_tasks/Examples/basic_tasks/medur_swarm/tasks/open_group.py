"""'group_split' command ("Open Group"): assign an individual per-bot goal
position to a set of specific UAV IDs, blocking the foreground dispatch
loop until every assigned bot arrives (or a stop is requested). Legacy
path, same character as specific_bot_goal.py -- not preemptable and not
routed through the background task runner."""

import time

import locatePosition
from swarm_tasks.simulation import simulation as sim

from medur_swarm import config, state
from medur_swarm.uav.guidance import (
    _drive_vehicle_towards,
    advance_bot_with_uav_pacing,
    pursuit_target_with_avoidance,
)


def run_group_split_command(data):
    """Never signals an outer-loop abort -- matches the original, whose
    try/except swallows any failure and falls through with no continue."""
    if not data.startswith(b"group_split"):
        return
    state.index = "data"
    try:
        decoded_index = data.decode(
            "utf-8"
        )  # Assuming utf-8 encoding, adjust if needed
        msg_parts = decoded_index.split(",")
        goal_lat = float(msg_parts[-2])
        goal_lon = float(msg_parts[-1])
        remaining_values = msg_parts[1:-2]
        goal_x, goal_y = locatePosition.geoToCart(
            state.origin, config.END_DISTANCE, [float(goal_lat), float(goal_lon)]
        )
        goal_position = (goal_x / 2, goal_y / 2)
        for val in remaining_values:
            try:
                bot_index = int(val)
                for l in range(state.num_bots):
                    if bot_index == state.pos_array[l]:
                        state.group_split_goal_pos[l] = goal_position
                        state.group_split_flag_array[l] = True
                        print(f"Updated bot {l} with goal at {goal_position}")
                        break  # Break out of the inner loop once the correct bot is found
            except ValueError:
                print(f"Invalid value in remaining_values: {val}, skipping.")
        print(
            "group_split_flag_array",
            state.group_split_flag_array,
            state.group_split_goal_pos,
        )
        if state.master_flag:
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
        while 1:
            time.sleep(0.1)
            if state.group_split_flag:
                state.group_split_flag = False
                break
            for i, b in enumerate(state.s.swarm):
                current_position = [b.x, b.y]
                if state.group_split_flag_array[i]:
                    dx = abs(state.group_split_goal_pos[i][0] - current_position[0])
                    dy = abs(state.group_split_goal_pos[i][1] - current_position[1])
                    if dx <= 10 and dy <= 10:
                        state.group_split_flag_array[i] = False
                        print("group_split_flag_array", state.group_split_flag_array)
                    if all(flag == False for flag in state.group_split_flag_array):
                        state.group_split_flag = True
                        break
                    else:
                        current_position = (b.x, b.y)
                        if state.group_split_flag_array[i]:
                            b.set_goal(
                                state.group_split_goal_pos[i][0],
                                state.group_split_goal_pos[i][1],
                            )
                            advance_bot_with_uav_pacing(
                                i, b, state.group_split_goal_pos[i], label="group_split"
                            )
                    # Pursuit point ahead of the bot's own heading, corrected
                    # for real UAV-to-UAV separation -- same guidance
                    # goal/search/split use, instead of the bot's raw position.
                    _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))

            if state.index == b"stop":
                state.group_split_flag = False
                break
    except Exception as e:
        print("exceptiiiooonnn", e)
        pass
