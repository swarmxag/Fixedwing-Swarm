"""A search/split target never sits inside the aircraft's orbit circle, and a
target already far enough away is sent unchanged.

Run:  python3 test_target_outside_loiter.py
"""

import math
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("SWARM_CMD_PORT", "12798")
os.environ.setdefault("SWARM_CTL_PORT", "12792")
os.environ.setdefault("SWARM_STATE_DIR", tempfile.mkdtemp())
sys.path.insert(0, HERE)
import stubs  # noqa: E402

stubs.install()

from medur_swarm import state  # noqa: E402
from medur_swarm.uav.guidance import keep_target_outside_loiter  # noqa: E402

BOT = SimpleNamespace(x=100.0, y=0.0, theta=0.0)
# WP_LOITER_RAD 600 + margin 50 = 650 m = 325 sim units.
MIN_SIM = 325.0


class KeepTargetOutsideLoiter(unittest.TestCase):
    def setUp(self):
        state.master_flag = True
        state.vehicles = [SimpleNamespace(parameters={"WP_LOITER_RAD": 600})]

    def test_far_target_is_unchanged(self):
        self.assertEqual(keep_target_outside_loiter(0, BOT, 400.0, 5.0, 0.0, 0.0), (400.0, 5.0))

    def test_target_at_the_limit_is_unchanged(self):
        self.assertEqual(keep_target_outside_loiter(0, BOT, MIN_SIM, 0.0, 0.0, 0.0), (MIN_SIM, 0.0))

    def test_close_target_moves_out_along_the_same_line(self):
        tx, ty = keep_target_outside_loiter(0, BOT, 30.0, 40.0, 0.0, 0.0)
        self.assertAlmostEqual(math.hypot(tx, ty), MIN_SIM)
        self.assertAlmostEqual(math.atan2(ty, tx), math.atan2(40.0, 30.0))

    def test_uses_the_aircraft_position(self):
        tx, ty = keep_target_outside_loiter(0, BOT, 510.0, 500.0, 500.0, 500.0)
        self.assertAlmostEqual(math.hypot(tx - 500.0, ty - 500.0), MIN_SIM)

    def test_target_on_aircraft_aims_at_the_bot(self):
        self.assertEqual(keep_target_outside_loiter(0, BOT, 0.0, 0.0, 0.0, 0.0), (MIN_SIM, 0.0))

    def test_follows_a_live_radius_change(self):
        state.vehicles[0].parameters["WP_LOITER_RAD"] = 200
        tx, ty = keep_target_outside_loiter(0, BOT, 10.0, 0.0, 0.0, 0.0)
        self.assertEqual((tx, ty), (125.0, 0.0))


if __name__ == "__main__":
    unittest.main()
