import math
from typing import List


def destination_location(
    homeLattitude: float,
    homeLongitude: float,
    distance: float | int,
    bearing: float | int,
) -> List[float]:
    R = 6371e3  # Radius of earth in metres
    rlat1 = homeLattitude * (math.pi / 180)
    rlon1 = homeLongitude * (math.pi / 180)
    d = distance
    bearing = bearing * (math.pi / 180)
    rlat2 = math.asin(
        (math.sin(rlat1) * math.cos(d / R))
        + (math.cos(rlat1) * math.sin(d / R) * math.cos(bearing))
    )
    rlon2 = rlon1 + math.atan2(
        (math.sin(bearing) * math.sin(d / R) * math.cos(rlat1)),
        (math.cos(d / R) - (math.sin(rlat1) * math.sin(rlat2))),
    )
    rlat2 = rlat2 * (180 / math.pi)
    rlon2 = rlon2 * (180 / math.pi)
    location = [rlat2, rlon2]
    return location


def Guided_Mission(t_lat: float, t_lon: float) -> List[List[float]]:

    lat_lon1 = destination_location(t_lat, t_lon, float(500), float(-90))
    lat1, lon1 = lat_lon1[0], lat_lon1[1]
    lat_lon2 = destination_location(t_lat, t_lon, float(500), float(90))
    lat2, lon2 = lat_lon2[0], lat_lon2[1]
    lat_lon3 = destination_location(t_lat, t_lon, float(1000), float(45))
    lat3, lon3 = lat_lon3[0], lat_lon3[1]

    result = [[lat1, lon1], [t_lat, t_lon], [lat2, lon2], [lat3, lon3]]

    return result
