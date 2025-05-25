# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AV1 to HEVC Converter
This creates both GUI and console versions of the application
"""

import os

block_cipher = None

# Analysis for GUI version
a_gui = Analysis(
    ['gui_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=['tkinter', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# Analysis for Console version
a_console = Analysis(
    ['av1_to_hevc.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=['click', 'colorama', 'tqdm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],  # Don't need tkinter for console version
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# Create PYZ archives
pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)
pyz_console = PYZ(a_console.pure, a_console.zipped_data, cipher=block_cipher)

# GUI executable
exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    a_gui.binaries,
    a_gui.zipfiles,
    a_gui.datas,
    [],
    name='AV1toHEVC-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None
)

# Console executable
exe_console = EXE(
    pyz_console,
    a_console.scripts,
    a_console.binaries,
    a_console.zipfiles,
    a_console.datas,
    [],
    name='AV1toHEVC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None
)

# Collection (not used for onefile build)
coll = COLLECT(
    exe_gui,
    exe_console,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AV1toHEVC'
) 