print("Running foraging example 1\nUsing source files for package imports\nPARAMETERS:")
import sys,os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..')))
print(sys.path)

import swarm_tasks

#Set demo parameters directly
import numpy as np
import random
import time
swarm_tasks.utils.robot.DEFAULT_NEIGHBOURHOOD_VAL = 7
swarm_tasks.utils.robot.DEFAULT_SIZE= 0.4
swarm_tasks.utils.robot.MAX_SPEED = 1.5
swarm_tasks.utils.robot.MAX_ANGULAR: 0.3
np.random.seed(42)
random.seed(42)
from scipy.spatial import distance
from swarm_tasks.simulation import simulation as sim
from swarm_tasks.simulation import visualizer as viz
from swarm_tasks.modules import follow
#Required modules
import swarm_tasks.utils as utils
import swarm_tasks.envs as envs
import swarm_tasks.controllers as ctrl
import swarm_tasks.controllers.potential_field as potf
import swarm_tasks.controllers.base_control as base_control
from swarm_tasks.modules.formations import line,circle	
from swarm_tasks.modules.dispersion import disp_field
from swarm_tasks.modules.aggregation import aggr_centroid, aggr_field
from swarm_tasks.modules import exploration as exp
from swarm_tasks.utils import robot as bot
from swarm_tasks.utils.weight_functions import linear_trunc, hyperbolic,sinusoidal,triangular
from swarm_tasks.tasks import area_coverage as cvg
from swarm_tasks.modules.formations import line
from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2, asin, degrees
from dronekit import connect, VehicleMode, LocationGlobalRelative
from bezier_curve import BezierCurve
from bezier_curve_multiple import BezierCurveMultiple
import socket,json
import threading
import locatePosition
import csv

file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
file_server_address = ('', 12003)  #receive from .....rx.py
file_sock.bind(file_server_address)

graph_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
graph_server_address = ('192.168.6.203', 12009)  #receive from .....rx.py

remove_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ('', 12008)  #receive from .....rx.py
sock2.bind(server_address2)
sock2.setblocking(0)
sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ('', 12002)  #receive from .....rx.py
sock3.bind(server_address3)

uav1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav1_server_address = ('192.168.6.203', 12002)  #receive from .....rx.py
uav2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav2_server_address = ('192.168.6.203', 12002)  #receive from .....rx.py
uav3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav3_server_address = ('192.168.6.203', 12002)
#uav4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#uav4_server_address = ('192.168.0.153', 12002)
#uav5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#uav5_server_address = ('192.168.0.153', 12002)

goal_table=[]
file_name=""
master_num=0
master_flag=False
print("file_name",file_name)
cwd = os.getcwd()

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
	graph_socket.sendto(str("Drone 3 master received").encode(), graph_server_address)	
except:
	pass		
while True:
	try:
		data,address=file_sock.recvfrom(1024)
		print("data",data)
		decoded_index = data.decode('utf-8') 
		print("decoded_index",decoded_index)
		graph_socket.sendto(str("Drone 3"+decoded_index).encode(), graph_server_address)
		file_name=decoded_index
		break
			
	except:
		pass
'''
master_num==3
master_flag=True
file_name="Medur_"

disperse_multiple_goals=[]
start_multiple_goals=[]
return_multiple_goals=[]
goal_points=[]
agg_goal_point=[]
origin=[]
removed_uav_homepos_array=[]

if(file_name=="Medur_"):
	origin=( 13.308039, 80.146629)#medur_vtol
	start_multiple_goals=[(4533.359571946137,  4534.582162146959),(5377.564492281329,  4421.370703097977),(5604.1003862181815,  4653.543172566769),(5337.341100049475,  4250.772625520308),(4518.998921425327,  4397.592049580196),(4301.768995360449,  4593.206644467459),(4456.608688538883,  4258.870187083201),(5303.847437392898,  4100.500955291573),(5551.116514904548,  4321.971920374709),(5244.308833824743,  3959.7844666417163),(4461.759579157777,  4109.740202033495)]
	#plan2[(4533.359571946137,  4534.582162146959),(5541.529225925758,  4398.968678463051),(5799.291002080761,  4651.218705350108),(5574.9320336883175,  4202.708479825763),(4518.998921425327,  4397.592049580196),(4301.768995360449,  4593.206644467459),(4456.608688538883,  4258.870187083201),(5568.515525467282,  4043.4876256302314),(5832.067947226436,  4301.679395717466),(5568.300107458491,  3887.6764008874325),(4461.759579157777,  4109.740202033495)]
	#plan1[(4525.754124970843,  4540.247117864114),(7042.036495192134,  4081.498042240694),(7572.850233419122,  4397.902557185096),(7054.010568720503,  3704.257212401159),(4525.749341561368,  4133.590978521016),(4043.784895040774,  4386.932320881892),(4415.993330884787,  3743.163108678769),(7008.169948105923,  3213.684247611162),(7724.160895424688,  3593.132632301485),(6991.440577817013,  2718.308185229332),(4459.746148555264,  3106.0575243964504)]
	multiple_goals=start_multiple_goals
	goal_points=start_multiple_goals
		 
if(file_name=="dce_airport"):
	origin=(12.858180, 80.030595)#dce
	start_multiple_goals=[(1161.9877697773895,3952.7219876760137),(1474.0593062047521,3922.1997184867887),(1746.4339033240276,3864.995130599164),(1627.7081983593039,3631.7809497202543),(1315.9537877228481,3750.6044128682397),(1058.1415227872608,3931.8705804860747)]
	goal_points=start_multiple_goals
	multiple_goals=start_multiple_goals


nextwaypoint=0
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('192.168.6.203', 12005)  #receive from .....rx.py

# Bind the socket to the port
remove_bot_server_address = ('192.168.6.203', 12001)  #receive from .....rx.py

sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address4 = ('', 12011)  #receive from .....rx.py
sock.bind(server_address4)

num_bots=10
vehicles=[]
pos_array=[]
heartbeat_ip=["192.168.0.151","192.168.0.152","192.168.0.153","192.168.0.154","192.168.0.155","192.168.0.156","192.168.0.157","192.168.0.158","192.168.0.159","192.168.0.160"]
heartbeat_ip_timeout=[0]*10
heartbeat_ip_timeout=[30,30,30,30,30,30,30,30,30,30]
goal_path_csv_array=[]
goal_path_csv_array_flag=False
csv_path = cwd+"/pos.csv"
skip_wp_flag=False
next_wp=0

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
        		for l in range(2):
        			graph_socket.sendto(str(msg).encode(), graph_server_address)	
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
        		for i in range(3):
        			sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
        		print("master_flag",master_flag)
        	
        	if decoded_index.startswith("pos_array"):        		
        		message = decoded_index[:9]  # Assuming "home_pos" is 8 characters long
        		array_data = decoded_index[9:]	
        		print("pos_array",pos_array)
        		pos_array = json.loads(array_data)
        		print("pos_array",pos_array)
        		
        		index="data"
        		msg="UAV 1 connected with "+str(len(pos_array))+" vehicles"
        		for i in range(3):
        			sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
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

def vehicle_connection():	
	global vehicles,pos_array,num_bots,graph_socket,graph_server_address,heartbeat_ip_timeout
	pos_array=[]
	vehicles=[]
	num_bots=0
	
	try:	
		vehicle1= connect('udpin:192.168.6.203:14561',baud=115200, heartbeat_timeout=heartbeat_ip_timeout[0])
		vehicle1.airspeed = 12
		print('Drone1')
		vehicles.append(vehicle1)
		pos_array.append(1)
		num_bots+=1
		msg="Drone1 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass
		print(	"Vehicle 1 is lost")
	try:		
		vehicle2= connect('udpin:192.168.6.203:14562',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[1])
		vehicle2.airspeed = 12
		print('Drone2')
		num_bots+=1	
		vehicles.append(vehicle2)
		pos_array.append(2)
		msg="Drone2 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass	
		print(	"Vehicle 2 is lost")
	
	try:
		vehicle3= connect('udpin:192.168.6.203:14563',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[2])
		vehicle3.airspeed = 12
		print('Drone3')
		num_bots+=1
		vehicles.append(vehicle3)
		pos_array.append(3)
		msg="Drone3 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass
		print(	"Vehicle 3 is lost")
	
	try:		
		vehicle4= connect('udpin:192.168.6.203:14564',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[3])
		vehicle4.airspeed = 12
		print('Drone4')
		num_bots+=1
		vehicles.append(vehicle4)
		pos_array.append(4)
		msg="Drone4 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass
		print(	"Vehicle 4 is lost")
	try:		
		vehicle5= connect('udpin:192.168.6.203:14565',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[4])
		vehicle5.airspeed = 12
		print('Drone5')
		num_bots+=1
		vehicles.append(vehicle5)
		pos_array.append(5)
		msg="Drone5 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass
		print(	"Vehicle 5 is lost")
	'''
	try:
		vehicle6= connect('udpin:192.168.6.203:14566',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[5])
		vehicle6.airspeed = 12
		print('Drone6')
		num_bots+=1
		vehicles.append(vehicle6)
		pos_array.append(6)
		msg="Drone6 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass	
		print(	"Vehicle 6 is lost")
		
	try:
		vehicle7= connect('udpin:192.168.6.203:14567',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[6])
		vehicle7.airspeed = 12
		print('Drone7')
		num_bots+=1
		vehicles.append(vehicle7)
		pos_array.append(7)
		msg="Drone7 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		
		pass
		print(	"Vehicle 7 is lost")	
	
	try:
		vehicle8= connect('udpin:192.168.6.203:14568',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[7])
		vehicle8.airspeed = 12
		print('Drone8')
		num_bots+=1
		vehicles.append(vehicle8)
		pos_array.append(8)
		msg="Drone8 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:	
		pass
		print(	"Vehicle 8 is lost")
	
	try:	
		vehicle9= connect('udpin:192.168.6.203:14569',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[8])
		vehicle9.airspeed = 12
		print('Drone9')
		num_bots+=1
		vehicles.append(vehicle9)
		pos_array.append(9)
		msg="Drone9 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 9 is lost")
	
	try:	
		vehicle10= connect('udpin:192.168.6.203:14570',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[9])
		vehicle10.airspeed = 12
		print('Drone10')
		vehicles.append(vehicle10)
		pos_array.append(10)
		num_bots+=1
		msg="Drone10 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 10 is lost")
	'''
	print(len(vehicles))
	
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
	
count=0

endDistance=20000
same_height=100
different_height=[300,310,300,310,300,200,220,240,260,280]
home_height=[50,60,70,80,90,100,110,120,130,140]
home_pos=[]
home_pos_lat_lon=[]
uav_home_pos=[]
current_lat_lon=[]
home_flag=False
home_flag1=False
search_flag=False
search_height_flag=False
return_height_flag=False
home_goto_flag=False
move_bot_flag=False
lost_vehicle_num=0
vehicle_lost_flag=False

landing_flag=False
# Iterate over the list of vehicles
robots = [(0, 0)] * 10

slave_heal_ip=["192.168.0.153"]*num_bots
heartbeat=[0]*num_bots

vehicle_uav_heartbeat_flag=False
disperse_flag=False

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address1 = ('192.168.0.210', 12010)
slave_heal_ip=["192.168.0.153"]*num_bots
           
all_uav_csv_grid_array=[0]*num_bots
robot_positions = [([0, 0]) for _ in range(20)]
print("origin#########",origin)

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
		    
		    
	if master_flag:	
		sent = graph_socket.sendto(str(msg).encode(), graph_server_address)

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
		#print("serialized_goal_data",serialized_goal_data)
		sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

	if master_flag:
		home_pos_lat_lon=[]
		home_pos=[]		
		for i,vehicle in enumerate(vehicles):		    
		    while not vehicle.home_location:
		    	cmds = vehicle.commands
		    	cmds.download()
		    	cmds.wait_ready()
		    	home = vehicle.home_location
		    	if not vehicle.home_location:
			    	print(" Waiting for home position...")
			    	time.sleep(3)
		    # Process the lat and lon as needed
		    print(f"Vehicle - Latitude: {home.lat}, Longitude: {home.lon}")
		    x,y = locatePosition.geoToCart (origin, endDistance, [home.lat,home.lon])
		    home_pos_lat_lon.append((home.lat,home.lon))
		    print("x,y",x/2,y/2)
		    home_pos.append((x / 2, y / 2))
		    if i < len(robots):
		        robots[i] = (x / 2, y / 2)
		    msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
		     
	if master_flag:
		serialized_data = json.dumps(home_pos)
		serialized_data="home_pos" + serialized_data
		sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
		#time.sleep(0.2)
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
	
if master_flag:
	vehicle_connection()
	while True:
	    all_armed = [False]*len(vehicles)  # Assume all vehicles are armed initially
	    print("!!!!")
	    for i,vehicle in enumerate(vehicles):
	        if vehicle.armed and vehicle.location.global_relative_frame.alt>28  :
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

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    time.sleep(3)
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto
    #  (otherwise the command after Vehicle.simple_takeoff will execute
    #   immediately).
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
#Initialize Simulation and GUI 
while True:
	if(uav_home_pos!=[]):
		print("num_bots",num_bots,uav_home_pos)
		s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name)
		for l in range(3):
			graph_socket.sendto(str("Drone 3 CONNECTED").encode(), graph_server_address)	
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
	sent = remove_socket.sendto(str(pop_bot_index).encode(), remove_bot_server_address)
	print("pop index",pop_bot_index)
	same_alt_flag=False
	uav_home_pos=[]
	for i,vehicle in enumerate(vehicles):
	    lat = vehicle.location.global_relative_frame.lat
	    lon = vehicle.location.global_relative_frame.lon	     
	    # Process the lat and lon as needed
	    #print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
	    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
	    #print("x,y",x/2,y/2)
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
while(1):
	if(master_flag):
		num_bots=len(vehicles)
	else:
		num_bots=len(pos_array)
	try:            
		data, address = sock2.recvfrom(1050)
		print ("!!msg", data)
		if(data==b"store_uav_pos"):
			if os.path.exists(csv_file_path):
    				os.remove(csv_file_path)
			
			with open(csv_file_path, mode='w', newline='') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerow(['X', 'Y'])  # Write header
				csv_writer.writerows(home_pos)
				csv_file.close()
		
		if(data==b"home_lock"):	
			sent = graph_socket.sendto(str("home_lock").encode(), graph_server_address)	
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
			     
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
		if data.startswith(b"share_data"):	
			print("data11",data)
			decoded_index = data.decode('utf-8')
			print("decoded_index",decoded_index)
			n,goal_table,s,grid_path_array=decoded_index.split(",")
			print("n,goal_table,s,grid_path_array",n,goal_table,s,grid_path_array)
			goal_table = goal_table.strip()
			grid_path_array=grid_path_array.strip()
			print(n,goal_table,s,grid_path_array,"grid_path_array")
			goal_table=json.loads(goal_table)
			grid_path_array=json.loads(grid_path_array)
			print("goal_table,grid_path_array",goal_table,grid_path_array)
			with open(csv_path, 'w') as csvfile:
					fieldnames = ['waypoint']
					writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
					writer.writerow({'waypoint':-1})
			with open(csv_path, 'a') as csvfile:
				fieldnames = ['waypoint']
				writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
				for t in goal_table:
					print("t",t)
					writer.writerow({'waypoint':t})
			sent = graph_socket.sendto(str("Data Shared").encode(), graph_server_address)
						
		if(data.startswith(b"takeoff")):
			decoded_index=data.decode('utf-8')
			print("decoded_index",decoded_index)
			data,takeoff_height=decoded_index.split(",")
			print("data,takeoff_height",data,takeoff_height)
			sent = graph_socket.sendto(str("takeoff").encode(), graph_server_address)
			for i, vehicle in enumerate(vehicles):
			    print(i)
			    thread = threading.Thread(target=arm_and_takeoff, args=(vehicle, int(takeoff_height)))				
			    vehicles_thread.append(thread)
			    thread.start()

			# Wait for all vehicles_thread to finish
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
			    			     
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			

		if(data==b"rtl"):			
			sent = graph_socket.sendto(str("rtl").encode(), graph_server_address)	
			for i,b in enumerate(s.swarm):
				if(pop_flag_arr[i]==0):
					i+=1	
				vehicles[i].mode = VehicleMode("RTL")
				vehicles[i].close()		
			break
				
		if(data==b"land"):			
			print("land!!!!!!!!!!!!!!!!")
			sent = graph_socket.sendto(str("land").encode(), graph_server_address)	
			for i,b in enumerate(s.swarm):
				if(pop_flag_arr[i]==0):
					i+=1	
				vehicles[i].mode = VehicleMode("LAND")		
			break
					
		if(data.startswith(b"remove_bot")) or (remove_flag):	
				sent = graph_socket.sendto(str("remove_bot").encode(), graph_server_address)	
				print("bot_goal!!!!!!!!!!!!")
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				f,remove_bot_num = decoded_index.split(",")
				print(f,remove_bot_num)
				print("remove_bot_num",remove_bot_num,pos_array)						
				remove_bot_flag=True
				print ("msg", index)
				for l in range(0,len(pos_array)):	
					if(int(remove_bot_num)==pos_array[l]):
						pop_bot_index=l
						print(l)
						break
				remove_bot_index=pop_bot_index
				print(pop_bot_index)
				pos_array.pop(pop_bot_index)
				print(len(pos_array))
				vehicles.pop(pop_bot_index)
				s.remove_bot(pop_bot_index)
				print(num_bots)
				print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!",pop_flag_arr)
				sent = remove_socket.sendto(str(pop_bot_index).encode(), remove_bot_server_address)
				print("pop index",pop_bot_index)
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    #print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))						
				print("uav_home_pos",uav_home_pos)    
				remove_flag=False
				uav_removed=True
				msg=str(remove_bot_num)+"- vehicle removed"
				sent = graph_socket.sendto(str(msg).encode(), graph_server_address)	
					
		if(data==b"add"):				
				bot_pos=[154.37296943770545 ,259.40487368680743]
				if(pop_flag):
					bot_ind=pop_bot_index
				else:
					bot_ind=num_bots
				s.add_bot(bot_ind,bot_pos)
				uav_home_pos.insert(bot_ind,(bot_pos[0],bot_pos[1]))
				pop_flag=False
				pop_flag_arr[pop_bot_index]=1
		
		if data.startswith(b'specific_bot_goal'): 
				sent = graph_socket.sendto(str("specific_bot_goal").encode(), graph_server_address)	
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
									if i < len(robots):
									    robots[i] = (b.x , b.y)
									msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
												       
						if master_flag:			
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						if(index==b"stop"):
							for i in range(3):
								sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
							specific_bot_goal_flag=False
							break	
				except Exception as e:
					print("exceptiiiooonnn",e)	
					pass
					
		if data.startswith(b'group_split'): 
				sent = graph_socket.sendto(str("group_split").encode(), graph_server_address)	
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
									if i < len(robots):
									    robots[i] = (b.x , b.y)
									msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
												       
						if master_flag:			
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						if(index==b"stop"):
							for i in range(3):
								sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
							group_split_flag=False
							break	
				except Exception as e:
					print("exceptiiiooonnn",e)	
					pass
					
		if data.startswith(b'goal'):				
				index="data"
				sent = graph_socket.sendto(str("goal").encode(), graph_server_address)	
				try:		
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					f = decoded_index[0:5]  # First coordinate pair
					goal_array = decoded_index[5:]  # All other coordinates
					goal_latlon = json.loads(goal_array)
					goal_xy=[]
					bot_reached=[0]*num_bots
					for x in goal_latlon:
					    x,y = locatePosition.geoToCart (origin, endDistance, [x[0],x[1]])
					    goal_xy.append((x/2,y/2))
					    print(goal_xy,"goal_xy")
					print(goal_xy,goal_xy[0],"goal")
					goal_xy_index=0
						
					'''
					f,goal_lat,goal_lon = decoded_index.split(",")
					goal_x,goal_y = locatePosition.geoToCart (origin, endDistance, [float(goal_lat),float(goal_lon)])	
					goal_position=(goal_x/2,goal_y/2)					
					bot_reached=[0]*num_bots
					print(goal_position)
					'''
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
							time.sleep(0.12)
						elif(num_bots==5):
							time.sleep(0.12)
						elif(num_bots==4):
							time.sleep(0.123)
						elif(num_bots==3):
							time.sleep(0.125)
						elif(num_bots==2):
							time.sleep(0.13)
						elif(num_bots==1):
							time.sleep(0.13)
						if(group_goal_flag):
							print("!!!!")
							group_goal_flag=False
							guided_circle_flag=True
							print("CCC",group_goal_flag,guided_circle_flag)
							break
						goal_position=goal_xy[goal_xy_index]
						for i,b in enumerate(s.swarm):
							current_position=[b.x,b.y]
							dx=abs(goal_position[0]-current_position[0])
							dy=abs(goal_position[1]-current_position[1])
							if(dx<=5 and dy<=5):
								bot_reached[i]=1
								print("GOal reached",goal_xy_index,goal_position,bot_reached)
								'''
								if (element==1 for element in reached_bot):
								    if(len(goal_xy)==1) or len(goal_xy)==len(goal_xy_index):
								        group_goal_flag=True									
								        break
								    else:
								        goal_xy_index+=1
                                '''
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
								if i < len(robots):
								    robots[i] = (b.x , b.y)
								msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
											       
						if master_flag:			
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						if(index==b"stop"):
							for i in range(3):
								sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
							print("Data",data)
							group_goal_flag=False						
							break	
				except:
					print("exception")	
					pass
		
		if(guided_circle_flag) or data==b"guided_circle":
			multiple_goals_latlon = generate_points(float(goal_latlon[-1][0]),float(goal_latlon[-1][1]), 8, 200,1)
			print("multiple_goals_latlon",multiple_goals_latlon)	
			multiple_goals=[]
			guided_circle_formation_table=[0]*num_bots
			for m in multiple_goals_latlon:
				x,y = locatePosition.geoToCart (origin, endDistance, m)
				multiple_goals.append((x/2,y/2))
			print("multiple_goals",multiple_goals)
			guided_circle_formation_goals=multiple_goals
			multiple_goals=guided_circle_formation_goals
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
				while 1:					
					if(guided_circle_formation_flag):
						guided_circle_formation_flag=False
						break					
		
					if(num_bots==10):
						time.sleep(0.1)
					elif(num_bots==9):
						time.sleep(0.1)
					elif(num_bots==8):
						time.sleep(0.11)
					elif(num_bots==7):
						time.sleep(0.11)
					elif(num_bots==6):
						time.sleep(0.12)
					elif(num_bots==5):
						time.sleep(0.12)
					elif(num_bots==4):
						time.sleep(0.123)
					elif(num_bots==3):
						time.sleep(0.125)
					elif(num_bots==2):
						time.sleep(0.13)
					elif(num_bots==1):
						time.sleep(0.13)
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]	
						cmd =cvg.goal_area_cvg(i,b,goal)
						cmd+= disp_field(b,neighbourhood_radius=50)
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
							if i < len(robots):
							    robots[i] = (b.x , b.y)
							msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
							
						if master_flag:						
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						guided_circle_formation_flag=True		
						break
	    					
		if data.startswith(b'same'):
				sent = graph_socket.sendto(str("same altitude").encode(), graph_server_address)
				velocity_flag=True	
				print ("msg", data)
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				data1, height = decoded_index.split(",")
				#uav,goalx,goaly=str(index).split(",")
				print(data1, height)
				#print(type(data1),type(height),type(step))	
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
										velocity_flag=False
										print("1st",alt_count)
										data="data"
										same_alt_flag=True
										break
					
					if(index==b"stop"):
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						index="data"
						velocity_flag=False
						data="search"
						break
												
		if data.startswith(b'different'): 
				sent = graph_socket.sendto(str("different altitude").encode(), graph_server_address)
				velocity_flag=True	
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
					#print("velocity_flag",velocity_flag)						
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
									velocity_flag=False
									print("1st",alt_count)
									data="data"
									diff_height_flag=True
									break
						else:
							data="data"
							diff_height_flag=True
							break
													
					if(index==b"stop"):
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						index="data"
						velocity_flag=False
						print("1st")
						data="search"
						break
						
		if(data.startswith(b"loiter_point")) or (circle_formation_flag) :
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			f,base_lat,base_lon,radius,circle_direction = decoded_index.split(",")
			print("f,loiter_radius ",f,base_lat,base_lon,radius,circle_direction )
			
			if master_flag:
				#time.sleep(0.1)
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    # Process the lat and lon as needed
				    #print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    #print("x,y",x/2,y/2)				    
				    uav_home_pos.append((x / 2, y / 2))						
				print("uav_home_pos",uav_home_pos)    
				#gui.close()
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
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
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )

			index="data"
			sent = graph_socket.sendto(str("loiter_radius").encode(), graph_server_address)				
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			
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
					if(num_bots==10):
						time.sleep(0.1)
					elif(num_bots==9):
						time.sleep(0.1)
					elif(num_bots==8):
						time.sleep(0.11)
					elif(num_bots==7):
						time.sleep(0.11)
					elif(num_bots==6):
						time.sleep(0.12)
					elif(num_bots==5):
						time.sleep(0.12)
					elif(num_bots==4):
						time.sleep(0.123)
					elif(num_bots==3):
						time.sleep(0.125)
					elif(num_bots==2):
						time.sleep(0.13)
					elif(num_bots==1):
						time.sleep(0.13)
											
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]			
						if(circle_formation_table[i]==0) :	
							lat = vehicles[i].location.global_relative_frame.lat
							lon = vehicles[i].location.global_relative_frame.lon
							x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
							plane_points=[x/2,y/2]
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=50)
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
								cmd+= disp_field(b,neighbourhood_radius=50)
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
									if i < len(robots):
									    robots[i] = (b.x , b.y)
									msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
									
							else:
								continue
							if master_flag:						
								sent = graph_socket.sendto(str(msg).encode(), graph_server_address)	
						if(circle_formation_table[i]==1):	
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=50)
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
							if i < len(robots):
							    robots[i] = (b.x , b.y)
							msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
							
						else:
							continue					
						
						if master_flag:						
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						start_flag=False
						circle_formation_flag=False		
						break
	
	
		if(data==b"clear_csv"):
			print("Clear csv")
			sent = graph_socket.sendto(str("CSV Cleared").encode(), graph_server_address)
			with open(csv_path, 'w') as csvfile:
					fieldnames = ['waypoint']
					writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
					writer.writerow({'waypoint':-1})	
			
		if(data.startswith(b'grid_path_planning')):
		    print("data",data)
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
			start_multiple_goals=path
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
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
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
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
			
			index="data"
			sent = graph_socket.sendto(str("navigate").encode(), graph_server_address)				
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			for b in s.swarm:				
				multiple_goals=start_multiple_goals
				print("multiple_goals",multiple_goals,len(multiple_goals))
				goal_table=[0]*num_bots
				print("goal_table",goal_table)
				current_table=[0]*num_bots
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				ind=0
				while 1:					
					if not start_flag:
						start_flag=False
						break										
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
					bot_array=[0]*num_bots
					for i,b in enumerate(s.swarm):
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
						cmd+= disp_field(b,neighbourhood_radius=50)
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
								#circle_formation_flag=True	
								#landing_flag=True				
								break					
						if master_flag:
							current_position = [b.x*2,b.y*2]
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
							if i < len(robots):
							    robots[i] = (b.x , b.y)
							msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
							
					if master_flag:				       
						if goal_path_csv_array_flag:						    
						    int_value = int(goal_path_csv_array[-1])
						    msg += ","+'path' + str(int_value)
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						start_flag=False
						circle_formation_flag=False		
						break
						
						
		if(data.startswith(b"search")) or (search_flag):
			print("data",data)
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			f,center_lat,center_lon,num_uavs,grid_space,coverage_area = decoded_index.split(",")
			curve= BezierCurveMultiple(origin, float(center_lat), float(center_lon),int(num_uavs),int(grid_space), int(coverage_area))
			val = curve.GridFormation()
			path = curve.generate_bezier_curve()
			if master_flag:
				sent = graph_socket.sendto(str("search").encode(), graph_server_address)				
				index="data"
				serialized_data = json.dumps(home_pos)
				serialized_data="home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				serialized_goal_data = json.dumps(goal_points)
				serialized_goal_data="goal_points" + serialized_goal_data
				sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)			
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
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
				utils.robot.DEFAULT_SIZE= 0.4				
				s = sim.Simulation(uav_home_pos,num_bots=num_bots, env_name=file_name)				
				gui = viz.Gui(s)
				gui.update()
				gui.close()
			print("Search Started")		
			f=""
			num_lines=0
			uav=0
			goal_lat=0.0
			goal_lon=0.0
			goal_x=0
			goal_y=0
			goal_bot_num=0
			goal_position=[]
			move_bot_flag_array=[False]*num_bots
			move_bot_pos_array=[0]*num_bots			
			search_start_time = time.time()
			covered_points=0				
			cwd = os.getcwd()
			print("search_flag_val",search_flag_val)
			if search_flag_val==0:
				search_flag_val+=1
				csv_file_paths=[]
				for i in range(1,len(pos_array)+1):
					print("i",i)
					csv_file_paths.append( os.path.join(cwd,f'd{i}.csv'))
				print("csv_file_paths",csv_file_paths)		
			message_count = 0
			removed_grid_path_array_index=0
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
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				reader = csv.reader(open(csv_file_paths[0]))
				num_lines= len(list(reader))
				if(remove_bot_flag):
					print("remove_bot_flag",remove_bot_flag)
					for m in remove_bot_array:
					    print("LLLLLL",remove_bot_array,m)
					    removed_uav_grid.append(all_uav_csv_grid_array.pop(m))
					    removed_grid_path_length.append(grid_path_array.pop(m))
					remove_bot_array=[]
					remove_bot_flag=False
					message="remove_uav"+","+"grid_path_file_name"+","+str(all_uav_csv_grid_array)+","+str(removed_grid_path_length)
					graph_socket.sendto(str(message).encode(), graph_server_address) 
					
				if(search_step==1):
					for i,b in enumerate(s.swarm):
						all_uav_csv_grid_array[i]=csv_file_paths[i]
					print("all_uav_csv_grid_array",all_uav_csv_grid_array)
					search_step+=1
				for i,b in enumerate(s.swarm):
					if(len(checkall_removed_grid_path_array_start_val)==len(pos_array)):
					    if all(c==1 for c in checkall_removed_grid_path_array_start_val):
						    if(same_alt_flag):
							    return_height_flag=False
							    landing_flag=True
						    else:
							    return_height_flag=True
							    landing_flag=True
					else:
					    print("length oflen(checkall_removed_grid_path_array_start_val",len(checkall_removed_grid_path_array_start_val))
					if all(x >= int(num_lines) for x in grid_path_array) and removed_grid_path_length!=[] and not removed_grid_path_array_flag:						
						print("removed_grid_path_length",removed_grid_path_length)						
						allocation,remaining_points_list  = allocate_drones(int(num_lines), removed_grid_path_length, len(pos_array))
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
						
					if all(x >= int(num_lines) for x in grid_path_array) and not removed_grid_path_length!=[]:
						if(same_alt_flag):
							return_height_flag=False
							landing_flag=True
						else:
							return_height_flag=True
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
					#x,y = locatePosition.geoToCart (origin, endDistance, [goal_lat_lon[0][0],goal_lat_lon[0][1]])
					goal=(x,y)
					cmd =cvg.goal_area_cvg(i,b,goal)
					value=[b.x*2,b.y*2]
					current_position=[b.x,b.y]
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])
					if(dx<=1 and dy<=1):						
						if grid_path_array[i]>=int(num_lines) and not removed_grid_path_array_flag:
							print("&&&")
							continue
						if grid_path_array[i]>=int(num_lines) and removed_grid_path_array_flag:
							removed_grid_path_array_start_val[i]+=1
							print("removed_grid_path_array_start_val",removed_grid_path_array_start_val)
							
						else:
							grid_path_array[i]+=1
							print("grid_path_array",grid_path_array)				
					cmd.exec(b)											
					elapsed_time = time.time() - search_start_time
					if master_flag:
						if pop_flag_arr[i]==1:							
							lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
						if i < len(robots):
						    robots[i] = (b.x , b.y)
						msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
						
				covered_points=0
				for h in grid_path_array:
					covered_points+=h
					if(percentage>98):
						pass
					else:
						percentage=100*(covered_points/((num_lines)*len(vehicles)))
				message_count+=1				
				if(message_count%30)==0:										
					if master_flag:								
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					grid_path_array_str = json.dumps(grid_path_array)
					msg=(str('search')+','+str(percentage)+','+str(elapsed_time)+','+grid_path_array_str)
					if master_flag:
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
				s.time_elapsed += 1   
					
				if(index==b"stop"):
					search_flag=False
					for i in range(3):
						sent = graph_socket.sendto(str("stop").encode(), graph_server_address)		
					if(same_alt_flag):
						return_height_flag=False						
					else:
						if start_return_csv_flag:
							return_height_flag=True						
					break
		
					
		if(landing_flag) or data==b"return":
			if master_flag:
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))						
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
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
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )

			index="data"
			sent = graph_socket.sendto(str("return loiter ").encode(), graph_server_address)				
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			multiple_goals=circle_formation_goals
			for b in s.swarm:										
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				ind=[0]*num_bots
				while 1:					
					if(landing_flag):
					    landing_flag=False
					    break					
					if(num_bots==10):
						time.sleep(0.1)
					elif(num_bots==9):
						time.sleep(0.1)
					elif(num_bots==8):
						time.sleep(0.11)
					elif(num_bots==7):
						time.sleep(0.11)
					elif(num_bots==6):
						time.sleep(0.12)
					elif(num_bots==5):
						time.sleep(0.12)
					elif(num_bots==4):
						time.sleep(0.123)
					elif(num_bots==3):
						time.sleep(0.125)
					elif(num_bots==2):
						time.sleep(0.13)
					elif(num_bots==1):
						time.sleep(0.13)
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]	
						
						cmd =cvg.goal_area_cvg(i,b,goal)
						cmd+= disp_field(b,neighbourhood_radius=50)
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
							if i < len(robots):
							    robots[i] = (b.x , b.y)
							msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
							
						if master_flag:						
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						circle_formation_flag=False		
						break
	
												
		if(data.startswith(b"home")) or (home_flag):
			print("JJJJ")
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			print(decoded_index,"MMM")
			f = decoded_index[0:4]  # First coordinate pair
			print(f,"@@@")
			return_array = decoded_index[5:]  # All other coordinates
			print('return_array',return_array)
			return_latlon = json.loads(return_array)
			return_xy=[]
			print(type(return_latlon),"&&&&")
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
				    # Process the lat and lon as needed
				    #print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    #print("x,y",x/2,y/2)
				    uav_home_pos.append((x / 2, y / 2))
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
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
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
				home_flag=True
				sent = graph_socket.sendto(str("home").encode(), graph_server_address)				
			bot_array_home=[0]*num_bots
			all_bot_reach_flag_home=False
			index="data"
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
				if(home_flag1):
					home_flag=False				
					for i,x in enumerate(s.swarm):
						print(i)
						vehicles[i].mode = VehicleMode("RTL")
						print('vehicle',vehicles[i],i,'rtl')
					break
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				for i,b in enumerate(s.swarm):
					current_position = [b.x,b.y]
					goal=return_xy[return_ind]
					cmd =cvg.goal_area_cvg(i,b,goal)
					#Execute
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
						with open(csv_path, 'a') as csvfile:
							fieldnames = ['waypoint']
							writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
							writer.writerow({'waypoint':-1})	
						home_flag1=True
						home_flag=False
						break
							
					if master_flag:										
						current_position = [b.x*2,b.y*2]
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						point1 = LocationGlobalRelative(lat,lon,home_height[i])
						vehicles[i].simple_goto(point1)
					if i < len(robots):
						    robots[i] = (b.x , b.y)
					msg = ','.join([f"{robot[0]},{robot[1]}" for robot in robots])		       
															       
				if master_flag:			
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
				if(index==b"stop"):
					for i in range(3):
						sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
					home_flag1=True
					home_flag=False
					
		if(home_flag1):
		    print("END")
		    break
	except:
		if(disperse_flag):	
			disperse_flag=False
		if(search_flag):
			search_flag=False
		if(return_flag):
			return_flag=False
		if(start_flag):
			start_flag=False
		if(circle_formation_flag):
			circle_formation_flag=False
		if(home_flag):
			home_flag=False
		if(home_goto_flag):
			home_goto_flag=False
		pass				
