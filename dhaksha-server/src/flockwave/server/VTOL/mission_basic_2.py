#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time, csv
from flockwave.server.model import UAV
from flockwave.server.ext.mavlink.automission import AutoMissionManager
from flockwave.server.ext.mavlink.enums import MAVCommand
from flockwave.gps.vectors import GPSCoordinate
from typing import List
from trio import sleep


async def add_mavlink_mission(i: int, alt: int, uav: UAV) -> None:
    manager = AutoMissionManager.for_uav(uav)
    await manager.clear_mission()
    search_file = "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/search-drone-"
    points_coordinate = []
    prev_lat, prev_lon = 0, 0
    with open(
        search_file + str(i) + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            lat = float(row[0])
            lon = float(row[1])
            points_coordinate.append(
                [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT],
            )
            prev_lat = lat
            prev_lon = lon
    points_coordinate.append(
        [GPSCoordinate(prev_lat, prev_lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM],
    )
    with open(
        "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/reverse-drone-"
        + str(i)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            lat = float(row[0])
            lon = float(row[1])
            points_coordinate.append(
                [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT],
            )
            prev_lat = lat
            prev_lon = lon
    points_coordinate.append(
        [GPSCoordinate(prev_lat, prev_lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM],
    )
    points_mission = convert_to_missioncmd(points_coordinate)
    await manager.set_automission_areas(points_mission)


def convert_to_missioncmd(
    points_coordinate: List[list[GPSCoordinate, MAVCommand]]
) -> List[tuple[MAVCommand, dict[str, int]]]:
    points_mission = [
        (
            (point[1]),
            {
                "x": int(point[0].lat * 1e7),
                "y": int(point[0].lon * 1e7),
                "z": int(point[0].ahl),
            },
        )
        for point in points_coordinate
    ]
    return points_mission


async def Dynamic_main(uavs: dict[str, UAV]) -> bool:
    from ..socket.globalVariable import getAlts, drone

    drone_id = drone
    alts = getAlts()
    for i, uav in enumerate(uavs):
        alt = alts[uav]
        vehicle = uavs[uav]
        print(i + 1)
        if vehicle:
            await vehicle.driver._send_guided_mode_single(vehicle)
            await sleep(0.5)
            await add_mavlink_mission(i + 1, alt, vehicle)
    return True
