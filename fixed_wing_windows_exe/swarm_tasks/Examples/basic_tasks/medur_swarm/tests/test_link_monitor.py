"""In-flight MAVLink link loss: the link is kept open, a dead one is reconnected
on the same slot (pos_array order unchanged, no locks held while connecting),
the bot is held while the link is down and re-aligned with the aircraft's fresh
position when it is back. UAVs whose link stays ok are not touched.

Run:  python3 test_link_monitor.py
"""

import os
import random
import sys
import tempfile
import threading
import time
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("SWARM_CMD_PORT", "12798")
os.environ.setdefault("SWARM_CTL_PORT", "12792")
os.environ.setdefault("SWARM_STATE_DIR", tempfile.mkdtemp())
sys.path.insert(0, HERE)
import stubs  # noqa: E402

stubs.install()

from medur_swarm import config, state  # noqa: E402
from medur_swarm.uav import connection, link_monitor, management  # noqa: E402

rng = random.SystemRandom()
GCS = 6


class FakeVehicle:
    def __init__(self, sys_id):
        self._handler = types.SimpleNamespace(_alive=True)
        self._listeners = {}
        self.requests = []
        self.closed = False
        self._master = types.SimpleNamespace(
            target_system=sys_id,
            mav=types.SimpleNamespace(request_data_stream_send=lambda *a: self.requests.append(a)),
        )
        frame = types.SimpleNamespace(lat=10.0, lon=20.0, alt=100.0)
        self.location = types.SimpleNamespace(global_relative_frame=frame)

    def on_message(self, name):
        def register(fn):
            self._listeners.setdefault(name, []).append(fn)
            return fn
        return register

    def deliver(self, name, msg_type=1):
        for fn in self._listeners.get(name, []):
            fn(self, name, types.SimpleNamespace(type=msg_type))

    def close(self):
        self.closed = True
        self._handler._alive = False


class LinkMonitor(unittest.TestCase):
    def setUp(self):
        link_monitor.mavutil = types.SimpleNamespace(
            mavlink=types.SimpleNamespace(MAV_TYPE_GCS=GCS, MAV_DATA_STREAM_ALL=0)
        )
        link_monitor._status.clear()
        link_monitor._realign.clear()
        link_monitor._stream_requested.clear()
        link_monitor._reconnecting.clear()
        state.master_flag = True
        n = rng.randint(3, 6)
        self.ids = sorted(rng.sample(range(1, 15), n))
        state.pos_array = list(self.ids)
        state.vehicles = [FakeVehicle(s) for s in self.ids]
        for v in state.vehicles:
            link_monitor.attach(v)
        state.bot_step_last_time.clear()
        state.uav_lookahead_points.clear()
        state.goal_min_distance.clear()
        self.resynced = []
        self.real_resync = link_monitor._resync_bot_position
        link_monitor._resync_bot_position = lambda i, force=False: self.resynced.append((i, force))
        self.real_retry = config.LINK_RECONNECT_RETRY_S
        config.LINK_RECONNECT_RETRY_S = 0.01
        self.lost = rng.randrange(n)

    def tearDown(self):
        link_monitor._resync_bot_position = self.real_resync
        config.LINK_RECONNECT_RETRY_S = self.real_retry
        state.pos_array, state.vehicles = [], []

    def silence(self, i, seconds):
        state.vehicles[i]._swarm_hb = time.monotonic() - seconds

    def test_dronekit_in_flight_abort_is_switched_off(self):
        for v in state.vehicles:
            self.assertEqual(v._heartbeat_error, 0)

    def test_short_gap_is_ignored(self):
        self.silence(self.lost, config.LINK_STALE_S * 0.5)
        link_monitor.check_once()
        self.assertTrue(all(link_monitor.ready(i) for i in range(len(self.ids))))
        self.assertEqual(link_monitor.link_states(), {})

    def test_stale_and_lost_hold_only_that_bot(self):
        self.silence(self.lost, config.LINK_STALE_S + 0.5)
        link_monitor.check_once()
        self.assertFalse(link_monitor.ready(self.lost))
        others = [i for i in range(len(self.ids)) if i != self.lost]
        self.assertTrue(all(link_monitor.ready(i) for i in others))
        self.silence(self.lost, config.LINK_LOST_S + 1)
        link_monitor.check_once()
        self.assertTrue(link_monitor.link_states()[self.ids[self.lost]].startswith("lost"))

    def test_restore_waits_for_fresh_position_then_aligns_bot(self):
        i, v = self.lost, state.vehicles[self.lost]
        state.bot_step_last_time[i] = 1.0
        state.uav_lookahead_points[i] = (5, 5)
        self.silence(i, config.LINK_LOST_S + rng.uniform(1, 60))
        link_monitor.check_once()
        v.deliver("HEARTBEAT")  # link back
        link_monitor.check_once()
        self.assertFalse(link_monitor.ready(i))  # location is still the frozen one
        self.assertEqual(self.resynced, [])
        time.sleep(0.05)  # next position message (real ones are ~0.25 s apart)
        v.deliver("GLOBAL_POSITION_INT")
        self.assertTrue(link_monitor.ready(i))
        self.assertEqual(self.resynced, [(i, True)])
        self.assertNotIn(i, state.bot_step_last_time)
        self.assertNotIn(i, state.uav_lookahead_points)
        self.assertTrue(link_monitor.ready(i))
        self.assertEqual(len(self.resynced), 1)  # aligned once, then normal

    def test_gcs_heartbeat_does_not_count(self):
        self.silence(self.lost, config.LINK_STALE_S + 1)
        state.vehicles[self.lost].deliver("HEARTBEAT", msg_type=GCS)
        link_monitor.check_once()
        self.assertFalse(link_monitor.ready(self.lost))

    def test_no_position_after_restore_asks_for_streams(self):
        v = state.vehicles[self.lost]
        self.silence(self.lost, config.LINK_LOST_S + 1)
        link_monitor.check_once()
        v.deliver("HEARTBEAT")
        link_monitor.check_once()
        link_monitor.check_once(time.monotonic() + config.LINK_POSITION_WAIT_S + 0.1)
        self.assertEqual(len(v.requests), 1)

    def reconnect_with(self, make, slot=None):
        slot = self.lost if slot is None else slot
        made = []

        def fake_connect(endpoint, **kw):
            v = make(len(made))
            made.append(v)
            return v

        real = sys.modules["dronekit"].connect if hasattr(sys.modules["dronekit"], "connect") else None
        sys.modules["dronekit"].connect = fake_connect
        try:
            state.vehicles[slot]._handler._alive = False  # dronekit's threads stopped
            link_monitor.check_once()
            deadline = time.time() + 5
            while link_monitor.reconnecting(self.ids[slot]) and time.time() < deadline:
                time.sleep(0.01)
        finally:
            if real is not None:
                sys.modules["dronekit"].connect = real
        return made

    def test_dead_link_reconnects_on_same_slot_order_unchanged(self):
        old = state.vehicles[self.lost]
        others = [v for v in state.vehicles if v is not old]
        made = self.reconnect_with(lambda k: FakeVehicle(self.ids[self.lost]))
        self.assertEqual(state.pos_array, self.ids)
        self.assertIs(state.vehicles[self.lost], made[-1])
        self.assertEqual(made[-1]._heartbeat_error, 0)
        self.assertTrue(old.closed)
        self.assertEqual([v for v in state.vehicles if v is not made[-1]], others)

    def test_wrong_aircraft_on_the_port_is_refused(self):
        wrong = max(self.ids) + 1
        made = self.reconnect_with(lambda k: FakeVehicle(wrong if k == 0 else self.ids[self.lost]))
        self.assertTrue(made[0].closed)
        self.assertIs(state.vehicles[self.lost], made[1])

    def test_uav_removed_while_reconnecting_is_left_out(self):
        sys_id = self.ids[self.lost]

        def make(k):
            with state.swarm_topology_lock:  # operator removes it meanwhile
                idx = state.pos_array.index(sys_id)
                state.pos_array.pop(idx)
                state.vehicles.pop(idx)
            return FakeVehicle(sys_id)

        made = self.reconnect_with(make)
        self.assertNotIn(sys_id, state.pos_array)
        self.assertTrue(made[0].closed)


class AddDoesNotFreezeTheSwarm(unittest.TestCase):
    def test_connect_runs_without_the_locks_and_keeps_the_slot(self):
        ids = sorted(rng.sample(range(1, 15), 4))
        state.master_flag = True
        state.pos_array = list(ids)
        state.vehicles = [FakeVehicle(s) for s in ids]
        target = rng.choice(ids)
        release, entered = threading.Event(), threading.Event()

        def slow_connect(endpoint, **kw):
            entered.set()
            release.wait(5)
            return FakeVehicle(target)

        real_connect, real_resync = management.connect, management._resync_bot_position
        management.connect = slow_connect
        management._resync_bot_position = lambda i, force=False: None
        try:
            t = threading.Thread(target=management.add_uav_to_swarm, args=(target,))
            t.start()
            self.assertTrue(entered.wait(5))
            got = state.active_goal_tasks_lock.acquire(timeout=1)  # the runner's lock
            self.assertTrue(got, "add held the task lock while connecting")
            state.active_goal_tasks_lock.release()
            release.set()
            t.join(5)
        finally:
            management.connect, management._resync_bot_position = real_connect, real_resync
        self.assertEqual(state.pos_array, ids)
        self.assertEqual(state.vehicles[ids.index(target)]._master.target_system, target)
        self.assertEqual(state.vehicles[ids.index(target)]._heartbeat_error, 0)


class PlotWindows(unittest.TestCase):
    def test_leftover_windows_are_closed(self):
        import matplotlib.pyplot as plt
        from swarm_tasks.simulation import visualizer as viz

        for _ in range(rng.randint(1, 3)):
            plt.figure()
        viz.close_leftover_windows()
        self.assertEqual(plt.get_fignums(), [])


class Wiring(unittest.TestCase):
    def src(self, *parts):
        return open(os.path.join(HERE, "..", *parts), encoding="utf-8").read()

    def test_every_bot_driver_checks_the_link(self):
        for parts in [("tasks", "runner.py"), ("tasks", "search.py"), ("tasks", "split.py"),
                      ("tasks", "navigate.py")]:
            self.assertIn("link_monitor.ready(i)", self.src(*parts), parts)

    def test_main_loop_closes_leftover_windows(self):
        self.assertIn("viz.close_leftover_windows()", self.src("main.py"))

    def test_mavlink_listens_on_every_interface(self):
        self.assertEqual(state.ip, "0.0.0.0")
        self.assertTrue(connection.connection_string_for_sysid(next(iter(config.PORT_DICT))).startswith("udpin:0.0.0.0:"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
