"""Shared helpers: real server Router + real swarm nodes (node_main.py)."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PKG, *[".."] * 5))
LINK = os.path.join(REPO, "Xag-Server", "src", "flockwave", "server", "swarm_link.py")

spec = importlib.util.spec_from_file_location("swarm_link_h", LINK)
link = importlib.util.module_from_spec(spec)
sys.modules["swarm_link_h"] = link
spec.loader.exec_module(link)

PORTS = {1: (12208, 12202), 2: (12218, 12212)}
IPS = {1: "127.0.0.1", 2: "127.0.0.2"}


class Node:
    def __init__(self, node_id, state_dir, uavs="1,2", mode="GUIDED", extra_env=None):
        self.id = node_id
        self.state_dir = state_dir
        self.log = os.path.join(state_dir, "node%d_exec.log" % node_id)
        self.out = os.path.join(state_dir, "node%d_stdout.txt" % node_id)
        open(self.log, "ab").close()
        self.env = dict(
            os.environ,
            SWARM_NODE_ID=str(node_id),
            SWARM_CMD_PORT=str(PORTS[node_id][0]),
            SWARM_CTL_PORT=str(PORTS[node_id][1]),
            SWARM_STATE_DIR=state_dir,
            HARNESS_LOG=self.log,
            HARNESS_UAVS=uavs,
            HARNESS_MODE=mode,
            PYTHONUNBUFFERED="1",
        )
        self.env.update(extra_env or {})
        self.proc = None

    def start(self, router=None, timeout=15):
        self._out = open(self.out, "ab")
        self.proc = subprocess.Popen(
            [sys.executable, "-W", "ignore", os.path.join(HERE, "node_main.py")],
            env=self.env, stdout=self._out, stderr=subprocess.STDOUT,
        )
        if router is not None:
            end = time.time() + timeout
            while time.time() < end:
                if self.proc.poll() is not None:
                    raise RuntimeError("node exited:\n" + self.output())
                if router.probe(self.id, timeout=0.2, retries=1) is not None:
                    return self
                time.sleep(0.2)
            raise RuntimeError("node never answered:\n" + self.output())
        return self

    def kill(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait()
        self.proc = None
        if getattr(self, "_out", None):
            self._out.close()

    stop = kill

    def output(self):
        try:
            return open(self.out, "rb").read().decode("utf-8", "replace")[-3000:]
        except OSError:
            return ""

    def executed(self):
        with open(self.log, "rb") as f:
            return [l for l in f.read().split(b"\n") if l]


def make_router(tmp, ids=(1,)):
    nodes = {str(i): {"ip": IPS[i], "cmd_port": PORTS[i][0], "ctl_port": PORTS[i][1]} for i in ids}
    nf = os.path.join(tmp, "nodes.json")
    json.dump({"nodes": nodes}, open(nf, "w"))
    return link.Router(nodes_file=nf, state_file=os.path.join(tmp, "master.json"), auto_replicate=False)


def wait_for(fn, timeout=6.0, step=0.05):
    end = time.time() + timeout
    while time.time() < end:
        if fn():
            return True
        time.sleep(step)
    return False


def command_status(prefix, node=None):
    """Latest server-side status of the newest command starting with prefix."""
    hits = [c for c in link.recent_commands(200) if c["cmd"].startswith(prefix) and (node is None or c["node"] == node)]
    return (hits[-1]["status"], hits[-1]["why"]) if hits else (None, None)


def wait_status(prefix, status, node=None, timeout=6.0):
    ok = wait_for(lambda: command_status(prefix, node)[0] == status, timeout)
    if not ok:
        raise AssertionError("command %r never reached %r; is %r" % (prefix, status, command_status(prefix, node)))
    return command_status(prefix, node)


def tmpdir():
    return tempfile.mkdtemp()
