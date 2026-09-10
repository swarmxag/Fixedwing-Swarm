"""Turning a bot's simulated position into a real fixed-wing GUIDED target:
virtual-leader pacing bounded by real UAV lead distance, forward look-ahead
along a Bezier curve or straight leg so the aircraft always has a line to
track, and the bot-reaches-waypoint/real-UAV-confirms-final-point handoff
rule that replaced the original "freeze until the real UAV arrives" design
(which a wide-turning fixed-wing could never satisfy).
"""

import math
import time

from dronekit import LocationGlobalRelative

import locatePosition
from swarm_tasks.modules.dispersion import disp_field
from swarm_tasks.tasks import area_coverage as cvg

from medur_swarm import config, state
from medur_swarm.utils import read_specific_line
from medur_swarm.uav.telemetry import (
    live_gps_plot_points,
    print_sim_vs_real_latlon_with_bot,
    uav_distance_to_goal,
)


def lookahead_point(x, y, theta, distance=10):
    lx = x + distance * math.cos(theta)
    ly = y + distance * math.sin(theta)
    return (lx, ly)


def compute_lookahead_target(x, y, theta, rx, ry, distance, min_lead=None):
    """The point handed to the real vehicle: a fixed point on the bot's
    heading line, `distance` ahead of the bot, that the vehicle closes on
    -- never a point that runs away from it, and never one that falls
    behind it. Canonical pursuit-point guidance, shared by goal, search,
    and split (via tasks/runner.py and each mission module).

    x, y, theta -- bot pose (sim frame)
    rx, ry      -- vehicle's live position (sim frame, same units as x, y)
    distance    -- lookahead distance ahead of the BOT, sim units
    min_lead    -- once the vehicle has passed the bot-anchored target,
                   how far ahead of the vehicle to keep it instead.
                   Defaults to half distance.

    along is the vehicle's signed progress along the bot's heading: >0
    means it has already passed the bot going that way. Anchoring the
    target to that progress (target_along = along + distance) is what
    misbehaves once the vehicle gets ahead -- the target then advances by
    exactly as much as the vehicle does, so the vehicle chases a carrot it
    can never reach and keeps building lead on the bot. Behind, the same
    formula is self-stabilising (the gap grows, giving a far target and a
    gentle straight-line pursuit), which is why only the "ahead" case
    shows the problem.

    So along is used here purely as a floor, not as the anchor: the
    target normally sits at a FIXED distance ahead of the bot, so a
    vehicle that is ahead actually closes on it and bleeds off its lead.
    Only when the vehicle has genuinely overflown that point does the
    target get pushed out, and then just by min_lead -- far enough to
    avoid commanding a reversal a fixed-wing can't fly.
    """
    if min_lead is None:
        min_lead = distance * 0.5

    # Signed distance of vehicle along the bot's current heading
    along = (rx - x) * math.cos(theta) + (ry - y) * math.sin(theta)

    target_along = max(distance, along + min_lead)

    return lookahead_point(x, y, theta, target_along)


def real_uav_avoidance_vector(i):
    """Push UAV i's guidance target away from every OTHER connected UAV's
    live GPS position within UAV_COLLISION_AVOID_RADIUS_M metres.

    Computed entirely from real telemetry (live_gps_plot_points), never
    from the simulated bots' own positions -- so it keeps meaning even
    after a bot and its real aircraft have drifted apart, and it reacts
    to where every other aircraft in the fleet *actually* is, not where
    its own bot's dead-reckoned twin thinks it is. Meant to be added
    directly onto a guidance target that is already in sim-frame (x, y)
    units, e.g. the point compute_lookahead_target/curve_guidance_position
    produces, before it's converted back to lat/lon for simple_goto.

    Returns (0.0, 0.0) if this UAV (or any given neighbor) has no live GPS
    fix yet, or if nothing is within range.
    """
    positions = live_gps_plot_points()
    if i >= len(positions) or positions[i] is None:
        return (0.0, 0.0)
    my_x, my_y = positions[i]
    push_x = push_y = 0.0
    for j, pos in enumerate(positions):
        if j == i or pos is None:
            continue
        dx = my_x - pos[0]
        dy = my_y - pos[1]
        dist_m = 2.0 * math.hypot(dx, dy)  # sim units are half-scale
        if dist_m <= 0 or dist_m >= config.UAV_COLLISION_AVOID_RADIUS_M:
            continue
        # Linear falloff: full push at zero separation, none at the radius.
        weight = (
            config.UAV_COLLISION_AVOID_RADIUS_M - dist_m
        ) / config.UAV_COLLISION_AVOID_RADIUS_M
        norm = math.hypot(dx, dy) or 1.0
        push_x += (dx / norm) * weight
        push_y += (dy / norm) * weight
    return (
        push_x * config.UAV_COLLISION_AVOID_GAIN,
        push_y * config.UAV_COLLISION_AVOID_GAIN,
    )


def pursuit_target_with_avoidance(i, b, distance=700):
    """Convenience wrapper combining compute_lookahead_target and
    real_uav_avoidance_vector: the pursuit point ahead of the bot's own
    heading (see compute_lookahead_target), corrected by every other real
    UAV's live separation (see real_uav_avoidance_vector). Returns a
    sim-frame (x, y) suitable to pass straight into
    _drive_vehicle_towards(i, b, guidance_position=...).

    Returns None (the caller then falls back to the bot's raw position)
    if this UAV has no live GPS fix to pursuit-anchor against.
    """
    if not state.master_flag or i >= len(state.vehicles):
        return None
    try:
        lat_v = state.vehicles[i].location.global_relative_frame.lat
        lon_v = state.vehicles[i].location.global_relative_frame.lon
        if lat_v is None or lon_v is None:
            return None
        rx, ry = locatePosition.geoToCart(
            state.origin, config.END_DISTANCE, [lat_v, lon_v]
        )
    except Exception as e:
        print("[pursuit-target] telemetry unavailable for vehicle", i, e)
        return None
    tx, ty = compute_lookahead_target(
        b.x, b.y, b.theta, rx / 2, ry / 2, distance=distance
    )
    # avoid_x, avoid_y = real_uav_avoidance_vector(i)
    return (tx, ty)


def signed_uav_lead(i, b):
    """Signed distance (metres) of the real UAV along the bot's own
    heading: positive means the UAV is already AHEAD of the bot, negative
    means it's behind.

    _pacing_step_size only sees the undirected `dis` -- how far apart they
    are, not which one is ahead -- so it slows the bot down whenever
    separation is large, whether the UAV is behind (correct: let the bot
    ease off so the aircraft can catch up) or ahead (wrong: slowing the
    bot down here just freezes its own CSV/waypoint progress while the
    real aircraft has already flown past, instead of letting the bot keep
    moving so the mission actually advances). This is what lets
    advance_bot_with_uav_pacing tell the two cases apart.

    Returns None if there's no live telemetry to compute it from --
    callers fall back to the undirected ramp in that case, exactly as
    before this existed.
    """
    if not state.master_flag or i >= len(state.vehicles):
        return None
    try:
        lat = state.vehicles[i].location.global_relative_frame.lat
        lon = state.vehicles[i].location.global_relative_frame.lon
        if lat is None or lon is None:
            return None
        rx, ry = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
    except Exception as e:
        print("[pacing] telemetry unavailable for vehicle", i, e)
        return None
    rx, ry = rx / 2, ry / 2  # sim units are half-scale
    # Project the UAV's sim-frame offset from the bot onto the bot's own
    # heading vector (cos theta, sin theta) -- this is the same signed
    # "along-heading" projection compute_lookahead_target uses, just
    # anchored on the bot instead of the lookahead target. >0 = UAV is
    # further along the bot's heading than the bot itself (ahead); <0 =
    # behind. Purely lateral separation (e.g. mid-turn) projects near zero
    # either way, which is what keeps a wide turn from being misread as lead.
    along_sim = (rx - b.x) * math.cos(b.theta) + (ry - b.y) * math.sin(b.theta)
    return 2.0 * along_sim  # sim units -> metres


def _pacing_step_size(dis):
    """Step size as a smooth ramp of UAV--bot separation, not a hard
    threshold. A single cutoff at UAV_FOLLOW_WINDOW_M chatters: ordinary
    noise in `dis` (GPS jitter, the bot's own speed feeding back into
    separation) straddling that one point flips step_size between
    UAV_MAX_VIRTUAL_STEP and UAV_MIN_VIRTUAL_STEP almost every tick --
    confirmed directly in flight logs. Ramping over UAV_FOLLOW_RAMP_M
    instead means a few metres of noise only nudges step_size by a
    proportional sliver, never a full swing.
    """
    # [lower, upper] is the ramp band, centred on UAV_FOLLOW_WINDOW_M and
    # UAV_FOLLOW_RAMP_M wide -- separation inside this band is what actually
    # interpolates; below/above it the step size is pinned to one extreme.
    half_ramp = config.UAV_FOLLOW_RAMP_M / 2
    lower = config.UAV_FOLLOW_WINDOW_M - half_ramp
    upper = config.UAV_FOLLOW_WINDOW_M + half_ramp
    if dis <= lower:
        return config.UAV_MAX_VIRTUAL_STEP  # normal: full pace, no lag
    if dis >= upper:
        return config.UAV_MIN_VIRTUAL_STEP  # over-lead: crawl, never freeze
    # Linear interpolation: t goes 0 -> 1 as dis crosses lower -> upper, so
    # step_size slides smoothly from the max pace down to the crawl floor
    # instead of snapping between the two (see docstring for why a snap
    # chatters in practice).
    t = (dis - lower) / (upper - lower)
    return config.UAV_MAX_VIRTUAL_STEP - t * (
        config.UAV_MAX_VIRTUAL_STEP - config.UAV_MIN_VIRTUAL_STEP
    )


def _groundspeed_step_size(i, b, cmd):
    """step_size that makes the bot cover exactly the ground the real
    aircraft covered since this bot's previous tick.

    bot.move() advances the bot by min(cmd.speed, bot.max_speed) * step_size
    sim units (utils/robot.py), so to travel `distance_sim` this tick:

        step_size = distance_sim / min(cmd.speed, bot.max_speed)

    with distance_sim = groundspeed * dt / 2 (metres -> half-scale sim units).

    The point is that the bot's speed becomes a physical quantity tied to the
    aircraft rather than a side effect of the runner loop's tick rate -- so
    the bot/UAV lead stays constant no matter how slow or fast the loop runs,
    which is what both the old distance brake (freezing) and its removal
    (overrun, aircraft loitering on a target the bot hadn't left yet) were
    failing to achieve.

    Returns None when it can't be computed -- no telemetry, no groundspeed,
    the bot's first tick (no dt yet), or a command with no magnitude to
    scale -- and the caller falls back to the fixed step.
    """
    if not config.GROUNDSPEED_PACING or not state.master_flag:
        return None
    if i >= len(state.vehicles):
        return None
    try:
        groundspeed = float(state.vehicles[i].groundspeed)
    except Exception as e:
        print("[pacing] groundspeed unavailable for vehicle", i, e)
        return None
    if groundspeed <= 0:
        return None

    now = time.monotonic()
    last = state.bot_step_last_time.get(i)
    state.bot_step_last_time[i] = now
    if last is None:
        return None  # first tick for this bot -- nothing to measure dt against
    dt = now - last
    if dt <= 0:
        return None
    # One stalled tick must not teleport the bot forward.
    dt = min(dt, config.BOT_STEP_MAX_DT_S)

    magnitude = min(cmd.speed, b.max_speed)
    if magnitude <= 1e-6:
        return None  # no field magnitude to scale; bot isn't going anywhere
    return (groundspeed * dt / 2.0) / magnitude


def advance_bot_with_uav_pacing(i, b, goal, label=""):
    """Advance the virtual leader at full pace, with a bounded lead.

    A large UAV--bot separation can be lateral (for example, while a
    fixed-wing UAV follows a 200 m turn), not evidence that the virtual bot
    is ahead, so separation must never be allowed to freeze the moving
    GUIDED target -- that reproduces the original loiter-on-arrival bug.
    But it also must not be unbounded: past UAV_FOLLOW_WINDOW_M the leader
    is consuming intermediate points faster than the aircraft can reach
    them, so it drops to a nonzero floor (UAV_MIN_VIRTUAL_STEP, never 0)
    until the aircraft closes back up. See _pacing_step_size for why this
    is a ramp rather than a single cutoff, and signed_uav_lead for why a
    large separation only slows the bot down when the UAV is BEHIND it --
    never when the UAV is already ahead.
    """
    # dis: undirected UAV<->bot separation in metres (sim-vs-real lat/lon
    # distance). signed_lead: same pair, but signed along the bot's own
    # heading -- >0 once the real UAV has actually passed the bot, <0 while
    # it's still behind. The two together are what let this function tell
    # "UAV lagging, ease the bot off" apart from "UAV already ahead, keep
    # the bot moving" even though both can produce a large `dis`.
    #
    # `dis` itself is still needed below (debug print + the return value,
    # which runner.py's mission lead-cap also reads), so it stays live.
    dis = print_sim_vs_real_latlon_with_bot(b, i, label=label)
    signed_lead = signed_uav_lead(i, b)

    before_x, before_y = b.x, b.y
    # goal_area_cvg is the bot's own steering command toward `goal`;
    # disp_field layers a separation force from nearby bots on top so two
    # bots converging on the same area don't collapse onto each other.
    # Built BEFORE step_size because groundspeed pacing scales against this
    # command's own magnitude (see _groundspeed_step_size).
    cmd = cvg.goal_area_cvg(i, b, goal)
    cmd += disp_field(b, neighbourhood_radius=100)

    # Bot advances at the real aircraft's ground speed, so the two stay
    # locked together regardless of how fast this loop happens to tick.
    # Falls back to the fixed full-pace step with no telemetry to derive it.
    step_size = _groundspeed_step_size(i, b, cmd)
    if step_size is None:
        step_size = config.UAV_MAX_VIRTUAL_STEP

    # --- UAV<->bot DISTANCE BRAKE, still disabled ---------------------
    # This slowed the bot down as a function of UAV<->bot separation, which
    # froze the bot (and so froze the GUIDED target) whenever the aircraft
    # lagged. Groundspeed pacing above addresses the same problem at its
    # source -- the lead can't run away if the bot moves at the aircraft's
    # own speed -- so this stays off. Restore it (and drop the groundspeed
    # call) to go back to the old behavior.
    # if signed_lead is not None and signed_lead > 0:
    #     # UAV is already ahead of the bot along its own heading -- never
    #     # slow the bot down for this; it would only freeze the bot's own
    #     # CSV/waypoint progress while the real aircraft has already flown
    #     # past, instead of letting the mission keep advancing.
    #     step_size = config.UAV_MAX_VIRTUAL_STEP
    # else:
    #     # UAV is behind (or signed_lead is unknown -- no live telemetry to
    #     # tell ahead from behind) -- fall back to the undirected ramp, which
    #     # eases the bot off the further behind the real aircraft falls.
    #     step_size = _pacing_step_size(dis)
    # --------------------------------------------------------------------

    # step_size scales how far THIS tick's exec advances the bot along the
    # combined field built above -- the single point where pacing (now the
    # aircraft's own ground speed) turns into the bot's motion.
    cmd.exec(b, step_size=step_size)
    moved_m = 2.0 * math.hypot(b.x - before_x, b.y - before_y)
    if config.BOT_SYNC_DEBUG:
        goal_distance_m = 2.0 * math.hypot(goal[0] - b.x, goal[1] - b.y)
        # `dis` is undirected -- it cannot tell a lagging aircraft from one
        # that has already overflown the bot, nor from one sitting off to the
        # side mid-turn. signed_lead resolves that: +ve AHEAD, -ve BEHIND,
        # ~0 means lateral (no real lead either way).
        if signed_lead is None:
            lead_text = "n/a"
        else:
            lead_text = (
                f"{signed_lead:+.1f}m " f"({'AHEAD' if signed_lead > 0 else 'BEHIND'})"
            )
        print(
            f"[bot-sync] label={label} bot={i} "
            f"dis={dis:.1f}m lead={lead_text} "
            f"step={step_size:.2f} cmd_speed={cmd.speed:.3f} "
            f"moved={moved_m:.2f}m goal_dist={goal_distance_m:.2f}m "
            f"pos=({b.x:.2f},{b.y:.2f}) goal=({goal[0]:.2f},{goal[1]:.2f})"
        )
    if moved_m < 1e-6:
        # A constant step cannot move a bot when the combined field has no
        # magnitude or Bot.step() rejects its proposed position as occupied.
        # Log only the stalled case so a live search is not flooded.
        print(
            f"[bot-stall] bot={i} label={label} cmd_speed={cmd.speed:.3f} "
            f"step={step_size:.2f} pos=({before_x:.2f},{before_y:.2f}) "
            f"goal=({goal[0]:.2f},{goal[1]:.2f})"
        )

    return dis, step_size


def _uav_loiter_radius_m(i):
    """The vehicle's active loiter radius (WP_LOITER_RAD), read live so a
    mid-flight change tracks, with a mission fallback."""
    if state.master_flag and i < len(state.vehicles):
        try:
            radius = abs(float(state.vehicles[i].parameters["WP_LOITER_RAD"]))
            if radius > 0:
                return radius
        except Exception:
            pass
    return config.UAV_DEFAULT_LOITER_RADIUS_M


def waypoint_flyby_radius(i, goal, next_goal=None, is_final=False):
    """Return a fly-by radius that cannot consume the following short leg."""
    if is_final:
        radius = _uav_loiter_radius_m(i) + config.UAV_FINAL_WAYPOINT_RADIUS_MARGIN_M
    else:
        radius = config.SEARCH_UAV_FLYBY_RADIUS_M
    if next_goal is not None:
        # Sim coordinates are half-scale; convert their separation to metres.
        next_leg_m = 2.0 * math.hypot(next_goal[0] - goal[0], next_goal[1] - goal[1])
        if next_leg_m > 0:
            radius = min(radius, 0.4 * next_leg_m)
    return radius


def _lookahead_along_points(curve_points, bot_position):
    """Project bot_position onto the polyline curve_points, then walk
    UAV_CURVE_LOOKAHEAD_M forward from that projection. Shared by both the
    CSV-driven curve case and the plain two-point straight-leg case below --
    the projection/lookahead math doesn't care whether the polyline came
    from consecutive Bezier samples or a single [current, next] pair.
    """
    if len(curve_points) < 2:
        return None

    bot_x, bot_y = bot_position
    closest_distance_sq = float("inf")
    progress_segment = 0
    progress_point = curve_points[0]
    for segment_index in range(len(curve_points) - 1):
        start = curve_points[segment_index]
        end = curve_points[segment_index + 1]
        segment_x = end[0] - start[0]
        segment_y = end[1] - start[1]
        segment_length_sq = segment_x * segment_x + segment_y * segment_y
        if segment_length_sq == 0:
            continue
        projection = (
            (bot_x - start[0]) * segment_x + (bot_y - start[1]) * segment_y
        ) / segment_length_sq
        projection = max(0.0, min(1.0, projection))
        projected_point = (
            start[0] + projection * segment_x,
            start[1] + projection * segment_y,
        )
        distance_sq = (bot_x - projected_point[0]) ** 2 + (
            bot_y - projected_point[1]
        ) ** 2
        if distance_sq < closest_distance_sq:
            closest_distance_sq = distance_sq
            progress_segment = segment_index
            progress_point = projected_point

    remaining_m = config.UAV_CURVE_LOOKAHEAD_M
    current_point = progress_point
    for segment_index in range(progress_segment, len(curve_points) - 1):
        end = curve_points[segment_index + 1]
        segment_m = 2.0 * math.hypot(
            end[0] - current_point[0], end[1] - current_point[1]
        )
        if segment_m > 0 and segment_m >= remaining_m:
            fraction = remaining_m / segment_m
            lookahead_point = (
                current_point[0] + fraction * (end[0] - current_point[0]),
                current_point[1] + fraction * (end[1] - current_point[1]),
            )
            return progress_point, lookahead_point
        remaining_m -= segment_m
        current_point = end

        # The remaining curve/leg is shorter than the configured look-ahead.
    return progress_point, curve_points[-1]


def curve_lookahead_goal(csv_path, line_index, num_lines, current_goal, bot_position):
    """Return continuous curve progress and a target ahead of that progress.

    The CSV's Bezier samples form a polyline. Rather than using the current
    CSV index as progress, project the bot's live virtual position onto that
    polyline every control cycle, then walk UAV_CURVE_LOOKAHEAD_M forward.
    This removes target jumps caused by discrete sample/index changes.
    """
    curve_points = [current_goal]
    for next_index in range(line_index + 1, num_lines):
        try:
            row = read_specific_line(csv_path, next_index)[0]
        except Exception as e:
            print("[curve-guidance] next point read failed", e)
            break
        if str(row[2]).strip().lower() != "true":
            break
        curve_points.append((row[0], row[1]))

    return _lookahead_along_points(curve_points, bot_position)


def line_lookahead_goal(current_goal, next_goal, bot_position):
    """Same forward-lead guidance as curve_lookahead_goal, for a plain
    straight leg. Without this, a straight-leg target sat directly on the
    bot's own (often near-static, pacing-capped) position -- giving the
    fixed-wing's guided controller no line direction to track and letting
    it drift/curve away from the intended leg instead of flying it. Returns
    None on the final leg (no next_goal to derive a direction from), same
    as the curve path falling back to the bot's raw position.
    """
    if next_goal is None:
        return None
    return _lookahead_along_points([current_goal, next_goal], bot_position)


def curve_guidance_position(b, curve_guidance):
    """Apply the curve-forward vector while preserving bot dispersion."""
    if curve_guidance is None:
        return None
    curve_progress, curve_lookahead = curve_guidance
    return (
        b.x + curve_lookahead[0] - curve_progress[0],
        b.y + curve_lookahead[1] - curve_progress[1],
    )


def log_curve_guidance(i, line_index, is_curve, curve_guidance):
    """Log curve parsing once per point, without flooding every control tick."""
    state_key = (line_index, is_curve, curve_guidance is not None)
    if state.last_curve_guidance_log.get(i) == state_key:
        return
    state.last_curve_guidance_log[i] = state_key
    if is_curve:
        print(
            f"[curve-guidance] UAV {state.pos_array[i]} index {line_index}: "
            f"{'look-ahead active' if curve_guidance else 'last curve sample; no forward point'}"
        )


def uav_reached_waypoint(
    i, b, goal, sim_radius=15.0, next_goal=None, is_curve=False, is_final=False
):
    """Advance every in-route point virtually; confirm only mission end by GPS.

    Holding the virtual leader at an intermediate grid point until a
    fixed-wing UAV flies into its acceptance radius freezes the GUIDED target.
    A wide-turn aircraft then keeps orbiting/cutting past that frozen point
    and cannot receive the next target. The bot's own reach test is the
    correct hand-off condition for all in-route points; real-UAV confirmation
    is needed only before declaring the final mission point complete.
    """
    if is_curve:
        bot_reached = (
            abs(goal[0] - b.x) <= config.UAV_CURVE_POINT_SWITCH_RADIUS
            and abs(goal[1] - b.y) <= config.UAV_CURVE_POINT_SWITCH_RADIUS
        )
    else:
        bot_reached = (
            abs(goal[0] - b.x) <= sim_radius and abs(goal[1] - b.y) <= sim_radius
        )
    if not is_final:
        return bot_reached, None

    distance = uav_distance_to_goal(i, goal)
    if distance is not None:
        return (
            bot_reached
            and distance <= waypoint_flyby_radius(i, goal, next_goal, is_final)
        ), distance
    if not state.master_flag:
        return bot_reached, None
        # Live missions must not falsely complete a leg during a telemetry gap.
    return False, None


def _drive_vehicle_towards(i, b, guidance_position=None):
    if state.master_flag and i < len(state.vehicles):
        position = guidance_position
        if position is None:
            # No pursuit target this tick (telemetry hiccup -- lat/lon None or
            # an exception in pursuit_target_with_avoidance). This used to fall
            # back to the bot's RAW position, which is actively dangerous once
            # the aircraft has overrun the bot: that point is then BEHIND the
            # aircraft, and ArduPilot answers a target it has already passed by
            # circling it. Hold the last good target instead, and if there
            # isn't one yet, command nothing at all this tick.
            position = state.uav_lookahead_points.get(i)
            if position is None:
                return
        state.uav_lookahead_points[i] = position
        current_position = (position[0] * 2, position[1] * 2)
        lat, lon = locatePosition.cartToGeo(
            state.origin, config.END_DISTANCE, current_position
        )
        if state.same_alt_flag:
            point1 = LocationGlobalRelative(lat, lon, state.same_height)
        else:
            point1 = LocationGlobalRelative(lat, lon, state.different_height[i])
        state.vehicles[i].simple_goto(point1)
