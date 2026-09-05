# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ('etc/conf/skybrush-virtual.jsonc', 'etc/conf'),
    ('etc/conf/skybrush-indoor.jsonc', 'etc/conf'),
    ('etc/conf/skybrush-indoor-dual.jsonc', 'etc/conf'),
    ('etc/conf/skybrush-outdoor.jsonc', 'etc/conf'),

]
binaries = []
hiddenimports = collect_submodules('flockwave.server.ext')

for package in ('flockwave', 'pymavlink', 'trio', 'quart', 'quart_trio', 'hypercorn'):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ['run_skybrushd.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='skybrushd',
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
