"""Tests for Step 4A: unsafe terrain detection (flockwave.server.terrain_unsafe and
its wiring into the terrain extension).

Unsafe means  elevation > threshold  (strictly), inside the Origin polygon only,
on the Step 2 grid that is already in memory -- never SRTM, never a new grid."""

import inspect
import time
from types import SimpleNamespace
from typing import Any, Dict, List

import numpy as np
import pytest

from flockwave.server import terrain_safety as ts
from flockwave.server import terrain_unsafe as tu
from flockwave.server.ext import terrain as T
from flockwave.server.geofence_validator import Fence

DLAT_PER_M = 1 / 111320.0


class PatternTerrain(T.TerrainManager):
    """Terrain whose elevation is defined per grid cell: `pattern[row][col]`
    (None = void). Counts every read."""

    def __init__(self, terrain_dir, pattern=None, func=None):
        super().__init__(terrain_dir)
        self.pattern, self.func, self.reads = pattern, func, 0
        self.bounds = None

    def download_tile(self, lat, lon):
        f = self.terrain_dir / f"{self.get_tile_name(lat, lon)}.hgt"
        f.write_bytes(b"")
        return f

    def get_elevation(self, latitude, longitude):
        self.reads += 1
        if self.func is not None:
            return self.func(latitude, longitude)
        b = self.bounds
        dlat, dlon, _, _ = T._grid_shape(b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], 20)
        r = round((b["max_lat"] - latitude) / dlat)
        c = round((longitude - b["min_lon"]) / dlon)
        return self.pattern[r][c]


def rect(rows, cols, lat0=22.5, lon0=76.5):
    """Rectangle polygon whose 20 m grid is exactly rows x cols."""
    dlat = 20 * DLAT_PER_M
    dlon = dlat / np.cos(np.radians(lat0))
    h, w = (rows - 1 - 0.5) * dlat, (cols - 1 - 0.5) * dlon
    return [[lat0, lon0], [lat0, lon0 + w], [lat0 + h, lon0 + w], [lat0 + h, lon0]]


def build_grid(tmp_path, pattern, polygon=None, pad=999.0):
    """A real Step 2 grid (built by the real generator) whose top-left
    rows x cols cells hold `pattern` (None = void) and lie inside the Origin.

    Step 2 sizes a grid with ceil(), so its last row and column can fall just
    outside the Origin polygon. Here they always do, and are filled with 999 m
    ("very unsafe") to prove the scan ignores terrain outside the Origin.
    """
    rows, cols = len(pattern), len(pattern[0])
    polygon = polygon or rect(rows + 1, cols + 1)  # covers rows-1+0.5 steps: the extra row/col is outside
    padded = [list(r) + [pad] for r in pattern] + [[pad] * (cols + 1)]
    mgr = PatternTerrain(tmp_path / "srtm", padded)
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    mgr.bounds = {"min_lat": min(lats), "max_lat": max(lats), "min_lon": min(lons), "max_lon": max(lons)}
    grid = T._build_terrain_grid_sync(mgr, polygon, 20)
    assert (grid["rows"], grid["cols"]) == (rows + 1, cols + 1)
    grid["origin_fingerprint"], grid["polygon"] = "fp-test", polygon
    return grid, mgr


def cell_pos(grid, r, c):
    b = grid["bounds"]
    dlat, dlon, _, _ = T._grid_shape(b["min_lat"], b["max_lat"], b["min_lon"], b["max_lon"], 20)
    return (
        round(T._cell_lat(b["max_lat"], dlat, r), tu.COORD_DECIMALS),
        round(T._cell_lon(b["min_lon"], dlon, c), tu.COORD_DECIMALS),
    )


SPEC_PATTERN = [
    [450.0, 470.0, 490.0],
    [460.0, 520.0, 480.0],
    [500.0, 455.0, 510.0],
]


# --- the core comparison --------------------------------------------------------------


def test_spec_example_only_cells_above_478_are_returned(tmp_path):
    grid, _ = build_grid(tmp_path, SPEC_PATTERN)
    result = T._build_unsafe_index_sync(grid).scan(478.0, "fp-test")

    expected = [  # row-major, north first
        (0, 2, 490.0), (1, 1, 520.0), (1, 2, 480.0), (2, 0, 500.0), (2, 2, 510.0),
    ]
    assert result["status"] == "unsafe"
    assert result["thresholdAMSL"] == 478.0
    assert result["count"] == 5 == len(result["unsafePoints"])
    assert result["unsafePoints"] == [
        {"lat": cell_pos(grid, r, c)[0], "lon": cell_pos(grid, r, c)[1], "elevation": e}
        for r, c, e in expected
    ]
    assert result["maxUnsafeElevation"] == 520.0
    assert result["highestPoint"] == {"lat": cell_pos(grid, 1, 1)[0], "lon": cell_pos(grid, 1, 1)[1], "elevation": 520.0}
    assert result["originFingerprint"] == "fp-test"
    safe_values = {450.0, 470.0, 460.0, 455.0}
    assert not safe_values & {p["elevation"] for p in result["unsafePoints"]}


def test_comparison_is_strictly_greater_than(tmp_path):
    grid, _ = build_grid(tmp_path, [[450, 477, 478], [478.0, 478.1, 500], [100, 100, 100]])
    result = T._build_unsafe_index_sync(grid).scan(478.0)
    assert sorted(p["elevation"] for p in result["unsafePoints"]) == [478.1, 500]  # 478 itself is safe


def test_no_unsafe_terrain_gives_the_safe_response(tmp_path):
    grid, _ = build_grid(tmp_path, SPEC_PATTERN)
    result = T._build_unsafe_index_sync(grid).scan(800.0, "fp-test")
    assert result == {
        "status": "safe",
        "thresholdAMSL": 800.0,
        "count": 0,
        "unsafePoints": [],
        "maxUnsafeElevation": None,
        "highestPoint": None,
        "originFingerprint": "fp-test",
    }


def test_unavailable_response_shape():
    assert tu.unavailable_response("fp") == {
        "status": "unavailable",
        "thresholdAMSL": None,
        "count": 0,
        "unsafePoints": [],
        "maxUnsafeElevation": None,
        "highestPoint": None,
        "originFingerprint": "fp",
    }


def test_missing_cells_are_never_unsafe_or_returned(tmp_path):
    pattern = [[None, 600.0, None], [450.0, None, 900.0], [None, 500.0, None]]
    grid, _ = build_grid(tmp_path, pattern)
    index = T._build_unsafe_index_sync(grid)
    assert index.checked_cells == 4  # 4 valid cells inside; voids and the outside row/col excluded
    result = index.scan(0.0)  # everything valid is above 0
    assert sorted(p["elevation"] for p in result["unsafePoints"]) == [450.0, 500.0, 600.0, 900.0]
    assert result["maxUnsafeElevation"] == 900.0


def test_highest_point_matches_step2_grid_statistics(tmp_path):
    # pad=100: Step 2's own max statistic covers the whole bounding box, so keep
    # the out-of-Origin row/col low here; Step 4A's highest point is Origin-only.
    grid, _ = build_grid(tmp_path, SPEC_PATTERN, pad=100.0)
    result = T._build_unsafe_index_sync(grid).scan(478.0)
    step2 = grid["stats"]["max_elevation_location"]
    assert result["highestPoint"]["lat"] == round(step2["lat"], tu.COORD_DECIMALS)
    assert result["highestPoint"]["lon"] == round(step2["lon"], tu.COORD_DECIMALS)
    assert result["highestPoint"]["elevation"] == grid["stats"]["max_elevation_m"]


def test_reported_lat_lon_are_the_cells_own_step2_positions(tmp_path):
    rng = np.random.default_rng(1)
    pattern = rng.integers(300, 800, size=(15, 20)).astype(float).tolist()
    grid, _ = build_grid(tmp_path, pattern)
    result = T._build_unsafe_index_sync(grid).scan(600.0)
    expected = [
        (*cell_pos(grid, r, c), pattern[r][c])
        for r in range(15) for c in range(20) if pattern[r][c] > 600.0
    ]
    assert [(p["lat"], p["lon"], p["elevation"]) for p in result["unsafePoints"]] == expected


# --- only the Origin operating area ------------------------------------------------------


def test_terrain_outside_the_origin_polygon_is_never_unsafe(tmp_path):
    lat0, lon0, n = 22.5, 76.5, 30
    dlat = 20 * DLAT_PER_M
    dlon = dlat / np.cos(np.radians(lat0))
    h, w = (n - 1.5) * dlat, (n - 1.5) * dlon
    # a triangle: its bounding box (= the grid) is twice as large as the Origin
    triangle = [[lat0, lon0], [lat0 + h, lon0], [lat0, lon0 + w]]
    mgr = PatternTerrain(tmp_path / "srtm", func=lambda lat, lon: 900.0)  # everything is "unsafe"
    grid = T._build_terrain_grid_sync(mgr, triangle, 20)
    grid["origin_fingerprint"], grid["polygon"] = "fp", triangle

    result = T._build_unsafe_index_sync(grid).scan(478.0)

    fence = Fence([(la, lo) for la, lo in triangle])  # the existing Origin fence class
    bd = grid["bounds"]
    dlat_, dlon_, _, _ = T._grid_shape(bd["min_lat"], bd["max_lat"], bd["min_lon"], bd["max_lon"], 20)
    expected = {
        cell_pos(grid, r, c)
        for r in range(grid["rows"])
        for c in range(grid["cols"])
        if fence.contains_point(T._cell_lat(bd["max_lat"], dlat_, r), T._cell_lon(bd["min_lon"], dlon_, c))
    }
    total = grid["rows"] * grid["cols"]
    got = {(p["lat"], p["lon"]) for p in result["unsafePoints"]}
    assert got == expected  # exactly the cells the Origin fence covers, none outside it
    assert 0.4 * total < result["count"] < 0.7 * total  # roughly half of the bounding box


def test_an_unusable_polygon_falls_back_to_the_whole_grid_area(tmp_path):
    grid, _ = build_grid(tmp_path, SPEC_PATTERN)
    grid["polygon"] = [[0.0, 0.0], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0]]  # self-intersecting
    index = T._build_unsafe_index_sync(grid)
    assert index.area == "grid_bounding_box" and index.checked_cells == 16  # no usable polygon: whole grid


# --- performance / scale ----------------------------------------------------------------------


def test_real_sized_grid_scans_fast_and_only_returns_unsafe_cells():
    rows, cols = 717, 845  # the size of the real Origin grid
    rng = np.random.default_rng(2)
    elev = rng.integers(350, 761, size=(rows, cols)).astype(float)
    grid = {
        "rows": rows, "cols": cols, "grid": elev.tolist(), "spacing_m": 20,
        "bounds": {"min_lat": 22.0, "max_lat": 22.0 + rows * 1e-4, "min_lon": 76.0, "max_lon": 76.0 + cols * 1e-4},
        "polygon": [[22.0 - 1, 76.0 - 1], [22.0 - 1, 77.0], [23.0, 77.0], [23.0, 76.0 - 1]],  # covers everything
    }
    lat = lambda r: 22.0 + rows * 1e-4 - r * 1e-4
    lon = lambda c: 76.0 + c * 1e-4

    started = time.perf_counter()
    index = tu.TerrainScanIndex(grid, lat, lon)
    build = time.perf_counter() - started
    started = time.perf_counter()
    result = index.scan(700.0)
    scan = time.perf_counter() - started

    oracle = int((elev > 700.0).sum())
    assert result["count"] == oracle and 0 < oracle < 0.2 * rows * cols
    assert result["maxUnsafeElevation"] == float(elev.max()) == 760.0
    assert build < 5.0 and scan < 2.0  # generous bounds; typically ~0.1 s / ~0.05 s


# --- Step 3 effective threshold ---------------------------------------------------------------


def make_tracker():
    t = ts.TerrainSafetyTracker()
    assert t.set_origin("fp", 378.0, (22.5, 76.5), 50.0)
    return t


def test_effective_threshold_is_origin_level_until_a_takeoff_is_commanded():
    t = make_tracker()
    t.update_uav("1", 0.0)
    e = t.effective_payload()
    assert (e["uavId"], e["safetyThresholdAMSL"], e["altitudeSource"]) == (None, 378.0, "initial_50m")


def test_effective_threshold_is_the_lowest_of_the_active_uavs():
    t = make_tracker()
    t.update_uav("3", 0.0)  # on the ground, not commanded: ignored
    t.command_takeoff(100, ["1"])
    t.command_takeoff(60, ["2"])
    e = t.effective_payload()
    assert (e["uavId"], e["safetyThresholdAMSL"]) == ("2", 388.0)  # 378 + 60 - 50

    t.update_uav("2", 150.0)  # UAV 2 climbs to 150, flying: threshold 478; UAV 1 (100 -> 428) is now lowest
    e = t.effective_payload()
    assert (e["uavId"], e["safetyThresholdAMSL"]) == ("1", 428.0)


def test_disconnected_uavs_do_not_pin_the_threshold():
    t = make_tracker()
    t.command_takeoff(60, ["gone"])
    t.command_takeoff(100, ["1"])
    assert t.effective_payload()["safetyThresholdAMSL"] == 388.0
    assert t.effective_payload(["1"])["safetyThresholdAMSL"] == 428.0
    assert make_tracker().effective_payload(["1"])["uavId"] is None


def test_no_effective_threshold_without_an_active_origin():
    assert ts.TerrainSafetyTracker().effective_payload() is None


# --- integration: Origin set, Takeoff, telemetry (real terrain ext, fake app) ------------------


ORIGIN_A = rect(20, 25)  # 20 x 25 grid at lon 76.5 ..
ORIGIN_B = rect(20, 25, lat0=23.3, lon0=77.4)


def elevation_of(lat, lon):
    """378 m at the western edge of Origin A, +400 m per 0.01 deg east; flat 350 m up north (Origin B)."""
    return 378.0 + (lon - 76.5) * 40000.0 if lat < 23 else 350.0


def fake_uav(ahl):
    return SimpleNamespace(status=SimpleNamespace(position=SimpleNamespace(ahl=ahl)))


class FakeApp:
    def __init__(self):
        self.uavs: Dict[str, Any] = {}
        self.sent: List[Dict[str, Any]] = []
        self.sys_msgs: List[str] = []
        self.pending: List[Any] = []
        hub = SimpleNamespace()

        async def broadcast_message(msg):
            self.sent.append(msg)

        hub.broadcast_message = broadcast_message
        hub.create_notification = lambda body: body
        self.message_hub = hub
        self.object_registry = SimpleNamespace(ids_by_type=lambda _t: list(self.uavs))

    def find_uav_by_id(self, uav_id, response=None):
        return self.uavs.get(uav_id)

    def run_in_background(self, fn, *args, **kwargs):
        self.pending.append((fn, args))

    async def flush(self):
        pending, self.pending = self.pending, []
        for fn, args in pending:
            await fn(*args)

    def request_to_send_SYS_MSG_message(self, text, severity=None):
        self.sys_msgs.append(text)

    def unsafe_msgs(self):
        return [m for m in self.sent if m.get("type") == "X-TERRAIN-UNSAFE-RESP"]

    def telemetry(self, uav_id, ahl):
        self.uavs[uav_id] = fake_uav(ahl)
        ts.on_uav_status_updated(self, [uav_id])


@pytest.fixture
def env(tmp_path, monkeypatch):
    mgr = PatternTerrain(tmp_path / "srtm", func=elevation_of)
    monkeypatch.setattr(T, "_terrain_manager", mgr)
    monkeypatch.setattr(T, "configuration", {"terrain_grid_dir": str(tmp_path / "grid"), "broadcast_unsafe_points": True})
    monkeypatch.setattr(T, "log", None)
    monkeypatch.setattr(T, "_terrain_grid_cache", None)
    monkeypatch.setattr(T, "_latest_origin_fingerprint", None)
    monkeypatch.setattr(T, "app", None)
    ts.tracker.reset()
    T._reset_unsafe_terrain()
    yield SimpleNamespace(mgr=mgr, app=FakeApp())
    ts.tracker.reset()
    T._reset_unsafe_terrain()


async def set_origin(env, polygon):
    origin = (min(p[0] for p in polygon), min(p[1] for p in polygon))
    await T.generate_terrain_grid_for_origin(env.app, polygon, origin)


def total_cells():
    g = T.get_cached_terrain_grid()
    return g["rows"] * g["cols"]


async def test_unsafe_terrain_is_sent_when_the_grid_is_ready_before_takeoff(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)

    (m,) = env.app.unsafe_msgs()
    assert m["type"] == "X-TERRAIN-UNSAFE-RESP"
    assert m["status"] == "unsafe"
    assert m["thresholdAMSL"] == 378.0  # 378 + 50 (initial) - 50
    assert (m["thresholdUavId"], m["altitudeSource"]) == (None, "initial_50m")
    assert m["originFingerprint"] == ts.tracker.origin_fingerprint
    assert 0 < m["count"] < total_cells()  # a part of the area, never the whole grid
    assert m["count"] == len(m["unsafePoints"])
    assert all(p["elevation"] > 378.0 for p in m["unsafePoints"])
    assert m["maxUnsafeElevation"] == max(p["elevation"] for p in m["unsafePoints"])
    assert m["highestPoint"]["elevation"] == m["maxUnsafeElevation"]
    assert set(m["unsafePoints"][0]) == {"lat", "lon", "elevation"}
    assert any("Unsafe terrain" in s for s in env.app.sys_msgs)


async def test_takeoff_command_rescans_the_same_grid_with_the_new_threshold(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    grid, reads = T.get_cached_terrain_grid(), env.mgr.reads
    (before,) = env.app.unsafe_msgs()
    env.app.sent.clear()

    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()

    (after,) = env.app.unsafe_msgs()
    assert after["thresholdAMSL"] == 428.0  # 378 + 100 - 50
    assert after["altitudeSource"] == "takeoff_altitude" and after["thresholdUavId"] == "1"
    assert 0 < after["count"] < before["count"]  # fewer cells are above the higher threshold
    assert all(p["elevation"] > 428.0 for p in after["unsafePoints"])
    assert T.get_cached_terrain_grid() is grid and env.mgr.reads == reads  # same grid, 0 SRTM reads


async def test_the_documented_threshold_change_example(env):
    """Reference 378, margin 50: height 50 -> 378 flags 400/450/760; Takeoff 100 -> 428 flags
    450/760; Takeoff 150 -> 478 flags only 760. Same grid every time."""
    mgr = env.mgr
    # bands of columns at 400 / 450 / 760 m; column 0 (the reference point) stays 378 m
    mgr.func = lambda lat, lon: {1: 400.0, 2: 450.0, 3: 760.0}.get(round((lon - 76.5) / 0.0005), 378.0)
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    (m,) = env.app.unsafe_msgs()
    assert m["thresholdAMSL"] == 378.0
    assert {p["elevation"] for p in m["unsafePoints"]} == {400.0, 450.0, 760.0}

    for takeoff, threshold, expected in ((100, 428.0, {450.0, 760.0}), (150, 478.0, {760.0})):
        env.app.sent.clear()
        ts.on_takeoff_commanded(env.app, takeoff, ["1"])
        await env.app.flush()
        (m,) = env.app.unsafe_msgs()
        assert m["thresholdAMSL"] == threshold  # 378 + takeoff - 50
        assert {p["elevation"] for p in m["unsafePoints"]} == expected
        assert m["maxUnsafeElevation"] == 760.0


async def test_flying_altitude_changes_rescan_only_on_meaningful_change(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    reads = env.mgr.reads
    env.app.sent.clear()

    for ahl in (10.0, 50.0, 99.0):  # climbing: threshold stays 428 -> nothing new
        env.app.telemetry("1", ahl)
    await env.app.flush()
    assert env.app.unsafe_msgs() == []

    env.app.telemetry("1", 100.0)  # reached: still 100 -> threshold unchanged -> nothing sent
    env.app.telemetry("1", 103.0)  # < 5 m
    await env.app.flush()
    assert env.app.unsafe_msgs() == []

    env.app.telemetry("1", 120.0)  # meaningful: 378 + 120 + 50
    await env.app.flush()
    (m,) = env.app.unsafe_msgs()
    assert (m["thresholdAMSL"], m["altitudeSource"]) == (448.0, "telemetry_agl")
    assert env.mgr.reads == reads  # never touched SRTM


async def test_safe_result_when_the_threshold_is_above_all_terrain(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 500, ["1"])  # 378 + 500 - 50 = 828 > the highest terrain
    await env.app.flush()
    (m,) = env.app.unsafe_msgs()
    assert (m["status"], m["count"], m["unsafePoints"]) == ("safe", 0, [])
    assert (m["maxUnsafeElevation"], m["highestPoint"]) == (None, None)


async def test_no_message_is_sent_when_the_effective_threshold_did_not_change(env):
    env.app.uavs["1"] = fake_uav(0.0)
    env.app.uavs["2"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()

    await T._refresh_unsafe_terrain(env.app)  # same threshold again
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    assert len(env.app.unsafe_msgs()) == 1
    env.app.sent.clear()

    ts.on_takeoff_commanded(env.app, 100, ["1"])  # same altitude again
    ts.on_takeoff_commanded(env.app, 300, ["2"])  # UAV 2's own threshold is higher: lowest one unchanged
    await env.app.flush()
    assert env.app.unsafe_msgs() == []


async def test_lowest_uav_threshold_drives_the_unsafe_result(env):
    for uav_id in ("1", "2"):
        env.app.uavs[uav_id] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 60, ["1"])
    ts.on_takeoff_commanded(env.app, 100, ["2"])
    await env.app.flush()
    m = env.app.unsafe_msgs()[-1]
    assert (m["thresholdAMSL"], m["thresholdUavId"]) == (388.0, "1")


async def test_new_origin_uses_its_own_grid_and_drops_the_old_result(env, monkeypatch):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    (a,) = env.app.unsafe_msgs()
    assert a["status"] == "unsafe"

    seen = {}
    orig = T._build_terrain_grid_sync

    def spy(*args, **kw):
        seen["unsafe_state_during_build"] = (T._unsafe_cache, T._unsafe_index, T._unsafe_broadcast_key)
        return orig(*args, **kw)

    monkeypatch.setattr(T, "_build_terrain_grid_sync", spy)
    env.app.sent.clear()
    await set_origin(env, ORIGIN_B)  # flat 350 m: nothing above 350 (== the threshold, and 350 is not > 350)
    assert seen["unsafe_state_during_build"] == (None, None, None)  # nothing of Origin A survives
    (b,) = env.app.unsafe_msgs()
    assert b["status"] == "safe" and b["count"] == 0
    assert b["originFingerprint"] == ts.tracker.origin_fingerprint != a["originFingerprint"]
    assert b["thresholdAMSL"] == 350.0  # 350 + 50 - 50: the new Origin's reference terrain


async def test_same_origin_set_again_sends_the_result_again(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    await set_origin(env, ORIGIN_A)
    assert len(env.app.unsafe_msgs()) == 2


async def test_request_handler_returns_current_result_read_only(env):
    T.app = env.app
    req = SimpleNamespace(body={})
    unavailable = await T.handle_X_TERRAIN_UNSAFE_REQ(req, None, None)
    assert unavailable["type"] == "X-TERRAIN-UNSAFE-RESP"
    assert (unavailable["status"], unavailable["count"], unavailable["thresholdAMSL"]) == ("unavailable", 0, None)

    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    grid, reads = T.get_cached_terrain_grid(), env.mgr.reads
    (broadcast,) = env.app.unsafe_msgs()
    resp = await T.handle_X_TERRAIN_UNSAFE_REQ(req, None, None)
    assert {k: v for k, v in resp.items() if k != "type"} == {k: v for k, v in broadcast.items() if k != "type"}

    ts.on_takeoff_commanded(env.app, 100, ["1"])  # threshold moves; ask before the broadcast is flushed
    resp = await T.handle_X_TERRAIN_UNSAFE_REQ(req, None, None)
    assert resp["thresholdAMSL"] == 428.0  # the request always answers for the CURRENT threshold
    await env.app.flush()
    assert T.get_cached_terrain_grid() is grid and env.mgr.reads == reads


async def test_a_threshold_is_scanned_once_however_often_it_is_asked_for(env, monkeypatch):
    T.app = env.app
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)

    scans, builds = [], []
    orig_scan = tu.TerrainScanIndex.scan
    orig_build = T._build_unsafe_index_sync
    monkeypatch.setattr(tu.TerrainScanIndex, "scan", lambda self, *a, **k: scans.append(a[0]) or orig_scan(self, *a, **k))
    monkeypatch.setattr(T, "_build_unsafe_index_sync", lambda g: builds.append(1) or orig_build(g))

    req = SimpleNamespace(body={})
    for _ in range(3):  # same threshold (378) as the scan done at grid-ready
        await T.handle_X_TERRAIN_UNSAFE_REQ(req, None, None)
    await T._refresh_unsafe_terrain(env.app)
    assert scans == [] and builds == []

    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()  # 428: one new scan, on the SAME index
    await T.handle_X_TERRAIN_UNSAFE_REQ(req, None, None)
    await T._refresh_unsafe_terrain(env.app)
    assert scans == [428.0] and builds == []


async def test_unavailable_when_step3_has_no_threshold(env):
    T.app = env.app
    await set_origin(env, ORIGIN_A)
    ts.tracker.clear_origin()  # e.g. the Origin reference elevation is unknown
    resp = await T.handle_X_TERRAIN_UNSAFE_REQ(SimpleNamespace(body={}), None, None)
    assert resp["status"] == "unavailable" and resp["unsafePoints"] == []


# --- wiring --------------------------------------------------------------------------------------


def test_step4a_is_attached_to_step3_and_the_socket_handler_is_registered():
    assert T._refresh_unsafe_terrain in ts._threshold_listeners
    assert (tu.EVENT_TYPE, tu.REQUEST_TYPE) == ("X-TERRAIN-UNSAFE-RESP", "X-TERRAIN-UNSAFE-REQ")
    run_source = inspect.getsource(T.run)
    assert "terrain_unsafe.REQUEST_TYPE: handle_X_TERRAIN_UNSAFE_REQ" in run_source


def test_step4a_does_not_touch_srtm_or_the_grid_generator():
    source = inspect.getsource(tu)
    assert "get_elevation" not in source and "TerrainManager" not in source
    unsafe_flow = "".join(
        inspect.getsource(f) for f in (T._current_unsafe_result, T._refresh_unsafe_terrain, T._build_unsafe_index_sync)
    )
    for forbidden in ("get_elevation", "_build_terrain_grid_sync", "download_tile", "_load_terrain_grid_sync"):
        assert forbidden not in unsafe_flow


# --- strict comparison at the threshold: terrain > threshold ----------------------------------


def test_terrain_equal_to_the_threshold_is_safe_and_just_above_is_unsafe(tmp_path):
    # TEST 4 and TEST 5, threshold 350
    grid, _ = build_grid(tmp_path, [[350.0, 350.1, 349.9], [100, 100, 100], [100, 100, 100]])
    result = T._build_unsafe_index_sync(grid).scan(350.0)
    assert [p["elevation"] for p in result["unsafePoints"]] == [350.1]  # 350.0 is safe, 349.9 too


async def test_end_to_end_threshold_350_terrain_350_safe_and_350_1_unsafe(env):
    # home terrain 300 (column 0); two bands: exactly 350.0 and 350.1
    env.mgr.func = lambda lat, lon: {1: 350.0, 2: 350.1}.get(round((lon - 76.5) / 0.0005), 300.0)
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)  # drone height 50 (default), margin 50 -> threshold 300
    (m,) = env.app.unsafe_msgs()
    assert m["thresholdAMSL"] == 300.0
    assert {p["elevation"] for p in m["unsafePoints"]} == {350.0, 350.1}  # both are above 300

    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 100, ["1"])  # 300 + 100 - 50 = 350
    await env.app.flush()
    (m,) = env.app.unsafe_msgs()
    assert m["thresholdAMSL"] == 350.0
    assert {p["elevation"] for p in m["unsafePoints"]} == {350.1}  # terrain == 350 is SAFE


async def test_unsafe_points_message_explains_the_threshold(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    m = env.app.unsafe_msgs()[-1]
    # the inputs of the calculation travel with the result, so a client never has to recompute it
    assert (m["referenceTerrainElevation"], m["safetyAltitude"], m["safetyMargin"]) == (378.0, 100.0, 50.0)
    assert m["thresholdAMSL"] == m["referenceTerrainElevation"] + m["safetyAltitude"] - m["safetyMargin"] == 428.0
    assert (m["thresholdUavId"], m["altitudeSource"]) == ("1", "takeoff_altitude")
