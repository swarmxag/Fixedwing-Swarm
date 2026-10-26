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
