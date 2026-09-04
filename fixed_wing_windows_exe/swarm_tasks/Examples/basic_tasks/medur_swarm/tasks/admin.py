"""Miscellaneous dispatch-loop commands that don't belong to any of the
named mission categories: origin/geofence refresh, snapshotting the swarm's
current position to CSV, locking in each vehicle's home position, and
arm+takeoff.

None of these commands ever abort the dispatch-loop iteration early (no
`continue` in the original inline blocks), so main.py just calls each of
these unconditionally -- every function re-checks `data` itself and is a
no-op when it doesn't match.
"""

import csv
import os
import shutil
import threading
import time

import locatePosition
import yaml
from shapely.geometry import Polygon
from swarm_tasks.simulation import simulation as sim

from medur_swarm import config, state


def apply_origin_update(data):
    if not data.startswith(b"origin"):
        return
    decoded_index = data.decode("utf-8")
    _, new_lat, new_lon = decoded_index.split(",")
    state.origin = (float(new_lat), float(new_lon))
    print("Origin updated dynamically:", state.origin)


def reload_geofence(data):
    if data != b"geofence":
        return
    try:
        rectangles_path = config.RECTANGLES_PATH
        with open(rectangles_path) as f:
            world_data = yaml.safe_load(f)
        new_size = (world_data["size"]["x"], world_data["size"]["y"])
        new_obstacles = [
            Polygon(o) for o in (world_data.get("obstacles") or [])
        ]
        state.s.env.obstacles = new_obstacles
        state.s.env.size = new_size
        state.s.size = new_size

        # Every s = sim.Simulation(..., env_name=file_name) call
        # throughout this script (preview rebuilds, vehicle
        # add/remove, etc.) loads its world via
        # World(filename=file_name+'.yaml'), which only looks
        # inside swarm_tasks/envs/worlds/ -- it can't see the
        # dynamic file above directly. Mirroring it into that
        # folder and pointing file_name at it means every future
        # rebuild picks up the current drawn area too, not just
        # this already-running s.
        worlds_dir = sim.envs.world.worlds_path
        shutil.copyfile(
            rectangles_path, os.path.join(worlds_dir, "rectangles.yaml")
        )
        state.file_name = "rectangles"

        print(
            f"Obstacles hot-reloaded from {rectangles_path}: {len(new_obstacles)} walls, origin:",
            state.origin,
        )
    except Exception as e:
        print(f"Error reloading obstacles: {e}")


def store_uav_pos(data):
    if data != b"store_uav_pos":
        return
    if os.path.exists(csv_file_path):
        os.remove(csv_file_path)

    with open(csv_file_path, mode="w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["X", "Y"])  # Write header
        csv_writer.writerows(state.home_pos)
        csv_file.close()


def lock_home_position(data):
    if data != b"home_lock":
        return
    for i, vehicle in enumerate(state.vehicles):
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
        x, y = locatePosition.geoToCart(
            state.origin, config.END_DISTANCE, [home.lat, home.lon]
        )
        state.home_pos_lat_lon[i] = (home.lat, home.lon)
        print("x,y", x / 2, y / 2)
        state.home_pos[i] = (x / 2, y / 2)
        if i < len(state.robots):
            state.robots[i] = (x / 2, y / 2)
        msg = ",".join([f"{robot[0]},{robot[1]}" for robot in state.robots])


def refresh_origin_and_rebuild_sim(data):
    if not data.startswith(b"origin"):
        return
    decoded_index = data.decode("utf-8")
    _, lat, lon = decoded_index.split(",")
    state.origin = (float(lat), float(lon))
    state.file_name = "rectangles"
    # uav_home_pos must be recomputed under the *new* origin here --
    # reusing whatever was left over from before this origin change
    # spawns bots at cartesian coordinates from the old frame, which
    # no longer lines up with the real UAVs converted through the
    # new origin, and stays wrong until the real aircraft happens to
    # fly within the dis<=300 resync radius of the stale bot.
    state.uav_home_pos = []
    for vehicle in state.vehicles:
        lat_i = vehicle.location.global_relative_frame.lat
        lon_i = vehicle.location.global_relative_frame.lon
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat_i, lon_i])
        state.uav_home_pos.append((x / 2, y / 2))
        # switches env to the dynamically-written world file
    state.s = sim.Simulation(
        state.uav_home_pos, num_bots=len(state.pos_array), env_name=state.file_name
    )
    print("Origin + obstacles refreshed:", state.origin, state.file_name)


def run_takeoff_command(data):
    if not data.startswith(b"takeoff"):
        return
    decoded_index = data.decode("utf-8")
    print("decoded_index", decoded_index)
    data, takeoff_height = decoded_index.split(",")
    print("data,takeoff_height", data, takeoff_height)
    vehicles_thread = []
    for i, vehicle in enumerate(state.vehicles):
        print(i)
        thread = threading.Thread(
            target=arm_and_takeoff, args=(vehicle, int(takeoff_height))
        )
        vehicles_thread.append(thread)
        thread.start()

    for thread in vehicles_thread:
        thread.join()

    for i, vehicle in enumerate(state.vehicles):
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
        x, y = locatePosition.geoToCart(
            state.origin, config.END_DISTANCE, [home.lat, home.lon]
        )
        state.home_pos_lat_lon[i] = (home.lat, home.lon)
        print("x,y", x / 2, y / 2)
        state.home_pos[i] = (x / 2, y / 2)
        if i < len(state.robots):
            state.robots[i] = (x / 2, y / 2)
        msg = ",".join([f"{robot[0]},{robot[1]}" for robot in state.robots])
