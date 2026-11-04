"""Bots never cross a wall out of the fence; goals/paths outside the fence are
refused before anything is assigned; nothing else about bot motion changes.

Run:  python3 test_fence_walls.py
"""

import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("SWARM_CMD_PORT", "12598")
os.environ.setdefault("SWARM_CTL_PORT", "12592")
os.environ.setdefault("SWARM_STATE_DIR", tempfile.mkdtemp())
sys.path.insert(0, HERE)
import stubs  # noqa: E402

stubs.install()

import yaml  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402

import swarm_tasks.utils.robot as robot  # noqa: E402
from swarm_tasks.envs.world import fence_polygon  # noqa: E402
from swarm_tasks.simulation import simulation as sim  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, *[".."] * 6))
rng = random.SystemRandom()


def make_sim(start, fence=True):
    """Square fence 0..100 with a 5-unit wall on its east side (x 100..105)."""
    s = sim.Simulation([start], num_bots=1)
    s.size = s.env.size = (300, 300)
    s.env.obstacles = [Polygon([(100, -5), (105, -5), (105, 105), (100, 105)])]
    s.env.fence = box(0, 0, 100, 100) if fence else None
    return s


class WallCrossing(unittest.TestCase):
    def step(self, s, theta, length):
        b = s.swarm[0]
        b.theta = theta
        b.step(length)
        return b.x, b.y

    def test_long_step_cannot_jump_the_wall(self):
        s = make_sim((98, 50))
        self.assertEqual(self.step(s, 0.0, 20), (98, 50))  # would land at x=118, past the wall

    def test_steps_that_do_not_cross_a_wall_are_unchanged(self):
        for _ in range(20):
            x0, y0 = rng.uniform(10, 60), rng.uniform(10, 90)
            theta, length = rng.uniform(-3.1, 3.1), rng.uniform(0.1, 8)
            with_wall = make_sim((x0, y0))
            no_wall = make_sim((x0, y0))
            no_wall.env.obstacles = []
            self.assertEqual(self.step(with_wall, theta, length), self.step(no_wall, theta, length))

    def test_bot_outside_the_fence_can_come_back_in(self):
        s = make_sim((110, 50))  # aircraft turned wide; GPS resync put its bot outside
        x, y = self.step(s, 3.14159, 20)
        self.assertLess(x, 100)

    def test_bot_inside_a_wall_can_leave_it(self):
        s = make_sim((102, 50))
        x, _ = self.step(s, 3.14159, 5)
        self.assertLess(x, 100)

    def test_unstuck_case_still_cannot_cross(self):
        s = make_sim((98, 50))
        other = robot.Bot(98.2, 50.1)
        other.set_sim(s)
        s.swarm.append(other)  # current position "not free" -> old code allowed any move
        self.assertEqual(self.step(s, 0.0, 20), (98, 50))

    def test_old_world_file_without_fence_blocks_both_ways(self):
        s = make_sim((110, 50), fence=False)
        self.assertEqual(self.step(s, 3.14159, 20), (110, 50))


class FenceInWorldFile(unittest.TestCase):
    def build_yaml(self):
        sys.path.insert(0, os.path.join(REPO, "Xag-Server", "src", "flockwave", "server"))
        import YamlCreation

        lat0, lon0 = rng.uniform(-60, 60), rng.uniform(-170, 170)
        span = rng.uniform(0.005, 0.05)
        fence = [[lat0, lon0], [lat0 + span, lon0 + 0.2 * span], [lat0 + span, lon0 + span], [lat0, lon0 + span]]
        tmp = tempfile.mkdtemp()
        real = YamlCreation.FenceToYAML.get_documents_folder
        YamlCreation.FenceToYAML.get_documents_folder = staticmethod(lambda: tmp)  # never touch ~/Documents
        try:
            conv = YamlCreation.FenceToYAML(fence_coordinates=[fence], labels=["outer"])
            conv.process_fences()
            _, text = conv.generate_yaml(os.path.join(tmp, "r.yaml"))
        finally:
            YamlCreation.FenceToYAML.get_documents_folder = real
        return yaml.safe_load(text)

    def test_fence_outline_lines_up_with_the_walls(self):
        world = self.build_yaml()
        self.assertEqual(len(world["fence"]), len(world["obstacles"]))
        for i, wall in enumerate(world["obstacles"]):
            self.assertEqual(wall[0], world["fence"][i])  # wall i starts on fence vertex i

    def test_walls_lie_outside_the_fence(self):
        world = self.build_yaml()
        fence = fence_polygon(world)
        for wall in world["obstacles"]:
            self.assertLess(Polygon(wall).intersection(fence).area, 1e-3)

    def test_old_file_has_no_fence(self):
        self.assertIsNone(fence_polygon({"name": "x", "size": {"x": 1, "y": 1}, "obstacles": []}))


class RefusingCommands(unittest.TestCase):
    def setUp(self):
        from medur_swarm import boundary, state

        self.boundary, self.state = boundary, state
        state.s = make_sim((50, 50))
        state.active_goal_tasks.clear()

    def test_points_inside_pass_outside_refused(self):
        self.boundary.check_points([(10, 10), (99, 99), (0, 0)], "goal")
        with self.assertRaises(self.boundary.FenceViolation):
            self.boundary.check_points([(10, 10), (101, 50)], "goal")

    def test_no_fence_outline_means_no_check(self):
        self.state.s.env.fence = None
        self.boundary.check_points([(1000, 1000)], "goal")

    def test_goal_refused_before_any_task_changes(self):
        from medur_swarm.tasks import runner

        self.state.active_goal_tasks[0] = before = {"type": "goal", "goals": [(1, 1)]}
        with self.assertRaises(self.boundary.FenceViolation):
            runner.assign_goal_tasks([0], [(50, 50), (150, 50)])
        self.assertIs(self.state.active_goal_tasks[0], before)
        with self.assertRaises(self.boundary.FenceViolation):
            runner.assign_autogoal_tasks([0], [(150, 50)], 100, 1)
        self.assertIs(self.state.active_goal_tasks[0], before)
        runner.assign_goal_tasks([0], [(50, 50)])  # inside: accepted as before
        self.assertEqual(self.state.active_goal_tasks[0]["goals"], [(50, 50)])

    def test_refused_plan_restores_path_files_and_tasks(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "uav_7_path.csv")
        open(path, "w").write("10,10,False\n20,20,False\n")
        real = self.boundary.uav_path_csv
        self.boundary.uav_path_csv = lambda uav_id: os.path.join(tmp, "uav_%s_path.csv" % uav_id)
        try:
            self.state.active_goal_tasks[3] = task = {"type": "mission"}
            snap = self.boundary.snapshot([7], [3])
            self.state.active_goal_tasks.pop(3)  # what the search handler does before generating
            open(path, "w").write("10,10,False\n500,20,False\n")  # new plan leaves the fence
            with self.assertRaises(self.boundary.FenceViolation):
                self.boundary.check_csv_paths([path], "search", restore=snap)
            self.assertEqual(open(path).read(), "10,10,False\n20,20,False\n")
            self.assertIs(self.state.active_goal_tasks[3], task)
        finally:
            self.boundary.uav_path_csv = real

    def test_refused_concurrent_command_does_not_interrupt_running_mission(self):
        from medur_swarm.communication import dispatch, sockets
        from medur_swarm.tasks import goal

        real = goal.handle_concurrent_goal_command

        def refuse(_data):
            raise self.boundary.FenceViolation("goal: point 1 is outside the fence")

        goal.handle_concurrent_goal_command = refuse
        try:
            started = sockets.pending_command.seq
            sockets.pending_command.data = b"goal_[[0,0]]_1_100_[1]"
            sockets.pending_command.seq += 1
            self.assertIsNone(dispatch.check_for_new_command(started))  # no MissionPreempted
            self.assertEqual(self.state.last_seq, sockets.pending_command.seq)
            self.assertIsNone(dispatch.check_for_new_command(started))  # consumed, not retried
        finally:
            goal.handle_concurrent_goal_command = real


if __name__ == "__main__":
    unittest.main(verbosity=2)
