"""
validation_sweep.py
===================
Runs the full MotoQuant physics engine against every bike in
``ALL_KNOWN_BIKES`` (287 specs) plus the three validated reference bikes
(K5, R1 4C8, Hayabusa Gen1), and generates a dated JSON report in
``reports/validation_YYYY-MM-DD.json``.

What it does
------------
1. For every spec, calls ``spec_to_bike_config`` + ``MotoQuantEngine.run()``
   and records the simulated ET, trap speed, and whether the run finished
   the quarter mile.  (A bike that doesn't reach 402 m within 15 s is
   flagged as ``over-time``.)
2. For the subset of specs that have real-world published ETs in
   ``BENCHMARKS`` (drawn from Cycle World / Sport Rider / MCN tests), it
   additionally records ``delta = sim_et - target_et``.
3. Aggregates: total sims, failures, pass-rate, mean/median abs-delta,
   bias, accuracy buckets (within 0.1/0.2/0.5/1.0 s).
4. Writes a machine-readable JSON report to ``reports/validation_<date>.json``
   and prints a human-readable summary to stdout.

Run with::

    python validation_sweep.py              # writes report for today
    python validation_sweep.py --json-only  # only writes JSON, no stdout
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import time
import warnings
from pathlib import Path

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# Silence importer/validator noise; we log per-bike status ourselves.
logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# ── Real-world ET benchmarks (same source list as validation_run.py) ─────────
# Each: (manufacturer_substr, model_substr, year_hint, target_et_s,
#         trap_kmh, source_label)
BENCHMARKS: list[tuple[str, str, int, float, float, str]] = [
    # Hayabusa family
    ("Suzuki", "Hayabusa", 2008, 9.85, 250, "Cycle World 2008"),
    ("Suzuki", "Hayabusa", 2021, 9.75, 248, "Sport Rider 2021"),
    # Kawasaki ZX / H2
    ("Kawasaki", "Ninja ZX-14R", 2012, 9.47, 246, "Cycle World 2012"),
    ("Kawasaki", "ZZR1400", 2006, 9.90, 242, "MCN 2006"),
    ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
    ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
    # GSX-R 1000 family
    ("Suzuki", "GSX-R 1000", 2007, 10.00, 239, "Sport Rider 2007"),
    ("Suzuki", "GSX-R 1000", 2009, 10.00, 239, "Sport Rider 2009"),
    ("Suzuki", "GSX-R 1000", 2017, 9.95, 240, "Cycle World 2017"),
    ("Suzuki", "GSX-R 1000", 2003, 10.10, 236, "Sport Rider 2003"),
    ("Suzuki", "GSX-R 1000", 2001, 10.20, 235, "Sport Rider 2001"),
    # BMW
    ("BMW", "S 1000 RR", 2015, 9.90, 240, "Cycle World 2015"),
    ("BMW", "S 1000 RR", 2019, 9.85, 243, "Cycle World 2019"),
    ("BMW", "M1000RR", 2021, 9.80, 245, "Cycle World 2021"),
    # ZX-10R
    ("Kawasaki", "Ninja ZX-10R", 2004, 10.30, 240, "Sport Rider 2004"),
    ("Kawasaki", "Ninja ZX-10R", 2011, 10.10, 240, "Sport Rider 2011"),
    ("Kawasaki", "Ninja ZX-10R", 2021, 10.00, 241, "Cycle World 2021"),
    # CBR1000RR family
    ("Honda", "CBR1000RR", 2008, 10.20, 238, "Sport Rider 2008"),
    ("Honda", "CBR1000RR-R", 2020, 9.95, 240, "Cycle World 2020"),
    ("Honda", "CBR 1000RR Fireblade SP", 2017, 10.10, 238, "Sport Rider 2017"),
    ("Honda", "CBR 1000RR Fireblade", 2004, 10.30, 234, "Sport Rider 2004"),
    # Ducati
    ("Ducati", "Panigale V4", 2018, 10.00, 240, "Cycle World 2018"),
    ("Ducati", "Panigale V4R", 2019, 10.05, 238, "Cycle World 2019"),
    ("Ducati", "1199 Panigale", 2012, 10.10, 235, "Cycle World 2012"),
    ("Ducati", "1299 Panigale", 2015, 9.95, 238, "Sport Rider 2015"),
    ("Ducati", "1098", 2007, 10.40, 230, "Cycle World 2007"),
    ("Ducati", "Streetfighter V4", 2020, 10.10, 235, "Cycle World 2020"),
    # Yamaha R1 family
    ("Yamaha", "YZF-R1", 2004, 10.30, 238, "Sport Rider 2004"),
    ("Yamaha", "YZF-R1", 2009, 10.20, 240, "Sport Rider 2009"),
    ("Yamaha", "YZF-R1", 2015, 10.10, 242, "Cycle World 2015"),
    ("Yamaha", "YZF-R1M", 2015, 10.05, 243, "Cycle World 2015"),
    ("Yamaha", "VMAX 1700", 2009, 10.30, 217, "Cycle World 2009"),
    ("Yamaha", "MT-10", 2016, 10.35, 228, "Cycle World 2016"),
    # Various
    ("Kawasaki", "Ninja ZX-9R", 2000, 10.50, 230, "Sport Rider 2000"),
    ("Suzuki", "TL1000R", 1998, 10.50, 231, "Cycle World 1998"),
    ("Aprilia", "RSV4 Factory", 2021, 10.05, 238, "Cycle World 2021"),
    ("Aprilia", "RSV4 1000", 2009, 10.40, 230, "Sport Rider 2009"),
    ("KTM", "1290 Super Duke R", 2022, 10.15, 230, "Cycle World 2022"),
    ("Triumph", "Rocket 3 R", 2020, 10.50, 226, "Cycle World 2020"),
    ("MV Agusta", "Brutale 1000 RR", 2019, 10.15, 240, "Cycle World 2019"),
    # 2-stroke benchmarks (Cycle World / historical drag tests / magazine)
    ("Yamaha", "RD350", 1973, 13.20, 152, "Cycle World 1973"),
    ("Yamaha", "RD400", 1976, 13.00, 156, "Cycle World 1976"),
    ("Suzuki", "RG500", 1985, 11.60, 180, "Cycle World 1985"),
    ("Honda", "NSR250R", 1990, 12.10, 172, "MCN 1990"),
    ("Aprilia", "RS250", 1996, 12.40, 168, "Sport Rider 1996"),
    # Indian-market small-cc (from local drag strip telemetry collected
    # by R2 Moto, Aamby Valley community runs — community logged)
    ("Bajaj", "Pulsar NS200", 2019, 15.80, 130, "Community runs 2019"),
    ("KTM", "Duke 390", 2019, 14.20, 150, "Community runs 2019"),
    ("Royal Enfield", "Continental GT 650", 2019, 14.50, 140, "MCN 2019"),
    ("Yamaha", "R15 V3", 2020, 16.20, 125, "Community runs 2020"),
    # Indian-market 150-400cc expansion (April 2026)
    ("Bajaj", "Pulsar RS 200", 2015, 15.70, 132, "Derived from 0-100 (autoX 2015)"),
    ("Bajaj", "Pulsar N250", 2021, 15.45, 135, "Derived from 0-100 (autoX 2021)"),
    ("Bajaj", "Pulsar NS400Z", 2024, 14.10, 155, "Derived from 0-100 (autoX 2024)"),
    ("KTM", "Duke 250", 2017, 15.20, 140, "Derived from 0-100 (motorbeam 2017)"),
    ("KTM", "RC 390", 2017, 13.16, 159, "ZeroTo60Times 2017"),
    ("TVS", "Apache RR 310", 2020, 14.80, 145, "Derived from 0-100 (bikewale 2020)"),
    ("TVS", "Apache RTR 200 4V", 2016, 15.90, 128, "Derived from 0-100 (bikewale 2016)"),
    ("Yamaha", "R15 V4", 2021, 16.40, 123, "Derived from 0-100 (autocar 2021)"),
    ("Yamaha", "MT-15", 2019, 15.80, 130, "Derived from 0-100 (bikewale 2019)"),
    ("Yamaha", "R3", 2015, 15.80, 125, "MotoStatz 2015"),
    ("Yamaha", "MT-03", 2020, 14.05, 92, "AccelerationTimes 2020"),
    ("Honda", "CB350RS", 2021, 15.50, 138, "Derived from 0-100 (bikewale 2021)"),
    ("Honda", "CBR500R", 2022, 13.51, 98, "MotoStatz 2022"),
    ("Honda", "CB650R", 2021, 11.80, 115, "AccelerationTimes 2021"),
    ("Suzuki", "Gixxer 250", 2018, 16.10, 126, "Derived from 0-100 (bikewale 2018)"),
    # Mid-range global expansion (April 2026)
    ("Suzuki", "SV650", 2016, 11.82, 115, "FastestLaps 2016"),
    ("Kawasaki", "Ninja 300", 2013, 14.60, 102, "MotoStatz 2013"),
    ("Kawasaki", "Ninja 400", 2018, 12.98, 102, "MotoStatz 2018"),
    ("Kawasaki", "Ninja 650", 2020, 12.30, 111, "MotoStatz 2020"),
    ("Kawasaki", "Z 650", 2017, 12.40, 110, "MotoStatz 2017"),
    ("Harley-Davidson", "Sportster S", 2021, 11.10, 122, "HDForums timeslip 2021"),
    ("Royal Enfield", "Continental GT 650", 2020, 13.90, 97, "FastestLaps 2020"),
    ("Triumph", "Trident 660", 2021, 12.00, 111, "MotoStatz 2021"),
    ("Triumph", "Speed 400", 2023, 14.50, 140, "Derived from 0-100 (bikewale 2023)"),
    ("Benelli", "302R", 2017, 15.80, 120, "MotorbikeCatalog 2017"),
    ("Benelli", "TNT 600i", 2014, 12.60, 108, "MotorbikeCatalog 2014"),
    ("Aprilia", "RS 457", 2024, 13.30, 97, "FastestLaps 2024"),
    # SE Asia enthusiast 150cc expansion (April 2026)
    ("Yamaha", "YZF-R7", 2022, 11.64, 116, "MotoStatz 2022"),
    ("Yamaha", "FZ25", 2018, 16.00, 127, "Derived from 0-100 (bikewale 2018)"),
]

REFERENCE_BIKES: list[tuple[str, int, callable, float, float, str]] = [
    ("Suzuki GSX-R 1000 K5", 2005, gsxr1000_k5, 9.97, 238, "Cycle World 2005"),
    ("Yamaha YZF-R1 4C8", 2007, yzfr1_4c8, 10.30, 240, "Sport Rider 2007"),
    ("Suzuki Hayabusa Gen1", 1999, hayabusa_gen1, 10.40, 235, "Cycle World 1999"),
]


def _model_match(pattern: str, spec_model: str) -> bool:
    """Word-boundary model match — avoids `YZF-R1` accidentally matching
    `YZF-R15`.  Uses simple tokenisation: split on space / hyphen and check
    every pattern token appears as a standalone token in the spec string.
    """
    import re as _re
    tokens = [t for t in _re.split(r"[\s\-]+", pattern) if t]
    spec_tokens = set(t for t in _re.split(r"[\s\-]+", spec_model) if t)
    return all(t in spec_tokens for t in tokens)


def find_spec(mfr: str, model: str, year: int):
    """Locate a spec in ALL_KNOWN_BIKES matching mfr/model/year."""
    for b in ALL_KNOWN_BIKES:
        if b.manufacturer != mfr:
            continue
        if not _model_match(model, b.model_name):
            continue
        if year < b.year_from or year > (b.year_to or b.year_from + 3):
            continue
        return b
    return None


def _sim_spec(spec) -> dict:
    """Run one simulation for a spec dict, return a record."""
    t0 = time.time()
    try:
        cfg = spec_to_bike_config(spec)
        result = MotoQuantEngine(cfg).run()
        took = time.time() - t0

        # Determine status and ET
        if not result.finished_quarter:
            status = "did-not-finish"
            sim_et_s = None
            sim_trap_kmh = None
        elif result.time_quarter > 14.9:  # finished but over 15s threshold
            status = "over-time"
            sim_et_s = round(float(result.time_quarter), 3)
            sim_trap_kmh = round(float(result.speed_quarter) * 3.6, 1)
        else:
            status = "ok"
            sim_et_s = round(float(result.time_quarter), 3)
            sim_trap_kmh = round(float(result.speed_quarter) * 3.6, 1)

        record = {
            "manufacturer": spec.manufacturer,
            "model": spec.model_name,
            "year_from": spec.year_from,
            "year_to": spec.year_to,
            "category": getattr(spec, "category", None),
            "displacement_cc": spec.displacement_cc,
            "stroke_type": getattr(spec, "stroke_type", None) or 4,
            "status": status,
            "wall_time_s": round(took, 3),
        }

        if sim_et_s is not None:
            record["sim_et_s"] = sim_et_s
            record["sim_trap_kmh"] = sim_trap_kmh
        else:
            # For did-not-finish, record max distance and elapsed time
            record["max_distance_m"] = round(result.max_distance_m, 1)
            record["elapsed_time_s"] = round(result.elapsed_time_s, 2)

        return record
    except Exception as exc:
        return {
            "manufacturer": spec.manufacturer,
            "model": spec.model_name,
            "year_from": spec.year_from,
            "year_to": spec.year_to,
            "category": getattr(spec, "category", None),
            "displacement_cc": spec.displacement_cc,
            "stroke_type": getattr(spec, "stroke_type", None) or 4,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "wall_time_s": round(time.time() - t0, 3),
        }


def run_sweep(verbose: bool = True) -> dict:
    """Run the sweep. Returns a dict ready for JSON serialization."""
    results: list[dict] = []
    benchmark_hits: list[dict] = []

    t_start = time.time()

    # 1. Reference bikes
    for name, year, factory, target_et, trap_kmh, source in REFERENCE_BIKES:
        t0 = time.time()
        try:
            cfg = factory()
            r = MotoQuantEngine(cfg).run()
            sim_et = float(r.time_quarter)
            sim_trap = float(r.speed_quarter) * 3.6
            rec = {
                "manufacturer": name.split()[0],
                "model": " ".join(name.split()[1:]),
                "year_from": year,
                "year_to": year,
                "category": getattr(cfg, "category", "sport"),
                "displacement_cc": cfg.engine.displacement_cc,
                "stroke_type": getattr(cfg.engine, "stroke_type", 4) or 4,
                "sim_et_s": round(sim_et, 3),
                "sim_trap_kmh": round(sim_trap, 1),
                "status": "ok" if sim_et <= 14.9 else "over-time",
                "wall_time_s": round(time.time() - t0, 3),
                "is_reference": True,
            }
            results.append(rec)
            benchmark_hits.append({
                **rec,
                "target_et_s": target_et,
                "target_trap_kmh": trap_kmh,
                "delta_et_s": round(sim_et - target_et, 3),
                "source": source,
            })
        except Exception as exc:
            results.append({
                "manufacturer": name.split()[0],
                "model": " ".join(name.split()[1:]),
                "year_from": year,
                "year_to": year,
                "status": "error",
                "error": str(exc),
                "is_reference": True,
            })

    # 2. Full catalog sweep
    n = len(ALL_KNOWN_BIKES)
    for i, spec in enumerate(ALL_KNOWN_BIKES, 1):
        rec = _sim_spec(spec)
        results.append(rec)
        if verbose and i % 25 == 0:
            print(
                f"  [{i:>3}/{n}] {rec['manufacturer'][:14]:<14} "
                f"{rec['model'][:26]:<26} "
                f"{rec.get('sim_et_s', '---')}s  {rec['status']}"
            )

        # benchmark match (word-boundary matching — not substring)
        for bmfr, bmodel, byear, tgt_et, tgt_trap, src in BENCHMARKS:
            if spec.manufacturer != bmfr:
                continue
            if not _model_match(bmodel, spec.model_name):
                continue
            if byear < spec.year_from or byear > (spec.year_to or spec.year_from + 3):
                continue
            if rec["status"] != "ok":
                break
            benchmark_hits.append({
                **rec,
                "benchmark_year": byear,
                "target_et_s": tgt_et,
                "target_trap_kmh": tgt_trap,
                "delta_et_s": round(rec["sim_et_s"] - tgt_et, 3),
                "source": src,
            })
            break

    t_elapsed = time.time() - t_start

    # 3. Aggregate stats
    n_total = len(results)
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_over = sum(1 for r in results if r["status"] == "over-time")
    n_dnf = sum(1 for r in results if r["status"] == "did-not-finish")
    n_err = sum(1 for r in results if r["status"] == "error")
    n_bench = len(benchmark_hits)
    abs_deltas = [abs(b["delta_et_s"]) for b in benchmark_hits]
    signed_deltas = [b["delta_et_s"] for b in benchmark_hits]

    def _bucket(x: float) -> int:
        return sum(1 for d in abs_deltas if d <= x)

    if abs_deltas:
        mean_abs = sum(abs_deltas) / len(abs_deltas)
        sorted_abs = sorted(abs_deltas)
        median_abs = sorted_abs[len(sorted_abs) // 2]
        bias = sum(signed_deltas) / len(signed_deltas)
    else:
        mean_abs = median_abs = bias = 0.0

    summary = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "wall_time_s": round(t_elapsed, 1),
        "bikes_total": n_total,
        "bikes_ok": n_ok,
        "bikes_over_time": n_over,
        "bikes_did_not_finish": n_dnf,
        "bikes_error": n_err,
        "benchmark_matches": n_bench,
        "mean_abs_delta_s": round(mean_abs, 3),
        "median_abs_delta_s": round(median_abs, 3),
        "bias_s": round(bias, 3),
        "within_0p10s": _bucket(0.10),
        "within_0p20s": _bucket(0.20),
        "within_0p50s": _bucket(0.50),
        "within_1p00s": _bucket(1.00),
        "pass_rate_0p20s": round(_bucket(0.20) / max(1, n_bench), 3),
    }

    return {
        "summary": summary,
        "benchmark_hits": benchmark_hits,
        "bikes": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-only", action="store_true", help="suppress stdout progress")
    ap.add_argument("--output-dir", default="reports", help="reports directory")
    args = ap.parse_args()

    verbose = not args.json_only
    if verbose:
        print(f"Validation sweep — {len(ALL_KNOWN_BIKES)} known bikes + "
              f"{len(REFERENCE_BIKES)} reference bikes")
        print("─" * 70)

    report = run_sweep(verbose=verbose)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    today = _dt.date.today().isoformat()
    out_path = out_dir / f"validation_{today}.json"
    out_path.write_text(json.dumps(report, indent=2))

    if verbose:
        s = report["summary"]
        print("\n" + "═" * 70)
        print(" VALIDATION SWEEP SUMMARY")
        print("═" * 70)
        print(f"  Bikes total:            {s['bikes_total']}")
        print(f"    ok:                   {s['bikes_ok']}")
        print(f"    over-time (>14.9s):   {s['bikes_over_time']}")
        print(f"    did-not-finish:       {s['bikes_did_not_finish']}")
        print(f"    error:                {s['bikes_error']}")
        print(f"  Benchmark matches:      {s['benchmark_matches']}")
        print(f"  Mean |ΔET|:             {s['mean_abs_delta_s']:.3f}s")
        print(f"  Median |ΔET|:           {s['median_abs_delta_s']:.3f}s")
        print(f"  Bias (sim − real):      {s['bias_s']:+.3f}s")
        print(f"  Within ±0.10s:          {s['within_0p10s']}/{s['benchmark_matches']}")
        print(f"  Within ±0.20s:          {s['within_0p20s']}/{s['benchmark_matches']}")
        print(f"  Within ±0.50s:          {s['within_0p50s']}/{s['benchmark_matches']}")
        print(f"  Within ±1.00s:          {s['within_1p00s']}/{s['benchmark_matches']}")
        print(f"  Pass-rate (±0.20s):     {s['pass_rate_0p20s']:.1%}")
        print(f"  Wall time:              {s['wall_time_s']:.1f}s")
        print()
        print(f"  Report written to:      {out_path}")


if __name__ == "__main__":
    main()
