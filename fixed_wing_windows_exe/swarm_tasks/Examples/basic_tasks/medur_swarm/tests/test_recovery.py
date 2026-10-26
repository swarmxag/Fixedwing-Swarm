"""Heartbeat, durable replication, failover reconciliation, stale epochs and the
idle-standby CPU fix -- real router, real nodes (real main loop).

Run:  python3 test_recovery.py
"""

import json
import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as h
from harness import command_status, link, wait_for, wait_status


class Failover(unittest.TestCase):
    extra2 = None  # env overrides for node 2

    def setUp(self):
        self.tmp = h.tmpdir()
        link.COMMAND_LOG.clear()
        self.router = h.make_router(self.tmp, (1, 2))
        self.n1 = h.Node(1, self.tmp).start(self.router)
        self.n2 = h.Node(2, self.tmp, **(self.extra2 or {})).start(self.router)
        self.fail_list = link.collect_failures()

    def tearDown(self):
        self.n1.kill()
        self.n2.kill()

    def role(self, n):
        st = self.router.probe(n) or {}
        return st.get("role"), st.get("promoting")

    def promote(self, n):
        res = self.router.set_master(n)
        self.assertTrue(res["ok"], res)
        self.assertTrue(wait_for(lambda: self.role(n) == ("master", False)), "never became master")
        return res

    def flying_master_1(self):
        """Master 1 has goal tasks for bots 0 and 1; standby 2 holds a replica."""
        self.promote(1)
        self.assertTrue(self.router.send("bg:0"))
        self.assertTrue(self.router.send("bg:1"))
        wait_status("bg:1", "running")
        rep = self.router.replicate_once()
        self.assertTrue(rep["ok"], rep)
        self.assertEqual(rep["delivered"], {2: True})
        self.assertEqual(rep["tasks"], 2)

    # ---- heartbeat + replication -------------------------------------------
    def test_replica_is_stored_durably_on_the_standby(self):
        self.flying_master_1()
        st = self.router.probe(2)
        self.assertEqual(st["replica_epoch"], 1)
        self.assertGreaterEqual(st["replica_version"], 1)
        saved = json.load(open(os.path.join(self.tmp, "node2_replica.json")))
        self.assertEqual(sorted(saved["tasks"]), ["0", "1"])
        self.assertEqual(saved["uav_ids"], [1, 2])
        self.assertEqual(saved["epoch"], 1)
        self.assertTrue(saved["tasks"]["0"]["goals"])           # active task content
        self.assertIn("guided_circle_radius", saved["tasks"]["0"])  # guided-circle state
        self.assertTrue(any(c["cmd"] == "bg:1" for c in saved["commands"]))  # command status
        # survives a standby restart
        self.n2.kill()
        self.n2 = h.Node(2, self.tmp).start(self.router)
        self.assertEqual(self.router.probe(2)["replica_epoch"], 1)

    def test_lost_master_is_flagged_but_never_auto_promoted(self):
        self.flying_master_1()
        self.assertFalse(self.router.master_lost)
        self.n1.kill()
        for _ in range(3):
            self.assertIsNone(self.router.replicate_once())
        self.assertTrue(self.router.master_lost)
        self.assertEqual(self.router.master, 1)                    # operator must confirm
        self.assertEqual(self.role(2)[0], "standby")
        self.assertTrue(self.router.status(probe=False)["master_health"]["lost"])

    def test_stale_snapshot_and_stale_epoch_are_refused_by_standby(self):
        self.flying_master_1()
        before = self.router.probe(2)["replica_version"]
        snap = self.router.links[1].call("snapshot", self.router.address(1, "cmd"))["data"]
        link2 = self.router.links[2]
        addr = self.router.address(2, "cmd")
        old = dict(snap, version=snap["version"] - 1)
        self.assertEqual(link2.call("replicate", addr, epoch=1, snap=old)["why"], "already_have_newer")
        low_epoch = dict(snap, epoch=0, version=snap["version"] + 10)
        self.assertEqual(link2.call("replicate", addr, epoch=1, snap=low_epoch)["why"], "stale_epoch")
        self.assertFalse(link2.call("replicate", addr, epoch=0, snap=snap)["ok"])  # epoch-fenced
        self.assertEqual(link2.call("replicate", addr, epoch=1, snap="junk")["why"], "bad_snapshot")
        self.assertEqual(self.router.probe(2)["replica_version"], before)  # nothing stale was stored

    def test_master_refuses_to_be_overwritten_by_a_replica(self):
        self.promote(1)
        r = self.router.links[1].call("replicate", self.router.address(1, "cmd"), epoch=1, snap={"schema": 1})
        self.assertEqual(r["why"], "i_am_master")

    # ---- failover reconciliation -------------------------------------------
    def test_promotion_reconciles_but_does_not_replay(self):
        self.flying_master_1()
        self.assertTrue(self.router.send("fg:30"))                 # outcome unknown at failure time
        wait_status("fg:30", "started")
        self.router.replicate_once()
        self.n1.kill()
        self.promote(2)
        st = self.router.probe(2)
        self.assertEqual(st["active_tasks"], 0)                    # nothing replayed on promotion
        self.assertEqual(st["recovery"]["resumable"], 2)
        self.assertGreaterEqual(st["recovery"]["unknown_commands"], 1)  # fg:30 outcome unknown
        self.assertEqual(self.n2.executed(), [])                    # no flight command ran

    def test_operator_confirmed_resume_reassigns_only_verified_goals(self):
        self.flying_master_1()
        self.n1.kill()
        self.promote(2)
        res = self.router.resume_recovery()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["resumable"], 2)
        self.assertTrue(wait_for(lambda: (self.router.probe(2) or {}).get("active_tasks") == 2))
        wait_status("recover_resume", "running", node=2)           # the new tasks are being flown

    def test_resume_refused_on_stale_version(self):
        self.flying_master_1()
        self.n1.kill()
        self.promote(2)
        self.assertTrue(self.router.send("recover_resume,999"))    # transport ok ...
        time.sleep(0.5)
        self.assertEqual(self.router.probe(2)["active_tasks"], 0)  # ... but nothing resumed

    def test_nothing_to_recover_without_replica(self):
        self.promote(1)
        self.n1.kill()
        self.promote(2)
        self.assertEqual(self.router.resume_recovery()["reason"], "nothing_to_recover")


class FailoverStaleReplica(Failover):
    extra2 = {"extra_env": {"SWARM_RECOVER_MAX_AGE": "0.5"}}

    def test_stale_replica_is_discarded_not_resumed(self):
        self.flying_master_1()
        self.n1.kill()
        time.sleep(1.0)
        self.promote(2)
        st = self.router.probe(2)
        self.assertEqual(st["recovery"]["resumable"], 0)
        res = self.router.resume_recovery()
        time.sleep(0.5)
        self.assertEqual(self.router.probe(2)["active_tasks"], 0)

    # the inherited tests assume a long max-age; skip them in this stricter variant
    for _n in [n for n in dir(Failover) if n.startswith("test_")]:
        locals()[_n] = None
    del _n


class FailoverWrongMode(Failover):
    extra2 = {"mode": "LOITER"}

    def test_uav_not_in_guided_mode_needs_operator(self):
        self.flying_master_1()
        self.n1.kill()
        self.promote(2)
        st = self.router.probe(2)
        self.assertEqual(st["recovery"]["resumable"], 0)
        self.assertEqual(st["recovery"]["needs_operator"], 2)
        self.router.resume_recovery()
        time.sleep(0.5)
        self.assertEqual(self.router.probe(2)["active_tasks"], 0)

    for _n in [n for n in dir(Failover) if n.startswith("test_")]:
        locals()[_n] = None
    del _n


class ReconcilePure(unittest.TestCase):
    """reconcile() rules, no processes."""

    @classmethod
    def setUpClass(cls):
        import stubs

        stubs.install()
        from medur_swarm.communication import replica

        cls.replica = replica

    def snap(self, **over):
        s = {"schema": 1, "node": 1, "epoch": 1, "version": 3, "taken_at": 1000.0, "uav_ids": [4, 5],
             "tasks": {"0": {"type": "goal", "goals": [[0, 0], [1, 1]], "goal_index": 0},
                       "1": {"type": "mission", "line_index": 7, "num_lines": 40}},
             "commands": [{"cmd": "split_x", "status": "running"}, {"cmd": "goal_y", "status": "completed"}]}
        s.update(over)
        return s

    def live(self, over=None):
        over = over or {}
        t = {4: {"connected": True, "mode": "GUIDED", "armed": True}, 5: {"connected": True, "mode": "GUIDED", "armed": True}}
        t.update(over)
        return t

    def verdicts(self, r):
        return {t["uav"]: (t["verdict"], t["reasons"]) for t in r["tasks"]}

    def test_goal_resumable_mission_never(self):
        r = self.replica.reconcile(self.snap(), self.live(), now=1005.0)
        v = self.verdicts(r)
        self.assertEqual(v[4][0], "resumable")
        self.assertEqual(v[5][0], "needs_reissue")                  # search/split are never auto-resumed
        self.assertEqual(r["resumable"], 1)
        self.assertEqual([c["cmd"] for c in r["unknown_commands"]], ["split_x"])

    def test_stale_replica_discards_everything(self):
        r = self.replica.reconcile(self.snap(), self.live(), now=1100.0, max_age=30)
        self.assertEqual(r["resumable"], 0)
        self.assertTrue(all(t["verdict"] in ("discard", "needs_reissue") for t in r["tasks"]))

    def test_disconnected_disarmed_or_wrong_mode(self):
        r = self.replica.reconcile(self.snap(), self.live({4: {"connected": False}}), now=1005.0)
        self.assertEqual(self.verdicts(r)[4][0], "discard")
        r = self.replica.reconcile(self.snap(), self.live({4: {"connected": True, "mode": "GUIDED", "armed": False}}), now=1005.0)
        self.assertIn("not_armed", self.verdicts(r)[4][1])
        r = self.replica.reconcile(self.snap(), self.live({4: {"connected": True, "mode": "RTL", "armed": True}}), now=1005.0)
        self.assertEqual(self.verdicts(r)[4][0], "needs_reissue")

    def test_finished_goal_not_resumed(self):
        s = self.snap()
        s["tasks"]["0"]["goal_index"] = 2
        r = self.replica.reconcile(s, self.live(), now=1005.0)
        self.assertEqual(self.verdicts(r)[4][0], "discard")

    def test_no_replica(self):
        self.assertEqual(self.replica.reconcile(None, {})["resumable"], 0)


class StandbyIdle(unittest.TestCase):
    def test_standby_wait_does_not_spin_a_core(self):
        code = (
            "import sys,threading,time\n"
            "sys.path.insert(0, %r)\n"
            "import stubs; stubs.install()\n"
            "from medur_swarm import state\n"
            "import medur_swarm.main as m\n"
            "state.uav_home_pos = []\n"
            "t = threading.Thread(target=m._bring_up_simulation, daemon=True); t.start()\n"
            "time.sleep(0.3); c0 = time.process_time(); time.sleep(2.0)\n"
            "print('CPU', time.process_time() - c0)\n" % h.HERE
        )
        env = dict(os.environ, SWARM_STATE_DIR=h.tempfile.mkdtemp(), SWARM_CMD_PORT="12298", SWARM_CTL_PORT="12292")
        out = subprocess.run([sys.executable, "-W", "ignore", "-c", code], env=env, capture_output=True, text=True, timeout=60)
        cpu = float([l for l in out.stdout.splitlines() if l.startswith("CPU")][0].split()[1])
        self.assertLess(cpu, 0.3, "standby spun the CPU: %.2fs in 2s" % cpu)


if __name__ == "__main__":
    unittest.main(verbosity=2)
