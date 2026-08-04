import os
import csv
import simplekml
from geopy.distance import distance
from geopy.point import Point
from .latlon2xy import geoToCart, cartToGeo
from .mission_paths import uav_path_csv, uav_path_kml
from .bezier_smoothing import generate_bezier_path
import numpy as np


class SpecificSplitMission:
    def __init__(
        self, origin, center_lat_lons, drone_array, grid_spacing, coverage_area
    ):
        self.origin = origin
        self.center_lat_lons = center_lat_lons
        self.drone_array = drone_array
        self.grid_spacing = grid_spacing
        self.coverage_area = coverage_area
        self.initial_heading = np.radians(0)  # Initial heading angle in radians
        self.G = 9.81  # Gravity (m/s²)
        self.MAX_BANK_ANGLE = np.radians(20)  # 20 degrees in radians -- matches search's BezierCurve
        self.SPEED = 18  # Aircraft speed in m/s
        self.TURN_RATE = (self.G * np.tan(self.MAX_BANK_ANGLE)) / self.SPEED  # rad/s
        self.sample_points = []
        self.path = []
        self.waypoints = []

    def _path_csv(self, uav_id):
        return uav_path_csv(uav_id)

    def _path_kml(self, uav_id):
        return uav_path_kml(uav_id)

    def CreateGridsForSpecifiedAreaAndSpecifiedDrones(
        self,
        center_latitude: float,
        center_longitude: float,
        uav_ids: list,
        grid_space: int,
        coverage_area: int,
    ) -> None:

        center_lat = center_latitude
        center_lon = center_longitude

        num_rectangles = len(uav_ids)
        grid_spacing = grid_space
        meters_for_extended_lines = 250

        full_width, full_height = coverage_area, coverage_area

        rectangle_height = full_height / num_rectangles

        center_point = Point(center_lat, center_lon)

        west_edge = distance(meters=full_width / 2).destination(center_point, 270)

        for i in range(num_rectangles):
            top_offset = (i * rectangle_height) - (full_height / 2) + (rectangle_height / 2)

            top_center = distance(meters=top_offset).destination(center_point, 0)
            top = distance(meters=rectangle_height / 2).destination(top_center, 0)
            bottom = distance(meters=rectangle_height / 2).destination(top_center, 180)

            csv_data = []

            current_lat = bottom.latitude
            line_number = 0

            while current_lat <= top.latitude:
                line_number += 1
                current_point = Point(current_lat, west_edge.longitude)
                east_point = distance(meters=full_width).destination(current_point, 90)
                if line_number % 2 == 1:
                    csv_data.append((current_point.latitude, current_point.longitude))
                    csv_data.append((east_point.latitude, east_point.longitude))
                else:
                    csv_data.append((east_point.latitude, east_point.longitude))
                    csv_data.append((current_point.latitude, current_point.longitude))

                if line_number % 2 == 1:
                    point_135 = distance(meters=meters_for_extended_lines).destination(
                        east_point, 110
                    )
                    csv_data.append((point_135.latitude, point_135.longitude))
                else:
                    point_225 = distance(meters=meters_for_extended_lines).destination(
                        current_point, 250
                    )
                    csv_data.append((point_225.latitude, point_225.longitude))

                current_lat = (
                    distance(meters=grid_spacing).destination(current_point, 0).latitude
                )

            uav_id = uav_ids[i]
            # Grid points never persisted -- fed straight into
            # generate_bezier_curve() below, same as the rest of this run;
            # see mission_paths.py module docstring.
            xy = []
            for data in csv_data:
                y, x = geoToCart(self.origin, 500000, data)
                xy.append((x / 2.0, y / 2.0))
            self.generate_bezier_curve(xy, uav_id)

    def write_kml(self, data, num):
        kml = simplekml.Kml()
        line = kml.newlinestring()
        line.altitudemode = simplekml.AltitudeMode.clamptoground
        line.style.linestyle.color = simplekml.Color.blue
        line.style.linestyle.width = 2
        kml_data = []
        if len(data) == 0:
            print("No Mission Data")
            return
        for i, cmd in enumerate(data):
            lat, lon = cartToGeo(self.origin, 500000, [cmd[0] * 2, cmd[1] * 2])
            kml_data.append([lat, lon])
        for i in range(len(kml_data) - 1):
            line.coords.addcoordinates(
                [
                    (kml_data[i][1], kml_data[i][0]),
                    (kml_data[i + 1][1], kml_data[i + 1][0]),
                ]
            )
            kml.newpoint(name="{}".format(i), coords=[(kml_data[i][1], kml_data[i][0])])
        kml.save(self._path_kml(num))

    def generate_bezier_curve(self, waypoints, index):
        self.waypoints.append(waypoints)
        # max_iter=500000 (vs. search's default 5000) is kept here
        # deliberately -- unchanged from this class's prior standalone
        # implementation.
        result, _is_bezier = generate_bezier_path(
            waypoints, self.SPEED, self.TURN_RATE, self.initial_heading,
            max_iter=500000,
        )
        self.sample_points.extend(result)
        self.path.append(result)
        self.write_kml(result, index)
        self.write_to_csv(result, index)
        return result

    def write_to_csv(self, data, num):
        with open(self._path_csv(num), "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            for row in data:
                csv_writer.writerow(row)

    def GroupSplitting(
        self, center_lat_lons, drone_array, grid_spacing, coverage_area
    ) -> bool:
        for i in range(len(center_lat_lons)):
            if len(drone_array[i]) == 0:
                continue
            self.CreateGridsForSpecifiedAreaAndSpecifiedDrones(
                center_lat_lons[i][0],
                center_lat_lons[i][1],
                drone_array[i],
                grid_spacing[i],
                coverage_area[i],
            )
        return True

    def return_latlon(self):
        lat_lon = []
        for paths in self.path:
            path_lat_lon = []
            for path in paths:
                lat, lon = cartToGeo(self.origin, 500000, [path[0] * 2, path[1] * 2])
                path_lat_lon.append([float(lon), float(lat)])
            lat_lon.append(path_lat_lon)

        return lat_lon
