# -*- mode: python ; coding: utf-8 -*-
import os
import site
from pathlib import Path

block_cipher = None

# Get Python site-packages directory dynamically
python_lib_path = site.getsitepackages()[0]
coincurve_dll_path = os.path.join(python_lib_path, 'Lib', 'site-packages', 'coincurve', 'libsecp256k1.dll')

a = Analysis(
    ['koalafolio\\gui_root.py'],
    pathex=[],
    binaries=[(coincurve_dll_path, 'coincurve')],
    datas=[('koalafolio/Import/defaultApiData.db','Import'),
           ('koalafolio/koalaicon.ico','.'),
           ('koalafolio/KoalaIcon.png','.'),
           ('koalafolio/graphics','graphics')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='koalafolio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['koalafolio\\KoalaIcon.ico'],
)