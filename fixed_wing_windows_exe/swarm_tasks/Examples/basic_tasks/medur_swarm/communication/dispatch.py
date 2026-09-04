"""Concurrent-command interception: lets a goal/search/split/different (and
add/remove) command targeting a specific UAV subset take effect immediately,
without preempting whatever mission the rest of the swarm is currently
flying. Any other newer command (or one with no subset, i.e. targeting the
whole swarm) still preempts the running foreground mission via
MissionPreempted."""

from medur_swarm import state
from medur_swarm.communication.sockets import pending_command


class MissionPreempted(Exception):
    """Raised from inside a mission-flying loop (by
    check_for_new_command) when a command newer than the one it started
    with has arrived on sock2 mid-mission. Carries the preempting
    command so the outer dispatch loop can process it immediately
    instead of waiting for the interrupted mission to finish."""

    def __init__(self, data, address):
        self.data = data
        self.address = address


def check_for_new_command(started_seq):
    """Call once per iteration inside an interruptible mission loop.
    Selected goal/search/split (and add/remove) commands targeting a
    specific UAV subset are handled concurrently without preempting the
    running mission; any other newer command (or one with no subset,
    i.e. targeting the whole swarm) still preempts it via
    MissionPreempted."""
    # Imported lazily to avoid a circular import: every tasks/*.py module
    # (and uav/management.py) calls back into this function from their own
    # foreground mission loops, while this function needs to call into
    # them. By the time any mission loop actually runs, main.py has
    # already finished importing every module below, so this resolves
    # exactly like a shared-module-global lookup would have in the
    # original single-file script.
    from medur_swarm.tasks.goal import (
        handle_concurrent_autogoal_command,
        handle_concurrent_goal_command,
    )
    from medur_swarm.tasks.search import handle_concurrent_search_command
    from medur_swarm.tasks.split import handle_concurrent_split_command
    from medur_swarm.tasks.altitude import handle_concurrent_different_command
    from medur_swarm.uav.management import (
        handle_concurrent_add_command,
        handle_concurrent_remove_command,
    )

    if pending_command.seq > started_seq:
        if pending_command.seq > state.handled_concurrent_command_seq and (
            handle_concurrent_goal_command(pending_command.data)
            or handle_concurrent_autogoal_command(pending_command.data)
            or handle_concurrent_search_command(pending_command.data)
            or handle_concurrent_split_command(pending_command.data)
            or handle_concurrent_different_command(pending_command.data)
            or handle_concurrent_remove_command(pending_command.data)
            or handle_concurrent_add_command(pending_command.data)
        ):
            state.handled_concurrent_command_seq = pending_command.seq
            state.last_seq = pending_command.seq
            return None
        if pending_command.seq <= state.handled_concurrent_command_seq:
            return None
        raise MissionPreempted(pending_command.data, pending_command.address)
