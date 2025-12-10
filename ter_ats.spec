# ter_ats.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys

# Entry script: login.py (this launches LoginApp, which then calls main.create_app)
entry_script = 'login.py'

# Extra data files to include (source, target_dir_inside_dist)
datas = [
    ('logo.png', '.'),
    ('dashboard.png', '.'),
    ('scan.png', '.'),
    ('admin.png', '.'),
    ('results.png', '.'),
    ('accounts.png', '.'),
    ('logout.png', '.'),
    # core data files
    ('ter_db2.sqlite', '.'),
    ('results.pkl', '.'),
    ('template.xlsx', '.'),
    ('summary.xlsx', '.'),
]

a = Analysis(
    [entry_script],
    pathex=[os.path.abspath('.')],   # project root
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
    optimize=0,
    strip=False,
    upx=True,
    upx_exclude=[],
    cipher=block_cipher,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TER_ATS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,    # GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,        # you can set an .ico here later
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TER_ATS',
)
