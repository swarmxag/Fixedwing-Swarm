# -*- mode: python -*-

from importlib import import_module
from pathlib import Path
import os
import sys
import site
import glob

from PyInstaller import __version__ as pyinstaller_version
from PyInstaller.utils.hooks import collect_submodules

# -------------------------------------------------------------------------
# Increase recursion limit
# -------------------------------------------------------------------------
sys.setrecursionlimit(sys.getrecursionlimit() * 10)

name = "operation_server"
single_file = False    # Produce ONEDIR directory-style build

root_dir = Path.cwd()
src_dir = root_dir / "src"

# -------------------------------------------------------------------------
# Encryption (optional, unchanged from original)
# -------------------------------------------------------------------------
key = os.environ.get("PYINSTALLER_KEY")

if pyinstaller_version >= "4.0":
    if not key:
        import secrets
        key = secrets.token_urlsafe(24)
else:
    if key:
        raise RuntimeError("Encryption not supported")

# -------------------------------------------------------------------------
# Prevent TkInter from being bundled
# -------------------------------------------------------------------------
sys.modules["FixTk"] = None

# -------------------------------------------------------------------------
# Extra modules to include (from your original)
# -------------------------------------------------------------------------
extra_modules = set([
    "flockwave.server.config",
    "scipy._lib.array_api_compat.numpy.fft",
    "scipy._lib.array_api_compat.numpy.linalg",
    "scipy._lib.array_api_compat.numpy.random",
])

# -------------------------------------------------------------------------
# Excluded modules
# -------------------------------------------------------------------------
exclude_modules = [
    "FixTk", "tcl", "tk", "_tkinter", "tkinter", "Tkinter",
    "lxml"
]

# -------------------------------------------------------------------------
# Load server configuration
# -------------------------------------------------------------------------
config_file = src_dir / "flockwave" / "server" / "config.py"
config = {}
exec(
    compile(open(config_file).read(), "config.py", "exec", dont_inherit=True),
    None,
    config
)

# -------------------------------------------------------------------------
# Extension helpers
# -------------------------------------------------------------------------
def extension_module(name):
    return f"flockwave.server.ext.{name}"

def is_extension_module(name):
    return name.startswith("flockwave.server.ext.")

# Add ext manager + configured extensions
extra_modules.add(extension_module("ext_manager"))
extra_modules.update(
    extension_module(ext)
    for ext in config["EXTENSIONS"]
    if not ext.startswith("_")
)

# -------------------------------------------------------------------------
# Resolve dependencies recursively (your original logic)
# -------------------------------------------------------------------------
changed = True
while changed:
    changed = False
    for module_name in sorted(extra_modules):
        if is_extension_module(module_name):
            try:
                imported = import_module(module_name)
                deps = set()

                if hasattr(imported, "get_dependencies"):
                    deps.update(imported.get_dependencies())
                elif hasattr(imported, "dependencies"):
                    deps.update(imported.dependencies)

                new = {extension_module(d) for d in deps} - extra_modules
                if new:
                    extra_modules.update(new)
                    changed = True

            except ImportError:
                pass

flockwave_src = r"C:\Users\Joel\Desktop\Fixedwing-Swarm\xag-server\venv\Lib\site-packages\flockwave"

# Copy whole flockwave folder into application
datas = [
    (flockwave_src, "flockwave")   # <--- FULL PACKAGE COPY
]

hiddenimports = collect_submodules("flockwave")

# -------------------------------------------------------------------------
# PyInstaller analysis
# -------------------------------------------------------------------------

hookspath = [
        str(root_dir / "etc" / "deployment" / "pyinstaller"),
        #str(root_dir / "etc" / "deployment" / "pyinstaller" / "pre_safe_import_module"),
]


runtime_hooks = [str(root_dir / "etc" / "deployment" / "pyinstaller" / "runtime_hook.py")]
'''
        str(root_dir
        / "etc"
        / "deployment"
        / "pyinstaller"
        / "hook-flockwave.server.ext.frontend.py"),
    str(
        root_dir
        / "etc"
        / "deployment"
        / "pyinstaller"
        / "hook-flockwave.server.ext.mavlink.py"
    ),
    str(
        root_dir
        / "etc"
        / "deployment"
        / "pyinstaller"
        / "hook-flockwave.server.ext.socketio.vendor.engineio_v3.py"
    ),
    str(
        root_dir
        / "etc"
        / "deployment"
        / "pyinstaller"
        / "hook-flockwave.server.ext.socketio.vendor.engineio_v4.py"
    ),
    str(
        root_dir
        / "etc"
        / "deployment"
        / "pyinstaller"
        / "hook-flockwave.server.ext.webui.py"
    ),
    str(root_dir / "etc" / "deployment" / "pyinstaller" / "hook-flockwave.spec.py"),
    str(root_dir / "etc" / "deployment" / "pyinstaller" / "hook-igrf_model.py"),
    str(root_dir / "etc" / "deployment" / "pyinstaller" / "pre_safe_import_module" / "hook-flockwave.protocols.py"),
    str(root_dir / "etc" / "deployment" / "pyinstaller" / "pre_safe_import_module" / "hook-flockwave.py")
]'''

a = Analysis(
    [str(src_dir / "flockwave" / "server" / "__main__.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=sorted(extra_modules),
    hookspath=hookspath,
    runtime_hooks=runtime_hooks,
    excludes=exclude_modules,
)

pyz = PYZ(a.pure, a.zipped_data)

# -------------------------------------------------------------------------
# EXE (ONEDIR MODE)
# -------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name=name,
    debug=False,
    strip=False,
    upx=True,
    console=True,
    entitlements_file=None )




coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name=name
)
