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
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OG_IMAGE_PATH = REPO / "web" / "public" / "og-image.png"
DB_PATH = REPO / "motoquant.db"


# ─── Source-of-truth derivation ──────────────────────────────────────────────


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

    # Fast test count (best effort — collect-only, longer timeout)
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            timeout=60,
        )
        # pytest --collect-only -q final line: "N tests collected in Xs" or just count
        for pat in [r"(\d+)\s+tests?\s+collected", r"^=+\s*(\d+)\s+tests?\s+collected"]:
            m = re.search(pat, result.stdout + result.stderr, re.MULTILINE)
            if m:
                truth["tests_collected"] = int(m.group(1))
                break
        else:
            truth["tests_collected"] = "ERROR: no count line"
    except Exception as exc:
        truth["tests_collected"] = f"ERROR: {exc}"

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
        "web/app/bikes/[id]/layout.js",
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
    (
        "web/app/pricing/page.js",
        r"Bike catalog \((\d{2,4}) bikes?\)",
        "all_known_bikes",
        "pricing tier description",
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
    # README
    ("README.md", r"(\d{2,4})\s*bikes?,", "all_known_bikes", "README bikes count"),
    ("README.md", r"(\d{2,4})\s*parts,", "parts_db", "README parts count"),
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
]


def _scan_file(path: Path, pattern: str, truth_value):
    """Return list of (line_num, declared, drift_bool, line_preview, match_obj) tuples."""
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
                drift = "?"
            elif isinstance(truth_value, float):
                drift = abs(declared_num - truth_value) > 0.005
            else:
                drift = declared_num != truth_value
            out.append((i, declared, drift, line.strip()[:120]))
    return out


# ─── In-place patching ───────────────────────────────────────────────────────


def _patch_file(path: Path, pattern: str, truth_value) -> int:
    """Apply pattern in-place, replacing group(1) with truth_value. Returns count of edits."""
    if isinstance(truth_value, str) and truth_value.startswith("ERROR"):
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

    new_text = re.sub(pattern, _replacer, text)
    if edits > 0 and new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return edits


def apply_fixes(truth, verbose=True):
    """Iterate PATTERNS, patch every file in place. Return list of changed paths."""
    changed = set()
    for file_glob, pattern, truth_key, desc in PATTERNS:
        truth_value = truth.get(truth_key)
        if truth_value is None or (
            isinstance(truth_value, str) and truth_value.startswith("ERROR")
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
    """Render a 1200×630 OG social card matching the existing layout."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError(
            "Pillow not installed. Run: pip install --user --break-system-packages Pillow"
        ) from exc

    out_path = output_path or OG_IMAGE_PATH

    W, H = 1200, 630
    BG = (10, 10, 12)  # near-black
    PANEL = (20, 20, 24)
    BORDER = (40, 40, 48)
    TEXT = (240, 240, 240)
    DIM = (140, 140, 150)
    ORANGE = (255, 122, 0)  # signal orange
    GREEN = (32, 200, 110)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    def _font(size, weight="regular"):
        # Try common system fonts; fall back to default
        candidates = []
        if weight == "bold":
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
            ]
        else:
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/DejaVuSans.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    f_pill = _font(20)
    f_brand = _font(96, "bold")
    f_tag = _font(38, "bold")
    f_sub = _font(20)
    f_stat_n = _font(64, "bold")
    f_stat_l = _font(18, "bold")
    f_url = _font(22, "bold")
    f_chart = _font(22, "bold")
    f_chart_sub = _font(16)

    # ── Top pill: "Free · Open Source · India" ─────────────────────────
    pill_text = "Free  ·  Open Source  ·  India"
    pill_x, pill_y = 60, 56
    bbox = d.textbbox((0, 0), pill_text, font=f_pill)
    pw = bbox[2] - bbox[0] + 60
    ph = bbox[3] - bbox[1] + 22
    d.rounded_rectangle(
        (pill_x, pill_y, pill_x + pw, pill_y + ph),
        radius=ph // 2,
        fill=PANEL,
        outline=BORDER,
        width=1,
    )
    # Orange dot
    d.ellipse(
        (pill_x + 18, pill_y + ph // 2 - 5, pill_x + 28, pill_y + ph // 2 + 5),
        fill=ORANGE,
    )
    d.text((pill_x + 36, pill_y + 10), pill_text, font=f_pill, fill=TEXT)

    # ── Brand wordmark ──────────────────────────────────────────────────
    d.text((60, 132), "MotoQuant", font=f_brand, fill=TEXT)
    d.text((60, 240), "The Physics of Faster", font=f_tag, fill=ORANGE)

    # Top-10 mean accuracy from latest sweep, fallback to ±0.032s
    top10 = "±0.032"
    try:
        sweep_files = sorted(REPO.glob("reports/sweep_et_*.json"), reverse=True)
        if sweep_files:
            data = json.loads(sweep_files[0].read_text())
            # data structure varies; look for top-10 mean in summary
            summary = data.get("summary") or {}
            if isinstance(summary, dict):
                for k in (
                    "top10_mean_abs_delta_s",
                    "top_10_mean_abs",
                    "top10_mean_delta",
                ):
                    if k in summary:
                        top10 = f"±{float(summary[k]):.3f}"
                        break
    except Exception:
        pass

    sub = f"Quarter-mile simulation  ·  {top10}s top-10 mean accuracy"
    d.text((60, 296), sub, font=f_sub, fill=DIM)

    # ── 4-stat grid in orange ───────────────────────────────────────────
    bikes_n = truth.get("all_known_bikes", "—")
    parts_n = truth.get("parts_db", "—")
    venues_n = truth.get("venues_db", "—")
    tests_n = truth.get("tests_collected", "—")
    if isinstance(tests_n, str) and tests_n.startswith("ERROR"):
        tests_n = "1000+"

    stats = [
        (str(bikes_n), "BIKES"),
        (str(parts_n), "PARTS"),
        (str(venues_n), "VENUES"),
        (str(tests_n), "TESTS"),
    ]

    grid_x, grid_y = 60, 380
    cell_w = 130
    gap = 20
    for i, (n, lbl) in enumerate(stats):
        x = grid_x + i * (cell_w + gap)
        y = grid_y
        d.text((x, y), n, font=f_stat_n, fill=ORANGE)
        d.text((x, y + 78), lbl, font=f_stat_l, fill=DIM)

    # ── motoquant.in pill (bottom-right) ────────────────────────────────
    url = "motoquant.in"
    bbox = d.textbbox((0, 0), url, font=f_url)
    uw = bbox[2] - bbox[0] + 42
    uh = bbox[3] - bbox[1] + 22
    ux = W - uw - 60
    uy = H - uh - 50
    d.rounded_rectangle(
        (ux, uy, ux + uw, uy + uh), radius=uh // 2, fill=ORANGE, outline=ORANGE
    )
    d.text((ux + 21, uy + 8), url, font=f_url, fill=(8, 8, 8))

    # ── Right panel: GSX-R K5 v(t) curve ─────────────────────────────────
    panel_x = 700
    panel_y = 100
    panel_w = 440
    panel_h = 300
    d.rounded_rectangle(
        (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h),
        radius=14,
        fill=PANEL,
        outline=BORDER,
        width=1,
    )

    # Header strip
    d.text(
        (panel_x + 22, panel_y + 18),
        "GSX-R 1000 K5  ·  Aamby Valley",
        font=f_chart,
        fill=TEXT,
    )
    d.text(
        (panel_x + 22, panel_y + 50),
        "Reference baseline · preserved exactly",
        font=f_chart_sub,
        fill=DIM,
    )

    # Plot region
    pad_l = 28
    pad_r = 28
    pad_t = 96
    pad_b = 56
    plot_x0 = panel_x + pad_l
    plot_y0 = panel_y + pad_t
    plot_x1 = panel_x + panel_w - pad_r
    plot_y1 = panel_y + panel_h - pad_b

    # Approx K5 v(t) curve (0 → 10.03s, 0 → 239 km/h) — sigmoid-ish ramp
    n_pts = 80
    t_max = 10.0334
    v_max = 239.8
    pts = []
    for i in range(n_pts):
        t = i * t_max / (n_pts - 1)
        # Empirical-ish K5 acceleration: rapid early ramp, then taper
        v = v_max * (1 - 2.71828 ** (-0.42 * t))
        x = plot_x0 + (plot_x1 - plot_x0) * (t / t_max)
        y = plot_y1 - (plot_y1 - plot_y0) * (v / v_max)
        pts.append((x, y))

    # Axis baseline
    d.line([(plot_x0, plot_y1), (plot_x1, plot_y1)], fill=BORDER, width=1)
    # Curve
    d.line(pts, fill=ORANGE, width=3)
    # End-point dot
    d.ellipse(
        (pts[-1][0] - 6, pts[-1][1] - 6, pts[-1][0] + 6, pts[-1][1] + 6), fill=ORANGE
    )

    # Footer badge
    badge_text = f"{t_max:.2f}s  ·  {v_max:.0f} km/h"
    bbox = d.textbbox((0, 0), badge_text, font=f_chart)
    bw = bbox[2] - bbox[0] + 30
    bh = bbox[3] - bbox[1] + 18
    bx = panel_x + panel_w - bw - 20
    by = panel_y + panel_h - bh - 16
    d.rounded_rectangle(
        (bx, by, bx + bw, by + bh), radius=bh // 2, fill=GREEN, outline=GREEN
    )
    d.text((bx + 15, by + 7), badge_text, font=f_chart, fill=(8, 8, 8))

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
            isinstance(truth_value, str) and truth_value.startswith("ERROR")
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
