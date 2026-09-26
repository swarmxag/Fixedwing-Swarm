"""Tests for the Step 3 terrain safety threshold (flockwave.server.terrain_safety)
and its wiring into the terrain extension (flockwave.server.ext.terrain).

Three stages per UAV:
  1. no Takeoff command yet        -> safety altitude 50 m   (initial_50m)
  2. Takeoff commanded, climbing   -> the commanded `alt`    (takeoff_altitude)
  3. AHL reached the commanded alt -> the actual AHL         (telemetry_agl)
"""

import inspect
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from flockwave.server import terrain_safety as ts
from flockwave.server.ext import terrain as T
from flockwave.server.terrain_safety import FlightPhase, TerrainSafetyTracker

REFERENCE = 378.0  # reference terrain elevation used in the examples
MARGIN = 50.0  # safety margin: a positive distance that is SUBTRACTED


def make_tracker(reference=REFERENCE, margin=MARGIN) -> TerrainSafetyTracker:
    t = TerrainSafetyTracker()
    assert t.set_origin("fp-A", reference, (22.5, 76.5), margin)
    return t


# --- The formula:  threshold = home terrain + drone height - safety margin -----------
#
# (This replaced  home terrain + height + offset.)  The margin is a POSITIVE distance
# that is subtracted; terrain strictly above the threshold is unsafe.


@pytest.mark.parametrize(
    "reference, height, margin, expected",
    [
        (300.0, 100.0, 50.0, 350.0),  # TEST 1
        (300.0, 50.0, 50.0, 300.0),  # TEST 2
        (300.0, 150.0, 50.0, 400.0),  # TEST 3
    ],
)
def test_threshold_is_home_terrain_plus_drone_height_minus_safety_margin(reference, height, margin, expected):
    assert ts.compute_threshold(reference, height, margin) == expected

    # the same through the tracker; the drone height comes from the Takeoff command
    t = TerrainSafetyTracker()
    assert t.set_origin("fp", reference, (0.0, 0.0), margin)
    (_origin, p) = t.command_takeoff(height, ["1"])
    assert p["referenceTerrainElevation"] == reference
    assert p["safetyAltitude"] == height
    assert p["safetyMargin"] == margin
    assert p["safetyThresholdAMSL"] == expected
    assert "safetyOffset" not in p  # renamed: it is a margin now, and it is subtracted


def test_pre_takeoff_drone_height_is_the_default_50_m_and_the_margin_is_subtracted():
    t = TerrainSafetyTracker()
    t.set_origin("fp", 300.0, (0.0, 0.0), 50.0)
    p = t.origin_payload()
    assert (p["safetyAltitude"], p["altitudeSource"]) == (50.0, "initial_50m")
    assert p["safetyThresholdAMSL"] == 300.0  # 300 + 50 - 50


def test_a_bigger_margin_lowers_the_threshold():
    for margin, expected in ((0.0, 400.0), (25.0, 375.0), (50.0, 350.0), (80.0, 320.0)):
        t = TerrainSafetyTracker()
        t.set_origin("fp", 300.0, (0.0, 0.0), margin)
        assert t.command_takeoff(100, ["1"])[1]["safetyThresholdAMSL"] == expected


def test_the_margin_is_a_positive_distance_and_a_negative_one_is_never_used():
    # TEST 6: users enter 50 to subtract 50; nobody has to enter -50
    assert ts.parse_safety_margin(50) == 50.0
    assert ts.parse_safety_margin(0) == 0.0  # no margin at all is allowed
    assert ts.parse_safety_margin(12.5) == 12.5
    for bad in (-50, -0.1, None, "50", float("nan"), float("inf"), True, [50]):
        assert ts.parse_safety_margin(bad) == ts.DEFAULT_SAFETY_MARGIN_M == 50.0
        assert not ts.is_valid_safety_margin(bad)

    # a negative margin must never turn into an ADDITION
    t = TerrainSafetyTracker()
    t.set_origin("fp", 300.0, (0.0, 0.0), -50.0)
    assert t.safety_margin == 50.0
    assert t.command_takeoff(100, ["1"])[1]["safetyThresholdAMSL"] == 350.0  # 300 + 100 - 50, not 450


def test_the_margin_can_change_only_with_a_new_origin_setup():
    t = make_tracker(reference=300.0, margin=50.0)
    assert t.origin_payload()["safetyThresholdAMSL"] == 300.0
    t.set_origin("fp-A", 300.0, (22.5, 76.5), 20.0)  # e.g. after a config change and a new Set Origin
    assert t.origin_payload()["safetyMargin"] == 20.0
    assert t.origin_payload()["safetyThresholdAMSL"] == 330.0


# --- Test 1: no Takeoff command -----------------------------------------------------


def test_no_takeoff_command_uses_initial_50m():
    t = make_tracker()
    p = t.update_uav("1", 0.0)

    assert p["safetyAltitude"] == 50.0
    assert p["altitudeSource"] == "initial_50m"
    assert p["flightPhase"] == "pre_takeoff"
    assert p["takeoffAltitude"] is None  # nothing commanded yet
    assert p["currentAltitudeAGL"] == 0.0
    assert p["safetyThresholdAMSL"] == 378.0  # 378 + 50 - 50
    assert p["type"] == "X-TERRAIN-SAFETY-THRESHOLD-RESP"


def test_initial_50m_is_available_without_any_uav_and_ignores_ground_noise():
    t = make_tracker()
    o = t.origin_payload()
    assert (o["uavId"], o["safetyAltitude"], o["altitudeSource"]) == (None, 50.0, "initial_50m")
    assert o["flightPhase"] == "pre_takeoff" and o["safetyThresholdAMSL"] == 378.0

    t.update_uav("1", 0.0)
    for noise in (0.3, -0.2, 1.1, 4.9, 12.0):  # no command: ground telemetry changes nothing
        assert t.update_uav("1", noise, armed=True, airborne=False) is None
    assert t.uav_payload("1")["safetyAltitude"] == 50.0


# --- Tests 2, 3, 4: the Takeoff command is the trigger --------------------------------


def test_takeoff_30_replaces_50_immediately():
    t = make_tracker()
    t.update_uav("1", 0.0)
    (origin, uav) = t.command_takeoff(30, ["1"])

    assert uav["safetyAltitude"] == 30.0
    assert uav["safetyThresholdAMSL"] == 358.0  # 378 + 30 - 50
    assert uav["altitudeSource"] == "takeoff_altitude"
    assert uav["currentAltitudeAGL"] == 0.0  # AHL still 0, and it does not matter
    assert origin["uavId"] is None and origin["safetyAltitude"] == 30.0


def test_takeoff_80_replaces_50_immediately_even_with_zero_ahl():
    t = make_tracker()
    t.update_uav("1", 0.0)
    (_origin, p) = t.command_takeoff(80, ["1"])

    # exactly the payload shape asked for
    assert p["takeoffAltitude"] == 80.0
    assert p["safetyAltitude"] == 80.0
    assert p["currentAltitudeAGL"] == 0.0
    assert p["altitudeSource"] == "takeoff_altitude"
    assert p["flightPhase"] == "climbing_to_takeoff_altitude"
    assert p["safetyThresholdAMSL"] == 408.0  # 378 + 80 - 50


def test_takeoff_100_replaces_50_immediately():
    t = make_tracker()
    t.update_uav("1", 0.0)
    (_origin, p) = t.command_takeoff(100, ["1"])
    assert p["safetyAltitude"] == 100.0 and p["safetyThresholdAMSL"] == 428.0


@pytest.mark.parametrize("alt", [20, 30, 50, 75, 80, 100, 250.5])
def test_any_takeoff_altitude_replaces_the_default(alt):
    t = make_tracker()
    t.update_uav("1", 0.0)
    (_origin, p) = t.command_takeoff(alt, ["1"])
    assert p["safetyAltitude"] == float(alt)
    assert p["safetyThresholdAMSL"] == REFERENCE + alt - MARGIN


def test_takeoff_command_needs_no_telemetry_at_all():
    t = make_tracker()  # UAV never reported anything
    (_origin, p) = t.command_takeoff(80, ["1"])
    assert p["safetyAltitude"] == 80.0 and p["currentAltitudeAGL"] is None


def test_invalid_takeoff_altitudes_are_ignored():
    t = make_tracker()
    t.update_uav("1", 0.0)
    for bad in (0, -5, None, "80", float("nan"), float("inf"), True):
        assert t.command_takeoff(bad, ["1"]) == []
    assert t.commanded_takeoff_altitude is None
    assert t.uav_payload("1")["safetyAltitude"] == 50.0


# --- Test 5: climbing keeps the commanded altitude -----------------------------------


def test_during_climb_safety_altitude_stays_at_the_commanded_altitude():
    t = make_tracker()
    t.update_uav("1", 0.0)
    t.command_takeoff(80, ["1"])

    for ahl in (0.0, 10.0, 20.0, 30.0, 50.0, 70.0, 79.0, 79.99):
        assert t.update_uav("1", ahl) is None  # nothing recalculated, nothing sent
        p = t.uav_payload("1")
        assert p["safetyAltitude"] == 80.0
        assert p["altitudeSource"] == "takeoff_altitude"
        assert p["flightPhase"] == "climbing_to_takeoff_altitude"
        assert p["safetyThresholdAMSL"] == 408.0


def test_climb_is_not_decided_by_heartbeat_or_ground_state():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    # armed/airborne flags only matter for landing and for un-commanded flight
    assert t.update_uav("1", 20.0, armed=True, airborne=True) is None
    assert t.update_uav("1", 20.0, armed=False, airborne=False) is None
    assert t.uav_payload("1")["safetyAltitude"] == 80.0


# --- Test 6: reaching the takeoff altitude -------------------------------------------


def test_reaching_takeoff_altitude_switches_to_telemetry_ahl():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    assert t.update_uav("1", 79.0) is None

    p = t.update_uav("1", 80.0)
    assert p["altitudeSource"] == "telemetry_agl"
    assert p["flightPhase"] == "flying"
    assert (p["takeoffAltitude"], p["safetyAltitude"], p["currentAltitudeAGL"]) == (80.0, 80.0, 80.0)
    assert p["safetyThresholdAMSL"] == 408.0


def test_overshooting_the_takeoff_altitude_also_switches():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    p = t.update_uav("1", 83.0)  # first sample already above the commanded altitude
    assert (p["safetyAltitude"], p["altitudeSource"]) == (83.0, "telemetry_agl")


# --- Test 7: flying ------------------------------------------------------------------


def test_flying_uses_actual_ahl_with_meaningful_change_threshold():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 80.0)

    assert t.update_uav("1", 82.0) is None  # < 5 m from the AHL used last
    p = t.update_uav("1", 85.0)
    assert (p["safetyAltitude"], p["safetyThresholdAMSL"]) == (85.0, 413.0)
    p = t.update_uav("1", 100.0)
    assert (p["safetyAltitude"], p["safetyThresholdAMSL"]) == (100.0, 428.0)
    p = t.update_uav("1", 150.0)
    assert (p["safetyAltitude"], p["safetyThresholdAMSL"]) == (150.0, 478.0)


def test_flying_payload_matches_the_documented_example():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 80.0)
    p = t.update_uav("1", 120.0)
    assert p["takeoffAltitude"] == 80.0
    assert p["safetyAltitude"] == 120.0
    assert p["currentAltitudeAGL"] == 120.0
    assert p["altitudeSource"] == "telemetry_agl"
    assert p["flightPhase"] == "flying"


def test_flying_below_the_takeoff_altitude_later_does_not_fall_back():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 80.0)
    p = t.update_uav("1", 60.0)  # e.g. the mission descends: still flying, still telemetry
    assert (p["safetyAltitude"], p["altitudeSource"], p["flightPhase"]) == (60.0, "telemetry_agl", "flying")


def test_default_recalc_threshold_and_boundary():
    assert ts.ALTITUDE_RECALC_THRESHOLD == 5.0
    assert ts.needs_recalculation(50, 52) is False
    assert ts.needs_recalculation(50, 56) is True
    assert ts.needs_recalculation(50, 54) is False and ts.needs_recalculation(50, 55) is True
    assert ts.needs_recalculation(50.3, 55.3) is True  # float rounding must not matter


def test_slow_drift_is_measured_against_last_calculation_not_last_sample():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 80.0)
    for ahl in (81.0, 82.0, 83.0, 84.0):
        assert t.update_uav("1", ahl) is None
    assert t.update_uav("1", 85.0)["safetyAltitude"] == 85.0


def test_select_safety_altitude_per_stage():
    S = ts.select_safety_altitude
    assert S(FlightPhase.PRE_TAKEOFF, None, 0.0) == (50.0, "initial_50m")
    assert S(FlightPhase.PRE_TAKEOFF, None, 30.0) == (50.0, "initial_50m")
    assert S(FlightPhase.CLIMBING, 80.0, 0.0) == (80.0, "takeoff_altitude")
    assert S(FlightPhase.CLIMBING, 80.0, 79.0) == (80.0, "takeoff_altitude")
    assert S(FlightPhase.FLYING, 80.0, 100.0) == (100.0, "telemetry_agl")
    assert S(FlightPhase.FLYING, 80.0, None) == (80.0, "takeoff_altitude")  # no usable AHL
    assert S(FlightPhase.FLYING, None, None) == (50.0, "initial_50m")


# --- new command, landing, flying without a command ------------------------------------


def test_pressing_takeoff_again_starts_the_climb_stage_over():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 100.0)  # flying at 100
    (_o, p) = t.command_takeoff(30, ["1"])
    assert (p["safetyAltitude"], p["altitudeSource"], p["flightPhase"]) == (
        30.0, "takeoff_altitude", "climbing_to_takeoff_altitude")

    p = t.update_uav("1", 100.0)  # next telemetry: 100 >= 30 -> flying again
    assert (p["safetyAltitude"], p["altitudeSource"]) == (100.0, "telemetry_agl")


def test_landing_returns_to_the_initial_default():
    t = make_tracker()
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 90.0, armed=True)
    assert t.commanded_takeoff_altitude == 80.0

    p = t.update_uav("1", 0.0, armed=False)  # landed and disarmed
    assert (p["safetyAltitude"], p["altitudeSource"], p["flightPhase"]) == (
        50.0, "initial_50m", "pre_takeoff")
    assert p["takeoffAltitude"] is None
    assert t.commanded_takeoff_altitude is None
    assert t.origin_payload()["altitudeSource"] == "initial_50m"


def test_uav_seen_flying_without_a_takeoff_command_uses_telemetry():
    t = make_tracker()  # e.g. server restarted mid-flight, or launched another way
    p = t.update_uav("1", 120.0, armed=True, airborne=True)
    assert (p["safetyAltitude"], p["altitudeSource"], p["flightPhase"]) == (120.0, "telemetry_agl", "flying")
    assert p["takeoffAltitude"] is None
    p = t.update_uav("2", 0.4, armed=True, airborne=False)  # on the ground: default applies
    assert (p["safetyAltitude"], p["altitudeSource"]) == (50.0, "initial_50m")


# --- multiple UAVs ---------------------------------------------------------------------


def test_command_only_affects_the_targeted_uavs():
    t = make_tracker()
    t.update_uav("1", 0.0)
    t.update_uav("2", 0.0)
    t.command_takeoff(80, ["1"])
    assert t.uav_payload("1")["safetyAltitude"] == 80.0
    assert t.uav_payload("2")["safetyAltitude"] == 50.0

    t.update_uav("1", 85.0)
    t.update_uav("2", 0.0)
    assert [p["uavId"] for p in t.snapshot()] == [None, "1", "2"]
    assert [p["uavId"] for p in t.snapshot(["2"])] == [None, "2"]


# --- Origin change / command before Origin ---------------------------------------------


def test_origin_change_before_takeoff_command_uses_new_reference():
    t = make_tracker(reference=300.0)
    assert t.origin_payload()["safetyThresholdAMSL"] == 300.0
    assert t.set_origin("fp-B", 350.0, (23.3, 77.4), 50.0)
    o = t.origin_payload()
    assert (o["referenceTerrainElevation"], o["safetyThresholdAMSL"]) == (350.0, 350.0)
    assert o["originFingerprint"] == "fp-B"


def test_origin_change_never_keeps_the_old_reference_elevation():
    t = make_tracker(reference=300.0)
    t.clear_origin()
    assert t.active is False and t.reference_terrain_elevation is None
    assert t.origin_payload() is None and t.snapshot() == []
    assert t.set_origin("fp", None, (0.0, 0.0), 50.0) is False and t.active is False


def test_origin_change_while_climbing_or_flying_keeps_the_uavs_stage():
    t = make_tracker(reference=300.0)
    t.command_takeoff(80, ["1", "2"])
    t.update_uav("1", 100.0)  # flying
    t.update_uav("2", 20.0)  # climbing

    t.clear_origin()
    assert t.set_origin("fp-B", 350.0, (23.3, 77.4), 50.0)
    by_uav = {p["uavId"]: p for p in t.snapshot()}
    assert by_uav["1"]["safetyThresholdAMSL"] == 400.0  # 350 + 100 - 50, telemetry
    assert by_uav["2"]["safetyThresholdAMSL"] == 380.0  # 350 + 80 - 50, still the commanded alt
    assert by_uav[None]["safetyThresholdAMSL"] == 380.0


def test_takeoff_command_before_any_origin_is_remembered():
    t = TerrainSafetyTracker()
    assert t.command_takeoff(80, ["1"]) == []  # nothing to publish yet
    assert t.wants_telemetry
    t.set_origin("fp", REFERENCE, (22.5, 76.5), MARGIN)
    by_uav = {p["uavId"]: p for p in t.snapshot()}
    assert by_uav["1"]["safetyThresholdAMSL"] == 408.0
    assert by_uav[None]["safetyThresholdAMSL"] == 408.0


# --- telemetry access ------------------------------------------------------------------


def test_read_uav_telemetry_uses_ahl_and_optional_heartbeat():
    from flockwave.server.ext.mavlink.enums import MAVMessageType, MAVModeFlag, MAVState

    armed = int(MAVModeFlag.SAFETY_ARMED)

    def uav(ahl, hb=None):
        d = {"status": SimpleNamespace(position=SimpleNamespace(ahl=ahl))}
        if hb is not None:
            heartbeat = SimpleNamespace(base_mode=hb[0], system_status=hb[1])
            d["get_last_message"] = lambda t: heartbeat if t == MAVMessageType.HEARTBEAT else None
        return SimpleNamespace(**d)

    assert ts.read_uav_telemetry(uav(12.5)) == (12.5, None, None)
    assert ts.read_uav_telemetry(uav(0.0, (armed, MAVState.STANDBY))) == (0.0, True, False)
    assert ts.read_uav_telemetry(uav(60.0, (armed, MAVState.ACTIVE))) == (60.0, True, True)
    assert ts.read_uav_telemetry(uav(60.0, (armed, MAVState.CRITICAL))) == (60.0, True, True)
    assert ts.read_uav_telemetry(uav(0.0, (0, MAVState.STANDBY))) == (0.0, False, False)
    assert ts.read_uav_telemetry(SimpleNamespace(status=None)) is None


# --- integration: real terrain extension, fake app ------------------------------------


class FakeTerrainManager(T.TerrainManager):
    """Deterministic terrain (378 m south of 23N, 350 m north of it) that counts
    every 'SRTM read'."""

    def __init__(self, terrain_dir):
        super().__init__(terrain_dir)
        self.reads = 0

    def download_tile(self, lat, lon):
        f = self.terrain_dir / f"{self.get_tile_name(lat, lon)}.hgt"
        f.write_bytes(b"")
        return f

    def get_elevation(self, latitude, longitude):
        self.reads += 1
        return 378.0 if latitude < 23 else 350.0


ORIGIN_A = [[22.5000, 76.5000], [22.5000, 76.5100], [22.5090, 76.5100], [22.5090, 76.5000]]
ORIGIN_B = [[23.3000, 77.4000], [23.3000, 77.4100], [23.3090, 77.4100], [23.3090, 77.4000]]


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

    def threshold_msgs(self):
        return [m for m in self.sent if m.get("type") == ts.EVENT_TYPE]

    def telemetry(self, uav_id, ahl):
        self.uavs[uav_id] = fake_uav(ahl)
        ts.on_uav_status_updated(self, [uav_id])


@pytest.fixture
def env(tmp_path, monkeypatch):
    mgr = FakeTerrainManager(tmp_path / "srtm")
    monkeypatch.setattr(T, "_terrain_manager", mgr)
    monkeypatch.setattr(T, "configuration", {"terrain_grid_dir": str(tmp_path / "grid")})
    monkeypatch.setattr(T, "log", None)
    monkeypatch.setattr(T, "_terrain_grid_cache", None)
    monkeypatch.setattr(T, "_latest_origin_fingerprint", None)
    ts.tracker.reset()
    yield SimpleNamespace(mgr=mgr, app=FakeApp())
    ts.tracker.reset()


async def set_origin(env, polygon):
    origin = (min(p[0] for p in polygon), min(p[1] for p in polygon))
    await T.generate_terrain_grid_for_origin(env.app, polygon, origin)


async def test_initial_threshold_is_sent_when_the_grid_is_ready(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)

    msgs = env.app.threshold_msgs()
    assert [m["uavId"] for m in msgs] == [None, "1"]
    for m in msgs:
        assert m["referenceTerrainElevation"] == 378.0
        assert m["safetyAltitude"] == 50.0
        assert m["altitudeSource"] == "initial_50m"
        assert m["flightPhase"] == "pre_takeoff"
        assert m["safetyThresholdAMSL"] == 378.0
    assert any("378.0" in s and "initial_50m" in s for s in env.app.sys_msgs)


async def test_pressing_takeoff_immediately_sends_the_updated_threshold(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()

    ts.on_takeoff_commanded(env.app, 80, ["1"])  # what the X-UAV-TAKEOFF handler calls
    assert env.app.threshold_msgs() == []  # scheduled, not yet flushed ...
    await env.app.flush()  # ... goes out at the next scheduling point; no telemetry needed

    by_uav = {m["uavId"]: m for m in env.app.threshold_msgs()}
    assert set(by_uav) == {None, "1"}
    m = by_uav["1"]
    assert m["type"] == "X-TERRAIN-SAFETY-THRESHOLD-RESP"
    assert (m["takeoffAltitude"], m["safetyAltitude"], m["currentAltitudeAGL"]) == (80.0, 80.0, 0.0)
    assert (m["altitudeSource"], m["flightPhase"]) == ("takeoff_altitude", "climbing_to_takeoff_altitude")
    assert m["safetyThresholdAMSL"] == 408.0
    assert by_uav[None]["safetyThresholdAMSL"] == 408.0


async def test_full_flow_pre_takeoff_climb_flying_via_the_telemetry_hook(env):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()

    ts.on_takeoff_commanded(env.app, 80, ["1"])
    await env.app.flush()
    env.app.sent.clear()

    for ahl in (0.0, 10.0, 30.0, 50.0, 70.0, 79.0):  # climbing: nothing changes, nothing sent
        env.app.telemetry("1", ahl)
    await env.app.flush()
    assert env.app.threshold_msgs() == []

    env.app.telemetry("1", 80.0)  # reached -> switch to telemetry
    await env.app.flush()
    (m,) = env.app.threshold_msgs()
    assert (m["altitudeSource"], m["flightPhase"], m["safetyAltitude"]) == ("telemetry_agl", "flying", 80.0)

    env.app.sent.clear()
    env.app.telemetry("1", 83.0)  # < 5 m: silent
    env.app.telemetry("1", 120.0)
    await env.app.flush()
    (m,) = env.app.threshold_msgs()
    assert (m["takeoffAltitude"], m["safetyAltitude"], m["currentAltitudeAGL"]) == (80.0, 120.0, 120.0)
    assert m["safetyThresholdAMSL"] == 448.0  # 378 + 120 - 50


async def test_takeoff_without_ids_applies_to_all_uavs(env):
    env.app.uavs["1"] = fake_uav(0.0)
    env.app.uavs["2"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()

    ts.on_takeoff_commanded(env.app, 100, [])
    await env.app.flush()
    by_uav = {m["uavId"]: m for m in env.app.threshold_msgs()}
    assert set(by_uav) == {None, "1", "2"}
    assert all(m["safetyAltitude"] == 100.0 for m in by_uav.values())


async def test_origin_change_uses_new_reference_before_and_during_flight(env):
    await set_origin(env, ORIGIN_A)
    assert ts.tracker.reference_terrain_elevation == 378.0

    env.app.sent.clear()
    await set_origin(env, ORIGIN_B)
    assert ts.tracker.reference_terrain_elevation == 350.0
    (m,) = env.app.threshold_msgs()
    assert m["safetyThresholdAMSL"] == 350.0  # 350 + 50 (initial) - 50

    env.app.uavs["1"] = fake_uav(0.0)
    ts.on_takeoff_commanded(env.app, 80, ["1"])
    env.app.telemetry("1", 100.0)  # flying
    env.app.sent.clear()
    await set_origin(env, ORIGIN_B)  # Origin set again while airborne
    by_uav = {m["uavId"]: m for m in env.app.threshold_msgs()}
    assert by_uav["1"]["safetyThresholdAMSL"] == 400.0  # 350 + 100 - 50


async def test_state_is_cleared_while_the_new_origin_grid_is_being_built(env, monkeypatch):
    await set_origin(env, ORIGIN_A)
    assert ts.tracker.active

    seen = {}
    orig_build = T._build_terrain_grid_sync

    def spy(*a, **k):
        seen["active_during_build"] = ts.tracker.active
        return orig_build(*a, **k)

    monkeypatch.setattr(T, "_build_terrain_grid_sync", spy)
    await set_origin(env, ORIGIN_B)
    assert seen == {"active_during_build": False}


async def test_altitude_changes_never_regenerate_grid_or_reread_srtm(env, monkeypatch):
    env.app.uavs["1"] = fake_uav(0.0)
    await set_origin(env, ORIGIN_A)
    await env.app.flush()

    grid_before = T.get_cached_terrain_grid()
    reads_before = env.mgr.reads
    assert reads_before > 0

    builds, loads = [], []
    monkeypatch.setattr(T, "_build_terrain_grid_sync", lambda *a, **k: builds.append(1))
    monkeypatch.setattr(T, "_load_terrain_grid_sync", lambda *a, **k: loads.append(1))

    ts.on_takeoff_commanded(env.app, 80, ["1"])
    for ahl in (0, 20, 79, 80, 85, 95, 120, 88, 60, 52, 30, 3):
        env.app.telemetry("1", float(ahl))
    ts.on_takeoff_commanded(env.app, 30, ["1"])
    await env.app.flush()

    assert builds == [] and loads == []  # no regeneration, no cache reload
    assert env.mgr.reads == reads_before  # no SRTM lookups at all
    assert T.get_cached_terrain_grid() is grid_before  # the same grid object throughout
    assert len(env.app.threshold_msgs()) > 3  # thresholds were being recalculated meanwhile


async def test_terrain_safety_failures_never_propagate_into_the_takeoff_path():
    class Boom(FakeApp):
        def find_uav_by_id(self, uav_id, response=None):
            raise RuntimeError("boom")

    ts.tracker.reset()
    try:
        ts.on_takeoff_commanded(Boom(), 80, ["1"])  # must not raise
        ts.tracker.set_origin("fp", REFERENCE, (0.0, 0.0), MARGIN)
        ts.on_uav_status_updated(Boom(), ["1"])  # must not raise either
    finally:
        ts.tracker.reset()


async def test_safety_request_handler_returns_current_thresholds(env):
    env.app.uavs["1"] = fake_uav(0.0)
    T.app = env.app
    try:
        unavailable = await T.handle_X_TERRAIN_SAFETY_REQ(SimpleNamespace(body={}), None, None)
        assert unavailable["status"] == "unavailable"

        await set_origin(env, ORIGIN_A)
        ts.on_takeoff_commanded(env.app, 80, ["1"])
        resp = await T.handle_X_TERRAIN_SAFETY_REQ(SimpleNamespace(body={}), None, None)
    finally:
        T.app = None
    assert resp["status"] == "ready"
    assert [t["uavId"] for t in resp["thresholds"]] == [None, "1"]
    assert resp["thresholds"][1]["safetyThresholdAMSL"] == 408.0


# --- wiring in app.py ------------------------------------------------------------------


def test_app_calls_the_terrain_hooks_at_the_right_places():
    from flockwave.server.app import SkybrushServer

    takeoff = inspect.getsource(SkybrushServer.dispatch_to_uavs)
    i_alt = takeoff.index("update_Takeoff_Alt(alt)")
    i_hook = takeoff.index("on_takeoff_commanded(self, alt, uav_ids)")
    assert i_alt < i_hook < takeoff.index("check_height")  # right after the alt is stored, before takeoff runs

    funnel = inspect.getsource(SkybrushServer.request_to_send_UAV_INF_message_for)
    assert "on_uav_status_updated(self, uav_ids)" in funnel


def test_grid_elevation_lookup_uses_the_grid_only():
    grid = {
        "bounds": {"min_lat": 10.0, "max_lat": 10.001, "min_lon": 20.0, "max_lon": 20.001},
        "spacing_m": 20,
    }
    _, _, rows, cols = T._grid_shape(10.0, 10.001, 20.0, 20.001, 20)
    grid["grid"] = [[float(r * 100 + c) for c in range(cols)] for r in range(rows)]
    assert T.get_grid_elevation(grid, 10.001, 20.0) == 0.0  # north-west cell
    assert T.get_grid_elevation(grid, 10.0, 20.0) == float((rows - 1) * 100)  # SW corner
    assert T.get_grid_elevation(grid, 11.0, 20.0) is None  # outside the grid
    grid["grid"][rows - 1][0] = None  # a void at the reference cell -> nearest valid neighbour
    assert T.get_grid_elevation(grid, 10.0, 20.0) is not None


# --- the safety margin from the extension configuration ------------------------------------


async def test_configured_safety_margin_is_subtracted(env, monkeypatch):
    monkeypatch.setattr(T, "configuration", {**T.configuration, "safety_margin_m": 30})
    await set_origin(env, ORIGIN_A)  # terrain at the Origin: 378 m
    o = ts.tracker.origin_payload()
    assert o["safetyMargin"] == 30.0
    assert o["safetyThresholdAMSL"] == 398.0  # 378 + 50 (initial height) - 30


async def test_default_safety_margin_when_not_configured(env):
    await set_origin(env, ORIGIN_A)
    assert ts.tracker.origin_payload()["safetyMargin"] == 50.0


async def test_a_negative_configured_margin_is_rejected_not_added(env, monkeypatch, capsys):
    monkeypatch.setattr(T, "configuration", {**T.configuration, "safety_margin_m": -50})
    await set_origin(env, ORIGIN_A)
    o = ts.tracker.origin_payload()
    assert o["safetyMargin"] == 50.0
    assert o["safetyThresholdAMSL"] == 378.0  # 378 + 50 - 50; NOT 378 + 50 + 50
    assert "ignoring safety_margin_m=-50" in capsys.readouterr().out


# --- the reference (home) terrain is the terrain at the UAV's HOME, not at the Origin corner ---
#
# (Real case: the corner of the Origin area was on a 6005 m slope, the drones stood on ~4096 m.)

CORNER = (30.7219, 79.7345)  # Origin corner: sits on a high peak
HOME_A = (30.8025, 79.8148)  # where the UAVs are
HOME_B = (30.8026, 79.8149)  # ~14 m from HOME_A
FAR = (30.8225, 79.8348)  # ~2.7 km away


def grid_lookup(lat, lon):
    """A stand-in for the terrain grid: 6005 m near the corner, 4096 m around HOME_A, 4077 m further east."""
    if lon > 79.83:
        return 4077.0
    return 4096.0 if lat > 30.75 else 6005.0


def home_tracker(margin=50.0, lookup=grid_lookup):
    t = TerrainSafetyTracker()
    assert t.set_origin("fp", 6005.0, CORNER, margin, lookup)
    return t


def test_before_any_uav_position_the_origin_corner_is_the_reference():
    t = home_tracker()
    o = t.origin_payload()
    assert (o["referenceTerrainElevation"], o["referenceSource"]) == (6005.0, "origin_corner")
    assert o["referenceLocation"] == {"lat": CORNER[0], "lon": CORNER[1]}
    assert o["safetyThresholdAMSL"] == 6005.0  # 6005 + 50 - 50


def test_the_reference_is_the_terrain_at_the_uav_home():
    t = home_tracker()
    p = t.update_uav("1", 0.0, position=HOME_A)
    assert (p["referenceTerrainElevation"], p["referenceSource"]) == (4096.0, "uav_home")
    assert p["referenceLocation"] == {"lat": HOME_A[0], "lon": HOME_A[1]}
    assert p["safetyThresholdAMSL"] == 4096.0  # 4096 + 50 (initial height) - 50
    # ... and so does the Origin-level threshold once a UAV home is known
    o = t.origin_payload()
    assert (o["referenceTerrainElevation"], o["referenceSource"]) == (4096.0, "swarm_home")
    assert o["safetyThresholdAMSL"] == 4096.0


def test_the_origin_level_reference_is_the_lowest_uav_home():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)  # 4096
    t.update_uav("2", 0.0, position=FAR)  # 4077
    assert t.uav_payload("1")["referenceTerrainElevation"] == 4096.0
    assert t.uav_payload("2")["referenceTerrainElevation"] == 4077.0
    o = t.origin_payload()
    assert (o["referenceTerrainElevation"], o["referenceSource"]) == (4077.0, "swarm_home")
    assert o["referenceLocation"] == {"lat": FAR[0], "lon": FAR[1]}
    assert t.origin_payload(["1"])["referenceTerrainElevation"] == 4096.0  # only connected UAVs count


def test_takeoff_threshold_uses_the_home_terrain():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)
    (_o, p) = t.command_takeoff(100, ["1"])
    assert p["safetyThresholdAMSL"] == 4146.0  # 4096 + 100 - 50, not 6005 + 100 - 50
    assert t.effective_payload()["referenceSource"] == "uav_home"


def test_the_home_is_frozen_from_the_takeoff_command_on():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)
    t.command_takeoff(80, ["1"])
    # it climbs, flies far away over lower terrain: the reference stays where it took off
    assert t.update_uav("1", 40.0, position=FAR) is None
    p = t.update_uav("1", 85.0, position=FAR)
    assert p["flightPhase"] == "flying"
    assert (p["referenceTerrainElevation"], p["referenceSource"]) == (4096.0, "uav_home")
    assert p["referenceLocation"] == {"lat": HOME_A[0], "lon": HOME_A[1]}


def test_gps_jitter_on_the_ground_does_not_move_the_home_or_republish():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)
    assert t.take_origin_change() is True
    assert t.take_origin_change() is False  # reported once
    assert t.update_uav("1", 0.0, position=HOME_B) is None  # ~14 m: still the same home
    assert t.uav_payload("1")["referenceLocation"] == {"lat": HOME_A[0], "lon": HOME_A[1]}
    assert t.take_origin_change() is False


def test_a_uav_carried_far_before_takeoff_gets_a_new_home():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)
    p = t.update_uav("1", 0.0, position=FAR)  # ~2.7 km away, still on the ground
    assert p["referenceTerrainElevation"] == 4077.0
    assert p["referenceLocation"] == {"lat": FAR[0], "lon": FAR[1]}


def test_unusable_positions_never_become_a_home():
    t = home_tracker()
    for bad in (None, (0.0, 0.0), (float("nan"), 79.8), (30.8, float("inf")), (91.0, 79.8), (30.8, 181.0), "x", (30.8,)):
        t.update_uav("1", 0.0, position=bad)
        assert t.uav_payload("1")["referenceSource"] == "origin_corner", bad
    assert ts.read_uav_position(SimpleNamespace(status=SimpleNamespace(position=SimpleNamespace(lat=0, lon=0)))) is None
    assert ts.read_uav_position(SimpleNamespace(status=SimpleNamespace(position=SimpleNamespace(lat=30.8, lon=79.8)))) == (30.8, 79.8)
    assert ts.read_uav_position(SimpleNamespace(status=None)) is None


def test_a_uav_first_seen_in_the_air_does_not_take_its_air_position_as_home():
    t = home_tracker()
    p = t.update_uav("1", 120.0, armed=True, airborne=True, position=HOME_A)
    assert p["flightPhase"] == "flying"
    assert p["referenceSource"] == "origin_corner"  # its takeoff place is unknown
    t.update_uav("2", 0.0, position=FAR)
    assert t.uav_payload("1")["referenceSource"] == "swarm_home"  # ... so it uses the swarm's lowest home


def test_a_position_outside_the_terrain_grid_falls_back_to_the_corner():
    t = home_tracker(lookup=lambda lat, lon: None)  # the grid does not cover it
    p = t.update_uav("1", 0.0, position=HOME_A)
    assert (p["referenceTerrainElevation"], p["referenceSource"]) == (6005.0, "origin_corner")


def test_a_new_origin_rereads_every_home_from_its_own_grid():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)
    assert t.uav_payload("1")["referenceTerrainElevation"] == 4096.0

    assert t.set_origin("fp-B", 5000.0, CORNER, 50.0, lambda lat, lon: 3900.0)  # another Origin, another grid
    p = t.uav_payload("1")
    assert (p["referenceTerrainElevation"], p["referenceSource"]) == (3900.0, "uav_home")  # no new position needed

    assert t.set_origin("fp-C", 5000.0, CORNER, 50.0, lambda lat, lon: None)  # UAV is outside this Origin's grid
    assert t.uav_payload("1")["referenceSource"] == "origin_corner"


def test_a_landed_uav_takes_the_place_it_landed_on_as_its_next_home():
    t = home_tracker()
    t.update_uav("1", 0.0, position=HOME_A)
    t.command_takeoff(80, ["1"])
    t.update_uav("1", 90.0, armed=True, position=FAR)  # flying
    p = t.update_uav("1", 0.0, armed=False, position=FAR)  # landed
    assert p["flightPhase"] == "pre_takeoff" and p["referenceSource"] == "origin_corner"  # home forgotten
    p = t.update_uav("1", 0.0, armed=False, position=FAR)  # next update: on the ground, new home
    assert (p["referenceTerrainElevation"], p["referenceSource"]) == (4077.0, "uav_home")


def test_a_takeoff_command_records_the_home_of_a_uav_not_seen_before():
    t = home_tracker()
    (_o, p) = t.command_takeoff(100, ["1"], positions={"1": HOME_A})
    assert (p["referenceTerrainElevation"], p["safetyThresholdAMSL"]) == (4096.0, 4146.0)


def test_the_margin_and_height_still_follow_the_formula_with_the_home_terrain():
    t = home_tracker(margin=30.0)
    t.update_uav("1", 0.0, position=HOME_A)
    (_o, p) = t.command_takeoff(120, ["1"])
    assert p["safetyThresholdAMSL"] == p["referenceTerrainElevation"] + p["safetyAltitude"] - p["safetyMargin"] == 4186.0


# integration: the hook, Set Origin and the messages -------------------------------------------------


def uav_at(ahl, position):
    return SimpleNamespace(
        status=SimpleNamespace(position=SimpleNamespace(ahl=ahl, lat=position[0], lon=position[1]))
    )


def high_corner_terrain(lat, lon):
    """Origin A: 600 m along the western edge (where the Origin corner is), 400 m everywhere else."""
    return 600.0 if lon < 76.5003 else 400.0


HOME_ON_A = (22.505, 76.505)  # inside Origin A, on the 400 m terrain


async def test_set_origin_with_uavs_on_low_ground_uses_their_terrain_not_the_corner(env):
    env.mgr.get_elevation = high_corner_terrain
    env.app.uavs["1"] = uav_at(0.0, HOME_ON_A)
    await set_origin(env, ORIGIN_A)  # the corner (west edge) is 600 m; the UAV stands on 400 m

    by_uav = {m["uavId"]: m for m in env.app.threshold_msgs()}
    assert (by_uav[None]["referenceTerrainElevation"], by_uav[None]["referenceSource"]) == (400.0, "swarm_home")
    assert (by_uav["1"]["referenceTerrainElevation"], by_uav["1"]["referenceSource"]) == (400.0, "uav_home")
    assert by_uav["1"]["safetyThresholdAMSL"] == 400.0  # 400 + 50 - 50 -- not 600
    assert ts.tracker.reference_terrain_elevation == 600.0  # the corner value is kept only as the fallback


async def test_a_uav_without_gps_keeps_the_corner_until_it_has_a_position(env):
    env.mgr.get_elevation = high_corner_terrain
    env.app.uavs["1"] = uav_at(0.0, (0.0, 0.0))  # no fix yet
    await set_origin(env, ORIGIN_A)
    assert env.app.threshold_msgs()[0]["referenceSource"] == "origin_corner"
    assert env.app.threshold_msgs()[0]["safetyThresholdAMSL"] == 600.0
    env.app.sent.clear()

    env.app.uavs["1"] = uav_at(0.0, HOME_ON_A)  # GPS fix arrives: no polling, the telemetry hook does it
    ts.on_uav_status_updated(env.app, ["1"])
    await env.app.flush()
    by_uav = {m["uavId"]: m for m in env.app.threshold_msgs()}
    assert set(by_uav) == {None, "1"}  # the Origin-level threshold is republished too
    assert by_uav[None]["safetyThresholdAMSL"] == 400.0
    assert by_uav["1"]["referenceSource"] == "uav_home"


async def test_the_takeoff_altitude_is_added_to_the_home_terrain(env):
    env.mgr.get_elevation = high_corner_terrain
    env.app.uavs["1"] = uav_at(0.0, HOME_ON_A)
    await set_origin(env, ORIGIN_A)
    env.app.sent.clear()
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    m = {x["uavId"]: x for x in env.app.threshold_msgs()}["1"]
    assert (m["referenceTerrainElevation"], m["safetyThresholdAMSL"]) == (400.0, 450.0)  # 400 + 100 - 50


async def test_the_takeoff_command_records_the_home_of_a_uav_that_had_no_telemetry_yet(env):
    env.mgr.get_elevation = high_corner_terrain
    await set_origin(env, ORIGIN_A)  # no UAVs at all yet: the corner (600 m) is the reference
    assert ts.tracker.origin_payload()["referenceSource"] == "origin_corner"
    env.app.sent.clear()

    env.app.uavs["1"] = uav_at(0.0, HOME_ON_A)  # first seen at the moment Takeoff is pressed
    ts.on_takeoff_commanded(env.app, 100, ["1"])
    await env.app.flush()
    m = {x["uavId"]: x for x in env.app.threshold_msgs()}["1"]
    assert (m["referenceTerrainElevation"], m["referenceSource"]) == (400.0, "uav_home")
    assert m["safetyThresholdAMSL"] == 450.0  # 400 + 100 - 50

