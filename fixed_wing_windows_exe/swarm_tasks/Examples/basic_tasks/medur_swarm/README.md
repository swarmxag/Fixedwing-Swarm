# medur_swarm

Fixed-wing swarm ground-control script, split out of the original
single-file `medur_fixed_wing.py` into modules organized by responsibility.
The entry point (`../medur_fixed_wing.py`) is a thin wrapper that just
bootstraps `sys.path` and calls `medur_swarm.main.run()`.

This document explains what each file does. See each module's own
docstrings/comments for the "why" behind specific decisions.

## Entry point

- **`../medur_fixed_wing.py`** — Adds `swarm_tasks` to `sys.path` and calls
  `medur_swarm.main.run()`. Nothing else lives here.

## Top level

| File | What it does |
|---|---|
| `config.py` | Constants that never change at runtime: MAVLink port map, heartbeat IP list, home altitudes, the geofence file path, sleep-time table, and all the virtual-leader-pacing/waypoint-radius tuning numbers. |
| `state.py` | Every piece of shared, mutable runtime state (connected vehicles, `pos_array`, `origin`, the simulation object `s`, altitude arrays, all the mission flags like `search_flag`/`split_flag`/`home_flag`, the background task dict, etc.) as plain attributes on one module. Every other file does `from medur_swarm import state` and reads/writes `state.x` — never `from state import x` — because several of these get wholesale replaced (`state.pos_array = [...]`), and that only stays visible everywhere if every reader goes through the module object. |
| `utils.py` | Small stateless-ish helpers: reading the origin from `rectangles.yaml`, generating circle points, reading one line of a mission CSV, parsing a UAV-id selection off the wire, and the drone/point redistribution math (`allocate_drones`) used when a UAV is removed mid-search. |
| `main.py` | Startup sequence (load origin → start listener threads → connect vehicles & wait for armed+altitude → build the Simulation → start the background task thread) and the main dispatch loop that reads each command off the mailbox and runs every command handler in the original's exact order. |

## `communication/`

| File | What it does |
|---|---|
| `sockets.py` | Owns the two UDP sockets (`sock2` for commands, `sock3` for collision/heartbeat), the thread-safe command mailbox, and the two background listener threads (`vehicle_collision_moniter_receive`, `_command_listener`). |
| `dispatch.py` | `MissionPreempted` (the exception a running mission raises when a newer command needs to interrupt it) and `check_for_new_command`, which lets a Goal/Search/Split/"different"/add/remove command targeting a specific UAV subset run concurrently instead of preempting the whole mission. |

## `uav/`

| File | What it does |
|---|---|
| `connection.py` | Finds the right network interface, opens the dronekit connection for each vehicle (`vehicle_connection`), and fetches each vehicle's current lat/lon (`fetch_location`). |
| `management.py` | Add/Remove UAV: `add_uav_to_swarm`, `remove_uav_from_swarm`, and the registry/index bookkeeping that keeps `pos_array`/`vehicles`/`different_height`/`s` in lock-step when the fleet changes size mid-mission. Also the legacy blocking `remove_vehicle`. |
| `telemetry.py` | Keeps the simulated swarm's (x, y) honest against live GPS — periodic resync, GPS-vs-sim distance reporting, and the read-only GPS overlay for the plot. |
| `guidance.py` | The core "make a fixed-wing actually fly this" logic: virtual-leader pacing bounded by real UAV lead distance, forward look-ahead along a Bezier curve or straight leg, the waypoint-reached test, and `_drive_vehicle_towards` (the actual `simple_goto` call). |

## `tasks/` — one file per mission category

| File | What it does |
|---|---|
| `runner.py` | The background thread that drives every bot with an active task (goal / mission-CSV / guided-circle / altitude), independent of whatever the foreground loop is doing. Also `assign_goal_tasks`, `assign_mission_tasks`, and the topology-sync logic used when a UAV is added/removed mid-mission. |
| `altitude.py` | The `different` command — restaggers per-bot altitude, live for busy bots, via an explicit background task for idle ones. |
| `goal.py` | **Goal** — send a UAV subset through an ordered list of points, handing off into a loitering circle at the end if configured. |
| `search.py` | **Search** — BezierCurveMultiple grid coverage flown by a selected UAV subset (or the whole fleet). |
| `split.py` | **Split** — AutoSplitMission (auto-grouped UAVs around center points); also owns the CSV-waypoint flight engine shared with Split Search. |
| `specific_split.py` | **Split Search** — SpecificSplitMission (operator hand-assigns specific UAV groups to specific centers); reuses `split.py`'s flight engine for the actual flying. |
| `open_group.py` | **Open Group** (`group_split` command) — assigns one goal position per named UAV. |
| `specific_bot_goal.py` | Send a single named UAV to one lat/lon goal. |
| `formation.py` | The older, pre-background-runner formation commands: standalone `guided_circle`, `same` altitude, and `loiter_point`. |
| `navigate.py` | `grid_path_planning` and `navigate` — fly the whole swarm through one shared Bezier grid in lockstep. |
| `home.py` | `home` (fly back along a return path) and the final-leg close-out onto each bot's recorded home position. |
| `admin.py` | Everything left over that isn't a mission: origin/geofence refresh, snapshotting positions to CSV, locking in home position, and takeoff. |

## Notes on fidelity to the original

This was a line-for-line refactor, not a rewrite. A few things worth
knowing if you're tracing behavior:

- The dispatch loop in `main.py` calls every command handler in the
  original's exact order, unconditionally, exactly like the original's
  flat (non-`elif`) `if` chain — more than one handler can fire for the
  same message (e.g. `remove`/`add` fall through into whatever flag-driven
  block follows).
- A few original blocks (`goal`, `different`, and `specificsplit`'s two
  failure paths) had an unconditional `continue` that aborted the *entire*
  dispatch iteration. The corresponding functions return `True` for that,
  and `main.py`'s loop `continue`s in response.
- Some pre-existing bugs were preserved rather than fixed: `takeoff` calls
  an undefined `arm_and_takeoff`; `same`'s completion check reads
  `alt`/`alt_count` that are never assigned; `navigate`'s skip-waypoint
  path and `store_uav_pos` reference an undefined `csv_path`/
  `csv_file_path`. All fail the same way they did before if triggered.
- Only confirmed-dead code was removed: write-only globals never read
  anywhere, one no-op statement, one unreachable block after a `continue`,
  and commented-out legacy blocks.
