# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('swarm_tasks\\envs\\worlds', 'swarm_tasks\\envs\\worlds')]
binaries = []
hiddenimports = ['swarm_tasks.utils', 'swarm_tasks.envs', 'swarm_tasks.simulation.simulation', 'swarm_tasks.simulation.visualizer', 'swarm_tasks.controllers.command', 'swarm_tasks.controllers', 'swarm_tasks.controllers.base_control', 'swarm_tasks.controllers.potential_field', 'swarm_tasks.modules.dispersion', 'swarm_tasks.modules.exploration', 'swarm_tasks.modules.formations.line', 'swarm_tasks.modules.formations.circle', 'swarm_tasks.utils.weight_functions', 'swarm_tasks.tasks.area_coverage', 'locatePosition', 'mission_paths', 'geopy.distance', 'geopy.point', 'simplekml', 'matplotlib.pyplot', 'numpy', 'mavproxy', 'lxml', 'bezier_curve', 'groupsplitauto', 'bezier_curve_multiple', 'groupsplitspecific', 'netifaces', 'wmi', 'yaml', 'shapely.geometry']
tmp_ret = collect_all('dronekit')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pymavlink')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('lxml')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('shapely')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['swarm_tasks\\Examples\\basic_tasks\\vtol_demo.py'],
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
    name='vtol_demo',
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
