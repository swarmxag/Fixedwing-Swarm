import os, json, socket, time, csv
from math import radians, cos, sin, sqrt, atan2
from .search import BezierCurve
from .AutoMission import AutoSplitMission
from .SpecificSplitMission import SpecificSplitMission
from .time import TimeCalculation


def fetch_file_content(file_path):
    lines = []
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
            new_lines = file_content.split("\n")

            # Compare new lines with existing lines and append only unique ones
            unique_new_lines = [line for line in new_lines]
            parsed_messages = []
            for line in unique_new_lines:
                if line == "":
                    continue
                time, message = line.split("\t")
                parsed_messages.append({"timestamp": time, "message": message})

            lines.extend(parsed_messages)
    except IOError as error:
        print("Error reading file:", error)
    return lines


master_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

adderss = {1: ("192.168.2.140", 12002), 2: ("192.168.2.140", 12008)}

master_num = 0
origin = None  # set by process_fence() once a fence has been drawn; consumed
               # directly by splitmission()/specificsplit() below, same
               # pattern as the copter server's swarm.py
# udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address1 = ('192.168.6.151', 12008)
# udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address2 = ('192.168.6.152', 12008)
udp_socket3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ("192.168.6.153", 12008)
# udp_socket4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address4 = ('192.168.6.154', 12008)
udp_socket5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address5 = ("192.168.6.155", 12008)
# udp_socket6 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address6 = ('192.168.6.156', 12008)
# udp_socket7 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address7 = ('192.168.6.157', 12008)
# udp_socket8 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address8 = ('192.168.6.158', 12008)
# udp_socket9 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address9 = ('192.168.6.159', 12008)
udp_socket10 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address10 = ("192.168.6.160", 12008)

# share_data_udp_socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# share_data_server_address1 = ('192.168.6.151', 12008)
# share_data_udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# share_data_server_address2 = ('192.168.6.152', 12008)
share_data_udp_socket3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_data_server_address3 = ("192.168.6.153", 12008)
# share_data_udp_socket4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# share_data_server_address4 = ('192.168.6.154', 12008)
share_data_udp_socket5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_data_server_address5 = ("192.168.6.155", 12008)
# udp_socket6 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address6 = ('192.168.6.156', 12008)
# share_data_udp_socket7 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# share_data_server_address7 = ('192.168.6.157', 12008)
# udp_socket8 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address8 = ('192.168.6.158', 12008)
# udp_socket9 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address9 = ('192.168.6.159', 12008)
share_data_udp_socket10 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
share_data_server_address10 = ("192.168.6.160", 12008)

# socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address11 = ('192.168.6.151', 12002)
# socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address12 = ('192.168.6.152', 12002)
socket3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address13 = ("192.168.6.153", 12002)
# socket4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address14 = ('192.168.6.154', 12002)
socket5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address15 = ("192.168.6.155", 12002)
# socket6 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address16 = ('192.168.6.156', 12002)
# socket7 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address17 = ('192.168.6.157', 12002)
# socket8 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address18 = ('192.168.6.158', 12002)
# socket9 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_address19 = ('192.168.6.159', 12002)
socket10 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address20 = ("192.168.6.160", 12002)

# file_sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address1 = ('192.168.6.151', 12003)
# file_sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address2 = ('192.168.6.152', 12003)
file_sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
file_server_address3 = ("192.168.6.153", 12003)
# file_sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address4 = ('192.168.6.154', 12003)
file_sock5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
file_server_address5 = ("192.168.6.155", 12003)
# file_sock6 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address6 = ('192.168.6.156', 12003)
# file_sock7 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address7 = ('192.168.6.157', 12003)
# file_sock8 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address8 = ('192.168.6.158', 12003)
# file_sock9 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file_server_address9 = ('192.168.6.159', 12003)
file_sock10 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
file_server_address10 = ("192.168.6.160", 12003)

"""
mavlink_sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mavlink_server_address1 = ('192.168.6.151', 12045)

mavlink_sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mavlink_server_address2 = ('192.168.6.152', 12045)
"""
mavlink_sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mavlink_server_address3 = ("192.168.6.153", 12045)

# mavlink_sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# mavlink_server_address4 = ('192.168.6.154', 12045)

mavlink_sock5 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mavlink_server_address5 = ("192.168.6.155", 12045)

# mavlink_sock6 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# mavlink_server_address6 = ('192.168.6.156', 12045)

# mavlink_sock7 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# mavlink_server_address7 = ('192.168.6.157', 12045)

# mavlink_sock8 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# mavlink_server_address8 = ('192.168.6.158', 12045)

# mavlink_sock9 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# mavlink_server_address9 = ('192.168.0.159', 12045)

mavlink_sock10 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mavlink_server_address10 = ("192.168.6.160", 12045)

from .YamlCreation import FenceToYAML


def _origin_file_path():
    swarm_folder = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env")
    os.makedirs(swarm_folder, exist_ok=True)
    return os.path.join(swarm_folder, "rectangles.yaml")


server_address_220 = ("192.168.2.140", 12008)

def push_origin_and_geofence(origin1):
    """Broadcast a fresh origin + geofence-refresh signal to all swarm computers,
    same ports/pattern as clear_csv()/start_socket() above."""
    data = "origin,{},{}".format(origin1[0], origin1[1])
    udp_socket3.sendto(data.encode(), server_address3)
    time.sleep(0.1)
    udp_socket5.sendto(data.encode(), server_address5)
    time.sleep(0.1)
    udp_socket10.sendto(data.encode(), server_address10)
    time.sleep(0.1)
    udp_socket3.sendto(data.encode(), server_address_220)
    time.sleep(0.1)

    sync = b"geofence"
    udp_socket3.sendto(sync, server_address3)
    udp_socket5.sendto(sync, server_address5)
    udp_socket10.sendto(sync, server_address10)
    udp_socket3.sendto(sync, server_address_220)
    return True


def get_origin():
    """Getter, not a bare name -- app.py does `from .swarm import *`, which
    would otherwise capture a frozen copy of `origin` at import time instead
    of staying linked to this module's live value. A function call resolves
    it fresh, inside this module's own namespace, every time."""
    return origin


def process_fence(coords, labels):
    """coords/labels: parsed the same way app.py's "fence" handler parses them.
    Writes rectangles.yaml (origin + obstacle walls) and pushes the refresh."""
    global origin
    fence_yaml = FenceToYAML(fence_coordinates=coords, labels=labels)
    fence_yaml.process_fences()
    new_origin, _ = fence_yaml.generate_yaml(_origin_file_path())
    origin = new_origin
    push_origin_and_geofence(origin)
    return origin


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the Earth's surface using the Haversine formula.

    Parameters:
    - lat1, lon1: Latitude and longitude of the first point (in degrees).
    - lat2, lon2: Latitude and longitude of the second point (in degrees).

    Returns:
    - The distance between the two points (in meters).
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371000 * c  # Radius of Earth in meters

    return distance


def calculate_flight_time():
    global flight_time_var, csv_files
    total_distance = 0
    num_uavs = 0

    for uav, csv_path in csv_files.items():
        lat_lon_points = []
        with open(csv_path, "rt") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header (first row)
            for row in csv_reader:
                lat, lon = map(float, row)
                lat_lon_points.append((lat, lon))

        total_distance_uav = 0
        for i in range(len(lat_lon_points) - 1):
            lat1, lon1 = lat_lon_points[i]
            lat2, lon2 = lat_lon_points[i + 1]
            distance = haversine(lat1, lon1, lat2, lon2)
            total_distance_uav += distance

        total_distance += total_distance_uav
        num_uavs += 1

    average_total_distance = total_distance / num_uavs
    average_speed = 3  # Assume average speed between 4 m/s and 5 m/s
    flight_time_seconds = average_total_distance / average_speed
    flight_time_minutes = flight_time_seconds / 60

    flight_time_var.set("Flight Time = {:.2f} minutes".format(flight_time_minutes))


def clear_csv():
    print("!!!CSV Cleared!!")
    global udp_socket, udp_socket2, server_address1, server_address2
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "clear_csv"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """       
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)       
    udp_socket7.sendto(str(data).encode(), server_address7)     
    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def start_socket():
    print("!!!Start!!")
    global udp_socket, udp_socket2, server_address1, server_address2
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "start"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)
    time.sleep(0.5)

    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)

    return True


def start1_socket():
    print("Start1........")
    global udp_socket, server_address1, server_address2, udp_socket2
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "start1"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def home_lock():
    print("Home position Locked....!!!!")
    global udp_socket, server_address1, server_address2, udp_socket2
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "home_lock"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def select_plot(filename):
    if filename != "":

        """
        file_sock1.sendto(str(filename).encode(),file_server_address1)
        time.sleep(0.5)
        file_sock2.sendto(str(filename).encode(),file_server_address2)
        time.sleep(0.5)
        """
        file_sock3.sendto(str(filename).encode(), file_server_address3)
        time.sleep(0.5)
        """
        file_sock4.sendto(str(filename).encode(),file_server_address4)
        time.sleep(0.5)
        """
        file_sock5.sendto(str(filename).encode(), file_server_address5)
        time.sleep(0.5)
        """
        file_sock6.sendto(str(filename).encode(),file_server_address6)
        time.sleep(0.5)

        file_sock7.sendto(str(filename).encode(),file_server_address7)		
        time.sleep(0.5)

        file_sock8.sendto(str(filename).encode(),file_server_address8)
        time.sleep(0.5)
        file_sock9.sendto(str(filename).encode(),file_server_address9)
        time.sleep(0.5)
        """
        file_sock10.sendto(str(filename).encode(), file_server_address10)
        return True


def share_data_func():
    from flockwave.server.socket.globalVariable import (
        get_goal_table,
        get_return_goal_table,
        get_grid_path_table,
    )

    # global goal_table,return_goal_table,filename,udp_socket,server_address1,server_address2,udp_socket2,grid_path_table
    # goal_table=[]
    grid_path_table = get_grid_path_table()
    goal_table = get_goal_table()

    if get_return_goal_table() is not None:
        combined_goal_table = get_goal_table() + get_return_goal_table()
        print("combined_goal_table", combined_goal_table)
        """
        share_data_udp_socket1.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address1)
        time.sleep(0.5)
        share_data_udp_socket2.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address2)
        time.sleep(0.5)
        """
        share_data_udp_socket3.sendto(
            (
                "share_data"
                + ","
                + str(combined_goal_table)
                + ","
                + "grid_path_table"
                + ","
                + str(grid_path_table)
            ).encode(),
            share_data_server_address3,
        )
        time.sleep(0.5)
        """
        share_data_udp_socket4.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address4)
        time.sleep(0.5)
        """
        share_data_udp_socket5.sendto(
            (
                "share_data"
                + ","
                + str(combined_goal_table)
                + ","
                + "grid_path_table"
                + ","
                + str(grid_path_table)
            ).encode(),
            share_data_server_address5,
        )
        time.sleep(0.5)
        """
        share_data_udp_socket6.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address6)
        time.sleep(0.5)

        share_data_udp_socket7.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address7)

        time.sleep(0.5)
        share_data_udp_socket8.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address8)
        time.sleep(0.5)
        share_data_udp_socket9.sendto(("share_data" + "," + str(combined_goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address9)
        time.sleep(0.5)
        """
        share_data_udp_socket10.sendto(
            (
                "share_data"
                + ","
                + str(combined_goal_table)
                + ","
                + "grid_path_table"
                + ","
                + str(grid_path_table)
            ).encode(),
            share_data_server_address10,
        )

    else:

        """
        share_data_udp_socket1.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address1)
        time.sleep(0.5)
        share_data_udp_socket2.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address2)
        time.sleep(0.5)
        """
        share_data_udp_socket3.sendto(
            (
                "share_data"
                + ","
                + str(goal_table)
                + ","
                + "grid_path_table"
                + ","
                + str(grid_path_table)
            ).encode(),
            share_data_server_address3,
        )
        time.sleep(0.5)
        """
        share_data_udp_socket4.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address4)
        time.sleep(0.5)
        """
        share_data_udp_socket5.sendto(
            (
                "share_data"
                + ","
                + str(goal_table)
                + ","
                + "grid_path_table"
                + ","
                + str(grid_path_table)
            ).encode(),
            share_data_server_address5,
        )
        time.sleep(0.5)
        """
        share_data_udp_socket6.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address6)
        time.sleep(0.5)

        share_data_udp_socket7.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address7)

        time.sleep(0.5)
        share_data_udp_socket8.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address8)
        time.sleep(0.5)
        share_data_udp_socket9.sendto(("share_data"+","+ str(goal_table)+","+"grid_path_table" +","+str( grid_path_table)).encode(), share_data_server_address9)
        time.sleep(0.5)
        """
        share_data_udp_socket10.sendto(
            (
                "share_data"
                + ","
                + str(goal_table)
                + ","
                + "grid_path_table"
                + ","
                + str(grid_path_table)
            ).encode(),
            share_data_server_address10,
        )
    return True


def disperse_socket():
    global udp_socket, server_address1, server_address2, udp_socket2
    print("Disperse!!!!!!")
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "disperse"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def takeoff_socket(alt):
    print("Takeoff...........")
    takeoff_alt = alt
    global udp_socket, server_address1, server_address2, udp_socket2
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "takeoff" + "," + str(takeoff_alt)
    """
    sent = udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    sent = udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    sent = udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    sent = udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    sent = udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    sent = udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    sent = udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    sent = udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    sent = udp_socket9.sendto(str(data).encode(), server_address9)

    time.sleep(0.5)
    """
    sent = udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def search_socket(points, gridspacing, coverage, ids):
    global master_udp, origin
    # global udp_socket,server_address1,server_address2,udp_socket2
    ids = ids or []
    print("Searching........")
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for num in points:
        num.reverse()
    data = str(
        "search"
        + ","
        + str(points[0][0])
        + ","
        + str(points[0][1])
        + ","
        + str(len(ids))
        + ","
        + str(gridspacing)
        + ","
        + json.dumps(coverage)
        + ","
        + json.dumps(ids)
    )
    print(points, len(ids), gridspacing, coverage, ids)
    master_udp.sendto(data.encode(), adderss.get(2))
    curve = BezierCurve(
        origin=origin,
        center_latitude=points[0][0],
        center_longitude=points[0][1],
        coverage_area=coverage,
        grid_space=gridspacing,
        num_of_drones=len(ids),
    )
    curve.GridFormation()
    curve.generate_bezier_curve()
    # curve.plot_curve()
    path = curve.return_latlon()
    time_sample = TimeCalculation(
        missions=curve.search_grid, speed=18, loiter_radius=200
    )
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    # udp_socket3.sendto(str(data).encode(), server_address3)
    # time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    # udp_socket5.sendto(str(data).encode(), server_address5)
    #
    # time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)          
    udp_socket7.sendto(str(data).encode(), server_address7) 
    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)    
    time.sleep(0.5)
    """
    # udp_socket10.sendto(str(data).encode(), server_address10)
    return path, time_sample.max_time()


def aggregate_socket():
    print("Aggregation..!!!!")
    data = "aggregate"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """     
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)

    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def home_socket():
    print("Home....******")
    data = "home"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)
    udp_socket7.sendto(str(data).encode(), server_address7)     
    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)      
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def airport_selection(filename):
    print(filename)
    """
    file_sock1.sendto(str(filename).encode(),file_server_address1)
    time.sleep(0.5)
    file_sock2.sendto(str(filename).encode(),file_server_address2)
    time.sleep(0.5)
    """
    file_sock3.sendto(str(filename).encode(), file_server_address3)
    time.sleep(0.5)
    """
    file_sock4.sendto(str(filename).encode(),file_server_address4)
    time.sleep(0.5)
    """
    file_sock5.sendto(str(filename).encode(), file_server_address5)
    time.sleep(0.5)
    """
    file_sock6.sendto(str(filename).encode(),file_server_address6)
    time.sleep(0.5)
    
    file_sock7.sendto(str(filename).encode(),file_server_address7)		
    time.sleep(0.5)
    
    file_sock8.sendto(str(filename).encode(),file_server_address8)
    time.sleep(0.5)
    file_sock9.sendto(str(filename).encode(),file_server_address9)
    time.sleep(0.5)
    """
    file_sock10.sendto(str(filename).encode(), file_server_address10)
    return True


def different_alt_socket(initial_alt, alt_diff, ids=None):
    global master_udp
    ids = ids or []
    data = str(initial_alt) + str(",") + str(alt_diff)
    g = str("different" + "," + str(data) + "," + json.dumps(ids))
    print(g)
    master_udp.sendto(g.encode(), adderss.get(2))
    """
    udp_socket.sendto(str(g).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(g).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(g).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(g).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(g).encode(), server_address5)
    time.sleep(0.5)
    """

    udp_socket6.sendto(str(g).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(g).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(g).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(g).encode(), server_address9)

    time.sleep(0.5)
    """
    udp_socket10.sendto(str(g).encode(), server_address10)
    return True


def same_alt_socket(alt_same):
    print("Same_altitude")
    data = alt_same
    print(data, "data")
    f = "same" + "," + str(data)
    print(f, "f")
    """
    udp_socket.sendto(str(f).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(f).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(f).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(f).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(f).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(f).encode(), server_address6)
    time.sleep(0.5)      
    udp_socket7.sendto(str(f).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(f).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(f).encode(), server_address9)       
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(f).encode(), server_address10)
    return True


def home_goto_socket():
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "home_goto"
    print(data)
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)

    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def rtl_socket():
    global socket, udp_socket, server_address1, server_address2, udp_socket2
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "rtl"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)      
    udp_socket7.sendto(str(data).encode(), server_address7)       
    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)      
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def stop_socket():
    print("STOP>>>>>>>>>>>>")
    global master_udp
    data = "stop"
    master_udp.sendto(data.encode(), adderss.get(1))

    # socket1.sendto(str(data).encode(), server_address11)
    # time.sleep(0.5)
    # socket2.sendto(str(data).encode(), server_address12)
    # time.sleep(0.5)
    #
    # socket3.sendto(str(data).encode(), server_address13)
    # time.sleep(0.5)
    #
    # socket4.sendto(str(data).encode(), server_address14)
    # time.sleep(0.5)
    #
    # socket5.sendto(str(data).encode(), server_address15)
    # time.sleep(0.5)
    #
    # socket6.sendto(str(data).encode(), server_address16)
    # time.sleep(0.5)
    #
    # socket7.sendto(str(data).encode(), server_address17)
    #
    # time.sleep(0.5)
    # socket8.sendto(str(data).encode(), server_address18)
    # time.sleep(0.5)
    # socket9.sendto(str(data).encode(), server_address19)
    # time.sleep(0.5)
    #
    # socket10.sendto(str(data).encode(), server_address20)
    return True


def return_socket():
    global socket, return_flag, udp_socket, server_address1, server_address2, udp_socket2
    # print("&&&&&")
    print("return")
    return_flag = True
    # udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = "return"
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def specific_bot_goal_socket(drone_num, goal_num):
    print("$$$##Specific_bot_goal###")
    d = "specific_bot_goal" + "," + str(drone_num) + "," + str(goal_num)
    print("d", d)
    """
    udp_socket.sendto(str(d).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(d).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(d).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(d).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(d).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(d).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(d).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(d).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(d).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(d).encode(), server_address10)
    return True


def goal_socket(goal_num, direction, radius, ids=None):
    print("***Group goal*****!!!!!")
    ids = ids or []
    for num in goal_num:
        num.reverse()
    data = str(
        "goal"
        + "_"
        + json.dumps(goal_num)
        + "_"
        + str(direction)
        + "_"
        + str(radius)
        + "_"
        + json.dumps(ids)
    )
    print("d", data)
    master_udp.sendto(data.encode(), adderss.get(2))
    # udp_socket.sendto(str(d).encode(), server_address1)
    # time.sleep(0.5)
    # udp_socket2.sendto(str(d).encode(), server_address2)
    # time.sleep(0.5)
    #
    # # udp_socket3.sendto(str(d).encode(), server_address3)
    # # time.sleep(0.5)
    # udp_socket4.sendto(str(d).encode(), server_address4)
    # time.sleep(0.5)
    #
    # udp_socket5.sendto(str(d).encode(), server_address5)
    # time.sleep(0.5)
    #
    # udp_socket6.sendto(str(d).encode(), server_address6)
    # time.sleep(0.5)
    #
    # udp_socket7.sendto(str(d).encode(), server_address7)
    #
    # time.sleep(0.5)
    # udp_socket8.sendto(str(d).encode(), server_address8)
    # time.sleep(0.5)
    # udp_socket9.sendto(str(d).encode(), server_address9)
    # time.sleep(0.5)
    #
    # udp_socket10.sendto(str(d).encode(), server_address10)
    return True


def master(master_num):

    data = "master" + "-" + str(master_num)
    print("data", data)
    """
    socket1.sendto(str(data).encode(), server_address11)
    time.sleep(0.5)
    socket2.sendto(str(data).encode(), server_address12)
    time.sleep(0.5)
    """
    socket3.sendto(str(data).encode(), server_address13)
    time.sleep(0.5)
    """
    socket4.sendto(str(data).encode(), server_address14)
    time.sleep(0.5)
    """
    socket5.sendto(str(data).encode(), server_address15)
    time.sleep(0.5)
    """
    socket6.sendto(str(data).encode(), server_address16)
    time.sleep(0.5)

    socket7.sendto(str(data).encode(), server_address17)

    time.sleep(0.5)
    socket8.sendto(str(data).encode(), server_address18)
    time.sleep(0.5)
    socket9.sendto(str(data).encode(), server_address19)
    time.sleep(0.5)
    """
    socket10.sendto(str(data).encode(), server_address20)
    result = mavlink_add(master_num)
    return result


def mavlink_add(uav):
    global master_udp
    data = str(str("add") + "," + str(uav))
    print(data)
    master_udp.sendto(data.encode(), adderss.get(2))
    """
    mavlink_sock1.sendto((data+port_array[0]).encode(), mavlink_server_address1)
    time.sleep(0.5)
    mavlink_sock2.sendto((data+port_array[1]).encode(), mavlink_server_address2)
    time.sleep(0.5)
   
    mavlink_sock3.sendto((data+port_array[2]).encode(), mavlink_server_address3)
    time.sleep(0.5)
    
    mavlink_sock4.sendto((data+port_array[3]).encode(), mavlink_server_address4)
    time.sleep(0.5)
  
    mavlink_sock5.sendto((data+port_array[4]).encode(), mavlink_server_address5)
    time.sleep(0.5)
   
    mavlink_sock6.sendto((data+port_array[5]).encode(), mavlink_server_address6)
    time.sleep(0.5)

    mavlink_sock7.sendto((data+port_array[6]).encode(), mavlink_server_address7)

    time.sleep(0.5)
    mavlink_sock8.sendto((data+port_array[7]).encode(), mavlink_server_address8)
    time.sleep(0.5)
    mavlink_sock9.sendto((data+port_array[8]).encode(), mavlink_server_address9)
    time.sleep(0.5)
    mavlink_sock10.sendto((data+port_array[9]).encode(), mavlink_server_address10)
    """
    return True


def mavlink_remove(uav):
    global master_udp
    data = str("remove" + "," + str(uav))
    print(data)
    master_udp.sendto(data.encode(), adderss.get(2))
    return True


def bot_remove(remove_uav_num):
    print("!!!bot_remove!!")

    data = "remove_bot" + "," + str(remove_uav_num)
    print("remove_link_num", remove_uav_num)
    """
    udp_socket.sendto(str(data).encode(), server_address1)
    time.sleep(0.5)
    udp_socket2.sendto(str(data).encode(), server_address2)
    time.sleep(0.5)
    """
    udp_socket3.sendto(str(data).encode(), server_address3)
    time.sleep(0.5)
    """
    udp_socket4.sendto(str(data).encode(), server_address4)
    time.sleep(0.5)
    """
    udp_socket5.sendto(str(data).encode(), server_address5)
    time.sleep(0.5)
    """
    udp_socket6.sendto(str(data).encode(), server_address6)
    time.sleep(0.5)

    udp_socket7.sendto(str(data).encode(), server_address7)

    time.sleep(0.5)
    udp_socket8.sendto(str(data).encode(), server_address8)
    time.sleep(0.5)
    udp_socket9.sendto(str(data).encode(), server_address9)
    time.sleep(0.5)
    """
    udp_socket10.sendto(str(data).encode(), server_address10)
    return True


def landing_mission_send(mission):
    for num in mission:
        num.reverse()
    global master_udp
    data = str("home,{}".format(mission))
    master_udp.sendto(data.encode(), adderss.get(2))
    return True


def navigate(center_latlon, gridspacing, coverage, ids):
    global master_udp, origin
    latlng = str(str(center_latlon[0][1]) + "," + str(center_latlon[0][0]))
    data = str(
        "navigate"
        + ","
        + str(latlng)
        + ","
        + str(1)
        + ","
        + str(gridspacing)
        + ","
        + json.dumps(coverage)
    )

    master_udp.sendto(data.encode(), adderss.get(2))
    curve = BezierCurve(
        origin=origin,
        center_latitude=center_latlon[0][1],
        center_longitude=center_latlon[0][0],
        coverage_area=coverage,
        grid_space=gridspacing,
        num_of_drones=1,
    )
    curve.GridFormation()
    curve.generate_bezier_curve()
    path = curve.return_latlon()
    time_sample = TimeCalculation(
        missions=curve.search_grid, speed=18, loiter_radius=200
    )
    return path, time_sample.max_time()


def loiter(center_latlon, direction):
    global master_udp
    s = str(str(center_latlon[0][1]) + "," + str(center_latlon[0][0]))
    data = str("loiter pointer" + "," + str(s) + "," + str(direction))
    print(data)
    master_udp.sendto(data.encode(), adderss.get(2))
    return True


def skip_point(skip_waypoint):
    global master_udp
    data = str("skip" + "," + str(skip_waypoint))
    master_udp.sendto(data.encode(), adderss.get(2))
    return True


def send_alts(alts):
    global master_udp
    data = str("alt" + "," + str(alts))
    print(data, adderss.get(2))
    master_udp.sendto(data.encode(), adderss.get(2))
    return True


def splitmission(center_latlon, uavs, gridspace, coverage):
    global master_udp, origin
    # group_split_center_lat_lon_array_len(uavs)_grid_space_coverage_area
    for latlon in center_latlon:
        latlon.reverse()
        latlon[0] = float(latlon[0])
        latlon[1] = float(latlon[1])
    data = str(
        "split"
        + "_"
        + json.dumps(center_latlon)
        + "_"
        + json.dumps(uavs)
        + "_"
        + json.dumps(gridspace)
        + "_"
        + json.dumps(coverage)
    )
    master_udp.sendto(data.encode(), adderss.get(2))
    split = AutoSplitMission(
        origin=origin,
        center_lat_lons=center_latlon,
        coverage_area=coverage,
        drone_list=uavs,
        grid_spacing=gridspace,
    )
    path = split.return_latlon()
    return path


def specificsplit(center_latlon, uavs, gridspace, coverage):
    global master_udp, origin
    grid = []
    coverageSpace = []
    for i in range(len(uavs)):
        grid.append(gridspace)
        coverageSpace.append(coverage)
    print(center_latlon, uavs, gridspace, coverage)
    split = SpecificSplitMission(
        origin=origin,
        center_lat_lons=center_latlon,
        drone_array=uavs,
        grid_spacing=grid,
        coverage_area=coverageSpace,
    )
    split.GroupSplitting(
        center_lat_lons=center_latlon,
        drone_array=uavs,
        grid_spacing=grid,
        coverage_area=coverageSpace,
    )
    path = split.return_latlon()
    data = str(
        "specificsplit"
        + "_"
        + json.dumps(center_latlon)
        + "_"
        + json.dumps(uavs)
        + "_"
        + json.dumps(grid)
        + "_"
        + json.dumps(coverageSpace)
    )
    master_udp.sendto(data.encode(), adderss.get(2))
    # split.waypoints/path store (lon, lat) pairs; TimeCalculation's haversine
    # call expects (lat, lon), so swap before estimating flight time.
    missions = [[(lat, lon) for lon, lat in segment] for segment in path]
    time_sample = TimeCalculation(missions=missions, speed=20, loiter_radius=200)
    return path, time_sample.max_time()
