# app.spec
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['login_app.py'], # Ponto de entrada é a tela de login
    pathex=[],
    binaries=[],
    datas=[
        ('icon.png', '.'),
        # Inclui os temas da interface para o ttkbootstrap funcionar
        *collect_data_files('ttkbootstrap')
    ],
    hiddenimports=[], # Geralmente não precisa de hidden imports
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
    name='PDVSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # console=False para não mostrar o terminal
    icon='icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDVSystem'
)