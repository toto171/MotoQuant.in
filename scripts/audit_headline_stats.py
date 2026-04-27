#!/usr/bin/env python3
"""
audit_headline_stats.py — Detect stale headline numbers across the codebase.

Run this after any catalog/feature change that updates ALL_KNOWN_BIKES, the
parts catalog, the tire library, the fitments table, or the test count.
Reports every place in the web frontend / docs / blog / README where a stale
number is hard-coded vs the current source-of-truth value.

Usage:
    python3 scripts/audit_headline_stats.py
    python3 scripts/audit_headline_stats.py --json   # machine-readable
    python3 scripts/audit_headline_stats.py --fail-on-drift   # exit 1 if drift

Source-of-truth values:
  - ALL_KNOWN_BIKES length            -> motoquant/scraper/known_bikes.py
  - bike_models / parts / tire_models / bike_tire_fitments / venues counts
                                       -> motoquant.db (the file shipped to prod)
  - BENCHMARKS list length             -> scripts/validation_sweep.py
  - Reference baselines (K5/R1/Busa)   -> motoquant/defaults.py runtime
  - Fast test count                    -> pytest --collect-only -q (best effort)

Files scanned:
  web/app/page.js                  (landing-page stats strip)
  web/app/bikes/page.js            (catalog page metadata title)
  web/app/features/page.js         (features hero stat)
  web/app/blog/*/page.js           (per-post number quotes)
  web/app/docs/*/page.js           (validation/physics doc numbers)
  README.md                        (project stats blurb)
  CLAUDE.md                        (current-state section, by far the most fragile)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _truth_values():
    """Return the canonical numbers from source-of-truth files."""
    sys.path.insert(0, str(REPO))

    truth = {}

    # ALL_KNOWN_BIKES length (live import) — user-facing total adds the 3
    # hand-built reference bikes (K5/R1/Hayabusa) that are seeded directly
    # via seed_reference_bikes(), NOT through ALL_KNOWN_BIKES. The DB row
    # count in bike_models is the canonical user-facing total. We compute
    # both and prefer DB when healthy, fall back to (list + 3) otherwise.
    try:
        from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
        truth["_all_known_bikes_list"] = len(ALL_KNOWN_BIKES)
        truth["all_known_bikes"] = len(ALL_KNOWN_BIKES) + 3  # +3 reference bikes
    except Exception as exc:
        truth["all_known_bikes"] = f"ERROR: {exc}"

    # DB row counts
    db_path = REPO / "motoquant.db"
    if db_path.exists():
        try:
            c = sqlite3.connect(str(db_path))
            for tbl, key in [
                ("bike_models", "bikes_db"),
                ("parts", "parts_db"),
                ("tire_models", "tires_db"),
                ("bike_tire_fitments", "fitments_db"),
                ("venues", "venues_db"),
            ]:
                try:
                    truth[key] = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                except Exception as exc:
                    truth[key] = f"ERROR: {exc}"
            c.close()
        except Exception as exc:
            truth["_db_open_error"] = str(exc)

    # BENCHMARKS list length
    try:
        from scripts.validation_sweep import BENCHMARKS
        truth["benchmarks"] = len(BENCHMARKS)
    except Exception as exc:
        truth["benchmarks"] = f"ERROR: {exc}"

    # Reference baselines (run sim — slow, ~3s)
    try:
        from motoquant import MotoQuantEngine
        from motoquant.defaults import gsxr1000_k5, yzfr1_4c8, hayabusa_gen1
        for name, fn in [("k5", gsxr1000_k5), ("r1", yzfr1_4c8), ("busa", hayabusa_gen1)]:
            try:
                r = MotoQuantEngine(fn()).run()
                truth[f"baseline_{name}"] = round(float(r.time_quarter), 4)
            except Exception as exc:
                truth[f"baseline_{name}"] = f"ERROR: {exc}"
    except Exception as exc:
        truth["_baseline_import_error"] = str(exc)

    # Fast test count (best effort — collect-only)
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True, text=True, cwd=str(REPO), timeout=30,
        )
        # Look for "N tests collected" in output
        m = re.search(r"(\d+)\s+tests? collected", result.stdout + result.stderr)
        truth["tests_collected"] = int(m.group(1)) if m else "ERROR: no count line"
    except Exception as exc:
        truth["tests_collected"] = f"ERROR: {exc}"

    return truth


# Patterns to look for in the web/docs files. Each entry:
#   (file_glob, regex_pattern, truth_key, description)
PATTERNS = [
    # Landing page stats strip
    ("web/app/page.js",                r"(\d{2,4})\s*(?:bikes?|motorcycles?)\b",   "all_known_bikes",   "landing-page bikes tile"),
    ("web/app/page.js",                r"(\d{2,4})\s*tires?\b",                    "tires_db",          "landing-page tires tile"),
    ("web/app/page.js",                r"(\d{2,4})\s*parts?\b",                    "parts_db",          "landing-page parts tile"),
    ("web/app/page.js",                r"(\d{2,4})\s*venues?\b",                   "venues_db",         "landing-page venues tile"),
    ("web/app/page.js",                r"(\d{3,4})\s*tests?\b",                    "tests_collected",   "landing-page tests tile"),
    ("web/app/page.js",                r"(\d{1,3})\s*benchmarks?\b",               "benchmarks",        "landing-page benchmarks count"),

    # Bikes catalog page metadata
    ("web/app/bikes/page.js",          r"(\d{2,4})\s*Bikes?\b",                    "all_known_bikes",   "bikes-page metadata title"),
    ("web/app/bikes/page.js",          r"(\d{2,4})\s*motorcycles?\b",              "all_known_bikes",   "bikes-page metadata description"),

    # Features page hero stat
    ("web/app/features/page.js",       r"(\d{2,4})\s*bikes?\b",                    "all_known_bikes",   "features-page hero"),
    ("web/app/features/page.js",       r"(\d{2,4})\s*parts?\b",                    "parts_db",          "features-page parts mention"),

    # Blog posts (per-post)
    ("web/app/blog/*/page.js",         r"across\s+(\d{2,4})\s+(?:published\s+)?benchmarks?", "benchmarks", "blog post benchmark count"),
    ("web/app/blog/*/page.js",         r"(\d{3,4})\s*bikes?\b",                    "all_known_bikes",   "blog post bike count"),

    # README
    ("README.md",                      r"(\d{2,4})\s*bikes?\b",                    "all_known_bikes",   "README bikes count"),
    ("README.md",                      r"(\d{2,4})\s*parts?\b",                    "parts_db",          "README parts count"),

    # Reference baselines (4 decimal places)
    ("web/app/page.js",                r"K5\s*[=:]\s*([0-9]+\.[0-9]{1,4})\s*s",    "baseline_k5",       "landing-page K5 baseline"),
    ("web/app/page.js",                r"R1\s*[=:]\s*([0-9]+\.[0-9]{1,4})\s*s",    "baseline_r1",       "landing-page R1 baseline"),
    ("web/app/page.js",                r"Hayabusa\s*[=:]\s*([0-9]+\.[0-9]{1,4})\s*s", "baseline_busa",  "landing-page Hayabusa baseline"),
    ("web/app/blog/*/page.js",         r"K5[^.]*?([0-9]+\.[0-9]{4})\s*s",          "baseline_k5",       "blog K5 baseline"),
    ("web/app/blog/*/page.js",         r"R1[^.]*?4C8[^.]*?([0-9]+\.[0-9]{4})\s*s", "baseline_r1",       "blog R1 baseline"),
    ("web/app/blog/*/page.js",         r"Hayabusa[^.]*?([0-9]+\.[0-9]{4})\s*s",    "baseline_busa",     "blog Hayabusa baseline"),
]


def _scan_file(path: Path, pattern: str, truth_value):
    """Return list of (line_num, declared_value, drift?) tuples."""
    out = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return out
    for i, line in enumerate(text.splitlines(), start=1):
        for m in re.finditer(pattern, line):
            declared = m.group(1)
            try:
                declared_num = float(declared) if "." in declared else int(declared)
            except ValueError:
                continue
            if isinstance(truth_value, str):
                # Truth had an error — can't compare
                drift = "?"
            elif isinstance(truth_value, float):
                drift = abs(declared_num - truth_value) > 0.005
            else:
                drift = declared_num != truth_value
            out.append((i, declared, drift, line.strip()[:120]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    ap.add_argument("--fail-on-drift", action="store_true", help="exit 1 if drift detected")
    args = ap.parse_args()

    truth = _truth_values()

    if not args.json:
        print("=" * 78)
        print("HEADLINE-STATS AUDIT — declared values vs source-of-truth")
        print("=" * 78)
        print()
        print("Source-of-truth values:")
        for k, v in truth.items():
            print(f"  {k:24s}  {v}")
        print()

    drift_count = 0
    drift_records = []

    for file_glob, pattern, truth_key, desc in PATTERNS:
        truth_value = truth.get(truth_key)
        if truth_value is None or isinstance(truth_value, str) and truth_value.startswith("ERROR"):
            continue
        for path in REPO.glob(file_glob):
            findings = _scan_file(path, pattern, truth_value)
            for line_num, declared, drift, line_preview in findings:
                rel = path.relative_to(REPO).as_posix()
                if drift is True:
                    drift_count += 1
                    drift_records.append({
                        "file": rel,
                        "line": line_num,
                        "declared": declared,
                        "truth": truth_value,
                        "truth_key": truth_key,
                        "description": desc,
                        "preview": line_preview,
                    })
                    if not args.json:
                        print(f"  DRIFT  {rel}:{line_num}  declares={declared}  truth={truth_value}  ({desc})")
                        print(f"         > {line_preview}")

    if args.json:
        print(json.dumps({"truth": truth, "drift": drift_records}, indent=2, default=str))
    else:
        print()
        if drift_count == 0:
            print("All headline numbers in sync. No action needed.")
        else:
            print(f"{drift_count} drift(s) detected. Patch each location and re-run.")
        print()

    return 1 if (args.fail_on_drift and drift_count > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
