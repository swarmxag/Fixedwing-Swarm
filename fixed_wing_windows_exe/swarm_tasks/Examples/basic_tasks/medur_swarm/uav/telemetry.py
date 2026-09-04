"""Keeping the simulated swarm's (x, y) positions honest against each
aircraft's live GPS fix, and reporting the sim-vs-real mismatch."""

import time

import locatePosition

from medur_swarm import config, state


def _resync_bot_position(i, force=False):
    """Nudge s.swarm[i].x/y (and robots[i]) toward vehicle i's live GPS.

    Runs at most once every GPS_RESYNC_INTERVAL seconds per bot (unless
    force=True) so real telemetry only ever *corrects* the swarm simulation
    periodically -- the potential-field motion (Bot.step()/move(), driven
    every fast tick by _goal_task_runner) is what actually moves the bots
    according to swarm logic in between. Resyncing on every tick instead of
    periodically would overwrite that motion before it ever accumulates,
    which defeats the swarm logic entirely.

    Only ever call this for an index from the thread that currently owns
    that bot's position (either _goal_task_runner, for indices it is
    actively driving via active_goal_tasks, or the main dispatch loop, for
    everything else). Bot.step()/move() do an unsynchronized read-then-write
    of self.x/self.y, so writing to the same index from two threads at once
    races it -- whichever write lands last silently wins, which either
    discards the GPS correction or discards an in-flight simulated step.
    """
    if (
        state.origin is None
        or i >= len(state.vehicles)
        or i >= len(state.s.swarm)
        or i >= len(state.robots)
    ):
        return
    now = time.time()
    if not force and (now - state.last_gps_resync.get(i, 0)) < config.GPS_RESYNC_INTERVAL:
        return
    try:
        lat = state.vehicles[i].location.global_relative_frame.lat
        lon = state.vehicles[i].location.global_relative_frame.lon
        if lat is None or lon is None:
            return
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
        state.s.swarm[i].x = x / 2
        state.s.swarm[i].y = y / 2
        state.robots[i] = (x / 2, y / 2)
        state.last_gps_resync[i] = now
    except Exception as e:
        print("[position-sync] failed for vehicle", i, e)


def sync_swarm_with_telemetry():
    """Refresh idle bots' simulated (x, y) from their vehicle's live GPS.

    The potential-field collision avoidance in utils/robot.py only ever
    moves s.swarm[i].x/y by dead-reckoned steps (Bot.step()); it never reads
    real telemetry. Without this resync the simulated position drifts away
    from where the aircraft actually is, so collision checks stop reflecting
    reality. Called once per dispatched command (mirrors copter_swarm.py).

    Bots with an active_goal_tasks entry are owned by _goal_task_runner for
    the duration of that task and are resynced there every cycle instead --
    see _resync_bot_position's docstring for why writing to them here too
    would race it.
    """
    if state.origin is None:
        return
    with state.active_goal_tasks_lock:
        busy = set(state.active_goal_tasks.keys())
    count = min(len(state.vehicles), len(state.s.swarm), len(state.robots))
    for i in range(count):
        if i not in busy:
            # Idle bots have no swarm-logic motion in progress to protect,
            # so always take the freshest GPS fix when a new command starts.
            _resync_bot_position(i, force=True)


def live_gps_plot_points():
    """Read every vehicle's current GPS fix, fresh, purely for plotting.

    Unlike _resync_bot_position this is read-only (never touches
    s.swarm[i].x/y) and is not throttled by GPS_RESYNC_INTERVAL, so the GPS
    overlay on the sim plot moves in real time even between the periodic
    simulation-state corrections. Returns a list aligned with s.swarm, with
    None for any bot whose fix isn't available yet.
    """
    points = [None] * len(state.vehicles)
    if state.origin is None:
        return points
    for i in range(len(state.vehicles)):
        try:
            lat = state.vehicles[i].location.global_relative_frame.lat
            lon = state.vehicles[i].location.global_relative_frame.lon
            if lat is None or lon is None:
                continue
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            points[i] = (x / 2, y / 2)
        except Exception:
            pass
    return points


def print_sim_vs_real_latlon(indexes, label=""):
    """For each bot index, print the simulated position converted to
    lat/lon, the vehicle's real dronekit lat/lon, and the difference
    between them -- so a mismatch between where the sim thinks a bot is and
    where the real aircraft actually is (the thing that can cause a real
    UAV to circle/orbit near a goal that the sim has already smoothly
    reached) is directly visible and quantified, not just visually implied
    by the plot overlay.
    """
    if state.origin is None:
        return
    for i in indexes:
        if i >= len(state.vehicles) or i >= len(state.s.swarm):
            continue
        try:
            sim_lat, sim_lon = locatePosition.cartToGeo(
                state.origin, config.END_DISTANCE, [state.s.swarm[i].x * 2, state.s.swarm[i].y * 2]
            )
            real_lat = state.vehicles[i].location.global_relative_frame.lat
            real_lon = state.vehicles[i].location.global_relative_frame.lon
            if real_lat is None or real_lon is None:
                continue
            distance = locatePosition.distance_bearing(
                real_lat, real_lon, sim_lat, sim_lon
            )
            # print(
            # 	f"[latlon-mismatch]{(' ' + label) if label else ''} UAV {pos_array[i]}: "
            # 	f"sim=({sim_lat:.7f},{sim_lon:.7f}) real=({real_lat:.7f},{real_lon:.7f}) "
            # 	f"diff=({distance:.2f} m)"
            # )
        except Exception as e:
            print("[latlon-mismatch] failed for vehicle", i, e)
    return distance


def print_sim_vs_real_latlon_with_bot(b, i, label=""):
    """For each bot index, print the simulated position converted to
    lat/lon, the vehicle's real dronekit lat/lon, and the difference
    between them -- so a mismatch between where the sim thinks a bot is and
    where the real aircraft actually is (the thing that can cause a real
    UAV to circle/orbit near a goal that the sim has already smoothly
    reached) is directly visible and quantified, not just visually implied
    by the plot overlay.
    """
    if state.origin is None:
        return 0
    try:
        sim_lat, sim_lon = locatePosition.cartToGeo(
            state.origin, config.END_DISTANCE, [b.x * 2, b.y * 2]
        )
        real_lat = state.vehicles[i].location.global_relative_frame.lat
        real_lon = state.vehicles[i].location.global_relative_frame.lon

        distance = locatePosition.distance_bearing(real_lat, real_lon, sim_lat, sim_lon)

    except Exception as e:
        print("[latlon-mismatch] failed for vehicle", i, e)
        return float("inf")
    return distance


def uav_distance_to_goal(i, goal):
    """Return live UAV-to-goal distance in metres, or None without telemetry."""
    if not state.master_flag or i >= len(state.vehicles) or state.origin is None:
        return None
    try:
        goal_lat, goal_lon = locatePosition.cartToGeo(
            state.origin, config.END_DISTANCE, [goal[0] * 2, goal[1] * 2]
        )
        frame = state.vehicles[i].location.global_relative_frame
        if frame.lat is None or frame.lon is None:
            return None
        return locatePosition.distance_bearing(frame.lat, frame.lon, goal_lat, goal_lon)
    except Exception as e:
        print("[uav-flyby] distance unavailable for vehicle", i, e)
        return None
