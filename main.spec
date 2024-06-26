# -*- mode: python ; coding: utf-8 -*-

from glob import glob
block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas = [],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

a.datas += [("icon.ico","icon.ico","DATA")]
a.datas += [("style.qss","style.qss","DATA")]
a.datas += Tree('./database', prefix='database')
a.datas += Tree('./translations', prefix='translations')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sims 4 Mods Translator',
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
    icon=['icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main'
)
