"""'specific_bot_goal' command: send a single named UAV to one lat/lon
goal, blocking the foreground dispatch loop until it arrives (or a stop
is requested). Legacy path -- unlike goal.py, this one is not preemptable
via check_for_new_command and does not run through the background task
runner."""

import time

import locatePosition

from medur_swarm import config, state
from medur_swarm.uav.guidance import (
    _drive_vehicle_towards,
    advance_bot_with_uav_pacing,
    pursuit_target_with_avoidance,
)


def run_specific_bot_goal_command(data):
    """Never signals an outer-loop abort -- matches the original, whose
    try/except swallows any failure and falls through with no continue."""
    if not data.startswith(b"specific_bot_goal"):
        return
    state.index = "data"
    goal_pos = [0] * state.num_bots
    specific_bot_goal_flag_array = [False] * state.num_bots
    try:
        decoded_index = data.decode(
            "utf-8"
        )  # Assuming utf-8 encoding, adjust if needed
        f, uav, goal_lat, goal_lon = decoded_index.split(",")
        goal_x, goal_y = locatePosition.geoToCart(
            state.origin, config.END_DISTANCE, [float(goal_lat), float(goal_lon)]
        )
        goal_position = (goal_x / 2, goal_y / 2)
        for l in range(0, state.num_bots):
            if int(uav) == state.pos_array[l]:
                uav = l
                print("uav,l", uav, l)
                break

        state.goal_bot_num = int(uav)
        print("goal_bot_num", state.goal_bot_num)
        goal_pos[state.goal_bot_num] = goal_position
        specific_bot_goal_flag_array[state.goal_bot_num] = True
        print("specific_bot_goal_flag_array", specific_bot_goal_flag_array)
        while 1:
            time.sleep(0.1)
            if state.specific_bot_goal_flag:
                state.specific_bot_goal_flag = False
                break

            for i, b in enumerate(state.s.swarm):
                current_position = [b.x, b.y]
                if specific_bot_goal_flag_array[i]:
                    dx = abs(goal_pos[i][0] - current_position[0])
                    dy = abs(goal_pos[i][1] - current_position[1])
                    if dx <= 10 and dy <= 10:
                        specific_bot_goal_flag_array[i] = False
                        print(
                            "specific_bot_goal_flag_array",
                            specific_bot_goal_flag_array,
                        )
                    if all(
                        flag == False for flag in specific_bot_goal_flag_array
                    ):
                        state.specific_bot_goal_flag = True
                        break
                    else:
                        current_position = (b.x, b.y)
                        if specific_bot_goal_flag_array[i]:
                            b.set_goal(goal_pos[i][0], goal_pos[i][1])
                            advance_bot_with_uav_pacing(
                                i, b, goal_pos[i], label="specific_bot_goal"
                            )
                    # Pursuit point ahead of the bot's own heading, corrected
                    # for real UAV-to-UAV separation -- same guidance
                    # goal/search/split use, instead of the bot's raw position.
                    _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))

            if state.index == b"stop":
                state.specific_bot_goal_flag = False
                break
    except Exception as e:
        print("exceptiiiooonnn", e)
        pass
