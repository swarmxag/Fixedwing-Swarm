"""Refuses commands that would take a UAV outside the drawn fence.

rectangles.yaml carries the fence outline under `fence:` (written by the
server's YamlCreation, in the same sim frame as the walls); the world loader
puts it on `state.s.env.fence`. Goal points and search/split paths outside it
raise FenceViolation BEFORE anything is assigned, so the command fails with a
clear reason instead of flying. Nothing about how bots move is changed here.

A world file written before the outline existed cannot be checked: that is
logged and the command is allowed, exactly as before.

Search/split generators overwrite each UAV's path CSV in place while they
build the plan, so a refused plan would otherwise leave those files (which
running missions read every tick) half-replaced. `snapshot()` before
generating, and pass it to `check_csv_paths()`; a refusal puts the files and
any tasks the handler had already removed back exactly as they were.
"""

import csv
import math
import os

import locatePosition
from shapely.geometry import Point

from mission_paths import uav_path_csv

from medur_swarm import config, state

_CIRCLE_SAMPLES = 36  # one test point every 10 degrees


class FenceViolation(ValueError):
    """A goal or path point lies outside the drawn fence."""


def _fence():
    sim = getattr(state, "s", None)
    return getattr(getattr(sim, "env", None), "fence", None)


def check_points(points, what):
    """Raise FenceViolation if any (x, y) sim-frame point is outside the fence."""
    fence = _fence()
    if fence is None:
        print(f"[fence] no fence outline loaded -- {what} not checked (draw the fence again)")
        return
    for k, p in enumerate(points):
        x, y = float(p[0]), float(p[1])
        if not fence.covers(Point(x, y)):
            raise FenceViolation(
                f"{what}: point {k + 1} ({x:.1f}, {y:.1f}) is outside the fence"
            )


def check_loiter(centres, what):
    """Raise FenceViolation if the loiter circle around any final point would
    leave the fence. centres: [((x, y) sim frame, radius_m), ...]. The circle
    is laid out in real metres (radius + GEOFENCE_LOITER_MARGIN_M) and taken
    to the sim frame with the same geoToCart the flight uses."""
    fence = _fence()
    if fence is None or state.origin is None:
        print(f"[fence] no fence outline loaded -- {what} loiter circle not checked")
        return
    margin = config.GEOFENCE_LOITER_MARGIN_M
    for k, ((x, y), radius_m) in enumerate(centres):
        # sim frame is half of geoToCart's (goal.py stores x/2, y/2): double it back
        lat, lon = locatePosition.cartToGeo(
            state.origin, config.END_DISTANCE, [float(x) * 2, float(y) * 2]
        )
        reach = abs(float(radius_m)) + margin
        for s in range(_CIRCLE_SAMPLES):
            a = 2.0 * math.pi * s / _CIRCLE_SAMPLES
            north, east = reach * math.cos(a), reach * math.sin(a)
            p_lat = lat + north / 111320.0
            p_lon = lon + east / (111320.0 * max(math.cos(math.radians(lat)), 1e-6))
            try:
                cx, cy = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [p_lat, p_lon])
                inside = fence.covers(Point(float(cx) / 2, float(cy) / 2))  # back to the sim frame
            except ValueError:  # beyond the mapped area, so beyond the fence too
                inside = False
            if not inside:
                raise FenceViolation(
                    f"{what}: point {k + 1} is too close to the fence -- the loiter circle "
                    f"({abs(float(radius_m)):.0f} m + {margin:.0f} m margin) would leave it"
                )


def snapshot(uav_ids=(), indexes=()):
    """Remember the path files of every connected UAV (plus `uav_ids`) and the
    tasks of `indexes`, so a refused plan can be undone."""
    files = {}
    for uav_id in set(int(u) for u in state.pos_array) | set(int(u) for u in uav_ids):
        path = uav_path_csv(uav_id)
        try:
            with open(path, "rb") as f:
                files[path] = f.read()
        except OSError:
            files[path] = None
    with state.active_goal_tasks_lock:
        tasks = {i: state.active_goal_tasks[i] for i in indexes if i in state.active_goal_tasks}
    return files, tasks


def _restore(snap):
    files, tasks = snap
    for path, data in files.items():
        try:
            if data is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                with open(path, "wb") as f:
                    f.write(data)
        except OSError as e:
            print("[fence] could not restore", path, e)
    with state.active_goal_tasks_lock:
        for i, task in tasks.items():
            state.active_goal_tasks.setdefault(i, task)


def check_csv_paths(paths, what, restore=None):
    """Raise FenceViolation if any point of these per-UAV path CSVs is outside
    the fence. With `restore` (from snapshot()), undo the plan first."""
    if _fence() is None:
        print(f"[fence] no fence outline loaded -- {what} paths not checked (draw the fence again)")
        return
    try:
        for path in paths:
            try:
                with open(path, newline="") as f:
                    rows = [r for r in csv.reader(f) if len(r) >= 2]
            except OSError:
                continue  # unreadable files are reported by the mission code itself
            points = []
            for r in rows:
                try:
                    points.append((float(r[0]), float(r[1])))
                except ValueError:
                    continue
            check_points(points, f"{what} path {os.path.basename(path)}")
    except FenceViolation:
        if restore is not None:
            _restore(restore)
        raise
