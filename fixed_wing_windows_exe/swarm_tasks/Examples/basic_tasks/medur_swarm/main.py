"""Entry point: startup sequence (sockets/threads, vehicle connection,
simulation bring-up) followed by the main command-dispatch loop.

The dispatch loop is a flat, non-exclusive sequence of `if` checks against
whatever command last arrived on sock2 -- exactly as in the original
single-file script, preserved so that:
  * more than one handler can fire for the same message (e.g. 'remove'
    falls through into whatever flag-driven block follows it),
  * a handler that ends with an unconditional "abort this iteration" (the
    original's inline `continue`) returns True, and main.py's loop
    `continue`s immediately -- see tasks/goal.py and tasks/split.py's
    docstrings for exactly which paths do this,
  * everything else falls through in order, matching the original.
"""

import time
import traceback

from swarm_tasks.simulation import simulation as sim

import swarm_tasks

from medur_swarm import config, state
from medur_swarm.utils import read_origin
from medur_swarm.communication import sockets
from medur_swarm.communication.dispatch import MissionPreempted
from medur_swarm.uav import connection as uav_connection
from medur_swarm.uav import management as uav_management
from medur_swarm.uav.telemetry import sync_swarm_with_telemetry
from medur_swarm.tasks import (
    admin,
    altitude,
    formation,
    goal,
    home,
    navigate,
    open_group,
    runner,
    search,
    specific_bot_goal,
    split,
)

swarm_tasks.utils.robot.DEFAULT_NEIGHBOURHOOD_VAL = 7
swarm_tasks.utils.robot.DEFAULT_SIZE = 0.4
swarm_tasks.utils.robot.MAX_SPEED = 1.5


def _load_origin():
    try:
        state.origin = read_origin(config.RECTANGLES_PATH)
        print("Origin loaded from rectangles.yaml:", state.origin)
    except Exception as e:
        state.origin = None
        print(
            f"No rectangles.yaml yet at {config.RECTANGLES_PATH} ({e}) -- origin will be set once a fence is drawn"
        )


def _bring_up_master():
    """Connect every vehicle, wait for all of them to be armed and above
    10 m, then take the first GPS fix. Mirrors the original script's
    top-level `if master_flag:` block exactly."""
    if not state.master_flag:
        return
    uav_connection.vehicle_connection()
    uav_management.register_active_uavs()
    while True:
        all_armed = [False] * len(
            state.vehicles
        )  # Assume all vehicles are armed initially
        for i, vehicle in enumerate(state.vehicles):
            alt = vehicle.location.global_relative_frame.alt
            if vehicle.armed and alt is not None and alt > 10:
                all_armed[i] = True
        if all(all_armed):
            uav_connection.fetch_location()
            break
        time.sleep(0.1)


def _bring_up_simulation():
    while True:
        if state.uav_home_pos != []:
            print("num_bots", state.num_bots, state.uav_home_pos)
            state.s = sim.Simulation(
                state.uav_home_pos,
                num_bots=len(state.pos_array),
                env_name=state.file_name,
            )
            runner.start_goal_task_thread()
            break
        else:
            pass


def _dispatch_one(data):
    """Runs every dispatch-loop handler for one already-fetched command,
    in the original's exact order. Returns True if the caller must
    `continue` the outer while(1) immediately (an original inline
    `continue`), matching goal.py/split.py's own contract."""
    runner._reset_mission_state()
    print("!!msg", data)
    if data == b"stop":
        runner.clear_all_active_tasks()
        return True
    sync_swarm_with_telemetry()

    admin.apply_origin_update(data)
    admin.reload_geofence(data)
    admin.store_uav_pos(data)
    admin.lock_home_position(data)
    admin.refresh_origin_and_rebuild_sim(data)
    admin.run_takeoff_command(data)

    uav_management.run_remove_command(data)
    uav_management.run_add_command(data)

    specific_bot_goal.run_specific_bot_goal_command(data)
    open_group.run_group_split_command(data)

    if goal.run_autogoal_command(data):
        return True

    if goal.run_autogoal_radius_command(data):
        return True

    if goal.run_goal_command(data):
        return True

    formation.run_guided_circle_command(data)
    formation.run_same_altitude_command(data)

    if data.startswith(b"different"):
        altitude.apply_different_heights(data.decode("utf-8"))
        return True

    formation.run_loiter_point_command(data)
    navigate.run_grid_path_planning_command(data)
    navigate.run_navigate_command(data)
    search.run_search_command(data)
    split.run_split_or_specific_split_command(data)
    home.run_home_command(data)
    home.run_home_return_final_leg(data)
    return False


def run():
    _load_origin()
    sockets.start_listener_threads()
    _bring_up_master()
    _bring_up_simulation()

    # _next_data/_next_address carry a preempting command straight into the
    # next iteration (see the MissionPreempted except-clause below) so it's
    # dispatched immediately, with no idle wait for a fresh mailbox seq.
    _next_data, _next_address = None, None
    state.last_seq = 0
    while 1:
        if state.master_flag:
            state.num_bots = len(state.vehicles)
        else:
            state.num_bots = len(state.pos_array)
        try:
            if _next_data is not None:
                data, address = _next_data, _next_address
                _next_data, _next_address = None, None
            else:
                while sockets.pending_command.seq <= state.last_seq:
                    time.sleep(0.01)
                data = sockets.pending_command.data
                address = sockets.pending_command.address
                state.last_seq = sockets.pending_command.seq

            if _dispatch_one(data):
                continue
        except MissionPreempted as preempt:
            # A mission loop noticed a newer command mid-flight (via
            # check_for_new_command) and unwound here instead of running to
            # completion. Dispatch the preempting command immediately on the
            # next iteration -- no idle wait for a fresh mailbox seq.
            _next_data, _next_address = preempt.data, preempt.address
            state.last_seq = sockets.pending_command.seq
        except Exception as e:
            # Previously a bare `pass` here -- any exception inside a mission
            # loop (search/split/goal/home/...) silently killed the mission for
            # every bot at once with zero trace, which is why a mid-mission
            # failure (e.g. an index mismatch after a bot removal) looked like
            # the swarm just stopped for no reason. Log it so the real cause is
            # visible instead of only the flags being reset.
            print("[mission] aborted by exception:", repr(e))
            traceback.print_exc()
            if state.search_flag:
                state.search_flag = False
            if state.split_flag:
                state.split_flag = False
            if state.start_flag:
                state.start_flag = False
            if state.circle_formation_flag:
                state.circle_formation_flag = False
            if state.home_flag:
                state.home_flag = False
            if state.home_goto_flag:
                state.home_goto_flag = False


if __name__ == "__main__":
    run()
