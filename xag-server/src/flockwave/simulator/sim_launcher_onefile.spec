# -*- mode: python ; coding: utf-8 -*-
# Single-file (onefile) build of the SITL simulator launcher.
# Mirrors sim_launcher.spec but produces one self-contained sim_launcher.exe
# instead of a onedir folder.

a = Analysis(
    ['sim_launcherv2.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='sim_launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
