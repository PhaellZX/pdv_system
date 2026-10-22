# build_scripts/server.spec
# -*- mode: python ; coding: utf-8 -*-
import os
import prophet
from PyInstaller.utils.hooks import collect_submodules

# Resolve project root directory relative to the build_scripts folder
project_root = os.path.abspath(os.path.join(SPECPATH, ".."))
prophet_path = os.path.dirname(prophet.__file__)

a = Analysis(
    [os.path.join(project_root, 'run_server.py')],  # Entry point points to root run_server.py
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(prophet_path, '*'), 'prophet/'),
        (os.path.join(project_root, 'assets', 'fonts', 'DejaVuSansMono.ttf'), 'assets/fonts')
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pandas',
        'prophet',
        'holidays',
        'lunarcalendar',
        'passlib.handlers.bcrypt',  # CryptContext bcrypt dependency
        *collect_submodules('prophet'),
        *collect_submodules('pandas')
    ],
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
    name='server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True  # Kept as True to retain stdout logs for Uvicorn background process
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='server'
)