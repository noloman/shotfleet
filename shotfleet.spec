# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('.build/ocr', '.build')]
datas += collect_data_files('certifi')


a = Analysis(
    ['shotfleet.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name='shotfleet',
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
    codesign_identity='Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)',
    entitlements_file='tools/entitlements.plist',
)
