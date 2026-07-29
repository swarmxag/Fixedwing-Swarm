import sys,os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..')))
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
import socket,json,csv,threading,yaml,shutil
from shapely.geometry import Polygon
import locatePosition
import netifaces,wmi
'''
file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
file_server_address = ('', 12003)  #receive from .....rx.py
file_sock.bind(file_server_address)

graph_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
graph_server_address = ('{}', 12009)  #receive from .....rx.py
'''

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ('', 12008)  #receive from .....rx.py
sock2.bind(server_address2)

sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ('', 12002)  #receive from .....rx.py
sock3.bind(server_address3)
'''
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
'''
goal_table=[]
file_name=""
master_num=0
master_flag=False
cwd = os.getcwd()

same_height=100
different_height=[300,310,300,310,300,310,300,310,300,310]
home_height=[50,60,70,80,90,100,110,120,130,140]

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
'''			
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
'''
master_num==3
master_flag=True
file_name=None  # no site preset -- operator draws a fence when enabling swarm

disperse_multiple_goals=[]
start_multiple_goals=[]
return_multiple_goals=[]
goal_points=[]
agg_goal_point=[]
removed_uav_homepos_array=[]

nextwaypoint=0

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

rectangles_path = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env", "rectangles.yaml")
try:
	origin = read_origin(rectangles_path)
	print("Origin loaded from rectangles.yaml:", origin)
except Exception as e:
	origin = None
	print(f"No rectangles.yaml yet at {rectangles_path} ({e}) -- origin will be set once a fence is drawn")

'''
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('{}', 12005)  #receive from .....rx.py

# Bind the socket to the port
remove_bot_server_address = ('{}', 12001)  #receive from .....rx.py

sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address4 = ('', 12011)  #receive from .....rx.py
sock.bind(server_address4)
'''
num_bots=10
vehicles=[]
port_array = [14551, 14552, 14553, 14554, 14555, 14556, 14557, 14558, 14559, 14560]
'''
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
'''
port_dict = {
    1:14551,
    2:14552,
    3:14553,
    4:14554,
    5:14555,
    6:14556,
    7:14557,
    8:14558,
    9:14559,
    10:14560
}

# Print the dictionary to verify
print(port_dict)

pos_array=[]
heartbeat_ip=["192.168.0.151","192.168.0.152","192.168.0.153","192.168.0.154","192.168.0.155","192.168.0.156","192.168.0.157","192.168.0.158","192.168.0.159","192.168.0.160"]
heartbeat_ip_timeout=[30]*10
goal_path_csv_array=[]
goal_path_csv_array_flag=False
skip_wp_flag=False
next_wp=0

def get_wifi_ip(iface_map):
    interfaces = netifaces.interfaces()
    # print(interfaces)
    for iface in netifaces.interfaces():
        try:
            #print(iface,iface_map[iface])
            # if iface in iface_map:
            adapter = iface_map[iface]
            # print(adapter)
            addrs = netifaces.ifaddresses(iface)
            #print(addrs)
            ipv4_info = addrs.get(netifaces.AF_INET, [])
            for addr in ipv4_info:
                ip = addr.get('addr')
                if ip and (adapter == "Ethernet" or adapter=="Wi-Fi" or iface == "eth0" or iface == "ensp20" or iface == "wlan0") and ip.startswith("192.168."):
                    return "192.168.2.135"
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
    #return get_wifi_ip(mappings)
    return "192.168.2.135"


def vehicle_collision_moniter_receive():	
        global index
        global vehicles
        global slave_heal_ip,master_flag,master_num,pos_array,home_pos,uav_home_pos,skip_wp_flag,next_wp
        while 1:
        	index, address = sock3.recvfrom(1024)
        	print ("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", index)    
        	decoded_index=index.decode('utf-8')
        	print("decoded_index",decoded_index)           
        	if decoded_index.startswith("master"):
        		m,master_num=decoded_index.split("-")
        		print("m,master_num",m,master_num)
        		msg='Drone 3 master_num '+str(master_num)+' data received'
        		if(int(master_num)==3):
        			if(master_flag):
        				pass
        			else:
        				master_flag=True       
        				CHECK_network_connection() 			
        				vehicle_connection()        				
        				fetch_location()
        				s=sim.Simulation(uav_home_pos,num_bots=len(vehicles),env_name=file_name)
        		else:
        			master_flag=False
        			
        		index="data"
        		data="data"
        		msg="master_num "+str(master_num)
        		print("master_flag",master_flag)
        	
        	if decoded_index.startswith("pos_array"):        		
        		message = decoded_index[:9]  # Assuming "home_pos" is 8 characters long
        		array_data = decoded_index[9:]	
        		print("pos_array",pos_array)
        		pos_array = json.loads(array_data)
        		print("pos_array",pos_array)        		
        		index="data"
        		msg="UAV 1 connected with "+str(len(pos_array))+" vehicles"
        		print("master_flag",master_flag)
        	if decoded_index.startswith("home_pos"):        		
        		message = decoded_index[:8]  # Assuming "home_pos" is 8 characters long
        		home_pos = decoded_index[8:]	
        		print("home_pos",home_pos)
        		home_pos = json.loads(home_pos)
        		print("home_pos",home_pos)
        		
        	if decoded_index.startswith("uav_home_pos"):
        		if(master_flag):
        			pass
        		else:        			
        			message = decoded_index[:12]  # Assuming "home_pos" is 8 characters long
        			uav_home_pos = decoded_index[12:]	
        			print("uav_home_pos",uav_home_pos)
        			uav_home_pos = json.loads(uav_home_pos)
        			print("uav_home_pos",uav_home_pos)
        	if decoded_index.startswith("skip_wp"):
        		print("decoded_index",decoded_index)
        		c,next_wp=decoded_index.split(",")
        		print("c,next_wp",c,next_wp)      
        		next_wp=int(next_wp)  	
        		print("next_wp",next_wp)								
        		skip_wp_flag=True
        		print("skip_wp_flag",skip_wp_flag)        		        
        			
collision_thread = threading.Thread(target=vehicle_collision_moniter_receive)
collision_thread.daemon=True
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


def handle_concurrent_goal_command(command_data):
	if not command_data.startswith(b"goal"):
		return False
	try:
		decoded_index = command_data.decode('utf-8')
		msg_parts = decoded_index.split('_')
		if len(msg_parts) < 5:
			return False
		goal_latlon = json.loads(msg_parts[1])
		selected_uav_ids = parse_selected_uav_ids(msg_parts[4])
		if not selected_uav_ids:
			return False
		selected_indexes = selected_swarm_indexes(selected_uav_ids)
		goal_xy = []
		for goal_point in goal_latlon:
			x, y = locatePosition.geoToCart(origin, endDistance, [float(goal_point[0]), float(goal_point[1])])
			goal_xy.append((x / 2, y / 2))
		assign_goal_tasks(selected_indexes, goal_xy)
		print("[concurrent goal] accepted during running mission", selected_uav_ids, selected_indexes)
		return True
	except Exception as e:
		print("[concurrent goal] failed", e)
		return False


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
		entry["connection"] = connection_string_for_sysid(int(sys_id)) if int(sys_id) in port_dict else entry.get("connection")
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
		print('[uav-order] skipped: pos_array/vehicles length mismatch', pos_array, len(vehicles))
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
	print('[uav-order] active order normalized', pos_array)
	return True


def add_uav_to_swarm(sys_id):
	global vehicles, pos_array, s, num_bots, uav_home_pos
	try:
		sys_id = int(sys_id)
		connection_str = connection_string_for_sysid(sys_id)
		print("[add-link] connection", sys_id, connection_str)
		if sys_id in pos_array:
			idx = pos_array.index(sys_id)
			try:
				vehicles[idx].close()
			except Exception:
				pass
			vehicles[idx] = connect(connection_str, baud=115200, heartbeat_timeout=30)
			uav_registry.setdefault(sys_id, {})["vehicle"] = vehicles[idx]
			uav_registry[sys_id]["active"] = True
			uav_registry[sys_id]["index"] = idx
			uav_task_state[sys_id] = "IDLE"
			print("[add-link] reconnected active UAV", sys_id, "index", idx)
			return True
		vehicle = connect(connection_str, baud=115200, heartbeat_timeout=30)
		lat = vehicle.location.global_relative_frame.lat
		lon = vehicle.location.global_relative_frame.lon
		x, y = locatePosition.geoToCart(origin, endDistance, [lat, lon])
		insert_index = len(pos_array)
		pos_array.append(sys_id)
		vehicles.append(vehicle)
		s.add_bot(insert_index, (x / 2, y / 2))
		if different_height:
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
		print("[add-link] added UAV as IDLE", sys_id, "index", insert_index, "pos_array", pos_array)
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
	return min(total_drones, (int(remaining_points) + points_per_drone - 1) // points_per_drone)


def allocate_drones(total_points, covered_points, total_drones):
	if isinstance(total_points, int):
		total_points = [total_points] * len(covered_points)
	remaining_points_list = [max(0, int(tp) - int(cp)) for tp, cp in zip(total_points, covered_points)]
	points_per_drone = [max(1, int(tp / 2)) for tp in total_points]
	uncovered_areas = [(i, points) for i, points in enumerate(remaining_points_list) if points > 0]
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
			needed = calculate_drones_needed(remaining_points_list[i], points_per_drone[i], total_drones)
			allocation[i] = needed
			total_drones -= needed
	print("[redistribution] allocation", allocation, "remaining", remaining_points_list)
	return allocation, remaining_points_list


def remove_uav_from_swarm(remove_bot_num):
	global pos_array, vehicles, s, different_height, pop_flag_arr, num_bots
	global remove_bot_flag, remove_bot_index, remove_bot_array, pop_bot_index
	global uav_home_pos, remove_flag, uav_removed, origin, endDistance, uav_registry, uav_task_state
	try:
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
		entry["active"] = False
		entry["index"] = None
		entry["connection"] = connection_string_for_sysid(remove_bot_num) if remove_bot_num in port_dict else entry.get("connection")
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
    Selected goal commands (and add/remove) are handled concurrently
    without preempting the running mission; any other newer command
    still preempts it via MissionPreempted."""
    global _handled_concurrent_command_seq, _last_seq
    if _pending_command.seq > started_seq:
        if _pending_command.seq > _handled_concurrent_command_seq and (handle_concurrent_goal_command(_pending_command.data) or handle_concurrent_remove_command(_pending_command.data) or handle_concurrent_add_command(_pending_command.data)):
            _handled_concurrent_command_seq = _pending_command.seq
            _last_seq = _pending_command.seq
            return None
        if _pending_command.seq <= _handled_concurrent_command_seq:
            return None
        raise MissionPreempted(_pending_command.data, _pending_command.address)

def CHECK_network_connection():
    global heartbeat_ip_timeout,heartbeat_ip
    for i,iter_follower in enumerate(heartbeat_ip_timeout):
	    response = os.system('ping -c 1 ' + heartbeat_ip[i])
	    if response==0:
	    	heartbeat_ip_timeout[i]=30
	    	pass
	    else: # Link is down.
	    	print ("link is down")
	    	linkdown_flag=True
	    	#master_ip="192.168.0.153"
	    	#slave_heal_ip[i] = 'nolink'    	    	
	    	heartbeat_ip_timeout[i]=1
    print(" heartbeat_ip_timeout",heartbeat_ip_timeout)


ip = get_interface_mapping()
print("ip",ip)

def vehicle_connection():	
	global vehicles,pos_array,num_bots,heartbeat_ip_timeout
	pos_array=[]
	vehicles=[]
	num_bots=0
	
	try:
		vehicle1= connect('udpin:{}:14554'.format(ip),baud=115200, heartbeat_timeout=heartbeat_ip_timeout[0])
		print('Drone1')
		vehicles.append(vehicle1)
		pos_array.append(vehicle1._master.target_system)
		num_bots+=1
		msg="Drone1 Connected"
	except:	
		pass
		print(	"Vehicle 1 is lost")
	try:		
		vehicle2= connect('udpin:{}:14555'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[1])
		print('Drone2')
		num_bots+=1	
		vehicles.append(vehicle2)
		pos_array.append(vehicle2._master.target_system)
		msg="Drone2 Connected"
	except:	
		pass	
		print(	"Vehicle 2 is lost")
	
	try:
		vehicle3= connect('udpin:{}:14556'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[2])
		print('Drone3')
		num_bots+=1 
		vehicles.append(vehicle3)
		pos_array.append(vehicle3._master.target_system)
		msg="Drone3 Connected"
	except:		
		pass
		print(	"Vehicle 3 is lost")
	
	# try:		
	# 	vehicle4= connect('udpin:{}:14554'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[3])
	# 	print('Drone4')
	# 	num_bots+=1
	# 	vehicles.append(vehicle4)
	# 	pos_array.append(vehicle4._master.target_system)
	# 	msg="Drone4 Connected"
	# except:		
	# 	pass
	# 	print(	"Vehicle 4 is lost")
	# try:		
	# 	vehicle5= connect('udpin:{}:14555'.format(ip),baud=115200,heartbeat_timeout=heartbeat_ip_timeout[4])
	# 	print('Drone5')
	# 	num_bots+=1
	# 	vehicles.append(vehicle5)
	# 	pos_array.append(vehicle5._master.target_system)
	# 	msg="Drone5 Connected"
	# except:	
	# 	pass
	# 	print(	"Vehicle 5 is lost")
	
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
	'''
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
	'''
	
count=0
endDistance=500000
home_pos=[]
home_pos_lat_lon=[]
uav_home_pos=[]
current_lat_lon=[]
home_flag=False
home_flag1=False
search_flag=False
home_goto_flag=False
lost_vehicle_num=0
vehicle_lost_flag=False

landing_flag=False
# Iterate over the list of vehicles
robots = [(0, 0)] * 10

slave_heal_ip=["192.168.0.153"]*num_bots
heartbeat=[0]*num_bots

vehicle_uav_heartbeat_flag=False

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address1 = ('192.168.0.210', 12010)
slave_heal_ip=["192.168.0.153"]*num_bots
           
all_uav_csv_grid_array=[0]*num_bots
robot_positions = [([0, 0]) for _ in range(20)]
print("origin#########",origin)

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
    1: 0.13
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
			return [int(part.strip().strip("\"").strip("'")) for part in cleaned.split(",") if part.strip()]
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
		print("[selected UAV] IDs not connected/in pos_array:", sorted(missing), "pos_array:", pos_array)
	return indexes

def fetch_location():
	global vehicles,home_pos_lat_lon,home_pos,uav_home_pos
	global robots
	uav_home_pos=[]
	current_lat_lon=[]
		
	if master_flag:	
		for i,vehicle in enumerate(vehicles):
		    lat = vehicle.location.global_relative_frame.lat
		    lon = vehicle.location.global_relative_frame.lon
		    #print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
		    current_lat_lon.append((lat,lon))			    
		    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
		    #print("x,y",x/2,y/2)
		    uav_home_pos.append((x / 2, y / 2))  
		    if i < len(robots):
		        robots[i] = (x / 2, y / 2)
		    msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
	'''	    
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
	'''
if master_flag:
	vehicle_connection()
	register_active_uavs()
	while True:
	    all_armed = [False]*len(vehicles)  # Assume all vehicles are armed initially
	    for i,vehicle in enumerate(vehicles):
	        altitude = vehicle.location.global_relative_frame.alt
	        if vehicle.armed and altitude is not None and altitude > 10:
	        #if vehicle.armed and vehicle.location.global_relative_frame.alt>10  :
	            all_armed[i] = True  # Set the flag to False  
	    if all(all_armed):
	        fetch_location()
	        break
	    time.sleep(0.1)
	    
	
def generate_points(lat, lon, num_points, radius,circle_direction):
    # List to store generated points
    points = []

    # Generate points in circular formation
    for i in range(num_points):
        # Calculate bearing angle
        
        bearing_sign = 1 if circle_direction == 1 else -1
        bearing = bearing_sign*(360 / num_points * i)

        # Calculate new latitude and longitude
        lat2 = asin(sin(radians(lat)) * cos(radius / 6371000) +
                    cos(radians(lat)) * sin(radius / 6371000) * cos(radians(bearing)))
        lon2 = radians(lon) + atan2(sin(radians(bearing)) * sin(radius / 6371000) * cos(radians(lat)),
                                    cos(radius / 6371000) - sin(radians(lat)) * sin(lat2))

        # Append the new point to the list
        points.append((degrees(lat2), degrees(lon2)))

    return points
    
def read_specific_line(csv_file_path, line_number):
    goal=[]    
    with open(csv_file_path, 'rt') as file:
        reader = csv.reader(file)
        for i in range(line_number):
            next(reader)
        # Read the desired line
        line = next(reader)
        goal.append((float(line[0]),float(line[1])))
        return goal


def arm_and_takeoff(vehicle, aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    print("Basic pre-arm checcks")
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    time.sleep(3)
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.90:
            print("Reached target altitude")
            break
        time.sleep(1)

data=""
same_alt_flag=False
index=0
flag_stop=False
return_flag=False
pop_flag_arr=[1]*num_bots
pop_flag=False
specific_bot_goal_flag=False
pop_bot_index=None
goal_bot_num=None
start_flag=False
start_return_csv_flag=False
circle_formation_flag=False
radius_of_earth = 6378100.0 # in meters
uav_home_flag=False
remove_flag=False
group_goal_flag=False
circle_formation_count=0
uav_removed=True
grid_path_array=[1]*num_bots
remove_bot_flag=False
remove_bot_index=0
search_step=1
percentage=0			
removed_uav_grid=[]
removed_grid_path_length=[]
removed_grid_path_array=[0]*len(pos_array)
removed_grid_path_array_start_val=[0]*len(pos_array)
checkall_removed_grid_path_array_start_val=[0]*len(pos_array)
removed_grid_filename=[0]*num_bots
removed_grid_path_array_flag=False
removed_uav_grid=[]
removed_grid_path_length=[]
remove_bot_flag=False
remove_bot_index=[]
remove_bot_array=[]
grid_completed_bot=[-1]*num_bots
uncovered_area_filename=[]
uncovered_area_points=[]
grid_completed_bot=[-1]*num_bots
circle_formation_table=[0]*num_bots
circle_formation_goals=[]
guided_circle_formation_table=[0]*num_bots
guided_circle_formation_goals=[]
guided_circle_flag=False
guided_circle_formation_flag=False
group_split_goal_pos=[0]*num_bots
group_split_flag_array=[False]*num_bots
group_split_flag=False
search_flag_val=0
split_flag_val=0
split_flag=False

#Initialize Simulation and GUI 

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
active_goal_tasks_lock = threading.Lock()


def assign_goal_tasks(selected_indexes, goal_xy):
	with active_goal_tasks_lock:
		for bot_index in selected_indexes:
			active_goal_tasks[bot_index] = {
				"goals": list(goal_xy),
				"goal_index": 0,
			}
	print("[goal-task] assigned", selected_indexes, goal_xy)


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
	print("[goal-task] compacted after remove", removed_index, sorted(active_goal_tasks.keys()))


def _goal_task_runner():
	"""Background thread, independent of the main command-dispatch loop.
	Continuously drives whichever bot indexes have an active_goal_tasks
	entry, so a goal assigned to one UAV keeps progressing regardless of
	whatever search/split/navigate mission the rest of the swarm is
	running in the main loop."""
	while True:
		time.sleep(sleep_times.get(len(pos_array), 0.1))
		try:
			with active_goal_tasks_lock:
				tasks_snapshot = list(active_goal_tasks.items())
			if not tasks_snapshot:
				continue
			completed = []
			for i, task in tasks_snapshot:
				if i >= len(s.swarm) or i >= len(pos_array):
					completed.append(i)
					continue
				goals = task.get("goals", [])
				goal_index = task.get("goal_index", 0)
				if goal_index >= len(goals):
					completed.append(i)
					continue
				b = s.swarm[i]
				goal_position = goals[goal_index]
				dx = abs(goal_position[0] - b.x)
				dy = abs(goal_position[1] - b.y)
				if dx <= 5 and dy <= 5:
					goal_index += 1
					if goal_index >= len(goals):
						completed.append(i)
						print("[goal-task] completed UAV", pos_array[i])
						continue
					with active_goal_tasks_lock:
						if i in active_goal_tasks:
							active_goal_tasks[i]["goal_index"] = goal_index
					goal_position = goals[goal_index]
				b.set_goal(goal_position[0], goal_position[1])
				cmd = cvg.goal_area_cvg(i, b, goal_position)
				cmd.exec(b)
				if master_flag and i < len(vehicles):
					current_position = (b.x * 2, b.y * 2)
					lat, lon = locatePosition.cartToGeo(origin, endDistance, current_position)
					if same_alt_flag:
						point1 = LocationGlobalRelative(lat, lon, same_height)
					else:
						point1 = LocationGlobalRelative(lat, lon, different_height[i])
					vehicles[i].simple_goto(point1)
			if completed:
				with active_goal_tasks_lock:
					for i in completed:
						active_goal_tasks.pop(i, None)
		except Exception as e:
			print("[goal-task] runner exception", e)

while True:
	if(uav_home_pos!=[]):
		print("num_bots",num_bots,uav_home_pos)
		s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name)
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
	global origin,endDistance
	global vehicles
	index=pos_array[lost_vehicle_num-1]
	print(index,"index")
	print("lost_vehicle_num",lost_vehicle_num,index,pos_array)
	vehicle_lost_flag=False
	pop_flag=True
	#print ("msg", index)
	for l in range(0,len(pos_array)):
		if(int(index)==pos_array[l]):
			pop_bot_index=l
			print("pop_bot_index,l",pop_bot_index,l)
			break
	pos_array.pop(pop_bot_index)
	vehicles.pop(pop_bot_index)
	s.remove_bot(pop_bot_index)
	print(num_bots)
	print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!",pop_flag_arr)
	print("pop index",pop_bot_index)
	same_alt_flag=False
	uav_home_pos=[]
	for i,vehicle in enumerate(vehicles):
	    lat = vehicle.location.global_relative_frame.lat
	    lon = vehicle.location.global_relative_frame.lon	     
	    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
	    different_height[i]=different_height[i]+2
	    uav_home_pos.append((x / 2, y / 2))						
	print("uav_home_pos",uav_home_pos)    
	remove_flag=False
	uav_removed=True
	while True:
		for i, b in enumerate(s.swarm):
			cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
			cmd.exec(b)
			if master_flag:
				value=[b.x*2,b.y*2]			
				lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
				
				if same_alt_flag:
					point1 = LocationGlobalRelative(lat,lon,same_height)
				else:
					point1 = LocationGlobalRelative(lat,lon,different_height[i])
				vehicles[i].simple_goto(point1)
				alt=[0]*num_bots
				alt_count=[0]*num_bots
				for i,vehicle in enumerate(vehicles):
					print("vehicle",vehicle,num_bots)
					alt[i]=vehicle.location.global_relative_frame.alt 
					print("alt[vehicle]",alt[i])
					if different_height[i] - 1.5 <= alt[i] <= different_height[i]+1.5:
						alt_count[i]=1
						print(alt_count,"alt_count")
						if all(count==1 for count in alt_count):		
							print("Reached target altitude")
							return index

vehicles_thread=[]
# _next_data/_next_address carry a preempting command straight into the
# next iteration (see the MissionPreempted except-clause below) so it's
# dispatched immediately, with no idle wait for a fresh mailbox seq.
_next_data, _next_address = None, None
_last_seq = 0
while(1):
	if(master_flag):
		num_bots=len(vehicles)
	else:
		num_bots=len(pos_array)
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
		print ("!!msg", data)
		if(data==b"stop"):
			with active_goal_tasks_lock:
				active_goal_tasks.clear()
			print("[goal-task] cleared by stop")
			continue
		if(data.startswith(b"origin")):
			decoded_index = data.decode('utf-8')
			_, new_lat, new_lon = decoded_index.split(",")
			origin = (float(new_lat), float(new_lon))
			print("Origin updated dynamically:", origin)

		if(data==b"geofence"):
			try:
				rectangles_path = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env", "rectangles.yaml")
				with open(rectangles_path) as f:
					world_data = yaml.safe_load(f)
				new_size = (world_data["size"]["x"], world_data["size"]["y"])
				new_obstacles = [Polygon(o) for o in (world_data.get("obstacles") or [])]
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
				shutil.copyfile(rectangles_path, os.path.join(worlds_dir, "rectangles.yaml"))
				file_name = "rectangles"

				print(f"Obstacles hot-reloaded from {rectangles_path}: {len(new_obstacles)} walls, origin:", origin)
			except Exception as e:
				print(f"Error reloading obstacles: {e}")

		if(data==b"store_uav_pos"):
			if os.path.exists(csv_file_path):
    				os.remove(csv_file_path)
			
			with open(csv_file_path, mode='w', newline='') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerow(['X', 'Y'])  # Write header
				csv_writer.writerows(home_pos)
				csv_file.close()
		
		if(data==b"home_lock"):		
			for i,vehicle in enumerate(vehicles):		    
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
			    x,y = locatePosition.geoToCart (origin, endDistance, [home.lat,home.lon])
			    home_pos_lat_lon[i]=(home.lat,home.lon)
			    print("x,y",x/2,y/2)
			    home_pos[i]=(x / 2, y / 2)
			    if i < len(robots):
			        robots[i] = (x / 2, y / 2)
			    msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		 
       
		if data.startswith(b"origin"):
			decoded_index = data.decode('utf-8')
			_, lat, lon = decoded_index.split(",")
			origin = (float(lat), float(lon))
			file_name = "rectangles"          # switches env to the dynamically-written world file
			s = sim.Simulation(uav_home_pos, num_bots=len(pos_array), env_name=file_name)
			print("Origin + obstacles refreshed:", origin, file_name)      
			     				
		if(data.startswith(b"takeoff")):
			decoded_index=data.decode('utf-8')
			print("decoded_index",decoded_index)
			data,takeoff_height=decoded_index.split(",")
			print("data,takeoff_height",data,takeoff_height)
			for i, vehicle in enumerate(vehicles):
			    print(i)
			    thread = threading.Thread(target=arm_and_takeoff, args=(vehicle, int(takeoff_height)))				
			    vehicles_thread.append(thread)
			    thread.start()

			for thread in vehicles_thread:
			    thread.join()
			
			for i,vehicle in enumerate(vehicles):		    
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
			    x,y = locatePosition.geoToCart (origin, endDistance, [home.lat,home.lon])
			    home_pos_lat_lon[i]=(home.lat,home.lon)
			    print("x,y",x/2,y/2)
			    home_pos[i]=(x / 2, y / 2)
			    if i < len(robots):
			        robots[i] = (x / 2, y / 2)
			    msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
			    			     
					
		if(data.startswith(b"remove")) or (remove_flag):
			decoded_index = data.decode("utf-8")
			f, remove_bot_num = decoded_index.split(",", 1)
			print("remove_bot_num", remove_bot_num, pos_array)
			remove_uav_from_swarm(remove_bot_num)
			data="index"

		if(data.startswith(b"add")):
			decoded_index = data.decode("utf-8")
			f, sys_id = decoded_index.split(",", 1)
			add_uav_to_swarm(sys_id)
			data="index"
		
		if data.startswith(b'specific_bot_goal'): 
				index="data"
				goal_pos=[0]*num_bots
				specific_bot_goal_flag_array=[False]*num_bots
				try:
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					f,uav, goal_lat,goal_lon = decoded_index.split(",")
					goal_x,goal_y = locatePosition.geoToCart (origin, endDistance, [float(goal_lat),float(goal_lon)])	
					goal_position=(goal_x/2,goal_y/2)									
					for l in range(0,num_bots):	
						if(int(uav)==pos_array[l]):
							uav=l
							print("uav,l",uav,l)
							break
					
					goal_bot_num=int(uav)
					print("goal_bot_num",goal_bot_num)
					goal_pos[goal_bot_num]=goal_position
					specific_bot_goal_flag_array[goal_bot_num]=True
					print("specific_bot_goal_flag_array",specific_bot_goal_flag_array)
					while 1:
						time.sleep(0.1)
						if(specific_bot_goal_flag):
							specific_bot_goal_flag=False
							break	
								
						for i,b in enumerate(s.swarm):
							current_position=[b.x,b.y]
							if(specific_bot_goal_flag_array[i]):
								dx=abs(goal_pos[i][0]-current_position[0])
								dy=abs(goal_pos[i][1]-current_position[1])
								if(dx<=5 and dy<=5):
									specific_bot_goal_flag_array[i]=False
									print("specific_bot_goal_flag_array",specific_bot_goal_flag_array)
								if all(flag==False for flag in specific_bot_goal_flag_array):
									specific_bot_goal_flag=True
									break					
								else:
									current_position = (b.x, b.y)
									if(specific_bot_goal_flag_array[i]):
									    b.set_goal(goal_pos[i][0], goal_pos[i][1])
									    cmd = cvg.goal_area_cvg(i, b, goal_pos[i])
									    cmd.exec(b)
								if master_flag:
									current_position = (b.x*2, b.y*2)
									lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									vehicles[i].simple_goto(point1)
												       
						if(index==b"stop"):
							specific_bot_goal_flag=False
							break	
				except Exception as e:
					print("exceptiiiooonnn",e)	
					pass
					
		if data.startswith(b'group_split'): 
				index="data"								
				try:
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					msg_parts = decoded_index.split(",")
					goal_lat = float(msg_parts[-2])
					goal_lon = float(msg_parts[-1]) 
					remaining_values = msg_parts[1:-2]
					goal_x,goal_y = locatePosition.geoToCart (origin, endDistance, [float(goal_lat),float(goal_lon)])	
					goal_position=(goal_x/2,goal_y/2)									
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
					print("group_split_flag_array",group_split_flag_array,group_split_goal_pos)
					if master_flag:
					    uav_home_pos=[]
					    index = "data"
					    for vehicle in vehicles:
					        lat = vehicle.location.global_relative_frame.lat
					        lon = vehicle.location.global_relative_frame.lon
					        x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
					        uav_home_pos.append((x / 2, y / 2))
					    '''
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
					    '''
					    s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )					
					while 1:
						time.sleep(0.1)
						if(group_split_flag):
							group_split_flag=False
							break									
						for i,b in enumerate(s.swarm):
							current_position=[b.x,b.y]
							if(group_split_flag_array[i]):
								dx=abs(group_split_goal_pos[i][0]-current_position[0])
								dy=abs(group_split_goal_pos[i][1]-current_position[1])
								if(dx<=5 and dy<=5):
									group_split_flag_array[i]=False
									print("group_split_flag_array",group_split_flag_array)
								if all(flag==False for flag in group_split_flag_array):
									group_split_flag=True
									break					
								else:
									current_position = (b.x, b.y)
									if(group_split_flag_array[i]):
									    b.set_goal(group_split_goal_pos[i][0], group_split_goal_pos[i][1])
									    cmd = cvg.goal_area_cvg(i, b, group_split_goal_pos[i])
									    cmd.exec(b)
								if master_flag:
									current_position = (b.x*2, b.y*2)
									lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									vehicles[i].simple_goto(point1)
												       
						if(index==b"stop"):
							group_split_flag=False
							break	
				except Exception as e:
					print("exceptiiiooonnn",e)	
					pass
					
		if data.startswith(b'goal'):				
				index="data"				
				try:		
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					msg_parts = decoded_index.split('_')
					print('msg_parts',msg_parts,len(msg_parts))
					f = msg_parts[0]  # First coordinate pair
					guided_circle_direction=msg_parts[2]
					guided_circle_radius=msg_parts[3]
					goal_array = msg_parts[1]  # All other coordinates
					goal_latlon = json.loads(goal_array)
					goal_xy=[]
					bot_reached=[0]*num_bots
					for x in goal_latlon:
					    print(origin,[x[0],x[1]])
					    x,y = locatePosition.geoToCart (origin, endDistance, [float(x[0]),float(x[1])])
					    goal_xy.append((x/2,y/2))
					    print(goal_xy,"goal_xy")
					print(goal_xy,goal_xy[0],"goal")
					selected_uav_ids = parse_selected_uav_ids(msg_parts[4] if len(msg_parts) > 4 else None)
					selected_indexes = selected_swarm_indexes(selected_uav_ids)
					selected_index_set = set(selected_indexes)
					print('[goal] selected_uav_ids', selected_uav_ids, 'selected_indexes', selected_indexes)
					assign_goal_tasks(selected_indexes, goal_xy)
					data=b"index"
					continue
					goal_xy_index=0
					if master_flag:
					    uav_home_pos=[]
					    index = "data"
					    for vehicle in vehicles:
					        lat = vehicle.location.global_relative_frame.lat
					        lon = vehicle.location.global_relative_frame.lon
					        x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
					        uav_home_pos.append((x / 2, y / 2))						
					    print("uav_home_pos",uav_home_pos)
					    '''
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
					    '''
					s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
					gui = viz.Gui(s)

					my_seq = _last_seq

					while 1:
						time.sleep(sleep_times.get(num_bots))
						check_for_new_command(my_seq)
						if(group_goal_flag):
							group_goal_flag=False
							guided_circle_flag=True
							if 'gui' in locals() and gui is not None:
								gui.close()
							break
						goal_position=goal_xy[goal_xy_index]
						for i,b in enumerate(s.swarm):
							current_position=[b.x,b.y]
							dx=abs(goal_position[0]-current_position[0])
							dy=abs(goal_position[1]-current_position[1])
							if(dx<=5 and dy<=5):
								bot_reached[i]=1
								print("Goal reached",goal_xy_index,goal_position,bot_reached)
								if any(element == 1 for element in bot_reached):
								     if goal_xy_index == len(goal_xy) - 1:
								        print('group_goal_flag',group_goal_flag)
								        group_goal_flag = True
								        break
								     else:
								        goal_xy_index+=1															   
							else:
								b.set_goal(goal_position[0], goal_position[1])
								cmd = cvg.goal_area_cvg(i, b, goal_position)
								cmd.exec(b) 	
							if master_flag:
								current_position = (b.x*2, b.y*2)	
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								vehicles[i].simple_goto(point1)
						
						if 'gui' in locals() and gui is not None:
							gui.show_goals([goal_position] * len(s.swarm))
							gui.update()

						if(index==b"stop"):
							print("Data",data)
							group_goal_flag=False
							if 'gui' in locals() and gui is not None:
								gui.close()
							break	
				except MissionPreempted:
					raise
				except Exception as e:
					import traceback
					traceback.print_exc()
					print("exception",e)	
					pass
		
		if(guided_circle_flag) or data==b"guided_circle":
			multiple_goals_latlon = generate_points(float(goal_latlon[-1][0]),float(goal_latlon[-1][1]), 8, int(guided_circle_radius),int(guided_circle_direction))
			print("multiple_goals_latlon",multiple_goals_latlon)	
			multiple_goals=[]
			guided_circle_formation_table=[0]*num_bots
			for m in multiple_goals_latlon:
				x,y = locatePosition.geoToCart (origin, endDistance, m)
				multiple_goals.append((x/2,y/2))
			print("multiple_goals",multiple_goals)
			for b in s.swarm:							
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				ind=[0]*num_bots
				my_seq = _last_seq
				while 1:					
					if(guided_circle_formation_flag):
						guided_circle_formation_flag=False
						guided_circle_flag=False
						break					
					time.sleep(sleep_times.get(num_bots))
					check_for_new_command(my_seq)
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]	
						cmd =cvg.goal_area_cvg(i,b,goal)
						cmd+= disp_field(b,neighbourhood_radius=100)
						cmd.exec(b)
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])	
						circle_formation_table[i]=1					
						if(dx<=5 and dy<=5):
							ind[i]+=1
							print("inddddddd",ind)
							if(ind[i]==len(multiple_goals)):
								ind[i]=0
						if master_flag:
							current_position = [b.x*2,b.y*2]
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
													
					if(index==b"stop"):	
						guided_circle_formation_flag=True		
						break
	    					
		if data.startswith(b'same'):
				print ("msg", data)
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				data1, height = decoded_index.split(",")
				print(data1, height)
				same_alt_flag=True
				same_height=int(height)
				while True:					
					for i, b in enumerate(s.swarm):
						cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
						cmd.exec(b)
						if master_flag:
							value=[b.x*2,b.y*2]						
							lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
					
							if same_height - 1.5 <= alt[i] <= same_height+1.5:
									alt_count[i]=1
									if all(count==1 for count in alt_count):		
										index="data"
										data="data"
										same_alt_flag=True
										break
					
					if(index==b"stop"):
						index="data"
						data="index"
						break
												
		if data.startswith(b'different'): 
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				data1, height,step = decoded_index.split(",")
				same_alt_flag=False
				for h in range(num_bots):
					different_height[h] = int(height) + int(step) * h
				print("different_height",different_height)
				alt_count=[0]*num_bots
				print("alt_count",alt_count)
				alt=[0]*num_bots
				diff_height_flag=False				
				alt_count1=0
				while True:	
					if(diff_height_flag):
						diff_height_flag=False
						break				
					for i, b in enumerate(s.swarm):
						cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
						cmd.exec(b)
						if master_flag:
							value=[b.x*2,b.y*2]						
							lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
							alt[i]=vehicles[i].location.global_relative_frame.alt 
							if different_height[i] - 1.5 <= alt[i] <= different_height[i]+1.5:
								alt_count[i]=1								
								if all(count==1 for count in alt_count):		
									print("Reached target altitude")
									index="data"
									data="data"
									diff_height_flag=True
									break
						else:
							data="data"
							diff_height_flag=True
							break
													
					if(index==b"stop"):
						index="data"
						data="index"
						break
						
		if(data.startswith(b"loiter_point")) or (circle_formation_flag) :
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			f,base_lat,base_lon,radius,circle_direction = decoded_index.split(",")
			print("f,loiter_radius ",f,base_lat,base_lon,radius,circle_direction )
			
			if master_flag:
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))						
				print("uav_home_pos",uav_home_pos)
				'''
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
				'''
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )

			index="data"
			
			#center_lat , center_lon = locatePosition.destination_location(float(base_lat),float(base_lon),700,90)
			#print("center_lat , center_lon",center_lat , center_lon)
			# Generate 10 points in a circular formation with a radius of 500 meters around the given point
			multiple_goals_latlon = generate_points(float(base_lat),float(base_lon), 8, int(radius),int(circle_direction))
			print("multiple_goals_latlon",multiple_goals_latlon)	
			multiple_goals=[]
			for m in multiple_goals_latlon:
				x,y = locatePosition.geoToCart (origin, endDistance, m)
				multiple_goals.append((x/2,y/2))
			print("multiple_goals",multiple_goals)
			circle_formation_goals=multiple_goals
			for b in s.swarm:										
				print("circle_formation_table",circle_formation_table)
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				ind=[0]*num_bots
				step=1
				while 1:					
					if(start_flag):
						break										
					time.sleep(sleep_times.get(num_bots))						
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]			
						if(circle_formation_table[i]==0) :	
							lat = vehicles[i].location.global_relative_frame.lat
							lon = vehicles[i].location.global_relative_frame.lon
							x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
							plane_points=[x/2,y/2]
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=100)
							cmd.exec(b)
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])
							if master_flag:
								current_position = [b.x*2,b.y*2]
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								if(step<=len(vehicles)):
								    step+=1
								    print("!!!!!!!!!!")
								    if same_alt_flag:
									    point1 = LocationGlobalRelative(float(base_lat),float(base_lon),same_height)
								    else:
									    point1 = LocationGlobalRelative(float(base_lat),float(base_lon),different_height[i])
								    vehicles[i].simple_goto(point1)
								if step==100:
								    if same_alt_flag:
									    point1 = LocationGlobalRelative(float(base_lat),float(base_lon),same_height)
								    else:
									    point1 = LocationGlobalRelative(float(base_lat),float(base_lon),different_height[i])
								    vehicles[i].simple_goto(point1)
								if step!=100:    
								    current_altitude = vehicle.location.global_relative_frame.alt
								    distance = locatePosition.distance_bearing(vehicles[i].location.global_relative_frame.lat,vehicles[i].location.global_relative_frame.lon,float(base_lat),float(base_lon))
								    if (different_height[i] - 5) <= current_altitude <= (different_height[i] + 5) and distance < 150:
								        uav_home_pos=[]
								        step=100
								        for vehicle in vehicles:
								            lat = vehicle.location.global_relative_frame.lat
								            lon = vehicle.location.global_relative_frame.lon
								            x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
								            uav_home_pos.append((x / 2, y / 2))
								        s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
							if i < len(robots):
							    robots[i] = (x / 2, y / 2)
							msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
							if(dx<50 and dy<50):
								cmd =cvg.goal_area_cvg(i,b,goal)
								cmd+= disp_field(b,neighbourhood_radius=100)
								cmd.exec(b)
								dx=abs(goal[0]-current_position[0])
								dy=abs(goal[1]-current_position[1])	
								circle_formation_table[i]=1					
								if(dx<=50 and dy<=50):
									ind[i]+=1									
									if(ind[i]==len(multiple_goals)):
										ind[i]=0
										
								if master_flag:
									current_position = [b.x*2,b.y*2]
									lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									vehicles[i].simple_goto(point1)
									
							else:
								continue
								
						if(circle_formation_table[i]==1):	
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=100)
							cmd.exec(b)
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])	
							circle_formation_table[i]=1					
							if(dx<=10 and dy<=10):
								ind[i]+=1
								print("index",ind)
								if(ind[i]==len(multiple_goals)):
									ind[i]=0
									
							if master_flag:
								current_position = [b.x*2,b.y*2]
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								vehicles[i].simple_goto(point1)
							
						else:
							continue					
						
					if(index==b"stop"):	
						start_flag=False
						circle_formation_flag=False		
						break
		
		if(data.startswith(b'grid_path_planning')):
		    decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
		    f,center_lat,center_lon,num_uavs,grid_space,coverage_area = decoded_index.split(",")
		    curve= BezierCurve(origin, float(center_lat), float(center_lon),int(num_uavs),int(grid_space), int(coverage_area))
		    val = curve.GridFormation()
		    path = curve.generate_bezier_curve()
		    start_multiple_goals=path
    
		if(data.startswith(b"navigate")) or (start_flag):
			print("data",data)
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			f,center_lat,center_lon,num_uavs,grid_space,coverage_area = decoded_index.split(",")
			curve= BezierCurve(origin, float(center_lat), float(center_lon),int(num_uavs),int(grid_space), int(coverage_area))
			val = curve.GridFormation()
			path = curve.generate_bezier_curve()
			multiple_goals=path
			if master_flag:
				#time.sleep(0.1)
				start_flag=True
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))						
				'''
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
				'''
			s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
			gui = viz.Gui(s)

			index="data"
						
			for b in s.swarm:				
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				ind=0
				my_seq = _last_seq
				diverted_indexes=set()
				while 1:
					if not start_flag:
						start_flag=False
						break
					time.sleep(sleep_times.get(num_bots))
					check_for_new_command(my_seq)
					bot_array=[0]*num_bots
					for i,b in enumerate(s.swarm):
						if i in active_goal_tasks:
							diverted_indexes.add(i)
						if i in diverted_indexes:
							continue
						current_position = [b.x,b.y]
						if(skip_wp_flag):
							with open(csv_path, 'a') as csvfile:
								print("next_wp",next_wp)
								next_wp=int(next_wp)-1
								start_return_csv_flag=True
								fieldnames = ['waypoint']
								writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
								writer.writerow({'waypoint':next_wp})
								goal_path_csv_array.append(next_wp)
								print("goal_path_csv_array",goal_path_csv_array)
								goal_path_csv_array_flag=True	
							for x,c in enumerate(s.swarm):
								goal_table[x]=next_wp
							print("goal_table",goal_table)
							skip_wp_flag=False
							ind=goal_table[i]							
						
						goal=multiple_goals[ind]
						cmd =cvg.goal_area_cvg(i,b,goal)
						cmd+= disp_field(b,neighbourhood_radius=100)
						cmd.exec(b)							
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])						
						if(dx<=1 and dy<=1):							
							bot_array[i]=1
						if any(element == 1 for element in bot_array):
					         if ind == len(multiple_goals) - 1:
					            print('all_bot_reach_flag',all_bot_reach_flag)
					            all_bot_reach_flag = True
					            break
					         else:
					            ind+=1
					            print('ind',ind,multiple_goals[ind])

						if (all_bot_reach_flag==True):
							with open(csv_path, 'a') as csvfile:
								start_return_csv_flag=True
								fieldnames = ['waypoint']
								writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
								writer.writerow({'waypoint':multiple_goals.index(goal)})
								print("multiple_goals.index(goal)",multiple_goals.index(goal))
								goal_path_csv_array.append(multiple_goals.index(goal))
								print("goal_path_csv_array",goal_path_csv_array)
								goal_path_csv_array_flag=True	
							all_bot_reach_flag=False
							bot_array=[0]*num_bots
							if (ind==len(multiple_goals)-1):
								print("Break")
								start_flag=False
								break					
						if master_flag:
							current_position = [b.x*2,b.y*2]
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
					
					if 'gui' in locals() and gui is not None:
						gui.show_goals([multiple_goals[ind]] * len(s.swarm))
						gui.update()

					if(index==b"stop"):
						print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						start_flag=False
						circle_formation_flag=False		
						if 'gui' in locals() and gui is not None:
							gui.close()
						break
		
		if(data.startswith(b"search")) or (search_flag):
			print("data",data)
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			print('decoded_index',decoded_index)
			msg_parts = decoded_index.split(",", 6)
			selected_uav_raw = msg_parts[6] if len(msg_parts) > 6 else None
			f,center_lat,center_lon,num_uavs,grid_space,coverage_area = msg_parts[:6]
			selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
			selected_indexes = selected_swarm_indexes(selected_uav_ids)
			selected_index_set = set(selected_indexes)
			effective_num_uavs = max(1, len(selected_indexes) if selected_uav_ids else int(num_uavs))
			print('[search] selected_uav_ids', selected_uav_ids, 'selected_indexes', selected_indexes)
			curve= BezierCurveMultiple(origin, float(center_lat), float(center_lon),effective_num_uavs,int(grid_space), int(coverage_area))
			val = curve.GridFormation()
			path = curve.generate_bezier_curve()
			search_step=1
			if master_flag:
				index="data"
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))
				'''
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
				'''				
				s = sim.Simulation(uav_home_pos,num_bots=num_bots, env_name=file_name)
				gui = viz.Gui(s)

			print("Search Started")
			search_flag_val=0
			f=""
			num_lines=0
			goal_position=[]
			cwd = os.getcwd()
			print("search_flag_val",search_flag_val)
			grid_path_array=[0]*len(pos_array)
			if search_flag_val==0:
				search_flag_val+=1
				csv_file_paths=[]
				for i in range(1,effective_num_uavs+1):
					csv_file_paths.append( os.path.join(curve.mission_dir,f'drone_{i}_path.csv'))
				print("csv_file_paths",csv_file_paths)
			removed_grid_path_array_index=0
			print('grid_path_array',grid_path_array)
			current_goals=[None]*len(pos_array)
			my_seq = _last_seq
			diverted_indexes=set()
			while 1:
				if(num_bots==10):
					time.sleep(0.1)
				elif(num_bots==9):
					time.sleep(0.1)
				elif(num_bots==8):
					time.sleep(0.11)
				elif(num_bots==7):
					time.sleep(0.11)
				elif(num_bots==6):
					time.sleep(0.12)#verified
				elif(num_bots==5):
					time.sleep(0.12)#verified
				elif(num_bots==4):
					time.sleep(0.123)
				elif(num_bots==3):
					time.sleep(0.125)
				elif(num_bots==2):
					time.sleep(0.13)
				elif(num_bots==1):
					time.sleep(0.13)						
				check_for_new_command(my_seq)
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				reader = csv.reader(open(csv_file_paths[0]))
				num_lines= len(list(reader))
				if(remove_bot_flag):
					print("remove_bot_flag,remove_bot_array",remove_bot_flag,remove_bot_array)
					removed_indexes = sorted(remove_bot_array, reverse=True)
					for m in removed_indexes:
						if 0 <= m < len(all_uav_csv_grid_array):
							removed_uav_grid.append(all_uav_csv_grid_array.pop(m))
						if 0 <= m < len(grid_path_array):
							removed_grid_path_length.append(grid_path_array.pop(m))
					for removed_index in removed_indexes:
						selected_indexes = [idx - 1 if idx > removed_index else idx for idx in selected_indexes if idx != removed_index]
					selected_index_set = set(selected_indexes)
					remove_bot_array=[]
					remove_bot_flag=False

				if(search_step==1):
					for path_slot, bot_index in enumerate(selected_indexes):
						all_uav_csv_grid_array[bot_index]=csv_file_paths[path_slot]
					print("all_uav_csv_grid_array",all_uav_csv_grid_array)
					search_step+=1
				for i,b in enumerate(s.swarm):
					if i not in selected_index_set:
						continue
					if i in active_goal_tasks:
						diverted_indexes.add(i)
					if i in diverted_indexes:
						continue
					if(len(checkall_removed_grid_path_array_start_val)==len(pos_array)):
					    if all(c==1 for c in checkall_removed_grid_path_array_start_val):
						    landing_flag=True
					else:
					    pass
					if all(grid_path_array[x] >= int(num_lines) for x in selected_indexes) and removed_grid_path_length!=[] and not removed_grid_path_array_flag:
						print("removed_grid_path_length",removed_grid_path_length)
						allocation,remaining_points_list  = allocate_drones(int(num_lines), removed_grid_path_length, len(selected_indexes))
						print("allocation,remaining_points_list",allocation,remaining_points_list)						
						for x,v in enumerate(remaining_points_list):
						    print("x",x)
						    if(removed_grid_path_length[x]==1):
						        start_index=removed_grid_path_length[x]
						    else:
						        start_index=removed_grid_path_length[x]-1
						    print("start_index",start_index)
						    print("JJJ",allocation[x])
						    if(allocation[x]==0) and removed_grid_path_length[x]!=int(num_lines):
						        uncovered_area_points.append(removed_grid_path_length[x])
						        uncovered_area_filename.append(removed_uav_grid[x])
						        print("uncovered_area_points",x,v,uncovered_area_points,uncovered_area_filename)
						        continue
						    elif(allocation[x]==0):
						        continue
						    add_points=math.ceil(remaining_points_list[x]/allocation[x])
						    print("add_points",math.ceil(add_points))
						    end_index=start_index+add_points+1
						    print("end_index",math.ceil(end_index))
						    for m in range(allocation[x]):
						        print('removed_grid_path_array_index',removed_grid_path_array_index)
						        if(m!=0):
						            end_index+=add_points
						        if(end_index>int(num_lines)):
						            end_index=int(num_lines)
						        removed_grid_path_array[removed_grid_path_array_index] = (start_index, end_index)
						        removed_grid_path_array_start_val[removed_grid_path_array_index] = start_index
						        removed_grid_filename[removed_grid_path_array_index]=removed_uav_grid[x]
						        print("removed_grid_path_array",removed_grid_path_array,removed_grid_path_array_start_val,removed_grid_filename)
						        start_index=end_index
						        removed_grid_path_array_index+=1
						print("removed_grid_path_array!!!!!",removed_grid_path_array,removed_grid_path_array_start_val,removed_grid_filename)
						removed_grid_path_array_flag=True
						
					if all(grid_path_array[x] >= int(num_lines) for x in selected_indexes) and not removed_grid_path_length!=[]:
						landing_flag=True
					if(removed_grid_path_array_flag):						
						if(removed_grid_path_array_start_val[i]==0):
							checkall_removed_grid_path_array_start_val[i]=1
							print("checkall_removed_grid_path_array_start_val",checkall_removed_grid_path_array_start_val)
							continue
						if(removed_grid_path_array_start_val[i]==removed_grid_path_array[i][1]):							
							checkall_removed_grid_path_array_start_val[i]=1
							if(uncovered_area_points!=[]):  
							    print("uncovered_area_points",uncovered_area_points)
							    for u,uncovered_area_point in enumerate(uncovered_area_points):
							        removed_grid_path_array[i]=(uncovered_area_point,int(num_lines)+1)
							        print('removed_grid_path_array',removed_grid_path_array)
							        removed_grid_path_array_start_val[i]=uncovered_area_points[u]
							        removed_grid_filename[i]=uncovered_area_filename[u]
							        removed_grid_path_array[i]=(uncovered_area_points[u],int(num_lines))
							        print('removed_grid_path_array_start_val',removed_grid_path_array_start_val,removed_grid_filename)
							        checkall_removed_grid_path_array_start_val[i]=0
							        uncovered_area_points.pop(u)
							        uncovered_area_filename.pop(u)							
							else:							    
							    continue						
					if grid_path_array[i]>=int(num_lines) and not removed_grid_path_array_flag:
						continue						
					if(removed_grid_path_array_flag):						
						goal_lat_lon = read_specific_line(removed_grid_filename[i], removed_grid_path_array_start_val[i])						
					else:					
						goal_lat_lon = read_specific_line(all_uav_csv_grid_array[i], grid_path_array[i])
					x,y = goal_lat_lon[0][0],goal_lat_lon[0][1]
					goal=(x,y)
					current_goals[i]=goal
					#print(f"CSV goal for bot {i}: {goal}, bot pos: {b.x:.1f}, {b.y:.1f}, ratio: {goal[0]/b.x:.2f}")
					cmd =cvg.goal_area_cvg(i,b,goal)
					value=[b.x*2,b.y*2]
					current_position=[b.x,b.y]
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])
					if(dx<=2 and dy<=2):						
						if grid_path_array[i]>=int(num_lines) and not removed_grid_path_array_flag:
							continue
						if grid_path_array[i]>=int(num_lines) and removed_grid_path_array_flag:
							removed_grid_path_array_start_val[i]+=1
							print("removed_grid_path_array_start_val",removed_grid_path_array_start_val)
							
						else:
							grid_path_array[i]+=1
							print("grid_path_array",grid_path_array)				
					cmd.exec(b)											
					if master_flag:
						if pop_flag_arr[i]==1:							
							lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)							
						
				s.time_elapsed += 1
				if master_flag and 'gui' in locals() and gui is not None:
					gui.show_goals(current_goals)
					gui.update()

				if(index==b"stop"):
					search_flag=False
					if master_flag and 'gui' in locals() and gui is not None:
						gui.close()
					break
					
						
		if(data.startswith(b"split")) or (data.startswith(b"specificsplit")):
			if (data.startswith(b"specificsplit")):
			    try:
			        decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			        msg_parts = decoded_index.split('_')
			        print('msg_parts',msg_parts)
			        f = msg_parts[0]  # First coordinate pair
			        center_lat_lon_array = msg_parts[1]  # All other coordinates
			        center_lat_lon_array = json.loads(center_lat_lon_array)
			        print('center_lat_lon_array',center_lat_lon_array) 
			        uav_array = msg_parts[2]
			        uav_array = json.loads(uav_array)
			        grid_space = msg_parts[3]
			        grid_space = json.loads(grid_space)
			        print('grid_space',grid_space)
			        coverage_area=msg_parts[4]
			        coverage_area = json.loads(coverage_area)
			        print('coverage_area',coverage_area)
			        # Full-coverage gate: every currently-connected UAV (pos_array)
			        # must be assigned to exactly one group and vice versa -- the
			        # mission loop below reads uav_{pos_array[i]}_path.csv for every
			        # i in pos_array, so a connected UAV left out of every group
			        # would crash that lookup mid-mission.
			        assigned_uav_ids = [int(u) for group in uav_array for u in group]
			        if set(assigned_uav_ids) != set(pos_array):
			            print('[specificsplit] rejected: group assignment', set(assigned_uav_ids), '!= connected pos_array', set(pos_array))
			            continue
			        else:
			            split = SpecificSplitMission(origin=origin,center_lat_lons=center_lat_lon_array, drone_array = uav_array, grid_spacing=grid_space,
                                     coverage_area=coverage_area)
			            isDone = split.GroupSplitting(
                            center_lat_lons=center_lat_lon_array,
                            drone_array=uav_array,
                            grid_spacing=grid_space,
                            coverage_area=coverage_area,
                        )
			    except Exception as e:
			        print('Exception',e)
			        continue
			if(data.startswith(b"split")):
			    try:
			        decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			        msg_parts = decoded_index.split('_')
			        print('msg_parts',msg_parts,len(msg_parts))
			        f = msg_parts[0]  # First coordinate pair
			        # msg_parts[2] is the operator's actual UAV-id selection from the
			        # GCS (not just a headcount) -- honored below, gated on it
			        # matching the swarm computer's own live pos_array exactly.
			        selected_uav_ids = [int(u) for u in json.loads(msg_parts[2])]
			        grid_space=msg_parts[3]
			        grid_space = json.loads(grid_space)
			        coverage_area=msg_parts[4]
			        coverage_area = json.loads(coverage_area)
			        center_lat_lon_array = msg_parts[1]  # All other coordinates
			        center_lat_lon_array = json.loads(center_lat_lon_array)
			        if set(selected_uav_ids) != set(pos_array):
			            print('[split] rejected: GCS selection', set(selected_uav_ids), '!= connected pos_array', set(pos_array))
			            continue
			        else:
			            split = AutoSplitMission(origin=origin,center_lat_lons=center_lat_lon_array, drone_list=selected_uav_ids, grid_spacing=int(grid_space),
                                     coverage_area=int(coverage_area))
			            isDone = split.GroupSplitting(
                            center_lat_lons=center_lat_lon_array,
                            num_of_drones=len(selected_uav_ids),
                            grid_spacing=int(grid_space),
                            coverage_area=int(coverage_area),
                        )
			    except Exception as e:
			        print('Exception',e)
			
			split_flag=True
			split_flag_val=0
			search_step=1
			all_uav_csv_grid_array=[0]*len(pos_array)
			grid_path_array=[0]*len(pos_array)
			num_lines=[0]*len(pos_array)
			pop_flag_arr=[1]*len(pos_array)
			removed_uav_grid=[]
			removed_grid_path_length=[]
			uncovered_area_points=[]
			uncovered_area_filename=[]
			removed_grid_path_array_flag=False
			removed_grid_path_array=[0]*len(pos_array)
			removed_grid_filename=[0]*len(pos_array)
			removed_grid_path_array_start_val=[0]*len(pos_array)
			checkall_removed_grid_path_array_start_val=[0]*len(pos_array)
			remove_bot_flag=False
			remove_bot_array=[]
			if master_flag:
				index="data"
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))
				'''
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
				'''
				s = sim.Simulation(uav_home_pos,num_bots=num_bots, env_name=file_name)
				gui = viz.Gui(s)

			print("Group Splitting Started")		
			f=""
			num_lines=[0]*len(pos_array)
			print('num_lines',num_lines)
			goal_bot_num=0
			goal_position=[]
			cwd = os.getcwd()
			grid_path_array=[0]*len(pos_array)
			print("split_flag_val",split_flag_val)
			if split_flag_val==0:
				split_flag_val+=1
				csv_file_paths=[]
				# Both plain split (AutoSplitMission.drone_list=pos_array) and
				# specific_split (uav_array) now write their per-drone files keyed
				# by real UAV id, not a sequential slot -- so csv_file_paths[i]
				# must be looked up by pos_array[i], the same id that indexes
				# s.swarm[i]/vehicles[i] everywhere else in this loop.
				for i in range(len(pos_array)):
					uav_id = pos_array[i]
					csv_file_paths.append( os.path.join(split.mission_dir, f'uav_{uav_id}_path.csv'))
					reader = csv.reader(open(csv_file_paths[i]))
					num_lines[i]= len(list(reader))
				print("csv_file_paths",csv_file_paths,num_lines)
			removed_grid_path_array_index=0
			my_seq = _last_seq
			print('grid_path_array',grid_path_array)
			current_goals=[None]*len(pos_array)
			diverted_indexes=set()
			while 1:
				time.sleep(sleep_times.get(num_bots))
				check_for_new_command(my_seq)
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				if(remove_bot_flag):
					print("remove_bot_flag",remove_bot_flag)
					for m in remove_bot_array:
					    print("LLLLLL",remove_bot_array,m)
					    removed_uav_grid.append(all_uav_csv_grid_array.pop(m))
					    removed_grid_path_length.append(grid_path_array.pop(m))
					remove_bot_array=[]
					remove_bot_flag=False 
					
				if(search_step==1):
					for i,b in enumerate(s.swarm):
						all_uav_csv_grid_array[i]=csv_file_paths[i]
					print("all_uav_csv_grid_array",all_uav_csv_grid_array)
					search_step+=1
				for i,b in enumerate(s.swarm):
					if i in active_goal_tasks:
						diverted_indexes.add(i)
					if i in diverted_indexes:
						continue
					if(len(checkall_removed_grid_path_array_start_val)==len(pos_array)):
					    if all(c==1 for c in checkall_removed_grid_path_array_start_val):
						    landing_flag=True
					else:
					    #print("length oflen(checkall_removed_grid_path_array_start_val",len(checkall_removed_grid_path_array_start_val))
					    pass
					if all(x >= int(num_lines[i]) for x in grid_path_array) and removed_grid_path_length!=[] and not removed_grid_path_array_flag:
						print("removed_grid_path_length",removed_grid_path_length)						
						allocation,remaining_points_list  = allocate_drones(int(num_lines[i]), removed_grid_path_length, len(pos_array))
						print("allocation,remaining_points_list",allocation,remaining_points_list)						
						for x,v in enumerate(remaining_points_list):
						    print("x",x)
						    if(removed_grid_path_length[x]==1):
						        start_index=removed_grid_path_length[x]
						    else:
						        start_index=removed_grid_path_length[x]-1
						    print("start_index",start_index)
						    print("JJJ",allocation[x])
						    if(allocation[x]==0) and removed_grid_path_length[x]!=int(num_lines[i]):
						        uncovered_area_points.append(removed_grid_path_length[x])
						        uncovered_area_filename.append(removed_uav_grid[x])
						        print("uncovered_area_points",x,v,uncovered_area_points,uncovered_area_filename)
						        continue
						    elif(allocation[x]==0):
						        continue
						    add_points=math.ceil(remaining_points_list[x]/allocation[x])
						    print("add_points",math.ceil(add_points))
						    end_index=start_index+add_points+1
						    print("end_index",math.ceil(end_index))
						    for m in range(allocation[x]):
						        print('removed_grid_path_array_index',removed_grid_path_array_index)
						        if(m!=0):
						            end_index+=add_points
						        if(end_index>int(num_lines[i])):
						            end_index=int(num_lines[i])
						        removed_grid_path_array[removed_grid_path_array_index] = (start_index, end_index)
						        removed_grid_path_array_start_val[removed_grid_path_array_index] = start_index
						        removed_grid_filename[removed_grid_path_array_index]=removed_uav_grid[x]
						        print("removed_grid_path_array",removed_grid_path_array,removed_grid_path_array_start_val,removed_grid_filename)
						        start_index=end_index
						        removed_grid_path_array_index+=1
						print("removed_grid_path_array!!!!!",removed_grid_path_array,removed_grid_path_array_start_val,removed_grid_filename)
						removed_grid_path_array_flag=True
						
					if all(x >= int(num_lines[i]) for x in grid_path_array) and not removed_grid_path_length!=[]:
						landing_flag=True
					if(removed_grid_path_array_flag):						
						if(removed_grid_path_array_start_val[i]==0):
							checkall_removed_grid_path_array_start_val[i]=1
							print("checkall_removed_grid_path_array_start_val",checkall_removed_grid_path_array_start_val)
							continue
						if(removed_grid_path_array_start_val[i]==removed_grid_path_array[i][1]):							
							checkall_removed_grid_path_array_start_val[i]=1
							if(uncovered_area_points!=[]):  
							    print("uncovered_area_points",uncovered_area_points)
							    for u,uncovered_area_point in enumerate(uncovered_area_points):
							        removed_grid_path_array[i]=(uncovered_area_point,int(num_lines[i])+1)
							        print('removed_grid_path_array',removed_grid_path_array)
							        removed_grid_path_array_start_val[i]=uncovered_area_points[u]
							        removed_grid_filename[i]=uncovered_area_filename[u]
							        removed_grid_path_array[i]=(uncovered_area_points[u],int(num_lines[i]))
							        print('removed_grid_path_array_start_val',removed_grid_path_array_start_val,removed_grid_filename)
							        checkall_removed_grid_path_array_start_val[i]=0
							        uncovered_area_points.pop(u)
							        uncovered_area_filename.pop(u)							
							else:							    
							    continue						
					if grid_path_array[i]>=int(num_lines[i]) and not removed_grid_path_array_flag:
						continue						
					if(removed_grid_path_array_flag):						
						goal_lat_lon = read_specific_line(removed_grid_filename[i], removed_grid_path_array_start_val[i])						
					else:					
						goal_lat_lon = read_specific_line(all_uav_csv_grid_array[i], grid_path_array[i])
					x,y = goal_lat_lon[0][0],goal_lat_lon[0][1]
					goal=(x,y)
					current_goals[i]=goal
					cmd =cvg.goal_area_cvg(i,b,goal)
					value=[b.x*2,b.y*2]
					current_position=[b.x,b.y]
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])
					if(dx<=2 and dy<=2):						
						if grid_path_array[i]>=int(num_lines[i]) and not removed_grid_path_array_flag:
							continue
						if grid_path_array[i]>=int(num_lines[i]) and removed_grid_path_array_flag:
							removed_grid_path_array_start_val[i]+=1
							print("removed_grid_path_array_start_val",removed_grid_path_array_start_val)						
						else:
							grid_path_array[i]+=1
							print("grid_path_array",grid_path_array)				
					cmd.exec(b)											
					if master_flag:
						if pop_flag_arr[i]==1:							
							lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
						
				s.time_elapsed += 1
				if master_flag and 'gui' in locals() and gui is not None:
					gui.show_goals(current_goals)
					gui.update()

				if(index==b"stop"):
					split_flag=False
					if master_flag and 'gui' in locals() and gui is not None:
						gui.close()
					break
														
		if(data.startswith(b"home")) or (home_flag):
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			f = decoded_index[0:4]  # First coordinate pair
			return_array = decoded_index[5:]  # All other coordinates
			return_latlon = json.loads(return_array)
			return_xy=[]
			for x in return_latlon:
			    x,y = locatePosition.geoToCart (origin, endDistance, [x[0],x[1]])
			    return_xy.append((x/2,y/2))
			print(return_xy,"return_xy") 
			return_ind=0
			if master_flag:
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))
				'''
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
				'''
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
				home_flag=True				
			bot_array_home=[0]*num_bots
			all_bot_reach_flag_home=False
			index="data"
			while 1:    
				time.sleep(sleep_times.get(num_bots))
				if(home_flag1):
					home_flag=False
					'''
					for i,x in enumerate(s.swarm):
						print(i)
						vehicles[i].mode = VehicleMode("RTL")
						print('vehicle',vehicles[i],i,'rtl')
					'''
					break
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				for i,b in enumerate(s.swarm):
					current_position = [b.x,b.y]
					goal=return_xy[return_ind]
					cmd =cvg.goal_area_cvg(i,b,goal)
					cmd.exec(b)
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])						
					if(dx<=5 and dy<=5):
						bot_array_home[i]=1
						if any(element == 1 for element in bot_array_home):
						    if(return_ind==len(return_xy)-1):
						        all_bot_reach_flag_home=True
						        print('all_bot_reach_flag_home',all_bot_reach_flag_home)
						        break
						    else:
						        return_ind+=1
						        print('return_ind',return_ind)
					if (all_bot_reach_flag_home==True):						
						'''
						with open(csv_path, 'a') as csvfile:
							fieldnames = ['waypoint']
							writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
							writer.writerow({'waypoint':-1})	
						'''
						home_flag1=True
						home_flag=False
						break
							
					if master_flag:										
						current_position = [b.x*2,b.y*2]
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						point1 = LocationGlobalRelative(lat,lon,home_height[i])
						vehicles[i].simple_goto(point1)
															       
				if(index==b"stop"):
					home_flag1=True
					home_flag=False
					
		if(home_flag1):
		    if master_flag:
		        uav_home_pos=[]
		        for vehicle in vehicles:
		            lat = vehicle.location.global_relative_frame.lat
		            lon = vehicle.location.global_relative_frame.lon
		            x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
		            uav_home_pos.append((x / 2, y / 2))
		        '''
		        serialized_data = json.dumps(home_pos)
		        serialized_data="uav_home_pos" + serialized_data
		        
		        for i in range(len(pos_array)):
		            uav1.sendto(serialized_data.encode(),uav1_server_address)
		            time.sleep(0.2)
		            uav2.sendto(serialized_data.encode(),uav2_server_address)
		            time.sleep(0.2)
		            uav3.sendto(serialized_data.encode(),uav3_server_address)
		            time.sleep(0.2)
				'''	
		        s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
		        home_flag1=True				
		    bot_array_home=[0]*num_bots
		    all_bot_reach_flag_home=False
		    index="data"
		    while 1:
		        time.sleep(sleep_times.get(num_bots))
		        if(all_bot_reach_flag_home==True):
		            home_flag1=False
		            home_flag=False					
		            print("END")
		            break
		        if(vehicle_lost_flag):
		            vehicle_lost_flag=True
		            x=remove_vehicle()
		            print(x)
		        print('ggg',home_pos)
		        for i,b in enumerate(s.swarm):
		            current_position = [b.x,b.y]
		            goal=home_pos[i]
		            cmd =cvg.goal_area_cvg(i,b,goal)
		            cmd.exec(b)
		            dx=abs(goal[0]-current_position[0])
		            dy=abs(goal[1]-current_position[1])						
		            if(dx<=0.1 and dy<=0.1):
		                bot_array_home[i]=1
		                if all(element == 1 for element in bot_array_home):
		                    all_bot_reach_flag_home=True
		                    print('all_bot_reach_flag_home',all_bot_reach_flag_home)
		                    break
					    
		            if (all_bot_reach_flag_home==True):						
		                    break
							
		            if master_flag:
		                current_position = [b.x*2,b.y*2]
		                lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
		                point1 = LocationGlobalRelative(lat,lon,home_height[i])
		                vehicles[i].simple_goto(point1)
		            									       
		        if(index==b"stop"):
		            home_flag1=False
		            home_flag=False
			
	except MissionPreempted as preempt:
		# A mission loop noticed a newer command mid-flight (via
		# check_for_new_command) and unwound here instead of running to
		# completion. Dispatch the preempting command immediately on the
		# next iteration -- no idle wait for a fresh mailbox seq.
		_next_data, _next_address = preempt.data, preempt.address
		_last_seq = _pending_command.seq
	except Exception as e:
		if(search_flag):
			search_flag=False
		if(split_flag):
			split_flag=False
		if(start_flag):
			start_flag=False
		if(circle_formation_flag):
			circle_formation_flag=False
		if(home_flag):
			home_flag=False
		if(home_goto_flag):
			home_goto_flag=False
		pass				
