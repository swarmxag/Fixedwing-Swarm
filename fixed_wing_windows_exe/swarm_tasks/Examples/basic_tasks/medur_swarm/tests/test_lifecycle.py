"""Execution lifecycle: transport ACK vs real execution, against the REAL
main loop. Also: preemption, cancel by stop, failure, background task
completion, duplicate delivery, restart recovery, Stop routing regression and
unsupported-command rejection.

Run:  python3 test_lifecycle.py
"""

import json
import os
import socket
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as h
from harness import command_status, link, wait_for, wait_status


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = h.tmpdir()
        link.COMMAND_LOG.clear()
        self.router = h.make_router(self.tmp, (1,))
        self.node = h.Node(1, self.tmp).start(self.router)
        res = self.router.set_master(1)
        self.assertTrue(res["ok"], res)
        self.assertTrue(wait_for(lambda: (self.router.probe(1) or {}).get("role") == "master"))
        self.fail_list = link.collect_failures()

    def tearDown(self):
        self.node.kill()

    def send(self, text):
        self.assertTrue(self.router.send(text), self.fail_list)

    def test_foreground_command_completes_only_after_it_ran(self):
        self.send("fg:0.6")
        wait_status("fg:0.6", "started")
        self.assertNotEqual(command_status("fg:0.6")[0], "completed")  # ACK is not completion
        wait_status("fg:0.6", "completed")

    def test_failure_is_reported_not_swallowed(self):
        self.send("fail")
        status, why = wait_status("fail", "failed")
        self.assertIn("boom", why)

    def test_foreground_preempted_by_newer_command(self):
        self.send("fg:5")
        wait_status("fg:5", "started")
        self.send("quick")
        wait_status("fg:5", "preempted")
        wait_status("quick", "completed")

    def test_stop_cancels_foreground_and_background(self):
        self.send("bg:0")
        wait_status("bg:0", "running")
        self.send("fg:5")
        wait_status("fg:5", "started")
        self.send("stop")
        wait_status("fg:5", "cancelled")
        wait_status("bg:0", "cancelled")
        wait_status("stop", "completed")
        self.assertEqual(self.router.probe(1)["active_tasks"], 0)

    def test_background_command_is_running_then_completes_when_tasks_end(self):
        self.send("bg:0")
        status, why = wait_status("bg:0", "running")
        self.assertEqual(self.router.probe(1)["active_tasks"], 1)
        time.sleep(0.3)
        self.assertEqual(command_status("bg:0")[0], "running")  # not "completed" while UAV is still flying
        self.send("finishbg:0")
        wait_status("bg:0", "completed")

    def test_fully_replaced_background_task_is_preempted(self):
        self.send("bg:0")
        wait_status("bg:0", "running")
        self.send("bg:0")  # same bot, newer command
        hits = [c for c in link.recent_commands(50) if c["cmd"] == "bg:0"]
        self.assertTrue(wait_for(lambda: [c["status"] for c in link.recent_commands(50) if c["cmd"] == "bg:0"][:2] == ["preempted", "running"]), hits)

    def test_partially_replaced_task_finishes_truthfully(self):
        self.send("bgmulti:0,1")
        wait_status("bgmulti:0,1", "running")
        self.send("bg:0")
        self.send("finishbg:1")
        self.send("finishbg:0")
        status, why = wait_status("bgmulti:0,1", "completed")
        self.assertIn("partially_preempted", why)

    def test_duplicate_delivery_executes_once(self):
        env = json.dumps({"k": "cmd", "v": 1, "sid": "dup1", "seq": 1, "epoch": self.router.epoch, "p": "dupcmd"}).encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        for _ in range(3):
            s.sendto(env, self.router.address(1, "cmd"))
            self.assertTrue(json.loads(s.recvfrom(65535)[0])["ok"])
        time.sleep(0.5)
        self.assertEqual(self.node.executed().count(b"dupcmd"), 1)

    def test_restart_marks_in_flight_command_interrupted(self):
        self.send("fg:30")
        wait_status("fg:30", "started")
        self.node.kill()  # crash mid-mission
        self.node = h.Node(1, self.tmp).start(self.router)
        status, why = wait_status("fg:30", "interrupted")
        self.assertEqual(why, "receiver_restart")
        # journal compaction keeps the record, marked terminal
        journal = os.path.join(self.tmp, "node1_journal.jsonl")
        last = {}
        for line in open(journal):
            r = json.loads(line)
            last[(r["sid"], r["seq"])] = r["status"]
        self.assertNotIn("started", last.values())

    def test_unsupported_commands_are_rejected_not_acked(self):
        for text in ("clear_csv", "remove_bot,1", "share_data,x"):
            self.assertFalse(self.router.send(text))
            self.assertEqual(self.fail_list[-1]["reason"], "unsupported_command")
            self.assertEqual(command_status(text)[0], "rejected")
        self.assertEqual(self.node.executed(), [])

    def test_clear_csv_broadcast_reports_failure(self):
        res = self.router.send_all("clear_csv")
        self.assertEqual(res, {1: "not_delivered"})


class StopRouting(unittest.TestCase):
    """explicit_stop() must reach BOTH the control and the command port."""

    def test_explicit_stop_sends_both_signals(self):
        sys.path.insert(0, os.path.join(h.REPO, "Xag-Server", "src"))
        import flockwave.server.swarm as swarm

        sent = []

        class Recorder:
            def sendto(self, data, kind):
                sent.append((data, kind))
                return True

        real = swarm.master_udp
        swarm.master_udp = Recorder()
        try:
            self.assertTrue(swarm.explicit_stop())
            self.assertEqual(sent, [(b"stop", "ctl"), (b"stop", "cmd")])
            sent.clear()
            swarm.stop_socket()  # the precursor other commands send: control port only
            self.assertEqual(sent, [(b"stop", "ctl")])
        finally:
            swarm.master_udp = real

    def test_stop_fails_if_either_leg_is_lost(self):
        sys.path.insert(0, os.path.join(h.REPO, "Xag-Server", "src"))
        import flockwave.server.swarm as swarm

        class Half:
            def sendto(self, data, kind):
                return kind == "ctl"

        real = swarm.master_udp
        swarm.master_udp = Half()
        try:
            self.assertFalse(swarm.explicit_stop())
        finally:
            swarm.master_udp = real


class HomeHandler(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(h.REPO, "Xag-Server", "src"))
        import flockwave.server.swarm as swarm

        self.parse = swarm.parse_rtl_height

    def test_valid(self):
        self.assertEqual(self.parse({}), (50.0, None))  # optional, defaults
        self.assertEqual(self.parse({"rtl_height": "75.5"}), (75.5, None))
        self.assertEqual(self.parse({"rtl_height": 120}), (120.0, None))

    def test_invalid(self):
        for bad in (-5, 0, "abc", None, float("nan"), 5000, [], {}):
            self.assertEqual(self.parse({"rtl_height": bad}), (None, "invalid_rtl_height"), bad)

    def test_handler_no_longer_calls_dict_pop_without_key(self):
        src = open(os.path.join(h.REPO, "Xag-Server", "src", "flockwave", "server", "app.py"), encoding="utf-8").read()
        code = [l for l in src.splitlines() if not l.strip().startswith("#")]
        self.assertFalse([l for l in code if "parameters.pop()" in l])
        self.assertIn("parse_rtl_height(parameters)", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
