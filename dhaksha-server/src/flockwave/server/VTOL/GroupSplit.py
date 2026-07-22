import csv
import simplekml
from geopy.distance import distance
from geopy.point import Point


def CreateGridsForSpecifiedAreaAndSpecifiedDrones(
    center_latitude: float,
    center_longitude: float,
    num_of_drones: int,
    grid_space: int,
    coverage_area: int,
    start_index: int,
) -> None:
    center_lat = center_latitude
    center_lon = center_longitude

    num_rectangles = num_of_drones
    grid_spacing = grid_space
    meters_for_extended_lines = 250

    full_width, full_height = coverage_area, coverage_area

    rectangle_height = full_height / num_rectangles

    center_point = Point(center_lat, center_lon)

    west_edge = distance(meters=full_width / 2).destination(center_point, 270)
    index = start_index

    for i in range(num_rectangles):
        top_offset = (i * rectangle_height) - (full_height / 2) + (rectangle_height / 2)

        top_center = distance(meters=top_offset).destination(center_point, 0)
        top = distance(meters=rectangle_height / 2).destination(top_center, 0)
        bottom = distance(meters=rectangle_height / 2).destination(top_center, 180)

        kml = simplekml.Kml()

        csv_data = []

        current_lat = bottom.latitude
        line_number = 0
        line = kml.newlinestring()
        line.altitudemode = simplekml.AltitudeMode.clamptoground
        line.style.linestyle.color = simplekml.Color.black
        line.style.linestyle.width = 2
        waypoint_number = 1

        while current_lat <= top.latitude:
            line_number += 1
            current_point = Point(current_lat, west_edge.longitude)
            east_point = distance(meters=full_width).destination(current_point, 90)
            if line_number % 2 == 1:
                csv_data.append((current_point.latitude, current_point.longitude))
                csv_data.append((east_point.latitude, east_point.longitude))

                line.coords.addcoordinates(
                    [
                        (current_point.longitude, current_point.latitude),
                        (east_point.longitude, east_point.latitude),
                    ]
                )
                kml.newpoint(
                    name=f"{waypoint_number}",
                    coords=[(current_point.longitude, current_point.latitude)],
                )
                waypoint_number += 1
                kml.newpoint(
                    name=f"{waypoint_number}",
                    coords=[(east_point.longitude, east_point.latitude)],
                )
                waypoint_number += 1
            else:
                csv_data.append((east_point.latitude, east_point.longitude))
                csv_data.append((current_point.latitude, current_point.longitude))

                line.coords.addcoordinates(
                    [
                        (east_point.longitude, east_point.latitude),
                        (current_point.longitude, current_point.latitude),
                    ]
                )
                kml.newpoint(
                    name=f"{waypoint_number}",
                    coords=[(east_point.longitude, east_point.latitude)],
                )
                waypoint_number += 1
                kml.newpoint(
                    name=f"{waypoint_number}",
                    coords=[(current_point.longitude, current_point.latitude)],
                )
                waypoint_number += 1

            if line_number % 2 == 1:
                point_135 = distance(meters=meters_for_extended_lines).destination(
                    east_point, 135
                )
                csv_data.append((point_135.latitude, point_135.longitude))
                line.coords.addcoordinates([(point_135.longitude, point_135.latitude)])
                kml.newpoint(
                    name=f"{waypoint_number}",
                    coords=[(point_135.longitude, point_135.latitude)],
                )
                waypoint_number += 1
            else:
                point_225 = distance(meters=meters_for_extended_lines).destination(
                    current_point, 225
                )
                csv_data.append((point_225.latitude, point_225.longitude))
                line.coords.addcoordinates([(point_225.longitude, point_225.latitude)])
                kml.newpoint(
                    name=f"{waypoint_number}",
                    coords=[(point_225.longitude, point_225.latitude)],
                )
                waypoint_number += 1

            current_lat = (
                distance(meters=grid_spacing).destination(current_point, 0).latitude
            )

        kml_filename = f"search-drone-{index}.kml"
        kml.save(
            "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/kmls/"
            + kml_filename
        )

        csv_filename = f"search-drone-{index}.csv"
        with open(
            "F:/Tharun/SWARM/VTOL_SWARM/Fixedwing-Swarm/dhaksha-server/src/flockwave/server/VTOL/csvs/"
            + csv_filename,
            mode="w",
            newline="",
        ) as file:
            writer = csv.writer(file)
            writer.writerows(csv_data)
        index += 1


def GroupSplitting(
    center_lat_lons: list[list[float]],
    num_of_drones: int,
    grid_spacing: int,
    coverage_area: int,
) -> bool:
    drones_array = [0] * len(center_lat_lons)
    for i in range(num_of_drones):
        drones_array[i % len(center_lat_lons)] += 1
    start = 1
    for i in range(len(center_lat_lons)):
        if drones_array[i] == 0:
            continue
        CreateGridsForSpecifiedAreaAndSpecifiedDrones(
            center_lat_lons[i][1],
            center_lat_lons[i][0],
            drones_array[i],
            grid_spacing,
            coverage_area,
            start,
        )
        start += drones_array[i]
    return True


# center_lat = 13.386046
# center_lon = 80.231535

# center_lat_lons = [
#     [13.386046, 80.231535],
#     [13.386046, 80.231535],
#     [13.386046, 80.231535],
#     [13.386046, 80.231535],
#     [13.386046, 80.231535],
#     [13.386046, 80.231535],
# ]

# num_of_drones = 15
# grid_spacing = 50
# coverage_area = 1200

# GroupSplitting(center_lat_lons, num_of_drones, grid_spacing, coverage_area)
