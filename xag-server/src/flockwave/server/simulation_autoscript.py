import os
import subprocess
import sys
import threading

from .swarm_autoscript import is_server_running
from .utils.packaging import is_packaged_with_pyinstaller
from .network import NetworkIP

# Local network IP used as the default server_address for simulation_exe()
ip = NetworkIP.get_ip()

simulation_process = None
vtol_demo_process = None


# Dev-mode: sim_launcher.exe (and the ArduPilot SITL binaries next to it)
# lives outside this repo. Override via env var on machines that differ
# from this one:
#   SIM_LAUNCHER_DIR - folder containing sim_launcher.exe, arducopter.exe,
#                       ArduPlane.exe, etc.
SIM_LAUNCHER_DIR = os.environ.get(
    "SIM_LAUNCHER_DIR",
    r"C:\Users\Dell\Documents\Mission Planner\sitl\simulator",
)

# Number of seconds to wait after launching the SITL/MAVProxy processes
# before starting vtol_demo.exe. ArduPilot SITL + MAVProxy need some time
# to boot and start sending heartbeats; vtol_demo.py's own dronekit
# connect() calls will still retry for a while beyond this (up to their
# own heartbeat_timeout), so this only needs to be a reasonable estimate,
# not exact.
# VTOL_DEMO_START_DELAY_SECONDS = float(
#     os.environ.get("VTOL_DEMO_START_DELAY_SECONDS", "12")
# )


# def _vtol_demo_path():
#     """Resolves the path to the bundled vtol_demo.exe.

#     In a packaged build, skybrushd.exe and missions\\vtol_demo.exe are
#     installed as siblings (see GCS-live's electron-builder extraFiles
#     config), so vtol_demo.exe is found relative to this executable's own
#     folder. In dev mode (running from source), override with the
#     VTOL_DEMO_EXE env var to point at a locally-built exe.
#     """
#     override = os.environ.get("VTOL_DEMO_EXE")
#     if override:
#         return override

#     if is_packaged_with_pyinstaller():
#         base_dir = os.path.dirname(sys.executable)
#     else:
#         # Dev-mode fallback: the sibling fixed_wing_windows_exe repo's build
#         # output, assuming the usual side-by-side checkout layout.
#         base_dir = os.path.abspath(
#             os.path.join(
#                 os.path.dirname(__file__),
#                 "..",
#                 "..",
#                 "..",
#                 "..",
#                 "fixed_wing_windows_exe",
#                 "dist",
#             )
#         )
#         return os.path.join(base_dir, "vtol_demo.exe")

#     return os.path.join(base_dir, "missions", "vtol_demo.exe")


# def _start_vtol_demo():
    
    
#     global vtol_demo_process

#     if is_server_running("vtol_demo.exe"):
#         print("[vtol_demo] already running, not starting a second instance")
#         return

#     vtol_demo_exe = _vtol_demo_path()
#     if not os.path.exists(vtol_demo_exe):
#         print(f"ERROR: vtol_demo.exe not found at {vtol_demo_exe}")
#         return

#     print("[vtol_demo] starting", vtol_demo_exe)
#     vtol_demo_process = subprocess.Popen(
#         [vtol_demo_exe],
#         cwd=os.path.dirname(vtol_demo_exe),
#         creationflags=subprocess.CREATE_NEW_CONSOLE,
#     )
#     print("[vtol_demo] started!", vtol_demo_process)


# def _schedule_vtol_demo_start():
#     timer = threading.Timer(VTOL_DEMO_START_DELAY_SECONDS, _start_vtol_demo)
#     timer.daemon = True
#     timer.start()

# # Per-vehicle SITL binary + --model flag, keyed by the lowercase value the
# # frontend sends as simVehicle.
VEHICLE_CONFIG = {
    "copter": {"exe": "arducopter.exe", "model": "quad"},
    "plane": {"exe": "ArduPlane.exe", "model": "quadplane"},
}


def simulation_exe(
    home_lat: float,
    home_lon: float,
    home_alt=0,
    count: int = 1,
    spacing: int = 30,
    col: int = 0,
    row: int = 0,
    server_address=ip,
    pattern="Line",
    vehicle="plane",
):
    global simulation_process

    config = VEHICLE_CONFIG.get(str(vehicle).lower(), VEHICLE_CONFIG["plane"])
    # Path where master.exe is running
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__)) 

    if getattr(sys, "frozen", False):
    # EXE mode
     simulator_dir = os.path.join(base_dir, "simulator")
    else:
    # Source mode
     simulator_dir = r"C:\Users\Joel\Desktop\simulator\simulator"

    server_exe = os.path.join(simulator_dir, "sim_launcher.exe")
    vehicle_exe = os.path.join(simulator_dir, "ArduPlane.exe")

    print("Simulator directory:", simulator_dir) 
    print("Looking for:", server_exe, vehicle_exe)
    print("Looking for:", server_exe, vehicle_exe)

    if not os.path.exists(server_exe) or not os.path.exists(vehicle_exe):
        print("ERROR: simulator exe(s) not found!")
        return

    cmdlist = [
        server_exe,
        "--exe",
        vehicle_exe,
        "--model",
        config["model"],
        "-n",
        str(count),
        "--spacing",
        str(spacing),
        "--home-lat",
        str(home_lat),
        "--home-lon",
        str(home_lon),
        "--sec-address",
        server_address,
        "--pattern",
        str(pattern).lower(),
    ]
    if col not in (None, "None"):
        cmdlist.extend(["--col", str(col)])

    if row not in (None, "None"):
        cmdlist.extend(["--row", str(row)])

    print("Command List:", cmdlist)
    print("Starting Simulation...")
    simulation_process = subprocess.Popen(
        cmdlist,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    
    print("Server started!", simulation_process)

    # Auto-launching vtol_demo.exe is a packaged-EXE-only convenience. When
    # running skybrushd from source, the developer is expected to start
    # vtol_demo.py manually in their own terminal.
    # if is_packaged_with_pyinstaller():
        # vtol_demo.exe needs the simulated vehicles to already be sending
        # MAVLink heartbeats before its dronekit connect() calls can
        # succeed, so it is started after a delay rather than immediately.
        # _schedule_vtol_demo_start()
    # else:
        # print("[vtol_demo] running from source: not auto-starting vtol_demo.exe")


def _kill_by_image(image_name: str) -> None:
    """Kill all running processes with the given executable name.

    MAVProxy and ArduPlane are launched by sim_launcher in their own process
    groups (sometimes with CREATE_NEW_CONSOLE), so they are NOT Windows
    children of the launcher PID and survive a `taskkill /T` tree-kill.
    Killing them by image name ensures every process inside the Windows
    Terminal tab exits, which causes the tab to close automatically.
    """
    try:
        result = subprocess.run(
            ["taskkill", "/IM", image_name, "/F"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.stdout.strip():
            print(f"  [{image_name}] {result.stdout.strip()}")
    except Exception as exc:
        print(f"Warning: could not kill {image_name}: {exc}")


def stop_simulation():
    global simulation_process, vtol_demo_process

    if simulation_process is None:
        print("No simulation process found")
        return False

    pid = simulation_process.pid

    print("Stopping Simulation...")
    print("Launcher PID:", pid)

    try:
        # Step 1 – Kill the launcher and every direct/indirect Windows child.
        # /PID = launcher PID  /T = include children  /F = force
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        print("taskkill output:")
        print(result.stdout)

        if result.stderr:
            print("taskkill error:")
            print(result.stderr)

        # Step 2 – Kill simulator-specific processes by image name.
        #
        # The terminal shown is Windows Terminal (tabbed app).  A tab closes
        # automatically only when ALL processes running inside it have exited.
        # MAVProxy (title "MAVProxy sysid=N") and ArduPlane are spawned by
        # sim_launcher inside their own process groups, so /T above misses
        # them.  Killing by image name guarantees the tab disappears.
        print("Killing simulator processes by name...")
        for image in ("ArduPlane.exe", "MAVProxy.exe", "mavproxy.exe", "vtol_demo.exe"):
            _kill_by_image(image)

        simulation_process = None
        vtol_demo_process = None
        print("Simulation stopped successfully")
        return True

    except Exception as e:
        print("Error stopping simulation:", e)
        simulation_process = None
        return False