import math
from .model.uav import UAV
from trio import sleep


def gps_bearing(
    homeLattitude, homeLongitude, destinationLattitude, destinationLongitude
):
    R = 6371e3  # Radius of earth in metres
    rlat1, rlat2 = math.radians(homeLattitude), math.radians(destinationLattitude)
    rlon1, rlon2 = math.radians(homeLongitude), math.radians(destinationLongitude)
    dlat, dlon = rlat2 - rlat1, rlon2 - rlon1

    a = (math.sin(dlat / 2) ** 2) + math.cos(rlat1) * math.cos(rlat2) * (
        math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c  # distance in metres

    y = math.sin(rlon2 - rlon1) * math.cos(rlat2)
    x = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(
        rlat2
    ) * math.cos(rlon2 - rlon1)
    bearing = math.degrees(math.atan2(y, x))

    return [distance, bearing]


def get_position(uav: UAV):
    loc = uav.status.position
    return loc.lat, loc.lon


def get_airspeed(uav: UAV):
    return uav.status.airspeed


async def speed_match(reference_model: int, vehicles: list[UAV]):
    while True:
        try:
            lat1, lon1 = get_position(vehicles[reference_model - 1])
            for i in range(0, len(vehicles)):
                if i != (reference_model - 1):
                    lat2, lon2 = get_position(vehicles[i])
                    distance, _ = gps_bearing(lat1, lon1, lat2, lon2)
                    print("Distance:", distance)
                    airspeed2 = get_airspeed(vehicles[i])
                    if distance >= 100 and airspeed2 <= 18:
                        await vehicles[i].driver._send_speed_correction(vehicles[i], 19)
                        sleep(0.2)
                    elif distance < 100 and airspeed2 < 17:
                        await vehicles[i].driver._send_speed_correction(vehicles[i], 18)
                        sleep(0.2)
        except Exception as e:
            print("Error:", e)
