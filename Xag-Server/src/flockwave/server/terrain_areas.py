"""Step 4B of the terrain-safety system: unsafe terrain as compact areas.

Step 4A decides which grid cells are unsafe (elevation > threshold, inside the
Origin, valid elevation). On real terrain that can be hundreds of thousands of
cells -- tens of MB as individual points. This module turns exactly those cells
into a handful of polygons that a map can draw directly.

Pipeline (all on the in-memory Step 2 grid; no SRTM, no new grid):

1. Runs        consecutive unsafe cells of a row become one horizontal run.
2. Components  runs of adjacent rows that share at least one column (i.e. cells
               sharing an EDGE: 4-neighbour connectivity) are joined with
               union-find. Cells touching only at a corner stay separate.
3. Outlines    per component, the union of its runs' rectangles is the exact
               outline of the unsafe cells, holes included; collinear vertices
               (left over from stacking row rectangles) are then removed, which
               changes nothing about the shape. Everything is done in cell-index
               space (x = column, y = row, one unit = one cell = `spacing_m`
               metres), where a cell is the unit square around its grid point.
               Vertices are turned into lat/lon with the very same `_cell_lat` /
               `_cell_lon` mapping Step 2 uses (they are linear, so fractional
               indices -- cell corners -- map correctly).
4. Simplify    optional and OFF by default (SIMPLIFY_TOLERANCE_M = 0). With a
               tolerance, an outline with more than EXACT_VERTEX_LIMIT vertices
               is simplified OUTWARD: it is first grown by the tolerance (mitre
               joins) and then Douglas-Peucker-simplified with a tolerance no
               larger than that growth. Every point of the exact outline is then
               inside the result (unsafe terrain can never be cut off), and the
               result is at most about twice the tolerance outside it. Small
               outlines stay exact. Measured on the real 717x845 grid, a
               tolerance below ~14 m (0.7 cell) cannot collapse a 20 m staircase
               and only adds false-unsafe area, so exact outlines are the default.
5. Clip        every polygon is intersected with the Origin polygon, so nothing
               red is ever outside the Origin, whatever growth or cell-square
               overhang happened before.

Components are simplified one by one, so two regions that only touch at a corner
remain two areas (their grown outlines may overlap by a few metres).

Severity is decided PER CELL before any of this (`classify_cell_severity`): RED
cells (above the drone's own altitude AMSL) and YELLOW cells (between it and the
threshold, i.e. inside the safety margin) run through steps 1-5 separately, so a
red area never contains a yellow or safe cell and one ridge can give a red area
on its top and yellow areas on its flanks. With a positive tolerance the grown
yellow outlines are cut back by the red ones, so the two never overlap.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import shapely

from flockwave.server.terrain_unsafe import COORD_DECIMALS, TerrainScanIndex

__all__ = (
    "EVENT_TYPE",
    "EXACT_VERTEX_LIMIT",
    "REQUEST_TYPE",
    "SIMPLIFY_TOLERANCE_M",
    "build_unsafe_areas",
    "classify_cell_severity",
    "safe_response",
    "unavailable_response",
)

EVENT_TYPE = "X-TERRAIN-UNSAFE-AREA-RESP"
REQUEST_TYPE = "X-TERRAIN-UNSAFE-AREA-REQ"

# Outward simplification tolerance in metres: simplified outlines lie 0 .. ~2 x
# this outside the exact unsafe cells, never inside. 0 (the default) = exact
# cell outlines, only lossless clean-up (collinear vertices). On the real grid
# the exact outlines are already 2-4.5x smaller than the raw union and at most
# ~100 KB; a positive tolerance trades accuracy for a further 10-50% (see the
# Step 4B report for the measured table).
SIMPLIFY_TOLERANCE_M = 0.0

# With a positive tolerance, outlines with at most this many coordinates (a ring
# counts its closing point; 24 = a shape with about 20 corners) are still left
# exact: single cells, rectangles, L shapes ... are never inflated.
EXACT_VERTEX_LIMIT = 24

# A clipped piece smaller than this (in cells^2) is numerical dust, not an area.
_MIN_PART_AREA = 1e-9


def unavailable_response(origin_fingerprint: Optional[str] = None) -> Dict[str, Any]:
    """No active Origin / grid / threshold."""
    return _response("unavailable", None, [], 0, None, origin_fingerprint)


def safe_response(
    threshold: float, origin_fingerprint: Optional[str] = None
) -> Dict[str, Any]:
    return _response("safe", float(threshold), [], 0, None, origin_fingerprint)


def _response(
    status: str,
    threshold: Optional[float],
    areas: List[Dict[str, Any]],
    unsafe_cells: int,
    highest: Optional[Dict[str, float]],
    origin_fingerprint: Optional[str],
    tolerance_m: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "thresholdAMSL": threshold,
        "areaCount": len(areas),
        "unsafeCellCount": unsafe_cells,
        "maxUnsafeElevation": highest["elevation"] if highest else None,
        "highestPoint": highest,
        "vertexCount": sum(
            len(a["polygon"]) - 1 + sum(len(h) - 1 for h in a["holes"]) for a in areas
        ),
        "simplifyToleranceM": tolerance_m,
        "areas": areas,
        "originFingerprint": origin_fingerprint,
    }


# --- 1 + 2: runs and 4-connected components ------------------------------------------


def _label_components(
    run_row: np.ndarray, run_c0: np.ndarray, run_c1: np.ndarray
) -> Tuple[np.ndarray, int]:
    """Component number of every run. Runs are sorted by (row, c0); `c1` is
    exclusive. Runs of consecutive rows are connected when their column ranges
    overlap by at least one column -- cells that share an edge. A run that only
    reaches the next row's run diagonally (c1 == other.c0) is NOT connected."""
    count = len(run_row)
    parent = list(range(count))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    row, c0, c1 = run_row.tolist(), run_c0.tolist(), run_c1.tolist()
    prev: Optional[Tuple[int, int, int]] = None  # (row, first run, one past last run)
    i = 0
    while i < count:
        r, j = row[i], i
        while j < count and row[j] == r:
            j += 1
        if prev is not None and prev[0] == r - 1:
            a, a_end, b, b_end = prev[1], prev[2], i, j
            while a < a_end and b < b_end:  # two-pointer sweep over both rows
                if c0[a] < c1[b] and c0[b] < c1[a]:
                    union(a, b)
                if c1[a] < c1[b]:
                    a += 1
                else:
                    b += 1
        prev = (r, i, j)
        i = j

    roots = np.fromiter((find(x) for x in range(count)), dtype=np.int64, count=count)
    _, comp = np.unique(roots, return_inverse=True)
    return comp.astype(np.int64), int(comp.max()) + 1


# --- 3 + 4 + 5: outlines, outward simplification, Origin clipping --------------------


def _component_outlines(comp_of_run, run_row, run_c0, run_c1, count) -> np.ndarray:
    """Exact outline (union of the run rectangles) of every component."""
    boxes = shapely.box(run_c0 - 0.5, run_row - 0.5, run_c1 - 0.5, run_row + 0.5)
    order = np.argsort(comp_of_run, kind="stable")
    bounds = np.searchsorted(comp_of_run[order], np.arange(count + 1))
    outlines = np.empty(count, dtype=object)
    for k in range(count):
        parts = boxes[order[bounds[k] : bounds[k + 1]]]
        outlines[k] = parts[0] if len(parts) == 1 else shapely.union_all(parts)
    # Lossless clean-up: stacking row rectangles leaves collinear vertices along
    # straight edges. Tolerance 0 removes exactly those and moves nothing.
    return shapely.simplify(outlines, 0.0, preserve_topology=True)


def _simplify_outward(outlines: np.ndarray, tolerance_cells: float) -> np.ndarray:
    """Outward-biased simplification of the complex outlines (see module doc)."""
    if tolerance_cells <= 0:
        return outlines
    complex_ = shapely.get_num_coordinates(outlines) > EXACT_VERTEX_LIMIT
    if complex_.any():
        grown = shapely.buffer(outlines[complex_], tolerance_cells, join_style="mitre")
        # simplification error < growth  =>  the exact outline stays inside
        outlines[complex_] = shapely.simplify(
            grown, tolerance_cells * 0.99, preserve_topology=True
        )
    return outlines


def _clip_to_origin(outlines: np.ndarray, region) -> np.ndarray:
    outside = ~shapely.covers(region, outlines)
    if outside.any():
        outlines[outside] = shapely.intersection(outlines[outside], region)
    invalid = ~shapely.is_valid(outlines)
    if invalid.any():
        outlines[invalid] = shapely.make_valid(outlines[invalid])
    return outlines


def _polygon_parts(geometry) -> List[Any]:
    return [
        g
        for g in shapely.get_parts(geometry)
        if g.geom_type == "Polygon" and g.area > _MIN_PART_AREA
    ]


# --- per-cell RED/YELLOW severity ------------------------------------------------------------


def classify_cell_severity(
    elevation: float,
    reference_terrain_elevation: float,
    safety_altitude: float,
    safety_margin: float,
) -> str:
    """ "red" / "yellow" / "safe" for ONE cell (its elevation already includes the
    terrain error buffer), with droneAMSL = reference_terrain_elevation + safety_altitude:

        red     elevation > droneAMSL                            the drone WILL hit it
        yellow  droneAMSL - margin < elevation <= droneAMSL      clears it, inside the margin
        safe    elevation <= droneAMSL - margin                  (= not above the threshold)

    `build_unsafe_areas` applies exactly this, vectorised, to every unsafe cell."""
    drone_amsl = reference_terrain_elevation + safety_altitude
    if elevation > drone_amsl:
        return "red"
    return "yellow" if elevation > drone_amsl - safety_margin else "safe"


# --- the whole of Step 4B ---------------------------------------------------------------


def _group_areas(
    index: TerrainScanIndex,
    hits: np.ndarray,
    elevation: np.ndarray,
    tolerance_cells: float,
    severity: Optional[str],
    rank: int,
    exclude: Any = None,
) -> Tuple[List[Tuple[Tuple[int, ...], Dict[str, Any]]], Any]:
    """Groups ONE class of cells (`hits`: sorted flat indices, `elevation`: theirs)
    into edge-connected areas. Returns ([(sort key, area)], union of the outlines).
    `exclude` (a geometry in cell-index space) is cut out of every outline before
    clipping, so a grown yellow outline never covers a red one."""
    n = int(hits.size)
    rows, cols = np.divmod(hits, index.cols)

    # 1. horizontal runs (consecutive flat indices within one row)
    is_start = np.ones(n, dtype=bool)
    is_start[1:] = (hits[1:] != hits[:-1] + 1) | (rows[1:] != rows[:-1])
    starts = np.flatnonzero(is_start)
    ends = np.append(starts[1:], n)
    run_row, run_c0, run_c1 = rows[starts], cols[starts], cols[ends - 1] + 1

    # 2. connected components
    comp_of_run, count = _label_components(run_row, run_c0, run_c1)
    cell_comp = np.repeat(comp_of_run, ends - starts)  # component of every cell

    # per-component statistics, one vectorised pass
    order = np.argsort(
        cell_comp, kind="stable"
    )  # groups cells; keeps scan order inside a group
    cell_count = np.bincount(cell_comp, minlength=count)
    group_start = np.concatenate(([0], np.cumsum(cell_count)[:-1]))
    e_sorted = elevation[order]
    group_max = np.maximum.reduceat(e_sorted, group_start)
    at_max = np.flatnonzero(e_sorted == np.repeat(group_max, cell_count))
    _, first = np.unique(cell_comp[order][at_max], return_index=True)
    best_cell = order[
        at_max[first]
    ]  # index into `hits`: first highest cell of each component

    def cell_point(cell: int) -> Dict[str, float]:
        return {
            "lat": float(np.round(index.cell_lat(rows[cell]), COORD_DECIMALS)),
            "lon": float(np.round(index.cell_lon(cols[cell]), COORD_DECIMALS)),
            "elevation": float(elevation[cell]),
        }

    # 3 - 5. outlines -> outward simplification -> (minus `exclude`) -> clip to the Origin
    outlines = _component_outlines(comp_of_run, run_row, run_c0, run_c1, count)
    outlines = _simplify_outward(outlines, tolerance_cells)
    if exclude is not None:
        outlines = shapely.difference(outlines, exclude)
    outlines = _clip_to_origin(outlines, index.clip_region())

    def ring(coords) -> List[List[float]]:
        xy = np.asarray(coords)
        lat = np.round(index.cell_lat(xy[:, 1]), COORD_DECIMALS)
        lon = np.round(index.cell_lon(xy[:, 0]), COORD_DECIMALS)
        return np.column_stack(
            (lat, lon)
        ).tolist()  # closed: first point repeated at the end

    entries = []  # (sort key, area)
    for k in range(count):
        parts = _polygon_parts(outlines[k])
        if not parts:
            continue
        component_cells = order[group_start[k] : group_start[k] + cell_count[k]]
        for part in parts:
            if len(parts) == 1:
                cells, max_elev, best = (
                    int(cell_count[k]),
                    float(group_max[k]),
                    int(best_cell[k]),
                )
            else:
                # Clipping split this component (a concave Origin): each piece gets
                # the statistics of the cells whose centres lie in it.
                inside = shapely.intersects_xy(
                    part, cols[component_cells], rows[component_cells]
                )
                mine = component_cells[inside]
                if mine.size == 0:
                    continue  # a sliver of a cell edge; its cell belongs to another piece
                cells = int(mine.size)
                max_elev = float(elevation[mine].max())
                best = int(mine[int(np.argmax(elevation[mine]))])
            area: Dict[str, Any] = {} if severity is None else {"severity": severity}
            area.update(
                {
                    "cellCount": cells,
                    "maxElevation": max_elev,
                    "highestPoint": cell_point(best),
                    "polygon": ring(part.exterior.coords),
                    "holes": [ring(h.coords) for h in part.interiors],
                }
            )
            entries.append(
                ((rank, -cells, int(hits[component_cells].min()), len(entries)), area)
            )

    return entries, shapely.union_all(outlines)


def build_unsafe_areas(
    index: TerrainScanIndex,
    threshold: float,
    origin_fingerprint: Optional[str] = None,
    tolerance_m: float = SIMPLIFY_TOLERANCE_M,
    drone_amsl: Optional[float] = None,
) -> Dict[str, Any]:
    """The unsafe terrain of `index` at `threshold` (= droneAMSL - margin) as
    connected areas with polygon outlines, computed from the same cells Step 4A
    reports.

    With `drone_amsl`, every unsafe cell is classified ON ITS OWN (see
    `classify_cell_severity`): cells above `drone_amsl` are RED, the rest are
    YELLOW, and the two classes are grouped into areas SEPARATELY -- a red area
    never contains a yellow or safe cell. Red areas come first. Without it
    (`None`) all unsafe cells form areas with no "severity" key, which a client
    draws red."""
    threshold = float(threshold)
    hits, elevation = index.unsafe_cells(threshold)  # exactly Step 4A's unsafe cells
    n = int(hits.size)
    if drone_amsl is not None and not math.isfinite(drone_amsl):
        drone_amsl = None
    red = (
        elevation > float(drone_amsl)
        if drone_amsl is not None
        else np.zeros(n, dtype=bool)
    )
    counts = {
        "redCellCount": int(red.sum()) if drone_amsl is not None else 0,
        "yellowCellCount": int(n - red.sum()) if drone_amsl is not None else 0,
        "droneAMSL": None if drone_amsl is None else float(drone_amsl),
        "terrainErrorBuffer": index.error_buffer_m,  # already included in every elevation
    }
    if n == 0:
        return {**safe_response(threshold, origin_fingerprint), **counts}

    tolerance_cells = max(0.0, float(tolerance_m)) / index.cell_size_m
    if drone_amsl is None:
        classes = [(None, np.ones(n, dtype=bool))]
    else:
        classes = [("red", red), ("yellow", ~red)]

    entries: List[Tuple[Tuple[int, ...], Dict[str, Any]]] = []
    red_cover = (
        None  # only needed when outlines are grown: exact cell outlines never overlap
    )
    for rank, (severity, mask) in enumerate(classes):
        if not mask.any():
            continue
        group, cover = _group_areas(
            index,
            hits[mask],
            elevation[mask],
            tolerance_cells,
            severity,
            rank,
            exclude=red_cover if severity == "yellow" else None,
        )
        entries.extend(group)
        if severity == "red" and tolerance_cells > 0:
            red_cover = cover

    entries.sort(
        key=lambda e: e[0]
    )  # red first, then biggest first; ties in scan order
    areas = [
        {"id": number, **area} for number, (_, area) in enumerate(entries, start=1)
    ]

    top = int(np.argmax(elevation))  # first highest unsafe cell overall
    row, col = divmod(int(hits[top]), index.cols)
    highest = {
        "lat": float(np.round(index.cell_lat(row), COORD_DECIMALS)),
        "lon": float(np.round(index.cell_lon(col), COORD_DECIMALS)),
        "elevation": float(elevation[top]),
    }
    return {
        **_response(
            "unsafe", threshold, areas, n, highest, origin_fingerprint, tolerance_m
        ),
        **counts,
    }
