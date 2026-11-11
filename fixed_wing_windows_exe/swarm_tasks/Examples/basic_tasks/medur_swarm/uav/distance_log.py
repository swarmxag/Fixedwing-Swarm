"""Read-only CSV log of each chosen UAV's distance to its bot and to its
look-ahead point, one file per UAV. Each UAV runs on its own thread and only
reads shared state, so it cannot change a bot, a target or a command. Choose
the UAVs in config.DISTANCE_LOG_UAV_IDS.
"""

import csv
import os
import threading
import time
from datetime import datetime

import locatePosition

from medur_swarm import config, state

HEADER = [
    "time",
    "elapsed_s",
    "uav",
    "mode",
    "uav_to_bot_m",
    "uav_to_lookahead_m",
    "nearest_uav",
    "nearest_uav_m",
    "nearest_uav_alt_diff_m",
]


def _nearest_uav(i, location):
    """(sys id, horizontal metres, altitude difference metres) of the closest
    other connected UAV, or None when there is no other fix."""
    best = None
    for j, other in enumerate(state.vehicles):
        if j == i:
            continue
        try:
            o = other.location.global_relative_frame
            if o.lat is None or o.lon is None:
                continue
            d = locatePosition.distance_bearing(location.lat, location.lon, o.lat, o.lon)
            alt = (
                abs(location.alt - o.alt)
                if location.alt is not None and o.alt is not None
                else None
            )
        except Exception:
            continue
        if best is None or d < best[1]:
            sys_id = state.pos_array[j] if j < len(state.pos_array) else j
            best = (sys_id, d, alt)
    return best

_started = False


def _bot_index(uav_id):
    """Current bot index of the UAV. Indexes shift when a UAV is removed."""
    for index, value in enumerate(state.pos_array):
        if int(value) == int(uav_id):
            return index
    return None


def _distance_to_sim_point(real_lat, real_lon, point):
    lat, lon = locatePosition.cartToGeo(
        state.origin, config.END_DISTANCE, [point[0] * 2, point[1] * 2]
    )
    return locatePosition.distance_bearing(real_lat, real_lon, lat, lon)


def sample(uav_id):
    """(mode, uav_to_bot_m, uav_to_lookahead_m, nearest), or None with nothing
    to measure. The look-ahead distance is None while the UAV has no commanded
    point; nearest is _nearest_uav's tuple or None."""
    if not state.master_flag or state.origin is None or state.s is None:
        return None
    i = _bot_index(uav_id)
    if i is None or i >= len(state.vehicles) or i >= len(state.s.swarm):
        return None
    vehicle = state.vehicles[i]
    location = vehicle.location.global_relative_frame
    if location.lat is None or location.lon is None:
        return None
    bot = state.s.swarm[i]
    to_bot = _distance_to_sim_point(location.lat, location.lon, (bot.x, bot.y))
    target = state.uav_lookahead_points.get(i)
    to_target = (
        None
        if target is None
        else _distance_to_sim_point(location.lat, location.lon, target)
    )
    return vehicle.mode.name, to_bot, to_target, _nearest_uav(i, location)


def _run(uav_id, interval_s, folder):
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"uav{uav_id}_distance_{stamp}.csv")
    start = time.monotonic()
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        f.flush()
        print("[distance-log] writing", path)
        while True:
            try:
                row = sample(uav_id)
                if row is not None:
                    mode, to_bot, to_target, nearest = row
                    if nearest is None:
                        near_id = near_m = near_alt = ""
                    else:
                        near_id = nearest[0]
                        near_m = f"{nearest[1]:.1f}"
                        near_alt = "" if nearest[2] is None else f"{nearest[2]:.1f}"
                    writer.writerow(
                        [
                            datetime.now().strftime("%H:%M:%S.%f")[:-3],
                            f"{time.monotonic() - start:.1f}",
                            uav_id,
                            mode,
                            f"{to_bot:.1f}",
                            "" if to_target is None else f"{to_target:.1f}",
                            near_id,
                            near_m,
                            near_alt,
                        ]
                    )
                    f.flush()
            except Exception as e:
                print("[distance-log] sample skipped", e)
            time.sleep(interval_s)


def _run_safely(uav_id, interval_s, folder):
    try:
        _run(uav_id, interval_s, folder)
    except Exception as e:
        print("[distance-log] stopped", e)


def start():
    """Start one logger thread per listed UAV, once. Does nothing when disabled."""
    global _started
    if _started or not config.DISTANCE_LOG_ENABLED:
        return
    _started = True
    for uav_id in config.DISTANCE_LOG_UAV_IDS:
        threading.Thread(
            target=_run_safely,
            args=(uav_id, config.DISTANCE_LOG_INTERVAL_S, config.DISTANCE_LOG_DIR),
            daemon=True,
            name=f"distance-log-uav{uav_id}",
        ).start()
