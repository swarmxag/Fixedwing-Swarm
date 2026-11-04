"""What a UAV joining or leaving the swarm does to state indexed by swarm
position.

Every per-UAV structure in this program is indexed by the UAV's position in
state.pos_array (the same index as state.vehicles and state.s.swarm). A
removal shifts every later UAV down by one, so each structure must drop the
removed slot -- otherwise the UAV behind it inherits its neighbour's target,
progress or timing. An addition appends one slot at the end, which must start
empty so the new UAV stays idle.

Layers:
  * management.remove_uav_from_swarm / add_uav_to_swarm move pos_array,
    vehicles, the simulation bot and the background tasks, and call
    apply_removal / apply_addition below in the same locked section
    (state.swarm_topology_lock + state.active_goal_tasks_lock), so no loop
    or thread ever sees a half-updated index frame.
  * apply_removal / apply_addition realign the common per-UAV state.
  * A running mission realigns only its own lists, by registering them with
    tracking() for the duration of its loop. Whole-swarm missions keep their
    membership by sys_id (members()/is_member()), so a UAV added mid-mission
    is not pulled into them.

A topology change is not a mission preemption: it never touches any other
UAV's target, path, progress or assignment.
"""

from contextlib import contextmanager

from medur_swarm import state

TOPOLOGY_PREFIXES = (b"remove,", b"add,")

# Common lists aligned with pos_array, and the value a newly added UAV gets.
# (pos_array, vehicles, s.swarm, different_height and pop_flag_arr are moved
# by management.py itself.)
_INDEXED_LISTS = (
    ("group_split_flag_array", False),
    ("group_split_goal_pos", 0),
    ("circle_formation_table", 0),
    ("guided_circle_formation_table", 0),
    ("home_pos", None),
    ("home_pos_lat_lon", None),
)

# Common dicts keyed by swarm index.
_INDEXED_DICTS = (
    "uav_lookahead_points",
    "bot_step_last_time",
    "goal_min_distance",
    "last_gps_resync",
    "last_curve_guidance_log",
)

_tracked = []  # [(list, fill)] registered by running missions


def is_topology_command(data):
    return isinstance(data, (bytes, bytearray)) and bytes(data).startswith(
        TOPOLOGY_PREFIXES
    )


def shift_after_removal(index, removed_index):
    """Index of the same UAV after removed_index left; None for the removed one."""
    if index == removed_index:
        return None
    return index - 1 if index > removed_index else index


def _remove_slot(values, removed_index):
    if 0 <= removed_index < len(values):
        values.pop(removed_index)


def _insert_slot(values, index, fill):
    # Some of these lists are pre-sized beyond the fleet; the new UAV's slot
    # must hold `fill` either way, and every lower slot keeps its value.
    if index <= len(values):
        values.insert(index, fill)
    else:
        values.extend([fill] * (index - len(values)))
        values.append(fill)


def _shift_dict(mapping, removed_index):
    shifted = {}
    for key, value in mapping.items():
        new_key = shift_after_removal(key, removed_index)
        if new_key is not None:
            shifted[new_key] = value
    mapping.clear()
    mapping.update(shifted)


def apply_removal(removed_index):
    """Realign common per-UAV state after the UAV at removed_index left.
    Call with state.swarm_topology_lock held, after pos_array/vehicles/s."""
    with state.swarm_topology_lock:
        for name, _fill in _INDEXED_LISTS:
            values = getattr(state, name, None)
            if isinstance(values, list):
                _remove_slot(values, removed_index)
        for name in _INDEXED_DICTS:
            mapping = getattr(state, name, None)
            if isinstance(mapping, dict):
                _shift_dict(mapping, removed_index)
        state.foreground_mission_indexes = {
            j
            for j in (
                shift_after_removal(i, removed_index)
                for i in state.foreground_mission_indexes
            )
            if j is not None
        }
        for values, _fill in _tracked:
            _remove_slot(values, removed_index)


def apply_addition(new_index):
    """Give the UAV just appended at new_index empty per-UAV state (idle).
    Call with state.swarm_topology_lock held, after pos_array/vehicles/s."""
    with state.swarm_topology_lock:
        for name, fill in _INDEXED_LISTS:
            values = getattr(state, name, None)
            if isinstance(values, list) and fill is not None:
                _insert_slot(values, new_index, fill)
        for name in _INDEXED_DICTS:
            mapping = getattr(state, name, None)
            if isinstance(mapping, dict):
                mapping.pop(new_index, None)
        for values, fill in _tracked:
            _insert_slot(values, new_index, fill)


@contextmanager
def tracking(*pairs):
    """Keep a running mission's own index-aligned lists in step with the
    swarm while the block runs: tracking((goal_pos, 0), (flags, False))."""
    entries = [(values, fill) for values, fill in pairs]
    with state.swarm_topology_lock:
        _tracked.extend(entries)
    try:
        yield
    finally:
        with state.swarm_topology_lock:
            for entry in entries:
                for k, tracked in enumerate(_tracked):
                    if tracked[0] is entry[0]:
                        del _tracked[k]
                        break


def members():
    """sys_ids of the UAVs a whole-swarm mission starts with."""
    with state.swarm_topology_lock:
        return {int(sys_id) for sys_id in state.pos_array}


def is_member(index, member_ids):
    """True if the UAV now at `index` belongs to a mission started with
    member_ids; a UAV added after the mission started does not."""
    return index < len(state.pos_array) and int(state.pos_array[index]) in member_ids
