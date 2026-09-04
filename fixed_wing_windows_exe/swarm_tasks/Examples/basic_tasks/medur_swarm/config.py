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
}

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
]

# --- Altitude staggering ---------------------------------------------------

HOME_HEIGHT = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]

# --- Coordinate conversion --------------------------------------------------

END_DISTANCE = 500000
RADIUS_OF_EARTH = 6378100.0  # metres

# --- Per-tick sleep, keyed by current fleet size ---------------------------

SLEEP_TIMES = {
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

# This is only a maximum for original grid waypoints. It is capped by the
# next leg length, and is never used for dense Bezier interpolation points.
SEARCH_UAV_FLYBY_RADIUS_M = 100.0
# Final-waypoint fly-by radius is the UAV's live loiter radius (WP_LOITER_RAD,
# read per control tick by guidance._uav_loiter_radius_m) plus this margin, so
# it tracks any in-flight loiter-radius change instead of being pinned to one
# number. UAV_DEFAULT_LOITER_RADIUS_M is the fallback when telemetry is absent.
UAV_DEFAULT_LOITER_RADIUS_M = 200.0
UAV_FINAL_WAYPOINT_RADIUS_MARGIN_M = 150.0
UAV_CURVE_POINT_SWITCH_RADIUS = 3.0  # sim units, bot-only progression

# Forward guidance distance for fixed-wing aircraft on a Bezier turn, in
# real (unscaled) metres. The bot still follows each sample for CVG safety.
UAV_CURVE_LOOKAHEAD_M = 0.0

# Print real UAV-to-bot separation for every moving command. This prints once
# per bot control tick; set False only when a quiet console is required.
BOT_SYNC_DEBUG = True

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
UAV_COLLISION_AVOID_GAIN = 0.6
