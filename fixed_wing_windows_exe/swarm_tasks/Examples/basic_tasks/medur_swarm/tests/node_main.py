"""Test node: the REAL medur_swarm main loop, dispatcher, lifecycle, runner task
bookkeeping, replica and sockets -- with only the hardware (dronekit, vehicles,
simulation) and the mission *body* faked. Run as a subprocess by the tests.

Fake mission bodies (payload prefixes):
  fg:<sec>        a foreground mission loop that polls check_for_new_command
  fail            raises
  bg:<i>          hand a goal task for bot <i> to the background runner
  bgmulti:<i>,<j> same for two bots
  finishbg:<i>    the background task for bot <i> finishes by itself
anything else completes immediately. Every executed payload is appended to
$HARNESS_LOG.

Env: SWARM_NODE_ID, SWARM_CMD_PORT, SWARM_CTL_PORT, SWARM_STATE_DIR,
     HARNESS_LOG, HARNESS_UAVS ("1,2,3"), HARNESS_MODE (default GUIDED).
"""

import os
import sys
import time
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stubs

stubs.install()

from medur_swarm import state
from medur_swarm.communication import dispatch, replica, sockets
from medur_swarm.tasks import runner
import medur_swarm.main as m

LOG = os.environ["HARNESS_LOG"]
UAVS = [int(x) for x in os.environ.get("HARNESS_UAVS", "1,2,3").split(",")]
MODE = os.environ.get("HARNESS_MODE", "GUIDED")


class FakeVehicle:
    def __init__(self):
        self.mode = types.SimpleNamespace(name=MODE)
        self.armed = True


def fake_connect():
    state.pos_array = list(UAVS)
    state.vehicles = [FakeVehicle() for _ in UAVS]


sockets.uav_connection.vehicle_connection = fake_connect
sockets.uav_connection.fetch_location = lambda: None
sockets.CHECK_network_connection = lambda: None
sockets.sim.Simulation = lambda *a, **k: None
state.origin = [12.0, 77.0]
if os.environ.get("SWARM_NODE_ID") is None:
    fake_connect()


def record(payload):
    with open(LOG, "ab") as f:
        f.write(payload + b"\n")


def fake_dispatch(data):
    record(data)
    if replica.run_resume_command(data):
        return True
    if data == b"stop":
        runner.clear_all_active_tasks()
        return True
    if data.startswith(b"fg:"):
        end = time.time() + float(data[3:])
        started = sockets.pending_command.seq
        while time.time() < end:
            dispatch.check_for_new_command(started)
            time.sleep(0.01)
        return False
    if data == b"fail":
        raise RuntimeError("boom")
    if data.startswith(b"bg:"):
        runner.assign_goal_tasks([int(data[3:])], [(0.0, 0.0), (5.0, 5.0)], "50", "1")
        return False
    if data.startswith(b"bgmulti:"):
        runner.assign_goal_tasks([int(x) for x in data[8:].split(b",")], [(0.0, 0.0)], "50", "1")
        return False
    if data.startswith(b"finishbg:"):
        with state.active_goal_tasks_lock:
            state.active_goal_tasks.pop(int(data[9:]), None)
        return False
    return False


m._load_origin = lambda: None
m._bring_up_master = lambda: None
m._bring_up_simulation = lambda: None
m._dispatch_one = fake_dispatch
m.run()
