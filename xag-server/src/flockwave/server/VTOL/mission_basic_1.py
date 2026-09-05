from flockwave.server.ext.mavlink.automission import AutoMissionManager
from flockwave.server.ext.mavlink.enums import MAVCommand
from flockwave.gps.vectors import GPSCoordinate
from flockwave.server.model import UAV
import csv
from typing import List


async def add_mavlink_mission1(
    i: int, alt: int, uav: UAV, rtl_height: int
) -> None:
    manager = AutoMissionManager.for_uav(uav)
    await manager.clear_mission()
    search_file = "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/search-drone-"
    flag = 0
    points_coordinate = [
        # [
        #     GPSCoordinate(lath, lonh, 0, initial_takeoff, 0),
        #     MAVCommand.NAV_VTOL_TAKEOFF,
        # ],
        # [
        #     GPSCoordinate(lath, lonh, 0, initial_takeoff, 0),
        #     MAVCommand.NAV_VTOL_TAKEOFF,
        # ],
    ]
    # with open(
    #     "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/forward-drone-{}.csv".format(
    #         i
    #     ),
    #     "r",
    # ) as f:
    #     csvreader = csv.reader(f)
    #     for row in csvreader:
    #         lat = float(row[0])
    #         lon = float(row[1])
    #         if flag == 2:
    #             points_coordinate.append(
    #                 [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT],
    #             )
    #             points_coordinate.append(
    #                 [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM],
    #             )
    #         else:
    #             points_coordinate.append(
    #                 [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT],
    #             )
    #         prev_lat = lat
    #         prev_lon = lon
    #         flag += 1
    # with open(
    #     search_file + str(i) + ".csv",
    #     "r",
    # ) as f:
    #     csvreader = csv.reader(f)
    #     for row in csvreader:
    #         lat = float(row[0])
    #         lon = float(row[1])
    #         points_coordinate.append(
    #             [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT]
    #         )
    #         prev_lat = lat
    #         prev_lon = lon
    # points_coordinate.append(
    #     [GPSCoordinate(prev_lat, prev_lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM]
    # )
    reverse_waypoints = 0
    with open(
        "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/reverse-drone-"
        + str(i)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            reverse_waypoints += 1
    count = 0
    print("reverse_waypoints",reverse_waypoints)
    with open(
        "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/reverse-drone-"
        + str(i)
        + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            # if count == reverse_waypoints - 4:
            # lat = float(row[0])
            # lon = float(row[1])
            # points_coordinate.append(
            #     [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT]
            # )
                # prev_lat = lat
                # prev_lon = lon
                # points_coordinate.append(
                #     [
                #         GPSCoordinate(prev_lat, prev_lon, 0, alt, 0),
                #         MAVCommand.NAV_LOITER_UNLIM,
                #     ]
                # )
            if count > reverse_waypoints - 3:
                lat = float(row[0])
                lon = float(row[1])
                points_coordinate.append(
                    [GPSCoordinate(lat, lon, 0, rtl_height, 0), MAVCommand.NAV_WAYPOINT]
                )
                prev_lat = lat
                prev_lon = lon
            else:
                lat = float(row[0])
                lon = float(row[1])
                points_coordinate.append(
                    [
                        GPSCoordinate(lat, lon, 0, alt, 0),
                        MAVCommand.NAV_WAYPOINT,
                    ]
                )
                prev_lat = lat
                prev_lon = lon
            flag = 1
            count += 1
    points_mission = convert_to_missioncmd(points_coordinate)
    await manager.set_automission_areas(points_mission)


async def add_mavlink_mission(i: int, alt: int, uav: UAV, initial_takeoff: int) -> None:
    manager = AutoMissionManager.for_uav(uav)
    await manager.clear_mission()
    search_file = "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/search-drone-"
    flag = 0
    lath, lonh = uav.status.position.lat, uav.status.position.lon
    points_coordinate = [
        [
            GPSCoordinate(lath, lonh, 0, initial_takeoff, 0),
            MAVCommand.NAV_VTOL_TAKEOFF,
        ],
        [
            GPSCoordinate(lath, lonh, 0, initial_takeoff, 0),
            MAVCommand.NAV_VTOL_TAKEOFF,
        ],
    ]
    with open(
        "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/forward-drone-{}.csv".format(
            i
        ),
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            lat = float(row[0])
            lon = float(row[1])
            if flag == 2:
                points_coordinate.append(
                    [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT],
                )
                points_coordinate.append(
                    [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM],
                )
            else:
                points_coordinate.append(
                    [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT],
                )
            prev_lat = lat
            prev_lon = lon
            flag += 1
    with open(
        search_file + str(i) + ".csv",
        "r",
    ) as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            lat = float(row[0])
            lon = float(row[1])
            points_coordinate.append(
                [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT]
            )
            prev_lat = lat
            prev_lon = lon
    points_coordinate.append(
        [GPSCoordinate(prev_lat, prev_lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM]
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
                [GPSCoordinate(lat, lon, 0, alt, 0), MAVCommand.NAV_WAYPOINT]
            )
            prev_lat = lat
            prev_lon = lon
    points_coordinate.append(
        [GPSCoordinate(prev_lat, prev_lon, 0, alt, 0), MAVCommand.NAV_LOITER_UNLIM]
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


async def main(uavs: dict[str, UAV]) -> bool:
    from ..socket.globalVariable import getAlts,vtol_rtl_height

    alts = getAlts()
    for i, uav in enumerate(uavs):
        # initial_takeoff = vtol_takeoff_height[int(uav)]
        alt = alts[uav]
        rtl_height = vtol_rtl_height[int(uav)]
        vehicle = uavs[uav]
        if vehicle:
            await add_mavlink_mission1(i + 1, alt, vehicle, rtl_height)
            # initial_takeoff += 5
        # await add_mavlink_mission(index, alt, uav, altitudes[i])
    print("Uploaded")
    return True
