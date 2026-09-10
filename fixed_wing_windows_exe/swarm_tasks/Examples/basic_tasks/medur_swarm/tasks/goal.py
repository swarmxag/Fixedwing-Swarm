"""'goal' command: send a UAV subset (or the whole swarm) through an
ordered list of goal points, handing off to a loitering circle at the end
if the operator configured one. The actual flying is owned by the
background task runner (tasks/runner.py, assign_goal_tasks); this module's
foreground loop only exists to plot progress and stay preemptable.

Also home to the 'autogoal' command ("Automate Goals" button): from ONE
operator point it lays out one non-overlapping loiter circle per UAV
along a bearing (goal_point_generator.generate_loiter_goal_points) and
assigns each UAV its own circle. Independent of 'goal' -- neither path
changes the other's behavior."""

import json
import time

from swarm_tasks.simulation import visualizer as viz

import locatePosition

from medur_swarm import config, state, terrain_gate
from medur_swarm.utils import parse_selected_uav_ids, selected_swarm_indexes
from medur_swarm.uav.telemetry import live_gps_plot_points
from medur_swarm.tasks.runner import assign_goal_tasks, assign_autogoal_tasks
from medur_swarm.communication.dispatch import check_for_new_command, MissionPreempted
from medur_swarm.goal_point_generator import (
    DEFAULT_BEARING_DEG,
    DEFAULT_SAFETY_MARGIN_M,
    loiter_goal_latlon_list,
)


def handle_concurrent_goal_command(command_data):
    if not command_data.startswith(b"goal"):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        msg_parts = decoded_index.split("_")
        if len(msg_parts) < 5:
            return False
        goal_latlon = json.loads(msg_parts[1])
        selected_uav_ids = parse_selected_uav_ids(msg_parts[4])
        if not selected_uav_ids:
            return False
        selected_indexes = selected_swarm_indexes(selected_uav_ids)
        goal_xy = []
        for goal_point in goal_latlon:
            x, y = locatePosition.geoToCart(
                state.origin,
                config.END_DISTANCE,
                [float(goal_point[0]), float(goal_point[1])],
            )
            goal_xy.append((x / 2, y / 2))
        guided_circle_direction = msg_parts[2]
        guided_circle_radius = msg_parts[3]
        # Concurrent goals never pass back through the server's gate, so this
        # is the only terrain check they get.
        route = [(float(p[0]), float(p[1])) for p in goal_latlon]
        ok, _ = terrain_gate.check_goals(
            selected_indexes, route, guided_circle_radius, label="concurrent goal"
        )
        if not ok:
            return False
        assign_goal_tasks(
            selected_indexes, goal_xy, guided_circle_radius, guided_circle_direction
        )
        print(
            "[concurrent goal] accepted during running mission",
            selected_uav_ids,
            selected_indexes,
        )
        return True
    except Exception as e:
        print("[concurrent goal] failed", e)
        return False


def run_goal_command(data):
    """The foreground 'goal' dispatch-loop handler.

    Returns True when the caller must `continue` the outer dispatch loop
    immediately -- which the original code always did once it reached the
    end of a successful parse (an unconditional `continue` right after the
    plotting loop below), so this returns True on that path. On any
    non-MissionPreempted exception it returns None/False instead, exactly
    mirroring the original's bare `except Exception: ... pass` with no
    continue -- letting the caller fall through to check whatever
    dispatch block comes next. MissionPreempted is not caught here: it
    must propagate all the way out to main.py's own per-iteration handler,
    exactly as the original's `except MissionPreempted: raise` did.
    """
    if not data.startswith(b"goal"):
        return
    state.index = "data"
    try:
        decoded_index = data.decode(
            "utf-8"
        )  # Assuming utf-8 encoding, adjust if needed
        msg_parts = decoded_index.split("_")
        print("msg_parts", msg_parts, len(msg_parts))
        f = msg_parts[0]  # First coordinate pair
        guided_circle_direction = msg_parts[2]
        guided_circle_radius = msg_parts[3]
        goal_array = msg_parts[1]  # All other coordinates
        goal_latlon = json.loads(goal_array)
        # Published for run_guided_circle_command (tasks/formation.py),
        # which only ever runs immediately after a 'goal' dispatch and
        # reads back whatever that dispatch last parsed here -- the same
        # implicit reliance on shared state the original script had via
        # one flat module scope.
        state.goal_latlon = goal_latlon
        state.guided_circle_direction = guided_circle_direction
        state.guided_circle_radius = guided_circle_radius
        goal_xy = []
        for x in goal_latlon:
            print(state.origin, [x[0], x[1]])
            x, y = locatePosition.geoToCart(
                state.origin, config.END_DISTANCE, [float(x[0]), float(x[1])]
            )
            goal_xy.append((x / 2, y / 2))
            print(goal_xy, "goal_xy")
        print(goal_xy, goal_xy[0], "goal")
        selected_uav_ids = parse_selected_uav_ids(
            msg_parts[4] if len(msg_parts) > 4 else None
        )
        selected_indexes = selected_swarm_indexes(selected_uav_ids)
        print(
            "[goal] selected_uav_ids",
            selected_uav_ids,
            "selected_indexes",
            selected_indexes,
        )
        # Second-layer terrain gate. The server already refused an unsafe goal
        # before transmitting it (that is where the operator sees a warning);
        # this re-checks against each UAV's live position and its actual
        # different_height[i], which the server does not have.
        route = [(float(p[0]), float(p[1])) for p in goal_latlon]
        ok, _ = terrain_gate.check_goals(
            selected_indexes, route, guided_circle_radius, label="goal"
        )
        if not ok:
            return True
        assign_goal_tasks(
            selected_indexes,
            goal_xy,
            guided_circle_radius,
            guided_circle_direction,
        )

        # Movement is owned by _goal_task_runner (background thread)
        # from here on -- this loop is read-only and exists purely to
        # plot what that thread is doing.
        _plot_goal_tasks(selected_indexes, label="goal")
        return True
    except MissionPreempted:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        print("exception", e)


def _plot_goal_tasks(selected_indexes, label="goal"):
    """Foreground, read-only plot loop for the background goal/autogoal
    tasks of `selected_indexes`.

    Movement is owned by _goal_task_runner (background thread);
    matplotlib calls must happen on the main thread, so this loop exists
    purely to draw what that thread is doing -- per-bot current goal,
    planned path, loiter circle, live GPS and the guidance look-ahead.
    check_for_new_command() keeps it preemptable/concurrent-safe exactly
    like the search/split loops. Returns once every selected task is gone
    (goal missions complete) or on an explicit stop; a persistent loiter
    (guided_circle / autogoal) keeps it running until stop/preempt.
    MissionPreempted propagates to the caller.
    """
    if not state.master_flag:
        return
    gui = viz.Gui(state.s)
    my_seq = state.last_seq
    try:
        while True:
            time.sleep(config.SLEEP_TIMES.get(state.num_bots, 0.01))
            check_for_new_command(my_seq)
            goals_by_bot = [None] * len(state.s.swarm)
            circles_by_bot = [None] * len(state.s.swarm)
            planned_paths_by_bot = [None] * len(state.s.swarm)
            with state.active_goal_tasks_lock:
                still_active = False
                for i in selected_indexes:
                    task = state.active_goal_tasks.get(i)
                    if task is None:
                        continue
                    still_active = True
                    if task.get("type") == "guided_circle":
                        circles_by_bot[i] = task.get("circle_points")
                    else:
                        goals = task.get("goals", [])
                        goal_index = task.get("goal_index", 0)
                        planned_paths_by_bot[i] = goals
                        if goal_index < len(goals):
                            goals_by_bot[i] = goals[goal_index]
            gps_pts = live_gps_plot_points()
            gui.show_goals(goals_by_bot)
            gui.show_circles(circles_by_bot)
            gui.show_planned_path(planned_paths_by_bot)
            gui.show_gps_positions(gps_pts)
            gui.show_lookahead(
                [state.uav_lookahead_points.get(k) for k in range(len(state.s.swarm))],
                gps_pts,
            )
            gui.update()
            # print_sim_vs_real_latlon(selected_indexes, label=label)
            if not still_active:
                break
            if state.index == b"stop":
                break
    finally:
        # MissionPreempted is raised by check_for_new_command above and
        # propagates straight out of this loop, so without a finally the
        # figure leaked on every preempted mission -- the two inline
        # gui.close() calls only covered the two clean exits.
        #
        # A leaked figure keeps live tkinter objects alive until the garbage
        # collector finalizes them, and the GC runs on whatever thread happens
        # to trigger it -- typically the background _goal_task_runner. Tk's
        # Variable.__del__ then calls into the interpreter from a non-GUI
        # thread and raises "RuntimeError: main thread is not in main loop",
        # printed as "Exception ignored in: <function Variable.__del__>".
        # Closing here keeps teardown deterministic and on the main thread.
        gui.close()


# ---------------------------------------------------------------------------
# 'autogoal' -- the "Automate Goals" button
# ---------------------------------------------------------------------------


def _autogoal_direction_sign(direction_raw):
    """Accept either the numeric sign the server already sends (1 / -1) or
    a raw 'ClockWise ...' / 'Anti ...' string, and return 1 or -1."""
    try:
        return 1 if int(float(direction_raw)) >= 0 else -1
    except (TypeError, ValueError):
        return -1 if str(direction_raw).strip().lower().startswith("a") else 1


def _autogoal_centers_to_sim_xy(latlon_list):
    """generate_loiter_goal_points output (real lat/lon) -> local sim
    frame (x/2, y/2), the same conversion run_goal_command uses on its
    goal points."""
    xy = []
    for lat, lon in latlon_list:
        x, y = locatePosition.geoToCart(
            state.origin, config.END_DISTANCE, [float(lat), float(lon)]
        )
        xy.append((x / 2, y / 2))
    return xy


def _parse_autogoal(msg_parts):
    """autogoal_<centersJson>_<direction>_<radius>_<idsJson>_<bearing>_<safety>"""
    centers = json.loads(msg_parts[1])
    direction = _autogoal_direction_sign(msg_parts[2])
    radius = float(msg_parts[3])
    selected_uav_ids = parse_selected_uav_ids(
        msg_parts[4] if len(msg_parts) > 4 else None
    )
    bearing_deg = (
        float(msg_parts[5])
        if len(msg_parts) > 5 and msg_parts[5]
        else DEFAULT_BEARING_DEG
    )
    safety_margin_m = (
        float(msg_parts[6])
        if len(msg_parts) > 6 and msg_parts[6]
        else DEFAULT_SAFETY_MARGIN_M
    )
    # The operator drops a single point; centers[0] is that point as
    # [lat, lon] (swarm.py autogoal_socket reverses it from the GCS's
    # [lon, lat], same as goal_socket).
    first = centers[0] if centers and isinstance(centers[0], (list, tuple)) else centers
    goal_lat, goal_lon = float(first[0]), float(first[1])
    return (
        goal_lat,
        goal_lon,
        direction,
        radius,
        selected_uav_ids,
        bearing_deg,
        safety_margin_m,
    )


def _apply_autogoal(
    goal_lat,
    goal_lon,
    direction,
    radius,
    selected_indexes,
    bearing_deg,
    safety_margin_m,
):
    """Shared by the foreground handler, the concurrent handler, and
    regenerate_autogoal: build per-UAV loiter centers and (re)assign the
    background tasks. Also stashes the inputs on state so a later
    radius-only change can regenerate without the operator re-selecting."""
    num_uavs = len(selected_indexes)
    if num_uavs < 1 or radius <= 0:
        print("[autogoal] nothing to do -- num_uavs", num_uavs, "radius", radius)
        return False
    centers_latlon = loiter_goal_latlon_list(
        goal_lat, goal_lon, num_uavs, radius, bearing_deg, safety_margin_m
    )
    # Every autogoal path lands here -- foreground, concurrent, and the
    # regenerate triggered by an in-flight 'autogoalrad' radius change -- so
    # one gate here covers all three. Each UAV gets its own circle, so each is
    # checked against its own centre rather than the operator's single point.
    problems = []
    for index, center in zip(selected_indexes, centers_latlon):
        ok, msgs = terrain_gate.check_goals(
            [index],
            [(float(center[0]), float(center[1]))],
            radius,
            label="autogoal",
        )
        if not ok:
            problems.extend(msgs)
    if problems:
        print("[autogoal] refused -- terrain above commanded altitude")
        return False

    per_uav_xy = _autogoal_centers_to_sim_xy(centers_latlon)
    assign_autogoal_tasks(selected_indexes, per_uav_xy, radius, direction)
    state.autogoal_params = {
        "goal_lat": goal_lat,
        "goal_lon": goal_lon,
        "direction": direction,
        "radius": radius,
        "bearing_deg": bearing_deg,
        "safety_margin_m": safety_margin_m,
        "selected_indexes": list(selected_indexes),
    }
    print(
        "[autogoal] centers",
        centers_latlon,
        "radius",
        radius,
        "bearing",
        bearing_deg,
        "margin",
        safety_margin_m,
    )
    return True


def regenerate_autogoal(
    new_radius=None, new_bearing_deg=None, new_safety_margin_m=None
):
    """Rebuild the "Automate Goals" layout from the last-applied inputs,
    overriding only what is passed. Called when the loiter radius is
    changed on board mid-flight (see the 'autogoalrad' command) -- the
    circles re-size and re-space and every UAV is re-tasked to its new
    center, all while flying."""
    params = getattr(state, "autogoal_params", None)
    if not params:
        print("[autogoal] regenerate skipped -- no active Automate Goals layout")
        return False
    radius = float(new_radius) if new_radius is not None else params["radius"]
    bearing_deg = (
        float(new_bearing_deg) if new_bearing_deg is not None else params["bearing_deg"]
    )
    safety_margin_m = (
        float(new_safety_margin_m)
        if new_safety_margin_m is not None
        else params["safety_margin_m"]
    )
    # Re-resolve indexes against the current fleet in case a UAV was
    # added/removed since the layout was first assigned.
    selected_indexes = [
        i for i in params["selected_indexes"] if i < len(state.pos_array)
    ] or params["selected_indexes"]
    return _apply_autogoal(
        params["goal_lat"],
        params["goal_lon"],
        params["direction"],
        radius,
        selected_indexes,
        bearing_deg,
        safety_margin_m,
    )


def handle_concurrent_autogoal_command(command_data):
    """Concurrent (UAV-subset) 'autogoal' -- mirrors
    handle_concurrent_goal_command: accepted without preempting whatever
    the rest of the swarm is doing, as long as a subset was named."""
    if not command_data.startswith(b"autogoal_"):
        return False
    try:
        msg_parts = command_data.decode("utf-8").split("_")
        if len(msg_parts) < 5:
            return False
        (
            goal_lat,
            goal_lon,
            direction,
            radius,
            selected_uav_ids,
            bearing_deg,
            safety_margin_m,
        ) = _parse_autogoal(msg_parts)
        if not selected_uav_ids:
            return False
        selected_indexes = selected_swarm_indexes(selected_uav_ids)
        ok = _apply_autogoal(
            goal_lat,
            goal_lon,
            direction,
            radius,
            selected_indexes,
            bearing_deg,
            safety_margin_m,
        )
        if ok:
            print(
                "[concurrent autogoal] accepted during running mission",
                selected_uav_ids,
            )
        return ok
    except Exception as e:
        print("[concurrent autogoal] failed", e)
        return False


def run_autogoal_command(data):
    """Foreground 'autogoal' dispatch handler. Returns True so main.py
    `continue`s the dispatch iteration, same contract as run_goal_command.

    Flying is owned by the background runner from assignment onward; the
    _plot_goal_tasks loop below is the read-only visualizer for it (per-UAV
    center, planned leg, and the loiter circle once each UAV arrives),
    shared with run_goal_command. The autogoal tasks never go inactive
    (each UAV loiters forever), so the loop runs until stop/preempt."""
    if not data.startswith(b"autogoal_"):
        return
    state.index = "data"
    try:
        msg_parts = data.decode("utf-8").split("_")
        (
            goal_lat,
            goal_lon,
            direction,
            radius,
            selected_uav_ids,
            bearing_deg,
            safety_margin_m,
        ) = _parse_autogoal(msg_parts)
        selected_indexes = selected_swarm_indexes(selected_uav_ids)
        print(
            "[autogoal] selected_uav_ids",
            selected_uav_ids,
            "selected_indexes",
            selected_indexes,
        )
        _apply_autogoal(
            goal_lat,
            goal_lon,
            direction,
            radius,
            selected_indexes,
            bearing_deg,
            safety_margin_m,
        )
        _plot_goal_tasks(selected_indexes, label="autogoal")
        return True
    except MissionPreempted:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        print("autogoal exception", e)


def run_autogoal_radius_command(data):
    """'autogoalrad_<radius>_<idsJson>' -- an on-board loiter-radius change
    (sent additively by the server's existing 'rad' settings handler).
    Regenerates the active Automate Goals layout at the new radius; a
    no-op if no such layout is running."""
    if not data.startswith(b"autogoalrad_"):
        return
    try:
        parts = data.decode("utf-8").split("_")
        new_radius = float(parts[1])
        if regenerate_autogoal(new_radius=new_radius):
            # This command preempted the autogoal plot loop to get here;
            # re-enter it on the regenerated layout so the visualizer keeps
            # updating (a purely-background loiter doesn't redraw itself).
            params = getattr(state, "autogoal_params", None) or {}
            _plot_goal_tasks(params.get("selected_indexes", []), label="autogoal")
        return True
    except MissionPreempted:
        raise
    except Exception as e:
        print("autogoalrad exception", e)
