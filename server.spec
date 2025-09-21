# server.spec
# -*- mode: python ; coding: utf-8 -*-
import os
import prophet
from PyInstaller.utils.hooks import collect_submodules

prophet_path = os.path.dirname(prophet.__file__)

a = Analysis(
    ['run_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(prophet_path, '*'), 'prophet/'),
        ('DejaVuSansMono.ttf', '.')
    ],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols',
        'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.lifespan',
        'uvicorn.lifespan.on', 'pandas', 'prophet', 'holidays', 'lunarcalendar',
        *collect_submodules('prophet'), 
        *collect_submodules('pandas'),
        'passlib.handlers.bcrypt' # <-- ADICIONE ESTA LINHA
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, exclude_binaries=True,
    name='server', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, name='server'
)