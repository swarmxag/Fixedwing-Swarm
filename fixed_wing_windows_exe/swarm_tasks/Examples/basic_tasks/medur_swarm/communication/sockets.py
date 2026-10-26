"""UDP command/telemetry sockets, the two background listener threads that
read them, and the command mailbox the main dispatch loop drains.

Importing this module has the same side effects the top of the original
single-file script had: it binds sock2/sock3 and starts both listener
threads immediately (daemon threads, so they never block process exit).
main.py imports this module early, in the same relative position the
original script created these sockets/threads, to preserve that ordering.
"""

import collections
import json
import os
import socket
import sys
import threading
import time

from swarm_tasks.simulation import simulation as sim

from medur_swarm import config, state
from medur_swarm.communication import lifecycle, reliable, replica
from medur_swarm.uav import connection as uav_connection

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ("", int(os.environ.get("SWARM_CMD_PORT", 12008)))  # receive from .....rx.py
sock2.bind(server_address2)

sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ("", int(os.environ.get("SWARM_CTL_PORT", 12002)))  # receive from .....rx.py
sock3.bind(server_address3)

# ---- node identity ---------------------------------------------------------
# SWARM_NODE_ID (the UAV number whose onboard computer this is, e.g. 1 for
# 192.168.6.101) turns on decentralised mode: the node starts as a STANDBY and
# only flies after the server promotes it with an authorised, epoch-fenced
# "role" message. Without it (the original single-computer setup) the node is
# always the master and accepts everything, exactly as before.
NODE_ID = int(os.environ["SWARM_NODE_ID"]) if os.environ.get("SWARM_NODE_ID") else None
LEGACY_MODE = NODE_ID is None
_role = "master" if LEGACY_MODE else "standby"
_promoting = False
if not LEGACY_MODE:
    state.master_flag = False  # a standby never opens MAVLink to the UAVs

# Payloads a standby still accepts: they keep it ready to take over.
_STANDBY_ALLOWED = (
    b"origin",
    b"geofence",
    b"pos_array",
    b"home_pos",
    b"uav_home_pos",
    b"master-",
)


# A datagram bigger than the recv buffer is dropped (and raises on Windows);
# search/split payloads carry JSON coverage + ids, so use the UDP maximum.
_RECV_BUFSIZE = 65535


def CHECK_network_connection():
    for i, iter_follower in enumerate(state.heartbeat_ip_timeout):
        count_flag = "-n" if sys.platform.startswith("win") else "-c"
        response = os.system("ping %s 1 %s" % (count_flag, config.HEARTBEAT_IP[i]))
        if response == 0:
            state.heartbeat_ip_timeout[i] = 30
            pass
        else:  # Link is down.
            print("link is down")
            linkdown_flag = True
            # master_ip="192.168.0.153"
            # slave_heal_ip[i] = 'nolink'
            state.heartbeat_ip_timeout[i] = 1
    print(" heartbeat_ip_timeout", state.heartbeat_ip_timeout)


def _become_master():
    """The original `master-3` take-over sequence, unchanged, now shared by
    the legacy master-N message and the authorised "role" message."""
    global _role, _promoting
    _promoting = True
    try:
        if state.master_flag:
            _role = "master"
            return
        state.master_flag = True
        CHECK_network_connection()
        uav_connection.vehicle_connection()
        uav_connection.fetch_location()
        state.s = sim.Simulation(
            state.uav_home_pos,
            num_bots=len(state.vehicles),
            env_name=state.file_name,
        )
        _role = "master"
        replica.prepare_after_promotion()  # report only: nothing is replayed
    except Exception as e:
        state.master_flag = False
        _role = "standby"
        print("[role] promotion FAILED, staying standby:", repr(e))
    finally:
        _promoting = False


def _become_standby():
    global _role
    state.master_flag = False
    _role = "standby"


def _handle_role(role, node, epoch):
    """Called by reliable.receive for an epoch-fenced, deduplicated "role"
    message. Promotion runs in a thread (vehicle connection can take long);
    the sender follows the real outcome through the status in later ACKs."""
    if not LEGACY_MODE and node != NODE_ID:
        return False, "wrong_node"
    if role == "master":
        if _promoting:
            return True, "promoting"
        threading.Thread(target=_become_master, daemon=True).start()
        return True, "promoting"
    if role == "standby":
        _become_standby()
        return True, "standby"
    return False, "bad_role"


# Commands the server can still send but that NO swarm handler implements.
# They used to be ACKed and then silently ignored; now they are refused so the
# operator sees "unsupported_command" instead of a false success.
_UNSUPPORTED = (b"clear_csv", b"remove_bot", b"share_data")


def _accept(payload, port_kind):
    """Receiver policy: reject unsupported commands, validate origin updates,
    and refuse mission commands on a node that is not the master."""
    if payload.startswith(_UNSUPPORTED):
        return False, "unsupported_command"
    if payload.startswith(b"origin,"):
        try:
            _, lat, lon = payload.decode("utf-8").split(",")[:3]
            if not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return False, "invalid_origin"
    if LEGACY_MODE or port_kind == "ctl" or _role == "master":
        return True, ""
    if payload.startswith(_STANDBY_ALLOWED):
        return True, ""
    return False, "not_master"


def _status():
    return {
        "node": NODE_ID,
        "legacy": LEGACY_MODE,
        "role": _role,
        "promoting": _promoting,
        "master_flag": bool(state.master_flag),
        "queued": len(_inbox),
        "commands": lifecycle.history(8),
        "unconsumed": pending_command.seq > state.last_seq,
        **replica.status_summary(),
        "last_seq": state.last_seq,
        "uavs": len(state.vehicles),
        "active_tasks": len(getattr(state, "active_goal_tasks", {})),
    }


def _snapshot():
    """Master -> server: the state a standby needs to take over."""
    if _role != "master":
        return False, "not_master", None
    return True, "snapshot", replica.build_snapshot(NODE_ID, reliable.current_epoch())


def _replicate(snap, epoch):
    """Server -> standby: keep the master's snapshot durably."""
    if _role == "master":
        return False, "i_am_master"
    return replica.store(snap, reliable.current_epoch())


reliable.status_provider = _status
reliable.snapshot_handler = _snapshot
reliable.replicate_handler = _replicate
reliable.role_handler = _handle_role
reliable.accept_policy = _accept


def vehicle_collision_moniter_receive():
    while 1:
        raw_index, address = sock3.recvfrom(_RECV_BUFSIZE)
        got = reliable.receive(raw_index, address, sock3, "ctl")
        if got is None:
            continue
        raw_index = got.payload
        print("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", raw_index)
        decoded_index = raw_index.decode("utf-8")
        print("decoded_index", decoded_index)
        state.index = raw_index
        if decoded_index.startswith("master"):
            m, master_num = decoded_index.split("-")
            state.master_num = master_num
            print("m,master_num", m, master_num)
            msg = "Drone 3 master_num " + str(master_num) + " data received"
            if int(master_num) == (3 if LEGACY_MODE else NODE_ID):
                _become_master()
            else:
                _become_standby()

            state.index = "data"
            data = "data"
            msg = "master_num " + str(state.master_num)
            print("master_flag", state.master_flag)

        if decoded_index.startswith("pos_array"):
            message = decoded_index[:9]  # Assuming "home_pos" is 8 characters long
            array_data = decoded_index[9:]
            print("pos_array", state.pos_array)
            state.pos_array = json.loads(array_data)
            print("pos_array", state.pos_array)
            state.index = "data"
            msg = "UAV 1 connected with " + str(len(state.pos_array)) + " vehicles"
            print("master_flag", state.master_flag)
        if decoded_index.startswith("home_pos"):
            message = decoded_index[:8]  # Assuming "home_pos" is 8 characters long
            home_pos = decoded_index[8:]
            print("home_pos", home_pos)
            state.home_pos = json.loads(home_pos)
            print("home_pos", state.home_pos)

        if decoded_index.startswith("uav_home_pos"):
            if state.master_flag:
                pass
            else:
                message = decoded_index[:12]  # Assuming "home_pos" is 8 characters long
                uav_home_pos = decoded_index[12:]
                print("uav_home_pos", uav_home_pos)
                state.uav_home_pos = json.loads(uav_home_pos)
                print("uav_home_pos", state.uav_home_pos)
        if decoded_index.startswith("skip_wp"):
            print("decoded_index", decoded_index)
            c, next_wp = decoded_index.split(",")
            print("c,next_wp", c, next_wp)
            state.next_wp = int(next_wp)
            print("next_wp", state.next_wp)
            state.skip_wp_flag = True
            print("skip_wp_flag", state.skip_wp_flag)


class _CommandMailbox:
    """Thread-safe single-slot mailbox for the latest not-yet-consumed
    sock2 command. Mirrors the sock3/collision_thread/index pattern
    already used above: plain attribute writes are atomic under the
    GIL, so no lock is needed. seq lets a mission loop tell a command
    newer than the one it is currently running apart from the command
    it is currently running.
    """

    def __init__(self):
        self.seq = 0
        self.data = None
        self.address = None


pending_command = _CommandMailbox()


class _Entry:
    __slots__ = ("payload", "address", "sid", "seq", "key", "started_reported")

    def __init__(self, payload, address, sid, seq):
        self.payload, self.address, self.sid, self.seq = payload, address, sid, seq
        self.key = _supersede_key(payload)
        self.started_reported = False


_inbox = collections.deque()
_inbox_cv = threading.Condition()
_promote_lock = threading.Lock()
_mailbox_entry = None  # the entry currently sitting in pending_command


def _event(entry, status, why=""):
    reliable.emit_event(sock2, entry.address, entry.sid, entry.seq, status, why)


def _supersede_key(payload):
    """Pending commands that carry the same key replace each other: only the
    latest goal / auto-goal plan / radius for the same UAV set is worth
    flying. Everything else (search, split, specific split, add/remove, ...)
    has no key and keeps strict arrival order."""
    try:
        text = payload.decode("utf-8")
        if text.startswith("goal_"):
            ids = text.rsplit("_", 1)[1]
            kind = "goal"
        elif text.startswith("autogoal_"):
            ids = text.rsplit("_", 3)[1]
            kind = "autogoal"
        elif text.startswith("autogoalrad_"):
            ids = text.rsplit("_", 1)[1]
            kind = "autogoalrad"
        else:
            return None
        return (kind, tuple(sorted(json.loads(ids))))
    except (ValueError, IndexError, TypeError, UnicodeDecodeError):
        return None


def _command_listener():
    """Receive + ACK on the socket thread, then only enqueue. Never blocks on
    the mission loop, so a retransmit is always ACKed promptly."""
    while 1:
        try:
            data, address = sock2.recvfrom(_RECV_BUFSIZE)
        except OSError as e:
            print("[commands] recv error:", repr(e))
            continue
        got = reliable.receive(data, address, sock2, "cmd")
        if got is None:
            continue
        entry = _Entry(got.payload, got.address, got.sid, got.seq)
        if entry.payload == b"stop":
            # stop supersedes everything still waiting behind the running command.
            with _inbox_cv:
                dropped = list(_inbox)
                _inbox.clear()
            for old in dropped:
                _event(old, "discarded", "stop")
            if dropped:
                print("[commands] stop discarded", len(dropped), "queued command(s)")
            _promote(entry)
        else:
            with _inbox_cv:
                if entry.key is not None:
                    keep = collections.deque()
                    for old in _inbox:
                        if old.key == entry.key:
                            _event(old, "superseded", "newer_" + entry.key[0])
                        else:
                            keep.append(old)
                    _inbox.clear()
                    _inbox.extend(keep)
                _inbox.append(entry)
                _inbox_cv.notify()


def _promote(entry):
    global _mailbox_entry
    with _promote_lock:
        if _mailbox_entry is not None and pending_command.seq > state.last_seq:
            # Only a stop can overwrite an unread command; say so.
            _event(_mailbox_entry, "superseded", "stop")
        pending_command.data = entry.payload
        pending_command.address = entry.address
        pending_command.seq += 1
        lifecycle.register(pending_command.seq, entry)
        _mailbox_entry = entry


def _command_feeder():
    """Moves queued commands into the single-slot mailbox one at a time, only
    after the previous one was consumed (state.last_seq caught up). This keeps
    the mailbox protocol every mission loop relies on unchanged while no
    longer letting a second datagram overwrite an unread first one. Also
    reports "started" once the dispatch loop has actually taken a command."""
    while 1:
        with _inbox_cv:
            while not _inbox:
                lifecycle.reconcile()
                _inbox_cv.wait(0.05)
            entry = _inbox[0]
        while pending_command.seq > state.last_seq:
            time.sleep(0.005)
            lifecycle.reconcile()
        with _inbox_cv:
            if not _inbox or _inbox[0] is not entry:
                continue  # superseded or discarded while we waited
            _inbox.popleft()
        _promote(entry)


def _start_lifecycle():
    """Wire execution-status events to the sender, open the durable journal
    and mark whatever was in flight before a restart as interrupted."""
    lifecycle.set_emitter(
        lambda meta, status, why: reliable.emit_event(
            sock2, meta.address, meta.sid, meta.seq, status, why
        )
    )
    folder = os.environ.get("SWARM_STATE_DIR") or os.path.join(
        os.path.expanduser("~"), "Documents", "swarm_env"
    )
    name = "legacy" if LEGACY_MODE else "node%s" % NODE_ID
    replica.configure(os.path.join(folder, "%s_replica.json" % name))
    lifecycle.open_journal(os.path.join(folder, "%s_journal.jsonl" % name))
    lifecycle.recover_journal(
        emit_to=lambda addr, sid, seq, status, why: reliable.emit_event(
            sock2, addr, sid, seq, status, why
        )
    )


def start_listener_threads():
    """Starts the collision-monitor and command-listener background
    threads. Split out from module import so main.py controls exactly
    when they start, matching the original script's top-to-bottom order
    (both threads are started right after this module's sockets are bound,
    before vehicle_connection()/fetch_location() are ever called -- those
    names are only looked up when a "master" message actually arrives, by
    which point the whole program has finished importing)."""
    _start_lifecycle()
    collision_thread = threading.Thread(target=vehicle_collision_moniter_receive)
    collision_thread.daemon = True
    collision_thread.start()

    command_listener_thread = threading.Thread(target=_command_listener)
    command_listener_thread.daemon = True
    command_listener_thread.start()

    command_feeder_thread = threading.Thread(target=_command_feeder)
    command_feeder_thread.daemon = True
    command_feeder_thread.start()
