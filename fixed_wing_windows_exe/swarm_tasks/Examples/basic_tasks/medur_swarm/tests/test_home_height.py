"""Home flies the commanded height, not a table of its own, and only the height
changed: the point it flies to is the one guidance gives, as before.

Run:  python3 test_home_height.py
"""

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

import locatePosition  # noqa: E402

from medur_swarm import config, state  # noqa: E402
from medur_swarm.tasks import home  # noqa: E402

TARGET = (10.0, 20.0)


class FakeVehicle:
    def __init__(self):
        self.commanded = None

    def simple_goto(self, point):
        self.commanded = point


class HomeHeight(unittest.TestCase):
    def setUp(self):
        self.saved = (
            state.master_flag, state.vehicles, state.origin, state.same_alt_flag,
            state.same_height, list(state.different_height),
        )
        self.paced = []
        self.saved_helpers = (
            home.advance_bot_with_uav_pacing, home.pursuit_target_with_avoidance,
            home.LocationGlobalRelative,
        )
        home.advance_bot_with_uav_pacing = lambda i, b, goal, label: self.paced.append((i, goal, label))
        home.pursuit_target_with_avoidance = lambda i, b: TARGET
        home.LocationGlobalRelative = lambda lat, lon, alt: (lat, lon, alt)
        state.master_flag = True
        state.origin = (26.0, 70.0)
        state.vehicles = [FakeVehicle(), FakeVehicle(), FakeVehicle()]
        state.same_alt_flag = False
        state.different_height[:3] = [100, 110, 120]

    def tearDown(self):
        (
            state.master_flag, state.vehicles, state.origin, state.same_alt_flag,
            state.same_height, heights,
        ) = self.saved
        state.different_height[:] = heights
        (
            home.advance_bot_with_uav_pacing, home.pursuit_target_with_avoidance,
            home.LocationGlobalRelative,
        ) = self.saved_helpers

    def drive(self, i):
        home._drive_home_leg(i, SimpleNamespace(x=0.0, y=0.0), (1.0, 2.0))
        return state.vehicles[i].commanded

    def test_flies_each_uavs_commanded_height(self):
        self.assertEqual([self.drive(i)[2] for i in range(3)], [100, 110, 120])

    def test_flies_the_shared_height_after_same(self):
        state.same_alt_flag = True
        state.same_height = 150
        self.assertEqual([self.drive(i)[2] for i in range(3)], [150, 150, 150])

    def test_stays_with_its_uav_when_one_ahead_is_removed(self):
        # removal compacts vehicles and different_height together
        state.different_height[:2] = [100, 120]
        state.vehicles = [FakeVehicle(), FakeVehicle()]
        self.assertEqual(self.drive(1)[2], 120)

    def test_only_the_height_changed(self):
        lat, lon = locatePosition.cartToGeo(
            state.origin, config.END_DISTANCE, (TARGET[0] * 2, TARGET[1] * 2)
        )
        self.assertEqual(self.drive(0)[:2], (lat, lon))
        self.assertEqual(self.paced, [(0, (1.0, 2.0), "home")])

    def test_no_home_table_left(self):
        self.assertFalse(hasattr(config, "HOME_HEIGHT"))


if __name__ == "__main__":
    unittest.main()
