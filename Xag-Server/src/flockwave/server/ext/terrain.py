"""Extension that provides terrain elevation lookup via Socket.IO using SRTM tiles."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import shutil
import struct
import time
import urllib.request
from contextlib import ExitStack
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import trio

from flockwave.server import terrain_areas, terrain_safety, terrain_unsafe
from flockwave.server.message_hub import MessageHub
from flockwave.server.model.client import Client
from flockwave.server.model.log import Severity
from flockwave.server.model.messages import FlockwaveMessage
from flockwave.server.model.uav import UAV
from flockwave.server.utils import overridden

log: Optional[Logger] = None
app = None
configuration = None


class TerrainManager:
    BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"

    def __init__(self, terrain_dir="terrain"):
        self.terrain_dir = Path(terrain_dir)
        self.terrain_dir.mkdir(parents=True, exist_ok=True)
        self._tiles: Dict[Tuple[int, int], Any] = {}

    def get_tile_name(self, lat, lon):
        lat = math.floor(lat)
        lon = math.floor(lon)

        lat_name = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"
        lon_name = f"E{lon:03d}" if lon >= 0 else f"W{abs(lon):03d}"

        return f"{lat_name}{lon_name}"

    def download_tile(self, lat, lon):
        lat = math.floor(lat)
        lon = math.floor(lon)

        tile = self.get_tile_name(lat, lon)

        hgt_file = self.terrain_dir / f"{tile}.hgt"
        gz_file = self.terrain_dir / f"{tile}.hgt.gz"

        # Already downloaded
        if hgt_file.exists():
            return hgt_file

        # Latitude folder
        lat_folder = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"

        url = f"{self.BASE_URL}/{lat_folder}/{tile}.hgt.gz"

        if log:
            log.info(f"[TERRAIN] Downloading SRTM tile {tile}.hgt from {url}")
        else:
            print(f"[TERRAIN] Downloading SRTM tile {tile}.hgt from {url}")

        try:
            urllib.request.urlretrieve(url, gz_file)

            with gzip.open(gz_file, "rb") as source:
                with open(hgt_file, "wb") as destination:
                    shutil.copyfileobj(source, destination)

            if gz_file.exists():
                gz_file.unlink()

            if log:
                log.info(f"[TERRAIN] Downloaded {tile}.hgt successfully")
            else:
                print(f"[TERRAIN] Downloaded {tile}.hgt successfully")

            return hgt_file

        except Exception as e:
            if log:
                log.error(f"[TERRAIN] Download failed for {tile}.hgt: {e}")
            else:
                print(f"[TERRAIN] Download failed for {tile}.hgt: {e}")

            if gz_file.exists():
                gz_file.unlink()

            if hgt_file.exists():
                hgt_file.unlink()

            return None

    def _tile_array(self, lat, lon):
        """Read-only memory-mapped view of the 3601x3601 big-endian int16 tile
        covering integer (lat, lon), opened once and reused for every lookup
        (instead of re-opening the .hgt file per sample). None if the tile is
        not on disk (or is not a complete 1-arc-second tile)."""
        key = (lat, lon)
        arr = self._tiles.get(key)
        if arr is not None:
            return arr
        hgt_file = self.terrain_dir / f"{self.get_tile_name(lat, lon)}.hgt"
        try:
            if hgt_file.stat().st_size != 3601 * 3601 * 2:
                return None
            arr = np.memmap(hgt_file, dtype=">i2", mode="r", shape=(3601, 3601))
        except (OSError, ValueError):
            return None
        self._tiles[key] = arr
        return arr

    def get_cached_elevation(self, latitude, longitude):
        """Elevation from a tile that is ALREADY on disk; never downloads, so it is
        safe on the telemetry path. None if the tile is missing or the cell is a void
        (a missing value, not an elevation of 0). Nearest pixel, no max-sampling and
        no error buffer: this is the raw SRTM height used for UAV homes."""
        lat, lon = math.floor(latitude), math.floor(longitude)
        arr = self._tile_array(lat, lon)
        if arr is None:
            return None
        row = max(0, min(3600, round((1.0 - (latitude - lat)) * 3600)))
        col = max(0, min(3600, round((longitude - lon) * 3600)))
        elevation = int(arr[row, col])
        return None if elevation == -32768 else float(elevation)

    # -- conservative per-cell sampling (Step 2 grid) ------------------------------------
    #
    # Pixels are addressed by GLOBAL integer arc-seconds: `ay` = latitude * 3600,
    # `bx` = longitude * 3600. Pixel (ay, bx) is the SRTM sample at exactly that
    # position and covers +-0.5 arc-second around it. Tile L (latitudes L..L+1)
    # owns the latitudes L*3600 < ay <= (L+1)*3600 (its row 0 is its northern
    # edge) and tile N owns N*3600 <= bx < (N+1)*3600; the duplicated edge row /
    # column of the neighbouring tile is used only when the owner is missing.

    def _pixel(self, ay: int, bx: int) -> Optional[float]:
        """Elevation of the global pixel (ay, bx); None for a void or a missing tile."""
        tile_lat, tile_lon = (ay - 1) // 3600, bx // 3600
        candidates = [(tile_lat, tile_lon)]
        if ay % 3600 == 0:
            candidates.append(
                (tile_lat + 1, tile_lon)
            )  # the same row as row 3600 of the tile above
        if bx % 3600 == 0:
            candidates.append(
                (tile_lat, tile_lon - 1)
            )  # the same column as column 3600 of the tile west
        for tl, tn in candidates:
            arr = self._tile_array(tl, tn)
            if arr is not None:
                value = int(arr[(tl + 1) * 3600 - ay, bx - tn * 3600])
                return None if value == -32768 else float(value)
        return None

    def _block_max(self, ay0: int, ay1: int, bx0: int, bx1: int) -> Optional[float]:
        """Highest valid pixel with ay0 <= ay <= ay1 and bx0 <= bx <= bx1, across
        tile edges; None if every pixel is void or missing."""
        best: Optional[float] = None
        for tl in range((ay0 - 1) // 3600, (ay1 - 1) // 3600 + 1):
            top = (tl + 1) * 3600
            r0, r1 = top - min(ay1, top), top - max(ay0, tl * 3600 + 1)
            for tn in range(bx0 // 3600, bx1 // 3600 + 1):
                arr = self._tile_array(tl, tn)
                if arr is None:
                    continue
                c0, c1 = (
                    max(bx0, tn * 3600) - tn * 3600,
                    min(bx1, tn * 3600 + 3599) - tn * 3600,
                )
                block = np.asarray(arr[r0 : r1 + 1, c0 : c1 + 1])
                valid = block[block != -32768]
                if valid.size:
                    value = float(valid.max())
                    best = value if best is None else max(best, value)
        return best

    def get_cell_elevation(self, latitude, longitude, half_dlat, half_dlon, spacing_m):
        """CONSERVATIVE elevation of the grid cell centred on (latitude, longitude)
        whose footprint is +-half_dlat / +-half_dlon degrees.

        * spacing < SRTM_PIXEL_M: bilinear interpolation of the 4 surrounding
          pixels, never less than the nearest pixel;
        * spacing >= SRTM_PIXEL_M: the maximum of every pixel whose area overlaps
          the footprint, so a peak narrower than the cell is never lost.

        Without a complete tile on disk this falls back to `get_elevation` (a
        single nearest-pixel sample, which may download the tile)."""
        if self._tile_array(math.floor(latitude), math.floor(longitude)) is None:
            return self.get_elevation(latitude, longitude)

        ya, xb = latitude * 3600.0, longitude * 3600.0
        if spacing_m >= SRTM_PIXEL_M:
            # pixel k covers [k - 0.5, k + 0.5]: overlaps [lo, hi] iff lo - 0.5 < k < hi + 0.5
            ay0 = math.floor(ya - half_dlat * 3600.0 - 0.5) + 1
            ay1 = math.ceil(ya + half_dlat * 3600.0 + 0.5) - 1
            bx0 = math.floor(xb - half_dlon * 3600.0 - 0.5) + 1
            bx1 = math.ceil(xb + half_dlon * 3600.0 + 0.5) - 1
            return self._block_max(ay0, ay1, bx0, bx1)

        nearest = self._pixel(round(ya), round(xb))
        ay, bx = math.floor(ya), math.floor(xb)
        fy, fx = ya - ay, xb - bx
        corners = (
            (self._pixel(ay, bx), (1 - fy) * (1 - fx)),
            (self._pixel(ay, bx + 1), (1 - fy) * fx),
            (self._pixel(ay + 1, bx), fy * (1 - fx)),
            (self._pixel(ay + 1, bx + 1), fy * fx),
        )
        values = [v for v, _ in corners if v is not None]
        if len(values) < 4:
            # a void among the four: no interpolation, the highest valid neighbour
            candidates = values + ([nearest] if nearest is not None else [])
            return max(candidates) if candidates else None
        bilinear = sum(v * w for v, w in corners)  # type: ignore[operator]
        return max(bilinear, nearest) if nearest is not None else bilinear

    def get_elevation(self, latitude, longitude):
        lat = math.floor(latitude)
        lon = math.floor(longitude)

        # Fast path: tile already memory-mapped. Same row/col maths and void
        # handling as the file-seek path below, so results are identical.
        # Nearest pixel (round); int() used to pick the north-west one.
        arr = self._tile_array(lat, lon)
        if arr is not None:
            row = max(0, min(3600, round((1.0 - (latitude - lat)) * 3600)))
            col = max(0, min(3600, round((longitude - lon) * 3600)))
            elevation = int(arr[row, col])
            return None if elevation == -32768 else float(elevation)

        # Download if required
        hgt_file = self.download_tile(lat, lon)

        if hgt_file is None or not hgt_file.exists():
            return None

        # SRTM 1 arc-second = 3601 x 3601
        SIZE = 3601

        # Position inside tile
        lat_fraction = latitude - lat
        lon_fraction = longitude - lon

        # Convert coordinates to the NEAREST pixel
        row = round((1.0 - lat_fraction) * 3600)
        col = round(lon_fraction * 3600)

        # Clamp
        row = max(0, min(3600, row))
        col = max(0, min(3600, col))

        # Calculate byte offset
        offset = (row * SIZE + col) * 2

        try:
            with open(hgt_file, "rb") as f:
                f.seek(offset)
                data = f.read(2)
                if len(data) < 2:
                    return None
                elevation = struct.unpack(">h", data)[0]

            # SRTM void value
            if elevation == -32768:
                return None

            return float(elevation)

        except Exception as e:
            if log:
                log.error(f"[TERRAIN] Read error: {e}")
            return None


# Module global terrain manager instance & in-flight background download synchronization
_terrain_manager: Optional[TerrainManager] = None
_in_flight_tile_events: Dict[str, trio.Event] = {}

# Step 2: terrain elevation grid over the Origin operating area.
TERRAIN_GRID_SPACING_M = (
    20  # legacy fixed spacing; still the default for direct builder/test calls
)

# Adaptive spacing. The grid spacing is chosen per Origin from the size of its
# bounding box so the sample count stays bounded:
#   1. start from the first row of this table whose limit is >= the longer side
#      of the area (small areas stay detailed: 30 m x 30 m -> 5 m);
#   2. if rows*cols still exceeds the point budget, raise the spacing (in
#      SPACING_STEP_M steps) until it fits. Beyond the table the spacing comes
#      straight from the budget: ~sqrt(width*height/budget).
# The budget (not the table) is the hard limit. Override with the
# `terrain_grid_max_points` configuration key.
MAX_TERRAIN_GRID_POINTS = 100_000
SPACING_STEP_M = 5
# (longest side of the area in metres, starting spacing in metres)
SPACING_TABLE = (
    (50, 5),
    (100, 10),
    (1_000, 20),
    (5_000, 30),
    (10_000, 50),
    (25_000, 100),
    (50_000, 150),
)
# Above this spacing, a peak narrower than the cell can fall between samples;
# logged as a warning (SRTM itself is ~30 m, so <= 30 m loses nothing).
COARSE_SPACING_WARN_M = 200

# Approximate size of one SRTM 1-arc-second pixel. Below this grid spacing a cell
# is bilinearly interpolated; from it on, a cell is the max of every pixel it
# overlaps (see TerrainManager.get_cell_elevation).
SRTM_PIXEL_M = 30

# Metres added to every cell elevation before it is compared with the safety
# threshold: SRTM vertical error, trees, small buildings. Extension setting
# `terrain_error_buffer_m`. Applied at scan time, never stored in the grid.
DEFAULT_TERRAIN_ERROR_BUFFER_M = 15.0

# Bump whenever the grid layout or how it is sampled changes: it is part of
# the Origin fingerprint AND checked on load, so caches written by an older
# layout are rejected and regenerated instead of being misread.
# 2: conservative per-cell sampling (max over the footprint / bilinear).
TERRAIN_GRID_VERSION = 2

# Persistent (on-disk) copy of the grid for the *current* Origin. Kept apart
# from the raw SRTM tile cache (`TerrainManager.terrain_dir`): the tiles are
# the source data, this file is the processed 20 m grid derived from them.
TERRAIN_GRID_CACHE_DIRNAME = "terrain_grid"
TERRAIN_GRID_CACHE_FILENAME = "terrain_grid_cache.json"

# Lat/lon are rounded to this many decimals before fingerprinting (~1 cm), so
# float noise from a JSON round-trip can't turn the same Origin into a
# "different" one.
_FINGERPRINT_COORD_DECIMALS = 7

# Cached grid for the *current* Origin operating area (the outer fence
# polygon). Regenerated every time "Set Origin" succeeds. There is only ever
# one active Origin at a time -- same single-value pattern as the `origin`
# global in swarm.py -- so this is a single cached object, not a dict keyed
# by area.
_terrain_grid_cache: Optional[Dict[str, Any]] = None

# Serialises grid generation: two quick "Set Origin" requests must not build
# or write the persistent cache concurrently. The second one waits, then
# finds the first one's result on disk if it is for the same Origin.
_terrain_grid_lock = trio.Lock()

# Fingerprint of the most recent "Set Origin". A grid is only published into
# `_terrain_grid_cache` if it still matches this, so a slow generation for an
# earlier Origin can't land after (and replace) a newer Origin's state.
_latest_origin_fingerprint: Optional[str] = None


def _get_terrain_manager(terrain_dir_setting: Optional[str] = None) -> TerrainManager:
    global _terrain_manager
    if _terrain_manager is None:
        if terrain_dir_setting:
            target_path = Path(terrain_dir_setting)
        else:
            # Default: point to medur_swarm/terrain directory in workspace if available
            possible_path = Path(
                r"C:\Users\Joel\Desktop\Fixedwing-Swarm\fixed_wing_windows_exe\swarm_tasks\Examples\basic_tasks\medur_swarm\terrain"
            )
            if possible_path.exists():
                target_path = possible_path
            else:
                target_path = Path("terrain")

        _terrain_manager = TerrainManager(str(target_path))
        if log:
            log.info(f"[TERRAIN] Initialized TerrainManager with path: {target_path}")
    return _terrain_manager


async def _ensure_tile_ready(mgr: TerrainManager, lat: float, lon: float) -> bool:
    """Ensures the SRTM tile covering (lat, lon) exists on disk, downloading
    it in a worker thread if it doesn't. Concurrent callers asking for the
    same tile (a hover lookup and a bulk range pre-fetch, or several hover
    lookups) share one in-flight download via `_in_flight_tile_events`
    instead of triggering it more than once.

    Returns True if the tile is present on disk afterwards, False if the
    download failed.
    """
    tile_name = mgr.get_tile_name(lat, lon)
    hgt_file = mgr.terrain_dir / f"{tile_name}.hgt"

    if hgt_file.exists():
        return True

    if tile_name in _in_flight_tile_events:
        if log:
            log.info(
                f"[TERRAIN] Waiting for in-progress download of SRTM tile {tile_name}..."
            )
        await _in_flight_tile_events[tile_name].wait()
        return hgt_file.exists()

    evt = trio.Event()
    _in_flight_tile_events[tile_name] = evt
    try:
        result = await trio.to_thread.run_sync(mgr.download_tile, lat, lon)
    finally:
        evt.set()
        _in_flight_tile_events.pop(tile_name, None)

    return result is not None


def _tiles_for_bbox(min_lat: float, max_lat: float, min_lon: float, max_lon: float):
    """Every 1x1 degree SRTM tile (as integer (lat, lon) floors) overlapping
    the given bounding box, inclusive of the edges."""
    lat_start, lat_end = math.floor(min_lat), math.floor(max_lat)
    lon_start, lon_end = math.floor(min_lon), math.floor(max_lon)
    return [
        (lat, lon)
        for lat in range(lat_start, lat_end + 1)
        for lon in range(lon_start, lon_end + 1)
    ]


def get_cached_terrain_grid() -> Optional[Dict[str, Any]]:
    """Returns the terrain elevation grid cached for the current Origin
    operating area, or None if none has been generated yet."""
    return _terrain_grid_cache


def _polygon_bbox(polygon_latlon: list):
    lats = [p[0] for p in polygon_latlon]
    lons = [p[1] for p in polygon_latlon]
    return min(lats), max(lats), min(lons), max(lons)


def _grid_shape(
    min_lat: float, max_lat: float, min_lon: float, max_lon: float, spacing_m: float
):
    """(dlat, dlon, rows, cols) of the sample grid over a bounding box. Shared
    by grid generation and cache validation so the two can never disagree
    about what shape a grid for a given Origin must have."""
    # Metres-per-degree at the area's centre latitude -- same approximation
    # already used for the fence buffer/origin-shift math in YamlCreation.py.
    center_lat = (min_lat + max_lat) / 2.0
    dlat = spacing_m / 111320.0
    dlon = spacing_m / (111320.0 * math.cos(math.radians(center_lat)))

    rows = max(1, int(math.ceil((max_lat - min_lat) / dlat)) + 1)
    cols = max(1, int(math.ceil((max_lon - min_lon) / dlon)) + 1)
    return dlat, dlon, rows, cols


def select_grid_spacing(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    max_points: Optional[int] = None,
) -> Tuple[float, int, int]:
    """(spacing_m, rows, cols) for the bounding box: the finest spacing from
    SPACING_TABLE that keeps rows*cols within `max_points`. Deterministic for a
    given box, so it can be part of the Origin fingerprint."""
    if max_points is None:
        max_points = int(
            (configuration.get("terrain_grid_max_points") if configuration else None)
            or MAX_TERRAIN_GRID_POINTS
        )
    center_lat = (min_lat + max_lat) / 2.0
    height_m = (max_lat - min_lat) * 111320.0
    width_m = (max_lon - min_lon) * 111320.0 * math.cos(math.radians(center_lat))

    longest = max(width_m, height_m)
    spacing = next(
        (s for limit, s in SPACING_TABLE if longest <= limit * 1.01), None
    )  # 1% tolerance for degree rounding
    if spacing is None:
        spacing = math.sqrt(max(width_m * height_m, 1.0) / max_points)
    spacing = max(SPACING_STEP_M, math.ceil(spacing / SPACING_STEP_M) * SPACING_STEP_M)

    _, _, rows, cols = _grid_shape(min_lat, max_lat, min_lon, max_lon, spacing)
    while rows * cols > max_points:
        spacing += SPACING_STEP_M
        _, _, rows, cols = _grid_shape(min_lat, max_lat, min_lon, max_lon, spacing)
    return float(spacing), rows, cols


def _cell_lat(max_lat, dlat, row):
    """Latitude of grid row `row` (north row first). Works on ints and on numpy
    index arrays alike; the ONE place cell latitude is defined -- grid
    generation and the Step 4A unsafe-terrain scan both use it."""
    return max_lat - row * dlat


def _cell_lon(min_lon, dlon, col):
    """Longitude of grid column `col`; see `_cell_lat`."""
    return min_lon + col * dlon


def _grid_log(message: str, level: str = "info") -> None:
    if log:
        getattr(log, level)(message)
    else:
        print(message)


def _normalized_polygon(polygon_latlon: list) -> List[List[float]]:
    """The Origin polygon as rounded [lat, lon] floats, vertex order kept.
    Raises TypeError/ValueError/IndexError on malformed points."""
    d = _FINGERPRINT_COORD_DECIMALS
    # `+ 0.0` turns a rounded -0.0 into 0.0 so both serialise identically.
    return [
        [round(float(p[0]), d) + 0.0, round(float(p[1]), d) + 0.0]
        for p in polygon_latlon
    ]


def compute_origin_fingerprint(polygon_latlon: list, spacing_m: float) -> str:
    """Deterministic fingerprint of an Origin as far as its terrain grid is
    concerned: the outer polygon + the grid spacing + the grid version.

    Not an ID of anything -- it only answers "was this saved grid built for the
    Origin that is selected right now?". Same inputs always give the same
    value; a different polygon, spacing or grid version gives a different one.
    """
    canonical = {
        "version": TERRAIN_GRID_VERSION,
        "spacing_m": float(spacing_m),
        "polygon": _normalized_polygon(polygon_latlon),
    }
    text = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _terrain_grid_cache_path(mgr: TerrainManager) -> Path:
    """<terrain_grid_dir or sibling 'terrain_grid' of the SRTM dir>/terrain_grid_cache.json"""
    override = configuration.get("terrain_grid_dir") if configuration else None
    base = (
        Path(override)
        if override
        else mgr.terrain_dir.parent / TERRAIN_GRID_CACHE_DIRNAME
    )
    return base / TERRAIN_GRID_CACHE_FILENAME


def _save_terrain_grid_sync(path: Path, result: Dict[str, Any]) -> None:
    """Writes `result` (as built by _build_terrain_grid_sync + fingerprint/
    polygon) to `path`, replacing whatever Origin's grid was there before.
    Written to a temp file and renamed into place, so a crash or power loss
    mid-write can never leave a half-written cache behind."""
    stats = result["stats"]
    doc = {
        "version": TERRAIN_GRID_VERSION,
        "origin_fingerprint": result["origin_fingerprint"],
        "generated_at": result["generated_at"],
        "spacing_m": result["spacing_m"],
        "polygon": result["polygon"],
        "bounds": result["bounds"],
        "rows": result["rows"],
        "cols": result["cols"],
        "num_samples": stats["num_samples"],
        "num_valid": stats["num_valid"],
        "num_missing": stats["num_missing"],
        "min_elevation_m": stats["min_elevation_m"],
        "max_elevation_m": stats["max_elevation_m"],
        "max_elevation_location": stats["max_elevation_location"],
        "grid": result["grid"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, separators=(",", ":"), allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _validate_grid_doc(
    doc: Dict[str, Any], polygon: List[List[float]], spacing_m: float
) -> Dict[str, Any]:
    """Structural check of a cache document whose fingerprint already matched.
    Returns the in-memory grid dict; raises ValueError describing the first
    inconsistency. Statistics are recomputed from the grid and compared with
    the stored ones, so a truncated or hand-edited file is caught."""
    bounds = doc.get("bounds")
    if not isinstance(bounds, dict):
        raise ValueError("bounds missing")
    exp_bounds = dict(
        zip(("min_lat", "max_lat", "min_lon", "max_lon"), _polygon_bbox(polygon))
    )
    for key, expected in exp_bounds.items():
        if bounds.get(key) != expected:
            raise ValueError(f"bounds.{key} does not match the Origin polygon")

    _, _, exp_rows, exp_cols = _grid_shape(*exp_bounds.values(), spacing_m)
    rows, cols, grid = doc.get("rows"), doc.get("cols"), doc.get("grid")
    if rows != exp_rows or cols != exp_cols:
        raise ValueError(f"grid is {rows}x{cols}, expected {exp_rows}x{exp_cols}")
    if not isinstance(grid, list) or len(grid) != rows:
        raise ValueError("grid row count does not match 'rows'")

    num_valid = num_missing = 0
    min_elev = max_elev = None
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != cols:
            raise ValueError(f"grid row {r} does not have {cols} columns")
        for v in row:
            if v is None:
                num_missing += 1
                continue
            if (
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
            ):
                raise ValueError(f"grid row {r} holds a non-numeric elevation {v!r}")
            num_valid += 1
            min_elev = v if min_elev is None else min(min_elev, v)
            max_elev = v if max_elev is None else max(max_elev, v)

    for key, actual in (
        ("num_samples", rows * cols),
        ("num_valid", num_valid),
        ("num_missing", num_missing),
        ("min_elevation_m", min_elev),
        ("max_elevation_m", max_elev),
    ):
        if doc.get(key) != actual:
            raise ValueError(f"{key} is {doc.get(key)!r}, grid says {actual!r}")

    max_loc = doc.get("max_elevation_location")
    if num_valid:
        if not (
            isinstance(max_loc, dict)
            and all(isinstance(max_loc.get(k), (int, float)) for k in ("lat", "lon"))
        ):
            raise ValueError("max_elevation_location missing")
    else:
        max_loc = None

    return {
        "generated_at": doc.get("generated_at"),
        "spacing_m": spacing_m,
        "bounds": exp_bounds,
        "rows": rows,
        "cols": cols,
        "grid": grid,
        "stats": {
            "num_samples": rows * cols,
            "num_valid": num_valid,
            "num_missing": num_missing,
            "min_elevation_m": min_elev,
            "max_elevation_m": max_elev,
            "max_elevation_location": max_loc,
        },
        "origin_fingerprint": doc["origin_fingerprint"],
        "polygon": polygon,
    }


def _load_terrain_grid_sync(
    path: Path, fingerprint: str, polygon: List[List[float]], spacing_m: float
) -> Optional[Dict[str, Any]]:
    """Loads the persistent grid at `path` if -- and only if -- it was built
    for exactly this Origin. Returns None (after logging why) for a missing,
    unreadable, corrupt, other-Origin, other-version or other-spacing cache;
    the caller then generates a fresh grid. Blocking file I/O: run via
    trio.to_thread.run_sync."""
    if not path.exists():
        _grid_log("[TERRAIN GRID] no persistent cache found")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        if not isinstance(doc, dict):
            raise ValueError("top level is not an object")
    except (
        OSError,
        ValueError,
    ) as e:  # JSONDecodeError and UnicodeDecodeError are ValueErrors
        _grid_log(
            f"[TERRAIN GRID] persistent cache is unreadable/corrupt ({e})", "warning"
        )
        _grid_log("[TERRAIN GRID] cached grid will NOT be used", "warning")
        return None

    _grid_log("[TERRAIN GRID] persistent cache found")

    saved_fp = doc.get("origin_fingerprint")
    if saved_fp != fingerprint:
        _grid_log(
            f"[TERRAIN GRID] Origin fingerprint mismatch "
            f"(saved={str(saved_fp)[:12]}, current={fingerprint[:12]})"
        )
        _grid_log("[TERRAIN GRID] cached grid will NOT be used")
        return None
    _grid_log("[TERRAIN GRID] Origin fingerprint matches")

    # Fingerprint already covers version/spacing/polygon; these are explicit
    # second checks against a hand-edited file or a hash collision.
    if doc.get("version") != TERRAIN_GRID_VERSION:
        _grid_log(
            f"[TERRAIN GRID] cache version {doc.get('version')!r} != {TERRAIN_GRID_VERSION}",
            "warning",
        )
        _grid_log("[TERRAIN GRID] cached grid will NOT be used", "warning")
        return None
    saved_spacing = doc.get("spacing_m")
    if not isinstance(saved_spacing, (int, float)) or float(saved_spacing) != float(
        spacing_m
    ):
        _grid_log(
            f"[TERRAIN GRID] cache spacing {saved_spacing!r} != {spacing_m}", "warning"
        )
        _grid_log("[TERRAIN GRID] cached grid will NOT be used", "warning")
        return None
    if doc.get("polygon") != polygon:
        _grid_log(
            "[TERRAIN GRID] cache polygon differs from the Origin polygon", "warning"
        )
        _grid_log("[TERRAIN GRID] cached grid will NOT be used", "warning")
        return None

    _grid_log("[TERRAIN GRID] loading cached grid")
    try:
        result = _validate_grid_doc(doc, polygon, spacing_m)
    except ValueError as e:
        _grid_log(f"[TERRAIN GRID] cached grid failed validation: {e}", "warning")
        _grid_log("[TERRAIN GRID] cached grid will NOT be used", "warning")
        return None

    _grid_log(f"[TERRAIN GRID] loaded: {result['rows']}x{result['cols']}")
    return result


def _build_terrain_grid_sync(
    mgr: TerrainManager, polygon_latlon: list, spacing_m: float, progress_cb=None
) -> Dict[str, Any]:
    """Samples elevation on a regular grid covering the bounding box of
    `polygon_latlon` (the Origin operating area / outer fence polygon, as
    [lat, lon] pairs) at `spacing_m` metre spacing. Every cell holds the
    CONSERVATIVE elevation of its whole footprint
    (TerrainManager.get_cell_elevation), not a single point sample.

    Blocking, so callers run it via trio.to_thread.run_sync rather than
    awaiting it directly. `progress_cb(fraction)` (optional) is called from
    this thread roughly every 5 % of the rows.
    """
    t_shape = time.perf_counter()
    min_lat, max_lat, min_lon, max_lon = _polygon_bbox(polygon_latlon)
    dlat, dlon, rows, cols = _grid_shape(min_lat, max_lat, min_lon, max_lon, spacing_m)
    shape_s = time.perf_counter() - t_shape
    t_lookup = time.perf_counter()
    report_every = max(1, rows // 20)

    grid: List[List[Optional[float]]] = []
    num_valid = 0
    num_missing = 0
    min_elev: Optional[float] = None
    max_elev: Optional[float] = None
    max_elev_location: Optional[Dict[str, float]] = None

    for r in range(rows):
        lat = _cell_lat(
            max_lat, dlat, r
        )  # north row first, matches the example grid layout
        row_values: List[Optional[float]] = []
        for c in range(cols):
            lon = _cell_lon(min_lon, dlon, c)
            # None already covers SRTM void (-32768)
            elevation = mgr.get_cell_elevation(
                lat, lon, dlat / 2.0, dlon / 2.0, spacing_m
            )
            row_values.append(elevation)
            if elevation is None:
                num_missing += 1
                continue
            num_valid += 1
            if min_elev is None or elevation < min_elev:
                min_elev = elevation
            if max_elev is None or elevation > max_elev:
                max_elev = elevation
                max_elev_location = {"lat": lat, "lon": lon}
        grid.append(row_values)
        if progress_cb is not None and (r + 1) % report_every == 0:
            progress_cb((r + 1) / rows)

    return {
        "timings": {"grid_s": shape_s, "lookup_s": time.perf_counter() - t_lookup},
        "generated_at": time.time(),
        "spacing_m": spacing_m,
        "bounds": {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        },
        "rows": rows,
        "cols": cols,
        "grid": grid,
        "stats": {
            "num_samples": rows * cols,
            "num_valid": num_valid,
            "num_missing": num_missing,
            "min_elevation_m": min_elev,
            "max_elevation_m": max_elev,
            "max_elevation_location": max_elev_location,
        },
    }


def get_grid_elevation(grid: Dict[str, Any], lat: float, lon: float) -> Optional[float]:
    """Elevation at (lat, lon) taken from an already-built terrain grid -- the
    nearest cell, no SRTM access. If that cell is a void, the nearest valid
    cell within 3 cells is used. None if the point lies outside the grid or
    there is no valid cell nearby."""
    b = grid["bounds"]
    dlat, dlon, rows, cols = _grid_shape(
        b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], grid["spacing_m"]
    )
    row = round((b["max_lat"] - lat) / dlat)
    col = round((lon - b["min_lon"]) / dlon)
    if not (0 <= row < rows and 0 <= col < cols):
        return None

    cells = grid["grid"]
    for radius in range(4):
        best = None
        for r in range(max(0, row - radius), min(rows, row + radius + 1)):
            for c in range(max(0, col - radius), min(cols, col + radius + 1)):
                if cells[r][c] is None:
                    continue
                d = (r - row) ** 2 + (c - col) ** 2
                if best is None or d < best[0]:
                    best = (d, cells[r][c])
        if best is not None:
            return best[1]
    return None


def _raw_terrain_elevation(
    grid: Optional[Dict[str, Any]], lat: float, lon: float
) -> Optional[float]:
    """The RAW terrain height at a point (m AMSL): the nearest SRTM pixel of a
    tile already on disk, else `grid`'s nearest cell. Used for the home /
    reference elevation, which must NOT be max-sampled: a home that is too high
    would make the drone look higher above the terrain than it is. Never
    downloads; None means unavailable (never 0)."""
    mgr = _terrain_manager
    value = mgr.get_cached_elevation(lat, lon) if mgr is not None else None
    if value is None and grid is not None:
        value = get_grid_elevation(
            grid, lat, lon
        )  # conservative (max) cell: only a fallback
    return value


def _home_terrain_elevation(lat: float, lon: float) -> Optional[float]:
    """Terrain at a UAV's HOME (m AMSL), independent of the planning Origin; see
    `_raw_terrain_elevation`."""
    return _raw_terrain_elevation(_terrain_grid_cache, lat, lon)


def _terrain_error_buffer_m() -> float:
    """Extension setting `terrain_error_buffer_m` (metres >= 0), else the default."""
    value = configuration.get("terrain_error_buffer_m") if configuration else None
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    ):
        return float(value)
    return DEFAULT_TERRAIN_ERROR_BUFFER_M


def _log_home_snapshot(context: str) -> None:
    """Logs every saved UAV home (position + terrain) -- used around Set Origin to
    show that the planning Origin change left the home reference untouched."""
    homes = terrain_safety.tracker.saved_homes()
    if not homes:
        _grid_log(f"[HOME] {context}: no saved UAV home")
        return
    for uav_id, (home, terrain) in homes.items():
        shown = "unavailable" if terrain is None else f"{terrain:.1f} m"
        _grid_log(
            f"[HOME] {context}: UAV {uav_id} home lat={home[0]:.7f} lon={home[1]:.7f} "
            f"homeTerrainAMSL={shown}"
        )


def _activate_terrain_safety(grid: Dict[str, Any], origin_latlon) -> None:
    """Step 3: start the safety threshold for the Origin whose grid was just
    published. The reference terrain elevation is the terrain at the Origin
    reference point (the swarm Origin, i.e. the south-west corner of the outer
    fence's bounding box), read from the grid -- nothing is re-read from SRTM."""
    if origin_latlon is not None:
        ref_lat, ref_lon = float(origin_latlon[0]), float(origin_latlon[1])
    else:
        ref_lat, ref_lon = grid["bounds"]["min_lat"], grid["bounds"]["min_lon"]

    configured = configuration.get("safety_margin_m") if configuration else None
    if configured is not None and not terrain_safety.is_valid_safety_margin(configured):
        _grid_log(
            f"[TERRAIN SAFETY] ignoring safety_margin_m={configured!r}: the margin is a "
            f"positive distance that is subtracted; using {terrain_safety.DEFAULT_SAFETY_MARGIN_M} m",
            "warning",
        )

    tracker = terrain_safety.tracker
    if tracker.set_origin(
        grid["origin_fingerprint"],
        _raw_terrain_elevation(grid, ref_lat, ref_lon),
        (ref_lat, ref_lon),
        configured,  # validated by the tracker (missing/invalid/negative -> default)
        # the terrain at a UAV's HOME: raw SRTM pixel, this grid only as a fallback
        lambda lat, lon: _raw_terrain_elevation(grid, lat, lon),
    ):
        _grid_log(
            f"[TERRAIN SAFETY] Origin corner terrain {tracker.reference_terrain_elevation} m "
            f"at ({ref_lat:.6f}, {ref_lon:.6f}) -- only used until a UAV position is known; "
            f"the reference of each threshold is the terrain at the UAV's home. "
            f"Safety margin {tracker.safety_margin} m "
            f"(threshold = home terrain + drone height - margin)"
        )
    else:
        _grid_log(
            "[TERRAIN SAFETY] no reference terrain elevation at the Origin point "
            "-- safety threshold unavailable",
            "warning",
        )


def _observe_registered_uavs(app_instance) -> None:
    """Records the current telemetry of every connected UAV, so UAVs that are
    already climbing or flying when an Origin is set get the right stage."""
    for uav_id in app_instance.object_registry.ids_by_type(UAV):
        uav = app_instance.find_uav_by_id(uav_id)
        telemetry = terrain_safety.read_uav_telemetry(uav) if uav is not None else None
        if telemetry is not None:
            terrain_safety.tracker.update_uav(
                str(uav_id),
                *telemetry,
                position=terrain_safety.read_uav_position(uav),
                autopilot_home=terrain_safety.read_uav_home(uav),
            )


# --- Step 4A: unsafe terrain ---------------------------------------------------
#
# Terrain above the current Step 3 threshold, found by scanning the Step 2 grid
# that is already in memory (see terrain_unsafe.py). Everything below is
# per-Origin state: dropped when a new Origin is set, rebuilt lazily.

_unsafe_index: Optional[terrain_unsafe.TerrainScanIndex] = None
_unsafe_index_grid: Optional[Dict[str, Any]] = (
    None  # the grid `_unsafe_index` was built from
)
_unsafe_cache: Optional[Tuple[Tuple[str, float], Dict[str, Any]]] = (
    None  # (fingerprint, threshold) -> result
)
_unsafe_broadcast_key: Optional[Tuple[str, float]] = None  # what clients were last told
_unsafe_lock = trio.Lock()  # one scan/broadcast at a time; the last threshold wins

# Step 4B: the same cells grouped into polygons (terrain_areas.py), cached and
# broadcast per (Origin, threshold) exactly like the Step 4A result above.
_areas_cache: Optional[Tuple[Tuple[str, float], Dict[str, Any]]] = None
_areas_broadcast_key: Optional[Tuple[str, float]] = None

# The threshold follows the live UAV altitude, so it changes with every climb
# step and each change rescans/regroups. Those are still computed and
# broadcast; only the log lines are limited to when the outcome changes.
_unsafe_logged: Optional[Tuple[Any, ...]] = None
_areas_logged: Optional[Tuple[Any, ...]] = None


def _reset_unsafe_terrain() -> None:
    """Drops everything derived from the previous Origin (Step 4A and 4B)."""
    global _unsafe_index, _unsafe_index_grid, _unsafe_cache, _unsafe_broadcast_key
    global _areas_cache, _areas_broadcast_key, _unsafe_logged, _areas_logged
    _unsafe_index = _unsafe_index_grid = _unsafe_cache = _unsafe_broadcast_key = None
    _areas_cache = _areas_broadcast_key = None
    _unsafe_logged = _areas_logged = None


def _build_unsafe_index_sync(grid: Dict[str, Any]) -> terrain_unsafe.TerrainScanIndex:
    """Scan index for `grid`, laid out with the Step 2 `_cell_lat`/`_cell_lon`,
    with the configured terrain error buffer added to every cell."""
    b = grid["bounds"]
    dlat, dlon, _, _ = _grid_shape(
        b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], grid["spacing_m"]
    )
    return terrain_unsafe.TerrainScanIndex(
        grid,
        lambda row: _cell_lat(b["max_lat"], dlat, row),
        lambda col: _cell_lon(b["min_lon"], dlon, col),
        error_buffer_m=_terrain_error_buffer_m(),
    )


def _unsafe_scan_target(app_instance):
    """(fingerprint, grid, effective threshold payload, cache key) for the
    current Origin and the current Step 3 threshold. Everything after the
    fingerprint is None when there is no active Origin / grid / threshold.
    Shared by Step 4A and 4B, so both always work on the same (Origin,
    threshold) pair."""
    tracker = terrain_safety.tracker
    fingerprint = tracker.origin_fingerprint
    grid = _terrain_grid_cache
    connected = (
        [str(i) for i in app_instance.object_registry.ids_by_type(UAV)]
        if app_instance is not None
        else None
    )
    effective = tracker.effective_payload(connected)
    if (
        grid is None
        or effective is None
        or grid.get("origin_fingerprint") != fingerprint
    ):
        return fingerprint, None, None, None
    # The threshold plus the three numbers it is made of (normally implied by the
    # threshold; kept in the key so two different calculations that happen to give
    # the same number are never mistaken for each other).
    key = (
        fingerprint,
        effective["safetyThresholdAMSL"],
        (
            effective["referenceTerrainElevation"],
            effective["safetyAltitude"],
            effective["safetyMargin"],
        ),
    )
    return fingerprint, grid, effective, key


def _threshold_inputs(effective) -> Dict[str, Any]:
    """What the current Step 3 threshold was built from, as reported with the
    unsafe-terrain results:  threshold = referenceTerrainElevation +
    safetyAltitude (drone height) - safetyMargin. Copied from Step 3 so clients
    can show the calculation without repeating it."""
    return {
        "thresholdUavId": effective["uavId"],
        "altitudeSource": effective["altitudeSource"],
        "referenceTerrainElevation": effective["referenceTerrainElevation"],
        "referenceSource": effective["referenceSource"],
        "referenceLocation": effective["referenceLocation"],
        "safetyAltitude": effective["safetyAltitude"],
        "safetyMargin": effective["safetyMargin"],
    }


def _superseded(grid, fingerprint) -> bool:
    """A newer Origin arrived while a worker thread was busy."""
    return (
        _terrain_grid_cache is not grid
        or terrain_safety.tracker.origin_fingerprint != fingerprint
    )


async def _ensure_unsafe_index(
    grid, fingerprint
) -> Optional[terrain_unsafe.TerrainScanIndex]:
    """The scan index of `grid` (built once per Origin, in a worker thread), or
    None if the Origin changed meanwhile. Call with `_unsafe_lock` held."""
    global _unsafe_index, _unsafe_index_grid
    index = _unsafe_index
    if index is not None and _unsafe_index_grid is grid:
        return index
    started = time.perf_counter()
    index = await trio.to_thread.run_sync(_build_unsafe_index_sync, grid)
    if _superseded(grid, fingerprint):
        return None
    _unsafe_index, _unsafe_index_grid = index, grid
    _grid_log(
        f"[TERRAIN UNSAFE] scan index built in {(time.perf_counter() - started) * 1000:.0f} ms: "
        f"{index.checked_cells} of {index.rows * index.cols} cells checked "
        f"(area: {index.area})",
        "info" if index.area == "origin_polygon" else "warning",
    )
    return index


async def _current_unsafe_result(
    app_instance,
) -> Tuple[Optional[Tuple[str, float]], Dict[str, Any]]:
    """(key, result) of the unsafe terrain for the current Origin at the current
    Step 3 threshold; key is None when unavailable. Rescans only when the
    (Origin, threshold) pair differs from the last scan. Call with
    `_unsafe_lock` held."""
    global _unsafe_cache, _unsafe_logged

    fingerprint, grid, effective, key = _unsafe_scan_target(app_instance)
    if key is None:
        return None, terrain_unsafe.unavailable_response(fingerprint)
    threshold = effective["safetyThresholdAMSL"]
    if _unsafe_cache is not None and _unsafe_cache[0] == key:
        _unsafe_cache[1].update(
            _threshold_inputs(effective)
        )  # e.g. which UAV/source drives it now
        return key, _unsafe_cache[1]

    index = await _ensure_unsafe_index(grid, fingerprint)
    if index is None:
        return None, terrain_unsafe.unavailable_response(
            terrain_safety.tracker.origin_fingerprint
        )

    started = time.perf_counter()
    result = await trio.to_thread.run_sync(index.scan, threshold, fingerprint)
    if _superseded(grid, fingerprint):
        return None, terrain_unsafe.unavailable_response(
            terrain_safety.tracker.origin_fingerprint
        )
    result.update(_threshold_inputs(effective))
    _unsafe_cache = (key, result)

    highest = result["highestPoint"]
    outcome = (fingerprint, result["count"], highest["elevation"] if highest else None)
    if outcome != _unsafe_logged:
        _unsafe_logged = outcome
        _grid_log(
            f"[TERRAIN UNSAFE] threshold {threshold:.1f} m: {result['count']} unsafe cell(s)"
            + (f", highest {highest['elevation']} m" if highest else "")
            + f" (scan {(time.perf_counter() - started) * 1000:.0f} ms, 0 SRTM reads)"
        )
    return key, result


def _broadcast_unsafe_points() -> bool:
    """Whether the full Step 4A point list is pushed to all clients after every
    threshold change (extension setting `broadcast_unsafe_points`, default off).
    On a real 717x845 grid that message is 30+ MB, so it is off now that Step 4B
    provides the compact version; X-TERRAIN-UNSAFE-REQ still returns it on demand."""
    return (
        bool(configuration.get("broadcast_unsafe_points", False))
        if configuration
        else False
    )


async def _refresh_unsafe_terrain(app_instance) -> None:
    """Runs after every published Step 3 threshold update (grid ready, Takeoff
    command, telemetry change): rescans the existing grid if the effective
    threshold changed and broadcasts X-TERRAIN-UNSAFE-RESP. Nothing is sent
    when the threshold did not actually change."""
    global _unsafe_broadcast_key
    if app_instance is None or not _broadcast_unsafe_points():
        return
    async with _unsafe_lock:
        key, result = await _current_unsafe_result(app_instance)
        if key is None or key == _unsafe_broadcast_key:
            return
        first_for_origin = (
            _unsafe_broadcast_key is None or _unsafe_broadcast_key[0] != key[0]
        )

        body = dict(result)
        body["type"] = terrain_unsafe.EVENT_TYPE
        hub = app_instance.message_hub
        await hub.broadcast_message(hub.create_notification(body))
        _unsafe_broadcast_key = key

        if first_for_origin:
            highest = result["highestPoint"]
            if result["count"]:
                text = (
                    f"Unsafe terrain: {result['count']} cell(s) above "
                    f"{result['thresholdAMSL']:.1f} m AMSL, highest {highest['elevation']:.0f} m."
                )
            else:
                text = f"No terrain above the {result['thresholdAMSL']:.1f} m AMSL safety threshold."
            app_instance.request_to_send_SYS_MSG_message(
                text, severity=Severity.WARNING if result["count"] else Severity.INFO
            )


# Step 3 calls this after every threshold update it publishes.
terrain_safety.add_threshold_listener(_refresh_unsafe_terrain)


# --- Step 4B: unsafe terrain as compact areas ----------------------------------------------


def _area_tolerance_m() -> float:
    """Outward simplification tolerance in metres (extension setting
    `unsafe_area_simplify_tolerance_m`; 0 = exact cell outlines)."""
    value = (
        configuration.get("unsafe_area_simplify_tolerance_m") if configuration else None
    )
    return (
        float(value)
        if isinstance(value, (int, float)) and value >= 0
        else terrain_areas.SIMPLIFY_TOLERANCE_M
    )


async def _current_unsafe_areas(
    app_instance,
) -> Tuple[Optional[Tuple[str, float]], Dict[str, Any]]:
    """(key, result) of the unsafe areas for the current Origin at the current
    Step 3 threshold; key is None when unavailable. Regrouped only when the
    (Origin, threshold) pair changed; runs on the scan index Step 4A uses. Call
    with `_unsafe_lock` held."""
    global _areas_cache, _areas_logged

    fingerprint, grid, effective, key = _unsafe_scan_target(app_instance)
    if key is None:
        return None, terrain_areas.unavailable_response(fingerprint)
    threshold = effective["safetyThresholdAMSL"]
    if _areas_cache is not None and _areas_cache[0] == key:
        _areas_cache[1].update(
            _threshold_inputs(effective)
        )  # e.g. which UAV/source drives it now
        return key, _areas_cache[1]

    index = await _ensure_unsafe_index(grid, fingerprint)
    if index is None:
        return None, terrain_areas.unavailable_response(
            terrain_safety.tracker.origin_fingerprint
        )

    # The drone's own altitude AMSL: cells above it are RED, cells between it and the
    # threshold (= droneAMSL - margin) are YELLOW -- classified per cell, see terrain_areas.
    drone_amsl = effective["referenceTerrainElevation"] + effective["safetyAltitude"]

    started = time.perf_counter()
    result = await trio.to_thread.run_sync(
        terrain_areas.build_unsafe_areas,
        index,
        threshold,
        fingerprint,
        _area_tolerance_m(),
        drone_amsl,
    )
    if _superseded(grid, fingerprint):
        return None, terrain_areas.unavailable_response(
            terrain_safety.tracker.origin_fingerprint
        )
    result.update(_threshold_inputs(effective))
    _areas_cache = (key, result)

    outcome = (
        fingerprint,
        result["unsafeCellCount"],
        result["redCellCount"],
        result["yellowCellCount"],
        result["areaCount"],
    )
    if outcome != _areas_logged:
        _areas_logged = outcome
        _grid_log(
            f"[TERRAIN AREAS] threshold {threshold:.1f} m, drone {drone_amsl:.1f} m AMSL, "
            f"buffer {index.error_buffer_m} m: {result['unsafeCellCount']} unsafe cell(s) "
            f"({result['redCellCount']} red, {result['yellowCellCount']} yellow) "
            f"-> {result['areaCount']} area(s), {result['vertexCount']} vertices "
            f"(grouped in {(time.perf_counter() - started) * 1000:.0f} ms, 0 SRTM reads)"
        )
    return key, result


async def _refresh_unsafe_areas(app_instance) -> None:
    """Runs after every published Step 3 threshold update, right after Step 4A:
    regroups the unsafe cells of the existing grid if the effective threshold
    changed and broadcasts X-TERRAIN-UNSAFE-AREA-RESP. Nothing is sent when the
    threshold did not actually change."""
    global _areas_broadcast_key
    if app_instance is None:
        return
    async with _unsafe_lock:
        key, result = await _current_unsafe_areas(app_instance)
        if key is None or key == _areas_broadcast_key:
            return
        first_for_origin = (
            _areas_broadcast_key is None or _areas_broadcast_key[0] != key[0]
        )

        body = dict(result)
        body["type"] = terrain_areas.EVENT_TYPE
        hub = app_instance.message_hub
        await hub.broadcast_message(hub.create_notification(body))
        _areas_broadcast_key = key

        if first_for_origin:
            if result["areaCount"]:
                text = (
                    f"Unsafe terrain: {result['areaCount']} area(s), {result['unsafeCellCount']} cell(s) "
                    f"above {result['thresholdAMSL']:.1f} m AMSL, highest "
                    f"{result['highestPoint']['elevation']:.0f} m."
                )
            else:
                text = f"No terrain above the {result['thresholdAMSL']:.1f} m AMSL safety threshold."
            app_instance.request_to_send_SYS_MSG_message(
                text,
                severity=Severity.WARNING if result["areaCount"] else Severity.INFO,
            )


terrain_safety.add_threshold_listener(_refresh_unsafe_areas)


def _log_grid_timings(result, source, num_tiles, timings, t_total) -> None:
    b = result["bounds"]
    center = (b["min_lat"] + b["max_lat"]) / 2.0
    height = (b["max_lat"] - b["min_lat"]) * 111320.0
    width = (b["max_lon"] - b["min_lon"]) * 111320.0 * math.cos(math.radians(center))
    f = lambda k: f"{timings[k]:.2f} s" if k in timings else "n/a"
    _grid_log(
        f"[TERRAIN GRID] Area: {width:.0f} x {height:.0f} m | Spacing: {result['spacing_m']:g} m | "
        f"Rows: {result['rows']} | Columns: {result['cols']} | Samples: {result['stats']['num_samples']} | "
        f"SRTM tiles: {num_tiles} | Tile download: {f('tiles_s')} | Grid generation: {f('grid_s')} | "
        f"Elevation lookup: {f('lookup_s')} | Terrain safety scan: {f('safety_s')} | "
        f"Cache save: {f('save_s')} | Total: {time.perf_counter() - t_total:.2f} s (source: {source})"
    )


async def generate_terrain_grid_for_origin(
    app_instance, polygon_latlon: list, origin_latlon=None
) -> None:
    """Builds and caches the terrain elevation grid for the Origin operating
    area after "Set Origin" succeeds, then broadcasts an X-TERRAIN-GRID-RESP
    notification with a summary (not the raw grid) once ready.

    Meant to be launched via `app.run_in_background(...)` from the "fence"
    handler in app.py so it never delays the Set Origin response -- same
    fire-and-forget relationship the frontend already has between
    requestTerrainRange() and the "fence" message.

    All SRTM tiles this needs are already on disk: the grid's bounding box is
    the same outer-fence polygon whose bbox X-TERRAIN-RANGE-REQ (Step 1) just
    downloaded tiles for, and that request covered every whole 1x1 degree
    tile overlapping it, which is a superset of any point inside the bbox.

    The grid is also persisted (see `_terrain_grid_cache_path`) together with
    the fingerprint of the Origin it was built for. If a saved grid exists
    whose fingerprint matches this Origin it is loaded instead of rebuilt;
    a grid saved for any other Origin is never used and gets overwritten.

    Once the grid is published, the Step 3 safety threshold is (re)started for
    this Origin from the grid -- see terrain_safety.py.
    """
    global _terrain_grid_cache, _latest_origin_fingerprint

    # "Set Origin" has happened, so whatever grid is in memory belongs to the
    # PREVIOUS Origin. Drop it right away: from here until this Origin's grid
    # is ready, get_cached_terrain_grid() returns None, never the old grid.
    _terrain_grid_cache = None
    # The PLANNING origin is replaced here; the UAVs' saved homes (position + terrain,
    # established by Takeoff) are deliberately not part of it.
    homes_before = terrain_safety.tracker.saved_homes()
    _grid_log(
        f"[TERRAIN] Set Origin: planning origin -> {origin_latlon} "
        f"({len(polygon_latlon) if isinstance(polygon_latlon, list) else 0} boundary point(s))"
    )
    _log_home_snapshot("saved home before Set Origin")
    terrain_safety.tracker.clear_origin()  # never keep the previous Origin's reference elevation
    _reset_unsafe_terrain()  # ... nor its unsafe-terrain result or scan index

    if not isinstance(polygon_latlon, list) or len(polygon_latlon) < 3:
        _latest_origin_fingerprint = None
        if log:
            log.warning("[TERRAIN GRID] skipped -- invalid/empty Origin polygon")
        return

    try:
        polygon = _normalized_polygon(polygon_latlon)
        spacing_m, sel_rows, sel_cols = select_grid_spacing(*_polygon_bbox(polygon))
        fingerprint = compute_origin_fingerprint(polygon_latlon, spacing_m)
    except (TypeError, ValueError, IndexError):
        _latest_origin_fingerprint = None
        if log:
            log.warning("[TERRAIN GRID] skipped -- malformed Origin polygon")
        return
    _latest_origin_fingerprint = fingerprint
    t_total = time.perf_counter()
    timings: Dict[str, float] = {}

    async def progress(pct: int, text: str) -> None:
        _grid_log(f"[TERRAIN GRID] Terrain preparation: {pct}% - {text}")
        if app_instance is not None:
            await app_instance.message_hub.broadcast_message(
                app_instance.message_hub.create_notification(
                    {
                        "type": "X-TERRAIN-GRID-RESP",
                        "status": "progress",
                        "progress": pct,
                        "message": text,
                    }
                )
            )

    await progress(0, "Terrain preparation...")

    mgr = _get_terrain_manager(
        configuration.get("terrain_dir") if configuration else None
    )
    cache_path = _terrain_grid_cache_path(mgr)

    async with _terrain_grid_lock:
        if fingerprint != _latest_origin_fingerprint:
            # Another "Set Origin" arrived while this one waited for the lock.
            _grid_log("[TERRAIN GRID] superseded by a newer Origin -- skipping")
            return

        result = await trio.to_thread.run_sync(
            _load_terrain_grid_sync, cache_path, fingerprint, polygon, spacing_m
        )
        source = "persistent_cache"

        if result is not None:
            _grid_log("[TERRAIN GRID] ready from persistent cache")
        else:
            source = "generated"
            _grid_log(
                f"[TERRAIN GRID] generating new grid for Origin area "
                f"({len(polygon_latlon)} boundary point(s), spacing={spacing_m}m, "
                f"{sel_rows}x{sel_cols}={sel_rows * sel_cols} samples)..."
            )
            if spacing_m > COARSE_SPACING_WARN_M:
                _grid_log(
                    f"[TERRAIN GRID] coarse {spacing_m:.0f} m spacing for this large area: "
                    f"terrain narrower than one cell may be missed",
                    "warning",
                )

            # SRTM tiles are a separate, older cache: reuse the ones on disk,
            # download only the missing ones (normally already fetched by
            # X-TERRAIN-RANGE-REQ, so this is usually a no-op).
            min_lat, max_lat, min_lon, max_lon = _polygon_bbox(polygon)
            tiles_ok = True
            tile_list = _tiles_for_bbox(min_lat, max_lat, min_lon, max_lon)
            await progress(20, "Downloading terrain tiles...")
            t0 = time.perf_counter()
            for tile_lat, tile_lon in tile_list:
                if not await _ensure_tile_ready(mgr, tile_lat, tile_lon):
                    tiles_ok = False
            timings["tiles_s"] = time.perf_counter() - t0
            await progress(40, "Generating terrain grid...")

            token = trio.lowlevel.current_trio_token()
            last_pct = [40]

            def on_rows(fraction: float) -> None:
                # called from the worker thread; 40% -> 85% while reading elevations
                pct = 40 + int(fraction * 45)
                if pct >= last_pct[0] + 5:
                    last_pct[0] = pct
                    trio.from_thread.run(
                        progress, pct, "Reading elevations...", trio_token=token
                    )

            # Sampled from the normalized polygon -- the exact input the
            # fingerprint covers -- so one fingerprint always means one grid.
            result = await trio.to_thread.run_sync(
                _build_terrain_grid_sync, mgr, polygon, spacing_m, on_rows
            )
            timings.update(result["timings"])
            result["origin_fingerprint"] = fingerprint
            result["polygon"] = polygon
            _grid_log("[TERRAIN GRID] grid generated")

            if not tiles_ok:
                # Cells over a tile that failed to download would be stored as
                # "missing" and then trusted forever, even once the tile is
                # available again. Keep this grid in memory only.
                _grid_log(
                    "[TERRAIN GRID] SRTM tile(s) unavailable -- grid NOT saved to persistent cache",
                    "warning",
                )
            else:
                try:
                    t0 = time.perf_counter()
                    await trio.to_thread.run_sync(
                        _save_terrain_grid_sync, cache_path, result
                    )
                    timings["save_s"] = time.perf_counter() - t0
                    _grid_log(f"[TERRAIN GRID] cache saved: {cache_path}")
                except (OSError, TypeError, ValueError) as e:
                    _grid_log(
                        f"[TERRAIN GRID] could not save persistent cache ({e}); "
                        f"continuing with in-memory grid",
                        "warning",
                    )

        # Publish only if no newer "Set Origin" arrived while we were busy.
        if fingerprint == _latest_origin_fingerprint:
            _terrain_grid_cache = result
            await progress(90, "Checking terrain safety...")
            _activate_terrain_safety(result, origin_latlon)
            if terrain_safety.tracker.saved_homes() == homes_before:
                _grid_log("[HOME] Set Origin finished: saved home reference unchanged")
            else:
                # only a pre-takeoff UAV that was moved, or one first seen meanwhile
                _grid_log(
                    "[HOME] saved home reference differs after Set Origin (pre-takeoff "
                    "telemetry, not Set Origin itself)",
                    "warning",
                )
            _log_home_snapshot("saved home after Set Origin")
        else:
            _grid_log(
                "[TERRAIN GRID] superseded by a newer Origin -- grid not published"
            )
            return

    stats = result["stats"]

    _grid_log(
        f"[TERRAIN GRID] ready: {result['rows']}x{result['cols']} "
        f"({stats['num_samples']} samples, {stats['num_valid']} valid, "
        f"{stats['num_missing']} missing) "
        f"min={stats['min_elevation_m']}m max={stats['max_elevation_m']}m"
    )

    if app_instance is None:
        return

    body = {
        "type": "X-TERRAIN-GRID-RESP",
        "status": "ready",
        "source": source,
        "bounds": result["bounds"],
        "spacing_m": result["spacing_m"],
        "rows": result["rows"],
        "cols": result["cols"],
        "stats": stats,
    }
    await app_instance.message_hub.broadcast_message(
        app_instance.message_hub.create_notification(body)
    )

    if stats["max_elevation_location"]:
        highest = (
            f"lat {stats['max_elevation_location']['lat']:.6f}, "
            f"lon {stats['max_elevation_location']['lon']:.6f}"
        )
    else:
        highest = "N/A"

    app_instance.request_to_send_SYS_MSG_message(
        f"Terrain grid {'loaded from saved cache' if source == 'persistent_cache' else 'ready'}: "
        f"{result['rows']}x{result['cols']} samples "
        f"@ {result['spacing_m']}m ({stats['num_valid']}/{stats['num_samples']} valid). "
        f"Elevation {stats['min_elevation_m']}-{stats['max_elevation_m']} m. "
        f"Highest terrain: {highest}.",
        severity=Severity.INFO,
    )

    # Step 3: send the initial safety threshold right away -- before any
    # Takeoff command, so the GCS can show it. UAVs already connected are read
    # first so ones that are already climbing/flying get their real stage.
    tracker = terrain_safety.tracker
    if not tracker.active:
        await app_instance.message_hub.broadcast_message(
            app_instance.message_hub.create_notification(
                {
                    "type": terrain_safety.EVENT_TYPE,
                    "status": "unavailable",
                    "reason": "no terrain elevation at the Origin reference point",
                    "originFingerprint": fingerprint,
                }
            )
        )
        return
    _observe_registered_uavs(app_instance)
    payloads = tracker.snapshot()
    t0 = time.perf_counter()
    await terrain_safety.publish_payloads(
        app_instance, payloads
    )  # runs the unsafe-terrain scan
    timings["safety_s"] = time.perf_counter() - t0
    _log_grid_timings(
        result, source, len(_tiles_for_bbox(*_polygon_bbox(polygon))), timings, t_total
    )
    await progress(100, "Terrain ready")
    first = payloads[0]
    app_instance.request_to_send_SYS_MSG_message(
        f"Terrain safety threshold {first['safetyThresholdAMSL']:.1f} m AMSL "
        f"(home terrain {first['referenceTerrainElevation']:.1f} m [{first['referenceSource']}] + "
        f"drone height {first['safetyAltitude']:.1f} m [{first['altitudeSource']}] - "
        f"safety margin {first['safetyMargin']:.1f} m).",
        severity=Severity.INFO,
    )


async def handle_X_TERRAIN_SAFETY_REQ(
    message: FlockwaveMessage, sender: Client, hub: MessageHub
):
    """Socket.IO handler for X-TERRAIN-SAFETY-REQ: returns the current safety
    thresholds (Origin level + every connected UAV), so a GCS that connects
    after the broadcasts still gets them. Read-only: no grid or SRTM access."""
    tracker = terrain_safety.tracker
    if not tracker.active:
        return {
            "type": terrain_safety.EVENT_TYPE,
            "status": "unavailable",
            "reason": "no terrain grid for the current Origin",
            "thresholds": [],
        }
    if app is not None:
        _observe_registered_uavs(app)
    return {
        "type": terrain_safety.EVENT_TYPE,
        "status": "ready",
        "thresholds": tracker.snapshot(),
    }


TERRAIN_CALC_REQUEST_TYPE = "X-TERRAIN-CALC-REQ"
TERRAIN_CALC_RESPONSE_TYPE = "X-TERRAIN-CALC-RESP"


async def handle_X_TERRAIN_CALC_REQ(
    message: FlockwaveMessage, sender: Client, hub: MessageHub
):
    """Socket.IO handler for X-TERRAIN-CALC-REQ (the GCS "Calculate" button):
    ``alt`` becomes the safety altitude of every UAV ON THE GROUND -- nothing is
    sent to any UAV, and a flying UAV keeps following its live altitude. The new
    threshold and unsafe areas are then broadcast as usual. The Takeoff
    command itself no longer changes terrain safety.

    Before an Origin is set the altitude is remembered and used as soon as
    the terrain grid is ready (``status`` "pending")."""
    alt = (message.body or {}).get("alt")
    if (
        isinstance(alt, bool)
        or not isinstance(alt, (int, float))
        or not math.isfinite(alt)
        or alt <= 0
    ):
        return {
            "type": TERRAIN_CALC_RESPONSE_TYPE,
            "status": "error",
            "error": "Altitude must be a positive number",
        }
    if app is None:
        return {
            "type": TERRAIN_CALC_RESPONSE_TYPE,
            "status": "error",
            "error": "Server not ready",
        }

    terrain_safety.on_takeoff_commanded(app, float(alt), [])  # [] = every UAV
    return {
        "type": TERRAIN_CALC_RESPONSE_TYPE,
        "status": "ok" if terrain_safety.tracker.active else "pending",
        "alt": float(alt),
    }


async def handle_X_TERRAIN_UNSAFE_REQ(
    message: FlockwaveMessage, sender: Client, hub: MessageHub
):
    """Socket.IO handler for X-TERRAIN-UNSAFE-REQ: read-only. Returns the unsafe
    terrain of the current Origin at the current Step 3 threshold (status
    "unsafe" / "safe" / "unavailable"), in the same shape as the
    X-TERRAIN-UNSAFE-RESP broadcast. Reuses the in-memory grid: no SRTM reads,
    no grid regeneration."""
    async with _unsafe_lock:
        _, result = await _current_unsafe_result(app)
    return {"type": terrain_unsafe.EVENT_TYPE, **result}


async def handle_X_TERRAIN_UNSAFE_AREA_REQ(
    message: FlockwaveMessage, sender: Client, hub: MessageHub
):
    """Socket.IO handler for X-TERRAIN-UNSAFE-AREA-REQ: read-only. Returns the
    unsafe terrain of the current Origin at the current Step 3 threshold as
    connected areas with polygon outlines ("unsafe" / "safe" / "unavailable"),
    in the same shape as the X-TERRAIN-UNSAFE-AREA-RESP broadcast. Reuses the
    in-memory grid and scan index: no SRTM reads, no grid regeneration."""
    async with _unsafe_lock:
        _, result = await _current_unsafe_areas(app)
    return {"type": terrain_areas.EVENT_TYPE, **result}


async def handle_X_TERRAIN_REQ(
    message: FlockwaveMessage, sender: Client, hub: MessageHub
):
    """Socket.IO handler for X-TERRAIN-REQ incoming messages -- the mouse
    hover lookup.

    Read-only: only ever reads a tile that's already on disk. It never
    downloads a missing one -- that used to happen here too (lazily, the
    first time a point in an undownloaded tile was hovered), but that
    meant hovering ANYWHERE on the map could trigger a download. Only
    "Set Origin" (X-TERRAIN-RANGE-REQ, handled below) is allowed to
    download tiles now; hovering outside a pre-fetched area just reports
    "not available" instead of fetching it on the spot.
    """
    body = message.body or {}
    lat = body.get("lat")
    lon = body.get("lon")

    if lat is None or lon is None:
        return {
            "type": "X-TERRAIN-RESP",
            "elevation": None,
            "error": "Invalid lat/lon parameters",
        }

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return {
            "type": "X-TERRAIN-RESP",
            "elevation": None,
            "error": "Non-numeric lat/lon",
        }

    mgr = _get_terrain_manager(
        configuration.get("terrain_dir") if configuration else None
    )

    tile_name = mgr.get_tile_name(lat, lon)
    hgt_file = mgr.terrain_dir / f"{tile_name}.hgt"
    elevation = mgr.get_elevation(lat, lon) if hgt_file.exists() else None
    if log:
        log.debug(
            f"[TERRAIN REQ] {lat:.4f}, {lon:.4f} -> {elevation} m "
            f"(tile {tile_name} {'cached' if hgt_file.exists() else 'not downloaded'})"
        )

    return {
        "type": "X-TERRAIN-RESP",
        "elevation": elevation,
        "lat": lat,
        "lon": lon,
    }


async def handle_X_TERRAIN_RANGE_REQ(
    message: FlockwaveMessage, sender: Client, hub: MessageHub
):
    """Socket.IO handler for X-TERRAIN-RANGE-REQ: pre-fetches every SRTM
    tile covering a drawn area (e.g. the geofence polygon submitted with
    "Set Origin") so later X-TERRAIN-REQ hover lookups over that area
    resolve from the local cache instead of each triggering their own
    lazy per-point download.

    Expects ``points``: a list of ``[lon, lat]`` pairs (the same shape the
    frontend already uses for drawn feature vertices), and covers their
    bounding box. Tiles already cached are left untouched; missing ones are
    downloaded here. A SYS-MSG notification is pushed to clients when a
    download starts and again when it finishes, independently of this
    request/response (the frontend doesn't need to poll for progress).
    """
    body = message.body or {}
    points = body.get("points")

    if log:
        log.info(
            f"[TERRAIN RANGE] request received: "
            f"{len(points) if isinstance(points, list) else points!r} points"
        )

    if not isinstance(points, list) or len(points) == 0:
        if log:
            log.warning("[TERRAIN RANGE] rejected -- no points supplied")
        return {
            "type": "X-TERRAIN-RANGE-RESP",
            "status": "error",
            "error": "No points supplied",
        }

    try:
        lons = [float(p[0]) for p in points]
        lats = [float(p[1]) for p in points]
    except (TypeError, ValueError, IndexError):
        return {
            "type": "X-TERRAIN-RANGE-RESP",
            "status": "error",
            "error": "Invalid points",
        }

    mgr = _get_terrain_manager(
        configuration.get("terrain_dir") if configuration else None
    )

    tiles = _tiles_for_bbox(min(lats), max(lats), min(lons), max(lons))
    missing = [
        (lat, lon, mgr.get_tile_name(lat, lon))
        for lat, lon in tiles
        if not (mgr.terrain_dir / f"{mgr.get_tile_name(lat, lon)}.hgt").exists()
    ]

    if not missing:
        if log:
            log.info(f"[TERRAIN RANGE] All {len(tiles)} SRTM tile(s) already cached")
        return {
            "type": "X-TERRAIN-RANGE-RESP",
            "status": "cached",
            "total_tiles": len(tiles),
            "downloaded_tiles": [],
            "failed_tiles": [],
        }

    if app:
        app.request_to_send_SYS_MSG_message(
            f"Downloading terrain data for the selected area "
            f"({len(missing)} SRTM tile{'s' if len(missing) != 1 else ''})...",
            severity=Severity.INFO,
        )

    downloaded, failed = [], []
    for lat, lon, tile_name in missing:
        ok = await _ensure_tile_ready(mgr, lat, lon)
        (downloaded if ok else failed).append(tile_name)

    if app:
        if failed:
            app.request_to_send_SYS_MSG_message(
                f"Terrain download completed with {len(failed)} failed tile"
                f"{'s' if len(failed) != 1 else ''}: {', '.join(failed)}",
                severity=Severity.WARNING,
            )
        else:
            app.request_to_send_SYS_MSG_message(
                f"Terrain download completed "
                f"({len(downloaded)} tile{'s' if len(downloaded) != 1 else ''}).",
                severity=Severity.INFO,
            )

    if log:
        log.info(
            f"[TERRAIN RANGE] downloaded={downloaded} failed={failed} "
            f"(of {len(tiles)} total tiles)"
        )

    return {
        "type": "X-TERRAIN-RANGE-RESP",
        "status": "completed",
        "total_tiles": len(tiles),
        "downloaded_tiles": downloaded,
        "failed_tiles": failed,
    }


async def run(app_instance, config, logger):
    """Extension main loop."""
    global app, configuration, log
    configuration = config
    log = logger

    _get_terrain_manager(configuration.get("terrain_dir") if configuration else None)
    # UAV homes read their elevation here, not from whichever planning grid is active
    terrain_safety.tracker.set_home_terrain_lookup(_home_terrain_elevation)

    with ExitStack() as stack:
        stack.enter_context(overridden(globals(), app=app_instance, log=logger))
        with app_instance.message_hub.use_message_handlers(
            {
                "X-TERRAIN-REQ": handle_X_TERRAIN_REQ,
                "X-TERRAIN-RANGE-REQ": handle_X_TERRAIN_RANGE_REQ,
                "X-TERRAIN-SAFETY-REQ": handle_X_TERRAIN_SAFETY_REQ,
                TERRAIN_CALC_REQUEST_TYPE: handle_X_TERRAIN_CALC_REQ,
                terrain_unsafe.REQUEST_TYPE: handle_X_TERRAIN_UNSAFE_REQ,
                terrain_areas.REQUEST_TYPE: handle_X_TERRAIN_UNSAFE_AREA_REQ,
            }
        ):
            await trio.sleep_forever()


dependencies = ("http_server", "socketio")
description = "SRTM Terrain elevation service over Socket.IO"
schema = {
    "properties": {
        "terrain_dir": {
            "type": "string",
            "title": "Terrain Directory",
            "description": "Path to SRTM .hgt terrain tiles directory",
        },
        "safety_margin_m": {
            "type": "number",
            "minimum": 0,
            "title": "Terrain Safety Margin (m)",
            "description": (
                "Positive distance subtracted from (home terrain elevation + drone "
                "height) to get the terrain safety threshold; terrain above the "
                "threshold is unsafe (default: 50)"
            ),
        },
        "broadcast_unsafe_points": {
            "type": "boolean",
            "title": "Broadcast Unsafe Points",
            "description": (
                "Push the full per-cell unsafe point list (X-TERRAIN-UNSAFE-RESP, "
                "can be 30+ MB) to all clients after every threshold change. Off by "
                "default: the compact X-TERRAIN-UNSAFE-AREA-RESP is always sent."
            ),
        },
        "unsafe_area_simplify_tolerance_m": {
            "type": "number",
            "title": "Unsafe Area Simplification Tolerance (m)",
            "description": (
                "Outward simplification tolerance of unsafe area outlines "
                "(default: 5; 0 = exact cell outlines)"
            ),
        },
        "terrain_grid_dir": {
            "type": "string",
            "title": "Terrain Grid Cache Directory",
            "description": (
                "Directory for the persistent processed terrain-grid cache "
                "(default: 'terrain_grid' next to the SRTM tiles directory)"
            ),
        },
    }
}
