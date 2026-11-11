"""'different' command: per-bot altitude re-staggering, applied either
live (idle bots get an explicit background altitude task) or picked up on
the fly by whatever task is already driving a busy bot."""

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
    with state.active_goal_tasks_lock:
        busy_indexes = set(state.active_goal_tasks.keys())
    # A foreground search/split/specificsplit loop flies its bots itself (they
    # are held out of active_goal_tasks on purpose), and already re-reads
    # different_height[i] every tick when it issues simple_goto -- so the array
    # update above is all those bots need. Assigning them a separate altitude
    # task instead makes the foreground loop treat them as "diverted" and drop
    # them from the mission permanently, so count them as busy here.
    busy_indexes |= set(state.foreground_mission_indexes)
    idle_indexes = [i for i in selected_indexes if i not in busy_indexes]
    if idle_indexes:
        assign_altitude_tasks(idle_indexes)
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
