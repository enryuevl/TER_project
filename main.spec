# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
import sys
import os

block_cipher = None
win32com_modules = collect_submodules('win32com.client')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
    'comtypes',
    'win32com',
    'win32com.client',
    'win32com.server',
    'pywintypes',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TER_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True  # Set to False if you want no console window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='TER_App'
)
