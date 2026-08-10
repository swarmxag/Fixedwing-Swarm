import socket
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import time
from matplotlib import pyplot as plt
from shapely.geometry.polygon import Polygon
from descartes import PolygonPatch
import matplotlib as mpl

import sys, yaml, os
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('', 12009)  # receive from .....rx.py
sock.bind(server_address)
sock.setblocking(0)

import time

obstacles = []
def load_yaml(filename):
	f = open(filename)
	dict_=yaml.safe_load(f)	
	size = (dict_['size']['x'], dict_['size']['y'])
	
	if dict_['obstacles']!=None:
		obstacle_list = dict_['obstacles']
		for o in obstacle_list:
			obstacles.append(Polygon(o))

	name = dict_['name']

	print("Loaded world: "+name)
	#print(obstacles)
	return size, obstacles
		
		
#uav_positions = {'uav_1': [], 'uav_2': [], 'uav_3': [], 'uav_4': [], 'uav_5': [], 'uav_6':[], 'uav_7':[], 'uav_8':[], 'uav_9':[], 'uav_10':[], 'uav_11':[], 'uav_12':[],'uav_13':[],'uav_14':[],'uav_15':[],'uav_16':[] }
uav_positions = {'uav_1': [], 'uav_2': [], 'uav_3': [], 'uav_4': [], 'uav_5': [], 'uav_6':[], 'uav_7':[], 'uav_8':[]}
start_time = time.time()
elapsed_time = 0

uav_colors = {
    'uav_1': 'b',
    'uav_2': 'g',
    'uav_3': 'r',
    'uav_4': 'c',
    'uav_5': 'm',
    'uav_6': 'y',
    'uav_7': 'purple',
    'uav_8': 'orange',
    
}



uav_trajectories = {} 
fig, ax = plt.subplots(figsize=(10, 10))
#plt.grid(True)
plt.ion()
print(mpl.is_interactive())
load_yaml(filename="rectangles1.yaml")


#plt.show()  
try:
    #fig=plt.figure(figsize=(10, 30))
    '''
    fig, ax = plt.subplots(figsize=(10,10))
    plt.grid(True)
    poly = Polygon([(0, 0), (0, 2), (1, 1),
    (2, 2), (2, 0), (1, 0.8), (0, 0)])
    x,y = poly.exterior.xy

    ax.fill(x,y, fc='gray', alpha=0.9)
    plt.draw()
    '''
    while True:
        try:
            data, address = sock.recvfrom(1024)
        except BlockingIOError:
            # No data available, continue with the next iteration
            continue

        
        a = data.decode('utf8').split(',')
        a = [value.strip('{}') for value in a]  # Remove curly braces

	
        for uav in uav_positions:
            uav_positions[uav].append((float(a.pop(0)), float(a.pop(0))))

            # Update the UAV's trajectory
            if uav not in uav_trajectories:
                uav_trajectories[uav] = {
                    'x': [],
                    'y': [],
                    'color': uav_colors[uav]
                }
            uav_trajectories[uav]['x'].append(uav_positions[uav][-1][0])
            uav_trajectories[uav]['y'].append(uav_positions[uav][-1][1])

        elapsed_time += 1
       
        if elapsed_time % 5 == 0:
            # Plotting at 5-second intervals
            plt.clf()  # Clear the previous plot
            for uav, positions in uav_trajectories.items():
                x, y, color = positions['x'], positions['y'], positions['color']
                plt.plot(x, y, linestyle='-', color=color, alpha=0.5)
                plt.plot(x[-1], y[-1], marker='o', label=uav, color=color)

                # Print coordinates
             #   print(f"{uav} Coordinates: ({x[-1]}, {y[-1]})")

            #print(f"Elapsed Time: {elapsed_time} seconds")
            #print()
            for obs in obstacles:
            	x,y = obs.exterior.xy
            	plt.fill(x,y, fc='gray', alpha=0.9)

	    #plt.draw()
            plt.title('UAV Positions')
            #plt.text(x[-1], y[-1],f"Elapsed Time: {elapsed_time} seconds", ha='right', va='top')
            plt.xlabel('X-axis')
            plt.ylabel('Y-axis')
            plt.legend()

            plt.xlim(0, 320)
            plt.ylim(0, 400)
            plt.pause(0.05)
    plt.show()
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
	
    sock.close()
