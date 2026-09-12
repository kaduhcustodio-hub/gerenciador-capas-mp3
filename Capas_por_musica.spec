# -*- mode: python ; coding: utf-8 -*-
"""
Arquivo de configuracao do PyInstaller para gerar o .exe
do Gerenciador de Capas e Metadados para MP3.

Uso:
    python -m PyInstaller --clean --noconfirm Capas_por_musica.spec
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

# =====================================================================
# Dados (arquivos que vao embutidos no .exe)
# =====================================================================
datas = []
hiddenimports = []

# --- Pasta i18n (arquivos JSON de traducao) ---
if os.path.isdir("i18n"):
    for arq in os.listdir("i18n"):
        if arq.endswith(".json"):
            datas.append((os.path.join("i18n", arq), "i18n"))
    print(f"[spec] Incluindo {len(datas)} arquivo(s) da pasta i18n/")

# --- Icone PNG (usado pelo iconphoto em runtime) ---
if os.path.exists("icon.png"):
    datas.append(("icon.png", "."))

# --- tkinterdnd2 (DLLs do TkDnD) ---
try:
    datas += collect_data_files("tkinterdnd2")
    hiddenimports += collect_submodules("tkinterdnd2")
except Exception as e:
    print(f"[spec] Aviso: tkinterdnd2 nao encontrado: {e}")

# --- Icone do EXE ---
icone = "icon.ico" if os.path.exists("icon.ico") else (
    "icon.png" if os.path.exists("icon.png") else None
)

# =====================================================================
# Analise
# =====================================================================
a = Analysis(
    ["Capas_por_musica.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports + [
        "mutagen.id3",
        "mutagen.mp3",
        "PIL._tkinter_finder",
        "pygame",
        "i18n",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "IPython",
        "notebook",
        "pytest",
        "setuptools",
        "pip",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GerenciadorCapas",
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
    icon=icone,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GerenciadorCapas",
)