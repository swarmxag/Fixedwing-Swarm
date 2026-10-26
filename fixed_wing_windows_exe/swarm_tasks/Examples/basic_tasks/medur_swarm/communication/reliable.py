"""Receiver half of the reliable command envelope (sender: Xag-Server
flockwave/server/swarm_link.py -- keep the two in sync).

Every datagram the server sends is a JSON envelope with a sender session id
`sid` and a per-sender sequence number `seq`:

    {"k":"cmd", "sid":..,"seq":N,"epoch":E,"p":"<legacy payload>"}   a command
    {"k":"ping","sid":..,"seq":N,"epoch":E}                          status probe
    {"k":"role","sid":..,"seq":N,"epoch":E,"role":"master|standby","node":ID}

and is answered by exactly one reply to the sender's source address:

    {"k":"ack","sid":..,"seq":N,"ok":bool,"why":str,"st":{...status...}}

A command that was ACKed "queued" later gets zero or more lifecycle events
({"k":"evt","sid":..,"seq":N,"st":"started|superseded|discarded","why":..}) so
the operator's view follows what the receiver actually did with it.

`receive()` ACKs, drops retransmitted duplicates (re-ACKing them so the sender
stops retrying), enforces the epoch fence and the accept policy, and returns
the untouched legacy payload, so every existing handler keeps parsing exactly
what it parsed before. Datagrams that are not envelopes pass through unchanged
(legacy senders keep working, unacked).
"""

import json
import threading
from collections import namedtuple

_DEDUP_SESSIONS = 16

_lock = threading.Lock()
_last_seq = {}  # sender session id -> highest seq accepted
_epoch = 0  # fencing token: anything from an older epoch is refused

# Hooks installed by communication/sockets.py.
status_provider = lambda: {}  # () -> dict, reported in every ACK's "st"
role_handler = None  # (role, node, epoch) -> (ok, why)
accept_policy = None  # (payload: bytes, port_kind) -> (ok, why)

Received = namedtuple("Received", "payload sid seq address")


def current_epoch():
    return _epoch


def set_epoch(epoch):
    global _epoch
    with _lock:
        _epoch = max(_epoch, int(epoch))


def _send(sock, address, obj):
    try:
        sock.sendto(json.dumps(obj, separators=(",", ":")).encode(), address)
    except OSError as e:
        print("[reliable] could not send reply:", repr(e))


def _status():
    try:
        st = dict(status_provider())
    except Exception as e:  # a broken provider must never stop ACKs
        st = {"status_error": repr(e)}
    st["epoch"] = _epoch
    return st


def _ack(sock, address, sid, seq, ok, why=""):
    _send(sock, address, {"k": "ack", "sid": sid, "seq": seq, "ok": ok, "why": why, "st": _status()})


def emit_event(sock, address, sid, seq, status, why=""):
    """Tell the sender what became of an already-ACKed command."""
    if sid is None:
        return  # legacy datagram: nobody is listening for events
    _send(sock, address, {"k": "evt", "sid": sid, "seq": seq, "st": status, "why": why})


def receive(data, address, sock, port_kind="cmd"):
    """Return a Received for something to dispatch, or None if the datagram
    was fully handled here (ping, role, duplicate, refusal, malformed)."""
    if not data.lstrip().startswith(b"{"):
        if accept_policy is not None:
            ok, why = accept_policy(data, port_kind)
            if not ok:
                print("[reliable] legacy datagram refused:", why, data[:40])
                return None
        return Received(data, None, None, address)  # legacy / third-party sender
    try:
        env = json.loads(data.decode("utf-8"))
        kind = env.get("k")
        if kind not in ("cmd", "ping", "role"):
            return Received(data, None, None, address)
        sid, seq, epoch = str(env["sid"]), int(env["seq"]), int(env.get("epoch", 0))
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, AttributeError) as e:
        print("[reliable] malformed envelope:", repr(e))
        return None

    if kind == "ping":  # read-only, idempotent: never deduplicated or fenced
        _ack(sock, address, sid, seq, True, "pong")
        return None

    with _lock:
        stale = epoch < _epoch
    if stale:
        print("[reliable] refused %s from stale epoch %d < %d" % (kind, epoch, _epoch))
        _ack(sock, address, sid, seq, False, "stale_epoch")
        return None

    if kind == "cmd":
        try:
            payload = env["p"].encode("utf-8")
        except (KeyError, AttributeError, UnicodeError):
            _ack(sock, address, sid, seq, False, "malformed")
            return None
        if accept_policy is not None:
            ok, why = accept_policy(payload, port_kind)
            if not ok:
                print("[reliable] refused command:", why, payload[:40])
                _ack(sock, address, sid, seq, False, why)
                return None

    with _lock:
        duplicate = seq <= _last_seq.get(sid, -1)
        if not duplicate:
            if sid not in _last_seq and len(_last_seq) >= _DEDUP_SESSIONS:
                _last_seq.pop(next(iter(_last_seq)))
            _last_seq[sid] = seq
    if duplicate:
        _ack(sock, address, sid, seq, True, "duplicate")
        return None

    set_epoch(epoch)  # the server is authoritative: adopt a newer epoch

    if kind == "role":
        ok, why = (False, "no_role_handler")
        if role_handler is not None:
            ok, why = role_handler(env.get("role"), env.get("node"), epoch)
        _ack(sock, address, sid, seq, ok, why)
        return None

    _ack(sock, address, sid, seq, True, "queued")
    return Received(payload, sid, seq, address)


def unwrap(data, address, sock, port_kind="cmd"):
    """Payload-only convenience wrapper around receive()."""
    got = receive(data, address, sock, port_kind)
    return None if got is None else got.payload
