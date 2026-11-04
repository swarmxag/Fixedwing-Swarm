"""Pack only what the swarm computer needs.

Run from anywhere:   python tools/build_swarm_bundle.py

Output (the repo itself is never modified):
  swarm_deploy/swarm_computer/    copy this to the onboard computer, then run
                                  swarm_tasks/Examples/basic_tasks/medur_fixed_wing.py
  swarm_deploy/unused_for_swarm/  every other file of fixed_wing_windows_exe
                                  (old scripts, terrain tiles, tests, examples),
                                  plus MANIFEST.txt saying why each is unused

"Needed" is computed, not hand-listed: modulefinder follows every import of
medur_fixed_wing.py, including imports inside functions, so re-running this
after a code change always packs the current set. The bundle keeps the same
folder layout, so no import has to change. At the end every bundled module is
imported from the bundle alone (flight hardware libraries stubbed) to prove
nothing is missing.
"""

import json
import os
import shutil
import subprocess
import sys
import sysconfig
import textwrap
from modulefinder import ModuleFinder

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXE = os.path.join(REPO, "fixed_wing_windows_exe")
BASIC_REL = os.path.join("swarm_tasks", "Examples", "basic_tasks")
ENTRY_REL = os.path.join(BASIC_REL, "medur_fixed_wing.py")
OUT = os.path.join(REPO, "swarm_deploy")
NEEDED_DIR = os.path.join(OUT, "swarm_computer")
UNUSED_DIR = os.path.join(OUT, "unused_for_swarm")

# Data files read at runtime (not imports). The program only ever loads the
# "rectangles" world (state.file_name); it is overwritten by every geofence.
DATA_FILES = [os.path.join("swarm_tasks", "envs", "worlds", "rectangles.yaml")]

# Third-party packages the bundled code imports (pip names).
REQUIREMENTS = [
    "dronekit",
    "pymavlink",
    "numpy",
    "scipy",
    "shapely",
    "pandas",
    "matplotlib",
    "PyYAML",
    "netifaces",
    "simplekml",
    "geopy",
]

SKIP_PARTS = {"venv", "__pycache__", ".git", ".pytest_cache"}


def needed_modules():
    stdlib = [sysconfig.get_paths()["stdlib"], sysconfig.get_paths()["platstdlib"]]
    basic = os.path.join(EXE, BASIC_REL)
    finder = ModuleFinder(path=[basic, EXE] + stdlib)  # the program's own search order
    finder.run_script(os.path.join(EXE, ENTRY_REL))
    files = set()
    for mod in finder.modules.values():
        f = getattr(mod, "__file__", None)
        if not f or not os.path.abspath(f).lower().startswith(EXE.lower() + os.sep):
            continue  # stdlib / other drives
        rel = os.path.relpath(os.path.abspath(f), EXE)
        # Only project files under swarm_tasks/. (A stdlib module importing its
        # own "test" package shows up as fixed_wing_windows_exe/test.py in this
        # scan; the program never imports that file.)
        if rel.startswith("swarm_tasks" + os.sep) and not (
            set(rel.split(os.sep)) & SKIP_PARTS
        ):
            files.add(rel)
    return sorted(files)


def all_files():
    for root, dirs, names in os.walk(EXE):
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        for n in names:
            if n.endswith(".pyc"):
                continue
            yield os.path.relpath(os.path.join(root, n), EXE)


def reason(rel):
    p = rel.replace("\\", "/")
    if "/medur_swarm/tests/" in p:
        return "development tests (run on the laptop, not needed to fly)"
    if p.endswith(".hgt") or "/terrain" in p:
        return "terrain code/tiles: nothing in the running program imports terrain_* (the gate is commented out)"
    if (
        "/oldfiles/" in p
        or "backup" in p
        or "_old" in p
        or "(copy)" in p
        or "before_seperate" in p
    ):
        return "old / backup version of the swarm script"
    if p.endswith((".png", ".jpg", ".kml", ".csv", ".log", ".txt", ".md", ".spec")):
        return "document, picture, log or generated output"
    if "/envs/worlds/" in p or "/envs/items/" in p:
        return "world/items file the program never loads (it only uses rectangles.yaml)"
    if p.startswith("swarm_tasks/Examples/full_tasks/") or p.startswith(
        "swarm_tasks/tests/"
    ):
        return "library example/test script"
    return "not imported by medur_fixed_wing.py"


def copy(rel, dest_root):
    dst = os.path.join(dest_root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(EXE, rel), dst)


def verify(bundle, modules):
    """Import every bundled module from the bundle alone, in a fresh interpreter."""
    names = []
    for rel in modules:
        if not rel.endswith(".py"):
            continue
        parts = rel[:-3].split(os.sep)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts[:3] == ["swarm_tasks", "Examples", "basic_tasks"]:
            parts = parts[3:]  # importable from basic_tasks (the script's own folder)
        if parts and parts[-1] != "medur_fixed_wing":
            names.append(".".join(parts))
    code = textwrap.dedent("""
        import importlib, json, os, sys, types
        bundle, basic = sys.argv[1], sys.argv[2]
        sys.path[:0] = [basic, bundle]          # same as running the entry script
        class _Any:
            def __getattr__(self, n): return _Any()
            def __call__(self, *a, **k): return _Any()
            def __iter__(self): return iter(())
        for n in ("dronekit", "pymavlink", "pymavlink.mavutil", "netifaces", "wmi"):
            m = types.ModuleType(n); m.__getattr__ = lambda a: _Any(); sys.modules[n] = m
        import matplotlib; matplotlib.use("Agg")
        bad, outside = [], []
        for name in json.loads(sys.argv[3]):
            try:
                mod = importlib.import_module(name)
            except Exception as e:
                bad.append("%s: %r" % (name, e)); continue
            f = os.path.abspath(getattr(mod, "__file__", "") or "")
            if f and not f.startswith(os.path.abspath(bundle)):
                outside.append("%s -> %s" % (name, f))
        print(json.dumps({"bad": bad, "outside": outside, "count": len(json.loads(sys.argv[3]))}))
        """)
    env = dict(
        os.environ,
        PYTHONPATH="",
        SWARM_CMD_PORT="12798",
        SWARM_CTL_PORT="12792",
        SWARM_STATE_DIR=os.path.join(OUT, "_verify_state"),
    )
    res = subprocess.run(
        [
            sys.executable,
            "-W",
            "ignore",
            "-c",
            code,
            bundle,
            os.path.join(bundle, BASIC_REL),
            json.dumps(names),
        ],
        cwd=os.path.join(bundle, BASIC_REL),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    shutil.rmtree(os.path.join(OUT, "_verify_state"), ignore_errors=True)
    lines = [l for l in res.stdout.splitlines() if l.startswith("{")]
    if not lines:
        raise SystemExit("verification did not run:\n" + res.stderr[-3000:])
    return json.loads(lines[-1])


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    with open(os.path.join(OUT, ".gitignore"), "w") as f:
        f.write("# generated by tools/build_swarm_bundle.py -- never commit\n*\n")

    modules = needed_modules()
    needed = modules + [d for d in DATA_FILES if os.path.exists(os.path.join(EXE, d))]
    needed_set = set(needed)
    for rel in needed:
        copy(rel, NEEDED_DIR)
    with open(os.path.join(NEEDED_DIR, "requirements.txt"), "w") as f:
        f.write(
            "\n".join(REQUIREMENTS)
            + "\n# wmi is only used on Windows; not needed on Linux\n"
        )
    with open(os.path.join(NEEDED_DIR, "README_DEPLOY.txt"), "w") as f:
        f.write(textwrap.dedent("""\
            Swarm computer bundle (generated by tools/build_swarm_bundle.py).

            Contains only what medur_fixed_wing.py imports, in the original folder layout.
            Install:  pip install -r requirements.txt
            Run:      export SWARM_NODE_ID=<this node's id>
                      cd swarm_tasks/Examples/basic_tasks
                      python3 medur_fixed_wing.py
            Then press Set Origin in the GUI before promoting this node.
            """))

    unused = [rel for rel in sorted(all_files()) if rel not in needed_set]
    for rel in unused:
        copy(rel, UNUSED_DIR)
    by_reason = {}
    for rel in unused:
        by_reason.setdefault(reason(rel), []).append(rel)
    with open(os.path.join(UNUSED_DIR, "MANIFEST.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Files of fixed_wing_windows_exe NOT needed on the swarm computer.\n"
            "Copies only -- the originals are untouched in the repo.\n\n"
        )
        for why, files in sorted(by_reason.items()):
            f.write("== %s (%d)\n" % (why, len(files)))
            f.writelines("   %s\n" % r for r in files)
            f.write("\n")

    result = verify(NEEDED_DIR, modules)
    size = lambda d: sum(
        os.path.getsize(os.path.join(r, n)) for r, _, ns in os.walk(d) for n in ns
    )
    print(
        "needed : %3d files, %6.2f MB -> %s"
        % (len(needed), size(NEEDED_DIR) / 1e6, NEEDED_DIR)
    )
    print(
        "unused : %3d files, %6.2f MB -> %s"
        % (len(unused), size(UNUSED_DIR) / 1e6, UNUSED_DIR)
    )
    print("import check: %d modules imported from the bundle" % result["count"])
    for b in result["bad"]:
        print("  IMPORT ERROR", b)
    for o in result["outside"]:
        print("  LOADED FROM OUTSIDE THE BUNDLE", o)
    if result["bad"] or result["outside"]:
        raise SystemExit(1)
    print("OK: no import errors, nothing loaded from outside the bundle")


if __name__ == "__main__":
    main()
