import sys,os
import socket
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..')))
import locatePosition
from scipy.spatial import distance
import swarm_tasks

#Set demo parameters directly
import numpy as np
import random
swarm_tasks.utils.robot.DEFAULT_NEIGHBOURHOOD_VAL = 6
swarm_tasks.utils.robot.DEFAULT_SIZE= 0.4
swarm_tasks.utils.robot.MAX_SPEED = 5
swarm_tasks.utils.robot.MAX_ANGULAR = 1.0
np.random.seed(42)
random.seed(42)

from swarm_tasks.simulation import simulation as sim
from swarm_tasks.simulation import visualizer as viz
from swarm_tasks.modules.formations import line

import swarm_tasks.utils as utils
import swarm_tasks.envs as envs
import swarm_tasks.controllers as ctrl
import swarm_tasks.controllers.potential_field as potf
import swarm_tasks.controllers.base_control as base_control

from swarm_tasks.tasks import area_coverage as cvg
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative
import threading

vehicle1= connect('udpin:192.168.29.226:14551',baud=115200, heartbeat_timeout=30)
vehicle1.airspeed = 8
print('Drone1')
vehicle2= connect('udpin:192.168.29.226:14552',baud=115200,heartbeat_timeout=30)
vehicle2.airspeed = 8
print('Drone2')
vehicle3= connect('udpin:192.168.29.226:14553',baud=115200,heartbeat_timeout=30)
vehicle3.airspeed = 8
print('Drone3')
vehicle4= connect('udpin:192.168.29.226:14554',baud=115200,heartbeat_timeout=30)
vehicle4.airspeed = 8
print('Drone4')
vehicle5= connect('udpin:192.168.29.226:14555',baud=115200,heartbeat_timeout=30)
vehicle5.airspeed = 8
print('Drone5')
vehicle6= connect('udpin:192.168.29.226:14556',baud=115200,heartbeat_timeout=30)
vehicle6.airspeed = 8
print('Drone6')
vehicle7= connect('udpin:192.168.29.226:14557',baud=115200,heartbeat_timeout=30)
vehicle7.airspeed = 8
print('Drone7')
vehicle8= connect('udpin:192.168.29.226:14558',baud=115200,heartbeat_timeout=30)
vehicle8.airspeed = 8
print('Drone8')
'''
vehicle9= connect('udpin:192.168.29.226:14559',baud=115200,heartbeat_timeout=30)
vehicle9.airspeed = 8
print('Drone9')
vehicle10= connect('udpin:192.168.29.226:14560',baud=115200,heartbeat_timeout=30)
vehicle10.airspeed = 8
print('Drone10')
vehicle11= connect('udpin:192.168.29.226:14561',baud=115200,heartbeat_timeout=30)
vehicle11.airspeed = 8
print('Drone11')
vehicle12= connect('udpin:192.168.29.226:14562',baud=115200,heartbeat_timeout=30)
vehicle12.airspeed = 8
print('Drone12')
vehicle13= connect('udpin:192.168.29.226:14563',baud=115200,heartbeat_timeout=30)
vehicle13.airspeed = 8
print('Drone13')
vehicle14= connect('udpin:192.168.29.226:14564',baud=115200,heartbeat_timeout=30)
vehicle14.airspeed = 8
print('Drone14')
vehicle15= connect('udpin:192.168.29.226:14565',baud=115200,heartbeat_timeout=30)
vehicle15.airspeed = 8
print('Drone15')
'''
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
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto
    #  (otherwise the command after Vehicle.simple_takeoff will execute
    #   immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)
'''
vehicle1_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle1, 30))
vehicle2_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle2, 33))
vehicle3_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle3, 36))
vehicle4_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle4, 39))
vehicle5_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle5, 42))
vehicle6_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle6, 45))
vehicle7_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle7, 48))
vehicle8_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle8, 51))

vehicle9_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle9, 10))
vehicle10_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle10, 10))
vehicle11_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle11, 10))
vehicle12_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle12, 10))
vehicle13_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle13, 10))
vehicle14_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle14, 10))
vehicle15_thread = threading.Thread(target=arm_and_takeoff, args=(vehicle15, 10))

#time.sleep(15)
# Start the threads

vehicle1_thread.start()
vehicle2_thread.start()
vehicle3_thread.start()
vehicle4_thread.start()
vehicle5_thread.start()
vehicle6_thread.start()
vehicle7_thread.start()
vehicle8_thread.start()

vehicle9_thread.start()
vehicle10_thread.start()
vehicle11_thread.start()
vehicle12_thread.start()
vehicle13_thread.start()
vehicle14_thread.start()
vehicle15_thread.start()

# Wait for all threads to finish
vehicle1_thread.join()
vehicle2_thread.join()
vehicle3_thread.join()
vehicle4_thread.join()
vehicle5_thread.join()
vehicle6_thread.join()
vehicle7_thread.join()
vehicle8_thread.join()

vehicle9_thread.join()
vehicle10_thread.join()
vehicle11_thread.join()
vehicle12_thread.join()
vehicle13_thread.join()
vehicle14_thread.join()
vehicle15_thread.join()
'''
num_bots=8
count=0
origin=(  12.928041,  80.044667)
endDistance=2000
same_height=20
different_height=[30,33,36,39,42,45,48,51]
home_pos=[]
vehicles = [globals()[f'vehicle{i}'] for i in range(1, num_bots+1)]
uav_home_pos=[]
# Iterate over the list of vehicles
for vehicle in vehicles:
    lat = vehicle.location.global_relative_frame.lat
    lon = vehicle.location.global_relative_frame.lon

    # Process the lat and lon as needed
    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
    print("x,y",x/2,y/2)
    uav_home_pos.append((x / 2, y / 2))
home_pos=uav_home_pos
#print("uav_home_pos",uav_home_pos)     

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('192.168.29.226', 12005)  #receive from .....rx.py


sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address2 = ('', 12008)  #receive from .....rx.py
sock2.bind(server_address2)
sock2.setblocking(0)

sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address3 = ('', 12002)  #receive from .....rx.py
sock3.bind(server_address3)


sim_flag=False
s = sim.Simulation(uav_home_pos,num_bots=8, env_name='rectangles' )
#s = sim.Simulation(num_bots=8, env_name='rectangles' )
area_covered = 0
start_time = time.time()
visited_positions = set()
data=""

elapsed_time= time.time() - start_time
gui = viz.Gui(s)
gui.show_env()
gui.show_bots()
#gui.show_grid()
#gui.show_coverage(area_covered,elapsed_time)
gui.show_coverage(area_covered,elapsed_time)
value=[]


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


robot_positions = [([0, 0]) for _ in range(20)]
index=0
flag_stop=False
flag=False
def vehicle_collision_moniter_receive():	
        global index
        while 1:
        	index, address = sock3.recvfrom(1024)
        	print ("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", index)
		
			
 			
collision_thread = threading.Thread(target=vehicle_collision_moniter_receive)
collision_thread.daemon=True
collision_thread.start()
#print("resume")

uav_pos=[]
flag_goal=False
velocity_flag=False
same_alt_flag=False
pop_flag_arr=[1]*num_bots
pop_flag=False
specific_bot_goal_flag=False
pop_bot_index=None
goal_bot_num=None
while 1:
	#time.sleep(0.095)
	try:            
		data, address = sock2.recvfrom(1050)
		print ("msg", data)
		if(data==b"rtl"):			
			print("rtl!!!!!!!!!!!!!!!!")
			
			print("Returning to Launch vehicle 1")
			vehicle1.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 2")
			vehicle2.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 3")
			vehicle3.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 4")
			vehicle4.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 5")
			vehicle5.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 6")
			vehicle6.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 7")
			vehicle7.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 8")
			vehicle8.mode = VehicleMode("RTL")
			'''
			print("Returning to Launch vehicle 9")
			vehicle9.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 10")
			vehicle10.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 11")			
			vehicle11.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 12")
			vehicle12.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 13")
			vehicle13.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 14")
			vehicle14.mode = VehicleMode("RTL")
			print("Returning to Launch vehicle 15")
			vehicle15.mode = VehicleMode("RTL")		
			'''			

			print("Close vehicle 1 object")
			vehicle1.close()
			print("Close vehicle 2 object")
			vehicle2.close()
			print("Close vehicle 3 object")
			vehicle3.close()
			print("Close vehicle 4 object")
			vehicle4.close()
			print("Close vehicle 5 object")
			vehicle5.close()
			print("Close vehicle 6 object")
			vehicle6.close()
			print("Close vehicle 7 object")
			vehicle7.close()
			print("Close vehicle 8 object")
			vehicle8.close()
			'''
			print("Close vehicle 9 object")
			vehicle9.close()
			print("Close vehicle 10 object")
			vehicle10.close()			
			print("Close vehicle 11 object")
			vehicle11.close()
			print("Close vehicle 12 object")
			vehicle12.close()
			print("Close vehicle 13 object")
			vehicle13.close()
			print("Close vehicle 14 object")
			vehicle14.close()
			print("Close vehicle 15 object")
			vehicle15.close()						
			'''
			break
						
		if(data==b"stop"):
			velocity_flag=True	
			print("Velocity zero called##############!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")	
			while True:					
				#print("velocity_flag",velocity_flag)						
				for i, b in enumerate(s.swarm):
					if(pop_flag):	
						if(i>=pop_bot_index):
							i+=1
					print("Velocity zero called##############!!!!!!!!!!!")
					cmd = potf.velocity(b.get_position(), b.sim, weights=potf.field_weights, order = 2, max_dist=3)
					cmd.exec(b)
					# Break out of the loop
					print("Velocity zero!!!!!!!!!!!")			
					value=[b.x*2,b.y*2]
					
					gui.show_coverage(area_covered,elapsed_time)
					#gui.show_coverage(area_covered),elapsed_time)
					
					print("Velocity Bot State",b.state)

					print("Drone 1 position",b.x,b.y)
					lat,lon = locatePosition.cartToGeo (origin, endDistance, value)
					#print ("Drone 1 lat,lon", lat,lon)
					if same_alt_flag:
						point1 = LocationGlobalRelative(lat,lon,same_height)
					else:
						point1 = LocationGlobalRelative(lat,lon,different_height[i])
					#print("point1",point1)
					vehicles[i].simple_goto(point1)
					
				if(index==b"resume"):
					index="data"
					velocity_flag=False
					print("1st")
					data="search"
					break
				if(index==b"same"):
					index="data"
					same_alt_flag=True
					
				if(index==b"different"):
					index="data"
					same_alt_flag=False
				if(index==b"search"):	
					index="data"
					data="search"
					break
			break										
			
		if(data == b"return"):
			print("Returning home!!!!!")
						
			multiple_goals=[ (35.90396282632777,66.41069933221634), (53.67301562074577,61.15028745701215),(59.72548887519441,75.7620373638096), (67.3908687933235,94.4996922955254), (115.77794435913532,75.81196367472195), (76.88432224281048,52.30554162290515), (102.05153767562574,44.621471767157615),  (106.51923290284807,57.229910201226254), (159.47766578648816,26.470351621780416), (172.5013414050436,55.592001591328746), (193.07443430252422,50.56668095048309), (187.7939145421656,93.31127124770721), (134.998240200056,122.55312638573875), (83.2536661121681,65.28703534882858), (124.74915247329356,38.360431793082526), (141.04588014486154,67.59674523733192), (129.1064654386974,46.11024326517572)]
			
			
			bot_paths={
				   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4]],				   
				   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4]],				   
				   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4]],				   
				   3:[multiple_goals[3],multiple_goals[4]],				   
				   4:[multiple_goals[4]],
				   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
				   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4]],
				   7:[multiple_goals[7],multiple_goals[4]],
				   8:[multiple_goals[8],multiple_goals[9],multiple_goals[15],multiple_goals[4]],
				   9:[multiple_goals[9],multiple_goals[4]],
				   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4]],
				   11:[multiple_goals[11],multiple_goals[9],multiple_goals[4]],
				   12:[multiple_goals[12],multiple_goals[4]],
				   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4]],
				   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
				   15:[multiple_goals[15],multiple_goals[4]],
				   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
			}
			
			YOUR_GOAL_THRESHOLD_DISTANCE=15
			YOUR_THRESHOLD_DISTANCE=15
			current_goal_index = [0] * len(s.swarm)			
			goal_table=[0]*len(s.swarm)
			print("goal_table",goal_table)
			current_table=[0]*len(s.swarm)
			length_arr=[0]*len(s.swarm)
			new_length_arr=[0]*len(s.swarm)
			count=[0]*len(s.swarm)
			step=0
			while 1:
				print("############")
				step+=1
				print("step",step)
				if(step==1):
					print("step",step)
					for i,b in enumerate(s.swarm):
						#print("potf.reached_goals",potf.reached_goals)							
						#if(potf.reached_goals[i]==False):
						current_position = [b.x,b.y]
						nearest_goal = min(multiple_goals, key=lambda goal: distance.euclidean(current_position, goal))
						print("current_position , nearest_goal",current_position,nearest_goal)
						goal_table[i]=multiple_goals.index(nearest_goal)
						#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
						print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
						
				
				else:
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]
						#print("current_position",current_position)
						
						#count[goal_table[i]]=count[goal_table[i]]+1
						#print("counter array",count)
						print("BOT {} reached",i)
						print("goal_table[goal_index]",goal_table)
						ind=goal_table[i]
						print("ind",ind)
						next_goal=bot_paths[ind]
						print("next_goal",next_goal)
						if(step==2):
							length_arr[i]=len(bot_paths[ind])
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
						print("goal",goal)
						cmd =cvg.goal_area_cvg(i,b,goal)
						cmd.exec(b)
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])						
						print("dx,dy",dx,dy)
						if(dx<=3 and dy<=3):									
							print("Goal_reached!!!!!!!!!!!")	
							new_length_arr[i]=length_arr[i]-1
							count[i]+=1

						current_position =[b.x*2,b.y*2]
						print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						#print ("Drone 1 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						#print("point1",point1)
						vehicles[i].simple_goto(point1)	
						
				if(index==b"stop"):
					index="data"
					print("#####################################")
					flag_stop=True
					data=b"stop"
					break
				if(index==b"goal_start"):
					index="data"
					print("#####################################")
					flag_stop=False
				if(index==b"same"):
					index="data"
					same_alt_flag=True
					
				if(index==b"different"):
					index="data"
					same_alt_flag=False
					
					
				if(index==b"return_agg"):
					index="data"
					
					uav_home_pos=[]
					for vehicle in vehicles:
					    lat = vehicle.location.global_relative_frame.lat
					    lon = vehicle.location.global_relative_frame.lon

					    # Process the lat and lon as needed
					    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
					    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
					    print("x,y",x/2,y/2)
					    uav_home_pos.append((x / 2, y / 2))
					gui.close()
					s = sim.Simulation(uav_home_pos,num_bots=8, env_name='rectangles2' )
					#s = sim.Simulation(num_bots=8, env_name='rectangles2' )
					gui = viz.Gui(s)
					gui.show_env()
					gui.show_bots()
					gui.update()

					multiple_goals=[(73.96117636452117,127.91803579497369), (65.54634695629352,109.12755801065643),  (63.41013384479621,97.84401186422897), (91.5160768050321,86.09636802282125), (116.38987154994989,75.54532264396974)]								
					
					bot_paths={
						   0:[multiple_goals[0]],				   
						   1:[multiple_goals[1]],
						   2:[multiple_goals[2],multiple_goals[1]],
						   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
						   4:[multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],						   
					}
					final_goals = [(56.67060240327152,137.11571147923303), (54.882715329261764,133.22353799842614), (52.865002099561295,129.20586596431852), (50.89323076160417,124.05617544812814), (49.47316838663865,120.3060434579547), (47.189383071261595,116.54279450950776), (45.40149599802176,112.31700615897387), (43.126003358093,107.4239880688872)]
					
					YOUR_GOAL_THRESHOLD_DISTANCE=15
					YOUR_THRESHOLD_DISTANCE=15
					current_goal_index = [0] * len(s.swarm)			
					goal_table=[0]*len(s.swarm)
					print("goal_table",goal_table)
					current_table=[0]*len(s.swarm)
					length_arr=[0]*len(s.swarm)
					new_length_arr=[0]*len(s.swarm)
					count=[0]*len(s.swarm)
					step=0
					search_flag=False
					while 1:
						print("############")
						step+=1
						print("step",step)
						if(step==1):
							print("step",step)
							for i,b in enumerate(s.swarm):
								#print("potf.reached_goals",potf.reached_goals)							
								#if(potf.reached_goals[i]==False):
								current_position = [b.x,b.y]
								nearest_goal = min(multiple_goals, key=lambda goal: distance.euclidean(current_position, goal))
								print("current_position , nearest_goal",current_position,nearest_goal)
								goal_table[i]=multiple_goals.index(nearest_goal)
								#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
								print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
								
						
						else:
							for i,b in enumerate(s.swarm):
								current_position =[b.x,b.y]
								#print("current_position",current_position)
								
								#count[goal_table[i]]=count[goal_table[i]]+1
								#print("counter array",count)
								#print("BOT {} reached",i)
								print("goal_table[goal_index]",goal_table)
								ind=goal_table[i]
								print("ind",ind)
								next_goal=bot_paths[ind]
								print("next_goal",next_goal)
								if(step==2):
									length_arr[i]=len(bot_paths[ind])
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
								print("goal",goal)
								cmd =cvg.goal_area_cvg(i,b,goal)
								cmd.exec(b)
								dx=abs(goal[0]-current_position[0])
								dy=abs(goal[1]-current_position[1])						
								print("dx,dy",dx,dy)
								if(dx<=3 and dy<=3):									
									print("Goal_reached!!!!!!!!!!!")	
									new_length_arr[i]=length_arr[i]-1
									count[i]+=1
										
								current_position =[b.x*2,b.y*2]
								#print("Drone 1 position",b.x,b.y)
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								#print ("Drone 1 lat,lon", lat,lon)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,differnt_height[i])
								#print("point1",point1)
								vehicles[i].simple_goto(point1)
								
						gui.update()	
						
						if(index==b"stop"):
							index="data"
							data="stop"
							break
											
						if(index==b"home"):
							index="data"
							#final_goals=[(32.2903241227201,70.00352017528128), (35.39587659192968,75.58573212764202), (38.05795344104797,82.5689642372139), (39.2898384507857,88.63539580017397), (41.28827430586475,95.07825618578006), (42.27075017965216,100.97797008134192), (45.283618766992234,107.71733173558592), (47.337998444613156,117.27735698811121)]
							final_goals=home_pos
							potf.reached_goals=[False]*num_bots
							while 1:
								if all(potf.reached_goals):
									print("potf.reached_goals",potf.reached_goals)
									#break
									exit()
								print("potf.reached_goals",potf.reached_goals)
								for i,b in enumerate(s.swarm):
									if(potf.reached_goals[i]==False):
										current_position = (b.x*2, b.y*2)
																	
										cmd =cvg.goal_area_cvg(i,b,final_goals[i])
										cmd.exec(b)
										print("Drone 1 position",b.x,b.y)
										lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
										#print ("Drone 1 lat,lon", lat,lon)
										if same_alt_flag:
											point1 = LocationGlobalRelative(lat,lon,same_height)
										else:
											point1 = LocationGlobalRelative(lat,lon,different_height[i])
										#print("point1",point1)
										vehicles[i].simple_goto(point1)
										
										if(index==b"stop"):
											index="data"
											flag_stop=True											
											break

										
								gui.update()
								if(index==b"exit"):
									exit()
														
					if(flag_stop):
						break							
														
				#sent = sock.sendto(str(msg).encode(), server_address)
				coverage_area = (len(visited_positions) / (s.grid.size/10)) * 100
				#print(f"Area covered = {coverage_area:.2f}%")
				gui.update()
			print("Goals_1 reached")
			if all(potf.reached_goals):
				print("potf.reached_goals",potf.reached_goals)
				break
			break
			exit()
		
		if(data==b"remove"):
				pop_flag=True
				pop_bot_index=5	
				pop_bot_index=	pop_bot_index-1		
				s.remove_bot(pop_bot_index)
				pop_flag_arr[pop_bot_index]=0
		
		if(data==b"add"):				
				bot_pos=[2349,376]
				bot_ind=pop_bot_index
				s.add_bot(bot_ind,bot_pos)
				#uav_home_pos.append((x / 2, y / 2))
				#uav_home_pos.append((bot_pos[0],bot_pos[1]))				
				uav_home_pos.insert(bot_ind,(bot_pos[0],bot_pos[1]))
				pop_flag=False
				pop_flag_arr[pop_bot_index]=1
				
		if(data==b"specific_bot_goal"):	
				try:
					print("bot_goal!!!!!!!!!!!!")
					index, address = sock3.recvfrom(1024)
					print("index",index)
					decoded_index = index.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					uav, goalx, goaly = decoded_index.split(",")
					#uav,goalx,goaly=str(index).split(",")
					print(uav,goalx,goaly)
					goal_bot_num=int(str(uav))
					print(goal_bot_num)
					goal_position=[float(goalx),float(goaly)]
					print(goal_position)
					goal_bot_num=goal_bot_num-1
					specific_bot_goal_flag=True
					while 1:
						if(potf.reached_goals[goal_bot_num]==True):		
							print("################hhhhhhhhhhhhhh#######")
							break					
						for i,b in enumerate(s.swarm):						
							if(potf.reached_goals[goal_bot_num]==True):		
								pop_flag=True
								pop_bot_index=goal_bot_num			
								s.remove_bot(goal_bot_num)
								pop_flag_arr[goal_bot_num]=0	
								print("break####################")
								break	
							'''
							if(potf.reached_goals[goal_bot_num]==True):										
								print("break####################")
								break	
							'''		
							if(pop_flag):	
								if(i>=pop_bot_index):
									i+=1					
							if(potf.reached_goals[goal_bot_num]==False):
								current_position = (b.x*2, b.y*2)						
								if(i==goal_bot_num):								
				
									print("i",i)
									#print("final_goals[goal_bot_num-1]",final_goals)
									#goal_position = final_goals[goal_bot_num-1]
									goal_position = [23,40]
									print("goal_position",goal_position)
									b.set_goal(goal_position[0], goal_position[1])
									cmd = cvg.goal_area_cvg(i, b, goal_position)								
									print("cmd11111 exceuted")
								else:
									print("dispersion")
									cmd = cvg.disp_exp_area_cvg(b)
									print("cmd exceuted")	

								print("@@@@@@@@@@@@@@@@@")			
								#print("final_goals[goal_bot_num-1]",final_goals[goal_bot_num-1])
								print("!!!!!!!!!!!!!!!!")
								cmd.exec(b) 	
								print("current_position",current_position)	
								print("Drone 1 position",b.x,b.y)
								lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
								#print ("Drone 1 lat,lon", lat,lon)
								if same_alt_flag:
									point1 = LocationGlobalRelative(lat,lon,same_height)
								else:
									point1 = LocationGlobalRelative(lat,lon,differnt_height)
								#print("point1",point1)
								vehicles[i].simple_goto(point1)
								
				except:
					print("exception")		
								
								
		if(data==b"nav_start"):
			multiple_goals=[ (201.17085628802127,191.97426012685696), (430.0299576080156,121.5363316277763), (581.468738086984,77.37929794272104),
 (591.3787484196037,122.92638515286971), (391.9421715848494,192.24189677210987), (300.7653031382698,219.55100199655226)]
			multiple_goals1=[(201.17085628802127,191.97426012685696)]
			bot_paths={
				   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[5]],				   
				   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[5]],
				   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[5]],
				   3:[multiple_goals[3],multiple_goals[4],multiple_goals[5]],
				   4:[multiple_goals[4],multiple_goals[5]],
				   5:[multiple_goals[5]],
			}
			
			YOUR_GOAL_THRESHOLD_DISTANCE=15
			YOUR_THRESHOLD_DISTANCE=15
			current_goal_index = [0] * len(s.swarm)			
			goal_table=[0]*len(s.swarm)
			print("goal_table",goal_table)
			current_table=[0]*len(s.swarm)
			length_arr=[0]*len(s.swarm)
			new_length_arr=[0]*len(s.swarm)
			count=[0]*len(s.swarm)
			step=0
			search_flag=False
			while 1:
				print("############")
				step+=1
				print("step",step)
				if(step==1):
					print("step",step)
					for i,b in enumerate(s.swarm):
						#print("potf.reached_goals",potf.reached_goals)							
						#if(potf.reached_goals[i]==False):
						current_position = [b.x,b.y]
						nearest_goal = min(multiple_goals1, key=lambda goal: distance.euclidean(current_position, goal))
						print("current_position , nearest_goal",current_position,nearest_goal)
						goal_table[i]=multiple_goals.index(nearest_goal)
						#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
						print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)
						
				
				else:
					for i,b in enumerate(s.swarm):
						current_position = [b.x,b.y]
						#print("current_position",current_position)
						
						#count[goal_table[i]]=count[goal_table[i]]+1
						#print("counter array",count)
						#print("BOT {} reached",i)
						print("goal_table[goal_index]",goal_table)
						ind=goal_table[i]
						print("ind",ind)
						next_goal=bot_paths[ind]
						print("next_goal",next_goal)
						if(step==2):
							length_arr[i]=len(bot_paths[ind])
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
						print("goal",goal)
						#Base control
						cmd = base_control.base_control(i,b,goal)
						cmd+= base_control.obstacle_avoidance(i,b,goal)
						
						#Behaviour
						cmd+=line(b)
						
						#Execute
						cmd.exec(b)
						dx=abs(goal[0]-current_position[0])
						dy=abs(goal[1]-current_position[1])						
						print("dx,dy",dx,dy)
						if(dx<=3 and dy<=3):									
							print("Goal_reached!!!!!!!!!!!")	
							new_length_arr[i]=length_arr[i]-1
							count[i]+=1
						'''
						current_position = [b.x*2,b.y*2]
						print("Drone 1 position",b.x,b.y)
						lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
						#print ("Drone 1 lat,lon", lat,lon)
						if same_alt_flag:
							point1 = LocationGlobalRelative(lat,lon,same_height)
						else:
							point1 = LocationGlobalRelative(lat,lon,different_height[i])
						vehicles[i].simple_goto(point1)
						'''
							
							
				if(index==b"disperse"):
					sim_flag=True
					index="data"
					
					uav_home_pos=[]
					for vehicle in vehicles:
					    lat = vehicle.location.global_relative_frame.lat
					    lon = vehicle.location.global_relative_frame.lon

					    # Process the lat and lon as needed
					    print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
					    x,y = locatePosition.geoToCart (origin, endDistance, [lat,lon])
					    print("x,y",x/2,y/2)
					    uav_home_pos.append((x / 2, y / 2))
					
					if(sim_flag):		
						gui.close()										
						s = sim.Simulation(uav_home_pos,num_bots=8, env_name='rectangles1' )
						#s = sim.Simulation(num_bots=8, env_name='rectangles1' )
						gui = viz.Gui(s)
						gui.show_env()
						gui.show_bots()
						gui.update()
						dispersion=[ (102.05153767562574,44.621471767157615), (134.998240200056,122.55312638573875),(172.5013414050436,55.592001591328746),(193.07443430252422,50.56668095048309), (187.7939145421656,93.31127124770721), (53.67301562074577,61.15028745701215), (106.51923290284807,57.229910201226254), (159.47766578648816,26.470351621780416),]
										
						while 1:
							if all(potf.reached_goals):
								print("potf.reached_goals",potf.reached_goals)
								break
							print("potf.reached_goals",potf.reached_goals)
							for i,b in enumerate(s.swarm):
								if(potf.reached_goals[i]==False):
									current_position = (b.x*2, b.y*2)		
									print("current_position",current_position)					
									cmd =cvg.goal_area_cvg(i,b,dispersion[i])
									cmd.exec(b)
									#print("Drone 1 position",b.x,b.y)
									lat,lon = locatePosition.cartToGeo (origin, endDistance, current_position)
									#print ("Drone 1 lat,lon", lat,lon)
									if same_alt_flag:
										point1 = LocationGlobalRelative(lat,lon,same_height)
									else:
										point1 = LocationGlobalRelative(lat,lon,different_height[i])
									#print("point1",point1)
									vehicles[i].simple_goto(point1)
									
							gui.update()
				
							if(index==b"search"):
								search_flag=True	
								index="data"		
								data="search"			
								print("Search started")
								break	
						if(search_flag):
							break
					
				
				#sent = sock.sendto(str(msg).encode(), server_address)
				#coverage_area = (len(visited_positions) / (s.grid.size/10)) * 100
				#print(f"Area covered = {coverage_area:.2f}%")
				gui.update()
												
			print("Goals_1 reached")
			#break	
		if(data==b"search"):			
			print("Search Started")	
			search_start_time = time.time()
			while 1:
				for i,b in enumerate(s.swarm):														
					#coverage = s.update_grid()		
					if(pop_flag):	
						print("pop_flag",pop_flag)			
						if(i>=pop_bot_index):
							i+=1
						
					cmd = cvg.disp_exp_area_cvg(b)
					#cmd = cvg.disp_exp_area_cvg(b, use_base_control=True, exp_weight_params=[1.0,1.5],disp_weight_params=[2.0,1.0]) * 2
					value=[b.x*2,b.y*2]
					cmd.exec(b)
					#print("value",i,value)
					#print("b.x,b.y",b.x,b.y)
					position = (round(b.x), round(b.y))
					# Check if the position has not been visited before
					if position not in visited_positions:
					    visited_positions.add(position)
					robot_positions[i] = [b.x, b.y]
					visited_positions.update(tuple(map(int, pos)) for pos in robot_positions)
					#print("x,y",i,b.x,b.y)
					#print(f"Robot {i + 1}: x={b.x}, y={b.y}")
					#print("elapsed_time",elapsed_time)
					elapsed_time = time.time() - search_start_time
					#print("elapsed_time",elapsed_time)
					gui.show_coverage(area_covered,elapsed_time)
					#gui.show_coverage(area_covered),elapsed_time)
					
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
				       str(robot8_x) + ',' + str(robot8_y))
								       
				area_covered=s.update_grid()				
				sent = sock.sendto(str(msg).encode(), server_address)				
				#gui.update_trajectory_plot()
				#print("!!!!!!!!!!")
				coverage_area = (len(visited_positions) / (s.grid.size)) * 1000
				#print(f"Area covered = {coverage_area:.3f}%")		
				elapsed_time = time.time() - start_time
				gui.show_coverage(area_covered,elapsed_time)
				#gui.show_coverage(area_covered,elapsed_time)				
				#s.update_grid()
				gui.update()
				s.time_elapsed += 1   
				
				if(index==b"return"):
					index="data"
					data="search"			
					print("Return started")
					break	
								
				if(index==b"bot_goal"):
					print("bot_goal!!!!!!!!!!!!")
					index, address = sock3.recvfrom(1024)
					print("index",index)
					decoded_index = index.decode('utf-8')  # Assuming utf-8 encoding, adjust if needed
					uav, goal= decoded_index.split(",")
					print(uav,goal)
					goal_bot_num=int(uav)
					print(goal_bot_num)
					goal_ind=int(goal)
					print(goal_ind)
					goal_bot_num=goal_bot_num-1
					goal_ind=goal_ind-1
					print("goal_ind",goal_ind)
					multiple_goals=[ (35.90396282632777,66.41069933221634), (53.67301562074577,61.15028745701215),(59.72548887519441,75.7620373638096), (67.3908687933235,94.4996922955254), (115.77794435913532,75.81196367472195), (76.88432224281048,52.30554162290515), (102.05153767562574,44.621471767157615),  (106.51923290284807,57.229910201226254), (159.47766578648816,26.470351621780416), (172.5013414050436,55.592001591328746), (193.07443430252422,50.56668095048309), (187.7939145421656,93.31127124770721), (134.998240200056,122.55312638573875), (83.2536661121681,65.28703534882858), (124.74915247329356,38.360431793082526), (141.04588014486154,67.59674523733192), (129.1064654386974,46.11024326517572), (165.65352541469167,97.95131865674259), (98.28772033194677,144.05458827520545), (70.59591283257126,151.6404360428771), (56.108333063992525,114.85732413566811)]
					if(goal_ind==0):
						bot_paths={
							   0:[multiple_goals[0]],				   
							   1:[multiple_goals[1],multiple_goals[0]],				   
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[0]],				   
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],				   
							   4:[multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   5:[multiple_goals[5],multiple_goals[1],multiple_goals[0]],
							   6:[multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[0]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[0]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[0]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   13:[multiple_goals[13],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[0]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[0]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							}
						
					if(goal_ind==1):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1]],				   
							   1:[multiple_goals[1]],				   
							   2:[multiple_goals[2],multiple_goals[1]],				   
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1]],				   
							   4:[multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   5:[multiple_goals[5],multiple_goals[1]],
							   6:[multiple_goals[6],multiple_goals[5],multiple_goals[1]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[5],multiple_goals[1]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[0]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   13:[multiple_goals[13],multiple_goals[2],multiple_goals[1]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1]],
							}
					if(goal_ind==2):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2]],				   
							   1:[multiple_goals[1],multiple_goals[2]],				   
							   2:[multiple_goals[2]],				   
							   3:[multiple_goals[3],multiple_goals[2]],				   
							   4:[multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   5:[multiple_goals[5],multiple_goals[1],multiple_goals[2]],
							   6:[multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2]],
							   7:[multiple_goals[7],multiple_goals[13],multiple_goals[2]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   13:[multiple_goals[13],multiple_goals[2]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[2]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[2]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[2]],
							}
					if(goal_ind==3):							
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3]],				   
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3]],				   
							   2:[multiple_goals[2],multiple_goals[3]],				   
							   3:[multiple_goals[3]],				   
							   4:[multiple_goals[4],multiple_goals[3]],
							   5:[multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[3]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[3]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[3]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[3]],
							   13:[multiple_goals[13],multiple_goals[2],multiple_goals[3]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[3]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[3]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[3]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[3]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[3]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3]],
							   20:[multiple_goals[20],multiple_goals[3]],
							}

					if(goal_ind==4):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4]],				   
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4]],				   
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4]],				   
							   3:[multiple_goals[3],multiple_goals[4]],				   
							   4:[multiple_goals[4]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4]],
							   7:[multiple_goals[7],multiple_goals[4]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[15],multiple_goals[4]],
							   9:[multiple_goals[9],multiple_goals[4]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[4]],
							   12:[multiple_goals[12],multiple_goals[4]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
							   15:[multiple_goals[15],multiple_goals[4]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4]],
							}
							
					if(goal_ind==5): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[5]],				   
							   1:[multiple_goals[1],multiple_goals[5]],				   
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[5]],				   
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5]],	   
							   4:[multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],	   
							   5:[multiple_goals[5]],
							   6:[multiple_goals[6],multiple_goals[5]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6],multiple_goals[5]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[5]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[5]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],	   
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[5]],	   
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5]],
							}
					if(goal_ind==6): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[5],multiple_goals[6]],				   
							   1:[multiple_goals[1],multiple_goals[5],multiple_goals[6]],				   
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6]],				   
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6]],	   
							   4:[multiple_goals[4],multiple_goals[7],multiple_goals[6]],	   
							   5:[multiple_goals[5],multiple_goals[6]],
							   6:[multiple_goals[6]],
							   7:[multiple_goals[7],multiple_goals[6]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[6]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[6]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[4],multiple_goals[7],multiple_goals[6]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[6]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[6]],
							   14:[multiple_goals[14],multiple_goals[6]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[6]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[6]],	   
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[6]],	   
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6]],
							}
					if(goal_ind==7): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[7]],				   
							   1:[multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[7]],				   
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[7]],				   
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[7]],	   
							   4:[multiple_goals[4],multiple_goals[7]],	   
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7]],
							   6:[multiple_goals[6],multiple_goals[7]],
							   7:[multiple_goals[7]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6],multiple_goals[7]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[4],multiple_goals[7]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[7]],
							   13:[multiple_goals[13],multiple_goals[7]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[7]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[7]],	   
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[7]],	   
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[7]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[7]],
							}
							
					if(goal_ind==8): 
						print("@@@@@@@@@@")
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8]],				   
							   1:[multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8]],
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8]],
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8]],	   
							   4:[multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[8]],	   
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8]],
							   6:[multiple_goals[6],multiple_goals[14],multiple_goals[8]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[8]],
							   8:[multiple_goals[8]],
							   9:[multiple_goals[9],multiple_goals[8]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[8]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[8]],
							   12:[multiple_goals[12],multiple_goals[11],multiple_goals[9],multiple_goals[8]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[8]],
							   14:[multiple_goals[14],multiple_goals[8]],
							   15:[multiple_goals[15],multiple_goals[9],multiple_goals[8]],
							   16:[multiple_goals[16],multiple_goals[8]],
							   17:[multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[8]],	   
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[8]],	   
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[8]],	   
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[8]],	   
							}	
					if(goal_ind==9): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9]],
							   4:[multiple_goals[4],multiple_goals[15],multiple_goals[9]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9]],
							   6:[multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9]],
							   8:[multiple_goals[8],multiple_goals[9]],
							   9:[multiple_goals[9]],
							   10:[multiple_goals[10],multiple_goals[9]],
							   11:[multiple_goals[11],multiple_goals[9]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[9]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[15],multiple_goals[9]],
							   14:[multiple_goals[14],multiple_goals[8],multiple_goals[9]],
							   15:[multiple_goals[15],multiple_goals[9]],
							   16:[multiple_goals[16],multiple_goals[8],multiple_goals[9]],
							   17:[multiple_goals[17],multiple_goals[11],multiple_goals[9]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[11],multiple_goals[9]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9]],
							}
					if(goal_ind==10): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   4:[multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10]],
							   6:[multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[10]],
							   9:[multiple_goals[9],multiple_goals[10]],
							   10:[multiple_goals[10]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[10]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[9],multiple_goals[10]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   14:[multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10]],
							   15:[multiple_goals[15],multiple_goals[9],multiple_goals[10]],
							   16:[multiple_goals[16],multiple_goals[8],multiple_goals[9],multiple_goals[10]],
							   17:[multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[10]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[11],multiple_goals[9],multiple_goals[10]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9],multiple_goals[10]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9],multiple_goals[10]],
							}
					if(goal_ind==11): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   4:[multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   6:[multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   9:[multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   10:[multiple_goals[10],multiple_goals[11]],
							   11:[multiple_goals[11]],
							   12:[multiple_goals[12],multiple_goals[11]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   14:[multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   15:[multiple_goals[15],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   16:[multiple_goals[16],multiple_goals[8],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   17:[multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[11],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9],multiple_goals[10],multiple_goals[11]],
							}
					
					if(goal_ind==12): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[12]],
							   4:[multiple_goals[4],multiple_goals[12]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[12]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[12]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[12]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[12]],
							   9:[multiple_goals[9],multiple_goals[11],multiple_goals[12]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[11],multiple_goals[12]],
							   11:[multiple_goals[11],multiple_goals[12]],
							   12:[multiple_goals[12]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[12]],
							   14:[multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[12]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[12]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[12]],
							   17:[multiple_goals[17],multiple_goals[12]],
							   18:[multiple_goals[18],multiple_goals[12]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9],multiple_goals[12]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[9],multiple_goals[12]],
							}
					
					if(goal_ind==13): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[13]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[13]],
							   2:[multiple_goals[2],multiple_goals[13]],
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[13]],
							   4:[multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[13]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[13]],
							   7:[multiple_goals[7],multiple_goals[13]],
							   8:[multiple_goals[8],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[13]],
							   9:[multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   11:[multiple_goals[11],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   13:[multiple_goals[13]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[13]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[13]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[12],multiple_goals[13]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[12],multiple_goals[13]],
							}
							
					if(goal_ind==14): 
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14]],
							   1:[multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14]],
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14]],
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14]],
							   4:[multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[14]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[14]],
							   6:[multiple_goals[6],multiple_goals[14]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[14]],
							   8:[multiple_goals[8],multiple_goals[14]],
							   9:[multiple_goals[9],multiple_goals[8],multiple_goals[14]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[8],multiple_goals[14]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[14]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[7],multiple_goals[13]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[6],multiple_goals[14]],
							   14:[multiple_goals[14]],
							   15:[multiple_goals[15],multiple_goals[9],multiple_goals[8],multiple_goals[14]],
							   16:[multiple_goals[16],multiple_goals[14]],
							   17:[multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[14]],
							   18:[multiple_goals[18],multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[14]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[14]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[14]],
							}
					
					if(goal_ind==15):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15]],				   
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[15]],				   
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[15]],	   
							   4:[multiple_goals[4],multiple_goals[15]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[15]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[15]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[15]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[15]],
							   9:[multiple_goals[9],multiple_goals[14]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[15]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[14]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[15]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[15]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4]],
							   15:[multiple_goals[15]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[15]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[15]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[15]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[15]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[15]],
							}
							
					if(goal_ind==16):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   1:[multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   2:[multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   3:[multiple_goals[3],multiple_goals[2],multiple_goals[1],multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   4:[multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   6:[multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   7:[multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   8:[multiple_goals[8],multiple_goals[16]],
							   9:[multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   11:[multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   12:[multiple_goals[12],multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   14:[multiple_goals[14],multiple_goals[16]],
							   15:[multiple_goals[15],multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   16:[multiple_goals[16]],
							   17:[multiple_goals[17],multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[11],multiple_goals[9],multiple_goals[8],multiple_goals[16]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[7],multiple_goals[6],multiple_goals[14],multiple_goals[16]],
							}
					
					if(goal_ind==17):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   4:[multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[13],multiple_goals[17]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[13],multiple_goals[17]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[13],multiple_goals[17]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[17]],
							   9:[multiple_goals[9],multiple_goals[11],multiple_goals[17]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[11],multiple_goals[17]],
							   11:[multiple_goals[11],multiple_goals[17]],
							   12:[multiple_goals[12],multiple_goals[17]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   14:[multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[17]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   16:[multiple_goals[16],multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[17]],
							   17:[multiple_goals[17]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[17]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[17]],
							}	
							
					if(goal_ind==18):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   4:[multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   5:[multiple_goals[5],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   6:[multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[12],multiple_goals[18]],
							   9:[multiple_goals[9],multiple_goals[11],multiple_goals[12],multiple_goals[18]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[11],multiple_goals[12],multiple_goals[18]],
							   11:[multiple_goals[11],multiple_goals[12],multiple_goals[18]],
							   12:[multiple_goals[12],multiple_goals[18]],
							   13:[multiple_goals[13],multiple_goals[7],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   14:[multiple_goals[14],multiple_goals[8],multiple_goals[9],multiple_goals[11],multiple_goals[12],multiple_goals[18]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[18]],
							   18:[multiple_goals[18]],
							   19:[multiple_goals[19],multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							   20:[multiple_goals[20],multiple_goals[3],multiple_goals[4],multiple_goals[12],multiple_goals[18]],
							}	
							
					if(goal_ind==19):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20],multiple_goals[19]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20],multiple_goals[19]],
							   3:[multiple_goals[3],multiple_goals[4],multiple_goals[20],multiple_goals[19]],
							   4:[multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   5:[multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20],multiple_goals[19]],
							   6:[multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20],multiple_goals[19]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   9:[multiple_goals[9],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   11:[multiple_goals[11],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   13:[multiple_goals[13],multiple_goals[2],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20],multiple_goals[19]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20],multiple_goals[19]],
							   19:[multiple_goals[19]],
							   20:[multiple_goals[20],multiple_goals[19]],
							}		
							
					if(goal_ind==20):
						bot_paths={
							   0:[multiple_goals[0],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[20]],
							   1:[multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20]],
							   2:[multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20]],
							   3:[multiple_goals[3],multiple_goals[20]],
							   4:[multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   5:[multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[20]],
							   6:[multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[20]],
							   7:[multiple_goals[7],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   8:[multiple_goals[8],multiple_goals[9],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   9:[multiple_goals[9],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   10:[multiple_goals[10],multiple_goals[9],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   11:[multiple_goals[11],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   12:[multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   13:[multiple_goals[13],multiple_goals[2],multiple_goals[3],multiple_goals[20]],
							   14:[multiple_goals[14],multiple_goals[6],multiple_goals[7],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   15:[multiple_goals[15],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   16:[multiple_goals[16],multiple_goals[14],multiple_goals[6],multiple_goals[5],multiple_goals[1],multiple_goals[2],multiple_goals[3],multiple_goals[4],multiple_goals[20]],
							   17:[multiple_goals[17],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   18:[multiple_goals[18],multiple_goals[12],multiple_goals[4],multiple_goals[3],multiple_goals[20]],
							   19:[multiple_goals[19],multiple_goals[20]],
							   20:[multiple_goals[20]],
							}					
					print("bot_paths",goal_ind,bot_paths)
					YOUR_GOAL_THRESHOLD_DISTANCE=15
					YOUR_THRESHOLD_DISTANCE=15
					current_goal_index = [0] * len(s.swarm)			
					goal_table=[0]*len(s.swarm)
					print("goal_table",goal_table)
					current_table=[0]*len(s.swarm)
					length_arr=[0]*len(s.swarm)
					new_length_arr=[0]*len(s.swarm)
					count=[0]*len(s.swarm)
					step=0
					goal_flag=False
					while 1:	
						if(pop_flag):	
							if(i>=pop_bot_index):
								i+=1	
									
						for i,b in enumerate(s.swarm):							
							if(i==goal_bot_num):	
								step+=1						
								current_position = [b.x,b.y]				
								print("i",i)			
																	
								if(step==1):
									nearest_goal = min(multiple_goals, key=lambda goal: distance.euclidean(current_position, goal))
									print("current_position , nearest_goal",current_position,nearest_goal)
									goal_table[i]=multiple_goals.index(nearest_goal)
									#print("!!!!!!!!!!!current_table!!!!!!!",current_table)
									print("!!!!!!!!!!!goalTable!!!!!!!",goal_table)

								else:							
									print("BOT {} reached",i)
									print("goal_table[goal_index]",goal_table)
									ind=goal_table[i]
									print("ind",ind)
									next_goal=bot_paths[ind]
									print("next_goal",next_goal)
									if(step==2):
										length_arr[i]=len(bot_paths[ind])
									if(count[i]==length_arr[i]):
										specific_bot_goal_flag=True
										break
									#print("length_arr",length_arr)
									#print("new_length_arr",new_length_arr)
									if(len(bot_paths[ind])<1):						
										print("BOT {i} goal reached",i)
										continue
									#print("len(bot_paths[ind]",len(bot_paths[ind]))
									#for i,b in enumerate(s.swarm):
									#current_position=[b.x,b.y]
									goal=bot_paths[goal_table[i]][count[i]]
									print("goal",goal)
									cmd =cvg.goal_area_cvg(i,b,goal)
									dx=abs(goal[0]-current_position[0])
									dy=abs(goal[1]-current_position[1])						
									print("dx,dy",dx,dy)
									if(dx<=3 and dy<=3):									
										print("Goal_reached!!!!!!!!!!!")	
										new_length_arr[i]=length_arr[i]-1
										count[i]+=1											
									
							else:
								print("dispersion")
								cmd = cvg.disp_exp_area_cvg(b)
								#cmd.exec(b) 
								print("cmd exceuted")	
												
							current_position =[b.x*2,b.y*2]
							cmd.exec(b)
							#print("Drone 1 position",b.x,b.y)
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
						       str(robot8_x) + ',' + str(robot8_y))
		
						if(specific_bot_goal_flag):
							specific_bot_goal_flag=False
							break
						if(index==b"search"):
							index="data"
							data="search"		
							potf.reached_goals[goal_bot_num]=True	
							print("Return started")
							continue	       
						area_covered=s.update_grid()				
						sent = sock.sendto(str(msg).encode(), server_address)				
						#gui.update_trajectory_plot()
						#print("!!!!!!!!!!")
						coverage_area = (len(visited_positions) / (s.grid.size)) * 1000
						#print(f"Area covered = {coverage_area:.3f}%")		
						elapsed_time = time.time() - start_time
						gui.show_coverage(area_covered,elapsed_time)
						#gui.show_coverage(area_covered,elapsed_time)				
						#s.update_grid()
						gui.update()
						s.time_elapsed += 1   
				
						gui.update()
						
			
																	
	except:	
		if(index=="return"):
			data="return"
		if(index=="search"):
			data="search"
		else:
			data=index
		gui.update()
				
gui.run()
