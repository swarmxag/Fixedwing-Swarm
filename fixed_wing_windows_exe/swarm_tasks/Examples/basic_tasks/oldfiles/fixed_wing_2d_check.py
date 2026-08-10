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
graph_server_address = ('192.168.0.210', 12009)  #receive from .....rx.py

remove_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ('', 12008)  #receive from .....rx.py
sock2.bind(server_address2)
sock2.setblocking(0)
sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ('', 12002)  #receive from .....rx.py
sock3.bind(server_address3)
"""
uav_data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav_data_sock_server_address = ('', 12020)  #receive from .....rx.py
uav_data_sock.bind(uav_data_sock_server_address)
"""
uav1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav1_server_address = ('192.168.0.153', 12002)  #receive from .....rx.py
uav2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav2_server_address = ('192.168.0.155', 12002)  #receive from .....rx.py
uav3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav3_server_address = ('192.168.0.160', 12002)
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
#print(cwd)

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
		'''
		try:
			data1,address=sock2.recvfrom(1024)
			print("data11",data1)
			decoded_index = data1.decode('utf-8')
			n,goal_table=decoded_index.split(",",1)
			goal_table = goal_table.strip()
			print(n,goal_table,"DDDDFFFFFF")
			goal_table=json.loads(goal_table)
			print("goal_table",goal_table)
			with open(csv_path, 'a') as csvfile:
				fieldnames = ['waypoint']
				writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
				
				for t in goal_table:
					print("t",t)
					writer.writerow({'waypoint':t})	
			break	
			
		except:
			print("EXCEption")
			pass
		'''
			
	except:
		pass

	
disperse_multiple_goals=[]
start_multiple_goals=[]
return_multiple_goals=[]
goal_points=[]
agg_goal_point=[]
origin=[]
removed_uav_homepos_array=[]
area_covered_percent=0
if(file_name=="Tambaram_airport"):
	origin=(  12.898623, 80.113572)
	goal_points=[ (415.55493438625564,456.51735869880645), (83.48744302662308,101.11535740333234), (226.0971604993888,244.04267706836725), (136.51502429278077,558.9285689733798), (261.3148828764992,547.2445918621977), (464.04383674010165,595.2929068098884), (563.7374435516844,618.4580193887477), (886.6281372464044,191.49529501331313), (626.7329941104032,337.6688861035689), (454.8685837758423,495.1852817532512), (451.5043231762099,372.4179270857997), (607.4623794307759,284.5931240445683), (894.4390416274568,125.91201735517623), (562.0346303502632,520.6877743618948), (236.8430237814994,501.74563655736), (192.10840232012194,123.04275266307708), (331.4831385385884,271.46973276106223), (374.21119553304294,505.8049307660936),]
	disperse_multiple_goals=[ (83.48744302662308,101.11535740333234), (226.0971604993888,244.04267706836725), (136.51502429278077,558.9285689733798), (261.3148828764992,547.2445918621977), (464.04383674010165,595.2929068098884), (563.7374435516844,618.4580193887477), (886.6281372464044,191.49529501331313), (626.7329941104032,337.6688861035689), (454.8685837758423,495.1852817532512),(451.5043231762099,372.4179270857997),]
	agg_goal_point=[415.55493438625564,456.51735869880645]
	area_covered_percent=67
	
if(file_name=="Tambaram_runway"):
	 origin=(  12.898623, 80.113572)
	 goal_points=[ (185.95668989890575,580.615934042732), (314.9059293398766,509.0896752141942), (82.92808854687563,99.58233082538148), (191.0971623241269,213.25552727004242), (358.82522854635977,394.6546267756296), (449.06902885889286,490.5114371911169), (534.1464105396387,584.4680928613654), (541.7522071541887,384.13450136678097), (701.302608361422,291.91674355314655), (917.7195646637302,173.31541999078996), (412.72624952349014,453.9844188543948), (268.5657860365068,301.01140212270036), (793.1769137323977,242.11486263617155),]
	 #disperse_multiple_goals=[ (185.95668989890575,580.615934042732), (314.9059293398766,509.0896752141942), (82.92808854687563,99.58233082538148), (191.0971623241269,213.25552727004242), (358.82522854635977,394.6546267756296), (449.06902885889286,490.5114371911169), (534.1464105396387,584.4680928613654), (541.7522071541887,384.13450136678097), (701.302608361422,291.91674355314655), (917.7195646637302,173.31541999078996),]
	 disperse_multiple_goals=[]
	 start_multiple_goals=[ (309.4438942665647,454.5134963488491), (335.55872242863904,466.9516743958527), (355.25794289613196,491.6204200933454), (412.72624952349014,453.9844188543948)]

	 multiple_goals=start_multiple_goals
	 start_bot_paths={
			   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3]],				   
			   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3]],
			   2:[multiple_goals[2],multiple_goals[3]],			  			   
			   3:[multiple_goals[3]],
			}
	 return_multiple_goals=[ (309.4438942665647,454.5134963488491), (335.55872242863904,466.9516743958527), (355.25794289613196,491.6204200933454), (412.72624952349014,453.9844188543948)]

	 return_bot_paths={
	 		   0:[multiple_goals[0]],				   
			   1:[multiple_goals[1],multiple_goals[0]],
			   2:[multiple_goals[2],multiple_goals[1],multiple_goals[0]],			  			   
			   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],			  			   
			  }
	 agg_goal_point=[415.55493438625564,456.51735869880645]	
	 area_covered_percent=37

if(file_name=="Medur_"):
	origin=(  13.337329, 80.156489)#medur_vtol
	goal_points=[ (179.40550274627913,308.15386473749555), (170.99513572947805,289.35827568680276), (168.86005545367016,278.07166026184615), (196.9510938076667,266.3208209010031), (221.81169795738273,255.76690549382712), (141.36847098185353,246.6297974398802), (159.12810083196678,241.36795466086144), (165.17736445453224,255.9836791630281), (172.83867941495768,274.7264309925827), (221.20009527209496,256.0336190545783), (182.32709847774157,232.5208029351906), (207.48096771410658,224.8346429075841), (211.9462937186256,237.44651100896382), (264.87664269879014,206.67858540983394), (277.8934118507254,235.80815686557324), (298.4555948189716,230.78146926893683), (293.17787532288014,273.5376866780221), (240.41019857324855,302.7874959996908), (188.6930646784506,245.50582780455525), (230.1665459467102,218.5718998451968), (123.06874511896862,243.5163968586071), (139.11279072454997,286.02406938652103), (160.29300426583518,342.7190679601935), (186.27125160742494,330.61502836178624),]
	disperse_multiple_goals=[(126.49449142221913 ,252.22651165464404),( 172.1520264516062 , 327.39164945923085 ),( 196.8655168435012 , 274.1906809896087)]
	agg_goal_point=(221.81169795738273,255.76690549382712)	 
	start_multiple_goals=[(3911.144123065738,3490.18197878929),
(3895.7696469693406,4041.4953009168635),
(4695.122336746442,4082.8443857040024),
(4689.6424946623265,3217.440744351253)]
	multiple_goals=start_multiple_goals
	return_multiple_goals=[(137.7428756446531,228.01648885194297), (183.181500938217,199.40073869268272), (254.73872931436202,175.87879124791422), (382.5930028997517,137.59072298234116), (396.18105557173845,180.73368924385224), (356.2526114920663,213.6371889794749), (296.30873078395405,227.94625181231143),(204.64747037947143,268.1606440873891)]
	area_covered_percent=40
		 
		 	 
if(file_name=="dce_airport"):
	origin=(12.858180, 80.030595)#dce
	goal_points=[ (179.40550274627913,308.15386473749555), (170.99513572947805,289.35827568680276), (168.86005545367016,278.07166026184615), (196.9510938076667,266.3208209010031), (221.81169795738273,255.76690549382712), (141.36847098185353,246.6297974398802), (159.12810083196678,241.36795466086144), (165.17736445453224,255.9836791630281), (172.83867941495768,274.7264309925827), (221.20009527209496,256.0336190545783), (182.32709847774157,232.5208029351906), (207.48096771410658,224.8346429075841), (211.9462937186256,237.44651100896382), (264.87664269879014,206.67858540983394), (277.8934118507254,235.80815686557324), (298.4555948189716,230.78146926893683), (293.17787532288014,273.5376866780221), (240.41019857324855,302.7874959996908), (188.6930646784506,245.50582780455525), (230.1665459467102,218.5718998451968), (123.06874511896862,243.5163968586071), (139.11279072454997,286.02406938652103), (160.29300426583518,342.7190679601935), (186.27125160742494,330.61502836178624),]
	disperse_multiple_goals=[(126.49449142221913 ,252.22651165464404),( 172.1520264516062 , 327.39164945923085 ),( 196.8655168435012 , 274.1906809896087)]
	agg_goal_point=(221.81169795738273,255.76690549382712)	 
	start_multiple_goals=[(1161.9877697773895,3952.7219876760137),(1474.0593062047521,3922.1997184867887),(1746.4339033240276,3864.995130599164),(1627.7081983593039,3631.7809497202543),(1315.9537877228481,3750.6044128682397),(1058.1415227872608,3931.8705804860747)]
	#start_multiple_goals=[(1618.4417252862331,3789.6226217193234),(1943.2865355892543,3763.725034391652),(2177.083296155596,3759.957785794867),(2189.152354169475,3470.0757215201543),(1894.9868873316173,3460.1511435205725),(1610.4780589324569,3478.340978005288),(1500.0270192572484,3368.961865854303),(1874.1327969837382,3214.436688908399),(2204.034808867265,3224.3654054369695)]
	#start_multiple_goals=[(1473.3692765766918,3839.438227628719),(2197.2139624323645,3826.4067662471107),(2890.873288694228,3905.430416954603),(3574.4026070429027,4001.1108654555637),(4219.0302243669075,4094.1501144795875),(4897.632335896987,4198.681725896295),(5411.611726568265,3977.4024056163244),(4126.4519596347645,3420.913859947042),(3143.510531127657,3313.781512602088),(2183.7922612555594,3443.2235544771975),(2068.840163927361,3354.0438269600613),(1201.148935647237,3701.186884339417)]
	multiple_goals=start_multiple_goals
	return_multiple_goals=[(137.7428756446531,228.01648885194297), (183.181500938217,199.40073869268272), (254.73872931436202,175.87879124791422), (382.5930028997517,137.59072298234116), (396.18105557173845,180.73368924385224), (356.2526114920663,213.6371889794749), (296.30873078395405,227.94625181231143),(204.64747037947143,268.1606440873891)]
	area_covered_percent=40
	


nextwaypoint=0
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('192.168.0.210', 12005)  #receive from .....rx.py

# Bind the socket to the port
remove_bot_server_address = ('192.168.0.210', 12001)  #receive from .....rx.py

sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address4 = ('', 12011)  #receive from .....rx.py
sock.bind(server_address4)

num_bots=10
vehicles=[]
pos_array=[]
heartbeat_ip=["192.168.0.151","192.168.0.152","192.168.0.153","192.168.0.154","192.168.0.155","192.168.0.156","192.168.0.157","192.168.0.158","192.168.0.159","192.168.0.160"]
heartbeat_ip_timeout=[0]*10
heartbeat_ip_timeout=[30,30,30,1,1,1,1,1,1,1]
goal_path_csv_array=[]
goal_path_csv_array_flag=False
csv_path = cwd+"/pos.csv"
skip_wp_flag=False
next_wp=0
#print("csv_path",csv_path)
"""
def vehicle_collision_moniter_receive():	
        global index
        #global vehicles
        #global slave_heal_ip,master_flag,master_num,pos_array,home_pos,uav_home_pos
        while 1:
        	index, address = sock3.recvfrom(1024)
        	print ("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", index)

"""
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
        		print("index",index)
        		#decoded_index=index.decode('utf-8')
        		#print("decoded_index",decoded_index)
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
        		print("index",index)
        		#decoded_index = index.decode('utf-8') 
        		#print("decoded_index",decoded_index)
        		#message_with_array = data.decode()
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
        	print("UUUUUUUU",type("home_pos"))
        	if decoded_index.startswith("home_pos"):
        		
        		print("index",index)
        		#decoded_index = index.decode('utf-8') 
        		#print("decoded_index",decoded_index)
        		message = decoded_index[:8]  # Assuming "home_pos" is 8 characters long
        		home_pos = decoded_index[8:]	
        		print("home_pos",home_pos)
        		home_pos = json.loads(home_pos)
        		print("home_pos",home_pos)
        		
        	if decoded_index.startswith("uav_home_pos"):
        		if(master_flag):
        			pass
        		else:
        			print("index",index)
        			#decoded_index = index.decode('utf-8') 
        			#print("decoded_index",decoded_index)
        			#message_with_array = data.decode()
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
        		
        	
"""
collision_thread = threading.Thread(target=uav_data_share)
collision_thread.daemon=True
collision_thread.start()        		
"""
        			
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
#CHECK_network_connection()

def vehicle_connection():	
	global vehicles,pos_array,num_bots,graph_socket,graph_server_address,heartbeat_ip_timeout
	pos_array=[]
	vehicles=[]
	num_bots=0
	
	try:	
		vehicle1= connect('udpin:192.168.0.153:14551',baud=115200, heartbeat_timeout=heartbeat_ip_timeout[0])
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
		vehicle2= connect('udpin:192.168.0.153:14552',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[1])
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
		vehicle3= connect('udpin:192.168.0.153:14553',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[2])
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
		vehicle4= connect('udpin:192.168.0.153:14554',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[3])
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
		vehicle5= connect('udpin:192.168.0.153:14555',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[4])
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
	try:
		vehicle6= connect('udpin:192.168.0.153:14556',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[5])
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
		vehicle7= connect('udpin:192.168.0.153:14557',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[6])
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
		vehicle8= connect('udpin:192.168.0.153:14558',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[7])
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
		vehicle9= connect('udpin:192.168.0.153:14559',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[8])
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
		vehicle10= connect('udpin:192.168.0.153:14560',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[9])
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
different_height=[100,130,160,190,220,250,280,310,340,370]
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

landing_flag=False
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
	global robot1_x,robot1_y
	global robot2_x,robot2_y
	global robot3_x,robot3_y
	global robot4_x,robot4_y
	global robot5_x,robot5_y
	global robot6_x,robot6_y
	global robot7_x,robot7_y
	global robot8_x,robot8_y
	global robot9_x,robot9_y
	global robot10_x,robot10_y
	
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
			    	time.sleep(1)
		    # Process the lat and lon as needed
		    print(f"Vehicle - Latitude: {home.lat}, Longitude: {home.lon}")
		    x,y = locatePosition.geoToCart (origin, endDistance, [home.lat,home.lon])
		    home_pos_lat_lon.append((home.lat,home.lon))
		    print("x,y",x/2,y/2)
		    home_pos.append((x / 2, y / 2))
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
	if master_flag:
		uav_home_pos=[]
		current_lat_lon=[]
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
		for i,vehicle in enumerate(vehicles):
		    lat = vehicle.location.global_relative_frame.lat
		    lon = vehicle.location.global_relative_frame.lon
		    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
		    current_lat_lon.append((lat,lon))			    
		    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
		    print("x,y",x/2,y/2)
		    uav_home_pos.append((x / 2, y / 2))  
		    
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
		print("serialized_goal_data",serialized_goal_data)
		sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

if master_flag:
	vehicle_connection() 	
	fetch_location()
	
#z=num_bots
#initial=str(z)+" Drones connected . Ready for takeoff"
#sent = graph_socket.sendto(str(initial).encode(), graph_server_address)

def generate_points(lat, lon, num_points, radius):
    # List to store generated points
    points = []

    # Generate points in circular formation
    for i in range(num_points):
        # Calculate bearing angle
        bearing = 360 / num_points * i

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

area_covered = 0
start_time = time.time()
visited_positions = set()
data=""
same_alt_flag=False
elapsed_time= time.time() - start_time
index=0
flag_stop=False
return_flag=False
aggregate_flag=False
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
home_counter=0
circle_formation_count=0
uav_removed=True
grid_path_array=[1]*num_bots
remove_bot_flag=False
remove_bot_index=0
search_step=1
percentage=0			
removed_uav_grid=[]
removed_grid_path_length=[]
grid_completed_bot=[-1]*num_bots
circle_formation_table=[0]*num_bots
circle_formation_goals=[]

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
	for l in range(0,len(pos_array)):
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
	print(num_bots)
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
			if master_flag:
				value=[b.x*2,b.y*2]			
				lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
				
				if same_alt_flag:
					point1 = LocationGlobalRelative(lat,lon,same_height)
				else:
					point1 = LocationGlobalRelative(lat,lon,different_height[i])
				print("point1",point1)
				vehicles[i].simple_goto(point1)
				print("$$$$$$$$$$$$$$$$")

				alt=[0]*num_bots
				alt_count=[0]*num_bots

				print("alt_count",alt_count)
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
		print ("msg", data)
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
			
		if data.startswith(b"share_data"):	
			#data1,address=sock2.recvfrom(1024)
			print("data11",data)
			decoded_index = data.decode('utf-8')
			print("decoded_index",decoded_index)
			#n, rest = decoded_index.split(",", 1)
			#print("n,rest",n,rest)
			#goal_table, rest = rest.split(",", 1)
			#print("goal_table, rest ",goal_table, rest )
			#s, grid_path_array = rest.split(",", 1)
			#print("s, grid_path_array",s, grid_path_array)
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
				print("^^^^^^^^^^")
				fieldnames = ['waypoint']
				writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
				print("DDDDDDDDD")
				
				for t in goal_table:
					print("t",t)
					writer.writerow({'waypoint':t})
			sent = graph_socket.sendto(str("Data Shared").encode(), graph_server_address)
						
		if(data.startswith(b"takeoff")):
			print("@@@@@@@@@@@@@")
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

			

		if(data==b"rtl"):			
			print("rtl!!!!!!!!!!!!!!!!")
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
				#vehicles[i].close()		
			break
					
		if(data.startswith(b"remove_bot")) or (remove_flag):	
				
				sent = graph_socket.sendto(str("remove_bot").encode(), graph_server_address)	
				print("bot_goal!!!!!!!!!!!!")
				print("data",data)
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				f,remove_bot_num = decoded_index.split(",")
				#uav,goalx,goaly=str(index).split(",")
				print(f,remove_bot_num)
				print("remove_bot_num",remove_bot_num,pos_array)
				#index=9
				#pos_array.pop(4)
				#num_bots-=1		
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
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))						
				print("uav_home_pos",uav_home_pos)    
				remove_flag=False
				uav_removed=True
				msg=str(remove_bot_num)+"- vehicle removed"
				sent = graph_socket.sendto(str(msg).encode(), graph_server_address)	
					
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
		
		if data.startswith(b'specific_bot_goal'): 
				#global goal_points
				sent = graph_socket.sendto(str("specific_bot_goal").encode(), graph_server_address)	
				index="data"
				goal_pos=[0]*num_bots
				specific_bot_goal_flag_array=[False]*num_bots
				print("goal_pos",goal_pos,"specific_bot_goal_flag_array",specific_bot_goal_flag_array)	
				
				try:
					print("bot_goal!!!!!!!!!!!!")
					#index, address = sock3.recvfrom(1024)
					print("data",data)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					f,uav, goal_point_num = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav, goal_point_num,type(goal_point_num))
					if goal_point_num.startswith('H'): 
						letter, goal_point_num = goal_point_num[0], int(goal_point_num[1:])
						print(letter, goal_point_num)						
						goal_position = home_pos[int(goal_point_num) - 1]
						print("HOME######## goal_position",goal_position,int(goal_point_num))
												
					else:
						goal_position=goal_points[int(goal_point_num)-1]
					for l in range(0,num_bots):
						print("^^^^^^^")	
						if(int(uav)==pos_array[l]):
							uav=l
							print("uav,l",uav,l)
							break
					
					goal_bot_num=int(uav)
					goal_pos[goal_bot_num]=goal_position
					specific_bot_goal_flag_array[goal_bot_num]=True
					while 1:						
						time.sleep(0.03)
						#print("pos_array",pos_array)
						try:							
							data, address = sock2.recvfrom(1050)		
							if data.startswith(b'specific_bot_goal'): 
								decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
								f,uav, goal_point_num = decoded_index.split(",")
								#uav,goalx,goaly=str(index).split(",")
								print(uav, goal_point_num,type(uav),type(goal_point_num))
								if goal_point_num.startswith('H'): 
									letter, goal_point_num = goal_point_num[0], int(goal_point_num[1:])
									print(letter, goal_point_num)		
									goal_position = home_pos[int(goal_point_num) - 1]
									print("HOME########goal_position",goal_position,int(goal_point_num))
															
								else:
									goal_position=goal_points[int(goal_point_num)-1]
								print("JJJJJJ",num_bots,pos_array)
								for l in range(0,num_bots):
									if(int(uav)==pos_array[l]):
										uav=l
										#print("uav,pos_array[l],l",uav,pos_array[l],l)
										break
								print("uav",uav)
								goal_bot_num=int(str(uav))
								goal_pos[goal_bot_num]=goal_position				
								print("goal_pos",goal_pos)
								specific_bot_goal_flag_array[goal_bot_num]=True
								print("specific_bot_goal_flag_array",specific_bot_goal_flag_array)
						except:							
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
									#print("dx,dy",dx,dy)
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
										#print ("Drone 3 lat,lon", lat,lon)
										if same_alt_flag:
											point1 = LocationGlobalRelative(lat,lon,same_height)
										else:
											point1 = LocationGlobalRelative(lat,lon,different_height[i])
										#print("point1",point1)
										vehicles[i].simple_goto(point1)
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
													       
							if master_flag:			
								sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
							if(index==b"stop"):
								for i in range(3):
									sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
								specific_bot_goal_flag=False
								break	
				except:
					print("exceptiiiooonnn")	
					pass			
					
		if data.startswith(b'goal'): 
				index="data"
				sent = graph_socket.sendto(str("goal").encode(), graph_server_address)	
				try:
					
					print("all_bot_goal!!!!!!!!!!!!")
					#index, address = sock3.recvfrom(1024)
					print("data",data)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					f,goal_pos_num=decoded_index.split(",")
					goal_position=goal_points[int(goal_pos_num)-1]				
					print(goal_position)
					bot_reached=[0]*num_bots
					while 1:
						if(num_bots==10):
							time.sleep(0.009)
						elif(num_bots==9):
							time.sleep(0.008)
						elif(num_bots==8):
							time.sleep(0.013)
						elif(num_bots==7):
							time.sleep(0.014)
						elif(num_bots==6):
							time.sleep(0.015)#verified
						elif(num_bots==5):
							time.sleep(0.016)#verified
						elif(num_bots==4):
							time.sleep(0.02)
						elif(num_bots==3):
							time.sleep(0.02)
						elif(num_bots==2):
							time.sleep(0.021)
						elif(num_bots==1):
							time.sleep(0.024)
						if(group_goal_flag):
							group_goal_flag=False
							break			
						for i,b in enumerate(s.swarm):
							current_position=[b.x,b.y]	
							#if(i==goal_bot_num):								
							dx=abs(goal_position[0]-current_position[0])
							dy=abs(goal_position[1]-current_position[1])				
							if(dx<=5 and dy<=5):
								bot_reached[i]=1
								print("bot_reached",bot_reached)
								if all(element==1 for element in bot_reached):
									group_goal_flag=True
									break					
							else:
								current_position = (b.x, b.y)		
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
											       
						if master_flag:			
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
						if(index==b"stop"):
							for i in range(3):
								sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
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
										print("Reached target altitude")
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
		if(data.startswith(b"start")) or (circle_formation_flag) :
			decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
			f,base_lat,base_lon = decoded_index.split(",")
			print("f,base_lat,base_lon ",f,base_lat,base_lon )
			
			if master_flag:
				#time.sleep(0.1)
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    # Process the lat and lon as needed
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    print("x,y",x/2,y/2)				    
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
			sent = graph_socket.sendto(str("start").encode(), graph_server_address)				
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			
			center_lat , center_lon = locatePosition.destination_location(float(base_lat),float(base_lon),700,90)
			print("center_lat , center_lon",center_lat , center_lon)
			# Generate 10 points in a circular formation with a radius of 500 meters around the given point
			multiple_goals_latlon = generate_points(center_lat, center_lon, 8, 500)
			print("multiple_goals_latlon",multiple_goals_latlon)	
			multiple_goals_latlon1=multiple_goals_latlon
			serialized_goal_data = json.dumps(multiple_goals_latlon1)
			serialized_goal_data="circle_latlon" + serialized_goal_data
			print("multiple_goals_latlon",serialized_goal_data)
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			
			multiple_goals=[]
			for m in multiple_goals_latlon:
				x,y = locatePosition.geoToCart (origin, endDistance, m)
				multiple_goals.append((x/2,y/2))
			print("multiple_goals",multiple_goals)
			circle_formation_goals=multiple_goals
			for b in s.swarm:				
	
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * num_bots							
				print("circle_formation_table",circle_formation_table)
				current_table=[0]*num_bots
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				disp_value=1
				dx_limit=80
				dy_limit=80
				ind=[0]*num_bots
				while 1:					
					if(start_flag):
						break	
			
					if(num_bots==10):
						time.sleep(0.009)
					elif(num_bots==9):
						time.sleep(0.008)
					elif(num_bots==8):
						time.sleep(0.013)
					elif(num_bots==7):
						time.sleep(0.014)
					elif(num_bots==6):
						time.sleep(0.015)#verified
					elif(num_bots==5):
						time.sleep(0.016)#verified
					elif(num_bots==4):
						time.sleep(0.02)
					elif(num_bots==3):
						time.sleep(0.06)
						disp_value=2
						dx_limit=100
						dy_limit=100	
					elif(num_bots==2):
						time.sleep(0.06)
						disp_value=2
						dx_limit=80
						dy_limit=80	
					elif(num_bots==1):
						time.sleep(0.05)	
						disp_value=1
						dx_limit=80
						dy_limit=80	
					step=1						
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]			
						if(circle_formation_table[i]==0) :	
							lat = vehicles[i].location.global_relative_frame.lat
							lon = vehicles[i].location.global_relative_frame.lon
							# Process the lat and lon as needed
							#print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
							x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
							plane_points=[x/2,y/2]
							#print("plane_points",plane_points)
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=2000)
							cmd.exec(b)
							dx=abs(goal[0]-plane_points[0])
							dy=abs(goal[1]-plane_points[1])
							if master_flag:
								current_position = [b.x*2,b.y*2]
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								vehicles[i].simple_goto(point1)
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
							if(dx<=300 and dy<=300):
								cmd =cvg.goal_area_cvg(i,b,goal)
								cmd+= disp_field(b,neighbourhood_radius=2000)
								cmd.exec(b)
								dx=abs(goal[0]-current_position[0])
								dy=abs(goal[1]-current_position[1])	
								circle_formation_table[i]=1					
								if(dx<=100 and dy<=100):
									ind[i]+=1
									print("inddddddd",ind)
									if(ind[i]==len(multiple_goals)):
										ind[i]=0
										print("ind####",ind)
								if master_flag:
									current_position = [b.x*2,b.y*2]
									lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									vehicles[i].simple_goto(point1)
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
							else:
								continue
							if master_flag:						
								sent = graph_socket.sendto(str(msg).encode(), graph_server_address)	
						if(circle_formation_table[i]==1):	
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=2000)
							cmd.exec(b)
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])	
							circle_formation_table[i]=1					
							if(dx<=dx_limit and dy<=dy_limit):
								ind[i]+=1
								print("inddddddd",ind)
								if(ind[i]==len(multiple_goals)):
									ind[i]=0
									print("ind####",ind)
							if master_flag:
								current_position = [b.x*2,b.y*2]
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								vehicles[i].simple_goto(point1)
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
						else:
							continue					
						
						if master_flag:						
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						start_flag=True
						circle_formation_flag=False		
						print("strat_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						break
	
	
		if(data==b"clear_csv"):
			print("Clear csv")
			sent = graph_socket.sendto(str("CSV Cleared").encode(), graph_server_address)
			with open(csv_path, 'w') as csvfile:
					fieldnames = ['waypoint']
					writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
					writer.writerow({'waypoint':-1})	
			
		if(data==b"navigate") or (start_flag):			
			if master_flag:
				#time.sleep(0.1)
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon

				    # Process the lat and lon as needed
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    print("x,y",x/2,y/2)
				    
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
			
			#s = sim.Simulation(num_bots, env_name='rectangles2' )
			#gui = viz.Gui(s)
			index="data"
			sent = graph_socket.sendto(str("start").encode(), graph_server_address)				
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			for b in s.swarm:				
				multiple_goals=start_multiple_goals			
				#bot_paths=start_bot_paths
				bot_paths={}
				for i in range(len(multiple_goals)):
					bot_paths[i]=multiple_goals[i:]
				print("bot_paths",bot_paths)
				#print("start_bot_paths-bot_paths",bot_paths)
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * num_bots			
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
				disp_value=1
				dx_limit=80
				dy_limit=80	
				while 1:					
					if(landing_flag):
						landing_flag=True
						circle_formation_flag=True
						break
								
					step+=1
					if(step==1):											
						for i,b in enumerate(s.swarm):
							'''
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
								message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
								graph_socket.sendto(str(message).encode(), graph_server_address) 
								removed_uav_homepos_array.append(home_pos.pop(i))
								print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
							'''
							current_position = [b.x,b.y]
							print("!!!!!!!!!!!current_table!!!!!!!",current_table)
							with open(csv_path,'rt')as text:
								data = csv.reader(text)
								for row in data: 
									data = (row)
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
						
					else:							
						if(num_bots==10):
							time.sleep(0.009)
						elif(num_bots==9):
							time.sleep(0.008)
						elif(num_bots==8):
							time.sleep(0.013)
						elif(num_bots==7):
							time.sleep(0.014)
						elif(num_bots==6):
							time.sleep(0.015)#verified
						elif(num_bots==5):
							time.sleep(0.016)#verified
						elif(num_bots==4):
							time.sleep(0.02)
						elif(num_bots==3):
							time.sleep(0.06)
							disp_value=2
							dx_limit=100
							dy_limit=100	
						elif(num_bots==2):
							time.sleep(0.06)
							disp_value=2
							dx_limit=80
							dy_limit=80	
						elif(num_bots==1):
							time.sleep(0.05)	
							disp_value=1
							dx_limit=80
							dy_limit=80					
						for i,b in enumerate(s.swarm):
							current_position = [b.x,b.y]
							ind=goal_table[i]
							if(step==2):
								length_arr[i]=len(bot_paths[ind])
								new_length_arr[i]=length_arr[i]
							if(count[i]==length_arr[i]):
								continue
							if(len(bot_paths[ind])<1):							
								continue
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
								
								length_arr[i]=len(bot_paths[ind])
								print("length_arr",length_arr)
								new_length_arr[i]=length_arr[i]
								print("new_length_arr",new_length_arr)
								count=[0]*num_bots
								if(count[i]==length_arr[i]):
									continue
								bot_array=[0]*num_bots
							goal=bot_paths[goal_table[i]][count[i]]
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd+= disp_field(b,neighbourhood_radius=2000)*disp_value
							cmd.exec(b)							
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])						
							if(dx<=dx_limit and dy<=dy_limit):
								bot_array[i]=1
								print("bot_array",bot_array)
												
							count_1=0
							for j in range(num_bots):
								if(bot_array[j]==1):
									count_1+=1
								#if(count_1==num_bots):
								if(count_1>=1):
									count_1=0
									bot_array=[0]*num_bots
									all_bot_reach_flag=True

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
								new_length_arr[i]=new_length_arr[i]-1
								for k in range(num_bots):
									count[k]+=1
									
								all_bot_reach_flag=False
								bot_array=[0]*num_bots
								if (goal==bot_paths[ind][-1]):
									print("Break")
									start_flag=False
									circle_formation_flag=True	
									landing_flag=True				
									break					
							if master_flag:
								current_position = [b.x*2,b.y*2]
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,different_height[i])
								vehicles[i].simple_goto(point1)
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
					
					
					
		if(landing_flag) or data==b"return":
			if master_flag:
				#time.sleep(0.1)
				uav_home_pos=[]
				index = "data"
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    # Process the lat and lon as needed
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    print("x,y",x/2,y/2)				    
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
			sent = graph_socket.sendto(str("start").encode(), graph_server_address)				
			
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			#print("serialized_goal_data",serialized_goal_data)
			graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			multiple_goals=circle_formation_goals
			
			print("multiple_goals",multiple_goals)
			for b in s.swarm:				
	
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * num_bots							
				print("circle_formation_table",circle_formation_table)
				current_table=[0]*num_bots
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				disp_value=1
				dx_limit=80
				dy_limit=80
				ind=[0]*num_bots
				while 1:					
					if(start_flag):
						break					
		
					if(num_bots==10):
						time.sleep(0.009)
					elif(num_bots==9):
						time.sleep(0.008)
					elif(num_bots==8):
						time.sleep(0.013)
					elif(num_bots==7):
						time.sleep(0.014)
					elif(num_bots==6):
						time.sleep(0.015)#verified
					elif(num_bots==5):
						time.sleep(0.016)#verified
					elif(num_bots==4):
						time.sleep(0.02)
					elif(num_bots==3):
						time.sleep(0.06)
						disp_value=2
						dx_limit=100
						dy_limit=100	
					elif(num_bots==2):
						time.sleep(0.06)
						disp_value=2
						dx_limit=80
						dy_limit=80	
					elif(num_bots==1):
						time.sleep(0.05)	
						disp_value=1
						dx_limit=80
						dy_limit=80
					step=1								
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]							
						goal=multiple_goals[ind[i]]	
						
						cmd =cvg.goal_area_cvg(i,b,goal)
						cmd+= disp_field(b,neighbourhood_radius=2000)
						cmd.exec(b)
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])	
						circle_formation_table[i]=1					
						if(dx<=dx_limit and dy<=dy_limit):
							ind[i]+=1
							print("inddddddd",ind)
							if(ind[i]==len(multiple_goals)):
								ind[i]=0
								print("ind####",ind)
						if master_flag:
							current_position = [b.x*2,b.y*2]
							lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
							if same_alt_flag:
								point1 = LocationGlobalRelative(lat,lon,same_height)
							else:
								point1 = LocationGlobalRelative(lat,lon,different_height[i])
							vehicles[i].simple_goto(point1)
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
								
					
						if master_flag:						
							sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						landing_flag=False
						circle_formation_flag=False		
						print("strat_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						break
	
													
		if(data==b"home") or (home_flag):
			if master_flag:
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon

				    # Process the lat and lon as needed
				    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    print("x,y",x/2,y/2)
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
			print("Home.......",home_pos)
			index="data"
			while 1:
				print("****%%%%%%%%%%%&&&&&&&&&")
				if(num_bots==10):
					time.sleep(0.009)
				elif(num_bots==9):
					time.sleep(0.008)
				elif(num_bots==8):
					time.sleep(0.013)
				elif(num_bots==7):
					time.sleep(0.014)
				elif(num_bots==6):
					time.sleep(0.015)#verified
				elif(num_bots==5):
					time.sleep(0.016)#verified
				elif(num_bots==4):
					time.sleep(0.02)
				elif(num_bots==3):
					time.sleep(0.02)
				elif(num_bots==2):
					time.sleep(0.021)
				elif(num_bots==1):
					time.sleep(0.024)
				print("JJJJJJ,home_flag1",home_flag1)
				if(home_flag1):
					print("BREAKKKKKKKKKKKKK")
					home_flag1=False
					break
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				for i,b in enumerate(s.swarm):
					'''					
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
						message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
						graph_socket.sendto(str(message).encode(), graph_server_address) 
						removed_uav_homepos_array.append(home_pos.pop(i))
						print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
					'''
					current_position = [b.x,b.y]
					print("current_position",current_position)
					#cmd =cvg.goal_area_cvg(i,b,home_pos[i],use_base_control=True, exp_weight_params=[15.0,15.5],disp_weight_params=[30.0,30.0])
					cmd =cvg.goal_area_cvg(i,b,home_pos[i])
					goal=home_pos[i]
					#Execute
					cmd.exec(b)
					
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])						
					#print("dx,dy",dx,dy)
					
					if(dx<=0.5 and dy<=0.5):
						bot_array_home[i]=1
						#print("bot_array",bot_array)	
					count_home=0
					print("count_home",count_home)
					for j in range(num_bots):
						#print("************")
						if(bot_array_home[j]==1):
							count_home+=1
						if(count_home==num_bots):
							count_home=0
							bot_array_home=[0]*num_bots
							all_bot_reach_flag_home=True

					#print("bot_array",bot_array)
					if (all_bot_reach_flag_home==True):
						with open(csv_path, 'a') as csvfile:
							fieldnames = ['waypoint']
							writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
							writer.writerow({'waypoint':-1})	
						home_flag1=True
							
					if master_flag:										
						current_position = [b.x*2,b.y*2]
						#print("Drone 3 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						#print ("Drone 3 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						vehicles[i].simple_goto(point1)
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
									       
				if master_flag:			
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
				#gui.update()	
				if(index==b"stop"):
					for i in range(3):
						sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
					home_flag1=True
					home_flag=False
					
	
		if(data==b"home_goto") or (home_goto_flag):
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			serialized_goal_data = json.dumps(goal_points)
			serialized_goal_data="goal_points" + serialized_goal_data
			print("serialized_goal_data",serialized_goal_data)
			sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			index = "data"
			sent = graph_socket.sendto(str("home_goto").encode(), graph_server_address)				
			bot_array_home=[0]*num_bots
			all_bot_reach_flag_home=False
			print("Home_goto.......")
			s = sim.Simulation(home_pos,num_bots=num_bots, env_name=file_name )

			if(vehicle_lost_flag):
				vehicle_lost_flag=True
				x=remove_vehicle()
				print(x)
			for i,b in enumerate(s.swarm):	
				'''				
				heartbeat[i]=vehicles[i].last_heartbeat
				#print( "heartbeat",heartbeat)					
				if(heartbeat[i]>10):
					#print("Vehicle ", i+1 ,"No heartbeat")   	
					lost_vehicle_num=i+1
					print("lostvehicle",lost_vehicle_num)   
					vehicle_lost_flag=True  
					#remove_flag=True           		
					message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
					graph_socket.sendto(str(message).encode(), graph_server_address) 
					removed_uav_homepos_array.append(home_pos.pop(i))
					print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
				'''						
				if master_flag:
					lat,lon = locatePosition.cartToGeo (origin, endDistance, [home_pos[i][0]*2,home_pos[i][1]*2])
					#print ("Drone 3 lat,lon", lat,lon)
					if same_alt_flag:
						point1 = LocationGlobalRelative(lat,lon,same_height)
					else:
						point1 = LocationGlobalRelative(lat,lon,different_height[i])
					vehicles[i].simple_goto(point1)
					
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
			if master_flag:				      							
				sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
				with open(csv_path, 'w') as csvfile:
						fieldnames = ['waypoint']
						writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
						writer.writerow({'waypoint':-1})	
	
			if(index==b"stop"):	
				for i in range(3):
					sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
				home_goto_flag=False
				start_flag=False
				return_flag=False
				home_flag=False
				#exit()				
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
		if(aggregate_flag):
			aggregate_flag=False
		if(home_flag):
			home_flag=False
		if(home_goto_flag):
			home_goto_flag=False
		pass				
