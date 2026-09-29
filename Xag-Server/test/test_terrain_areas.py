"""Tests for Step 4B: unsafe terrain grouped into compact polygon areas
(flockwave.server.terrain_areas and its wiring into the terrain extension).

Step 4A decides which cells are unsafe (elevation > threshold, inside the Origin,
valid elevation); Step 4B only groups exactly those cells: 4-connected
components, outlined by polygons in the Step 2 lat/lon mapping, simplified
outward only, clipped to the Origin."""

import json
import os
import time
from types import SimpleNamespace

import numpy as np
import pytest
import shapely

from flockwave.server import terrain_areas as ta
from flockwave.server import terrain_safety as ts
from flockwave.server import terrain_unsafe as tu
from flockwave.server.ext import terrain as T

# reuse the 4A test helpers: a real Step 2 grid builder, fake terrain and fake app
from test_terrain_unsafe import (  # noqa: E402
    ORIGIN_A,
    ORIGIN_B,
    FakeApp,
    PatternTerrain,
    cell_pos,
    elevation_of,
    fake_uav,
    rect,
)

UNSAFE, SAFE = 600.0, 100.0
THRESHOLD = 500.0
MARGIN = 2  # safe cells around every test pattern, so no cell touches the Origin edge


def grid_from(tmp_path, art, polygon=None):
    """Real Step 2 grid from ASCII art: '#' = 600 m (unsafe at 500), '.' = 100 m,
    'x' = void (None). The art is embedded with a safe margin; returns
    (index, grid, offset) where art cell (i, j) is grid cell (i + MARGIN, j + MARGIN)."""
    rows = [list(line) for line in art]
    w = max(len(r) for r in rows)
    values = [[SAFE] * (w + 2 * MARGIN) for _ in range(MARGIN)]
    for r in rows:
        line = [SAFE] * MARGIN
        for ch in r + ["."] * (w - len(r)):
            line.append({"#": UNSAFE, ".": SAFE, "x": None}[ch])
        values.append(line + [SAFE] * MARGIN)
    values += [[SAFE] * (w + 2 * MARGIN) for _ in range(MARGIN)]
    return grid_from_values(tmp_path, values, polygon)


def grid_from_values(tmp_path, values, polygon=None):
    n, m = len(values), len(values[0])
    polygon = polygon or rect(n + 1, m + 1)  # +1: Step 2 rounds the size up; the extra row/col is outside
    padded = [list(r) + [999.0] for r in values] + [[999.0] * (m + 1)]
    mgr = PatternTerrain(tmp_path / "srtm", padded)
    lats, lons = [p[0] for p in polygon], [p[1] for p in polygon]
    mgr.bounds = {"min_lat": min(lats), "max_lat": max(lats), "min_lon": min(lons), "max_lon": max(lons)}
    grid = T._build_terrain_grid_sync(mgr, polygon, 20)
    grid["origin_fingerprint"], grid["polygon"] = "fp-test", polygon
    return T._build_unsafe_index_sync(grid), grid, MARGIN


def areas_of(tmp_path, art, threshold=THRESHOLD, **kw):
    index, grid, _ = grid_from(tmp_path, art, kw.pop("polygon", None))
    return ta.build_unsafe_areas(index, threshold, "fp-test", **kw), index, grid


def corners(grid, r, c, r2=None, c2=None):
    """Lat/lon of the outer corners of the cell block r..r2 x c..c2 (default one cell), by the Step 2 mapping."""
    r2 = r if r2 is None else r2
    c2 = c if c2 is None else c2
    b = grid["bounds"]
    dlat, dlon, _, _ = T._grid_shape(b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], 20)
    lats = [round(T._cell_lat(b["max_lat"], dlat, r - 0.5), 7), round(T._cell_lat(b["max_lat"], dlat, r2 + 0.5), 7)]
    lons = [round(T._cell_lon(b["min_lon"], dlon, c - 0.5), 7), round(T._cell_lon(b["min_lon"], dlon, c2 + 0.5), 7)]
    return {(la, lo) for la in lats for lo in lons}


def ring_points(ring):
    return {tuple(p) for p in ring}


def to_polygon(area):
    return shapely.Polygon(
        [(lo, la) for la, lo in area["polygon"]], [[(lo, la) for la, lo in h] for h in area["holes"]]
    )


# --- 1-6: grouping and connectivity ---------------------------------------------------------------


def test_one_unsafe_cell_gives_one_small_polygon(tmp_path):
    result, _, grid = areas_of(tmp_path, ["#"])
    assert (result["status"], result["areaCount"], result["unsafeCellCount"]) == ("unsafe", 1, 1)
    (area,) = result["areas"]
    assert (area["id"], area["cellCount"], area["holes"]) == (1, 1, [])
    assert area["polygon"][0] == area["polygon"][-1] and len(area["polygon"]) == 5  # a closed square
    assert ring_points(area["polygon"]) == corners(grid, MARGIN, MARGIN)  # exactly the cell's own square


def test_two_horizontally_adjacent_cells_are_one_polygon(tmp_path):
    result, _, grid = areas_of(tmp_path, ["##"])
    (area,) = result["areas"]
    assert result["areaCount"] == 1 and area["cellCount"] == 2
    assert ring_points(area["polygon"]) == corners(grid, MARGIN, MARGIN, MARGIN, MARGIN + 1)  # one 2x1 rectangle


def test_two_vertically_adjacent_cells_are_one_polygon(tmp_path):
    result, _, grid = areas_of(tmp_path, ["#", "#"])
    (area,) = result["areas"]
    assert result["areaCount"] == 1 and area["cellCount"] == 2
    assert ring_points(area["polygon"]) == corners(grid, MARGIN, MARGIN, MARGIN + 1, MARGIN)


def test_diagonal_only_cells_are_separate_polygons(tmp_path):
    result, _, grid = areas_of(tmp_path, ["#.", ".#"])
    assert result["areaCount"] == 2 and result["unsafeCellCount"] == 2
    assert [a["cellCount"] for a in result["areas"]] == [1, 1]
    assert {frozenset(ring_points(a["polygon"])) for a in result["areas"]} == {
        frozenset(corners(grid, MARGIN, MARGIN)), frozenset(corners(grid, MARGIN + 1, MARGIN + 1))
    }


def test_block_plus_a_cell_touching_only_at_a_corner_is_two_areas(tmp_path):
    # the documented example: four cells in one region, the diagonal cell separate
    result, _, _ = areas_of(tmp_path, ["##.", "##.", "..#"])
    assert result["areaCount"] == 2
    assert [a["cellCount"] for a in result["areas"]] == [4, 1]  # biggest first
    assert [a["id"] for a in result["areas"]] == [1, 2]


def test_corner_touching_regions_stay_separate_even_when_simplified(tmp_path):
    # Two big staircase triangles meeting at a single corner. Growing an outline
    # outward would fuse polygons that touch, so components must be outlined
    # (and simplified) one by one -- the connectivity rule is edge-sharing only.
    n = 12
    art = ["#" * (i + 1) for i in range(n)] + ["." * n + "#" * (i + 1) for i in range(n)]
    for tolerance in (0, 15):
        result, _, _ = areas_of(tmp_path, art, tolerance_m=tolerance)
        assert result["areaCount"] == 2, tolerance
        assert [a["cellCount"] for a in result["areas"]] == [78, 78]


def test_a_large_contiguous_block_is_one_polygon(tmp_path):
    result, _, grid = areas_of(tmp_path, ["#" * 40] * 30)
    (area,) = result["areas"]
    assert result["areaCount"] == 1 and area["cellCount"] == 1200 == result["unsafeCellCount"]
    assert len(area["polygon"]) == 5 and area["holes"] == []  # 1200 cells -> 4 corners
    assert ring_points(area["polygon"]) == corners(grid, MARGIN, MARGIN, MARGIN + 29, MARGIN + 39)


def test_multiple_disconnected_regions_are_returned_separately(tmp_path):
    art = ["###...#....", "###...#....", "......#....", "...........", "..##.......", "..##.......", "...........", "........#.."]
    result, _, _ = areas_of(tmp_path, art)
    assert result["areaCount"] == 4
    assert [a["cellCount"] for a in result["areas"]] == [6, 4, 3, 1]
    assert result["unsafeCellCount"] == 14 == sum(a["cellCount"] for a in result["areas"])
    assert [a["id"] for a in result["areas"]] == [1, 2, 3, 4]


# --- 7-10: safe / missing / outside / strict --------------------------------------------------------


def test_safe_grid_gives_status_safe_and_no_areas(tmp_path):
    result, _, _ = areas_of(tmp_path, ["...", "..."])
    assert result == {
        "status": "safe", "thresholdAMSL": THRESHOLD, "areaCount": 0, "unsafeCellCount": 0,
        "maxUnsafeElevation": None, "highestPoint": None, "vertexCount": 0, "simplifyToleranceM": None,
        "areas": [], "originFingerprint": "fp-test",
        # Data coverage travels with every response, "safe" included: safe over a
        # largely void Origin has verified almost nothing (see void handling below).
        "originCellCount": 42, "checkedCellCount": 42, "voidCellCount": 0, "voidFraction": 0.0,
    }


def test_unavailable_response_shape():
    r = ta.unavailable_response("fp")
    assert (r["status"], r["thresholdAMSL"], r["areaCount"], r["unsafeCellCount"], r["areas"]) == (
        "unavailable", None, 0, 0, [])
    assert (r["maxUnsafeElevation"], r["highestPoint"], r["originFingerprint"]) == (None, None, "fp")


def test_missing_cells_are_never_unsafe_and_do_not_connect_regions(tmp_path):
    result, index, _ = areas_of(tmp_path, ["#x#", "xx.", "##x"])
    assert result["unsafeCellCount"] == 4  # the void cells are not counted, not drawn
    assert result["areaCount"] == 3  # '#x#' is NOT bridged by the void between them; '##' is one area
    assert sorted(a["cellCount"] for a in result["areas"]) == [1, 1, 2]
    assert index.scan(THRESHOLD)["count"] == 4  # the same 4 cells Step 4A reports


def test_cells_outside_the_origin_are_never_included(tmp_path):
    n = 24
    dlat = 20 / 111320.0
    dlon = dlat / np.cos(np.radians(22.5))
    h, w = (n - 1.5) * dlat, (n - 1.5) * dlon
    triangle = [[22.5, 76.5], [22.5 + h, 76.5], [22.5, 76.5 + w]]  # half of its bounding box
    mgr = PatternTerrain(tmp_path / "srtm", func=lambda lat, lon: 900.0)  # every cell is very unsafe
    grid = T._build_terrain_grid_sync(mgr, triangle, 20)
    grid["origin_fingerprint"], grid["polygon"] = "fp", triangle
    index = T._build_unsafe_index_sync(grid)

    result = ta.build_unsafe_areas(index, 500.0, "fp")
    total = grid["rows"] * grid["cols"]
    assert result["unsafeCellCount"] == index.checked_cells < 0.6 * total  # only cells inside the Origin
    origin = shapely.Polygon([(lo, la) for la, lo in triangle])
    for area in result["areas"]:
        assert shapely.covers(shapely.buffer(origin, 2e-7), to_polygon(area))  # within 2 cm (7-decimal rounding)


def test_strict_threshold_equal_elevation_is_safe(tmp_path):
    values = [[SAFE] * 8 for _ in range(8)]
    values[3][2], values[3][3], values[3][4] = 500.0, 500.1, 500.0
    index, grid, _ = grid_from_values(tmp_path, values)
    result = ta.build_unsafe_areas(index, 500.0, "fp")
    assert result["unsafeCellCount"] == 1 and result["areas"][0]["maxElevation"] == 500.1
    assert ring_points(result["areas"][0]["polygon"]) == corners(grid, 3, 3)
    assert ta.build_unsafe_areas(index, 500.1, "fp")["status"] == "safe"  # 500.1 == threshold -> safe


# --- 11: the polygon follows the real shape ------------------------------------------------------


def test_an_l_shaped_region_gets_an_l_shaped_polygon_not_a_bounding_box(tmp_path):
    result, _, grid = areas_of(tmp_path, ["##.", "##.", "###"])
    (area,) = result["areas"]
    assert area["cellCount"] == 7 and len(area["polygon"]) == 7  # 6 corners of the L
    poly = to_polygon(area)
    box = shapely.box(*poly.bounds)
    assert poly.area == pytest.approx(box.area * 7 / 9, rel=1e-3)  # 7 of the 9 cells, not the full rectangle
    b = grid["bounds"]
    dlat, dlon, _, _ = T._grid_shape(b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], 20)
    empty_cell = shapely.Point(  # the cell in the notch: art (0, 2)
        T._cell_lon(b["min_lon"], dlon, MARGIN + 2), T._cell_lat(b["max_lat"], dlat, MARGIN)
    )
    assert not poly.intersects(empty_cell)


def test_holes_inside_a_region_are_preserved(tmp_path):
    art = ["#" * 9] * 9
    art[4] = "####.####"  # a single safe cell in the middle of a large unsafe block
    result, _, grid = areas_of(tmp_path, art)
    (area,) = result["areas"]
    assert area["cellCount"] == 80 and len(area["holes"]) == 1
    assert ring_points(area["holes"][0]) == corners(grid, MARGIN + 4, MARGIN + 4)
    assert to_polygon(area).area < shapely.box(*to_polygon(area).bounds).area  # the hole is really cut out


def test_highest_point_and_statistics_per_area(tmp_path):
    values = [[SAFE] * 12 for _ in range(12)]
    for (r, c, e) in [(2, 2, 600.0), (2, 3, 650.0), (3, 2, 650.0), (8, 8, 700.0), (8, 9, 510.0)]:
        values[r][c] = e
    index, grid, _ = grid_from_values(tmp_path, values)
    result = ta.build_unsafe_areas(index, 500.0, "fp")
    first, second = result["areas"]  # 3 cells (650 max), then 2 cells (700 max)
    assert (first["cellCount"], first["maxElevation"]) == (3, 650.0)
    # first of the two 650 cells in scan order (north first, west first): row 2, col 3
    assert (first["highestPoint"]["lat"], first["highestPoint"]["lon"]) == cell_pos(grid, 2, 3)
    assert (second["cellCount"], second["maxElevation"]) == (2, 700.0)
    assert (second["highestPoint"]["lat"], second["highestPoint"]["lon"]) == cell_pos(grid, 8, 8)
    assert result["maxUnsafeElevation"] == 700.0 and result["highestPoint"] == second["highestPoint"]


# --- 15: exact Step 2 mapping; same cells as Step 4A ------------------------------------------------


def test_polygon_coordinates_use_the_step2_mapping_and_match_step4a(tmp_path):
    rng = np.random.default_rng(3)
    values = rng.integers(300, 700, size=(20, 26)).astype(float).tolist()
    index, grid, _ = grid_from_values(tmp_path, values)
    a4 = index.scan(500.0, "fp")
    a4b = ta.build_unsafe_areas(index, 500.0, "fp", tolerance_m=0)  # exact outlines

    assert a4b["unsafeCellCount"] == a4["count"] and a4b["highestPoint"] == a4["highestPoint"]
    assert a4b["maxUnsafeElevation"] == a4["maxUnsafeElevation"]
    assert sum(a["cellCount"] for a in a4b["areas"]) == a4["count"]

    union = shapely.union_all([to_polygon(a) for a in a4b["areas"]])
    b = grid["bounds"]
    dlat, dlon, _, _ = T._grid_shape(b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], 20)
    # the exact outline is precisely the union of the unsafe cells' squares, each corner from _cell_lat/_cell_lon
    squares = []
    for p in a4["unsafePoints"]:
        squares.append(shapely.box(p["lon"] - dlon / 2, p["lat"] - dlat / 2, p["lon"] + dlon / 2, p["lat"] + dlat / 2))
    expected = shapely.union_all(squares)
    origin = shapely.Polygon([(lo, la) for la, lo in grid["polygon"]])
    assert shapely.symmetric_difference(shapely.intersection(expected, origin), union).area < 5e-3 * expected.area
    # and every unsafe cell centre of Step 4A lies inside the polygons
    assert shapely.intersects_xy(union, [p["lon"] for p in a4["unsafePoints"]], [p["lat"] for p in a4["unsafePoints"]]).all()


# --- outward simplification (never cuts unsafe terrain off) -----------------------------------------


def staircase_region(n=30):
    """A big diagonal band with a very long one-cell staircase boundary (collinear points stripped)."""
    cells = [(r, c) for r in range(n) for c in range(n) if abs(r - c) <= 3]
    band = shapely.union_all([shapely.box(c - 0.5, r - 0.5, c + 0.5, r + 0.5) for r, c in cells])
    return shapely.simplify(band, 0.0, preserve_topology=True)


def test_simplification_is_outward_only_bounded_and_valid():
    exact = staircase_region()
    tol = 15.0 / 20.0  # 15 m in cells: enough to collapse a one-cell staircase
    simplified = ta._simplify_outward(np.array([exact], dtype=object), tol)[0]

    assert shapely.get_num_coordinates(simplified) < shapely.get_num_coordinates(exact) / 2  # really reduced
    assert simplified.is_valid
    assert shapely.difference(exact, simplified).area < 1e-9  # NOTHING of the exact outline is cut off
    assert shapely.buffer(exact, 2 * tol + 1e-9).covers(simplified)  # and never further than ~2 x tolerance out
    assert simplified.area > exact.area  # it only ever grows (a narrow band grows a lot: the cost of a tolerance)


def test_a_tolerance_too_small_for_the_grid_changes_nothing_useful():
    exact = staircase_region()
    out = ta._simplify_outward(np.array([exact], dtype=object), 5.0 / 20.0)[0]  # 5 m < half a diagonal step
    assert shapely.get_num_coordinates(out) >= shapely.get_num_coordinates(exact) * 0.9  # (why the default is 0)


def test_small_outlines_are_never_simplified_or_inflated():
    for shape in (shapely.box(-0.5, -0.5, 0.5, 0.5), shapely.box(0, 0, 7, 3),
                  shapely.union_all([shapely.box(0, 0, 3, 3), shapely.box(0, 3, 6, 4)])):
        out = ta._simplify_outward(np.array([shape], dtype=object), 0.25)[0]
        assert out.equals(shape)  # <= EXACT_VERTEX_LIMIT coordinates: left exactly as is


def test_zero_tolerance_gives_exact_outlines(tmp_path):
    art = [("#" * 30)[: 3 + i] for i in range(24)]  # a staircase
    exact, _, _ = areas_of(tmp_path, art, tolerance_m=0)
    default, _, _ = areas_of(tmp_path, art)
    assert default["areas"] == exact["areas"] and default["simplifyToleranceM"] == 0.0  # exact is the default
    simplified, _, _ = areas_of(tmp_path, art, tolerance_m=15)
    assert simplified["vertexCount"] < exact["vertexCount"]  # simplification did reduce
    e, s = to_polygon(exact["areas"][0]), to_polygon(simplified["areas"][0])
    assert shapely.difference(e, s).area < 1e-9 * e.area  # ... without losing any unsafe area
    assert exact["areas"][0]["cellCount"] == simplified["areas"][0]["cellCount"]


def test_a_component_split_by_the_clip_region_reports_each_piece(tmp_path):
    index, _, _ = grid_from(tmp_path, ["#" * 10] * 4)  # one 10 x 4 block
    # An Origin made of two pieces with a gap between them (index space: x = column, y = row).
    left = shapely.box(-1.0, -1.0, 5.4, 10.0)   # holds the centres of columns 2..5
    right = shapely.box(7.6, -1.0, 20.0, 10.0)  # holds the centres of columns 8..11
    region = shapely.MultiPolygon([left, right])
    shapely.prepare(region)
    index.clip_region = lambda: region

    result = ta.build_unsafe_areas(index, THRESHOLD, "fp")
    assert result["areaCount"] == 2  # one component, clipped into two pieces -> two areas
    assert [a["cellCount"] for a in result["areas"]] == [16, 16]  # the cells whose centres lie in each piece
    xs = sorted(min(x for _, x in a["polygon"]) for a in result["areas"])
    assert xs[0] < xs[1]  # the two polygons are really apart, not one shape spanning the gap


def test_polygons_never_extend_beyond_a_concave_origin(tmp_path):
    n, m = 14, 20
    base = rect(n + 1, m + 1)
    lat0, lon0 = base[0]
    lat1, lon1 = base[2]
    mid = (lon0 + lon1) / 2
    notch = lat0 + (lat1 - lat0) * 0.6
    u_shape = [[lat0, lon0], [lat0, lon1], [lat1, lon1], [lat1, mid + 0.0003], [notch, mid + 0.0003],
               [notch, mid - 0.0003], [lat1, mid - 0.0003], [lat1, lon0]]  # a notch cut into one edge
    index, grid, _ = grid_from_values(tmp_path, [[UNSAFE] * m for _ in range(n)], polygon=u_shape)
    origin = shapely.Polygon([(lo, la) for la, lo in u_shape])
    for tolerance in (0, 15):
        result = ta.build_unsafe_areas(index, THRESHOLD, "fp", tolerance_m=tolerance)
        union = shapely.union_all([to_polygon(a) for a in result["areas"]])
        assert shapely.covers(shapely.buffer(origin, 2e-7), union)  # inside the Origin, notch included
        assert union.area == pytest.approx(origin.area, rel=0.1)  # and the rest of it is covered


# --- 17: real-sized grid ------------------------------------------------------------------------------


def smooth_terrain(rows=717, cols=845, seed=5):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:rows, 0:cols].astype(float)
    z = np.full((rows, cols), 400.0)
    for _ in range(25):  # hills
        cy, cx, sy, sx = rng.uniform(0, rows), rng.uniform(0, cols), rng.uniform(30, 120), rng.uniform(30, 120)
        z += rng.uniform(40, 260) * np.exp(-(((y - cy) / sy) ** 2 + ((x - cx) / sx) ** 2))
    return np.round(z)


def test_real_sized_grid_shrinks_the_payload_dramatically():
    rows, cols = 717, 845
    z = smooth_terrain(rows, cols)
    grid = {
        "rows": rows, "cols": cols, "grid": z.tolist(), "spacing_m": 20,
        "bounds": {"min_lat": 22.0, "max_lat": 22.0 + rows * 1e-4, "min_lon": 76.0, "max_lon": 76.0 + cols * 1e-4},
        "polygon": [[21.0, 75.0], [21.0, 77.0], [23.0, 77.0], [23.0, 75.0]],  # covers the whole grid
    }
    index = tu.TerrainScanIndex(
        grid, lambda r: 22.0 + rows * 1e-4 - r * 1e-4, lambda c: 76.0 + c * 1e-4
    )
    threshold = float(np.percentile(z, 15))  # a low threshold: most of the grid is unsafe

    a4 = index.scan(threshold, "fp")
    started = time.perf_counter()
    a4b = ta.build_unsafe_areas(index, threshold, "fp")
    elapsed = time.perf_counter() - started

    size4, size4b = len(json.dumps(a4)), len(json.dumps(a4b))
    assert a4["count"] > 400_000  # the problem case: hundreds of thousands of unsafe cells
    assert a4b["unsafeCellCount"] == a4["count"] and a4b["highestPoint"] == a4["highestPoint"]
    assert a4b["areaCount"] < 200 and a4b["vertexCount"] < 20_000
    assert size4b < size4 / 100  # 100x or more smaller
    assert elapsed < 3.0
    print(f"\n4A {a4['count']} points {size4 / 1e6:.1f} MB -> 4B {a4b['areaCount']} areas, "
          f"{a4b['vertexCount']} vertices, {size4b / 1e3:.0f} KB in {elapsed * 1000:.0f} ms")


REAL_CACHE = os.path.join(
    os.path.dirname(__file__), "..", "..", "fixed_wing_windows_exe", "swarm_tasks", "Examples", "basic_tasks",
    "medur_swarm", "terrain_grid", "terrain_grid_cache.json",
)


@pytest.mark.skipif(not os.path.exists(REAL_CACHE), reason="the real persisted terrain grid is not on this machine")
def test_on_the_real_persisted_grid_nothing_unsafe_is_lost_and_nothing_leaves_the_origin():
    doc = json.load(open(REAL_CACHE, encoding="utf-8"))
    grid = T._validate_grid_doc(doc, doc["polygon"], doc["spacing_m"])
    index = T._build_unsafe_index_sync(grid)
    origin = shapely.Polygon([(lo, la) for la, lo in doc["polygon"]])
    ref = T.get_grid_elevation(grid, grid["bounds"]["min_lat"], grid["bounds"]["min_lon"])
    for altitude in (50, 100, 150):
        threshold = ref + altitude - 50.0
        a4 = index.scan(threshold)
        a4b = ta.build_unsafe_areas(index, threshold)
        assert a4b["unsafeCellCount"] == a4["count"]
        union = shapely.union_all([to_polygon(a) for a in a4b["areas"]])
        pts = a4["unsafePoints"]
        assert shapely.intersects_xy(union, [p["lon"] for p in pts], [p["lat"] for p in pts]).all()
        assert shapely.covers(shapely.buffer(origin, 2e-7), union)
        # (the size RATIO depends on how much of whatever grid is on disk is unsafe; the synthetic
        # real-sized test pins the big reduction. Here: never larger than the point list.)
        assert len(json.dumps(a4b)) < len(json.dumps(a4))


# --- integration: Origin set, Takeoff, telemetry (real terrain ext, fake app) ------------------------


@pytest.fixture
def env(tmp_path, monkeypatch):
    mgr = PatternTerrain(tmp_path / "srtm", func=elevation_of)
    monkeypatch.setattr(T, "_terrain_manager", mgr)
    monkeypatch.setattr(T, "configuration", {"terrain_grid_dir": str(tmp_path / "grid")})  # defaults otherwise
    monkeypatch.setattr(T, "log", None)
    monkeypatch.setattr(T, "_terrain_grid_cache", None)
    monkeypatch.setattr(T, "_latest_origin_fingerprint", None)
    monkeypatch.setattr(T, "app", None)
    ts.tracker.reset()
    T._reset_unsafe_terrain()
    yield SimpleNamespace(mgr=mgr, app=FakeApp())
    ts.tracker.reset()
    T._reset_unsafe_terrain()


def area_msgs(app):
    return [m for m in app.sent if m.get("type") == "X-TERRAIN-UNSAFE-AREA-RESP"]


async def set_origin(env, polygon):
    origin = (min(p[0] for p in polygon), min(p[1] for p in polygon))
    await T.generate_terrain_grid_for_origin(env.app, polygon, origin)


async def test_areas_are_sent_when_the_grid_is_ready_and_the_point_list_is_not(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)

    (m,) = area_msgs(env.app)
    assert (m["type"], m["status"], m["thresholdAMSL"]) == ("X-TERRAIN-UNSAFE-AREA-RESP", "unsafe", 378.0)
    assert m["areaCount"] == len(m["areas"]) >= 1
    assert m["unsafeCellCount"] == sum(a["cellCount"] for a in m["areas"]) > 0
    assert m["originFingerprint"] == ts.tracker.origin_fingerprint
    assert m["maxUnsafeElevation"] == m["highestPoint"]["elevation"] == max(a["maxElevation"] for a in m["areas"])
    assert (m["thresholdUavId"], m["altitudeSource"]) == (None, "initial_50m")
    assert not [x for x in env.app.sent if x.get("type") == "X-TERRAIN-UNSAFE-RESP"]  # 4A's 30 MB push is off by default
    assert any("area(s)" in s for s in env.app.sys_msgs)


async def test_the_point_list_broadcast_can_still_be_enabled(env, monkeypatch):
    monkeypatch.setattr(T, "configuration", {**T.configuration, "broadcast_unsafe_points": True})
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    assert len(area_msgs(env.app)) == 1
    assert len([x for x in env.app.sent if x.get("type") == "X-TERRAIN-UNSAFE-RESP"]) == 1


async def test_areas_match_step4a_cells_and_are_far_smaller(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    (m,) = area_msgs(env.app)
    async with T._unsafe_lock:
        _, a4 = await T._current_unsafe_result(env.app)
    assert m["unsafeCellCount"] == a4["count"] and m["highestPoint"] == a4["highestPoint"]
    assert len(json.dumps(m)) < len(json.dumps(a4)) / 5
    union = shapely.union_all([to_polygon(a) for a in m["areas"]])
    assert shapely.intersects_xy(union, [p["lon"] for p in a4["unsafePoints"]], [p["lat"] for p in a4["unsafePoints"]]).all()


async def test_takeoff_command_regroups_the_same_grid_with_the_new_threshold(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    grid, reads = T.get_cached_terrain_grid(), env.mgr.reads
    (before,) = area_msgs(env.app)
    env.app.sent.clear()

    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()

    (after,) = area_msgs(env.app)
    assert after["thresholdAMSL"] == 428.0
    assert 0 < after["unsafeCellCount"] < before["unsafeCellCount"]
    assert (after["thresholdUavId"], after["altitudeSource"]) == ("1", "takeoff_altitude")
    assert T.get_cached_terrain_grid() is grid and env.mgr.reads == reads  # same grid, 0 SRTM reads


async def test_flying_altitude_changes_regroup_only_on_a_meaningful_change(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    env.app.sent.clear()

    for ahl in (10.0, 60.0, 99.0, 100.0, 103.0):  # climbing / reached / < 5 m: threshold stays 428
        env.app.telemetry("1", ahl)
    await env.app.flush()
    assert area_msgs(env.app) == []

    env.app.telemetry("1", 120.0)  # meaningful -> 378 + 120 - 50
    await env.app.flush()
    (m,) = area_msgs(env.app)
    assert (m["thresholdAMSL"], m["altitudeSource"]) == (448.0, "telemetry_agl")


async def test_safe_result_when_the_threshold_is_above_all_terrain(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 500, ["1"])  # 378 + 500 - 50 = 828 m > the highest terrain
    await env.app.flush()
    (m,) = area_msgs(env.app)
    assert (m["status"], m["areaCount"], m["unsafeCellCount"], m["areas"]) == ("safe", 0, 0, [])
    assert (m["maxUnsafeElevation"], m["highestPoint"]) == (None, None)


async def test_new_origin_clears_the_previous_polygons(env, monkeypatch):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    (a,) = area_msgs(env.app)
    assert a["areaCount"] >= 1

    seen = {}
    orig = T._build_terrain_grid_sync

    def spy(*args, **kw):
        seen["state"] = (T._areas_cache, T._areas_broadcast_key, T._unsafe_index)
        return orig(*args, **kw)

    monkeypatch.setattr(T, "_build_terrain_grid_sync", spy)
    env.app.sent.clear()
    await set_origin(env, ORIGIN_B)  # flat 350 m: nothing above 350 (terrain == threshold is safe)
    assert seen["state"] == (None, None, None)  # nothing of Origin A survives while B is built
    (b,) = area_msgs(env.app)
    assert (b["status"], b["areaCount"]) == ("safe", 0)
    assert b["originFingerprint"] == ts.tracker.origin_fingerprint != a["originFingerprint"]
    assert b["thresholdAMSL"] == 350.0

    T.app = env.app
    try:
        cached = await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(SimpleNamespace(body={}), None, None)
    finally:
        T.app = None
    assert cached["areas"] == [] and cached["originFingerprint"] == b["originFingerprint"]


async def test_same_origin_and_threshold_reuse_the_cached_result(env, monkeypatch):
    T.app = env.app
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    calls = []
    orig = ta.build_unsafe_areas
    monkeypatch.setattr(ta, "build_unsafe_areas", lambda *a, **k: calls.append(a[1]) or orig(*a, **k))
    builds = []
    orig_index = T._build_unsafe_index_sync
    monkeypatch.setattr(T, "_build_unsafe_index_sync", lambda g: builds.append(1) or orig_index(g))

    req = SimpleNamespace(body={})
    for _ in range(3):
        await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(req, None, None)
    await T._refresh_unsafe_areas(env.app)
    assert calls == [] and builds == []  # same Origin + same threshold: no regrouping, no new index
    assert len(area_msgs(env.app)) == 1  # ... and nothing re-sent

    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()  # 428: exactly one new grouping, on the SAME index
    await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(req, None, None)
    await T._refresh_unsafe_areas(env.app)
    T.app = None
    assert calls == [428.0] and builds == []
    assert len(area_msgs(env.app)) == 2


async def test_request_handler_is_read_only_and_answers_for_the_current_threshold(env):
    T.app = env.app
    try:
        req = SimpleNamespace(body={})
        empty = await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(req, None, None)
        assert (empty["type"], empty["status"], empty["thresholdAMSL"], empty["areas"]) == (
            "X-TERRAIN-UNSAFE-AREA-RESP", "unavailable", None, [])

        env.app.uavs["1"] = fake_uav(0.0)
        await set_origin(env, ORIGIN_A)
        grid, reads = T.get_cached_terrain_grid(), env.mgr.reads
        (broadcast,) = area_msgs(env.app)
        resp = await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(req, None, None)
        assert {k: v for k, v in resp.items() if k != "type"} == {k: v for k, v in broadcast.items() if k != "type"}

        ts.on_takeoff_commanded(env.app, 100, ["1"])  # threshold moves; ask before the broadcast is flushed
        resp = await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(req, None, None)
        assert resp["thresholdAMSL"] == 428.0
        await env.app.flush()
        assert T.get_cached_terrain_grid() is grid and env.mgr.reads == reads
    finally:
        T.app = None


# --- wiring ---------------------------------------------------------------------------------------------


def test_step4b_is_attached_to_step3_and_registered_as_a_socket_handler():
    import inspect

    assert T._refresh_unsafe_areas in ts._threshold_listeners and T._refresh_unsafe_terrain in ts._threshold_listeners
    assert (ta.EVENT_TYPE, ta.REQUEST_TYPE) == ("X-TERRAIN-UNSAFE-AREA-RESP", "X-TERRAIN-UNSAFE-AREA-REQ")
    assert "terrain_areas.REQUEST_TYPE: handle_X_TERRAIN_UNSAFE_AREA_REQ" in inspect.getsource(T.run)


def test_step4b_never_touches_srtm_or_the_grid_generator():
    import inspect

    module = inspect.getsource(ta)
    assert "get_elevation" not in module and "TerrainManager" not in module and "download" not in module
    flow = "".join(inspect.getsource(f) for f in (T._current_unsafe_areas, T._refresh_unsafe_areas))
    for forbidden in ("get_elevation", "_build_terrain_grid_sync", "download_tile", "_load_terrain_grid_sync"):
        assert forbidden not in flow


# --- the new threshold formula in the area messages ------------------------------------------------


async def test_area_message_explains_the_threshold_and_follows_the_formula(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    (m,) = area_msgs(env.app)
    assert (m["referenceTerrainElevation"], m["safetyAltitude"], m["safetyMargin"]) == (378.0, 50.0, 50.0)
    assert m["thresholdAMSL"] == 378.0 == m["referenceTerrainElevation"] + m["safetyAltitude"] - m["safetyMargin"]

    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    (m,) = area_msgs(env.app)
    assert (m["referenceTerrainElevation"], m["safetyAltitude"], m["safetyMargin"]) == (378.0, 100.0, 50.0)
    assert m["thresholdAMSL"] == 428.0 == m["referenceTerrainElevation"] + m["safetyAltitude"] - m["safetyMargin"]


async def test_end_to_end_the_polygons_use_terrain_greater_than_home_plus_height_minus_margin(env):
    # home 300; a band at exactly 350.0 and a band at 350.1
    env.mgr.func = lambda lat, lon: {1: 350.0, 2: 350.1}.get(round((lon - 76.5) / 0.0005), 300.0)
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    (m,) = area_msgs(env.app)
    assert m["thresholdAMSL"] == 300.0 and m["areaCount"] >= 1

    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 100, ["1"])  # 300 + 100 - 50 = 350
    await env.app.flush()
    (m,) = area_msgs(env.app)
    assert m["thresholdAMSL"] == 350.0
    assert m["maxUnsafeElevation"] == 350.1  # only the 350.1 band; the 350.0 band is exactly at the threshold: safe
    assert all(a["maxElevation"] == 350.1 for a in m["areas"])

    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 101, ["1"])  # 351: now the 350.1 band is safe too
    await env.app.flush()
    (m,) = area_msgs(env.app)
    assert (m["thresholdAMSL"], m["status"], m["areaCount"]) == (351.0, "safe", 0)


async def test_a_request_shows_the_current_inputs_even_when_no_new_broadcast_was_needed(env):
    T.app = env.app
    try:
        env.app.uavs["1"] = fake_uav(0.0)
        await set_origin(env, ORIGIN_A)
        ts.on_takeoff_commanded(env.app, 100, ["1"])
        await env.app.flush()
        env.app.sent.clear()

        env.app.telemetry("1", 100.0)  # reaches the commanded altitude: same threshold, now from telemetry
        await env.app.flush()
        assert area_msgs(env.app) == []  # threshold unchanged -> nothing re-sent
        resp = await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(SimpleNamespace(body={}), None, None)
        assert (resp["thresholdAMSL"], resp["altitudeSource"]) == (428.0, "telemetry_agl")  # ... but the answer is current
    finally:
        T.app = None


# --- per-area RED/YELLOW severity -----------------------------------------------------------


def test_classify_area_severity_matches_the_first_worked_example():
    # home = 5779, area maxElevation = 6091, margin = 50 -> relative = 312
    home, terrain, margin = 5779.0, 6091.0, 50.0
    cases = [
        (250, "red"), (300, "red"),
        (312, "yellow"), (320, "yellow"), (350, "yellow"), (361, "yellow"),
        (362, "clear"),
    ]
    for ahl, expected in cases:
        assert ta.classify_area_severity(terrain, home, ahl, margin) == expected, ahl


def test_classify_area_severity_matches_the_second_worked_example():
    # home = 5779, area maxElevation = 5979, margin = 50 -> relative = 200
    home, terrain, margin = 5779.0, 5979.0, 50.0
    cases = [
        (150, "red"),
        (200, "yellow"), (220, "yellow"), (240, "yellow"), (249, "yellow"),
        (250, "clear"),
    ]
    for ahl, expected in cases:
        assert ta.classify_area_severity(terrain, home, ahl, margin) == expected, ahl


def test_attach_area_severity_writes_red_or_yellow_onto_each_area():
    areas = [{"maxElevation": 6091.0}, {"maxElevation": 5979.0}]
    ta.attach_area_severity(areas, 5779.0, 300.0, 50.0)
    # relative 312 -> 300 is red; relative 200 -> 300 is (200+50=250 <= 300) clamped-clear -> yellow
    assert [a["severity"] for a in areas] == ["red", "yellow"]


def test_attach_area_severity_never_writes_clear_even_when_the_math_would_say_so():
    # Can't happen for a real response (that area's own condition would already have removed
    # it), but attach_area_severity must still never put "clear" on the wire.
    areas = [{"maxElevation": 5979.0}]
    ta.attach_area_severity(areas, 5779.0, 250.0, 50.0)  # relative 200; 250 >= 200 + 50
    assert areas[0]["severity"] == "yellow"


def test_attach_area_severity_is_a_noop_without_all_three_finite_inputs():
    for reference, altitude, margin in [
        (None, 300.0, 50.0),
        (5779.0, None, 50.0),
        (5779.0, 300.0, None),
        ("not-a-number", 300.0, 50.0),
        (5779.0, float("nan"), 50.0),
    ]:
        areas = [{"maxElevation": 6091.0}]
        ta.attach_area_severity(areas, reference, altitude, margin)
        assert "severity" not in areas[0], (reference, altitude, margin)


def test_step4b_severity_never_touches_srtm_the_grid_or_the_unsafe_decision():
    import inspect

    module = inspect.getsource(ta)
    # the new functions must not depend on anything build_unsafe_areas doesn't already use
    assert "get_elevation" not in module and "TerrainManager" not in module
    # and must never redefine what "unsafe" means (no new threshold comparison against elevation)
    severity_src = inspect.getsource(ta.classify_area_severity) + inspect.getsource(ta.attach_area_severity)
    assert "unsafe_cells" not in severity_src and "TerrainScanIndex" not in severity_src


async def test_area_severity_flows_through_the_real_broadcast_pipeline(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()

    (m,) = area_msgs(env.app)
    assert m["areaCount"] >= 1
    for area in m["areas"]:
        assert area["severity"] in ("red", "yellow")  # never "clear" on the wire
        relative = area["maxElevation"] - m["referenceTerrainElevation"]
        expected = "red" if m["safetyAltitude"] < relative else "yellow"
        assert area["severity"] == expected

    env.app.sent.clear()
    env.app.telemetry("1", 120.0)  # a meaningful (>= 5 m) AHL change -> Step 3 recalculates
    await env.app.flush()

    (m2,) = area_msgs(env.app)
    for area in m2["areas"]:
        relative = area["maxElevation"] - m2["referenceTerrainElevation"]
        expected = "red" if m2["safetyAltitude"] < relative else "yellow"
        assert area["severity"] == expected


async def test_area_severity_is_cached_together_with_the_areas_it_belongs_to(env):
    T.app = env.app
    try:
        env.app.uavs["1"] = fake_uav(0.0)
        await set_origin(env, ORIGIN_A)
        env.app.sent.clear()
        ts.on_takeoff_commanded(env.app, 100, ["1"])
        await env.app.flush()
        (broadcast,) = area_msgs(env.app)

        resp = await T.handle_X_TERRAIN_UNSAFE_AREA_REQ(SimpleNamespace(body={}), None, None)
        assert [a["severity"] for a in resp["areas"]] == [a["severity"] for a in broadcast["areas"]]
    finally:
        T.app = None


async def test_area_messages_use_the_uav_home_terrain_and_say_where_it_came_from(env):
    from test_terrain_safety import high_corner_terrain, uav_at

    home = (22.5015, 76.502)  # inside this file's (small) ORIGIN_A
    env.mgr.func = high_corner_terrain  # 600 m at the Origin corner, 400 m where the UAV stands
    env.app.uavs["1"] = uav_at(0.0, home)
    await set_origin(env, ORIGIN_A)
    (m,) = area_msgs(env.app)
    assert m["referenceTerrainElevation"] == 400.0 and m["referenceSource"] == "swarm_home"
    assert m["referenceLocation"] == {"lat": home[0], "lon": home[1]}
    assert m["thresholdAMSL"] == 400.0 == m["referenceTerrainElevation"] + m["safetyAltitude"] - m["safetyMargin"]
    # the 600 m band along the western edge IS above a 400 m threshold (and it would be invisible
    # if the corner's 600 m were used as home instead)
    assert (m["status"], m["maxUnsafeElevation"]) == ("unsafe", 600.0)

    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    (m,) = area_msgs(env.app)
    assert (m["thresholdUavId"], m["referenceSource"], m["thresholdAMSL"]) == ("1", "uav_home", 450.0)



# --- SRTM voids are reported, not silently treated as safe -----------------------------
#
# A void cell inside the Origin has no elevation, so it becomes -inf in the scan and can
# never compare as unsafe. That is unavoidable -- you cannot test terrain you have no
# data for -- but it must not be presented as verified-clear terrain. Every response
# therefore carries the void count and fraction.


def test_a_fully_void_origin_reports_safe_but_declares_zero_coverage(tmp_path):
    """The dangerous case: nothing is drawn, yet nothing was actually checked."""
    result, index, _ = areas_of(tmp_path, ["xxx", "xxx"])

    assert result["status"] == "safe"       # no unsafe cell can be found ...
    assert result["areaCount"] == 0
    assert result["voidCellCount"] == 6    # ... because 6 cells have no data
    assert result["checkedCellCount"] == result["originCellCount"] - 6
    assert result["voidFraction"] > 0.0
    assert index.void_cells == 6


def test_void_cells_next_to_unsafe_terrain_are_counted_separately(tmp_path):
    """Voids and unsafe cells coexist: the areas are still exact, and the void
    count tells the operator the rest of the Origin was not fully verified."""
    result, _, _ = areas_of(tmp_path, ["#x", "##"])

    assert result["status"] == "unsafe"
    assert result["unsafeCellCount"] == 3   # the void is NOT counted as unsafe
    assert result["voidCellCount"] == 1
    assert result["checkedCellCount"] == result["originCellCount"] - 1


def test_a_void_free_origin_reports_full_coverage(tmp_path):
    result, _, _ = areas_of(tmp_path, ["#.", ".."])

    assert result["voidCellCount"] == 0
    assert result["voidFraction"] == 0.0
    assert result["checkedCellCount"] == result["originCellCount"]


def test_void_fraction_is_the_share_of_the_origin_with_no_data(tmp_path):
    result, index, _ = areas_of(tmp_path, ["xxxx", "xxxx"])

    expected = index.void_cells / index.origin_cells
    assert result["voidFraction"] == round(expected, 6)
    assert 0.0 < result["voidFraction"] < 1.0  # the safe margin around the art has data
