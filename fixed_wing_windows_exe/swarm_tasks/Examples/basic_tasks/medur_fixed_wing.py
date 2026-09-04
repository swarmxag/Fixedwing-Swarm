"""Entry point for the fixed-wing swarm ground-control script.

Implementation lives in medur_swarm/ (communication, uav connection/
management/telemetry/guidance, and one module per mission command --
Goal, Search, Split, Split Search, Open Group, formation, home, admin).
See medur_swarm/main.py for the startup sequence and dispatch loop.
"""

import os
import sys

# swarm_tasks lives three directories up from this file
# (fixed_wing_windows_exe/swarm_tasks/...) -- needed on sys.path before
# medur_swarm (which imports swarm_tasks.* throughout) can be imported.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from medur_swarm.main import run

if __name__ == "__main__":
    run()
