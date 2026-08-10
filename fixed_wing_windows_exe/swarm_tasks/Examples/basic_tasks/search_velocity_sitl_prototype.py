"""SITL prototype: drive a single fixed-wing UAV's search mission with
streamed GUIDED heading + airspeed commands instead of simulated-bot-
position + simple_goto.

Why this exists
----------------
medur_fixed_wing.py's search loop drives a *simulated* potential-field bot
and then tells the real UAV to fly to wherever that bot currently sits
(vehicles[i].simple_goto(...)). Any lag between a sim tick and the MAVLink
send lets the real aircraft catch up to and loiter on a now-stale position
target -- that's the circling/corner-cutting problem this session kept
re-tuning (bot speed/step_size, then lead-distance + rate-limiting) without
fully closing.

NOTE: an earlier version of this file used SET_POSITION_TARGET_LOCAL_NED
(streamed NED velocity), copying the pattern from this repo's kamikaze.py.
That message is Copter/Rover-oriented -- ArduPlane's GUIDED mode does not
consume a general velocity vector that way. For fixed-wing, GUIDED mode's
actual supported primitives are: simple_goto (position), DO_CHANGE_SPEED
(airspeed/groundspeed), and, since ArduPilot ~4.2, GUIDED_CHANGE_HEADING
(commanded heading). This version uses the latter two instead -- heading
driven by the potential field's direction-to-goal, speed held at cruise --
so there's still no position target to "arrive at and loiter on".

Scope, deliberately narrow (single aircraft, no collision avoidance): see
the conversation this came out of before extending it to multiple vehicles
-- that needs a min-airspeed clamp revisited, since repulsion can otherwise
ask for near-zero speed, which a fixed-wing cannot do.

Before running against SITL, check/edit:
  1. SITL_CONNECTION below -- must match your actual SITL output port.
  2. Whether your SITL spawns on the ground (needs the arm+takeoff roll
     below) or already airborne (skip arm_and_takeoff's takeoff call).
  3. MIN_AIRSPEED_MPS is a placeholder -- set it above this airframe's
     real stall speed / ARSPD_FBW_MIN before this ever nears hardware.

Things this prototype exists to answer empirically -- don't assume, watch
the printed COMMAND_ACK results and telemetry in the SITL console:
  A. Does GUIDED_CHANGE_HEADING get MAV_RESULT_ACCEPTED on this firmware
     (4.6, per this session), and does the vehicle's actual ground track
     match the commanded heading (course-over-ground type, param1=0) or
     does wind/crab angle mean HEADING type (param1=1) tracks better?
  B. Unlike streamed velocity, a GUIDED command is normally a one-shot that
     the vehicle holds until superseded, not something that needs a high
     refresh rate to avoid a stream-loss failsafe -- confirm that's true
     here rather than assuming it, and see what happens on a hard-kill of
     this script mid-flight vs an orderly Ctrl+C (falls back to LOITER
     below).
"""

import csv
import time
from math import atan2, cos, degrees, sin, sqrt

from dronekit import connect, VehicleMode
from pymavlink import mavutil

from locatePosition import geoToCart, cartToGeo
from bezier_curve_multiple import BezierCurveMultiple
from mission_paths import uav_path_csv

# --- Config: edit these for your SITL setup -------------------------------
SITL_CONNECTION = "tcp:127.0.0.1:5762"  # dronekit -> SITL/MAVProxy output port
TAKEOFF_ALT_M = 50
CRUISE_SPEED_MPS = 18          # matches BezierCurveMultiple's own path-shape assumption (self.SPEED)
MIN_AIRSPEED_MPS = 12          # placeholder -- real stall speed / ARSPD_FBW_MIN + margin
COMMAND_SEND_HZ = 2            # guided commands are one-shot/held, not streamed -- see note B above;
                                # this just sets how often we re-evaluate heading toward the goal
WAYPOINT_RADIUS_M = 15         # advance to next goal once real position is this close
GRID_SPACE_M = 60
COVERAGE_AREA_M = 300
CENTER_OFFSET_NORTH_M = 300    # test grid center, this far north of home
UAV_SLOT_ID = 1

HEADING_TYPE_COURSE_OVER_GROUND = 0  # ground-track direction -- matches what the potential field computes
HEADING_TYPE_HEADING = 1             # airframe nose direction -- try this if COG drifts off track under wind


def _on_command_ack(_vehicle, _name, message):
	result_name = mavutil.mavlink.enums["MAV_RESULT"].get(message.result, message.result)
	print(f"[sitl] COMMAND_ACK command={message.command} result={result_name}")


def send_guided_change_heading(vehicle, heading_deg, heading_type=HEADING_TYPE_COURSE_OVER_GROUND):
	msg = vehicle.message_factory.command_long_encode(
		0, 0,
		mavutil.mavlink.MAV_CMD_GUIDED_CHANGE_HEADING,
		0,
		heading_type,       # param1: 0=course over ground, 1=heading
		heading_deg % 360,  # param2: target heading, degrees
		0, 0, 0, 0, 0,      # params 3-7: unused for this command -- confirm via COMMAND_ACK printout
	)
	vehicle.send_mavlink(msg)


def send_change_airspeed(vehicle, speed_mps):
	msg = vehicle.message_factory.command_long_encode(
		0, 0,
		mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
		0,
		0,          # param1: speed type, 0=airspeed
		speed_mps,  # param2: target speed, m/s
		-1,         # param3: throttle %, -1 = no change
		0,          # param4: 0=absolute
		0, 0, 0,
	)
	vehicle.send_mavlink(msg)


def connect_and_prepare():
	print(f"[sitl] connecting to {SITL_CONNECTION} ...")
	vehicle = connect(SITL_CONNECTION, wait_ready=True, timeout=60)
	vehicle.add_message_listener("COMMAND_ACK", _on_command_ack)
	print("[sitl] connected. mode:", vehicle.mode.name, "armed:", vehicle.armed)
	return vehicle


def arm_and_takeoff(vehicle, target_alt):
	print("[sitl] waiting for vehicle to become armable...")
	while not vehicle.is_armable:
		time.sleep(1)
	vehicle.mode = VehicleMode("GUIDED")
	vehicle.armed = True
	while not vehicle.armed:
		print("[sitl] waiting for arming...")
		time.sleep(1)
	print("[sitl] armed. taking off to", target_alt, "m")
	vehicle.simple_takeoff(target_alt)
	while True:
		alt = vehicle.location.global_relative_frame.alt
		print("[sitl] altitude:", alt)
		if alt is not None and alt >= target_alt * 0.9:
			break
		time.sleep(1)


def build_test_search_path(vehicle):
	"""Origin = this vehicle's own home position (no rectangles.yaml needed
	for a SITL prototype). CSV columns match production: (x, y, is_bezier),
	x/y in BezierCurveMultiple's halved cartesian convention."""
	home = vehicle.location.global_frame
	origin = (home.lat, home.lon)
	center_lat, center_lon = cartToGeo(origin, 500000, [0, CENTER_OFFSET_NORTH_M])
	curve = BezierCurveMultiple(
		origin=origin,
		center_latitude=center_lat,
		center_longitude=center_lon,
		num_of_drones=1,
		grid_space=GRID_SPACE_M,
		coverage_area=COVERAGE_AREA_M,
		uav_ids=[UAV_SLOT_ID],
	)
	curve.GridFormation()
	curve.generate_bezier_curve()
	csv_path = uav_path_csv(UAV_SLOT_ID)
	goals = []
	with open(csv_path, newline="") as f:
		for row in csv.reader(f):
			goals.append((float(row[0]), float(row[1]), row[2]))
	print(f"[sitl] generated {len(goals)} waypoints -> {csv_path}")
	return origin, goals


def fly_to_goal_with_heading(vehicle, origin, goal_lat, goal_lon, tick_s):
	"""Command heading + airspeed toward (goal_lat, goal_lon) until the
	vehicle's real GPS position is within WAYPOINT_RADIUS_M -- no simulated
	proxy involved, the reached-check is against live telemetry throughout."""
	send_change_airspeed(vehicle, CRUISE_SPEED_MPS)
	while True:
		cur = vehicle.location.global_relative_frame
		cur_x, cur_y = geoToCart(origin, 500000, [cur.lat, cur.lon])
		goal_x, goal_y = geoToCart(origin, 500000, [goal_lat, goal_lon])
		dx, dy = goal_x - cur_x, goal_y - cur_y
		dist = sqrt(dx * dx + dy * dy)
		if dist <= WAYPOINT_RADIUS_M:
			print(f"[sitl] waypoint reached, dist={dist:.1f} m")
			return
		heading_math = atan2(dy, dx)  # math convention: 0=east, ccw+ (x=east, y=north)
		heading_compass_deg = (90 - degrees(heading_math)) % 360  # -> 0=north, cw+
		send_guided_change_heading(vehicle, heading_compass_deg)
		print(
			f"[sitl] dist={dist:7.1f} m  cmd_heading={heading_compass_deg:6.1f} deg  "
			f"vehicle_heading={vehicle.heading}  airspeed={vehicle.airspeed:.1f}  "
			f"groundspeed={vehicle.groundspeed:.1f}"
		)
		time.sleep(tick_s)


def run_search_heading_prototype():
	vehicle = connect_and_prepare()
	try:
		arm_and_takeoff(vehicle, TAKEOFF_ALT_M)
		origin, goals = build_test_search_path(vehicle)
		vehicle.mode = VehicleMode("GUIDED")
		tick_s = 1.0 / COMMAND_SEND_HZ
		for idx, (gx, gy, is_curve) in enumerate(goals):
			goal_lat, goal_lon = cartToGeo(origin, 500000, [gx * 2, gy * 2])
			print(f"[sitl] -> waypoint {idx + 1}/{len(goals)} curve={is_curve}")
			fly_to_goal_with_heading(vehicle, origin, goal_lat, goal_lon, tick_s)
		print("[sitl] search path complete -- switching to RTL")
		vehicle.mode = VehicleMode("RTL")
	except KeyboardInterrupt:
		print("[sitl] interrupted -- switching to LOITER as an explicit client-side fallback")
		vehicle.mode = VehicleMode("LOITER")
	finally:
		vehicle.close()


if __name__ == "__main__":
	run_search_heading_prototype()
