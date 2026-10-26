"""Routing / master-selection / failover gate. Two real receivers (real
sockets.py + reliable.py, flight deps stubbed) on 127.0.0.1 and 127.0.0.2
behave as two onboard computers; the real server Router drives them.

Run:  python3 test_router.py
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PKG, *[".."] * 5))
LINK = os.path.join(REPO, "Xag-Server", "src", "flockwave", "server", "swarm_link.py")

spec = importlib.util.spec_from_file_location("swarm_link_r", LINK)
link = importlib.util.module_from_spec(spec)
sys.modules["swarm_link_r"] = link
spec.loader.exec_module(link)

PORTS = {1: (12008, 12002), 2: (12018, 12012)}
IPS = {1: "127.0.0.1", 2: "127.0.0.2"}


class Node:
    def __init__(self, node_id, busy=0.0):
        self.id, self.busy = node_id, busy
        self.out = tempfile.mktemp(suffix=".log")
        open(self.out, "wb").close()
        self.proc = None

    def start(self):
        env = dict(os.environ, SWARM_NODE_ID=str(self.id), SWARM_CMD_PORT=str(PORTS[self.id][0]),
                   SWARM_CTL_PORT=str(PORTS[self.id][1]))
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "transport_receiver.py"), self.out, str(self.busy)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert self.proc.stdout.readline().strip() == b"READY", self.proc.stderr.read()
        return self

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()
            self.proc.stdout.close()
            self.proc.stderr.close()
            self.proc = None

    def got(self, wait=0.4):
        time.sleep(wait)
        with open(self.out, "rb") as f:
            return [l for l in f.read().split(b"\n") if l]


def make_router(tmp):
    nodes = {str(i): {"ip": IPS[i], "cmd_port": PORTS[i][0], "ctl_port": PORTS[i][1]} for i in (1, 2)}
    nf = os.path.join(tmp, "nodes.json")
    json.dump({"nodes": nodes}, open(nf, "w"))
    return link.Router(nodes_file=nf, state_file=os.path.join(tmp, "master.json")), nf


def wait_for(fn, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        if fn():
            return True
        time.sleep(0.05)
    return False


GOAL = "goal_[[1.0,2.0]]_1_50_[1]"


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.n1, self.n2 = Node(1).start(), Node(2).start()
        self.router, self.nodes_file = make_router(self.tmp)
        self.fail = link.collect_failures()

    def tearDown(self):
        self.n1.stop()
        self.n2.stop()

    def role_of(self, node):
        st = self.router.probe(node)
        return None if st is None else ("promoting" if st.get("promoting") else st.get("role"))

    def promote(self, node):
        res = self.router.set_master(node)
        self.assertTrue(res["ok"], res)
        self.assertTrue(wait_for(lambda: self.role_of(node) == "master"), "node never reported master")
        return res

    def test_no_master_means_refused_not_lost(self):
        self.assertFalse(self.router.send("search,1,2,3,4,[],[1]"))
        self.assertEqual(self.fail[-1]["reason"], "no_master_selected")
        self.assertEqual(self.n1.got(0.2) + self.n2.got(0.0), [])

    def test_nodes_start_standby_and_report_their_own_state(self):
        st = self.router.status()
        self.assertEqual([n["status"]["role"] for n in st["nodes"]], ["standby", "standby"])
        self.assertTrue(all(n["reachable"] for n in st["nodes"]))

    def test_commands_go_to_master_only(self):
        self.promote(1)
        self.assertTrue(self.router.send(GOAL))
        self.assertEqual(self.n1.got(), [GOAL.encode()])
        self.assertEqual(self.n2.got(0.0), [])

    def test_standby_refuses_mission_command_directly(self):
        self.promote(1)
        ok = self.router.links[2].sendto(GOAL.encode(), self.router.address(2, "cmd"), self.router.epoch)
        self.assertFalse(ok)
        self.assertEqual(self.fail[-1]["reason"], "not_master")
        self.assertEqual(self.n2.got(), [])

    def test_origin_goes_to_every_node_and_is_validated(self):
        res = self.router.send_all("origin,12.5,77.5")
        self.assertEqual(res, {1: True, 2: True})
        self.assertEqual(self.n1.got(), [b"origin,12.5,77.5"])
        self.assertEqual(self.n2.got(0.0), [b"origin,12.5,77.5"])
        res = self.router.send_all("origin,999,0")
        self.assertEqual(res, {1: "not_delivered", 2: "not_delivered"})
        self.assertIn("invalid_origin", [f["reason"] for f in self.fail])

    def test_unregistered_target_refused(self):
        self.promote(1)
        self.assertFalse(self.router.send("goal_[[1.0,2.0]]_1_50_[9]"))
        self.assertIn("unregistered_uav", self.fail[-1]["reason"])

    def test_failover_fences_old_master(self):
        self.promote(1)
        res = self.promote(2)
        self.assertEqual((res["epoch"], res["old_master_demoted"]), (2, True))
        self.assertEqual(self.role_of(1), "standby")
        self.assertTrue(self.router.send(GOAL))
        self.assertEqual(self.n2.got(), [GOAL.encode()])
        self.assertEqual(self.n1.got(0.0), [])
        # a delayed command from the old epoch is refused even by the (re)promoted-looking node
        ok = self.router.links[1].sendto(GOAL.encode(), self.router.address(1, "cmd"), 1)
        self.assertFalse(ok)
        self.assertEqual(self.fail[-1]["reason"], "stale_epoch")

    def test_failover_when_old_master_is_down_then_it_returns(self):
        self.promote(1)
        self.n1.stop()
        res = self.promote(2)
        self.assertFalse(res["old_master_demoted"])
        self.assertEqual(self.router.pending_demotions, {1})
        self.n1.start()  # restarts as standby, epoch 0
        self.router.status()  # retries the demotion
        self.assertEqual(self.router.pending_demotions, set())
        self.assertEqual(self.role_of(1), "standby")
        self.assertEqual(self.role_of(2), "master")

    def test_ineligible_candidate_changes_nothing(self):
        self.promote(1)
        self.n2.stop()
        res = self.router.set_master(2)
        self.assertEqual((res["ok"], res["reasons"]), (False, ["unreachable"]))
        self.assertEqual((self.router.master, self.router.epoch), (1, 1))
        self.assertEqual(self.role_of(1), "master")
        res = self.router.set_master(7)
        self.assertEqual(res["reasons"], ["not_registered"])

    def test_epoch_survives_server_restart(self):
        self.promote(1)
        again, _ = make_router(self.tmp)
        self.assertEqual((again.master, again.epoch), (1, 1))

    def test_superseded_goal_gets_terminal_status(self):
        self.n1.stop()
        self.n1 = Node(1, busy=0.6).start()
        self.promote(1)
        self.assertTrue(self.router.send("add,1"))              # consumed, receiver now "busy"
        time.sleep(0.15)
        self.assertTrue(self.router.send("remove,1"))           # promoted to mailbox, unread
        self.assertTrue(self.router.send(GOAL))                 # pending behind it
        self.assertTrue(self.router.send(GOAL.replace("50", "75")))  # newer goal, same UAV set
        time.sleep(0.5)
        by_cmd = {c["cmd"]: c for c in link.recent_commands(50)}
        self.assertEqual(by_cmd[GOAL[:48]]["status"], "superseded")
        self.assertEqual(by_cmd[GOAL[:48]]["why"], "newer_goal")
        got = self.n1.got(2.5)
        self.assertEqual(got.count(GOAL.encode()), 0)           # the superseded plan never flew
        self.assertIn(GOAL.replace("50", "75").encode(), got)
        self.assertEqual(got[:2], [b"add,1", b"remove,1"])      # ordering of other commands kept

    def test_invalid_node_table_refuses_to_route(self):
        with open(self.nodes_file, "w") as f:
            json.dump({"nodes": {"1": {"ip": "10.0.0.1"}, "2": {"ip": "10.0.0.1"}}}, f)
        bad = link.Router(nodes_file=self.nodes_file, state_file=os.path.join(self.tmp, "m2.json"))
        self.assertIn("duplicate ip", bad.load_error)
        self.assertFalse(bad.send("stop"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
