"""Add/remove UAV: keeping pos_array/vehicles/s/different_height/uav_registry
in lock-step whenever a UAV joins or leaves the connected fleet mid-mission."""

import swarm_tasks.controllers.potential_field as potf
import locatePosition
from dronekit import connect, LocationGlobalRelative

from medur_swarm import config, state
from medur_swarm.uav.connection import connection_string_for_sysid
from medur_swarm.uav.telemetry import _resync_bot_position


def register_active_uavs():
    for idx, sys_id in enumerate(state.pos_array):
        entry = state.uav_registry.setdefault(int(sys_id), {})
        entry["sys_id"] = int(sys_id)
        entry["active"] = True
        entry.setdefault("original_index", idx)
        entry["index"] = idx
        entry["connection"] = (
            connection_string_for_sysid(int(sys_id))
            if int(sys_id) in config.PORT_DICT
            else entry.get("connection")
        )
        if idx < len(state.vehicles):
            entry["vehicle"] = state.vehicles[idx]
        state.uav_task_state.setdefault(int(sys_id), "IDLE")


def rebuild_uav_home_positions():
    state.uav_home_pos = []
    for vehicle in state.vehicles:
        lat = vehicle.location.global_relative_frame.lat
        lon = vehicle.location.global_relative_frame.lon
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
        state.uav_home_pos.append((x / 2, y / 2))
    state.num_bots = len(state.pos_array)
    return state.uav_home_pos


def normalize_active_uav_order():
    if len(state.pos_array) != len(state.vehicles):
        print(
            "[uav-order] skipped: pos_array/vehicles length mismatch",
            state.pos_array,
            len(state.vehicles),
        )
        return False
    combined = []
    for idx, sys_id in enumerate(state.pos_array):
        height = state.different_height[idx] if idx < len(state.different_height) else 300
        pop_flag = state.pop_flag_arr[idx] if idx < len(state.pop_flag_arr) else 1
        combined.append((int(sys_id), state.vehicles[idx], height, pop_flag))
    combined.sort(key=lambda item: item[0])
    state.pos_array[:] = [item[0] for item in combined]
    state.vehicles[:] = [item[1] for item in combined]
    state.different_height[:] = [item[2] for item in combined]
    state.pop_flag_arr[:] = [item[3] for item in combined]
    rebuild_uav_home_positions()
    register_active_uavs()
    print("[uav-order] active order normalized", state.pos_array)
    return True


def add_uav_to_swarm(sys_id):
    try:
        # The topology and active task indexes must stay in the same frame.
        # active_goal_tasks_lock is initialized before commands can arrive.
        with state.swarm_topology_lock, state.active_goal_tasks_lock:
            sys_id = int(sys_id)
            connection_str = connection_string_for_sysid(sys_id)
            print("[add-link] connection", sys_id, connection_str)
            if sys_id in state.pos_array:
                idx = state.pos_array.index(sys_id)
                try:
                    state.vehicles[idx].close()
                except Exception:
                    pass
                state.vehicles[idx] = connect(
                    connection_str, baud=115200, heartbeat_timeout=30
                )
                state.uav_registry.setdefault(sys_id, {})["vehicle"] = state.vehicles[idx]
                state.uav_registry[sys_id]["active"] = True
                state.uav_registry[sys_id]["index"] = idx
                state.uav_task_state[sys_id] = "IDLE"
                # The UAV may have been physically flown (GUIDED fly-to or manual
                # RC) while disconnected -- without this, s.swarm[idx].x/y is
                # left exactly wherever it was before removal, so the sim bot
                # reappears stuck at the old position instead of where the
                # aircraft actually is now.
                _resync_bot_position(idx, force=True)
                print("[add-link] reconnected active UAV", sys_id, "index", idx)
                return True
            vehicle = connect(connection_str, baud=115200, heartbeat_timeout=30)
            lat = vehicle.location.global_relative_frame.lat
            lon = vehicle.location.global_relative_frame.lon
            x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
            insert_index = len(state.pos_array)
            # A reconnected UAV is appended so an active mission's compacted
            # indexes are not disturbed. It must nevertheless retain the
            # altitude it had before removal, rather than inheriting the last
            # active UAV's (often much higher) altitude.
            previous_entry = state.uav_registry.get(sys_id, {})
            restored_height = previous_entry.get("different_height")
            state.pos_array.append(sys_id)
            state.vehicles.append(vehicle)
            state.s.add_bot(insert_index, (x / 2, y / 2))
            if restored_height is not None:
                state.different_height.append(restored_height)
            elif state.different_height:
                state.different_height.append(state.different_height[-1])
            else:
                state.different_height.append(300)
            state.pop_flag_arr.append(1)
            rebuild_uav_home_positions()
            state.uav_registry[sys_id] = {
                "sys_id": sys_id,
                "active": True,
                "index": insert_index,
                "connection": connection_str,
                "vehicle": vehicle,
            }
            state.uav_task_state[sys_id] = "IDLE"
            print(
                "[add-link] added UAV as IDLE",
                sys_id,
                "index",
                insert_index,
                "pos_array",
                state.pos_array,
            )
            return True
    except Exception as e:
        print("[add-link] failed", sys_id, e)
        return False


def remove_uav_from_swarm(remove_bot_num):
    from medur_swarm.tasks.runner import remove_goal_task_index

    try:
        # Hold the task lock for the *whole* compaction. In particular,
        # s.remove_bot(), vehicles.pop(), and task-key shifting must appear as
        # one atomic topology change to the background driver.
        with state.swarm_topology_lock, state.active_goal_tasks_lock:
            remove_bot_num = int(remove_bot_num)
            if remove_bot_num not in state.pos_array:
                print("[remove-link] not found", remove_bot_num, "pos_array", state.pos_array)
                return False
            pop_bot_index = state.pos_array.index(remove_bot_num)
            state.remove_bot_index = pop_bot_index
            print("[remove-link] removing", remove_bot_num, "at index", pop_bot_index)
            entry = state.uav_registry.setdefault(remove_bot_num, {})
            entry["sys_id"] = remove_bot_num
            entry.setdefault("original_index", pop_bot_index)
            if pop_bot_index < len(state.different_height):
                entry["different_height"] = state.different_height[pop_bot_index]
            entry["active"] = False
            entry["index"] = None
            entry["connection"] = (
                connection_string_for_sysid(remove_bot_num)
                if remove_bot_num in config.PORT_DICT
                else entry.get("connection")
            )
            state.uav_task_state[remove_bot_num] = "IDLE"
            state.remove_bot_flag = True
            state.remove_bot_array.append(pop_bot_index)
            state.pos_array.pop(pop_bot_index)
            try:
                state.vehicles[pop_bot_index].close()
            except Exception as e:
                print("[remove-link] vehicle close failed", e)
            state.vehicles.pop(pop_bot_index)
            state.s.remove_bot(pop_bot_index)
            remove_goal_task_index(pop_bot_index)
            if pop_bot_index < len(state.different_height):
                state.different_height.pop(pop_bot_index)
            if pop_bot_index < len(state.pop_flag_arr):
                state.pop_flag_arr.pop(pop_bot_index)
            state.num_bots = len(state.pos_array)
            state.uav_home_pos = []
            for vehicle in state.vehicles:
                lat = vehicle.location.global_relative_frame.lat
                lon = vehicle.location.global_relative_frame.lon
                x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
                state.uav_home_pos.append((x / 2, y / 2))
            state.remove_flag = False
            state.uav_removed = True
            state.pop_bot_index = None
            register_active_uavs()
            print("[remove-link] remaining pos_array", state.pos_array, "num_bots", state.num_bots)
            return True
    except Exception as e:
        print("[remove-link] failed", remove_bot_num, e)
        return False


def handle_concurrent_remove_command(command_data):
    if not command_data.startswith(b"remove"):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        f, remove_bot_num = decoded_index.split(",", 1)
        return remove_uav_from_swarm(remove_bot_num)
    except Exception as e:
        print("[concurrent remove] failed", e)
        return False


def handle_concurrent_add_command(command_data):
    if not command_data.startswith(b"add"):
        return False
    try:
        decoded_index = command_data.decode("utf-8")
        f, sys_id = decoded_index.split(",", 1)
        return add_uav_to_swarm(sys_id)
    except Exception as e:
        print("[concurrent add] failed", e)
        return False


def run_remove_command(data):
    """Foreground 'remove' dispatch-loop handler ("Remove UAV"). Falls
    through unconditionally -- the original set `data = b"index"` and let
    execution continue into whatever block comes next in the same
    iteration (matching the non-exclusive if-chain design), never
    aborting the loop early."""
    if not (data.startswith(b"remove") or state.remove_flag):
        return
    decoded_index = data.decode("utf-8")
    f, remove_bot_num = decoded_index.split(",", 1)
    print("remove_bot_num", remove_bot_num, state.pos_array)
    remove_uav_from_swarm(remove_bot_num)


def run_add_command(data):
    """Foreground 'add' dispatch-loop handler ("Add UAV"). Same
    fall-through behavior as run_remove_command."""
    if not data.startswith(b"add"):
        return
    decoded_index = data.decode("utf-8")
    f, sys_id = decoded_index.split(",", 1)
    add_uav_to_swarm(sys_id)


def remove_vehicle():
    """Legacy blocking removal path. Not reachable from the current
    dispatch loop or any concurrent-command handler (both now go through
    remove_uav_from_swarm), but vehicle_lost_flag/remove_vehicle() calls
    inside the search/split/home mission loops (tasks/*.py) still reference
    this exact function -- kept verbatim."""
    index = state.pos_array[state.lost_vehicle_num - 1]
    print(index, "index")
    print("lost_vehicle_num", state.lost_vehicle_num, index, state.pos_array)
    state.vehicle_lost_flag = False
    pop_flag = True
    # print ("msg", index)
    pop_bot_index = None
    for l in range(0, len(state.pos_array)):
        if int(index) == state.pos_array[l]:
            pop_bot_index = l
            print("pop_bot_index,l", pop_bot_index, l)
            break
    state.pos_array.pop(pop_bot_index)
    state.vehicles.pop(pop_bot_index)
    state.s.remove_bot(pop_bot_index)
    print(state.num_bots)
    print("!!!!!!!!!!!!pop_flag_arr!!!!!!!!!!!", state.pop_flag_arr)
    print("pop index", pop_bot_index)
    state.same_alt_flag = False
    state.uav_home_pos = []
    for i, vehicle in enumerate(state.vehicles):
        lat = vehicle.location.global_relative_frame.lat
        lon = vehicle.location.global_relative_frame.lon
        x, y = locatePosition.geoToCart(state.origin, config.END_DISTANCE, [lat, lon])
        state.different_height[i] = state.different_height[i] + 2
        state.uav_home_pos.append((x / 2, y / 2))
    print("uav_home_pos", state.uav_home_pos)
    state.remove_flag = False
    state.uav_removed = True
    while True:
        for i, b in enumerate(state.s.swarm):
            cmd = potf.velocity(
                b.get_position(), b.sim, weights=potf.field_weights, order=2, max_dist=5
            )
            cmd.exec(b)
            if state.master_flag:
                value = [b.x * 2, b.y * 2]
                lat, lon = locatePosition.cartToGeo(state.origin, config.END_DISTANCE, value)

                if state.same_alt_flag:
                    point1 = LocationGlobalRelative(lat, lon, state.same_height)
                else:
                    point1 = LocationGlobalRelative(lat, lon, state.different_height[i])
                state.vehicles[i].simple_goto(point1)
                alt = [0] * state.num_bots
                alt_count = [0] * state.num_bots
                for i, vehicle in enumerate(state.vehicles):
                    print("vehicle", vehicle, state.num_bots)
                    alt[i] = vehicle.location.global_relative_frame.alt
                    print("alt[vehicle]", alt[i])
                    if state.different_height[i] - 1.5 <= alt[i] <= state.different_height[i] + 1.5:
                        alt_count[i] = 1
                        print(alt_count, "alt_count")
                        if all(count == 1 for count in alt_count):
                            print("Reached target altitude")
                            return index
