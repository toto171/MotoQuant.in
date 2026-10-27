#!/usr/bin/env python3
"""
audit_headline_stats.py — Detect stale headline numbers across the codebase.

Run this after any catalog/feature change that updates ALL_KNOWN_BIKES, the
parts catalog, the tire library, the fitments table, or the test count.
Reports every place in the web frontend / docs / blog / README where a stale
number is hard-coded vs the current source-of-truth value.

Usage:
    python3 scripts/audit_headline_stats.py                  # report only
    python3 scripts/audit_headline_stats.py --json           # machine-readable
    python3 scripts/audit_headline_stats.py --fail-on-drift  # exit 1 on drift
    python3 scripts/audit_headline_stats.py --fix            # auto-patch in-place
    python3 scripts/audit_headline_stats.py --regen-og       # regenerate OG card
    python3 scripts/audit_headline_stats.py --fix --regen-og # both (postflight gate)

Source-of-truth values:
  - bike_models / parts / tire_models / bike_tire_fitments / venues counts
                                       -> motoquant.db (the file shipped to prod)
  - ALL_KNOWN_BIKES list length        -> motoquant/scraper/known_bikes.py
  - BENCHMARKS list length             -> scripts/validation_sweep.py
  - Reference baselines (K5/R1/Busa)   -> motoquant/defaults.py runtime
  - Fast test count                    -> pytest --collect-only -q (best effort)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OG_IMAGE_PATH = REPO / "web" / "public" / "og-image.png"
DB_PATH = REPO / "motoquant.db"
# Optional committed fallback for the fast-test count (one integer, first line).
# Lets the audit report a real number where pytest cannot run (Cowork sandbox
# lacks scipy/fastapi/pytest) without faking it.
TEST_COUNT_FILE = REPO / "reports" / "test_count.txt"
# Sentinel prefix for non-numeric, non-error tests_collected values so the drift
# scanner and the --fix patcher both leave the count untouched.
TEST_COUNT_SKIP_PREFIX = "skipped"


# ─── Source-of-truth derivation ──────────────────────────────────────────────


def _collect_test_count():
    """Best-effort fast-test count that degrades gracefully.

    Returns an int when pytest can collect, otherwise a clean human string
    ("skipped (...)") -- never a raw "ERROR" that muddies the audit output.
    """
    if importlib.util.find_spec("pytest") is None:
        committed = _committed_test_count()
        if committed is not None:
            return committed
        return "skipped (pytest unavailable)"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            timeout=60,
        )
        for pat in [r"(\d+)\s+tests?\s+collected", r"^=+\s*(\d+)\s+tests?\s+collected"]:
            m = re.search(pat, result.stdout + result.stderr, re.MULTILINE)
            if m:
                return int(m.group(1))
        committed = _committed_test_count()
        if committed is not None:
            return committed
        return "skipped (pytest collection produced no count)"
    except Exception as exc:  # noqa: BLE001 -- best-effort, never fatal
        committed = _committed_test_count()
        if committed is not None:
            return committed
        return "skipped (pytest could not run: %s)" % type(exc).__name__


def _committed_test_count():
    """Read reports/test_count.txt if present; return int or None."""
    try:
        if TEST_COUNT_FILE.exists():
            first = TEST_COUNT_FILE.read_text(encoding="utf-8").strip().splitlines()[0]
            return int(re.search(r"\d+", first).group(0))
    except Exception:
        return None
    return None


def _truth_values():
    """Return the canonical numbers from source-of-truth files."""
    sys.path.insert(0, str(REPO))

    truth = {}

    # ALL_KNOWN_BIKES list (live import). User-facing bike count is the DB
    # row count when DB is healthy (that's what the API returns); fall back
    # to len(list) + 3 reference bikes only if DB is unreachable.
    try:
        from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

        truth["_all_known_bikes_list"] = len(ALL_KNOWN_BIKES)
    except Exception as exc:
        truth["_all_known_bikes_list"] = f"ERROR: {exc}"

    # DB row counts — primary source of truth for user-facing copy
    if DB_PATH.exists():
        try:
            c = sqlite3.connect(str(DB_PATH))
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

    # User-facing bike count: DB if healthy, else list+3
    if isinstance(truth.get("bikes_db"), int):
        truth["all_known_bikes"] = truth["bikes_db"]
    elif isinstance(truth.get("_all_known_bikes_list"), int):
        truth["all_known_bikes"] = truth["_all_known_bikes_list"] + 3
    else:
        truth["all_known_bikes"] = "ERROR: no source"

    # BENCHMARKS list length
    try:
        from scripts.validation_sweep import BENCHMARKS

        truth["benchmarks"] = len(BENCHMARKS)
    except Exception as exc:
        truth["benchmarks"] = f"ERROR: {exc}"

    # Reference baselines (run sim — slow, ~3s)
    try:
        from motoquant import MotoQuantEngine
        from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

        for name, fn in [
            ("k5", gsxr1000_k5),
            ("r1", yzfr1_4c8),
            ("busa", hayabusa_gen1),
        ]:
            try:
                r = MotoQuantEngine(fn()).run()
                truth[f"baseline_{name}"] = round(float(r.time_quarter), 4)
            except Exception as exc:
                truth[f"baseline_{name}"] = f"ERROR: {exc}"
    except Exception as exc:
        truth["_baseline_import_error"] = str(exc)

    # Fast test count (best effort). pytest is not installable in every
    # environment (the Cowork sandbox has no scipy/fastapi/pytest), so this
    # degrades gracefully -- never an "ERROR" that muddies the report. Order
    # of preference: live collection, reports/test_count.txt, "skipped".
    truth["tests_collected"] = _collect_test_count()

    # OG image freshness — compare mtime to motoquant.db
    if OG_IMAGE_PATH.exists() and DB_PATH.exists():
        og_mtime = OG_IMAGE_PATH.stat().st_mtime
        db_mtime = DB_PATH.stat().st_mtime
        truth["_og_image_mtime"] = og_mtime
        truth["_db_mtime"] = db_mtime
        truth["og_image_stale"] = og_mtime < db_mtime

    return truth


# ─── Drift patterns ──────────────────────────────────────────────────────────
# Each entry: (file_glob, regex_pattern, truth_key, description)
# Group 1 of the regex must capture the declared numeric value.
PATTERNS = [
    # MCP server tool descriptions + the Claude skill (2026-08-08: two new
    # count-bearing surfaces the audit previously did not scan)
    (
        "motoquant/mcp_server.py",
        r"(\d{2,4})-bike catalog",
        "all_known_bikes",
        "mcp search_bikes tool description",
    ),
    (
        "motoquant/mcp_server.py",
        r"(\d{2,4})-part catalog",
        "parts_db",
        "mcp search_parts tool description",
    ),
    (
        "skills/motoquant/SKILL.md",
        r"(\d{2,4})\s*bikes?,",
        "all_known_bikes",
        "skill catalog bikes count",
    ),
    (
        "skills/motoquant/SKILL.md",
        r"(\d{2,4})\s*parts?,",
        "parts_db",
        "skill catalog parts count",
    ),
    (
        "skills/motoquant/SKILL.md",
        r"(\d{2,4})\s*tires?,",
        "tires_db",
        "skill catalog tires count",
    ),
    # Landing page stats strip
    (
        "web/app/page.js",
        r"(\d{2,4})\s*(?:bikes?|motorcycles?)\b",
        "all_known_bikes",
        "landing-page bikes tile",
    ),
    (
        "web/app/page.js",
        r"num:\s*(\d{2,4})\s*,\s*label:\s*'BIKES'",
        "all_known_bikes",
        "landing-page BIKES num",
    ),
    (
        "web/app/page.js",
        r"num:\s*(\d{2,4})\s*,\s*label:\s*'PARTS'",
        "parts_db",
        "landing-page PARTS num",
    ),
    ("web/app/page.js", r"(\d{2,4})\s*tires?\b", "tires_db", "landing-page tires tile"),
    ("web/app/page.js", r"(\d{2,4})\s*parts?\b", "parts_db", "landing-page parts tile"),
    (
        "web/app/page.js",
        r"(\d{2,4})\s*venues?\b",
        "venues_db",
        "landing-page venues tile",
    ),
    (
        "web/app/page.js",
        r"(\d{3,4})\s*tests?\b",
        "tests_collected",
        "landing-page tests tile",
    ),
    (
        "web/app/page.js",
        r"(\d{1,3})\s*benchmarks?\b",
        "benchmarks",
        "landing-page benchmarks count",
    ),
    # Bikes catalog page metadata
    (
        "web/app/bikes/layout.js",
        r"(\d{2,4})\s*(?:Bikes?|bikes?)\b",
        "all_known_bikes",
        "bikes-page metadata",
    ),
    (
        "web/app/bikes/layout.js",
        r"(\d{2,4})\s*motorcycles?\b",
        "all_known_bikes",
        "bikes-page metadata description",
    ),
    (
        "web/app/bikes/layout.js",
        r"numberOfItems:\s*(\d{2,4})",
        "all_known_bikes",
        "bikes-page schema numberOfItems",
    ),
    (
        # Brackets escaped: Path.glob reads a bare "[id]" as a character
        # class, so this target silently matched NOTHING for months.
        "web/app/bikes/[[]id]/layout.js",
        r"(\d{2,4})\s*(?:bikes?|motorcycles?)\b",
        "all_known_bikes",
        "bikes-id layout",
    ),
    (
        "web/app/bikes/page.js",
        r"(\d{2,4})\s*(?:Bikes?|bikes?)\b",
        "all_known_bikes",
        "bikes-page body",
    ),
    # Features page hero stat
    (
        "web/app/features/page.js",
        r"(\d{2,4})\s*bikes?\b",
        "all_known_bikes",
        "features-page hero",
    ),
    (
        "web/app/features/page.js",
        r"num:\s*'(\d{2,4})'\s*,\s*label:\s*'Parts'",
        "parts_db",
        "features-page parts num",
    ),
    (
        "web/app/features/layout.js",
        r"(\d{2,4})-bike\s+catalog",
        "all_known_bikes",
        "features-page meta description",
    ),
    # Layout / metadata / OG / Twitter
    (
        "web/app/layout.js",
        r"split times for (\d{2,4})\+\s*bikes",
        "all_known_bikes",
        "layout meta description",
    ),
    (
        "web/app/layout.js",
        r"covering (\d{2,4}) motorcycles?",
        "all_known_bikes",
        "layout OG/Twitter alt motorcycles",
    ),
    ("web/app/layout.js", r"(\d{2,4}) parts,", "parts_db", "layout OG alt parts"),
    ("web/app/layout.js", r"(\d{2,4}) tires,", "tires_db", "layout OG alt tires"),
    ("web/app/layout.js", r"(\d{2,4}) venues", "venues_db", "layout OG alt venues"),
    # Schema.org structured data
    (
        "web/app/StructuredData.js",
        r"(\d{2,4})\+\s*bikes",
        "all_known_bikes",
        "Schema.org description bikes",
    ),
    (
        "web/app/StructuredData.js",
        r"(\d{2,4}) motorcycles?",
        "all_known_bikes",
        "Schema.org motorcycles",
    ),
    (
        "web/app/StructuredData.js",
        r"(\d{2,4})-part",
        "parts_db",
        "Schema.org N-part catalog",
    ),
    (
        "web/app/StructuredData.js",
        r"(\d{2,4})\s*bikes?\s+across",
        "all_known_bikes",
        "Schema.org bikes across mfgs",
    ),
    # Simulator, About, Whitepaper, Pricing
    (
        "web/app/simulator/layout.js",
        r"(\d{2,4}) motorcycles?",
        "all_known_bikes",
        "simulator OG alt",
    ),
    (
        "web/app/about/page.js",
        r"(\d{2,4}) bikes?,",
        "all_known_bikes",
        "about-page bikes",
    ),
    ("web/app/about/page.js", r"(\d{2,4}) parts?,", "parts_db", "about-page parts"),
    ("web/app/about/page.js", r"(\d{2,4}) venues", "venues_db", "about-page venues"),
    (
        "web/app/whitepaper/page.js",
        r"(\d{2,4})-bike catalog",
        "all_known_bikes",
        "whitepaper bike catalog mention",
    ),
    (
        "web/app/whitepaper/page.js",
        r"(\d{2,4})-part library",
        "parts_db",
        "whitepaper part library mention",
    ),
    (
        "web/app/whitepaper/page.js",
        r"all (\d{2,4}) bikes",
        "all_known_bikes",
        "whitepaper all-bikes claim",
    ),
    (
        "web/app/whitepaper/page.js",
        r"num:\s*'(\d{2,4})'\s*,\s*label:\s*'Catalog bikes'",
        "all_known_bikes",
        "whitepaper catalog bikes num",
    ),
    # Blog posts (per-post)
    (
        "web/app/blog/*/page.js",
        r"across\s+(\d{2,4})\s+(?:published\s+)?benchmarks?",
        "benchmarks",
        "blog post benchmark count",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4}) catalog bikes?",
        "all_known_bikes",
        "blog 'N catalog bikes'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4}) different bikes",
        "all_known_bikes",
        "blog 'N different bikes'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4}) bikes individually",
        "all_known_bikes",
        "blog 'measured each of N bikes'",
    ),
    # ── Extended coverage (added 2026-07-04) — catalog-count phrasings the
    #    original PATTERNS missed. Every catalog/feature change was drifting
    #    these silently: StructuredData line-88 description + FAQ answer, the
    #    PageHero doc-comment usage banner, tool-page {value,label} stat tiles,
    #    the "N bikes" (no "+") metadata descriptions, and several blog
    #    phrasings. Kept tight so --fix only ever touches the captured count.
    #    Deliberately NOT matched: "N+ other bikes" CTAs — those are rounded
    #    lower bounds, not exact counts, so --fix must leave them alone.
    #
    # Schema.org SoftwareApplication description (line ~88) + FAQ answer.
    (
        "web/app/StructuredData.js",
        r"covering (\d{2,4}) bikes",
        "all_known_bikes",
        "Schema.org description bikes count",
    ),
    (
        "web/app/StructuredData.js",
        r"bikes, (\d{2,4}) parts",
        "parts_db",
        "Schema.org description parts count",
    ),
    (
        "web/app/StructuredData.js",
        r"parts, (\d{2,4}) tires",
        "tires_db",
        "Schema.org description tires count",
    ),
    (
        "web/app/StructuredData.js",
        r"(\d{2,4}) production bikes",
        "all_known_bikes",
        "Schema.org FAQ production bikes",
    ),
    # PageHero doc-comment usage banner (component header example).
    (
        "web/components/PageHero.js",
        r"(\d{2,4}) bikes with full physics",
        "all_known_bikes",
        "PageHero doc-comment bikes",
    ),
    (
        "web/components/PageHero.js",
        r"catalog loaded \[(\d{2,4})/",
        "all_known_bikes",
        "PageHero doc-comment kicker slot1",
    ),
    (
        "web/components/PageHero.js",
        r"catalog loaded \[\d{2,4}/(\d{2,4})\]",
        "all_known_bikes",
        "PageHero doc-comment kicker slot2",
    ),
    (
        "web/components/PageHero.js",
        r"value:\s*(\d{2,4})\s*,\s*label:\s*'BIKES'",
        "all_known_bikes",
        "PageHero doc-comment BIKES tile",
    ),
    (
        "web/components/PageHero.js",
        r"value:\s*(\d{2,4})\s*,\s*label:\s*'TIRES'",
        "tires_db",
        "PageHero doc-comment TIRES tile",
    ),
    # Tool-page PageHero stat tiles ({ value: N, label: 'BIKES' } etc.) —
    # optimize / autotune / bikes and any future tool page.
    (
        "web/app/*/page.js",
        r"value:\s*(\d{2,4})\s*,\s*label:\s*'BIKES'",
        "all_known_bikes",
        "tool-page BIKES stat tile",
    ),
    (
        "web/app/*/page.js",
        r"value:\s*(\d{2,4})\s*,\s*label:\s*'PARTS'",
        "parts_db",
        "tool-page PARTS stat tile",
    ),
    (
        "web/app/*/page.js",
        r"value:\s*(\d{2,4})\s*,\s*label:\s*'TIRES'",
        "tires_db",
        "tool-page TIRES stat tile",
    ),
    (
        "web/app/*/page.js",
        r"value:\s*(\d{2,5})\s*,\s*label:\s*'FITMENTS'",
        "fitments_db",
        "tool-page FITMENTS stat tile",
    ),
    (
        "web/app/*/page.js",
        r"value:\s*(\d{1,4})\s*,\s*label:\s*'VENUES'",
        "venues_db",
        "tool-page VENUES stat tile",
    ),
    (
        "web/app/bikes/page.js",
        r"catalog loaded \[(\d{2,4})/",
        "all_known_bikes",
        "bikes-page kicker slot1",
    ),
    (
        "web/app/bikes/page.js",
        r"catalog loaded \[\d{2,4}/(\d{2,4})\]",
        "all_known_bikes",
        "bikes-page kicker slot2",
    ),
    # Landing-page STATS strip TIRES/VENUES num tiles (BIKES/PARTS already
    # covered above; TIRES + VENUES had no pattern).
    (
        "web/app/page.js",
        r"num:\s*(\d{2,4})\s*,\s*label:\s*'TIRES'",
        "tires_db",
        "landing-page TIRES num",
    ),
    (
        "web/app/page.js",
        r"num:\s*(\d{1,4})\s*,\s*label:\s*'VENUES'",
        "venues_db",
        "landing-page VENUES num",
    ),
    # Metadata descriptions that say "... for N bikes ..." (no "+").
    (
        "web/app/layout.js",
        r"split for (\d{2,4}) bikes",
        "all_known_bikes",
        "layout meta description bikes",
    ),
    (
        "web/app/simulator/layout.js",
        r"Predictor for (\d{2,4}) Bikes",
        "all_known_bikes",
        "simulator title bikes",
    ),
    (
        "web/app/simulator/layout.js",
        r"split for (\d{2,4}) bikes",
        "all_known_bikes",
        "simulator description bikes",
    ),
    (
        "web/app/docs/getting-started/page.js",
        r"pick from (\d{2,4}) bikes",
        "all_known_bikes",
        "getting-started bikes count",
    ),
    (
        "web/app/not-found.js",
        r"Browse (\d{2,4}) bikes",
        "all_known_bikes",
        "not-found bikes CTA",
    ),
    (
        "web/components/CommandPalette.js",
        r"the (\d{2,4})-bike catalog",
        "all_known_bikes",
        "CommandPalette doc-comment catalog",
    ),
    (
        "web/app/docs/physics/SubModelsCtaVariant.js",
        r"(\d{2,4}) bikes",
        "all_known_bikes",
        "SubModels CTA bikes",
    ),
    (
        "web/app/features/page.js",
        r"'(\d{2,4}) parts\.",
        "parts_db",
        "features parts subtitle",
    ),
    (
        "web/app/features/page.js",
        r"catalog covers (\d{2,4}) upgrades",
        "parts_db",
        "features parts body upgrades",
    ),
    # Additional blog-post catalog phrasings.
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4}) bikes with",
        "all_known_bikes",
        "blog 'N bikes with'",
    ),
    (
        "web/app/blog/*/page.js",
        r"catalog of (\d{3,4}) bikes",
        "all_known_bikes",
        "blog 'catalog of N bikes'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4})-bike catalog",
        "all_known_bikes",
        "blog 'N-bike catalog'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4}) parts in the catalog",
        "parts_db",
        "blog 'N parts in the catalog'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{3,4})-part ROI",
        "parts_db",
        "blog 'N-part ROI engine'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{2,4}) tires across",
        "tires_db",
        "blog 'N tires across'",
    ),
    (
        "web/app/blog/*/page.js",
        r"(\d{2,4})-tire fitment",
        "tires_db",
        "blog 'N-tire fitment library'",
    ),
    # README
    ("README.md", r"(\d{2,4})\s*bikes?,", "all_known_bikes", "README bikes count"),
    ("README.md", r"(\d{2,4})\s*parts,", "parts_db", "README parts count"),
    # "260 tires" drifted past the audit on 2026-07-06 because only bikes/parts
    # had README checkers — keep the tires + benchmark counts pinned too.
    ("README.md", r"(\d{2,4})\s*tires,", "tires_db", "README tires count"),
    (
        "README.md",
        r"against (\d{2,3}) published benchmarks",
        "benchmarks",
        "README benchmarks count",
    ),
    # ── README + issue-template baselines (added 2026-07-25 audit) ──────────
    #    docs/INVARIANTS.md I6 claims this script enforces the headline stats
    #    "quoted in web pages, README, and docs", but every baseline pattern
    #    was scoped to web/app/**. README.md therefore published the RETIRED
    #    pre-epoch pins (10.034 / 10.286 / 10.472) as the current contract on
    #    the repo's front page, and the bug-report template asked reporters to
    #    confirm K5 ≤ 10.034 ± 0.07 — a box a healthy tree cannot tick — while
    #    `make audit` reported "All headline numbers in sync". These close
    #    that gap so the claim in I6 is true.
    (
        "README.md",
        r"K5\s*→\s*([0-9]+\.[0-9]{1,4})\s*s",
        "baseline_k5",
        "README K5 baseline",
    ),
    (
        "README.md",
        r"R1\s+4C8\s*→\s*([0-9]+\.[0-9]{1,4})\s*s",
        "baseline_r1",
        "README R1 baseline",
    ),
    (
        "README.md",
        r"Hayabusa\s+Gen1\s*→\s*([0-9]+\.[0-9]{1,4})\s*s",
        "baseline_busa",
        "README Hayabusa baseline",
    ),
    (
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        r"K5 sim is within\s+([0-9]+\.[0-9]{1,4})s",
        "baseline_k5",
        "bug-report template K5 baseline",
    ),
    (
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        r"R1 sim is within\s+([0-9]+\.[0-9]{1,4})s",
        "baseline_r1",
        "bug-report template R1 baseline",
    ),
    # Reference baselines (4 decimal places) — these MUST stay pinned
    (
        "web/app/page.js",
        r"K5\s*[=:]\s*([0-9]+\.[0-9]{1,4})\s*s",
        "baseline_k5",
        "landing-page K5 baseline",
    ),
    (
        "web/app/page.js",
        r"R1\s*[=:]\s*([0-9]+\.[0-9]{1,4})\s*s",
        "baseline_r1",
        "landing-page R1 baseline",
    ),
    (
        "web/app/page.js",
        r"Hayabusa\s*[=:]\s*([0-9]+\.[0-9]{1,4})\s*s",
        "baseline_busa",
        "landing-page Hayabusa baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"K5[^.]*?([0-9]+\.[0-9]{4})\s*s",
        "baseline_k5",
        "blog K5 baseline",
    ),
    (
        "web/app/blog/*/page.js",
        # [^.0-9] (not [^.]) so list sentences like "K5 ..., R1 4C8, and
        # Hayabusa Gen 1 ... (10.0334s / 10.2859s / 10.4712s)" don't capture
        # K5's number — the false positive that mangled the 600cc blog post
        # when --fix ran on 2026-06-07.
        r"R1\s+4C8[^.0-9]*?([0-9]+\.[0-9]{4})\s*s",
        "baseline_r1",
        "blog R1 baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"Hayabusa\s+Gen1[^.]*?([0-9]+\.[0-9]{4})\s*s",
        "baseline_busa",
        "blog Hayabusa baseline",
    ),
    # ── Baseline free-prose forms (added 2026-07-17) — "…pinned/preserved in
    #    the simulator at NN.NNNN s" and "(around NN.NN s sim …)" phrasings.
    #    The H2 SX blog quoted the retired Hayabusa pin as "Gen 1 baseline
    #    preserved in the simulator at 10.4712 s" and survived the gate
    #    because the structured patterns above require the literal
    #    "Gen1"/"4C8" tokens. Anchored on the three reference bikes; [^.]*?
    #    keeps each match inside one sentence (and refuses to hop across an
    #    earlier decimal number); 4-decimal figures are the pin tell for the
    #    "at" form, while 2-decimal "around" claims that honestly round the
    #    current pin pass via the existing 0.005 float tolerance. Era-marked
    #    lines stay exempt (HISTORICAL_LINE_MARKER, handled in _scan_file /
    #    _patch_file).
    (
        "web/app/blog/*/page.js",
        r"K5\b[^.]*?\bat\s+([0-9]+\.[0-9]{4})\s*s",
        "baseline_k5",
        "blog K5 'at N.NNNN s' prose baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"\bR1\b[^.]*?\bat\s+([0-9]+\.[0-9]{4})\s*s",
        "baseline_r1",
        "blog R1 'at N.NNNN s' prose baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"Hayabusa\b[^.]*?\bat\s+([0-9]+\.[0-9]{4})\s*s",
        "baseline_busa",
        "blog Hayabusa 'at N.NNNN s' prose baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"K5\b[^.]*?\baround\s+([0-9]+\.[0-9]{2,4})\s*s\s+sim\b",
        "baseline_k5",
        "blog K5 'around N.NN s sim' prose baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"\bR1\b[^.]*?\baround\s+([0-9]+\.[0-9]{2,4})\s*s\s+sim\b",
        "baseline_r1",
        "blog R1 'around N.NN s sim' prose baseline",
    ),
    (
        "web/app/blog/*/page.js",
        r"Hayabusa\b[^.]*?\baround\s+([0-9]+\.[0-9]{2,4})\s*s\s+sim\b",
        "baseline_busa",
        "blog Hayabusa 'around N.NN s sim' prose baseline",
    ),
]


# Lines carrying this marker narrate a DATED historical episode (e.g. "the
# baselines sat at 10.0334s before/after that change") — the numbers are
# facts about a past epoch, not live claims, so rewriting them to the
# current pins would falsify history. Writers must pair the marker with an
# explicit date/epoch reference in the same passage. Added July 13, 2026
# when the physics epoch re-based the reference pins.
HISTORICAL_LINE_MARKER = "[historical baselines]"


def _scan_file(path: Path, pattern: str, truth_value):
    """Return list of (line_num, declared, drift_bool, line_preview, match_obj) tuples."""
    out = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return out
    for i, line in enumerate(text.splitlines(), start=1):
        if HISTORICAL_LINE_MARKER in line:
            continue
        for m in re.finditer(pattern, line):
            declared = m.group(1)
            try:
                declared_num = float(declared) if "." in declared else int(declared)
            except ValueError:
                continue
            if isinstance(truth_value, str):
                drift = "?"
            elif isinstance(truth_value, float):
                drift = abs(declared_num - truth_value) > 0.005
            else:
                drift = declared_num != truth_value
            out.append((i, declared, drift, line.strip()[:120]))
    return out


# ─── In-place patching ───────────────────────────────────────────────────────


def _patch_file(path: Path, pattern: str, truth_value) -> int:
    """Apply pattern in-place, replacing group(1) with truth_value. Returns count of edits.

    Lines carrying HISTORICAL_LINE_MARKER are never patched (see the marker's
    doc comment) — _scan_file skips them, so they are never reported as drift
    either; this guard is belt-and-braces for direct callers."""
    if isinstance(truth_value, str) and (
        truth_value.startswith(("ERROR", TEST_COUNT_SKIP_PREFIX))
    ):
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0

    if isinstance(truth_value, float):
        truth_str = f"{truth_value:.4f}"
        tol = 0.0001
    else:
        truth_str = str(truth_value)
        tol = None

    edits = 0

    def _replacer(m):
        nonlocal edits
        declared = m.group(1)
        try:
            declared_num = float(declared) if "." in declared else int(declared)
        except ValueError:
            return m.group(0)
        if tol is not None:
            if abs(declared_num - truth_value) <= tol:
                return m.group(0)
        else:
            if declared_num == truth_value:
                return m.group(0)
        # Replace just the captured group within the full match.
        full = m.group(0)
        start_in_match = m.start(1) - m.start(0)
        end_in_match = m.end(1) - m.start(0)
        edits += 1
        return full[:start_in_match] + truth_str + full[end_in_match:]

    # Patch line-by-line so HISTORICAL_LINE_MARKER lines are never touched.
    out_lines = []
    for line in text.splitlines(keepends=True):
        if HISTORICAL_LINE_MARKER in line:
            out_lines.append(line)
            continue
        out_lines.append(re.sub(pattern, _replacer, line))
    new_text = "".join(out_lines)
    if edits > 0 and new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return edits


def apply_fixes(truth, verbose=True):
    """Iterate PATTERNS, patch every file in place. Return list of changed paths."""
    changed = set()
    for file_glob, pattern, truth_key, desc in PATTERNS:
        truth_value = truth.get(truth_key)
        if truth_value is None or (
            isinstance(truth_value, str)
            and (truth_value.startswith(("ERROR", TEST_COUNT_SKIP_PREFIX)))
        ):
            continue
        for path in REPO.glob(file_glob):
            n = _patch_file(path, pattern, truth_value)
            if n > 0:
                rel = path.relative_to(REPO).as_posix()
                changed.add(rel)
                if verbose:
                    print(f"  PATCH  {rel}  ({n}× {desc} → {truth_value})")
    return sorted(changed)


# ─── OG card regeneration ────────────────────────────────────────────────────


def regenerate_og_card(truth, output_path: Path | None = None, verbose=True) -> Path:
    """Render the 1200x630 OG social card.

    EVERGREEN BY DESIGN (July 2026, operator decision): the card carries no
    catalog counts, no accuracy figures, no beta copy — nothing that goes
    stale when the DB grows or a physics epoch moves the pins. It is pure
    brand: the identity-kit redline-Q mark, the Moto/Quant lockup, the
    tagline, an unlabeled v(t) curve, and the domain. `truth` is accepted
    for call-site compatibility but deliberately unused.
    """
    del truth  # evergreen — see docstring
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError(
            "Pillow not installed. Run: pip install --user --break-system-packages Pillow"
        ) from exc

    out_path = output_path or OG_IMAGE_PATH

    W, H = 1200, 630
    # IGNITION v5 brand (identity kit): Ink surfaces + Signal orange.
    BG = (10, 10, 11)
    TEXT = (240, 240, 240)
    DIM = (140, 140, 150)
    ORANGE = (255, 94, 31)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    def _font(size, weight="regular"):
        candidates = (
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
            ]
            if weight == "bold"
            else [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        )
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    f_brand = _font(92, "bold")
    f_tag = _font(36, "bold")
    f_sub = _font(21)
    f_url = _font(22, "bold")
    f_chart = _font(20, "bold")

    # ── Redline-Q mark (identity-kit geometry, 512 reference frame) ──────
    def draw_mark(cx0, cy0, size):
        """Supersampled mark pasted at (cx0, cy0) top-left, side = size."""
        ss = 4
        m = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
        md = ImageDraw.Draw(m)
        k = size * ss / 512.0
        cx, cy = 256 * k, 263.6 * k
        r_out, r_in = 153.6 * k, 107.52 * k
        md.ellipse(
            [cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=(255, 255, 255, 255)
        )
        md.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(*BG, 255))
        gr = r_out * 1.25
        md.pieslice([cx - gr, cy - gr, cx + gr, cy + gr], -60, -30, fill=(*BG, 255))
        quad = [(296.89, 240.25), (397.22, 152.95), (392.58, 95.69), (278.97, 222.33)]
        md.polygon([(x * k, y * k) for x, y in quad], fill=(*ORANGE, 255))
        hub = 13.6 * k
        md.ellipse([cx - hub, cy - hub, cx + hub, cy + hub], fill=(*ORANGE, 255))
        m = m.resize((size, size), Image.LANCZOS)
        img.paste(m, (cx0, cy0), m)

    # ── v(t) sweep — unlabeled, drawn first so type always wins ──────────
    pts = []
    n_pts = 110
    for i in range(n_pts):
        t = i / (n_pts - 1)
        v = 1 - 2.71828 ** (-4.2 * t)
        x = 80 + (1120 - 80) * t
        yy = 548 - (548 - 408) * v
        pts.append((x, yy))
    d.line(pts, fill=(120, 48, 20), width=6)
    d.line(pts, fill=ORANGE, width=3)
    ex, ey = pts[-1]
    d.ellipse((ex - 8, ey - 8, ex + 8, ey + 8), fill=ORANGE)
    d.ellipse((ex - 3, ey - 3, ex + 3, ey + 3), fill=(255, 255, 255))
    d.text((830, 438), "v(t)  ·  quarter mile", font=f_chart, fill=(96, 96, 100))

    # ── Dashed centerline motif (the strip) under the curve ──────────────
    y = 548
    x = 60
    while x < 900:
        d.line([(x, y), (x + 26, y)], fill=(58, 58, 62), width=3)
        x += 52

    # ── Brand block: mark + lockup + tagline + evergreen sub ─────────────
    draw_mark(52, 96, 190)
    moto_w = d.textbbox((0, 0), "Moto", font=f_brand)[2]
    d.text((262, 138), "Moto", font=f_brand, fill=TEXT)
    d.text((262 + moto_w, 138), "Quant", font=f_brand, fill=ORANGE)
    d.text((266, 258), "The physics of faster", font=f_tag, fill=TEXT)
    d.text(
        (266, 316),
        "Physics-based quarter-mile simulation for motorcycles",
        font=f_sub,
        fill=DIM,
    )

    # ── Bottom row: origin line + domain pill ─────────────────────────────
    d.text(
        (60, 572), "Built in India for the drag racing community", font=f_sub, fill=DIM
    )
    dom_text = "motoquant.in"
    bbox = d.textbbox((0, 0), dom_text, font=f_url)
    dw = bbox[2] - bbox[0] + 44
    dh = 46
    dx, dy = W - dw - 60, H - dh - 34
    d.rounded_rectangle((dx, dy, dx + dw, dy + dh), radius=dh // 2, fill=ORANGE)
    d.text((dx + 22, dy + 11), dom_text, font=f_url, fill=(10, 10, 11))

    img.save(out_path, "PNG", optimize=True)
    if verbose:
        size_kb = out_path.stat().st_size // 1024
        print(
            f"  REGEN  {out_path.relative_to(REPO).as_posix()}  ({W}×{H}, {size_kb} KB)"
        )
    return out_path


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    ap.add_argument(
        "--fail-on-drift", action="store_true", help="exit 1 if drift detected"
    )
    ap.add_argument(
        "--fix",
        action="store_true",
        help="auto-patch declared values to truth in-place",
    )
    ap.add_argument(
        "--regen-og", action="store_true", help="regenerate OG social-card PNG"
    )
    args = ap.parse_args()

    truth = _truth_values()

    # ── Drift report ────────────────────────────────────────────────────
    drift_count = 0
    drift_records = []
    for file_glob, pattern, truth_key, desc in PATTERNS:
        truth_value = truth.get(truth_key)
        if truth_value is None or (
            isinstance(truth_value, str)
            and (truth_value.startswith(("ERROR", TEST_COUNT_SKIP_PREFIX)))
        ):
            continue
        for path in REPO.glob(file_glob):
            findings = _scan_file(path, pattern, truth_value)
            for line_num, declared, drift, line_preview in findings:
                if drift is True:
                    drift_count += 1
                    drift_records.append(
                        {
                            "file": path.relative_to(REPO).as_posix(),
                            "line": line_num,
                            "declared": declared,
                            "truth": truth_value,
                            "truth_key": truth_key,
                            "description": desc,
                        }
                    )

    if not args.json:
        print("=" * 78)
        print("HEADLINE-STATS AUDIT — declared values vs source-of-truth")
        print("=" * 78)
        print()
        print("Source-of-truth values:")
        for k, v in truth.items():
            print(f"  {k:24s}  {v}")
        print()
        for rec in drift_records:
            print(
                f"  DRIFT  {rec['file']}:{rec['line']}  declares={rec['declared']}  truth={rec['truth']}  ({rec['description']})"
            )

    # ── Apply fixes ─────────────────────────────────────────────────────
    changed_files = []
    if args.fix:
        if not args.json:
            print()
            print("Applying --fix in-place...")
        changed_files = apply_fixes(truth, verbose=not args.json)

    # ── Regenerate OG card ──────────────────────────────────────────────
    # Triggered by --regen-og, OR by --fix when (a) the image is older than
    # the DB, OR (b) we just patched any numeric drift in this run (since
    # the image bakes those numbers in).
    og_regenerated = False
    needs_regen = (
        args.regen_og
        or (args.fix and truth.get("og_image_stale"))
        or (args.fix and bool(changed_files))
    )
    if needs_regen:
        if not args.json:
            print()
            print("Regenerating OG social card...")
        try:
            regenerate_og_card(truth, verbose=not args.json)
            og_regenerated = True
            changed_files.append(OG_IMAGE_PATH.relative_to(REPO).as_posix())
        except Exception as exc:
            print(f"  OG REGEN FAILED: {exc}", file=sys.stderr)
            if args.fix:
                # Fix mode treats OG regen failure as soft — don't abort
                pass
            else:
                return 2

    if args.json:
        print(
            json.dumps(
                {
                    "truth": truth,
                    "drift": drift_records,
                    "fixed_files": changed_files,
                    "og_regenerated": og_regenerated,
                },
                indent=2,
                default=str,
            )
        )
    else:
        print()
        if drift_count == 0 and not changed_files:
            print("All headline numbers in sync. No action needed.")
        elif args.fix:
            n = len(set(changed_files))
            print(f"{drift_count} drift(s) detected, {n} file(s) modified by --fix.")
        else:
            print(
                f"{drift_count} drift(s) detected. Patch each location and re-run, or use --fix."
            )
        print()

    return 1 if (args.fail_on_drift and drift_count > 0 and not args.fix) else 0


if __name__ == "__main__":
    sys.exit(main())
