#!/usr/bin/env python3
"""
MotoQuant health check — one-command state-of-the-world.

A fast (<30 s) snapshot of the repo's health that any contributor or agent can
run to know where things stand before touching anything: physics baselines,
lint/format, catalog counts, headline-stat drift, git state, and a secret scan.
It does NOT run the full test suite (that's `make test`, ~25 min) — this is the
glance you take first.

    python scripts/health_check.py          # human-readable dashboard
    python scripts/health_check.py --json    # machine-readable (for dashboards/CI)

Exit code: 0 if nothing is FAIL, 1 if any check FAILs. WARN never fails the run.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Secret-shaped patterns to refuse in tracked files. Deliberately conservative —
# these are real token prefixes, not generic entropy, to keep false positives low.
_SECRET_PATTERNS = [
    r"github_pat_[A-Za-z0-9_]{40,}",
    r"ghp_[A-Za-z0-9]{36,}",
    r"gsk_[A-Za-z0-9]{40,}",
    r"sk-[A-Za-z0-9]{40,}",
    r"AIza[0-9A-Za-z_-]{35}",
    r"xox[baprs]-[A-Za-z0-9-]{20,}",
    r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) ",
]


class Check:
    def __init__(self, name):
        self.name = name
        self.status = "ok"  # ok | warn | fail
        self.detail = ""

    def as_dict(self):
        return {"name": self.name, "status": self.status, "detail": self.detail}


def _run(cmd, timeout=120):
    """Run a command, return (returncode, stdout+stderr). Never raises."""
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as exc:  # noqa: BLE001
        return 127, f"{type(exc).__name__}: {exc}"


def check_baselines() -> Check:
    c = Check("physics baselines")
    rc, out = _run([sys.executable, os.path.join("scripts", "check_baselines.py")])
    if rc == 0:
        c.detail = "K5/R1/Hayabusa bit-identical"
    else:
        c.status = "fail"
        c.detail = out.strip().splitlines()[-1] if out.strip() else "drift"
    return c


def check_ruff() -> Check:
    c = Check("ruff lint + format")
    rc1, _ = _run(["ruff", "check", "motoquant/", "tests/", "scripts/"])
    rc2, _ = _run(["ruff", "format", "--check", "."])
    if rc1 == 0 and rc2 == 0:
        c.detail = "clean"
    elif rc1 == 127 or rc2 == 127:
        c.status = "warn"
        c.detail = "ruff not installed (pip install ruff)"
    else:
        c.status = "fail"
        c.detail = (
            f"lint={'ok' if rc1 == 0 else 'FAIL'} format={'ok' if rc2 == 0 else 'FAIL'}"
        )
    return c


def check_catalog() -> Check:
    c = Check("catalog (motoquant.db)")
    db = os.environ.get("MOTOQUANT_DB", os.path.join(ROOT, "motoquant.db"))
    if not os.path.exists(db):
        c.status = "warn"
        c.detail = "no motoquant.db (run `make db`)"
        return c
    try:
        import sqlite3

        conn = sqlite3.connect(db)
        counts = {}
        for tbl in (
            "bike_models",
            "parts",
            "tire_models",
            "venues",
            "bike_tire_fitments",
        ):
            try:
                counts[tbl] = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            except Exception:
                counts[tbl] = "?"
        conn.close()
        c.detail = (
            f"{counts['bike_models']} bikes / {counts['parts']} parts / "
            f"{counts['tire_models']} tires / {counts['venues']} venues / "
            f"{counts['bike_tire_fitments']} fitments"
        )
    except Exception as exc:  # noqa: BLE001
        c.status = "warn"
        c.detail = f"could not read DB: {exc}"
    return c


def check_headline_stats() -> Check:
    c = Check("headline-stat drift")
    script = os.path.join("scripts", "audit_headline_stats.py")
    if not os.path.exists(os.path.join(ROOT, script)):
        c.status = "warn"
        c.detail = "audit script missing"
        return c
    # --fail-on-drift is REQUIRED: without it audit_headline_stats.py always
    # exits 0 by its own contract, so the old `... or rc == 0` short-circuit
    # made this row report "in sync" unconditionally — a gate that could never
    # fire (found in the 2026-07-25 audit; README had been publishing retired
    # baselines while `make health` reported no drift).
    rc, out = _run([sys.executable, script, "--fail-on-drift"])
    if rc == 0:
        c.detail = "in sync"
    else:
        c.status = "warn"  # drift is a doc issue, not a build failure
        n = len([ln for ln in out.splitlines() if ln.strip().startswith("DRIFT")])
        c.detail = (
            f"{n or 'some'} drift(s) — run `python scripts/audit_headline_stats.py`"
        )
    return c


def check_tests_collect() -> Check:
    c = Check("test collection")
    # `-o addopts=` clears repo default addopts (coverage etc.) so collect emits
    # a clean node-id list; count "::" lines — robust across pytest versions.
    rc, out = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        timeout=300,
    )
    n = sum(1 for ln in out.splitlines() if "::" in ln)
    if n > 0:
        c.detail = f"{n} tests collected (run `make test` to execute)"
        if "error" in out.lower() and rc != 0:
            c.status = "warn"
            c.detail += " — collection had errors"
    else:
        c.status = "warn"
        c.detail = "could not count tests (is pytest installed?)"
    return c


def check_git() -> Check:
    c = Check("git state")
    rc, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, dirty = _run(["git", "status", "--porcelain"])
    dirty_n = len([ln for ln in dirty.splitlines() if ln.strip()])
    c.detail = f"branch={branch.strip()} · {dirty_n} uncommitted file(s)"
    return c


def check_secrets() -> Check:
    c = Check("secret scan (tracked files)")
    import re

    rc, files = _run(["git", "ls-files"])
    if rc != 0:
        c.status = "warn"
        c.detail = "git ls-files failed"
        return c
    pat = re.compile("|".join(_SECRET_PATTERNS))
    hits = []
    skip_ext = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".db",
        ".npz",
        ".pkl",
        ".woff",
        ".woff2",
        ".lock",
    )
    for rel in files.splitlines():
        rel = rel.strip()
        if not rel or rel.endswith(skip_ext):
            continue
        path = os.path.join(ROOT, rel)
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if pat.search(line):
                        hits.append(f"{rel}:{i}")
                        break
        except Exception:
            continue
    if hits:
        c.status = "fail"
        c.detail = f"{len(hits)} possible secret(s): {', '.join(hits[:5])}"
    else:
        c.detail = "no token-shaped strings in tracked files"
    return c


CHECKS = [
    check_baselines,
    check_ruff,
    check_catalog,
    check_headline_stats,
    check_tests_collect,
    check_git,
    check_secrets,
]

_ICON = {"ok": "✓", "warn": "!", "fail": "✗"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--secrets-only",
        action="store_true",
        help="run ONLY the secret scan (fast; used by the pre-commit hook)",
    )
    args = ap.parse_args()

    checks = [check_secrets] if args.secrets_only else CHECKS
    results = [fn() for fn in checks]

    if args.json:
        print(json.dumps([r.as_dict() for r in results], indent=2))
    else:
        print("\n  MotoQuant health check")
        print("  " + "─" * 40)
        for r in results:
            print(f"  [{_ICON[r.status]}] {r.name:26s} {r.detail}")
        print("  " + "─" * 40)
        n_fail = sum(1 for r in results if r.status == "fail")
        n_warn = sum(1 for r in results if r.status == "warn")
        verdict = "HEALTHY" if n_fail == 0 else "NEEDS ATTENTION"
        print(f"  {verdict}  ({n_fail} fail, {n_warn} warn)\n")

    return 1 if any(r.status == "fail" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
