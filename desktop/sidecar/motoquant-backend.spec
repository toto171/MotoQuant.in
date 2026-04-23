# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the MotoQuant backend sidecar.

Produces a single-file executable named ``motoquant-backend`` that launches
the FastAPI server (uvicorn + motoquant.api) on a host/port supplied by
Tauri. See ``sidecar_entry.py`` for the launcher details.

Usage::

    cd desktop/sidecar
    pip install -r requirements-sidecar.txt     # includes pyinstaller
    pyinstaller motoquant-backend.spec --clean --noconfirm
    # → dist/motoquant-backend(.exe)

Output name is plain ``motoquant-backend`` — rename to the Rust target
triple before dropping into ``desktop/src-tauri/bin/`` (see README).
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

SIDECAR_DIR = Path(os.getcwd())
# .spec is typically invoked from desktop/sidecar/, so root is two levels up.
REPO_ROOT = SIDECAR_DIR.parent.parent

# ── Data files to bundle ──────────────────────────────────────────────────
# The seeded SQLite catalog. Bundling is the simplest path — trade-off is
# that DB updates require rebuilding the sidecar. See README for the
# alternative: ship DB as a Tauri resource and pass the path via env var.
DB_PATH = REPO_ROOT / "motoquant.db"
assert DB_PATH.exists(), (
    f"Expected seeded DB at {DB_PATH}. Run `python -m motoquant.run db init "
    f"&& python -m motoquant.run import --known-bikes && python -m motoquant.run db seed` first."
)

datas = [
    (str(DB_PATH), "."),  # → <MEIPASS>/motoquant.db
]

# Optional: ship surrogate model pickles too. Uncomment when the DNN
# surrogate becomes a first-class feature (currently loaded lazily).
# SURROGATE = REPO_ROOT / "artifacts" / "surrogate"
# if SURROGATE.exists():
#     datas.append((str(SURROGATE), "artifacts/surrogate"))

# ── Hidden imports ────────────────────────────────────────────────────────
# uvicorn + starlette + motoquant submodules are dynamic imports that
# PyInstaller's static analysis sometimes misses.
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
        "email_validator",
    ]
)

# ── Excludes ──────────────────────────────────────────────────────────────
# Heavy scientific deps the API endpoint itself doesn't need. These are
# pulled in only by optional calibration/analysis code paths (Sobol
# analysis, surrogate training). Excluding shrinks the binary ~80–150 MB.
excludes = [
    "matplotlib",
    "notebook",
    "jupyter",
    "pytest",
    "sphinx",
    "torch",          # Surrogate DNN training (offline tool only)
    "tensorflow",     # Not a runtime dep
    "sklearn",        # Only used in surrogate training
    "xgboost",        # Only used in surrogate_xgb offline training
    "SALib",          # Sobol analysis, offline tool only
    "streamlit",      # app.py is a separate entry
]

block_cipher = None

a = Analysis(
    [str(SIDECAR_DIR / "sidecar_entry.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="motoquant-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Keep console=True so Tauri's stdout/stderr pipes in lib.rs capture
    # the uvicorn startup log. On Windows this means a console window will
    # briefly flash when Tauri spawns the sidecar — Tauri's Command API
    # hides it at spawn time, so end-users don't see it.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
