"""Generic, mostly-pure helpers: geometry, CSV access, UAV-id selection
parsing, and drone-count allocation for redistributing a removed UAV's
remaining grid points."""

import csv
import json
from math import radians, sin, cos, atan2, asin, degrees

import yaml

from medur_swarm import state


def read_origin(filepath):
    """Same approach copter_swarm.py uses: read origin straight from the
    persisted rectangles.yaml on disk at startup, so it's already valid by
    the time the arm+altitude wait loop calls fetch_location() -- no
    hardcoded per-site preset, no polling required."""
    print("Reading YAML from:", filepath)
    with open(filepath) as f:
        data = yaml.safe_load(f)
    origin = data.get("origin")
    if isinstance(origin, str):
        origin = origin.strip("()")
        lat, lon = origin.split(",")
        origin = (float(lat), float(lon))
    return origin


def generate_points(lat, lon, num_points, radius, circle_direction):
    # List to store generated points
    points = []

    # Generate points in circular formation
    for i in range(num_points):
        # Calculate bearing angle

        bearing_sign = 1 if circle_direction == 1 else -1
        bearing = bearing_sign * (360 / num_points * i)

        # Calculate new latitude and longitude
        lat2 = asin(
            sin(radians(lat)) * cos(radius / 6371000)
            + cos(radians(lat)) * sin(radius / 6371000) * cos(radians(bearing))
        )
        lon2 = radians(lon) + atan2(
            sin(radians(bearing)) * sin(radius / 6371000) * cos(radians(lat)),
            cos(radius / 6371000) - sin(radians(lat)) * sin(lat2),
        )

        # Append the new point to the list
        points.append((degrees(lat2), degrees(lon2)))

    return points


def read_specific_line(csv_file_path, line_number):
    goal = []
    with open(csv_file_path, "rt") as file:
        reader = csv.reader(file)
        for i in range(line_number):
            next(reader)
            # Read the desired line
        line = next(reader)
        goal.append((float(line[0]), float(line[1]), str(line[2])))
        return goal


def parse_selected_uav_ids(raw_ids):
    if raw_ids is None:
        return []
    try:
        return [int(uav_id) for uav_id in json.loads(raw_ids)]
    except Exception:
        try:
            cleaned = str(raw_ids).strip().strip("[]")
            if not cleaned:
                return []
            return [
                int(part.strip().strip('"').strip("'"))
                for part in cleaned.split(",")
                if part.strip()
            ]
        except Exception as e:
            print("[selected UAV parse] failed", raw_ids, e)
            return []


def selected_swarm_indexes(selected_uav_ids):
    if not selected_uav_ids:
        return list(range(len(state.pos_array)))
    selected = {int(uav_id) for uav_id in selected_uav_ids}
    indexes = [i for i, uav_id in enumerate(state.pos_array) if int(uav_id) in selected]
    missing = selected.difference({int(uav_id) for uav_id in state.pos_array})
    if missing:
        print(
            "[selected UAV] IDs not connected/in pos_array:",
            sorted(missing),
            "pos_array:",
            state.pos_array,
        )
    return indexes


def calculate_drones_needed(remaining_points, points_per_drone, total_drones):
    if remaining_points <= 0:
        return 0
    if remaining_points <= 4:
        return 1
    points_per_drone = max(1, int(points_per_drone))
    return min(
        total_drones, (int(remaining_points) + points_per_drone - 1) // points_per_drone
    )


def allocate_drones(total_points, covered_points, total_drones):
    if isinstance(total_points, int):
        total_points = [total_points] * len(covered_points)
    remaining_points_list = [
        max(0, int(tp) - int(cp)) for tp, cp in zip(total_points, covered_points)
    ]
    points_per_drone = [max(1, int(tp / 2)) for tp in total_points]
    uncovered_areas = [
        (i, points) for i, points in enumerate(remaining_points_list) if points > 0
    ]
    allocation = {i: 0 for i in range(len(covered_points))}
    if total_drones <= 0:
        return allocation, remaining_points_list
    if total_drones <= len(uncovered_areas):
        for i, _ in uncovered_areas:
            if total_drones <= 0:
                break
            allocation[i] = 1
            total_drones -= 1
    else:
        for i, _ in uncovered_areas:
            if total_drones <= 0:
                break
            needed = calculate_drones_needed(
                remaining_points_list[i], points_per_drone[i], total_drones
            )
            allocation[i] = needed
            total_drones -= needed
    print("[redistribution] allocation", allocation, "remaining", remaining_points_list)
    return allocation, remaining_points_list
