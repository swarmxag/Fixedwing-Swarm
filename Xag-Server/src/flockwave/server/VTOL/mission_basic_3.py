#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
© Copyright 2015-2016, 3D Robotics.
mission_basic.py: Example demonstrating basic mission operations including creating, clearing and monitoring missions.

Full documentation is provided at https://dronekit-python.readthedocs.io/en/latest/examples/mission_basic.html
"""
from __future__ import print_function

from dronekit import (
    connect,
    LocationGlobalRelative,
    LocationGlobal,
    Command,
)
import math, csv, os
from pymavlink import mavutil


def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the
    specified `original_location`. The returned Location has the same `alt` value
    as `original_location`.

    The function is useful when you want to move the vehicle around specifying locations relative to
    the current vehicle position.
    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
    For more information see:
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """
    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

    # New position in decimal degrees
    newlat = original_location.lat + (dLat * 180 / math.pi)
    newlon = original_location.lon + (dLon * 180 / math.pi)
    return LocationGlobal(newlat, newlon, original_location.alt)


def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5


def distance_to_current_waypoint(vehicle):
    """
    Gets distance in metres to the current waypoint.
    It returns None for the first waypoint (Home location).
    """
    nextwaypoint = vehicle.commands.next
    if nextwaypoint == 0:
        return None
    missionitem = vehicle.commands[nextwaypoint - 1]  # commands are zero indexed
    lat = missionitem.x
    lon = missionitem.y
    alt = missionitem.z
    targetWaypointLocation = LocationGlobalRelative(lat, lon, alt)
    distancetopoint = get_distance_metres(
        vehicle.location.global_frame, targetWaypointLocation
    )
    return distancetopoint


def download_mission():
    """
    Download the current mission from the vehicle.
    """
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()  # wait until download is complete.


def adds_square_mission(vehicle, i, altitude, alt):
    """
    Adds a takeoff command and four waypoint commands to the current mission.
    The waypoints are positioned to form a square of side length 2*aSize around the specified LocationGlobal (aLocation).

    The function assumes vehicle.commands matches the vehicle mission state
    (you must have called download at least once in the session and after clearing the mission)
    """

    cmds = vehicle.commands
    flag = 0

    current_path = os.getcwd()

    print(" Clear any existing commands")
    cmds.clear()

    print(" Define/add new commands.")
    flag = 0
    prev_lat, prev_lon = 0, 0
    cmds.add(
        Command(
            0,
            0,
            0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_VTOL_TAKEOFF,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            30,
        )
    )
    cmds.add(
        Command(
            0,
            0,
            0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_VTOL_TAKEOFF,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            30,
        )
    )
    with open(
        "C:/Users/mspac/Documents/sundar/vtol_code/mission_basic/Medur/3-drones/forward-drone-"
        + str(i + 1)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            lat = float(row[0])
            lon = float(row[1])
            if not flag:
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        altitude,
                    )
                )
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        altitude,
                    )
                )
            elif flag == 1 or flag == 2:
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        altitude,
                    )
                )
            else:
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        alt,
                    )
                )
            prev_lat = lat
            prev_lon = lon
            flag += 1
    count = 1
    search_waypoints = 0
    with open(
        "C:/Users/mspac/Documents/sundar/vtol_code/mission_basic/Medur/3-drones/search-drone-"
        + str(i + 1)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            search_waypoints += 1
    search_waypoints -= 1
    with open(
        "C:/Users/mspac/Documents/sundar/vtol_code/mission_basic/Medur/3-drones/search-drone-"
        + str(i + 1)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            if count >= search_waypoints:
                lat = float(row[0])
                lon = float(row[1])
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        altitude,
                    )
                )
            else:
                lat = float(row[0])
                lon = float(row[1])
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        alt,
                    )
                )
            prev_lat = lat
            prev_lon = lon
            count += 1
    cmds.add(
        Command(
            0,
            0,
            0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM,
            0,
            0,
            0,
            0,
            0,
            0,
            prev_lat,
            prev_lon,
            altitude,
        )
    )

    flag = 0
    reverse_waypoints = 0
    with open(
        "C:/Users/mspac/Documents/sundar/vtol_code/mission_basic/Medur/3-drones/reverse-drone-"
        + str(i + 1)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            reverse_waypoints += 1
    reverse_waypoints -= 2
    count = 0
    with open(
        "C:/Users/mspac/Documents/sundar/vtol_code/mission_basic/Medur/3-drones/reverse-drone-"
        + str(i + 1)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            print(row)
            if not flag or count >= reverse_waypoints:
                lat = float(row[0])
                lon = float(row[1])
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        altitude,
                    )
                )
                prev_lat = lat
                prev_lon = lon
            else:
                lat = float(row[0])
                lon = float(row[1])
                cmds.add(
                    Command(
                        0,
                        0,
                        0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        lat,
                        lon,
                        alt,
                    )
                )
                prev_lat = lat
                prev_lon = lon
            flag = 1
            count += 1
    cmds.add(
        Command(
            0,
            0,
            0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_LOITER_UNLIM,
            0,
            0,
            0,
            0,
            0,
            0,
            prev_lat,
            prev_lon,
            altitude,
        )
    )

    print("Upload new commands to vehicle")
    cmds.upload()


vehicles = []

vehicle1 = connect("udpin:192.168.0.129:14551", heartbeat_timeout=30)
vehicles.append(vehicle1)
vehicle2 = connect("udpin:192.168.0.129:14552", heartbeat_timeout=30)
vehicles.append(vehicle2)
vehicle3 = connect("udpin:192.168.0.129:14553", heartbeat_timeout=30)
vehicles.append(vehicle3)
vehicle4 = connect("udpin:192.168.0.129:14554", heartbeat_timeout=30)
vehicles.append(vehicle4)
vehicle5 = connect("udpin:192.168.0.129:14555", heartbeat_timeout=30)
vehicles.append(vehicle5)
vehicle6 = connect("udpin:192.168.0.129:14556", heartbeat_timeout=30)
vehicles.append(vehicle6)
vehicle7 = connect("udpin:192.168.0.129:14557", heartbeat_timeout=30)
vehicles.append(vehicle7)
vehicle8 = connect("udpin:192.168.0.129:14558", heartbeat_timeout=30)
vehicles.append(vehicle8)
vehicle9 = connect("udpin:192.168.0.129:14559", heartbeat_timeout=30)
vehicles.append(vehicle9)
# vehicle10 = connect("udpin:192.168.0.129:14560", heartbeat_timeout=30)
# vehicles.append(vehicle10)
# vehicle11 = connect("udpin:192.168.0.129:14558", heartbeat_timeout=30)
# vehicles.append(vehicle11)
# vehicle12 = connect("udpin:192.168.0.129:14560", heartbeat_timeout=30)
# vehicles.append(vehicle12)
# vehicle13 = connect("udpin:192.168.0.129:14568", heartbeat_timeout=30)
# vehicles.append(vehicle13)
# vehicle14 = connect("udpin:192.168.0.129:14559", heartbeat_timeout=30)
# vehicles.append(vehicle14)
# vehicle15 = connect("udpin:192.168.0.129:14560", heartbeat_timeout=30)
# vehicles.append(vehicle15)
# vehicle16 = connect("udpin:192.168.0.129:14558", heartbeat_timeout=30)
# vehicles.append(vehicle16)
# vehicle17 = connect("udpin:192.168.0.129:14560", heartbeat_timeout=30)
# vehicles.append(vehicle17)
# vehicle18 = connect("udpin:192.168.0.129:14568", heartbeat_timeout=30)
# vehicles.append(vehicle18)
# vehicle19 = connect("udpin:192.168.0.129:14559", heartbeat_timeout=30)
# vehicles.append(vehicle19)
# vehicle20 = connect("udpin:192.168.0.129:14560", heartbeat_timeout=30)
# vehicles.append(vehicle20)
print(vehicles)
altitudes = [
    100,
    110,
    120,
    130,
    140,
    150,
    160,
    170,
    180,
    190,
    200,
    210,
    220,
    230,
    240,
    250,
    260,
    270,
    280,
    290,
]
alt = 100

index = 0
for vehicle in vehicles:
    adds_square_mission(vehicle, index, altitudes[index], alt)
    if index % 2 == 0:
        alt += 20
    else:
        alt -= 20
    index += 1
    vehicle.close()
