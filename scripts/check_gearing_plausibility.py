#!/usr/bin/env python3
"""Gearing plausibility gate over every bike in ALL_KNOWN_BIKES.

A bike's overall gearing is implausible when its top gear is far taller than the
engine can pull, or when its terminal speed is reached several gears below top.
Both symptoms come from a primary-reduction or cassette that does not belong to
the bike (a litre-bike primary on a 150 cc single, a sibling's cassette, ...).

Criteria (calibrated on bikes whose gearing is verified against service manuals):

  (a) top-gear road speed at PEAK-POWER rpm  /  simulated terminal speed  > 1.25
      (verified bikes sit at 0.74-1.07; the catalog median is 0.98)
  (b) terminal speed is reached 2+ gears below the top gear
      (verified bikes have a gap of at most 1)

The peak-power-rpm normalisation (rather than redline) keeps the inferred-redline
factor from contaminating the metric.  Terminal speed needs a top-speed simulation,
so it is cached in ``tests/data/gearing_plausibility_baseline.json`` ("terminal"
table, every bike); the analytic part is recomputed on the fly.

The baseline also records which bikes are CURRENTLY flagged, with a cause bucket:

  generic-primary    no spec primary and no Tier-1 entry: the Tier-2 default
                     primary (a litre inline-4 value) is used
  tier1-unverified   a Tier-1 entry supplies the primary (its own value is unsourced
                     for several Indian models) or a substring match hit a sibling
  explicit-spec      the spec carries its own primary_ratio
  tall-by-design     generic primary on an adventure/cruiser/touring bike of 600 cc+,
                     where a tall top gear is plausible

Usage:
    python scripts/check_gearing_plausibility.py               # compare to baseline
    python scripts/check_gearing_plausibility.py --write-baseline   # re-simulate + rewrite
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASELINE_PATH = ROOT / "tests" / "data" / "gearing_plausibility_baseline.json"

APK_LIMIT = 1.25
GEAR_GAP_LIMIT = 2
_TALL_BY_DESIGN_CATEGORIES = {"adventure", "cruiser", "touring", "touring_cruiser"}


def bike_keys(specs) -> list[str]:
    """Stable per-spec keys: 'mfr|model|year_from-year_to', '#n' for repeats."""
    seen: dict[str, int] = {}
    keys = []
    for s in specs:
        base = f"{s.manufacturer}|{s.model_name}|{s.year_from}-{s.year_to}"
        n = seen.get(base, 0)
        seen[base] = n + 1
        keys.append(base if n == 0 else f"{base}#{n + 1}")
    return keys


def _tier1_entry(spec):
    from motoquant.scraper import gear_ratios as G

    mfr = spec.manufacturer.lower().strip().replace(" ", "_")

    def norm(s):
        return (
            s.lower()
            .replace("-", "")
            .replace("_", "")
            .replace(".", "")
            .replace(" ", "")
        )

    ml, mn = spec.model_name.lower(), norm(spec.model_name)
    hits = []
    for e in G._DB:
        if e["mfr"] != mfr:
            continue
        p = e["model"].lower()
        if not (G._pattern_match(p, ml) or G._pattern_match(norm(e["model"]), mn)):
            continue
        if spec.year_from is not None:
            a, b = e["year"]
            if not a <= spec.year_from <= b:
                continue
        hits.append((len(p), e))
    hits.sort(key=lambda x: -x[0])
    return hits[0][1] if hits else None


def cause_bucket(spec) -> str:
    if spec.primary_ratio:
        return "explicit-spec"
    if _tier1_entry(spec) is not None:
        return "tier1-unverified"
    cc = spec.displacement_cc or 0
    if (spec.category or "").lower() in _TALL_BY_DESIGN_CATEGORIES and cc >= 600:
        return "tall-by-design"
    return "generic-primary"


def analytic_metrics(spec) -> dict:
    """Top-gear speed at peak-power rpm and gear count (no simulation)."""
    from motoquant.scraper.importer import spec_to_bike_config

    cfg = spec_to_bike_config(spec)
    dt = cfg.drivetrain
    ngear = len(dt.gear_ratios)
    peak_rpm = cfg.engine.peak_power_rpm
    v_top_kmh = (
        peak_rpm
        * 2
        * math.pi
        / 60
        * cfg.tires.rear_rolling_radius_m
        / dt.overall_ratio(ngear - 1)
        * 3.6
    )
    return {"ngear": ngear, "v_top_at_peak_kmh": v_top_kmh}


def terminal_speed(spec) -> tuple[float, int]:
    """(terminal km/h, terminal gear 1-based) from the sweep-identical top-speed run."""
    from motoquant.physics import MotoQuantEngine
    from motoquant.scraper.importer import spec_to_bike_config

    cfg = spec_to_bike_config(spec)
    ts = MotoQuantEngine(cfg).run_top_speed(max_time=60.0)
    return float(ts.terminal_velocity_kmh), int(ts.terminal_gear)


def _terminal_job(args):
    key, idx = args
    warnings.simplefilter("ignore")
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    return key, terminal_speed(ALL_KNOWN_BIKES[idx])


def compute_terminal_table(specs, keys, only=None, workers=3) -> dict:
    """Run top-speed sims for every bike (or only the keys in ``only``)."""
    jobs = [(k, i) for i, k in enumerate(keys) if only is None or k in only]
    if not jobs:
        return {}
    from multiprocessing import Pool

    with Pool(workers) as pool:
        out = pool.map(_terminal_job, jobs, chunksize=4)
    return {k: [round(t[0], 3), t[1]] for k, t in out}


def evaluate(specs, keys, terminal_table) -> dict:
    """Return {key: metrics} for every bike flagged by criterion (a) or (b)."""
    flagged = {}
    for spec, key in zip(specs, keys):
        term = terminal_table.get(key)
        if term is None:
            continue
        m = analytic_metrics(spec)
        term_kmh, term_gear = term
        apk = m["v_top_at_peak_kmh"] / term_kmh if term_kmh else float("inf")
        gap = m["ngear"] - term_gear
        fa, fb = apk > APK_LIMIT, gap >= GEAR_GAP_LIMIT
        if fa or fb:
            flagged[key] = {
                "apk": round(apk, 3),
                "gear_gap": gap,
                "criteria": ("a" if fa else "") + ("b" if fb else ""),
                "bucket": cause_bucket(spec),
            }
    return flagged


def load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text())


def main() -> int:
    warnings.simplefilter("ignore")
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    specs = list(ALL_KNOWN_BIKES)
    keys = bike_keys(specs)

    if "--write-baseline" in sys.argv:
        terminal = compute_terminal_table(specs, keys)
        flagged = evaluate(specs, keys, terminal)
        data = {
            "criteria": {
                "apk_limit": APK_LIMIT,
                "gear_gap_limit": GEAR_GAP_LIMIT,
                "apk": "top-gear speed at peak-power rpm / terminal speed",
            },
            "terminal": dict(sorted(terminal.items())),
            "flagged": dict(sorted(flagged.items())),
        }
        BASELINE_PATH.write_text(json.dumps(data, indent=1) + "\n")
        buckets: dict[str, int] = {}
        for v in flagged.values():
            buckets[v["bucket"]] = buckets.get(v["bucket"], 0) + 1
        print(f"wrote {BASELINE_PATH}: {len(flagged)}/{len(specs)} flagged {buckets}")
        return 0

    base = load_baseline()
    terminal = dict(base["terminal"])
    missing = {k for k in keys if k not in terminal}
    terminal.update(compute_terminal_table(specs, keys, only=missing))
    flagged = evaluate(specs, keys, terminal)
    new = sorted(set(flagged) - set(base["flagged"]))
    fixed = sorted(set(base["flagged"]) - set(flagged))
    for k in new:
        print(f"NEWLY FLAGGED: {k} {flagged[k]}")
    for k in fixed:
        print(f"NO LONGER FLAGGED (shrink the baseline): {k}")
    print(f"{len(flagged)} flagged, {len(new)} new, {len(fixed)} fixed")
    return 1 if (new or fixed) else 0


if __name__ == "__main__":
    sys.exit(main())
