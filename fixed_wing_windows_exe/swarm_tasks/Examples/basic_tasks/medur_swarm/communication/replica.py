"""State replication to standby nodes, and safe recovery after a promotion.

Master  : `build_snapshot()` -> a JSON-safe picture of what it is doing (active
          tasks with their versions, UAV membership, guided-circle / auto-goal
          state, altitude plan, recent command statuses, master epoch).
Standby : `store()` keeps the newest snapshot durably on disk (atomic write),
          refusing stale epochs and older versions.
Promote : `reconcile()` compares the stored snapshot with LIVE UAV telemetry
          and with the pending-command outcomes, and produces a report.
          NOTHING is replayed automatically. Only goal-type tasks that pass
          every check can be resumed, and only by an explicit operator command
          (`recover_resume,<version>`); search / split / altitude work and any
          command whose outcome is unknown must be re-issued by the operator.
"""

import json
import os
import threading
import time

from medur_swarm import state
from medur_swarm.communication import lifecycle

SCHEMA = 1
# A replica older than this was taken too long before the failure to say where
# the aircraft are in their task: refuse to resume from it.
RECOVER_MAX_AGE_S = float(os.environ.get("SWARM_RECOVER_MAX_AGE", "30"))
RESUMABLE_MODES = {"GUIDED"}

_lock = threading.Lock()
_version = 0
_path = None
latest = None  # newest stored snapshot (standby) -- survives restart via disk
report = None  # last reconcile() result (new master)


def configure(path):
    global _path
    _path = path
    load()


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [jsonable(v) for v in obj]
    if hasattr(obj, "tolist"):
        return jsonable(obj.tolist())
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return obj if obj == obj and obj not in (float("inf"), float("-inf")) else None
    return None  # not representable: drop rather than invent


def build_snapshot(node, epoch):
    """Master side. Reads shared state under the task lock."""
    global _version
    with _lock:
        _version += 1
        version = _version
    with state.active_goal_tasks_lock:
        tasks = jsonable(dict(state.active_goal_tasks))
    return {
        "schema": SCHEMA,
        "node": node,
        "epoch": epoch,
        "version": version,
        "taken_at": time.time(),
        "uav_ids": jsonable(list(getattr(state, "pos_array", []))),
        "origin": jsonable(getattr(state, "origin", None)),
        "tasks": tasks,
        "task_owner": jsonable(dict(getattr(state, "task_owner", {}))),
        "autogoal_params": jsonable(getattr(state, "autogoal_params", None)),
        "guided_circle": {
            "goal_latlon": jsonable(getattr(state, "goal_latlon", None)),
            "radius": jsonable(getattr(state, "guided_circle_radius", None)),
            "direction": jsonable(getattr(state, "guided_circle_direction", None)),
        },
        "altitude": {
            "different_height": jsonable(getattr(state, "different_height", None)),
            "same_height": jsonable(getattr(state, "same_height", None)),
            "same_alt_flag": jsonable(getattr(state, "same_alt_flag", None)),
        },
        "commands": lifecycle.history(50),
    }


def _key(snap):
    return (int(snap.get("epoch", 0)), int(snap.get("version", 0)))


def store(snap, current_epoch):
    """Standby side. Returns (ok, why)."""
    global latest
    if not isinstance(snap, dict) or snap.get("schema") != SCHEMA:
        return False, "bad_snapshot"
    if int(snap.get("epoch", 0)) < current_epoch:
        return False, "stale_epoch"
    with _lock:
        if latest is not None and _key(snap) <= _key(latest):
            return True, "already_have_newer"
        latest = snap
        if _path:
            tmp = _path + ".tmp"
            os.makedirs(os.path.dirname(_path) or ".", exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(snap, f, separators=(",", ":"))
            os.replace(tmp, _path)
    return True, "stored"


def load():
    global latest
    if _path and os.path.exists(_path):
        try:
            with open(_path, encoding="utf-8") as f:
                latest = json.load(f)
        except (OSError, ValueError):
            latest = None
    return latest


def age_seconds(snap=None, now=None):
    snap = snap or latest
    if not snap:
        return None
    return (now if now is not None else time.time()) - snap.get("taken_at", 0)


# ---- reconciliation (pure: telemetry is passed in) -------------------------

def reconcile(snap, telemetry, now=None, max_age=None):
    """telemetry: {uav_id: {"connected": bool, "mode": str, "armed": bool}}.
    Returns a report; verdicts are only advice -- see run_resume_command."""
    now = time.time() if now is None else now
    max_age = RECOVER_MAX_AGE_S if max_age is None else max_age
    if not snap:
        return {"replica": None, "tasks": [], "unknown_commands": [], "resumable": 0}
    age = now - snap.get("taken_at", 0)
    stale = age > max_age
    ids = snap.get("uav_ids", [])
    tasks = []
    for key, task in sorted(snap.get("tasks", {}).items(), key=lambda kv: int(kv[0])):
        idx = int(key)
        uav = ids[idx] if idx < len(ids) else None
        entry = {"index": idx, "uav": uav, "type": task.get("type"), "reasons": []}
        live = telemetry.get(uav)
        if stale:
            entry["reasons"].append("replica_stale(%.0fs>%.0fs)" % (age, max_age))
        if uav is None or live is None or not live.get("connected"):
            entry["reasons"].append("uav_not_connected")
        else:
            if not live.get("armed"):
                entry["reasons"].append("not_armed")
            if str(live.get("mode", "")).upper() not in RESUMABLE_MODES:
                entry["reasons"].append("mode_%s" % live.get("mode"))
        if task.get("type") == "goal":
            if int(task.get("goal_index", 0)) >= len(task.get("goals", [])):
                entry["reasons"].append("no_goals_remaining")
            elif task.get("circle_points") is not None:
                entry["reasons"].append("already_in_final_circle")
            entry["verdict"] = "resumable" if not entry["reasons"] else (
                "discard" if stale or any(r in ("uav_not_connected", "not_armed", "no_goals_remaining")
                                          for r in entry["reasons"]) else "needs_reissue")
        else:
            entry["reasons"].append("%s_task_must_be_reissued_by_operator" % task.get("type"))
            entry["verdict"] = "needs_reissue"
        tasks.append(entry)
    unknown = [
        {"cmd": c.get("cmd"), "last_status": c.get("status"), "outcome": "unknown"}
        for c in snap.get("commands", [])
        if c.get("status") not in lifecycle.TERMINAL
    ]
    return {
        "replica": {
            "node": snap.get("node"),
            "epoch": snap.get("epoch"),
            "version": snap.get("version"),
            "age_s": round(age, 1),
        },
        "tasks": tasks,
        "unknown_commands": unknown,
        "resumable": sum(1 for t in tasks if t["verdict"] == "resumable"),
    }


def live_telemetry():
    """{uav_id: {...}} from the connected dronekit vehicles."""
    out = {}
    vehicles = getattr(state, "vehicles", [])
    ids = getattr(state, "pos_array", [])
    for i, uav in enumerate(ids):
        try:
            v = vehicles[i]
            out[uav] = {"connected": True, "mode": v.mode.name, "armed": bool(v.armed)}
        except Exception:
            out[uav] = {"connected": False}
    return out


def prepare_after_promotion():
    """Called once the new master has connected to the UAVs. Never raises."""
    global report
    try:
        report = reconcile(latest, live_telemetry())
        state.recovery_report = report
        print("[recovery] replica reconciled:", json.dumps(report)[:300])
    except Exception as e:
        report = {"error": repr(e), "tasks": [], "unknown_commands": [], "resumable": 0}
        print("[recovery] reconcile failed:", repr(e))
    return report


def status_summary():
    r = report
    return {
        "replica_version": None if latest is None else latest.get("version"),
        "replica_epoch": None if latest is None else latest.get("epoch"),
        "replica_age_s": None if latest is None else round(age_seconds(), 1),
        "recovery": None if r is None else {
            "version": (r.get("replica") or {}).get("version"),
            "resumable": r.get("resumable", 0),
            "needs_operator": sum(1 for t in r.get("tasks", []) if t["verdict"] != "resumable"),
            "unknown_commands": len(r.get("unknown_commands", [])),
        },
    }


# ---- operator-confirmed resume ---------------------------------------------

def run_resume_command(data):
    """`recover_resume,<version>` -- re-assign ONLY goal tasks that still pass
    reconcile() against telemetry taken now. Returns True if it handled the
    command (so the dispatch chain can stop)."""
    if not data.startswith(b"recover_resume"):
        return False
    global report
    from medur_swarm.tasks import runner  # lazy: heavy flight imports

    try:
        version = int(data.decode("utf-8").split(",")[1])
    except (IndexError, ValueError):
        print("[recovery] resume refused: bad command")
        return True
    snap = latest
    if snap is None or int(snap.get("version", -1)) != version:
        print("[recovery] resume refused: replica version mismatch (have %s, asked %s)"
              % (None if snap is None else snap.get("version"), version))
        return True
    if snap.get("origin") != jsonable(getattr(state, "origin", None)):
        print("[recovery] resume refused: origin differs from the failed master's")
        return True
    fresh = reconcile(snap, live_telemetry())
    report = fresh
    state.recovery_report = fresh
    resumed = []
    for t in fresh["tasks"]:
        if t["verdict"] != "resumable":
            continue
        task = snap["tasks"][str(t["index"])]
        try:
            new_index = list(state.pos_array).index(t["uav"])
        except ValueError:
            continue
        goals = [tuple(g) for g in task["goals"][int(task.get("goal_index", 0)):]]
        runner.assign_goal_tasks(
            [new_index], goals, task.get("guided_circle_radius"), task.get("guided_circle_direction")
        )
        resumed.append(t["uav"])
    print("[recovery] resumed goal tasks for UAVs:", resumed)
    return True
