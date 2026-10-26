"""Server -> swarm-computer link: reliable transport, node table, master routing.

Layers
------
* `ReliableUdp`  one per node. Stop-and-wait: every message is a sequenced JSON
  envelope that is retransmitted until the node ACKs it, so commands arrive in
  order and at most once. A reader thread also collects the node's later
  lifecycle events ("started", "superseded", "discarded"), so the GUI follows
  what the receiver actually did with a command.
* `Router`       the node table (UAV id -> NUC address), the active master, the
  fencing epoch, and every routing rule. Mission commands go to the active
  master only; origin/geofence/clear_csv go to every node; a master change is
  an operator-confirmed, eligibility-checked, epoch-fenced transition.

Receiver half: medur_swarm/communication/reliable.py (keep both in sync).

Node table file (JSON, `SWARM_NODES_FILE` or ~/Documents/swarm_env/swarm_nodes.json):

    {"cmd_port": 12008, "ctl_port": 12002,
     "nodes": {"1": {"ip": "192.168.6.101"}, "2": {"ip": "192.168.6.102"}}}

Without that file the router runs in LEGACY mode: one implicit node at
127.0.0.1, always the master -- the original single-computer behaviour.
"""

import collections
import concurrent.futures
import contextvars
import ipaddress
import json
import os
import socket
import threading
import time
import uuid

ACK_TIMEOUT = float(os.environ.get("SWARM_ACK_TIMEOUT", "0.25"))
RETRIES = int(os.environ.get("SWARM_RETRIES", "4"))
MAX_PAYLOAD = 60000
LEGACY_NODE = 0

_failures = contextvars.ContextVar("swarm_link_failures", default=None)


def collect_failures():
    """Start collecting delivery failures for the current request; returns
    the (initially empty) list that routed sends append to."""
    failures = []
    _failures.set(failures)
    return failures


def record_failure(node, address, reason, payload=""):
    print("[swarm_link] NOT DELIVERED to node %s %s: %s (%s)" % (node, address, reason, str(payload)[:60]))
    failures = _failures.get()
    if failures is not None:
        failures.append({"node": node, "address": "%s:%s" % tuple(address) if address else None, "reason": reason})


# --- command lifecycle log (what the receiver reports, not what we assume) ---

COMMAND_LOG = collections.OrderedDict()  # (node, sid, seq) -> dict
_log_lock = threading.Lock()
_LOG_MAX = 200


def _log_command(node, sid, seq, payload, status):
    with _log_lock:
        COMMAND_LOG[(node, sid, seq)] = {
            "node": node,
            "seq": seq,
            "cmd": str(payload)[:48],
            "status": status,
            "why": "",
            "ts": time.time(),
        }
        while len(COMMAND_LOG) > _LOG_MAX:
            COMMAND_LOG.popitem(last=False)


def _update_command(node, sid, seq, status, why=""):
    with _log_lock:
        entry = COMMAND_LOG.get((node, sid, seq))
        if entry is not None:
            entry["status"], entry["why"], entry["ts"] = status, why, time.time()


def recent_commands(limit=30):
    with _log_lock:
        return list(COMMAND_LOG.values())[-limit:]


class ReliableUdp:
    def __init__(self, timeout=ACK_TIMEOUT, retries=RETRIES, node=LEGACY_NODE):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("", 0))
        self._timeout = timeout
        self._retries = retries
        self.node = node
        self._sid = uuid.uuid4().hex[:12]
        self._seq = 0
        self._send_lock = threading.Lock()  # one exchange at a time => in-order delivery
        self._waiting = {}  # seq -> [threading.Event, reply]
        self.epoch = 0
        self.last_status = {}
        threading.Thread(target=self._reader, daemon=True).start()

    # -- receive side ------------------------------------------------------
    def _reader(self):
        while True:
            try:
                data, _src = self._sock.recvfrom(65535)
                msg = json.loads(data.decode("utf-8"))
            except (OSError, ValueError):
                continue  # e.g. ICMP port-unreachable surfaced by Windows
            if msg.get("sid") != self._sid:
                continue
            if msg.get("k") == "ack":
                slot = self._waiting.get(msg.get("seq"))
                if slot is not None:
                    slot[1] = msg
                    slot[0].set()
            elif msg.get("k") == "evt":
                _update_command(self.node, self._sid, msg.get("seq"), msg.get("st"), msg.get("why", ""))

    # -- send side ---------------------------------------------------------
    def _exchange(self, fields, address, epoch=None, timeout=None, retries=None):
        """Send one envelope, wait for its ACK. Returns the ACK dict or None."""
        timeout = self._timeout if timeout is None else timeout
        retries = self._retries if retries is None else retries
        with self._send_lock:
            self._seq += 1
            seq = self._seq
            msg = {"v": 1, "sid": self._sid, "seq": seq, "epoch": self.epoch if epoch is None else epoch}
            msg.update(fields)
            packet = json.dumps(msg, separators=(",", ":")).encode("utf-8")
            slot = [threading.Event(), None]
            self._waiting[seq] = slot
            try:
                for _ in range(retries):
                    self._sock.sendto(packet, address)
                    if slot[0].wait(timeout):
                        self.last_status = slot[1].get("st") or self.last_status
                        return dict(slot[1], seq=seq)
                return None
            finally:
                self._waiting.pop(seq, None)

    def sendto(self, data, address, epoch=None):
        """Deliver one command. True once ACKed; False (and a recorded
        failure) if the node never answered or refused it."""
        payload = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else str(data)
        if len(payload) > MAX_PAYLOAD:
            return self._fail(address, payload, "payload_too_large")
        ack = self._exchange({"k": "cmd", "p": payload}, address, epoch)
        if ack is None:
            return self._fail(address, payload, "no_ack")
        if not ack.get("ok"):
            return self._fail(address, payload, ack.get("why") or "rejected")
        _log_command(self.node, self._sid, ack["seq"], payload, "queued")
        return True

    def call(self, kind, address, epoch=None, timeout=None, retries=None, **fields):
        """Management exchange (ping / role). Returns the ACK dict or None;
        never records a delivery failure (callers interpret the result)."""
        return self._exchange(dict(fields, k=kind), address, epoch, timeout, retries)

    def _fail(self, address, payload, reason):
        record_failure(self.node, address, reason, payload)
        return False


# ---------------------------------------------------------------------------


def _target_ids(payload):
    """UAV ids a known command is aimed at (None = whole swarm / unknown)."""
    try:
        text = payload if isinstance(payload, str) else payload.decode("utf-8")
        if text.startswith(("goal_", "autogoalrad_")):
            ids = json.loads(text.rsplit("_", 1)[1])
        elif text.startswith("autogoal_"):
            ids = json.loads(text.rsplit("_", 3)[1])
        elif text.startswith("different,"):
            ids = json.loads(text.split(",", 3)[3])
        elif text.startswith("search,"):
            ids = json.loads(text.split(",", 6)[6])
        elif text.startswith("split_"):
            ids = json.loads(text.split("_")[2])
        elif text.startswith("specificsplit_"):
            ids = [i for group in json.loads(text.split("_")[2]) for i in group]
        elif text.startswith(("add,", "remove,", "remove_bot,")):
            ids = [int(text.split(",", 1)[1])]
        else:
            return None
        return [int(i) for i in ids] or None
    except (ValueError, IndexError, TypeError, UnicodeDecodeError):
        return None


class Router:
    def __init__(self, nodes_file=None, state_file=None):
        folder = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env")
        self._nodes_file = nodes_file or os.environ.get("SWARM_NODES_FILE") or os.path.join(folder, "swarm_nodes.json")
        self._state_file = state_file or os.path.join(folder, "swarm_master.json")
        self._lock = threading.RLock()
        self.nodes = {}  # uav id -> {"ip", "cmd", "ctl"}
        self.master = None
        self.epoch = 0
        self.pending_demotions = set()
        self.links = {}
        self.load_error = None
        self._load()

    # -- configuration -----------------------------------------------------
    @property
    def legacy(self):
        return LEGACY_NODE in self.nodes

    def _load(self):
        try:
            with open(self._nodes_file, encoding="utf-8") as f:
                cfg = json.load(f)
            cmd_port, ctl_port = int(cfg.get("cmd_port", 12008)), int(cfg.get("ctl_port", 12002))
            nodes, seen_ips = {}, set()
            for key, value in cfg["nodes"].items():
                uav_id, ip = int(key), str(ipaddress.ip_address(value["ip"]))
                if uav_id <= 0:
                    raise ValueError("node id must be positive: %s" % key)
                if ip in seen_ips:
                    raise ValueError("duplicate ip %s" % ip)
                seen_ips.add(ip)
                nodes[uav_id] = {"ip": ip, "cmd": int(value.get("cmd_port", cmd_port)), "ctl": int(value.get("ctl_port", ctl_port))}
            if not nodes:
                raise ValueError("no nodes")
            self.nodes = nodes
        except FileNotFoundError:
            self.nodes = {LEGACY_NODE: {"ip": "127.0.0.1", "cmd": 12008, "ctl": 12002}}
        except (ValueError, KeyError, TypeError, OSError) as e:
            self.load_error = "invalid node table %s: %r" % (self._nodes_file, e)
            print("[swarm_link]", self.load_error)
            self.nodes = {}  # refuse to guess: nothing is routable until fixed
        for uav_id in self.nodes:
            self.links[uav_id] = ReliableUdp(node=uav_id)
        if self.legacy and self.nodes:
            self.master = LEGACY_NODE
        else:
            self._load_state()

    def _load_state(self):
        try:
            with open(self._state_file, encoding="utf-8") as f:
                saved = json.load(f)
            self.epoch = int(saved.get("epoch", 0))
            master = saved.get("master")
            self.master = master if master in self.nodes else None
        except (OSError, ValueError, TypeError):
            pass

    def _save_state(self):
        os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
        tmp = self._state_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"master": self.master, "epoch": self.epoch}, f)
        os.replace(tmp, self._state_file)  # epoch must never go backwards across a restart

    # -- addressing --------------------------------------------------------
    def address(self, node, kind):
        n = self.nodes[node]
        return (n["ip"], n["cmd"] if kind == "cmd" else n["ctl"])

    # -- sending -----------------------------------------------------------
    def send(self, data, kind="cmd"):
        """Deliver a command to the ACTIVE MASTER only."""
        payload = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else str(data)
        if self.load_error:
            return self._refuse(payload, self.load_error)
        if self.master is None:
            return self._refuse(payload, "no_master_selected")
        targets = _target_ids(payload)
        if targets and not self.legacy:
            unknown = [i for i in targets if i not in self.nodes]
            if unknown:
                return self._refuse(payload, "unregistered_uav:%s" % unknown)
        return self.links[self.master].sendto(payload, self.address(self.master, kind), self.epoch)

    def _refuse(self, payload, reason):
        record_failure(self.master, None, reason, payload)
        return False

    def send_all(self, data, kind="cmd"):
        """Deliver to EVERY node (origin / geofence / clear_csv). Returns
        {node: True | reason}; failures are also recorded for the request."""
        payload = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else str(data)
        if not self.nodes:
            self._refuse(payload, self.load_error or "no_nodes")
            return {}
        results = {}

        def one(node):
            link = self.links[node]
            ok = link.sendto(payload, self.address(node, kind), self.epoch)
            return node, ok

        # Worker threads do not inherit the request's failure list, so collect
        # in the calling thread from the return values.
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.nodes)) as pool:
            futures = [pool.submit(contextvars.copy_context().run, one, n) for n in self.nodes]
            for fut in futures:
                node, ok = fut.result()
                results[node] = True if ok else "not_delivered"
        return results

    # -- liveness / eligibility -------------------------------------------
    def probe(self, node, timeout=0.2, retries=2):
        """Ask the node for its real state. None if it does not answer."""
        ack = self.links[node].call("ping", self.address(node, "cmd"), timeout=timeout, retries=retries)
        return None if ack is None else ack.get("st") or {}

    def eligibility(self, node):
        reasons = []
        status = None
        if self.legacy:
            reasons.append("legacy_mode_single_computer")
        elif node not in self.nodes:
            reasons.append("not_registered")
        else:
            status = self.probe(node)
            if status is None:
                reasons.append("unreachable")
            else:
                if status.get("legacy"):
                    reasons.append("node_not_in_decentralised_mode")
                if status.get("epoch", 0) > self.epoch:
                    reasons.append("node_epoch_ahead")
                if status.get("promoting"):
                    reasons.append("promotion_in_progress")
                if node == self.master and status.get("role") == "master":
                    reasons.append("already_master")
        return {"node": node, "eligible": not reasons, "reasons": reasons, "status": status}

    # -- master transition -------------------------------------------------
    def set_master(self, node):
        """Operator-confirmed, fenced master change. Nothing changes unless the
        candidate accepts the new epoch."""
        with self._lock:
            check = self.eligibility(node)
            if not check["eligible"]:
                return {"ok": False, "reason": "not_eligible", **check}
            new_epoch = self.epoch + 1
            old = self.master
            demoted = None
            if old is not None and old != node:
                ack = self.links[old].call("role", self.address(old, "cmd"), epoch=new_epoch, role="standby", node=old, timeout=0.3, retries=3)
                if ack is not None and not ack.get("ok"):
                    return {"ok": False, "reason": "old_master_refused_demotion:%s" % ack.get("why"), **check}
                demoted = ack is not None  # None = unreachable: assume down, fence by epoch, retry later
            ack = self.links[node].call("role", self.address(node, "cmd"), epoch=new_epoch, role="master", node=node, timeout=0.3, retries=4)
            if ack is None or not ack.get("ok"):
                return {"ok": False, "reason": "candidate_refused:%s" % (None if ack is None else ack.get("why")), "old_master_demoted": demoted, **check}
            self.master, self.epoch = node, new_epoch
            self._save_state()
            if old is not None and old != node and not demoted:
                self.pending_demotions.add(old)
            return {"ok": True, "master": node, "epoch": new_epoch, "old_master": old, "old_master_demoted": demoted, "status": ack.get("st")}

    def retry_demotions(self):
        for old in list(self.pending_demotions):
            ack = self.links[old].call("role", self.address(old, "cmd"), epoch=self.epoch, role="standby", node=old, timeout=0.2, retries=1)
            if ack is not None and ack.get("ok"):
                self.pending_demotions.discard(old)

    # -- operator view -----------------------------------------------------
    def status(self, probe=True):
        """What the GUI shows. Every node field comes from the node itself."""
        if probe:
            self.retry_demotions()
        ids = sorted(self.nodes)
        if probe and ids:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(ids)) as pool:
                states = list(pool.map(self.probe, ids))
        else:
            states = [self.links[n].last_status or None for n in ids]
        out = [
            {"id": n, "ip": self.nodes[n]["ip"], "reachable": st is not None, "status": st}
            for n, st in zip(ids, states)
        ]
        return {
            "legacy": self.legacy,
            "load_error": self.load_error,
            "master": self.master,
            "epoch": self.epoch,
            "pending_demotions": sorted(self.pending_demotions),
            "nodes": out,
            "commands": recent_commands(),
        }


class RoutedSocket:
    """Drop-in for the plain `master_udp` socket swarm.py used. The old second
    argument (an address) is now just a port kind -- "cmd" or "ctl" -- because
    where it goes is the router's decision, not the caller's."""

    def __init__(self, router):
        self._router = router

    def sendto(self, data, kind):
        return self._router.send(data, kind)


class _NullSocket:
    """Stands in for the old per-computer sockets whose fan-out is now handled
    by routing (the master is sent to once, through RoutedSocket)."""

    def sendto(self, data, address=None):
        return True


ROUTER = Router()
