"""The geofence refresh carries the rectangles.yaml text to the onboard computer.
Values are random on every run: nothing under test may depend on them.

Run:  python3 test_geofence_payload.py
"""

import base64
import os
import random
import subprocess
import sys
import tempfile
import textwrap
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *[".."] * 6))
rng = random.SystemRandom()


def make_yaml():
    x, y = rng.randint(50, 90000), rng.randint(50, 90000)
    walls = "".join(
        "  - [[%.2f,%.2f],[%.2f,%.2f],[%.2f,%.2f]]\n" % tuple(rng.uniform(0, 1000) for _ in range(6))
        for _ in range(rng.randint(1, 4))
    )
    origin = "(%f, %f)" % (rng.uniform(-60, 60), rng.uniform(-170, 170))
    return "name: Rectangles\nsize:\n  x: %d\n  y: %d\n\nobstacles:\n%sorigin: %s" % (x, y, walls, origin)


class ServerMessage(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(REPO, "Xag-Server", "src"))
        import flockwave.server.swarm as swarm

        self.swarm = swarm

    def test_message_carries_the_exact_yaml(self):
        text = make_yaml()
        msg = self.swarm._geofence_message(text)
        self.assertTrue(msg.startswith("geofence,"))
        self.assertEqual(base64.b64decode(msg[len("geofence,"):]).decode("utf-8"), text)

    def test_falls_back_to_the_plain_message(self):
        self.assertEqual(self.swarm._geofence_message(None), "geofence")
        self.assertEqual(self.swarm._geofence_message(""), "geofence")
        self.assertEqual(self.swarm._geofence_message("x" * (self.swarm.FENCE_MAX_BYTES + 1)), "geofence")

    def test_fits_in_one_datagram_at_the_limit(self):
        msg = self.swarm._geofence_message("x" * self.swarm.FENCE_MAX_BYTES)
        self.assertLess(len(msg), 60000)


class NodeSide(unittest.TestCase):
    """The real admin.reload_geofence, with its output folders redirected."""

    def run_node(self, body):
        tmp = tempfile.mkdtemp()
        code = textwrap.dedent(
            """
            import base64, os, sys, types
            sys.path.insert(0, %r)
            import stubs; stubs.install()
            from medur_swarm import config, state
            from medur_swarm.tasks import admin
            tmp = %r
            config.RECTANGLES_PATH = os.path.join(tmp, "swarm_env", "rectangles.yaml")
            worlds = os.path.join(tmp, "worlds"); os.makedirs(worlds)
            admin.sim.envs.world.worlds_path = worlds
            state.s = types.SimpleNamespace(env=types.SimpleNamespace(obstacles=None, size=None), size=None)
            def send(text):
                admin.reload_geofence(("geofence," + base64.b64encode(text.encode()).decode()).encode())
            """
        ) % (HERE, tmp) + textwrap.dedent(body)
        env = dict(os.environ, SWARM_STATE_DIR=tempfile.mkdtemp(), SWARM_CMD_PORT="12498", SWARM_CTL_PORT="12492")
        out = subprocess.run([sys.executable, "-W", "ignore", "-c", code], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-1500:])
        return tmp, out.stdout

    def test_received_yaml_is_stored_and_reloaded(self):
        text = make_yaml()
        tmp, out = self.run_node("send(%r)\nprint('SIZE', state.s.size, len(state.s.env.obstacles))" % text)
        self.assertEqual(open(os.path.join(tmp, "swarm_env", "rectangles.yaml"), encoding="utf-8").read(), text)
        self.assertEqual(open(os.path.join(tmp, "worlds", "rectangles.yaml"), encoding="utf-8").read(), text)
        world = yaml.safe_load(text)
        self.assertIn("SIZE (%d, %d) %d" % (world["size"]["x"], world["size"]["y"], len(world["obstacles"])), out)

    def test_each_new_geofence_replaces_the_previous_one(self):
        first, second = make_yaml(), make_yaml()
        tmp, _ = self.run_node("send(%r)\nsend(%r)" % (first, second))
        self.assertEqual(open(os.path.join(tmp, "swarm_env", "rectangles.yaml"), encoding="utf-8").read(), second)

    def test_invalid_data_never_replaces_the_current_file(self):
        good = make_yaml()
        tmp, _ = self.run_node(
            "send(%r)\n"
            "admin.reload_geofence(b'geofence,@@not base64@@')\n"
            "send('size: {x: 1}')\n"
            "send('just text')\n" % good
        )
        self.assertEqual(open(os.path.join(tmp, "swarm_env", "rectangles.yaml"), encoding="utf-8").read(), good)

    def test_plain_geofence_still_rereads_the_local_file(self):
        text = make_yaml()
        tmp, out = self.run_node(
            "os.makedirs(os.path.dirname(config.RECTANGLES_PATH))\n"
            "open(config.RECTANGLES_PATH, 'w').write(%r)\n"
            "admin.reload_geofence(b'geofence')\n"
            "print('SIZE', state.s.size)" % text
        )
        world = yaml.safe_load(text)
        self.assertIn("SIZE (%d, %d)" % (world["size"]["x"], world["size"]["y"]), out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
