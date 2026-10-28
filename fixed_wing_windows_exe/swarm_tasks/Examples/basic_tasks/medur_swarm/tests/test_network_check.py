"""CHECK_network_connection must not abort a promotion when config.HEARTBEAT_IP
has fewer addresses than there are heartbeat-timeout slots.

Run:  python3 test_network_check.py
"""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class NetworkCheck(unittest.TestCase):
    def test_fewer_heartbeat_ips_than_slots_does_not_abort_promotion(self):
        code = textwrap.dedent(
            """
            import sys
            sys.path.insert(0, %r)
            import stubs; stubs.install()
            from medur_swarm import config, state
            from medur_swarm.communication import sockets
            sockets.os.system = lambda cmd: 0
            config.HEARTBEAT_IP = ["10.0.0.1", "10.0.0.2"]
            state.heartbeat_ip_timeout = [5] * 15
            sockets.CHECK_network_connection()
            print("OK", state.heartbeat_ip_timeout[:3])
            """
        ) % HERE
        env = dict(os.environ, SWARM_STATE_DIR=tempfile.mkdtemp(), SWARM_CMD_PORT="12398", SWARM_CTL_PORT="12392")
        out = subprocess.run([sys.executable, "-W", "ignore", "-c", code], env=env, capture_output=True, text=True, timeout=60)
        self.assertIn("OK [30, 30, 5]", out.stdout, out.stderr[-1500:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
