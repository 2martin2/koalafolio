# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['koalafolio\\gui_root.py'],
    pathex=[],
    binaries=[],
    datas=[('koalafolio/Import/defaultApiData.db', 'Import'), ('koalafolio/koalaicon.ico', '.'), ('koalafolio/koalaicon.png', '.'), ('koalafolio/graphics/', 'graphics')],
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
    [],
    exclude_binaries=True,
    name='koalafolio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['koalafolio\\KoalaIcon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='koalafolio',
)
