import os
import subprocess

simulation_process = None

# Dev-mode: sim_launcher.exe (and the ArduPilot SITL binaries next to it)
# lives outside this repo. Override via env var on machines that differ
# from this one:
#   SIM_LAUNCHER_DIR - folder containing sim_launcher.exe, arducopter.exe,
#                       ArduPlane.exe, etc.
SIM_LAUNCHER_DIR = os.environ.get(
    "SIM_LAUNCHER_DIR",
    r"C:\Users\Dell\Downloads\simulator\simulator",
)

# Per-vehicle SITL binary + --model flag, keyed by the lowercase value the
# frontend sends as simVehicle.
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
    server_address="127.0.0.1",
    pattern="Line",
    vehicle="plane",
):
    global simulation_process

    config = VEHICLE_CONFIG.get(str(vehicle).lower(), VEHICLE_CONFIG["plane"])

    server_exe = os.path.join(SIM_LAUNCHER_DIR, "sim_launcher.exe")
    vehicle_exe = os.path.join(SIM_LAUNCHER_DIR, config["exe"])
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
        cwd=SIM_LAUNCHER_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    print("Server started!", simulation_process)


def stop_simulation():
    global simulation_process
    if not simulation_process:
        print("No simulation process found")
        return

    if simulation_process.poll() is None:
        print("Stopping Simulation...")
        simulation_process.terminate()

        try:
            simulation_process.wait(timeout=5)
            print("Simulation stopped successfully")
        except subprocess.TimeoutExpired:
            print("Force killing simulation...")
            simulation_process.kill()
    else:
        print("Simulation already stopped")

    simulation_process = None
