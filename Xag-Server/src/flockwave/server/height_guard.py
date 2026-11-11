"""Server-side gate: nothing flies at a height the operator did not give.

A swarm computer starts on a default height table, and goes back to it after a
restart or when another computer becomes master. So this does not trust what
was sent: before a flying command it compares the heights the operator gave
with the ones the master reports it is really using (the snapshot it already
provides, Router.master_snapshot). Any target UAV that differs, for whatever
reason, refuses the command before anything is sent and the GUI receives
"height_not_set|<message>". This works the same with one computer or many.

A UAV the master does not fly is not a target: the swarm would ignore it. An
empty id list means every UAV the master flies, as it does on the swarm computer.
"""

REFUSED = "height_not_set"

_expected = {}  # UAV id (int) -> height the operator gave through "different"
_same_height = None  # height the operator gave through "same"


def _ints(ids):
    """GUI ids are zero-padded strings ("01")."""
    result = []
    for uav_id in ids or ():
        try:
            result.append(int(uav_id))
        except (TypeError, ValueError):
            print(f"[height-guard] ignoring unusable UAV id {uav_id!r}")
    return result


def _refusal(text):
    print("[height-guard] command refused:", text)
    return f"{REFUSED}|{text}"


def note_different(base, step, ids, snapshot):
    """The master acknowledged 'different'. It computes base + step * <position
    of the UAV in its own list>, so that list is needed to know each height."""
    swarm_ids = _ints((snapshot or {}).get("uav_ids"))
    for uav_id in _ints(ids) or swarm_ids:
        if uav_id in swarm_ids:
            _expected[uav_id] = base + step * swarm_ids.index(uav_id)


def note_same(height):
    """The master acknowledged 'same'."""
    global _same_height
    _same_height = float(height)


def check(ids, snapshot):
    """None if the command may be sent, otherwise the refusal for the GUI.
    `snapshot` is the master's own report, None if it could not be read."""
    if not snapshot:
        return _refusal(
            "Height not confirmed: could not read the heights from the swarm "
            "computer. Check the swarm link."
        )
    altitude = snapshot.get("altitude") or {}
    swarm_ids = _ints(snapshot.get("uav_ids"))
    requested = _ints(ids)
    targets = [u for u in swarm_ids if not requested or u in requested]

    if altitude.get("same_alt_flag"):
        ok = _same_height is not None and altitude.get("same_height") == _same_height
        missing = [] if ok else targets
    else:
        table = altitude.get("different_height") or []
        missing = [
            u
            for u in targets
            if swarm_ids.index(u) >= len(table)
            or _expected.get(u) != table[swarm_ids.index(u)]
        ]
    if not missing:
        return None
    names = ", ".join(str(u) for u in sorted(missing))
    return _refusal(f"Height not set for UAV {names}. Send Change Altitude first.")
