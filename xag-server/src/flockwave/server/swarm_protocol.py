"""JSON command schema shared by this server (swarm.py) and the swarm-computer
receiver (swarm_controller.py / command_queue.py, in the fixed_wing_1 repo at
fixed_wing/swarm_tasks/Examples/basic_tasks/).

This file is mirrored BY HAND from that repo's copy at the same relative
path. There is no shared package between the two deployments, so keep both
copies in sync when adding, removing, or changing a command's parameters.

Wire format: one JSON object per UDP datagram, sent server -> swarm computer
only (this channel has no replies today, matching the previous string
protocol):

    {"cmd": "<name>", "params": {...}}
"""

# Commands with a real, working handler on the swarm-computer side today.
COMMAND_SCHEMA = {
    "search": ("points", "grid_spacing", "coverage", "num_uavs", "origin"),
    "goal": ("goals", "direction", "radius"),
    "navigate": ("center", "grid_spacing", "coverage", "num_uavs", "origin"),
    "loiter": ("center", "direction", "radius"),
    "split": ("centers", "num_uavs", "grid_spacing", "coverage", "origin"),
    # specificsplit's grid_spacing/coverage are per-area LISTS (one entry per
    # center), matching SpecificSplitMission.GroupSplitting's signature.
    "specificsplit": ("centers", "uav_groups", "grid_spacing", "coverage", "origin"),
    "landing": ("return_points",),
    "add_uav": ("sys_id",),
    "remove_uav": ("sys_id",),
    # "master" today only ever reconnects a drone's MAVLink link (its other
    # effect, multi-companion-computer master election, is dead code removed
    # in this refactor) -- kept as a distinct command name for compatibility,
    # but it is handled identically to add_uav.
    "master": ("sys_id",),
    "same_altitude": ("altitude",),
    "different_altitude": ("initial_altitude", "step"),
    "specific_bot_goal": ("uav", "goal"),
    "stop": (),
    "skip_waypoint": ("waypoint",),
    "remove_bot": ("sys_id",),
    "home_lock": (),
    "origin": ("lat", "lon"),
    "geofence": (),
    "takeoff": ("altitude",),
    "group_split": ("uavs", "goal"),
    "grid_path_planning": ("center", "num_uavs", "grid_spacing", "coverage"),
    "store_uav_pos": (),
    # Documented no-op: the real landing path is "landing" (see above). Kept
    # so a stray "home" datagram is acknowledged in logs instead of crashing.
    "home": (),
}

# Commands with a sender in this file but NO handler on the swarm-computer
# side today (never implemented, or superseded). Kept only so the legacy
# senders below have a documented schema entry -- swarm_controller.py's
# dispatch table has no cmd_* method for these, so they are logged and
# dropped like any other unrecognized command.
SENDER_ONLY_STUBS = {
    "return": (),
    "clear_csv": (),
    "start": (),
    "start1": (),
    "select_plot": ("filename",),
    "share_data": (),
    "disperse": (),
    "aggregate": (),
    "home_goto": (),
    "rtl": (),
    "legacy_takeoff": ("alt",),
    "send_alts": ("alts",),
    "airport_selection": ("filename",),
}

# Commands that represent a long-running "mission" tracking loop. Only one may
# be active at a time; a new mission command arriving while one is already
# running is dropped with a warning (send "stop" first) rather than queued.
MISSION_COMMANDS = frozenset({
    "search", "goal", "navigate", "loiter", "split", "specificsplit",
    "landing", "specific_bot_goal", "same_altitude", "different_altitude",
    "group_split",
})

# Commands honored as mid-mission interrupts (checked every tick of a running
# mission's loop instead of only between commands).
INTERRUPT_COMMANDS = frozenset({"stop", "skip_waypoint"})


def all_command_names():
    return set(COMMAND_SCHEMA) | set(SENDER_ONLY_STUBS)
