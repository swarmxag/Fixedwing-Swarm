"""'home' command: fly the swarm back through a given return path, then
(home_flag1) close the final leg onto each bot's own recorded home_pos.
Not preemptable via check_for_new_command -- matches the original, which
never wired that mechanism into this block."""

import json
import time

import locatePosition
from dronekit import LocationGlobalRelative
from swarm_tasks.simulation import simulation as sim

from medur_swarm import config, state
from medur_swarm.uav.guidance import advance_bot_with_uav_pacing, pursuit_target_with_avoidance
from medur_swarm.uav.management import remove_vehicle


def _drive_home_leg(i, b, goal):
    """Pace the bot toward `goal` (same field composition as
    goal/search/split) and send the real UAV a pursuit point corrected for
    other real UAVs' separation -- but keep the home-specific fixed
    per-slot altitude (config.HOME_HEIGHT), not the same_alt_flag/
    different_height altitude every other command uses, since that's the
    altitude home has always returned at."""
    advance_bot_with_uav_pacing(i, b, goal, label="home")
    if state.master_flag and i < len(state.vehicles):
        target = pursuit_target_with_avoidance(i, b)
        position = target if target is not None else (b.x, b.y)
        current_position = (position[0] * 2, position[1] * 2)
        lat, lon = locatePosition.cartToGeo(state.origin, config.END_DISTANCE, current_position)
        point1 = LocationGlobalRelative(lat, lon, config.HOME_HEIGHT[i])
        state.vehicles[i].simple_goto(point1)


def run_home_command(data):
    if not (data.startswith(b"home") or state.home_flag):
        return
    decoded_index = data.decode(
        "utf-8"
    )  # Assuming utf-8 encoding, adjust if needed
    f = decoded_index[0:4]  # First coordinate pair
    return_array = decoded_index[5:]  # All other coordinates
    return_latlon = json.loads(return_array)
    return_xy = []
    for x in return_latlon:
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [x[0], x[1]])
        return_xy.append((x / 2, y / 2))
    print(return_xy, "return_xy")
    return_ind = 0
    if state.master_flag:
        state.uav_home_pos = []
        for vehicle in state.vehicles:
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            state.uav_home_pos.append((x / 2, y / 2))
        state.s = sim.Simulation(
            state.uav_home_pos, num_bots=len(state.pos_array), env_name=state.file_name
        )
        state.home_flag = True
    bot_array_home = [0] * state.num_bots
    all_bot_reach_flag_home = False
    state.index = "data"
    while 1:
        time.sleep(config.SLEEP_TIMES.get(state.num_bots))
        if state.home_flag1:
            state.home_flag = False
            break
        if state.vehicle_lost_flag:
            state.vehicle_lost_flag = True
            x = remove_vehicle()
            print(x)
        for i, b in enumerate(state.s.swarm):
            current_position = [b.x, b.y]
            goal = return_xy[return_ind]
            dx = abs(goal[0] - current_position[0])
            dy = abs(goal[1] - current_position[1])
            if dx <= 5 and dy <= 5:
                bot_array_home[i] = 1
                if any(element == 1 for element in bot_array_home):
                    if return_ind == len(return_xy) - 1:
                        all_bot_reach_flag_home = True
                        print(
                            "all_bot_reach_flag_home", all_bot_reach_flag_home
                        )
                        break
                    else:
                        return_ind += 1
                        print("return_ind", return_ind)
            if all_bot_reach_flag_home == True:
                state.home_flag1 = True
                state.home_flag = False
                break

            _drive_home_leg(i, b, goal)

        if state.index == b"stop":
            state.home_flag1 = True
            state.home_flag = False


def run_home_return_final_leg(data):
    if not state.home_flag1:
        return
    if state.master_flag:
        state.uav_home_pos = []
        for vehicle in state.vehicles:
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            state.uav_home_pos.append((x / 2, y / 2))
        state.s = sim.Simulation(
            state.uav_home_pos, num_bots=len(state.pos_array), env_name=state.file_name
        )
        state.home_flag1 = True
    bot_array_home = [0] * state.num_bots
    all_bot_reach_flag_home = False
    state.index = "data"
    while 1:
        time.sleep(config.SLEEP_TIMES.get(state.num_bots))
        if all_bot_reach_flag_home == True:
            state.home_flag1 = False
            state.home_flag = False
            print("END")
            break
        if state.vehicle_lost_flag:
            state.vehicle_lost_flag = True
            x = remove_vehicle()
            print(x)
        print("ggg", state.home_pos)
        for i, b in enumerate(state.s.swarm):
            current_position = [b.x, b.y]
            goal = state.home_pos[i]
            dx = abs(goal[0] - current_position[0])
            dy = abs(goal[1] - current_position[1])
            if dx <= 0.1 and dy <= 0.1:
                bot_array_home[i] = 1
                if all(element == 1 for element in bot_array_home):
                    all_bot_reach_flag_home = True
                    print("all_bot_reach_flag_home", all_bot_reach_flag_home)
                    break

            if all_bot_reach_flag_home == True:
                break

            _drive_home_leg(i, b, goal)

        if state.index == b"stop":
            state.home_flag1 = False
            state.home_flag = False
