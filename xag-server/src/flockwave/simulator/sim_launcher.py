#!/usr/bin/env python3
"""
SITL launcher that detects ArduCopter readiness by scanning arducopter.log (no socket probing).
- Per-drone logs under logs/arducopter/{sysid}/
- MAVProxy launched in real cmd.exe windows on Windows (one per sysid)
"""

import os
import sys
import math
import shutil
import subprocess
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import netifaces, wmi
from datetime import datetime


LAUNCH_TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")


# --- Tunables ---
PER_INSTANCE_BASE_STRIDE = 100   # unique base port step per instance
PORT_WAIT_TIMEOUT = 20.0         # seconds to wait for readiness via log scanning
LOG_POLL_INTERVAL = 0.2          # seconds between checking the log file
# -----------------

def make_log_filename(sysid: int, log_type: str) -> str:
    # log_type is "sitl" or "mav"
    runid = RUN_COUNTER.get(sysid, 0)
   
    return f"{sysid}_{LAUNCH_TIMESTAMP}_{log_type}.log"

def get_wifi_ip(iface_map):
    for iface in netifaces.interfaces():
        try:
            # Normalize interface name to match mapping
            iface_norm = iface.replace("{", "").replace("}", "").lower()

            # Get adapter name
            adapter = iface_map.get(iface_norm, "").lower()
            iface_lower = iface.lower()

            # -------------------------
            # Detect Real Ethernet
            # -------------------------
            is_ethernet = (
                adapter.startswith("ethernet")
                or iface_lower.startswith("ethernet")
                or "local area connection" in adapter
                or "lan" in adapter
                or iface_lower.startswith(("eth", "enp", "eno"))
            )

            # -------------------------
            # Detect Real WiFi
            # -------------------------
            is_wifi = (
                adapter.startswith(("wi-fi", "wifi"))
                or iface_lower.startswith(("wi-fi", "wifi"))
                or "wireless" in adapter
                or iface_lower.startswith("wlan")
            )

            # -------------------------
            # Exclude Virtual Interfaces
            # -------------------------
            if any(
                v in adapter
                for v in ["vm", "virtual", "host-only", "vethernet", "bridge"]
            ):
                continue

            if not (is_ethernet or is_wifi):
                continue

            # -------------------------
            # Get IPv4 address
            # -------------------------
            addrs = netifaces.ifaddresses(iface)
            ipv4_info = addrs.get(netifaces.AF_INET, [])

            for addr in ipv4_info:
                ip = addr.get("addr")
                if ip and ip.startswith("192.168."):
                    return ip

        except Exception as e:
            print(f"Error on interface {iface}: {e}")

    return None


def get_interface_mapping():
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

def compute_homes(n, lat0, lon0, spacing_m):
    homes = []
    lat_deg_per_m = 1.0 / 111111.0
    lon_deg_per_m = 1.0 / (111111.0 * math.cos(math.radians(lat0)))
    for i in range(n):
        dx = spacing_m * i
        lat = lat0
        lon = lon0 + dx * lon_deg_per_m
        homes.append((lat, lon))
    return homes

def expected_tcp_port(base_port_for_instance, instance_idx):
    # We choose the instance's TCP port to be base_port_for_instance (unique per instance)
    return base_port_for_instance

def launch_arducopter(exe_path: Path, idx: int, sysid: int, model: str,
                     lat: float, lon: float, alt: float, base_port: int, logdir: Path) -> subprocess.Popen:
    """Launch ArduCopter headless; writes to arducopter.log in logdir."""
    logdir.mkdir(parents=True, exist_ok=True)
    ardup_log = logdir / "arducopter.log"
    args = [
        str(exe_path),
        "--base-port", str(base_port),
        "-I", str(idx),
        "--model", model,
        "--home", f"{lat},{lon},{alt},0",
        "--sysid", str(sysid),
    ]
    lf = open(ardup_log, "a", buffering=1, encoding="utf-8", errors="ignore")
    creationflags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW on Windows
    p = subprocess.Popen(args, stdout=lf, stderr=lf, creationflags=creationflags)
    return p

# Heuristic readiness regex patterns (case-insensitive)
_READINESS_PATTERNS = [
    re.compile(r"\bserial\d*\b.*\bTCP\b", re.IGNORECASE),        # "SERIAL0 on TCP ..."
    re.compile(r"\blistening\b.*\btcp\b", re.IGNORECASE),        # "Listening on TCP ..."
    re.compile(r"\bbound\b.*\b127\.0\.0\.1\b", re.IGNORECASE),   # "Bound to 127.0.0.1:..."
    re.compile(r"\bconnected\b.*\btcp\b", re.IGNORECASE),        # "Connected to tcp:..."
    re.compile(r"\bSITL\b.*\brunning\b", re.IGNORECASE),         # "SITL ... running"
    re.compile(r"\bmavlink\b.*\bconnected\b", re.IGNORECASE),    # "MAVLink connected"
]

def check_log_for_readiness(logpath: Path, start_pos: int) -> (bool, int, str):
    """
    Read new lines from logpath starting at start_pos (byte offset).
    Return (found_flag, new_pos, matched_line_or_empty).
    """
    try:
        with logpath.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(start_pos)
            data = f.read()
            new_pos = f.tell()
    except FileNotFoundError:
        return False, start_pos, ""
    if not data:
        return False, new_pos, ""
    # scan lines
    for line in data.splitlines():
        for rx in _READINESS_PATTERNS:
            if rx.search(line):
                return True, new_pos, line.strip()
    return False, new_pos, ""

def wait_for_ardup_ready_by_log(proc: subprocess.Popen, logpath: Path, timeout: float) -> bool:
    """
    Wait until the arducopter process writes a readiness pattern into logpath.
    Returns True if readiness detected, False on timeout or process exit.
    """
    deadline = time.time() + timeout
    # start reading from end of existing file to only look at new lines
    try:
        start_pos = logpath.stat().st_size
    except FileNotFoundError:
        start_pos = 0
    while time.time() < deadline:
        # if process exited early, stop waiting
        if proc.poll() is not None:
            # process died; no readiness
            return False
        found, start_pos, matched = check_log_for_readiness(logpath, start_pos)
        if found:
            # readiness confirmed
            print(f"[watchdog] readiness detected in {logpath}: {matched}")
            return True
        time.sleep(LOG_POLL_INTERVAL)
    return False

def start_mavproxy_in_cmd(tcp_port: int, gcs_addr: str, gcs_port: int,sec_addr:str,
                          per_udp: int, sysid: int, logdir: Path, mavproxy_cmd: str = None,
                          keep_open: bool = True) -> subprocess.Popen:
    """
    Launch MAVProxy in a new Windows cmd.exe window using 'start'.
    keep_open True  -> use cmd /k (window stays open)
    keep_open False -> use cmd /c (window closes when process exits)
    On non-Windows, runs headless and logs to mavproxy.log.
    """
    logdir.mkdir(parents=True, exist_ok=True)
    mav_log = logdir / "mavproxy.log"
    outs = [f"--out=udp:{gcs_addr}:{gcs_port}", f"--out=udp:{sec_addr}:{per_udp}"]

    if mavproxy_cmd:
        cmd_list = [mavproxy_cmd, f"--master=tcp:127.0.0.1:{tcp_port}"] + outs + ["--no-console","--nowait", "-c", "--udp-timeout=50", "--force-connected"]
    else:
        cmd_list = [sys.executable, "-m", "MAVProxy", f"--master=tcp:127.0.0.1:{tcp_port}"] + outs + ["--nowait", "-c", "--udp-timeout=50", "--force-connected"]

    if os.name == "nt":
        cmdline = subprocess.list2cmdline(cmd_list)
        cmd_option = "/k" if keep_open else "/c"
        full_cmd = f'start "MAVProxy sysid={sysid}" cmd {cmd_option} {cmdline}'
        p = subprocess.Popen(full_cmd, shell=True)
    else:
        lf = open(mav_log, "a", buffering=1, encoding="utf-8", errors="ignore")
        p = subprocess.Popen(cmd_list, stdout=lf, stderr=lf)
    print(f"[mavproxy] sysid={sysid} launched (tcp:{tcp_port}) -> udp:{gcs_addr}:{gcs_port} (per-drone udp {per_udp})")
    return p

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--exe", required=True, help="path to arducopter executable")
    p.add_argument("--model", default="quad")
    p.add_argument("-n", "--count", type=int, default=2)
    p.add_argument("--spacing", type=float, default=10.0)
    p.add_argument("--home-lat", type=float, default=13.0067)
    p.add_argument("--home-lon", type=float, default=80.2570)
    p.add_argument("--home-alt", type=float, default=5.0)
    p.add_argument("--gcs-address", default="127.0.0.1")
    p.add_argument("--gcs-port", type=int, default=14550)
    p.add_argument("--sec-address", type=str, default=None)
    p.add_argument("--base-port", type=int, default=5670, help="starting base port (unique per instance using stride)")
    p.add_argument("--start-sysid", type=int, default=1)
    p.add_argument("--log-dir", default="./logs")
    p.add_argument("--keep-open", action="store_true", help="Keep cmd windows open after MAVProxy starts (cmd /k)")
    args = p.parse_args()
    
    if args.sec_address == None:
        secondary_ip =  get_interface_mapping() 
    else:
        secondary_ip = "192.168.6.220"

    exe_path = Path(args.exe).resolve()
    if not exe_path.exists():
        print("ERROR: arducopter exe not found:", exe_path)
        sys.exit(2)

    log_root = Path(args.log_dir).resolve() / "arducopter"
    log_root.mkdir(parents=True, exist_ok=True)

    mavproxy_cmd = find_mavproxy_cmd()
    if mavproxy_cmd:
        print("Using global MAVProxy:", mavproxy_cmd)
    else:
        print("No MAVProxy executable found on PATH. Will use python -m MAVProxy.")

    homes = compute_homes(args.count, args.home_lat, args.home_lon, args.spacing)

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
                # Launch arducopter headless (no console)
                p = launch_arducopter(exe_path, i, info["sysid"], args.model, lat, lon, args.home_alt, info["base_port_for_instance"], info["logdir"])
                info["ardup"] = p

                # Wait for readiness by scanning arducopter.log (no socket)
                ardup_log = info["logdir"] / "arducopter.log"
                ready = wait_for_ardup_ready_by_log(p, ardup_log, PORT_WAIT_TIMEOUT)
                if not ready:
                    print(f"[WARN] sysid={info['sysid']} readiness not detected within {PORT_WAIT_TIMEOUT}s (check {ardup_log})")
                    # proceed anyway (or you can choose to return/raise here)
                # Start MAVProxy (cmd window on Windows)
                if os.name == "nt":
                    info["mavp"] = start_mavproxy_in_cmd(info["tcp_port"], args.gcs_address, args.gcs_port,secondary_ip, info["per_udp"], info["sysid"], info["logdir"], mavproxy_cmd, keep_open=args.keep_open)
                else:
                    info["mavp"] = start_mavproxy_headless(info["tcp_port"], args.gcs_address, args.gcs_port, info["per_udp"], info["sysid"], info["logdir"], mavproxy_cmd)

            futures.append(ex.submit(start_instance))

        # wait for all startup tasks to finish
        for fut in futures:
            try:
                fut.result()
            except Exception as e:
                print("Instance start raised:", e)

    print(f"All instances started. Logs under: {log_root}")
    try:
        while True:
            alive_ard = sum(1 for i in instances.values() if i["ardup"] and i["ardup"].poll() is None)
            # For MAVProxy launched via cmd 'start', poll may not reflect actual child; just count launched entries
            alive_mav_launched = sum(1 for i in instances.values() if i.get("mavp") is not None)
            print(f"Alive ardup: {alive_ard}/{args.count}   mavproxy (launched): {alive_mav_launched}/{args.count}", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all children...")
        for info in instances.values():
            if info.get("mavp"):
                try:
                    info["mavp"].terminate()
                except Exception:
                    pass
            if info.get("ardup"):
                try:
                    info["ardup"].terminate()
                except Exception:
                    pass
        print("Done. Exiting.")
        sys.exit(0)
     


if __name__ == "__main__":
    main()
