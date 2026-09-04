"""Background per-bot task driver.

Once a bot has an entry in state.active_goal_tasks (assigned by a Goal,
Search, or Split/Split-Search command -- see the sibling task modules --
this background thread keeps driving it every tick, independent of
whatever the foreground dispatch loop in main.py is doing for any other
bot. This is what lets a command targeted at a UAV subset run concurrently
with whatever the rest of the swarm is doing.
"""

import csv
import threading
import time

import locatePosition

from medur_swarm import config, state
from medur_swarm.utils import generate_points, read_specific_line
from medur_swarm.uav.guidance import (
    _drive_vehicle_towards,
    _uav_loiter_radius_m,
    advance_bot_with_uav_pacing,
    pursuit_target_with_avoidance,
    signed_uav_lead,
    uav_reached_waypoint,
)
from medur_swarm.uav.telemetry import uav_distance_to_goal


def _reset_mission_state():
    """Clear the mission-scoped state shared/leaked across the
    interruptible mission loops (Goal, Guided Circle, Navigate, Search,
    Split/Specific Split) so a freshly dispatched command -- whether it
    arrived normally or preempted a running mission -- never inherits
    residue from whatever ran before it. Called once per dispatched
    command, right before the command is matched against the if-chain
    below. Connection/topology state (vehicles, pos_array, origin, s)
    is intentionally left alone -- a new mission keeps flying the same
    connected swarm, it does not drop it.
    """
    state.landing_flag = False
    state.removed_uav_grid = []
    state.removed_grid_path_length = []
    state.removed_grid_path_array = [0] * len(state.pos_array)
    state.removed_grid_path_array_start_val = [0] * len(state.pos_array)
    state.checkall_removed_grid_path_array_start_val = [0] * len(state.pos_array)
    state.removed_grid_filename = [0] * len(state.pos_array)
    state.removed_grid_path_array_flag = False
    state.removed_grid_path_array_index = 0
    state.uncovered_area_points = []
    state.uncovered_area_filename = []
    state.group_goal_flag = False
    state.guided_circle_flag = False
    state.guided_circle_formation_flag = False
    # No foreground search/split/specificsplit loop is running at dispatch time
    # (we only get here between missions), so clear the set that tells
    # apply_different_heights which bots such a loop is currently flying.
    state.foreground_mission_indexes = set()
    # Stale look-ahead markers from the previous mission -- the new mission's
    # first drive tick repopulates this per bot.
    state.uav_lookahead_points.clear()


def clear_all_active_tasks():
    """'stop' dispatch-loop command: drop every in-flight background
    task. The caller (main.py) must abort the rest of that dispatch
    iteration immediately afterward, matching the original's unconditional
    `continue` right after this."""
    with state.active_goal_tasks_lock:
        state.active_goal_tasks.clear()
    # Drop the stored "Automate Goals" layout too, so a later on-board
    # radius change doesn't silently resurrect a stopped loiter formation.
    state.autogoal_params = None
    state.goal_min_distance.clear()
    state.bot_step_last_time.clear()
    print("[goal-task] cleared by stop")


def assign_goal_tasks(
    selected_indexes, goal_xy, guided_circle_radius=None, guided_circle_direction=None
):
    with state.active_goal_tasks_lock:
        for slot, bot_index in enumerate(selected_indexes):
            # Fresh task -- start the closest-approach latch and the
            # groundspeed-pacing clock over for this bot.
            state.goal_min_distance.pop(bot_index, None)
            state.bot_step_last_time.pop(bot_index, None)
            state.active_goal_tasks[bot_index] = {
                "type": "goal",
                "goals": list(goal_xy),
                "goal_index": 0,
                "guided_circle_radius": guided_circle_radius,
                "guided_circle_direction": guided_circle_direction,
                # Used by _start_guided_circle_task to stagger this bot's
                # starting ring slot instead of every bot in the group
                # converging on circle_points[0] at once.
                "circle_slot": slot,
                "circle_slot_count": len(selected_indexes),
            }
    print(
        "[goal-task] assigned",
        selected_indexes,
        goal_xy,
        "circle_radius",
        guided_circle_radius,
        "circle_direction",
        guided_circle_direction,
    )


def assign_autogoal_tasks(
    selected_indexes, per_uav_goal_xy, guided_circle_radius, guided_circle_direction
):
    """'Automate Goals' variant of assign_goal_tasks.

    Unlike a normal goal command -- where every selected bot shares one
    ordered waypoint list -- here each bot gets its OWN single-point goal
    (its dedicated loiter center, laid out by
    goal_point_generator.generate_loiter_goal_points). On arrival the
    existing _start_guided_circle_task turns that into a loiter circle of
    `guided_circle_radius` around that same center, so every bot ends up
    on its own non-overlapping circle.

    circle_slot/circle_slot_count are pinned to 0/1: each bot owns its
    circle alone, so there is no group of bots to stagger it against.

    Re-calling this (e.g. after a mid-flight radius change regenerates the
    layout) simply overwrites each bot's task, same "new command
    terminates the old one" behavior assign_goal_tasks already has.
    """
    with state.active_goal_tasks_lock:
        for slot, bot_index in enumerate(selected_indexes):
            if slot < len(per_uav_goal_xy):
                goal_xy = tuple(per_uav_goal_xy[slot])
            elif per_uav_goal_xy:
                goal_xy = tuple(per_uav_goal_xy[-1])
            else:
                continue
            # Same fresh-task reset as assign_goal_tasks -- matters here too,
            # since a mid-flight radius change re-runs this for every UAV.
            state.goal_min_distance.pop(bot_index, None)
            state.bot_step_last_time.pop(bot_index, None)
            state.active_goal_tasks[bot_index] = {
                "type": "goal",
                "goals": [goal_xy],
                "goal_index": 0,
                "guided_circle_radius": guided_circle_radius,
                "guided_circle_direction": guided_circle_direction,
                "circle_slot": 0,
                "circle_slot_count": 1,
            }
    print(
        "[autogoal-task] assigned",
        selected_indexes,
        per_uav_goal_xy,
        "circle_radius",
        guided_circle_radius,
        "circle_direction",
        guided_circle_direction,
    )


def assign_mission_tasks(csv_paths_by_index, label):
    """Registers a waypoint-follow task (used by search and split) for each
    given bot index, keyed by its own per-drone CSV file. Runs in the same
    background thread/dict as goal tasks, so a search or split assigned to
    one UAV subset progresses independently of whatever goal/search/split
    the rest of the swarm is doing -- assigning any task type to a bot
    index simply overwrites whatever task (of any type) that index had
    before, matching the "new command terminates the old one, never
    resumes it" behavior goal already has."""
    with state.active_goal_tasks_lock:
        for bot_index, csv_path in csv_paths_by_index.items():
            try:
                with open(csv_path, "rt") as f:
                    num_lines = sum(1 for _ in csv.reader(f))
            except Exception as e:
                print(f"[{label}-task] failed to read {csv_path}: {e}")
                continue
            state.active_goal_tasks[bot_index] = {
                "type": "mission",
                "label": label,
                "csv_path": csv_path,
                "line_index": 0,
                "num_lines": num_lines,
            }
    print(f"[{label}-task] assigned", csv_paths_by_index)


def remove_goal_task_index(removed_index):
    with state.active_goal_tasks_lock:
        if removed_index in state.active_goal_tasks:
            del state.active_goal_tasks[removed_index]
        shifted_tasks = {}
        for bot_index, task in state.active_goal_tasks.items():
            new_index = bot_index - 1 if bot_index > removed_index else bot_index
            shifted_tasks[new_index] = task
        state.active_goal_tasks.clear()
        state.active_goal_tasks.update(shifted_tasks)
    print(
        "[goal-task] compacted after remove",
        removed_index,
        sorted(state.active_goal_tasks.keys()),
    )


def synchronize_mission_topology(
    selected_indexes,
    csv_file_paths,
    all_csv_paths,
    grid_indexes,
    line_counts,
    current_goals,
    planned_paths,
):
    """Apply queued UAV removals to one foreground search/split mission.

    These lists are all indexed by the simulator's compacted bot index. A
    removed UAV must therefore remove the matching CSV *slot* before indexes
    are shifted; otherwise the UAV after it is given the removed UAV's path.
    The resize also makes adding an idle UAV safe while a selected subset is
    still executing.
    """
    removed_indexes = (
        sorted(set(state.remove_bot_array), reverse=True) if state.remove_bot_flag else []
    )
    for removed_index in removed_indexes:
        # csv_file_paths is indexed by selected_indexes, not by bot index.
        if removed_index in selected_indexes:
            path_slot = selected_indexes.index(removed_index)
            if path_slot < len(csv_file_paths):
                csv_file_paths.pop(path_slot)
        for values in (
            all_csv_paths,
            grid_indexes,
            line_counts,
            current_goals,
            planned_paths,
        ):
            if 0 <= removed_index < len(values):
                values.pop(removed_index)
        selected_indexes = [
            index - 1 if index > removed_index else index
            for index in selected_indexes
            if index != removed_index
        ]

    # Addition appends an IDLE bot. Keep every foreground bookkeeping array
    # aligned, but do not add that new bot to selected_indexes: it must not be
    # accidentally assigned a path from the already-running mission.
    target_size = len(state.pos_array)
    for values, fill in (
        (all_csv_paths, 0),
        (grid_indexes, 0),
        (line_counts, 0),
        (current_goals, None),
        (planned_paths, None),
    ):
        del values[target_size:]
        values.extend([fill] * (target_size - len(values)))

    if removed_indexes:
        print(
            "[mission-topology] removed indexes",
            removed_indexes,
            "remaining selected indexes",
            selected_indexes,
        )
        state.remove_bot_array = []
        state.remove_bot_flag = False
    return selected_indexes


def _build_circle_points(center_xy, radius, direction):
    """8 ring points of `radius` metres around a sim-frame centre, returned in
    the sim frame. Shared by the initial handoff and by the mid-flight rebuild
    that keeps the plotted ring matching a changed WP_LOITER_RAD."""
    center_lat, center_lon = locatePosition.cartToGeo(
        state.origin, config.END_DISTANCE, [center_xy[0] * 2, center_xy[1] * 2]
    )
    circle_latlon = generate_points(center_lat, center_lon, 8, radius, direction)
    points = []
    for m in circle_latlon:
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, m)
        points.append((x / 2, y / 2))
    return points


def _start_guided_circle_task(i, task):
    """Transitions a completed goal task into a loitering circle around its
    final goal point. Mirrors the original (dead) foreground guided_circle
    block: 8 points around goal_latlon[-1] via generate_points(), converted
    to the local sim frame the same way.

    The command's `guided_circle_radius` is only the "did the operator ask
    for a loiter?" flag -- when one was asked for, the ring is sized from
    the vehicle's LIVE WP_LOITER_RAD (_uav_loiter_radius_m), so a loiter
    radius changed on board -- or set straight on the autopilot -- is what
    the generated circle follows, not a value frozen into the command.
    Only called when a radius was actually given; if not, the goal task
    just completes and the UAV holds position."""
    goals = task.get("goals", [])
    radius_raw = task.get("guided_circle_radius")
    direction_raw = task.get("guided_circle_direction")
    try:
        # radius arrives as a string off the wire (e.g. "0") -- a non-empty
        # string is truthy in Python even when it means "no loiter
        # configured", so convert before checking rather than after.
        requested_radius = int(float(radius_raw)) if radius_raw is not None else 0
    except (TypeError, ValueError):
        requested_radius = 0
    try:
        direction = int(float(direction_raw)) if direction_raw is not None else 1
    except (TypeError, ValueError):
        direction = 1
    if not goals or requested_radius <= 0:
        return None
    # Ring size = the aircraft's own current loiter radius, with the
    # requested value as the fallback if the live parameter can't be read.
    radius = _uav_loiter_radius_m(i)
    if radius <= 0:
        radius = requested_radius
    print(
        "guided_circle radius (live WP_LOITER_RAD)", radius,
        "requested", requested_radius,
    )
    try:
        # goals[-1] is a local sim-frame (x, y) point (the /2-scaled output
        # of geoToCart in handle_concurrent_goal_command), not lat/lon --
        # _build_circle_points converts back to real coordinates for the geo
        # math and returns the ring in the sim frame.
        last_goal_x, last_goal_y = goals[-1][0], goals[-1][1]
        circle_points = _build_circle_points(
            (last_goal_x, last_goal_y), radius, direction
        )
    except Exception as e:
        print("[guided-circle] failed to start for UAV", state.pos_array[i], e)
        return None
    # Stagger this bot's starting ring point by its slot among the bots
    # that were assigned this goal together, so they fan out onto distinct
    # circle_points immediately instead of every bot heading for
    # circle_points[0] and fighting over the same physical spot.
    circle_slot = task.get("circle_slot", 0)
    circle_slot_count = task.get("circle_slot_count") or 1
    start_index = round(circle_slot * len(circle_points) / circle_slot_count) % len(
        circle_points
    )
    print(
        "[guided-circle] starting for UAV",
        state.pos_array[i],
        "radius",
        radius,
        "direction",
        direction,
        "slot",
        circle_slot,
        "of",
        circle_slot_count,
        "start_index",
        start_index,
    )
    return {
        "type": "guided_circle",
        "circle_points": circle_points,
        "circle_index": start_index,
        # The ring's centre (= the final goal point, sim frame). This is what
        # is actually commanded to the aircraft now: ArduPilot Plane in GUIDED
        # loiters around a position target at its own WP_LOITER_RAD, so the
        # autopilot flies a true constant-radius orbit instead of chasing the
        # synthesized ring. circle_points is kept for the plot overlay (and
        # for the pursuit path, if it is ever restored).
        "center": (last_goal_x, last_goal_y),
        # What circle_points was drawn at, so _drive_guided_circle_task can
        # notice a mid-flight WP_LOITER_RAD change and redraw the ring.
        "radius": radius,
        "direction": direction,
    }


def _drive_goal_task(i, b, task, completed):
    goals = task.get("goals", [])
    goal_index = task.get("goal_index", 0)
    if goal_index >= len(goals):
        completed.append(i)
        return
    goal_position = goals[goal_index]
    next_goal = goals[goal_index + 1] if goal_index + 1 < len(goals) else None
    if next_goal is None:
        # FINAL goal point: the bot keeps flying to its exact xy and the real
        # UAV keeps following it, but the guided circle is triggered purely by
        # the real UAV closing within its own live WP_LOITER_RAD of the goal --
        # no bot-arrival requirement and no extra flyby margin, so it peels
        # into the loiter the way native GUIDED mode does instead of first
        # having to reach the exact point. (uav_reached_waypoint's general
        # bot_reached AND flyby-radius rule still applies everywhere else --
        # intermediate points here, and search/split via _drive_mission_task.)
        goal_distance = uav_distance_to_goal(i, goal_position)
        if goal_distance is not None:
            radius = _uav_loiter_radius_m(i)
            # The threshold MUST sit outside WP_LOITER_RAD, not on it. Once
            # the bot parks on the final goal the aircraft is commanded that
            # exact point, and ArduPilot answers a GUIDED position target by
            # loitering around it at WP_LOITER_RAD -- so the aircraft's
            # distance to the goal converges to the loiter radius itself and
            # can never go below it. Testing "distance <= radius" therefore
            # tests the boundary of what is physically achievable and fails by
            # a couple of metres, forever (observed: dis pinned at 2162.4 m
            # against a ~2160 m radius, frozen tick after tick, bot parked
            # 0.45 m from its goal). The margin is what makes "the aircraft
            # has settled into its loiter around the goal" actually testable.
            arrival_radius = radius + config.UAV_FINAL_WAYPOINT_RADIUS_MARGIN_M
            reached_goal = goal_distance <= arrival_radius
            # Latch the closest approach. Testing "inside the radius right
            # now" alone needs a tick to sample the aircraft while it is in
            # there, and a mid-flight radius reduction (e.g. 1000 -> 600) can
            # take that window away from a UAV that was already inside the old
            # one -- it then flies past, starts receding, and never qualifies
            # again. Once the aircraft has come within a couple of radii and
            # then clearly turned away, it has made its pass: hand off.
            min_seen = state.goal_min_distance.get(i)
            if min_seen is None or goal_distance < min_seen:
                state.goal_min_distance[i] = goal_distance
                min_seen = goal_distance
            if (
                not reached_goal
                and min_seen <= arrival_radius * config.GOAL_CLOSEST_APPROACH_FACTOR
                and goal_distance > min_seen + config.GOAL_RECEDE_MARGIN_M
            ):
                reached_goal = True
                print(
                    f"[goal-task] UAV {state.pos_array[i]} passed closest "
                    f"approach {min_seen:.0f} m (now {goal_distance:.0f} m, "
                    f"radius {radius:.0f} m) -- starting circle"
                )
        elif not state.master_flag:
            # Sim-only run (no real vehicles): fall back to the bot's own
            # arrival test, exactly as uav_reached_waypoint does.
            reached_goal, goal_distance = uav_reached_waypoint(
                i, b, goal_position, sim_radius=15, is_final=True
            )
        else:
            # Live mission with a telemetry gap -- never complete on a guess.
            reached_goal = False
    else:
        reached_goal, goal_distance = uav_reached_waypoint(
            i,
            b,
            goal_position,
            sim_radius=15,
            next_goal=next_goal,
            is_final=False,
        )
    if reached_goal:
        if config.BOT_SYNC_DEBUG:
            print(
                f"[waypoint-advance] label=goal bot={i} "
                f"index={goal_index}->{goal_index + 1} "
                f"bot=({b.x:.2f},{b.y:.2f}) goal=({goal_position[0]:.2f},{goal_position[1]:.2f})"
            )
        if goal_distance is not None:
            print(f"[uav-flyby] bot {i}: switching goal at {goal_distance:.1f} m")
        goal_index += 1
        if goal_index >= len(goals):
            try:
                requested = int(float(task.get("guided_circle_radius") or 0))
            except (TypeError, ValueError):
                requested = 0
            circle_radius = _uav_loiter_radius_m(i) if requested > 0 else 0
            print(
                f"[goal-task] UAV {state.pos_array[i]} reached its final goal; "
                f"guided-circle radius = {circle_radius} m (live WP_LOITER_RAD)"
            )
            circle_task = _start_guided_circle_task(i, task)
            # This goal task is over either way -- drop its closest-approach
            # latch so a later goal for this bot starts measuring afresh.
            state.goal_min_distance.pop(i, None)
            with state.active_goal_tasks_lock:
                if i in state.active_goal_tasks:
                    if circle_task is not None:
                        state.active_goal_tasks[i] = circle_task
                    else:
                        del state.active_goal_tasks[i]
            if circle_task is None:
                completed.append(i)
                print("[goal-task] completed UAV", state.pos_array[i])
            return
        with state.active_goal_tasks_lock:
            if i in state.active_goal_tasks:
                state.active_goal_tasks[i]["goal_index"] = goal_index
        goal_position = goals[goal_index]
    # Bot still advances via advance_bot_with_uav_pacing -- the UAV<->bot
    # distance-based slowdown/freeze inside it is what's commented out (see
    # the "DISABLED for testing" block in uav/guidance.py), not the call
    # itself, so 'goal' keeps moving at full pace regardless of that distance.
    advance_bot_with_uav_pacing(i, b, goal_position, label="goal")
    # The aircraft is sent the BOT'S OWN POSITION and nothing else. No
    # look-ahead projection, no avoidance offset, no distance term of any
    # kind is added on top -- the bot's cmd.exec (goal steering + bot
    # dispersion, paced at the aircraft's own ground speed) is the single
    # thing that decides where this UAV is told to go.
    #
    # This is what makes the end state correct by construction: when the bot
    # reaches its final goal it stops, so the commanded point stops with it,
    # ON the goal. The aircraft arrives and ArduPilot simply loiters there at
    # WP_LOITER_RAD -- native GUIDED behaviour, no synthesized ring needed to
    # get it. And because nothing is ever added to the bot's position, there
    # is no longer any way for the target to end up miles beyond the goal.
    #
    # (The previous pursuit target did exactly that: it projected 720 SIM
    # units = 1440 m along the bot's heading, so once the bot stalled on its
    # goal the aircraft was still being sent 1.4 km past it, flew out there,
    # loitered on that point, and receded from the goal it was meant to
    # capture. Restore pursuit_target_with_avoidance(i, b) here to go back.)
    _drive_vehicle_towards(i, b, (b.x, b.y))


def _drive_guided_circle_task(i, b, task, completed):
    """Continuous loiter -- never adds to completed under normal operation;
    only stops via active_goal_tasks being overwritten by a new command or
    cleared by an explicit stop, matching the original design's intent
    (circle until told otherwise)."""
    circle_points = task.get("circle_points", [])
    if not circle_points:
        completed.append(i)
        return
    center = task.get("center")
    if center is None:
        # Older/partial task dicts: fall back to the ring's centroid.
        center = (
            sum(p[0] for p in circle_points) / len(circle_points),
            sum(p[1] for p in circle_points) / len(circle_points),
        )

    # Keep the drawn ring honest when WP_LOITER_RAD changes mid-flight. The
    # aircraft's actual orbit follows the parameter immediately (the autopilot
    # is flying it), but circle_points was generated once at handoff -- so
    # without this the overlay keeps showing the OLD radius while the aircraft
    # flies the new one. That is the "plot not showing properly" after a live
    # radius change on a 'goal': autogoal escapes it only because a radius
    # change there rebuilds every task from scratch.
    live_radius = _uav_loiter_radius_m(i)
    built_radius = task.get("radius")
    if (
        built_radius
        and live_radius > 0
        and abs(live_radius - built_radius) > config.CIRCLE_RADIUS_REDRAW_TOLERANCE_M
    ):
        try:
            circle_points = _build_circle_points(
                center, live_radius, task.get("direction", 1)
            )
            with state.active_goal_tasks_lock:
                if i in state.active_goal_tasks:
                    state.active_goal_tasks[i]["circle_points"] = circle_points
                    state.active_goal_tasks[i]["radius"] = live_radius
            print(
                f"[guided-circle] UAV {state.pos_array[i]} ring redrawn "
                f"{built_radius:.0f} m -> {live_radius:.0f} m (live WP_LOITER_RAD)"
            )
        except Exception as e:
            print("[guided-circle] ring redraw failed for UAV", state.pos_array[i], e)

    circle_index = task.get("circle_index", 0) % len(circle_points)
    goal_position = circle_points[circle_index]
    # Wide dispersion term (matches the reference implementation's loiter
    # loop) keeps bots that start on/near the same ring point pushed apart
    # from each other throughout the circle, on top of the per-bot starting
    # stagger assigned in _start_guided_circle_task. advance_bot_with_uav_pacing
    # applies that same dispersion field internally, plus real-UAV-distance
    # pacing -- previously this called cmd.exec(b) with no step_size at
    # all, so the bot lapped the ring at full speed regardless of whether
    # the real aircraft (which can't match a tight ring's turn rate) was
    # anywhere close to keeping up, and the gap between them only grew.
    advance_bot_with_uav_pacing(i, b, goal_position, label="guided_circle")
    dx = abs(goal_position[0] - b.x)
    dy = abs(goal_position[1] - b.y)
    if dx <= 5 and dy <= 5:
        circle_index = (circle_index + 1) % len(circle_points)
        with state.active_goal_tasks_lock:
            if i in state.active_goal_tasks:
                state.active_goal_tasks[i]["circle_index"] = circle_index
    # NATIVE LOITER: command the ring's CENTRE and let the autopilot orbit it.
    # ArduPilot Plane in GUIDED flies to a position target and then loiters
    # around it at its own WP_LOITER_RAD (direction from that parameter's
    # sign), giving a true constant-radius orbit flown within the aircraft's
    # own turn limits.
    #
    # The pursuit path below did the opposite: pursuit_target_with_avoidance
    # defaults to distance=720 SIM units = 1440 m real, i.e. ~7x a 200 m ring
    # radius, projected along the bot's instantaneous heading -- so the plane
    # was being sent 1.4 km out on the ring's TANGENT every tick and wandered
    # far outside the intended loiter radius instead of circling it.
    # Uncomment it (and comment out the centre command) to go back.
    # `center` is resolved once at the top of this function (the ring rebuild
    # needs it too), so it is just used here.
    _drive_vehicle_towards(i, b, center)
    # _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))


def _drive_mission_task(i, b, task, completed):
    line_index = task.get("line_index", 0)
    num_lines = task.get("num_lines", 0)
    label = task.get("label", "mission")
    if line_index >= num_lines:
        completed.append(i)
        print(f"[{label}-task] completed UAV", state.pos_array[i])
        return
    try:
        goal_lat_lon = read_specific_line(task["csv_path"], line_index)
    except Exception as e:
        print(f"[{label}-task] read failed", task.get("csv_path"), e)
        completed.append(i)
        return
    goal_position = (goal_lat_lon[0][0], goal_lat_lon[0][1])
    is_curve = str(goal_lat_lon[0][2]).strip().lower() == "true"
    is_last_point = line_index >= num_lines - 1
    sim_radius = (
        config.MISSION_FINAL_POINT_RADIUS if is_last_point else config.MISSION_POINT_SWITCH_RADIUS
    )
    next_goal = None
    if not is_last_point:
        try:
            next_row = read_specific_line(task["csv_path"], line_index + 1)
            next_goal = (next_row[0][0], next_row[0][1])
        except Exception as e:
            print(f"[{label}-task] next point read failed", e)
    # If the bot has already arrived at goal_position, pacing it toward
    # that same point again pulls with ~zero magnitude and it goes fully
    # static -- and a static bot means a static pursuit target
    # (compute_lookahead_target is anchored on the bot's own x/y/heading),
    # which risks the real aircraft closing in on a fixed point and
    # orbiting it while a lead-cap hold keeps line_index from advancing.
    # Pacing toward next_goal instead keeps the bot -- and therefore the
    # pursuit target -- moving, without touching line_index itself; that
    # still only advances once the lead cap below allows it.
    already_at_goal = (
        abs(goal_position[0] - b.x) <= sim_radius
        and abs(goal_position[1] - b.y) <= sim_radius
    )
    pacing_target = next_goal if (already_at_goal and next_goal is not None) else goal_position
    dis, _step_size = advance_bot_with_uav_pacing(i, b, pacing_target, label="mission")
    reached_goal, goal_distance = uav_reached_waypoint(
        i,
        b,
        goal_position,
        sim_radius=sim_radius,
        next_goal=next_goal,
        is_curve=is_curve,
        is_final=is_last_point,
    )
    if reached_goal:
        if goal_distance is not None:
            print(
                f"[uav-flyby] bot {i}: switching {label} point at {goal_distance:.1f} m"
            )
        signed_lead = signed_uav_lead(i, b)
        uav_is_ahead = signed_lead is not None and signed_lead > 0
        if dis > config.UAV_MAX_VIRTUAL_LEAD_M and not uav_is_ahead:
            # Real aircraft is too far BEHIND to commit to a new point yet
            # -- hold line_index here (the bot still tracks this same
            # point; only advancing to the NEXT one is paused) so the lead
            # can't keep growing unbounded the way it did with pacing
            # alone. Never holds just because `dis` is large when the UAV
            # is actually ahead -- that's not lagging.
            if config.BOT_SYNC_DEBUG:
                print(
                    f"[lead-cap] bot={i} holding at current {label} point -- "
                    f"dis={dis:.1f}m exceeds "
                    f"UAV_MAX_VIRTUAL_LEAD_M={config.UAV_MAX_VIRTUAL_LEAD_M:.0f}m"
                )
        else:
            line_index += 1
            with state.active_goal_tasks_lock:
                if i in state.active_goal_tasks:
                    state.active_goal_tasks[i]["line_index"] = line_index
    # Pursuit point ahead of the bot's own heading, corrected for real
    # UAV-to-UAV separation -- same guidance goal/search/split all use now,
    # instead of the CSV-line-anchored curve/line look-ahead this used to
    # compute from the bot's own position alone.
    _drive_vehicle_towards(i, b, pursuit_target_with_avoidance(i, b))


def _goal_task_runner():
    """Background thread, independent of the main command-dispatch loop.
    Continuously drives whichever bot indexes have an active_goal_tasks
    entry (goal, search, or split), so any command assigned to a UAV
    subset keeps progressing regardless of what the rest of the swarm is
    doing. There is no foreground "current mission" for these three
    command types anymore -- check_for_new_command/MissionPreempted is
    only reached by whatever hasn't been generalized this way yet
    (navigate, home, etc.)."""
    from medur_swarm.tasks.altitude import _drive_altitude_task

    while True:
        time.sleep(config.SLEEP_TIMES.get(len(state.pos_array), 0.1))
        try:
            # Keep assignment/replacement and a complete drive tick mutually
            # exclusive. A selected-UAV command therefore takes effect at the
            # next tick at the latest, with no stale command after replacement.
            with state.active_goal_tasks_lock:
                tasks_snapshot = list(state.active_goal_tasks.items())
                if not tasks_snapshot:
                    continue
                completed = []
                for i, task in tasks_snapshot:
                    if state.active_goal_tasks.get(i) is not task:
                        continue
                    if i >= len(state.s.swarm) or i >= len(state.pos_array):
                        completed.append(i)
                        continue
                    b = state.s.swarm[i]
                    task_type = task.get("type")
                    if task_type == "mission":
                        _drive_mission_task(i, b, task, completed)
                    elif task_type == "guided_circle":
                        _drive_guided_circle_task(i, b, task, completed)
                    elif task_type == "altitude":
                        _drive_altitude_task(i, b, task, completed)
                    else:
                        _drive_goal_task(i, b, task, completed)
                if completed:
                    for i in completed:
                        state.active_goal_tasks.pop(i, None)
            # NOTE: deliberately does not call gui.update() here.
            # matplotlib's default Tk backend is not thread-safe -- all GUI
            # calls must happen on the thread that created the figure
            # (the main thread, via a foreground search/split/navigate
            # loop's own gui.update() calls). Calling it from this
            # background thread throws "Calling Tcl from different
            # apartment"/"main thread is not in main loop" every cycle.
            # Consequence: a UAV running purely as a background concurrent
            # task, with nothing currently occupying a foreground loop,
            # won't visibly move on the plot until some foreground loop's
            # own gui.update() call happens to run again.
        except Exception as e:
            print("[goal-task] runner exception", e)


def start_goal_task_thread():
    goal_task_thread = threading.Thread(target=_goal_task_runner)
    goal_task_thread.daemon = True
    goal_task_thread.start()
    return goal_task_thread
