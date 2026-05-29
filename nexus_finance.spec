# PyInstaller spec for Nexus Finance (run: build_exe.bat)
from PyInstaller.utils.hooks import collect_all

block_cipher = None

hiddenimports = [
    "pandas",
    "matplotlib.backends.backend_tkagg",
    "tksheet",
    "views",
    "views.dashboard",
    "views.transactions",
    "views.settings",
    "views.calculators",
    "views.calc_ui",
    "calculators",
    "calc_charts",
    "charts",
    "db",
    "models",
    "dates",
    "balances",
    "paths",
]

datas = []
binaries = []

for pkg in ("customtkinter", "matplotlib"):
    tmp = collect_all(pkg)
    datas += tmp[0]
    binaries += tmp[1]
    hiddenimports += tmp[2]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Nexus Finance",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Nexus Finance",
)
