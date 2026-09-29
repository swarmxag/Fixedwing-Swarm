"""Step 4A of the terrain-safety system: which terrain is above the threshold.

Compares the terrain elevations of the current Origin's Step 2 grid with the
current Step 3 safety threshold and reports the cells with

    elevation > threshold        (strictly greater)

as ``{lat, lon, elevation}`` points.

Everything here works on the grid that already exists in memory: it never reads
SRTM, never rebuilds the grid, and never looks at the altitude logic -- the
threshold is handed in. Only cells inside the Origin polygon (the Step 2 grid
covers its bounding box, which can be larger) and with a valid elevation are
considered.

`TerrainScanIndex` is built once per Origin (a numpy copy of the grid plus an
"inside the Origin" mask). Each threshold change after that is one vectorised
comparison over that index.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import numpy as np
import shapely

from flockwave.server.geofence_validator import Fence

__all__ = ("EVENT_TYPE", "REQUEST_TYPE", "TerrainScanIndex", "safe_response", "unavailable_response")

EVENT_TYPE = "X-TERRAIN-UNSAFE-RESP"
REQUEST_TYPE = "X-TERRAIN-UNSAFE-REQ"

# Reported lat/lon are rounded to this many decimals (~1 cm): it does not
# change which cell a point is, and it roughly halves the JSON size.
COORD_DECIMALS = 7


def unavailable_response(origin_fingerprint: Optional[str] = None) -> Dict[str, Any]:
    """No active Origin / grid / threshold."""
    return _response("unavailable", None, [], origin_fingerprint)


def _response(
    status: str,
    threshold: Optional[float],
    points: List[Dict[str, float]],
    origin_fingerprint: Optional[str],
    highest: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "thresholdAMSL": threshold,
        "count": len(points),
        "unsafePoints": points,
        "maxUnsafeElevation": highest["elevation"] if highest else None,
        "highestPoint": highest,
        "originFingerprint": origin_fingerprint,
    }


def safe_response(threshold: float, origin_fingerprint: Optional[str] = None) -> Dict[str, Any]:
    return _response("safe", threshold, [], origin_fingerprint)


class TerrainScanIndex:
    """Scan-ready form of one Step 2 terrain grid.

    `cell_lat(row)` / `cell_lon(col)` must be the coordinate conversion Step 2
    used to lay the grid out (ext/terrain.py `_cell_lat` / `_cell_lon`, bound to
    this grid's bounds and spacing). They are applied to numpy index arrays, so
    the reported position of a cell is by construction the one Step 2 gave it.
    """

    def __init__(
        self,
        grid: Dict[str, Any],
        cell_lat: Callable[[Any], Any],
        cell_lon: Callable[[Any], Any],
    ) -> None:
        rows, cols = int(grid["rows"]), int(grid["cols"])
        elevations = np.array(grid["grid"], dtype=float)  # a missing cell (None) becomes NaN
        if elevations.shape != (rows, cols):
            raise ValueError(f"grid is {elevations.shape}, expected {(rows, cols)}")

        self.rows, self.cols = rows, cols
        self.cell_lat, self.cell_lon = cell_lat, cell_lon
        self.cell_size_m = float(grid["spacing_m"])
        self._origin_latlon = grid.get("polygon")
        self._clip_region = None  # built lazily by clip_region()

        lons, lats = np.meshgrid(cell_lon(np.arange(cols)), cell_lat(np.arange(rows)))
        try:
            # The existing Origin fence class (boundary counts as inside).
            fence = Fence([(lat, lon) for lat, lon in grid["polygon"]], label="origin")
            inside = shapely.intersects_xy(fence.polygon.context, lons, lats)
            self.area = "origin_polygon"
        except (ValueError, TypeError, KeyError):
            inside = np.ones((rows, cols), dtype=bool)  # unusable polygon: whole grid area
            self.area = "grid_bounding_box"

        # -inf marks a cell that can never be unsafe: no elevation, or outside
        # the Origin. Everything else keeps its elevation.
        valid = inside & ~np.isnan(elevations)
        self._scan = np.where(valid, elevations, -np.inf)
        self.checked_cells = int(valid.sum())

        # A cell inside the Origin with NO elevation (an SRTM void) is -inf
        # above, so it can never compare as unsafe -- it is reported as safe
        # terrain while in truth it is UNSURVEYED. Voids cluster on steep slopes
        # and in radar shadow, i.e. exactly where terrain is dangerous, so the
        # count has to reach the operator rather than only a server log.
        self.origin_cells = int(inside.sum())
        self.void_cells = int((inside & np.isnan(elevations)).sum())

    @property
    def void_fraction(self) -> float:
        """Share of the Origin with no elevation data at all, 0.0 .. 1.0. A
        response that reports "safe" over a high void fraction has verified very
        little; the frontend surfaces this rather than implying full coverage."""
        return self.void_cells / self.origin_cells if self.origin_cells else 0.0

    def coverage(self) -> Dict[str, Any]:
        """Data-coverage facts to attach to any response built from this index,
        whatever its status -- "safe" needs them at least as much as "unsafe"."""
        return {
            "originCellCount": self.origin_cells,
            "checkedCellCount": self.checked_cells,
            "voidCellCount": self.void_cells,
            "voidFraction": round(self.void_fraction, 6),
        }

    def unsafe_cells(self, threshold: float):
        """(flat indices, elevations) of the checked cells with elevation >
        threshold, in row-major order (north first). The one place "unsafe" is
        decided: the point list (`scan`) and the area grouping (Step 4B) both
        start from exactly this."""
        hits = np.flatnonzero(self._scan > float(threshold))
        return hits, self._scan.ravel()[hits]

    def clip_region(self):
        """The Origin operating area as a shapely polygon in cell-index space
        (x = column, y = row, one unit per cell), prepared for fast predicates.

        Cell (row, col) is the unit square centred on (col, row). The Step 2
        mapping is linear, so the Origin polygon's straight edges stay straight
        when converted; `cell_lat` / `cell_lon` map any (fractional) index back.
        When the Origin polygon was unusable (`area` is "grid_bounding_box") the
        region is the whole grid instead.
        """
        if self._clip_region is None:
            if self.area == "origin_polygon":
                lat0, lat1 = np.asarray(self.cell_lat(np.array([0.0, 1.0]))).tolist()
                lon0, lon1 = np.asarray(self.cell_lon(np.array([0.0, 1.0]))).tolist()
                ring = [((lon - lon0) / (lon1 - lon0), (lat0 - lat) / (lat0 - lat1)) for lat, lon in self._origin_latlon]
                region = shapely.Polygon(ring)
            else:
                region = shapely.box(-0.5, -0.5, self.cols - 0.5, self.rows - 0.5)
            shapely.prepare(region)
            self._clip_region = region
        return self._clip_region

    def scan(self, threshold: float, origin_fingerprint: Optional[str] = None) -> Dict[str, Any]:
        """Every checked cell with elevation > threshold, plus the highest one,
        from a single pass. No grid regeneration, no SRTM access."""
        threshold = float(threshold)
        hits, elevation = self.unsafe_cells(threshold)  # flat, row-major (north first)
        if hits.size == 0:
            return safe_response(threshold, origin_fingerprint)

        rows, cols = np.divmod(hits, self.cols)
        lat = np.round(self.cell_lat(rows), COORD_DECIMALS).tolist()
        lon = np.round(self.cell_lon(cols), COORD_DECIMALS).tolist()
        elev = elevation.tolist()

        points = [{"lat": a, "lon": b, "elevation": c} for a, b, c in zip(lat, lon, elev)]
        highest = points[int(np.argmax(elevation))]  # first of the highest, in scan order
        return _response("unsafe", threshold, points, origin_fingerprint, dict(highest))
