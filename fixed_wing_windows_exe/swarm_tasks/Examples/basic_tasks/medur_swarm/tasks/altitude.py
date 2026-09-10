"""'different' command: per-bot altitude re-staggering, applied either
live (idle bots get an explicit background altitude task) or picked up on
the fly by whatever task is already driving a busy bot."""

from swarm_tasks.modules.dispersion import disp_field
from swarm_tasks.tasks import area_coverage as cvg

from medur_swarm import state, terrain_gate
from medur_swarm.utils import parse_selected_uav_ids, selected_swarm_indexes
from medur_swarm.uav.guidance import _drive_vehicle_towards


def apply_different_heights(decoded_index):
    """Parses a 'different,{height},{step}[,{ids}]' command and updates the
    shared different_height[] array for the targeted bot indexes (or every
    connected UAV if no ids given). Height is computed from each bot's real
    pos_array index (height + step*bot_index), not its position within the
    selection, so a partial re-stagger stays consistent with the whole
    fleet's existing layering instead of restarting from the base altitude.

    Critically, this never touches (x,y)/task state for bots that already
    have an active goal/mission/guided_circle task -- their own
    _drive_vehicle_towards() call reads different_height[i] fresh every
    tick, so updating it here alone re-targets their altitude on their very
    next drive tick with zero interruption to whatever they were already
    flying. The same holds for a bot being flown by a foreground
    search/split/specificsplit loop (tracked in state.foreground_mission_indexes)
    -- that loop's own simple_goto reads different_height[i] fresh every tick.
    Only a bot that is neither gets an explicit altitude task assigned, since
    nothing would otherwise command it to actually climb or descend."""
    parts = decoded_index.split(",", 3)
    height = int(parts[1])
    step = int(parts[2])
    selected_uav_raw = parts[3] if len(parts) > 3 else None
    selected_uav_ids = parse_selected_uav_ids(selected_uav_raw)
    selected_indexes = selected_swarm_indexes(selected_uav_ids)
    # Terrain check on the new ladder, ADVISORY ONLY -- it reports and the
    # command proceeds regardless. Raising altitude is how an operator clears a
    # terrain-blocked goal, so refusing the climb would trap the fleet: the
    # goal is refused for being under terrain, the fix is refused too, and
    # refusing leaves them at the OLD, lower altitude. Refusal belongs on the
    # goal command, which is what actually flies them at the terrain.
    proposed = {
        bot_index: height + step * bot_index
        for bot_index in selected_indexes
        if bot_index < len(state.different_height)
    }
    terrain_gate.check_altitude_change(proposed, label="different")

    state.same_alt_flag = False
    for bot_index in selected_indexes:
        if bot_index < len(state.different_height):
            state.different_height[bot_index] = height + step * bot_index
    print(
        "[different] updated different_height",
        state.different_height,
        "for indexes",
        selected_indexes,
    )
    with state.active_goal_tasks_lock:
        busy_indexes = set(state.active_goal_tasks.keys())
    # A foreground search/split/specificsplit loop flies its bots itself (they
    # are held out of active_goal_tasks on purpose), and already re-reads
    # different_height[i] every tick when it issues simple_goto -- so the array
    # update above is all those bots need. Assigning them a separate altitude
    # task instead makes the foreground loop treat them as "diverted" and drop
    # them from the mission permanently, so count them as busy here.
    busy_indexes |= set(state.foreground_mission_indexes)
    idle_indexes = [i for i in selected_indexes if i not in busy_indexes]
    if idle_indexes:
        assign_altitude_tasks(idle_indexes)
    return True


def assign_altitude_tasks(selected_indexes):
    with state.active_goal_tasks_lock:
        for bot_index in selected_indexes:
            state.active_goal_tasks[bot_index] = {
                "type": "altitude",
            }
    print(
        "[altitude-task] assigned (idle bots climbing/descending in place)",
        selected_indexes,
    )


def handle_concurrent_different_command(command_data):
    if not command_data.startswith(b"different"):
        return False
    try:
        return apply_different_heights(command_data.decode("utf-8"))
    except Exception as e:
        print("[concurrent different] failed", e)
        return False


def _drive_altitude_task(i, b, task, completed):
    """Holds the bot at its current (x,y) -- via a goal fixed at its own
    position, plus real disp_field repulsion so several idle bots
    re-staging altitude at once don't drift into each other -- while it
    climbs/descends to its just-updated different_height[i]. Completes
    (frees the bot back to fully idle) once the real vehicle reports being
    within tolerance of the target altitude, mirroring the original
    blocking loop's own completion check."""
    goal_position = (b.x, b.y)
    cmd = cvg.goal_area_cvg(i, b, goal_position)
    cmd += disp_field(b, neighbourhood_radius=100)
    cmd.exec(b)
    # The bot's own position must be passed EXPLICITLY. Calling this with no
    # guidance_position means "no target this tick", which falls back to
    # state.uav_lookahead_points[i] -- the last target some earlier command
    # left behind -- and commands nothing at all when there isn't one. A bot
    # that has not flown a goal yet this session therefore got no simple_goto,
    # so the aircraft was never told to change altitude and simply never
    # climbed. Passing (b.x, b.y) is what the docstring above already says
    # this does: hold station here and change height.
    _drive_vehicle_towards(i, b, (b.x, b.y))
    if state.master_flag and i < len(state.vehicles) and i < len(state.different_height):
        try:
            current_alt = state.vehicles[i].location.global_relative_frame.alt
        except Exception:
            current_alt = None
        if current_alt is not None and abs(current_alt - state.different_height[i]) <= 1.5:
            completed.append(i)
            print("[altitude-task] reached target altitude for UAV", state.pos_array[i])
