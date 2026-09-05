#!/usr/local/bin/python
#shell script not need
import time, threading
import signal
import subprocess
from math import sin, cos, sqrt, atan2, radians
from dronekit import connect, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
from math import sqrt, pow
import time
import argparse
import sys
import pickle
from multiprocessing import Queue, Process, Value
import socket
import os
import math
import copy
import serial
import pid

import socket, struct

R = 6373.0

# Global Variables and Flags
vehicle = None
ignore_target = True
tangential_speed = 50 # cm/s
#circle_period = sys.maxint
home_location = None
last_centering_time = 0



#gps_coordinates = Queue()
shell_commands = Queue()
last_image_location = Queue(maxsize=1)


camera_width=1920
camera_height=1080
camera_vfov=33.9234               #51.9784
camera_hfov=56.07          #72.5845

dist_to_vel=0.15	  ##0.15 m/s  ###

descent_radius=2   #in m/s
last_set_velocity = 0
vel_update_rate=0.1     ##sec
descent_rate=0.5      #0.5

vel_speed_min = 1
vel_speed_max = 20  #default 4  .........change this parameter to adjust decent speed

vel_accel =  0.5   # 0.5 - maximum acceleration in m/s/s



# Simulator flag
SIM = False

#ser = serial.Serial('/dev/ttyUSB0', 9600)

update_rate = 0.01 # 100 hertz update rate
rcCMD = [1500,1500,1500,1000,1000,1000,1000,1000]

#....uav...inital pos.....
lat1 = 0.0
lon1 = 0.0

#..strike..target.....pos
lat2 = 0.0
lon2 = 0.0

radius_of_earth = 6378100.0 # in meters



dat = 0  #..vel_speed_last


# horizontal velocity pid controller.  maximum effect is 10 degree lean
xy_p = 1.0
xy_i = 0.0
xy_d = 0.0
xy_imax = 10.0
vel_xy_pid = pid.pid(xy_p, xy_i, xy_d, math.radians(xy_imax))


def condition_yaw(heading, relative=False):
    global vehicle

    if relative:
        is_relative=1 #yaw relative to direction of travel
    else:
        is_relative=0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)



def shift_to_origin(pt,width,height):
        print ("pt", pt)
        print ("width", width)
        print ("height", height)       
        return ((pt[0] - width/2.0),(-1*pt[1] + height/2.0))


def pixel_point_to_position_xy(pixel_position,distance):
		thetaX = pixel_position[0] * camera_hfov / camera_width
		print ("thetaX", thetaX)

		thetaY = pixel_position[1] * camera_vfov / camera_height
		print ("thetaY", thetaY)
		x = distance * math.tan(math.radians(thetaX))
		y = distance * math.tan(math.radians(thetaY))
		print ("x,y", (x,y))
		return (x,y)


def set_velocity(velocity_x, velocity_y, velocity_z,yaw):
        #only let commands through at 10hz
        if(time.time() - 0) > vel_update_rate:
            last_set_velocity = time.time()
            # create the SET_POSITION_TARGET_LOCAL_NED command
            print("mavutil.mavlink.MAV_FRAME_LOCAL_NED",mavutil.mavlink.MAV_FRAME_LOCAL_NED)
            msg = vehicle.message_factory.set_position_target_local_ned_encode(
                                                         0,       # time_boot_ms (not used)
                                                         0, 0,    # target system, target component
                                                         mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
                                                         0x01C7,  # type_mask (ignore pos | ignore acc)
                                                         0, 0, 0, # x, y, z positions (not used)
                                                         velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
                                                         0, 0, 0, # x, y, z acceleration (not used)
                                                         yaw, 0)    # yaw, yaw_rate (not used)
            # send command to vehicle
            vehicle.send_mavlink(msg)
            vehicle.flush()

def get_ef_velocity_vector(pitch, yaw, speed):
	cos_pitch = math.cos(pitch)
	x = speed * math.cos(yaw) * cos_pitch
	y = speed * math.sin(yaw) * cos_pitch
	z = speed * math.sin(pitch)
	return x,y,z

def gps_distance(lat1, lon1, lat2, lon2):
    #print("GGGGGGGGGGG")
    '''return distance between two points in meters,
    coordinates are in degrees
    thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
    from math import radians, cos, sin, sqrt, atan2
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1
    a = sin(0.5*dLat)**2 + sin(0.5*dLon)**2 * cos(lat1) * cos(lat2)
    c = 2.0 * atan2(sqrt(a), sqrt(1.0-a))
    return radius_of_earth * c


def gps_bearing(lat1, lon1, lat2, lon2):

    '''return bearing between two points in degrees, in range 0-360
    thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
    from math import sin, cos, atan2, radians, degrees
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1    
    y = sin(dLon) * cos(lat2)
    x = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dLon)
    bearing = degrees(atan2(y, x))
    if bearing < 0:
        bearing += 360.0
    return bearing


def condition_yaw(heading, relative=False):
    """
    Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).
    This method sets an absolute heading by default, but you can set the `relative` parameter
    to `True` to set yaw relative to the current yaw heading.
    """
    if relative:
        is_relative = 1 #yaw relative to direction of travel
    else:
        is_relative = 0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)



def move_to_target(c_lat1,c_lon1,g_lat2,g_lon2,alt):
		print("!!!!!!!!!!!!")
		#lat1 = vehicle.location.global_frame.lat
		#lon1 = vehicle.location.global_frame.lon
		global lat1,lon1,lat2,lon2, dat
		lat1=c_lat1
		lon1=c_lon1
		lat2=g_lat2
		lon2=g_lon2
		print ("lat1, lon1, lat2, lon2", lat1, lon1, lat2, lon2)
		print ("....dat..", dat)
		Tdist = gps_distance(lat1, lon1, lat2, lon2)
		print ("...Tdist..", Tdist)
		Tbearing = gps_bearing(lat1, lon1, lat2, lon2)
		#alt = vehicle.location.global_relative_frame.alt
		print ("....alt...", alt)
		print ("...Tbearing", Tbearing)		
			
		pitch_angle = math.degrees(math.atan(Tdist/alt))
		pitch_angle = abs(90-int(pitch_angle))
		print ("pitch_angle...", pitch_angle)

		#send velocity commands toward target heading
		pitch_angle, yaw_angle = int(pitch_angle), int(Tbearing)

		pitch_final = math.radians(pitch_angle)
		yaw_final = math.radians(yaw_angle)
		print ("pitch_final,yaw_final", pitch_final, yaw_final)
		speed = (Tdist * dist_to_vel)

		print (".........speed..", speed)

		dt = vel_xy_pid.get_dt(2.0)
		print ("......dt....", dt)

		# apply min and max speed limit
		speed = min(speed, vel_speed_max)
		speed = max(speed, vel_speed_min)

		print (".........qw...", speed)

		

		# apply acceleration limit
		speed_chg_max = vel_accel * dt

		
		speed = min(speed, dat + speed_chg_max)
		speed = max(speed, dat - speed_chg_max)

		print ("....123.....qw...", speed)

		# record speed for next iteration
		dat = speed

		#guided_target_vel = get_ef_velocity_vector(pitch_final, yaw_final, speed)
		guided_target_vel = get_ef_velocity_vector(pitch_final, yaw_final, speed)
		print ("...????????????.", guided_target_vel,yaw_final)
		return(guided_target_vel,yaw_final)
		#set_velocity(guided_target_vel[0], guided_target_vel[1], guided_target_vel[2],yaw_final)
		

def geo_loop(latitude, longitude, altitude):
    global vehicle
    lat = vehicle.location.global_relative_frame.lat
    lon = vehicle.location.global_relative_frame.lon
    alt = vehicle.location.global_relative_frame.alt
    alt = abs(alt)
    print ("Navigating to point")
    #vehicle.mode = VehicleMode("GUIDED")
    target = LocationGlobalRelative(latitude, longitude, 0)
    print (target)
    #timeout = 20
    #min_distance = 0.000005 # Parameter to tune by experimenting
    min_distance = 200 # Parameter to tune by experimentin
    #vehicle.simple_goto(target, groundspeed=speed)
    start = time.time()
    print (start)    
    while True:
        #print vehicle.mode.name
        current = time.time() - start
        #print current
        #print vehicle.location.global_frame.lat
        print ("target.lat, target.lon", (target.lat, target.lon))
        print ("vehicle.lat, vehicle.lon", (vehicle.location.global_frame.lat, vehicle.location.global_frame.lon))
        lat1 = radians(vehicle.location.global_frame.lat)
        lon1 = radians(vehicle.location.global_frame.lon)
        lat2 = radians(target.lat)
        lon2 = radians(target.lon)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        distance = (distance * 1000)
        print("Result:", distance)
        output = ("dist b/w vehicle to geo_search and vehicle lat & lon:", (distance, lat, lon))
        output = str(output)
        ##ser.write(output+ '\r\n')
        if distance<=min_distance:
            print ("Reached target location")
            break;
        time.sleep(0.5)


 
def main():

        print ("Set default/target airspeed to 18")
        vehicle.airspeed = 18
        time.sleep(1)
        
        """
	cmds = vehicle.commands
	cmds.download()
	cmds.wait_ready()
	home_lat = vehicle.home_location.lat
	home_lon = vehicle.home_location.lon
	print "home_lat", home_lat
	print "home_lon", home_lon
        """
        print ("vehicle mode", vehicle.mode)
        #subprocess.Popen("python /home/dhaksha/Target_video/TargetGpsVideo/Target_GPS.py", shell=True)

	##geo_loop(12.947050, 80.136863, 0)  ###input lat/lon
        print ("Set default/target airspeed to 3")


        ###subprocess.Popen("python /home/dhaksha/Target_video/TargetGpsVideo/Target_GPS.py", shell=True)

        count = 0
        count01 = 0
        count03 = 0
        timeout = 20
	#Tbearing = gps_bearing(lat1, lon1, lat2, lon2)
	#condition_yaw(Tbearing)
	#time.sleep(2)
	#vehicle.simple_goto(target, groundspeed=speed)
	#vehicle.groundspeed = 14
        time.sleep(1)
        
        while True:
        	move_to_target()
		
						    		            
if __name__ == '__main__':
    print ("==Inicio==")
    main()

