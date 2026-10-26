"""Receiver half of the reliable command envelope.

The server wraps every legacy command string in a small JSON envelope:

    {"k":"cmd","v":1,"sid":"<sender session>","seq":N,"epoch":E,"p":"<legacy payload>"}

and expects, per command, one reply to the sender's source address:

    {"k":"ack","sid":"<sid>","seq":N,"ok":true|false,"why":"<reason>"}

`unwrap()` is called by both UDP listeners. It ACKs, drops retransmitted
duplicates (re-ACKing them so the sender stops retrying) and returns the
untouched legacy payload bytes, so every existing handler keeps parsing
exactly what it parsed before. Datagrams that are not envelopes are passed
through unchanged (legacy / third-party senders keep working, unacked).
"""

import json
import threading

_MAGIC = b"{"  # legacy commands are plain text and never start with a brace
_DEDUP_SESSIONS = 16

_lock = threading.Lock()
_last_seq = {}  # sender session id -> highest seq accepted
_epoch = 0  # fencing token: commands from an older epoch are refused


def current_epoch():
    return _epoch


def set_epoch(epoch):
    global _epoch
    with _lock:
        _epoch = max(_epoch, int(epoch))


def _reply(sock, address, sid, seq, ok, why=""):
    msg = {"k": "ack", "sid": sid, "seq": seq, "ok": ok, "why": why}
    try:
        sock.sendto(json.dumps(msg, separators=(",", ":")).encode(), address)
    except OSError as e:
        print("[reliable] could not send ack:", repr(e))


def unwrap(data, address, sock):
    """Return the legacy payload bytes to dispatch, or None if the datagram
    was consumed here (duplicate, stale epoch or malformed envelope)."""
    if not data.lstrip().startswith(_MAGIC):
        return data
    try:
        env = json.loads(data.decode("utf-8"))
        if env.get("k") != "cmd":
            return data
        sid, seq, epoch = str(env["sid"]), int(env["seq"]), int(env.get("epoch", 0))
        payload = env["p"].encode("utf-8")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as e:
        print("[reliable] malformed envelope:", repr(e))
        return None

    with _lock:
        if epoch < _epoch:
            stale = True
        else:
            stale = False
            duplicate = seq <= _last_seq.get(sid, -1)
            if not duplicate:
                if sid not in _last_seq and len(_last_seq) >= _DEDUP_SESSIONS:
                    _last_seq.pop(next(iter(_last_seq)))
                _last_seq[sid] = seq
    if stale:
        print("[reliable] refused command from stale epoch", epoch, "<", _epoch)
        _reply(sock, address, sid, seq, False, "stale_epoch")
        return None
    _reply(sock, address, sid, seq, True, "duplicate" if duplicate else "queued")
    if duplicate:
        return None
    return payload
