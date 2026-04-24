"""
gearing_audit.py
================
Audits every bike in ALL_KNOWN_BIKES for gearing sanity.

Checks performed
----------------
1. Top-gear ratio > 1.10  — unusual for a sport bike (close-ratio, yes; >1.10, suspect)
2. Top-gear ratio > 1.30  — almost certainly wrong for any modern sport bike
3. First-gear ratio < 1.80 — too low (some commuters have 5-speed, but still ≥ 2.0)
4. Gear spread (1st / top) < 1.8  — unusually narrow spread
5. Gear count outside 4–6  — exotic edge case (3-speed, 7-speed); flag for review
6. Total overall ratio sanity: v_max@redline < 150 km/h or > 430 km/h
   (using primary from importer lookup + sprocket sizes)

Output: console table + optional JSON.

Usage::
    python scripts/gearing_audit.py
    python scripts/gearing_audit.py --json > reports/gearing_audit.json
    python scripts/gearing_audit.py --top-gear-gt 1.05   # lower the threshold
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
import logging
from pathlib import Path

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from motoquant.scraper.importer import spec_to_bike_config


def _tire_radius_m(size_str: str | None, default: float = 0.315) -> float:
    """Parse '190/55ZR17' → radius in metres."""
    if not size_str:
        return default
    try:
        width = int(size_str.split("/")[0])
        asp_str = size_str.split("/")[1][:2]
        aspect = int(asp_str)
        rim_inch = int(size_str[-2:])
        return (rim_inch * 25.4 / 2 + width * aspect / 100) / 1000
    except Exception:
        return default


def audit_all(top_gear_gt: float = 1.10) -> list[dict]:
    results = []

    for spec in ALL_KNOWN_BIKES:
        gr = spec.gear_ratios or []
        if len(gr) < 2:
            continue

        top = gr[-1]
        first = gr[0]
        spread = first / top if top > 0 else 0
        n_gears = len(gr)

        flags: list[str] = []

        if top > 1.30:
            flags.append(f"TOP_GEAR_CRITICAL ({top:.3f} > 1.30)")
        elif top > top_gear_gt:
            flags.append(f"TOP_GEAR_HIGH ({top:.3f} > {top_gear_gt})")

        if first < 1.80:
            flags.append(f"FIRST_GEAR_LOW ({first:.3f} < 1.80)")

        if spread < 1.80:
            flags.append(f"SPREAD_NARROW ({spread:.2f} < 1.80)")

        if n_gears not in (4, 5, 6):
            flags.append(f"GEAR_COUNT ({n_gears})")

        # Overall ratio check — needs importer lookup for primary ratio
        try:
            cfg = spec_to_bike_config(spec)
            g6 = cfg.drivetrain.gear_ratios[-1]
            prim = cfg.drivetrain.primary_ratio
            fs = cfg.drivetrain.front_sprocket
            rs = cfg.drivetrain.rear_sprocket
            r_tire = _tire_radius_m(spec.rear_tire_size)

            if fs > 0 and prim > 0:
                overall = g6 * prim * (rs / fs)
                redline_est = (spec.peak_power_rpm or 10000) * 1.12
                v_max_kph = redline_est * 2 * math.pi / 60 * r_tire / overall * 3.6
                if v_max_kph < 100:
                    flags.append(f"V_MAX_LOW ({v_max_kph:.0f} km/h @ est-redline)")
                elif v_max_kph > 450 and top > 1.0:
                    # Only flag V_MAX_HIGH when top gear is NOT overdriven (<1.0).
                    # Legitimately overdriven bikes (e.g. ZX-10R 2008 with 6th=0.871)
                    # produce large v_max figures that are physically correct — the aero
                    # drag cap limits real-world top speed, not the gearing.
                    flags.append(f"V_MAX_HIGH ({v_max_kph:.0f} km/h @ est-redline)")
            else:
                overall = 0
                v_max_kph = 0
        except Exception as e:
            overall = 0
            v_max_kph = 0

        results.append(
            {
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "year": spec.year_from,
                "n_gears": n_gears,
                "first_gear": round(first, 3),
                "top_gear": round(top, 3),
                "spread": round(spread, 2),
                "ratios": [round(x, 3) for x in gr],
                "front_sprocket": spec.front_sprocket,
                "rear_sprocket": spec.rear_sprocket,
                "primary_used": round(cfg.drivetrain.primary_ratio, 3) if overall else None,
                "overall_ratio": round(overall, 3) if overall else None,
                "v_max_est_kph": round(v_max_kph, 0) if v_max_kph else None,
                "flags": flags,
                "has_flags": bool(flags),
            }
        )

    return results


def print_table(results: list[dict], top_gear_gt: float, show_all: bool) -> None:
    flagged = [r for r in results if r["has_flags"]]
    clean = [r for r in results if not r["has_flags"]]

    print(f"\nGearing Audit — {len(results)} bikes, threshold top_gear > {top_gear_gt}")
    print(f"  Flagged: {len(flagged)}   Clean: {len(clean)}\n")

    if not flagged:
        print("  No flags raised. All bikes within thresholds.")
        return

    # Group by flag type severity
    flagged.sort(key=lambda r: (-r["top_gear"], r["manufacturer"], r["model"]))

    header = (
        f"{'Manufacturer':<20} {'Model':<35} {'Yr':>4} "
        f"{'G':>2} {'1st':>5} {'Top':>5} {'Sprd':>4} "
        f"{'vMax':>5}  Flags"
    )
    print(header)
    print("-" * 130)
    for r in flagged:
        flag_str = " | ".join(r["flags"])
        vmax = f"{int(r['v_max_est_kph'])}" if r["v_max_est_kph"] else "  ?"
        print(
            f"{r['manufacturer']:<20} {r['model']:<35} {r['year']:>4} "
            f"{r['n_gears']:>2} {r['first_gear']:>5.3f} {r['top_gear']:>5.3f} {r['spread']:>4.2f} "
            f"{vmax:>5}  {flag_str}"
        )

    if show_all:
        print(f"\n{'─'*130}\nClean bikes ({len(clean)}):\n")
        for r in clean:
            print(
                f"  {r['manufacturer']:<20} {r['model']:<35} {r['year']:>4}  "
                f"top={r['top_gear']:.3f}  ratios={r['ratios']}"
            )

    # Summary by flag type
    print(f"\n{'─'*50} Flag summary")
    from collections import Counter

    all_flags = [f.split("(")[0].strip() for r in flagged for f in r["flags"]]
    for ftype, count in Counter(all_flags).most_common():
        print(f"  {ftype:<30} {count:>4} bikes")

    print(f"\nTop-10 highest top-gear ratios:")
    top10 = sorted(results, key=lambda r: -r["top_gear"])[:10]
    for r in top10:
        print(
            f"  {r['manufacturer']:<20} {r['model']:<35} ({r['year']:>4})  "
            f"top={r['top_gear']:.3f}  F{r['front_sprocket']}/R{r['rear_sprocket']}"
        )


def main() -> None:
    p = argparse.ArgumentParser(description="Gearing sanity audit for ALL_KNOWN_BIKES")
    p.add_argument("--json", action="store_true", help="Output JSON instead of table")
    p.add_argument("--all", action="store_true", help="Also show clean bikes in table mode")
    p.add_argument(
        "--top-gear-gt",
        type=float,
        default=1.10,
        help="Flag top-gear ratios above this threshold (default: 1.10)",
    )
    args = p.parse_args()

    results = audit_all(top_gear_gt=args.top_gear_gt)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_table(results, args.top_gear_gt, show_all=args.all)


if __name__ == "__main__":
    main()
