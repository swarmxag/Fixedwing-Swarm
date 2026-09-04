from shapely.geometry import Point, Polygon
from shapely.prepared import prep
import math


# -----------------------------
# Base fence class (geometry owner)
# -----------------------------
class Fence:
    def __init__(self, fence_coords, label=None):
        """
        :param fence_coords: List of (lat, lon) tuples
        """
        # Convert (lat, lon) -> (lon, lat) for Shapely
        polygon = Polygon([(lon, lat) for lat, lon in fence_coords])

        if not polygon.is_valid:
            raise ValueError(f"Invalid fence polygon: {label or 'fence'}")

        self.polygon = prep(polygon)
        self.label = label or "fence"

    def contains_point(self, lat, lon):
        """
        Check if a point is inside or on the boundary of the fence.
        """
        return self.polygon.covers(Point(lon, lat))


# -----------------------------
# Goal validator (simple point checks)
# -----------------------------
class GoalFenceValidator:
    def __init__(self, fence: Fence):
        self.fence = fence

    def is_point_inside(self, point, obstacles=None):
        """
        Check if a single point is inside the fence and not inside any obstacle.
        Returns True, False, or 'in_obstacle'.
        """
        lat, lon = point

        if not self.fence.contains_point(lat, lon):
            return False

        if obstacles:
            p = Point(lon, lat)
            if any(obs.contains(p) for obs in obstacles):
                return 'in_obstacle'

        return True

    def are_points_all_inside(self, points):
        """
        Check if all points are inside the fence.
        """
        return all(self.is_point_inside(p) for p in points)


# -----------------------------
# Search / coverage validator (area-aware)
# -----------------------------
class SearchAreaValidator:
    def __init__(self, fence: Fence):
        self.fence = fence

    def _offset_point(self, lat, lon, dx_m, dy_m):
        """
        Offset a lat/lon point by meters.
        dx_m: east (+) / west (-)
        dy_m: north (+) / south (-)
        """
        meters_per_deg_lat = 111_320
        meters_per_deg_lon = meters_per_deg_lat * math.cos(math.radians(lat))

        new_lat = lat + (dy_m / meters_per_deg_lat)
        new_lon = lon + (dx_m / meters_per_deg_lon)

        return new_lat, new_lon

    def is_point_with_coverage_inside(self, point, coverage_area_m):
        """
        Check if a point and its coverage area (diameter in meters) are fully inside the fence.
        """
        lat, lon = point
        radius = coverage_area_m / 2

        # Points to check: center + top/bottom/left/right edges
        check_points = [
            (lat, lon),  # center
            self._offset_point(lat, lon, 0, radius),  # top
            self._offset_point(lat, lon, 0, -radius),  # bottom
            self._offset_point(lat, lon, radius, 0),  # right
            self._offset_point(lat, lon, -radius, 0),  # left
        ]

        return all(self.fence.contains_point(p[0], p[1]) for p in check_points)

    def are_points_with_coverage_inside(self, points, coverage_diameter_m):
        """
        Check if ALL points (with coverage area) are fully inside the fence.

        :param points: list of (lat, lon)
        :param coverage_diameter_m: coverage diameter in meters
        :return: True if all points are valid
        """
        return all(
            self.is_point_with_coverage_inside(p, coverage_diameter_m) for p in points
        )
