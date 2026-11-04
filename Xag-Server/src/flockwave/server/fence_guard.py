"""Server-side geofence gate for operator commands.

The drawn outer fence (lat/lon) is remembered whenever a fence is processed.
Goal, auto-goal, search, split and specific-split commands are checked against
it BEFORE anything is sent to the swarm computer; a command outside it is not
sent at all and the GUI receives "out_of_boundary|Command not sent: <reason>".
The swarm computer keeps its own check as a second layer.

Every check returns None when the command is inside (or when no fence has been
drawn yet -- those commands are already refused as "origin_not_set"), or the
refusal string to return to the GUI.
"""

import math

from .geofence_validator import Fence

REFUSED = "out_of_boundary"
EARTH_RADIUS_M = 6371000.0
# Extra room around a loiter circle (wind, tracking error). The swarm computer
# uses the same value (config.GEOFENCE_LOITER_MARGIN_M).
LOITER_MARGIN_M = 50.0
_CIRCLE_SAMPLES = 36  # one test point every 10 degrees

_outer = None  # Fence of the last drawn outer boundary


def set_outer_fence(latlon_points):
    """latlon_points: the outer fence as [[lat, lon], ...]."""
    global _outer
    try:
        _outer = Fence([(float(p[0]), float(p[1])) for p in latlon_points], label="outer")
    except (ValueError, TypeError, IndexError) as e:
        print("[fence-guard] could not use the drawn fence:", e)
        _outer = None


def refusal(reason):
    return "%s|Command not sent: %s" % (REFUSED, reason)


def _offset(lat, lon, east_m, north_m):
    lat2 = lat + north_m / 111320.0
    lon2 = lon + east_m / (111320.0 * max(math.cos(math.radians(lat)), 1e-6))
    return lat2, lon2


def _destination(lat, lon, bearing_deg, distance_m):
    """Same great-circle step the swarm uses to lay out auto-goal centres."""
    lat1, lon1, brg = math.radians(lat), math.radians(lon), math.radians(bearing_deg)
    d = distance_m / EARTH_RADIUS_M
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(brg))
    lon2 = lon1 + math.atan2(
        math.sin(brg) * math.sin(d) * math.cos(lat1), math.cos(d) - math.sin(lat1) * math.sin(lat2)
    )
    return math.degrees(lat2), math.degrees(lon2)


def check_points(latlon_points, what):
    """Each point [lat, lon] must be inside the fence."""
    if _outer is None:
        return None
    for k, p in enumerate(latlon_points):
        lat, lon = float(p[0]), float(p[1])
        if not _outer.contains_point(lat, lon):
            return refusal("%s point %d is outside the geofence" % (what, k + 1))
    return None


def check_loiter(center_latlons, radius_m, what):
    """A fixed-wing orbits its final point; the whole circle (radius_m plus
    LOITER_MARGIN_M) around each centre [lat, lon] must be inside the fence."""
    if _outer is None:
        return None
    radius = abs(_num(radius_m, 0.0))
    reach = radius + LOITER_MARGIN_M
    for k, p in enumerate(center_latlons):
        lat, lon = float(p[0]), float(p[1])
        for s in range(_CIRCLE_SAMPLES):
            a = 2.0 * math.pi * s / _CIRCLE_SAMPLES
            if not _outer.contains_point(*_offset(lat, lon, reach * math.sin(a), reach * math.cos(a))):
                return refusal(
                    "%s point %d is too close to the geofence -- the loiter circle "
                    "(%.0f m + %.0f m margin) would leave it"
                    % (what, k + 1, radius, LOITER_MARGIN_M)
                )
    return None


def check_areas(center_latlons, coverage_m, what):
    """The coverage square (side `coverage_m`) around each centre must be inside:
    centre, four corners and four edge midpoints are tested."""
    if _outer is None:
        return None
    try:
        half = float(coverage_m) / 2.0
    except (TypeError, ValueError):
        half = 0.0
    for k, p in enumerate(center_latlons):
        lat, lon = float(p[0]), float(p[1])
        for east, north in [(0, 0), (half, half), (half, -half), (-half, half), (-half, -half),
                            (half, 0), (-half, 0), (0, half), (0, -half)]:
            if not _outer.contains_point(*_offset(lat, lon, east, north)):
                return refusal("%s area %d is outside the geofence" % (what, k + 1))
    return None


def _num(value, fallback):
    """Same fallbacks autogoal_socket applies (None / NaN / text -> default)."""
    try:
        value = float(value)
        return fallback if value != value else value
    except (TypeError, ValueError):
        return fallback


def check_autogoal(gui_coords, num_uavs, radius_m, bearing_deg, safety_margin_m):
    """Every loiter centre the swarm will lay out (one per UAV, along the bearing,
    2*radius + margin apart) must be inside the fence, and so must the loiter
    circle around it. gui_coords is the GUI's [[lon, lat]] (the operator's
    single point)."""
    if _outer is None:
        return None
    try:
        lat, lon = float(gui_coords[0][1]), float(gui_coords[0][0])
    except (TypeError, ValueError, IndexError, KeyError):
        return None  # malformed: leave it to the existing handler, as before
    spacing = 2.0 * _num(radius_m, 0.0) + _num(safety_margin_m, 50.0)
    bearing = _num(bearing_deg, 90.0)
    centres = [
        (lat, lon) if i == 0 else _destination(lat, lon, bearing, i * spacing)
        for i in range(max(1, int(num_uavs)))
    ]
    return check_points(centres, "auto-goal") or check_loiter(centres, radius_m, "auto-goal")
