"""Server-side geofence gate: goal / auto-goal / search / split commands outside
the drawn fence are refused before anything is sent to the swarm computer.
Fences and points are random on every run.

Run:  python3 test_server_fence_guard.py
"""

import math
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *[".."] * 6))
sys.path.insert(0, os.path.join(REPO, "Xag-Server", "src"))

from flockwave.server import fence_guard  # noqa: E402

rng = random.SystemRandom()
M_PER_DEG = 111320.0


class Guard(unittest.TestCase):
    def setUp(self):
        # A random square fence, side 2..20 km, given as [lat, lon] (what the
        # fence handler passes after reversing the GUI's [lon, lat]).
        self.lat0, self.lon0 = rng.uniform(-60, 60), rng.uniform(-170, 170)
        self.side_m = rng.uniform(2000, 20000)
        dlat = self.side_m / M_PER_DEG
        dlon = self.side_m / (M_PER_DEG * math.cos(math.radians(self.lat0)))
        self.dlat, self.dlon = dlat, dlon
        fence_guard.set_outer_fence(
            [[self.lat0, self.lon0], [self.lat0 + dlat, self.lon0],
             [self.lat0 + dlat, self.lon0 + dlon], [self.lat0, self.lon0 + dlon]]
        )
        self.centre = (self.lat0 + dlat / 2, self.lon0 + dlon / 2)

    def tearDown(self):
        fence_guard._outer = None

    def gui(self, lat, lon):  # the GUI sends [lon, lat]
        return [lon, lat]

    def test_goal_inside_passes_outside_is_refused(self):
        inside = [self.centre, (self.lat0 + self.dlat * 0.1, self.lon0 + self.dlon * 0.9)]
        self.assertIsNone(fence_guard.check_points(inside, "goal"))
        outside = inside + [(self.lat0 + self.dlat * 1.2, self.lon0 + self.dlon / 2)]
        res = fence_guard.check_points(outside, "goal")
        self.assertEqual(res, "out_of_boundary|Command not sent: goal point 3 is outside the geofence")

    def test_search_area_must_fit(self):
        small = self.side_m * 0.5
        self.assertIsNone(fence_guard.check_areas([self.centre], small, "search"))
        self.assertTrue(fence_guard.check_areas([self.centre], self.side_m * 1.2, "search").startswith("out_of_boundary"))
        # centre inside but its square crosses the edge
        near_edge = (self.lat0 + self.dlat * 0.05, self.centre[1])
        self.assertTrue(fence_guard.check_areas([near_edge], small, "search").startswith("out_of_boundary"))

    def test_split_names_the_area_outside(self):
        far = (self.lat0 - self.dlat, self.lon0)
        res = fence_guard.check_areas([self.centre, far], self.side_m * 0.1, "split")
        self.assertIn("split area 2 is outside", res)

    def test_autogoal_checks_every_generated_centre(self):
        # 3 UAVs, east from the centre: spacing = 2r + margin
        r = self.side_m * 0.05
        ok = fence_guard.check_autogoal([self.gui(*self.centre)], 3, r, 90, 0)
        self.assertIsNone(ok)  # 4r east of centre = 0.2*side: still inside
        many = int(self.side_m / (2 * r)) + 2  # enough UAVs to run past the east edge
        res = fence_guard.check_autogoal([self.gui(*self.centre)], many, r, 90, 0)
        self.assertIn("auto-goal point", res)

    def test_autogoal_blank_fields_use_the_same_defaults(self):
        self.assertIsNone(fence_guard.check_autogoal([self.gui(*self.centre)], 1, None, None, None))
        self.assertIsNone(fence_guard.check_autogoal(None, 2, 100, 90, 50))  # malformed: not this gate's call

    def test_loiter_circle_must_fit(self):
        r = rng.uniform(100, 600)
        reach = r + fence_guard.LOITER_MARGIN_M
        mid_lon = self.lon0 + self.dlon / 2
        close = (self.lat0 + reach * rng.uniform(0.1, 0.9) / M_PER_DEG, mid_lon)
        roomy = (self.lat0 + (reach + rng.uniform(20, 200)) / M_PER_DEG, mid_lon)
        self.assertIsNone(fence_guard.check_loiter([self.centre, roomy], r, "final goal"))
        res = fence_guard.check_loiter([close], r, "final goal")
        self.assertTrue(res.startswith("out_of_boundary|Command not sent: final goal point 1 is too close"))
        self.assertIn("%.0f m + %.0f m margin" % (r, fence_guard.LOITER_MARGIN_M), res)
        self.assertIsNotNone(fence_guard.check_loiter([close], -r, "final goal"))  # anticlockwise sign

    def test_autogoal_centre_too_close_for_its_circle(self):
        r = rng.uniform(100, 600)
        near_south = (self.lat0 + (r * 0.5) / M_PER_DEG, self.centre[1])
        res = fence_guard.check_autogoal([self.gui(*near_south)], 1, r, 90, 50)
        self.assertIn("auto-goal point 1 is too close", res)

    def test_no_fence_drawn_means_no_check(self):
        fence_guard._outer = None
        self.assertIsNone(fence_guard.check_points([(0.0, 0.0)], "goal"))
        self.assertIsNone(fence_guard.check_areas([(0.0, 0.0)], 1e6, "search"))


class Wiring(unittest.TestCase):
    """Each handler checks BEFORE it sends anything (incl. stop_socket)."""

    def setUp(self):
        self.src = open(os.path.join(REPO, "Xag-Server", "src", "flockwave", "server", "app.py"), encoding="utf-8").read()

    def block(self, msg):
        start = self.src.index('if msg == "%s":' % msg)
        return self.src[start:self.src.index("\n        if msg ==", start + 10)]

    def test_check_comes_before_any_send(self):
        for msg, sender in [("goal", "goal_socket("), ("autogoal", "autogoal_socket("),
                            ("search", "search_socket("), ("groupsplit", "splitmission("),
                            ("spificsplit", "specificsplit(")]:
            b = self.block(msg)
            self.assertIn("fence_guard.check_", b, msg)
            self.assertLess(b.index("fence_guard.check_"), b.index(sender), msg)
            if "stop_socket()" in b:
                self.assertLess(b.index("fence_guard.check_"), b.index("stop_socket()"), msg)

    def test_goal_checks_the_loiter_circle_of_the_final_point_before_sending(self):
        b = self.block("goal")
        self.assertIn("fence_guard.check_loiter(", b)
        self.assertLess(b.index("fence_guard.check_loiter("), b.index("goal_socket("))
        self.assertIn('[-1:]', b[b.index("check_loiter("):b.index("goal_socket(")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
