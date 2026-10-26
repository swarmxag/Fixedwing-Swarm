"""Transport gate: port binding, duplicates, lost acks, large messages, stale
epochs, receiver restart, sender reconnect, FIFO queue + stop.

Run:  python3 test_transport.py      (Ubuntu / NUC or Windows)
"""

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PKG, *[".."] * 5))
LINK = os.path.join(REPO, "Xag-Server", "src", "flockwave", "server", "swarm_link.py")
RELIABLE = os.path.join(PKG, "communication", "reliable.py")
CMD = ("127.0.0.1", 12008)
CTL = ("127.0.0.1", 12002)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


link = load("swarm_link_t", LINK)


class Receiver:
    def __init__(self, busy=0.0):
        self.out = tempfile.mktemp(suffix=".log")
        open(self.out, "wb").close()
        self.busy = busy
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "transport_receiver.py"), self.out, str(self.busy)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        line = self.proc.stdout.readline().strip()
        assert line == b"READY", self.proc.stderr.read()
        return self

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()
            self.proc = None

    def got(self, wait=0.4):
        time.sleep(wait)
        return [l for l in open(self.out, "rb").read().split(b"\n") if l]


class Transport(unittest.TestCase):
    def setUp(self):
        self.r = Receiver().start()
        self.u = link.ReliableUdp(timeout=0.15, retries=4)
        self.failures = link.collect_failures()

    def tearDown(self):
        self.r.stop()

    def test_port_binding_conflict_is_detected(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with self.assertRaises(OSError):  # a 2nd swarm process on a host must fail loudly
            s.bind(("", 12008))
        s.close()

    def test_normal_and_control_port(self):
        self.assertTrue(self.u.sendto(b"goal_[[1,2]]_1_50_[]", CMD))
        self.assertTrue(self.u.sendto(b"master-3", CTL))
        self.assertIn(b"goal_[[1,2]]_1_50_[]", self.r.got())

    def test_duplicate_envelope_executes_once(self):
        env = json.dumps({"k": "cmd", "v": 1, "sid": "dupsid", "seq": 1, "epoch": 0, "p": "search,1"}).encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        acks = []
        for _ in range(3):
            s.sendto(env, CMD)
            acks.append(json.loads(s.recvfrom(2048)[0]))
        self.assertTrue(all(a["ok"] for a in acks))
        self.assertEqual(acks[1]["why"], "duplicate")
        self.assertEqual(self.r.got().count(b"search,1"), 1)

    def test_lost_ack_retransmit_still_exactly_once(self):
        proxy = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        proxy.bind(("127.0.0.1", 0))
        fwd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        fwd.settimeout(0.5)
        swallowed = [2]

        def run():
            while True:
                try:
                    d, client = proxy.recvfrom(65535)
                except OSError:
                    return
                fwd.sendto(d, CMD)
                try:
                    ack, _ = fwd.recvfrom(2048)
                except socket.timeout:
                    continue
                if swallowed[0] > 0:
                    swallowed[0] -= 1
                    continue
                proxy.sendto(ack, client)

        threading.Thread(target=run, daemon=True).start()
        self.assertTrue(self.u.sendto(b"split_x", proxy.getsockname()))
        proxy.close()
        self.assertEqual(self.r.got().count(b"split_x"), 1)

    def test_large_message(self):
        big = b"search," + b"9" * 50000
        self.assertTrue(self.u.sendto(big, CMD))
        self.assertIn(big, self.r.got(0.8))

    def test_stale_epoch_refused_in_separate_process(self):
        # reliable.set_epoch is process-local, so exercise it on the module directly.
        rel = load("reliable_t", RELIABLE)
        out = []

        class S:
            def sendto(self, data, addr):
                out.append(json.loads(data))

        def env(epoch, seq):
            return json.dumps({"k": "cmd", "sid": "s", "seq": seq, "epoch": epoch, "p": "x"}).encode()

        rel.set_epoch(3)
        self.assertIsNone(rel.unwrap(env(2, 1), ("a", 1), S()))
        self.assertEqual(out[-1]["why"], "stale_epoch")
        self.assertFalse(out[-1]["ok"])
        self.assertEqual(rel.unwrap(env(3, 2), ("a", 1), S()), b"x")

    def test_receiver_restart(self):
        self.assertTrue(self.u.sendto(b"before", CMD))
        time.sleep(0.3)  # ACK means "queued in receiver memory"; let it run before the crash
        self.r.stop()
        time.sleep(0.2)
        self.assertFalse(self.u.sendto(b"during_outage", CMD))  # reported, never silently lost
        self.assertEqual(self.failures[-1]["reason"], "no_ack")
        self.r.start()
        self.assertTrue(self.u.sendto(b"after", CMD))  # same sender session, receiver dedup state reset
        self.assertEqual(self.r.got(), [b"before", b"after"])

    def test_sender_reconnect_new_session(self):
        self.assertTrue(self.u.sendto(b"one", CMD))
        u2 = link.ReliableUdp(timeout=0.15, retries=3)  # server restart => seq restarts at 1
        self.assertTrue(u2.sendto(b"two", CMD))
        self.assertEqual(self.r.got(), [b"one", b"two"])

    def test_fifo_not_overwritten_while_busy_and_stop_clears(self):
        self.r.stop()
        time.sleep(0.3)
        self.r = Receiver(busy=0.5).start()
        self.assertTrue(self.u.sendto(b"c1", CMD))
        time.sleep(0.2)  # c1 is now being "flown"
        for p in (b"c2", b"c3", b"c4"):
            self.assertTrue(self.u.sendto(p, CMD))
        self.assertTrue(self.u.sendto(b"stop", CMD))
        got = self.r.got(1.5)
        self.assertEqual(got[0], b"c1")  # running command is never overwritten
        self.assertIn(b"stop", got)
        self.assertNotIn(b"c4", got)  # superseded by stop


if __name__ == "__main__":
    unittest.main(verbosity=2)
