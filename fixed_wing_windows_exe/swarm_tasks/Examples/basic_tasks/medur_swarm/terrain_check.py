"""Terrain reader and pre-flight terrain-clearance checks.

Answers one question, in three shapes: "is any terrain in the region the
aircraft is about to occupy higher than the altitude it will be flown at?"

TWO INPUT FORMATS, ONE QUERY PATH
---------------------------------
ArduPilot .DAT (from terrain.ardupilot.org, 100 m posts) and SRTM .hgt (the
1- or 3-arc-second squares terrain_data.py already downloads, 30 m posts).
.DAT wins when both exist for a square, purely because it is what the
autopilot itself carries; .hgt fills every gap, which is what stops a shifted
operating area from becoming an unmapped one. Both are normalised at load
into the same shape -- patches carrying their own corner lat/lon and
degrees-per-cell -- so nothing downstream knows or cares which it got.
Measured agreement between the two over this site: mean +3.1 m, max 8 m, with
.DAT reading HIGH (the safe direction).

    check_leg()      -- the corridor swept while flying to a goal
    check_loiter()   -- the disc the aircraft orbits once it arrives
    check_area()     -- one bounding box, giving a single mission floor

WHY THE ALTITUDE MATH LOOKS THE WAY IT DOES
-------------------------------------------
uav/guidance.py commands `simple_goto(LocationGlobalRelative(lat, lon, alt))`,
and LocationGlobalRelative altitude is **relative to home** -- not AMSL and
not AGL. Terrain data is AMSL. Comparing the two directly is the obvious way
to get this wrong by the elevation of the launch site.

So every check here works in the frame the code already commands in: it
converts terrain to a *rise above the terrain at home*, and compares that to
the commanded relative altitude:

    terrain_rise     = terrain_max_amsl - home_terrain_amsl
    required_rel_alt = terrain_rise + min_clearance_m
    SAFE  iff  commanded_rel_alt >= required_rel_alt

Taking home's elevation from this same dataset (rather than from GPS AMSL)
means any datum/geoid bias in the data cancels on both sides, and there is
no dependence on GPS altitude, which carries its own several-metre bias.
`home_amsl_crosscheck()` compares that against the vehicle's own AMSL-minus-
relative figure so a wrong home position or a missing tile is still caught.

FILE FORMAT (verified empirically against terrain.ardupilot.org output,
not from remembered constants -- see the block-overlap assertion in
_load_tile, which fails loudly if a future file disagrees)
-------------------------------------------------------------------------
Each .DAT is a flat sequence of 2048-byte blocks:

    offset  0  uint64  bitmap        (0x00ffffffffffffff = 56 4x4 subgrids)
    offset  8  int32   lat_e7        SW corner of the block
    offset 12  int32   lon_e7
    offset 16  uint16  crc
    offset 18  uint16  version       (== 1)
    offset 20  uint16  spacing       (metres between grid posts, e.g. 100)
    offset 22  int16   height[28][32]  x = north, y = east; flat x*32 + y
    ...                              remainder is padding

Blocks are ordered row-major: index = grid_idx_x * blocks_per_row + grid_idx_y,
stepping 24 cells north per x and 28 cells east per y -- a 4-cell overlap
between neighbours in both directions. Because blocks overlap, a cell can be
visited twice; that is harmless when all we take is a maximum.

Longitude degrees-per-cell is derived from each block's OWN corner latitude,
because the generator re-derives the longitude scale per latitude row (the
tile is an equidistant-in-metres grid, not a regular lat/lon grid).
"""

import math
import os
from collections import namedtuple

import numpy as np

# --- Format constants (all verified against real files) --------------------

BLOCK_BYTES = 2048
GRID_X = 28  # north
GRID_Y = 32  # east
HEIGHTS_OFF = 22
HEIGHTS_N = GRID_X * GRID_Y  # 896
BLOCK_STRIDE_X = 24  # cells north between consecutive blocks
BLOCK_STRIDE_Y = 28  # cells east
EXPECTED_VERSION = 1

# Metres per degree of latitude, matching ArduPilot's LOCATION_SCALING_FACTOR
# (1e7 * 0.011131884502145034), so cell positions land where the generator
# put them rather than a few metres off.
M_PER_DEG_LAT = 111318.84502145034

# Heights at or below this are "no data" rather than a real elevation.
VOID_THRESHOLD = -30000

# --- Tuning: the vertical budget -------------------------------------------
#
# The clearance requirement is a BUDGET of named error sources plus a real
# safety buffer, not one guessed number -- so each term can be argued with,
# measured, and revised on its own. Summed linearly rather than in quadrature:
# baro drift and altitude-hold error are systematic and can align, and RSS
# would report ~30 m for the same terms, quietly halving the protection.

# SRTM v3 published absolute vertical accuracy (LE90).
DEM_VERTICAL_ERROR_M = 16.0
# Structures a radar-derived surface model does not contain -- masts, towers,
# power lines. Site-specific; raise it for built-up or wooded areas.
UNMAPPED_OBSTACLE_M = 15.0
# Barometric drift between arming and the far end of a sortie, as pressure and
# temperature move. LocationGlobalRelative altitude is baro-derived.
BARO_DRIFT_M = 15.0
# Fixed-wing altitude-hold error, worst case in turns and thermals.
ALTITUDE_HOLD_ERROR_M = 15.0
# Note there is deliberately NO term for .DAT resampling: measured against the
# 30 m .hgt tiles for this site the 100 m posts run mean +3.3 m / max +8 m,
# i.e. biased HIGH, which is the safe direction. Not banked, not paid for.
ERROR_BUDGET_M = (
    DEM_VERTICAL_ERROR_M + UNMAPPED_OBSTACLE_M + BARO_DRIFT_M + ALTITUDE_HOLD_ERROR_M
)  # 61 m

# The margin actually being flown with, on top of the error budget.
SAFETY_BUFFER_M = 60.0

MIN_CLEARANCE_M = ERROR_BUDGET_M + SAFETY_BUFFER_M  # 121 m

# Margin below which a route is allowed but flagged. A binary pass/fail gives
# the operator no warning of a route that only just clears.
CAUTION_MARGIN_M = 50.0

# --- Tuning: the lateral buffer --------------------------------------------
#
# Sized from MEASURED tracking error, not from a round number. The [bot-sync]
# logs for this airframe show the aircraft sitting 1084-1234 m from the point
# it is being commanded to (groundspeed pacing holds whatever separation the
# initial turn-in opened up, and never closes it). Terrain under the commanded
# line is irrelevant when the aircraft is a kilometre off it, so a buffer
# below the tracking error would be self-deception. On top of that sit a
# ~200 m turn radius and up to ~93 m of collision-avoidance displacement
# (UAV_COLLISION_AVOID_GAIN).
#
# Revisit this if the pacing lag is ever closed -- but re-measure, don't guess.
LEG_HALF_WIDTH_M = 1000.0

# Added to WP_LOITER_RAD when checking the loiter disc: same tracking error,
# plus orbit overshoot and wind drift.
LOITER_MARGIN_M = 1000.0

# If more than this fraction of the sampled cells are void/missing, the
# region is reported unknown rather than clear -- absence of data is not
# evidence of flat ground.
MAX_VOID_FRACTION = 0.02


Verdict = namedtuple(
    "Verdict",
    [
        "safe",  # bool -- False means refuse the command (level == BLOCK)
        "level",  # "OK" | "CAUTION" | "BLOCK"
        "reason",  # short human-readable string
        "terrain_max_amsl",  # highest terrain found, metres AMSL
        "terrain_rise",  # that height above the home datum
        "required_rel_alt",  # the MSA: terrain_rise + MIN_CLEARANCE_M
        "commanded_rel_alt",  # what was going to be sent
        "margin",  # commanded - required; negative = BLOCK
        "location",  # (lat, lon) of the offending max, for the message
        "cells",  # how many grid cells were examined
        "void_fraction",
    ],
)


class TerrainUnavailable(Exception):
    """No tile covers a point that had to be checked. Never swallow this --
    an unchecked region must not be reported as clear."""


class TerrainDB:
    """Lazily-loaded, cached reader over a directory of ArduPilot .DAT tiles."""

    def __init__(self, terrain_dir, min_clearance_m=MIN_CLEARANCE_M):
        self.terrain_dir = terrain_dir
        self.min_clearance_m = float(min_clearance_m)
        self._tiles = {}  # "N26E070" -> dict or None (known-missing)

    # -- tile loading ------------------------------------------------------

    @staticmethod
    def tile_name(lat, lon):
        la, lo = int(math.floor(lat)), int(math.floor(lon))
        ns = f"N{la:02d}" if la >= 0 else f"S{abs(la):02d}"
        ew = f"E{lo:03d}" if lo >= 0 else f"W{abs(lo):03d}"
        return f"{ns}{ew}"

    def _find_tile_file(self, name):
        """(path, kind) for the first readable tile of either format, or
        (None, None). ArduPilot .DAT is preferred only because it is what the
        autopilot itself carries; SRTM .hgt is finer (30 m posts vs 100 m) and
        is used whenever a .DAT is absent -- which is what stops a shifted
        operating area from becoming an unmapped one."""
        for ext, kind in (
            (".DAT", "dat"),
            (".dat", "dat"),
            (".hgt", "hgt"),
            (".HGT", "hgt"),
        ):
            path = os.path.join(self.terrain_dir, name + ext)
            if os.path.exists(path):
                return path, kind
        return None, None

    def _load_tile(self, name):
        if name in self._tiles:
            return self._tiles[name]
        path, kind = self._find_tile_file(name)
        if path is None:
            self._tiles[name] = None
            return None
        tile = self._load_dat(path) if kind == "dat" else self._load_hgt(path, name)
        self._tiles[name] = tile
        return tile

    def _load_hgt(self, path, name):
        """SRTM .hgt: one square of big-endian int16 metres AMSL, 3601x3601
        (1 arc-second) or 1201x1201 (3 arc-second), row 0 at the NORTH edge.

        Presented as a single patch in the same shape the .DAT blocks use, so
        every query below works on either format unchanged. The raw array is
        flipped vertically because the rest of this module indexes north-
        ascending (x = 0 at the tile's southern edge), matching .DAT blocks.
        """
        size = os.path.getsize(path)
        n = int(round(math.sqrt(size / 2.0)))
        if n * n * 2 != size or n not in (1201, 3601):
            raise ValueError(f"{path}: {size} bytes is not a square SRTM tile")

        raw = np.fromfile(path, dtype=">i2").reshape(n, n)
        heights = np.ascontiguousarray(raw[::-1, :]).reshape(1, n, n)

        lat0 = float(int(name[1:3]) * (1 if name[0] in "Nn" else -1))
        lon0 = float(int(name[4:7]) * (1 if name[3] in "Ee" else -1))
        step = 1.0 / (n - 1)  # degrees per post, both axes

        return {
            "path": path,
            "kind": "hgt",
            "heights": heights,
            "nx": n,
            "ny": n,
            "lat0": np.array([lat0]),
            "lon0": np.array([lon0]),
            "dlat_cell": step,
            "dlon_cell": np.array([step]),
            "spacing_m": step * M_PER_DEG_LAT,
            "nblocks": 1,
            "blocks_per_row": 1,
            "lat_hi": np.array([lat0 + 1.0]),
            "lon_hi": np.array([lon0 + 1.0]),
        }

    def _load_dat(self, path):
        raw = np.fromfile(path, dtype=np.uint8)
        if raw.size % BLOCK_BYTES:
            raise ValueError(
                f"{path}: size {raw.size} is not a multiple of {BLOCK_BYTES}"
            )
        raw = raw.reshape(-1, BLOCK_BYTES)
        nblocks = raw.shape[0]

        lat_e7 = np.ascontiguousarray(raw[:, 8:12]).view("<i4").ravel()
        lon_e7 = np.ascontiguousarray(raw[:, 12:16]).view("<i4").ravel()
        version = np.ascontiguousarray(raw[:, 18:20]).view("<u2").ravel()
        spacing = np.ascontiguousarray(raw[:, 20:22]).view("<u2").ravel()

        if not np.all(version == EXPECTED_VERSION):
            raise ValueError(
                f"{path}: unexpected terrain format version(s) "
                f"{sorted(set(version.tolist()))}"
            )
        if len(set(spacing.tolist())) != 1:
            raise ValueError(
                f"{path}: mixed grid spacings {sorted(set(spacing.tolist()))}"
            )
        spacing_m = float(spacing[0])

        heights = (
            np.ascontiguousarray(raw[:, HEIGHTS_OFF : HEIGHTS_OFF + HEIGHTS_N * 2])
            .view("<i2")
            .reshape(nblocks, GRID_X, GRID_Y)
        )

        # blocks_per_row: how many blocks share the southernmost latitude.
        first = lat_e7[0]
        diff = np.nonzero(lat_e7 != first)[0]
        blocks_per_row = int(diff[0]) if diff.size else nblocks
        if blocks_per_row <= 0 or nblocks % blocks_per_row:
            raise ValueError(
                f"{path}: {nblocks} blocks not divisible by row width "
                f"{blocks_per_row}"
            )

        # Assert the documented overlap actually holds, so a format change is
        # caught here rather than silently producing wrong clearances.
        if nblocks > blocks_per_row + 1:
            a, b, c = heights[0], heights[1], heights[blocks_per_row]
            if not np.array_equal(
                a[:, BLOCK_STRIDE_Y:GRID_Y], b[:, 0 : GRID_Y - BLOCK_STRIDE_Y]
            ):
                raise ValueError(
                    f"{path}: east block overlap mismatch -- layout changed"
                )
            if not np.array_equal(
                a[BLOCK_STRIDE_X:GRID_X, :], c[0 : GRID_X - BLOCK_STRIDE_X, :]
            ):
                raise ValueError(
                    f"{path}: north block overlap mismatch -- layout changed"
                )

        lat0 = lat_e7 / 1e7
        lon0 = lon_e7 / 1e7
        dlat_cell = spacing_m / M_PER_DEG_LAT
        # Per-block longitude scale, from each block's own corner latitude.
        dlon_cell = spacing_m / (M_PER_DEG_LAT * np.cos(np.radians(lat0)))

        return {
            "path": path,
            "kind": "dat",
            "heights": heights,
            "nx": GRID_X,
            "ny": GRID_Y,
            "lat0": lat0,
            "lon0": lon0,
            "dlat_cell": dlat_cell,
            "dlon_cell": dlon_cell,
            "spacing_m": spacing_m,
            "nblocks": nblocks,
            "blocks_per_row": blocks_per_row,
            # Block footprints, for intersection tests.
            "lat_hi": lat0 + (GRID_X - 1) * dlat_cell,
            "lon_hi": lon0 + (GRID_Y - 1) * dlon_cell,
        }

    def tiles_for_bbox(self, lat_min, lat_max, lon_min, lon_max):
        names = []
        for la in range(int(math.floor(lat_min)), int(math.floor(lat_max)) + 1):
            for lo in range(int(math.floor(lon_min)), int(math.floor(lon_max)) + 1):
                names.append(self.tile_name(la, lo))
        return names

    # -- raw queries -------------------------------------------------------

    def max_in_bbox(self, lat_min, lat_max, lon_min, lon_max, allow_partial=False):
        """(max_amsl, argmax_latlon, n_cells, n_void) over a lat/lon box.

        Raises TerrainUnavailable if any tile covering the box is missing,
        unless allow_partial -- in which case the maximum over the tiles that
        ARE present is returned. Use allow_partial only where a box is a
        deliberately generous "somewhere around here" region whose edges are
        expected to fall off the installed data (the altitude gate's
        half-degree box around the origin); never for a route, where a gap in
        coverage is exactly the case that must fail closed.
        """
        best = None
        best_at = None
        n_cells = 0
        n_void = 0
        missing = []

        for name in self.tiles_for_bbox(lat_min, lat_max, lon_min, lon_max):
            tile = self._load_tile(name)
            if tile is None:
                missing.append(name)
                continue

            # Blocks whose footprint intersects the box.
            sel = np.nonzero(
                (tile["lat_hi"] >= lat_min)
                & (tile["lat0"] <= lat_max)
                & (tile["lon_hi"] >= lon_min)
                & (tile["lon0"] <= lon_max)
            )[0]
            for bi in sel:
                lat0 = tile["lat0"][bi]
                lon0 = tile["lon0"][bi]
                dla = tile["dlat_cell"]
                dlo = tile["dlon_cell"][bi]

                x0 = max(0, int(math.floor((lat_min - lat0) / dla)))
                x1 = min(tile["nx"] - 1, int(math.ceil((lat_max - lat0) / dla)))
                y0 = max(0, int(math.floor((lon_min - lon0) / dlo)))
                y1 = min(tile["ny"] - 1, int(math.ceil((lon_max - lon0) / dlo)))
                if x0 > x1 or y0 > y1:
                    continue

                sub = tile["heights"][bi, x0 : x1 + 1, y0 : y1 + 1]
                valid = sub > VOID_THRESHOLD
                n_cells += sub.size
                n_void += int(sub.size - valid.sum())
                if not valid.any():
                    continue
                masked = np.where(valid, sub, np.int16(VOID_THRESHOLD))
                idx = int(np.argmax(masked))
                val = int(masked.flat[idx])
                if best is None or val > best:
                    best = val
                    dx, dy = divmod(idx, sub.shape[1])
                    best_at = (lat0 + (x0 + dx) * dla, lon0 + (y0 + dy) * dlo)

        if missing and best is None:
            raise TerrainUnavailable(
                f"no terrain tile(s) {', '.join(sorted(set(missing)))} in {self.terrain_dir}"
            )
        if missing and not allow_partial:
            raise TerrainUnavailable(
                f"region only partly covered -- missing tile(s) "
                f"{', '.join(sorted(set(missing)))}"
            )
        return best, best_at, n_cells, n_void

    def max_in_disc(self, lat, lon, radius_m, allow_partial=False):
        """Same, restricted to a true circle rather than its bounding box."""
        dlat = radius_m / M_PER_DEG_LAT
        dlon = radius_m / (M_PER_DEG_LAT * max(math.cos(math.radians(lat)), 1e-6))
        lat_min, lat_max = lat - dlat, lat + dlat
        lon_min, lon_max = lon - dlon, lon + dlon

        best = None
        best_at = None
        n_cells = 0
        n_void = 0
        missing = []
        cos_lat = math.cos(math.radians(lat))

        for name in self.tiles_for_bbox(lat_min, lat_max, lon_min, lon_max):
            tile = self._load_tile(name)
            if tile is None:
                missing.append(name)
                continue
            sel = np.nonzero(
                (tile["lat_hi"] >= lat_min)
                & (tile["lat0"] <= lat_max)
                & (tile["lon_hi"] >= lon_min)
                & (tile["lon0"] <= lon_max)
            )[0]
            for bi in sel:
                lat0 = tile["lat0"][bi]
                lon0 = tile["lon0"][bi]
                dla = tile["dlat_cell"]
                dlo = tile["dlon_cell"][bi]
                x0 = max(0, int(math.floor((lat_min - lat0) / dla)))
                x1 = min(tile["nx"] - 1, int(math.ceil((lat_max - lat0) / dla)))
                y0 = max(0, int(math.floor((lon_min - lon0) / dlo)))
                y1 = min(tile["ny"] - 1, int(math.ceil((lon_max - lon0) / dlo)))
                if x0 > x1 or y0 > y1:
                    continue

                sub = tile["heights"][bi, x0 : x1 + 1, y0 : y1 + 1]
                xs = lat0 + (np.arange(x0, x1 + 1) * dla)
                ys = lon0 + (np.arange(y0, y1 + 1) * dlo)
                north = (xs - lat) * M_PER_DEG_LAT
                east = (ys - lon) * M_PER_DEG_LAT * cos_lat
                d2 = north[:, None] ** 2 + east[None, :] ** 2
                inside = (d2 <= radius_m * radius_m) & (sub > VOID_THRESHOLD)
                n_cells += int((d2 <= radius_m * radius_m).sum())
                n_void += int(
                    ((d2 <= radius_m * radius_m) & (sub <= VOID_THRESHOLD)).sum()
                )
                if not inside.any():
                    continue
                masked = np.where(inside, sub, np.int16(VOID_THRESHOLD))
                idx = int(np.argmax(masked))
                val = int(masked.flat[idx])
                if best is None or val > best:
                    best = val
                    dx, dy = divmod(idx, sub.shape[1])
                    best_at = (xs[dx], ys[dy])

        if missing and (best is None or not allow_partial):
            raise TerrainUnavailable(
                f"missing terrain tile(s) {', '.join(sorted(set(missing)))}"
            )
        if best is None and not n_cells:
            # Radius smaller than the grid spacing, so no post centre landed
            # inside the circle. Fall back to the nearest post rather than
            # reporting well-covered ground as "no data".
            val = self.nearest(lat, lon)
            if val is not None:
                return val, (lat, lon), 1, 0
            return None, (lat, lon), 1, 1
        return best, best_at, n_cells, n_void

    def max_along_corridor(self, lat1, lon1, lat2, lon2, half_width_m):
        """Max terrain within half_width_m of the segment (lat1,lon1)-(lat2,lon2).

        Walked as overlapping discs of radius half_width_m spaced half that
        apart, which covers the full corridor width (a point at perpendicular
        distance d between two centres spaced s is within sqrt((s/2)^2 + d^2)
        of the nearer one, so s = w/2 covers d up to 0.968w).
        """
        cos_lat = math.cos(math.radians((lat1 + lat2) / 2.0))
        north = (lat2 - lat1) * M_PER_DEG_LAT
        east = (lon2 - lon1) * M_PER_DEG_LAT * cos_lat
        length = math.hypot(north, east)

        step = max(half_width_m / 2.0, 1.0)
        n = max(1, int(math.ceil(length / step)))

        best = None
        best_at = None
        n_cells = 0
        n_void = 0
        for k in range(n + 1):
            t = k / float(n)
            plat = lat1 + (lat2 - lat1) * t
            plon = lon1 + (lon2 - lon1) * t
            val, at, cells, void = self.max_in_disc(plat, plon, half_width_m)
            n_cells += cells
            n_void += void
            if val is not None and (best is None or val > best):
                best, best_at = val, at
        return best, best_at, n_cells, n_void

    def nearest(self, lat, lon):
        """Elevation of the grid post nearest (lat, lon), or None.

        Not expressible as a tiny max_in_disc: posts are `spacing` metres
        apart, so any disc smaller than that contains no post centre at all
        and would report "no data" for perfectly well-covered ground.
        """
        tile = self._load_tile(self.tile_name(lat, lon))
        if tile is None:
            raise TerrainUnavailable(
                f"missing terrain tile {self.tile_name(lat, lon)} in {self.terrain_dir}"
            )
        dla = tile["dlat_cell"]
        if tile["kind"] == "hgt":
            # One patch covering the whole degree square.
            bi = 0
        else:
            # Locate the .DAT block by its row/column grid, so this stays O(1)
            # instead of scanning ~1800 block headers per lookup.
            bpr = tile["blocks_per_row"]
            nrows = tile["nblocks"] // bpr
            gx = int((lat - tile["lat0"][0]) / (BLOCK_STRIDE_X * dla))
            gx = max(0, min(nrows - 1, gx))
            row = slice(gx * bpr, (gx + 1) * bpr)
            gy = int(np.searchsorted(tile["lon0"][row], lon, side="right")) - 1
            gy = max(0, min(bpr - 1, gy))
            bi = gx * bpr + gy

        x = int(round((lat - tile["lat0"][bi]) / dla))
        y = int(round((lon - tile["lon0"][bi]) / tile["dlon_cell"][bi]))
        x = max(0, min(tile["nx"] - 1, x))
        y = max(0, min(tile["ny"] - 1, y))
        val = int(tile["heights"][bi, x, y])
        return None if val <= VOID_THRESHOLD else val

    def elevation(self, lat, lon):
        """Terrain elevation at a single point, metres AMSL, or None."""
        return self.nearest(lat, lon)


# --- Clearance checks ------------------------------------------------------


def _verdict(db, terrain_max, at, cells, void, home_elev, commanded_rel_alt, what):
    if terrain_max is None:
        return Verdict(
            False,
            "BLOCK",
            f"{what}: no terrain data",
            None,
            None,
            None,
            commanded_rel_alt,
            None,
            at,
            cells,
            1.0,
        )
    if home_elev is None:
        # Without the home datum there is nothing to express the commanded
        # relative altitude against, so nothing can be declared clear.
        return Verdict(
            False,
            "BLOCK",
            f"{what}: home datum unknown -- cannot convert commanded "
            f"relative altitude to AMSL",
            terrain_max,
            None,
            None,
            commanded_rel_alt,
            None,
            at,
            cells,
            0.0,
        )

    void_fraction = (void / float(cells)) if cells else 0.0
    rise = terrain_max - home_elev
    required = rise + db.min_clearance_m
    margin = commanded_rel_alt - required

    if void_fraction > MAX_VOID_FRACTION:
        return Verdict(
            False,
            "BLOCK",
            f"{what}: {void_fraction:.0%} of the region has no terrain " f"data",
            terrain_max,
            rise,
            required,
            commanded_rel_alt,
            margin,
            at,
            cells,
            void_fraction,
        )
    if margin < 0:
        return Verdict(
            False,
            "BLOCK",
            f"{what}: terrain reaches {terrain_max} m AMSL "
            f"({rise:+.0f} m above home) at {at[0]:.5f},{at[1]:.5f}; "
            f"needs {required:.0f} m but commanded {commanded_rel_alt:.0f} m "
            f"({margin:.0f} m short)",
            terrain_max,
            rise,
            required,
            commanded_rel_alt,
            margin,
            at,
            cells,
            void_fraction,
        )
    if margin < CAUTION_MARGIN_M:
        # Allowed, but said out loud: this route only just clears, and every
        # term in the error budget is already spent getting it there.
        return Verdict(
            True,
            "CAUTION",
            f"{what}: only {margin:.0f} m above the {required:.0f} m minimum "
            f"(terrain {terrain_max} m AMSL at {at[0]:.5f},{at[1]:.5f})",
            terrain_max,
            rise,
            required,
            commanded_rel_alt,
            margin,
            at,
            cells,
            void_fraction,
        )
    return Verdict(
        True,
        "OK",
        f"{what}: clear by {margin:.0f} m",
        terrain_max,
        rise,
        required,
        commanded_rel_alt,
        margin,
        at,
        cells,
        void_fraction,
    )


def check_leg(
    db, home_elev, start, goal, commanded_rel_alt, half_width_m=LEG_HALF_WIDTH_M
):
    """The corridor swept while flying from `start` to `goal` (both (lat, lon))."""
    t_max, at, cells, void = db.max_along_corridor(
        start[0], start[1], goal[0], goal[1], half_width_m
    )
    return _verdict(db, t_max, at, cells, void, home_elev, commanded_rel_alt, "leg")


def check_loiter(
    db,
    home_elev,
    center,
    loiter_radius_m,
    commanded_rel_alt,
    margin_m=LOITER_MARGIN_M,
    allow_partial=False,
):
    """The disc the aircraft orbits once it arrives at `center`."""
    t_max, at, cells, void = db.max_in_disc(
        center[0], center[1], loiter_radius_m + margin_m, allow_partial=allow_partial
    )
    return _verdict(db, t_max, at, cells, void, home_elev, commanded_rel_alt, "loiter")


def check_around(
    db, home_elev, center, radius_m, commanded_rel_alt, allow_partial=True
):
    """Terrain within radius_m of a point the aircraft is currently at.

    Used for altitude changes, where there is no route to check -- only where
    the aircraft is right now. Defaults to allow_partial because this disc is
    a "near here" region whose edge may legitimately run off the installed
    tiles, unlike a route.
    """
    t_max, at, cells, void = db.max_in_disc(
        center[0], center[1], radius_m, allow_partial=allow_partial
    )
    return _verdict(db, t_max, at, cells, void, home_elev, commanded_rel_alt, "nearby")


def check_area(
    db,
    home_elev,
    lat_min,
    lat_max,
    lon_min,
    lon_max,
    commanded_rel_alt,
    allow_partial=False,
):
    """One bounding box -- the whole operating area.

    allow_partial checks whatever the installed tiles cover instead of
    refusing outright; see TerrainDB.max_in_bbox for when that is appropriate.
    """
    t_max, at, cells, void = db.max_in_bbox(
        lat_min, lat_max, lon_min, lon_max, allow_partial=allow_partial
    )
    return _verdict(db, t_max, at, cells, void, home_elev, commanded_rel_alt, "area")


def route_msa(
    db,
    home_amsl,
    start,
    goals,
    loiter_radius_m,
    half_width_m=LEG_HALF_WIDTH_M,
    margin_m=LOITER_MARGIN_M,
):
    """Minimum safe altitude for a whole route, RELATIVE TO HOME.

    The planning counterpart to the check functions: instead of judging one
    proposed altitude, it returns the altitude the route actually requires --
    so the operator can be shown "this needs 289 m" while still drawing it,
    rather than finding out by having a command refused.

    Returns (msa_rel_alt, terrain_max_amsl, (lat, lon) of the governing peak),
    or (None, None, None) if there is nothing to measure. Propagates
    TerrainUnavailable: a route crossing unmapped ground has no MSA.
    """
    if home_amsl is None or not goals:
        return None, None, None

    worst = None
    worst_at = None
    point = start
    for goal in goals:
        t_max, at, _, _ = db.max_along_corridor(
            point[0], point[1], goal[0], goal[1], half_width_m
        )
        if t_max is not None and (worst is None or t_max > worst):
            worst, worst_at = t_max, at
        point = goal

    t_max, at, _, _ = db.max_in_disc(
        goals[-1][0], goals[-1][1], loiter_radius_m + margin_m
    )
    if t_max is not None and (worst is None or t_max > worst):
        worst, worst_at = t_max, at

    if worst is None:
        return None, None, None
    return (worst - home_amsl) + db.min_clearance_m, worst, worst_at


def home_amsl_crosscheck(
    db, home_lat, home_lon, vehicle_amsl, vehicle_rel_alt, tolerance_m=30.0
):
    """Compare the dataset's home elevation against the vehicle's own
    (AMSL - relative) figure. A large disagreement means a wrong home
    position, the wrong tile, or a GPS altitude problem -- any of which
    invalidates every clearance number below. Returns (ok, dataset, gps, diff).
    """
    dataset = db.elevation(home_lat, home_lon)
    if dataset is None or vehicle_amsl is None or vehicle_rel_alt is None:
        return False, dataset, None, None
    gps = vehicle_amsl - vehicle_rel_alt
    diff = gps - dataset
    return abs(diff) <= tolerance_m, dataset, gps, diff
