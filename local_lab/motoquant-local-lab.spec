# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MotoQuant Local Lab.

One-file executable bundling the full physics engine, the seeded 541-bike
catalog DB, the numpy surrogate, and the desktop UI's static build. On
launch it starts uvicorn on localhost and opens the browser — the whole
product running on the operator's own CPU (see local_lab/entry.py).

Build (from the repo root)::

    # 1. Build the UI in Local Lab mode (same-origin API, no auth gate)
    cd desktop && VITE_LOCAL_LAB=1 npx vite build && cd ..
    # 2. Freeze
    pip install -r requirements-api.txt pyinstaller
    pyinstaller local_lab/motoquant-local-lab.spec --clean --noconfirm
    # -> dist/MotoQuantLocalLab(.exe)

Descends from the retired desktop/sidecar/motoquant-backend.spec (removed
in the June-13 hosted-only re-arch; recovered via git show b52f4b5^:...).
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# Spec is invoked from the repo root (pyinstaller local_lab/<spec>), and
# PyInstaller sets CWD to where the command runs.
REPO_ROOT = Path(os.getcwd())

# ── Data files ────────────────────────────────────────────────────────────
DB_PATH = REPO_ROOT / "motoquant.db"
assert DB_PATH.exists(), f"Expected seeded DB at {DB_PATH}"

# entry.py copies the DB out of the one-file extraction dir to a persistent
# per-user location on first boot, so saved runs survive restarts.
datas = [(str(DB_PATH), ".")]

# Only the pure-numpy surrogate the runtime loader actually reads — lands at
# <MEIPASS>/artifacts/surrogate/ which is exactly where api._load_surrogate()
# resolves (Path(__file__).parent.parent == sys._MEIPASS when frozen).
SURROGATE_NPZ = REPO_ROOT / "artifacts" / "surrogate" / "surrogate_numpy.npz"
assert SURROGATE_NPZ.exists(), f"Expected surrogate at {SURROGATE_NPZ}"
datas.append((str(SURROGATE_NPZ), "artifacts/surrogate"))

# The desktop UI's static build (vite -> desktop/dist), served same-origin
# by the API when MOTOQUANT_LOCAL_UI is set (entry.py points it here).
UI_DIST = REPO_ROOT / "desktop" / "dist"
assert (UI_DIST / "index.html").exists(), (
    f"Expected built UI at {UI_DIST} - run: cd desktop && VITE_LOCAL_LAB=1 npx vite build"
)
datas.append((str(UI_DIST), "ui"))

# ── Hidden imports ────────────────────────────────────────────────────────
hiddenimports = (
    collect_submodules("motoquant")
    + [
        "uvicorn",
        "uvicorn.config",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.wsproto_impl",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "h11",
        "anyio._backends._asyncio",
        "fastapi",
        "pydantic",
    ]
)

# ── Excludes ──────────────────────────────────────────────────────────────
# Heavy deps only used by offline training / hosted-only features. All are
# behind try/except or lazy imports in motoquant (verified July 8 recon):
#  - torch/sklearn/xgboost/SALib: surrogate TRAINING + Sobol, offline only
#    (runtime inference is the pure-numpy npz)
#  - jose/razorpay/sentry_sdk: auth/payments/telemetry — pointless on a
#    single-user local box; api.py degrades gracefully (require_tier stub,
#    routers skip mounting). anthropic/openai are KEPT so chat works when
#    the operator exports a provider key. scipy is KEPT for the Dragy
#    calibrator + Sobol sampling paths.
excludes = [
    "matplotlib",
    "notebook",
    "jupyter",
    "pytest",
    "sphinx",
    "torch",
    "tensorflow",
    "sklearn",
    "xgboost",
    "SALib",
    "streamlit",
    "jose",
    "razorpay",
    "sentry_sdk",
]

a = Analysis(
    [str(REPO_ROOT / "local_lab" / "entry.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MotoQuantLocalLab",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Console stays on: uvicorn logs + per-request lines ARE the stress-test
    # telemetry the operator wants to watch.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
