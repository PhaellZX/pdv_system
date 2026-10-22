# build_scripts/app.spec
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

# Resolve project root path relative to the build_scripts folder
project_root = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(project_root, 'src', 'views', 'login_view.py')],  # Entry point points to src/views/login_view.py
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'assets', 'icons', 'icon.png'), 'assets/icons'),
        (os.path.join(project_root, 'assets', 'fonts', 'DejaVuSansMono.ttf'), 'assets/fonts'),
        # Include ttkbootstrap interface themes data files
        *collect_data_files('ttkbootstrap')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='POSSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # console=False hides the terminal window
    icon=os.path.join(project_root, 'assets', 'icons', 'icon.ico')
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='POSSystem'
)