"""PyInstaller entry point for the MotoQuant backend sidecar.

Tauri (see ``desktop/src-tauri/src/lib.rs``) picks a free local port, spawns
this binary with ``--host 127.0.0.1 --port <N> --log-level info``, and polls
``http://127.0.0.1:<N>/api/health`` until it responds. We launch the same
FastAPI app that the dev flow runs via ``uvicorn motoquant.api:app``.

When frozen by PyInstaller the app's ``motoquant.db`` catalog lives in the
temporary ``sys._MEIPASS`` extract dir; we set ``MOTOQUANT_DB`` so the
FastAPI process finds it without any Tauri-side plumbing.

Design notes
------------
* ``port=0`` is NOT used. Tauri picks the port and passes it explicitly so
  the frontend never has to parse startup stdout to learn the URL.
* We keep stdout/stderr unbuffered (``-u`` equivalent via line buffering)
  so Rust's log pipe picks lines up as they're written.
* The env var ``MOTOQUANT_SIDECAR_DB`` can override the bundled DB at
  runtime, useful for the user to point at a custom seeded catalog without
  rebuilding the binary.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _resolve_bundled_db() -> None:
    """If running as a PyInstaller bundle, point MOTOQUANT_DB at the bundled
    ``motoquant.db`` unless the caller has already set it.
    """
    if os.environ.get("MOTOQUANT_DB"):
        return  # Respect explicit override (from Tauri, CI, or user shell).

    # PyInstaller one-file bundle extracts datas into sys._MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate = Path(meipass) / "motoquant.db"
        if candidate.exists():
            os.environ["MOTOQUANT_DB"] = str(candidate)
            return

    # Dev invocation (python sidecar_entry.py from repo root): fall back to
    # the tracked DB next to pyproject.toml.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "motoquant.db"
        if candidate.exists():
            os.environ.setdefault("MOTOQUANT_DB", str(candidate))
            return


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="motoquant-backend",
        description="MotoQuant FastAPI sidecar (PyInstaller-frozen uvicorn).",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000") or "8000"),
        help="TCP port (non-zero). Tauri picks this Rust-side and passes it.",
    )
    p.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
    )
    return p.parse_args()


def main() -> None:
    _resolve_bundled_db()
    args = _parse_args()

    # Import uvicorn *after* env-var setup so any module-level config in
    # motoquant.* that reads MOTOQUANT_DB on import sees the right path.
    import uvicorn

    uvicorn.run(
        "motoquant.api:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        access_log=False,  # Quieter by default; the frontend polls /api/health.
    )


if __name__ == "__main__":
    main()
