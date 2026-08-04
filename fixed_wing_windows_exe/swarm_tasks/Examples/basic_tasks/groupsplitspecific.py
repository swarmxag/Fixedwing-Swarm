import csv,os,sys
import simplekml
from geopy.distance import distance
from geopy.point import Point
from locatePosition import geoToCart,cartToGeo
from mission_paths import uav_path_csv, uav_path_kml
from bezier_smoothing import generate_bezier_path
import numpy as np
import matplotlib.pyplot as plt

class SpecificSplitMission():
    def __init__(self, origin,center_lat_lons, drone_array, grid_spacing, coverage_area):
        self.origin = origin
        self.center_lat_lons = center_lat_lons
        self.drone_array = drone_array
        self.grid_spacing = grid_spacing
        self.coverage_area = coverage_area
        self.initial_heading = np.radians(0)  # Initial heading angle in radians
        self.G = 9.81  # Gravity (m/s²)
        self.MAX_BANK_ANGLE = np.radians(20)  # 20 degrees in radians -- matches search's BezierCurveMultiple
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

        grid_spacing = grid_space
        meters_for_extended_lines = 250
        full_width, full_height = coverage_area, coverage_area

        rectangle_height = full_height / len(uav_ids)

        center_point = Point(center_lat, center_lon)

        west_edge = distance(meters=full_width / 2).destination(center_point, 270)

        for i in range(len(uav_ids)):
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
                x,y = geoToCart(self.origin,500000,data)
                xy.append((x/2.0,y/2.0))
            self.generate_bezier_curve(xy,uav_id)
            
    def write_kml(self,data,num):
        kml = simplekml.Kml()
        line = kml.newlinestring()
        line.altitudemode = simplekml.AltitudeMode.clamptoground
        line.style.linestyle.color = simplekml.Color.blue
        line.style.linestyle.width = 2
        kml_data = []
        if len(data) == 0:
            print("No Mission Data")
            return
        for i,cmd in enumerate(data):
            lat,lon = cartToGeo(self.origin,500000,[cmd[0]*2,cmd[1]*2])
            kml_data.append([lat,lon])
        for i in range(len(kml_data)-1):
            line.coords.addcoordinates(
                    [
                        (kml_data[i][1], kml_data[i][0]),
                        (kml_data[i+1][1],kml_data[i+1][0]),
                    ]
                )
            kml.newpoint(name="{}".format(i),coords=[(kml_data[i][1], kml_data[i][0])])
        kml.save(self._path_kml(num))

    def generate_bezier_curve(self,waypoints,index):
        self.waypoints.append(waypoints)
        result, is_bezier = generate_bezier_path(
            waypoints, self.SPEED, self.TURN_RATE, self.initial_heading
        )
        self.sample_points.extend(result)
        self.path.append(result)
        self.write_kml(result,index)
        self.write_to_csv(result,index,is_bezier)
        return result
    
    def plot_curve(self):
        plt.figure(figsize=(8, 6))
        num_of_drones=0
        for num in self.drone_array:
            num_of_drones+=len(num)    
        for num in range(num_of_drones):
            predict_path = np.array(self.path[num])
            sampled_points = np.array(self.sample_points)
            waypoints = self.waypoints[num]
            plt.plot(predict_path[:, 0], predict_path[:, 1], 'r-', linewidth=2)
            plt.scatter(*zip(*waypoints), color='blue', s=100, marker='X')

            plt.scatter(sampled_points[:, 0], sampled_points[:, 1], color='black', marker='o', s=40)

    # Annotate the sampled Bézier points with t-values
        for i, (x, y) in enumerate(sampled_points):
            plt.text(x, y, f'w', fontsize=10, verticalalignment='top', horizontalalignment='left')

        plt.xlabel("X Position (m)")
        plt.ylabel("Y Position (m)")
        plt.title("Aircraft Path Prediction with 40° Roll Limit")
        plt.legend()
        plt.grid()
        plt.axis("equal")

            # --- Ensure Plot Opens Correctly ---
        plt.show(block=True)  # Ensures the window stays open

    def write_to_csv(self, data, num, is_bezier=None):
        if is_bezier is None:
            is_bezier = [False] * len(data)
        with open(self._path_csv(num), "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            for row, flag in zip(data, is_bezier):
                csv_writer.writerow(list(row) + [flag])

    def GroupSplitting(
            self,
            center_lat_lons,
            drone_array,
            grid_spacing,
            coverage_area
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

'''
center_latlon = [
    [13.391341, 80.236145],
    [13.386840, 80.257992],
    [13.393423, 80.224792],
    [13.383977, 80.236774],
    [13.373029, 80.236966],
]
origin = ( 13.210665, 80.099739) #[13.375812,80.225549]
drone_array = [[2,4],[5,7],[1],[6],[3,8]]
grid_spacing = [50,100,50,100,50]
coverage_area = [1000,2000,2000,1000,1000]
split = SpecificSplitMission(origin=origin,center_lat_lons=center_latlon, drone_array=drone_array, grid_spacing=grid_spacing,
                         coverage_area=coverage_area)
isDone = split.GroupSplitting(
    center_lat_lons=center_latlon,
    drone_array=drone_array,
    grid_spacing=grid_spacing,
    coverage_area=coverage_area,
)
split.plot_curve()
print(isDone)

'''