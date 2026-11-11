"""Static configuration and tuning constants for the fixed-wing swarm script.

Nothing in this module is ever reassigned at runtime -- values that change
while the swarm is running (connected vehicles, origin, per-bot task state,
...) live in state.py instead.
"""

import os

# Persisted geofence/origin drawn by the operator in the GCS. Read at
# startup (main.py) and re-read whenever a "geofence" or "search" command
# needs the latest drawn fence.
RECTANGLES_PATH = os.path.join(
    os.path.expanduser("~"), "Documents", "swarm_env", "rectangles.yaml"
)

# --- MAVLink / networking -----------------------------------------------

# sys_id -> local mavlink UDP port the corresponding SITL/companion computer
# listens on.
PORT_DICT = {
    1: 14551,
    2: 14552,
    3: 14553,
    4: 14554,
    5: 14555,
    6: 14556,
    7: 14557,
    8: 14558,
    9: 14559,
    10: 14560,
    11: 14561,
    12: 14562,
    13: 14563,
    14: 14564,
    15: 14565,
}

# Parallel connection (uav/connection.py). None -> one worker per endpoint.
CONNECT_MAX_WORKERS = None
# Whole-cycle cap = longest heartbeat timeout + this. Covers dronekit's
# unbounded "wait until board has booted" step after the first heartbeat.
CONNECT_DEADLINE_GRACE_S = 60

# --- In-flight MAVLink link watch (uav/link_monitor.py) ---------------------
# No heartbeat for LINK_STALE_S: the UAV's bot is held (its mission does not
# advance on frozen telemetry). LINK_LOST_S: reported as lost. When heartbeats
# return, the bot is moved to the aircraft's first fresh GPS position and the
# mission continues; no position within LINK_POSITION_WAIT_S -> ask the
# autopilot for its telemetry streams again. A link whose dronekit threads
# stopped is reconnected on the same slot, retrying every LINK_RECONNECT_RETRY_S.
LINK_STALE_S = 3.0
LINK_LOST_S = 10.0
LINK_CHECK_INTERVAL_S = 0.5
LINK_POSITION_WAIT_S = 3.0
LINK_RECONNECT_TIMEOUT_S = 30
LINK_RECONNECT_RETRY_S = 5.0

HEARTBEAT_IP = [
    "192.168.0.151",
    "192.168.0.152",
    "192.168.0.153",
    "192.168.0.154",
    "192.168.0.155",
    "192.168.0.156",
    "192.168.0.157",
    "192.168.0.158",
    "192.168.0.159",
    "192.168.0.160",
    "192.168.0.161",
    "192.168.0.162",
    "192.168.0.163",
    "192.168.0.164",
    "192.168.0.165",
]

# --- Coordinate conversion --------------------------------------------------

END_DISTANCE = 500000
RADIUS_OF_EARTH = 6378100.0  # metres

# --- Per-tick sleep, keyed by current fleet size ---------------------------

SLEEP_TIMES = {
    15: 0.1,
    14: 0.1,
    13: 0.1,
    12: 0.1,
    11: 0.1,
    10: 0.1,
    9: 0.1,
    8: 0.11,
    7: 0.11,
    6: 0.12,
    5: 0.12,
    4: 0.123,
    3: 0.125,
    2: 0.13,
    1: 0.13,
}

# --- GPS resync ---------------------------------------------------------

# Seconds between real-GPS corrections per bot.
GPS_RESYNC_INTERVAL = 2.0

# --- Virtual-leader pacing (see uav/guidance.py for the rationale) ---------

UAV_MAX_VIRTUAL_STEP = 1.0
UAV_FOLLOW_WINDOW_M = 700.0  # centre of the full-pace/crawl transition
UAV_MAX_VIRTUAL_LEAD_M = 700.0  # expected worst-case lead at UAV_MIN_VIRTUAL_STEP
UAV_MIN_VIRTUAL_STEP = 0.15  # floor once well past UAV_FOLLOW_WINDOW_M -- never 0
# Width of the linear ramp centred on UAV_FOLLOW_WINDOW_M: step_size is
# UAV_MAX_VIRTUAL_STEP at (UAV_FOLLOW_WINDOW_M - ramp/2) and below, and
# UAV_MIN_VIRTUAL_STEP at (UAV_FOLLOW_WINDOW_M + ramp/2) and above, sliding
# smoothly in between. A hard single-point threshold here chatters: real
# GPS/bot-motion noise straddling the cutoff flips step_size between the
# two extremes almost every tick (observed directly in flight logs -- `dis`
# oscillating a few metres either side of the threshold, step_size flipping
# 1.0/0.15/1.0/0.15 tick to tick). The ramp removes the cutoff entirely, so
# there's nothing for that noise to trigger a full-swing flip on.
UAV_FOLLOW_RAMP_M = 100.0

# --- Groundspeed pacing (uav/guidance.py _groundspeed_step_size) -----------
#
# The bot's distance per tick is min(cmd.speed, bot.max_speed) * step_size in
# sim units (utils/robot.py move/step). With a FIXED step_size that works out
# to ~3 m per tick, and the tick period is SLEEP_TIMES[num_bots] plus however
# long the loop body takes -- so the virtual leader's effective ground speed
# landed somewhere around 15-30 m/s and drifted with bot count and CPU load,
# untethered from the aircraft's real speed. The aircraft then either
# overran the bot (and, having reached its GUIDED target, started loitering
# on it until the bot caught up) or fell behind it.
#
# Deriving step_size from (live groundspeed x measured dt) instead makes the
# bot cover exactly what the aircraft covers, so the lead between them stays
# constant by construction -- no runaway lead to brake for, and no overrun.
GROUNDSPEED_PACING = True

# --- Bot <-> UAV leash (uav/guidance.py _leash_factor) ----------------------
#
# Groundspeed pacing alone never lets the bot react to WHERE its UAV is, so
# once the UAV fell behind (a turn, a slow climb, a late handoff) the bot kept
# going at full speed and the gap only grew (observed: lead -1.3 km). The leash
# scales the bot's step so it holds UAV_BOT_GAP_M ahead of its UAV: it slows
# for a lagging UAV and pulls ahead of one catching up.
LEASH_PACING = True
# Gap the leash holds between the bot and its UAV, metres. About 20 m of it is
# used up by a 1 s telemetry delay, so 75 flies as roughly 55 m.
UAV_BOT_GAP_M = 75.0
# Waypoint distance ahead of the BOT, metres. None -> each UAV's live
# WP_LOITER_RAD + UAV_LOOKAHEAD_RADIUS_MARGIN_M. A target only just outside the
# loiter circle makes ArduPlane fly alongside it, so keep the margin generous.
UAV_LOOKAHEAD_M = None
UAV_LOOKAHEAD_RADIUS_MARGIN_M = 200.0
# Gap error (m) over which the factor goes from 1.0 to its clamp.
LEASH_RAMP_M = 60.0
LEASH_MIN_FACTOR = 0.15  # never 0: a frozen bot freezes the waypoint
LEASH_MAX_FACTOR = 1.5

# --- Bot <-> bot avoidance (uav/guidance.py smooth_bot_avoidance) -----------
#
# Replaces disp_field(neighbourhood_radius=100) in advance_bot_with_uav_pacing,
# whose radial 150/r push cancelled the goal pull head-on and parked two bots
# against each other. This one also slides each bot sideways past the other.
# False -> the old disp_field behaviour.
BOT_SMOOTH_AVOIDANCE = True
# Sim units (half-scale): 50 -> avoidance starts 100 m apart.
BOT_AVOID_RADIUS = 50.0
# Push straight away at contact; the goal pull is ~15 for comparison.
BOT_AVOID_GAIN = 20.0
# Sideways slide at contact -- what actually gets the bots past each other.
BOT_AVOID_TANGENT_GAIN = 25.0
# Upper clamp on the measured dt, so one stalled tick (GUI redraw, mission
# preempt, a blocking telemetry read) advances the bot by at most this much
# time's worth of travel instead of teleporting it forward.
BOT_STEP_MAX_DT_S = 0.5

# --- Final-goal -> guided-circle handoff (tasks/runner.py) -----------------
#
# The handoff fires when the real UAV is within its live WP_LOITER_RAD of the
# final goal. That alone depends on a tick sampling the aircraft while it is
# inside the radius, which a mid-flight radius reduction can defeat. So the
# closest approach is also latched: once the aircraft has come within
# (radius * GOAL_CLOSEST_APPROACH_FACTOR) and then started receding by more
# than GOAL_RECEDE_MARGIN_M, it has made its pass and the circle starts.
GOAL_CLOSEST_APPROACH_FACTOR = 2.0
GOAL_RECEDE_MARGIN_M = 100.0

# The guided-circle ring is generated once at handoff, but the aircraft's own
# orbit follows WP_LOITER_RAD live (the autopilot flies it). Rebuild the ring
# when the live radius has moved more than this from the one it was drawn at,
# so a mid-flight radius change is reflected on the plot instead of leaving a
# stale circle at the old size. Metres.
CIRCLE_RADIUS_REDRAW_TOLERANCE_M = 5.0
# Goal loiter: the bot rides the real UAV's orbit on the WP_LOITER_RAD circle
# (guidance.advance_bot_on_loiter_circle). Per-tick bot travel is capped at
# this many times the UAV's ground speed, so it glides onto the circle.
GUIDED_CIRCLE_BOT_CATCHUP = 3.0
# Ground speed used for that cap when telemetry reports 0, m/s.
GUIDED_CIRCLE_BOT_FALLBACK_SPEED_MS = 20.0
# Loiter rings (tasks/runner.py _assign_loiter_ring/_pick_ring): each UAV
# circling a goal gets its own WP_LOITER_RAD, written back to the original
# when it stops circling. False -> no parameter writes.
#
# Normal mode: RING_COUNT rings spread over (lowest radius in the group) ..
# + RING_BAND_M; a UAV takes the first ring with nobody on it within
# RING_MIN_VERTICAL_M of its height. With the 10 m different_height step:
# rings 600/650/700, drones on one ring 30 m apart in height, 10 drones fit
# in the band. Only if all are blocked: rings outside it every RING_STEP_M.
# Same-altitude mode: base + k * RING_STEP_M (height can't separate them).
# Simulated closest approach, same height, 18/25 m/s: 50 m apart ~47 m,
# 60 m ~57 m without avoidance (about 90-100 m with it); 10 m apart ~9 m.
GUIDED_CIRCLE_RINGS = True
GUIDED_CIRCLE_RING_COUNT = 3
GUIDED_CIRCLE_RING_BAND_M = 100.0
GUIDED_CIRCLE_RING_MIN_VERTICAL_M = 25.0
GUIDED_CIRCLE_RING_STEP_M = 60.0
# Final goals closer than this (metres) count as the same goal for rings.
GUIDED_CIRCLE_SAME_GOAL_M = 50.0

# This is only a maximum for original grid waypoints. It is capped by the
# next leg length, and is never used for dense Bezier interpolation points.
SEARCH_UAV_FLYBY_RADIUS_M = 100.0
# Final-waypoint fly-by radius is the UAV's live loiter radius (WP_LOITER_RAD,
# read per control tick by guidance._uav_loiter_radius_m) plus this margin, so
# it tracks any in-flight loiter-radius change instead of being pinned to one
# number. UAV_DEFAULT_LOITER_RADIUS_M is the fallback when telemetry is absent.
UAV_DEFAULT_LOITER_RADIUS_M = 200.0
UAV_FINAL_WAYPOINT_RADIUS_MARGIN_M = 150.0
# A goal whose loiter circle (live WP_LOITER_RAD plus this margin) would leave
# the fence is refused. The server uses the same value (fence_guard.LOITER_MARGIN_M).
GEOFENCE_LOITER_MARGIN_M = 50.0
UAV_CURVE_POINT_SWITCH_RADIUS = 3.0  # sim units, bot-only progression

# Forward guidance distance for fixed-wing aircraft on a Bezier turn, in
# real (unscaled) metres. The bot still follows each sample for CVG safety.
UAV_CURVE_LOOKAHEAD_M = 0.0

# Print real UAV-to-bot separation for every moving command, once per bot
# control tick, but only while the real UAV is AHEAD of its bot (signed lead
# > 0); set False for a quiet console.
BOT_SYNC_DEBUG = True

# CSV log of each listed UAV's distance to its bot and its look-ahead point
# (read-only, see uav/distance_log.py). DISTANCE_LOG_UAV_IDS are UAV numbers in
# pos_array; one file per UAV per program start. A UAV not connected writes
# only the header. False turns it off.
DISTANCE_LOG_ENABLED = True
DISTANCE_LOG_UAV_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
DISTANCE_LOG_INTERVAL_S = 0.5
DISTANCE_LOG_DIR = os.path.join(
    os.path.expanduser("~"), "Documents", "swarm_env", "distance_logs"
)

# Show the matplotlib reference plot window. False keeps every plot
# computation (the figure is still built and updated off-screen) but never
# opens or redraws a window.
SHOW_PLOT = True

# A fixed-wing can't turn on a dime, so a wide switch radius issues the next
# CSV point's command while still approaching the current one -- turn
# anticipation, the way a real AUTO mission's WP_RADIUS acceptance works.
# The last point of a run keeps the tighter tolerance since that is where
# mission completion is actually judged.
MISSION_POINT_SWITCH_RADIUS = 15  # sim units; tune to airframe turn radius
MISSION_FINAL_POINT_RADIUS = 10

# --- Real-UAV to real-UAV separation (collision avoidance) -----------------
#
# Computed from every connected vehicle's *live GPS*, independent of the
# simulated bots' own separation -- once each real aircraft is being paced
# individually (advance_bot_with_uav_pacing / compute_lookahead_target),
# the bots no longer necessarily track real separation closely enough for
# disp_field alone to be a meaningful safety margin between the real
# aircraft. See uav/guidance.py:real_uav_avoidance_vector.

# Real-world radius (metres) within which two real UAVs start pushing each
# other's guidance target apart.
UAV_COLLISION_AVOID_RADIUS_M = 150.0
# How strongly that push is applied to the final guidance target (0 = off).
# The push per neighbour is a UNIT vector scaled by weight (1 at zero
# separation, 0 at the radius) times this gain, in SIM units -- so the real
# displacement of the commanded point is 2 * weight * gain metres. At the
# old 0.6 that was 1.2 m at its absolute maximum, i.e. nothing at all next to
# a ~200 m fixed-wing turn radius; the term was wired up but could never
# actually move an aircraft. 50 gives it authority on the scale of the
# separations it is trying to defend:
#     10 m apart -> 93 m shift    50 m apart -> 67 m shift
#     25 m apart -> 83 m shift   100 m apart -> 33 m shift
UAV_COLLISION_AVOID_GAIN = 50.0

# --- Terrain data ---------------------------------------------------------

# Folder of SRTM .hgt tiles. terrain_gate reads from it and terrain_data
# downloads into it, so both must agree on this one path.
TERRAIN_DIR = os.environ.get(
    "XAG_TERRAIN_DIR",
    os.path.join(os.path.expanduser("~"), "Documents", "swarm_env", "terrain"),
)

# Ground fetched beyond the fence polygon on every side. The terrain gate
# samples past the polygon edge (1 km corridors, loiter radius + 1 km, 3 km on
# an altitude change), and a route check fails if a tile it touches is missing.
TERRAIN_FENCE_MARGIN_M = 5000.0
