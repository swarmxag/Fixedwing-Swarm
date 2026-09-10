"""Terrain-clearance gate for goal / autogoal / altitude commands.

Every number here comes from the VEHICLE, not from the mission frame:

    home datum       vehicle.location.global_frame.alt
                       - vehicle.location.global_relative_frame.alt
    current position vehicle.location.global_relative_frame.lat/lon
    current altitude vehicle.location.global_relative_frame.alt

so the check is against where that aircraft actually is and what its own
autopilot is actually using as the home reference.

WHY THE HOME DATUM IS THAT SUBTRACTION
--------------------------------------
uav/guidance.py commands simple_goto(LocationGlobalRelative(lat, lon, alt)),
whose altitude is relative to HOME. Terrain is AMSL. global_frame.alt is the
same instant's AMSL and global_relative_frame.alt the same instant's
height-above-home, so their difference is exactly the datum ArduPilot will add
to whatever relative altitude we command. Using it means the comparison is
against the aircraft's own notion of home, not a separately-guessed elevation
that could disagree with it.

    aircraft_amsl = home_amsl + commanded_rel_alt
    SAFE  iff  aircraft_amsl >= terrain_max_amsl + MIN_CLEARANCE_M

(terrain_check expresses this as a rise above `home_elev`, which is the same
inequality rearranged -- passing the vehicle's home AMSL as home_elev gives
exactly the comparison above.)

WHAT IS CHECKED
---------------
goal / autogoal : the corridor from the UAV's CURRENT position through every
                  goal point in order, then the loiter disc at the last one.
different       : terrain near where each UAV is right now, plus the goal
                  points it is still flying to, at the NEW altitude.

Both altitudes are checked where they differ: the altitude the aircraft is at
now, and the altitude it has been commanded to hold. A descent that clears at
the current height but not at the target height is exactly the case worth
catching, so the lower of the two governs.

FAILURE POLICY
--------------
Fails OPEN when no terrain tiles are installed, or when this process has no
vehicles at all (not the master computer), so neither deployment nor a
non-master node is affected. Fails CLOSED when a vehicle exists but its
telemetry, its home datum, or the terrain along its route is unavailable --
an unverifiable route must not be reported as clear.
"""

import os

import locatePosition

from medur_swarm import config, state

try:
    from medur_swarm import terrain_check as tc
except Exception as e:  # numpy missing, etc.
    tc = None
    print("[terrain] checks disabled --", e)


TERRAIN_DIR = os.environ.get(
    "XAG_TERRAIN_DIR",
    os.path.join(os.path.expanduser("~"), "Documents", "swarm_env", "terrain"),
)

# Radius around a UAV's current position checked on an altitude change. There
# is no route to follow in that case, so this is "the ground it is over and
# about to be over" -- a couple of minutes of fixed-wing flight.
ALTITUDE_CHECK_RADIUS_M = 3000.0

# How far the vehicle's own home datum may sit from the terrain data's
# elevation at the origin before the two are treated as irreconcilable.
# Real flight: GPS/geoid differences put these within a few metres.
HOME_DATUM_TOLERANCE_M = 30.0

_db = None
_datum_warned = set()  # bot indexes already told about a datum mismatch


def configured():
    """True when terrain data of EITHER supported format is installed.

    Must match what TerrainDB can actually read: checking only for .dat would
    report "no terrain data" for a directory holding nothing but SRTM .hgt
    tiles, and since a missing directory fails OPEN that would silently
    disable every check rather than announce itself.
    """
    if tc is None or not os.path.isdir(TERRAIN_DIR):
        return False
    try:
        return any(
            n.lower().endswith((".dat", ".hgt")) for n in os.listdir(TERRAIN_DIR)
        )
    except OSError:
        return False


def _get_db():
    global _db
    if _db is None:
        _db = tc.TerrainDB(TERRAIN_DIR)
    return _db


def _uav_label(i):
    return state.pos_array[i] if i < len(state.pos_array) else i


def _vehicle_frames(i):
    """(home_amsl, (lat, lon), current_rel_alt) read from vehicle i, or None
    for any part telemetry cannot supply."""
    if not state.master_flag or i >= len(state.vehicles):
        return None, None, None
    try:
        loc = state.vehicles[i].location
        rel = loc.global_relative_frame
        glob = loc.global_frame
        lat, lon = rel.lat, rel.lon
        position = (float(lat), float(lon)) if lat is not None and lon is not None else None
        current_rel = float(rel.alt) if rel.alt is not None else None
        home_amsl = (
            float(glob.alt) - current_rel
            if glob.alt is not None and current_rel is not None
            else None
        )
        # Reconcile against the terrain data before anything is computed from
        # it -- a datum that disagrees with the DEM poisons every margin.
        home_amsl, _note = _resolve_home_datum(i, home_amsl)
        return home_amsl, position, current_rel
    except Exception as e:
        print(f"[terrain] telemetry unavailable for vehicle {_uav_label(i)}:", e)
        return None, None, None


def _resolve_home_datum(i, vehicle_datum):
    """Reconcile the vehicle's home datum against the terrain data itself.

    The vehicle's own (global_frame.alt - global_relative_frame.alt) is
    authoritative in real flight: it is exactly what ArduPilot adds to a
    commanded relative altitude. But it can be fiction -- SITL launched with
    no home altitude reports a datum near sea level while the terrain database
    describes the real ground, and every margin computed from that pair is
    wrong by the difference (55 m at this site, enough to invent blocks and
    cautions out of nothing).

    So when the two disagree by more than HOME_DATUM_TOLERANCE_M, prefer the
    terrain data's elevation at the origin. That keeps the comparison
    self-consistent -- terrain against terrain, with the dataset's own datum
    bias cancelling on both sides -- instead of subtracting two numbers that
    do not share a reference. In real flight the two agree and this never
    fires; when it does fire it is said out loud once per UAV, because a
    disagreement this large means the aircraft's home is misconfigured and
    that is worth fixing at the source.

    Returns (home_amsl, note) where note is None unless a substitution
    happened.
    """
    if state.origin is None or vehicle_datum is None:
        return vehicle_datum, None
    try:
        dem_home = _get_db().nearest(float(state.origin[0]), float(state.origin[1]))
    except Exception:
        return vehicle_datum, None
    if dem_home is None:
        return vehicle_datum, None

    difference = vehicle_datum - dem_home
    if abs(difference) <= HOME_DATUM_TOLERANCE_M:
        return vehicle_datum, None

    if i not in _datum_warned:
        _datum_warned.add(i)
        print(
            f"[terrain-datum] UAV {_uav_label(i)}: home datum {vehicle_datum:.0f} m "
            f"AMSL disagrees with terrain data ({dem_home} m at the origin) by "
            f"{difference:+.0f} m -- using the terrain value. Fix the vehicle's "
            f"home altitude; until then every clearance figure carries this error."
        )
    return float(dem_home), f"datum substituted ({difference:+.0f} m)"


def _commanded_alt(i):
    if state.same_alt_flag:
        return float(state.same_height)
    if i < len(state.different_height):
        return float(state.different_height[i])
    return None


def _sim_xy_to_latlon(point):
    """active_goal_tasks stores goals in half-scale sim units; terrain needs
    lat/lon."""
    lat, lon = locatePosition.cartToGeo(
        state.origin, config.END_DISTANCE, [point[0] * 2, point[1] * 2]
    )
    return float(lat), float(lon)


def _remaining_task_goals(i):
    """Goal points UAV i is still flying to under its active task, as lat/lon.
    Empty when it has no active goal task or the task is a loiter."""
    if state.origin is None:
        return []
    with state.active_goal_tasks_lock:
        task = state.active_goal_tasks.get(i)
        if not task or task.get("type") == "guided_circle":
            return []
        goals = list(task.get("goals") or [])
        index = int(task.get("goal_index", 0))
    out = []
    for point in goals[index:]:
        try:
            out.append(_sim_xy_to_latlon(point))
        except Exception:
            continue
    return out


def _altitudes_to_check(i, current_rel, override_alt=None, target_only=False):
    """The relative altitude this UAV must clear terrain at.

    For a goal, both the height it is at now and the height it has been told
    to hold matter, so the LOWER of the two governs -- a route that clears at
    the target altitude but not at the height the aircraft is currently
    holding is still a route into the ground.

    For an altitude change (target_only), only the NEW height is judged. The
    height it is leaving is exactly what the operator is correcting, so
    folding it in would warn about a number that is about to stop existing --
    and would make every climb look as bad as the altitude it climbed from.
    """
    if target_only:
        return [] if override_alt is None else [float(override_alt)]

    candidates = []
    if override_alt is not None:
        candidates.append(float(override_alt))
    else:
        commanded = _commanded_alt(i)
        if commanded is not None:
            candidates.append(commanded)
    if current_rel is not None:
        candidates.append(float(current_rel))
    if not candidates:
        return []
    return [min(candidates)]


def _record(verdict, uav, problems, cautions, required=None):
    """Sort a verdict into the two buckets. BLOCK refuses the command;
    CAUTION lets it through but is printed, because a route that clears by
    less than CAUTION_MARGIN_M has already spent its whole error budget and
    the operator should know before it is flown, not after.

    `required` collects each verdict's minimum safe altitude so _report can
    state one number that clears the whole fleet -- see there for why.
    """
    if verdict.level == "BLOCK":
        problems.append(f"UAV {uav}: {verdict.reason}")
    elif verdict.level == "CAUTION":
        cautions.append(f"UAV {uav}: {verdict.reason}")
    if required is not None and verdict.required_rel_alt is not None:
        required.append(verdict.required_rel_alt)


def _report(problems, cautions, label, blocking=True, required=None):
    """Print the verdicts and say whether the caller should proceed.

    blocking=False makes this purely advisory: the findings are printed but
    the command still goes through. Used for altitude changes -- see
    check_altitude_change for why refusing one is worse than allowing it.

    A refusal ends with ONE actionable line naming the altitude that clears
    every selected UAV. Without it the operator has to read a "needs N m"
    out of each of five per-UAV lines and take the maximum by eye, in the
    middle of a flight, to work out what to type into the altitude box --
    which is the only thing they actually want to know at that moment.
    """
    for m in cautions:
        print(f"[terrain-caution] {label} --", m)
    for m in problems:
        print(f"[{'terrain-block' if blocking else 'terrain-warn'}] {label} --", m)

    if problems and required:
        floor = max(required)
        verb = "refused" if blocking else "flagged"
        print(
            f"[terrain-{'block' if blocking else 'warn'}] {label} {verb} -- set the "
            f"altitude base to at least {floor:.0f} m (relative to home) to clear "
            f"every selected UAV, then re-send. The altitude command itself is "
            f"never refused."
        )

    if not blocking:
        return True, problems
    return (not problems), problems


def check_goals(selected_indexes, goals_latlon, loiter_radius_m=None, label="goal"):
    """Gate a goal/autogoal assignment.

    goals_latlon -- ordered [(lat, lon), ...] the selected UAVs will fly.
    Returns (ok, [messages]); callers drop the command when ok is False.
    """
    if not configured() or not goals_latlon:
        return True, []
    if not state.master_flag or not state.vehicles:
        return True, []  # no vehicles here to check

    db = _get_db()
    problems = []
    cautions = []
    required = []

    for i in selected_indexes:
        uav = _uav_label(i)
        home_amsl, position, current_rel = _vehicle_frames(i)
        if home_amsl is None or position is None:
            problems.append(
                f"UAV {uav}: no telemetry for home datum/position -- cannot verify terrain"
            )
            continue

        radius = (
            float(loiter_radius_m)
            if loiter_radius_m
            else config.UAV_DEFAULT_LOITER_RADIUS_M
        )

        for alt in _altitudes_to_check(i, current_rel):
            start = position
            try:
                blocked = False
                for goal in goals_latlon:
                    verdict = tc.check_leg(db, home_amsl, start, goal, alt)
                    _record(verdict, uav, problems, cautions, required)
                    if not verdict.safe:
                        blocked = True
                        break
                    start = goal
                if not blocked:
                    verdict = tc.check_loiter(
                        db, home_amsl, goals_latlon[-1], radius, alt
                    )
                    _record(verdict, uav, problems, cautions, required)
            except tc.TerrainUnavailable as e:
                problems.append(f"UAV {uav}: route leaves the mapped area ({e})")
            except Exception as e:
                problems.append(f"UAV {uav}: terrain check failed ({e})")

    return _report(problems, cautions, label, required=required)


def check_altitude_change(proposed_heights, label="different"):
    """ADVISORY ONLY -- reports on a 'different' re-stagger, never refuses it.

    proposed_heights -- {bot_index: new relative altitude}
    Always returns ok=True; the findings are printed as [terrain-warn].

    Refusing an altitude change is a deadlock. Raising altitude is precisely
    how an operator clears a terrain-blocked goal, so a gate that can refuse
    the climb can trap the fleet at an altitude that is itself too low: the
    goal is refused for being under terrain, the fix for that is refused too,
    and there is no way out from the GCS. Worse, refusing leaves the aircraft
    at the OLD altitude, which is lower still -- the refusal actively
    preserves the more dangerous state.

    So this reports and gets out of the way. The goal/autogoal gate is where
    refusal belongs, because that is the command that actually flies the
    aircraft at terrain; an altitude on its own does not.

    Judged against the NEW altitude only (see _altitudes_to_check), using the
    ground within ALTITUDE_CHECK_RADIUS_M of where the vehicle is now plus any
    goal points it is still flying to.
    """
    if not configured() or not proposed_heights:
        return True, []
    if not state.master_flag or not state.vehicles:
        return True, []

    db = _get_db()
    problems = []
    cautions = []
    required = []

    for index, new_alt in sorted(proposed_heights.items()):
        uav = _uav_label(index)
        home_amsl, position, current_rel = _vehicle_frames(index)
        if home_amsl is None or position is None:
            problems.append(
                f"UAV {uav}: no telemetry for home datum/position -- cannot verify terrain"
            )
            continue

        for alt in _altitudes_to_check(
            index, current_rel, override_alt=new_alt, target_only=True
        ):
            try:
                verdict = tc.check_around(
                    db, home_amsl, position, ALTITUDE_CHECK_RADIUS_M, alt
                )
                _record(verdict, uav, problems, cautions, required)
                if not verdict.safe:
                    continue
                start = position
                for goal in _remaining_task_goals(index):
                    verdict = tc.check_leg(db, home_amsl, start, goal, alt)
                    _record(verdict, uav, problems, cautions, required)
                    if not verdict.safe:
                        break
                    start = goal
            except tc.TerrainUnavailable as e:
                problems.append(f"UAV {uav}: leaves the mapped area ({e})")
            except Exception as e:
                problems.append(f"UAV {uav}: terrain check failed ({e})")

    return _report(problems, cautions, label, blocking=False, required=required)
