import numpy as np
import csv, os, sys
import simplekml
from geopy.distance import distance
from geopy.point import Point
from locatePosition import geoToCart, cartToGeo
from mission_paths import uav_path_csv, uav_path_kml
from bezier_smoothing import generate_bezier_path
import matplotlib.pyplot as plt

# class BezierCurveMultiple:
#     def __init__(
#         self,
#         origin,
#         center_latitude,
#         center_longitude,
#         num_of_drones,
#         grid_space,
#         coverage_area,
#         uav_ids=None,
#     ):
#         self.initial_heading = np.radians(0)  # Initial heading angle in radians
#         self.G = 9.81  # Gravity (m/s²)
#         self.MAX_BANK_ANGLE = np.radians(20)  # 20 degrees in radians
#         self.SPEED = 18  # Aircraft speed in m/s
#         self.TURN_RATE = (self.G * np.tan(self.MAX_BANK_ANGLE)) / self.SPEED  # rad/s
#         self.origin = origin
#         self.center_latitude = center_latitude
#         self.center_longitude = center_longitude
#         self.num_of_drones = num_of_drones
#         self.grid_space = grid_space
#         self.coverage_area = coverage_area
#         # Real UAV ids, same order as the drone slots -- this is what the
#         # single persistent output file per UAV gets named after (see
#         # mission_paths.py). Falls back to the slot number itself if the
#         # caller doesn't have real ids handy, same as the old behaviour.
#         self.uav_ids = list(uav_ids) if uav_ids else list(range(1, num_of_drones + 1))
#         self.path = []
#         self.waypoints = []
#         self.sample_points = []
#         # Grid points, keyed by drone slot (1-based) -- kept in memory only.
#         # Never persisted: nothing outside generate_bezier_curve() (which
#         # runs immediately after GridFormation() in the same call) ever
#         # needs the raw grid, only the bezier-smoothed path that follows.
#         self._grid_by_slot = {}

#     def _uav_id(self, drone_num):
#         return self.uav_ids[drone_num - 1]

#     def _path_csv(self, drone_num):
#         return uav_path_csv(self._uav_id(drone_num))

#     def _path_kml(self, drone_num):
#         return uav_path_kml(self._uav_id(drone_num))

#     def write_to_csv(self, data, num):
#         with open(self._path_csv(num), "w", newline="") as csvfile:
#             csv_writer = csv.writer(csvfile)
#             for row in data:
#                 csv_writer.writerow(row)

#     def get_heading_to_target(self, current_pos, target_pos):
#         """Compute the heading angle required to face the target waypoint."""
#         dx, dy = target_pos[0] - current_pos[0], target_pos[1] - current_pos[1]
#         return np.arctan2(dy, dx)

#     def normalize_angle(self, angle):
#         """Ensure angles stay within -π to π range."""
#         return (angle + np.pi) % (2 * np.pi) - np.pi

#     def GridFormation(self):
#         center_lat = self.center_latitude
#         center_lon = self.center_longitude

#         num_rectangles = self.num_of_drones
#         grid_spacing = self.grid_space
#         meters_for_extended_lines = 250
#         gap_between_rectangles = 50

#         full_width, full_height = self.coverage_area, self.coverage_area

#         total_gap_height = (num_rectangles - 1) * gap_between_rectangles
#         available_height = full_height - total_gap_height
#         rectangle_height = available_height / num_rectangles

#         center_point = Point(center_lat, center_lon)

#         csv_datas = []

#         west_edge = distance(meters=full_width / 2).destination(center_point, 270)

#         for i in range(num_rectangles):
#             top_offset = (
#                 (i * rectangle_height) - (full_height / 2) + (rectangle_height / 2)
#             )

#             top_center = distance(meters=top_offset).destination(center_point, 0)
#             top = distance(meters=rectangle_height / 2).destination(top_center, 0)
#             bottom = distance(meters=rectangle_height / 2).destination(top_center, 180)

#             csv_data = []

#             current_lat = bottom.latitude
#             line_number = 0

#             while current_lat <= top.latitude:
#                 line_number += 1
#                 current_point = Point(current_lat, west_edge.longitude)
#                 east_point = distance(meters=full_width).destination(current_point, 90)
#                 if line_number % 2 == 1:
#                     csv_data.append((current_point.latitude, current_point.longitude))
#                     csv_data.append((east_point.latitude, east_point.longitude))
#                 else:
#                     csv_data.append((east_point.latitude, east_point.longitude))
#                     csv_data.append((current_point.latitude, current_point.longitude))

#                 if line_number % 2 == 1:
#                     point_135 = distance(meters=meters_for_extended_lines).destination(
#                         east_point, 110
#                     )
#                     csv_data.append((point_135.latitude, point_135.longitude))
#                 else:
#                     point_225 = distance(meters=meters_for_extended_lines).destination(
#                         current_point, 240
#                     )
#                     csv_data.append((point_225.latitude, point_225.longitude))

#                 current_lat = (
#                     distance(meters=grid_spacing).destination(current_point, 0).latitude
#                 )
#             csv_datas.append(csv_data)

#         # Grid points kept in memory only (self._grid_by_slot), keyed by
#         # 1-based drone slot -- generate_bezier_curve() reads them straight
#         # back out below; nothing else ever needs the raw grid once the
#         # bezier-smoothed path has been produced, so it's never written to
#         # disk (see mission_paths.py module docstring).
#         minimum_waypoints = len(min(csv_datas, key=len))
#         for i in range(len(csv_datas)):
#             points = []
#             for j in range(len(csv_datas[i])):
#                 if j >= minimum_waypoints:
#                     break
#                 x, y = geoToCart(self.origin, 500000, csv_datas[i][j])
#                 points.append((x / 2, y / 2))
#             self._grid_by_slot[i + 1] = points

#     def predict_path_with_waypoints(
#         self,
#         initial_pos,
#         initial_heading,
#         speed,
#         turn_rate,
#         waypoints,
#         dt=0.1,
#         max_iter=5000,
#     ):
#         """
#         Predicts the aircraft's movement through multiple waypoints.

#         Parameters:
#         - initial_pos: (x, y) tuple for the start position
#         - initial_heading: Initial heading in radians
#         - speed: Constant velocity (m/s)
#         - turn_rate: Max turn rate (rad/s)
#         - waypoints: List of (x, y) waypoints
#         - dt: Time step (s)
#         - max_iter: Prevent infinite loops by limiting iterations

#         Returns:
#         - A list of (x, y) positions representing the predicted path.
#         """
#         x, y = initial_pos
#         theta = initial_heading
#         path = [(x, y)]

#         for target in waypoints:
#             iteration = 0
#             while np.hypot(target[0] - x, target[1] - y) > speed * dt:
#                 if iteration > max_iter:
#                     print(
#                         f"Warning: Exceeded max iterations while moving to waypoint {target}, skipping!"
#                     )
#                     break  # Prevent infinite loop

#                 desired_theta = self.get_heading_to_target((x, y), target)

#                 heading_diff = self.normalize_angle(
#                     desired_theta - theta
#                 )  # Normalize angle difference

#                 # Adjust heading smoothly within the turn rate limit
#                 theta += np.clip(heading_diff, -turn_rate * dt, turn_rate * dt)

#                 # Move the aircraft forward
#                 x += speed * np.cos(theta) * dt
#                 y += speed * np.sin(theta) * dt

#                 path.append((x, y))
#                 iteration += 2
#         return np.array(path)

#     def generate_bezier_curve(self):
#         for num in range(self.num_of_drones):
#             waypoints = [list(point) for point in self._grid_by_slot.get(num + 1, [])]
#             self.waypoints.extend(waypoints)

#             result = [waypoints[0]]
#             alternative = False

#             for i in range(1, len(waypoints) - 1, 3):
#                 if i + 2 < len(waypoints) - 1:  # Ensure we don't include the last line
#                     if alternative:
#                         heading = 180
#                         alternative = False
#                     else:
#                         heading = self.initial_heading
#                         alternative = True
#                     data = []
#                     path1 = self.predict_path_with_waypoints(
#                         waypoints[i],
#                         heading,
#                         self.SPEED,
#                         self.TURN_RATE,
#                         [waypoints[i], waypoints[i + 1], waypoints[i + 2]],
#                     )
#                     sampled_indices = np.linspace(
#                         0, len(path1) - 1, 10, dtype=int
#                     )  # Select 20 key points
#                     sampled_points = path1[sampled_indices]
#                     for sample_point in sampled_points:
#                         data.append(sample_point.tolist())
#                     data.append(waypoints[i + 2])
#                     self.sample_points.extend(data)
#                     result.extend(data)
#                 else:
#                     j = i
#                     while j <= len(waypoints) - 1:
#                         result.append(waypoints[j])
#                         j += 1
#             self.path.append(result)
#             self.write_to_csv(result, num + 1)
#             self.write_kml(result, num + 1)
#         return self.path

#     def write_kml(self, data, num):
#         kml = simplekml.Kml()
#         line = kml.newlinestring()
#         line.altitudemode = simplekml.AltitudeMode.clamptoground
#         line.style.linestyle.color = simplekml.Color.blue
#         line.style.linestyle.width = 2
#         kml_data = []
#         if len(data) == 0:
#             print("No Mission Data")
#             return
#         for i, cmd in enumerate(data):
#             lat, lon = cartToGeo(self.origin, 500000, [cmd[0] * 2, cmd[1] * 2])
#             kml_data.append([lat, lon])
#         for i in range(len(kml_data) - 1):
#             line.coords.addcoordinates(
#                 [
#                     (kml_data[i][1], kml_data[i][0]),
#                     (kml_data[i + 1][1], kml_data[i + 1][0]),
#                 ]
#             )
#             kml.newpoint(name="{}".format(i), coords=[(kml_data[i][1], kml_data[i][0])])
#         kml.save(self._path_kml(num))

#     def plot_curve(self):
#         for num in range(self.num_of_drones):
#             predict_path = np.array(self.path[num])
#             # sampled_points = np.array(self.sample_points)
#             plt.figure(figsize=(8, 6))
#             plt.plot(
#                 predict_path[:, 0],
#                 predict_path[:, 1],
#                 "r-",
#                 label="Predicted Path",
#                 linewidth=2,
#             )
#             plt.scatter(
#                 *zip(*self.waypoints),
#                 color="blue",
#                 s=100,
#                 label="Waypoints",
#                 marker="X",
#             )

#             #     plt.scatter(sampled_points[:, 0], sampled_points[:, 1], color='black', marker='o', s=40, label="Bézier Points")

#             # # Annotate the sampled Bézier points with t-values
#             #     for i, (x, y) in enumerate(sampled_points):
#             #         plt.text(x, y, f'w', fontsize=10, verticalalignment='top', horizontalalignment='left')

#             plt.xlabel("X Position (m)")
#             plt.ylabel("Y Position (m)")
#             plt.title("Aircraft Path Prediction with 40° Roll Limit")
#             plt.legend()
#             plt.grid()
#             plt.axis("equal")

#             # --- Ensure Plot Opens Correctly ---
#             plt.show(block=True)  # Ensures the window stays open


class BezierCurveMultiple:
    def __init__(
        self,
        origin,
        center_latitude,
        center_longitude,
        num_of_drones,
        grid_space,
        coverage_area,
        uav_ids=None,
        min_turn_radius=None,
        cruise_speed=None,
    ):
        self.initial_heading = np.radians(0)  # Initial heading angle in radians
        self.G = 9.81  # Gravity (m/s²)
        self.MAX_BANK_ANGLE = np.radians(20)
        # min_turn_radius (metres): shape every generated turn to this radius
        # instead of the bank-angle default (~91 m at SPEED=18, bank=20 deg),
        # so the planned path is trackable by an aircraft flying that loiter
        # radius. Falls back to the bank-angle geometry when not supplied.
        self.SPEED = (
            float(cruise_speed) if cruise_speed and float(cruise_speed) > 0 else 18.0
        )
        if min_turn_radius and float(min_turn_radius) > 0:
            self.TURN_RADIUS = float(min_turn_radius)
        else:
            self.TURN_RADIUS = (self.SPEED ** 2) / (
                self.G * np.tan(self.MAX_BANK_ANGLE)
            )
        self.TURN_RATE = self.SPEED / self.TURN_RADIUS
        if grid_space and grid_space < 2 * self.TURN_RADIUS:
            print(
                f"[bezier] WARNING grid_space={grid_space} m < 2*turn_radius="
                f"{2 * self.TURN_RADIUS:.0f} m -- 180 deg turn-arounds will bulge "
                f"past adjacent lines / the coverage box"
            )
        self.origin = origin
        self.center_latitude = center_latitude
        self.center_longitude = center_longitude
        self.num_of_drones = num_of_drones
        self.grid_space = grid_space
        self.coverage_area = coverage_area
        # Real UAV ids, same order as the drone slots -- this is what the
        # single persistent output file per UAV gets named after (see
        # mission_paths.py). Falls back to the slot number itself if the
        # caller doesn't have real ids handy, same as the old behaviour.
        self.uav_ids = list(uav_ids) if uav_ids else list(range(1, num_of_drones + 1))
        self.path = []
        self.waypoints = []
        self.sample_points = []
        # Grid points, keyed by drone slot (1-based) -- kept in memory only.
        # Never persisted: nothing outside generate_bezier_curve() (which
        # runs immediately after GridFormation() in the same call) ever
        # needs the raw grid, only the bezier-smoothed path that follows.
        self._grid_by_slot = {}

    def _uav_id(self, drone_num):
        return self.uav_ids[drone_num - 1]

    def _path_csv(self, drone_num):
        return uav_path_csv(self._uav_id(drone_num))

    def _path_kml(self, drone_num):
        return uav_path_kml(self._uav_id(drone_num))

    def write_to_csv(self, data, num, is_bezier=None):
        if is_bezier is None:
            is_bezier = [False] * len(data)
        with open(self._path_csv(num), "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            for row, flag in zip(data, is_bezier):
                csv_writer.writerow(list(row) + [flag])

    def GridFormation(self):
        center_lat = self.center_latitude
        center_lon = self.center_longitude

        num_rectangles = self.num_of_drones
        grid_spacing = self.grid_space
        # Turn-around overshoot beyond each row end. A 180 deg turn needs ~2R
        # of lateral room, so scale this with the configured turn radius (kept
        # at least the original 250 m so small-radius behaviour is unchanged).
        meters_for_extended_lines = max(250.0, 2.2 * self.TURN_RADIUS)
        gap_between_rectangles = 50

        full_width, full_height = self.coverage_area, self.coverage_area

        total_gap_height = (num_rectangles - 1) * gap_between_rectangles
        available_height = full_height - total_gap_height
        rectangle_height = available_height / num_rectangles

        center_point = Point(center_lat, center_lon)

        csv_datas = []

        west_edge = distance(meters=full_width / 2).destination(center_point, 270)

        for i in range(num_rectangles):
            top_offset = (
                (i * rectangle_height) - (full_height / 2) + (rectangle_height / 2)
            )

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
            csv_datas.append(csv_data)

        # Grid points kept in memory only (self._grid_by_slot), keyed by
        # 1-based drone slot -- generate_bezier_curve() reads them straight
        # back out below; nothing else ever needs the raw grid once the
        # bezier-smoothed path has been produced, so it's never written to
        # disk (see mission_paths.py module docstring).
        for i in range(len(csv_datas)):
            points = []
            for waypoint in csv_datas[i]:
                x, y = geoToCart(self.origin, 500000, waypoint)
                points.append((x / 2, y / 2))
            self._grid_by_slot[i + 1] = points

    def generate_bezier_curve(self):
        for num in range(self.num_of_drones):
            waypoints = [list(point) for point in self._grid_by_slot.get(num + 1, [])]
            self.waypoints.extend(waypoints)

            result, is_bezier = generate_bezier_path(
                waypoints, self.SPEED, self.TURN_RATE, self.initial_heading
            )
            self.sample_points.extend(result)
            self.path.append(result)
            self.write_to_csv(result, num + 1, is_bezier)
            self.write_kml(result, num + 1)
        return self.path

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

    def plot_curve(self):
        for num in range(self.num_of_drones):
            predict_path = np.array(self.path[num])
            # sampled_points = np.array(self.sample_points)
            plt.figure(figsize=(8, 6))
            plt.plot(
                predict_path[:, 0],
                predict_path[:, 1],
                "r-",
                label="Predicted Path",
                linewidth=2,
            )
            plt.scatter(
                *zip(*self.waypoints),
                color="blue",
                s=100,
                label="Waypoints",
                marker="X",
            )

            #     plt.scatter(sampled_points[:, 0], sampled_points[:, 1], color='black', marker='o', s=40, label="Bézier Points")

            # # Annotate the sampled Bézier points with t-values
            #     for i, (x, y) in enumerate(sampled_points):
            #         plt.text(x, y, f'w', fontsize=10, verticalalignment='top', horizontalalignment='left')

            plt.xlabel("X Position (m)")
            plt.ylabel("Y Position (m)")
            plt.title("Aircraft Path Prediction with 40° Roll Limit")
            plt.legend()
            plt.grid()
            plt.axis("equal")

            # --- Ensure Plot Opens Correctly ---
            plt.show(block=True)  # Ensures the window stays open


"""
origin = [ 13.308039,  80.146629]
curve = BezierCurveMultiple(origin=origin,center_latitude=  13.372730,center_longitude=  80.238806,num_of_drones=5,grid_space=100,coverage_area=2000)
curve.GridFormation()
path = curve.generate_bezier_curve()
print(len(path))
curve.plot_curve()
"""
