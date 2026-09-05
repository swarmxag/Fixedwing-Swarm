#!/usr/bin/env python3
"""
Fixed SITL launcher:
 - scans arducopter.log for readiness (no socket probing)
 - per-drone logs under logs/<exe_name>/<sysid>/ (you can change root)
 - launches MAVProxy in real cmd.exe windows on Windows (one per sysid) or headless on other OSes
 - supports patterns for compute_homes (line, grid, triangle, circle, spiral)
 - respects --sec-address if passed
"""

import os
import sys
import math
import shutil
import subprocess
import psutil

import time
import re
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Optional dependencies for interface discovery; if not present we handle gracefully.
try:
    import netifaces
    import wmi
except Exception:
    netifaces = None
    wmi = None

LAUNCH_TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
RUN_COUNTER = {}   # sysid -> run count (used by make_log_filename)

# --- Tunables ---
PER_INSTANCE_BASE_STRIDE = 100   # unique base port step per instance
PORT_WAIT_TIMEOUT = 20.0         # seconds to wait for readiness via log scanning
LOG_POLL_INTERVAL = 0.2          # seconds between checking the log file
# -----------------


def make_log_filename(sysid: int, log_type: str) -> str:
    """
    Create filename like: <sysid>_<LAUNCH_TIMESTAMP>_<runid>_<log_type>.log
    runid increments per sysid each time this function is called.
    """
    runid = RUN_COUNTER.get(sysid, 0)
    RUN_COUNTER[sysid] = runid + 1
    return f"{sysid}_{LAUNCH_TIMESTAMP}_{runid}_{log_type}.log"


def get_wifi_ip(iface_map):
    if netifaces is None:
        return None
    for iface in netifaces.interfaces():
        try:
            iface_norm = iface.replace("{", "").replace("}", "").lower()
            adapter = iface_map.get(iface_norm, "").lower()
            iface_lower = iface.lower()

            is_ethernet = (
                adapter.startswith("ethernet")
                or iface_lower.startswith("ethernet")
                or "local area connection" in adapter
                or "lan" in adapter
                or iface_lower.startswith(("eth", "enp", "eno"))
            )

            is_wifi = (
                adapter.startswith(("wi-fi", "wifi"))
                or iface_lower.startswith(("wi-fi", "wifi"))
                or "wireless" in adapter
                or iface_lower.startswith("wlan")
            )

            if any(v in adapter for v in ["vm", "virtual", "host-only", "vethernet", "bridge"]):
                continue

            if not (is_ethernet or is_wifi):
                continue

            addrs = netifaces.ifaddresses(iface)
            ipv4_info = addrs.get(netifaces.AF_INET, [])
            for addr in ipv4_info:
                ip = addr.get("addr")
                if ip and ip.startswith("192.168."):
                    return ip
        except Exception:
            continue
    return None


def get_interface_mapping():
    if wmi is None or netifaces is None:
        return None
    c = wmi.WMI()
    mappings = {}
    for nic in c.Win32_NetworkAdapter():
        if nic.GUID:
            guid_norm = nic.GUID.replace("{", "").replace("}", "").lower()
            mappings[guid_norm] = nic.NetConnectionID or nic.Name
    return get_wifi_ip(mappings)


def find_mavproxy_cmd():
    mp = shutil.which("mavproxy.exe") or shutil.which("mavproxy")
    if mp:
        return mp
    mp2 = shutil.which("mavproxy.py")
    if mp2:
        return mp2
    return None


def compute_homes(n: int,
                  lat0: float,
                  lon0: float,
                  spacing_m: float,
                  pattern: str = "line",
                  row: Optional[int] = None,
                  col: Optional[int] = None) -> List[Tuple[float, float]]:
    """
    Generate n home positions (lat, lon) in degrees around base (lat0, lon0).
    pattern: "line" | "grid" | "triangle" | "circle" | "spiral"
    """
    if n <= 0:
        return []

    lat_deg_per_m = 1.0 / 111111.0
    lon_deg_per_m = 1.0 / (111111.0 * math.cos(math.radians(lat0)))

    homes: List[Tuple[float, float]] = []
    pattern = (pattern or "line").lower()

    if pattern == "line":
        total_width = spacing_m * (n - 1)
        start_x = - total_width / 2.0
        for i in range(n):
            dx = start_x + i * spacing_m
            lat = lat0
            lon = lon0 + dx * lon_deg_per_m
            homes.append((lat, lon))

    elif pattern == "grid":
        if row is None and col is None:
            cols = int(math.ceil(math.sqrt(n)))
            rows = int(math.ceil(n / cols))
        elif row is None:
            cols = int(col)
            rows = int(math.ceil(n / cols))
        elif col is None:
            rows = int(row)
            cols = int(math.ceil(n / rows))
        else:
            rows = int(row); cols = int(col)

        total_w = spacing_m * (cols - 1)
        total_h = spacing_m * (rows - 1)
        start_x = - total_w / 2.0
        start_y = total_h / 2.0
        count = 0
        for r in range(rows):
            for c in range(cols):
                if count >= n:
                    break
                dx = start_x + c * spacing_m
                dy = start_y - r * spacing_m
                lat = lat0 + dy * lat_deg_per_m
                lon = lon0 + dx * lon_deg_per_m
                homes.append((lat, lon))
                count += 1
            if count >= n:
                break

    elif pattern == "triangle":
        if row is None:
            R = int(math.ceil((math.sqrt(8*n + 1) - 1) / 2))
        else:
            R = int(row)
        counts = list(range(1, R+1))
        total = sum(counts)
        if total < n:
            counts[-1] += (n - total)
            total = n
        count = 0
        total_height = spacing_m * (len(counts) - 1)
        start_y = total_height / 2.0
        for r_idx, rc in enumerate(counts):
            if count >= n:
                break
            row_width = spacing_m * (rc - 1) if rc > 1 else 0.0
            start_x = - row_width / 2.0
            dy = start_y - r_idx * spacing_m
            for j in range(rc):
                if count >= n:
                    break
                dx = start_x + j * spacing_m
                lat = lat0 + dy * lat_deg_per_m
                lon = lon0 + dx * lon_deg_per_m
                homes.append((lat, lon))
                count += 1

    elif pattern == "circle":
        if n == 1:
            homes.append((lat0, lon0))
        else:
            r = spacing_m * n / (2.0 * math.pi)
            for i in range(n):
                theta = 2.0 * math.pi * i / n
                dx = r * math.cos(theta)
                dy = r * math.sin(theta)
                lat = lat0 + dy * lat_deg_per_m
                lon = lon0 + dx * lon_deg_per_m
                homes.append((lat, lon))

    elif pattern == "spiral":
        if n == 1:
            homes.append((lat0, lon0))
        else:
            b = spacing_m / (2.0 * math.pi)
            a = 0.0
            for i in range(n):
                theta = i * (2.0 * math.pi / max(8, n))
                r = a + b * theta
                dx = r * math.cos(theta)
                dy = r * math.sin(theta)
                lat = lat0 + dy * lat_deg_per_m
                lon = lon0 + dx * lon_deg_per_m
                homes.append((lat, lon))

    else:
        return compute_homes(n, lat0, lon0, spacing_m, pattern="line")

    return homes


def expected_tcp_port(base_port_for_instance, instance_idx):
    return base_port_for_instance


def launch_arducopter(exe_path: Path, idx: int, sysid: int, model: str,
                     lat: float, lon: float, alt: float, base_port: int, logdir: Path) -> subprocess.Popen:
    logdir.mkdir(parents=True, exist_ok=True)
    # produce SITL log filename per pattern
    sitl_logname = make_log_filename(sysid, "sitl")
    ardup_log = logdir / sitl_logname
    args = [
        str(exe_path),
        "--base-port", str(base_port),
        "-I", str(idx),
        "--model", model,
        "--home", f"{lat},{lon},{alt},0",
        "--sysid", str(sysid),
    ]
    lf = open(ardup_log, "a", buffering=1, encoding="utf-8", errors="ignore")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    p = subprocess.Popen(args, stdout=lf, stderr=lf, creationflags=creationflags)
    return p, ardup_log


# readiness regexes
_READINESS_PATTERNS = [
    re.compile(r"\bserial\d*\b.*\bTCP\b", re.IGNORECASE),
    re.compile(r"\blistening\b.*\btcp\b", re.IGNORECASE),
    re.compile(r"\bbound\b.*\b127\.0\.0\.1\b", re.IGNORECASE),
    re.compile(r"\bconnected\b.*\btcp\b", re.IGNORECASE),
    re.compile(r"\bSITL\b.*\brunning\b", re.IGNORECASE),
    re.compile(r"\bmavlink\b.*\bconnected\b", re.IGNORECASE),
]


def check_log_for_readiness(logpath: Path, start_pos: int):
    try:
        with logpath.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(start_pos)
            data = f.read()
            new_pos = f.tell()
    except FileNotFoundError:
        return False, start_pos, ""
    if not data:
        return False, new_pos, ""
    for line in data.splitlines():
        for rx in _READINESS_PATTERNS:
            if rx.search(line):
                return True, new_pos, line.strip()
    return False, new_pos, ""


def wait_for_ardup_ready_by_log(proc: subprocess.Popen, logpath: Path, timeout: float) -> bool:
    deadline = time.time() + timeout
    try:
        start_pos = logpath.stat().st_size
    except FileNotFoundError:
        start_pos = 0
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        found, start_pos, matched = check_log_for_readiness(logpath, start_pos)
        if found:
            print(f"[watchdog] readiness detected in {logpath}: {matched}")
            return True
        time.sleep(LOG_POLL_INTERVAL)
    return False

def start_mavproxy(tcp_port:int,sysid: int, gcs_addr: str, gcs_port: int, sec_addr:str, logdir: Path,per_udp: int):
    """
    Start MAVProxy using mavproxy.exe with Popen (recommended way).
    No console window. Safe auto-terminate when parent closes.
    """

   

    logdir.mkdir(parents=True, exist_ok=True)
    mav_logname = make_log_filename(sysid, "mavproxy")
    mav_log = logdir / mav_logname
    # outs = [f"--out=udp:{gcs_addr}:{gcs_port}", f"--out=udp:{sec_addr}:{per_udp}"]


    # log_file = logdir / "mavproxy.log"
    lf = open(mav_log, "a", buffering=1, encoding="utf-8", errors="ignore")

    # --- Windows console suppression ---
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE

    # --- MAVProxy arguments ---
    args = [
        "mavproxy.exe",
        f"--master=tcp:127.0.0.1:{tcp_port}",
        f"--out=udp:{gcs_addr}:{gcs_port}",
        f"--out=udp:{sec_addr}:{per_udp}",
        f"--target-system={sysid}",
        "--non-interactive",
        "--force-connected",
        "--udp-timeout=50",
        "--nowait",
        "--no-console",
        "--daemon",              # important: prevents UI loop
        f"--logfile={mav_log}"
    ]

    # --- Start MAVProxy like SITL ---
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
        
    )

    return p , mav_log

def start_mavproxy_headless(tcp_port: int, gcs_addr: str, gcs_port: int,
                            per_udp: int, sysid: int, logdir: Path, mavproxy_cmd: str = None) -> subprocess.Popen:
    logdir.mkdir(parents=True, exist_ok=True)
    mav_logname = make_log_filename(sysid, "mav")
    mav_log = logdir / mav_logname
    outs = [f"--out=udp:{gcs_addr}:{gcs_port}", f"--out=udp:0.0.0.0:{per_udp}"]
    if mavproxy_cmd:
        cmd_list = [mavproxy_cmd, f"--master=tcp:127.0.0.1:{tcp_port}"] + outs + ["--nowait", "-c", "--udp-timeout=50", "--force-connected"]
    else:
        cmd_list = [sys.executable, "-m", "MAVProxy", f"--master=tcp:127.0.0.1:{tcp_port}"] + outs + ["--nowait", "-c", "--udp-timeout=50", "--force-connected"]
    lf = open(mav_log, "a", buffering=1, encoding="utf-8", errors="ignore")
    creationflags = 0x08000000 if os.name == "nt" else 0
    p = subprocess.Popen(cmd_list, stdout=lf, stderr=lf, creationflags=creationflags)
    print(f"[mavproxy headless] sysid={sysid} pid={p.pid} -> udp:{gcs_addr}:{gcs_port}")
    return p
def kill_by_starter_pid(starter_pid: int, verbose: bool = False):
    """
    Find child PIDs of the starter and kill entire trees using taskkill.
    If none found, still try taskkill on the starter pid.
    """
    if starter_pid is None:
        return
    # First find descendants
    descendants = _collect_descendants(starter_pid, max_depth=6)
    if verbose:
        print(f"[kill] descendants of starter {starter_pid}: {descendants}")

    # For each discovered descendant, force kill its tree
    for child_pid in descendants:
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(child_pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if verbose:
                print(f"[kill] taskkill PID {child_pid}")
        except Exception as e:
            if verbose:
                print(f"[kill] failed taskkill {child_pid}: {e}")

    # Also try to taskkill the starter in case it still has window or leftovers
    try:
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(starter_pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if verbose:
            print(f"[kill] taskkill starter {starter_pid}")
    except Exception:
        pass



def start_mavproxy_in_cmd(tcp_port: int, gcs_addr: str, gcs_port: int, sec_addr: str,
                          per_udp: int, sysid: int, logdir: Path, mavproxy_cmd: str = None,
                          keep_open: bool = True) -> subprocess.Popen:
    """
    Launch MAVProxy using cmd.exe in a new console (CREATE_NEW_CONSOLE). Returns Popen for cmd.exe.
    We also pass --logfile to MAVProxy so it writes to the log file even when running in a console.
    """
    logdir.mkdir(parents=True, exist_ok=True)
    mav_logname = make_log_filename(sysid, "mav")
    mav_log = logdir / mav_logname

    outs = [f"--out=udp:{gcs_addr}:{gcs_port}", f"--out=udp:{sec_addr}:{per_udp}"]

    if mavproxy_cmd:
        cmd_list = [mavproxy_cmd, f"--master=tcp:127.0.0.1:{tcp_port}"] + outs + ["--nowait", "--no-console","-c", "--udp-timeout=50", "--force-connected"]
    else:
        cmd_list = [sys.executable, "-m", "MAVProxy", f"--master=tcp:127.0.0.1:{tcp_port}"] + outs + ["--nowait", "-c", "--udp-timeout=50", "--force-connected", f"--logfile={str(mav_log)}"]

    if os.name == "nt":
        # Build command string properly quoted
        cmdline = subprocess.list2cmdline(cmd_list)
        cmd_option = "/k" if keep_open else "/c"
        full_cmd = f'start "MAVProxy sysid={sysid}" cmd {cmd_option} {cmdline}'
        p = subprocess.Popen(full_cmd, shell=True ,stdin=subprocess.PIPE,creationflags = subprocess.CREATE_NEW_PROCESS_GROUP, text=True)
        print(f"[mavproxy cmd] sysid={sysid} launched in new console (cmd.exe) pid={p.pid}")
    else:
        # Non-windows fallback (headless)
        p = start_mavproxy_headless(tcp_port, gcs_addr, gcs_port, per_udp, sysid, logdir, mavproxy_cmd)
    return p , mav_log


def kill_tree_by_starter_pid(starter_pid:int, wait:float=0.5):
    """
    Given pid returned by Popen(..., shell=True), find real children recursively
    and kill them (tries graceful then force).
    """
    try:
        parent = psutil.Process(starter_pid)
    except psutil.NoSuchProcess:
        return

    # find all descendants (children of child etc.)
    descendants = parent.children(recursive=True)
    # if none, still check parent itself
    targets = descendants[:]  # copy

    # attempt graceful terminate first
    for p in targets:
        try:
            p.terminate()
        except Exception:
            pass
    gone, alive = psutil.wait_procs(targets, timeout=wait)

    # force kill remaining
    for p in alive:
        try:
            p.kill()
        except Exception:
            pass

    # finally ensure any direct children of starter are killed with taskkill just in case
    try:
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(starter_pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def kill_process_tree(p: subprocess.Popen):
    """Kill process and its children. Works on Windows (taskkill) and POSIX (pgid)."""
    if not p:
        return
    try:
        pid = p.pid
        if pid is None:
            return
    except Exception:
        return

    # # POSIX: kill process group if available
    # if os.name != "nt":
    #     try:
    #         pgid = os.getpgid(pid)
    #         os.killpg(pgid, signal.SIGTERM)
    #         return
    #     except Exception:
    #         # fallback to terminate single pid
    #         try:
    #             p.terminate()
    #         except Exception:
    #             pass
    #         return

    # Windows: use taskkill to kill tree (reliable)
    try:
        subprocess.run(["taskkill","/F", "/PID", str(pid), "/T" ],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        print(f"task kill {pid}")
    except Exception:
        try:
            p.terminate()
        except Exception:
            pass


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--exe", required=True, help="path to arducopter executable")
    p.add_argument("--model", default="quad")
    p.add_argument("-n", "--count", type=int, default=2)
    p.add_argument("--spacing", type=float, default=10.0)
    p.add_argument("--col", type=int, default=None)
    p.add_argument("--row", type=int, default=None)
    p.add_argument("--pattern", type=str, default="line", help="line|grid|triangle|circle|spiral")
    p.add_argument("--home-lat", type=float, default=13.0067)
    p.add_argument("--home-lon", type=float, default=80.2570)
    p.add_argument("--home-alt", type=float, default=5.0)
    p.add_argument("--gcs-address", default="127.0.0.1")
    p.add_argument("--gcs-port", type=int, default=14550)
    p.add_argument("--sec-address", type=str, default="127.0.0.1")
    p.add_argument("--base-port", type=int, default=5670)
    p.add_argument("--start-sysid", type=int, default=1)
    p.add_argument("--log-dir", default="./logs")
    p.add_argument("--keep-open", action="store_true", help="Keep cmd windows open after MAVProxy starts (cmd /k)")
    args = p.parse_args()

    # Resolve secondary address preference:
    if args.sec_address:
        secondary_ip = args.sec_address
    else:
        
        secondary_ip = discovered or "127.0.0.1"

    exe_path = Path(args.exe).resolve()
    if not exe_path.exists():
        print("ERROR: arducopter exe not found:", exe_path)
        sys.exit(2)

    # Use logs/<exe_name>/<sysid>/ as you requested earlier
    exe_name = exe_path.stem
    log_root = Path(args.log_dir).resolve() / exe_name
    log_root.mkdir(parents=True, exist_ok=True)

    mavproxy_cmd = find_mavproxy_cmd()
    if mavproxy_cmd:
        print("Using global MAVProxy:", mavproxy_cmd)
    else:
        print("No MAVProxy executable found on PATH. Will use python -m MAVProxy.")

    homes = compute_homes(args.count, args.home_lat, args.home_lon, args.spacing, args.pattern, args.row, args.col)

    instances = {}
    with ThreadPoolExecutor(max_workers=max(1, args.count)) as ex:
        futures = []
        for i in range(args.count):
            sysid = args.start_sysid + i
            per_udp = 14550 + sysid
            base_port_for_instance = args.base_port + i * PER_INSTANCE_BASE_STRIDE
            tcp_port = expected_tcp_port(base_port_for_instance, i)
            drone_logdir = log_root / str(sysid)

            instances[i] = {
                "idx": i,
                "sysid": sysid,
                "home": homes[i],
                "per_udp": per_udp,
                "base_port_for_instance": base_port_for_instance,
                "tcp_port": tcp_port,
                "ardup": None,
                "mavp": None,
                "logdir": drone_logdir,
            }

            def start_instance(i=i, info=instances[i]):
                lat, lon = info["home"]
                info["logdir"].mkdir(parents=True, exist_ok=True)
                p , ardup_log= launch_arducopter(exe_path, i, info["sysid"], args.model, lat, lon, args.home_alt, info["base_port_for_instance"], info["logdir"])
                info["ardup"] = p

                # ardup_log = info["logdir"] / make_log_filename(info["sysid"], "sitl")  # tail the file we create
                # if file not yet created, use the consistent name: it's created by launch_arducopter open
                # wait for readiness
                ready = wait_for_ardup_ready_by_log(p, ardup_log, PORT_WAIT_TIMEOUT)
                if not ready:
                    print(f"[WARN] sysid={info['sysid']} readiness not detected within {PORT_WAIT_TIMEOUT}s (check {info['logdir']})")

                if os.name == "nt":
                    # info ["mavp"] ,_= start_mavproxy(info["tcp_port"], info["sysid"],args.gcs_address,args.gcs_port,secondary_ip,info["logdir"],info["per_udp"])
                    info["mavp"], _ = start_mavproxy_in_cmd(info["tcp_port"], args.gcs_address, args.gcs_port, secondary_ip, info["per_udp"], info["sysid"], info["logdir"], mavproxy_cmd, keep_open=args.keep_open)
                else:
                    info["mavp"] = start_mavproxy_headless(info["tcp_port"], args.gcs_address, args.gcs_port, info["per_udp"], info["sysid"], info["logdir"], mavproxy_cmd)

            futures.append(ex.submit(start_instance))

        for fut in futures:
            try:
                fut.result()
            except Exception as e:
                   import traceback
                   print("Instance start raised:", e)
                   traceback.print_exc()

    print(f"All instances started. Logs under: {log_root}")
    try:
        while True:
            alive_ard = sum(1 for i in instances.values() if i["ardup"] and i["ardup"].poll() is None)
            alive_mav_launched = sum(1 for i in instances.values() if i.get("mavp") is not None)
            print(f"Alive ardup: {alive_ard}/{args.count}   mavproxy (launched): {alive_mav_launched}/{args.count}", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all children...")
        for info in instances.values():
            if info.get("mavp"):
                try:

                    print(type(info.get("mavp")))
                    # kill_tree_by_starter_pid(info.get("mavp"))
                    # kill_process_tree(info.get("mavp"))
                    # info.get("mavp").stdin.write("exit\r\n")
                    # info.get("mavp").stdin.flush()
                    kill_by_starter_pid(info.get("mavp"), verbose=True)
                    
                    # info["mavp"].terminate()
                except Exception:
                    pass
            if info.get("ardup"):
                try:
                    kill_by_starter_pid(info.get("ardup"), verbose=True)
                    # kill_process_tree(info.get("ardup"))
                    # info["ardup"].terminate()
                except Exception:
                    pass
        print("Done. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
