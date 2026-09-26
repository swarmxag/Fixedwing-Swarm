"""Diagnostic terrain sampling under an 'autogoal' loiter circle.

Read-only, print-only, backend-log-only: samples SRTM terrain elevation
at points spread across a UAV's loiter circle (not just the center) and
logs the highest elevation found, using the existing
terrain_data.TerrainManager. It never changes goal geometry, altitude,
or vehicle commands, and it never blocks a mission -- any failure here is
caught and logged, not raised.

Deliberately kept separate from goal_point_generator.py (geometry) and
tasks/goal.py (dispatch) so vertical clearance enforcement and frontend
notifications can be layered on later without touching this diagnostic.

Called from tasks/goal.py's _apply_autogoal, which is shared by the
'autogoal' foreground handler, the concurrent 'autogoal' handler, and
regenerate_autogoal (on-board loiter-radius changes) -- i.e. every path
that (re)establishes the per-UAV loiter circles for "Automate Goals".
"""

import math
from pathlib import Path

from medur_swarm.terrain_data import TerrainManager

EARTH_RADIUS_M = 6371000.0

# Grid spacing used to sample inside the loiter circle. SRTM1 tiles are
# ~30 m/pixel at the equator, so this is close to native resolution
# without hammering the same pixel repeatedly.
SAMPLE_SPACING_M = 20.0

# Same tiles directory the SRTM .hgt files are cached/committed under
# (medur_swarm/terrain/*.hgt), resolved relative to this file so it works
# regardless of where the repo is checked out.
_TERRAIN_DIR = Path(__file__).resolve().parent / "terrain"

_terrain_manager = TerrainManager(str(_TERRAIN_DIR))


def _offset_latlon(lat, lon, north_m, east_m):
    """(lat, lon) shifted by north_m/east_m metres. Flat-earth local
    approximation -- fine at loiter-circle scale (hundreds of metres)."""
    lat_rad = math.radians(lat)
    dlat_deg = math.degrees(north_m / EARTH_RADIUS_M)
    dlon_deg = math.degrees(east_m / (EARTH_RADIUS_M * math.cos(lat_rad)))
    return lat + dlat_deg, lon + dlon_deg


def check_loiter_circle_terrain(goal_lat, goal_lon, loiter_radius_m, label=None):
    """Sample terrain elevation across the loiter circle centered on
    (goal_lat, goal_lon) with radius loiter_radius_m.

    Diagnostic-verification mode: prints one [TERRAIN SAMPLE] block per
    sample point (valid or missing), a [TERRAIN CHECK] ... SUMMARY block,
    and a [HIGHEST TERRAIN] block naming exactly which sample produced the
    reported max -- enough to manually recompute/verify the result from
    the log alone. Sampling grid, spacing, coordinate conversion, and the
    TerrainManager lookup itself are unchanged; this only adds logging
    around them.

    Returns the summary dict for callers that want it, but nothing
    currently acts on the return value.
    """
    if loiter_radius_m is None or loiter_radius_m <= 0:
        print("[TERRAIN CHECK] skipped -- invalid loiter radius", loiter_radius_m)
        return None

    tag = f" {label}" if label else ""

    step = SAMPLE_SPACING_M
    half_steps = max(1, int(math.ceil(loiter_radius_m / step)))

    samples_checked = 0
    missing_samples = 0
    highest_elevation_m = None
    highest_lat = None
    highest_lon = None
    highest_north_m = None
    highest_east_m = None
    highest_sample_number = None

    for i in range(-half_steps, half_steps + 1):
        north_m = i * step
        for j in range(-half_steps, half_steps + 1):
            east_m = j * step
            if (north_m * north_m + east_m * east_m) > (loiter_radius_m * loiter_radius_m):
                continue

            samples_checked += 1
            sample_lat, sample_lon = _offset_latlon(goal_lat, goal_lon, north_m, east_m)
            # Exact lat/lon handed to TerrainManager.get_elevation -- logged
            # before the call so it can't drift from what was actually looked up.
            elevation_m = _terrain_manager.get_elevation(sample_lat, sample_lon)

            print(f"[TERRAIN SAMPLE]{tag} #{samples_checked}")
            print(f"Offset N: {north_m:.1f} m")
            print(f"Offset E: {east_m:.1f} m")
            print(f"Latitude: {sample_lat:.6f}")
            print(f"Longitude: {sample_lon:.6f}")

            if elevation_m is None:
                missing_samples += 1
                print("Elevation: N/A")
                continue

            print(f"Elevation: {elevation_m} m")

            if highest_elevation_m is None or elevation_m > highest_elevation_m:
                highest_elevation_m = elevation_m
                highest_lat = sample_lat
                highest_lon = sample_lon
                highest_north_m = north_m
                highest_east_m = east_m
                highest_sample_number = samples_checked

    valid_samples = samples_checked - missing_samples

    print(f"[TERRAIN CHECK]{tag} SUMMARY")
    print(f"Goal: {goal_lat:.4f}, {goal_lon:.4f}")
    print(f"Loiter radius: {loiter_radius_m:.0f} m")
    print(f"Samples checked: {samples_checked}")
    print(f"Valid samples: {valid_samples}")
    print(f"Missing samples: {missing_samples}")
    if highest_elevation_m is not None:
        print(f"Highest terrain: {highest_elevation_m} m")
        print(f"Highest terrain location: {highest_lat:.6f}, {highest_lon:.6f}")
    else:
        print("Highest terrain: N/A -- no valid samples")

    if highest_sample_number is not None:
        print(f"[HIGHEST TERRAIN]{tag}")
        print(f"Sample: #{highest_sample_number}")
        print(f"Latitude: {highest_lat:.6f}")
        print(f"Longitude: {highest_lon:.6f}")
        print(f"Offset N: {highest_north_m:.1f} m")
        print(f"Offset E: {highest_east_m:.1f} m")
        print(f"Elevation: {highest_elevation_m} m")

    return {
        "goal_lat": goal_lat,
        "goal_lon": goal_lon,
        "loiter_radius_m": loiter_radius_m,
        "samples_checked": samples_checked,
        "valid_samples": valid_samples,
        "missing_samples": missing_samples,
        "highest_elevation_m": highest_elevation_m,
        "highest_lat": highest_lat,
        "highest_lon": highest_lon,
        "highest_sample_number": highest_sample_number,
    }
