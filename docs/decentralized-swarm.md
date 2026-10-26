# Decentralised swarm: node table, master selection, command routing

## Setup

1. **Node table** (server machine): copy `swarm_nodes.example.json` to
   `~/Documents/swarm_env/swarm_nodes.json` and list every UAV's onboard computer.
   Ids and IPs must be unique; an invalid file makes the server refuse to route
   (and the GUI shows the error) rather than guess.
   Without the file the server runs in *legacy mode*: one swarm computer on
   127.0.0.1 that is always the master (the original behaviour).
2. **Each NUC**: set `SWARM_NODE_ID=<its UAV number>` before starting the swarm
   program (e.g. `1` for 192.168.6.101). The node then starts as a *standby* and
   flies only after the operator promotes it. Optional: `SWARM_CMD_PORT`
   (default 12008) and `SWARM_CTL_PORT` (default 12002).
3. Server tuning (optional): `SWARM_ACK_TIMEOUT` (0.25 s), `SWARM_RETRIES` (4).

## Behaviour

| Command | Goes to | Delivery |
|---|---|---|
| search, split, specific split, goal, autogoal, autogoal radius, add/remove UAV, different/same altitude, stop, home, loiter, landing, takeoff | the active master only | ACKed, retried, in order, exactly once |
| origin, geofence, clear_csv | every node (so a standby is ready to take over) | ACKed per node |
| master change | candidate (promote) and old master (demote) | operator-confirmed, eligibility-checked, epoch-fenced |

* A command is **refused loudly** (error in the GUI) when no master is selected,
  the node table is invalid, a targeted UAV id is not registered, or the master
  never ACKs. It is never silently dropped.
* ACK means *queued on the receiver*. The receiver then reports `started`,
  `superseded` (a newer goal / auto-goal / radius for the same UAV set replaced it
  while it was still pending, or a stop overwrote it) or `discarded` (a stop
  cleared the queue). These appear under "Last commands" in the swarm panel.
  Completion of a mission is not tracked yet.
* Search / split / specific split / include-exclude are never merged or reordered.
* A standby refuses mission commands (`not_master`) but still accepts origin,
  geofence, clear_csv and the control-port messages.
* Epoch: each master change increments a persisted epoch. Nodes refuse any
  message from an older epoch (`stale_epoch`), so a delayed command or a
  returning old master cannot act. A demotion that could not be delivered is
  retried until the old master answers.
* Master change flow (GUI): click a UAV in the swarm panel -> the server returns
  an eligibility report -> confirm. Eligible = registered, answering a probe,
  decentralised mode on, not already master, not mid-promotion.

## Tests

`python3 medur_swarm/tests/test_transport.py` and `test_router.py`
(Ubuntu and Windows). They start real receivers and the real router; no flight
hardware or dronekit needed.

## Phase 3: execution status, Stop, replication, recovery

### Command status: transport vs execution
`received` (transport ACK) is **not** execution. The swarm computer then reports, from
its real main loop (`communication/lifecycle.py`), one of:

| status | meaning |
|---|---|
| received | datagram reached the node and passed policy (ACK) |
| started | the dispatch loop took the command |
| running | work was handed to background per-UAV tasks, which are still flying |
| completed | foreground command ran to its end / the last of its background tasks ended. It does **not** mean the aircraft reached a goal safely |
| failed | a handler raised (reason included) |
| preempted | a newer command took over before it finished (or replaced all its tasks) |
| cancelled | an explicit Stop dropped it |
| interrupted | outcome unknown: UAV removed under it, or the node restarted mid-command (read back from the on-disk journal) |
| superseded / discarded | never ran: replaced by a newer plan, or cleared by Stop |
| rejected | refused at the door (`unsupported_command`, `not_master`, `stale_epoch`, `invalid_origin`...) |

Known coarse spot: a subset goal that overwrites part of a *foreground* mission's tasks
is not noted against that foreground command.

### Stop
"stop" is two signals; the operator Stop (`explicit_stop`) sends both:
* control port 12002 -> `state.index = b"stop"` -> breaks foreground mission loops;
* command port 12008 -> `runner.clear_all_active_tasks()` -> drops background tasks and
  the auto-goal layout.
Neither commands the aircraft to hold; UAVs keep their last guided target. The precursor
`stop_socket()` that other commands send stays control-port-only on purpose (so adding or
removing one UAV does not wipe other UAVs' goals). There is currently **no Stop button**
in the swarm panel (it is commented out in `SwarmPanel.jsx`).

### Heartbeat, replication, recovery
* The server asks the master for a snapshot every second; the answer is the heartbeat.
  3 misses -> `master_lost` banner. **Promotion is never automatic.**
* The snapshot (epoch, version, tasks incl. guided-circle fields, auto-goal layout, UAV
  membership, altitude plan, last 50 command statuses) is relayed to every standby and
  stored atomically on disk (`node<ID>_replica.json`); stale epochs and older versions are
  refused. Relay goes through the server; if the server is down, replication stops.
* On promotion the new master connects to the UAVs, then **reconciles** the replica with
  live telemetry and reports. It replays nothing. A task is `resumable` only if the replica
  is fresh (`SWARM_RECOVER_MAX_AGE`, default 30 s), the UAV is connected, armed and GUIDED,
  and it is a goal task with goals left. Search/split/altitude tasks and commands whose
  outcome was unknown are listed for the operator to re-issue.
* "Resume verified goals" (GUI, with confirmation) sends `recover_resume,<replica version>`;
  the node re-checks against fresh telemetry and refuses a mismatched version or origin.

### Commands without a swarm-side handler
`clear_csv`, `remove_bot`, `share_data` are now **rejected** (`unsupported_command`) instead
of being ACKed and ignored. Still plain, unacknowledged UDP to the old hard-coded IPs
(`192.168.6.153/155/160`): `select_plot`, `airport_selection` (port 12003) and
`share_data_func` (port 12008). The swarm has no listener/handler for them; they do nothing.

### Env summary
`SWARM_NODE_ID`, `SWARM_CMD_PORT`, `SWARM_CTL_PORT`, `SWARM_STATE_DIR` (journal + replica,
default `~/Documents/swarm_env`), `SWARM_RECOVER_MAX_AGE`, `SWARM_ACK_TIMEOUT`, `SWARM_RETRIES`.

### Tests (Ubuntu 22.04 and Windows)
`test_transport.py` (9), `test_router.py` (12), `test_lifecycle.py` (16),
`test_recovery.py` (16). They run the real main loop / router with only hardware faked.
