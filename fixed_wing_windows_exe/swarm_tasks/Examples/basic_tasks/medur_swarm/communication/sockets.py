"""UDP command/telemetry sockets, the two background listener threads that
read them, and the command mailbox the main dispatch loop drains.

Importing this module has the same side effects the top of the original
single-file script had: it binds sock2/sock3 and starts both listener
threads immediately (daemon threads, so they never block process exit).
main.py imports this module early, in the same relative position the
original script created these sockets/threads, to preserve that ordering.
"""

import json
import os
import socket
import threading

from swarm_tasks.simulation import simulation as sim

from medur_swarm import config, state
from medur_swarm.uav import connection as uav_connection

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = ("", 12008)  # receive from .....rx.py
sock2.bind(server_address2)

sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address3 = ("", 12002)  # receive from .....rx.py
sock3.bind(server_address3)


def CHECK_network_connection():
    for i, iter_follower in enumerate(state.heartbeat_ip_timeout):
        response = os.system("ping -c 1 " + config.HEARTBEAT_IP[i])
        if response == 0:
            state.heartbeat_ip_timeout[i] = 30
            pass
        else:  # Link is down.
            print("link is down")
            linkdown_flag = True
            # master_ip="192.168.0.153"
            # slave_heal_ip[i] = 'nolink'
            state.heartbeat_ip_timeout[i] = 1
    print(" heartbeat_ip_timeout", state.heartbeat_ip_timeout)


def vehicle_collision_moniter_receive():
    while 1:
        raw_index, address = sock3.recvfrom(1024)
        print("msg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", raw_index)
        decoded_index = raw_index.decode("utf-8")
        print("decoded_index", decoded_index)
        state.index = raw_index
        if decoded_index.startswith("master"):
            m, master_num = decoded_index.split("-")
            state.master_num = master_num
            print("m,master_num", m, master_num)
            msg = "Drone 3 master_num " + str(master_num) + " data received"
            if int(master_num) == 3:
                if state.master_flag:
                    pass
                else:
                    state.master_flag = True
                    CHECK_network_connection()
                    uav_connection.vehicle_connection()
                    uav_connection.fetch_location()
                    state.s = sim.Simulation(
                        state.uav_home_pos,
                        num_bots=len(state.vehicles),
                        env_name=state.file_name,
                    )
            else:
                state.master_flag = False

            state.index = "data"
            data = "data"
            msg = "master_num " + str(state.master_num)
            print("master_flag", state.master_flag)

        if decoded_index.startswith("pos_array"):
            message = decoded_index[:9]  # Assuming "home_pos" is 8 characters long
            array_data = decoded_index[9:]
            print("pos_array", state.pos_array)
            state.pos_array = json.loads(array_data)
            print("pos_array", state.pos_array)
            state.index = "data"
            msg = "UAV 1 connected with " + str(len(state.pos_array)) + " vehicles"
            print("master_flag", state.master_flag)
        if decoded_index.startswith("home_pos"):
            message = decoded_index[:8]  # Assuming "home_pos" is 8 characters long
            home_pos = decoded_index[8:]
            print("home_pos", home_pos)
            state.home_pos = json.loads(home_pos)
            print("home_pos", state.home_pos)

        if decoded_index.startswith("uav_home_pos"):
            if state.master_flag:
                pass
            else:
                message = decoded_index[:12]  # Assuming "home_pos" is 8 characters long
                uav_home_pos = decoded_index[12:]
                print("uav_home_pos", uav_home_pos)
                state.uav_home_pos = json.loads(uav_home_pos)
                print("uav_home_pos", state.uav_home_pos)
        if decoded_index.startswith("skip_wp"):
            print("decoded_index", decoded_index)
            c, next_wp = decoded_index.split(",")
            print("c,next_wp", c, next_wp)
            state.next_wp = int(next_wp)
            print("next_wp", state.next_wp)
            state.skip_wp_flag = True
            print("skip_wp_flag", state.skip_wp_flag)


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


pending_command = _CommandMailbox()


def _command_listener():
    while 1:
        data, address = sock2.recvfrom(1050)
        pending_command.data = data
        pending_command.address = address
        pending_command.seq += 1


def start_listener_threads():
    """Starts the collision-monitor and command-listener background
    threads. Split out from module import so main.py controls exactly
    when they start, matching the original script's top-to-bottom order
    (both threads are started right after this module's sockets are bound,
    before vehicle_connection()/fetch_location() are ever called -- those
    names are only looked up when a "master" message actually arrives, by
    which point the whole program has finished importing)."""
    collision_thread = threading.Thread(target=vehicle_collision_moniter_receive)
    collision_thread.daemon = True
    collision_thread.start()

    command_listener_thread = threading.Thread(target=_command_listener)
    command_listener_thread.daemon = True
    command_listener_thread.start()
