import sys, os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import swarm_tasks
import time
from swarm_tasks.simulation import simulation as sim
from swarm_tasks.simulation import visualizer as viz
import swarm_tasks.controllers.potential_field as potf
from swarm_tasks.modules.dispersion import disp_field
from swarm_tasks.tasks import area_coverage as cvg
from math import radians, sin, cos, sqrt, atan2, asin, degrees
from dronekit import connect, VehicleMode, LocationGlobalRelative
from bezier_curve import BezierCurve
from groupsplitauto import AutoSplitMission
from bezier_curve_multiple import BezierCurveMultiple
from groupsplitspecific import SpecificSplitMission
import socket, json, csv, threading, yaml, shutil, traceback
from shapely.geometry import Polygon
import locatePosition
from mission_paths import uav_path_csv, snapshot_uav_path_csv
import netifaces, wmi

swarm_tasks.utils.robot.DEFAULT_NEIGHBOURHOOD_VAL = 7
swarm_tasks.utils.robot.DEFAULT_SIZE = 0.4
swarm_tasks.utils.robot.MAX_SPEED = 1.5
swarm_tasks.utils.robot.MAX_ANGULAR: 0.3
"""
file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
file_server_address = ('', 12003)  #receive from .....rx.py
file_sock.bind(file_server_address)

graph_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
graph_server_address = ('{}', 12009)  #receive from .....rx.py
"""

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ("", 12008)  # receive from .....rx.py
sock2.bind(server_address2)

sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ("", 12002)  # receive from .....rx.py
sock3.bind(server_address3)
"""
uav1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav1_server_address = ('192.168.6.151', 12002)  #receive from .....rx.py
uav2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav2_server_address = ('192.168.6.152', 12002)  #receive from .....rx.py
uav3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav3_server_address = ('192.168.6.153', 12002)
#uav4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#uav4_server_address = ('192.168.0.153', 12002)
#uav5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#uav5_server_address = ('192.168.0.153', 12002)
"""
goal_table = []
file_name = ""
master_num = 0
master_flag = False
cwd = os.getcwd()

same_height = 100
different_height = [200, 210, 220, 230, 240, 310, 300, 310, 300, 310]
home_height = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]

# try:
# 	index,address=sock2.recvfrom(1024)
# 	print("data",index)
# 	decoded_index = index.decode('utf-8')
# 	data1, height,step = decoded_index.split(",")
# 	same_alt_flag=False
# 	for h in range(10):
# 		different_height[h] = int(height) + int(step) * h
# 	print("different_height",different_height)
# 	index="data"
# except Exception as e:
# 	print("Exception", e)
# 	pass

# sock2 is now owned by the dedicated _command_listener thread (added
# below, after collision_thread) -- it mirrors collision_thread's
# blocking sock3 read, so sock2 stays blocking here (no setblocking(0)).
"""			
try:
	index,address=sock3.recvfrom(1024)
	print("data",index)
	decoded_index = index.decode('utf-8') 
	print("decoded_index",decoded_index)
	m,master_num=decoded_index.split("-")
	print("m,master_num",m,master_num)
	if(int(master_num)==3):
		master_flag=True
	print("master_flag",master_flag)
		
except:
	pass

while True:
	try:
		data,address=file_sock.recvfrom(1024)
		print("data",data)
		decoded_index = data.decode('utf-8') 
		print("decoded_index",decoded_index)
		file_name=decoded_index
		break
			
	except:
		pass
"""
master_num == 3
master_flag = True
file_name = None  # no site preset -- operator draws a fence when enabling swarm

disperse_multiple_goals = []
start_multiple_goals = []
return_multiple_goals = []
goal_points = []
agg_goal_point = []
removed_uav_homepos_array = []

nextwaypoint = 0


def read_origin(filepath):
    """Same approach copter_swarm.py uses: read origin straight from the
    persisted rectangles.yaml on disk at startup, so it's already valid by
    the time the arm+altitude wait loop calls fetch_location() -- no
    hardcoded per-site preset, no polling required."""
    print("Reading YAML from:", filepath)
    with open(filepath) as f:
        data = yaml.safe_load(f)
    origin = data.get("origin")
    if isinstance(origin, str):
        origin = origin.strip("()")
        lat, lon = origin.split(",")
        origin = (float(lat), float(lon))
    return origin


rectangles_path = os.path.join(
    os.path.expanduser("~"), "Documents", "swarm_env", "rectangles.yaml"
)
try:
    origin = read_origin(rectangles_path)
    print("Origin loaded from rectangles.yaml:", origin)
except Exception as e:
    origin = None
    print(
        f"No rectangles.yaml yet at {rectangles_path} ({e}) -- origin will be set once a fence is drawn"
    )

"""
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('{}', 12005)  #receive from .....rx.py

# Bind the socket to the port
remove_bot_server_address = ('{}', 12001)  #receive from .....rx.py

sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address4 = ('', 12011)  #receive from .....rx.py
sock.bind(server_address4)
"""
num_bots = 10
vehicles = []
port_array = [14551, 14552, 14553, 14554, 14555, 14556, 14557, 14558, 14559, 14560]
"""
port_dict = {
    5:14551,
    7:14552,
    8:14553,
    11:14554,
    14:14555,
    15:14556,
    20:14557,
    22:14558,
    24:14559,
    25:14560
}
"""
port_dict = {
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

# Print the dictionary to verify
print(port_dict)

pos_array = []
heartbeat_ip = [
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
heartbeat_ip_timeout = [30] * 10
goal_path_csv_array = []
goal_path_csv_array_flag = False
skip_wp_flag = False
next_wp = 0


def get_wifi_ip(iface_map):
    interfaces = netifaces.interfaces()
    # print(interfaces)
    for iface in netifaces.interfaces():
        try:
            # print(iface,iface_map[iface])
            # if iface in iface_map:
            adapter = iface_map[iface]
            # print(adapter)
            addrs = netifaces.ifaddresses(iface)
            # print(addrs)
            ipv4_info = addrs.get(netifaces.AF_INET, [])
            for addr in ipv4_info:
                ip = addr.get("addr")
                if (
                    ip
                    and (
                        adapter == "Ethernet"
                        or adapter == "Wi-Fi"
                        or iface == "eth0"
                        or iface == "ensp20"
                        or iface == "wlan0"
                    )
                    and ip.startswith("192.168.")
                ):
                    return "192.168.2.117"
        except Exception as e:
            print(f"Error on interface {iface}: {e}")
    return None


def get_interface_mapping():
    c = wmi.WMI()
    # print(c.Win32_NetworkAdapter()[1])
    mappings = {}
    for nic in c.Win32_NetworkAdapter():
        # print(nic)
        if nic.GUID:
            mappings[nic.GUID.upper()] = nic.NetConnectionID or nic.Name
            # return get_wifi_ip(mappings)
    return "172.26.96.1"


def vehicle_collision_moniter_receive():
    global index
    global vehicles
    global slave_heal_ip, master_flag, master_num, pos_array, home_pos, uav_home_pos, skip_wp_flag, next_wp
    while 1:
        index, address = sock3.recvfrom(1024)
        print("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", index)
        decoded_index = index.decode("utf-8")
        print("decoded_index", decoded_index)
        if decoded_index.startswith("master"):
            m, master_num = decoded_index.split("-")
            print("m,master_num", m, master_num)
            msg = "Drone 3 master_num " + str(master_num) + " data received"
            if int(master_num) == 3:
                if master_flag:
                    pass
                else:
                    master_flag = True
                    CHECK_network_connection()
                    vehicle_connection()
                    fetch_location()
                    s = sim.Simulation(
                        uav_home_pos, num_bots=len(vehicles), env_name=file_name
                    )
            else:
                master_flag = False

            index = "data"
            data = "data"
            msg = "master_num " + str(master_num)
            print("master_flag", master_flag)

        if decoded_index.startswith("pos_array"):
            message = decoded_index[:9]  # Assuming "home_pos" is 8 characters long
            array_data = decoded_index[9:]
            print("pos_array", pos_array)
            pos_array = json.loads(array_data)
            print("pos_array", pos_array)
            index = "data"
            msg = "UAV 1 connected with " + str(len(pos_array)) + " vehicles"
            print("master_flag", master_flag)
        if decoded_index.startswith("home_pos"):
            message = decoded_index[:8]  # Assuming "home_pos" is 8 characters long
            home_pos = decoded_index[8:]
            print("home_pos", home_pos)
            home_pos = json.loads(home_pos)
            print("home_pos", home_pos)

        if decoded_index.startswith("uav_home_pos"):
            if master_flag:
                pass
            else:
                message = decoded_index[:12]  # Assuming "home_pos" is 8 characters long
                uav_home_pos = decoded_index[12:]
                print("uav_home_pos", uav_home_pos)
                uav_home_pos = json.loads(uav_home_pos)
                print("uav_home_pos", uav_home_pos)
        if decoded_index.startswith("skip_wp"):
            print("decoded_index", decoded_index)
            c, next_wp = decoded_index.split(",")
            print("c,next_wp", c, next_wp)
            next_wp = int(next_wp)
            print("next_wp", next_wp)
            skip_wp_flag = True
            print("skip_wp_flag", skip_wp_flag)


collision_thread = threading.Thread(target=vehicle_collision_moniter_receive)
collision_thread.daemon = True
collision_thread.start()


class _CommandMailbox:
    """Thread-safe single-slot mailbox for the latest not-yet-consumed
    sock2 command. Mirrors the sock3/collision_thread/index pattern
    already used above: plain attribute writes are atomic under the
    GIL, so no lock is needed. seq lets a mission loop tell a command
    newer than the one it is currently running apart from the command
    it is currently running.
    """

    def __init__(self):
        self.seq = 0
        self.data = None
        self.address = None


_pending_command = _CommandMailbox()


def _command_listener():
    while 1:
        data, address = sock2.recvfrom(1050)
        _pending_command.data = data
        _pending_command.address = address
        _pending_command.seq += 1


command_listener_thread = threading.Thread(target=_command_listener)
command_listener_thread.daemon = True
command_listener_thread.start()


class MissionPreempted(Exception):
    """Raised from inside a mission-flying loop (by
    check_for_new_command) when a command newer than the one it started
    with has arrived on sock2 mid-mission. Carries the preempting
    command so the outer dispatch loop can process it immediately
    instead of waiting for the interrupted mission to finish."""

    def __init__(self, data, address):
        self.data = data
        self.address = address


# Ported from individual-uav-access-add-remove (goal/add/remove concurrency
# slice only -- see check_for_new_command below for what still preempts).
_handled_concurrent_command_seq = 0
uav_registry = {}  # sys_id -> stable vehicle/topology state
uav_task_state = {}  # sys_id -> IDLE/GOAL/SEARCH/SPLIT/SPECIFIC_SPLIT
pending_work_queue = []  # unfinished search/split segments awaiting reassignment
# Adding/removing a UAV changes the index used by *every* fleet-aligned list.
# Keep it mutually exclusive with the background task driver, otherwise the
# driver can read vehicle[i] while another thread has just compacted it.
swarm_topology_lock = threading.RLock()


def handle_concurrent_goal_command(command_data):
    if not command_data.startswith(b"goal"):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        msg_parts = decoded_index.split("_")
        if len(msg_parts) < 5:
            return False
        goal_latlon = json.loads(msg_parts[1])
        selected_uav_ids = parse_selected_uav_ids(msg_parts[4])
        if not selected_uav_ids:
            return False
        selected_indexes = selected_swarm_indexes(selected_uav_ids)
        goal_xy = []
        for goal_point in goal_latlon:
            x, y = locatePosition.geoToCart(
                origin, endDistance, [float(goal_point[0]), float(goal_point[1])]
            )
            goal_xy.append((x / 2, y / 2))
        guided_circle_direction = msg_parts[2]
        guided_circle_radius = msg_parts[3]
        assign_goal_tasks(
            selected_indexes, goal_xy, guided_circle_radius, guided_circle_direction
        )
        print(
            "[concurrent goal] accepted during running mission",
            selected_uav_ids,
            selected_indexes,
        )
        return True
    except Exception as e:
        print("[concurrent goal] failed", e)
        return False


def start_search_mission(decoded_index):
    """Parses a 'search,...' command and registers it as a background
    mission task for whichever UAV subset it targets, without touching
    the foreground dispatch loop. Only used for the concurrent-intercept
    path (search arriving while something else is already running) --
    a fresh top-level search dispatch still uses its own foreground loop,
    unchanged."""
    msg_parts = decoded_index.split(",", 6)
    selected_uav_raw = msg_parts[6] if len(msg_parts) > 6 else None
    f, center_lat, center_lon, num_uavs, grid_space, coverage_area = msg_parts[:6]
    selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
    if not selected_uav_ids:
        return False
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    effective_num_uavs = max(1, len(selected_indexes))
    curve = BezierCurveMultiple(
        origin,
        float(center_lat),
        float(center_lon),
        effective_num_uavs,
        int(grid_space),
        int(coverage_area),
        uav_ids=selected_uav_ids,
    )
    curve.GridFormation()
    curve.generate_bezier_curve()
    csv_paths_by_index = {}
    for path_slot, bot_index in enumerate(selected_indexes):
        csv_paths_by_index[bot_index] = uav_path_csv(selected_uav_ids[path_slot])
    assign_mission_tasks(csv_paths_by_index, "search")
    print(
        "[concurrent search] accepted during running mission",
        selected_uav_ids,
        selected_indexes,
    )
    return True


def start_split_mission(decoded_index):
    """Parses a 'split,...' or 'specificsplit,...' command and registers it
    as a background mission task for whichever UAV subset it targets, same
    concurrent-intercept-only role as start_search_mission above."""
    if decoded_index.startswith("specificsplit"):
        msg_parts = decoded_index.split("_")
        center_lat_lon_array = json.loads(msg_parts[1])
        uav_array = json.loads(msg_parts[2])
        grid_space = json.loads(msg_parts[3])
        coverage_area = json.loads(msg_parts[4])
        assigned_uav_ids = [int(u) for group in uav_array for u in group]
        if not assigned_uav_ids or not set(assigned_uav_ids).issubset(set(pos_array)):
            print(
                "[concurrent specificsplit] rejected: group assignment",
                set(assigned_uav_ids),
                "not a subset of connected pos_array",
                set(pos_array),
            )
            return False
        selected_uav_ids = assigned_uav_ids
        split = SpecificSplitMission(
            origin=origin,
            center_lat_lons=center_lat_lon_array,
            drone_array=uav_array,
            grid_spacing=grid_space,
            coverage_area=coverage_area,
        )
        split.GroupSplitting(
            center_lat_lons=center_lat_lon_array,
            drone_array=uav_array,
            grid_spacing=grid_space,
            coverage_area=coverage_area,
        )
    else:
        msg_parts = decoded_index.split("_")
        selected_uav_ids = [int(u) for u in json.loads(msg_parts[2])]
        grid_space = json.loads(msg_parts[3])
        coverage_area = json.loads(msg_parts[4])
        center_lat_lon_array = json.loads(msg_parts[1])
        if not selected_uav_ids or not set(selected_uav_ids).issubset(set(pos_array)):
            print(
                "[concurrent split] rejected: GCS selection",
                set(selected_uav_ids),
                "not a subset of connected pos_array",
                set(pos_array),
            )
            return False
        split = AutoSplitMission(
            origin=origin,
            center_lat_lons=center_lat_lon_array,
            drone_list=selected_uav_ids,
            grid_spacing=int(grid_space),
            coverage_area=int(coverage_area),
        )
        split.GroupSplitting(
            center_lat_lons=center_lat_lon_array,
            num_of_drones=len(selected_uav_ids),
            grid_spacing=int(grid_space),
            coverage_area=int(coverage_area),
        )
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    csv_paths_by_index = {}
    for bot_index in selected_indexes:
        uav_id = pos_array[bot_index]
        csv_paths_by_index[bot_index] = uav_path_csv(uav_id)
    assign_mission_tasks(csv_paths_by_index, "split")
    print(
        "[concurrent split] accepted during running mission",
        selected_uav_ids,
        selected_indexes,
    )
    return True


def handle_concurrent_search_command(command_data):
    if not command_data.startswith(b"search"):
        return False
    try:
        return start_search_mission(command_data.decode("utf-8"))
    except Exception as e:
        print("[concurrent search] failed", e)
        return False


def handle_concurrent_split_command(command_data):
    if not (
        command_data.startswith(b"split") or command_data.startswith(b"specificsplit")
    ):
        return False
    try:
        return start_split_mission(command_data.decode("utf-8"))
    except Exception as e:
        print("[concurrent split] failed", e)
        return False


def apply_different_heights(decoded_index):
    """Parses a 'different,{height},{step}[,{ids}]' command and updates the
    shared different_height[] array for the targeted bot indexes (or every
    connected UAV if no ids given). Height is computed from each bot's real
    pos_array index (height + step*bot_index), not its position within the
    selection, so a partial re-stagger stays consistent with the whole
    fleet's existing layering instead of restarting from the base altitude.

    Critically, this never touches (x,y)/task state for bots that already
    have an active goal/mission/guided_circle task -- their own
    _drive_vehicle_towards() call reads different_height[i] fresh every
    tick, so updating it here alone re-targets their altitude on their very
    next drive tick with zero interruption to whatever they were already
    flying. Only bots with no active task get an explicit altitude task
    assigned, since nothing would otherwise command them to actually climb
    or descend."""
    global same_alt_flag
    parts = decoded_index.split(",", 3)
    height = int(parts[1])
    step = int(parts[2])
    selected_uav_raw = parts[3] if len(parts) > 3 else None
    selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    same_alt_flag = False
    for bot_index in selected_indexes:
        if bot_index < len(different_height):
            different_height[bot_index] = height + step * bot_index
    print(
        "[different] updated different_height",
        different_height,
        "for indexes",
        selected_indexes,
    )
    with active_goal_tasks_lock:
        busy_indexes = set(active_goal_tasks.keys())
    idle_indexes = [i for i in selected_indexes if i not in busy_indexes]
    if idle_indexes:
        assign_altitude_tasks(idle_indexes)
    return True


def assign_altitude_tasks(selected_indexes):
    with active_goal_tasks_lock:
        for bot_index in selected_indexes:
            active_goal_tasks[bot_index] = {
                "type": "altitude",
            }
    print(
        "[altitude-task] assigned (idle bots climbing/descending in place)",
        selected_indexes,
    )


def handle_concurrent_different_command(command_data):
    if not command_data.startswith(b"different"):
        return False
    try:
        return apply_different_heights(command_data.decode("utf-8"))
    except Exception as e:
        print("[concurrent different] failed", e)
        return False


GPS_RESYNC_INTERVAL = 2.0  # seconds between real-GPS corrections per bot
_last_gps_resync = {}  # bot index -> monotonic time.time() of last correction


def _resync_bot_position(i, force=False):
    """Nudge s.swarm[i].x/y (and robots[i]) toward vehicle i's live GPS.

    Runs at most once every GPS_RESYNC_INTERVAL seconds per bot (unless
    force=True) so real telemetry only ever *corrects* the swarm simulation
    periodically -- the potential-field motion (Bot.step()/move(), driven
    every fast tick by _goal_task_runner) is what actually moves the bots
    according to swarm logic in between. Resyncing on every tick instead of
    periodically would overwrite that motion before it ever accumulates,
    which defeats the swarm logic entirely.

    Only ever call this for an index from the thread that currently owns
    that bot's position (either _goal_task_runner, for indices it is
    actively driving via active_goal_tasks, or the main dispatch loop, for
    everything else). Bot.step()/move() do an unsynchronized read-then-write
    of self.x/self.y, so writing to the same index from two threads at once
    races it -- whichever write lands last silently wins, which either
    discards the GPS correction or discards an in-flight simulated step.
    """
    global robots
    if origin is None or i >= len(vehicles) or i >= len(s.swarm) or i >= len(robots):
        return
    now = time.time()
    if not force and (now - _last_gps_resync.get(i, 0)) < GPS_RESYNC_INTERVAL:
        return
    try:
        lat = vehicles[i].location.global_relative_frame.lat
        lon = vehicles[i].location.global_relative_frame.lon
        if lat is None or lon is None:
            return
        x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
        s.swarm[i].x = x / 2
        s.swarm[i].y = y / 2
        robots[i] = (x / 2, y / 2)
        _last_gps_resync[i] = now
    except Exception as e:
        print("[position-sync] failed for vehicle", i, e)


def sync_swarm_with_telemetry():
    """Refresh idle bots' simulated (x, y) from their vehicle's live GPS.

    The potential-field collision avoidance in utils/robot.py only ever
    moves s.swarm[i].x/y by dead-reckoned steps (Bot.step()); it never reads
    real telemetry. Without this resync the simulated position drifts away
    from where the aircraft actually is, so collision checks stop reflecting
    reality. Called once per dispatched command (mirrors copter_swarm.py).

    Bots with an active_goal_tasks entry are owned by _goal_task_runner for
    the duration of that task and are resynced there every cycle instead --
    see _resync_bot_position's docstring for why writing to them here too
    would race it.
    """
    if origin is None:
        return
    with active_goal_tasks_lock:
        busy = set(active_goal_tasks.keys())
    count = min(len(vehicles), len(s.swarm), len(robots))
    for i in range(count):
        if i not in busy:
            # Idle bots have no swarm-logic motion in progress to protect,
            # so always take the freshest GPS fix when a new command starts.
            _resync_bot_position(i, force=True)


def live_gps_plot_points():
    """Read every vehicle's current GPS fix, fresh, purely for plotting.

    Unlike _resync_bot_position this is read-only (never touches
    s.swarm[i].x/y) and is not throttled by GPS_RESYNC_INTERVAL, so the GPS
    overlay on the sim plot moves in real time even between the periodic
    simulation-state corrections. Returns a list aligned with s.swarm, with
    None for any bot whose fix isn't available yet.
    """
    points = [None] * len(vehicles)
    if origin is None:
        return points
    for i in range(len(vehicles)):
        try:
            lat = vehicles[i].location.global_relative_frame.lat
            lon = vehicles[i].location.global_relative_frame.lon
            if lat is None or lon is None:
                continue
            x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
            points[i] = (x / 2, y / 2)
        except Exception:
            pass
    return points


def print_sim_vs_real_latlon(indexes, label=""):
    """For each bot index, print the simulated position converted to
    lat/lon, the vehicle's real dronekit lat/lon, and the difference
    between them -- so a mismatch between where the sim thinks a bot is and
    where the real aircraft actually is (the thing that can cause a real
    UAV to circle/orbit near a goal that the sim has already smoothly
    reached) is directly visible and quantified, not just visually implied
    by the plot overlay.
    """
    if origin is None:
        return
    for i in indexes:
        if i >= len(vehicles) or i >= len(s.swarm):
            continue
        try:
            sim_lat, sim_lon = locatePosition.cartToGeo(
                origin, endDistance, [s.swarm[i].x * 2, s.swarm[i].y * 2]
            )
            real_lat = vehicles[i].location.global_relative_frame.lat
            real_lon = vehicles[i].location.global_relative_frame.lon
            if real_lat is None or real_lon is None:
                continue
            distance = locatePosition.distance_bearing(
                real_lat, real_lon, sim_lat, sim_lon
            )
            # print(
            # 	f"[latlon-mismatch]{(' ' + label) if label else ''} UAV {pos_array[i]}: "
            # 	f"sim=({sim_lat:.7f},{sim_lon:.7f}) real=({real_lat:.7f},{real_lon:.7f}) "
            # 	f"diff=({distance:.2f} m)"
            # )
        except Exception as e:
            print("[latlon-mismatch] failed for vehicle", i, e)
    return distance


def print_sim_vs_real_latlon_with_bot(b, i, label=""):
    """For each bot index, print the simulated position converted to
    lat/lon, the vehicle's real dronekit lat/lon, and the difference
    between them -- so a mismatch between where the sim thinks a bot is and
    where the real aircraft actually is (the thing that can cause a real
    UAV to circle/orbit near a goal that the sim has already smoothly
    reached) is directly visible and quantified, not just visually implied
    by the plot overlay.
    """
    if origin is None:
        return 0
    try:
        sim_lat, sim_lon = locatePosition.cartToGeo(
            origin, endDistance, [b.x * 2, b.y * 2]
        )
        real_lat = vehicles[i].location.global_relative_frame.lat
        real_lon = vehicles[i].location.global_relative_frame.lon

        distance = locatePosition.distance_bearing(real_lat, real_lon, sim_lat, sim_lon)

    except Exception as e:
        print("[latlon-mismatch] failed for vehicle", i, e)
        return float("inf")
    return distance


# The swarm simulator is a virtual leader for each fixed-wing aircraft.  Do
# not stop that leader when it gets ahead: a fixed-wing vehicle can loiter
# around a frozen target and never reduce the error enough to restart it.
# But an unbounded leader is just as broken the other way: with nothing
# capping how far it can run ahead, it consumes intermediate curve/grid
# points (whose hand-off is bot-only, see uav_reached_waypoint()) far
# faster than the real aircraft can fly the equivalent ground distance,
# so the aircraft ends up beelining toward a point several indices ahead
# instead of tracing the intended path. The leader therefore advances at
# full step below UAV_FOLLOW_WINDOW_M of lead, and drops to a nonzero
# floor (UAV_MIN_VIRTUAL_STEP, never 0 -- a literal freeze is what caused
# the original loiter bug) once past it, so a real aircraft flying at any
# normal cruise speed keeps closing the gap. UAV_MAX_VIRTUAL_LEAD_M is not
# a separately enforced hard stop; it documents the lead this floor is
# sized to keep the aircraft within under normal flight. See
# advance_bot_with_uav_pacing(). Distances are metres (the same units
# returned by distance_bearing).
UAV_MAX_VIRTUAL_STEP = 1.0
UAV_FOLLOW_WINDOW_M = 150.0  # below this lead, advance at full pace
UAV_MAX_VIRTUAL_LEAD_M = 300.0  # expected worst-case lead at UAV_MIN_VIRTUAL_STEP
UAV_MIN_VIRTUAL_STEP = 0.15  # floor once over UAV_FOLLOW_WINDOW_M -- never 0
# This is only a maximum for original grid waypoints. It is capped by the
# next leg length, and is never used for dense Bezier interpolation points.
SEARCH_UAV_FLYBY_RADIUS_M = 100.0
UAV_FINAL_WAYPOINT_RADIUS_M = 75.0
UAV_CURVE_POINT_SWITCH_RADIUS = 2.0  # sim units, bot-only progression
# Forward guidance distance for fixed-wing aircraft on a Bezier turn, in
# real (unscaled) metres. The bot still follows each sample for CVG safety.
UAV_CURVE_LOOKAHEAD_M = 45.0
# Print real UAV-to-bot separation for every moving command.  This prints once
# per bot control tick; set False only when a quiet console is required.
BOT_SYNC_DEBUG = True


def advance_bot_with_uav_pacing(i, b, goal, label=""):
    """Advance the virtual leader at full pace, with a bounded lead.

    A large UAV--bot separation can be lateral (for example, while a
    fixed-wing UAV follows a 200 m turn), not evidence that the virtual bot
    is ahead, so separation must never be allowed to freeze the moving
    GUIDED target -- that reproduces the original loiter-on-arrival bug.
    But it also must not be unbounded: past UAV_FOLLOW_WINDOW_M the leader
    is consuming intermediate points faster than the aircraft can reach
    them, so it drops to a nonzero floor (UAV_MIN_VIRTUAL_STEP, never 0)
    until the aircraft closes back up.
    """
    dis = print_sim_vs_real_latlon_with_bot(b, i, label=label)
    if dis <= UAV_FOLLOW_WINDOW_M:
        step_size = UAV_MAX_VIRTUAL_STEP  # normal: full pace, no lag
    else:
        step_size = UAV_MIN_VIRTUAL_STEP  # over-lead: crawl, never freeze

    before_x, before_y = b.x, b.y
    cmd = cvg.goal_area_cvg(i, b, goal)
    cmd += disp_field(b, neighbourhood_radius=100)
    cmd.exec(b, step_size=step_size)
    moved_m = 2.0 * math.hypot(b.x - before_x, b.y - before_y)
    if BOT_SYNC_DEBUG:
        goal_distance_m = 2.0 * math.hypot(goal[0] - b.x, goal[1] - b.y)
        print(
            f"[bot-sync] label={label} bot={i} "
            f"dis={dis:.1f}m step={step_size:.2f} cmd_speed={cmd.speed:.3f} "
            f"moved={moved_m:.2f}m goal_dist={goal_distance_m:.2f}m "
            f"pos=({b.x:.2f},{b.y:.2f}) goal=({goal[0]:.2f},{goal[1]:.2f})"
        )
    if moved_m < 1e-6:
        # A constant step cannot move a bot when the combined field has no
        # magnitude or Bot.step() rejects its proposed position as occupied.
        # Log only the stalled case so a live search is not flooded.
        print(
            f"[bot-stall] bot={i} label={label} cmd_speed={cmd.speed:.3f} "
            f"step={step_size:.2f} pos=({before_x:.2f},{before_y:.2f}) "
            f"goal=({goal[0]:.2f},{goal[1]:.2f})"
        )

    return dis, step_size


def uav_distance_to_goal(i, goal):
    """Return live UAV-to-goal distance in metres, or None without telemetry."""
    if not master_flag or i >= len(vehicles) or origin is None:
        return None
    try:
        goal_lat, goal_lon = locatePosition.cartToGeo(
            origin, endDistance, [goal[0] * 2, goal[1] * 2]
        )
        frame = vehicles[i].location.global_relative_frame
        if frame.lat is None or frame.lon is None:
            return None
        return locatePosition.distance_bearing(frame.lat, frame.lon, goal_lat, goal_lon)
    except Exception as e:
        print("[uav-flyby] distance unavailable for vehicle", i, e)
        return None


def waypoint_flyby_radius(goal, next_goal=None, is_final=False):
    """Return a fly-by radius that cannot consume the following short leg."""
    radius = UAV_FINAL_WAYPOINT_RADIUS_M if is_final else SEARCH_UAV_FLYBY_RADIUS_M
    if next_goal is not None:
        # Sim coordinates are half-scale; convert their separation to metres.
        next_leg_m = 2.0 * math.hypot(next_goal[0] - goal[0], next_goal[1] - goal[1])
        if next_leg_m > 0:
            radius = min(radius, 0.4 * next_leg_m)
    return radius


def curve_lookahead_goal(csv_path, line_index, num_lines, current_goal, bot_position):
    """Return continuous curve progress and a target ahead of that progress.

    The CSV's Bezier samples form a polyline.  Rather than using the current
    CSV index as progress, project the bot's live virtual position onto that
    polyline every control cycle, then walk UAV_CURVE_LOOKAHEAD_M forward.
    This removes target jumps caused by discrete sample/index changes.
    """
    curve_points = [current_goal]
    for next_index in range(line_index + 1, num_lines):
        try:
            row = read_specific_line(csv_path, next_index)[0]
        except Exception as e:
            print("[curve-guidance] next point read failed", e)
            break
        if str(row[2]).strip().lower() != "true":
            break
        curve_points.append((row[0], row[1]))

    if len(curve_points) < 2:
        return None

    bot_x, bot_y = bot_position
    closest_distance_sq = float("inf")
    progress_segment = 0
    progress_point = curve_points[0]
    for segment_index in range(len(curve_points) - 1):
        start = curve_points[segment_index]
        end = curve_points[segment_index + 1]
        segment_x = end[0] - start[0]
        segment_y = end[1] - start[1]
        segment_length_sq = segment_x * segment_x + segment_y * segment_y
        if segment_length_sq == 0:
            continue
        projection = (
            (bot_x - start[0]) * segment_x + (bot_y - start[1]) * segment_y
        ) / segment_length_sq
        projection = max(0.0, min(1.0, projection))
        projected_point = (
            start[0] + projection * segment_x,
            start[1] + projection * segment_y,
        )
        distance_sq = (bot_x - projected_point[0]) ** 2 + (
            bot_y - projected_point[1]
        ) ** 2
        if distance_sq < closest_distance_sq:
            closest_distance_sq = distance_sq
            progress_segment = segment_index
            progress_point = projected_point

    remaining_m = UAV_CURVE_LOOKAHEAD_M
    current_point = progress_point
    for segment_index in range(progress_segment, len(curve_points) - 1):
        end = curve_points[segment_index + 1]
        segment_m = 2.0 * math.hypot(
            end[0] - current_point[0], end[1] - current_point[1]
        )
        if segment_m > 0 and segment_m >= remaining_m:
            fraction = remaining_m / segment_m
            lookahead_point = (
                current_point[0] + fraction * (end[0] - current_point[0]),
                current_point[1] + fraction * (end[1] - current_point[1]),
            )
            return progress_point, lookahead_point
        remaining_m -= segment_m
        current_point = end

        # The remaining curve is shorter than the configured look-ahead.
    return progress_point, curve_points[-1]


_last_curve_guidance_log = {}


def curve_guidance_position(b, curve_guidance):
    """Apply the curve-forward vector while preserving bot dispersion."""
    if curve_guidance is None:
        return None
    curve_progress, curve_lookahead = curve_guidance
    return (
        b.x + curve_lookahead[0] - curve_progress[0],
        b.y + curve_lookahead[1] - curve_progress[1],
    )


def log_curve_guidance(i, line_index, is_curve, curve_guidance):
    """Log curve parsing once per point, without flooding every control tick."""
    state = (line_index, is_curve, curve_guidance is not None)
    if _last_curve_guidance_log.get(i) == state:
        return
    _last_curve_guidance_log[i] = state
    if is_curve:
        print(
            f"[curve-guidance] UAV {pos_array[i]} index {line_index}: "
            f"{'look-ahead active' if curve_guidance else 'last curve sample; no forward point'}"
        )


def uav_reached_waypoint(
    i, b, goal, sim_radius=15.0, next_goal=None, is_curve=False, is_final=False
):
    """Advance every in-route point virtually; confirm only mission end by GPS.

    Holding the virtual leader at an intermediate grid point until a
    fixed-wing UAV flies into its acceptance radius freezes the GUIDED target.
    A wide-turn aircraft then keeps orbiting/cutting past that frozen point
    and cannot receive the next target.  The bot's own reach test is the
    correct hand-off condition for all in-route points; real-UAV confirmation
    is needed only before declaring the final mission point complete.
    """
    if is_curve:
        bot_reached = (
            abs(goal[0] - b.x) <= UAV_CURVE_POINT_SWITCH_RADIUS
            and abs(goal[1] - b.y) <= UAV_CURVE_POINT_SWITCH_RADIUS
        )
    else:
        bot_reached = (
            abs(goal[0] - b.x) <= sim_radius and abs(goal[1] - b.y) <= sim_radius
        )
    if not is_final:
        return bot_reached, None

    distance = uav_distance_to_goal(i, goal)
    if distance is not None:
        return (
            bot_reached and distance <= waypoint_flyby_radius(goal, next_goal, is_final)
        ), distance
    if not master_flag:
        return bot_reached, None
        # Live missions must not falsely complete a leg during a telemetry gap.
    return False, None


def connection_string_for_sysid(sys_id):
    if int(sys_id) not in port_dict:
        raise KeyError(f"SYS_ID {sys_id} not found in port_dict")
    return f"udpin:{ip}:{port_dict[int(sys_id)]}"


def register_active_uavs():
    for idx, sys_id in enumerate(pos_array):
        entry = uav_registry.setdefault(int(sys_id), {})
        entry["sys_id"] = int(sys_id)
        entry["active"] = True
        entry.setdefault("original_index", idx)
        entry["index"] = idx
        entry["connection"] = (
            connection_string_for_sysid(int(sys_id))
            if int(sys_id) in port_dict
            else entry.get("connection")
        )
        if idx < len(vehicles):
            entry["vehicle"] = vehicles[idx]
        uav_task_state.setdefault(int(sys_id), "IDLE")


def rebuild_uav_home_positions():
    global uav_home_pos, num_bots
    uav_home_pos = []
    for vehicle in vehicles:
        lat = vehicle.location.global_relative_frame.lat
        lon = vehicle.location.global_relative_frame.lon
        x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
        uav_home_pos.append((x / 2, y / 2))
    num_bots = len(pos_array)
    return uav_home_pos


def normalize_active_uav_order():
    global pos_array, vehicles, different_height, pop_flag_arr
    if len(pos_array) != len(vehicles):
        print(
            "[uav-order] skipped: pos_array/vehicles length mismatch",
            pos_array,
            len(vehicles),
        )
        return False
    combined = []
    for idx, sys_id in enumerate(pos_array):
        height = different_height[idx] if idx < len(different_height) else 300
        pop_flag = pop_flag_arr[idx] if idx < len(pop_flag_arr) else 1
        combined.append((int(sys_id), vehicles[idx], height, pop_flag))
    combined.sort(key=lambda item: item[0])
    pos_array[:] = [item[0] for item in combined]
    vehicles[:] = [item[1] for item in combined]
    different_height[:] = [item[2] for item in combined]
    pop_flag_arr[:] = [item[3] for item in combined]
    rebuild_uav_home_positions()
    register_active_uavs()
    print("[uav-order] active order normalized", pos_array)
    return True


def add_uav_to_swarm(sys_id):
    global vehicles, pos_array, s, num_bots, uav_home_pos
    try:
        # The topology and active task indexes must stay in the same frame.
        # active_goal_tasks_lock is initialized before commands can arrive.
        with swarm_topology_lock, active_goal_tasks_lock:
            sys_id = int(sys_id)
            connection_str = connection_string_for_sysid(sys_id)
            print("[add-link] connection", sys_id, connection_str)
            if sys_id in pos_array:
                idx = pos_array.index(sys_id)
                try:
                    vehicles[idx].close()
                except Exception:
                    pass
                vehicles[idx] = connect(
                    connection_str, baud=115200, heartbeat_timeout=30
                )
                uav_registry.setdefault(sys_id, {})["vehicle"] = vehicles[idx]
                uav_registry[sys_id]["active"] = True
                uav_registry[sys_id]["index"] = idx
                uav_task_state[sys_id] = "IDLE"
                # The UAV may have been physically flown (GUIDED fly-to or manual
                # RC) while disconnected -- without this, s.swarm[idx].x/y is
                # left exactly wherever it was before removal, so the sim bot
                # reappears stuck at the old position instead of where the
                # aircraft actually is now.
                _resync_bot_position(idx, force=True)
                print("[add-link] reconnected active UAV", sys_id, "index", idx)
                return True
            vehicle = connect(connection_str, baud=115200, heartbeat_timeout=30)
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
            insert_index = len(pos_array)
            # A reconnected UAV is appended so an active mission's compacted
            # indexes are not disturbed.  It must nevertheless retain the
            # altitude it had before removal, rather than inheriting the last
            # active UAV's (often much higher) altitude.
            previous_entry = uav_registry.get(sys_id, {})
            restored_height = previous_entry.get("different_height")
            pos_array.append(sys_id)
            vehicles.append(vehicle)
            s.add_bot(insert_index, (x / 2, y / 2))
            if restored_height is not None:
                different_height.append(restored_height)
            elif different_height:
                different_height.append(different_height[-1])
            else:
                different_height.append(300)
            pop_flag_arr.append(1)
            rebuild_uav_home_positions()
            uav_registry[sys_id] = {
                "sys_id": sys_id,
                "active": True,
                "index": insert_index,
                "connection": connection_str,
                "vehicle": vehicle,
            }
            uav_task_state[sys_id] = "IDLE"
            print(
                "[add-link] added UAV as IDLE",
                sys_id,
                "index",
                insert_index,
                "pos_array",
                pos_array,
            )
            return True
    except Exception as e:
        print("[add-link] failed", sys_id, e)
        return False


def calculate_drones_needed(remaining_points, points_per_drone, total_drones):
    if remaining_points <= 0:
        return 0
    if remaining_points <= 4:
        return 1
    points_per_drone = max(1, int(points_per_drone))
    return min(
        total_drones, (int(remaining_points) + points_per_drone - 1) // points_per_drone
    )


def allocate_drones(total_points, covered_points, total_drones):
    if isinstance(total_points, int):
        total_points = [total_points] * len(covered_points)
    remaining_points_list = [
        max(0, int(tp) - int(cp)) for tp, cp in zip(total_points, covered_points)
    ]
    points_per_drone = [max(1, int(tp / 2)) for tp in total_points]
    uncovered_areas = [
        (i, points) for i, points in enumerate(remaining_points_list) if points > 0
    ]
    allocation = {i: 0 for i in range(len(covered_points))}
    if total_drones <= 0:
        return allocation, remaining_points_list
    if total_drones <= len(uncovered_areas):
        for i, _ in uncovered_areas:
            if total_drones <= 0:
                break
            allocation[i] = 1
            total_drones -= 1
    else:
        for i, _ in uncovered_areas:
            if total_drones <= 0:
                break
            needed = calculate_drones_needed(
                remaining_points_list[i], points_per_drone[i], total_drones
            )
            allocation[i] = needed
            total_drones -= needed
    print("[redistribution] allocation", allocation, "remaining", remaining_points_list)
    return allocation, remaining_points_list


def remove_uav_from_swarm(remove_bot_num):
    global pos_array, vehicles, s, different_height, pop_flag_arr, num_bots
    global remove_bot_flag, remove_bot_index, remove_bot_array, pop_bot_index
    global uav_home_pos, remove_flag, uav_removed, origin, endDistance, uav_registry, uav_task_state
    try:
        # Hold the task lock for the *whole* compaction.  In particular,
        # s.remove_bot(), vehicles.pop(), and task-key shifting must appear as
        # one atomic topology change to the background driver.
        with swarm_topology_lock, active_goal_tasks_lock:
            remove_bot_num = int(remove_bot_num)
            if remove_bot_num not in pos_array:
                print("[remove-link] not found", remove_bot_num, "pos_array", pos_array)
                return False
            pop_bot_index = pos_array.index(remove_bot_num)
            remove_bot_index = pop_bot_index
            print("[remove-link] removing", remove_bot_num, "at index", pop_bot_index)
            entry = uav_registry.setdefault(remove_bot_num, {})
            entry["sys_id"] = remove_bot_num
            entry.setdefault("original_index", pop_bot_index)
            if pop_bot_index < len(different_height):
                entry["different_height"] = different_height[pop_bot_index]
            entry["active"] = False
            entry["index"] = None
            entry["connection"] = (
                connection_string_for_sysid(remove_bot_num)
                if remove_bot_num in port_dict
                else entry.get("connection")
            )
            uav_task_state[remove_bot_num] = "IDLE"
            remove_bot_flag = True
            remove_bot_array.append(pop_bot_index)
            pos_array.pop(pop_bot_index)
            try:
                vehicles[pop_bot_index].close()
            except Exception as e:
                print("[remove-link] vehicle close failed", e)
            vehicles.pop(pop_bot_index)
            s.remove_bot(pop_bot_index)
            remove_goal_task_index(pop_bot_index)
            if pop_bot_index < len(different_height):
                different_height.pop(pop_bot_index)
            if pop_bot_index < len(pop_flag_arr):
                pop_flag_arr.pop(pop_bot_index)
            num_bots = len(pos_array)
            uav_home_pos = []
            for vehicle in vehicles:
                lat = vehicle.location.global_relative_frame.lat
                lon = vehicle.location.global_relative_frame.lon
                x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                uav_home_pos.append((x / 2, y / 2))
            remove_flag = False
            uav_removed = True
            pop_bot_index = None
            register_active_uavs()
            print("[remove-link] remaining pos_array", pos_array, "num_bots", num_bots)
            return True
    except Exception as e:
        print("[remove-link] failed", remove_bot_num, e)
        return False


def handle_concurrent_remove_command(command_data):
    if not command_data.startswith(b"remove"):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        f, remove_bot_num = decoded_index.split(",", 1)
        return remove_uav_from_swarm(remove_bot_num)
    except Exception as e:
        print("[concurrent remove] failed", e)
        return False


def handle_concurrent_add_command(command_data):
    if not command_data.startswith(b"add"):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        f, sys_id = decoded_index.split(",", 1)
        return add_uav_to_swarm(sys_id)
    except Exception as e:
        print("[concurrent add] failed", e)
        return False


def check_for_new_command(started_seq):
    """Call once per iteration inside an interruptible mission loop.
    Selected goal/search/split commands (and add/remove) targeting a
    specific UAV subset are handled concurrently without preempting the
    running mission; any other newer command (or one with no subset,
    i.e. targeting the whole swarm) still preempts it via
    MissionPreempted."""
    global _handled_concurrent_command_seq, _last_seq
    if _pending_command.seq > started_seq:
        if _pending_command.seq > _handled_concurrent_command_seq and (
            handle_concurrent_goal_command(_pending_command.data)
            or handle_concurrent_search_command(_pending_command.data)
            or handle_concurrent_split_command(_pending_command.data)
            or handle_concurrent_different_command(_pending_command.data)
            or handle_concurrent_remove_command(_pending_command.data)
            or handle_concurrent_add_command(_pending_command.data)
        ):
            _handled_concurrent_command_seq = _pending_command.seq
            _last_seq = _pending_command.seq
            return None
        if _pending_command.seq <= _handled_concurrent_command_seq:
            return None
        raise MissionPreempted(_pending_command.data, _pending_command.address)


def CHECK_network_connection():
    global heartbeat_ip_timeout, heartbeat_ip
    for i, iter_follower in enumerate(heartbeat_ip_timeout):
        response = os.system("ping -c 1 " + heartbeat_ip[i])
        if response == 0:
            heartbeat_ip_timeout[i] = 30
            pass
        else:  # Link is down.
            print("link is down")
            linkdown_flag = True
            # master_ip="192.168.0.153"
            # slave_heal_ip[i] = 'nolink'
            heartbeat_ip_timeout[i] = 1
    print(" heartbeat_ip_timeout", heartbeat_ip_timeout)


ip = get_interface_mapping()
print("ip", ip)


def vehicle_connection():
    global vehicles, pos_array, num_bots, heartbeat_ip_timeout
    pos_array = []
    vehicles = []
    num_bots = 0

    try:
        vehicle1 = connect(
            "udpin:{}:14551".format(ip),
            baud=115200,
            heartbeat_timeout=heartbeat_ip_timeout[0],
        )
        print("Drone1")
        vehicles.append(vehicle1)
        pos_array.append(vehicle1._master.target_system)
        num_bots += 1
        msg = "Drone1 Connected"
    except:
        pass
        print("Vehicle 1 is lost")
    try:
        vehicle2 = connect(
            "udpin:{}:14552".format(ip),
            baud=115200,
            heartbeat_timeout=heartbeat_ip_timeout[1],
        )
        print("Drone2")
        num_bots += 1
        vehicles.append(vehicle2)
        pos_array.append(vehicle2._master.target_system)
        msg = "Drone2 Connected"
    except:
        pass
        print("Vehicle 2 is lost")

    try:
        vehicle3 = connect(
            "udpin:{}:14553".format(ip),
            baud=115200,
            heartbeat_timeout=heartbeat_ip_timeout[2],
        )
        print("Drone3")
        num_bots += 1
        vehicles.append(vehicle3)
        pos_array.append(vehicle3._master.target_system)
        msg = "Drone3 Connected"
    except:
        pass
        print("Vehicle 3 is lost")

    try:
        vehicle4 = connect(
            "udpin:{}:14554".format(ip),
            baud=115200,
            heartbeat_timeout=heartbeat_ip_timeout[3],
        )
        print("Drone4")
        num_bots += 1
        vehicles.append(vehicle4)
        pos_array.append(vehicle4._master.target_system)
        msg = "Drone4 Connected"
    except:
        pass
        print("Vehicle 4 is lost")
    try:
        vehicle5 = connect(
            "udpin:{}:14555".format(ip),
            baud=115200,
            heartbeat_timeout=heartbeat_ip_timeout[4],
        )
        print("Drone5")
        num_bots += 1
        vehicles.append(vehicle5)
        pos_array.append(vehicle5._master.target_system)
        msg = "Drone5 Connected"
    except:
        pass
        print("Vehicle 5 is lost")

    # try:
    # 	vehicle6= connect('udpin:{}:14556'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[5])
    # 	print('Drone6')
    # 	num_bots+=1
    # 	vehicles.append(vehicle6)
    # 	pos_array.append(vehicle6._master.target_system)
    # 	msg="Drone6 Connected"
    # except:
    # 	pass
    # 	print(	"Vehicle 6 is lost")

    # try:
    # 	vehicle7= connect('udpin:{}:14557'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[6])
    # 	print('Drone7')
    # 	num_bots+=1
    # 	vehicles.append(vehicle7)
    # 	pos_array.append(vehicle7._master.target_system)
    # 	msg="Drone7 Connected"
    # except:
    # 	pass
    # 	print(	"Vehicle 7 is lost")

    # try:
    # 	vehicle8= connect('udpin:{}:14558'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[7])
    # 	print('Drone8')
    # 	num_bots+=1
    # 	vehicles.append(vehicle8)
    # 	pos_array.append(vehicle8._master.target_system)
    # 	msg="Drone8 Connected"
    # except:
    # 	pass
    # 	print(	"Vehicle 8 is lost")

    # try:
    # 	vehicle9= connect('udpin:{}:14559'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[8])
    # 	print('Drone9')
    # 	num_bots+=1
    # 	vehicles.append(vehicle9)
    # 	pos_array.append(vehicle9._master.target_system)
    # 	msg="Drone9 Connected"
    # except:
    # 	pass
    # 	print(	"Vehicle 9 is lost")

    # try:
    # 	vehicle10= connect('udpin:{}:14560'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[9])
    # 	print('Drone10')
    # 	vehicles.append(vehicle10)
    # 	pos_array.append(vehicle10._master.target_system)
    # 	num_bots+=1
    # 	msg="Drone10 Connected"
    # except:
    # 	pass
    # 	print(	"Vehicle 10 is lost")

    print(len(vehicles))
    """
	serialized_data = json.dumps(pos_array)
	serialized_data="pos_array" + serialized_data
	print("serialized_data",serialized_data)
	
	for f in range(len(vehicles)):
		uav1.sendto(serialized_data.encode(), uav1_server_address)
		time.sleep(0.2)
		uav2.sendto(serialized_data.encode(), uav2_server_address)
		time.sleep(0.2)
		uav3.sendto(serialized_data.encode(), uav3_server_address)
		time.sleep(0.2)
		#uav4.sendto(serialized_data.encode(), uav4_server_address)
		#time.sleep(0.2)
		#uav5.sendto(serialized_data.encode(), #uav5_server_address)
	"""


count = 0
endDistance = 500000
home_pos = []
home_pos_lat_lon = []
uav_home_pos = []
current_lat_lon = []
home_flag = False
home_flag1 = False
search_flag = False
home_goto_flag = False
lost_vehicle_num = 0
vehicle_lost_flag = False

landing_flag = False
# Iterate over the list of vehicles
robots = [(0, 0)] * 10

slave_heal_ip = ["192.168.0.153"] * num_bots
heartbeat = [0] * num_bots

vehicle_uav_heartbeat_flag = False

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address1 = ("192.168.0.210", 12010)
slave_heal_ip = ["192.168.0.153"] * num_bots

all_uav_csv_grid_array = [0] * num_bots
robot_positions = [([0, 0]) for _ in range(20)]
print("origin#########", origin)

sleep_times = {
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


def parse_selected_uav_ids(raw_ids):
    if raw_ids is None:
        return []
    try:
        return [int(uav_id) for uav_id in json.loads(raw_ids)]
    except Exception:
        try:
            cleaned = str(raw_ids).strip().strip("[]")
            if not cleaned:
                return []
            return [
                int(part.strip().strip('"').strip("'"))
                for part in cleaned.split(",")
                if part.strip()
            ]
        except Exception as e:
            print("[selected UAV parse] failed", raw_ids, e)
            return []


def selected_swarm_indexes(selected_uav_ids):
    if not selected_uav_ids:
        return list(range(len(pos_array)))
    selected = {int(uav_id) for uav_id in selected_uav_ids}
    indexes = [i for i, uav_id in enumerate(pos_array) if int(uav_id) in selected]
    missing = selected.difference({int(uav_id) for uav_id in pos_array})
    if missing:
        print(
            "[selected UAV] IDs not connected/in pos_array:",
            sorted(missing),
            "pos_array:",
            pos_array,
        )
    return indexes


def fetch_location():
    global vehicles, home_pos_lat_lon, home_pos, uav_home_pos
    global robots
    uav_home_pos = []
    current_lat_lon = []

    if master_flag:
        for i, vehicle in enumerate(vehicles):
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            # print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
            current_lat_lon.append((lat, lon))
            x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
            # print("x,y",x/2,y/2)
            uav_home_pos.append((x / 2, y / 2))
            if i < len(robots):
                robots[i] = (x / 2, y / 2)
            msg = ",".join([f"{robot[0]},{robot[1]}" for robot in robots])
    """	    
	if master_flag:
		serialized_data = json.dumps(uav_home_pos)
		serialized_data="uav_home_pos" + serialized_data
		
		for i in range(len(pos_array)):			
			uav1.sendto(serialized_data.encode(),uav1_server_address)
			time.sleep(0.2)
			uav2.sendto(serialized_data.encode(),uav2_server_address)
			time.sleep(0.2)
			uav3.sendto(serialized_data.encode(),uav3_server_address)	
			time.sleep(0.2)
			#uav4.sendto(serialized_data.encode(), uav4_server_address)
			#time.sleep(0.2)
			#uav5.sendto(serialized_data.encode(), #uav5_server_address)
        
		serialized_goal_data = json.dumps(goal_points)
		serialized_goal_data="goal_points" + serialized_goal_data
		home_pos_lat_lon=current_lat_lon
		home_pos=uav_home_pos
		print('home_pos',home_pos,home_pos_lat_lon)
	"""


if master_flag:
    vehicle_connection()
    register_active_uavs()
    while True:
        all_armed = [False] * len(vehicles)  # Assume all vehicles are armed initially
        for i, vehicle in enumerate(vehicles):
            altitude = vehicle.location.global_relative_frame.alt
            if vehicle.armed and altitude is not None and altitude > 10:
                # if vehicle.armed and vehicle.location.global_relative_frame.alt>10  :
                all_armed[i] = True  # Set the flag to False
        if all(all_armed):
            fetch_location()
            break
        time.sleep(0.1)


def generate_points(lat, lon, num_points, radius, circle_direction):
    # List to store generated points
    points = []

    # Generate points in circular formation
    for i in range(num_points):
        # Calculate bearing angle

        bearing_sign = 1 if circle_direction == 1 else -1
        bearing = bearing_sign * (360 / num_points * i)

        # Calculate new latitude and longitude
        lat2 = asin(
            sin(radians(lat)) * cos(radius / 6371000)
            + cos(radians(lat)) * sin(radius / 6371000) * cos(radians(bearing))
        )
        lon2 = radians(lon) + atan2(
            sin(radians(bearing)) * sin(radius / 6371000) * cos(radians(lat)),
            cos(radius / 6371000) - sin(radians(lat)) * sin(lat2),
        )

        # Append the new point to the list
        points.append((degrees(lat2), degrees(lon2)))

    return points


def read_specific_line(csv_file_path, line_number):
    goal = []
    with open(csv_file_path, "rt") as file:
        reader = csv.reader(file)
        for i in range(line_number):
            next(reader)
            # Read the desired line
        line = next(reader)
        goal.append((float(line[0]), float(line[1]), str(line[2])))
        return goal


# def arm_and_takeoff(vehicle, aTargetAltitude):
#     """
#     Arms vehicle and fly to aTargetAltitude.
#     """
#     print("Basic pre-arm checcks")
#     # Don't try to arm until autopilot is ready
#     while not vehicle.is_armable:
#         print(" Waiting for vehicle to initialise...")
#         time.sleep(1)

#     print("Arming motors")
#     # Copter should arm in GUIDED mode
#     vehicle.mode = VehicleMode("GUIDED")
#     vehicle.armed = True

#     while not vehicle.armed:
#         print(" Waiting for arming...")
#         time.sleep(1)

#     print("Taking off!")
#     time.sleep(3)
#     vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

#     while True:
#         print(" Altitude: ", vehicle.location.global_relative_frame.alt)
#         # Break and return from function just below target altitude.
#         if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.90:
#             print("Reached target altitude")
#             break
#         time.sleep(1)

data = ""
same_alt_flag = False
index = 0
flag_stop = False
return_flag = False
pop_flag_arr = [1] * num_bots
pop_flag = False
specific_bot_goal_flag = False
pop_bot_index = None
goal_bot_num = None
start_flag = False
start_return_csv_flag = False
circle_formation_flag = False
radius_of_earth = 6378100.0  # in meters
uav_home_flag = False
remove_flag = False
group_goal_flag = False
circle_formation_count = 0
uav_removed = True
grid_path_array = [1] * num_bots
remove_bot_flag = False
remove_bot_index = 0
search_step = 1
percentage = 0
removed_uav_grid = []
removed_grid_path_length = []
removed_grid_path_array = [0] * len(pos_array)
removed_grid_path_array_start_val = [0] * len(pos_array)
checkall_removed_grid_path_array_start_val = [0] * len(pos_array)
removed_grid_filename = [0] * num_bots
removed_grid_path_array_flag = False
removed_uav_grid = []
removed_grid_path_length = []
remove_bot_flag = False
remove_bot_index = []
remove_bot_array = []
grid_completed_bot = [-1] * num_bots
uncovered_area_filename = []
uncovered_area_points = []
grid_completed_bot = [-1] * num_bots
circle_formation_table = [0] * num_bots
circle_formation_goals = []
guided_circle_formation_table = [0] * num_bots
guided_circle_formation_goals = []
guided_circle_flag = False
guided_circle_formation_flag = False
group_split_goal_pos = [0] * num_bots
group_split_flag_array = [False] * num_bots
group_split_flag = False
search_flag_val = 0
split_flag_val = 0
split_flag = False

# Initialize Simulation and GUI


def _reset_mission_state():
    """Clear the mission-scoped state shared/leaked across the
    interruptible mission loops (Goal, Guided Circle, Navigate, Search,
    Split/Specific Split) so a freshly dispatched command -- whether it
    arrived normally or preempted a running mission -- never inherits
    residue from whatever ran before it. Called once per dispatched
    command, right before the command is matched against the if-chain
    below. Connection/topology state (vehicles, pos_array, origin, s)
    is intentionally left alone -- a new mission keeps flying the same
    connected swarm, it does not drop it.
    """
    global landing_flag, removed_uav_grid, removed_grid_path_length
    global removed_grid_path_array, removed_grid_path_array_start_val
    global checkall_removed_grid_path_array_start_val, removed_grid_filename
    global removed_grid_path_array_flag, removed_grid_path_array_index
    global uncovered_area_points, uncovered_area_filename
    global group_goal_flag, guided_circle_flag, guided_circle_formation_flag

    landing_flag = False
    removed_uav_grid = []
    removed_grid_path_length = []
    removed_grid_path_array = [0] * len(pos_array)
    removed_grid_path_array_start_val = [0] * len(pos_array)
    checkall_removed_grid_path_array_start_val = [0] * len(pos_array)
    removed_grid_filename = [0] * len(pos_array)
    removed_grid_path_array_flag = False
    removed_grid_path_array_index = 0
    uncovered_area_points = []
    uncovered_area_filename = []
    group_goal_flag = False
    guided_circle_flag = False
    guided_circle_formation_flag = False


active_goal_tasks = {}
# A task replacement must be atomic with the runner tick that reads and
# drives it.  RLock permits the task drivers' small state updates while the
# runner holds this lock, preventing an overwritten task from issuing one
# stale simple_goto or modifying the replacement task's waypoint index.
active_goal_tasks_lock = threading.RLock()


def assign_goal_tasks(
    selected_indexes, goal_xy, guided_circle_radius=None, guided_circle_direction=None
):
    with active_goal_tasks_lock:
        for slot, bot_index in enumerate(selected_indexes):
            active_goal_tasks[bot_index] = {
                "type": "goal",
                "goals": list(goal_xy),
                "goal_index": 0,
                "guided_circle_radius": guided_circle_radius,
                "guided_circle_direction": guided_circle_direction,
                # Used by _start_guided_circle_task to stagger this bot's
                # starting ring slot instead of every bot in the group
                # converging on circle_points[0] at once.
                "circle_slot": slot,
                "circle_slot_count": len(selected_indexes),
            }
    print(
        "[goal-task] assigned",
        selected_indexes,
        goal_xy,
        "circle_radius",
        guided_circle_radius,
        "circle_direction",
        guided_circle_direction,
    )


def assign_mission_tasks(csv_paths_by_index, label):
    """Registers a waypoint-follow task (used by search and split) for each
    given bot index, keyed by its own per-drone CSV file. Runs in the same
    background thread/dict as goal tasks, so a search or split assigned to
    one UAV subset progresses independently of whatever goal/search/split
    the rest of the swarm is doing -- assigning any task type to a bot
    index simply overwrites whatever task (of any type) that index had
    before, matching the "new command terminates the old one, never
    resumes it" behavior goal already has."""
    with active_goal_tasks_lock:
        for bot_index, csv_path in csv_paths_by_index.items():
            try:
                with open(csv_path, "rt") as f:
                    num_lines = sum(1 for _ in csv.reader(f))
            except Exception as e:
                print(f"[{label}-task] failed to read {csv_path}: {e}")
                continue
            active_goal_tasks[bot_index] = {
                "type": "mission",
                "label": label,
                "csv_path": csv_path,
                "line_index": 0,
                "num_lines": num_lines,
            }
    print(f"[{label}-task] assigned", csv_paths_by_index)


def remove_goal_task_index(removed_index):
    with active_goal_tasks_lock:
        if removed_index in active_goal_tasks:
            del active_goal_tasks[removed_index]
        shifted_tasks = {}
        for bot_index, task in active_goal_tasks.items():
            new_index = bot_index - 1 if bot_index > removed_index else bot_index
            shifted_tasks[new_index] = task
        active_goal_tasks.clear()
        active_goal_tasks.update(shifted_tasks)
    print(
        "[goal-task] compacted after remove",
        removed_index,
        sorted(active_goal_tasks.keys()),
    )


def synchronize_mission_topology(
    selected_indexes,
    csv_file_paths,
    all_csv_paths,
    grid_indexes,
    line_counts,
    current_goals,
    planned_paths,
):
    """Apply queued UAV removals to one foreground search/split mission.

    These lists are all indexed by the simulator's compacted bot index.  A
    removed UAV must therefore remove the matching CSV *slot* before indexes
    are shifted; otherwise the UAV after it is given the removed UAV's path.
    The resize also makes adding an idle UAV safe while a selected subset is
    still executing.
    """
    global remove_bot_flag, remove_bot_array

    removed_indexes = (
        sorted(set(remove_bot_array), reverse=True) if remove_bot_flag else []
    )
    for removed_index in removed_indexes:
        # csv_file_paths is indexed by selected_indexes, not by bot index.
        if removed_index in selected_indexes:
            path_slot = selected_indexes.index(removed_index)
            if path_slot < len(csv_file_paths):
                csv_file_paths.pop(path_slot)
        for values in (
            all_csv_paths,
            grid_indexes,
            line_counts,
            current_goals,
            planned_paths,
        ):
            if 0 <= removed_index < len(values):
                values.pop(removed_index)
        selected_indexes = [
            index - 1 if index > removed_index else index
            for index in selected_indexes
            if index != removed_index
        ]

    # Addition appends an IDLE bot.  Keep every foreground bookkeeping array
    # aligned, but do not add that new bot to selected_indexes: it must not be
    # accidentally assigned a path from the already-running mission.
    target_size = len(pos_array)
    for values, fill in (
        (all_csv_paths, 0),
        (grid_indexes, 0),
        (line_counts, 0),
        (current_goals, None),
        (planned_paths, None),
    ):
        del values[target_size:]
        values.extend([fill] * (target_size - len(values)))

    if removed_indexes:
        print(
            "[mission-topology] removed indexes",
            removed_indexes,
            "remaining selected indexes",
            selected_indexes,
        )
        remove_bot_array = []
        remove_bot_flag = False
    return selected_indexes


def _start_guided_circle_task(i, task):
    """Transitions a completed goal task into a loitering circle around its
    final goal point, sized/oriented by whatever radius/direction the
    operator configured (Swarm UAVs settings tab) when the goal command was
    issued. Mirrors the original (dead) foreground guided_circle block: 8
    points around goal_latlon[-1] via generate_points(), converted to the
    local sim frame the same way. Only called when a radius was actually
    given -- if not, the goal task just completes and the UAV holds
    position, same as before this restoration."""
    goals = task.get("goals", [])
    radius_raw = task.get("guided_circle_radius")
    print("guided_circle_radius", radius_raw)
    direction_raw = task.get("guided_circle_direction")
    try:
        # radius/direction arrive as strings off the wire (e.g. "0") -- a
        # non-empty string is truthy in Python even when it means "no
        # loiter configured", so convert before checking rather than after.
        radius = int(float(radius_raw)) if radius_raw is not None else 0
    except (TypeError, ValueError):
        radius = 0
    try:
        direction = int(float(direction_raw)) if direction_raw is not None else 1
    except (TypeError, ValueError):
        direction = 1
    if not goals or radius <= 0:
        return None
    try:
        # goals[-1] is a local sim-frame (x, y) point (the /2-scaled output
        # of geoToCart in handle_concurrent_goal_command), not lat/lon --
        # convert back to real coordinates before doing geo math on it.
        last_goal_x, last_goal_y = goals[-1][0], goals[-1][1]
        last_goal_lat, last_goal_lon = locatePosition.cartToGeo(
            origin, endDistance, [last_goal_x * 2, last_goal_y * 2]
        )
        circle_latlon = generate_points(
            last_goal_lat, last_goal_lon, 8, radius, direction
        )
        circle_points = []
        for m in circle_latlon:
            x, y = locatePosition.geoToCart(origin, endDistance, m)
            circle_points.append((x / 2, y / 2))
    except Exception as e:
        print("[guided-circle] failed to start for UAV", pos_array[i], e)
        return None
    # Stagger this bot's starting ring point by its slot among the bots
    # that were assigned this goal together, so they fan out onto distinct
    # circle_points immediately instead of every bot heading for
    # circle_points[0] and fighting over the same physical spot.
    circle_slot = task.get("circle_slot", 0)
    circle_slot_count = task.get("circle_slot_count") or 1
    start_index = round(circle_slot * len(circle_points) / circle_slot_count) % len(
        circle_points
    )
    print(
        "[guided-circle] starting for UAV",
        pos_array[i],
        "radius",
        radius,
        "direction",
        direction,
        "slot",
        circle_slot,
        "of",
        circle_slot_count,
        "start_index",
        start_index,
    )
    return {
        "type": "guided_circle",
        "circle_points": circle_points,
        "circle_index": start_index,
    }


def _drive_goal_task(i, b, task, completed):
    goals = task.get("goals", [])
    goal_index = task.get("goal_index", 0)
    if goal_index >= len(goals):
        completed.append(i)
        return
    goal_position = goals[goal_index]
    next_goal = goals[goal_index + 1] if goal_index + 1 < len(goals) else None
    reached_goal, goal_distance = uav_reached_waypoint(
        i,
        b,
        goal_position,
        sim_radius=15,
        next_goal=next_goal,
        is_final=next_goal is None,
    )
    if reached_goal:
        if BOT_SYNC_DEBUG:
            print(
                f"[waypoint-advance] label=goal bot={i} "
                f"index={goal_index}->{goal_index + 1} "
                f"bot=({b.x:.2f},{b.y:.2f}) goal=({goal_position[0]:.2f},{goal_position[1]:.2f})"
            )
        if goal_distance is not None:
            print(f"[uav-flyby] bot {i}: switching goal at {goal_distance:.1f} m")
        goal_index += 1
        if goal_index >= len(goals):
            try:
                circle_radius = int(float(task.get("guided_circle_radius") or 0))
            except (TypeError, ValueError):
                circle_radius = 0
            print(
                f"[goal-task] UAV {pos_array[i]} reached its final goal; "
                f"guided-circle radius = {circle_radius} m"
            )
            circle_task = _start_guided_circle_task(i, task)
            with active_goal_tasks_lock:
                if i in active_goal_tasks:
                    if circle_task is not None:
                        active_goal_tasks[i] = circle_task
                    else:
                        del active_goal_tasks[i]
            if circle_task is None:
                completed.append(i)
                print("[goal-task] completed UAV", pos_array[i])
            return
        with active_goal_tasks_lock:
            if i in active_goal_tasks:
                active_goal_tasks[i]["goal_index"] = goal_index
        goal_position = goals[goal_index]
    # b.set_goal(goal_position[0], goal_position[1])
    # cmd = cvg.goal_area_cvg(i, b, goal_position)
    # cmd.exec(b)
    advance_bot_with_uav_pacing(i, b, goal_position, label="goal")
    _drive_vehicle_towards(i, b)


def _drive_guided_circle_task(i, b, task, completed):
    """Continuous loiter -- never adds to completed under normal operation;
    only stops via active_goal_tasks being overwritten by a new command or
    cleared by an explicit stop, matching the original design's intent
    (circle until told otherwise)."""
    circle_points = task.get("circle_points", [])
    if not circle_points:
        completed.append(i)
        return
    circle_index = task.get("circle_index", 0)
    goal_position = circle_points[circle_index]
    # Wide dispersion term (matches the reference implementation's loiter
    # loop) keeps bots that start on/near the same ring point pushed apart
    # from each other throughout the circle, on top of the per-bot starting
    # stagger assigned in _start_guided_circle_task.
    cmd = cvg.goal_area_cvg(i, b, goal_position)
    cmd += disp_field(b, neighbourhood_radius=100)
    cmd.exec(b)
    dx = abs(goal_position[0] - b.x)
    dy = abs(goal_position[1] - b.y)
    if dx <= 5 and dy <= 5:
        circle_index = (circle_index + 1) % len(circle_points)
        with active_goal_tasks_lock:
            if i in active_goal_tasks:
                active_goal_tasks[i]["circle_index"] = circle_index
    _drive_vehicle_towards(i, b)


# A fixed-wing can't turn on a dime, so waiting for a tight arrival
# tolerance before switching to the next CSV point means the switch happens
# too late relative to the airframe's real turn radius. Several of the
# closely-spaced bezier turn-around samples then satisfy that same tight
# check within one or two ticks once the bot is finally close, which reads
# as line_index jumping several points at once -- the vehicle (driven off
# b.x/b.y via _drive_vehicle_towards) is only ever commanded toward
# whichever point line_index lands on, so it cuts a straight line to it
# instead of having been guided through the ones in between. Switching on a
# wider radius issues the next point's command while still approaching the
# current one -- turn anticipation, the way a real AUTO mission's WP_RADIUS
# acceptance works -- so line_index advances one point at a time. The last
# point of a run keeps the old tight tolerance since that is where mission
# completion is actually judged.
MISSION_POINT_SWITCH_RADIUS = 15  # sim units; tune to airframe turn radius
MISSION_FINAL_POINT_RADIUS = 10


def _drive_mission_task(i, b, task, completed):
    line_index = task.get("line_index", 0)
    num_lines = task.get("num_lines", 0)
    label = task.get("label", "mission")
    if line_index >= num_lines:
        completed.append(i)
        print(f"[{label}-task] completed UAV", pos_array[i])
        return
    try:
        goal_lat_lon = read_specific_line(task["csv_path"], line_index)
    except Exception as e:
        print(f"[{label}-task] read failed", task.get("csv_path"), e)
        completed.append(i)
        return
    goal_position = (goal_lat_lon[0][0], goal_lat_lon[0][1])
    is_curve = str(goal_lat_lon[0][2]).strip().lower() == "true"
    curve_guidance = (
        curve_lookahead_goal(
            task["csv_path"], line_index, num_lines, goal_position, (b.x, b.y)
        )
        if is_curve
        else None
    )
    log_curve_guidance(i, line_index, is_curve, curve_guidance)
    is_last_point = line_index >= num_lines - 1
    sim_radius = (
        MISSION_FINAL_POINT_RADIUS if is_last_point else MISSION_POINT_SWITCH_RADIUS
    )
    next_goal = None
    if not is_last_point:
        try:
            next_row = read_specific_line(task["csv_path"], line_index + 1)
            next_goal = (next_row[0][0], next_row[0][1])
        except Exception as e:
            print(f"[{label}-task] next point read failed", e)
    reached_goal, goal_distance = uav_reached_waypoint(
        i,
        b,
        goal_position,
        sim_radius=sim_radius,
        next_goal=next_goal,
        is_curve=is_curve,
        is_final=is_last_point,
    )
    if reached_goal:
        if goal_distance is not None:
            print(
                f"[uav-flyby] bot {i}: switching {label} point at {goal_distance:.1f} m"
            )
        line_index += 1
        with active_goal_tasks_lock:
            if i in active_goal_tasks:
                active_goal_tasks[i]["line_index"] = line_index
    _dis, step_size = advance_bot_with_uav_pacing(i, b, goal_position, label="mission")
    guidance_position = curve_guidance_position(b, curve_guidance)
    _drive_vehicle_towards(i, b, guidance_position)


def _drive_vehicle_towards(i, b, guidance_position=None):
    if master_flag and i < len(vehicles):
        position = guidance_position if guidance_position is not None else (b.x, b.y)
        current_position = (position[0] * 2, position[1] * 2)
        lat, lon = locatePosition.cartToGeo(origin, endDistance, current_position)
        if same_alt_flag:
            point1 = LocationGlobalRelative(lat, lon, same_height)
        else:
            point1 = LocationGlobalRelative(lat, lon, different_height[i])
        vehicles[i].simple_goto(point1)


def _drive_altitude_task(i, b, task, completed):
    """Holds the bot at its current (x,y) -- via a goal fixed at its own
    position, plus real disp_field repulsion so several idle bots
    re-staging altitude at once don't drift into each other -- while it
    climbs/descends to its just-updated different_height[i]. Completes
    (frees the bot back to fully idle) once the real vehicle reports being
    within tolerance of the target altitude, mirroring the original
    blocking loop's own completion check."""
    goal_position = (b.x, b.y)
    cmd = cvg.goal_area_cvg(i, b, goal_position)
    cmd += disp_field(b, neighbourhood_radius=100)
    cmd.exec(b)
    # dis = print_sim_vs_real_latlon_with_bot(b,i, label="search")
    # if dis <= 300:
    # 	print(f"Bot {i} dis:{dis}.")
    # 	cmd =cvg.goal_area_cvg(i,b,goal_position)
    # 	cmd += disp_field(b, neighbourhood_radius=100)
    # 	cmd.exec(b,step_size=1)
    _drive_vehicle_towards(i, b)
    if master_flag and i < len(vehicles) and i < len(different_height):
        try:
            current_alt = vehicles[i].location.global_relative_frame.alt
        except Exception:
            current_alt = None
        if current_alt is not None and abs(current_alt - different_height[i]) <= 1.5:
            completed.append(i)
            print("[altitude-task] reached target altitude for UAV", pos_array[i])


def _goal_task_runner():
    """Background thread, independent of the main command-dispatch loop.
    Continuously drives whichever bot indexes have an active_goal_tasks
    entry (goal, search, or split), so any command assigned to a UAV
    subset keeps progressing regardless of what the rest of the swarm is
    doing. There is no foreground "current mission" for these three
    command types anymore -- check_for_new_command/MissionPreempted is
    only reached by whatever hasn't been generalized this way yet
    (navigate, home, etc.)."""
    while True:
        time.sleep(sleep_times.get(len(pos_array), 0.1))
        try:
            # Keep assignment/replacement and a complete drive tick mutually
            # exclusive.  A selected-UAV command therefore takes effect at the
            # next tick at the latest, with no stale command after replacement.
            with active_goal_tasks_lock:
                tasks_snapshot = list(active_goal_tasks.items())
                if not tasks_snapshot:
                    continue
                completed = []
                for i, task in tasks_snapshot:
                    if active_goal_tasks.get(i) is not task:
                        continue
                    if i >= len(s.swarm) or i >= len(pos_array):
                        completed.append(i)
                        continue
                    b = s.swarm[i]
                    task_type = task.get("type")
                    if task_type == "mission":
                        _drive_mission_task(i, b, task, completed)
                    elif task_type == "guided_circle":
                        _drive_guided_circle_task(i, b, task, completed)
                    elif task_type == "altitude":
                        _drive_altitude_task(i, b, task, completed)
                    else:
                        _drive_goal_task(i, b, task, completed)
                if completed:
                    for i in completed:
                        active_goal_tasks.pop(i, None)
            # NOTE: deliberately does not call gui.update() here.
            # matplotlib's default Tk backend is not thread-safe -- all GUI
            # calls must happen on the thread that created the figure
            # (the main thread, via a foreground search/split/navigate
            # loop's own gui.update() calls). Calling it from this
            # background thread throws "Calling Tcl from different
            # apartment"/"main thread is not in main loop" every cycle.
            # Consequence: a UAV running purely as a background concurrent
            # task, with nothing currently occupying a foreground loop,
            # won't visibly move on the plot until some foreground loop's
            # own gui.update() call happens to run again.
        except Exception as e:
            print("[goal-task] runner exception", e)


while True:
    if uav_home_pos != []:
        print("num_bots", num_bots, uav_home_pos)
        s = sim.Simulation(uav_home_pos, num_bots=len(pos_array), env_name=file_name)
        goal_task_thread = threading.Thread(target=_goal_task_runner)
        goal_task_thread.daemon = True
        goal_task_thread.start()
        break
    else:
        pass


def remove_vehicle():
    global pos_array
    global vehicle_lost_flag
    global lost_vehicle_num
    global pop_bot_index
    global same_alt_flag
    global same_height
    global different_height
    global origin, endDistance
    global vehicles
    index = pos_array[lost_vehicle_num - 1]
    print(index, "index")
    print("lost_vehicle_num", lost_vehicle_num, index, pos_array)
    vehicle_lost_flag = False
    pop_flag = True
    # print ("msg", index)
    for l in range(0, len(pos_array)):
        if int(index) == pos_array[l]:
            pop_bot_index = l
            print("pop_bot_index,l", pop_bot_index, l)
            break
    pos_array.pop(pop_bot_index)
    vehicles.pop(pop_bot_index)
    s.remove_bot(pop_bot_index)
    print(num_bots)
    print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!", pop_flag_arr)
    print("pop index", pop_bot_index)
    same_alt_flag = False
    uav_home_pos = []
    for i, vehicle in enumerate(vehicles):
        lat = vehicle.location.global_relative_frame.lat
        lon = vehicle.location.global_relative_frame.lon
        x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
        different_height[i] = different_height[i] + 2
        uav_home_pos.append((x / 2, y / 2))
    print("uav_home_pos", uav_home_pos)
    remove_flag = False
    uav_removed = True
    while True:
        for i, b in enumerate(s.swarm):
            cmd = potf.velocity(
                b.get_position(), b.sim, weights=potf.field_weights, order=2, max_dist=5
            )
            cmd.exec(b)
            if master_flag:
                value = [b.x * 2, b.y * 2]
                lat, lon = locatePosition.cartToGeo(origin, endDistance, value)

                if same_alt_flag:
                    point1 = LocationGlobalRelative(lat, lon, same_height)
                else:
                    point1 = LocationGlobalRelative(lat, lon, different_height[i])
                vehicles[i].simple_goto(point1)
                alt = [0] * num_bots
                alt_count = [0] * num_bots
                for i, vehicle in enumerate(vehicles):
                    print("vehicle", vehicle, num_bots)
                    alt[i] = vehicle.location.global_relative_frame.alt
                    print("alt[vehicle]", alt[i])
                    if different_height[i] - 1.5 <= alt[i] <= different_height[i] + 1.5:
                        alt_count[i] = 1
                        print(alt_count, "alt_count")
                        if all(count == 1 for count in alt_count):
                            print("Reached target altitude")
                            return index


vehicles_thread = []
# _next_data/_next_address carry a preempting command straight into the
# next iteration (see the MissionPreempted except-clause below) so it's
# dispatched immediately, with no idle wait for a fresh mailbox seq.
_next_data, _next_address = None, None
_last_seq = 0
while 1:
    if master_flag:
        num_bots = len(vehicles)
    else:
        num_bots = len(pos_array)
    try:
        if _next_data is not None:
            data, address = _next_data, _next_address
            _next_data, _next_address = None, None
        else:
            while _pending_command.seq <= _last_seq:
                time.sleep(0.01)
            data = _pending_command.data
            address = _pending_command.address
            _last_seq = _pending_command.seq
        _reset_mission_state()
        print("!!msg", data)
        if data == b"stop":
            with active_goal_tasks_lock:
                active_goal_tasks.clear()
            print("[goal-task] cleared by stop")
            continue
        sync_swarm_with_telemetry()
        if data.startswith(b"origin"):
            decoded_index = data.decode("utf-8")
            _, new_lat, new_lon = decoded_index.split(",")
            origin = (float(new_lat), float(new_lon))
            print("Origin updated dynamically:", origin)

        if data == b"geofence":
            try:
                rectangles_path = os.path.join(
                    os.path.expanduser("~"), "Documents", "swarm_env", "rectangles.yaml"
                )
                with open(rectangles_path) as f:
                    world_data = yaml.safe_load(f)
                new_size = (world_data["size"]["x"], world_data["size"]["y"])
                new_obstacles = [
                    Polygon(o) for o in (world_data.get("obstacles") or [])
                ]
                s.env.obstacles = new_obstacles
                s.env.size = new_size
                s.size = new_size

                # Every s = sim.Simulation(..., env_name=file_name) call
                # throughout this script (preview rebuilds, vehicle
                # add/remove, etc.) loads its world via
                # World(filename=file_name+'.yaml'), which only looks
                # inside swarm_tasks/envs/worlds/ -- it can't see the
                # dynamic file above directly. Mirroring it into that
                # folder and pointing file_name at it means every future
                # rebuild picks up the current drawn area too, not just
                # this already-running s.
                worlds_dir = sim.envs.world.worlds_path
                shutil.copyfile(
                    rectangles_path, os.path.join(worlds_dir, "rectangles.yaml")
                )
                file_name = "rectangles"

                print(
                    f"Obstacles hot-reloaded from {rectangles_path}: {len(new_obstacles)} walls, origin:",
                    origin,
                )
            except Exception as e:
                print(f"Error reloading obstacles: {e}")

        if data == b"store_uav_pos":
            if os.path.exists(csv_file_path):
                os.remove(csv_file_path)

            with open(csv_file_path, mode="w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["X", "Y"])  # Write header
                csv_writer.writerows(home_pos)
                csv_file.close()

        if data == b"home_lock":
            for i, vehicle in enumerate(vehicles):
                while not vehicle.home_location:
                    cmds = vehicle.commands
                    cmds.download()
                    cmds.wait_ready()
                    home = vehicle.home_location
                    if not vehicle.home_location:
                        print(" Waiting for home position...")
                        time.sleep(1)
                        # Process the lat and lon as needed
                print(f"Vehicle - Latitude: {home.lat}, Longitude: {home.lon}")
                x, y = locatePosition.geoToCart(
                    origin, endDistance, [home.lat, home.lon]
                )
                home_pos_lat_lon[i] = (home.lat, home.lon)
                print("x,y", x / 2, y / 2)
                home_pos[i] = (x / 2, y / 2)
                if i < len(robots):
                    robots[i] = (x / 2, y / 2)
                msg = ",".join([f"{robot[0]},{robot[1]}" for robot in robots])

        if data.startswith(b"origin"):
            decoded_index = data.decode("utf-8")
            _, lat, lon = decoded_index.split(",")
            origin = (float(lat), float(lon))
            file_name = "rectangles"
            # uav_home_pos must be recomputed under the *new* origin here --
            # reusing whatever was left over from before this origin change
            # spawns bots at cartesian coordinates from the old frame, which
            # no longer lines up with the real UAVs converted through the
            # new origin, and stays wrong until the real aircraft happens to
            # fly within the dis<=300 resync radius of the stale bot.
            uav_home_pos = []
            for vehicle in vehicles:
                lat_i = vehicle.location.global_relative_frame.lat
                lon_i = vehicle.location.global_relative_frame.lon
                x, y = locatePosition.geoToCart(origin, endDistance, [lat_i, lon_i])
                uav_home_pos.append((x / 2, y / 2))
                # switches env to the dynamically-written world file
            s = sim.Simulation(
                uav_home_pos, num_bots=len(pos_array), env_name=file_name
            )
            print("Origin + obstacles refreshed:", origin, file_name)

        if data.startswith(b"takeoff"):
            decoded_index = data.decode("utf-8")
            print("decoded_index", decoded_index)
            data, takeoff_height = decoded_index.split(",")
            print("data,takeoff_height", data, takeoff_height)
            for i, vehicle in enumerate(vehicles):
                print(i)
                thread = threading.Thread(
                    target=arm_and_takeoff, args=(vehicle, int(takeoff_height))
                )
                vehicles_thread.append(thread)
                thread.start()

            for thread in vehicles_thread:
                thread.join()

            for i, vehicle in enumerate(vehicles):
                while not vehicle.home_location:
                    cmds = vehicle.commands
                    cmds.download()
                    cmds.wait_ready()
                    home = vehicle.home_location
                    if not vehicle.home_location:
                        print(" Waiting for home position...")
                        time.sleep(1)
                        # Process the lat and lon as needed
                print(f"Vehicle - Latitude: {home.lat}, Longitude: {home.lon}")
                x, y = locatePosition.geoToCart(
                    origin, endDistance, [home.lat, home.lon]
                )
                home_pos_lat_lon[i] = (home.lat, home.lon)
                print("x,y", x / 2, y / 2)
                home_pos[i] = (x / 2, y / 2)
                if i < len(robots):
                    robots[i] = (x / 2, y / 2)
                msg = ",".join([f"{robot[0]},{robot[1]}" for robot in robots])

        if (data.startswith(b"remove")) or (remove_flag):
            decoded_index = data.decode("utf-8")
            f, remove_bot_num = decoded_index.split(",", 1)
            print("remove_bot_num", remove_bot_num, pos_array)
            remove_uav_from_swarm(remove_bot_num)
            data = b"index"

        if data.startswith(b"add"):
            decoded_index = data.decode("utf-8")
            f, sys_id = decoded_index.split(",", 1)
            add_uav_to_swarm(sys_id)
            data = b"index"

        if data.startswith(b"specific_bot_goal"):
            index = "data"
            goal_pos = [0] * num_bots
            specific_bot_goal_flag_array = [False] * num_bots
            try:
                decoded_index = data.decode(
                    "utf-8"
                )  # Assuming utf-8 encoding, adjust if needed
                f, uav, goal_lat, goal_lon = decoded_index.split(",")
                goal_x, goal_y = locatePosition.geoToCart(
                    origin, endDistance, [float(goal_lat), float(goal_lon)]
                )
                goal_position = (goal_x / 2, goal_y / 2)
                for l in range(0, num_bots):
                    if int(uav) == pos_array[l]:
                        uav = l
                        print("uav,l", uav, l)
                        break

                goal_bot_num = int(uav)
                print("goal_bot_num", goal_bot_num)
                goal_pos[goal_bot_num] = goal_position
                specific_bot_goal_flag_array[goal_bot_num] = True
                print("specific_bot_goal_flag_array", specific_bot_goal_flag_array)
                while 1:
                    time.sleep(0.1)
                    if specific_bot_goal_flag:
                        specific_bot_goal_flag = False
                        break

                    for i, b in enumerate(s.swarm):
                        current_position = [b.x, b.y]
                        if specific_bot_goal_flag_array[i]:
                            dx = abs(goal_pos[i][0] - current_position[0])
                            dy = abs(goal_pos[i][1] - current_position[1])
                            if dx <= 10 and dy <= 10:
                                specific_bot_goal_flag_array[i] = False
                                print(
                                    "specific_bot_goal_flag_array",
                                    specific_bot_goal_flag_array,
                                )
                            if all(
                                flag == False for flag in specific_bot_goal_flag_array
                            ):
                                specific_bot_goal_flag = True
                                break
                            else:
                                current_position = (b.x, b.y)
                                if specific_bot_goal_flag_array[i]:
                                    b.set_goal(goal_pos[i][0], goal_pos[i][1])
                                    cmd = cvg.goal_area_cvg(i, b, goal_pos[i])
                                    cmd.exec(b)
                            if master_flag:
                                current_position = (b.x * 2, b.y * 2)
                                lat, lon = locatePosition.cartToGeo(
                                    origin, endDistance, current_position
                                )
                                if same_alt_flag:
                                    point1 = LocationGlobalRelative(
                                        lat, lon, same_height
                                    )
                                else:
                                    point1 = LocationGlobalRelative(
                                        lat, lon, different_height[i]
                                    )
                                vehicles[i].simple_goto(point1)

                    if index == b"stop":
                        specific_bot_goal_flag = False
                        break
            except Exception as e:
                print("exceptiiiooonnn", e)
                pass

        if data.startswith(b"group_split"):
            index = "data"
            try:
                decoded_index = data.decode(
                    "utf-8"
                )  # Assuming utf-8 encoding, adjust if needed
                msg_parts = decoded_index.split(",")
                goal_lat = float(msg_parts[-2])
                goal_lon = float(msg_parts[-1])
                remaining_values = msg_parts[1:-2]
                goal_x, goal_y = locatePosition.geoToCart(
                    origin, endDistance, [float(goal_lat), float(goal_lon)]
                )
                goal_position = (goal_x / 2, goal_y / 2)
                for val in remaining_values:
                    try:
                        bot_index = int(val)
                        for l in range(num_bots):
                            if bot_index == pos_array[l]:
                                group_split_goal_pos[l] = goal_position
                                group_split_flag_array[l] = True
                                print(f"Updated bot {l} with goal at {goal_position}")
                                break  # Break out of the inner loop once the correct bot is found
                    except ValueError:
                        print(f"Invalid value in remaining_values: {val}, skipping.")
                print(
                    "group_split_flag_array",
                    group_split_flag_array,
                    group_split_goal_pos,
                )
                if master_flag:
                    uav_home_pos = []
                    index = "data"
                    for vehicle in vehicles:
                        lat = vehicle.location.global_relative_frame.lat
                        lon = vehicle.location.global_relative_frame.lon
                        x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                        uav_home_pos.append((x / 2, y / 2))
                    """
					    serialized_data = json.dumps(home_pos)
					    serialized_data="uav_home_pos" + serialized_data
					    for i in range(len(pos_array)):
					        uav1.sendto(serialized_data.encode(),uav1_server_address)
					        time.sleep(0.2)
					        uav2.sendto(serialized_data.encode(),uav2_server_address)
					        time.sleep(0.2)
					        uav3.sendto(serialized_data.encode(),uav3_server_address)
					        time.sleep(0.2)
					        #uav4.sendto(serialized_data.encode(), uav4_server_address)
					        #time.sleep(0.2)
					        #uav5.sendto(serialized_data.encode(), #uav5_server_address)
					    """
                    s = sim.Simulation(
                        uav_home_pos, num_bots=len(pos_array), env_name=file_name
                    )
                while 1:
                    time.sleep(0.1)
                    if group_split_flag:
                        group_split_flag = False
                        break
                    for i, b in enumerate(s.swarm):
                        current_position = [b.x, b.y]
                        if group_split_flag_array[i]:
                            dx = abs(group_split_goal_pos[i][0] - current_position[0])
                            dy = abs(group_split_goal_pos[i][1] - current_position[1])
                            if dx <= 10 and dy <= 10:
                                group_split_flag_array[i] = False
                                print("group_split_flag_array", group_split_flag_array)
                            if all(flag == False for flag in group_split_flag_array):
                                group_split_flag = True
                                break
                            else:
                                current_position = (b.x, b.y)
                                if group_split_flag_array[i]:
                                    b.set_goal(
                                        group_split_goal_pos[i][0],
                                        group_split_goal_pos[i][1],
                                    )
                                    cmd = cvg.goal_area_cvg(
                                        i, b, group_split_goal_pos[i]
                                    )
                                    cmd.exec(b)
                            if master_flag:
                                current_position = (b.x * 2, b.y * 2)
                                lat, lon = locatePosition.cartToGeo(
                                    origin, endDistance, current_position
                                )
                                if same_alt_flag:
                                    point1 = LocationGlobalRelative(
                                        lat, lon, same_height
                                    )
                                else:
                                    point1 = LocationGlobalRelative(
                                        lat, lon, different_height[i]
                                    )
                                vehicles[i].simple_goto(point1)

                    if index == b"stop":
                        group_split_flag = False
                        break
            except Exception as e:
                print("exceptiiiooonnn", e)
                pass

        if data.startswith(b"goal"):
            index = "data"
            try:
                decoded_index = data.decode(
                    "utf-8"
                )  # Assuming utf-8 encoding, adjust if needed
                msg_parts = decoded_index.split("_")
                print("msg_parts", msg_parts, len(msg_parts))
                f = msg_parts[0]  # First coordinate pair
                guided_circle_direction = msg_parts[2]
                guided_circle_radius = msg_parts[3]
                goal_array = msg_parts[1]  # All other coordinates
                goal_latlon = json.loads(goal_array)
                goal_xy = []
                bot_reached = [0] * num_bots
                for x in goal_latlon:
                    print(origin, [x[0], x[1]])
                    x, y = locatePosition.geoToCart(
                        origin, endDistance, [float(x[0]), float(x[1])]
                    )
                    goal_xy.append((x / 2, y / 2))
                    print(goal_xy, "goal_xy")
                print(goal_xy, goal_xy[0], "goal")
                selected_uav_ids = parse_selected_uav_ids(
                    msg_parts[4] if len(msg_parts) > 4 else None
                )
                selected_indexes = selected_swarm_indexes(selected_uav_ids)
                selected_index_set = set(selected_indexes)
                print(
                    "[goal] selected_uav_ids",
                    selected_uav_ids,
                    "selected_indexes",
                    selected_indexes,
                )
                assign_goal_tasks(
                    selected_indexes,
                    goal_xy,
                    guided_circle_radius,
                    guided_circle_direction,
                )

                # Movement is owned by _goal_task_runner (background thread)
                # from here on -- this loop is read-only and exists purely to
                # plot what that thread is doing (matplotlib calls must happen
                # on the main thread, so the background thread can't plot
                # itself). check_for_new_command() keeps it preemptable/
                # concurrent-safe exactly like the search/split loops.
                if master_flag:
                    gui = viz.Gui(s)
                    my_seq = _last_seq
                    while True:
                        time.sleep(sleep_times.get(num_bots, 0.1))
                        check_for_new_command(my_seq)
                        goals_by_bot = [None] * len(s.swarm)
                        circles_by_bot = [None] * len(s.swarm)
                        planned_paths_by_bot = [None] * len(s.swarm)
                        with active_goal_tasks_lock:
                            still_active = False
                            for i in selected_indexes:
                                task = active_goal_tasks.get(i)
                                if task is None:
                                    continue
                                still_active = True
                                if task.get("type") == "guided_circle":
                                    circles_by_bot[i] = task.get("circle_points")
                                else:
                                    goals = task.get("goals", [])
                                    goal_index = task.get("goal_index", 0)
                                    planned_paths_by_bot[i] = goals
                                    if goal_index < len(goals):
                                        goals_by_bot[i] = goals[goal_index]
                        gui.show_goals(goals_by_bot)
                        gui.show_circles(circles_by_bot)
                        gui.show_planned_path(planned_paths_by_bot)
                        gui.show_gps_positions(live_gps_plot_points())
                        gui.update()
                        # print_sim_vs_real_latlon(selected_indexes, label="goal")
                        if not still_active:
                            gui.close()
                            break
                        if index == b"stop":
                            gui.close()
                            break
                data = b"index"
                continue
                goal_xy_index = 0
                if master_flag:
                    uav_home_pos = []
                    index = "data"
                    for vehicle in vehicles:
                        lat = vehicle.location.global_relative_frame.lat
                        lon = vehicle.location.global_relative_frame.lon
                        x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                        uav_home_pos.append((x / 2, y / 2))
                    print("uav_home_pos", uav_home_pos)
                    """
				        serialized_data = json.dumps(home_pos)
					    serialized_data="uav_home_pos" + serialized_data
					    for i in range(len(pos_array)):
					        uav1.sendto(serialized_data.encode(),uav1_server_address)
					        time.sleep(0.2)
					        uav2.sendto(serialized_data.encode(),uav2_server_address)
					        time.sleep(0.2)
					        uav3.sendto(serialized_data.encode(),uav3_server_address)
					        time.sleep(0.2)
					        #uav4.sendto(serialized_data.encode(), uav4_server_address)
					        #time.sleep(0.2)
					        #uav5.sendto(serialized_data.encode(), #uav5_server_address)
					    """
                s = sim.Simulation(
                    uav_home_pos, num_bots=len(pos_array), env_name=file_name
                )
                gui = viz.Gui(s)

                my_seq = _last_seq

                while 1:
                    time.sleep(sleep_times.get(num_bots))
                    check_for_new_command(my_seq)
                    if group_goal_flag:
                        group_goal_flag = False
                        guided_circle_flag = True
                        if "gui" in locals() and gui is not None:
                            gui.close()
                        break
                    goal_position = goal_xy[goal_xy_index]
                    for i, b in enumerate(s.swarm):
                        current_position = [b.x, b.y]
                        dx = abs(goal_position[0] - current_position[0])
                        dy = abs(goal_position[1] - current_position[1])
                        if dx <= 5 and dy <= 5:
                            bot_reached[i] = 1
                            print(
                                "Goal reached",
                                goal_xy_index,
                                goal_position,
                                bot_reached,
                            )
                            if any(element == 1 for element in bot_reached):
                                if goal_xy_index == len(goal_xy) - 1:
                                    print("group_goal_flag", group_goal_flag)
                                    group_goal_flag = True
                                    break
                                else:
                                    goal_xy_index += 1
                        else:
                            b.set_goal(goal_position[0], goal_position[1])
                            cmd = cvg.goal_area_cvg(i, b, goal_position)
                            cmd.exec(b)
                        if master_flag:
                            current_position = (b.x * 2, b.y * 2)
                            lat, lon = locatePosition.cartToGeo(
                                origin, endDistance, current_position
                            )
                            if same_alt_flag:
                                point1 = LocationGlobalRelative(lat, lon, same_height)
                            else:
                                point1 = LocationGlobalRelative(
                                    lat, lon, different_height[i]
                                )
                            vehicles[i].simple_goto(point1)

                    if "gui" in locals() and gui is not None:
                        gui.show_goals([goal_position] * len(s.swarm))
                        gui.update()

                    if index == b"stop":
                        print("Data", data)
                        group_goal_flag = False
                        if "gui" in locals() and gui is not None:
                            gui.close()
                        break
            except MissionPreempted:
                raise
            except Exception as e:
                import traceback

                traceback.print_exc()
                print("exception", e)
                pass

        if (guided_circle_flag) or data == b"guided_circle":
            multiple_goals_latlon = generate_points(
                float(goal_latlon[-1][0]),
                float(goal_latlon[-1][1]),
                8,
                int(guided_circle_radius),
                int(guided_circle_direction),
            )
            print("multiple_goals_latlon", multiple_goals_latlon)
            multiple_goals = []
            guided_circle_formation_table = [0] * num_bots
            for m in multiple_goals_latlon:
                x, y = locatePosition.geoToCart(origin, endDistance, m)
                multiple_goals.append((x / 2, y / 2))
            print("multiple_goals", multiple_goals)
            for b in s.swarm:
                length_arr = [0] * num_bots
                new_length_arr = [0] * num_bots
                count = [0] * num_bots
                step = 0
                search_flag = False
                all_bot_reach_flag = False
                bot_array = [0] * num_bots
                ind = [0] * num_bots
                my_seq = _last_seq
                while 1:
                    if guided_circle_formation_flag:
                        guided_circle_formation_flag = False
                        guided_circle_flag = False
                        break
                    time.sleep(sleep_times.get(num_bots))
                    check_for_new_command(my_seq)
                    for i, b in enumerate(s.swarm):
                        current_position = [b.x, b.y]
                        goal = multiple_goals[ind[i]]
                        # cmd =cvg.goal_area_cvg(i,b,goal)
                        # cmd+= disp_field(b,neighbourhood_radius=100)
                        # cmd.exec(b)
                        advance_bot_with_uav_pacing(
                            i, b, goal, label="guided_circle_formation"
                        )
                        dx = abs(goal[0] - current_position[0])
                        dy = abs(goal[1] - current_position[1])
                        circle_formation_table[i] = 1
                        # This is an intentional circular formation, not a finite
                        # fly-by route.  Advance its virtual circle points locally.
                        if dx <= 5 and dy <= 5:
                            ind[i] += 1
                            print("inddddddd", ind)
                            if ind[i] == len(multiple_goals):
                                ind[i] = 0
                        if master_flag:
                            current_position = [b.x * 2, b.y * 2]
                            lat, lon = locatePosition.cartToGeo(
                                origin, endDistance, current_position
                            )
                            if same_alt_flag:
                                point1 = LocationGlobalRelative(lat, lon, same_height)
                            else:
                                point1 = LocationGlobalRelative(
                                    lat, lon, different_height[i]
                                )
                            vehicles[i].simple_goto(point1)

                    if index == b"stop":
                        guided_circle_formation_flag = True
                        break

        if data.startswith(b"same"):
            print("msg", data)
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            data1, height = decoded_index.split(",")
            print(data1, height)
            same_alt_flag = True
            same_height = int(height)
            while True:
                for i, b in enumerate(s.swarm):
                    cmd = potf.velocity(
                        b.get_position(),
                        b.sim,
                        weights=potf.field_weights,
                        order=2,
                        max_dist=5,
                    )
                    cmd.exec(b)
                    if master_flag:
                        value = [b.x * 2, b.y * 2]
                        lat, lon = locatePosition.cartToGeo(origin, endDistance, value)
                        if same_alt_flag:
                            point1 = LocationGlobalRelative(lat, lon, same_height)
                        else:
                            point1 = LocationGlobalRelative(
                                lat, lon, different_height[i]
                            )
                        vehicles[i].simple_goto(point1)

                        if same_height - 1.5 <= alt[i] <= same_height + 1.5:
                            alt_count[i] = 1
                            if all(count == 1 for count in alt_count):
                                index = "data"
                                data = b"data"
                                same_alt_flag = True
                                break

                if index == b"stop":
                    index = "data"
                    data = b"index"
                    break

        if data.startswith(b"different"):
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            apply_different_heights(decoded_index)
            data = b"index"
            continue
            data1, height, step = decoded_index.split(",")
            same_alt_flag = False
            for h in range(num_bots):
                different_height[h] = int(height) + int(step) * h
            print("different_height", different_height)
            alt_count = [0] * num_bots
            print("alt_count", alt_count)
            alt = [0] * num_bots
            diff_height_flag = False
            alt_count1 = 0
            while True:
                if diff_height_flag:
                    diff_height_flag = False
                    break
                for i, b in enumerate(s.swarm):
                    cmd = potf.velocity(
                        b.get_position(),
                        b.sim,
                        weights=potf.field_weights,
                        order=2,
                        max_dist=5,
                    )
                    cmd.exec(b)
                    if master_flag:
                        value = [b.x * 2, b.y * 2]
                        lat, lon = locatePosition.cartToGeo(origin, endDistance, value)
                        if same_alt_flag:
                            point1 = LocationGlobalRelative(lat, lon, same_height)
                        else:
                            point1 = LocationGlobalRelative(
                                lat, lon, different_height[i]
                            )
                        vehicles[i].simple_goto(point1)
                        alt[i] = vehicles[i].location.global_relative_frame.alt
                        if (
                            different_height[i] - 1.5
                            <= alt[i]
                            <= different_height[i] + 1.5
                        ):
                            alt_count[i] = 1
                            if all(count == 1 for count in alt_count):
                                print("Reached target altitude")
                                index = "data"
                                data = b"data"
                                diff_height_flag = True
                                break
                    else:
                        data = b"data"
                        diff_height_flag = True
                        break

                if index == b"stop":
                    index = "data"
                    data = b"index"
                    break

        if (data.startswith(b"loiter_point")) or (circle_formation_flag):
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            f, base_lat, base_lon, radius, circle_direction = decoded_index.split(",")
            print("f,loiter_radius ", f, base_lat, base_lon, radius, circle_direction)

            if master_flag:
                uav_home_pos = []
                index = "data"
                for vehicle in vehicles:
                    lat = vehicle.location.global_relative_frame.lat
                    lon = vehicle.location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                    uav_home_pos.append((x / 2, y / 2))
                print("uav_home_pos", uav_home_pos)
                """
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.2)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.2)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.2)
					#uav4.sendto(serialized_data.encode(), uav4_server_address)
					#time.sleep(0.2)
					#uav5.sendto(serialized_data.encode(), #uav5_server_address)
				"""
                s = sim.Simulation(
                    uav_home_pos, num_bots=len(pos_array), env_name=file_name
                )

            index = "data"

            # center_lat , center_lon = locatePosition.destination_location(float(base_lat),float(base_lon),700,90)
            # print("center_lat , center_lon",center_lat , center_lon)
            # Generate 10 points in a circular formation with a radius of 500 meters around the given point
            multiple_goals_latlon = generate_points(
                float(base_lat), float(base_lon), 8, int(radius), int(circle_direction)
            )
            print("multiple_goals_latlon", multiple_goals_latlon)
            multiple_goals = []
            for m in multiple_goals_latlon:
                x, y = locatePosition.geoToCart(origin, endDistance, m)
                multiple_goals.append((x / 2, y / 2))
            print("multiple_goals", multiple_goals)
            circle_formation_goals = multiple_goals
            for b in s.swarm:
                print("circle_formation_table", circle_formation_table)
                length_arr = [0] * num_bots
                new_length_arr = [0] * num_bots
                count = [0] * num_bots
                step = 0
                all_bot_reach_flag = False
                bot_array = [0] * num_bots
                ind = [0] * num_bots
                step = 1
                while 1:
                    if start_flag:
                        break
                    time.sleep(sleep_times.get(num_bots))
                    for i, b in enumerate(s.swarm):
                        current_position = [b.x, b.y]
                        goal = multiple_goals[ind[i]]
                        if circle_formation_table[i] == 0:
                            lat = vehicles[i].location.global_relative_frame.lat
                            lon = vehicles[i].location.global_relative_frame.lon
                            x, y = locatePosition.geoToCart(
                                origin, endDistance, [lat, lon]
                            )
                            plane_points = [x / 2, y / 2]
                            advance_bot_with_uav_pacing(
                                i, b, goal, label="loiter_point"
                            )
                            # cmd =cvg.goal_area_cvg(i,b,goal)
                            # cmd+= disp_field(b,neighbourhood_radius=100)
                            # cmd.exec(b)
                            dx = abs(goal[0] - current_position[0])
                            dy = abs(goal[1] - current_position[1])
                            if master_flag:
                                current_position = [b.x * 2, b.y * 2]
                                lat, lon = locatePosition.cartToGeo(
                                    origin, endDistance, current_position
                                )
                                if step <= len(vehicles):
                                    step += 1
                                    print("!!!!!!!!!!")
                                    if same_alt_flag:
                                        point1 = LocationGlobalRelative(
                                            float(base_lat),
                                            float(base_lon),
                                            same_height,
                                        )
                                    else:
                                        point1 = LocationGlobalRelative(
                                            float(base_lat),
                                            float(base_lon),
                                            different_height[i],
                                        )
                                    vehicles[i].simple_goto(point1)
                                if step == 100:
                                    if same_alt_flag:
                                        point1 = LocationGlobalRelative(
                                            float(base_lat),
                                            float(base_lon),
                                            same_height,
                                        )
                                    else:
                                        point1 = LocationGlobalRelative(
                                            float(base_lat),
                                            float(base_lon),
                                            different_height[i],
                                        )
                                    vehicles[i].simple_goto(point1)
                                if step != 100:
                                    # current_altitude = vehicle.location.global_relative_frame.alt
                                    current_altitude = vehicles[
                                        i
                                    ].location.global_relative_frame.alt
                                    distance = locatePosition.distance_bearing(
                                        vehicles[i].location.global_relative_frame.lat,
                                        vehicles[i].location.global_relative_frame.lon,
                                        float(base_lat),
                                        float(base_lon),
                                    )
                                    if (
                                        different_height[i] - 5
                                    ) <= current_altitude <= (
                                        different_height[i] + 5
                                    ) and distance < 150:
                                        uav_home_pos = []
                                        step = 100
                                        for vehicle in vehicles:
                                            lat = (
                                                vehicle.location.global_relative_frame.lat
                                            )
                                            lon = (
                                                vehicle.location.global_relative_frame.lon
                                            )
                                            x, y = locatePosition.geoToCart(
                                                origin, endDistance, [lat, lon]
                                            )
                                            uav_home_pos.append((x / 2, y / 2))
                                        s = sim.Simulation(
                                            uav_home_pos,
                                            num_bots=len(pos_array),
                                            env_name=file_name,
                                        )
                            if i < len(robots):
                                robots[i] = (x / 2, y / 2)
                            msg = ",".join(
                                [f"{robot[0]},{robot[1]}" for robot in robots]
                            )
                            if dx < 50 and dy < 50:
                                cmd = cvg.goal_area_cvg(i, b, goal)
                                cmd += disp_field(b, neighbourhood_radius=100)
                                cmd.exec(b)
                                dx = abs(goal[0] - current_position[0])
                                dy = abs(goal[1] - current_position[1])
                                circle_formation_table[i] = 1
                                if dx <= 50 and dy <= 50:
                                    ind[i] += 1
                                    if ind[i] == len(multiple_goals):
                                        ind[i] = 0

                                if master_flag:
                                    current_position = [b.x * 2, b.y * 2]
                                    lat, lon = locatePosition.cartToGeo(
                                        origin, endDistance, current_position
                                    )
                                    if same_alt_flag:
                                        point1 = LocationGlobalRelative(
                                            lat, lon, same_height
                                        )
                                    else:
                                        point1 = LocationGlobalRelative(
                                            lat, lon, different_height[i]
                                        )
                                    vehicles[i].simple_goto(point1)

                            else:
                                continue

                        if circle_formation_table[i] == 1:
                            cmd = cvg.goal_area_cvg(i, b, goal)
                            cmd += disp_field(b, neighbourhood_radius=100)
                            cmd.exec(b)
                            dx = abs(goal[0] - current_position[0])
                            dy = abs(goal[1] - current_position[1])
                            circle_formation_table[i] = 1
                            if dx <= 10 and dy <= 10:
                                ind[i] += 1
                                print("index", ind)
                                if ind[i] == len(multiple_goals):
                                    ind[i] = 0

                            if master_flag:
                                current_position = [b.x * 2, b.y * 2]
                                lat, lon = locatePosition.cartToGeo(
                                    origin, endDistance, current_position
                                )
                                if same_alt_flag:
                                    point1 = LocationGlobalRelative(
                                        lat, lon, same_height
                                    )
                                else:
                                    point1 = LocationGlobalRelative(
                                        lat, lon, different_height[i]
                                    )
                                vehicles[i].simple_goto(point1)

                        else:
                            continue

                    if index == b"stop":
                        start_flag = False
                        circle_formation_flag = False
                        break

        if data.startswith(b"grid_path_planning"):
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            f, center_lat, center_lon, num_uavs, grid_space, coverage_area = (
                decoded_index.split(",")
            )
            curve = BezierCurve(
                origin,
                float(center_lat),
                float(center_lon),
                int(num_uavs),
                int(grid_space),
                int(coverage_area),
            )
            val = curve.GridFormation()
            path = curve.generate_bezier_curve()
            start_multiple_goals = path

        if (data.startswith(b"navigate")) or (start_flag):
            print("data", data)
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            f, center_lat, center_lon, num_uavs, grid_space, coverage_area = (
                decoded_index.split(",")
            )
            curve = BezierCurve(
                origin,
                float(center_lat),
                float(center_lon),
                int(num_uavs),
                int(grid_space),
                int(coverage_area),
            )
            val = curve.GridFormation()
            path = curve.generate_bezier_curve()
            multiple_goals = path
            if master_flag:
                # time.sleep(0.1)
                start_flag = True
                uav_home_pos = []
                index = "data"
                for vehicle in vehicles:
                    lat = vehicle.location.global_relative_frame.lat
                    lon = vehicle.location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                    uav_home_pos.append((x / 2, y / 2))
                """
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data				
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.2)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.2)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.2)
					#uav4.sendto(serialized_data.encode(), uav4_server_address)
					#time.sleep(0.2)
					#uav5.sendto(serialized_data.encode(), #uav5_server_address)
				"""
            s = sim.Simulation(
                uav_home_pos, num_bots=len(pos_array), env_name=file_name
            )
            gui = viz.Gui(s)

            index = "data"

            for b in s.swarm:
                search_flag = False
                all_bot_reach_flag = False
                bot_array = [0] * num_bots
                ind = 0
                my_seq = _last_seq
                diverted_indexes = set()
                while 1:
                    if not start_flag:
                        start_flag = False
                        break
                    time.sleep(sleep_times.get(num_bots))
                    check_for_new_command(my_seq)
                    bot_array = [0] * num_bots
                    for i, b in enumerate(s.swarm):
                        if i in active_goal_tasks:
                            diverted_indexes.add(i)
                        if i in diverted_indexes:
                            continue
                        current_position = [b.x, b.y]
                        if skip_wp_flag:
                            with open(csv_path, "a") as csvfile:
                                print("next_wp", next_wp)
                                next_wp = int(next_wp) - 1
                                start_return_csv_flag = True
                                fieldnames = ["waypoint"]
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow({"waypoint": next_wp})
                                goal_path_csv_array.append(next_wp)
                                print("goal_path_csv_array", goal_path_csv_array)
                                goal_path_csv_array_flag = True
                            for x, c in enumerate(s.swarm):
                                goal_table[x] = next_wp
                            print("goal_table", goal_table)
                            skip_wp_flag = False
                            ind = goal_table[i]

                        goal = multiple_goals[ind]
                        # cmd =cvg.goal_area_cvg(i,b,goal)
                        # cmd+= disp_field(b,neighbourhood_radius=100)
                        # cmd.exec(b)
                        advance_bot_with_uav_pacing(i, b, goal, label="navigate")
                        dx = abs(goal[0] - current_position[0])
                        dy = abs(goal[1] - current_position[1])
                        if dx <= 1 and dy <= 1:
                            bot_array[i] = 1
                        if any(element == 1 for element in bot_array):
                            if ind == len(multiple_goals) - 1:
                                print("all_bot_reach_flag", all_bot_reach_flag)
                                all_bot_reach_flag = True
                                break
                            else:
                                ind += 1
                                print("ind", ind, multiple_goals[ind])

                        if all_bot_reach_flag == True:
                            with open(csv_path, "a") as csvfile:
                                start_return_csv_flag = True
                                fieldnames = ["waypoint"]
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow(
                                    {"waypoint": multiple_goals.index(goal)}
                                )
                                print(
                                    "multiple_goals.index(goal)",
                                    multiple_goals.index(goal),
                                )
                                goal_path_csv_array.append(multiple_goals.index(goal))
                                print("goal_path_csv_array", goal_path_csv_array)
                                goal_path_csv_array_flag = True
                            all_bot_reach_flag = False
                            bot_array = [0] * num_bots
                            if ind == len(multiple_goals) - 1:
                                print("Break")
                                start_flag = False
                                break
                        if master_flag:
                            current_position = [b.x * 2, b.y * 2]
                            lat, lon = locatePosition.cartToGeo(
                                origin, endDistance, current_position
                            )
                            if same_alt_flag:
                                point1 = LocationGlobalRelative(lat, lon, same_height)
                            else:
                                point1 = LocationGlobalRelative(
                                    lat, lon, different_height[i]
                                )
                            vehicles[i].simple_goto(point1)

                    if "gui" in locals() and gui is not None:
                        gui.show_goals([multiple_goals[ind]] * len(s.swarm))
                        gui.show_planned_path([multiple_goals] * len(s.swarm))
                        gui.show_gps_positions(live_gps_plot_points())
                        gui.update()
                        print_sim_vs_real_latlon(
                            [
                                i
                                for i in range(len(s.swarm))
                                if i not in diverted_indexes
                            ],
                            label="navigate",
                        )

                    if index == b"stop":
                        print(
                            "start_flag",
                            start_flag,
                            "circle_formation_flag",
                            circle_formation_flag,
                        )
                        start_flag = False
                        circle_formation_flag = False
                        if "gui" in locals() and gui is not None:
                            gui.close()
                        break

        if (data.startswith(b"search")) or (search_flag):
            print("data", data)
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            print("decoded_index", decoded_index)
            msg_parts = decoded_index.split(",", 6)
            selected_uav_raw = msg_parts[6] if len(msg_parts) > 6 else None
            f, center_lat, center_lon, num_uavs, grid_space, coverage_area = msg_parts[
                :6
            ]
            selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
            selected_indexes = selected_swarm_indexes(selected_uav_ids)
            selected_index_set = set(selected_indexes)
            # A bot can still have an active_goal_tasks entry from an earlier
            # goal command (still en route, or already looping forever as a
            # guided_circle) -- without clearing it here, this fresh search
            # would see it below and mark the bot "diverted" before it's
            # ever given a single search waypoint, silently ceding control
            # to the stale task instead of actually starting the search.
            with active_goal_tasks_lock:
                for i in selected_indexes:
                    active_goal_tasks.pop(i, None)
            effective_num_uavs = max(
                1, len(selected_indexes) if selected_uav_ids else int(num_uavs)
            )
            print(
                "[search] selected_uav_ids",
                selected_uav_ids,
                "selected_indexes",
                selected_indexes,
            )
            # Whole-swarm search (no explicit subset) targets every connected
            # UAV in pos_array order -- same order effective_num_uavs falls
            # back to num_uavs (== len(pos_array)) for, so the two line up.
            ids_for_curve = (
                selected_uav_ids if selected_uav_ids else pos_array[:effective_num_uavs]
            )
            curve = BezierCurveMultiple(
                origin,
                float(center_lat),
                float(center_lon),
                effective_num_uavs,
                int(grid_space),
                int(coverage_area),
                uav_ids=ids_for_curve,
            )
            val = curve.GridFormation()
            path = curve.generate_bezier_curve()
            search_step = 1
            if master_flag:
                index = "data"
                uav_home_pos = []
                for vehicle in vehicles:
                    lat = vehicle.location.global_relative_frame.lat
                    lon = vehicle.location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                    uav_home_pos.append((x / 2, y / 2))
                """
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.2)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.2)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.2)
					#uav4.sendto(serialized_data.encode(), uav4_server_address)
					#time.sleep(0.2)
					#uav5.sendto(serialized_data.encode(), #uav5_server_address)			
				"""
                swarm_tasks.utils.robot.DEFAULT_SIZE = 0.4
                s = sim.Simulation(uav_home_pos, num_bots=num_bots, env_name=file_name)
                gui = viz.Gui(s)

            print("Search Started")
            search_flag_val = 0
            f = ""
            num_lines = [0] * len(pos_array)
            goal_position = []
            cwd = os.getcwd()
            print("search_flag_val", search_flag_val)
            grid_path_array = [0] * len(pos_array)
            # A previous split/search may have left this module-level list at
            # a different fleet size.  Start each mission in the current
            # topology, rather than waiting for the first removal to expose it.
            all_uav_csv_grid_array = [0] * len(pos_array)
            if search_flag_val == 0:
                search_flag_val += 1
                csv_file_paths = []
                for i in range(1, effective_num_uavs + 1):
                    csv_file_paths.append(uav_path_csv(ids_for_curve[i - 1]))
                print("csv_file_paths", csv_file_paths)
            removed_grid_path_array_index = 0
            print("grid_path_array", grid_path_array)
            current_goals = [None] * len(pos_array)
            planned_paths_by_bot = [None] * len(pos_array)
            my_seq = _last_seq
            diverted_indexes = set()
            origin = read_origin(rectangles_path)
            while 1:
                if num_bots == 10:
                    time.sleep(0.1)
                elif num_bots == 9:
                    time.sleep(0.1)
                elif num_bots == 8:
                    time.sleep(0.11)
                elif num_bots == 7:
                    time.sleep(0.11)
                elif num_bots == 6:
                    time.sleep(0.12)  # verified
                elif num_bots == 5:
                    time.sleep(0.12)  # verified
                elif num_bots == 4:
                    time.sleep(0.123)
                elif num_bots == 3:
                    time.sleep(0.125)
                elif num_bots == 2:
                    time.sleep(0.13)
                elif num_bots == 1:
                    time.sleep(0.13)
                check_for_new_command(my_seq)
                if vehicle_lost_flag:
                    vehicle_lost_flag = True
                    x = remove_vehicle()
                    print(x)
                if remove_bot_flag:
                    # Preserve progress for redistribution before compacting
                    # the foreground mission arrays below.
                    for m in sorted(set(remove_bot_array), reverse=True):
                        if 0 <= m < len(all_uav_csv_grid_array):
                            removed_uav_grid.append(all_uav_csv_grid_array[m])
                        if 0 <= m < len(grid_path_array):
                            removed_grid_path_length.append(grid_path_array[m])
                selected_indexes = synchronize_mission_topology(
                    selected_indexes,
                    csv_file_paths,
                    all_uav_csv_grid_array,
                    grid_path_array,
                    num_lines,
                    current_goals,
                    planned_paths_by_bot,
                )
                selected_index_set = set(selected_indexes)

                if search_step == 1:
                    for path_slot, bot_index in enumerate(selected_indexes):
                        if path_slot >= len(csv_file_paths) or bot_index >= len(
                            all_uav_csv_grid_array
                        ):
                            print(
                                "[search] skipped stale path assignment",
                                path_slot,
                                bot_index,
                            )
                            continue
                        all_uav_csv_grid_array[bot_index] = csv_file_paths[path_slot]
                        # Read once here (not every tick), per bot -- both the
                        # line count used for THIS bot's own grid_path_array
                        # bounds check below, and the whole planned route for
                        # the show_planned_path() overlay. Per-bot matters: a
                        # concurrent redirect (search re-targeting a UAV
                        # subset while this mission is still running, see
                        # start_search_mission()) overwrites just that
                        # subset's csv files with a differently-sized grid --
                        # a single num_lines shared across every bot (read
                        # from whichever one file) would silently go wrong
                        # for every OTHER, unrelated bot still reading its
                        # own file, causing an out-of-range
                        # read_specific_line() the moment that bot's
                        # grid_path_array outpaces the now-wrong shared bound.
                        try:
                            with open(all_uav_csv_grid_array[bot_index], "rt") as f:
                                rows = list(csv.reader(f))
                            num_lines[bot_index] = len(rows)
                            planned_paths_by_bot[bot_index] = [
                                (float(row[0]), float(row[1])) for row in rows
                            ]
                        except Exception as e:
                            print("[planned-path] failed to read for bot", bot_index, e)
                    print(
                        "all_uav_csv_grid_array",
                        all_uav_csv_grid_array,
                        "num_lines",
                        num_lines,
                    )
                    search_step += 1
                for i, b in enumerate(s.swarm):
                    if i not in selected_index_set:
                        continue
                    if i in active_goal_tasks:
                        diverted_indexes.add(i)
                    if i in diverted_indexes:
                        continue
                    if len(checkall_removed_grid_path_array_start_val) == len(
                        pos_array
                    ):
                        if all(
                            c == 1 for c in checkall_removed_grid_path_array_start_val
                        ):
                            landing_flag = True
                    else:
                        pass
                    if (
                        all(
                            grid_path_array[x] >= int(num_lines[x])
                            for x in selected_indexes
                        )
                        and removed_grid_path_length != []
                        and not removed_grid_path_array_flag
                    ):
                        print("removed_grid_path_length", removed_grid_path_length)
                        allocation, remaining_points_list = allocate_drones(
                            int(num_lines[i]),
                            removed_grid_path_length,
                            len(selected_indexes),
                        )
                        print(
                            "allocation,remaining_points_list",
                            allocation,
                            remaining_points_list,
                        )
                        for x, v in enumerate(remaining_points_list):
                            print("x", x)
                            if removed_grid_path_length[x] == 1:
                                start_index = removed_grid_path_length[x]
                            else:
                                start_index = removed_grid_path_length[x] - 1
                            print("start_index", start_index)
                            print("JJJ", allocation[x])
                            if (allocation[x] == 0) and removed_grid_path_length[
                                x
                            ] != int(num_lines[i]):
                                uncovered_area_points.append(
                                    removed_grid_path_length[x]
                                )
                                uncovered_area_filename.append(removed_uav_grid[x])
                                print(
                                    "uncovered_area_points",
                                    x,
                                    v,
                                    uncovered_area_points,
                                    uncovered_area_filename,
                                )
                                continue
                            elif allocation[x] == 0:
                                continue
                            add_points = math.ceil(
                                remaining_points_list[x] / allocation[x]
                            )
                            print("add_points", math.ceil(add_points))
                            end_index = start_index + add_points + 1
                            print("end_index", math.ceil(end_index))
                            for m in range(allocation[x]):
                                print(
                                    "removed_grid_path_array_index",
                                    removed_grid_path_array_index,
                                )
                                if m != 0:
                                    end_index += add_points
                                if end_index > int(num_lines[i]):
                                    end_index = int(num_lines[i])
                                removed_grid_path_array[
                                    removed_grid_path_array_index
                                ] = (start_index, end_index)
                                removed_grid_path_array_start_val[
                                    removed_grid_path_array_index
                                ] = start_index
                                removed_grid_filename[removed_grid_path_array_index] = (
                                    removed_uav_grid[x]
                                )
                                print(
                                    "removed_grid_path_array",
                                    removed_grid_path_array,
                                    removed_grid_path_array_start_val,
                                    removed_grid_filename,
                                )
                                start_index = end_index
                                removed_grid_path_array_index += 1
                        print(
                            "removed_grid_path_array!!!!!",
                            removed_grid_path_array,
                            removed_grid_path_array_start_val,
                            removed_grid_filename,
                        )
                        removed_grid_path_array_flag = True

                    if (
                        all(
                            grid_path_array[x] >= int(num_lines[x])
                            for x in selected_indexes
                        )
                        and not removed_grid_path_length != []
                    ):
                        landing_flag = True
                    if removed_grid_path_array_flag:
                        if removed_grid_path_array_start_val[i] == 0:
                            checkall_removed_grid_path_array_start_val[i] = 1
                            print(
                                "checkall_removed_grid_path_array_start_val",
                                checkall_removed_grid_path_array_start_val,
                            )
                            continue
                        if (
                            removed_grid_path_array_start_val[i]
                            == removed_grid_path_array[i][1]
                        ):
                            checkall_removed_grid_path_array_start_val[i] = 1
                            if uncovered_area_points != []:
                                print("uncovered_area_points", uncovered_area_points)
                                for u, uncovered_area_point in enumerate(
                                    uncovered_area_points
                                ):
                                    removed_grid_path_array[i] = (
                                        uncovered_area_point,
                                        int(num_lines[i]) + 1,
                                    )
                                    print(
                                        "removed_grid_path_array",
                                        removed_grid_path_array,
                                    )
                                    removed_grid_path_array_start_val[i] = (
                                        uncovered_area_points[u]
                                    )
                                    removed_grid_filename[i] = uncovered_area_filename[
                                        u
                                    ]
                                    removed_grid_path_array[i] = (
                                        uncovered_area_points[u],
                                        int(num_lines[i]),
                                    )
                                    print(
                                        "removed_grid_path_array_start_val",
                                        removed_grid_path_array_start_val,
                                        removed_grid_filename,
                                    )
                                    checkall_removed_grid_path_array_start_val[i] = 0
                                    uncovered_area_points.pop(u)
                                    uncovered_area_filename.pop(u)
                            else:
                                continue
                    if (
                        grid_path_array[i] >= int(num_lines[i])
                        and not removed_grid_path_array_flag
                    ):
                        continue
                    if removed_grid_path_array_flag:
                        goal_lat_lon = read_specific_line(
                            removed_grid_filename[i],
                            removed_grid_path_array_start_val[i],
                        )
                    else:
                        goal_lat_lon = read_specific_line(
                            all_uav_csv_grid_array[i], grid_path_array[i]
                        )
                    x, y, isCurve = (
                        goal_lat_lon[0][0],
                        goal_lat_lon[0][1],
                        goal_lat_lon[0][2],
                    )
                    goal = (x, y)
                    current_goals[i] = goal
                    # print(f"CSV goal for bot {i}: {goal}, bot pos: {b.x:.1f}, {b.y:.1f}, ratio: {goal[0]/b.x:.2f}")
                    _dis, step_size = advance_bot_with_uav_pacing(
                        i, b, goal, label="search"
                    )
                    current_position = [b.x, b.y]
                    dx = abs(goal[0] - current_position[0])
                    dy = abs(goal[1] - current_position[1])
                    is_curve = str(isCurve).strip().lower() == "true"
                    guidance_position = None
                    if is_curve:
                        curve_index = (
                            removed_grid_path_array_start_val[i]
                            if removed_grid_path_array_flag
                            else grid_path_array[i]
                        )
                        curve_csv = (
                            removed_grid_filename[i]
                            if removed_grid_path_array_flag
                            else all_uav_csv_grid_array[i]
                        )
                        curve_num_lines = (
                            removed_grid_path_array[i][1]
                            if removed_grid_path_array_flag
                            else int(num_lines[i])
                        )
                        curve_guidance = curve_lookahead_goal(
                            curve_csv, curve_index, curve_num_lines, goal, (b.x, b.y)
                        )
                        guidance_position = curve_guidance_position(b, curve_guidance)
                        lookahead_goal = curve_guidance[1] if curve_guidance else goal
                        print(
                            f"[CURVE] idx={curve_index} "
                            f"bot=({b.x:.2f},{b.y:.2f}) "
                            f"goal=({goal[0]:.2f},{goal[1]:.2f}) "
                            f"lookahead=({lookahead_goal[0]:.2f},{lookahead_goal[1]:.2f}) "
                            f"step={step_size:.2f}"
                        )
                    # Bot motion remains on the current CSV sample; only the fixed-wing
                    # target is moved ahead continuously through a curve.
                    position_for_uav = (
                        guidance_position
                        if guidance_position is not None
                        else (b.x, b.y)
                    )
                    value = [position_for_uav[0] * 2, position_for_uav[1] * 2]
                    next_goal = None
                    is_final = False
                    try:
                        if removed_grid_path_array_flag:
                            next_index = removed_grid_path_array_start_val[i] + 1
                            is_final = next_index >= removed_grid_path_array[i][1]
                            if not is_final:
                                next_row = read_specific_line(
                                    removed_grid_filename[i], next_index
                                )
                                next_goal = (next_row[0][0], next_row[0][1])
                        else:
                            next_index = grid_path_array[i] + 1
                            is_final = next_index >= int(num_lines[i])
                            if not is_final:
                                next_row = read_specific_line(
                                    all_uav_csv_grid_array[i], next_index
                                )
                                next_goal = (next_row[0][0], next_row[0][1])
                    except Exception as e:
                        print("[search] next point read failed", i, e)
                    reached_search_waypoint, uav_goal_distance = uav_reached_waypoint(
                        i,
                        b,
                        goal,
                        sim_radius=15,
                        next_goal=next_goal,
                        is_curve=is_curve,
                        is_final=is_final,
                    )
                    if reached_search_waypoint:
                        if BOT_SYNC_DEBUG:
                            print(
                                f"[waypoint-advance] label=search bot={i} "
                                f"index={grid_path_array[i]}->{grid_path_array[i] + 1} "
                                f"bot=({b.x:.2f},{b.y:.2f}) goal=({goal[0]:.2f},{goal[1]:.2f})"
                            )
                        if uav_goal_distance is not None:
                            print(
                                f"[uav-flyby] bot {i}: switching search point at "
                                f"{uav_goal_distance:.1f} m"
                            )
                        if (
                            grid_path_array[i] >= int(num_lines[i])
                            and not removed_grid_path_array_flag
                        ):
                            continue
                        if (
                            grid_path_array[i] >= int(num_lines[i])
                            and removed_grid_path_array_flag
                        ):
                            removed_grid_path_array_start_val[i] += 1
                            print(
                                "removed_grid_path_array_start_val",
                                removed_grid_path_array_start_val,
                            )

                        else:
                            grid_path_array[i] += 1
                            print("grid_path_array", grid_path_array)
                    # cmd.exec(b,step_size)
                    if master_flag:
                        if pop_flag_arr[i] == 1:
                            lat, lon = locatePosition.cartToGeo(
                                origin, endDistance, value
                            )
                        if same_alt_flag:
                            point1 = LocationGlobalRelative(lat, lon, same_height)
                        else:
                            point1 = LocationGlobalRelative(
                                lat, lon, different_height[i]
                            )
                        vehicles[i].simple_goto(point1)

                s.time_elapsed += 1
                if master_flag and "gui" in locals() and gui is not None:
                    gui.show_goals(current_goals)
                    gui.show_planned_path(planned_paths_by_bot)
                    gui.show_gps_positions(live_gps_plot_points())
                    gui.update()

                if index == b"stop":
                    search_flag = False
                    if master_flag and "gui" in locals() and gui is not None:
                        gui.close()
                    break

        if (data.startswith(b"split")) or (data.startswith(b"specificsplit")):
            if data.startswith(b"specificsplit"):
                try:
                    decoded_index = data.decode(
                        "utf-8"
                    )  # Assuming utf-8 encoding, adjust if needed
                    msg_parts = decoded_index.split("_")
                    print("msg_parts", msg_parts)
                    f = msg_parts[0]  # First coordinate pair
                    center_lat_lon_array = msg_parts[1]  # All other coordinates
                    center_lat_lon_array = json.loads(center_lat_lon_array)
                    print("center_lat_lon_array", center_lat_lon_array)
                    uav_array = msg_parts[2]
                    uav_array = json.loads(uav_array)
                    grid_space = msg_parts[3]
                    grid_space = json.loads(grid_space)
                    print("grid_space", grid_space)
                    coverage_area = msg_parts[4]
                    coverage_area = json.loads(coverage_area)
                    print("coverage_area", coverage_area)
                    # Subset gate: assigned UAVs must be a non-empty subset of
                    # the currently-connected pos_array -- they no longer have
                    # to cover every connected UAV, so some can be left out
                    # for a separate command. selected_uav_ids/selected_indexes
                    # (set below) gate the shared csv_file_paths/movement-loop
                    # code further down so only these indexes are touched.
                    assigned_uav_ids = [int(u) for group in uav_array for u in group]
                    if not assigned_uav_ids or not set(assigned_uav_ids).issubset(
                        set(pos_array)
                    ):
                        print(
                            "[specificsplit] rejected: group assignment",
                            set(assigned_uav_ids),
                            "not a subset of connected pos_array",
                            set(pos_array),
                        )
                        continue
                    else:
                        selected_uav_ids = assigned_uav_ids
                        split = SpecificSplitMission(
                            origin=origin,
                            center_lat_lons=center_lat_lon_array,
                            drone_array=uav_array,
                            grid_spacing=grid_space,
                            coverage_area=coverage_area,
                        )
                        isDone = split.GroupSplitting(
                            center_lat_lons=center_lat_lon_array,
                            drone_array=uav_array,
                            grid_spacing=grid_space,
                            coverage_area=coverage_area,
                        )
                except Exception as e:
                    print("Exception", e)
                    continue
            if data.startswith(b"split"):
                try:
                    decoded_index = data.decode(
                        "utf-8"
                    )  # Assuming utf-8 encoding, adjust if needed
                    msg_parts = decoded_index.split("_")
                    print("msg_parts", msg_parts, len(msg_parts))
                    f = msg_parts[0]  # First coordinate pair
                    # msg_parts[2] is the operator's actual UAV-id selection from the
                    # GCS (not just a headcount) -- honored below, gated as a
                    # subset of the swarm computer's own live pos_array.
                    selected_uav_ids = [int(u) for u in json.loads(msg_parts[2])]
                    grid_space = msg_parts[3]
                    grid_space = json.loads(grid_space)
                    coverage_area = msg_parts[4]
                    coverage_area = json.loads(coverage_area)
                    center_lat_lon_array = msg_parts[1]  # All other coordinates
                    center_lat_lon_array = json.loads(center_lat_lon_array)
                    if not selected_uav_ids or not set(selected_uav_ids).issubset(
                        set(pos_array)
                    ):
                        print(
                            "[split] rejected: GCS selection",
                            set(selected_uav_ids),
                            "not a subset of connected pos_array",
                            set(pos_array),
                        )
                        continue
                    else:
                        split = AutoSplitMission(
                            origin=origin,
                            center_lat_lons=center_lat_lon_array,
                            drone_list=selected_uav_ids,
                            grid_spacing=int(grid_space),
                            coverage_area=int(coverage_area),
                        )
                        isDone = split.GroupSplitting(
                            center_lat_lons=center_lat_lon_array,
                            num_of_drones=len(selected_uav_ids),
                            grid_spacing=int(grid_space),
                            coverage_area=int(coverage_area),
                        )
                except Exception as e:
                    print("Exception", e)

            split_flag = True
            split_flag_val = 0
            search_step = 1
            all_uav_csv_grid_array = [0] * len(pos_array)
            grid_path_array = [0] * len(pos_array)
            num_lines = [0] * len(pos_array)
            pop_flag_arr = [1] * len(pos_array)
            removed_uav_grid = []
            removed_grid_path_length = []
            uncovered_area_points = []
            uncovered_area_filename = []
            removed_grid_path_array_flag = False
            removed_grid_path_array = [0] * len(pos_array)
            removed_grid_filename = [0] * len(pos_array)
            removed_grid_path_array_start_val = [0] * len(pos_array)
            checkall_removed_grid_path_array_start_val = [0] * len(pos_array)
            remove_bot_flag = False
            remove_bot_array = []
            selected_indexes = selected_swarm_indexes(selected_uav_ids)
            selected_index_set = set(selected_indexes)
            print(
                "[split] selected_uav_ids",
                selected_uav_ids,
                "selected_indexes",
                selected_indexes,
            )
            if master_flag:
                index = "data"
                uav_home_pos = []
                for vehicle in vehicles:
                    lat = vehicle.location.global_relative_frame.lat
                    lon = vehicle.location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                    uav_home_pos.append((x / 2, y / 2))
                """
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data				
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.2)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.2)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.2)
					#uav4.sendto(serialized_data.encode(), uav4_server_address)
					#time.sleep(0.2)
					#uav5.sendto(serialized_data.encode(), #uav5_server_address)			
				"""
                swarm_tasks.utils.robot.DEFAULT_SIZE = 0.4
                s = sim.Simulation(uav_home_pos, num_bots=num_bots, env_name=file_name)
                gui = viz.Gui(s)

            print("Group Splitting Started")
            f = ""
            num_lines = [0] * len(pos_array)
            print("num_lines", num_lines)
            goal_bot_num = 0
            goal_position = []
            cwd = os.getcwd()
            grid_path_array = [0] * len(pos_array)
            print("split_flag_val", split_flag_val)
            planned_paths_by_bot = [None] * len(pos_array)
            if split_flag_val == 0:
                split_flag_val += 1
                csv_file_paths = []
                # Both plain split (AutoSplitMission.drone_list=selected_uav_ids) and
                # specific_split (uav_array) only write per-drone files for the
                # selected subset -- so only build/open a file for each selected
                # bot_index (real UAV id via pos_array[bot_index]), never the
                # full pos_array, or an unselected UAV's missing file would
                # crash this open().
                for path_slot, bot_index in enumerate(selected_indexes):
                    uav_id = pos_array[bot_index]
                    csv_path = uav_path_csv(uav_id)
                    csv_file_paths.append(csv_path)
                    reader = csv.reader(open(csv_path))
                    rows = list(reader)
                    num_lines[bot_index] = len(rows)
                    # Whole planned route cached once here (not every tick)
                    # purely for the show_planned_path() overlay below.
                    try:
                        planned_paths_by_bot[bot_index] = [
                            (float(row[0]), float(row[1])) for row in rows
                        ]
                    except Exception as e:
                        print("[planned-path] failed to parse for bot", bot_index, e)
                print("csv_file_paths", csv_file_paths, num_lines)
            removed_grid_path_array_index = 0
            my_seq = _last_seq
            print("grid_path_array", grid_path_array)
            current_goals = [None] * len(pos_array)
            diverted_indexes = set()
            while 1:
                time.sleep(sleep_times.get(num_bots))
                check_for_new_command(my_seq)
                if vehicle_lost_flag:
                    vehicle_lost_flag = True
                    x = remove_vehicle()
                    print(x)
                if remove_bot_flag:
                    for m in sorted(set(remove_bot_array), reverse=True):
                        if 0 <= m < len(all_uav_csv_grid_array):
                            removed_uav_grid.append(all_uav_csv_grid_array[m])
                        if 0 <= m < len(grid_path_array):
                            removed_grid_path_length.append(grid_path_array[m])
                selected_indexes = synchronize_mission_topology(
                    selected_indexes,
                    csv_file_paths,
                    all_uav_csv_grid_array,
                    grid_path_array,
                    num_lines,
                    current_goals,
                    planned_paths_by_bot,
                )
                selected_index_set = set(selected_indexes)

                if search_step == 1:
                    for path_slot, bot_index in enumerate(selected_indexes):
                        if path_slot >= len(csv_file_paths) or bot_index >= len(
                            all_uav_csv_grid_array
                        ):
                            print(
                                "[split] skipped stale path assignment",
                                path_slot,
                                bot_index,
                            )
                            continue
                        all_uav_csv_grid_array[bot_index] = csv_file_paths[path_slot]
                    print("all_uav_csv_grid_array", all_uav_csv_grid_array)
                    search_step += 1
                for i, b in enumerate(s.swarm):
                    if i not in selected_index_set:
                        continue
                    if i in active_goal_tasks:
                        diverted_indexes.add(i)
                    if i in diverted_indexes:
                        continue
                    if len(checkall_removed_grid_path_array_start_val) == len(
                        pos_array
                    ):
                        if all(
                            c == 1 for c in checkall_removed_grid_path_array_start_val
                        ):
                            landing_flag = True
                    else:
                        # print("length oflen(checkall_removed_grid_path_array_start_val",len(checkall_removed_grid_path_array_start_val))
                        pass
                    if (
                        all(
                            grid_path_array[x] >= int(num_lines[x])
                            for x in selected_indexes
                        )
                        and removed_grid_path_length != []
                        and not removed_grid_path_array_flag
                    ):
                        print("removed_grid_path_length", removed_grid_path_length)
                        allocation, remaining_points_list = allocate_drones(
                            int(num_lines[i]),
                            removed_grid_path_length,
                            len(selected_indexes),
                        )
                        print(
                            "allocation,remaining_points_list",
                            allocation,
                            remaining_points_list,
                        )
                        for x, v in enumerate(remaining_points_list):
                            print("x", x)
                            if removed_grid_path_length[x] == 1:
                                start_index = removed_grid_path_length[x]
                            else:
                                start_index = removed_grid_path_length[x] - 1
                            print("start_index", start_index)
                            print("JJJ", allocation[x])
                            if (allocation[x] == 0) and removed_grid_path_length[
                                x
                            ] != int(num_lines[i]):
                                uncovered_area_points.append(
                                    removed_grid_path_length[x]
                                )
                                uncovered_area_filename.append(removed_uav_grid[x])
                                print(
                                    "uncovered_area_points",
                                    x,
                                    v,
                                    uncovered_area_points,
                                    uncovered_area_filename,
                                )
                                continue
                            elif allocation[x] == 0:
                                continue
                            add_points = math.ceil(
                                remaining_points_list[x] / allocation[x]
                            )
                            print("add_points", math.ceil(add_points))
                            end_index = start_index + add_points + 1
                            print("end_index", math.ceil(end_index))
                            for m in range(allocation[x]):
                                print(
                                    "removed_grid_path_array_index",
                                    removed_grid_path_array_index,
                                )
                                if m != 0:
                                    end_index += add_points
                                if end_index > int(num_lines[i]):
                                    end_index = int(num_lines[i])
                                removed_grid_path_array[
                                    removed_grid_path_array_index
                                ] = (start_index, end_index)
                                removed_grid_path_array_start_val[
                                    removed_grid_path_array_index
                                ] = start_index
                                removed_grid_filename[removed_grid_path_array_index] = (
                                    removed_uav_grid[x]
                                )
                                print(
                                    "removed_grid_path_array",
                                    removed_grid_path_array,
                                    removed_grid_path_array_start_val,
                                    removed_grid_filename,
                                )
                                start_index = end_index
                                removed_grid_path_array_index += 1
                        print(
                            "removed_grid_path_array!!!!!",
                            removed_grid_path_array,
                            removed_grid_path_array_start_val,
                            removed_grid_filename,
                        )
                        removed_grid_path_array_flag = True

                    if (
                        all(
                            grid_path_array[x] >= int(num_lines[x])
                            for x in selected_indexes
                        )
                        and not removed_grid_path_length != []
                    ):
                        landing_flag = True
                    if removed_grid_path_array_flag:
                        if removed_grid_path_array_start_val[i] == 0:
                            checkall_removed_grid_path_array_start_val[i] = 1
                            print(
                                "checkall_removed_grid_path_array_start_val",
                                checkall_removed_grid_path_array_start_val,
                            )
                            continue
                        if (
                            removed_grid_path_array_start_val[i]
                            == removed_grid_path_array[i][1]
                        ):
                            checkall_removed_grid_path_array_start_val[i] = 1
                            if uncovered_area_points != []:
                                print("uncovered_area_points", uncovered_area_points)
                                for u, uncovered_area_point in enumerate(
                                    uncovered_area_points
                                ):
                                    removed_grid_path_array[i] = (
                                        uncovered_area_point,
                                        int(num_lines[i]) + 1,
                                    )
                                    print(
                                        "removed_grid_path_array",
                                        removed_grid_path_array,
                                    )
                                    removed_grid_path_array_start_val[i] = (
                                        uncovered_area_points[u]
                                    )
                                    removed_grid_filename[i] = uncovered_area_filename[
                                        u
                                    ]
                                    removed_grid_path_array[i] = (
                                        uncovered_area_points[u],
                                        int(num_lines[i]),
                                    )
                                    print(
                                        "removed_grid_path_array_start_val",
                                        removed_grid_path_array_start_val,
                                        removed_grid_filename,
                                    )
                                    checkall_removed_grid_path_array_start_val[i] = 0
                                    uncovered_area_points.pop(u)
                                    uncovered_area_filename.pop(u)
                            else:
                                continue
                    if (
                        grid_path_array[i] >= int(num_lines[i])
                        and not removed_grid_path_array_flag
                    ):
                        continue
                    if removed_grid_path_array_flag:
                        goal_lat_lon = read_specific_line(
                            removed_grid_filename[i],
                            removed_grid_path_array_start_val[i],
                        )
                    else:
                        goal_lat_lon = read_specific_line(
                            all_uav_csv_grid_array[i], grid_path_array[i]
                        )
                    x, y, isCurve = (
                        goal_lat_lon[0][0],
                        goal_lat_lon[0][1],
                        goal_lat_lon[0][2],
                    )
                    goal = (x, y)
                    current_goals[i] = goal
                    current_position = [b.x, b.y]
                    dx = abs(goal[0] - current_position[0])
                    dy = abs(goal[1] - current_position[1])
                    is_curve = str(isCurve).strip().lower() == "true"
                    next_goal = None
                    is_final = False
                    try:
                        if removed_grid_path_array_flag:
                            next_index = removed_grid_path_array_start_val[i] + 1
                            is_final = next_index >= removed_grid_path_array[i][1]
                            if not is_final:
                                next_row = read_specific_line(
                                    removed_grid_filename[i], next_index
                                )
                                next_goal = (next_row[0][0], next_row[0][1])
                        else:
                            next_index = grid_path_array[i] + 1
                            is_final = next_index >= int(num_lines[i])
                            if not is_final:
                                next_row = read_specific_line(
                                    all_uav_csv_grid_array[i], next_index
                                )
                                next_goal = (next_row[0][0], next_row[0][1])
                    except Exception as e:
                        print("[split] next point read failed", i, e)
                    reached_split_waypoint, split_goal_distance = uav_reached_waypoint(
                        i,
                        b,
                        goal,
                        sim_radius=5,
                        next_goal=next_goal,
                        is_curve=is_curve,
                        is_final=is_final,
                    )
                    if reached_split_waypoint:
                        if split_goal_distance is not None:
                            print(
                                f"[uav-flyby] bot {i}: switching split point at "
                                f"{split_goal_distance:.1f} m"
                            )
                        if (
                            grid_path_array[i] >= int(num_lines[i])
                            and not removed_grid_path_array_flag
                        ):
                            continue
                        if (
                            grid_path_array[i] >= int(num_lines[i])
                            and removed_grid_path_array_flag
                        ):
                            removed_grid_path_array_start_val[i] += 1
                            print(
                                "removed_grid_path_array_start_val",
                                removed_grid_path_array_start_val,
                            )
                        else:
                            grid_path_array[i] += 1
                            print("grid_path_array", grid_path_array)
                    _dis, step_size = advance_bot_with_uav_pacing(
                        i, b, goal, label="split"
                    )
                    guidance_position = None
                    if is_curve:
                        curve_index = (
                            removed_grid_path_array_start_val[i]
                            if removed_grid_path_array_flag
                            else grid_path_array[i]
                        )
                        curve_csv = (
                            removed_grid_filename[i]
                            if removed_grid_path_array_flag
                            else all_uav_csv_grid_array[i]
                        )
                        curve_num_lines = (
                            removed_grid_path_array[i][1]
                            if removed_grid_path_array_flag
                            else int(num_lines[i])
                        )
                        curve_guidance = curve_lookahead_goal(
                            curve_csv, curve_index, curve_num_lines, goal, (b.x, b.y)
                        )
                        guidance_position = curve_guidance_position(b, curve_guidance)
                        lookahead_goal = curve_guidance[1] if curve_guidance else goal
                        print(
                            f"[CURVE] idx={curve_index} "
                            f"bot=({b.x:.2f},{b.y:.2f}) "
                            f"goal=({goal[0]:.2f},{goal[1]:.2f}) "
                            f"lookahead=({lookahead_goal[0]:.2f},{lookahead_goal[1]:.2f}) "
                            f"step={step_size:.2f}"
                        )
                    position_for_uav = (
                        guidance_position
                        if guidance_position is not None
                        else (b.x, b.y)
                    )
                    value = [position_for_uav[0] * 2, position_for_uav[1] * 2]
                    if master_flag:
                        if pop_flag_arr[i] == 1:
                            lat, lon = locatePosition.cartToGeo(
                                origin, endDistance, value
                            )
                            if same_alt_flag:
                                point1 = LocationGlobalRelative(lat, lon, same_height)
                            else:
                                point1 = LocationGlobalRelative(
                                    lat, lon, different_height[i]
                                )
                            vehicles[i].simple_goto(point1)

                s.time_elapsed += 1
                if master_flag and "gui" in locals() and gui is not None:
                    gui.show_goals(current_goals)
                    gui.show_planned_path(planned_paths_by_bot)
                    gui.show_gps_positions(live_gps_plot_points())
                    gui.update()
                    print_sim_vs_real_latlon(selected_indexes, label="split")

                if index == b"stop":
                    split_flag = False
                    if master_flag and "gui" in locals() and gui is not None:
                        gui.close()
                    break

        if (data.startswith(b"home")) or (home_flag):
            decoded_index = data.decode(
                "utf-8"
            )  # Assuming utf-8 encoding, adjust if needed
            f = decoded_index[0:4]  # First coordinate pair
            return_array = decoded_index[5:]  # All other coordinates
            return_latlon = json.loads(return_array)
            return_xy = []
            for x in return_latlon:
                x, y = locatePosition.geoToCart(origin, endDistance, [x[0], x[1]])
                return_xy.append((x / 2, y / 2))
            print(return_xy, "return_xy")
            return_ind = 0
            if master_flag:
                uav_home_pos = []
                for vehicle in vehicles:
                    lat = vehicle.location.global_relative_frame.lat
                    lon = vehicle.location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                    uav_home_pos.append((x / 2, y / 2))
                """
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.2)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.2)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.2)
					#uav4.sendto(serialized_data.encode(), uav4_server_address)
					#time.sleep(0.2)
					#uav5.sendto(serialized_data.encode(), #uav5_server_address)
				"""
                s = sim.Simulation(
                    uav_home_pos, num_bots=len(pos_array), env_name=file_name
                )
                home_flag = True
            bot_array_home = [0] * num_bots
            all_bot_reach_flag_home = False
            index = "data"
            while 1:
                time.sleep(sleep_times.get(num_bots))
                if home_flag1:
                    home_flag = False
                    """
					for i,x in enumerate(s.swarm):
						print(i)
						vehicles[i].mode = VehicleMode("RTL")
						print('vehicle',vehicles[i],i,'rtl')
					"""
                    break
                if vehicle_lost_flag:
                    vehicle_lost_flag = True
                    x = remove_vehicle()
                    print(x)
                for i, b in enumerate(s.swarm):
                    current_position = [b.x, b.y]
                    goal = return_xy[return_ind]
                    cmd = cvg.goal_area_cvg(i, b, goal)
                    cmd.exec(b)
                    dx = abs(goal[0] - current_position[0])
                    dy = abs(goal[1] - current_position[1])
                    if dx <= 5 and dy <= 5:
                        bot_array_home[i] = 1
                        if any(element == 1 for element in bot_array_home):
                            if return_ind == len(return_xy) - 1:
                                all_bot_reach_flag_home = True
                                print(
                                    "all_bot_reach_flag_home", all_bot_reach_flag_home
                                )
                                break
                            else:
                                return_ind += 1
                                print("return_ind", return_ind)
                    if all_bot_reach_flag_home == True:
                        """
                        with open(csv_path, 'a') as csvfile:
                                fieldnames = ['waypoint']
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow({'waypoint':-1})
                        """
                        home_flag1 = True
                        home_flag = False
                        break

                    if master_flag:
                        current_position = [b.x * 2, b.y * 2]
                        lat, lon = locatePosition.cartToGeo(
                            origin, endDistance, current_position
                        )
                        point1 = LocationGlobalRelative(lat, lon, home_height[i])
                        vehicles[i].simple_goto(point1)

                if index == b"stop":
                    home_flag1 = True
                    home_flag = False

        if home_flag1:
            if master_flag:
                uav_home_pos = []
                for vehicle in vehicles:
                    lat = vehicle.location.global_relative_frame.lat
                    lon = vehicle.location.global_relative_frame.lon
                    x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
                    uav_home_pos.append((x / 2, y / 2))
                """
		        serialized_data = json.dumps(home_pos)
		        serialized_data="uav_home_pos" + serialized_data
		        
		        for i in range(len(pos_array)):
		            uav1.sendto(serialized_data.encode(),uav1_server_address)
		            time.sleep(0.2)
		            uav2.sendto(serialized_data.encode(),uav2_server_address)
		            time.sleep(0.2)
		            uav3.sendto(serialized_data.encode(),uav3_server_address)
		            time.sleep(0.2)
				"""
                s = sim.Simulation(
                    uav_home_pos, num_bots=len(pos_array), env_name=file_name
                )
                home_flag1 = True
            bot_array_home = [0] * num_bots
            all_bot_reach_flag_home = False
            index = "data"
            while 1:
                time.sleep(sleep_times.get(num_bots))
                if all_bot_reach_flag_home == True:
                    home_flag1 = False
                    home_flag = False
                    print("END")
                    break
                if vehicle_lost_flag:
                    vehicle_lost_flag = True
                    x = remove_vehicle()
                    print(x)
                print("ggg", home_pos)
                for i, b in enumerate(s.swarm):
                    current_position = [b.x, b.y]
                    goal = home_pos[i]
                    cmd = cvg.goal_area_cvg(i, b, goal)
                    cmd.exec(b)
                    dx = abs(goal[0] - current_position[0])
                    dy = abs(goal[1] - current_position[1])
                    if dx <= 0.1 and dy <= 0.1:
                        bot_array_home[i] = 1
                        if all(element == 1 for element in bot_array_home):
                            all_bot_reach_flag_home = True
                            print("all_bot_reach_flag_home", all_bot_reach_flag_home)
                            break

                    if all_bot_reach_flag_home == True:
                        break

                    if master_flag:
                        current_position = [b.x * 2, b.y * 2]
                        lat, lon = locatePosition.cartToGeo(
                            origin, endDistance, current_position
                        )
                        point1 = LocationGlobalRelative(lat, lon, home_height[i])
                        vehicles[i].simple_goto(point1)

                if index == b"stop":
                    home_flag1 = False
                    home_flag = False

    except MissionPreempted as preempt:
        # A mission loop noticed a newer command mid-flight (via
        # check_for_new_command) and unwound here instead of running to
        # completion. Dispatch the preempting command immediately on the
        # next iteration -- no idle wait for a fresh mailbox seq.
        _next_data, _next_address = preempt.data, preempt.address
        _last_seq = _pending_command.seq
    except Exception as e:
        # Previously a bare `pass` here -- any exception inside a mission
        # loop (search/split/goal/home/...) silently killed the mission for
        # every bot at once with zero trace, which is why a mid-mission
        # failure (e.g. an index mismatch after a bot removal) looked like
        # the swarm just stopped for no reason. Log it so the real cause is
        # visible instead of only the flags being reset.
        print("[mission] aborted by exception:", repr(e))
        traceback.print_exc()
        if search_flag:
            search_flag = False
        if split_flag:
            split_flag = False
        if start_flag:
            start_flag = False
        if circle_formation_flag:
            circle_formation_flag = False
        if home_flag:
            home_flag = False
        if home_goto_flag:
            home_goto_flag = False
        pass
