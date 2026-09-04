"""Shared, mutable runtime state for the fixed-wing swarm script.

Every other module in medur_swarm imports this module object (never its
individual names) and reads/writes attributes on it, e.g. ``state.pos_array``.
That is required, not a style preference: several of these names are
rebound wholesale at runtime (``state.pos_array = [...]``, ``state.s =
sim.Simulation(...)``, ...) rather than mutated in place, and a `from
state import pos_array` elsewhere would keep pointing at the old object
after such a rebind. This mirrors exactly how the original single-file
script relied on plain module globals shared across every function via one
namespace -- splitting into modules removes that free sharing, so this
module restores it explicitly.

Threading note: active_goal_tasks_lock and swarm_topology_lock guard the
groups of these attributes the original code held them across; see
tasks/runner.py and uav/management.py for how they're used.
"""

import threading

# --- Networking / GCS link -------------------------------------------------

master_num = 0
master_flag = True
file_name = None  # no site preset -- operator draws a fence when enabling swarm

heartbeat_ip_timeout = [30] * 10
slave_heal_ip = ["192.168.0.153"] * 10

# --- Origin / coordinate frame ----------------------------------------------

origin = None  # set at startup from rectangles.yaml if present, else on fence draw

# --- Fleet topology ----------------------------------------------------------

num_bots = 10
vehicles = []
pos_array = []
robots = [(0, 0)] * 10

# sys_id -> stable vehicle/topology state
uav_registry = {}
# sys_id -> IDLE/GOAL/SEARCH/SPLIT/SPECIFIC_SPLIT
uav_task_state = {}

# Adding/removing a UAV changes the index used by *every* fleet-aligned list.
# Keep it mutually exclusive with the background task driver, otherwise the
# driver can read vehicle[i] while another thread has just compacted it.
swarm_topology_lock = threading.RLock()

# --- Home / current position bookkeeping ------------------------------------

home_pos = []
home_pos_lat_lon = []
uav_home_pos = []

# --- Altitude staggering (mutated by "same"/"different" commands) ----------

same_height = 100
same_alt_flag = False
different_height = [200, 210, 220, 230, 240, 310, 300, 310, 300, 310]

# --- Simulation / GUI --------------------------------------------------------

s = None  # swarm_tasks.simulation.simulation.Simulation, created once fleet is known

# --- sock3-driven mailbox: last raw message, doubles as the "stop" signal --

index = 0

# --- Vehicle-lost / removal bookkeeping --------------------------------------

vehicle_lost_flag = False
lost_vehicle_num = 0
pop_bot_index = None
remove_flag = False
remove_bot_flag = False
remove_bot_index = 0
remove_bot_array = []
uav_removed = True
pop_flag_arr = [1] * num_bots

# --- Command-loop bookkeeping (skip-waypoint path from sock3) ---------------

skip_wp_flag = False
next_wp = 0
goal_table = []
goal_path_csv_array = []
goal_path_csv_array_flag = False
start_return_csv_flag = False

# --- Mission-flow flags (persist across dispatch-loop iterations, exactly
# as they did as bare module globals in the original single-file script) ---

search_flag = False
search_flag_val = 0
search_step = 1

split_flag = False
split_flag_val = 0

start_flag = False
circle_formation_flag = False
circle_formation_count = 0
circle_formation_table = [0] * num_bots

home_flag = False
home_flag1 = False

guided_circle_flag = False
guided_circle_formation_flag = False
guided_circle_formation_table = [0] * num_bots

group_goal_flag = False

group_split_flag = False
group_split_flag_array = [False] * num_bots
group_split_goal_pos = [0] * num_bots

specific_bot_goal_flag = False
goal_bot_num = None

home_goto_flag = False
landing_flag = False

# --- Grid/CSV mission progress (search + split) ------------------------------

grid_path_array = [1] * num_bots
all_uav_csv_grid_array = [0] * num_bots

removed_uav_grid = []
removed_grid_path_length = []
removed_grid_path_array = [0] * len(pos_array)
removed_grid_path_array_start_val = [0] * len(pos_array)
removed_grid_path_array_index = 0
checkall_removed_grid_path_array_start_val = [0] * len(pos_array)
removed_grid_filename = [0] * num_bots
removed_grid_path_array_flag = False

uncovered_area_filename = []
uncovered_area_points = []

# --- Background per-bot task driver (goal / mission / guided-circle /
# altitude) -- see tasks/runner.py -------------------------------------------

active_goal_tasks = {}
# Last-applied "Automate Goals" (autogoal) inputs: goal_lat/goal_lon,
# direction, radius, bearing_deg, safety_margin_m, selected_indexes. Set by
# tasks/goal.py when an autogoal command is assigned; read by
# regenerate_autogoal() so an on-board loiter-radius change can re-space and
# re-size every UAV's circle without the operator re-selecting. None until
# the first autogoal command of the run.
autogoal_params = None
# A task replacement must be atomic with the runner tick that reads and
# drives it. RLock permits the task drivers' small state updates while the
# runner holds this lock, preventing an overwritten task from issuing one
# stale simple_goto or modifying the replacement task's waypoint index.
active_goal_tasks_lock = threading.RLock()

# Bot indexes currently being flown by a foreground search/split/specificsplit
# loop. Those loops own their bots' movement directly (the bots are deliberately
# kept OUT of active_goal_tasks), so apply_different_heights() must treat these
# as busy too -- otherwise it sees them as idle and assigns a standalone
# altitude task, which the foreground loop then reads as "diverted" and drops
# the bot from the mission for good. The loop's own per-tick simple_goto already
# reads different_height[i] fresh, so updating the array alone is enough.
foreground_mission_indexes = set()

# Bot index -> (x, y) in the sim frame: the forward look-ahead / pursuit target
# most recently handed to that bot's real UAV (simple_goto). Written by every
# path that computes a vehicle target (guidance._drive_vehicle_towards for
# goal/mission/guided-circle, and the search/split foreground loops); read by
# each foreground loop's GUI block and drawn by Gui.show_lookahead so the
# guidance lead (bot waypoint -> look-ahead target -> aircraft) is visible.
uav_lookahead_points = {}

# bot index -> time.monotonic() of that bot's last pacing step. Used by
# uav/guidance.py's groundspeed pacing to measure the REAL elapsed time
# between ticks, so the virtual leader advances by (aircraft groundspeed x
# dt) instead of a fixed step whose effective speed was just a side effect
# of the runner loop's sleep + workload (and therefore drifted with bot
# count and CPU load).
bot_step_last_time = {}

# bot index -> smallest real-UAV-to-final-goal distance (metres) seen so far
# on the current goal task. Lets the goal -> guided-circle handoff latch on
# closest approach instead of depending on a tick happening to sample the
# aircraft inside the loiter radius: shrinking WP_LOITER_RAD mid-flight
# (e.g. 1000 -> 600) used to strand a UAV that was already inside the old
# radius but outside the new one. Cleared whenever a goal task is assigned
# or handed off. See tasks/runner.py _drive_goal_task.
goal_min_distance = {}

# Ported from individual-uav-access-add-remove (goal/add/remove concurrency
# slice only -- see communication/dispatch.py's check_for_new_command for
# what still preempts).
handled_concurrent_command_seq = 0
last_seq = 0

# --- GPS resync bookkeeping (uav/telemetry.py) ------------------------------

last_gps_resync = {}  # bot index -> monotonic time.time() of last correction
last_curve_guidance_log = {}  # bot index -> (line_index, is_curve, has_lookahead)

# --- Cross-command leftovers ------------------------------------------------
#
# goal_latlon, guided_circle_radius, guided_circle_direction: deliberately
# NOT given initial values here. tasks/goal.py sets them as a side effect
# of parsing a 'goal' command; tasks/formation.py's guided_circle handler
# reads them back with no assignment of its own. This mirrors the
# original single-file script exactly: those three were plain module
# globals that only ever got a value from the 'goal' block, so sending
# 'guided_circle' with no preceding 'goal' in the same run raised
# NameError there and raises AttributeError here -- same latent bug,
# preserved rather than papered over.
