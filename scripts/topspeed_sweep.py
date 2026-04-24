"""
topspeed_sweep.py
==================
Runs MotoQuantEngine.run_top_speed() across every ALL_KNOWN_BIKES spec and
scores the results against a curated list of published top-speed benchmarks
(factory claims + derestricted magazine tests).

Outputs:
    reports/sweep_topspeed_YYYY-MM-DD.json      # per-bike V_max, t, distance
    reports/sweep_topspeed_benchmarks_YYYY-MM-DD.json  # delta vs published

Run with::
    python scripts/topspeed_sweep.py              # writes reports for today
    python scripts/topspeed_sweep.py --json-only  # suppress stdout

Why this is separate from validation_sweep.py:
    validation_sweep.py focuses on quarter-mile ET + trap. Top-speed runs
    are a different physics regime (high Reynolds drag, top-gear pull, aero
    sensitivity dominant) and deserve their own scoring + regression tests
    so that accuracy in one regime doesn't mask problems in the other.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import time
import warnings
from pathlib import Path

# Reuse the word-boundary model matcher from validation_sweep so "Duke 390"
# doesn't accidentally match "Duke 390 Adventure".
from validation_sweep import _model_match  # type: ignore

from motoquant import MotoQuantEngine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


# ── Published top-speed benchmarks ────────────────────────────────────────
# Format: (manufacturer_substr, model_substr, year_hint, target_kmh, source)
# Sources: factory specs, Cycle World, Sport Rider, MCN magazine tests,
# derestricted V-max runs. For factory-limited hyperbikes (299 km/h gentleman's
# agreement) the target is the limited figure; the sim-delta column lets us
# tell at a glance whether the sim is respecting the limit or blowing past it.
BENCHMARKS: list[tuple[str, str, int, float, str]] = [
    # ── Hyperbikes (factory-limited to 299 km/h by gentleman's agreement) ──
    ("Suzuki", "Hayabusa", 1999, 299, "factory-limited"),
    ("Suzuki", "Hayabusa", 2008, 299, "factory-limited"),
    ("Suzuki", "Hayabusa", 2021, 299, "factory-limited"),
    ("Kawasaki", "Ninja ZX-14R", 2012, 299, "factory-limited"),
    ("Kawasaki", "ZZR1400", 2006, 299, "factory-limited"),
    ("Kawasaki", "Ninja H2", 2015, 340, "factory / MCN derestricted"),
    # ── Litre superbikes (factory-limited; tests show 280-320 derestricted) ─
    ("Suzuki", "GSX-R 1000", 2005, 283, "Cycle World derestricted"),
    ("Suzuki", "GSX-R 1000", 2007, 293, "Sport Rider"),
    ("Suzuki", "GSX-R 1000", 2017, 299, "factory-limited"),
    ("BMW", "S 1000 RR", 2019, 303, "derestricted"),
    ("BMW", "M1000RR", 2021, 314, "derestricted"),
    ("Kawasaki", "Ninja ZX-10R", 2021, 300, "MCN"),
    ("Honda", "CBR1000RR", 2020, 299, "MCN"),
    ("Yamaha", "YZF-R1", 2015, 298, "MCN"),
    ("Ducati", "Panigale V4", 2018, 299, "MCN"),
    ("Aprilia", "RSV4 Factory", 2021, 293, "MCN"),
    # ── Naked / sport-tourer ──────────────────────────────────────────────
    ("KTM", "1290 Super Duke R", 2022, 290, "factory"),
    ("Yamaha", "MT-10", 2016, 258, "MCN"),
    ("BMW", "R1250GS", 2019, 220, "MCN"),
    # ── Big cruisers / muscle ─────────────────────────────────────────────
    ("Triumph", "Rocket 3 R", 2020, 225, "factory"),
    ("Yamaha", "VMAX 1700", 2009, 235, "MCN"),
    # ── Mid-sport twins/triples ───────────────────────────────────────────
    ("Yamaha", "YZF-R7", 2022, 220, "MCN"),
    ("Aprilia", "RS 660", 2021, 220, "MCN"),
    ("Aprilia", "RS 457", 2024, 180, "factory / reviews"),
    ("Suzuki", "SV650", 2016, 215, "MCN"),
    ("Kawasaki", "Ninja 650", 2020, 208, "MCN"),
    ("Honda", "CB650R", 2021, 209, "MCN"),
    ("Triumph", "Trident 660", 2021, 220, "MCN"),
    # ── Entry sport twins ─────────────────────────────────────────────────
    ("Kawasaki", "Ninja 400", 2018, 185, "MCN"),
    ("Kawasaki", "Ninja 300", 2013, 171, "MCN"),
    ("Kawasaki", "Ninja ZX-4RR", 2023, 220, "MCN"),
    # ── Indian-market 150-400cc ───────────────────────────────────────────
    ("KTM", "Duke 390", 2019, 167, "factory"),
    ("Bajaj", "Pulsar NS200", 2019, 136, "factory"),
    ("Bajaj", "Pulsar RS 200", 2015, 141, "factory"),
    ("Yamaha", "YZF-R15 V3", 2018, 139, "factory"),
    ("TVS", "Apache RR 310", 2020, 160, "factory"),
    # ── 2-stroke classics ─────────────────────────────────────────────────
    ("Yamaha", "RD350", 1973, 175, "factory"),
    ("Yamaha", "RD400 Daytona", 1976, 177, "factory"),
    ("Kawasaki", "H2 Mach IV", 1973, 201, "factory"),
    ("Suzuki", "RG500", 1985, 220, "factory"),
]


def _sim_spec(spec) -> dict:
    """Run top-speed sim on one spec, return a JSON-friendly dict."""
    cfg = spec_to_bike_config(spec)
    ts = MotoQuantEngine(cfg).run_top_speed(max_time=90.0)
    return {
        "manufacturer": spec.manufacturer,
        "model": spec.model_name,
        "year": spec.year_from,
        "disp_cc": spec.displacement_cc,
        "power_hp": spec.peak_power_hp,
        "mass_kg": spec.dry_mass_kg,
        "stroke_type": getattr(spec, "stroke_type", None) or 4,
        "v_max_kmh": round(ts.terminal_velocity_kmh, 1),
        "time_to_term_s": round(ts.time_to_terminal_s, 2),
        "dist_to_term_m": round(ts.distance_to_terminal_m, 0),
        "gear_at_term": ts.terminal_gear,
        "rpm_at_term": round(ts.terminal_rpm, 0),
        "power_at_term_kw": round(ts.terminal_power_kw, 1),
        "reached_plateau": ts.reached_plateau,
    }


def _match(mfr_sub: str, mdl_sub: str, year_hint: int, results: list[dict]):
    cands = [
        r
        for r in results
        if mfr_sub.lower() in r["manufacturer"].lower()
        and _model_match(mdl_sub, r["model"])
    ]
    if not cands:
        return None
    cands.sort(key=lambda r: abs((r["year"] or 0) - year_hint))
    return cands[0]


def run_sweep(verbose: bool = True) -> dict:
    t0 = time.perf_counter()
    results = []
    fails = 0
    for spec in ALL_KNOWN_BIKES:
        try:
            results.append(_sim_spec(spec))
        except Exception as exc:
            fails += 1
            if verbose and fails <= 3:
                print(f"FAIL {spec.manufacturer} {spec.model_name}: {exc}")
    wall = time.perf_counter() - t0

    # Score against benchmarks
    scored = []
    for mfr, mdl, yr, target, src in BENCHMARKS:
        m = _match(mfr, mdl, yr, results)
        if not m:
            continue
        delta = m["v_max_kmh"] - target
        scored.append(
            {
                "benchmark": f"{mfr} {mdl} ({yr})",
                "target_kmh": target,
                "sim_kmh": m["v_max_kmh"],
                "delta_kmh": delta,
                "source": src,
                "bike_match": f"{m['manufacturer']} {m['model']}",
            }
        )

    abs_d = [abs(x["delta_kmh"]) for x in scored]
    deltas = [x["delta_kmh"] for x in scored]

    summary = {
        "date": _dt.date.today().isoformat(),
        "n_bikes_simmed": len(results),
        "n_fails": fails,
        "plateau_count": sum(1 for r in results if r["reached_plateau"]),
        "wall_time_s": round(wall, 1),
        "benchmarks_matched": len(scored),
        "mean_abs_delta_kmh": round(sum(abs_d) / len(abs_d), 1) if abs_d else None,
        "median_abs_delta_kmh": round(sorted(abs_d)[len(abs_d) // 2], 1)
        if abs_d
        else None,
        "bias_kmh": round(sum(deltas) / len(deltas), 1) if deltas else None,
        "within_10_kmh": sum(1 for d in abs_d if d <= 10),
        "within_20_kmh": sum(1 for d in abs_d if d <= 20),
        "within_30_kmh": sum(1 for d in abs_d if d <= 30),
    }

    if verbose:
        print(
            f"Top-speed sweep: {summary['n_bikes_simmed']} bikes, {summary['n_fails']} fails, "
            f"wall {summary['wall_time_s']}s"
        )
        print(f"  Plateau hit: {summary['plateau_count']}/{summary['n_bikes_simmed']}")
        print(f"  Benchmarks matched: {summary['benchmarks_matched']}")
        print(
            f"  Mean |Δ|: {summary['mean_abs_delta_kmh']} km/h  "
            f"median: {summary['median_abs_delta_kmh']}  bias: {summary['bias_kmh']:+}"
        )
        print(
            f"  Within ±10/±20/±30 km/h: "
            f"{summary['within_10_kmh']}/{summary['within_20_kmh']}/{summary['within_30_kmh']}"
        )

    return {"summary": summary, "sims": results, "scored": scored}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--json-only", action="store_true")
    args = p.parse_args()

    report = run_sweep(verbose=not args.json_only)

    out_dir = Path(__file__).parent.parent / "reports"
    out_dir.mkdir(exist_ok=True)
    date = _dt.date.today().isoformat()
    out = out_dir / f"sweep_topspeed_{date}.json"
    out.write_text(json.dumps(report, indent=2))
    if not args.json_only:
        print(f"\nReport: {out}")


if __name__ == "__main__":
    main()
