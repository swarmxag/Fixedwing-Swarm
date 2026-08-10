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
from dronekit import connect, VehicleMode, LocationGlobalRelative
import socket,json,threading,csv
import locatePosition


file_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
file_server_address = ('', 12003)  #receive from .....rx.py
file_sock.bind(file_server_address)

graph_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
graph_server_address = ('192.168.6.210', 12009)  #receive from .....rx.py

remove_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ('', 12008)  #receive from .....rx.py
sock2.bind(server_address2)
sock2.setblocking(0)
sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ('', 12002)  #receive from .....rx.py
sock3.bind(server_address3)

uav1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav1_server_address = ('192.168.6.157', 12002)  #receive from .....rx.py
uav2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav2_server_address = ('192.168.6.157', 12002)  #receive from .....rx.py
uav3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav3_server_address = ('192.168.6.158', 12002)
uav4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav4_server_address = ('192.168.6.164', 12002)
uav5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav5_server_address = ('192.168.6.165', 12002)
"""
uav6 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav6_server_address = ('192.168.6.156', 12002)  #receive from .....rx.py
uav7 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav7_server_address = ('192.168.6.157', 12002)  #receive from .....rx.py
uav8 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav8_server_address = ('192.168.6.158', 12002)
uav9 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav9_server_address = ('192.168.6.159', 12002)
uav10 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav10_server_address = ('192.168.6.160', 12002)
uav11 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav11_server_address = ('192.168.6.161', 12002)  #receive from .....rx.py
uav12 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav12_server_address = ('192.168.6.162', 12002)  #receive from .....rx.py
uav13 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav13_server_address = ('192.168.6.163', 12002)
uav14 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav14_server_address = ('192.168.6.164', 12002)
uav15 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
uav15_server_address = ('192.168.6.165', 12002)
"""
goal_table=[]
file_name=""
master_num=0
master_flag=False
print("file_name",file_name)

try:
	index,address=sock3.recvfrom(1024)
	print("data",index)
	decoded_index = index.decode('utf-8') 
	print("decoded_index",decoded_index)
	m,master_num=decoded_index.split("-")
	print("m,master_num",m,master_num)
	if(int(master_num)==7):
		master_flag=True
	print("master_flag",master_flag)
	graph_socket.sendto(str("Drone 7 master received").encode(), graph_server_address)	
except:
	pass		
while True:
	try:
		data,address=file_sock.recvfrom(1024)
		print("data",data)
		decoded_index = data.decode('utf-8') 
		print("decoded_index",decoded_index)
		graph_socket.sendto(str("Drone 7"+decoded_index).encode(), graph_server_address)
		file_name=decoded_index
		break
		
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
	 goal_points=[(185.95668989890575,580.615934042732), (314.9059293398766,509.0896752141942), (82.92808854687563,99.58233082538148), (191.0971623241269,213.25552727004242),(358.82522854635977,394.6546267756296),(449.06902885889286,490.5114371911169), (534.1464105396387,584.4680928613654),(541.7522071541887,384.13450136678097),(701.302608361422,291.91674355314655),(917.7195646637302,173.31541999078996),(412.72624952349014,453.9844188543948),(578.7054096836255,630.5181148831541),(490.37004230348606,537.2020905616838),(282.26850028937844,307.62839843038483), (131.41800709908222,152.8022876624719)]
	 
	 disperse_multiple_goals=[]
	 start_multiple_goals=[ (409.3819522951202,  542.7586676578036),(399.07769928207716, 529.2988015621116),( 420.7126209600318,  513.4804639623623),( 451.747288870521,  496.155804404058),(381.45025584284593, 418.81219710581036)]
	 multiple_goals=start_multiple_goals
	 
	 return_multiple_goals=[ (409.3819522951202,  542.7586676578036),(399.07769928207716, 529.2988015621116),( 420.7126209600318,  513.4804639623623),( 451.747288870521,  496.155804404058),(381.45025584284593, 418.81219710581036)]
	 
	 agg_goal_point=[381.45025584284593, 418.81219710581036]	
	 area_covered_percent=70
	 
if(file_name=="dce_airport"):
	origin=(12.924801, 80.042719)#dce
	goal_points=[ (179.40550274627913,308.15386473749555), (170.99513572947805,289.35827568680276), (168.86005545367016,278.07166026184615), (196.9510938076667,266.3208209010031), (221.81169795738273,255.76690549382712), (141.36847098185353,246.6297974398802), (159.12810083196678,241.36795466086144), (165.17736445453224,255.9836791630281), (172.83867941495768,274.7264309925827), (221.20009527209496,256.0336190545783), (182.32709847774157,232.5208029351906), (207.48096771410658,224.8346429075841), (211.9462937186256,237.44651100896382), (264.87664269879014,206.67858540983394), (277.8934118507254,235.80815686557324), (298.4555948189716,230.78146926893683), (293.17787532288014,273.5376866780221), (240.41019857324855,302.7874959996908), (188.6930646784506,245.50582780455525), (230.1665459467102,218.5718998451968), (123.06874511896862,243.5163968586071), (139.11279072454997,286.02406938652103), (160.29300426583518,342.7190679601935), (186.27125160742494,330.61502836178624),]
	disperse_multiple_goals=[]
	agg_goal_point=(221.81169795738273,255.76690549382712)	 
	start_multiple_goals=[(137.7428756446531,228.01648885194297), (183.181500938217,199.40073869268272), (254.73872931436202,175.87879124791422), (382.5930028997517,137.59072298234116), (396.18105557173845,180.73368924385224), (356.2526114920663,213.6371889794749), (296.30873078395405,227.94625181231143)]
	multiple_goals=start_multiple_goals
	return_multiple_goals=[(137.7428756446531,228.01648885194297), (183.181500938217,199.40073869268272), (254.73872931436202,175.87879124791422), (382.5930028997517,137.59072298234116), (396.18105557173845,180.73368924385224), (356.2526114920663,213.6371889794749), (296.30873078395405,227.94625181231143)]
	area_covered_percent=90
	
nextwaypoint=0
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('192.168.6.210', 12005)  #receive from .....rx.py

sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address4 = ('', 12011)  #receive from .....rx.py
sock.bind(server_address4)

num_bots=15
vehicles=[]
pos_array=[]
heartbeat_ip=["192.168.6.151","192.168.6.152","192.168.6.157","192.168.6.154","192.168.6.155","192.168.6.156","192.168.6.157","192.168.6.158","192.168.6.159","192.168.6.160","192.168.6.161","192.168.6.162","192.168.6.163","192.168.6.164","192.168.6.165"]
heartbeat_ip_timeout=[0]*15
#heartbeat_ip_timeout=[30]*15
goal_path_csv_array=[]
goal_path_csv_array_flag=False

def vehicle_collision_moniter_receive():	
        global index
        global vehicles
        global slave_heal_ip,master_flag,master_num,pos_array,home_pos,uav_home_pos
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
        		msg='Drone 7 master_num '+str(master_num)+' data received'
        		for l in range(2):
        			graph_socket.sendto(str(msg).encode(), graph_server_address)	
        		if(int(master_num)==7):
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
        			message = decoded_index[:12]  # Assuming "home_pos" is 8 characters long
        			uav_home_pos = decoded_index[12:]	
        			print("uav_home_pos",uav_home_pos)
        			uav_home_pos = json.loads(uav_home_pos)
        			print("uav_home_pos",uav_home_pos)
        			
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
	    	heartbeat_ip_timeout[i]=3
    print(" heartbeat_ip_timeout",heartbeat_ip_timeout)
CHECK_network_connection()

def vehicle_connection():	
	global vehicles,pos_array,num_bots,graph_socket,graph_server_address,heartbeat_ip_timeout
	pos_array=[]
	vehicles=[]
	num_bots=0
	
	try:	
		vehicle1= connect('udpin:192.168.6.157:14551',baud=115200, heartbeat_timeout=heartbeat_ip_timeout[0])
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
		vehicle2= connect('udpin:192.168.6.157:14552',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[1])
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
		vehicle3= connect('udpin:192.168.6.157:14553',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[2])
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
		vehicle4= connect('udpin:192.168.6.157:14554',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[3])
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
		vehicle5= connect('udpin:192.168.6.157:14555',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[4])
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
		vehicle6= connect('udpin:192.168.6.157:14556',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[5])
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
		vehicle7= connect('udpin:192.168.6.157:14557',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[6])
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
		vehicle8= connect('udpin:192.168.6.157:14558',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[7])
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
		vehicle9= connect('udpin:192.168.6.157:14559',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[8])
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
		vehicle10= connect('udpin:192.168.6.157:14560',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[9])
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
	try:	
		vehicle11= connect('udpin:192.168.6.157:14561',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[10])
		vehicle11.airspeed = 12
		print('Drone11')
		vehicles.append(vehicle11)
		pos_array.append(11)
		num_bots+=1
		msg="Drone11 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 11 is lost")
	try:	
		vehicle12= connect('udpin:192.168.6.157:14562',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[11])
		vehicle12.airspeed = 12
		print('Drone12')
		vehicles.append(vehicle12)
		pos_array.append(12)
		num_bots+=1
		msg="Drone12 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 12 is lost")
	try:	
		vehicle13= connect('udpin:192.168.6.157:14563',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[12])
		vehicle13.airspeed = 12
		print('Drone13')
		vehicles.append(vehicle13)
		pos_array.append(13)
		num_bots+=1
		msg="Drone13 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 13 is lost")
		
	try:	
		vehicle14= connect('udpin:192.168.6.157:14564',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[13])
		vehicle14.airspeed = 12
		print('Drone14')
		vehicles.append(vehicle14)
		pos_array.append(14)
		num_bots+=1
		msg="Drone14 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 14 is lost")
	try:	
		vehicle15= connect('udpin:192.168.6.157:14565',baud=115200,heartbeat_timeout=heartbeat_ip_timeout[14])
		vehicle15.airspeed = 12
		print('Drone15')
		vehicles.append(vehicle15)
		pos_array.append(15)
		num_bots+=1
		msg="Drone15 Connected"
		graph_socket.sendto(str(msg).encode(), graph_server_address)
	except:
		pass
		print(	"Vehicle 15 is lost")
	print(len(vehicles))
	
	serialized_data = json.dumps(pos_array)
	serialized_data="pos_array" + serialized_data
	print("serialized_data",serialized_data)
	for f in range(len(vehicles)):
		uav1.sendto(serialized_data.encode(), uav1_server_address)
		time.sleep(0.05)
		uav2.sendto(serialized_data.encode(), uav2_server_address)
		time.sleep(0.05)
		uav3.sendto(serialized_data.encode(), uav3_server_address)
		time.sleep(0.05)
		uav4.sendto(serialized_data.encode(), uav4_server_address)
		time.sleep(0.05)
		uav5.sendto(serialized_data.encode(), uav5_server_address)
		"""
		time.sleep(0.05)
		uav6.sendto(serialized_data.encode(), uav6_server_address)
		time.sleep(0.05)
		uav7.sendto(serialized_data.encode(), uav7_server_address)
		time.sleep(0.05)
		uav8.sendto(serialized_data.encode(), uav8_server_address)
		time.sleep(0.05)
		uav9.sendto(serialized_data.encode(), uav9_server_address)
		time.sleep(0.05)
		uav10.sendto(serialized_data.encode(), uav10_server_address)
		time.sleep(0.05)
		uav11.sendto(serialized_data.encode(), uav11_server_address)
		time.sleep(0.05)
		uav12.sendto(serialized_data.encode(), uav12_server_address)
		time.sleep(0.05)
		uav13.sendto(serialized_data.encode(), uav13_server_address)
		time.sleep(0.05)
		uav14.sendto(serialized_data.encode(), uav14_server_address)
		time.sleep(0.05)
		uav15.sendto(serialized_data.encode(), uav15_server_address)
		"""
	
count=0
endDistance=8000
same_height=30
different_height=[0]*num_bots
#different_height=[30,31,32,33,34,35,36,37,38,39,40,41,42,43,44]
home_pos=[]
home_pos_lat_lon=[]
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

slave_heal_ip=["192.168.6.157"]*num_bots
heartbeat=[0]*num_bots

vehicle_uav_heartbeat_flag=False
disperse_flag=False

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address1 = ('192.168.6.210', 12010)
slave_heal_ip=["192.168.6.157"]*num_bots
           

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
	global robot11_x,robot11_y
	global robot12_x,robot12_y
	global robot13_x,robot13_y
	global robot14_x,robot14_y
	global robot15_x,robot15_y
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
			str(robot10_x) + ',' + str(robot10_y)+ ',' +
		       str(robot11_x) + ',' + str(robot11_y)+ ',' +
		       str(robot12_x) + ',' + str(robot12_y)+ ',' +
		       str(robot13_x) + ',' + str(robot13_y)+ ',' +
		       str(robot14_x) + ',' + str(robot14_y)+ ',' +
		       str(robot15_x) + ',' + str(robot15_y))
					       
		    print("msg",msg) 
	if master_flag:
		serialized_data = json.dumps(home_pos)
		serialized_data="home_pos" + serialized_data
		sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
		#time.sleep(0.05)
		for i in range(len(pos_array)):
			uav1.sendto(serialized_data.encode(),uav1_server_address)
			time.sleep(0.05)
			uav2.sendto(serialized_data.encode(),uav2_server_address)
			time.sleep(0.05)
			uav3.sendto(serialized_data.encode(),uav3_server_address)
			time.sleep(0.05)
			uav4.sendto(serialized_data.encode(), uav4_server_address)
			time.sleep(0.05)
			uav5.sendto(serialized_data.encode(), uav5_server_address)
			"""
			time.sleep(0.05)
			uav6.sendto(serialized_data.encode(), uav6_server_address)
			time.sleep(0.05)
			uav7.sendto(serialized_data.encode(), uav7_server_address)
			time.sleep(0.05)
			uav8.sendto(serialized_data.encode(), uav8_server_address)
			time.sleep(0.05)
			uav9.sendto(serialized_data.encode(), uav9_server_address)
			time.sleep(0.05)
			uav10.sendto(serialized_data.encode(), uav10_server_address)
			time.sleep(0.05)
			uav11.sendto(serialized_data.encode(), uav11_server_address)
			time.sleep(0.05)
			uav12.sendto(serialized_data.encode(), uav12_server_address)
			time.sleep(0.05)
			uav13.sendto(serialized_data.encode(), uav13_server_address)
			time.sleep(0.05)
			uav14.sendto(serialized_data.encode(), uav14_server_address)
			time.sleep(0.05)
			uav15.sendto(serialized_data.encode(), uav15_server_address)
			"""
	if master_flag:
		uav_home_pos=[]
		current_lat_lon=[]	
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
			str(robot10_x) + ',' + str(robot10_y)+ ',' +
		       str(robot11_x) + ',' + str(robot11_y)+ ',' +
		       str(robot12_x) + ',' + str(robot12_y)+ ',' +
		       str(robot13_x) + ',' + str(robot13_y)+ ',' +
		       str(robot14_x) + ',' + str(robot14_y)+ ',' +
		       str(robot15_x) + ',' + str(robot15_y))
		    print("msg..",msg)
	if master_flag:	
		sent = graph_socket.sendto(str(msg).encode(), graph_server_address)

	if master_flag:
		serialized_data = json.dumps(uav_home_pos)
		serialized_data="uav_home_pos" + serialized_data
		for i in range(len(pos_array)):			
			uav1.sendto(serialized_data.encode(),uav1_server_address)
			time.sleep(0.05)
			uav2.sendto(serialized_data.encode(),uav2_server_address)
			time.sleep(0.05)
			uav3.sendto(serialized_data.encode(),uav3_server_address)	
			time.sleep(0.05)
			uav4.sendto(serialized_data.encode(), uav4_server_address)
			time.sleep(0.05)
			uav5.sendto(serialized_data.encode(), uav5_server_address)
			"""
			time.sleep(0.05)
			uav6.sendto(serialized_data.encode(), uav6_server_address)
			time.sleep(0.05)
			uav7.sendto(serialized_data.encode(), uav7_server_address)
			time.sleep(0.05)
			uav8.sendto(serialized_data.encode(), uav8_server_address)
			time.sleep(0.05)
			uav9.sendto(serialized_data.encode(), uav9_server_address)
			time.sleep(0.05)
			uav10.sendto(serialized_data.encode(), uav10_server_address)
			time.sleep(0.05)
			uav11.sendto(serialized_data.encode(), uav11_server_address)
			time.sleep(0.05)
			uav12.sendto(serialized_data.encode(), uav12_server_address)
			time.sleep(0.05)
			uav13.sendto(serialized_data.encode(), uav13_server_address)
			time.sleep(0.05)
			uav14.sendto(serialized_data.encode(), uav14_server_address)
			time.sleep(0.05)
			uav15.sendto(serialized_data.encode(), uav15_server_address)
			"""

		serialized_goal_data = json.dumps(goal_points)
		serialized_goal_data="goal_points" + serialized_goal_data
		print("serialized_goal_data",serialized_goal_data)
		sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

if master_flag:
	vehicle_connection() 	
	fetch_location()
	
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
same_alt_flag=True
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
#Initialize Simulation and GUI 
while True:
	if(uav_home_pos!=[]):
		print("num_bots",num_bots,uav_home_pos)
		s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name)
		'''
		if(pos_array!=[]):
			s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name)
		else:
			s = sim.Simulation(uav_home_pos,num_bots=len(uav_home_pos), env_name=file_name)
			pos_array=[1]*len(uav_home_pos)
		'''
		for l in range(3):
			graph_socket.sendto(str("Drone 7 CONNECTED").encode(), graph_server_address)	
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
	#sent = remove_socket.sendto(str(pop_bot_index).encode(), remove_bot_server_address)
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
				str(robot10_x) + ',' + str(robot10_y)+ ',' +
			       str(robot11_x) + ',' + str(robot11_y)+ ',' +
			       str(robot12_x) + ',' + str(robot12_y)+ ',' +
			       str(robot13_x) + ',' + str(robot13_y)+ ',' +
			       str(robot14_x) + ',' + str(robot14_y)+ ',' +
			       str(robot15_x) + ',' + str(robot15_y))
						       
			    print("msg",msg) 
			serialized_data = json.dumps(home_pos)
			serialized_data="home_pos" + serialized_data
			sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
			
		if data.startswith(b"share_data"):	
			#data1,address=sock2.recvfrom(1024)
			print("data11",data)
			decoded_index = data.decode('utf-8')
			print("decoded_index",decoded_index)
			n,goal_table=decoded_index.split(",",1)
			goal_table = goal_table.strip()
			print(n,goal_table,"DDDDFFFFFF")
			goal_table=json.loads(goal_table)
			print("goal_table",goal_table)
			with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'w') as csvfile:
					fieldnames = ['waypoint']
					writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
					writer.writerow({'waypoint':-1})
			with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
				print("^^^^^^^^^^")
				fieldnames = ['waypoint']
				writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
				print("DDDDDDDDD")
				
				for t in goal_table:
					print("t",t)
					writer.writerow({'waypoint':t})
			
						
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
				str(robot10_x) + ',' + str(robot10_y)+ ',' +
			       str(robot11_x) + ',' + str(robot11_y)+ ',' +
			       str(robot12_x) + ',' + str(robot12_y)+ ',' +
			       str(robot13_x) + ',' + str(robot13_y)+ ',' +
			       str(robot14_x) + ',' + str(robot14_y)+ ',' +
			       str(robot15_x) + ',' + str(robot15_y))
						       
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
				print(f,remove_bot_num)
				print("remove_bot_num",remove_bot_num,pos_array)					
				pop_flag=True
				print ("msg", index)
				for l in range(0,len(pos_array)):	
					if(int(remove_bot_num)==pos_array[l]):
						pop_bot_index=l
						print(l)
						break
				pos_array.pop(pop_bot_index)
				print("len(pos_array),len(vehicles)",len(vehicles),len(pos_array))
				print("11111111111111111111",pop_bot_index)
				vehicles.pop(pop_bot_index)
				print(len(home_pos),"len(home_pos)")
				home_pos.pop(pop_bot_index)
				print(len(home_pos),"len(home_pos)")
				print("uav_length",len(uav_home_pos))				
				uav_home_pos.pop(pop_bot_index)
				print("uav_length",len(uav_home_pos))									
				s.remove_bot(pop_bot_index)
				print("num_bots",num_bots)
				num_bots-=1
				print("num_bots",num_bots)
				print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!",pop_flag_arr)
				
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

		#if(data==b"specific_bot_goal"):	
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
									print("HOME######## goal_position",goal_position,int(goal_point_num))
															
								else:
									goal_position=goal_points[int(goal_point_num)-1]
								#goal_position=goal_points[int(goal_point_num)-1]	
								print("JJJJJJ",num_bots,pos_array)
								for l in range(0,num_bots):	
									if(int(uav)==pos_array[l]):
										uav=l
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
										#print ("Drone 1 lat,lon", lat,lon)
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
									       str(robot10_x) + ',' + str(robot10_y)+ ',' +
									       str(robot11_x) + ',' + str(robot11_y)+ ',' +
									       str(robot12_x) + ',' + str(robot12_y)+ ',' +
									       str(robot13_x) + ',' + str(robot13_y)+ ',' +
									       str(robot14_x) + ',' + str(robot14_y)+ ',' +
									       str(robot15_x) + ',' + str(robot15_y))
													       
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
							       str(robot10_x) + ',' + str(robot10_y)+ ',' +
							       str(robot11_x) + ',' + str(robot11_y)+ ',' +
							       str(robot12_x) + ',' + str(robot12_y)+ ',' +
							       str(robot13_x) + ',' + str(robot13_y)+ ',' +
							       str(robot14_x) + ',' + str(robot14_y)+ ',' +
							       str(robot15_x) + ',' + str(robot15_y))
											       
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
							#print ("Drone 1 lat,lon", lat,lon)
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
		if data.startswith(b'different'): 
				sent = graph_socket.sendto(str("different altitude").encode(), graph_server_address)
				velocity_flag=True	
				print ("msg", data)
				decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
				data1, height,step = decoded_index.split(",")				
				print(data1, height,step)
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
		
		if(data==b"start") or (circle_formation_flag):			
			sent = graph_socket.sendto(str("circle formation").encode(), graph_server_address)	
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
					#print("i",i)
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					time.sleep(0.05)
					"""
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)	
					"""		
				print("uav_home_pos",uav_home_pos)    
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
				print("circle_formation_count",circle_formation_count)
				serialized_data = json.dumps(home_pos)
				serialized_data="home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				serialized_goal_data = json.dumps(goal_points)
				serialized_goal_data="goal_points" + serialized_goal_data
				print("serialized_goal_data",serialized_goal_data)
				sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			while circle_formation_count<2500:
				if(index==b"stop"):
					for i in range(3):
						sent = graph_socket.sendto(str("stop").encode(), graph_server_address)	
					circle_formation_flag=False	
					print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
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
					time.sleep(0.02)
				elif(num_bots==2):
					time.sleep(0.021)
				elif(num_bots==1):
					time.sleep(0.024)
				circle_formation_flag=True
				start_flag=True
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				for i,b in enumerate(s.swarm):
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
						message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
						graph_socket.sendto(str(message).encode(), graph_server_address) 
						removed_uav_homepos_array.append(home_pos.pop(i))
						print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
					'''
					
					circle_formation_count+=1					
					cmd = base_control.base_control(i,b,home_pos[0])
					cmd+= base_control.obstacle_avoidance(i,b,home_pos[0])					
					#Behaviour
					cmd+=circle(b,100)
					cmd += disp_field(b)					 
					#Execute
					cmd.exec(b)
					if master_flag:
						current_position = [b.x*2,b.y*2]
						#print(current_position)
						#print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						#print ("Drone 1 lat,lon", lat,lon)
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
					       str(robot10_x) + ',' + str(robot10_y)+ ',' +
					       str(robot11_x) + ',' + str(robot11_y)+ ',' +
					       str(robot12_x) + ',' + str(robot12_y)+ ',' +
					       str(robot13_x) + ',' + str(robot13_y)+ ',' +
					       str(robot14_x) + ',' + str(robot14_y)+ ',' +
					       str(robot15_x) + ',' + str(robot15_y))
				if master_flag:
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
		
		if(data==b"clear_csv"):
			print("Clear csv")
			sent = graph_socket.sendto(str("CSV Cleared").encode(), graph_server_address)
			with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'w') as csvfile:
					fieldnames = ['waypoint']
					writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
					writer.writerow({'waypoint':-1})	
			
		if(data==b"start1") or (start_flag):
			if(circle_formation_count>=2500):
				circle_formation_flag=False
				start_flag=True
			if master_flag:
				#time.sleep(0.05)
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
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					time.sleep(0.05)
					"""
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)
					"""
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

			for b in s.swarm:
				multiple_goals=start_multiple_goals							
				bot_paths={}
				for i in range(len(multiple_goals)):
					bot_paths[i]=multiple_goals[i:]
				#print("bot_paths",bot_paths)
				#print("start_bot_paths-bot_paths",bot_paths)
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * num_bots			
				goal_table=[0]*num_bots
				#print("goal_table",goal_table)
				current_table=[0]*num_bots
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				search_flag=False
				all_bot_reach_flag=False
				bot_array=[0]*num_bots
				
				while 1:
					#print("master_flag",master_flag)
					#print("pop_flag_arr",pop_flag_arr)
					
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
							#print("%%%%pos_array%%%%%%",pos_array)
							
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
							
							#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
							with open('/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv','rt')as text:
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
						       str(robot10_x) + ',' + str(robot10_y)+ ',' +
						       str(robot11_x) + ',' + str(robot11_y)+ ',' +
						       str(robot12_x) + ',' + str(robot12_y)+ ',' +
						       str(robot13_x) + ',' + str(robot13_y)+ ',' +
						       str(robot14_x) + ',' + str(robot14_y)+ ',' +
						       str(robot15_x) + ',' + str(robot15_y))
						
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
							time.sleep(0.02)
						elif(num_bots==2):
							time.sleep(0.021)
						elif(num_bots==1):
							time.sleep(0.024)						
						#print("&&&&&&&")
						for i,b in enumerate(s.swarm):							
							print(len(s.swarm))
							'''
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
								message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
								graph_socket.sendto(str(message).encode(), graph_server_address)  
								removed_uav_homepos_array.append(home_pos.pop(i))
								print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
							'''
															
							current_position = [b.x,b.y]
							#print("current_position",current_position)	
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
								continue
							goal=bot_paths[goal_table[i]][count[i]]
							
							#print("111111",i,b,goal)
							
							cmd =cvg.goal_area_cvg(i,b,goal)
							
							#Execute
							cmd.exec(b)
							#print("2222222",i,b,goal)							
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])						
							#print("dx,dy",dx,dy)
							if(dx<=10 and dy<=10):
								bot_array[i]=1
								print("bot_array",bot_array)
												
							count_1=0
							for j in range(num_bots):
								if(bot_array[j]==1):
									count_1+=1
								if(count_1==num_bots):
									count_1=0
									bot_array=[0]*num_bots
									all_bot_reach_flag=True

							if (all_bot_reach_flag==True):
								with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
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
									#print("Break")
									start_flag=False
									search_height_flag=True
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
							       str(robot10_x) + ',' + str(robot10_y)+ ',' +
							       str(robot11_x) + ',' + str(robot11_y)+ ',' +
							       str(robot12_x) + ',' + str(robot12_y)+ ',' +
							       str(robot13_x) + ',' + str(robot13_y)+ ',' +
							       str(robot14_x) + ',' + str(robot14_y)+ ',' +
							       str(robot15_x) + ',' + str(robot15_y))
					if master_flag:				       
						if goal_path_csv_array_flag:
						    int_value = int(goal_path_csv_array[-1])
						    msg += ","+'path' + str(int_value)
						   # goal_path_csv_array_flag=False
						#print("msg",msg)			
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					if(index==b"stop"):	
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)		
						print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
						start_flag=False
						circle_formation_flag=False		
						print("start_flag",start_flag,"circle_formation_flag",circle_formation_flag)
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
						same_height
						
						if(pop_flag):
							same_height+=3
						
						alt=[0]*num_bots
						alt_count=[0]*num_bots
						alt_count1=0						
						while True:	
							time.sleep(0.01)
							if(index==b"stop"):
								for i in range(3):
									sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
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
							#print("velocity_flag",velocity_flag)						
							for i, b in enumerate(s.swarm):
								
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
									message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
									graph_socket.sendto(str(message).encode(), graph_server_address)  
									removed_uav_homepos_array.append(home_pos.pop(i))
									print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
								'''								
								cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=5)
								cmd.exec(b)
								if master_flag:
									value=[b.x*2,b.y*2]
									lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
									#print ("Drone 1 lat,lon", lat,lon)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									#print("point1",point1)
									vehicles[i].simple_goto(point1)
								
									for i,vehicle in enumerate(vehicles):
										alt[i]=vehicle.location.global_relative_frame.alt 
										#print("alt[vehicle]",alt[i])
										if same_alt_flag:
											if same_height - 1.5 <= alt[i] <= same_height + 1.5:
												alt_count[i]=1
												#alt_count1+=1										
												if all(count==1 for count in alt_count):	
												#if(alt_count1==num_bots):
													print("Reached target altitude")
													search_height_flag=False
													disperse_flag=True
													break
										
										else:
											if different_height[i] - 1.5 <= alt[i] <= different_height[i] + 1.5:
												alt_count[i]=1
												#alt_count1+=1										
												if all(count==1 for count in alt_count):
												#if(alt_count1==num_bots):
													print("Reached target altitude")
													search_height_flag=False
													disperse_flag=True
													break
								else:
									print("Reached target altitude")
									search_height_flag=False
									disperse_flag=True
									break	
								
		if(data==b"disperse") or (disperse_flag):
			sent = graph_socket.sendto(str("disperse").encode(), graph_server_address)				
			index="data"	
			print("Disperse!!!!!",num_bots,uav_home_pos)
			
			if master_flag:
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))				
				utils.robot.DEFAULT_SIZE= 0.4
				serialized_data = json.dumps(home_pos)
				serialized_data="home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				serialized_goal_data = json.dumps(goal_points)
				serialized_goal_data="goal_points" + serialized_goal_data
				print("serialized_goal_data",serialized_goal_data)
				sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					time.sleep(0.05)
					"""
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)
					"""
				print("file_name+'_search'",file_name+'_search')
				s = sim.Simulation(uav_home_pos,num_bots=num_bots, env_name=file_name+'_search' )
			disperse_bot_goal=[0]*num_bots
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
			all_bot_reach_flag_rev=False
			bot_array_rev=[0]*num_bots
			disperse_start_time = time.time()
			print("disperse_start_time",disperse_start_time)
			multiple_goals=disperse_multiple_goals
			while True:	
				
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
								  		
							message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
							graph_socket.sendto(str(message).encode(), graph_server_address) 
							removed_uav_homepos_array.append(home_pos.pop(i))
							print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
						'''
						
						print("disperse_start_time",disperse_start_time)											
						if(multiple_goals==[]):
							cmd = base_control.exp_control(b)
							cmd+= disp_field(b,neighbourhood_radius=500)*15
							cmd+= base_control.exp_obstacle_avoidance(b)*30
						else:
							current_position = [b.x,b.y]
							cmd = base_control.base_control(i,b,multiple_goals[i])
							cmd = disp_field(b)*2
							cmd+= base_control.obstacle_avoidance(i,b,multiple_goals[i])
							dx=abs(multiple_goals[i][0]-current_position[0])
							dy=abs(multiple_goals[i][1]-current_position[1])
							if(dx<=3 and dy<=3):	
								new_length_arr[i]=new_length_arr[i]-1	
								disperse_bot_goal[i]=1
							
							if all(goal==1 for goal in disperse_bot_goal):
								disperse_flag=False
								search_flag=True
								print(search_flag,"search_flag")
								break
						elapsed_time = time.time() - disperse_start_time
						print("Disperse elapsed_time",elapsed_time)						
						cmd.exec(b)
						if master_flag:
							current_position =[b.x*2,b.y*2]						
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
						       str(robot10_x) + ',' + str(robot10_y)+ ',' +
						       str(robot11_x) + ',' + str(robot11_y)+ ',' +
						       str(robot12_x) + ',' + str(robot12_y)+ ',' +
						       str(robot13_x) + ',' + str(robot13_y)+ ',' +
						       str(robot14_x) + ',' + str(robot14_y)+ ',' +
						       str(robot15_x) + ',' + str(robot15_y))
					if(multiple_goals==[]):				       
						if(elapsed_time>30):
							disperse_flag=False
							search_flag=True
							break
					if master_flag:
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
								#gui.update()						
					if(index==b"search") or (search_flag):
						#print("FFFFFFF")
						disperse_flag=False
						search_flag=True
						break
					
					if(index==b"stop"):
						print("Disperse Stoped!!!")
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)		
						disperse_flag=False
						break
					
								
								
		if(data==b"search") or (search_flag):
			if master_flag:
				sent = graph_socket.sendto(str("search").encode(), graph_server_address)				
				index="data"
				serialized_data = json.dumps(home_pos)
				serialized_data="home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				serialized_goal_data = json.dumps(goal_points)
				serialized_goal_data="goal_points" + serialized_goal_data
				#print("serialized_goal_data",serialized_goal_data)
				sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)
			
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon

				    # Process the lat and lon as needed
				   # print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    #print("x,y",x/2,y/2)
				    uav_home_pos.append((x / 2, y / 2))
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					"""
					time.sleep(0.05)
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)
					"""
				utils.robot.DEFAULT_SIZE= 0.4				
				s = sim.Simulation(uav_home_pos,num_bots=num_bots, env_name=file_name+'_search' )
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
			move_bot_flag_array=[False]*num_bots
			move_bot_pos_array=[0]*num_bots			
			search_start_time = time.time()
			
			while 1:	
				if(num_bots==10):
					time.sleep(0.005)
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
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				if(aggregate_flag):
					break
				try:
					data,address=sock2.recvfrom(1024)
					#print("data",data)
					decoded_index = data.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					#print("decoded_index",type(decoded_index),decoded_index)					
					f,uav, goal_point_num = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav, goal_point_num)
					#print("pos_array",pos_array)
					for l in range(0,num_bots):	
						if(int(uav)==pos_array[l]):
							uav=l
							print("uav,l",uav,l)
							break
					
					
					if(f=="move_bot"):
						sent = graph_socket.sendto(str("move_bot").encode(), graph_server_address)
						move_bot_flag=True						
						goal_bot_num=int(uav)
						#print("#####",goal_bot_num)
						goal_position=goal_points[int(goal_point_num)-1]					
						move_bot_flag_array[goal_bot_num]=True
						move_bot_pos_array[goal_bot_num]=goal_position
						print("move_bot_flag_array",move_bot_flag_array)
						print("move_bot_pos_array",move_bot_pos_array)
				except:
					for i,b in enumerate(s.swarm):
						area=gui.show_coverage(area_covered,elapsed_time)	
						if((area*10)>area_covered_percent) or (aggregate_flag):
							if(same_alt_flag):
								return_height_flag=False
								aggregate_flag=True
							else:
								return_height_flag=True
								aggregate_flag=True
							break						
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
							message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
							graph_socket.sendto(str(message).encode(), graph_server_address) 
							removed_uav_homepos_array.append(home_pos.pop(i))
					
							print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
						'''
						current_position=[b.x,b.y]
						if(move_bot_flag) or (move_bot_flag_array[i]):
							if(move_bot_flag_array[i]):
								print("move_bot_pos_array,i,val",i,move_bot_pos_array[i],move_bot_pos_array[i][0],move_bot_pos_array[i][1])
								b.set_goal(move_bot_pos_array[i][0],move_bot_pos_array[i][1])
								cmd = cvg.goal_area_cvg(i, b, move_bot_pos_array[i])							 	
								dx=abs(move_bot_pos_array[i][0]-current_position[0])
								dy=abs(move_bot_pos_array[i][1]-current_position[1])
								#print("move_bot_pos_array",move_bot_pos_array)
								if(dx<=1 and dy<=1):
									move_bot_flag_array[i]=False
									
								if all(flag==False for flag in move_bot_flag_array):
									move_bot_flag=False
									break
																									
							else:
								#print("I###########",i)
								cmd = cvg.disp_exp_area_cvg(b, use_base_control=True, exp_weight_params=[1.0,1.5],disp_weight_params=[2.0,2.5]) *2
						else:
							cmd = cvg.disp_exp_area_cvg(b) 					
						value=[b.x*2,b.y*2]
						cmd.exec(b)
						#print("value",i,value)
												
						elapsed_time = time.time() - search_start_time
						
						gui.show_coverage(area_covered,elapsed_time)						
						if master_flag:
							if pop_flag_arr[i]==1:								
								lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
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
						       str(robot8_x) + ',' + str(robot8_y)+',' +
						       str(robot9_x) + ',' + str(robot9_y)+',' +
						       str(robot10_x) + ',' + str(robot10_y)+ ',' +
						       str(robot11_x) + ',' + str(robot11_y)+ ',' +
						       str(robot12_x) + ',' + str(robot12_y)+ ',' +
						       str(robot13_x) + ',' + str(robot13_y)+ ',' +
						       str(robot14_x) + ',' + str(robot14_y)+ ',' +
						       str(robot15_x) + ',' + str(robot15_y))
										       
					area_covered=s.update_grid()	
					if master_flag:								
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					area=gui.show_coverage(area_covered,elapsed_time)
					#print("!!!!!!!!!!!!AREA covered!!!!!!!!",area*10,elapsed_time)
					msg=(str('search')+','+str(area*10)+','+str(elapsed_time))
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
			
				
		if(data==b"aggregate") or (aggregate_flag):
			search_flag=False
			if master_flag:
				sent = graph_socket.sendto(str("aggregate").encode(), graph_server_address)				
				index="data"	
				uav_home_pos=[]
				for vehicle in vehicles:
				    lat = vehicle.location.global_relative_frame.lat
				    lon = vehicle.location.global_relative_frame.lon
				    # Process the lat and lon as needed
				    #print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
				    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
				    uav_home_pos.append((x / 2, y / 2))
				serialized_data = json.dumps(home_pos)
				serialized_data="uav_home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				for i in range(len(pos_array)):
					uav1.sendto(serialized_data.encode(),uav1_server_address)
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					time.sleep(0.05)
					"""
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)
					"""
			if not start_return_csv_flag:
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
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
			current_goal_index = [0] * num_bots			
			goal_table=[0]*num_bots
			#print("goal_table",goal_table)
			current_table=[0]*num_bots
			length_arr=[0]*num_bots
			new_length_arr=[0]*num_bots
			count=[0]*num_bots
			step=0
			all_bot_reach_flag_rev=False
			bot_array_rev=[0]*num_bots
			while True:
				if(return_height_flag):
					index = "data"
					velocity_flag=True	
					same_alt_flag=False
					alt=[0]*num_bots
					alt_count=[0]*num_bots
					alt_count1=0
					while True:	
						time.sleep(0.01)
						if(index==b"stop"):
							for i in range(3):
								sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
							index="data"
							aggregate_flag=True
							return_height_flag=False
							flag_stop=True
							data=b"stop"
							break
						if(aggregate_flag):
							print("aggregate_flag####")
							break				
						print("velocity_flag",velocity_flag)						
						if(vehicle_lost_flag):
							vehicle_lost_flag=True
							x=remove_vehicle()
							print(x)
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
								for i,vehicle in enumerate(vehicles):
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
										
										message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
										graph_socket.sendto(str(message).encode(), graph_server_address)  	
										removed_uav_homepos_array.append(home_pos.pop(i))
									
										print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
									'''
									alt[i]=vehicle.location.global_relative_frame.alt 
									print("alt[vehicle]",alt[i])
									if same_alt_flag:
										if same_height - 1.5 <= alt[i] <= same_height+1.5:
											alt_count[i]=1
											if all(count==1 for count in alt_count):
												print("Reached target altitude")
												return_height_flag=False
												aggregate_flag=True
												break			
									else:
										if different_height[i] - 1.5 <= alt[i] <= different_height[i]+1.5:
											alt_count[i]=1			
											if all(count==1 for count in alt_count):
												print("Reached target altitude")
												return_height_flag=False
												aggregate_flag=True
												break
							else:
								return_height_flag=False
								aggregate_flag=True
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
					time.sleep(0.02)
				elif(num_bots==2):
					time.sleep(0.021)
				elif(num_bots==1):
					time.sleep(0.024)
				if(return_flag):
					break
				step+=1
				if(vehicle_lost_flag):
					vehicle_lost_flag=True
					x=remove_vehicle()
					print(x)
				if(step==1):										
					for i,b in enumerate(s.swarm):						
						current_position = [b.x,b.y]
						nearest_goal = min(multiple_goals, key=lambda goal: distance.euclidean(current_position, goal))

						goal_table[i]=multiple_goals.index(nearest_goal)
						#print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)	
				
				else:										
					for i,b in enumerate(s.swarm):
						if(vehicle_lost_flag):
							vehicle_lost_flag=True
							x=remove_vehicle()
							print(x)
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
							message= "vehicle "+str(pos_array[i])+" has no heartbeat"             
							graph_socket.sendto(str(message).encode(), graph_server_address)
							removed_uav_homepos_array.append(home_pos.pop(i))
						
							print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
						'''
						current_position = [b.x,b.y]
						ind=goal_table[i]
						next_goal=bot_paths[ind]
						if(step==2):
							length_arr[i]=len(bot_paths[ind])
							new_length_arr[i]=length_arr[i]
						if(count[i]==length_arr[i]):
							continue
						
						if(len(bot_paths[ind])<1):							
							print("BOT {i} goal reached",i)
							continue
						
						goal=agg_goal_point
						cmd = base_control.base_control(i,b,goal)*10
						cmd+= base_control.obstacle_avoidance(i,b,goal)*50
						cmd += aggr_centroid(b, neighbourhood_radius=500 ,single_state=False, state=0)*50
						t = b.sim.time_elapsed
						weight_exp = hyperbolic(t)
						#print(weight_exp,"weight_exp")
						cmd += exp.explore(b)*weight_exp						
						cmd.exec(b)							
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])						
						if(dx<=5 and dy<=5):									
							new_length_arr[i]=new_length_arr[i]-1
							print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)
							count[i]+=1
						#print("count array",count)
						if(count[i]>=1):
							print("Drone ",i,"reached")
							bot_array_rev[i]=1
						#print("bot_array_rev",bot_array_rev)
						count_1=0	
						for j in range(num_bots):
							if(bot_array_rev[j]==1):
								count_1+=1
							#print("count_1",count_1)
							if(count_1==num_bots):
								aggregate_flag=False
								if start_return_csv_flag:
									return_flag=True
								else:
									return_flag=False
								print(return_height_flag,return_flag,"return_height_flag,return_flag")
								break
						if master_flag:		
							current_position =[b.x*2,b.y*2]
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
						       str(robot10_x) + ',' + str(robot10_y)+ ',' +
						       str(robot11_x) + ',' + str(robot11_y)+ ',' +
						       str(robot12_x) + ',' + str(robot12_y)+ ',' +
						       str(robot13_x) + ',' + str(robot13_y)+ ',' +
						       str(robot14_x) + ',' + str(robot14_y)+ ',' +
						       str(robot15_x) + ',' + str(robot15_y))
										       
					if master_flag:			
						sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
					
					if(index==b"stop"):
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						index="data"
						aggregate_flag=False
						flag_stop=True
						data=b"stop"
						break
					
					if(index==b"return"):
						return_flag=True
						aggregate_flag=False
					
		if(data==b"return") or (return_flag):
			index="data"
			if master_flag:
				sent = graph_socket.sendto(str("return").encode(), graph_server_address)				
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
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					"""
					time.sleep(0.05)
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)
					"""
				s = sim.Simulation(uav_home_pos,num_bots=num_bots, env_name=file_name)
				serialized_data = json.dumps(home_pos)
				serialized_data="home_pos" + serialized_data
				sent = graph_socket.sendto(serialized_data.encode(), graph_server_address)
				serialized_goal_data = json.dumps(goal_points)
				serialized_goal_data="goal_points" + serialized_goal_data
				print("serialized_goal_data",serialized_goal_data)
				sent = graph_socket.sendto(serialized_goal_data.encode(), graph_server_address)

			for b in s.swarm:	
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
					message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
					graph_socket.sendto(str(message).encode(), graph_server_address) 
					removed_uav_homepos_array.append(home_pos.pop(i))
					print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
				'''
				
				multiple_goals=return_multiple_goals				
				bot_paths={}
				for i in range(len(multiple_goals)):
					bot_paths[i]=multiple_goals[:i+1][::-1]
				#print("bot_paths",bot_paths)
				
				YOUR_GOAL_THRESHOLD_DISTANCE=15
				YOUR_THRESHOLD_DISTANCE=15
				current_goal_index = [0] * num_bots			
				goal_table=[0]*num_bots
				#print("goal_table",goal_table)
				current_table=[0]*num_bots
				length_arr=[0]*num_bots
				new_length_arr=[0]*num_bots
				count=[0]*num_bots
				step=0
				search_flag=False
				bot_array_return=[0]*num_bots
				all_bot_reach_flag_1=False
				print("return_flag################",return_flag)
				while 1:
					
					if(home_flag):
						break					
					if(num_bots==10):
						time.sleep(0.003)
					elif(num_bots==9):
						time.sleep(0.008)
					elif(num_bots==8):
						time.sleep(0.01)
					elif(num_bots==7):
						time.sleep(0.01)
					elif(num_bots==6):
						time.sleep(0.015)#verified
					elif(num_bots==5):
						time.sleep(0.012)#verified
					elif(num_bots==4):
						time.sleep(0.015)
					elif(num_bots==3):
						time.sleep(0.018)
					elif(num_bots==2):
						time.sleep(0.021)
					elif(num_bots==1):
						time.sleep(0.024)
					step+=1
					if(vehicle_lost_flag):
						vehicle_lost_flag=True
						x=remove_vehicle()
						print(x)

					if(step==1):
						#print("step",step)
						for i,b in enumerate(s.swarm):						
							current_position = [b.x,b.y]
							with open('/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv','rt')as text:
								data = csv.reader(text)
								for row in data: 
									data = (row)
									#print ("loc",data[-1])
									nextwaypoint=int(data[-1])				
									if(len(multiple_goals)-1== nextwaypoint) or nextwaypoint == 0 :
										pass		
									else:
										nextwaypoint-=1
							
							#print("nextwaypoint",nextwaypoint)
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
							print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
					else:
						for i,b in enumerate(s.swarm):
							current_position = [b.x,b.y]
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
								        		
								message= "vehicle "+str(pos_array[i])+" has no heartbeat"                   		
								graph_socket.sendto(str(message).encode(), graph_server_address) 
								removed_uav_homepos_array.append(home_pos.pop(i))
							
								print("home_pos,removed_uav_homepos_array",home_pos,removed_uav_homepos_array,len(home_pos))
									#print("current_position",current_position)
							'''
							ind=goal_table[i]
							next_goal=bot_paths[ind]
							if(step==2):
								length_arr[i]=len(bot_paths[ind])
								new_length_arr[i]=length_arr[i]
							if(count[i]==length_arr[i]):
								continue
							if(len(bot_paths[ind])<1):							
								print("BOT {i} goal reached",i)
								continue
							goal=bot_paths[goal_table[i]][count[i]]
							cmd =cvg.goal_area_cvg(i,b,goal)
							cmd.exec(b)
							dx=abs(goal[0]-current_position[0])
							dy=abs(goal[1]-current_position[1])						
							if(dx<=10 and dy<=10):
								bot_array_return[i]=1	
							count_1=0
							for j in range(num_bots):
								if(bot_array_return[j]==1):
									count_1+=1
								if(count_1==num_bots):
									count_1=0
									bot_array_return=[0]*num_bots
									all_bot_reach_flag_1=True

							
							if (all_bot_reach_flag_1==True):		
								with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
									fieldnames = ['waypoint']
									writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
									writer.writerow({'waypoint':multiple_goals.index(goal)})
									print("multiple_goals.index(goal)",multiple_goals.index(goal))
									goal_path_csv_array.append(multiple_goals.index(goal))
									print("goal_path_csv_array",goal_path_csv_array)
									goal_path_csv_array_flag=True		
								new_length_arr[i]=new_length_arr[i]-1
								print("new_length_arr[i],length_arr[i]-1",new_length_arr[i],length_arr[i]-1)

								for k in range(num_bots):
									count[k]+=1
								all_bot_reach_flag_1=False
								bot_array_return=[0]*num_bots
								if (goal==bot_paths[ind][-1]):
									print("Break")
									return_flag=False
									home_flag=True						
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
							       str(robot10_x) + ',' + str(robot10_y)+ ',' +
							       str(robot11_x) + ',' + str(robot11_y)+ ',' +
							       str(robot12_x) + ',' + str(robot12_y)+ ',' +
							       str(robot13_x) + ',' + str(robot13_y)+ ',' +
							       str(robot14_x) + ',' + str(robot14_y)+ ',' +
							       str(robot15_x) + ',' + str(robot15_y))
											       
						if master_flag:				       
							if goal_path_csv_array_flag:
							    int_value = int(goal_path_csv_array[-1])
							    #print("int_value",int_value)
							    msg += ","+'return_path' + str(int_value)
							    sent = graph_socket.sendto(str(msg).encode(), graph_server_address)	
						
					if(index==b"stop"):
						for i in range(3):
							sent = graph_socket.sendto(str("stop").encode(), graph_server_address)
						print("return_flag################",return_flag)
						return_flag=False
						aggregate_flag=False
						start_flag=False
						break
													
		if(data==b"home") or (home_flag):
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
					time.sleep(0.05)
					uav2.sendto(serialized_data.encode(),uav2_server_address)
					time.sleep(0.05)
					uav3.sendto(serialized_data.encode(),uav3_server_address)
					time.sleep(0.05)
					uav4.sendto(serialized_data.encode(), uav4_server_address)
					time.sleep(0.05)
					uav5.sendto(serialized_data.encode(), uav5_server_address)
					"""
					time.sleep(0.05)
					uav6.sendto(serialized_data.encode(), uav6_server_address)
					time.sleep(0.05)
					uav7.sendto(serialized_data.encode(), uav7_server_address)
					time.sleep(0.05)
					uav8.sendto(serialized_data.encode(), uav8_server_address)
					time.sleep(0.05)
					uav9.sendto(serialized_data.encode(), uav9_server_address)
					time.sleep(0.05)
					uav10.sendto(serialized_data.encode(), uav10_server_address)
					time.sleep(0.05)
					uav11.sendto(serialized_data.encode(), uav11_server_address)
					time.sleep(0.05)
					uav12.sendto(serialized_data.encode(), uav12_server_address)
					time.sleep(0.05)
					uav13.sendto(serialized_data.encode(), uav13_server_address)
					time.sleep(0.05)
					uav14.sendto(serialized_data.encode(), uav14_server_address)
					time.sleep(0.05)
					uav15.sendto(serialized_data.encode(), uav15_server_address)
					"""
				s = sim.Simulation(uav_home_pos,num_bots=len(pos_array), env_name=file_name )
				home_flag=True
				sent = graph_socket.sendto(str("home").encode(), graph_server_address)				
			bot_array_home=[0]*num_bots
			all_bot_reach_flag_home=False
			print("Home.......",home_pos)
			index="data"
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
				if(home_flag1):
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
					#print("current_position",current_position)
					cmd =cvg.goal_area_cvg(i,b,home_pos[i])
					goal=home_pos[i]
					#Execute
					cmd.exec(b)					
					dx=abs(goal[0]-current_position[0])
					dy=abs(goal[1]-current_position[1])						
					#print("dx,dy",dx,dy)					
					if(dx<=0.1 and dy<=0.1):
						bot_array_home[i]=1	
					count_home=0
					#print("count_home",count_home)
					for j in range(num_bots):
						if(bot_array_home[j]==1):
							count_home+=1
						if(count_home==num_bots):
							count_home=0
							bot_array_home=[0]*num_bots
							all_bot_reach_flag_home=True

					if (all_bot_reach_flag_home==True):
						with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'a') as csvfile:
							fieldnames = ['waypoint']
							writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
							writer.writerow({'waypoint':-1})	
						home_flag1=True
							
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
					       str(robot10_x) + ',' + str(robot10_y)+ ',' +
					       str(robot11_x) + ',' + str(robot11_y)+ ',' +
					       str(robot12_x) + ',' + str(robot12_y)+ ',' +
					       str(robot13_x) + ',' + str(robot13_y)+ ',' +
					       str(robot14_x) + ',' + str(robot14_y)+ ',' +
					       str(robot15_x) + ',' + str(robot15_y))
									       
				if master_flag:			
					sent = graph_socket.sendto(str(msg).encode(), graph_server_address)	
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
				       str(robot10_x) + ',' + str(robot10_y)+ ',' +
				       str(robot11_x) + ',' + str(robot11_y)+ ',' +
				       str(robot12_x) + ',' + str(robot12_y)+ ',' +
				       str(robot13_x) + ',' + str(robot13_y)+ ',' +
				       str(robot14_x) + ',' + str(robot14_y)+ ',' +
				       str(robot15_x) + ',' + str(robot15_y))
			if master_flag:				      							
				sent = graph_socket.sendto(str(msg).encode(), graph_server_address)
				with open(r'/home/dhaksha/Desktop/meharbaba/swarm_tasks/Examples/basic_tasks/pos.csv', 'w') as csvfile:
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
