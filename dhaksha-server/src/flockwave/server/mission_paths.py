"""Shared output-directory convention for grid-generation missions.

Mirrors the same ~/Documents/swarm_env/ convention already used for
rectangles.yaml (see swarm.py::_origin_file_path()), so mission output lives
next to it instead of scattered across hardcoded dev-machine paths.

Twin of fixed_wing_windows_exe/swarm_tasks/Examples/basic_tasks/mission_paths.py
-- kept as a separate file since the two sides run as independent
processes/machines, not shared code.

One CSV + one KML per UAV, in a single flat directory, overwritten in place
by whichever mission (search/split/specificsplit) most recently targeted
that UAV -- there is deliberately no per-run history here. Only the path
CSV is ever read back by anything (medur_fixed_wing.py during flight,
this side for the GCS trajectory display); the KML is written purely for a
human to open in Earth/QGIS. The old per-run timestamped-folder scheme
(mission_dir(), below) is kept only because a UAV being removed
mid-mission still needs its outgoing path preserved long enough for its
uncovered remainder to be redistributed to the rest of the swarm --
snapshot_uav_path_csv() exists for exactly that handoff; without it,
re-adding that UAV and giving it a new mission would overwrite the very
file the redistribution logic is still reading from.
"""

import os
import shutil
import time
import uuid


def mission_dir(feature: str) -> str:
    """Create and return a fresh ~/Documents/swarm_env/missions/<feature>/<run_id>/
    folder for one grid-generation run. Call once per planner-object
    construction and reuse the returned path -- calling again later would
    mint a new run_id and point at an empty folder.

    Superseded by uav_path_csv()/uav_path_kml() for search/split/
    specificsplit's own output (see module docstring) -- kept around as a
    general-purpose timestamped-run helper for anything that still wants
    per-run history."""
    run_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    path = os.path.join(
        os.path.expanduser("~"), "Documents", "swarm_env", "missions", feature, run_id
    )
    os.makedirs(path, exist_ok=True)
    return path


def uav_output_dir() -> str:
    """Flat, non-timestamped directory holding the single current path CSV
    and KML for every UAV. Created once; every mission type writes into the
    same directory, keyed by real UAV id, not by feature or run."""
    path = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env", "missions")
    os.makedirs(path, exist_ok=True)
    return path


def uav_path_csv(uav_id) -> str:
    """The one path CSV a UAV has at any given time -- overwritten in place
    by whichever mission (search/split/specificsplit) most recently
    targeted this UAV id. This is the only output file anything reads back:
    medur_fixed_wing.py during flight, and the GCS trajectory display."""
    return os.path.join(uav_output_dir(), f"uav_{uav_id}_path.csv")


def uav_path_kml(uav_id) -> str:
    """Human-viewable curve for a UAV's current path -- same overwrite-in-
    place lifecycle as uav_path_csv(). Never read back by any code."""
    return os.path.join(uav_output_dir(), f"uav_{uav_id}.kml")


def snapshot_uav_path_csv(uav_id):
    """Copy a UAV's current path CSV to its own permanent, never-overwritten
    file, for the moment that UAV is removed mid-mission.

    uav_path_csv(uav_id) gets overwritten the instant that UAV is re-added
    and given a new mission -- but work-redistribution logic needs to keep
    reading the *removed* UAV's uncovered remainder from that file for
    potentially a while after removal, while other UAVs pick it up. Call
    this at removal time and hand the returned path to the redistribution
    bookkeeping (e.g. medur_fixed_wing.py's removed_grid_filename) instead
    of the live uav_path_csv(uav_id) path, so a premature re-add/overwrite
    can't corrupt an in-flight handoff. Returns None if the UAV had no
    current path file (e.g. it was never given a coverage mission)."""
    src = uav_path_csv(uav_id)
    if not os.path.exists(src):
        return None
    dst = os.path.join(
        uav_output_dir(),
        "removed",
        f"uav_{uav_id}_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}.csv",
    )
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst
