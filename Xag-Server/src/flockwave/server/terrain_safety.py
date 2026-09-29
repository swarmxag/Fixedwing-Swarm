"""Step 3 of the terrain-safety system: the safety threshold.

    safetyThresholdAMSL = referenceTerrainElevation + safetyAltitude - safetyMargin

Terrain STRICTLY above that AMSL elevation is unsafe (Step 4). `safetyMargin` is a
positive distance in metres that is SUBTRACTED: a margin of 50 m puts the
threshold 50 m below (home terrain + drone height), i.e. it flags terrain that
comes within 50 m of the drone's altitude, not only terrain above it.

`referenceTerrainElevation` is the terrain elevation at the UAV's HOME: the place
it stands on before its Takeoff command (read from the Step 2 terrain grid, so no
SRTM access). Until a UAV has a valid position the corner of the Origin area is used,
and `referenceSource` says which one a threshold was built from:
``uav_home`` / ``swarm_home`` (the lowest home of all UAVs, used for the Origin-level
threshold) / ``origin_corner`` (no UAV position known yet).

`safetyAltitude` (the drone height) follows three stages per UAV, driven by the operator's Takeoff
command and by telemetry -- never by "height == 0":

1. ``pre_takeoff`` -- no Takeoff command yet: a fixed default of 50 m, so terrain
   safety information can be shown in the GCS before takeoff
   (altitudeSource ``initial_50m``).
2. ``climbing_to_takeoff_altitude`` -- from the moment ``X-UAV-TAKEOFF`` is
   received until the UAV's height above home (AHL) reaches the commanded
   altitude: exactly the commanded ``alt`` (altitudeSource ``takeoff_altitude``),
   whatever the AHL is meanwhile. The command itself is the trigger: nothing
   waits for the UAV to move.
3. ``flying`` -- once AHL has reached the commanded altitude: the actual AHL from
   telemetry (altitudeSource ``telemetry_agl``), recalculated only when it moves
   by at least ALTITUDE_RECALC_THRESHOLD from the value last used.

This module holds bookkeeping only. It never reads SRTM and never touches the
Step 2 terrain grid: the terrain extension (ext/terrain.py) hands it the
reference elevation of each Origin, and app.py hands it takeoff commands and
telemetry updates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Tuple

__all__ = (
    "ALTITUDE_RECALC_THRESHOLD",
    "DEFAULT_SAFETY_MARGIN_M",
    "EVENT_TYPE",
    "HOME_RELATCH_DISTANCE_M",
    "INITIAL_SAFETY_ALTITUDE_M",
    "FlightPhase",
    "TerrainSafetyTracker",
    "add_threshold_listener",
    "compute_threshold",
    "is_valid_safety_margin",
    "needs_recalculation",
    "parse_safety_margin",
    "read_uav_position",
    "on_altitude_commanded",
    "select_safety_altitude",
    "tracker",
)

EVENT_TYPE = "X-TERRAIN-SAFETY-THRESHOLD-RESP"

# Safety altitude used until a Takeoff command exists (stage 1). Only a default:
# the first Takeoff command replaces it.
INITIAL_SAFETY_ALTITUDE_M = 50.0

# Safety margin in metres, subtracted from (home terrain + drone height);
# extension setting `safety_margin_m`. Always a positive distance.
DEFAULT_SAFETY_MARGIN_M = 50.0

# An in-flight AHL change smaller than this (metres), measured from the AHL used
# for the last calculation, does not trigger a new calculation or message.
ALTITUDE_RECALC_THRESHOLD = 5.0

# The takeoff altitude counts as reached when AHL >= commanded alt - tolerance.
TAKEOFF_REACHED_TOLERANCE_M = 0.0

# A climb that never quite reaches the commanded altitude must not keep the UAV
# in `climbing` for the rest of the sortie: that stage reports the COMMANDED
# altitude, so a UAV levelling off below it would be treated as higher than it
# is -- an error in the unsafe direction, and a permanent one. Fixed-wing
# altitude-hold error alone makes levelling off a few metres low routine.
#
# So a climb is also considered finished once AHL stops rising: after this many
# consecutive telemetry updates without a gain of at least
# CLIMB_PROGRESS_EPSILON_M over the highest AHL seen so far, the UAV switches to
# reporting its real AHL. A genuine climb keeps resetting the counter and is
# unaffected. Counted in updates rather than seconds because this module has no
# clock -- at a few Hz of UAV-INF this is on the order of several seconds.
CLIMB_STALL_UPDATES = 20

# AHL gain that counts as "still climbing" (below this is noise, not progress).
CLIMB_PROGRESS_EPSILON_M = 1.0

# Stall detection only applies to a UAV that is actually up: one sitting on the
# ground after a Takeoff command has a flat AHL too, and must keep reporting the
# commanded altitude (that is the pre-flight planning view, and treating it as
# "flying at 0 m" would flag nearly all terrain). Used only when the heartbeat
# does not already say `airborne`.
MIN_AIRBORNE_AHL_M = 20.0

# Where the reference (home) terrain elevation of a threshold comes from.
SOURCE_UAV_HOME = "uav_home"
SOURCE_SWARM_HOME = "swarm_home"
SOURCE_ORIGIN_CORNER = "origin_corner"

# A UAV that is still on the ground and has moved farther than this from its
# recorded home gets a new home (it was carried elsewhere); GPS jitter does not.
HOME_RELATCH_DISTANCE_M = 20.0

SOURCE_INITIAL = "initial_50m"
SOURCE_TAKEOFF_ALTITUDE = "takeoff_altitude"
SOURCE_TELEMETRY_AGL = "telemetry_agl"
# An in-flight level-off the operator commanded ("same") that is LOWER than the
# UAV's current AHL: the descent is treated as already in effect.
SOURCE_COMMANDED_ALTITUDE = "commanded_altitude"

_EPSILON = 1e-9


class FlightPhase(str, Enum):
    PRE_TAKEOFF = "pre_takeoff"
    CLIMBING = "climbing_to_takeoff_altitude"
    FLYING = "flying"


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def compute_threshold(
    reference_terrain_elevation: float, safety_altitude: float, safety_margin: float
) -> float:
    """safetyThresholdAMSL = home terrain + drone height - safety margin.

    `safety_margin` is a positive distance that is subtracted; do not pass a
    negative number to "subtract" more (see `parse_safety_margin`)."""
    return reference_terrain_elevation + safety_altitude - safety_margin


def is_valid_safety_margin(value: Any) -> bool:
    """A safety margin is a finite number of metres >= 0."""
    return _is_number(value) and value >= 0


def parse_safety_margin(value: Any) -> float:
    """The configured safety margin as a positive distance in metres. Anything
    that is not a finite number >= 0 (missing, invalid, or NEGATIVE) gives the
    default: the margin is always subtracted, so a negative value must never
    silently turn into an addition."""
    return float(value) if is_valid_safety_margin(value) else DEFAULT_SAFETY_MARGIN_M


def select_safety_altitude(
    phase: FlightPhase,
    takeoff_altitude: Optional[float],
    flying_agl: Optional[float],
    commanded_altitude: Optional[float] = None,
) -> Tuple[float, str]:
    """(safetyAltitude, altitudeSource) for a stage.

    * flying with a valid AHL -> that AHL, or a lower COMMANDED altitude if one
      is pending (see below)
    * a Takeoff command exists (climbing, or flying without a usable AHL)
      -> the commanded altitude
    * otherwise -> the 50 m initial default

    `commanded_altitude` is an in-flight level-off target the operator has asked
    for but the UAV may not have reached yet (the "same" command). The LOWER of
    it and the actual AHL governs, which is the same rule the swarm-side gate
    applies: a commanded DESCENT is a hazard the moment it is ordered, so it
    counts immediately, while a commanded CLIMB earns no credit until the UAV
    has actually gained the height. Omitted (None) reproduces the previous
    behaviour exactly.
    """
    if phase is FlightPhase.FLYING and _is_number(flying_agl):
        if _is_number(commanded_altitude) and commanded_altitude < flying_agl:  # type: ignore[operator]
            return float(commanded_altitude), SOURCE_COMMANDED_ALTITUDE  # type: ignore[arg-type]
        return float(flying_agl), SOURCE_TELEMETRY_AGL  # type: ignore[arg-type]
    if takeoff_altitude is not None:
        return float(takeoff_altitude), SOURCE_TAKEOFF_ALTITUDE
    return INITIAL_SAFETY_ALTITUDE_M, SOURCE_INITIAL


def needs_recalculation(
    last_agl: Optional[float],
    new_agl: Optional[float],
    threshold: float = ALTITUDE_RECALC_THRESHOLD,
) -> bool:
    """Whether a new AHL differs enough from the AHL used for the last
    calculation (not from the last *sample*, so slow drift accumulates). A
    change of exactly `threshold` counts."""
    if not _is_number(new_agl):
        return False
    if not _is_number(last_agl):
        return True
    return abs(new_agl - last_agl) >= threshold - _EPSILON  # type: ignore[operator]


def _valid_position(position: Any) -> bool:
    """A usable lat/lon: finite, in range, and not the (0, 0) the MAVLink driver
    reports while a UAV has no GPS fix yet."""
    try:
        lat, lon = float(position[0]), float(position[1])
    except (TypeError, ValueError, IndexError):
        return False
    return (
        math.isfinite(lat)
        and math.isfinite(lon)
        and abs(lat) <= 90
        and abs(lon) <= 180
        and not (abs(lat) < 1e-6 and abs(lon) < 1e-6)
    )


def _distance_m(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Approximate distance in metres between two lat/lon points (same
    equirectangular approximation the terrain grid uses)."""
    dlat = (a[0] - b[0]) * 111320.0
    dlon = (a[1] - b[1]) * 111320.0 * math.cos(math.radians((a[0] + b[0]) / 2.0))
    return math.hypot(dlat, dlon)


@dataclass
class _UAVState:
    takeoff_alt: Optional[float] = None  # commanded via X-UAV-TAKEOFF; None = no command
    reached: bool = False  # AHL has reached takeoff_alt (or UAV seen flying) -> stage 3
    current_agl: Optional[float] = None  # latest telemetry AHL
    calc_agl: Optional[float] = None  # AHL the current stage-3 threshold was computed from
    home: Optional[Tuple[float, float]] = None  # where it stood before its Takeoff command
    home_terrain: Optional[float] = None  # terrain elevation at `home` (m AMSL), from the grid
    climb_peak: Optional[float] = None  # highest AHL seen during the current climb
    climb_stall: int = 0  # consecutive updates with no meaningful gain on climb_peak
    commanded_alt: Optional[float] = None  # in-flight level-off target ("same"); None = none pending

    @property
    def phase(self) -> FlightPhase:
        if self.reached:
            return FlightPhase.FLYING
        if self.takeoff_alt is not None:
            return FlightPhase.CLIMBING
        return FlightPhase.PRE_TAKEOFF


class TerrainSafetyTracker:
    """Safety-threshold state for the current Origin and for each UAV.

    What belongs to an Origin (reference terrain elevation, fingerprint) is
    dropped by `clear_origin()`. What belongs to a UAV (its Takeoff command and
    flight stage) is NOT: changing the Origin while a UAV is climbing or flying
    does not un-take-off it. `reset()` drops everything.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._uavs: Dict[str, _UAVState] = {}
        self.commanded_takeoff_altitude: Optional[float] = None  # last command, any UAV
        self.clear_origin()

    def clear_origin(self) -> None:
        """Forget the previous Origin, including its reference elevation."""
        self.active = False
        self.origin_fingerprint: Optional[str] = None
        self.reference_terrain_elevation: Optional[float] = None
        self.reference_location: Optional[Tuple[float, float]] = None
        self.safety_margin = DEFAULT_SAFETY_MARGIN_M
        self._home_terrain_lookup: Optional[Callable[[float, float], Optional[float]]] = None
        self._origin_dirty = False

    @property
    def wants_telemetry(self) -> bool:
        """Whether telemetry updates matter right now (cheap hot-path test)."""
        return self.active or self.commanded_takeoff_altitude is not None

    def set_origin(
        self,
        origin_fingerprint: str,
        reference_terrain_elevation: Optional[float],
        reference_location: Tuple[float, float],
        safety_margin: float,
        home_terrain_lookup: Optional[Callable[[float, float], Optional[float]]] = None,
    ) -> bool:
        """Starts tracking a new Origin. Returns False -- and stays inactive --
        if the reference terrain elevation is unknown.

        `reference_terrain_elevation` / `reference_location` describe the corner of
        the Origin area: the fallback used until a UAV's own home is known.
        `home_terrain_lookup(lat, lon)` gives the terrain elevation at a UAV's home
        from this Origin's terrain grid (None outside the grid)."""
        self.clear_origin()
        self.origin_fingerprint = origin_fingerprint
        self.reference_location = reference_location
        self.safety_margin = parse_safety_margin(safety_margin)
        self._home_terrain_lookup = home_terrain_lookup
        # UAV homes belong to the UAVs, but their terrain elevation to this Origin's grid
        for st in self._uavs.values():
            st.home_terrain = self._lookup_home_terrain(st.home) if st.home else None
        if _is_number(reference_terrain_elevation):
            self.reference_terrain_elevation = float(reference_terrain_elevation)  # type: ignore[arg-type]
            self.active = True
        return self.active

    # -- home terrain -----------------------------------------------------------

    def _lookup_home_terrain(self, position: Optional[Tuple[float, float]]) -> Optional[float]:
        if position is None or self._home_terrain_lookup is None:
            return None
        value = self._home_terrain_lookup(position[0], position[1])
        return float(value) if _is_number(value) else None

    def _latch_home(self, st: _UAVState, position: Any) -> bool:
        """Records the UAV's home from its position (first valid one, or a new one
        if it was carried > HOME_RELATCH_DISTANCE_M away). Returns whether the
        terrain elevation at its home changed."""
        if not _valid_position(position):
            return False
        here = (float(position[0]), float(position[1]))
        if st.home is not None and _distance_m(st.home, here) < HOME_RELATCH_DISTANCE_M:
            return False
        previous = st.home_terrain
        st.home = here
        st.home_terrain = self._lookup_home_terrain(here)
        return st.home_terrain != previous

    def _swarm_reference(self, wanted: Optional[set] = None) -> Tuple[float, Tuple[float, float], str]:
        """The Origin-level reference: the LOWEST home terrain among the UAVs with a
        known home (lowest = lowest threshold = flags the most terrain, so it covers
        the others), else the corner of the Origin area."""
        homes = [
            st
            for uav_id, st in self._uavs.items()
            if st.home_terrain is not None and (wanted is None or uav_id in wanted)
        ]
        if homes:
            lowest = min(homes, key=lambda s: s.home_terrain)  # type: ignore[arg-type,return-value]
            return lowest.home_terrain, lowest.home, SOURCE_SWARM_HOME  # type: ignore[return-value]
        return self.reference_terrain_elevation, self.reference_location, SOURCE_ORIGIN_CORNER  # type: ignore[return-value]

    def _reference_for(self, st: Optional[_UAVState], wanted: Optional[set] = None):
        if st is not None and st.home_terrain is not None and st.home is not None:
            return st.home_terrain, st.home, SOURCE_UAV_HOME
        return self._swarm_reference(wanted)

    def take_origin_change(self) -> bool:
        """True (once) if a UAV's home changed, which may have moved the
        Origin-level reference; the caller then also publishes `origin_payload()`."""
        dirty, self._origin_dirty = self._origin_dirty, False
        return dirty

    # -- payloads ---------------------------------------------------------------

    def _payload(
        self,
        uav_id: Optional[str],
        phase: FlightPhase,
        takeoff_alt: Optional[float],
        current_agl: Optional[float],
        flying_agl: Optional[float],
        reference: Tuple[float, Tuple[float, float], str],
        commanded_alt: Optional[float] = None,
    ) -> Dict[str, Any]:
        reference_terrain, reference_location, reference_source = reference
        altitude, source = select_safety_altitude(
            phase, takeoff_alt, flying_agl, commanded_alt
        )
        return {
            "type": EVENT_TYPE,
            "status": "ready",
            "uavId": uav_id,
            "originFingerprint": self.origin_fingerprint,
            # Home the reference terrain elevation was read at, and what kind of home it is
            "referenceLocation": {"lat": reference_location[0], "lon": reference_location[1]},
            "referenceSource": reference_source,
            "referenceTerrainElevation": reference_terrain,
            # Three separate things: what was commanded, what the UAV reports,
            # and the altitude the threshold is actually built from.
            "takeoffAltitude": takeoff_alt,
            "currentAltitudeAGL": current_agl,
            "safetyAltitude": altitude,
            "safetyMargin": self.safety_margin,
            "safetyThresholdAMSL": compute_threshold(
                reference_terrain, altitude, self.safety_margin
            ),
            "altitudeSource": source,
            "flightPhase": phase.value,
        }

    def origin_payload(self, uav_ids: Optional[Iterable[str]] = None) -> Optional[Dict[str, Any]]:
        """The threshold for the Origin itself (uavId None): the initial 50 m
        until a Takeoff command exists, then the commanded altitude. Available
        as soon as the grid is, with no UAV involved; its home terrain is the
        lowest known UAV home (`uav_ids` limits it to connected UAVs), or the
        corner of the Origin area while no UAV position is known."""
        if not self.active:
            return None
        commanded = self.commanded_takeoff_altitude
        phase = FlightPhase.PRE_TAKEOFF if commanded is None else FlightPhase.CLIMBING
        wanted = set(uav_ids) if uav_ids is not None else None
        return self._payload(None, phase, commanded, None, None, self._swarm_reference(wanted))

    def uav_payload(self, uav_id: str) -> Optional[Dict[str, Any]]:
        st = self._uavs.get(uav_id)
        if not self.active or st is None:
            return None
        # Stage 3 reports the AHL the threshold was built from, so the two
        # numbers in one message always agree.
        reported = st.calc_agl if st.reached and _is_number(st.calc_agl) else st.current_agl
        return self._payload(
            uav_id,
            st.phase,
            st.takeoff_alt,
            reported,
            st.calc_agl,
            self._reference_for(st),
            st.commanded_alt,
        )

    def effective_payload(self, uav_ids: Optional[Iterable[str]] = None) -> Optional[Dict[str, Any]]:
        """The single threshold that terrain checks (Step 4) work against.

        The lowest threshold among the UAVs that have been commanded to take off
        or are flying -- the lowest one flags the most terrain, so it covers
        every other UAV too. With no such UAV (nothing commanded yet) it is the
        Origin-level payload. `uav_ids` limits the UAVs considered to those
        still connected.
        """
        if not self.active:
            return None
        wanted = set(uav_ids) if uav_ids is not None else None
        candidates = [
            self.uav_payload(uav_id)
            for uav_id, st in self._uavs.items()
            if st.phase is not FlightPhase.PRE_TAKEOFF and (wanted is None or uav_id in wanted)
        ]
        candidates = [p for p in candidates if p is not None]
        if candidates:
            return min(candidates, key=lambda p: p["safetyThresholdAMSL"])
        return self.origin_payload(wanted)

    def snapshot(self, uav_ids: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        """Origin-level payload followed by one per known UAV (optionally only
        those in `uav_ids`)."""
        wanted = set(uav_ids) if uav_ids is not None else None
        out = [self.origin_payload(wanted)]
        for uav_id in self._uavs:
            if wanted is None or uav_id in wanted:
                out.append(self.uav_payload(uav_id))
        return [p for p in out if p is not None]

    # -- events -----------------------------------------------------------------

    def command_takeoff(
        self,
        altitude: Any,
        uav_ids: Iterable[str],
        current_agls: Optional[Dict[str, Any]] = None,
        positions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """The operator pressed Takeoff: `altitude` becomes the safety altitude
        of the given UAVs immediately -- whatever their AHL currently is. A new
        command always starts the climb stage over. Returns the payloads to
        send now ([] if the altitude is invalid or no Origin terrain is active
        yet; the command is remembered either way)."""
        if not _is_number(altitude) or altitude <= 0:
            return []
        altitude = float(altitude)
        self.commanded_takeoff_altitude = altitude
        ids = [str(i) for i in uav_ids]
        for uav_id in ids:
            st = self._uavs.setdefault(uav_id, _UAVState())
            if positions and st.home is None and self._latch_home(st, positions.get(uav_id)):
                self._origin_dirty = True
            st.takeoff_alt = altitude  # from here on the home is frozen (phase is no longer pre-takeoff)
            st.reached = False
            st.calc_agl = None
            st.climb_peak, st.climb_stall = None, 0  # a new command starts a new climb
            st.commanded_alt = None  # a new Takeoff supersedes a pending level-off
            if current_agls and _is_number(current_agls.get(uav_id)):
                st.current_agl = float(current_agls[uav_id])
        return self.snapshot(ids)

    def command_altitude(
        self, altitude: Any, uav_ids: Iterable[str]
    ) -> List[Dict[str, Any]]:
        """The operator commanded one shared level-off altitude for UAVs already
        in the air (the "same" command). Unlike `command_takeoff` this does NOT
        restart the climb stage or re-freeze the home: the UAVs stay in whatever
        stage they are in, and the altitude only takes effect where it is LOWER
        than the UAV's actual AHL (see `select_safety_altitude`).

        Only safe for a command whose altitude is ONE scalar shared by every
        targeted UAV. The per-UAV "different" ladder must not be routed here: the
        server computes its steps as `alt + i*alt_diff` over the selection, while
        the swarm computer flies `alt + step*bot_index` over `pos_array`, so the
        value here would not be the one being flown. Those UAVs are covered by
        telemetry instead, once they reach their new altitude.

        Returns the payloads to send now ([] if the altitude is invalid or no
        Origin terrain is active yet).
        """
        if not _is_number(altitude) or altitude <= 0:
            return []
        altitude = float(altitude)
        ids = [str(i) for i in uav_ids]
        for uav_id in ids:
            self._uavs.setdefault(uav_id, _UAVState()).commanded_alt = altitude
        return self.snapshot(ids)

    def update_uav(
        self,
        uav_id: str,
        ahl: Any,
        armed: Optional[bool] = None,
        airborne: Optional[bool] = None,
        position: Optional[Tuple[float, float]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Feeds one telemetry observation (AHL; `armed` / `airborne` when the
        autopilot's heartbeat says; `position` = (lat, lon)). Returns the new
        payload if the threshold changed -- first sighting, reaching the takeoff
        altitude, landing, a new home, or an in-flight AHL change of at least
        ALTITUDE_RECALC_THRESHOLD -- else None.

        While the UAV is still before its Takeoff command (and not seen flying),
        its position is its home: the terrain elevation there is the reference of
        its threshold. The home is fixed from the Takeoff command on.

        While climbing, AHL is only compared with the commanded altitude; it
        never changes the safety altitude.
        """
        ahl = float(ahl) if _is_number(ahl) else None
        st = self._uavs.get(uav_id)
        changed = st is None
        if st is None:
            st = self._uavs[uav_id] = _UAVState()
        st.current_agl = ahl

        # A commanded level-off only matters while the UAV is still ABOVE it.
        # Once it has descended to (or below) that altitude the command has been
        # achieved and telemetry governs again -- otherwise a stale value would
        # keep clamping the threshold after a later, higher command.
        if (
            st.commanded_alt is not None
            and ahl is not None
            and ahl <= st.commanded_alt + _EPSILON
        ):
            st.commanded_alt = None
            changed = True

        if st.phase is FlightPhase.PRE_TAKEOFF and not airborne and self._latch_home(st, position):
            changed = True
            self._origin_dirty = True

        if st.reached:
            if armed is False:
                # Landed: back to "no Takeoff command" (the command was consumed),
                # and the place it landed on will be its next home.
                st.takeoff_alt, st.reached, st.calc_agl = None, False, None
                st.home = st.home_terrain = None
                st.climb_peak, st.climb_stall = None, 0
                st.commanded_alt = None
                self._origin_dirty = True
                self._refresh_commanded_altitude()
                changed = True
            elif needs_recalculation(st.calc_agl, ahl):
                st.calc_agl = ahl
                changed = True
        elif st.takeoff_alt is not None:
            if ahl is not None and ahl >= st.takeoff_alt - TAKEOFF_REACHED_TOLERANCE_M - _EPSILON:
                st.reached, st.calc_agl = True, ahl
                st.climb_peak, st.climb_stall = None, 0
                changed = True
            elif ahl is not None and self._climb_stalled(st, ahl, airborne):
                # Levelled off below the commanded altitude: stop reporting the
                # commanded value (which is now higher than the UAV actually is)
                # and switch to its real AHL, as if the altitude had been reached.
                st.reached, st.calc_agl = True, ahl
                st.climb_peak, st.climb_stall = None, 0
                changed = True
        elif airborne and ahl is not None:
            # Seen flying with no Takeoff command on record (launched some other
            # way, or the server restarted mid-flight): the 50 m default would
            # be wrong for a UAV that is already up there, so use telemetry.
            st.reached, st.calc_agl = True, ahl
            changed = True

        return self.uav_payload(uav_id) if changed else None

    def _climb_stalled(
        self, st: _UAVState, ahl: float, airborne: Optional[bool]
    ) -> bool:
        """Whether this UAV has stopped climbing short of its commanded altitude.

        Any gain of at least CLIMB_PROGRESS_EPSILON_M on the highest AHL seen so
        far counts as progress and resets the counter, so a real climb -- however
        slow or uneven -- never trips this. Returns True only once the counter
        reaches CLIMB_STALL_UPDATES.
        """
        # A UAV still on the ground has a flat AHL too; that is not a stalled
        # climb, and must keep reporting the commanded altitude.
        if not (airborne if airborne is not None else ahl >= MIN_AIRBORNE_AHL_M):
            st.climb_peak, st.climb_stall = None, 0
            return False

        if st.climb_peak is None or ahl >= st.climb_peak + CLIMB_PROGRESS_EPSILON_M:
            st.climb_peak = max(ahl, st.climb_peak if st.climb_peak is not None else ahl)
            st.climb_stall = 0
            return False

        st.climb_stall += 1
        return st.climb_stall >= CLIMB_STALL_UPDATES

    def _refresh_commanded_altitude(self) -> None:
        if not any(s.takeoff_alt is not None for s in self._uavs.values()):
            self.commanded_takeoff_altitude = None


# One active Origin at a time -- same single-value pattern as `origin` in
# swarm.py and `_terrain_grid_cache` in ext/terrain.py.
tracker = TerrainSafetyTracker()


# --- telemetry access -----------------------------------------------------------

_mavlink_enums: Any = None


def _load_mavlink_enums():
    global _mavlink_enums
    if _mavlink_enums is None:
        try:
            from flockwave.server.ext.mavlink import enums

            _mavlink_enums = enums
        except Exception:  # no MAVLink extension -> just no heartbeat information
            _mavlink_enums = False
    return _mavlink_enums or None


def read_uav_telemetry(uav: Any) -> Optional[Tuple[Optional[float], Optional[bool], Optional[bool]]]:
    """(AHL, armed, airborne) for a UAV; None if it has no position at all.

    AHL is ``uav.status.position.ahl`` -- GLOBAL_POSITION_INT.relative_alt, the
    height above home. (The MAVLink driver never fills ``position.agl``.)

    `armed` / `airborne` come from the heartbeat the MAVLink driver already
    keeps (None when there is none): airborne = armed and MAV_STATE in
    ACTIVE / CRITICAL / EMERGENCY. They are used only to notice a landing and
    a UAV that is already flying without any Takeoff command on record --
    never to decide the takeoff stage.
    """
    position = getattr(getattr(uav, "status", None), "position", None)
    if position is None:
        return None
    ahl = getattr(position, "ahl", None)

    armed = airborne = None
    enums = _load_mavlink_enums()
    get_last_message = getattr(uav, "get_last_message", None)
    if enums is not None and get_last_message is not None:
        heartbeat = get_last_message(enums.MAVMessageType.HEARTBEAT)
        if heartbeat is not None:
            armed = bool(heartbeat.base_mode & enums.MAVModeFlag.SAFETY_ARMED)
            airborne = armed and heartbeat.system_status in (
                enums.MAVState.ACTIVE,
                enums.MAVState.CRITICAL,
                enums.MAVState.EMERGENCY,
            )
    return ahl, armed, airborne


def read_uav_position(uav: Any) -> Optional[Tuple[float, float]]:
    """(lat, lon) of a UAV, or None without a usable GPS position."""
    position = getattr(getattr(uav, "status", None), "position", None)
    here = (getattr(position, "lat", None), getattr(position, "lon", None))
    return (float(here[0]), float(here[1])) if _valid_position(here) else None  # type: ignore[arg-type]


# --- app hooks --------------------------------------------------------------------


# Called after every published batch of threshold payloads -- the one place a
# Step 3 threshold change becomes visible -- so later steps (Step 4A: unsafe
# terrain) can react to it without a polling loop of their own.
_threshold_listeners: List[Callable[[Any], Awaitable[None]]] = []


def add_threshold_listener(listener: Callable[[Any], Awaitable[None]]) -> None:
    if listener not in _threshold_listeners:
        _threshold_listeners.append(listener)


async def publish_payloads(app: Any, payloads: Iterable[Dict[str, Any]]) -> None:
    hub = app.message_hub
    for payload in payloads:
        await hub.broadcast_message(hub.create_notification(dict(payload)))
    for listener in list(_threshold_listeners):
        try:
            await listener(app)
        except Exception:
            _log_hook_failure(app, f"threshold listener {getattr(listener, '__name__', listener)}")


def on_uav_status_updated(app: Any, uav_ids: Iterable[str]) -> None:
    """Called for every UAV telemetry update (from
    ``App.request_to_send_UAV_INF_message_for``), so it is on the hot path: it
    returns at once while nothing needs tracking and otherwise only compares
    numbers. A message goes out only when a threshold actually changed. Never
    raises: terrain safety must not be able to disturb telemetry handling.
    """
    if not tracker.wants_telemetry:
        return
    try:
        payloads = []
        for uav_id in uav_ids:
            uav = app.find_uav_by_id(uav_id)
            telemetry = read_uav_telemetry(uav) if uav is not None else None
            if telemetry is None:
                continue
            payload = tracker.update_uav(str(uav_id), *telemetry, position=read_uav_position(uav))
            if payload is not None:
                payloads.append(payload)
        if payloads and tracker.take_origin_change():
            # a UAV's home changed: the Origin-level threshold (lowest home) may have too
            origin_level = tracker.origin_payload()
            if origin_level is not None:
                payloads.insert(0, origin_level)
        if payloads:
            app.run_in_background(publish_payloads, app, payloads)
    except Exception:
        _log_hook_failure(app, "telemetry update")


def on_takeoff_commanded(app: Any, altitude: Any, uav_ids: Iterable[str]) -> None:
    """Called the moment ``X-UAV-TAKEOFF`` is received (with its ``alt``), before
    the UAV has moved. Updates the safety altitude and schedules the new
    threshold for broadcast right away. Empty `uav_ids` means every UAV. Never
    raises: a fault here must not get in the way of the takeoff itself.
    """
    try:
        ids = [str(i) for i in uav_ids]
        agls = {}
        positions = {}
        if not ids:
            from flockwave.server.model.uav import UAV

            ids = [str(i) for i in app.object_registry.ids_by_type(UAV)]
        for uav_id in ids:
            uav = app.find_uav_by_id(uav_id)
            telemetry = read_uav_telemetry(uav) if uav is not None else None
            if telemetry is not None:
                agls[uav_id] = telemetry[0]
            positions[uav_id] = read_uav_position(uav) if uav is not None else None
        payloads = tracker.command_takeoff(altitude, ids, agls, positions)
        if payloads:
            app.run_in_background(publish_payloads, app, payloads)
    except Exception:
        _log_hook_failure(app, "takeoff command")


def on_altitude_commanded(app: Any, altitude: Any, uav_ids: Iterable[str]) -> None:
    """Called when the operator commands ONE shared altitude for UAVs already in
    the air (the ``same`` command). Empty `uav_ids` means every UAV, which is what
    ``same`` does. Never raises: a fault here must not get in the way of the
    altitude change itself.

    Deliberately NOT wired to the ``different`` ladder -- see
    `TerrainSafetyTracker.command_altitude` for why the server cannot know those
    per-UAV altitudes correctly.
    """
    try:
        ids = [str(i) for i in uav_ids]
        if not ids:
            from flockwave.server.model.uav import UAV

            ids = [str(i) for i in app.object_registry.ids_by_type(UAV)]
        payloads = tracker.command_altitude(altitude, ids)
        if payloads:
            app.run_in_background(publish_payloads, app, payloads)
    except Exception:
        _log_hook_failure(app, "altitude command")


def _log_hook_failure(app: Any, what: str) -> None:
    import logging

    logging.getLogger(__name__).exception("terrain safety: %s handling failed", what)
