"""Geofence first: origin/geofence are applied the moment they arrive while the
swarm program is still starting up (not after the arming wait), a node without
a geofence cannot take over, and an out-of-range origin no longer stops the
start-up. Real router, real nodes, real start-up wait; values random per run.

Run:  python3 test_geofence_first.py
"""

import base64
import os
import random
import subprocess
import sys
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as h
from harness import link, wait_for

rng = random.SystemRandom()


def make_yaml():
    x, y = rng.randint(50, 90000), rng.randint(50, 90000)
    return "name: Rectangles\nsize:\n  x: %d\n  y: %d\n\nobstacles:\n  - [[1,1],[2,1],[2,2]]\norigin: (%f, %f)" % (
        x, y, rng.uniform(-60, 60), rng.uniform(-170, 170))


class StartingNode(unittest.TestCase):
    def setUp(self):
        self.tmp = h.tmpdir()
        link.COMMAND_LOG.clear()
        self.router = h.make_router(self.tmp, (1,))
        env = {"HARNESS_REAL_BRINGUP": "1", "HARNESS_NO_FENCE": "1"}
        self.node = h.Node(1, self.tmp, extra_env=env).start(self.router)

    def tearDown(self):
        self.node.kill()

    def stored(self):
        try:
            return open(os.path.join(self.tmp, "node1_rectangles.yaml"), encoding="utf-8").read()
        except OSError:
            return None

    def test_no_takeover_before_a_geofence(self):
        self.assertIs(self.router.probe(1)["fence_ready"], False)
        check = self.router.eligibility(1)
        self.assertIn("no_geofence", check["reasons"])
        self.assertFalse(self.router.set_master(1)["ok"])
        self.assertEqual(self.router.probe(1)["role"], "standby")

    def test_geofence_applied_immediately_then_takeover_allowed(self):
        text = make_yaml()
        lat, lon = round(rng.uniform(-60, 60), 6), round(rng.uniform(-170, 170), 6)
        self.assertEqual(self.router.send_all("origin,%s,%s" % (lat, lon)), {1: True})
        msg = "geofence," + base64.b64encode(text.encode()).decode()
        self.assertEqual(self.router.send_all(msg), {1: True})
        # applied while the node is still in its start-up wait -- not queued
        self.assertTrue(wait_for(lambda: (self.router.probe(1) or {}).get("fence_ready") is True))
        self.assertEqual(self.stored(), text)
        self.assertEqual(h.command_status("geofence,", node=1), ("completed", "applied_before_start"))
        self.assertEqual(h.command_status("origin,", node=1), ("completed", "applied_before_start"))
        self.assertEqual(self.node.executed(), [])  # the command loop never had to run
        self.assertEqual(self.router.eligibility(1)["reasons"], [])
        self.assertTrue(self.router.set_master(1)["ok"])
        self.assertTrue(wait_for(lambda: (self.router.probe(1) or {}).get("role") == "master"))

    def test_bad_geofence_is_reported_not_applied(self):
        self.router.send_all("geofence,@@@not-base64@@@")
        self.assertTrue(wait_for(lambda: h.command_status("geofence,", node=1)[0] == "failed"))
        self.assertIs(self.router.probe(1)["fence_ready"], False)
        self.assertIsNone(self.stored())


class RunningNode(unittest.TestCase):
    """Once the command loop runs, origin goes through the queue exactly as before."""

    def test_origin_goes_through_the_command_loop(self):
        tmp = h.tmpdir()
        router = h.make_router(tmp, (1,))
        node = h.Node(1, tmp).start(router)
        try:
            self.assertTrue(router.set_master(1)["ok"])
            self.assertTrue(wait_for(lambda: (router.probe(1) or {}).get("role") == "master"))
            self.assertTrue(router.send("origin,12.5,77.5"))
            self.assertTrue(wait_for(lambda: b"origin,12.5,77.5" in node.executed()))
        finally:
            node.kill()


class StartupSurvivesOldOrigin(unittest.TestCase):
    def test_out_of_range_origin_waits_instead_of_stopping(self):
        code = textwrap.dedent(
            """
            import sys, types
            sys.path.insert(0, %r)
            import stubs; stubs.install()
            from medur_swarm import state
            import medur_swarm.main as m
            m.time.sleep = lambda s: None
            calls = []
            def fetch():
                calls.append(1)
                if len(calls) == 1:
                    raise ValueError("A value (26.39) in x_new is above the interpolation range")
                state.uav_home_pos = [(1.0, 2.0)]
            m.uav_connection.vehicle_connection = lambda: None
            m.uav_connection.fetch_location = fetch
            m.uav_management.register_active_uavs = lambda: None
            v = types.SimpleNamespace(armed=True, location=types.SimpleNamespace(
                global_relative_frame=types.SimpleNamespace(lat=26.39, lon=70.9, alt=20.0)))
            state.vehicles = [v]
            state.master_flag = True
            m._bring_up_master()
            print("RETURNED", len(calls), state.uav_home_pos)
            """
        ) % h.HERE
        env = dict(os.environ, SWARM_STATE_DIR=h.tempfile.mkdtemp(), SWARM_CMD_PORT="12698", SWARM_CTL_PORT="12692")
        out = subprocess.run([sys.executable, "-W", "ignore", "-c", code], env=env, capture_output=True, text=True, timeout=60)
        self.assertIn("RETURNED 2 [(1.0, 2.0)]", out.stdout, out.stderr[-1500:])
        self.assertIn("give the geofence", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
