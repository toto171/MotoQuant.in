"""MotoQuant Local Lab launcher.

Boots the full MotoQuant FastAPI engine on localhost and serves the
desktop UI's static build from the same origin. Designed to run either
frozen (PyInstaller one-file exe) or straight from a checkout::

    python -m local_lab.entry --port 8000

Boot sequence (order matters — motoquant.api reads env at import):
  1. Resolve the bundle root (sys._MEIPASS when frozen, repo root otherwise).
  2. Copy the seeded catalog DB to a persistent per-user data dir ONCE
     (one-file bundles extract to a temp dir that is wiped on exit, so
     saved runs would be lost without the copy-out; an existing copy is
     never overwritten unless --fresh-db).
  3. Set MOTOQUANT_DB / MOTOQUANT_LOCAL_UI / MOTOQUANT_RATE_LIMIT and
     scrub Render's keep-warm trigger env.
  4. Import motoquant.api and hand the app to uvicorn; open the browser.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import sys
import threading
import webbrowser
from pathlib import Path

APP_NAME = "MotoQuantLocalLab"
DEFAULT_PORT = 8000


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def bundle_root() -> Path:
    """Directory holding bundled data (DB seed, surrogate, ui/)."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def default_data_dir() -> Path:
    """Per-user writable dir where the live DB persists across runs."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "motoquant-local-lab"


def resolve_ui_dir(root: Path) -> Path:
    """Bundled ui/ when frozen; the vite build output in a dev checkout."""
    bundled = root / "ui"
    if bundled.is_dir():
        return bundled
    return root / "desktop" / "dist"


def prepare_database(seed_db: Path, data_dir: Path, fresh: bool = False) -> Path:
    """Copy the bundled seed DB into data_dir once; keep an existing copy.

    Mirrors docker-entrypoint.sh's persistent-disk semantics: first boot
    seeds, later boots preserve accumulated saved runs / usage rows.
    ``fresh=True`` discards the live copy and re-seeds from the bundle.
    """
    if not seed_db.is_file():
        raise FileNotFoundError(f"bundled seed DB not found: {seed_db}")
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / "motoquant.db"
    if fresh and target.exists():
        target.unlink()
    if not target.exists():
        shutil.copy2(seed_db, target)
        print(f"[local-lab] seeded live DB at {target}")
    else:
        print(
            f"[local-lab] using existing live DB at {target} (pass --fresh-db to reset)"
        )
    return target


def build_env(db_path: Path, ui_dir: Path | None) -> dict[str, str]:
    """Env the engine needs, single-user local defaults. Returns what was set."""
    env = {
        "MOTOQUANT_DB": str(db_path),
        # Single local user hammering the optimizer IS the use case here —
        # the per-IP limiter only gets in the way of a stress test.
        "MOTOQUANT_RATE_LIMIT": os.environ.get("MOTOQUANT_RATE_LIMIT", "false"),
    }
    if ui_dir is not None and ui_dir.is_dir():
        env["MOTOQUANT_LOCAL_UI"] = str(ui_dir)
    for key, value in env.items():
        os.environ[key] = value
    # A stray Render var would start the keep-warm self-ping loop against
    # a URL that isn't us. Never wanted locally.
    for stale in ("RENDER_EXTERNAL_URL", "MOTOQUANT_KEEPWARM_URL"):
        os.environ.pop(stale, None)
    return env


def pick_port(preferred: int) -> int:
    """Preferred port if free, else an OS-assigned ephemeral one."""
    for candidate in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
            except OSError:
                continue
            return sock.getsockname()[1]
    raise OSError("no free TCP port available on 127.0.0.1")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="MotoQuant Local Lab — full engine + UI on your own CPU.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="preferred port (default 8000; falls back to a free one)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="bind address (default 127.0.0.1 — local only)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="don't auto-open the browser"
    )
    parser.add_argument(
        "--fresh-db",
        action="store_true",
        help="reset the live DB from the bundled seed catalog",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=None, help="override the per-user data dir"
    )
    args = parser.parse_args(argv)

    root = bundle_root()
    data_dir = args.data_dir or default_data_dir()
    db_path = prepare_database(root / "motoquant.db", data_dir, fresh=args.fresh_db)
    ui_dir = resolve_ui_dir(root)
    build_env(db_path, ui_dir if ui_dir.is_dir() else None)

    # Import AFTER env setup — motoquant.api reads MOTOQUANT_LOCAL_UI at
    # import time and MOTOQUANT_DB on first connection.
    import uvicorn

    from motoquant.api import app

    port = pick_port(args.port)
    if port != args.port:
        print(f"[local-lab] port {args.port} busy, using {port}")
    url = f"http://{args.host}:{port}"
    print(f"[local-lab] MotoQuant Local Lab starting at {url}")
    if not ui_dir.is_dir():
        print("[local-lab] WARNING: no bundled UI found — API only (see /docs)")

    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, [url]).start()

    uvicorn.run(
        app,
        host=args.host,
        port=port,
        log_level=os.environ.get("UVICORN_LOG_LEVEL", "info"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
