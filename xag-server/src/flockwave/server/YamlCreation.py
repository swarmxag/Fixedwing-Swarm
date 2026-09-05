# import math
# from scipy import interpolate
# import os, sys


# class FenceToYAML:
#     def __init__(
#         self,
#         fence_coordinates,
#         labels,
#         endDistance=50000000,
#         buffer_distance=10,
#         origin_shift_m=0,
#     ):
#         self.fence_coordinates = fence_coordinates
#         self.labels = labels
#         self.endDistance = endDistance
#         self.buffer_distance = buffer_distance
#         self.origin_shift_m = origin_shift_m
#         self.origin = None
#         self.obstacles_list = []
#         print(fence_coordinates)

#     # ----------------------------------------------------
#     # Compute destination lat/lon given distance and bearing
#     # ----------------------------------------------------
#     @staticmethod
#     def destination_location(lat, lon, distance_m, bearing_deg):
#         R = 6371000.0  # Earth radius in meters
#         lat1 = math.radians(lat)
#         lon1 = math.radians(lon)
#         bearing = math.radians(bearing_deg)

#         lat2 = math.asin(
#             math.sin(lat1) * math.cos(distance_m / R)
#             + math.cos(lat1) * math.sin(distance_m / R) * math.cos(bearing)
#         )
#         lon2 = lon1 + math.atan2(
#             math.sin(bearing) * math.sin(distance_m / R) * math.cos(lat1),
#             math.cos(distance_m / R) - math.sin(lat1) * math.sin(lat2),
#         )

#         return (math.degrees(lat2), math.degrees(lon2))

#     def cartToGeo(self, cartLocation):
#         # The initial point of rectangle in (x,y) is (0,0) so considering the current
#         # location as origin and retreiving the latitude and longitude from the GPS
#         # origin = (12.948048, 80.139742) Format
#         endDistance = self.endDistance
#         origin = self.origin

#         # Calculating the hypot end point for interpolating the latitudes and longitudes
#         rEndDistance = math.sqrt(2 * (endDistance**2))

#         # The bearing for the hypot angle is 45 degrees considering coverage area as square
#         bearing = 45

#         # Determining the Latitude and Longitude of Middle point of the sqaure area
#         # and hypot end point of square area for interpolating latitude and longitude
#         lEnd, rEnd = self.destination_location(
#             origin[0], origin[1], rEndDistance, 180 + bearing
#         ), self.destination_location(origin[0], origin[1], rEndDistance, bearing)

#         # Array of (x,y)
#         x_cart, y_cart = [-endDistance, 0, endDistance], [-endDistance, 0, endDistance]

#         # Array of (latitude, longitude)
#         x_lon, y_lat = [lEnd[1], origin[1], rEnd[1]], [lEnd[0], origin[0], rEnd[0]]

#         # Latitude interpolation function
#         f_lat = interpolate.interp1d(y_cart, y_lat)

#         # Longitude interpolation function
#         f_lon = interpolate.interp1d(x_cart, x_lon)

#         # Converting (latitude, longitude) to (x,y) using interpolation function
#         lat, lon = f_lat(cartLocation[1]), f_lon(cartLocation[0])
#         return (lat, lon)

#     def convert_to_latlon_array(self, points):
#         lat_lons = []
#         for i in range(len(points)):
#             for j in range(len(points[i])):
#                 print(i, j)
#                 x, y = self.cartToGeo((points[i][j][0] * 2, points[i][j][1] * 2))
#                 lat_lons.append([x, y])
#         # for boundary in points:
#         #     for point in boundary:
#         #         res = self.cartToGeo(point)
#         #         lat_lons.append(res)
#         print("lat_lons", lat_lons)

#     # ----------------------------------------------------
#     # Convert geolocation to cartesian x, y
#     # ----------------------------------------------------
#     def geoToCart(self, geoLocation):
#         endDistance = self.endDistance
#         origin = self.origin

#         rEndDistance = math.sqrt(2 * (endDistance**2))
#         bearing = 45

#         lEnd = self.destination_location(
#             origin[0], origin[1], rEndDistance, 180 + bearing
#         )
#         rEnd = self.destination_location(origin[0], origin[1], rEndDistance, bearing)

#         x_cart, y_cart = [-endDistance, 0, endDistance], [-endDistance, 0, endDistance]
#         x_lon, y_lat = [lEnd[1], origin[1], rEnd[1]], [lEnd[0], origin[0], rEnd[0]]

#         f_lat = interpolate.interp1d(y_lat, y_cart)
#         f_lon = interpolate.interp1d(x_lon, x_cart)

#         y, x = f_lat(geoLocation[0]), f_lon(geoLocation[1])
#         return float(x), float(y)

#     # ----------------------------------------------------
#     # Generate an outward buffer around polygon
#     # ----------------------------------------------------
#     def generate_outer_simple(self, inner_polygon, offset_m=None):
#         if offset_m is None:
#             offset_m = self.buffer_distance
#         lat_c = sum(p[0] for p in inner_polygon) / len(inner_polygon)
#         lon_c = sum(p[1] for p in inner_polygon) / len(inner_polygon)
#         outer_polygon = []
#         for lat, lon in inner_polygon:
#             d_lat = lat - lat_c
#             d_lon = lon - lon_c
#             length = math.sqrt(d_lat**2 + d_lon**2)
#             if length == 0:
#                 length = 1
#             scale = offset_m / 111320
#             new_lat = lat + (d_lat / length) * scale
#             new_lon = lon + (d_lon / length) * scale
#             outer_polygon.append([new_lat, new_lon])
#         return outer_polygon

#     # ----------------------------------------------------
#     # Compute origin shifted southwest
#     # ----------------------------------------------------
#     def compute_origin(self):
#         outer_index = self.labels.index("outer")
#         outer_fence = self.fence_coordinates[outer_index]

#         min_lat = min(lat for lat, _ in outer_fence)
#         min_lon = min(lon for _, lon in outer_fence)

#         lat_shift = self.origin_shift_m / 111320
#         lon_shift = self.origin_shift_m / (111320 * math.cos(math.radians(min_lat)))
#         self.origin = (min_lat - lat_shift, min_lon - lon_shift)
#         print(f"✅ Origin shifted {self.origin_shift_m} m southwest: {self.origin}")
#         return self.origin

#     # ----------------------------------------------------
#     # Convert polygon points to XY
#     # ----------------------------------------------------
#     def convert_to_xy_array(self, name, points, scale_factor=2):
#         xy_points = []
#         for lat, lon in points:
#             x, y = self.geoToCart((lat, lon))
#             xy_points.append([x / scale_factor, y / scale_factor])
#             xy_points.append([(x + 10) / scale_factor, (y + 10) / scale_factor])
#         # print(f"\n{name} XY Points:")
#         # print(xy_points)
#         x, y = self.geoToCart((points[0][0], points[0][1]))
#         xy_points.append([x / scale_factor, y / scale_factor])
#         xy_points[2], xy_points[3] = xy_points[3], xy_points[2]
#         return xy_points

#     # ----------------------------------------------------
#     # Process all fences and generate obstacles list
#     # ----------------------------------------------------
#     def process_fences(self):
#         print("Outerrrrrrrrrrrr")
#         if self.origin is None:
#             self.compute_origin()

#         outer_index = self.labels.index("outer")
#         outer_fence = self.fence_coordinates[outer_index]
#         outer_polygon = self.generate_outer_simple(outer_fence)
#         print("Outer Polygon", outer_polygon)
#         inner_polygon = outer_fence
#         all_points = inner_polygon + outer_polygon

#         # Define boundaries
#         top_boundary = [
#             all_points[0],
#             all_points[len(inner_polygon)],
#             all_points[len(inner_polygon) + 1],
#             all_points[1],
#         ]
#         right_boundary = [
#             all_points[1],
#             all_points[len(inner_polygon) + 1],
#             all_points[len(inner_polygon) + 2],
#             all_points[2],
#         ]
#         bottom_boundary = [
#             all_points[2],
#             all_points[len(inner_polygon) + 2],
#             all_points[len(inner_polygon) + 3],
#             all_points[3],
#         ]
#         left_boundary = [
#             all_points[3],
#             all_points[len(inner_polygon) + 3],
#             all_points[len(inner_polygon)],
#             all_points[0],
#         ]
#         print(top_boundary, right_boundary, bottom_boundary, left_boundary)
#         # Convert boundaries to XY
#         self.obstacles_list = [
#             self.convert_to_xy_array("Right Boundary", right_boundary),
#             self.convert_to_xy_array("Bottom Boundary", bottom_boundary),
#             self.convert_to_xy_array("Left Boundary", left_boundary),
#             self.convert_to_xy_array("Top Boundary", top_boundary),
#         ]

#         boundaries = []
#         for i in range(1, len(outer_polygon)):
#             boundaries.append([outer_polygon[i], outer_polygon[i - 1]])
#         boundaries.append([outer_polygon[-1], outer_polygon[0]])
#         self.obstacles_list = []
#         for index, point in enumerate(boundaries):
#             result = self.convert_to_xy_array("boundary", point)
#             self.obstacles_list.append(result)
#         print("Final Obstacle Lists", self.obstacles_list)
#         self.convert_to_latlon_array(self.obstacles_list)

#         # Convert inner fences
#         for i, label in enumerate(self.labels):
#             if label != "outer":
#                 name = f"Fence_{label}_{i}"
#                 boundaries = []
#                 for j in range(1, len(self.fence_coordinates[i])):
#                     boundaries.append(
#                         [self.fence_coordinates[i][j], self.fence_coordinates[i][j - 1]]
#                     )
#                 boundaries.append(
#                     [self.fence_coordinates[i][-1], self.fence_coordinates[i][0]]
#                 )
#                 print("Boundaries", boundaries)
#                 for index, point in enumerate(boundaries):
#                     # result = self.convert_to_xy_array("boundary", point)
#                     # self.obstacles_list.append(result)
#                     inner_xy = self.convert_to_xy_array(name, point)
#                     self.obstacles_list.append(inner_xy)

#         return self.obstacles_list

#     # ----------------------------------------------------
#     # Compute map size and shift to positive quadrant
#     # ----------------------------------------------------
#     def compute_size_and_shift(self, padding=1):
#         all_points = [p for boundary in self.obstacles_list for p in boundary]
#         xs = [p[0] for p in all_points]
#         ys = [p[1] for p in all_points]

#         min_x, max_x = min(xs), max(xs)
#         min_y, max_y = min(ys), max(ys)

#         size_x = int(round(max_x - min_x + padding))
#         size_y = int(round(max_y - min_y + padding))

#         shifted_obstacles_list = []
#         for boundary in self.obstacles_list:
#             shifted_boundary = [[x - min_x / 2, y - min_y / 2] for x, y in boundary]
#             shifted_obstacles_list.append(shifted_boundary)

#         return size_x, size_y, shifted_obstacles_list

#     @staticmethod
#     def get_documents_folder():
#         documents = os.path.join(os.path.expanduser("~"), "Documents")
#         swarm_folder = os.path.join(documents, "swarm_env")
#         os.makedirs(swarm_folder, exist_ok=True)
#         return swarm_folder

#     # ----------------------------------------------------
#     # Generate YAML file
#     # ----------------------------------------------------
#     def generate_yaml(self, filename=None):
#         # import os

#         # # If user does not give a base_path → use AppData/Roaming
#         # if base_path is None:
#         #     base_path = os.path.join(os.environ["APPDATA"])

#         # # Create swarm_env folder inside base_path
#         # swarm_folder = os.path.join(base_path, "swarm_env")
#         # os.makedirs(swarm_folder, exist_ok=True)

#         # # Final YAML file path
#         # filename = os.path.join(swarm_folder, "rectangles.yaml")

#         # # Create or overwrite YAML
#         # if not os.path.exists(filename):
#         #     open(filename, "w").close()
#         # If filename not provided, save to Documents/swarm_env
#         if filename is None:
#             base_folder = self.get_documents_folder()
#             filename = os.path.join(base_folder, "rectangles.yaml")

#         print(f"YAML file will be saved to: {filename}")
#         size_x, size_y, shifted_obstacles_list = self.compute_size_and_shift()
#         yaml_lines = []
#         yaml_lines.append("name: Rectangles")
#         yaml_lines.append("size:")
#         yaml_lines.append(f"  x: {size_x}")
#         yaml_lines.append(f"  y: {size_y}")
#         yaml_lines.append("\nobstacles:")

#         for boundary in shifted_obstacles_list:
#             formatted_points = ",".join([f"[{x:.2f},{y:.2f}]" for x, y in boundary])
#             yaml_lines.append(f"  - [{formatted_points}]")

#         yaml_lines.append(f"origin: {self.origin}")
#         yaml_text = "\n".join(yaml_lines)
#         with open(filename, "w") as f:
#             f.write(yaml_text)

#             print("✅ YAML generated successfully!")
#         return self.origin, yaml_text


# # fence_yaml = FenceToYAML(
# #     fence_coordinates=[
# #         [
# #             [12.64574179013492, 78.95099201286281],
# #             [12.786899185083527, 79.05483920723651],
# #             [12.77604374599403, 79.09563634457626],
# #             [12.624018381981145, 79.03258621680206],
# #         ],
# #         [
# #             [12.602293129009254, 79.2514071361368],
# #             [12.537106054529474, 79.17723054851551],
# #             [12.493639019394095, 79.25511597966594],
# #         ],
# #         [
# #             [13.079819155564664, 78.9954979229914],
# #             [12.504506464230573, 78.79522115056197],
# #             [12.290696013318666, 79.38863392227263],
# #             [12.77604374599403, 79.42572221608327],
# #         ],
# #     ],
# #     labels=[None, None, "outer"],
# # )
# # fence_yaml.process_fences()  # generate XY points
# # yaml_text = fence_yaml.generate_yaml("rectangles.yaml")
# # print(yaml_text)


import math
from scipy import interpolate
import os, sys


class FenceToYAML:
    def __init__(
        self,
        fence_coordinates,
        labels,
        endDistance=500000,
        buffer_distance=10,
        origin_shift_m=0,
    ):
        # Ensure coordinates are floats
        self.fence_coordinates = [
            [[float(lat), float(lon)] for lat, lon in fence]
            for fence in fence_coordinates
        ]
        self.labels = labels
        self.endDistance = endDistance
        self.buffer_distance = buffer_distance
        self.origin_shift_m = origin_shift_m
        self.origin = None
        self.obstacles_list = []

    # -------------------------
    # Destination lat/lon
    # -------------------------
    @staticmethod
    def destination_location(lat, lon, distance_m, bearing_deg):
        R = 6371000.0
        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        bearing = math.radians(bearing_deg)

        lat2 = math.asin(
            math.sin(lat1) * math.cos(distance_m / R)
            + math.cos(lat1) * math.sin(distance_m / R) * math.cos(bearing)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(distance_m / R) * math.cos(lat1),
            math.cos(distance_m / R) - math.sin(lat1) * math.sin(lat2),
        )
        return (math.degrees(lat2), math.degrees(lon2))

    # -------------------------
    # Geo → Cartesian
    # -------------------------
    def geoToCart(self, geoLocation):
        rEndDistance = math.sqrt(2 * (self.endDistance**2))
        bearing = 45
        lEnd = self.destination_location(
            self.origin[0], self.origin[1], rEndDistance, 180 + bearing
        )
        rEnd = self.destination_location(
            self.origin[0], self.origin[1], rEndDistance, bearing
        )

        x_cart, y_cart = [-self.endDistance, 0, self.endDistance], [
            -self.endDistance,
            0,
            self.endDistance,
        ]
        x_lon, y_lat = [lEnd[1], self.origin[1], rEnd[1]], [
            lEnd[0],
            self.origin[0],
            rEnd[0],
        ]

        f_lat = interpolate.interp1d(y_lat, y_cart)
        f_lon = interpolate.interp1d(x_lon, x_cart)

        y, x = f_lat(geoLocation[0]), f_lon(geoLocation[1])
        return float(x), float(y)

    # -------------------------
    # Generate buffer
    # -------------------------
    def generate_outer_simple(self, inner_polygon, offset_m=None):
        if offset_m is None:
            offset_m = self.buffer_distance
        lat_c = sum(p[0] for p in inner_polygon) / len(inner_polygon)
        lon_c = sum(p[1] for p in inner_polygon) / len(inner_polygon)
        outer_polygon = []
        for lat, lon in inner_polygon:
            d_lat = lat - lat_c
            d_lon = lon - lon_c
            length = math.sqrt(d_lat**2 + d_lon**2) or 1
            scale = offset_m / 111320
            outer_polygon.append(
                [lat + (d_lat / length) * scale, lon + (d_lon / length) * scale]
            )
        return outer_polygon

    # -------------------------
    # Compute origin
    # -------------------------
    def compute_origin(self):
        outer_index = self.labels.index("outer")
        outer_fence = self.fence_coordinates[outer_index]
        min_lat = min(lat for lat, _ in outer_fence)
        min_lon = min(lon for _, lon in outer_fence)
        lat_shift = self.origin_shift_m / 111320
        lon_shift = self.origin_shift_m / (111320 * math.cos(math.radians(min_lat)))
        self.origin = (min_lat - lat_shift, min_lon - lon_shift)
        return self.origin

    # -------------------------
    # Convert polygon → XY
    # -------------------------
    def convert_to_xy_array(self, points, scale_factor=2):
        return [
            [x / scale_factor, y / scale_factor]
            for lat, lon in points
            for x, y in [self.geoToCart((lat, lon))]
        ]

    # -------------------------
    # Process fences + auto-update YAML
    # -------------------------
    # def process_fences(self):
    #     if self.origin is None:
    #         self.compute_origin()

    #     outer_index = self.labels.index("outer")
    #     outer_fence = self.fence_coordinates[outer_index]
    #     outer_polygon = self.generate_outer_simple(outer_fence)

    #     inner_polygon = outer_fence
    #     all_points = inner_polygon + outer_polygon

    #     # Boundaries
    #     top_boundary = [
    #         all_points[0],
    #         all_points[len(inner_polygon)],
    #         all_points[len(inner_polygon) + 1],
    #         all_points[1],
    #     ]
    #     right_boundary = [
    #         all_points[1],
    #         all_points[len(inner_polygon) + 1],
    #         all_points[len(inner_polygon) + 2],
    #         all_points[2],
    #     ]
    #     bottom_boundary = [
    #         all_points[2],
    #         all_points[len(inner_polygon) + 2],
    #         all_points[len(inner_polygon) + 3],
    #         all_points[3],
    #     ]
    #     left_boundary = [
    #         all_points[3],
    #         all_points[len(inner_polygon) + 3],
    #         all_points[len(inner_polygon)],
    #         all_points[0],
    #     ]

    #     self.obstacles_list = [
    #         self.convert_to_xy_array(right_boundary),
    #         self.convert_to_xy_array(bottom_boundary),
    #         self.convert_to_xy_array(left_boundary),
    #         self.convert_to_xy_array(top_boundary),
    #     ]

    #     # Inner fences
    #     for i, label in enumerate(self.labels):
    #         if label != "outer":
    #             self.obstacles_list.append(
    #                 self.convert_to_xy_array(self.fence_coordinates[i])
    #             )

    #     # Update YAML automatically
    #     self.generate_yaml()
    #     return self.obstacles_list

    def process_fences(self):
        if self.origin is None:
            self.compute_origin()

        outer_index = self.labels.index("outer")
        outer_fence = self.fence_coordinates[outer_index]
        outer_polygon = self.generate_outer_simple(outer_fence)

        inner_polygon = outer_fence
        n = len(inner_polygon)  # Works for any N, not just 4

        self.obstacles_list = []

        # Generate N boundary wall quads, one per edge
        for i in range(n):
            next_i = (i + 1) % n  # Wraps around: last → first

            wall = [
                inner_polygon[i],  # Inner edge start
                inner_polygon[next_i],  # Inner edge end
                outer_polygon[next_i],  # Outer edge end
                outer_polygon[i],  # Outer edge start
            ]
            self.obstacles_list.append(self.convert_to_xy_array(wall))

        # Inner fences (NFZ, restricted zones, etc.)
        for i, label in enumerate(self.labels):
            if label != "outer":
                self.obstacles_list.append(
                    self.convert_to_xy_array(self.fence_coordinates[i])
                )

        self.generate_yaml()
        return self.obstacles_list

    # -------------------------
    # Compute size & shift
    # -------------------------
    def compute_size_and_shift(self, padding=1):
        all_points = [p for boundary in self.obstacles_list for p in boundary]
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        size_x = int(round(max_x - min_x + padding))
        size_y = int(round(max_y - min_y + padding))
        shifted_obstacles_list = [
            [[x - min_x / 2, y - min_y / 2] for x, y in boundary]
            for boundary in self.obstacles_list
        ]
        return size_x, size_y, shifted_obstacles_list

    @staticmethod
    def get_documents_folder():
        swarm_folder = os.path.join(os.path.expanduser("~"), "Documents", "swarm_env")
        os.makedirs(swarm_folder, exist_ok=True)
        return swarm_folder

    # -------------------------
    # Generate YAML
    # -------------------------
    def generate_yaml(self, filename=None):
        if filename is None:
            filename = os.path.join(self.get_documents_folder(), "rectangles.yaml")

        size_x, size_y, shifted_obstacles_list = self.compute_size_and_shift()
        yaml_lines = [
            "name: Rectangles",
            "size:",
            f"  x: {size_x}",
            f"  y: {size_y}",
            "",
            "obstacles:",
        ]
        for boundary in shifted_obstacles_list:
            formatted = ",".join([f"[{x:.2f},{y:.2f}]" for x, y in boundary])
            yaml_lines.append(f"  - [{formatted}]")
        yaml_lines.append(f"origin: {self.origin}")
        yaml_text = "\n".join(yaml_lines)

        with open(filename, "w") as f:
            f.write(yaml_text)
        print(f"✅ YAML updated at: {filename}")
        return self.origin, yaml_text
