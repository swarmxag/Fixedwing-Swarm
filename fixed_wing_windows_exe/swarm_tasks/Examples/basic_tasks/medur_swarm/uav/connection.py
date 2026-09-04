"""Vehicle connection/discovery: which network interface to dial out from,
opening the dronekit links for the fleet, and refreshing each vehicle's
GPS-derived home position."""

import netifaces
import wmi
from dronekit import connect

import locatePosition

from medur_swarm import config, state


def get_wifi_ip(iface_map):
    interfaces = netifaces.interfaces()
    # print(interfaces)
    for iface in netifaces.interfaces():
        try:
            # print(iface,iface_map[iface])
            # if iface in iface_map:
            adapter = iface_map[iface]
            # print(adapter)
            addrs = netifaces.ifaddresses(iface)
            # print(addrs)
            ipv4_info = addrs.get(netifaces.AF_INET, [])
            for addr in ipv4_info:
                ip = addr.get("addr")
                if (
                    ip
                    and (
                        adapter == "Ethernet"
                        or adapter == "Wi-Fi"
                        or iface == "eth0"
                        or iface == "ensp20"
                        or iface == "wlan0"
                    )
                    and ip.startswith("192.168.")
                ):
                    return "192.168.2.117"
        except Exception as e:
            print(f"Error on interface {iface}: {e}")
    return None


def get_interface_mapping():
    c = wmi.WMI()
    # print(c.Win32_NetworkAdapter()[1])
    mappings = {}
    for nic in c.Win32_NetworkAdapter():
        # print(nic)
        if nic.GUID:
            mappings[nic.GUID.upper()] = nic.NetConnectionID or nic.Name
            # return get_wifi_ip(mappings)
    return "127.0.0.1"


# Computed once, at import time, exactly like the original script's
# module-level `ip = get_interface_mapping()` -- never reassigned again.
state.ip = get_interface_mapping()
print("ip", state.ip)


def connection_string_for_sysid(sys_id):
    if int(sys_id) not in config.PORT_DICT:
        raise KeyError(f"SYS_ID {sys_id} not found in port_dict")
    return f"udpin:{state.ip}:{config.PORT_DICT[int(sys_id)]}"


def vehicle_connection():
    state.pos_array = []
    state.vehicles = []
    state.num_bots = 0

    try:
        vehicle1 = connect(
            "udpin:{}:14551".format(state.ip),
            baud=115200,
            heartbeat_timeout=state.heartbeat_ip_timeout[0],
        )
        print("Drone1")
        state.vehicles.append(vehicle1)
        state.pos_array.append(vehicle1._master.target_system)
        state.num_bots += 1
        msg = "Drone1 Connected"
    except:
        pass
        print("Vehicle 1 is lost")
    try:
        vehicle2 = connect(
            "udpin:{}:14552".format(state.ip),
            baud=115200,
            heartbeat_timeout=state.heartbeat_ip_timeout[1],
        )
        print("Drone2")
        state.num_bots += 1
        state.vehicles.append(vehicle2)
        state.pos_array.append(vehicle2._master.target_system)
        msg = "Drone2 Connected"
    except:
        pass
        print("Vehicle 2 is lost")

    try:
        vehicle3 = connect(
            "udpin:{}:14553".format(state.ip),
            baud=115200,
            heartbeat_timeout=state.heartbeat_ip_timeout[2],
        )
        print("Drone3")
        state.num_bots += 1
        state.vehicles.append(vehicle3)
        state.pos_array.append(vehicle3._master.target_system)
        msg = "Drone3 Connected"
    except:
        pass
        print("Vehicle 3 is lost")

    try:
        vehicle4 = connect(
            "udpin:{}:14554".format(state.ip),
            baud=115200,
            heartbeat_timeout=state.heartbeat_ip_timeout[3],
        )
        print("Drone4")
        state.num_bots += 1
        state.vehicles.append(vehicle4)
        state.pos_array.append(vehicle4._master.target_system)
        msg = "Drone4 Connected"
    except:
        pass
        print("Vehicle 4 is lost")
    try:
        vehicle5 = connect(
            "udpin:{}:14555".format(state.ip),
            baud=115200,
            heartbeat_timeout=state.heartbeat_ip_timeout[4],
        )
        print("Drone5")
        state.num_bots += 1
        state.vehicles.append(vehicle5)
        state.pos_array.append(vehicle5._master.target_system)
        msg = "Drone5 Connected"
    except:
        pass
        print("Vehicle 5 is lost")

    # try:
    #     vehicle6 = connect(
    #         "udpin:{}:14556".format(state.ip),
    #         baud=115200,
    #         heartbeat_timeout=state.heartbeat_ip_timeout[5],
    #     )
    #     print("Drone6")
    #     state.num_bots += 1
    #     state.vehicles.append(vehicle6)
    #     state.pos_array.append(vehicle6._master.target_system)
    #     msg = "Drone6 Connected"
    # except:
    #     pass
    #     print("Vehicle 6 is lost")

    # try:
    #     vehicle7 = connect(
    #         "udpin:{}:14557".format(state.ip),
    #         baud=115200,
    #         heartbeat_timeout=state.heartbeat_ip_timeout[6],
    #     )
    #     print("Drone7")
    #     state.num_bots += 1
    #     state.vehicles.append(vehicle7)
    #     state.pos_array.append(vehicle7._master.target_system)
    #     msg = "Drone7 Connected"
    # except:
    #     pass
    #     print("Vehicle 7 is lost")

    # try:
    #     vehicle8 = connect(
    #         "udpin:{}:14558".format(state.ip),
    #         baud=115200,
    #         heartbeat_timeout=state.heartbeat_ip_timeout[7],
    #     )
    #     print("Drone8")
    #     state.num_bots += 1
    #     state.vehicles.append(vehicle8)
    #     state.pos_array.append(vehicle8._master.target_system)
    #     msg = "Drone8 Connected"
    # except:
    #     pass
    #     print("Vehicle 8 is lost")

    # try:
    #     vehicle9 = connect(
    #         "udpin:{}:14559".format(state.ip),
    #         baud=115200,
    #         heartbeat_timeout=state.heartbeat_ip_timeout[8],
    #     )
    #     print("Drone9")
    #     state.num_bots += 1
    #     state.vehicles.append(vehicle9)
    #     state.pos_array.append(vehicle9._master.target_system)
    #     msg = "Drone9 Connected"
    # except:
    #     pass
    #     print("Vehicle 9 is lost")

    # try:
    #     vehicle10 = connect(
    #         "udpin:{}:14560".format(state.ip),
    #         baud=115200,
    #         heartbeat_timeout=state.heartbeat_ip_timeout[9],
    #     )
    #     print("Drone10")
    #     state.num_bots += 1
    #     state.vehicles.append(vehicle10)
    #     state.pos_array.append(vehicle10._master.target_system)
    #     msg = "Drone10 Connected"
    # except:
    #     pass
    #     print("Vehicle 10 is lost")

    # print(len(state.vehicles))


def fetch_location():
    state.uav_home_pos = []
    current_lat_lon = []

    if state.master_flag:
        for i, vehicle in enumerate(state.vehicles):
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            # print(f"Vehicle - Latitude: {lat}, Longitude: {lon}")
            current_lat_lon.append((lat, lon))
            x, y = locatePosition.geoToCart(
                state.origin, config.END_DISTANCE, [lat, lon]
            )
            # print("x,y",x/2,y/2)
            state.uav_home_pos.append((x / 2, y / 2))
            if i < len(state.robots):
                state.robots[i] = (x / 2, y / 2)
            msg = ",".join([f"{robot[0]},{robot[1]}" for robot in state.robots])
