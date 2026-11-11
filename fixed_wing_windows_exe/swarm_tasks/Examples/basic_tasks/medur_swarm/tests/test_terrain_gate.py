"""terrain_gate: the home datum is compared at the vehicle's own home, and the
stated minimum altitude covers the whole route. Uses a synthetic SRTM tile.

Run:  python3 test_terrain_gate.py
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("SWARM_CMD_PORT", "12698")
os.environ.setdefault("SWARM_CTL_PORT", "12692")
os.environ.setdefault("SWARM_STATE_DIR", tempfile.mkdtemp())
sys.path.insert(0, HERE)
import stubs  # noqa: E402

stubs.install()

from medur_swarm import state, terrain_check as tc, terrain_gate as gate  # noqa: E402

SIZE = 1201  # 3 arc-second tile


def row(lat):
    return int(round((27 - lat) * (SIZE - 1)))


def col(lon):
    return int(round((lon - 70) * (SIZE - 1)))


def write_tile(directory):
    """Flat 300 m, a ridge of 400 m on the first leg, one of 700 m on the second,
    and a 400 m hill at the origin (a corner of the fence)."""
    heights = np.full((SIZE, SIZE), 300, dtype=">i2")
    heights[row(26.32) : row(26.28), col(70.28) : col(70.32)] = 400
    heights[row(26.62) : row(26.58), col(70.58) : col(70.62)] = 700
    heights[row(26.02) : row(26.0) + 1, col(70.0) : col(70.02) + 1] = 400
    heights.tofile(os.path.join(directory, "N26E070.hgt"))


def vehicle(home_location, home_amsl=300.0, rel_alt=150.0):
    return SimpleNamespace(
        home_location=home_location,
        location=SimpleNamespace(
            global_relative_frame=SimpleNamespace(lat=26.1, lon=70.1, alt=rel_alt),
            global_frame=SimpleNamespace(alt=home_amsl + rel_alt),
        ),
    )


def run_quietly(function, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = function(*args)
    return result, out.getvalue()


class TerrainGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.mkdtemp()
        write_tile(cls.directory)

    def setUp(self):
        gate.TERRAIN_DIR = self.directory
        gate.reset()
        gate._datum_warned.clear()
        state.master_flag = True
        state.pos_array = [1]
        state.origin = (26.01, 70.01)  # on the 400 m hill
        state.same_alt_flag = True
        state.same_height = 150
        state.different_height = [150]
        state.active_goal_tasks = {}
        state.active_goal_tasks_lock = threading.Lock()
        self.own_home = SimpleNamespace(lat=26.1, lon=70.1)

    def frames(self, *args, **kwargs):
        state.vehicles = [vehicle(*args, **kwargs)]
        return run_quietly(gate._vehicle_frames, 0)

    def test_terrain_at_the_origin_does_not_replace_a_correct_datum(self):
        (home_amsl, _, _), _ = self.frames(self.own_home)
        self.assertEqual(home_amsl, 300.0)

    def test_wrong_datum_is_replaced_by_the_terrain_at_the_uavs_own_home(self):
        (home_amsl, _, _), printed = self.frames(self.own_home, home_amsl=5.0)
        self.assertEqual(home_amsl, 300.0)
        self.assertIn("at its home", printed)

    def test_datum_within_tolerance_of_own_home_is_kept(self):
        (home_amsl, _, _), _ = self.frames(self.own_home, home_amsl=320.0)
        self.assertEqual(home_amsl, 320.0)

    def test_unknown_home_position_keeps_the_vehicles_datum(self):
        (home_amsl, _, _), _ = self.frames(None, home_amsl=5.0)
        self.assertEqual(home_amsl, 5.0)

    def test_stated_minimum_altitude_covers_every_leg(self):
        state.vehicles = [vehicle(self.own_home)]
        goals = [(26.3, 70.3), (26.6, 70.6)]
        (ok, _), printed = run_quietly(gate.check_goals, [0], goals)
        self.assertTrue(ok)  # still advisory only
        stated = float(re.search(r"at least (\d+) m", printed).group(1))
        expected = tc.route_msa(gate._get_db(), 300.0, (26.1, 70.1), goals, 200)[0]
        self.assertEqual(stated, round(expected))
        self.assertEqual(stated, 521)

    def test_altitude_change_states_the_altitude_for_the_remaining_goals_too(self):
        state.vehicles = [vehicle(self.own_home)]
        original = gate._remaining_task_goals
        gate._remaining_task_goals = lambda i: [(26.6, 70.6)]
        try:
            (ok, _), printed = run_quietly(gate.check_altitude_change, {0: 150.0})
        finally:
            gate._remaining_task_goals = original
        self.assertTrue(ok)
        self.assertEqual(float(re.search(r"at least (\d+) m", printed).group(1)), 521)


if __name__ == "__main__":
    unittest.main()
