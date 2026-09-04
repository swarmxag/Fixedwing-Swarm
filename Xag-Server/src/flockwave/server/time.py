import math
from typing import List

class TimeCalculation:
    def __init__(self, missions: List[tuple[float]] = [], speed: int = 18, loiter_radius: int = 200) -> None:
        self.missions = missions
        self.num_drones = len(missions)
        self.total_time_array = []
        self.loiter_radius = loiter_radius
        self.speed = speed
        self.calculate_total_time()

    def haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371e3  # Earth's radius in meters

        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  # Distance in meters

    def estimate_mission_time(self, waypoints: tuple[float]) -> float:
        """
        waypoints: List of tuples [(lat, lon), (lat, lon), ...]
        speed: Speed in m/s
        loiter_radius: Radius of the loiter circle in meters
        """
        total_distance = 0
        total_loiter_time = 0

        for i in range(len(waypoints) - 1):
            total_distance += self.haversine(*waypoints[i], *waypoints[i + 1])

        # Add loiter time for each waypoint except home
        for i in range(1, len(waypoints)):
            loiter_circumference = 2 * math.pi * self.loiter_radius
            total_loiter_time += loiter_circumference / self.speed

        total_time = (total_distance / self.speed) + total_loiter_time  # Time in seconds
        return total_time

    def calculate_total_time(self) -> None:
        for mission in self.missions:
            time_sec = self.estimate_mission_time(waypoints=mission)
            self.total_time_array.append(time_sec)

    def max_time(self) -> float:
        return round(max(self.total_time_array) / 60)

    def min_time(self) -> float:
        return min(self.total_time_array) / 60

    def get_avg_time(self) -> float:
        time_avg = sum(self.total_time_array)
        return time_avg / len(self.total_time_array) / 60
