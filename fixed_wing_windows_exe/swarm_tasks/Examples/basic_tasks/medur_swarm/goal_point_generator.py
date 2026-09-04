"""Goal-point generation for the swarm.

Two independent strategies live here:

1. ``generate_loiter_goal_points`` -- the "Automate Goals" strategy.
   The operator drops ONE goal point; this lays out one loiter CENTER per
   UAV, marching along a single bearing, spaced far enough apart that the
   loiter circles never overlap::

        goal (UAV1)      goal2 (UAV2)      goal3 (UAV3)
           O ......         O ......          O ......
          /   r   \\        /   r   \\         /   r   \\
          \\       /        \\       /         \\       /
           `.....'          `.....'           `.....'
           |<-- 2r + safety_margin -->|

   Each UAV then loiters around its own center at ``loiter_radius_m``.

2. ``destination_point`` -- shared spherical forward-geodesic helper
   (same formula as ``utils.generate_points``), reused by both this module
   and callers that need "point at bearing/distance from here".

The regeneration entry point is just calling ``generate_loiter_goal_points``
again with a new radius/bearing/margin: ``center_spacing`` is derived from
the radius, so a mid-flight radius change re-spaces every center and
re-sizes every circle. ``regenerate_loiter_goal_points`` is a named alias
for that, for call sites where "regenerate" reads clearer than "generate".

Pure module: no imports from ``medur_swarm.state`` or any live-vehicle
code, so it is safe to import from the dispatch loop and unit-test on its
own.
"""

import math

EARTH_RADIUS_M = 6371000.0

# Fallbacks used when the GCS payload omits these (older client, or the
# field was left blank). Kept in sync with SwarmPanel.jsx's defaults.
DEFAULT_BEARING_DEG = 90.0
DEFAULT_SAFETY_MARGIN_M = 50.0


def destination_point(lat, lon, bearing_deg, distance_m):
    """Lat/lon reached by travelling ``distance_m`` from ``(lat, lon)``
    along the great circle at compass bearing ``bearing_deg``. Returns
    ``(lat, lon)`` in degrees."""

    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing = math.radians(bearing_deg)

    angular_distance = distance_m / EARTH_RADIUS_M

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


def loiter_center_spacing(loiter_radius_m, safety_margin_m=DEFAULT_SAFETY_MARGIN_M):
    """Distance between two consecutive loiter centers so their circles
    stay clear of each other::

           radius       radius
             r            r
             O------------O
           minimum gap = r + r  (+ safety_margin_m of clearance)
    """
    return 2.0 * loiter_radius_m + safety_margin_m


def generate_loiter_goal_points(
    goal_lat,
    goal_lon,
    num_uavs,
    loiter_radius_m,
    bearing_deg=DEFAULT_BEARING_DEG,
    safety_margin_m=DEFAULT_SAFETY_MARGIN_M,
):
    """Generate one loiter-center goal for each UAV.

    UAV 1 sits on the given goal point. UAV 2..N are placed sequentially
    along ``bearing_deg``, ``loiter_center_spacing`` apart.

    Example (radius 600 m, margin 50 m -> spacing 1250 m, bearing 90)::

        UAV 1 -> 0 m       UAV 2 -> 1250 m    UAV 3 -> 2500 m
        UAV 4 -> 3750 m    UAV 5 -> 5000 m

    Returns a list of dicts, one per UAV (index-aligned with the selected
    UAV list): ``uav_id`` (1-based), ``goal_lat``, ``goal_lon``,
    ``loiter_radius_m``, ``distance_from_center_m``, ``bearing_deg``.
    """

    if num_uavs < 1:
        raise ValueError("num_uavs must be >= 1")
    if loiter_radius_m <= 0:
        raise ValueError("loiter_radius_m must be > 0")

    bearing_deg = float(bearing_deg)
    safety_margin_m = float(safety_margin_m)
    center_spacing = loiter_center_spacing(loiter_radius_m, safety_margin_m)

    goal_points = []
    for i in range(num_uavs):
        if i == 0:
            distance_from_goal = 0.0
            lat, lon = goal_lat, goal_lon
        else:
            distance_from_goal = i * center_spacing
            lat, lon = destination_point(
                goal_lat, goal_lon, bearing_deg, distance_from_goal
            )

        goal_points.append(
            {
                "uav_id": i + 1,
                "goal_lat": lat,
                "goal_lon": lon,
                "loiter_radius_m": loiter_radius_m,
                "distance_from_center_m": distance_from_goal,
                "bearing_deg": bearing_deg,
            }
        )

    return goal_points


# "Regenerate" is the same computation with new inputs -- named separately
# only so mid-flight radius/bearing changes read clearly at the call site.
regenerate_loiter_goal_points = generate_loiter_goal_points


def loiter_goal_latlon_list(
    goal_lat,
    goal_lon,
    num_uavs,
    loiter_radius_m,
    bearing_deg=DEFAULT_BEARING_DEG,
    safety_margin_m=DEFAULT_SAFETY_MARGIN_M,
):
    """Same as ``generate_loiter_goal_points`` but returns a plain
    ``[(lat, lon), ...]`` list -- the shape the swarm task assigner wants
    before converting to the local sim frame."""
    return [
        (p["goal_lat"], p["goal_lon"])
        for p in generate_loiter_goal_points(
            goal_lat, goal_lon, num_uavs, loiter_radius_m, bearing_deg, safety_margin_m
        )
    ]


if __name__ == "__main__":
    demo = generate_loiter_goal_points(
        goal_lat=26.96256333175016,
        goal_lon=70.95419682498871,
        num_uavs=5,
        loiter_radius_m=600,
        bearing_deg=90,
        safety_margin_m=50,
    )
    for point in demo:
        print(
            f"UAV {point['uav_id']}: "
            f"{point['goal_lat']:.8f}, {point['goal_lon']:.8f} | "
            f"{point['distance_from_center_m']} m"
        )
