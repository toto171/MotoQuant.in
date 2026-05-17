#!/usr/bin/env python3
"""Stamp STATUS.md _updated and last_run with the current UTC timestamp.

Called by scripts/session_postflight.sh after the agent work is staged but
before the commit, so the bump rides the same commit. Also safe to run
standalone for testing.

Resolves INBOX:322 (self-review M1 Section B.2/B.3): the GH-Actions
heartbeat side-channel reads _LAST_RUN_JSON._updated to decide whether
the autonomous system has gone dark. If _updated stays null, the
staleness check misfires on every cron tick.

Usage:
    python3 scripts/stamp_status_timestamps.py             # stamps STATUS.md in CWD
    python3 scripts/stamp_status_timestamps.py path/to/STATUS.md
    python3 scripts/stamp_status_timestamps.py --now 2026-05-17T04:30:29Z

Exit codes:
    0 — stamped (or no-op if file already had this exact timestamp)
    1 — STATUS.md missing or malformed (no _updated field, no last_run line)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import sys


_UPDATED_RE = re.compile(r'"_updated"\s*:\s*(?:null|"[^"]*")\s*,')
_LAST_RUN_RE = re.compile(r"^last_run:[ \t]*(\S[^\n]*)?$", re.MULTILINE)
_LAST_RUN_COMMENT = (
    "<!-- AUTO-UPDATED — used by catchup_detect to decide if we need recovery mode -->"
)


def stamp(text: str, now_iso: str) -> tuple[str, bool, bool]:
    """Apply both substitutions. Returns (new_text, updated_changed, last_run_changed)."""
    new_text, n_updated = _UPDATED_RE.subn(
        f'"_updated": "{now_iso}",', text, count=1
    )
    new_text, n_last_run = _LAST_RUN_RE.subn(
        f"last_run: {now_iso}  {_LAST_RUN_COMMENT}",
        new_text,
        count=1,
    )
    return new_text, n_updated > 0, n_last_run > 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default="STATUS.md",
        help="path to STATUS.md (default: ./STATUS.md)",
    )
    parser.add_argument(
        "--now",
        help="ISO timestamp to stamp (default: current UTC time)",
    )
    args = parser.parse_args(argv)

    now_iso = args.now or _dt.datetime.now(_dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    p = pathlib.Path(args.path)
    if not p.exists():
        print(f"[stamp_status] {p} not found", file=sys.stderr)
        return 1

    text = p.read_text()
    new_text, did_updated, did_last_run = stamp(text, now_iso)

    if not did_updated and not did_last_run:
        print(
            f"[stamp_status] {p}: neither _updated nor last_run pattern matched — "
            "STATUS.md may be malformed",
            file=sys.stderr,
        )
        return 1

    if new_text != text:
        p.write_text(new_text)

    flags = []
    if did_updated:
        flags.append("_updated")
    if did_last_run:
        flags.append("last_run")
    print(f"[stamp_status] {p}: stamped {'+'.join(flags)} → {now_iso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
