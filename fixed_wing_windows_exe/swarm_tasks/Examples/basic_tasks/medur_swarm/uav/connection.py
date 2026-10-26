"""Vehicle connection/discovery: which network interface to dial out from,
opening the dronekit links for the fleet, and refreshing each vehicle's
GPS-derived home position."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait

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
                    return "192.168.6.117"
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

# Guards against two connection cycles overlapping (startup and a master
# handover in sockets.py both call vehicle_connection()).
_connection_lock = threading.Lock()


def connection_string_for_sysid(sys_id):
    if int(sys_id) not in config.PORT_DICT:
        raise KeyError(f"SYS_ID {sys_id} not found in port_dict")
    return f"udpin:{state.ip}:{config.PORT_DICT[int(sys_id)]}"


def _close_quietly(vehicle):
    try:
        vehicle.close()
    except Exception as e:
        print(f"[connect] error closing vehicle: {e!r}")


def _connect_one(slot, sys_id, port, heartbeat_timeout):
    """Worker: ONE connection attempt. Touches no shared state -- it only
    returns its result, tagged with its slot, for vehicle_connection() to
    place. On a heartbeat timeout dronekit closes its own socket before
    raising, so a failed attempt leaves nothing open behind it."""
    endpoint = "udpin:{}:{}".format(state.ip, port)
    print(f"[connect] slot={slot} sys_id={sys_id} {endpoint} attempt started")
    started = time.monotonic()
    try:
        vehicle = connect(endpoint, baud=115200, heartbeat_timeout=heartbeat_timeout)
    except Exception as e:
        return slot, sys_id, endpoint, None, e, time.monotonic() - started
    return slot, sys_id, endpoint, vehicle, None, time.monotonic() - started


def _close_late_arrival(future):
    """A connect that finishes after the deadline is not part of this cycle:
    close it so its port is free and it never runs as an untracked vehicle."""
    try:
        slot, sys_id, endpoint, vehicle, _error, _elapsed = future.result()
    except Exception:
        return
    if vehicle is not None:
        print(
            f"[connect] slot={slot} sys_id={sys_id} {endpoint} connected AFTER "
            f"the deadline -- closing it, it is not in this cycle"
        )
        _close_quietly(vehicle)


def vehicle_connection():
    """Connect every endpoint in config.PORT_DICT in PARALLEL.

    Ordering contract (unchanged from the sequential version): state.vehicles
    and state.pos_array are compact, index-aligned lists of the CONNECTED
    drones in ascending sys_id (PORT_DICT) order -- never in the order the
    attempts happen to finish. GCS selection maps sys_id -> index through
    pos_array (utils.selected_swarm_indexes), so the same physical aircraft is
    selected and commanded exactly as before.
    """
    if not _connection_lock.acquire(blocking=False):
        print(
            "[connect] a connection cycle is already running -- ignoring this request"
        )
        return
    try:
        _run_connection_cycle()
    finally:
        _connection_lock.release()


def _run_connection_cycle():
    # Close the previous cycle's links first: they hold the very UDP ports
    # about to be re-bound, and must not linger as stale, untracked vehicles.
    for old in state.vehicles:
        _close_quietly(old)

    state.pos_array = []
    state.vehicles = []
    state.num_bots = 0

    endpoints = sorted(config.PORT_DICT.items())  # slot i <-> i-th sys_id
    workers = config.CONNECT_MAX_WORKERS or len(endpoints)
    timeouts = [
        state.heartbeat_ip_timeout[i] if i < len(state.heartbeat_ip_timeout) else 30
        for i in range(len(endpoints))
    ]
    # dronekit's heartbeat wait is bounded, but its "wait until board has
    # booted" loop is not -- so one aircraft stuck booting cannot hold every
    # other one hostage, the whole cycle is capped.
    deadline_s = max(timeouts, default=0) + config.CONNECT_DEADLINE_GRACE_S

    print(
        f"[connect] connecting {len(endpoints)} endpoints in parallel "
        f"(workers={workers}, deadline={deadline_s:.0f}s)"
    )
    cycle_started = time.monotonic()
    results = [None] * len(endpoints)  # filled BY SLOT, never by finish order

    executor = ThreadPoolExecutor(max_workers=workers)
    futures = [
        executor.submit(_connect_one, slot, sys_id, port, timeouts[slot])
        for slot, (sys_id, port) in enumerate(endpoints)
    ]
    done, not_done = wait(futures, timeout=deadline_s)
    for future in not_done:
        # cancel() only stops attempts still queued (CONNECT_MAX_WORKERS <
        # endpoints); running ones get closed if they connect late. Done by hand
        # because shutdown(cancel_futures=True) needs Python 3.9+.
        if not future.cancel():
            future.add_done_callback(_close_late_arrival)
    executor.shutdown(wait=False)

    for future in done:
        slot, sys_id, endpoint, vehicle, error, elapsed = future.result()
        results[slot] = (sys_id, endpoint, vehicle, error, elapsed)

    # Single deterministic step, on this thread only: walk the slots in
    # PORT_DICT order and append the connected ones.
    failed = []
    for slot, (sys_id, port) in enumerate(endpoints):
        result = results[slot]
        if result is None:
            print(
                f"[connect] slot={slot} sys_id={sys_id} port={port} TIMED OUT "
                f"(no result within {deadline_s:.0f}s)"
            )
            failed.append(sys_id)
            continue
        _sys_id, endpoint, vehicle, error, elapsed = result
        if vehicle is None:
            print(
                f"[connect] slot={slot} sys_id={sys_id} {endpoint} FAILED after "
                f"{elapsed:.1f}s: {error!r}"
            )
            print("Vehicle {} is lost".format(sys_id))
            failed.append(sys_id)
            continue
        target = vehicle._master.target_system
        if int(target) != int(sys_id):
            print(
                f"[connect] WARNING slot={slot} port={port} expected sys_id "
                f"{sys_id} but heartbeat says {target}"
            )
        print(
            f"[connect] slot={slot} sys_id={sys_id} {endpoint} CONNECTED in "
            f"{elapsed:.1f}s"
        )
        print("Drone{}".format(sys_id))
        state.num_bots += 1
        state.vehicles.append(vehicle)
        state.pos_array.append(target)

    print(
        f"[connect] done in {time.monotonic() - cycle_started:.1f}s: "
        f"configured={len(endpoints)} connected={len(state.vehicles)} "
        f"unavailable={len(failed)} {failed} pos_array={state.pos_array}"
    )

    # After ALL connections, so every drone counts toward the loiter radius.
    loiter = []
    for vehicle in state.vehicles:
        loiter.append(abs(float(vehicle.parameters["WP_LOITER_RAD"])))
    radius = max(loiter) if loiter else config.UAV_DEFAULT_LOITER_RADIUS_M
    state._loiter_radius = radius

    print(len(state.vehicles))


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
