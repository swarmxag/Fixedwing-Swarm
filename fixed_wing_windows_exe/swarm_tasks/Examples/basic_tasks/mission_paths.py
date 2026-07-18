"""Shared output-directory convention for grid-generation missions.

Mirrors the same ~/Documents/swarm_env/ convention already used for
rectangles.yaml (see medur_fixed_wing.py::read_origin()), so mission output
lives next to it instead of scattered flat across the script's own source
folder. Each mission submission gets its own fresh, timestamped folder --
nothing is ever silently overwritten by the next run.

Twin of dhaksha-server/src/flockwave/server/mission_paths.py -- kept as a
separate file since the two sides run as independent processes/machines,
not shared code.
"""

import os
import time
import uuid


def mission_dir(feature):
    """Create and return a fresh ~/Documents/swarm_env/missions/<feature>/<run_id>/
    folder for one grid-generation run. Call once per planner-object
    construction and reuse the returned path -- calling again later would
    mint a new run_id and point at an empty folder.

    run_id is timestamp-prefixed for human sorting/browsing, with a short
    random suffix so two calls within the same second (e.g. rapid repeated
    submissions) never collide on the same folder and silently clobber each
    other's output."""
    run_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    path = os.path.join(
        os.path.expanduser("~"), "Documents", "swarm_env", "missions", feature, run_id
    )
    os.makedirs(path, exist_ok=True)
    return path
