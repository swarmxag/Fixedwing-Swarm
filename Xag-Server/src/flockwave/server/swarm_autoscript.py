import os
import shutil
import subprocess

import psutil

# Dev-mode: fixed-wing swarm runs as a raw script, not a packaged exe.
# Override via env vars on machines that differ from this one (e.g. no venv,
# or a different install path):
#   FIXED_WING_PYTHON  - full path to the interpreter to launch it with
#   FIXED_WING_SCRIPT  - full path to medur_fixed_wing.py
_VENV_PYTHON = r"D:\nithya\myenv\Scripts\python.exe"
FIXED_WING_SCRIPT = os.environ.get(
    "FIXED_WING_SCRIPT",
    r"D:\Kamikaze-Fuze-GUI\fixed_wing_windows_exe\swarm_tasks"
    r"\Examples\basic_tasks\medur_fixed_wing.py",
)

# Prefer an explicit env override, then this machine's known venv, then just
# whatever "python" resolves to on PATH (plain system install, no venv).
FIXED_WING_PYTHON = (
    os.environ.get("FIXED_WING_PYTHON")
    or (_VENV_PYTHON if os.path.exists(_VENV_PYTHON) else None)
    or shutil.which("python")
    or "python"
)


def is_server_running(exe_name):
    """Check if a process with the given exe_name is running, either as the
    packaged executable or as its source script run via python.exe."""
    script_name = os.path.splitext(exe_name)[0]
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            if proc.info["name"] == exe_name:
                return True
            if proc.info["name"] in ("python.exe", "python") and proc.info["cmdline"]:
                if script_name in " ".join(proc.info["cmdline"]):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def run_server_exe(sim_enable=False, server_address="127.0.0.1"):
    """Launch the fixed-wing swarm script under its own venv in a new console,
    the same way run_server_exe() launches copter_swarm.exe."""
    if os.sep in FIXED_WING_PYTHON and not os.path.exists(FIXED_WING_PYTHON):
        print(f"ERROR: python interpreter not found at {FIXED_WING_PYTHON}")
        return

    if not os.path.exists(FIXED_WING_SCRIPT):
        print(f"ERROR: medur_fixed_wing.py not found at {FIXED_WING_SCRIPT}")
        return

    print("Starting fixed-wing swarm server (dev mode)...")
    cmdlist = [FIXED_WING_PYTHON, FIXED_WING_SCRIPT]
    print(cmdlist)
    subprocess.Popen(
        cmdlist,
        cwd=os.path.dirname(FIXED_WING_SCRIPT),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    print("Server started!")
