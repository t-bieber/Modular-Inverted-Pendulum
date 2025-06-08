# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

# Use absolute path of the spec file itself to get to project root
project_root = os.path.dirname(r"C:\Users\tb112\Documents\IP_Aufbau_neu\Modular-Inverted-Pendulum\control\python_pc\main.py")
controllers_path = os.path.join(project_root, "controllers")
gui_path = os.path.join(project_root, "gui")

# Discover dynamically-loaded modules
hidden_imports = collect_submodules("controllers")

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
        datas=[
        (os.path.join("controllers", "*.py"), "controllers"),
        (os.path.join("gui", "*.py"), "gui"),
    ],
    hiddenimports=hidden_imports,
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
    name='InvertedPendulumGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False  # Set to True if you want a terminal window too
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='InvertedPendulumGUI'
)
