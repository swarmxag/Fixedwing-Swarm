"""Per-UAV MAVLink link watch.

dronekit closes a link for good once it has seen no heartbeat for
`heartbeat_timeout` seconds (it keeps checking after connect, in flight), so
an outage longer than that left the UAV deaf for the rest of the flight while
its bot kept planning. Here:

  * attach() switches that in-flight abort off right after connect, so the
    socket stays open and the same Vehicle resumes when packets return;
  * a monitor thread classifies every UAV as ok / stale / lost / dead from our
    own heartbeat timestamps (dronekit's last_heartbeat freezes once its
    threads have stopped);
  * a dead link is reconnected in the background on the SAME slot, without
    holding the topology/task locks while connecting, so pos_array order,
    heights and tasks are untouched and the other UAVs keep flying;
  * ready(i), called by whichever thread drives bot i, holds the bot while its
    link is not ok, and once it is ok again moves the bot to the aircraft's
    fresh GPS position before letting the mission continue.

A UAV whose link stays ok is never affected: ready() returns True and nothing
else here touches its bot.
"""

import threading
import time

from pymavlink import mavutil

from medur_swarm import config, state
from medur_swarm.uav.telemetry import _resync_bot_position

OK, STALE, LOST, DEAD = "ok", "stale", "lost", "dead"

_status = {}  # sys_id -> {"state": str, "since": monotonic time}
_realign = (
    {}
)  # sys_id -> monotonic time the link came back (waiting for a fresh position)
_stream_requested = {}  # sys_id -> last time we re-asked for telemetry streams
_reconnecting = set()  # sys_ids with a reconnect thread running
_lock = threading.Lock()


def attach(vehicle):
    """Call once on every Vehicle right after a successful connect()."""
    # dronekit's own watchdog would close the link after heartbeat_timeout
    # seconds of silence, in flight, permanently. 0 switches only that off;
    # the connect-time timeout has already done its job.
    vehicle._heartbeat_error = 0
    vehicle._swarm_hb = time.monotonic()
    vehicle._swarm_pos = 0.0

    @vehicle.on_message("HEARTBEAT")
    def _heartbeat(_vehicle, _name, msg):
        if msg.type != mavutil.mavlink.MAV_TYPE_GCS:
            vehicle._swarm_hb = time.monotonic()

    @vehicle.on_message("GLOBAL_POSITION_INT")
    def _position(_vehicle, _name, _msg):
        vehicle._swarm_pos = time.monotonic()


def _classify(vehicle, now):
    handler = getattr(vehicle, "_handler", None)
    if handler is not None and not getattr(handler, "_alive", True):
        return DEAD
    age = now - getattr(vehicle, "_swarm_hb", now)
    if age >= config.LINK_LOST_S:
        return LOST
    if age >= config.LINK_STALE_S:
        return STALE
    return OK


def reconnecting(sys_id):
    with _lock:
        return int(sys_id) in _reconnecting


def link_states():
    """{sys_id: "lost 14s"} for every UAV whose link is not ok (for the GCS)."""
    now = time.monotonic()
    with _lock:
        return {
            int(sys_id): "%s %ds" % (entry["state"], now - entry["since"])
            for sys_id, entry in _status.items()
            if entry["state"] != OK
        }


def ready(i):
    """True if bot i may be driven this tick. Call from the thread that owns
    bot i's movement (it may move the bot)."""
    if not state.master_flag or i >= len(state.pos_array) or i >= len(state.vehicles):
        return True
    sys_id = int(state.pos_array[i])
    with _lock:
        entry = _status.get(sys_id)
        if entry is not None and entry["state"] != OK:
            return False
        since = _realign.get(sys_id)
    if since is None:
        return True
    if getattr(state.vehicles[i], "_swarm_pos", 0.0) <= since:
        return False  # still the position frozen at the outage; wait for a fresh one
    _resync_bot_position(i, force=True)
    state.bot_step_last_time.pop(i, None)
    state.uav_lookahead_points.pop(i, None)
    state.goal_min_distance.pop(i, None)
    with _lock:
        _realign.pop(sys_id, None)
    print(
        "[link] UAV", sys_id, "bot moved to the aircraft's position; mission continues"
    )
    return True


def _request_streams(sys_id, vehicle, now):
    """No fresh position after the link came back: the autopilot may have
    rebooted and reset its stream rates, so ask again (same request connect makes)."""
    if now - _stream_requested.get(sys_id, 0.0) < config.LINK_POSITION_WAIT_S:
        return
    _stream_requested[sys_id] = now
    try:
        vehicle._master.mav.request_data_stream_send(
            0, 0, mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
        )
        print(
            "[link] UAV", sys_id, "no position yet -- asked for telemetry streams again"
        )
    except Exception as e:
        print("[link] UAV", sys_id, "stream request failed:", repr(e))


def _slot_of(sys_id, vehicle):
    """Index of sys_id if `vehicle` is still the one in its slot, else None."""
    if sys_id not in state.pos_array:
        return None
    idx = state.pos_array.index(sys_id)
    if idx >= len(state.vehicles) or state.vehicles[idx] is not vehicle:
        return None
    return idx


def _reconnect(sys_id, old):
    from dronekit import connect

    from medur_swarm.uav.connection import connection_string_for_sysid

    try:
        while state.master_flag:
            with state.swarm_topology_lock:
                if _slot_of(sys_id, old) is None:
                    return  # removed or replaced meanwhile
            try:
                old.close()  # frees the UDP port; already closed if dronekit stopped
            except Exception:
                pass
            endpoint = connection_string_for_sysid(sys_id)
            print("[link] UAV", sys_id, "reconnecting", endpoint)
            try:
                vehicle = connect(
                    endpoint,
                    baud=115200,
                    heartbeat_timeout=config.LINK_RECONNECT_TIMEOUT_S,
                    source_system=253,
                )
            except Exception as e:
                print("[link] UAV", sys_id, "reconnect failed:", repr(e))
                time.sleep(config.LINK_RECONNECT_RETRY_S)
                continue
            target = int(vehicle._master.target_system)
            if target != sys_id:
                print(
                    "[link] port of UAV",
                    sys_id,
                    "answered as sys_id",
                    target,
                    "-- refused",
                )
                try:
                    vehicle.close()
                except Exception:
                    pass
                time.sleep(config.LINK_RECONNECT_RETRY_S)
                continue
            attach(vehicle)
            # Only the swap is locked: one short step, same slot.
            with state.swarm_topology_lock, state.active_goal_tasks_lock:
                idx = _slot_of(sys_id, old)
                if idx is not None:
                    state.vehicles[idx] = vehicle
                    entry = state.uav_registry.setdefault(sys_id, {})
                    entry["vehicle"] = vehicle
                    print(
                        "[link] UAV",
                        sys_id,
                        "reconnected in slot",
                        idx,
                        "pos_array",
                        state.pos_array,
                    )
                    return
            vehicle.close()  # the UAV was removed while we were connecting
            return
    finally:
        with _lock:
            _reconnecting.discard(sys_id)


def check_once(now=None):
    """One monitor pass (the thread calls this every LINK_CHECK_INTERVAL_S)."""
    if not state.master_flag:
        return
    now = time.monotonic() if now is None else now
    with state.swarm_topology_lock:
        pairs = list(zip([int(s) for s in state.pos_array], state.vehicles))
    present = set()
    for sys_id, vehicle in pairs:
        present.add(sys_id)
        new = _classify(vehicle, now)
        start_reconnect = False
        with _lock:
            old = _status.get(sys_id, {}).get("state", OK)
            if new != old:
                since = _status.get(sys_id, {}).get("since", now)
                _status[sys_id] = {"state": new, "since": now}
                if new == OK:
                    _realign[sys_id] = now
                    print(
                        "[link] UAV",
                        sys_id,
                        "link restored after %.0f s" % (now - since),
                    )
                else:
                    print("[link] UAV", sys_id, "link", new)
            if new == DEAD and sys_id not in _reconnecting:
                _reconnecting.add(sys_id)
                start_reconnect = True
            waiting = (
                sys_id in _realign
                and getattr(vehicle, "_swarm_pos", 0.0) <= _realign[sys_id]
            )
            waited = waiting and now - _realign[sys_id] >= config.LINK_POSITION_WAIT_S
        if start_reconnect:
            threading.Thread(
                target=_reconnect, args=(sys_id, vehicle), daemon=True
            ).start()
        if waited:
            _request_streams(sys_id, vehicle, now)
    with _lock:
        for sys_id in list(_status):
            if sys_id not in present:  # removed from the swarm
                _status.pop(sys_id, None)
                _realign.pop(sys_id, None)


def _run():
    while True:
        time.sleep(config.LINK_CHECK_INTERVAL_S)
        try:
            check_once()
        except Exception as e:
            print("[link] monitor error:", repr(e))


_started = False


def start():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_run, daemon=True).start()
