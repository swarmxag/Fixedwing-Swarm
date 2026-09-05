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
from dronekit import connect, VehicleMode, LocationGlobalRelative
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
graph_server_address = ('192.168.29.69', 12009)  #receive from .....rx.py

remove_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

file_name=""

vehicles=[]
global_path_csv=[]
num_bots=10
pos_array=[0]*num_bots
global_uavs=[0]*num_bots
global_heartbeat=[0]*num_bots
slave_heal_ip=[0]*num_bots
master_table=[0]*num_bots
p_address=['192.168.29.152','192.168.29.151','192.168.29.153']
p_socket=[]
processor_server_address=[]
all_xy=[0]*10
master_ip=p_address[0]
master_table[0]=1
master_flag=False 
linkdown_flag=False
master_path=[]
if(master_ip=='192.168.29.151'):
	master_flag=True
	print("master_ip,master_table",master_ip,master_table,master_flag)	
master_num=1
change_master_flag=False
p_sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
p_server_address1 = ('192.168.29.151', 12015)  #receive from .....rx.py

p_sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
p_server_address2 = ('192.168.29.152', 12015)  #receive from .....rx.py
p_sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
p_server_address3 = ('192.168.29.153', 12015)  #receive from .....rx.py

disperse_multiple_goals=[]
goal_points=[]
agg_goal_point=[]
origin=[]
area_covered_percent=0
position=[]
home_position=[]
if(file_name=="Tambaram_airport"):
	origin=(  12.898623, 80.113572)
	goal_points=[ (415.55493438625564,456.51735869880645), (83.48744302662308,101.11535740333234), (226.0971604993888,244.04267706836725), (136.51502429278077,558.9285689733798), (261.3148828764992,547.2445918621977), (464.04383674010165,595.2929068098884), (563.7374435516844,618.4580193887477), (886.6281372464044,191.49529501331313), (626.7329941104032,337.6688861035689), (454.8685837758423,495.1852817532512), (451.5043231762099,372.4179270857997), (607.4623794307759,284.5931240445683), (894.4390416274568,125.91201735517623), (562.0346303502632,520.6877743618948), (236.8430237814994,501.74563655736), (192.10840232012194,123.04275266307708), (331.4831385385884,271.46973276106223), (374.21119553304294,505.8049307660936),]
	disperse_multiple_goals=[ (83.48744302662308,101.11535740333234), (226.0971604993888,244.04267706836725), (136.51502429278077,558.9285689733798), (261.3148828764992,547.2445918621977), (464.04383674010165,595.2929068098884), (563.7374435516844,618.4580193887477), (886.6281372464044,191.49529501331313), (626.7329941104032,337.6688861035689), (454.8685837758423,495.1852817532512),(451.5043231762099,372.4179270857997),]
	agg_goal_point=[415.55493438625564,456.51735869880645]
	area_covered_percent=67
	
if(file_name=="Tambaram_runway"):
	 origin=(  12.898623, 80.113572)

	 goal_points=[(185.95668989890575,580.615934042732), (314.9059293398766,509.0896752141942), (82.92808854687563,99.58233082538148), (191.0971623241269,213.25552727004242), (358.82522854635977,394.6546267756296), (449.06902885889286,490.5114371911169), (534.1464105396387,584.4680928613654), (541.7522071541887,384.13450136678097), (701.302608361422,291.91674355314655), (917.7195646637302,173.31541999078996),]
	 disperse_multiple_goals=[ (185.95668989890575,580.615934042732), (314.9059293398766,509.0896752141942), (82.92808854687563,99.58233082538148), (191.0971623241269,213.25552727004242), (358.82522854635977,394.6546267756296), (449.06902885889286,490.5114371911169), (534.1464105396387,584.4680928613654), (541.7522071541887,384.13450136678097), (701.302608361422,291.91674355314655), (917.7195646637302,173.31541999078996),
 ]
	 agg_goal_point=[415.55493438625564,456.51735869880645]	
	 area_covered_percent=67
	 
if(file_name=="dce_airport"):
	origin=(12.924801, 80.042719)#dce

	goal_points=[ (179.40550274627913,308.15386473749555), (170.99513572947805,289.35827568680276), (168.86005545367016,278.07166026184615), (196.9510938076667,266.3208209010031), (221.81169795738273,255.76690549382712), (141.36847098185353,246.6297974398802), (159.12810083196678,241.36795466086144), (165.17736445453224,255.9836791630281), (172.83867941495768,274.7264309925827), (221.20009527209496,256.0336190545783), (182.32709847774157,232.5208029351906), (207.48096771410658,224.8346429075841), (211.9462937186256,237.44651100896382), (264.87664269879014,206.67858540983394), (277.8934118507254,235.80815686557324), (298.4555948189716,230.78146926893683), (293.17787532288014,273.5376866780221), (240.41019857324855,302.7874959996908), (188.6930646784506,245.50582780455525), (230.1665459467102,218.5718998451968), (123.06874511896862,243.5163968586071), (139.11279072454997,286.02406938652103), (160.29300426583518,342.7190679601935), (186.27125160742494,330.61502836178624),]
	disperse_multiple_goals=[]
	agg_goal_point=(221.81169795738273,255.76690549382712)	 
	start_multiple_goals=[(157.64131776911836,209.16847386901821), (360.12460897774656,143.7605934973306), (581.468738086984,77.37929794272104),  (599.2505498180748,112.92467247032282),  (602.6444203564429,153.256210887913), (508.0359474466252,199.22290470278386),  (356.44627567858686,213.57908756056852), (290.83411085872586,223.81593558812182), (221.81169795738273,255.76690549382712)]
	return_multiple_goals=[(157.64131776911836,209.16847386901821), (360.12460897774656,143.7605934973306), (581.468738086984,77.37929794272104),  (599.2505498180748,112.92467247032282),  (602.6444203564429,153.256210887913), (508.0359474466252,199.22290470278386),(356.44627567858686,213.57908756056852), (290.65645997127996,232.81715396747316), (221.81169795738273,255.76690549382712),]
	area_covered_percent=67
	
csv_file_path = "/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/uav_data_log.csv" 
csv_file_path1 = "/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/waypoints.csv" 
nextwaypoint=0
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('192.168.29.69', 12005)  #receive from .....rx.py


sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address2 = ('', 12008)  #receive from .....rx.py
sock2.bind(server_address2)
sock2.setblocking(0)

sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address3 = ('', 12002)  #receive from .....rx.py
sock3.bind(server_address3)

# Bind the socket to the port
remove_bot_server_address = ('192.168.29.69', 12001)  #receive from .....rx.py

sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address4 = ('', 12011)  #receive from .....rx.py
sock.bind(server_address4)

print("file_name",file_name)
while file_name=="":
	try:
		data,address=file_sock.recvfrom(12003)
		print("data",data)
		decoded_index = data.decode('utf-8') 
		print("decoded_index",decoded_index)
		graph_socket.sendto(str(decoded_index).encode(), graph_server_address)	
		file_name=decoded_index
	except:
		pass

xy_sock_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
xy_sock_receiver_port = ('', 12015)  
xy_sock_receiver.bind(xy_sock_receiver_port)	
xy_sock_receiver.setblocking(0)
def receive_xy():
	while 1:
		try:
			print("XXXXXXXXXXXXXXXXXX")
			xy_sock_receiver.settimeout(1)  # Timeout of  	
			xy, address = xy_sock_receiver.recvfrom(1050)
			print("data",xy)
			decoded_index = xy.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			print("decoded_index",decoded_index)
			x,y= decoded_index.split(",")
			print("x,y",float(x),float(y))
			lat,lon = locatePosition.cartToGeo (origin, endDistance, (float(x),float(y)))			
			if same_alt_flag:
				point1 = LocationGlobalRelative(lat,lon,same_height)
			else:
				point1 = LocationGlobalRelative(lat,lon,different_height[i])
			print("point1",point1)
			vehicle1.simple_goto(point1)
			print("!!!!!!!!!!!!!!!5555555")
			if(xy==""):
				print("JJJJJJJJ")			
				break
			return 1
		except:
			pass
			
uav1_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav1_server_address = ('192.168.29.151', 12021)

uav2_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav2_server_address = ('192.168.29.152', 12021)

uav3_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav3_server_address = ('192.168.29.153', 12021)

gggggg=0
all_xy=[0]*num_bots
# Bi nd the socket to the port
uav_receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav_receiver_server_address = ('', 12021)  #receive from .....rx.py
uav_receiver_sock.bind(uav_receiver_server_address)
uav_receiver_sock.setblocking(0)

share_path_sock1=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_path_sock1_server_address = ('192.168.29.151', 12031)

share_path_sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_path_sock2_server_address = ('192.168.29.152', 12031)

share_path_sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_path_sock3_server_address = ('192.168.29.153', 12031)
				

num_bots=0
vehicles=[]
pos_array=[]
#heartbeat_ip=["192.168.6.101","192.168.6.102","192.168.6.103","192.168.6.104","192.168.6.105","192.168.6.106","192.168.6.107","192.168.6.108","192.168.6.109","192.168.6.110"]*10
heartbeat_ip=["192.168.29.125"]*10
heartbeat_ip_timeout=[0]*10

share_path_sock_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_path_sock_receiver_server_address = ('', 12031)  #receive from .....rx.py
share_path_sock_receiver.bind(share_path_sock_receiver_server_address)
share_path_sock_receiver.setblocking(0)

try:	
	vehicle1= connect('udpin:192.168.29.151:14551',baud=115200, heartbeat_timeout=30)
	vehicle1.airspeed = 12
	print('Drone1')
	vehicles.append(vehicle1)
	print("vehicles",vehicles)
	pos_array.append(1)
	num_bots+=1
	print(global_uavs,"global_uavs")

except:	
	pass
	print(	"Vehicle 1 is lost")

def share_path_csv_receive():
	global global_path_csv
	print("NNNNNNNNNNNNN",global_path_csv)
	while 1:
		try:
			v,address=share_path_sock_receiver.recvfrom(1024)
			print("dataVVVVVVVVVV",v)
			decoded_index = v.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			print("decoded_indexVVVVVVVVVVVVVVVVV",decoded_index,type(decoded_index))
			#path = decoded_index.split(",")
			#print("path",path)
			#if int(decoded_index) not in global_path_csv:
			print("BBBBBBBBBBBBB")
			global_path_csv.append(int(decoded_index))
			print("global_path_csv",global_path_csv) 
			return decoded_index	
		except:
			pass

share_path_csv_receive_thread = threading.Thread(target=share_path_csv_receive)
share_path_csv_receive_thread.daemon = True
share_path_csv_receive_thread.start()
"""	
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
	    	#master_ip="192.168.29.152"
	    	#slave_heal_ip[i] = 'nolink'    	    	
	    	heartbeat_ip_timeout[i]=3
    print(" heartbeat_ip_timeout",heartbeat_ip_timeout)
CHECK_network_connection()
"""
def CHECK_network_connection():
    global slave_heal_ip
    global vehicles,linkdown_flag    	    	 	    	
    global lost_vehicle_num
    global vehicle_lost_flag
    global master_num
    global change_master_flag,master_ip,master_flag
    while 1:
    	    try:
    	    	data, address = sock2.recvfrom(1050)
    	    	print("FFFFFFFFFFFF",data)
    	    	break
    	    except:
    	    	time.sleep(15)    	  
    	    	print("master_ip",master_table,master_ip,p_address,type(master_ip))
    	    	response = os.system('ping -c 1 ' + master_ip)
    	    	if response==0:
    	    		pass
    	    	else:
    	    		print ("link is down")
    	    		linkdown_flag=True    	    	 	    	
    	    		master_table[master_num]=1       
    	    		master_table[master_num-1]=2
    	    		master_ip=p_address[master_num]
    	    		print("master_ip!!!!!!!!!!!!",master_ip)
    	    		master_num=master_num+1   
    	    		print("master_table,master_num",master_table, master_num)       
    	    		if(master_table[0]==1): 
	    	    		print("$$$$$$$$$$$$$$$",master_flag)   	
	    	    		master_flag=True    			    	    	
    	    		l=linkdown_uav_remove()     
    	    		position=[]
    	    		for i,vehicle in enumerate(vehicles):
	    	    		lat = vehicle.location.global_relative_frame.lat
	    	    		lon = vehicle.location.global_relative_frame.lon

			       # Process the lat and lon as needed
		    	    	print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
		    	    	current_lat_lon.append((lat,lon))			    
		    	    	x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
		    	    	print("x,y",x/2,y/2)
		    	    	position.append((x / 2, y / 2))
		    	    	print(position,"position",position[0][0],position[0][1])
		    	    	uav_home_pos[0]=(x / 2, y / 2)

	    	    	#share_data()
    	    		data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_pos[0][0])+" , "+str(home_pos[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
    	    		print(data,"data")	
				
    	    		print(home_pos,uav_home_pos,"home_pos,uav_home_pos")
				
    	    		for i in range(12):
    	    			time.sleep(0.1)			
    	    			sent = uav1_sock.sendto(data.encode(), uav1_server_address)
    	    			time.sleep(0.1)
    	    			sent = uav2_sock.sendto(data.encode(), uav2_server_address)
    	    			time.sleep(0.1)
    	    			sent = uav3_sock.sendto(data.encode(), uav3_server_address)  
    	    			
    	    			#receive_xy()  	    	  
    	    		with open(r'/home/dhaksha/Desktop/decentralized/uav1/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv', 'w') as csvfile:
	    	    		fieldnames = ['waypoint']
	    	    		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	    	    		writer.writerow({'waypoint':-1})
	    	    		for g in global_path_csv:
	    	    			print("Arrray global_paath_csv",g)
	    	    			writer.writerow({'waypoint':g})
	    	    	#break	  		

check_network_thread=threading.Thread(target=CHECK_network_connection)
check_network_thread.daemon=True
check_network_thread.start()	
print(len(vehicles))

def uav_data_receive():
	global index
	global vehicles
	global slave_heal_ip
	global uav_home_pos
	global home_pos
	while 1:
		#print("^^^^^^^^^^^^")
		try:
			xy, address = uav_receiver_sock.recvfrom(1050)
			print("data",data)
			decoded_index = xy.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			print("decoded_index",decoded_index)
			uav,uav_num,add,home_pos_x,home_pos_y,uav_pos_x,uav_pos_y = decoded_index.split(",")
			print("uav,ip",uav,uav_num,add,home_pos_x,home_pos_y,uav_pos_x,uav_pos_y )
			global_uavs[int(uav_num)-1]=1
			global_heartbeat[int(uav_num)-1]=1
			slave_heal_ip[int(uav_num)-1]=add
			print("len(home_pos)",len(home_pos),len(uav_home_pos))
			home_pos[int(uav_num)-1]=(float(home_pos_x),float(home_pos_y))
			uav_home_pos[int(uav_num)-1]=(float(uav_pos_x),float(uav_pos_y))
			print("KKKKK",float(home_pos_x),float(home_pos_y),(float(uav_pos_x),float(uav_pos_y)))
			print("home_pos",home_pos)
			print("uav_home_pos",uav_home_pos)
			print("global_uavs",global_uavs,uav2_server_address[0],type(uav2_server_address[0]),"global_heartbeat",global_heartbeat)
			# Close the client socket
			'''
			if(start_flag):
				s = sim.Simulation(uav_home_pos,num_bots=num_uavs, env_name='rectangles' )
			if(search_flag):
				s = sim.Simulation(uav_home_pos,num_bots=num_uavs, env_name='rectangles1' )
			if(return_flag):
				s = sim.Simulation(uav_home_pos,num_bots=num_uavs, env_name='rectangles2' )
			'''
		except:
			pass
uav_data_receive_thread = threading.Thread(target=uav_data_receive)
uav_data_receive_thread.daemon = True
uav_data_receive_thread.start()

def linkdown_uav_remove():
	global pop_bot_index,master_num,master_table,same_alt_flag,global_heartbeat
	global num_uavs,remove_flag,uav_removed,different_height,all_xy,global_uavs
	pop_bot_index=master_table[master_num-2]
	s.remove_bot(pop_bot_index)
	print(num_uavs)	
	print("*****")
	sent = remove_socket.sendto(str(pop_bot_index).encode(), remove_bot_server_address)
	print("pop index",pop_bot_index)
	global_uavs[pop_bot_index]=0
	global_heartbeat[pop_bot_index]=0
	same_alt_flag=False
	remove_flag=False
	uav_removed=True
	while True:
		for i, b in enumerate(s.swarm):
			cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
			cmd.exec(b)
			all_xy[i]=[b.x*2,b.y*2]
			print("all_xy",all_xy)
			if(master_flag):	
				print("CCCCCCCCCCCCCCCC")	
					       
				if(len(s.swarm)-1==i):
					try:
						s1=str(all_xy[0][0])+","+str(all_xy[0][1])
					except:
						pass
					try:
						s2=str(all_xy[1][0])+","+str(all_xy[1][1])
					except:
						pass
					try:
						s3=str(all_xy[2][0])+","+str(all_xy[2][1])
					except:
						pass
					#s=1
					print(s1,s2,"s")
					
					try:
						p_sock1.sendto(str(s1).encode(), p_server_address1)
					except:
						pass
					try:
						p_sock2.sendto(str(s2).encode(), p_server_address2)
					except:
						pass
					try:							
						p_sock3.sendto(str(s3).encode(), p_server_address3)
					except:
						pass
					a=receive_xy()							
					
			else:
				a=receive_xy()					
				print("$$$$$$$$$$$$$$$$")
			alt=0
			alt_count=0
			print("alt_count",alt_count)
			#for i,vehicle in enumerate(vehicles):
			print("vehicle",vehicle,num_uavs)
			alt=vehicle2.location.global_relative_frame.alt 
			#print("alt[vehicle]",alt[i])											
			if different_height[1] - 1.5 <= alt <= different_height[1]+1.5:
				alt_count=1
				print(alt_count,"alt_count")					
				print("Reached target altitude")
				return pop_bot_index

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

#z=len(vehicles)
#initial=str(z)+" Drones connected . Ready for takeoff"
#sent = graph_socket.sendto(str(initial).encode(), graph_server_address)
#num_bots=10
count=0

endDistance=8000
same_height=30
different_height=[30,31,32,33,34,35,36,37,38,39]
#search_height=[15,18,21,24,27]
home_pos=[]
home_pos_lat_lon=[]
#vehicles = [globals()[f'vehicle{i}'] for i in range(1, num_bots+1)]
print(vehicles)
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
# Iterate over the list of vehicles
robot1_x,robot1_y = 0,0
robot2_x,robot2_y = 0,0
robot3_x,robot3_y = 0,0
robot4_x,robot4_y = 0,0
robot5_x,robot5_y = 0,0
robot6_x,robot6_y = 0,0
robot7_x,robot7_y = 0,0
robot8_x,robot8_y = 0,0
robot9_x,robot9_y = 0,0
robot10_x,robot10_y = 0,0
robot11_x,robot11_y = 0,0
robot12_x,robot12_y = 0,0
robot13_x,robot13_y = 0,0
robot14_x,robot14_y = 0,0
robot15_x,robot15_y = 0,0
robot16_x,robot16_y = 0,0

slave_heal_ip=["192.168.29.125"]*len(vehicles)
heartbeat=[0]*len(vehicles)

vehicle_uav_heartbeat_flag=False
disperse_flag=False

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address1 = ('192.168.29.69', 12010)
slave_heal_ip=["192.168.29.125"]*len(vehicles)

def vehicle_collision_moniter_receive():	
        global index
        global vehicles
        global slave_heal_ip
        while 1:
        	index, address = sock3.recvfrom(1024)
        	print ("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", index)
		#vehicle_uav_heartbeat_flag=True
	
 			
collision_thread = threading.Thread(target=vehicle_collision_moniter_receive)
collision_thread.daemon=True
collision_thread.start()
           

robot_positions = [([0, 0]) for _ in range(20)]
print("origin#########",origin)
for i,vehicle in enumerate(vehicles):
    print("@@@@@@@@@@@")
    
    
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    home = vehicle.home_location
    
    print(home.lat,home.lon)
    while home.lat is None:
        print(" Waiting for home position...")
        time.sleep(1)
    # Process the lat and lon as needed
    print(f"Vehicle - Latitude: {home.lat}, Longitude: {home.lon}")
    x,y = locatePosition.geoToCart (origin, endDistance, [home.lat,home.lon])
    home_pos_lat_lon.append((home.lat,home.lon))
    print("x,y",x/2,y/2)
    home_pos.append((x / 2, y / 2))
    print("x,y",x/2,y/2)
    home_position.append((x / 2, y / 2))
    home_pos[0]=(x / 2, y / 2)
    if i==0:
    	robot1_x,robot1_y={x/2},{y/2}
    elif i==1:
    	robot2_x,robot2_y={x/2},{y/2}
    elif i==2:
    	robot3_x,robot3_y={x/2},{y/2}
    elif i==3:
    	robot4_x,robot4_y={x/2},{y/2}
    elif i==4:
    	robot5_x,robot5_y={x/2},{y/2}
    elif i==5:
    	robot6_x,robot6_y={x/2},{y/2}
    elif i==6:
    	robot7_x,robot7_y={x/2},{y/2}
    elif i==7:
    	robot8_x,robot8_y={x/2},{y/2}	
    elif i==8:
    	robot9_x,robot9_y={x/2},{y/2}
    elif i==9:
    	robot10_x,robot10_y={x/2},{y/2}
    elif i==10:
    	robot11_x,robot11_y={x/2},{y/2}
    elif i==11:
    	robot12_x,robot12_y={x/2},{y/2}
    elif i==12:
    	robot13_x,robot13_y={x/2},{y/2}
    elif i==13:
    	robot14_x,robot14_y={x/2},{y/2}
    elif i==14:
    	robot15_x,robot15_y={x/2},{y/2}
    elif i==15:
    	robot16_x,robot16_y={x/2},{y/2}
    else:
	    print('invalid')
    msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
    	str(robot2_x) + ',' + str(robot2_y) + ',' +
	str(robot3_x) + ',' + str(robot3_y) + ',' +
	str(robot4_x) + ',' + str(robot4_y) + ',' +
	str(robot5_x) + ',' + str(robot5_y) + ',' +
	str(robot6_x) + ',' + str(robot6_y) + ',' +
	str(robot7_x) + ',' + str(robot7_y) + ',' +
	str(robot8_x) + ',' + str(robot8_y) + ',' +
	str(robot9_x) + ',' + str(robot9_y) + ',' +
	str(robot10_x) + ',' + str(robot10_y))
			       
    print("msg",msg) 
serialized_data = json.dumps(home_pos)
serialized_data="home_pos" + serialized_data
sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
print("JJJJJJJJJJJ")

serialized_goal_data = json.dumps(goal_points)
serialized_goal_data="goal_points" + serialized_goal_data
print("serialized_goal_data",serialized_goal_data)
sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

for i,vehicle in enumerate(vehicles):
    lat = vehicle.location.global_relative_frame.lat
    lon = vehicle.location.global_relative_frame.lon

       # Process the lat and lon as needed
    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
    current_lat_lon.append((lat,lon))			    
    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
    print("x,y",x/2,y/2)
    position.append((x / 2, y / 2))
    print(position,"position",position[0][0],position[0][1])
    uav_home_pos[0]=(x / 2, y / 2)
    if i==0:
    	robot1_x,robot1_y={x/2},{y/2}
    elif i==1:
    	robot2_x,robot2_y={x/2},{y/2}
    elif i==2:
    	robot3_x,robot3_y={x/2},{y/2}
    elif i==3:
    	robot4_x,robot4_y={x/2},{y/2}
    elif i==4:
    	robot5_x,robot5_y={x/2},{y/2}
    elif i==5:
    	robot6_x,robot6_y={x/2},{y/2}
    elif i==6:
    	robot7_x,robot7_y={x/2},{y/2}
    elif i==7:
    	robot8_x,robot8_y={x/2},{y/2}	
    elif i==8:
    	robot9_x,robot9_y={x/2},{y/2}
    elif i==9:
    	robot10_x,robot10_y={x/2},{y/2}
    elif i==10:
    	robot11_x,robot11_y={x/2},{y/2}
    elif i==11:
    	robot12_x,robot12_y={x/2},{y/2}
    elif i==12:
    	robot13_x,robot13_y={x/2},{y/2}
    elif i==13:
    	robot14_x,robot14_y={x/2},{y/2}
    elif i==14:
    	robot15_x,robot15_y={x/2},{y/2}
    elif i==15:
    	robot16_x,robot16_y={x/2},{y/2}
    else:
	    print('invalid')
    msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
    	str(robot2_x) + ',' + str(robot2_y) + ',' +
	str(robot3_x) + ',' + str(robot3_y) + ',' +
	str(robot4_x) + ',' + str(robot4_y) + ',' +
	str(robot5_x) + ',' + str(robot5_y) + ',' +
	str(robot6_x) + ',' + str(robot6_y) + ',' +
	str(robot7_x) + ',' + str(robot7_y) + ',' +
	str(robot8_x) + ',' + str(robot8_y) + ',' +
	str(robot9_x) + ',' + str(robot9_y) + ',' +
	str(robot10_x) + ',' + str(robot10_y))
    print("msg..",msg)
sent = graph_socket.sendto(str(msg).encode(), graph_server_address)

area_covered = 0
start_time = time.time()
visited_positions = set()
data=""
same_alt_flag=True
elapsed_time= time.time() - start_time


index=0
flag_stop=False
return_flag=False
aggregate_flag=False
pop_flag_arr=[1]*len(vehicles)
pop_flag=False
specific_bot_goal_flag=False
pop_bot_index=None
goal_bot_num=None
start_flag=False
circle_formation_flag=False
radius_of_earth = 6378100.0 # in meters
uav_home_flag=False
remove_flag=False
group_goal_flag=False
home_counter=0
circle_formation_count=0
uav_removed=True
#Initialize Simulation and GUI 
s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=file_name)
#gui = viz.Gui(s)
#gui.show_env()

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
	print("!!!!!remove flag enabled",pos_array)
	
	#if(vehicle_lost_flag):
	print("vehicle_lost_flag",vehicle_lost_flag,lost_vehicle_num,pos_array)
	index=pos_array[lost_vehicle_num-1]
	print(index,"index")
	print("lost_vehicle_num",lost_vehicle_num,index,pos_array)
	vehicle_lost_flag=False
	pop_flag=True
	#print ("msg", index)
	for l in range(0,len(vehicles)):
		print("^^^^^^^")	
		if(int(index)==pos_array[l]):
			pop_bot_index=l
			print("pop_bot_index,l",pop_bot_index,l)
			break

	print("hhhhhhhhh",pop_bot_index)
	pos_array.pop(pop_bot_index)
	print(len(pos_array))

	print("11111111111111111111",pop_bot_index)
	#pop_bot_index=	pop_bot_index
	#print(pop_bot_index)
	print(vehicles)
	#vehicles.pop(f'vehicle{pop_bot_index}')
	vehicles.pop(pop_bot_index)
	#vehicles.pop(pop_bot_index)
	print("555555555555",vehicles)
	#num_bots-=1
	#pop_bot_index=	pop_bot_index-1		
	s.remove_bot(pop_bot_index)
	print(len(vehicles))
	print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!",pop_flag_arr)
	#for i in range(3):
	print("*************")
	sent = remove_socket.sendto(str(pop_bot_index).encode(), remove_bot_server_address)
	print("pop index",pop_bot_index)
	same_alt_flag=False
	
	
	uav_home_pos=[]
	for i,vehicle in enumerate(vehicles):
	    lat = vehicle.location.global_relative_frame.lat
	    lon = vehicle.location.global_relative_frame.lon
	     
	    # Process the lat and lon as needed
	    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
	    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
	    print("x,y",x/2,y/2)
	    different_height[i]=different_height[i]+2
	    uav_home_pos.append((x / 2, y / 2))						
	print("uav_home_pos",uav_home_pos)    
	remove_flag=False
	uav_removed=True
	while True:
		for i, b in enumerate(s.swarm):
			cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
			cmd.exec(b)
			value=[b.x*2,b.y*2]												

			print("Drone 1 position",b.x,b.y)
			lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
			
			if same_alt_flag:
				point1 = LocationGlobalRelative(lat,lon,same_height)
			else:
				point1 = LocationGlobalRelative(lat,lon,different_height[i])
			print("point1",point1)
			vehicles[i].simple_goto(point1)
			print("$$$$$$$$$$$$$$$$")

			alt=[0]*len(vehicles)
			alt_count=[0]*len(vehicles)

			print("alt_count",alt_count)
			for i,vehicle in enumerate(vehicles):
				print("vehicle",vehicle,len(vehicles))
				alt[i]=vehicle.location.global_relative_frame.alt 
				print("alt[vehicle]",alt[i])											
				if different_height[i] - 1.5 <= alt[i] <= different_height[i]+1.5:
					alt_count[i]=1
					print(alt_count,"alt_count")
					if all(count==1 for count in alt_count):		
						print("Reached target altitude")
						return index
	#return index
vehicles_thread=[]
while(1):
	try:            
		data, address = sock2.recvfrom(1050)
		print ("msg", data)
		if(data==b"store_uav_pos"):
			if os.path.exists(csv_file_path):
    				os.remove(csv_file_path)
			
			with open(csv_file_path, mode='w', newline='') as csv_file:
				csv_writer = csv.writer(csv_file)
				csv_writer.writerow(['X', 'Y'])  # Write header
				csv_writer.writerows(home_pos)
				csv_file.close()
		if(data==b"share_data"):
			data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_pos[0][0])+" , "+str(home_pos[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
			print(data,"data")	
			
			print(home_pos,uav_home_pos,"home_pos,uav_home_pos")
			
			for i in range(6):
				time.sleep(0.1)			
				sent = uav1_sock.sendto(data.encode(), uav1_server_address)
				time.sleep(0.1)
				sent = uav2_sock.sendto(data.encode(), uav2_server_address)
				time.sleep(0.1)
				sent = uav3_sock.sendto(data.encode(), uav3_server_address)
				#sent = uav4_sock.sendto(data.encode(), uav4_server_address)
				#sent = uav5_sock.sendto(data.encode(), uav5_server_address)
				#receive_xy()
			
			
			num_uavs=global_uavs.count(1)
			print(num_uavs,home_pos,uav_home_pos,"num_uavs,home_pos,uav_home_pos")	
		if(data==b"takeoff"):
			print("@@@@@@@@@@@@@")
			
			thread = threading.Thread(target=arm_and_takeoff, args=(vehicle1, 30))					
			thread.start()

			# Wait for all vehicles_thread to finish
			
			thread.join()
		if(data==b"simulate"):
			
			num_uavs=global_uavs.count(1)
			heartbeat=[0]*num_uavs
			pop_flag_arr=[1]*num_uavs	
			print(num_uavs,"num_uavs")
			s = sim.Simulation(uav_home_pos,num_bots=num_uavs, env_name=file_name)
			

		if(data==b"rtl"):			
			print("rtl!!!!!!!!!!!!!!!!")
			vehicle1.mode = VehicleMode("RTL")
			vehicle1.close()				
			break
				
		if(data==b"land"):			
			print("land!!!!!!!!!!!!!!!!")
			for i,b in enumerate(s.swarm):
				if(pop_flag_arr[i]==0):
					i+=1	
				vehicles[i].mode = VehicleMode("LAND")
				vehicles[i].close()		
			break
					
		if(data==b"remove") or (remove_flag):	
				'''
				for l in range(0,num_bots):
					pos_array.append(l+1)
				'''
				print("lost_vehicle_num",lost_vehicle_num,index,pos_array)
				#index=9
				#pos_array.pop(4)
				#num_bots-=1		
				pop_flag=True
				print ("msg", index)
				for l in range(0,len(vehicles)):	
					if(int(index)==pos_array[l]):
						pop_bot_index=l
						print(l)
						break
				#pop_bot_index=int(index)
				print(pop_bot_index)
				pos_array.pop(pop_bot_index)
				print(len(pos_array))
				'''
				for l,key in enumerate(test_dict.keys()):
					print("Key:", key, "Value:", test_dict[key])
					if(key==pop_bot_index):
						print(l)
						pop_bot_index=l
				'''
				print("11111111111111111111",pop_bot_index)
				#pop_bot_index=	pop_bot_index
				#print(pop_bot_index)
				print(vehicles)
				#vehicles.pop(f'vehicle{pop_bot_index}')
				vehicles.pop(pop_bot_index)
				#vehicles.pop(pop_bot_index)
				print("555555555555",vehicles)
				#num_bots-=1
				#pop_bot_index=	pop_bot_index-1		
				s.remove_bot(pop_bot_index)
				print(len(vehicles))
				print('2222222222222')
				#pop_flag_arr[pop_bot_index]=0
				#remove_count+=1
				
				print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!",pop_flag_arr)
				#for i in range(3):
				print("*************")
				sent = remove_socket.sendto(str(pop_bot_index).encode(), remove_bot_server_address)
				print("pop index",pop_bot_index)
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon

				    # Process the lat and lon as needed
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    print("x,y",x/2,y/2)
				    
				    uav_home_pos.append((x / 2, y / 2))						
				print("uav_home_pos",uav_home_pos)    
				remove_flag=False
				uav_removed=True
				print("exit@@@@@")
				
						
		if(data==b"add"):				
				bot_pos=[154.37296943770545 ,259.40487368680743]
				#print ("msg", index)
				#decoded_index = index.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				#bot_pos_x,bot_pos_y = decoded_index.split(",")
				#bot_pos=[float(str(bot_pos_x)),float(str(bot_pos_x))]
				if(pop_flag):
					bot_ind=pop_bot_index
				else:
					bot_ind=num_bots
				s.add_bot(bot_ind,bot_pos)
				#uav_home_pos.append((x / 2, y / 2))
				#uav_home_pos.append((bot_pos[0],bot_pos[1]))				
				uav_home_pos.insert(bot_ind,(bot_pos[0],bot_pos[1]))
				pop_flag=False
				pop_flag_arr[pop_bot_index]=1

		#if(data==b"specific_bot_goal"):	
		if data.startswith(b'specific_bot_goal'): 
				#global goal_points
				index="data"
				goal_pos=[0]*len(vehicles)
				specific_bot_goal_flag_array=[False]*len(vehicles)
				print("goal_pos",goal_pos,"specific_bot_goal_flag_array",specific_bot_goal_flag_array)	
				try:
					print("bot_goal!!!!!!!!!!!!")
					#index, address = sock3.recvfrom(1024)
					print("data",data)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					f,uav, goal_point_num = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav, goal_point_num)
					
					goal_position=goal_points[int(goal_point_num)-1]

					"""
					f,uav, goal_lat, goal_lon = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav, goal_lat, goal_lon)					
					goalx,goaly = locatePosition.geoToCart (origin, endDistance, goal_pos)
					
					print("x,y",goalx,goaly)
					"""
					goal_bot_num=int(str(uav))
					print(goal_bot_num)
					#goal_position=[float(goalx/2),float(goaly/2)]
					print(goal_position)
					goal_bot_num=goal_bot_num-1
					print(goal_bot_num,goal_pos[goal_bot_num])
					goal_pos[goal_bot_num]=goal_position
					print("goal_position",goal_pos,specific_bot_goal_flag_array)	
					print("goal_pos[goal_point_num]",goal_pos)				
					specific_bot_goal_flag_array[goal_bot_num]=True
					print("goal_position",goal_pos,specific_bot_goal_flag_array)
					#specific_bot_goal_flag=True
					while 1:						
						time.sleep(0.01)
						
						try:
							print("bot_goal!!!!!!!!!!!!")
							#index, address = sock3.recvfrom(1024)
							data, address = sock2.recvfrom(1050)
							print("data",data)
							if data.startswith(b'specific_bot_goal'): 
								decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
								f,uav, goal_point_num = decoded_index.split(",")
								#uav,goalx,goaly=str(index).split(",")
								print(uav, goal_point_num)
								
								goal_position=goal_points[int(goal_point_num)-1]	
								
								goal_bot_num=int(str(uav))
								print(goal_bot_num)
								#goal_position=[float(goalx/2),float(goaly/2)]
								print(goal_position)
								goal_bot_num=goal_bot_num-1
								print(goal_bot_num,goal_pos[goal_bot_num])
								goal_pos[goal_bot_num]=goal_position
								print("goal_position",goal_pos,specific_bot_goal_flag_array)	
								print("goal_pos[goal_point_num]",goal_pos)				
								specific_bot_goal_flag_array[goal_bot_num]=True
								print("goal_position",goal_pos,specific_bot_goal_flag_array)
								#specific_bot_goal_flag=True
						except:
							#pass
							
							if(specific_bot_goal_flag):
								specific_bot_goal_flag=False
								break	
									
							for i,b in enumerate(s.swarm):
								
								current_position=[b.x,b.y]	
								print("specific_bot_goal_flag_array",specific_bot_goal_flag_array,goal_pos)
								#if(i==goal_bot_num):	
								if(specific_bot_goal_flag_array[i]):							
									dx=abs(goal_pos[i][0]-current_position[0])
									dy=abs(goal_pos[i][1]-current_position[1])						
									print("dx,dy",dx,dy)
									if(dx<=5 and dy<=5):
										specific_bot_goal_flag_array[i]=False
										print("specific_bot_goal_flag_array",specific_bot_goal_flag_array)
									if all(flag==False for flag in specific_bot_goal_flag_array):							
										print("**************")
										specific_bot_goal_flag=True
										break					
									else:
										current_position = (b.x, b.y)						
										#if(i==goal_bot_num):								
										if(specific_bot_goal_flag_array[i]):	
											print("i",i)
											#print("final_goals[goal_bot_num-1]",final_goals)
											#goal_position = final_goals[goal_bot_num-1]
											#goal_position = [23,40]										
											b.set_goal(goal_pos[i][0], goal_pos[i][1])
											cmd = cvg.goal_area_cvg(i, b, goal_pos[i])								
											print("cmd11111 exceuted")
																			
											cmd.exec(b) 	
									
								#	print("bot_array",bot_array)
								#	print("current_position",current_position)	
								#	print("Drone 1 position",b.x,b.y)
									"""
									current_position = (b.x*2, b.y*2)						
									lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
									#print ("Drone 1 lat,lon", lat,lon)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									#print("point1",point1)
									vehicles[i].simple_goto(point1)
									"""
									all_xy[i] = [b.x*2,b.y*2]					
									if(master_flag):
										if(len(s.swarm)-1==i):
											try:
												s1=str(all_xy[0][0])+","+str(all_xy[0][1])
											except:
												pass
											try:
												s2=str(all_xy[1][0])+","+str(all_xy[1][1])
											except:
												pass
											try:
												s3=str(all_xy[2][0])+","+str(all_xy[2][1])
											except:
												pass
											#s=1
											print(s1,s2,"s")
											
											try:
												p_sock1.sendto(str(s1).encode(), p_server_address1)
											except:
												pass
											try:
												p_sock2.sendto(str(s2).encode(), p_server_address2)
											except:
												pass
											try:							
												p_sock3.sendto(str(s3).encode(), p_server_address3)
											except:
												pass
											a=receive_xy()							
												
										else:
											print("JJJJJJJJ")
											a=receive_xy()
									if i==0:
									    robot1_x,robot1_y={b.x},{b.y}
									elif i==1:
									    robot2_x,robot2_y={b.x},{b.y}
									elif i==2:
									    robot3_x,robot3_y={b.x},{b.y}
									elif i==3:
									    robot4_x,robot4_y={b.x},{b.y}
									elif i==4:
									    robot5_x,robot5_y={b.x},{b.y}
									elif i==5:
									    robot6_x,robot6_y={b.x},{b.y}
									elif i==6:
									    robot7_x,robot7_y={b.x},{b.y}
									elif i==7:
									    robot8_x,robot8_y={b.x},{b.y}
									elif i==8:
									    robot9_x,robot9_y={b.x},{b.y}
									elif i==9:
									    robot10_x,robot10_y={b.x},{b.y}
									elif i==10:
									    robot11_x,robot11_y={b.x},{b.y}
									elif i==11:
									    robot12_x,robot12_y={b.x},{b.y}
									elif i==12:
									    robot13_x,robot13_y={b.x},{b.y}
									elif i==13:
									    robot14_x,robot14_y={b.x},{b.y}
									elif i==14:
									    robot15_x,robot15_y={b.x},{b.y}
									elif i==15:
									    robot16_x,robot16_y={b.x},{b.y}
									else:
									    print('invalid')
									msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
								       str(robot2_x) + ',' + str(robot2_y) + ',' +
								       str(robot3_x) + ',' + str(robot3_y) + ',' +
								       str(robot4_x) + ',' + str(robot4_y) + ',' +
								       str(robot5_x) + ',' + str(robot5_y) + ',' +
								       str(robot6_x) + ',' + str(robot6_y) + ',' +
								       str(robot7_x) + ',' + str(robot7_y) + ',' +
								       str(robot8_x) + ',' + str(robot8_y)+ ',' +
								       str(robot9_x) + ',' + str(robot9_y)+ ',' +
								       str(robot10_x) + ',' + str(robot10_y))
												       
											
								sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
							if(index==b"stop"):
								specific_bot_goal_flag=False
								
								break	
				except:
					print("exception")	
					pass			
					
		if data.startswith(b'goal'): 
				index="data"
				
				try:
					
					print("all_bot_goal!!!!!!!!!!!!")
					#index, address = sock3.recvfrom(1024)
					print("data",data)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					f,goal_pos_num=decoded_index.split(",")
					goal_position=goal_points[int(goal_pos_num)-1]
					
					"""
					f, goal_lat, goal_lon = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(f, goal_lat, goal_lon)
					goalx,goaly = locatePosition.geoToCart (origin, endDistance, [goal_lat, goal_lon])
					print("x,y",goalx,goaly)
					#goal_bot_num=int(str(uav))
					#print(goal_bot_num)
					goal_position=[float(goalx/2),float(goaly/2)]
					"""
					print(goal_position)
					#goal_bot_num=goal_bot_num-1
					#specific_bot_goal_flag=True
					bot_reached=[0]*len(vehicles)
					while 1:
						if(len(vehicles)==10):
							time.sleep(0.003)
						elif(len(vehicles)==9):
							time.sleep(0.008)
						elif(len(vehicles)==8):
							time.sleep(0.01)
						elif(len(vehicles)==7):
							time.sleep(0.01)
						elif(len(vehicles)==6):
							time.sleep(0.009)#verified
						elif(len(vehicles)==5):
							time.sleep(0.012)#verified
						elif(len(vehicles)==4):
							time.sleep(0.015)
						elif(len(vehicles)==3):
							time.sleep(0.018)
						elif(len(vehicles)==2):
							time.sleep(0.021)
						elif(len(vehicles)==1):
							time.sleep(0.024)
						if(group_goal_flag):
							group_goal_flag=False
							break			
						for i,b in enumerate(s.swarm):
							'''
							if(pop_flag_arr[i]==0):
								i+=1						
							
							if(pop_flag):	
								if(i>=pop_bot_index):
									i+=1
							'''
							current_position=[b.x,b.y]	
							#if(i==goal_bot_num):								
							dx=abs(goal_position[0]-current_position[0])
							dy=abs(goal_position[1]-current_position[1])						
							print("dx,dy",dx,dy)
							if(dx<=5 and dy<=5):
								bot_reached[i]=1
								print("bot_reached",bot_reached)
								if all(element==1 for element in bot_reached):
									group_goal_flag=True
									break					
							else:
								current_position = (b.x, b.y)						
								#if(i==goal_bot_num):								
								print("i",i)
								
								print("goal_position",goal_position)
								b.set_goal(goal_position[0], goal_position[1])
								cmd = cvg.goal_area_cvg(i, b, goal_position)								
								print("cmd11111 exceuted")
						
								print("@@@@@@@@@@@@@@@@@")			
								#print("final_goals[goal_bot_num-1]",final_goals[goal_bot_num-1])
								print("!!!!!!!!!!!!!!!!")
								cmd.exec(b) 	
						
						#	print("bot_array",bot_array)
						#	print("current_position",current_position)	
						#	print("Drone 1 position",b.x,b.y)
							"""
							current_position = (b.x*2, b.y*2)						
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							#print ("Drone 1 lat,lon", lat,lon)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							#print("point1",point1)
							vehicles[i].simple_goto(point1)
							"""
							if i==0:
							    robot1_x,robot1_y={b.x},{b.y}
							elif i==1:
							    robot2_x,robot2_y={b.x},{b.y}
							elif i==2:
							    robot3_x,robot3_y={b.x},{b.y}
							elif i==3:
							    robot4_x,robot4_y={b.x},{b.y}
							elif i==4:
							    robot5_x,robot5_y={b.x},{b.y}
							elif i==5:
							    robot6_x,robot6_y={b.x},{b.y}
							elif i==6:
							    robot7_x,robot7_y={b.x},{b.y}
							elif i==7:
							    robot8_x,robot8_y={b.x},{b.y}
							elif i==8:
							    robot9_x,robot9_y={b.x},{b.y}
							elif i==9:
							    robot10_x,robot10_y={b.x},{b.y}
							elif i==10:
							    robot11_x,robot11_y={b.x},{b.y}
							elif i==11:
							    robot12_x,robot12_y={b.x},{b.y}
							elif i==12:
							    robot13_x,robot13_y={b.x},{b.y}
							elif i==13:
							    robot14_x,robot14_y={b.x},{b.y}
							elif i==14:
							    robot15_x,robot15_y={b.x},{b.y}
							elif i==15:
							    robot16_x,robot16_y={b.x},{b.y}
							else:
							    print('invalid')
							msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
						       str(robot2_x) + ',' + str(robot2_y) + ',' +
						       str(robot3_x) + ',' + str(robot3_y) + ',' +
						       str(robot4_x) + ',' + str(robot4_y) + ',' +
						       str(robot5_x) + ',' + str(robot5_y) + ',' +
						       str(robot6_x) + ',' + str(robot6_y) + ',' +
						       str(robot7_x) + ',' + str(robot7_y) + ',' +
						       str(robot8_x) + ',' + str(robot8_y)+ ',' +
						       str(robot9_x) + ',' + str(robot9_y)+ ',' +
						       str(robot10_x) + ',' + str(robot10_y))
										       
									
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						if(index==b"stop"):
							group_goal_flag=False
							print("Data",data)
														
							break	
				except:
					print("exception")	
					pass			
					
		#if(data==b"same"):
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

				#print("Velocity zero called##############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")	
				while True:					
					#print("velocity_flag",velocity_flag)						
					for i, b in enumerate(s.swarm):
						'''
						if(pop_flag):	
							if(i>=pop_bot_index):
								i+=1						
						
						if(pop_flag_arr[i]==0):
							i+=1
						'''
						#print("Velocity zero called##############!!!!!!!!!!!")
						cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
						cmd.exec(b)
						# Break out of the loop
						#print("Velocity zero!!!!!!!!!!!")	
						"""		
						value=[b.x*2,b.y*2]						
						#print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
						#print ("Drone 1 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						#print("point1",point1)
						vehicles[i].simple_goto(point1)
						"""
					if(index==b"resume"):
						sent = graph_socket.sendto(str("resume").encode(), graph_server_address)				
						index="data"
						velocity_flag=False
						print("1st")
						data="search"
						break
												
		#if(data==b"different"):
		if data.startswith(b'different'): 
				sent = graph_socket.sendto(str("different altitude").encode(), graph_server_address)				
				velocity_flag=True	
				print ("msg", data)
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				data1, height,step = decoded_index.split(",")
				#uav,goalx,goaly=str(index).split(",")
				print(data1, height,step)
				#print(type(data1),type(height),type(step))	
				same_alt_flag=False
				#height = int(height)
				for h in range(len(vehicles)):
					different_height[h] = int(height) + int(step) * h
				print("different_height",different_height)
				alt_count=[0]*len(vehicles)
				print("alt_count",alt_count)
				alt=[0]*len(vehicles)
				diff_height_flag=False
				
				alt_count1=0
				#print("Velocity zero called##############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")	
				while True:	
					if(diff_height_flag):
						diff_height_flag=False
						break				
					#print("velocity_flag",velocity_flag)						
					for i, b in enumerate(s.swarm):
						'''
						if(pop_flag):	
							if(i>=pop_bot_index):
								i+=1
						
						if(pop_flag_arr[i]==0):
							i+=1
						'''
						#print("Velocity zero called##############!!!!!!!!!!!")
						cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
						cmd.exec(b)
						# Break out of the loop
						#print("Velocity zero!!!!!!!!!!!")	
						"""		
						value=[b.x*2,b.y*2]						
						#print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
						#print ("Drone 1 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						#print("point1",point1)
						vehicles[i].simple_goto(point1)
						"""
						alt[i]=vehicles[i].location.global_relative_frame.alt 
						print("alt[vehicle]",alt)
						#if same_height - 1.5 <= alt[i] <= same_height+1.5: 											
						if different_height[i] - 1.5 <= alt[i] <= different_height[i]+1.5:
							alt_count[i]=1
							#alt_count1+=1
							if all(count==1 for count in alt_count):		
							#if(alt_count1==len(vehicles)):
								print("Reached target altitude")
								index="data"
								velocity_flag=False
								print("1st",alt_count)
								data="data"
								diff_height_flag=True
								break
					
					if(index==b"resume"):
						index="data"
						velocity_flag=False
						print("1st")
						data="search"
						break
				

		if(data==b"start") or (circle_formation_flag):			
			sent = graph_socket.sendto(str("circle formation").encode(), graph_server_address)	
			if(gggggg==0):
				gggggg+=1
				position=[]
				for i,vehicle in enumerate(vehicles):
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon

				       # Process the lat and lon as needed
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    current_lat_lon.append((lat,lon))			    
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    print("x,y",x/2,y/2)
				    position.append((x / 2, y / 2))
				    print(position,"position",position[0][0],position[0][1])
				    uav_home_pos[0]=(x / 2, y / 2)

				data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_position[0][0])+" , "+str(home_position[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
				print(data,"data")		
				for i in range(6):
					time.sleep(0.1)			
					sent = uav1_sock.sendto(data.encode(), uav1_server_address)
					time.sleep(0.1)
					sent = uav2_sock.sendto(data.encode(), uav2_server_address)
					time.sleep(0.1)
					sent = uav3_sock.sendto(data.encode(), uav3_server_address) 
				num_uavs=global_uavs.count(1)
				print(num_uavs,home_pos,uav_home_pos,"num_uavs,home_pos,uav_home_pos")	
				
				#gui.close()
				s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=file_name )
				
			#s = sim.Simulation(num_bots, env_name='rectangles2' )
			#gui = viz.Gui(s)			
			print("circle_formation_count",circle_formation_count)
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			while circle_formation_count<5000:
				print("$$$$$$$$$")
				circle_formation_flag=True
				start_flag=True
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				for i,b in enumerate(s.swarm):
					heartbeat[i]=vehicles[i].last_heartbeat
                					
					#print( "heartbeat",heartbeat)
					#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
					#print("slave_heal_ip[i]",slave_heal_ip[i])
					if(heartbeat[i]>10):
						#print("Vehicle ", i+1 ,"No heartbeat")   	
						lost_vehicle_num=i+1
						print("lostvehicle",lost_vehicle_num)   
						vehicle_lost_flag=True  						
						message= "vehicle "+str(i+1)+" has no heartbeat"                   		
						sock1.sendto(str(message).encode(), server_address1) 
					print("^^^^^^^")
					circle_formation_count+=1
					print("HHHHHHH")
					cmd = base_control.base_control(i,b,home_pos[0])
					print("((((((((((((")
					cmd+= base_control.obstacle_avoidance(i,b,home_pos[0])					
					print("%%%%%%%%")
					#Behaviour
					cmd+=circle(b,100)
					cmd += disp_field(b)
					 
					print("###########")
					#Execute
					cmd.exec(b)
					print("#####")
					all_xy[i]=[b.x*2,b.y*2]
					print("all_xy",all_xy)
					if(master_flag):	
						print("CCCCCCCCCCCCCCCC")	
							       
						if(len(s.swarm)-1==i):
							try:
								s1=str(all_xy[0][0])+","+str(all_xy[0][1])
							except:
								pass
							try:
								print("JJJJJJJJJJJJJJJJJJ")
								s2=str(all_xy[1][0])+","+str(all_xy[1][1])
							except:
								pass
							try:
								s3=str(all_xy[2][0])+","+str(all_xy[2][1])
							except:
								pass
							#s=1
							print(s1,s2,"s")
							
							try:
								p_sock1.sendto(str(s1).encode(), p_server_address1)
							except:
								pass
							try:
								print("JJJJJJJJJJJJJJJJJJ")
								p_sock2.sendto(str(s2).encode(), p_server_address2)
							except:
								pass
							try:							
								p_sock3.sendto(str(s3).encode(), p_server_address3)
							except:
								pass
							a=receive_xy()							
							
					else:
						print("KKK")
						a=receive_xy()	
					"""
					current_position = [b.x*2,b.y*2]
					print(current_position)
					print("Drone 1 position",b.x,b.y)
					lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
					
					#print ("Drone 1 lat,lon", lat,lon)
					if same_alt_flag:
						point1 = LocationGlobalRelative(lat,lon,same_height)
					else:
						point1 = LocationGlobalRelative(lat,lon,different_height[i])
					vehicles[i].simple_goto(point1)
					"""
					if i==0:
					    robot1_x,robot1_y={b.x},{b.y}
					elif i==1:
					    robot2_x,robot2_y={b.x},{b.y}
					elif i==2:
					    robot3_x,robot3_y={b.x},{b.y}
					elif i==3:
					    robot4_x,robot4_y={b.x},{b.y}
					elif i==4:
					    robot5_x,robot5_y={b.x},{b.y}
					elif i==5:
					    robot6_x,robot6_y={b.x},{b.y}
					elif i==6:
					    robot7_x,robot7_y={b.x},{b.y}
					elif i==7:
					    robot8_x,robot8_y={b.x},{b.y}
					elif i==8:
					    robot9_x,robot9_y={b.x},{b.y}
					elif i==9:
					    robot10_x,robot10_y={b.x},{b.y}
					elif i==10:
					    robot11_x,robot11_y={b.x},{b.y}
					elif i==11:
					    robot12_x,robot12_y={b.x},{b.y}
					elif i==12:
					    robot13_x,robot13_y={b.x},{b.y}
					elif i==13:
					    robot14_x,robot14_y={b.x},{b.y}
					elif i==14:
					    robot15_x,robot15_y={b.x},{b.y}
					elif i==15:
					    robot16_x,robot16_y={b.x},{b.y}
					else:
					    print('invalid')
					msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
				       str(robot2_x) + ',' + str(robot2_y) + ',' +
				       str(robot3_x) + ',' + str(robot3_y) + ',' +
				       str(robot4_x) + ',' + str(robot4_y) + ',' +
				       str(robot5_x) + ',' + str(robot5_y) + ',' +
				       str(robot6_x) + ',' + str(robot6_y) + ',' +
				       str(robot7_x) + ',' + str(robot7_y) + ',' +
				       str(robot8_x) + ',' + str(robot8_y) + ',' +
				       str(robot9_x) + ',' + str(robot9_y) + ',' +
				       str(robot10_x) + ',' + str(robot10_y))
								       
							
				sent = graph_socket.sendto(str(msg).encode(), graph_server_address)

				#gui.update()
					
			
		if(data==b"start1") or (start_flag):
			if(circle_formation_count>=5000):
				circle_formation_flag=False
				start_flag=True					
			position=[]			
			for i,vehicle in enumerate(vehicles):
			    lat = vehicle.location.global_relative_frame.lat
			    lon = vehicle.location.global_relative_frame.lon

			       # Process the lat and lon as needed
			    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
			    current_lat_lon.append((lat,lon))			    
			    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
			    print("x,y",x/2,y/2)
			    position.append((x / 2, y / 2))
			    print(position,"position",position[0][0],position[0][1])
			    uav_home_pos[0]=(x / 2, y / 2)

			data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_position[0][0])+" , "+str(home_position[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
			print(data,"data")	
			for i in range(6):
				time.sleep(0.1)			
				sent = uav1_sock.sendto(data.encode(), uav1_server_address)
				time.sleep(0.1)
				sent = uav2_sock.sendto(data.encode(), uav2_server_address)
				time.sleep(0.1)
				sent = uav3_sock.sendto(data.encode(), uav3_server_address)
				#sent = uav3_sock.sendto(data.encode(), uav3_server_address)
				#sent = uav4_sock.sendto(data.encode(), uav4_server_address)
				#sent = uav5_sock.sendto(data.encode(), uav5_server_address)			
					
			num_uavs=global_uavs.count(1)
			print(num_uavs,home_pos,uav_home_pos,"num_uavs,home_pos,uav_home_pos")	
			print("uav_home_pos!!!!!!!!!!",uav_home_pos,num_uavs)  
			#gui.close()
						
			sent = graph_socket.sendto(str("start").encode(), graph_server_address)	
			#gui.close()
			s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=file_name )					
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			for b in s.swarm:
				'''
				if(vehicle_lost_flag):
					print("############",vehicle_lost_flag)
					vehicle_lost_flag=True
					break	
				'''

				multiple_goals=start_multiple_goals			
				bot_paths={
					   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[8]],				   
					   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[8]],
					   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[8]],
					   3:[multiple_goals[3],multiple_goals[4],multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[8]],
					   4:[multiple_goals[4],multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[8]],
					   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[8]],
					   6:[multiple_goals[6],multiple_goals[7],multiple_goals[8]],
					   7:[multiple_goals[7],multiple_goals[8]],
					   8:[multiple_goals[8]],

				}
				
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * len(vehicles)			
				goal_table=[0]*len(vehicles)
				print("goal_table",goal_table)
				current_table=[0]*len(vehicles)
				length_arr=[0]*len(vehicles)
				new_length_arr=[0]*len(vehicles)
				count=[0]*len(vehicles)
				step=0
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*len(vehicles)
				
				while 1:
					print("############")
					print("pop_flag_arr",pop_flag_arr)
					'''
					if(vehicle_uav_heartbeat_flag):
						search_height_flag=True
						pop_flag=True
						pop_bot_index=int(str(uav_heartbeat))
						#same_height+=3
					'''
					if(search_height_flag):
						break
					if(vehicle_lost_flag):
						vehicle_lost_flag=True
						x=remove_vehicle()
						print(x)
					
					step+=1
					print("step",step)
					if(step==1):											
						for i,b in enumerate(s.swarm):
							print("%%%%pos_array%%%%%%",pos_array)
							'''
							if(pop_flag_arr[i]==0):
								i+=1
							#print("step",step,i)
							'''
												#print("potf.reached_goals",potf.reached_goals)							
							#if(potf.reached_goals[i]==False):
							heartbeat[i]=vehicles[i].last_heartbeat
							#print( "heartbeat",heartbeat)
							#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
							#print("slave_heal_ip[i]",slave_heal_ip[i])
							if(heartbeat[i]>10):
								#print("Vehicle ", i+1 ,"No heartbeat")   	
								lost_vehicle_num=i
								print("lostvehicle",lost_vehicle_num)   
								vehicle_lost_flag=True  
								remove_flag=True           		
								message= "vehicle "+str(i+1)+" has no heartbeat"                   		
								sock1.sendto(str(message).encode(), server_address1) 
							current_position = [b.x,b.y]
							#nearest_goal = min(multiple_goals1, key=lambda goal: distance.euclidean(current_position, goal))
							#goal_ind=multiple_goals.index(nearest_goal)							
							#goal_table[i]=multiple_goals.index(nearest_goal)
							
							#gui.update()
							print("!!!!!!!!!!!current_table!!!!!!!",current_table)
							with open('/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv','rt')as text:
								data = csv.reader(text)
								for row in data: 
									data = (row)
									#print ("loc",data[-1])
									nextwaypoint=int(data[-1])							
							print("nextwaypoint!!!!!!!!!!!!!",nextwaypoint)
							if (nextwaypoint+1)==len(multiple_goals):
								goal_table[i]=nextwaypoint
							else:
								goal_table[i]=nextwaypoint+1
							print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
							if i==0:
							    robot1_x,robot1_y={b.x},{b.y}
							elif i==1:
							    robot2_x,robot2_y={b.x},{b.y}
							elif i==2:
							    robot3_x,robot3_y={b.x},{b.y}
							elif i==3:
							    robot4_x,robot4_y={b.x},{b.y}
							elif i==4:
							    robot5_x,robot5_y={b.x},{b.y}
							elif i==5:
							    robot6_x,robot6_y={b.x},{b.y}
							elif i==6:
							    robot7_x,robot7_y={b.x},{b.y}
							elif i==7:
							    robot8_x,robot8_y={b.x},{b.y}
							elif i==8:
							    robot9_x,robot9_y={b.x},{b.y}
							elif i==9:
							    robot10_x,robot10_y={b.x},{b.y}
							elif i==10:
							    robot11_x,robot11_y={b.x},{b.y}
							elif i==11:
							    robot12_x,robot12_y={b.x},{b.y}
							elif i==12:
							    robot13_x,robot13_y={b.x},{b.y}
							elif i==13:
							    robot14_x,robot14_y={b.x},{b.y}
							elif i==14:
							    robot15_x,robot15_y={b.x},{b.y}
							elif i==15:
							    robot16_x,robot16_y={b.x},{b.y}
							else:
							    print('invalid')
							msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
						       str(robot2_x) + ',' + str(robot2_y) + ',' +
						       str(robot3_x) + ',' + str(robot3_y) + ',' +
						       str(robot4_x) + ',' + str(robot4_y) + ',' +
						       str(robot5_x) + ',' + str(robot5_y) + ',' +
						       str(robot6_x) + ',' + str(robot6_y) + ',' +
						       str(robot7_x) + ',' + str(robot7_y) + ',' +
						       str(robot8_x) + ',' + str(robot8_y) + ',' +
						       str(robot9_x) + ',' + str(robot9_y) + ',' +
						       str(robot10_x) + ',' + str(robot10_y))
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						print("@@@@@@@@@@@@@@@@@")
					else:
						print("###################")
						
						if(len(vehicles)==10):
							time.sleep(0.003)
						elif(len(vehicles)==9):
							time.sleep(0.008)
						elif(len(vehicles)==8):
							time.sleep(0.01)
						elif(len(vehicles)==7):
							time.sleep(0.01)
						elif(len(vehicles)==6):
							time.sleep(0.009)#verified
						elif(len(vehicles)==5):
							time.sleep(0.012)#verified
						elif(len(vehicles)==4):
							time.sleep(0.015)
						elif(len(vehicles)==3):
							time.sleep(0.018)
						elif(len(vehicles)==2):
							time.sleep(0.021)
						elif(len(vehicles)==1):
							time.sleep(0.024)						
						print("&&&&&&&")
						for i,b in enumerate(s.swarm):							
							print(len(s.swarm))
							heartbeat[i]=vehicles[i].last_heartbeat
							#print( "heartbeat",heartbeat)
							#print(" Last Heartbeat: %s" , i+1,vehicles[i].last_heartbeat)
							#print("slave_heal_ip[i]",slave_heal_ip[i])
							if(heartbeat[i]>10):
								print("Vehicle ", i+1 ,"No heartbeat")   	
								lost_vehicle_num=i+1
								print("lostvehicle",lost_vehicle_num)   
								vehicle_lost_flag=True  
								#remove_flag=True           		
								message= "vehicle "+str(i+1)+" has no heartbeat"                   		
								sock1.sendto(str(message).encode(), server_address1) 
															
							current_position = [b.x,b.y]
							print("current_position",current_position)
							
							#count[goal_table[i]]=count[goal_table[i]]+1
							#print("counter array",count)
							#print("BOT {} reached",i)
							#print("goal_table[goal_index]",goal_table)
							ind=goal_table[i]
							print("ind",ind)
							next_goal=bot_paths[ind]
							print("next_goal",next_goal)
							if(step==2):
								length_arr[i]=len(bot_paths[ind])
								new_length_arr[i]=length_arr[i]
							if(count[i]==length_arr[i]):
								continue
							#print("length_arr",length_arr)
							#print("new_length_arr",new_length_arr)
							if(len(bot_paths[ind])<1):							
								#print("BOT {i} goal reached",i)
								continue
							#print("len(bot_paths[ind]",len(bot_paths[ind]))
							#for i,b in enumerate(s.swarm):
							#current_position=[b.x,b.y]
							goal=bot_paths[goal_table[i]][count[i]]
							print("goal",goal)
							print("multiple_goals[0]",multiple_goals[0])
							#if(goal==multiple_goals[1]):
							#	print("INitial time.sleep")
							#	time.sleep(20)
							#Base control
							#cmd = base_control.base_control(i,b,goal)
							#cmd+= base_control.obstacle_avoidance(i,b,goal)
							
							#Behaviour
							#cmd+=line(b)
							print("111111",i,b,goal)
							#cmd =cvg.goal_area_cvg(i,b,goal,use_base_control=True, exp_weight_params=[15.0,15.5],disp_weight_params=[30.0,30.0])
							cmd =cvg.goal_area_cvg(i,b,goal)
							
							#Execute
							cmd.exec(b)
							print("2222222",i,b,goal)
							#print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])						
							print("dx,dy",dx,dy)
							if(dx<=10 and dy<=10):
								bot_array[i]=1
								print("bot_array",bot_array)
								#if len(bot_array)==len(vehicles):
									#all_bot_reach_flag=True									
							count_1=0
							#print("count_1",count_1)
							for j in range(len(vehicles)):
								#print("************")
								if(bot_array[j]==1):
									count_1+=1
								if(count_1==len(vehicles)):
									count_1=0
									bot_array=[0]*len(vehicles)
									all_bot_reach_flag=True

							#print("bot_array",bot_array)
							if (all_bot_reach_flag==True):								
								#print("Goal_reached!!!!!!!!!!!")
								with open(r'/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
									fieldnames = ['waypoint']
									writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
									writer.writerow({'waypoint':multiple_goals.index(goal)})	
								new_length_arr[i]=new_length_arr[i]-1
								#print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
								#count[i]+=1
								if(master_flag):
										#global_path_csv.append(path)
										#path=str(multiple_goals.index(goal))
										print("global_path_csv",global_path_csv,path,type(path))
										
										for i in range(6):
								    	    		print("VVV@@@@@@@@@@@@@@@@@@@@KKKKKKKK")
								    	    		#time.sleep(0.1)			
								    	    		share_path_sock1.sendto(str(path).encode(), share_path_sock1_server_address)
								    	    		print("str(path:",path,str(path))
								    	    		#time.sleep(0.1)
								    	    		share_path_sock2.sendto(str(path).encode(), share_path_sock2_server_address)
								    	    		#time.sleep(0.1)
								    	    		share_path_sock3.sendto(str(path).encode(), share_path_sock3_server_address)
								    	    		print("multiple_goals.index(goal),global_path_csv",multiple_goals.index(goal),global_path_csv)
								for k in range(len(vehicles)):
									count[k]+=1
									
								all_bot_reach_flag=False
								bot_array=[0]*len(vehicles)
								#print("goal,bot_paths[ind][-1]",goal,bot_paths[ind][-1])
								if (goal==bot_paths[ind][-1]):
									print("Break")
									start_flag=False
									search_height_flag=True						
									break
							all_xy[i] = [b.x*2,b.y*2]		
							print("multiple_goals.index(goal),global_path_csv",multiple_goals.index(goal),global_path_csv)			
							if(master_flag):		
								
								print("&&&&&&&&&&&&&")	       
								if(len(s.swarm)-1==i):
									try:
										s1=str(all_xy[0][0])+","+str(all_xy[0][1])
									except:
										pass
									try:
										print("JJJJJJJJJJJJJJJJJJ")
										s2=str(all_xy[1][0])+","+str(all_xy[1][1])
									except:
										pass
									try:
										s3=str(all_xy[2][0])+","+str(all_xy[2][1])
									except:
										pass
									#s=1
									print(s1,s2,"s")
									
									try:
										p_sock1.sendto(str(s1).encode(), p_server_address1)
									except:
										pass
									try:
										print("JJJJJJJJJJJJJJJJJJ")
										p_sock2.sendto(str(s2).encode(), p_server_address2)
									except:
										pass
									try:							
										p_sock3.sendto(str(s3).encode(), p_server_address3)
									except:
										pass
									a=receive_xy()							
									
							else:
								a=receive_xy()
							"""
							current_position = [b.x*2,b.y*2]
							#print("Drone 1 position",b.x,b.y)
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							
							#print ("Drone 1 lat,lon", lat,lon)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
							"""
							if i==0:
							    robot1_x,robot1_y={b.x},{b.y}
							elif i==1:
							    robot2_x,robot2_y={b.x},{b.y}
							elif i==2:
							    robot3_x,robot3_y={b.x},{b.y}
							elif i==3:
							    robot4_x,robot4_y={b.x},{b.y}
							elif i==4:
							    robot5_x,robot5_y={b.x},{b.y}
							elif i==5:
							    robot6_x,robot6_y={b.x},{b.y}
							elif i==6:
							    robot7_x,robot7_y={b.x},{b.y}
							elif i==7:
							    robot8_x,robot8_y={b.x},{b.y}
							elif i==8:
							    robot9_x,robot9_y={b.x},{b.y}
							elif i==9:
							    robot10_x,robot10_y={b.x},{b.y}
							elif i==10:
							    robot11_x,robot11_y={b.x},{b.y}
							elif i==11:
							    robot12_x,robot12_y={b.x},{b.y}
							elif i==12:
							    robot13_x,robot13_y={b.x},{b.y}
							elif i==13:
							    robot14_x,robot14_y={b.x},{b.y}
							elif i==14:
							    robot15_x,robot15_y={b.x},{b.y}
							elif i==15:
							    robot16_x,robot16_y={b.x},{b.y}
							else:
							    print('invalid')
							msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
						       str(robot2_x) + ',' + str(robot2_y) + ',' +
						       str(robot3_x) + ',' + str(robot3_y) + ',' +
						       str(robot4_x) + ',' + str(robot4_y) + ',' +
						       str(robot5_x) + ',' + str(robot5_y) + ',' +
						       str(robot6_x) + ',' + str(robot6_y) + ',' +
						       str(robot7_x) + ',' + str(robot7_y) + ',' +
						       str(robot8_x) + ',' + str(robot8_y) + ',' +
						       str(robot9_x) + ',' + str(robot9_y) + ',' +
						       str(robot10_x) + ',' + str(robot10_y))
										       
									
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						
					#gui.update()
					
					if(index==b"stop"):	
						print("strat_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						start_flag=False
						circle_formation_flag=False		
						print("strat_flag",start_flag,"circle_formation_flag",circle_formation_flag)				
						break
					if(index==b"search"):
						search_flag=True						
					if(disperse_flag):
						start_flag=False
						search_height_flag=False
						#disperse_flag=True
						break
					if(search_height_flag):
						start_flag=False
						velocity_flag=True	
						same_alt_flag=True
						same_height=30
						
						if(pop_flag):
							same_height+=3
						
						alt=[0]*len(vehicles)
						alt_count=[0]*len(vehicles)
						alt_count1=0
						print("Velocity zero called##############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")	
						while True:	
							if(index==b"stop"):
								start_flag=False
								break
							if(index==b"search"):
								start_flag=False
								search_height_flag=False
								search_flag=True							
								break
							#time.sleep(0.01)
							if(disperse_flag):
								start_flag=False
								search_height_flag=False
								break				
							print("velocity_flag",velocity_flag)						
							for i, b in enumerate(s.swarm):
								'''
								if(pop_flag):	
									if(i>=pop_bot_index):
										i+=1
								'''
								heartbeat[i]=vehicles[i].last_heartbeat
								#print( "heartbeat",heartbeat)
								#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
								#print("slave_heal_ip[i]",slave_heal_ip[i])
								if(heartbeat[i]>10):
									#print("Vehicle ", i+1 ,"No heartbeat")   	
									lost_vehicle_num=i+1
									print("lostvehicle",lost_vehicle_num)   
									vehicle_lost_flag=True  
									#remove_flag=True           		
									message= "vehicle "+str(i+1)+" has no heartbeat"                   		
									sock1.sendto(str(message).encode(), server_address1) 
								#print("Velocity zero called##############!!!!!!!!!!!")
								cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
								cmd.exec(b)
								# Break out of the loop
								#print("Velocity zero!!!!!!!!!!!")			
								#value=[b.x*2,b.y*2]
								all_xy[i] = [b.x*2,b.y*2]					
										       
								if(master_flag):	
								
									print("UUUUUUUUUUUUUUU")		       
									
									if(len(s.swarm)-1==i):
										try:
											s1=str(all_xy[0][0])+","+str(all_xy[0][1])
										except:
											pass
										try:
											s2=str(all_xy[1][0])+","+str(all_xy[1][1])
										except:
											pass
										try:
											s3=str(all_xy[2][0])+","+str(all_xy[2][1])
										except:
											pass
										#s=1
										print(s1,s2,"s")
										
										try:
											p_sock1.sendto(str(s1).encode(), p_server_address1)
										except:
											pass
										try:
											p_sock2.sendto(str(s2).encode(), p_server_address2)
										except:
											pass
										try:							
											p_sock3.sendto(str(s3).encode(), p_server_address3)
										except:
											pass
										a=receive_xy()							
											
									else:
										print("JJJJJJJJ")
										a=receive_xy()
								#gui.show_coverage(area_covered,elapsed_time)

								
								#print("Velocity Bot State",b.state)

								print("Drone 1 position",b.x,b.y)
								lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
								#print ("Drone 1 lat,lon", lat,lon)
								
								"""
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								#print("point1",point1)
								vehicles[i].simple_goto(point1)
								"""
								for i,vehicle in enumerate(vehicles):
									alt[i]=vehicle.location.global_relative_frame.alt 
									print("alt[vehicle]",alt[i])
									if same_height - 1.5 <= alt[i] <= same_height + 1.5:
										alt_count[i]=1
											#alt_count1+=1										
										if all(count==1 for count in alt_count):	
										#if(alt_count1==len(vehicles)):
											print("Reached target altitude")
											search_height_flag=False
											disperse_flag=True
											break
								
		if(data==b"disperse") or (disperse_flag):
		#	sent = graph_socket.sendto(str("disperse").encode(), graph_server_address)				
			index="data"	
			print("Disperse!!!!!",len(vehicles),uav_home_pos)
			position=[]
			for i,vehicle in enumerate(vehicles):
			    lat = vehicle.location.global_relative_frame.lat
			    lon = vehicle.location.global_relative_frame.lon

			       # Process the lat and lon as needed
			    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
			    current_lat_lon.append((lat,lon))			    
			    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
			    print("x,y",x/2,y/2)
			    position.append((x / 2, y / 2))
			    print(position,"position",position[0][0],position[0][1])
			    uav_home_pos[0]=(x / 2, y / 2)

			data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_position[0][0])+" , "+str(home_position[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
			print(data,"data")	
			for i in range(6):
				time.sleep(0.1)			
				sent = uav1_sock.sendto(data.encode(), uav1_server_address)
				time.sleep(0.1)
				sent = uav2_sock.sendto(data.encode(), uav2_server_address)
				time.sleep(0.1)
				sent = uav3_sock.sendto(data.encode(), uav3_server_address)
				#sent = uav4_sock.sendto(data.encode(), uav4_server_address)
				#sent = uav5_sock.sendto(data.encode(), uav5_server_address)	
			
			num_uavs=global_uavs.count(1)
			print(num_uavs,home_pos,uav_home_pos,"num_uavs,home_pos,uav_home_pos")	
			s = sim.Simulation(uav_home_pos,num_bots=num_uavs, env_name=file_name )
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			'''
			if os.path.isfile(dce_search_file):
			    selected_file = dce_search_file
			else:
			    # If the DCE search file is not available, use the DCE file
			    selected_file = file_name  # Replace "dce_file" with the name of your DCE file
			'''
			#s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=selected_file )
			print("file_name+'_search'",file_name+'_search')
			s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=file_name+'_search' )
			print("KKKKKKKK")
			disperse_bot_goal=[0]*len(vehicles)
			YOUR_GOAL_THRESHOLD_DISTANCE=15
			YOUR_THRESHOLD_DISTANCE=15
			current_goal_index = [0] * len(vehicles)			
			goal_table=[0]*len(vehicles)
			print("goal_table",goal_table)
			current_table=[0]*len(vehicles)
			length_arr=[0]*len(vehicles)
			new_length_arr=[0]*len(vehicles)
			count=[0]*len(vehicles)
			step=0
			all_bot_reach_flag_rev=False
			bot_array_rev=[0]*len(vehicles)
			disperse_start_time = time.time()
			print("disperse_start_time",disperse_start_time)
			multiple_goals=disperse_multiple_goals
			while True:				
				try:
					data,address=sock2.recvfrom(1024)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					
					if(data==b"search"):
						search_flag=True
						break
				except:
					if(vehicle_lost_flag):
						vehicle_lost_flag=True
						x=remove_vehicle()
						print(x)
					for i,b in enumerate(s.swarm):
					
						heartbeat[i]=vehicles[i].last_heartbeat
						#print( "heartbeat",heartbeat)
						#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
						#print("slave_heal_ip[i]",slave_heal_ip[i])
						if(heartbeat[i]>10):
							#print("Vehicle ", i+1 ,"No heartbeat")   	
							lost_vehicle_num=i+1
							print("lostvehicle",lost_vehicle_num)   
							vehicle_lost_flag=True  
								  		
							message= "vehicle "+str(i+1)+" has no heartbeat"                   		
							sock1.sendto(str(message).encode(), server_address1) 
						
						print("disperse_start_time",disperse_start_time)											
						if(disperse_multiple_goals==[]):
							print("************")
							cmd = base_control.exp_control(b)
							cmd+= disp_field(b,neighbourhood_radius=500)*15
							#cmd+= disp_field(b)*15
							cmd+= base_control.exp_obstacle_avoidance(b)*30
						else:
							print("&&&&&&&&&&&")
							current_position = [b.x,b.y]
							cmd = base_control.base_control(i,b,multiple_goals[i])					
							cmd = disp_field(b)*2
							cmd+= base_control.obstacle_avoidance(i,b,multiple_goals[i])
							dx=abs(multiple_goals[i][0]-current_position[0])
							dy=abs(multiple_goals[i][1]-current_position[1])						
							#print("dx,dy",dx,dy)
							if(dx<=3 and dy<=3):									
								#print("Goal_reached!!!!!!!!!!!")	
								new_length_arr[i]=new_length_arr[i]-1
								#print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
								disperse_bot_goal[i]=1
								print("disperse_bot_goal",disperse_bot_goal)
								#bot_array_rev[i]=1
							
							#if(goal==bot_paths[goal_table[i]][-1]):
							#	print("Drone ",i,"reached")
							#	bot_array_rev[i]=1
							
							if all(goal==1 for goal in disperse_bot_goal):
								disperse_flag=False
								search_flag=True
								print(search_flag,"search_flag")
								break
						"""
						cmd = base_control.exp_control(b)
						cmd+= disp_field(b,neighbourhood_radius=500)*15					
						cmd+= base_control.exp_obstacle_avoidance(b)*30
						"""
						elapsed_time = time.time() - disperse_start_time
						print("Disperse elapsed_time",elapsed_time)
						#Behaviour
						#cmd+=line(b)
						cmd.exec(b)
						"""		
						current_position =[b.x*2,b.y*2]
						#print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						#print ("Drone 1 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						#print("point1",point1)
						vehicles[i].simple_goto(point1)	
						"""
						all_xy[i] = [b.x*2,b.y*2]					
								       
						if(master_flag):	
						
							print("UUUUUUUUUUUUUUU")		       
							
							if(len(s.swarm)-1==i):
								try:
									s1=str(all_xy[0][0])+","+str(all_xy[0][1])
								except:
									pass
								try:
									s2=str(all_xy[1][0])+","+str(all_xy[1][1])
								except:
									pass
								try:
									s3=str(all_xy[2][0])+","+str(all_xy[2][1])
								except:
									pass
								#s=1
								print(s1,s2,"s")
								
								try:
									p_sock1.sendto(str(s1).encode(), p_server_address1)
								except:
									pass
								try:
									p_sock2.sendto(str(s2).encode(), p_server_address2)
								except:
									pass
								try:							
									p_sock3.sendto(str(s3).encode(), p_server_address3)
								except:
									pass
								a=receive_xy()							
									
							else:
								print("JJJJJJJJ")
								a=receive_xy()
						if i==0:
						    robot1_x,robot1_y={b.x},{b.y}
						elif i==1:
						    robot2_x,robot2_y={b.x},{b.y}
						elif i==2:
						    robot3_x,robot3_y={b.x},{b.y}
						elif i==3:
						    robot4_x,robot4_y={b.x},{b.y}
						elif i==4:
						    robot5_x,robot5_y={b.x},{b.y}
						elif i==5:
						    robot6_x,robot6_y={b.x},{b.y}
						elif i==6:
						    robot7_x,robot7_y={b.x},{b.y}
						elif i==7:
						    robot8_x,robot8_y={b.x},{b.y}
						elif i==8:
						    robot9_x,robot9_y={b.x},{b.y}
						elif i==9:
						    robot10_x,robot10_y={b.x},{b.y}
						elif i==10:
						    robot11_x,robot11_y={b.x},{b.y}
						elif i==11:
						    robot12_x,robot12_y={b.x},{b.y}
						elif i==12:
						    robot13_x,robot13_y={b.x},{b.y}
						elif i==13:
						    robot14_x,robot14_y={b.x},{b.y}
						elif i==14:
						    robot15_x,robot15_y={b.x},{b.y}
						elif i==15:
						    robot16_x,robot16_y={b.x},{b.y}
						else:
						    print('invalid')
						msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
					       str(robot2_x) + ',' + str(robot2_y) + ',' +
					       str(robot3_x) + ',' + str(robot3_y) + ',' +
					       str(robot4_x) + ',' + str(robot4_y) + ',' +
					       str(robot5_x) + ',' + str(robot5_y) + ',' +
					       str(robot6_x) + ',' + str(robot6_y) + ',' +
					       str(robot7_x) + ',' + str(robot7_y) + ',' +
					       str(robot8_x) + ',' + str(robot8_y) + ',' +
					       str(robot9_x) + ',' + str(robot9_y) + ',' +
					       str(robot10_x) + ',' + str(robot10_y))
									       
					if(elapsed_time>45):
						disperse_flag=False
						search_flag=True
						break
					
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
								#gui.update()						
					if(index==b"search") or (search_flag):
						print("FFFFFFF")
						disperse_flag=False
						search_flag=True
						break
								
								
		if(data==b"search") or (search_flag):
			sent = graph_socket.sendto(str("search").encode(), graph_server_address)				
			index="data"
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			position=[]
			for i,vehicle in enumerate(vehicles):
			    lat = vehicle.location.global_relative_frame.lat
			    lon = vehicle.location.global_relative_frame.lon

			       # Process the lat and lon as needed
			    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
			    current_lat_lon.append((lat,lon))			    
			    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
			    print("x,y",x/2,y/2)
			    position.append((x / 2, y / 2))
			    print(position,"position",position[0][0],position[0][1])
			    uav_home_pos[0]=(x / 2, y / 2)

			data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_position[0][0])+" , "+str(home_position[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
			print(data,"data")	
			for i in range(6):
				time.sleep(0.1)			
				sent = uav1_sock.sendto(data.encode(), uav1_server_address)
				time.sleep(0.1)
				sent = uav2_sock.sendto(data.encode(), uav2_server_address)
				time.sleep(0.1)
				sent = uav3_sock.sendto(data.encode(), uav3_server_address)
				#sent = uav4_sock.sendto(data.encode(), uav4_server_address)
				#sent = uav5_sock.sendto(data.encode(), uav5_server_address)	f
			
			num_uavs=global_uavs.count(1)
			print(num_uavs,home_pos,uav_home_pos,"num_uavs,home_pos,uav_home_pos")	
			s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=file_name+'_search' )
			
			gui = viz.Gui(s)
			#gui.show_env()
			#gui.show_bots()
			gui.update()
			gui.close()
			
			print("Search Started")
			f=""
			uav=0
			goal_lat=0.0
			goal_lon=0.0
			goal_x=0
			goal_y=0
			goal_bot_num=0
			goal_position=[]
			move_bot_flag_array=[False]*len(vehicles)
			move_bot_pos_array=[0]*len(vehicles)			
			search_start_time = time.time()
			while 1:	
				
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				try:
					data,address=sock2.recvfrom(1024)
					print("data",data)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					print("decoded_index",type(decoded_index),decoded_index)					
					f,uav, goal_point_num = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav, goal_point_num)
					
					
					"""
					f,uav, goal_lat, goal_lon = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav, goal_lat, goal_lon)					
					goalx,goaly = locatePosition.geoToCart (origin, endDistance, goal_pos)
					
					print("x,y",goalx,goaly)
					"""
										
					
					#if(data.startswith(b"move_bot")):
					'''
					if(f=="move_bot"):
						move_bot_flag=True
						print("explore_bot_goal!!!!!!!!!!!!")						
						print("index",data)
						"""
						goalx,goaly = locatePosition.geoToCart (origin, endDistance, [goal_lat, goal_lon])
						print("x,y",goalx,goaly)
						"""
						goal_bot_num=int(str(uav))
						print(goal_bot_num)
						goal_position=[float(goalx/2),float(goaly/2)]
						print(goal_position)
						goal_bot_num=goal_bot_num-1
						#specific_bot_goal_flag=True
					'''
					if(f=="move_bot"):
						move_bot_flag=True
						print("explore_bot_goal!!!!!!!!!!!!")						
						print("index",data)
						goal_bot_num=int(str(uav))
						print(goal_bot_num)
						goal_position=goal_points[int(goal_point_num)-1]
						print("goal_position",goal_position,goal_position[0],goal_position[1])
						#goal_position=[float(goalx/2),float(goaly/2)]
						print(goal_position)
						goal_bot_num=goal_bot_num-1
						move_bot_flag_array[goal_bot_num]=True
						move_bot_pos_array[goal_bot_num]=goal_position
						print("move_bot_flag_array",move_bot_flag_array)
						print("move_bot_pos_array",move_bot_pos_array)
				except:
					for i,b in enumerate(s.swarm):									
						area=gui.show_coverage(area_covered,elapsed_time)	
						if((area*10)>67) or (aggregate_flag):
							aggregate_flag=True
							break																		
						heartbeat[i]=vehicles[i].last_heartbeat
						#print( "heartbeat",heartbeat)
						#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
						#print("slave_heal_ip[i]",slave_heal_ip[i])
						if(heartbeat[i]>10):
							#print("Vehicle ", i+1 ,"No heartbeat")   	
							lost_vehicle_num=i+1
							print("lostvehicle",lost_vehicle_num)   
							vehicle_lost_flag=True  
							#remove_flag=True           		
							message= "vehicle "+str(i+1)+" has no heartbeat"                   		
							sock1.sendto(str(message).encode(), server_address1) 
						current_position=[b.x,b.y]
						if(move_bot_flag) or (move_bot_flag_array[i]):
						#if(move_bot_flag_array[i]):
							
							if(move_bot_flag_array[i]):								
												
																																								
								print("goal_position",i,move_bot_pos_array[i])
								print("move_bot_pos_array,i,val",i,move_bot_pos_array[i],move_bot_pos_array[i][0],move_bot_pos_array[i][1])
								"""
								goal_position[0]=move_bot_pos_array[i][0]
								goal_position[1]=move_bot_pos_array[i][1]
								print("goal_position[0],goal_position[1]",goal_position[0],goal_position[1])
								"""
								b.set_goal(move_bot_pos_array[i][0],move_bot_pos_array[i][1])
								cmd = cvg.goal_area_cvg(i, b, move_bot_pos_array[i])							 	
								print("cmd11111 exceuted")

								dx=abs(move_bot_pos_array[i][0]-current_position[0])
								dy=abs(move_bot_pos_array[i][1]-current_position[1])					
								print("dx,dy",dx,dy)
								print("move_bot_flag_array",move_bot_flag_array)
								print("move_bot_pos_array",move_bot_pos_array)				
								if(dx<=1 and dy<=1):
									
									move_bot_flag_array[i]=False
									
								if all(flag==False for flag in move_bot_flag_array):							
									move_bot_flag=False
									break
																									
							else:
								print("I###########",i)
								cmd = cvg.disp_exp_area_cvg(b, use_base_control=True, exp_weight_params=[1.0,1.5],disp_weight_params=[2.0,2.5]) *2
					
					
						else:
							#cmd = cvg.disp_exp_area_cvg(b, use_base_control=True, exp_weight_params=[25.0,25.5],disp_weight_params=[50.0,50.0]) 
							print("^^^^^^^^^^^^^^^^^^^^^^^^^",i)					
							cmd = cvg.disp_exp_area_cvg(b) 					
						value=[b.x*2,b.y*2]
						cmd.exec(b)
						#print("value",i,value)
												
						elapsed_time = time.time() - search_start_time
						
						gui.show_coverage(area_covered,elapsed_time)
						
						"""
						#print("Bot State",b.state)
						if pop_flag_arr[i]==1:
							#print("Drone 1 position",b.x,b.y)
							lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
				 				#print ("Drone 1 lat,lon", lat,lon)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							#print("point1",point1)
							vehicles[i].simple_goto(point1)
						"""
						all_xy[i] = [b.x*2,b.y*2]					
										       
						if(master_flag):	
						
							print("UUUUUUUUUUUUUUU")		       
							
							if(len(s.swarm)-1==i):
								try:
									s1=str(all_xy[0][0])+","+str(all_xy[0][1])
								except:
									pass
								try:
									s2=str(all_xy[1][0])+","+str(all_xy[1][1])
								except:
									pass
								try:
									s3=str(all_xy[2][0])+","+str(all_xy[2][1])
								except:
									pass
								#s=1
								print(s1,s2,"s")
								
								try:
									p_sock1.sendto(str(s1).encode(), p_server_address1)
								except:
									pass
								try:
									p_sock2.sendto(str(s2).encode(), p_server_address2)
								except:
									pass
								try:							
									p_sock3.sendto(str(s3).encode(), p_server_address3)
								except:
									pass
								a=receive_xy()							
									
							else:
								print("JJJJJJJJ")
								a=receive_xy()
						if i==0:
						    robot1_x,robot1_y={b.x},{b.y}
						elif i==1:
						    robot2_x,robot2_y={b.x},{b.y}
						elif i==2:
						    robot3_x,robot3_y={b.x},{b.y}
						elif i==3:
						    robot4_x,robot4_y={b.x},{b.y}
						elif i==4:
						    robot5_x,robot5_y={b.x},{b.y}
						elif i==5:
						    robot6_x,robot6_y={b.x},{b.y}
						elif i==6:
						    robot7_x,robot7_y={b.x},{b.y}
						elif i==7:
						    robot8_x,robot8_y={b.x},{b.y}
						elif i==8:
						    robot9_x,robot9_y={b.x},{b.y}
						elif i==9:
						    robot10_x,robot10_y={b.x},{b.y}
						elif i==10:
						    robot11_x,robot11_y={b.x},{b.y}
						elif i==11:
						    robot12_x,robot12_y={b.x},{b.y}
						elif i==12:
						    robot13_x,robot13_y={b.x},{b.y}
						elif i==13:
						    robot14_x,robot14_y={b.x},{b.y}
						elif i==14:
						    robot15_x,robot15_y={b.x},{b.y}
						elif i==15:
						    robot16_x,robot16_y={b.x},{b.y}
						else:
						    print('invalid')
						msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
					       str(robot2_x) + ',' + str(robot2_y) + ',' +
					       str(robot3_x) + ',' + str(robot3_y) + ',' +
					       str(robot4_x) + ',' + str(robot4_y) + ',' +
					       str(robot5_x) + ',' + str(robot5_y) + ',' +
					       str(robot6_x) + ',' + str(robot6_y) + ',' +
					       str(robot7_x) + ',' + str(robot7_y) + ',' +
					       str(robot8_x) + ',' + str(robot8_y)+',' +
					       str(robot9_x) + ',' + str(robot9_y)+',' +
					       str(robot10_x) + ',' + str(robot10_y))
									       
					area_covered=s.update_grid()				
					#sent = sock.sendto(str(msg).encode(), server_address)				
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)				
					#gui.update_trajectory_plot()
					#print("!!!!!!!!!!area_covered",area_covered)
					#coverage_area = (len(visited_positions) / (s.grid.size)) * 1000
					#print(f"Area covered = {coverage_area:.3f}%")		
					#elapsed_time = time.time() - search_start_time
					#gui.show_coverage(area_covered,elapsed_time)         
					area=gui.show_coverage(area_covered,elapsed_time)
					print("!!!!!!!!!!!!AREA covered!!!!!!!!",area*10,elapsed_time)
					msg=(str('search')+','+str(area*10)+','+str(elapsed_time))
					#sent = sock.sendto(str(msg).encode(), server_address)
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)				
					#s.update_grid()
					#gui.update()
					s.time_elapsed += 1   
					#print("NNNNNNNNNNNN",index)
					#if index.startswith(b'move_bot'): 	
					"""			
					if(index==b"move_bot"):
						move_bot_flag=True
						print("explore_bot_goal!!!!!!!!!!!!")	
						index, address = sock3.recvfrom(1024)				
						print("index",index)
						decoded_index = index.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
						f,uav, goal_lat, goal_lon = decoded_index.split(",")
						#uav,goalx,goaly=str(index).split(",")
						print(uav, goal_lat, goal_lon)
						goalx,goaly = locatePosition.geoToCart (origin, endDistance, [goal_lat, goal_lon])
						print("x,y",goalx,goaly)
						goal_bot_num=int(str(uav))
						print(goal_bot_num)
						goal_position=[float(goalx/2),float(goaly/2)]
						print(goal_position)
						goal_bot_num=goal_bot_num-1
						#specific_bot_goal_flag=True
					print("JJJJMM")
					"""
					if(index==b"stop") or (flag_stop):
						search_flag=False
						break
					
					if(index==b"aggregate") or (aggregate_flag):
						search_flag=False
						aggregate_flag=True
						break
					
							
						
						
		if(data==b"aggregate") or (aggregate_flag):
			search_flag=False
			sent = graph_socket.sendto(str("aggregate").encode(), graph_server_address)				
			index="data"	
			print("Aggregate!!!!")
			
			multiple_goals=[(415.55493438625564,456.51735869880645), (83.48744302662308,101.11535740333234), (226.0971604993888,244.04267706836725), (136.51502429278077,558.9285689733798), (261.3148828764992,547.2445918621977), (464.04383674010165,595.2929068098884), (563.7374435516844,618.4580193887477), (886.6281372464044,191.49529501331313), (626.7329941104032,337.6688861035689), (454.8685837758423,495.1852817532512), (451.5043231762099,372.4179270857997), (451.5043231762099,372.4179270857997)]
			
			
			bot_paths={
				   0:[multiple_goals[0],multiple_goals[1],multiple_goals[4]],				   
				   1:[multiple_goals[1],multiple_goals[4]],				   
				   2:[multiple_goals[2],multiple_goals[1],multiple_goals[4]],				   
				   3:[multiple_goals[3],multiple_goals[4]],				   
				   4:[multiple_goals[4]],
				   5:[multiple_goals[5],multiple_goals[6],multiple_goals[4]],
				   6:[multiple_goals[6],multiple_goals[4]],
				   7:[multiple_goals[7],multiple_goals[10],multiple_goals[6],multiple_goals[4]],
				   8:[multiple_goals[8],multiple_goals[1],multiple_goals[4]],
				   9:[multiple_goals[9],multiple_goals[2],multiple_goals[1],multiple_goals[4]],
				   10:[multiple_goals[10],multiple_goals[6],multiple_goals[4]],
				   11:[multiple_goals[11],multiple_goals[4]],
			}
			
			
			YOUR_GOAL_THRESHOLD_DISTANCE=15
			YOUR_THRESHOLD_DISTANCE=15
			current_goal_index = [0] * len(vehicles)			
			goal_table=[0]*len(vehicles)
			print("goal_table",goal_table)
			current_table=[0]*len(vehicles)
			length_arr=[0]*len(vehicles)
			new_length_arr=[0]*len(vehicles)
			count=[0]*len(vehicles)
			step=0
			all_bot_reach_flag_rev=False
			bot_array_rev=[0]*len(vehicles)
			while True:
				#time.sleep(0.01)
				print("JJJJJJJJJ")
				if(return_height_flag):
					break
				#print("############")
				step+=1
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				#print("step",step)
				if(step==1):										
					for i,b in enumerate(s.swarm):
						#print("************")
						#print("potf.reached_goals",potf.reached_goals)							
						#if(potf.reached_goals[i]==False):
						current_position = [b.x,b.y]
						nearest_goal = min(multiple_goals, key=lambda goal: distance.euclidean(current_position, goal))
						#print("current_position , nearest_goal",current_position,nearest_goal)
						goal_table[i]=multiple_goals.index(nearest_goal)
						#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
						print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)	
				
				else:										
					for i,b in enumerate(s.swarm):											
						if(vehicle_lost_flag):
							vehicle_lost_flag=True
							x=remove_vehicle()
							print(x)
						heartbeat[i]=vehicles[i].last_heartbeat
						#print( "heartbeat",heartbeat)
						#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
						#print("slave_heal_ip[i]",slave_heal_ip[i])
						if(heartbeat[i]>10):
							#print("Vehicle ", i+1 ,"No heartbeat")   	
							lost_vehicle_num=i+1
							print("lostvehicle",lost_vehicle_num)   
							vehicle_lost_flag=True  
							#remove_flag=True           		
							message= "vehicle "+str(i+1)+" has no heartbeat"                   		
							sock1.sendto(str(message).encode(), server_address1) 
						current_position = [b.x,b.y]
						#print("current_position",current_position)
						
						#count[goal_table[i]]=count[goal_table[i]]+1
						#print("counter array",count)
						#print("BOT {} reached",i)
						#print("goal_table[goal_index]",goal_table)
						ind=goal_table[i]
						#print("ind",ind)
						next_goal=bot_paths[ind]
						#print("next_goal",next_goal)
						if(step==2):
							length_arr[i]=len(bot_paths[ind])
							new_length_arr[i]=length_arr[i]
						if(count[i]==length_arr[i]):
							continue
						
						if(len(bot_paths[ind])<1):							
							print("BOT {i} goal reached",i)
							continue
						
						#goal=bot_paths[goal_table[i]][count[i]]
						
						#cmd =cvg.goal_area_cvg(i,b,goal)
						#cmd.exec(b)
						goal=agg_goal_point
						cmd = base_control.base_control(i,b,goal)*10
						cmd+= base_control.obstacle_avoidance(i,b,goal)*50
						cmd += aggr_centroid(b, neighbourhood_radius=500 ,single_state=False, state=0)*50
						#exp_weight_function=hyperbolic						
						t = b.sim.time_elapsed
						#print(t,b.sim.time_elapsed,"b.s.time_elapsed")
						weight_exp = hyperbolic(t)
						print(weight_exp,"weight_exp")
						cmd += exp.explore(b)*weight_exp
						
						cmd.exec(b)											
						
						
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])						
						if(dx<=5 and dy<=5):									
							#print("Goal_reached!!!!!!!!!!!")	
							new_length_arr[i]=new_length_arr[i]-1
							print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
							count[i]+=1
							#bot_array_rev[i]=1
						print("count array",count)
						#if(goal==bot_paths[goal_table[i]][-1]):
						if(count[i]>=1):
							print("Drone ",i,"reached")
							bot_array_rev[i]=1
						print("bot_array_rev",bot_array_rev)
						count_1=0	
						for j in range(len(vehicles)):
							print("************")
							if(bot_array_rev[j]==1):
								count_1+=1
							print("count_1",count_1)
							if(count_1==len(vehicles)):
								#all_bot_reach_flag_1=True
								aggregate_flag=False
								return_height_flag=True
								print(return_height_flag,"return_height_flag")
								break
						"""		
						current_position =[b.x*2,b.y*2]
						#print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						#print ("Drone 1 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						#print("point1",point1)
						vehicles[i].simple_goto(point1)	
						"""
						all_xy[i] = [b.x*2,b.y*2]
						if(master_flag):							
							if(len(s.swarm)-1==i):
								try:
									s1=str(all_xy[0][0])+","+str(all_xy[0][1])
								except:
									pass
								try:
									s2=str(all_xy[1][0])+","+str(all_xy[1][1])
								except:
									pass
								try:
									s3=str(all_xy[2][0])+","+str(all_xy[2][1])
								except:
									pass
								#s=1
								print(s1,s2,"s")
								
								try:
									p_sock1.sendto(str(s1).encode(), p_server_address1)
								except:
									pass
								try:
									p_sock2.sendto(str(s2).encode(), p_server_address2)
								except:
									pass
								try:							
									p_sock3.sendto(str(s3).encode(), p_server_address3)
								except:
									pass
								a=receive_xy()							
									
							else:
								print("JJJJJJJJ")
								a=receive_xy()
						if i==0:
						    robot1_x,robot1_y={b.x},{b.y}
						elif i==1:
						    robot2_x,robot2_y={b.x},{b.y}
						elif i==2:
						    robot3_x,robot3_y={b.x},{b.y}
						elif i==3:
						    robot4_x,robot4_y={b.x},{b.y}
						elif i==4:
						    robot5_x,robot5_y={b.x},{b.y}
						elif i==5:
						    robot6_x,robot6_y={b.x},{b.y}
						elif i==6:
						    robot7_x,robot7_y={b.x},{b.y}
						elif i==7:
						    robot8_x,robot8_y={b.x},{b.y}
						elif i==8:
						    robot9_x,robot9_y={b.x},{b.y}
						elif i==9:
						    robot10_x,robot10_y={b.x},{b.y}
						elif i==10:
						    robot11_x,robot11_y={b.x},{b.y}
						elif i==11:
						    robot12_x,robot12_y={b.x},{b.y}
						elif i==12:
						    robot13_x,robot13_y={b.x},{b.y}
						elif i==13:
						    robot14_x,robot14_y={b.x},{b.y}
						elif i==14:
						    robot15_x,robot15_y={b.x},{b.y}
						elif i==15:
						    robot16_x,robot16_y={b.x},{b.y}
						else:
						    print('invalid')
						msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
					       str(robot2_x) + ',' + str(robot2_y) + ',' +
					       str(robot3_x) + ',' + str(robot3_y) + ',' +
					       str(robot4_x) + ',' + str(robot4_y) + ',' +
					       str(robot5_x) + ',' + str(robot5_y) + ',' +
					       str(robot6_x) + ',' + str(robot6_y) + ',' +
					       str(robot7_x) + ',' + str(robot7_y) + ',' +
					       str(robot8_x) + ',' + str(robot8_y) + ',' +
					       str(robot9_x) + ',' + str(robot9_y) + ',' +
					       str(robot10_x) + ',' + str(robot10_y))
									       
								
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					
					if(index==b"stop"):
						sent = graph_socket.sendto(str("stop").encode(), graph_server_address)				
						index="data"
						aggregate_flag=False
						flag_stop=True
						data=b"stop"
						break
					
					if(index==b"return"):
						return_flag=True
						return_height_flag=True						
							
					if(return_height_flag):
						velocity_flag=True	
						same_alt_flag=False
						same_height=30
						alt=[0]*len(vehicles)
						alt_count=[0]*len(vehicles)
						alt_count1=0
						print("Velocity zero called##############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")	
						while True:	
							if(index==b"stop"):
								sent = graph_socket.sendto(str("stop").encode(), graph_server_address)				
								index="data"
								aggregate_flag=False
								return_height_flag=False
								#return_flag=True
								flag_stop=True
								data=b"stop"
								break
							if(return_flag):
								print("REturn####")
								break				
							print("velocity_flag",velocity_flag)						
							if(vehicle_lost_flag):
								vehicle_lost_flag=True
								x=remove_vehicle()
								print(x)
							for i, b in enumerate(s.swarm):
								
								#print("Velocity zero called##############!!!!!!!!!!!")
								cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
								cmd.exec(b)
								"""			
								value=[b.x*2,b.y*2]												
								#gui.show_coverage(area_covered,elapsed_time)
								#print("Velocity Bot State",b.state)

								print("Drone 1 position",b.x,b.y)
								lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
								#print ("Drone 1 lat,lon", lat,lon)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								#print("point1",point1)
								vehicles[i].simple_goto(point1)
								"""
								all_xy[i] = [b.x*2,b.y*2]					
								if(master_flag):
									if(len(s.swarm)-1==i):
										try:
											s1=str(all_xy[0][0])+","+str(all_xy[0][1])
										except:
											pass
										try:
											s2=str(all_xy[1][0])+","+str(all_xy[1][1])
										except:
											pass
										try:
											s3=str(all_xy[2][0])+","+str(all_xy[2][1])
										except:
											pass
										#s=1
										print(s1,s2,"s")
										
										try:
											p_sock1.sendto(str(s1).encode(), p_server_address1)
										except:
											pass
										try:
											p_sock2.sendto(str(s2).encode(), p_server_address2)
										except:
											pass
										try:							
											p_sock3.sendto(str(s3).encode(), p_server_address3)
										except:
											pass
										a=receive_xy()							
											
									else:
										print("JJJJJJJJ")
										a=receive_xy()
								print("return_flag",return_flag)
								for i,vehicle in enumerate(vehicles):
									heartbeat[i]=vehicles[i].last_heartbeat
									#print( "heartbeat",heartbeat)
									#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
									#print("slave_heal_ip[i]",slave_heal_ip[i])
									if(heartbeat[i]>10):
										#print("Vehicle ", i+1 ,"No heartbeat")   	
										lost_vehicle_num=i+1
										print("lostvehicle",lost_vehicle_num)   
										vehicle_lost_flag=True  
										
										message= "vehicle "+str(i+1)+" has no heartbeat"                   		
										sock1.sendto(str(message).encode(), server_address1) 	
									alt[i]=vehicle.location.global_relative_frame.alt 
									print("alt[vehicle]",alt[i])
									#if same_height - 1.5 <= alt[i] <= same_height+1.5: 											
									if different_height[i] - 1.5 <= alt[i] <= different_height[i]+1.5:
										alt_count[i]=1
										#alt_count1+=1
										if all(count==1 for count in alt_count):		
										#if(alt_count1==len(vehicles)):
											print("Reached target altitude")
											#return_flag=True
											return_height_flag=False
											return_flag=True
											break
				
					
		if(data==b"return") or (return_flag):
			index="data"
			sent = graph_socket.sendto(str("return").encode(), graph_server_address)				
			position=[]
			for i,vehicle in enumerate(vehicles):
			    lat = vehicle.location.global_relative_frame.lat
			    lon = vehicle.location.global_relative_frame.lon

			       # Process the lat and lon as needed
			    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
			    current_lat_lon.append((lat,lon))			    
			    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
			    print("x,y",x/2,y/2)
			    position.append((x / 2, y / 2))
			    print(position,"position",position[0][0],position[0][1])
			    uav_home_pos[0]=(x / 2, y / 2)

			data="uav"+" , "+" 1 "+" , "+"192.168.29.151"+" , "+str(home_position[0][0])+" , "+str(home_position[0][1])+" , "+str(position[0][0])+" , "+str(position[0][1])
			print(data,"data")	
			for i in range(6):
				time.sleep(0.1)			
				sent = uav1_sock.sendto(data.encode(), uav1_server_address)
				time.sleep(0.1)
				sent = uav2_sock.sendto(data.encode(), uav2_server_address)
				time.sleep(0.1)
				sent = uav3_sock.sendto(data.encode(), uav3_server_address)
				#sent = uav4_sock.sendto(data.encode(), uav4_server_address)
				#sent = uav5_sock.sendto(data.encode(), uav5_server_address)	f
			
			num_uavs=global_uavs.count(1)
			print(num_uavs,home_pos,uav_home_pos,"num_uavs,home_pos,uav_home_pos")	
			s = sim.Simulation(uav_home_pos,num_bots=len(vehicles), env_name=file_name)
			#s = sim.Simulation(num_bots, env_name='rectangles2' )
			#gui = viz.Gui(s)
			#gui.show_env()
			#gui.show_bots()
			#gui.update()
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			for b in s.swarm:											
				heartbeat[i]=vehicles[i].last_heartbeat
				#print( "heartbeat",heartbeat)
				#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
				#print("slave_heal_ip[i]",slave_heal_ip[i])
				if(heartbeat[i]>10):
					#print("Vehicle ", i+1 ,"No heartbeat")   	
					lost_vehicle_num=i+1
					print("lostvehicle",lost_vehicle_num)   
					vehicle_lost_flag=True  
					#remove_flag=True           		
					message= "vehicle "+str(i+1)+" has no heartbeat"                   		
					sock1.sendto(str(message).encode(), server_address1) 
				multiple_goals=return_multiple_goals
				bot_paths={
					   0:[multiple_goals[0]],				   
					   1:[multiple_goals[1],multiple_goals[0]],
					   2:[multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					   4:[multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					   5:[multiple_goals[5],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					   6:[multiple_goals[6],multiple_goals[5],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					   7:[multiple_goals[7],multiple_goals[6],multiple_goals[5],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					   8:[multiple_goals[8],multiple_goals[7],multiple_goals[6],multiple_goals[5],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
					  

				}
				
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * len(vehicles)			
				goal_table=[0]*len(vehicles)
				print("goal_table",goal_table)
				current_table=[0]*len(vehicles)
				length_arr=[0]*len(vehicles)
				new_length_arr=[0]*len(vehicles)
				count=[0]*len(vehicles)
				step=0
				search_flag=False
				bot_array_return=[0]*len(vehicles)
				all_bot_reach_flag_1=False
				print("return_flag################",return_flag)
				while 1:
					
					if(home_flag):
						break					
					if(len(vehicles)==10):
						time.sleep(0.003)
					elif(len(vehicles)==9):
						time.sleep(0.008)
					elif(len(vehicles)==8):
						time.sleep(0.01)
					elif(len(vehicles)==7):
						time.sleep(0.01)
					elif(len(vehicles)==6):
						time.sleep(0.009)#verified
					elif(len(vehicles)==5):
						time.sleep(0.012)#verified
					elif(len(vehicles)==4):
						time.sleep(0.015)
					elif(len(vehicles)==3):
						time.sleep(0.018)
					elif(len(vehicles)==2):
						time.sleep(0.021)
					elif(len(vehicles)==1):
						time.sleep(0.024)
					step+=1
					if(vehicle_lost_flag):
						vehicle_lost_flag=True
						x=remove_vehicle()
						print(x)

					if(step==1):
						print("step",step)
						for i,b in enumerate(s.swarm):
							#print("potf.reached_goals",potf.reached_goals)							
							#if(potf.reached_goals[i]==False):
							current_position = [b.x,b.y]
							#nearest_goal = min(multiple_goals1, key=lambda goal: distance.euclidean(current_position, goal))
							#print("current_position , nearest_goal",current_position,nearest_goal)
							#goal_ind=multiple_goals.index(nearest_goal)
							with open('/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv','rt')as text:
								data = csv.reader(text)
								for row in data: 
									data = (row)
									print ("loc",data[-1])
									nextwaypoint=int(data[-1])							
							
							print("nextwaypoint",nextwaypoint)
							goal_table[i]=nextwaypoint
							'''
							print("goal_ind",goal_ind)
							print(len(bot_paths[goal_ind]),"len(bot_paths[goal_ind])")
							print("len(bot_paths[goal_ind+1])",len(bot_paths[goal_ind+1]))
							if (len(bot_paths[goal_ind]))>(len(bot_paths[goal_ind+1])):
								goal_table[i]=multiple_goals.index(nearest_goal)+1								
								print("multiple_goals.index(nearest_goal)+1",multiple_goals.index(nearest_goal)+1)								
							#print("current_position , nearest_goal",current_position,nearest_goal)
							else:
								goal_table[i]=multiple_goals.index(nearest_goal)
							'''
							#goal_table[i]=multiple_goals.index(nearest_goal)
							#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
							print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
							
					
					else:
						for i,b in enumerate(s.swarm):
							current_position = [b.x,b.y]
							heartbeat[i]=vehicles[i].last_heartbeat
							#print( "heartbeat",heartbeat)
							#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
							#print("slave_heal_ip[i]",slave_heal_ip[i])
							if(heartbeat[i]>10):
								#print("Vehicle ", i+1 ,"No heartbeat")   	
								lost_vehicle_num=i+1
								print("lostvehicle",lost_vehicle_num)   
								vehicle_lost_flag=True  
								#remove_flag=True           		
								message= "vehicle "+str(i+1)+" has no heartbeat"                   		
								sock1.sendto(str(message).encode(), server_address1) 
									#print("current_position",current_position)
							
							#count[goal_table[i]]=count[goal_table[i]]+1
							#print("counter array",count)
							#print("BOT {} reached",i)
							#print("goal_table[goal_index]",goal_table)
							ind=goal_table[i]
							#print("ind",ind)
							next_goal=bot_paths[ind]
							#print("next_goal",next_goal)
							#print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
							if(step==2):
								length_arr[i]=len(bot_paths[ind])
								new_length_arr[i]=length_arr[i]
							if(count[i]==length_arr[i]):
								continue
							#print("length_arr",length_arr)
							#print("new_length_arr",new_length_arr)
							if(len(bot_paths[ind])<1):							
								print("BOT {i} goal reached",i)
								continue
							#print("len(bot_paths[ind]",len(bot_paths[ind]))
							#for i,b in enumerate(s.swarm):
							#current_position=[b.x,b.y]
							goal=bot_paths[goal_table[i]][count[i]]
							#print("goal",goal)
							#Base control
							#cmd = base_control.base_control(i,b,goal)
							#cmd+= base_control.obstacle_avoidance(i,b,goal)
							
							#Behaviour
							#cmd+=line(b)
							#cmd =cvg.goal_area_cvg(i,b,goal,use_base_control=True, exp_weight_params=[15.0,15.5],disp_weight_params=[30.0,30.0])
							cmd =cvg.goal_area_cvg(i,b,goal)
							#Execute
							cmd.exec(b)
							#print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])						
							#print("dx,dy",dx,dy)
							if(dx<=10 and dy<=10):
								bot_array_return[i]=1
								#print("bot_array",bot_array)
	
							count_1=0
							#print("count_1",count_1)
							for j in range(len(vehicles)):
								#print("************")
								if(bot_array_return[j]==1):
									count_1+=1
								if(count_1==len(vehicles)):
									count_1=0
									bot_array_return=[0]*len(vehicles)
									all_bot_reach_flag_1=True

							#print("bot_array",bot_array)
							if (all_bot_reach_flag_1==True):								
								#print("Goal_reached!!!!!!!!!!!")	
								with open(r'/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
									fieldnames = ['waypoint']
									writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
									writer.writerow({'waypoint':multiple_goals.index(goal)})	
								new_length_arr[i]=new_length_arr[i]-1
								print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
								#count[i]+=1
								for k in range(len(vehicles)):
									count[k]+=1
								all_bot_reach_flag_1=False
								bot_array_return=[0]*len(vehicles)
								#print("goal,bot_paths[ind][-1]",goal,bot_paths[ind][-1])
								if (goal==bot_paths[ind][-1]):
									print("Break")
									return_flag=False
									home_flag=True						
									break		
							"""
							current_position = [b.x*2,b.y*2]
							#print("Drone 1 position",b.x,b.y)
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							#print ("Drone 1 lat,lon", lat,lon)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
							"""
							all_xy[i] = [b.x*2,b.y*2]					
										       
							if(master_flag):	
							
								print("UUUUUUUUUUUUUUU")		       
								
								if(len(s.swarm)-1==i):
									try:
										s1=str(all_xy[0][0])+","+str(all_xy[0][1])
									except:
										pass
									try:
										s2=str(all_xy[1][0])+","+str(all_xy[1][1])
									except:
										pass
									try:
										s3=str(all_xy[2][0])+","+str(all_xy[2][1])
									except:
										pass
									#s=1
									print(s1,s2,"s")
									
									try:
										p_sock1.sendto(str(s1).encode(), p_server_address1)
									except:
										pass
									try:
										p_sock2.sendto(str(s2).encode(), p_server_address2)
									except:
										pass
									try:							
										p_sock3.sendto(str(s3).encode(), p_server_address3)
									except:
										pass
									a=receive_xy()							
										
								else:
									print("JJJJJJJJ")
									a=receive_xy()
							if i==0:
							    robot1_x,robot1_y={b.x},{b.y}
							elif i==1:
							    robot2_x,robot2_y={b.x},{b.y}
							elif i==2:
							    robot3_x,robot3_y={b.x},{b.y}
							elif i==3:
							    robot4_x,robot4_y={b.x},{b.y}
							elif i==4:
							    robot5_x,robot5_y={b.x},{b.y}
							elif i==5:
							    robot6_x,robot6_y={b.x},{b.y}
							elif i==6:
							    robot7_x,robot7_y={b.x},{b.y}
							elif i==7:
							    robot8_x,robot8_y={b.x},{b.y}
							elif i==8:
							    robot9_x,robot9_y={b.x},{b.y}
							elif i==9:
							    robot10_x,robot10_y={b.x},{b.y}
							elif i==10:
							    robot11_x,robot11_y={b.x},{b.y}
							elif i==11:
							    robot12_x,robot12_y={b.x},{b.y}
							elif i==12:
							    robot13_x,robot13_y={b.x},{b.y}
							elif i==13:
							    robot14_x,robot14_y={b.x},{b.y}
							elif i==14:
							    robot15_x,robot15_y={b.x},{b.y}
							elif i==15:
							    robot16_x,robot16_y={b.x},{b.y}
							else:
							    print('invalid')
							msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
						       str(robot2_x) + ',' + str(robot2_y) + ',' +
						       str(robot3_x) + ',' + str(robot3_y) + ',' +
						       str(robot4_x) + ',' + str(robot4_y) + ',' +
						       str(robot5_x) + ',' + str(robot5_y) + ',' +
						       str(robot6_x) + ',' + str(robot6_y) + ',' +
						       str(robot7_x) + ',' + str(robot7_y) + ',' +
						       str(robot8_x) + ',' + str(robot8_y) + ',' +
						       str(robot9_x) + ',' + str(robot9_y) + ',' +
						       str(robot10_x) + ',' + str(robot10_y))
										       
									
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)													
						#print("msg",msg)				
					
					#gui.update()
					if(index==b"stop"):
						print("^^^^^^^^^^")						
						print("return_flag################",return_flag)
						return_flag=False
						start_flag=False
						print("$$$$$$$$$$$$$")
						break
													
		if(data==b"home") or (home_flag):
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			sent = graph_socket.sendto(str("home").encode(), graph_server_address)				
			bot_array_home=[0]*len(vehicles)
			all_bot_reach_flag_home=False
			print("Home.......",home_pos)
				
			while 1:
				if(len(vehicles)==10):
					time.sleep(0.003)
				elif(len(vehicles)==9):
					time.sleep(0.008)
				elif(len(vehicles)==8):
					time.sleep(0.01)
				elif(len(vehicles)==7):
					time.sleep(0.01)
				elif(len(vehicles)==6):
					time.sleep(0.009)#verified
				elif(len(vehicles)==5):
					time.sleep(0.012)#verified
				elif(len(vehicles)==4):
					time.sleep(0.015)
				elif(len(vehicles)==3):
					time.sleep(0.018)
				elif(len(vehicles)==2):
					time.sleep(0.021)
				elif(len(vehicles)==1):
					time.sleep(0.024)
				print("JJJJJJ,home_flag1",home_flag1)
				if(home_flag1):
					break
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				for i,b in enumerate(s.swarm):					
					heartbeat[i]=vehicles[i].last_heartbeat
					print( "heartbeat",heartbeat)
					#print(" Last Heartbeat: %s" , vehicles[i].last_heartbeat)
					#print("slave_heal_ip[i]",slave_heal_ip[i])
					if(heartbeat[i]>10):
						#print("Vehicle ", i+1 ,"No heartbeat")   	
						lost_vehicle_num=i+1
						print("lostvehicle",lost_vehicle_num)   
						vehicle_lost_flag=True  
						#remove_flag=True           		
						message= "vehicle "+str(i+1)+" has no heartbeat"                   		
						sock1.sendto(str(message).encode(), server_address1) 
					current_position = [b.x,b.y]
					print("current_position",current_position)
					#cmd =cvg.goal_area_cvg(i,b,home_pos[i],use_base_control=True, exp_weight_params=[15.0,15.5],disp_weight_params=[30.0,30.0])
					cmd =cvg.goal_area_cvg(i,b,home_pos[i])
					goal=home_pos[i]
					#Execute
					cmd.exec(b)
					
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])						
					print("dx,dy",dx,dy)
					
					if(dx<=0.5 and dy<=0.5):
						bot_array_home[i]=1
						#print("bot_array",bot_array)	
					count_home=0
					print("count_home",count_home)
					for j in range(len(vehicles)):
						#print("************")
						if(bot_array_home[j]==1):
							count_home+=1
						if(count_home==len(vehicles)):
							count_home=0
							bot_array_home=[0]*len(vehicles)
							all_bot_reach_flag_home=True

					#print("bot_array",bot_array)
					if (all_bot_reach_flag_home==True):
						with open(r'/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
							fieldnames = ['waypoint']
							writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
							writer.writerow({'waypoint':-1})	
						home_flag1=True
							
					"""							
					current_position = [b.x*2,b.y*2]
					#print("Drone 1 position",b.x,b.y)
					lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
					#print ("Drone 1 lat,lon", lat,lon)
					if same_alt_flag:
						point1 = LocationGlobalRelative(lat,lon,same_height)
					else:
						point1 = LocationGlobalRelative(lat,lon,different_height[i])
					vehicles[i].simple_goto(point1)
					"""
					all_xy[i] = [b.x*2,b.y*2]					
										       
					if(master_flag):	
					
						print("UUUUUUUUUUUUUUU")		       
						
						if(len(s.swarm)-1==i):
							try:
								s1=str(all_xy[0][0])+","+str(all_xy[0][1])
							except:
								pass
							try:
								s2=str(all_xy[1][0])+","+str(all_xy[1][1])
							except:
								pass
							try:
								s3=str(all_xy[2][0])+","+str(all_xy[2][1])
							except:
								pass
							#s=1
							print(s1,s2,"s")
							
							try:
								p_sock1.sendto(str(s1).encode(), p_server_address1)
							except:
								pass
							try:
								p_sock2.sendto(str(s2).encode(), p_server_address2)
							except:
								pass
							try:							
								p_sock3.sendto(str(s3).encode(), p_server_address3)
							except:
								pass
							a=receive_xy()							
								
						else:
							print("JJJJJJJJ")
							a=receive_xy()
					if i==0:
					    robot1_x,robot1_y={b.x},{b.y}
					elif i==1:
					    robot2_x,robot2_y={b.x},{b.y}
					elif i==2:
					    robot3_x,robot3_y={b.x},{b.y}
					elif i==3:
					    robot4_x,robot4_y={b.x},{b.y}
					elif i==4:
					    robot5_x,robot5_y={b.x},{b.y}
					elif i==5:
					    robot6_x,robot6_y={b.x},{b.y}
					elif i==6:
					    robot7_x,robot7_y={b.x},{b.y}
					elif i==7:
					    robot8_x,robot8_y={b.x},{b.y}
					elif i==8:
					    robot9_x,robot9_y={b.x},{b.y}
					elif i==9:
					    robot10_x,robot10_y={b.x},{b.y}
					elif i==10:
					    robot11_x,robot11_y={b.x},{b.y}
					elif i==11:
					    robot12_x,robot12_y={b.x},{b.y}
					elif i==12:
					    robot13_x,robot13_y={b.x},{b.y}
					elif i==13:
					    robot14_x,robot14_y={b.x},{b.y}
					elif i==14:
					    robot15_x,robot15_y={b.x},{b.y}
					elif i==15:
					    robot16_x,robot16_y={b.x},{b.y}
					else:
					    print('invalid')
					msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
				       str(robot2_x) + ',' + str(robot2_y) + ',' +
				       str(robot3_x) + ',' + str(robot3_y) + ',' +
				       str(robot4_x) + ',' + str(robot4_y) + ',' +
				       str(robot5_x) + ',' + str(robot5_y) + ',' +
				       str(robot6_x) + ',' + str(robot6_y) + ',' +
				       str(robot7_x) + ',' + str(robot7_y) + ',' +
				       str(robot8_x) + ',' + str(robot8_y) + ',' +
				       str(robot9_x) + ',' + str(robot9_y) + ',' +
				       str(robot10_x) + ',' + str(robot10_y))
								       
							
				sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
				#gui.update()	
				if(index==b"stop"):					
					home_flag1=True
					home_flag=False
					sent = graph_socket.sendto(str("stop").encode(), graph_server_address)				
					break
				
				
		if(data==b"home_goto") or (home_goto_flag):
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			sent = graph_socket.sendto(str("home").encode(), graph_server_address)				
			bot_array_home=[0]*len(vehicles)
			all_bot_reach_flag_home=False
			print("Home_goto.......")
			s = sim.Simulation(home_pos,num_bots=len(vehicles), env_name=file_name )

			if(vehicle_lost_flag):
				vehicle_lost_flag=True
				x=remove_vehicle()
				print(x)
			for i,b in enumerate(s.swarm):					
				heartbeat[i]=vehicles[i].last_heartbeat
				#print( "heartbeat",heartbeat)					
				if(heartbeat[i]>10):
					#print("Vehicle ", i+1 ,"No heartbeat")   	
					lost_vehicle_num=i+1
					print("lostvehicle",lost_vehicle_num)   
					vehicle_lost_flag=True  
					#remove_flag=True           		
					message= "vehicle "+str(i+1)+" has no heartbeat"                   		
					sock1.sendto(str(message).encode(), server_address1) 				
				"""			
				#current_position = [home_pos[i][0]*2,home_pos[i][1]*2]
				#print("Drone 1 position",b.x,b.y)
				lat,lon = locatePosition.cartToGeo (origin, endDistance, [home_pos[i][0]*2,home_pos[i][1]*2])
				#print ("Drone 1 lat,lon", lat,lon)
				if same_alt_flag:
					point1 = LocationGlobalRelative(lat,lon,same_height)
				else:
					point1 = LocationGlobalRelative(lat,lon,different_height[i])
				vehicles[i].simple_goto(point1)
				"""
				all_xy[i] = [b.x*2,b.y*2]					
										       
				if(master_flag):	
				
					print("UUUUUUUUUUUUUUU")		       
					
					if(len(s.swarm)-1==i):
						try:
							s1=str(all_xy[0][0])+","+str(all_xy[0][1])
						except:
							pass
						try:
							s2=str(all_xy[1][0])+","+str(all_xy[1][1])
						except:
							pass
						try:
							s3=str(all_xy[2][0])+","+str(all_xy[2][1])
						except:
							pass
						#s=1
						print(s1,s2,"s")
						
						try:
							p_sock1.sendto(str(s1).encode(), p_server_address1)
						except:
							pass
						try:
							p_sock2.sendto(str(s2).encode(), p_server_address2)
						except:
							pass
						try:							
							p_sock3.sendto(str(s3).encode(), p_server_address3)
						except:
							pass
						a=receive_xy()							
							
					else:
						print("JJJJJJJJ")
						a=receive_xy()
				if i==0:
				    robot1_x,robot1_y={b.x},{b.y}
				elif i==1:
				    robot2_x,robot2_y={b.x},{b.y}
				elif i==2:
				    robot3_x,robot3_y={b.x},{b.y}
				elif i==3:
				    robot4_x,robot4_y={b.x},{b.y}
				elif i==4:
				    robot5_x,robot5_y={b.x},{b.y}
				elif i==5:
				    robot6_x,robot6_y={b.x},{b.y}
				elif i==6:
				    robot7_x,robot7_y={b.x},{b.y}
				elif i==7:
				    robot8_x,robot8_y={b.x},{b.y}
				elif i==8:
				    robot9_x,robot9_y={b.x},{b.y}
				elif i==9:
				    robot10_x,robot10_y={b.x},{b.y}
				elif i==10:
				    robot11_x,robot11_y={b.x},{b.y}
				elif i==11:
				    robot12_x,robot12_y={b.x},{b.y}
				elif i==12:
				    robot13_x,robot13_y={b.x},{b.y}
				elif i==13:
				    robot14_x,robot14_y={b.x},{b.y}
				elif i==14:
				    robot15_x,robot15_y={b.x},{b.y}
				elif i==15:
				    robot16_x,robot16_y={b.x},{b.y}
				else:
				    print('invalid')
				msg = (str(robot1_x) + ',' + str(robot1_y) + ',' +
			       str(robot2_x) + ',' + str(robot2_y) + ',' +
			       str(robot3_x) + ',' + str(robot3_y) + ',' +
			       str(robot4_x) + ',' + str(robot4_y) + ',' +
			       str(robot5_x) + ',' + str(robot5_y) + ',' +
			       str(robot6_x) + ',' + str(robot6_y) + ',' +
			       str(robot7_x) + ',' + str(robot7_y) + ',' +
			       str(robot8_x) + ',' + str(robot8_y) + ',' +
			       str(robot9_x) + ',' + str(robot9_y) + ',' +
			       str(robot10_x) + ',' + str(robot10_y))
							       
						
			sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
			#gui.update()
			with open(r'/home/dhaksha/Desktop/main/dce_swarm_nav/swarm_tasks-main/swarm_tasks/Examples/basic_tasks/pos.csv', 'w') as csvfile:
					fieldnames = ['waypoint']
					writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
					writer.writerow({'waypoint':-1})	
				#home_flag1=True	
			if(index==b"stop"):					
				home_goto_flag=False
				start_flag=False
				return_flag=False
				home_flag=False
				exit()				
				break		

	except:
		pass				
