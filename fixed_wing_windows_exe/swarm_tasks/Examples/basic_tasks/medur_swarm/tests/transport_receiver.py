"""Test helper: runs the REAL communication/sockets.py + reliable.py with the
heavy flight dependencies stubbed, and plays the role of main.run()'s mailbox
consumer. Every command the swarm would dispatch is appended to argv[1]."""

import os
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)  # .../medur_swarm


def _mod(name, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


medur = _mod("medur_swarm", __path__=[PKG])
_mod("medur_swarm.communication", __path__=[os.path.join(PKG, "communication")])
state = _mod(
    "medur_swarm.state",
    last_seq=0,
    heartbeat_ip_timeout=[],
    master_flag=False,
    pos_array=[],
    master_num=0,
    index=None,
    next_wp=0,
    skip_wp_flag=False,
    home_pos=[],
    uav_home_pos=[],
    vehicles=[],
    file_name="x",
    s=None,
)
_mod("medur_swarm.config", HEARTBEAT_IP=[])
_mod("medur_swarm.uav", __path__=[])
_mod(
    "medur_swarm.uav.connection",
    vehicle_connection=lambda: None,
    fetch_location=lambda: None,
)
medur.state, medur.config = state, sys.modules["medur_swarm.config"]
_mod("swarm_tasks")
_mod("swarm_tasks.simulation")
class _Sim:
    def __init__(self, *args, **kwargs):
        pass


_mod("swarm_tasks.simulation.simulation", Simulation=_Sim)
sys.modules["swarm_tasks.simulation"].simulation = sys.modules[
    "swarm_tasks.simulation.simulation"
]
sys.modules["swarm_tasks"].simulation = sys.modules["swarm_tasks.simulation"]

from medur_swarm.communication import sockets  # binds 12008/12002 like production

sockets.start_listener_threads()
out = sys.argv[1]
busy = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0  # simulate a slow mission loop
print("READY", flush=True)
while True:
    while sockets.pending_command.seq <= state.last_seq:
        time.sleep(0.005)
    data = sockets.pending_command.data
    state.last_seq = sockets.pending_command.seq
    with open(out, "ab") as f:
        f.write(data + b"\n")
    time.sleep(busy)
