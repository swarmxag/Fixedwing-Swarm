"""Legacy formation flows that predate the background task runner:
'guided_circle' (a standalone loiter-formation command -- distinct from
the automatic post-goal loiter tasks/runner.py starts once a goal task
completes), 'same' altitude, and 'loiter_point'/circle_formation. None of
these are preemptable via check_for_new_command except guided_circle,
matching the original exactly."""

import time

import locatePosition
from dronekit import LocationGlobalRelative
import swarm_tasks.controllers.potential_field as potf
from swarm_tasks.modules.dispersion import disp_field
from swarm_tasks.simulation import simulation as sim
from swarm_tasks.tasks import area_coverage as cvg

from medur_swarm import config, state
from medur_swarm.utils import generate_points
from medur_swarm.uav.guidance import (
    _drive_vehicle_towards,
    advance_bot_with_uav_pacing,
    pursuit_target_with_avoidance,
)
from medur_swarm.communication.dispatch import check_for_new_command


def run_guided_circle_command(data):
    """'guided_circle' standalone formation command. Reads
    state.goal_latlon/guided_circle_radius/guided_circle_direction, which
    are only ever set as a side effect of a 'goal' command (see
    tasks/goal.py) -- exactly the same implicit reliance on whatever the
    last 'goal' dispatch parsed that the original single-file script had
    via its shared flat scope. Sending 'guided_circle' with no prior
    'goal' in the same process raises, same as the original (there
    `goal_latlon` etc. would simply be undefined names)."""
    if not (state.guided_circle_flag or data == b"guided_circle"):
        return
    goal_latlon = state.goal_latlon
    guided_circle_radius = state.guided_circle_radius
    guided_circle_direction = state.guided_circle_direction
    multiple_goals_latlon = generate_points(
        float(goal_latlon[-1][0]),
        float(goal_latlon[-1][1]),
        8,
        int(guided_circle_radius),
        int(guided_circle_direction),
    )
    print("multiple_goals_latlon", multiple_goals_latlon)
    multiple_goals = []
    for m in multiple_goals_latlon:
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, m)
        multiple_goals.append((x / 2, y / 2))
    print("multiple_goals", multiple_goals)
    for b in state.s.swarm:
        ind = [0] * state.num_bots
        my_seq = state.last_seq
        while 1:
            if state.guided_circle_formation_flag:
                state.guided_circle_formation_flag = False
                state.guided_circle_flag = False
                break
            time.sleep(config.SLEEP_TIMES.get(state.num_bots))
            check_for_new_command(my_seq)
            for i, b in enumerate(state.s.swarm):
                current_position = [b.x, b.y]
                goal = multiple_goals[ind[i]]
                advance_bot_with_uav_pacing(
                    i, b, goal, label="guided_circle_formation"
                )
                dx = abs(goal[0] - current_position[0])
                dy = abs(goal[1] - current_position[1])
                state.circle_formation_table[i] = 1
                # This is an intentional circular formation, not a finite
                # fly-by route. Advance its virtual circle points locally.
                if dx <= 5 and dy <= 5:
                    ind[i] += 1
                    print("inddddddd", ind)
                    if ind[i] == len(multiple_goals):
                        ind[i] = 0
                # Pursuit point ahead of the bot's own heading, corrected
                # for real UAV-to-UAV separation -- same guidance
                # goal/search/split use, instead of the bot's raw position.
                _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))

            if state.index == b"stop":
                state.guided_circle_formation_flag = True
                break


def run_same_altitude_command(data):
    """'same' command: level every bot to one shared altitude. Preserved
    verbatim including a pre-existing latent bug -- `alt`/`alt_count`
    are read here but never assigned anywhere reachable beforehand, so
    the completion check raises NameError the first time this runs (with
    master_flag True); that exception propagates out to main.py's own
    per-iteration exception handler exactly as it did in the original
    single-file script."""
    if not data.startswith(b"same"):
        return
    print("msg", data)
    decoded_index = data.decode(
        "utf-8"
    )  # Assuming utf-8 encoding, adjust if needed
    data1, height = decoded_index.split(",")
    print(data1, height)
    state.same_alt_flag = True
    state.same_height = int(height)
    while True:
        for i, b in enumerate(state.s.swarm):
            cmd = potf.velocity(
                b.get_position(),
                b.sim,
                weights=potf.field_weights,
                order=2,
                max_dist=5,
            )
            cmd.exec(b)
            if state.master_flag:
                value = [b.x * 2, b.y * 2]
                lat, lon = locatePosition.cartToGeo(state.origin, config.END_DISTANCE, value)
                if state.same_alt_flag:
                    point1 = LocationGlobalRelative(lat, lon, state.same_height)
                else:
                    point1 = LocationGlobalRelative(
                        lat, lon, state.different_height[i]
                    )
                state.vehicles[i].simple_goto(point1)

                if state.same_height - 1.5 <= alt[i] <= state.same_height + 1.5:
                    alt_count[i] = 1
                    if all(count == 1 for count in alt_count):
                        state.index = "data"
                        data = b"data"
                        state.same_alt_flag = True
                        break

        if state.index == b"stop":
            state.index = "data"
            data = b"index"
            break


def run_loiter_point_command(data):
    """'loiter_point'/circle_formation command. Not preemptable via
    check_for_new_command -- matches the original exactly (that
    mechanism was never wired into this block)."""
    if not (data.startswith(b"loiter_point") or state.circle_formation_flag):
        return
    decoded_index = data.decode(
        "utf-8"
    )  # Assuming utf-8 encoding, adjust if needed
    f, base_lat, base_lon, radius, circle_direction = decoded_index.split(",")
    print("f,loiter_radius ", f, base_lat, base_lon, radius, circle_direction)

    if state.master_flag:
        state.uav_home_pos = []
        state.index = "data"
        for vehicle in state.vehicles:
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            state.uav_home_pos.append((x / 2, y / 2))
        print("uav_home_pos", state.uav_home_pos)
        state.s = sim.Simulation(
            state.uav_home_pos, num_bots=len(state.pos_array), env_name=state.file_name
        )

    state.index = "data"

    # Generate 8 points in a circular formation with the given radius
    # around the given point.
    multiple_goals_latlon = generate_points(
        float(base_lat), float(base_lon), 8, int(radius), int(circle_direction)
    )
    print("multiple_goals_latlon", multiple_goals_latlon)
    multiple_goals = []
    for m in multiple_goals_latlon:
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, m)
        multiple_goals.append((x / 2, y / 2))
    print("multiple_goals", multiple_goals)
    for b in state.s.swarm:
        print("circle_formation_table", state.circle_formation_table)
        ind = [0] * state.num_bots
        step = 1
        while 1:
            if state.start_flag:
                break
            time.sleep(config.SLEEP_TIMES.get(state.num_bots))
            for i, b in enumerate(state.s.swarm):
                current_position = [b.x, b.y]
                goal = multiple_goals[ind[i]]
                if state.circle_formation_table[i] == 0:
                    lat = state.vehicles[i].location.global_relative_frame.lat
                    lon = state.vehicles[i].location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(
                        state.origin, config.END_DISTANCE, [lat, lon]
                    )
                    plane_points = [x / 2, y / 2]
                    advance_bot_with_uav_pacing(
                        i, b, goal, label="loiter_point"
                    )
                    dx = abs(goal[0] - current_position[0])
                    dy = abs(goal[1] - current_position[1])
                    if state.master_flag:
                        current_position = [b.x * 2, b.y * 2]
                        lat, lon = locatePosition.cartToGeo(
                            state.origin, config.END_DISTANCE, current_position
                        )
                        if step <= len(state.vehicles):
                            step += 1
                            print("!!!!!!!!!!")
                            if state.same_alt_flag:
                                point1 = LocationGlobalRelative(
                                    float(base_lat),
                                    float(base_lon),
                                    state.same_height,
                                )
                            else:
                                point1 = LocationGlobalRelative(
                                    float(base_lat),
                                    float(base_lon),
                                    state.different_height[i],
                                )
                            state.vehicles[i].simple_goto(point1)
                        if step == 100:
                            if state.same_alt_flag:
                                point1 = LocationGlobalRelative(
                                    float(base_lat),
                                    float(base_lon),
                                    state.same_height,
                                )
                            else:
                                point1 = LocationGlobalRelative(
                                    float(base_lat),
                                    float(base_lon),
                                    state.different_height[i],
                                )
                            state.vehicles[i].simple_goto(point1)
                        if step != 100:
                            current_altitude = state.vehicles[
                                i
                            ].location.global_relative_frame.alt
                            distance = locatePosition.distance_bearing(
                                state.vehicles[i].location.global_relative_frame.lat,
                                state.vehicles[i].location.global_relative_frame.lon,
                                float(base_lat),
                                float(base_lon),
                            )
                            if (
                                state.different_height[i] - 5
                            ) <= current_altitude <= (
                                state.different_height[i] + 5
                            ) and distance < 150:
                                state.uav_home_pos = []
                                step = 100
                                for vehicle in state.vehicles:
                                    lat = (
                                        vehicle.location.global_relative_frame.lat
                                    )
                                    lon = (
                                        vehicle.location.global_relative_frame.lon
                                    )
                                    x, y = locatePosition.geoToCart(
                                        state.origin, config.END_DISTANCE, [lat, lon]
                                    )
                                    state.uav_home_pos.append((x / 2, y / 2))
                                state.s = sim.Simulation(
                                    state.uav_home_pos,
                                    num_bots=len(state.pos_array),
                                    env_name=state.file_name,
                                )
                    if i < len(state.robots):
                        state.robots[i] = (x / 2, y / 2)
                    msg = ",".join(
                        [f"{robot[0]},{robot[1]}" for robot in state.robots]
                    )
                    if dx < 50 and dy < 50:
                        cmd = cvg.goal_area_cvg(i, b, goal)
                        cmd += disp_field(b, neighbourhood_radius=100)
                        cmd.exec(b)
                        dx = abs(goal[0] - current_position[0])
                        dy = abs(goal[1] - current_position[1])
                        state.circle_formation_table[i] = 1
                        if dx <= 50 and dy <= 50:
                            ind[i] += 1
                            if ind[i] == len(multiple_goals):
                                ind[i] = 0

                        # Pursuit point ahead of the bot's own heading,
                        # corrected for real UAV-to-UAV separation -- same
                        # guidance goal/search/split use, instead of the
                        # bot's raw position.
                        _drive_vehicle_towards(
                            i, b, pursuit_target_with_avoidance(i, b)
                        )

                    else:
                        continue

                if state.circle_formation_table[i] == 1:
                    cmd = cvg.goal_area_cvg(i, b, goal)
                    cmd += disp_field(b, neighbourhood_radius=100)
                    cmd.exec(b)
                    dx = abs(goal[0] - current_position[0])
                    dy = abs(goal[1] - current_position[1])
                    state.circle_formation_table[i] = 1
                    if dx <= 10 and dy <= 10:
                        ind[i] += 1
                        print("index", ind)
                        if ind[i] == len(multiple_goals):
                            ind[i] = 0

                    # Pursuit point ahead of the bot's own heading,
                    # corrected for real UAV-to-UAV separation -- same
                    # guidance goal/search/split use, instead of the
                    # bot's raw position.
                    _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))

                else:
                    continue

            if state.index == b"stop":
                state.start_flag = False
                state.circle_formation_flag = False
                break
