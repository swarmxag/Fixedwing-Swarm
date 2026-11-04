"""A final goal whose loiter circle (live WP_LOITER_RAD + margin) would leave the
fence is refused on the swarm computer; points that are only flown through keep
the plain inside check. Fence, radius and positions are random on every run.

Run:  python3 test_loiter_fence.py
"""

import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("SWARM_CMD_PORT", "12698")
os.environ.setdefault("SWARM_CTL_PORT", "12692")
os.environ.setdefault("SWARM_STATE_DIR", tempfile.mkdtemp())
sys.path.insert(0, HERE)
import stubs  # noqa: E402

stubs.install()

import locatePosition  # noqa: E402
from shapely.geometry import box  # noqa: E402

from medur_swarm import boundary, config, state  # noqa: E402
from medur_swarm.tasks import runner  # noqa: E402

rng = random.SystemRandom()
M_PER_DEG = 111320.0


class LoiterInsideFence(unittest.TestCase):
    def setUp(self):
        self.lat0, self.lon0 = rng.uniform(-50, 50), rng.uniform(-170, 170)
        self.side_m = rng.uniform(4000, 15000)
        self.dlat = self.side_m / M_PER_DEG
        state.origin = (self.lat0, self.lon0)
        x1, y1 = self.xy(self.lat0 + self.dlat, self.lon0 + self.dlat)
        state.s = type("Sim", (), {})()
        state.s.env = type("Env", (), {})()
        state.s.env.fence = box(0, 0, x1, y1)  # sim frame, same conversion as the flight
        self.radius = rng.uniform(100, 600)
        self.real_radius = runner._uav_loiter_radius_m
        runner._uav_loiter_radius_m = lambda i: self.radius  # the UAV's live WP_LOITER_RAD
        state.active_goal_tasks.clear()

    def tearDown(self):
        runner._uav_loiter_radius_m = self.real_radius
        state.origin = None
        state.active_goal_tasks.clear()

    def xy(self, lat, lon):
        """Sim frame, exactly as goal.py builds goal points: geoToCart / 2."""
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
        return (float(x) / 2, float(y) / 2)

    def north_of_south_edge(self, metres):
        """A point `metres` inside the south fence edge, half way along it."""
        return self.xy(self.lat0 + metres / M_PER_DEG, self.lon0 + self.dlat / 2)

    def reach(self):
        return self.radius + config.GEOFENCE_LOITER_MARGIN_M

    def test_final_goal_near_edge_refused_with_nothing_assigned(self):
        too_close = self.north_of_south_edge(self.reach() * rng.uniform(0.1, 0.9))
        centre = self.north_of_south_edge(self.side_m / 2)
        with self.assertRaises(boundary.FenceViolation) as e:
            runner.assign_goal_tasks([0], [centre, too_close])
        self.assertIn("loiter circle", str(e.exception))
        self.assertEqual(state.active_goal_tasks, {})

    def test_final_goal_with_room_for_the_circle_accepted(self):
        far_enough = self.north_of_south_edge(self.reach() + rng.uniform(20, 200))
        runner.assign_goal_tasks([0], [far_enough])
        self.assertEqual(state.active_goal_tasks[0]["goals"], [far_enough])

    def test_intermediate_point_near_edge_is_only_flown_through(self):
        near = self.north_of_south_edge(self.reach() * 0.5)
        centre = self.north_of_south_edge(self.side_m / 2)
        runner.assign_goal_tasks([0], [near, centre])  # loiter is around `centre`
        self.assertEqual(state.active_goal_tasks[0]["goals"], [near, centre])

    def test_biggest_live_radius_of_the_selected_uavs_counts(self):
        point = self.north_of_south_edge(self.reach() + 30)
        radii = {0: self.radius, 1: self.radius + 100}
        runner._uav_loiter_radius_m = lambda i: radii[i]
        runner.assign_goal_tasks([0], [point])
        with self.assertRaises(boundary.FenceViolation):
            runner.assign_goal_tasks([0, 1], [point])

    def test_autogoal_each_centre_and_the_layout_radius(self):
        ok = self.north_of_south_edge(self.reach() + 30)
        bad = self.north_of_south_edge(self.reach() * 0.5)
        runner.assign_autogoal_tasks([0], [ok], self.radius, 1)
        with self.assertRaises(boundary.FenceViolation):
            runner.assign_autogoal_tasks([0, 1], [ok, bad], self.radius, 1)
        with self.assertRaises(boundary.FenceViolation):  # radius change ahead of WP_LOITER_RAD
            runner.assign_autogoal_tasks([0], [ok], self.radius + 100, 1)

    def test_1000m_radius_needs_1050m_not_double(self):
        # Field report: radius 1000 m, goals 1000-1500 m from the fence refused,
        # only ~2000 m accepted (the circle was tested at twice its size).
        self.radius = 1000.0
        runner.assign_goal_tasks([0], [self.north_of_south_edge(1500.0)])  # 1500 >= 1050: accepted
        runner.assign_goal_tasks([0], [self.north_of_south_edge(1100.0)])
        with self.assertRaises(boundary.FenceViolation):
            runner.assign_goal_tasks([0], [self.north_of_south_edge(1000.0)])  # 1000 < 1050

    def test_no_fence_or_origin_means_no_check(self):
        state.origin = None
        runner.assign_goal_tasks([0], [(1.0, 1.0)])
        self.assertIn(0, state.active_goal_tasks)


if __name__ == "__main__":
    unittest.main(verbosity=2)
