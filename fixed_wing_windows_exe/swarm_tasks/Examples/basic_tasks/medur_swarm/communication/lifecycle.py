"""Truthful execution lifecycle of every command the swarm computer runs.

Transport acknowledgement ("received") only says the datagram reached the
receiver. This module reports what the dispatch loop then actually did:

    received -> started -> completed                 foreground command ran to its end
                        -> running -> completed      work handed to background per-UAV tasks,
                                                     finished when the last of those tasks ended
                        -> failed                    a handler raised
                        -> preempted                 a newer command took over before it finished
                        -> cancelled                 an explicit stop dropped its tasks
                        -> interrupted               outcome unknown: UAV removed under it, or the
                                                     receiver restarted / lost the master role
    received -> superseded | discarded               never ran (replaced by a newer plan / stop)
    (refused at the door)  -> rejected               unsupported or invalid command

"completed" never means "the aircraft reached its goal safely"; it means the
swarm program's own work for that command finished. Every transition is
appended to a durable journal so a restart can mark whatever was in flight as
`interrupted` instead of leaving it looking alive.
"""

import json
import os
import threading
import time

from medur_swarm import state

TERMINAL = {
    "completed", "failed", "preempted", "cancelled", "interrupted",
    "rejected", "superseded", "discarded",
}

_lock = threading.RLock()
_emit = lambda meta, status, why: None  # installed by sockets.py
_meta = {}  # mailbox seq -> object with .sid .seq .address .payload
_status = {}  # mailbox seq -> {"status", "why"}
_running = {}  # mailbox seq -> pending terminal (status, why) | None
_partial = {}  # mailbox seq -> seq that took some (not all) of its tasks
_claim_seq = None  # command whose handler is assigning tasks right now
current_seq = None  # command the main loop is dispatching
_journal = None
_history = []  # recent transitions, replicated to standbys

if not hasattr(state, "task_owner"):
    state.task_owner = {}  # bot index -> mailbox seq of the command that owns its task


def set_emitter(fn):
    global _emit
    _emit = fn


def register(seq, meta):
    with _lock:
        _meta[seq] = meta
        for old in [s for s in _meta if s < seq - 64]:
            _meta.pop(old, None)
            _status.pop(old, None)


# ---- journal ---------------------------------------------------------------

def open_journal(path):
    global _journal
    _journal = path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def _write(record):
    if _journal is None:
        return
    try:
        with open(_journal, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    except OSError as e:
        print("[lifecycle] journal write failed:", repr(e))


def recover_journal(emit_to=None, epoch=0):
    """After a restart: every command whose last journalled status is not
    terminal had an unknown outcome. Mark it `interrupted` (and tell its
    sender if it is still listening). Returns the list of interrupted records.
    Compacts the journal to its most recent entries."""
    if _journal is None or not os.path.exists(_journal):
        return []
    last = {}
    try:
        with open(_journal, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                last[(rec.get("sid"), rec.get("seq"))] = rec
    except OSError:
        return []
    interrupted = []
    for rec in last.values():
        if rec["status"] not in TERMINAL:
            rec = dict(rec, status="interrupted", why="receiver_restart", ts=time.time())
            _write(rec)
            interrupted.append(rec)
            last[(rec["sid"], rec["seq"])] = rec  # compaction must keep the terminal record
            if emit_to is not None and rec.get("addr"):
                emit_to(tuple(rec["addr"]), rec["sid"], rec["seq"], "interrupted", "receiver_restart")
    keep = sorted(last.values(), key=lambda r: r.get("ts", 0))[-500:]
    try:
        with open(_journal, "w", encoding="utf-8") as f:
            for rec in keep:
                f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    except OSError:
        pass
    return interrupted


def _set(seq, status, why=""):
    with _lock:
        meta = _meta.get(seq)
        if meta is None:
            return
        prev = _status.get(seq, {}).get("status")
        if prev in TERMINAL:
            return  # a terminal status is final
        _status[seq] = {"status": status, "why": why}
        rec = {
            "sid": meta.sid, "seq": meta.seq, "addr": list(meta.address) if meta.address else None,
            "cmd": meta.payload[:48].decode("utf-8", "replace"), "status": status, "why": why,
            "ts": time.time(), "epoch": _epoch(),
        }
        _write(rec)
        _history.append(rec)
        del _history[:-100]
    _emit(meta, status, why)


def _epoch():
    try:
        from medur_swarm.communication import reliable
        return reliable.current_epoch()
    except Exception:
        return 0


def history(limit=50):
    with _lock:
        return [dict(r) for r in _history[-limit:]]


def status_of(seq):
    with _lock:
        return dict(_status.get(seq, {}))


# ---- main-loop hooks -------------------------------------------------------

def begin(seq, payload=b""):
    global current_seq
    current_seq = seq
    _set(seq, "started")


def foreground_done(seq):
    """The dispatch handlers returned normally."""
    if _owns_tasks(seq):
        with _lock:
            _running.setdefault(seq, None)
        _set(seq, "running", "background_tasks_active")
    else:
        _set(seq, "completed")


def foreground_preempted(seq, by_payload=b""):
    if seq is None:
        return
    if by_payload == b"stop":
        _set(seq, "cancelled", "stop")
    else:
        _set(seq, "preempted", "newer_command")


def foreground_failed(seq, exc):
    if seq is not None:
        _set(seq, "failed", repr(exc)[:120])


class claiming:
    """Context for a handler that may assign background tasks on behalf of a
    command that is being handled concurrently (not via the main loop)."""

    def __init__(self, seq):
        self.seq = seq

    def __enter__(self):
        global _claim_seq
        _claim_seq = self.seq

    def __exit__(self, *exc):
        global _claim_seq
        _claim_seq = None
        return False


def concurrent_handled(seq):
    _set(seq, "started")
    foreground_done(seq)


# ---- background task ownership --------------------------------------------

def _owner():
    return _claim_seq if _claim_seq is not None else current_seq


def _owned(seq):
    return [i for i in state.active_goal_tasks if state.task_owner.get(i) == seq]


def _owns_tasks(seq):
    with state.active_goal_tasks_lock:
        return bool(_owned(seq))


def claim(bot_index):
    """Call (inside active_goal_tasks_lock) right before a task is created or
    overwritten for `bot_index`."""
    seq = _owner()
    prev = state.task_owner.get(bot_index)
    if prev is not None and prev != seq and prev in _running:
        remaining = [i for i in _owned(prev) if i != bot_index]
        if remaining:
            _partial[prev] = seq
        else:
            _running[prev] = ("preempted", "tasks_replaced_by_newer_command")
    state.task_owner[bot_index] = seq


def note_cancel_all():
    """An explicit stop is about to clear every background task."""
    with _lock:
        for seq in _running:
            _running[seq] = ("cancelled", "stop")


def note_task_removed(removed_index):
    """A UAV was removed from the swarm under its task (indexes then shift)."""
    seq = state.task_owner.get(removed_index)
    with _lock:
        if seq in _running and _running[seq] is None:
            _running[seq] = ("interrupted", "uav_removed")
    shifted = {}
    for idx, owner in state.task_owner.items():
        if idx == removed_index:
            continue
        shifted[idx - 1 if idx > removed_index else idx] = owner
    state.task_owner.clear()
    state.task_owner.update(shifted)


def reconcile():
    """Finish `running` commands whose last background task has ended.
    Called a few times a second from the command feeder thread."""
    with _lock:
        pending = list(_running.items())
    for seq, cause in pending:
        if _owns_tasks(seq):
            continue
        with _lock:
            _running.pop(seq, None)
        if cause is None:
            if seq in _partial:
                _set(seq, "completed", "partially_preempted_by_%s" % _partial.pop(seq))
            else:
                _set(seq, "completed", "tasks_finished")
        else:
            _set(seq, *cause)
