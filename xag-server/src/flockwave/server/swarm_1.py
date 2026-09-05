import os
import json
import socket
from math import radians, cos, sin, sqrt, atan2
from .search import BezierCurve
from .AutoMission import AutoSplitMission
from .SpecificSplitMission import SpecificSplitMission
from .time import TimeCalculation
from .swarm_protocol import COMMAND_SCHEMA, SENDER_ONLY_STUBS


def fetch_file_content(file_path):
    lines = []
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
            new_lines = file_content.split("\n")

            # Compare new lines with existing lines and append only unique ones
            unique_new_lines = [line for line in new_lines]
            parsed_messages = []
            for line in unique_new_lines:
                if line == "":
                    continue
                time, message = line.split("\t")
                parsed_messages.append({"timestamp": time, "message": message})

            lines.extend(parsed_messages)
    except IOError as error:
        print("Error reading file:", error)
    return lines


SWARM_HOST = os.getenv("SWARM_HOST") or os.getenv("FIXED_WING_SWARM_HOST") or "192.168.6.220"
SWARM_PORT = 12008


class LoggingUDPSocket:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def sendto(self, data, address):
        try:
            printable = data.decode("utf-8") if isinstance(data, bytes) else str(data)
        except Exception:
            printable = repr(data)
        print(f"[SERVER->SWARM] {self.name} {address}: {printable}")
        return self.sock.sendto(data, address)

    def close(self):
        return self.sock.close()


master_udp = LoggingUDPSocket("master_udp")

# Both keys point at the same (SWARM_HOST, SWARM_PORT) now that the swarm
# computer listens on a single consolidated port -- kept as two keys so
# call sites that still say adderss.get(1)/adderss.get(2) don't need editing.
adderss = {1: (SWARM_HOST, SWARM_PORT), 2: (SWARM_HOST, SWARM_PORT)}


def send_command(cmd: str, address_key: int = 2, **params) -> bool:
    """Single JSON-envelope sender. Replaces the previous per-command ad hoc
    comma/underscore string formats with {"cmd": ..., "params": {...}},
    matching swarm_protocol.COMMAND_SCHEMA / SENDER_ONLY_STUBS on both ends.
    """
    if cmd not in COMMAND_SCHEMA and cmd not in SENDER_ONLY_STUBS:
        print(f"[SERVER->SWARM] WARNING: '{cmd}' is not in swarm_protocol.py's schema")
    payload = json.dumps({"cmd": cmd, "params": params}).encode("utf-8")
    master_udp.sendto(payload, adderss.get(address_key))
    return True


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the Earth's surface using the Haversine formula.

    Parameters:
    - lat1, lon1: Latitude and longitude of the first point (in degrees).
    - lat2, lon2: Latitude and longitude of the second point (in degrees).

    Returns:
    - The distance between the two points (in meters).
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371000 * c  # Radius of Earth in meters

    return distance


def calculate_flight_time():
    # Not network I/O, not part of this refactor -- left untouched. Note it
    # references csv_files/flight_time_var globals that are never defined
    # anywhere in this module; calling this today would raise NameError. It
    # is not invoked from socket_response.
    import csv

    global flight_time_var, csv_files
    total_distance = 0
    num_uavs = 0

    for uav, csv_path in csv_files.items():
        lat_lon_points = []
        with open(csv_path, "rt") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header (first row)
            for row in csv_reader:
                lat, lon = map(float, row)
                lat_lon_points.append((lat, lon))

        total_distance_uav = 0
        for i in range(len(lat_lon_points) - 1):
            lat1, lon1 = lat_lon_points[i]
            lat2, lon2 = lat_lon_points[i + 1]
            distance = haversine(lat1, lon1, lat2, lon2)
            total_distance_uav += distance

        total_distance += total_distance_uav
        num_uavs += 1

    average_total_distance = total_distance / num_uavs
    average_speed = 3  # Assume average speed between 4 m/s and 5 m/s
    flight_time_seconds = average_total_distance / average_speed
    flight_time_minutes = flight_time_seconds / 60

    flight_time_var.set("Flight Time = {:.2f} minutes".format(flight_time_minutes))


# ---------------------------------------------------------------------- #
# Real, working commands (COMMAND_SCHEMA)
# ---------------------------------------------------------------------- #


def set_origin(lat, lon):
    return send_command("origin", lat=lat, lon=lon)


def set_geofence():
    return send_command("geofence")


def generate_origin(origin1):
    """Convenience wrapper: not called from socket_response today, but kept
    plumbed and working in case a future GUI control needs to push both the
    mission origin and a geofence refresh together."""
    set_origin(origin1[0], origin1[1])
    set_geofence()
    return True


def _origin_file_path():
    swarm_folder = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env")
    os.makedirs(swarm_folder, exist_ok=True)
    return os.path.join(swarm_folder, "rectangles.yaml")


def _min_corner_origin(points):
    """South-west (min-lat, min-lon) corner of `points`, a [lat, lon] list --
    used to derive a mission-specific origin fresh from its own drawn/center
    area, instead of a hardcoded constant or a separately-set geofence
    origin. Every caller must also send this value to the swarm computer
    (rather than relying on it to recompute/re-read one locally), so the GUI
    preview and the actual flown path always linearize around the same
    point."""
    origin_lat = min(float(p[0]) for p in points)
    origin_lon = min(float(p[1]) for p in points)
    return [origin_lat, origin_lon]


def update_geofence_origin(points):
    """Computes an origin from a user-drawn area on the GCS map (the
    south-west / min-lat,min-lon corner of `points`, a [lat, lon] list),
    writes it to rectangles.yaml, and pushes it to the swarm computer.

    Mirrors the min-corner approach already proven in a sibling fixed-wing
    server's FenceToYAML.compute_origin (no shift margin, matching that
    class's default origin_shift_m=0) -- but only handles the origin, not
    obstacle/no-fly-zone boundary generation, per the requested scope of
    "origin and geofence just need to be dynamic".
    """
    import yaml

    origin_lat, origin_lon = _min_corner_origin(points)

    with open(_origin_file_path(), "w") as f:
        yaml.safe_dump({"origin": [origin_lat, origin_lon]}, f)

    set_origin(origin_lat, origin_lon)
    set_geofence()
    return [origin_lat, origin_lon]


def home_lock():
    return send_command("home_lock")


def home_socket():
    # Documented no-op: the real landing path is landing_mission_send(),
    # triggered by the GUI's "landing" message. This exists so a stray
    # "home" GUI message is acknowledged in swarm-side logs instead of
    # (as before) crashing app.py's socket_response via a `parameters.pop()`
    # bug -- see the "home" branch fix in socket_response.
    return send_command("home")


def search_socket(points, gridspacing, coverage, ids):
    """Sends the real "search" command and returns the same local GUI-preview
    path/time-estimate as before (server-side BezierCurve/TimeCalculation are
    unrelated to and unchanged by the swarm-computer-side rewrite).

    Origin is derived fresh from this mission's own drawn area (min-lat,
    min-lon corner of `points`, same technique as update_geofence_origin)
    instead of a hardcoded constant, and sent explicitly to the swarm
    computer (rather than left for it to read from its own, separately
    maintained, local rectangles.yaml) so the preview and the actual flown
    path always linearize around the identical origin."""
    for num in points:
        num.reverse()
    origin = _min_corner_origin(points)
    curve = BezierCurve(
        origin=origin,
        center_latitude=points[0][0],
        center_longitude=points[0][1],
        coverage_area=coverage,
        grid_space=gridspacing,
        num_of_drones=len(ids),
    )
    curve.GridFormation()
    curve.generate_bezier_curve()
    path = curve.return_latlon()
    print("origin:{} \n center_lat:{} \n center_lon:{} \n coverage:{} \n gridspace:{} \n ids:{}".format(origin,points[0][0],points[0][1],coverage,gridspacing,len(ids)))
    time_sample = TimeCalculation(missions=curve.search_grid, speed=18, loiter_radius=200)
    # for num in points:
    #     num.reverse()
    data = str(
        "search"
        + ","
        + str(points[0][0])
        + ","
        + str(points[0][1])
        + ","
        + str(len(ids))
        + ","
        + str(gridspacing)
        + ","
        + str(coverage)
    )
    print(points, len(ids), gridspacing, coverage)
    master_udp.sendto(data.encode(), adderss.get(2))

    # send_command("search", points=points, grid_spacing=gridspacing,
    #              coverage=coverage, num_uavs=len(ids), origin=origin)
    return path, time_sample.max_time()


def different_alt_socket(initial_alt, alt_diff):
    return send_command("different_altitude", initial_altitude=initial_alt, step=alt_diff)


def same_alt_socket(alt_same):
    # Previously sent only to the legacy hardcoded-IP sockets (ip/
    # 155/160), which the real swarm computer at SWARM_HOST never listens on
    # -- this command had no effect at all before this fix.
    return send_command("same_altitude", altitude=alt_same)


def return_socket():
    # Kept as a documented stub: no matching handler exists on the swarm
    # side today (confirmed by full audit of the receiver's command set).
    return send_command("return")


def specific_bot_goal_socket(uav, lat, lon):
    # Signature change from the previous (drone_num, goal_num): goal_num used
    # to be whatever the caller passed straight into a comma-joined string,
    # which broke as soon as it was a [lat, lon] list (e.g.
    # "specific_bot_goal,3,[13.2, 80.1]" splits into 4 comma fields, not the
    # 3 the receiver expected). Taking lat/lon directly avoids that.
    return send_command("specific_bot_goal", uav=uav, goal=[lat, lon])


def goal_socket(goal_num, direction, radius):
    coords = [[float(x) for x in reversed(sublist)] for sublist in goal_num]
    data = str("goal" + "_" + str(goal_num) + "_" + str(direction) + "_" + str(radius))
    print(data,type(data))
    master_udp.sendto(data.encode(), adderss.get(2))
    # send_command("goal", goals=coords, direction=direction, radius=radius)
    return True


def mavlink_add(uav):
    return send_command("add_uav", sys_id=uav)


def mavlink_remove(uav):
    return send_command("remove_uav", sys_id=uav)


def bot_remove(remove_uav_num):
    # Previously sent only to the legacy hardcoded-IP sockets -- had no
    # effect at all before this fix (same issue as same_alt_socket).
    return send_command("remove_bot", sys_id=remove_uav_num)


def master(master_num):
    # Multi-companion-computer master election is dead code (removed on the
    # swarm side); "master"'s only real effect there is now identical to
    # add_uav, so this no longer also calls mavlink_add() locally -- the
    # swarm-side handler does that itself.
    return send_command("master", sys_id=master_num)


def stop_socket():
    return send_command("stop", address_key=1)


def landing_mission_send(mission):
    for num in mission:
        num.reverse()
    return send_command("landing", return_points=mission)


def navigate(center_latlon, gridspacing, coverage, ids):
    lat, lon = center_latlon[0][1], center_latlon[0][0]
    # Same min-corner-of-the-drawn-area technique as search_socket, derived
    # from this mission's own single point instead of a hardcoded/geofence
    # origin (min-corner of a single point is just that point).
    origin = _min_corner_origin([[lat, lon]])
    curve = BezierCurve(
        origin=origin,
        center_latitude=lat,
        center_longitude=lon,
        coverage_area=coverage,
        grid_space=gridspacing,
        num_of_drones=1,
    )
    curve.GridFormation()
    curve.generate_bezier_curve()
    path = curve.return_latlon()
    time_sample = TimeCalculation(missions=curve.search_grid, speed=18, loiter_radius=200)

    send_command("navigate", center=[lat, lon], grid_spacing=gridspacing,
                 coverage=coverage, num_uavs=len(ids), origin=origin)
    return path, time_sample.max_time()


def loiter(center_latlon, direction, radius):
    lat, lon = center_latlon[0][1], center_latlon[0][0]
    return send_command("loiter", center=[lat, lon], direction=direction, radius=radius)


def skip_point(skip_waypoint):
    # Previously sent to adderss[2] while the swarm side only ever listened
    # for it on the OTHER port (12002) -- had no effect at all before this
    # fix. The consolidated single-port design on the swarm side means this
    # is now just another JSON command, handled as a mid-mission interrupt.
    return send_command("skip_waypoint", waypoint=skip_waypoint)


def splitmission(center_latlon, uavs, gridspace, coverage):
    for latlon in center_latlon:
        latlon.reverse()
    # Same min-corner-of-the-drawn-area technique as search_socket, derived
    # from this mission's own centers instead of AutoSplitMission's previous
    # hardcoded origin.
    origin = _min_corner_origin(center_latlon)
    split = AutoSplitMission(
        origin=origin,
        center_lat_lons=center_latlon,
        coverage_area=coverage,
        num_of_drones=len(uavs),
        grid_spacing=gridspace,
    )
    path = split.return_latlon()

    send_command("split", centers=center_latlon, num_uavs=len(uavs),
                 grid_spacing=gridspace, coverage=coverage, origin=origin)
    return path


def specificsplit(center_latlon, uavs, gridspace, coverage):
    grid = [gridspace for _ in uavs]
    coverageSpace = [coverage for _ in uavs]
    origin = _min_corner_origin(center_latlon)
    # Preview must be generated with the same per-group algorithm the
    # swarm-computer side's specificsplit_ handler uses (SpecificSplitMission),
    # not AutoSplitMission (that's the group-split algorithm) -- otherwise the
    # GUI preview doesn't match what actually gets flown.
    split = SpecificSplitMission(
        origin=origin,
        center_lat_lons=center_latlon,
        drone_array=uavs,
        grid_spacing=grid,
        coverage_area=coverageSpace,
    )
    waypoints = split.GroupSplitting(
        center_lat_lons=center_latlon,
        drone_array=uavs,
        grid_spacing=grid,
        coverage_area=coverageSpace,
    )
    path = [[[float(lon), float(lat)] for lon, lat in group] for group in waypoints]
    time_sample = TimeCalculation(missions=split.waypoints, speed=20, loiter_radius=200)

    send_command("specificsplit", centers=center_latlon, uav_groups=uavs,
                 grid_spacing=grid, coverage=coverageSpace, origin=origin)
    return path, time_sample.max_time()


def takeoff(altitude):
    """Plumbed for manual/testing use of the swarm-computer's real "takeoff"
    handler over this protocol. NOT wired to any GUI action -- the GUI's
    takeoff button goes through the separate X-UAV-TAKEOFF / dispatch_to_uavs
    path, untouched by this refactor."""
    return send_command("takeoff", altitude=altitude)


def group_split(uavs, lat, lon):
    """No GUI/app.py sender exists for this today; kept plumbed since the
    swarm-computer side has a real handler for it."""
    return send_command("group_split", uavs=uavs, goal=[lat, lon])


def grid_path_planning(center, num_uavs, grid_spacing, coverage):
    """No GUI/app.py sender exists for this today; kept plumbed since the
    swarm-computer side has a real handler for it."""
    return send_command("grid_path_planning", center=center, num_uavs=num_uavs,
                         grid_spacing=grid_spacing, coverage=coverage)


def store_uav_pos():
    """No GUI/app.py sender exists for this today; kept plumbed since the
    swarm-computer side has a real handler for it."""
    return send_command("store_uav_pos")


# ---------------------------------------------------------------------- #
# Documented stubs (SENDER_ONLY_STUBS): no matching handler exists on the
# swarm-computer side for any of these, whether reachable from the GUI or
# not. Kept as explicit no-op-on-the-far-end senders per product decision,
# rather than deleted, so the intent stays documented for future revival.
# Each previously fanned out to a set of hardcoded per-drone IP sockets
# (ip/155/160) that the real swarm computer never listens on;
# that ~110 lines of dead socket bookkeeping is removed.
# ---------------------------------------------------------------------- #


def clear_csv():
    return send_command("clear_csv")


def start_socket():
    return send_command("start")


def start1_socket():
    return send_command("start1")


def select_plot(filename):
    if filename != "":
        return send_command("select_plot", filename=filename)
    return False


def share_data_func():
    from flockwave.server.socket.globalVariable import (
        get_goal_table,
        get_return_goal_table,
        get_grid_path_table,
    )

    grid_path_table = get_grid_path_table()
    goal_table = get_goal_table()
    if get_return_goal_table() is not None:
        goal_table = goal_table + get_return_goal_table()
    return send_command("share_data")


def disperse_socket():
    return send_command("disperse")


def aggregate_socket():
    return send_command("aggregate")


def home_goto_socket():
    return send_command("home_goto")


def rtl_socket():
    return send_command("rtl")


def takeoff_socket(alt):
    # Distinct from the real `takeoff()` schema entry above -- this is the
    # legacy sender that was never wired to a GUI action and has no matching
    # swarm-side handler; namespaced as "legacy_takeoff" so it can't collide.
    return send_command("legacy_takeoff", alt=alt)


def send_alts(alts):
    return send_command("send_alts", alts=alts)


def airport_selection(filename):
    return send_command("airport_selection", filename=filename)
