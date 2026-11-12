"""'different' command (and the sender 'same' uses): change ONLY the height of
the selected UAVs, whatever they are doing -- the height table that every
running command reads is updated, and ArduPlane's altitude-only GUIDED command
is sent to each of them. No task, no position, nothing interrupted."""

import threading
import time

from swarm_tasks.modules.dispersion import disp_field
from swarm_tasks.tasks import area_coverage as cvg

from medur_swarm import state
from medur_swarm.communication import lifecycle
from medur_swarm.utils import parse_selected_uav_ids, selected_swarm_indexes


def apply_different_heights(decoded_index):
    """Parses a 'different,{height},{step}[,{ids}]' command and updates the
    shared different_height[] array for the targeted bot indexes (or every
    connected UAV if no ids given). Height is computed from each bot's real
    pos_array index (height + step*bot_index), not its position within the
    selection, so a partial re-stagger stays consistent with the whole
    fleet's existing layering instead of restarting from the base altitude.

    Critically, this never touches (x,y)/task state for bots that already
    have an active goal/mission/guided_circle task -- their own
    _drive_vehicle_towards() call reads different_height[i] fresh every
    tick, so updating it here alone re-targets their altitude on their very
    next drive tick with zero interruption to whatever they were already
    flying. The same holds for a bot being flown by a foreground
    search/split/specificsplit loop (tracked in state.foreground_mission_indexes)
    -- that loop's own simple_goto reads different_height[i] fresh every tick.
    Only a bot that is neither gets an explicit altitude task assigned, since
    nothing would otherwise command it to actually climb or descend."""
    parts = decoded_index.split(",", 3)
    height = int(parts[1])
    step = int(parts[2])
    selected_uav_raw = parts[3] if len(parts) > 3 else None
    selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
    selected_indexes = selected_swarm_indexes(selected_uav_ids)

    state.same_alt_flag = False
    state.different_step = step  # a re-added UAV is layered with this step
    for bot_index in selected_indexes:
        if bot_index < len(state.different_height):
            state.different_height[bot_index] = height + step * bot_index
    print(
        "[different] updated different_height",
        state.different_height,
        "for indexes",
        selected_indexes,
    )
    # Height only, for EVERY selected UAV -- idle, on a goal, loitering, in a
    # search/split, anything. No task is assigned and no position is sent, so
    # whatever a UAV is doing carries on untouched (its own commands already
    # use the new different_height[i]). The altitude-only command is sent to
    # all of them because once ArduPlane has received one, it ignores the
    # height of later position commands (SITL, Plane 4.8: asked 140 m by
    # simple_goto, stayed at the 120 m of the earlier altitude-only command).
    if state.master_flag:
        request_altitude_change(
            [
                (i, state.different_height[i])
                for i in selected_indexes
                if i < len(state.different_height)
            ]
        )
    return True


def assign_altitude_tasks(selected_indexes):
    with state.active_goal_tasks_lock:
        for bot_index in selected_indexes:
            lifecycle.claim(bot_index)
            state.active_goal_tasks[bot_index] = {
                "type": "altitude",
            }
    print(
        "[altitude-task] assigned (idle bots climbing/descending in place)",
        selected_indexes,
    )


def handle_concurrent_different_command(command_data):
    if not command_data.startswith(b"different"):
        return False
    try:
        return apply_different_heights(command_data.decode("utf-8"))
    except Exception as e:
        print("[concurrent different] failed", e)
        return False


# ArduPilot's altitude-only GUIDED command (Plane 4.1+): changes the target
# altitude and keeps the current GUIDED position target, so the aircraft keeps
# circling exactly where it is. Verified in SITL on Plane 4.8 (ACCEPTED, climbed
# 100 -> 120 m, loiter centre unchanged).
MAV_CMD_GUIDED_CHANGE_ALTITUDE = 43001
MAV_FRAME_GLOBAL_RELATIVE_ALT = 3  # same altitude reference as simple_goto
ALTITUDE_RESEND_S = 3.0  # resend until reached, in case a packet is lost
ALTITUDE_TIMEOUT_S = 120.0
ALTITUDE_TOLERANCE_M = 1.5

_ack_listening = set()
_last_ack = {}  # id(vehicle) -> MAV_RESULT of its last altitude command
_ACK_NAMES = {
    0: "ACCEPTED",
    1: "TEMPORARILY_REJECTED",
    2: "DENIED",
    3: "UNSUPPORTED",
    4: "FAILED",
}


def _listen_for_altitude_acks(vehicle):
    if id(vehicle) in _ack_listening:
        return
    _ack_listening.add(id(vehicle))

    @vehicle.on_message("COMMAND_ACK")
    def _ack(_self, _name, msg):
        if msg.command == MAV_CMD_GUIDED_CHANGE_ALTITUDE:
            _last_ack[id(vehicle)] = msg.result


def _send_altitude_change(vehicle, target_alt):
    """Altitude only -- no position is sent, so nothing can move the aircraft
    sideways. param3 (climb rate) 0 = autopilot default."""
    _listen_for_altitude_acks(vehicle)
    msg = vehicle.message_factory.command_int_encode(
        vehicle._master.target_system,
        vehicle._master.target_component,
        MAV_FRAME_GLOBAL_RELATIVE_ALT,
        MAV_CMD_GUIDED_CHANGE_ALTITUDE,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        float(target_alt),
    )
    vehicle.send_mavlink(msg)


# --- Altitude sender: height changes without tasks -------------------------
# One background thread resends the altitude-only command every
# ALTITUDE_RESEND_S until the UAV is within ALTITUDE_TOLERANCE_M of its new
# height (or ALTITUDE_TIMEOUT_S), then forgets it. It is NOT a task: it never
# appears in active_goal_tasks, never sends a position, never marks a UAV
# busy, so a running goal / loiter / search / split is never interrupted.

_pending_lock = threading.Lock()
_pending = {}  # id(vehicle) -> {"vehicle", "uav", "target", "started", "sent"}
_sender_thread = None


def request_altitude_change(index_heights):
    """index_heights: [(swarm index, height m relative to home), ...]. A newer
    request for the same UAV replaces the older one."""
    for i, target in index_heights:
        if not (0 <= i < len(state.vehicles)):
            continue
        vehicle = state.vehicles[i]
        uav = state.pos_array[i] if i < len(state.pos_array) else i
        try:
            mode = vehicle.mode.name
        except Exception:
            mode = None
        if mode != "GUIDED":
            print(
                f"[altitude] UAV {uav} is in {mode}, not GUIDED -- height {target} m "
                f"stored, not sent (no position is ever sent instead)"
            )
            continue
        with _pending_lock:
            _pending[id(vehicle)] = {
                "vehicle": vehicle,
                "uav": uav,
                "target": float(target),
                "started": time.monotonic(),
                "sent": 0.0,
            }
        print(
            f"[altitude] UAV {uav}: height -> {target} m "
            f"(altitude only, current operation unchanged)"
        )
    _ensure_sender()


def _ensure_sender():
    global _sender_thread
    if _sender_thread is None or not _sender_thread.is_alive():
        _sender_thread = threading.Thread(
            target=_sender_loop, daemon=True, name="altitude-sender"
        )
        _sender_thread.start()


def _sender_loop():
    while True:
        time.sleep(0.5)
        with _pending_lock:
            jobs = list(_pending.items())
        for key, job in jobs:
            try:
                _altitude_step(key, job)
            except Exception as e:  # e.g. the UAV was removed and its link closed
                print("[altitude] sender stopped for UAV", job["uav"], repr(e))
                _drop(key, job)


def _drop(key, job):
    with _pending_lock:
        if _pending.get(key) is job:
            del _pending[key]


def _altitude_step(key, job):
    vehicle, uav, target = job["vehicle"], job["uav"], job["target"]
    now = time.monotonic()
    alt = vehicle.location.global_relative_frame.alt
    if alt is not None and abs(alt - target) <= ALTITUDE_TOLERANCE_M:
        print(f"[altitude] UAV {uav} reached {target} m")
        _drop(key, job)
        return
    mode = vehicle.mode.name
    if mode != "GUIDED":
        print(f"[altitude] UAV {uav} left GUIDED ({mode}) -- stopped sending {target} m")
        _drop(key, job)
        return
    if now - job["started"] > ALTITUDE_TIMEOUT_S:
        print(
            f"[altitude] UAV {uav} did not reach {target} m within "
            f"{ALTITUDE_TIMEOUT_S:.0f} s (now {alt} m) -- giving up"
        )
        _drop(key, job)
        return
    result = _last_ack.get(key)
    if result not in (None, 0) and job.get("reported") != result:
        job["reported"] = result
        print(
            f"[altitude] UAV {uav} rejected the altitude change: "
            f"{_ACK_NAMES.get(result, result)}"
        )
    if now - job["sent"] >= ALTITUDE_RESEND_S:
        _last_ack.pop(key, None)
        _send_altitude_change(vehicle, target)
        job["sent"] = now


def _drive_altitude_task(i, b, task, completed):
    """Idle UAV, new height: change ONLY its altitude, with the altitude-only
    GUIDED command, and send no position at all -- it keeps circling where it
    already is. (This used to simple_goto the bot's (x, y), which could be an
    old bot position or a point on the loiter circle, so the aircraft could be
    moved somewhere nobody planned.) Completes once the real altitude is
    within ALTITUDE_TOLERANCE_M of different_height[i]. Not in GUIDED: nothing
    is sent and the task ends, with a message."""
    # The plotted bot just holds where it is (as before); the aircraft no
    # longer follows it.
    cmd = cvg.goal_area_cvg(i, b, (b.x, b.y))
    cmd += disp_field(b, neighbourhood_radius=100)
    cmd.exec(b)
    if not (
        state.master_flag
        and i < len(state.vehicles)
        and i < len(state.different_height)
    ):
        return
    vehicle = state.vehicles[i]
    uav = state.pos_array[i] if i < len(state.pos_array) else i
    target_alt = state.different_height[i]
    now = time.monotonic()
    started = task.setdefault("started", now)
    try:
        current_alt = vehicle.location.global_relative_frame.alt
        mode = vehicle.mode.name
    except Exception:
        return  # telemetry hiccup: try again next tick
    if (
        current_alt is not None
        and abs(current_alt - target_alt) <= ALTITUDE_TOLERANCE_M
    ):
        completed.append(i)
        print("[altitude-task] reached target altitude for UAV", uav, target_alt)
        return
    if mode != "GUIDED":
        completed.append(i)
        print(
            f"[altitude-task] UAV {uav} is in {mode}, not GUIDED -- altitude-only "
            f"change not sent (no position is ever sent instead)"
        )
        return
    if now - started > ALTITUDE_TIMEOUT_S:
        completed.append(i)
        print(
            f"[altitude-task] UAV {uav} did not reach {target_alt} m within "
            f"{ALTITUDE_TIMEOUT_S:.0f} s (now {current_alt} m) -- giving up"
        )
        return
    result = _last_ack.get(id(vehicle))
    if result not in (None, 0) and task.get("reported_ack") != result:
        task["reported_ack"] = result
        print(
            f"[altitude-task] UAV {uav} rejected the altitude change: "
            f"{_ACK_NAMES.get(result, result)}"
        )
    if (
        task.get("target") != target_alt
        or now - task.get("sent", 0.0) >= ALTITUDE_RESEND_S
    ):
        if task.get("target") != target_alt:
            print(
                f"[altitude-task] UAV {uav}: altitude-only change "
                f"{current_alt} -> {target_alt} m (position unchanged)"
            )
        _last_ack.pop(id(vehicle), None)
        _send_altitude_change(vehicle, target_alt)
        task["target"] = target_alt
        task["sent"] = now
