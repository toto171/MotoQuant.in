#!/usr/bin/env python3
"""sweep_with_clusters.py — run the 287-bike sweep and classify each
benchmark into the physics-calibration clusters used in CLAUDE.md.

Usage::

    python scripts/sweep_with_clusters.py OUT_JSON

Clusters (matches CLAUDE.md Apr 24 PM taxonomy):
  - ``litre-sport-195+``  (sport ≥195 hp)
  - ``litre-sport-600-1000``
  - ``mid-twin-500-700``
  - ``cruiser-1300+``
  - ``mid-twin-300-500``
  - ``entry-200-300``
  - ``entry-150-200``
  - ``two-stroke``
  - ``other``  (falls through the above)
"""

import json
import logging
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from scripts.validation_sweep import BENCHMARKS


def _wb_match(pattern: str, spec_str: str) -> bool:
    """Word-boundary token-set match. Splits on space/hyphen/dot and checks
    every pattern token appears as a standalone token in spec_str. Avoids
    the YZF-R1 vs YZF-R15 substring collision documented in CLAUDE.md
    April 21 fix and April 27 sanity-sweep regression discovery."""
    import re as _re

    tokens = [t for t in _re.split(r"[\s\-\.]+", pattern.lower()) if t]
    spec_tokens = {t for t in _re.split(r"[\s\-\.]+", spec_str.lower()) if t}
    return all(t in spec_tokens for t in tokens)


def _model_specificity_score(pattern: str) -> int:
    """Number of distinct tokens in pattern after splitting on space /
    hyphen / dot. Used to pick the *most-specific* benchmark match —
    e.g. 'Ninja H2 SX' (3 tokens) outranks 'Ninja H2' (2 tokens). Kept
    in sync with `scripts/validation_sweep.py::_model_specificity_score`.
    """
    import re as _re

    return len([t for t in _re.split(r"[\s\-\.]+", pattern) if t])


def cluster_for(manufacturer, model_name, disp_cc, power_hp, stroke_type, category):
    if stroke_type == 2:
        return "two-stroke"
    cat = (category or "sport").lower()
    if cat in ("cruiser", "touring", "muscle") and disp_cc and disp_cc >= 1300:
        return "cruiser-1300+"
    # Apr 27, 2026: high-displacement muscle/sport bikes (VMAX 1700,
    # Triumph Rocket 3, B-King) can be tagged "naked" or "sport" in
    # known_bikes.py for engine-inertia tuning reasons, but their mass
    # profile is cruiser-class. Route them to cruiser-1300+ to prevent
    # the litre-sport-195+ cluster from being polluted by 320 kg muscle
    # bikes whose ETs are inherently slower than 220 kg sport-1000s.
    if disp_cc and disp_cc >= 1500 and cat in ("naked", "sport"):
        return "cruiser-1300+"
    if cat in ("sport", "naked") and power_hp and power_hp >= 195:
        return "litre-sport-195+"
    if disp_cc:
        if 600 <= disp_cc < 1100 and cat in ("sport", "naked"):
            return "litre-sport-600-1000"
        if 500 <= disp_cc < 700:
            return "mid-twin-500-700"
        if 300 <= disp_cc < 500:
            return "mid-twin-300-500"
        if 200 <= disp_cc < 300:
            return "entry-200-300"
        if 150 <= disp_cc < 200:
            return "entry-150-200"
    return "other"


def run_sweep(out_path):
    results = []
    t0 = time.time()

    # Reference baselines first
    for label, fn in [
        ("K5", gsxr1000_k5),
        ("R1", yzfr1_4c8),
        ("Hayabusa", hayabusa_gen1),
    ]:
        cfg = fn()
        r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
        results.append(
            {
                "kind": "reference",
                "label": label,
                "name": cfg.name,
                "sim_et": float(r.time_quarter) if r.finished_quarter else None,
                "sim_trap_kmh": float(r.speed_quarter * 3.6)
                if r.finished_quarter
                else None,
                "finished": bool(r.finished_quarter),
            }
        )

    # Catalog sweep
    for i, spec in enumerate(ALL_KNOWN_BIKES):
        try:
            cfg = spec_to_bike_config(spec)
            r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
            rec = {
                "kind": "catalog",
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "year_from": spec.year_from,
                "year_to": spec.year_to,
                "disp_cc": spec.displacement_cc,
                "power_hp": spec.peak_power_hp,
                "stroke_type": getattr(spec, "stroke_type", 4) or 4,
                "category": getattr(spec, "category", None),
                "cluster": cluster_for(
                    spec.manufacturer,
                    spec.model_name,
                    spec.displacement_cc,
                    spec.peak_power_hp,
                    getattr(spec, "stroke_type", 4) or 4,
                    getattr(spec, "category", None),
                ),
                "finished": bool(r.finished_quarter),
                "sim_et": float(r.time_quarter) if r.finished_quarter else None,
                "sim_trap_kmh": float(r.speed_quarter * 3.6)
                if r.finished_quarter
                else None,
                "elapsed_s": float(r.elapsed_time_s),
            }
        except Exception as exc:
            rec = {
                "kind": "catalog",
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "error": f"{type(exc).__name__}: {exc}"[:200],
            }
        results.append(rec)

    # Attach benchmarks — score-and-pick (Option 2 from DISPATCH_INBOX
    # 2026-05-25). For each catalog row, scan every benchmark that
    # passes manufacturer + word-boundary model + year-range filters,
    # then pick the *most-specific* one (highest model-token-count).
    # Robust against benchmark insertion-order and prior first-match-
    # wins shadowing of long patterns by short ones, e.g.
    # "Ninja H2 SX (2018-2023)" now correctly binds to the 3-token
    # "Ninja H2 SX" benchmark rather than the 2-token "Ninja H2".
    bench_map = {}
    for bmfr, bmodel, byear, tgt_et, tgt_trap, src in BENCHMARKS:
        bench_map.setdefault((bmfr.lower(), bmodel.lower()), []).append(
            (byear, tgt_et, tgt_trap, src)
        )

    for rec in results:
        if rec.get("kind") != "catalog" or rec.get("error"):
            continue
        m_lo = rec["manufacturer"].lower()
        mod_lo = rec["model"].lower()
        yf = rec.get("year_from") or 0
        yt = rec.get("year_to") or yf

        best_match = None
        best_score = -1
        best_in_range = False  # in-range matches always beat out-of-range
        for (bm, bmod), entries in bench_map.items():
            if not (_wb_match(bm, m_lo) and _wb_match(bmod, mod_lo)):
                continue
            # Pick best entry from this benchmark group (in-range year first)
            in_range_entry = None
            for byear, tgt_et, tgt_trap, src in entries:
                if yf <= byear <= yt or (not yt and yf == byear):
                    in_range_entry = (tgt_et, tgt_trap, src)
                    break
            fallback_entry = (entries[0][1], entries[0][2], entries[0][3])
            chosen_entry = (
                in_range_entry if in_range_entry is not None else fallback_entry
            )
            entry_in_range = in_range_entry is not None
            score = _model_specificity_score(bmod)

            # Prefer in-range over out-of-range; within same range-status,
            # prefer higher specificity.
            if entry_in_range and not best_in_range:
                best_match = chosen_entry
                best_score = score
                best_in_range = True
            elif entry_in_range == best_in_range and score > best_score:
                best_match = chosen_entry
                best_score = score

        if best_match is not None and rec.get("sim_et") is not None:
            tgt_et, tgt_trap, src = best_match
            rec["bench_et"] = float(tgt_et)
            rec["bench_trap_kmh"] = float(tgt_trap)
            rec["bench_src"] = src
            rec["delta_et"] = float(rec["sim_et"] - tgt_et)

    took = time.time() - t0
    summary = _summarize(results)
    out = {"took_s": took, "results": results, "summary": summary}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)

    print(f"\nSweep took {took:.1f}s — {len(results)} rows written to {out_path}")
    _print_summary(summary)
    return 0


def _summarize(results):
    ref = {}
    by_cluster = {}
    all_deltas = []
    errors = 0
    dnf = 0
    for rec in results:
        if rec.get("kind") == "reference":
            ref[rec["label"]] = rec["sim_et"]
            continue
        if rec.get("error"):
            errors += 1
            continue
        if not rec.get("finished"):
            dnf += 1
        cl = rec.get("cluster", "other")
        entry = by_cluster.setdefault(
            cl, {"bikes": 0, "finished": 0, "dnf": 0, "deltas": []}
        )
        entry["bikes"] += 1
        if rec.get("finished"):
            entry["finished"] += 1
        else:
            entry["dnf"] += 1
        if rec.get("delta_et") is not None:
            entry["deltas"].append(rec["delta_et"])
            all_deltas.append(rec["delta_et"])

    def _stats(deltas):
        if not deltas:
            return {}
        import statistics as st

        abs_deltas = [abs(x) for x in deltas]
        return {
            "n": len(deltas),
            "mean_abs_delta": st.mean(abs_deltas),
            "median_abs_delta": st.median(abs_deltas),
            "bias": st.mean(deltas),
            "within_0.10": sum(1 for x in abs_deltas if x <= 0.10),
            "within_0.20": sum(1 for x in abs_deltas if x <= 0.20),
            "within_0.50": sum(1 for x in abs_deltas if x <= 0.50),
            "within_1.00": sum(1 for x in abs_deltas if x <= 1.00),
        }

    summary = {
        "references": ref,
        "total_bikes": sum(e["bikes"] for e in by_cluster.values()),
        "errors": errors,
        "dnf": dnf,
        "clusters": {
            cl: {
                **{k: v for k, v in e.items() if k != "deltas"},
                "stats": _stats(e["deltas"]),
            }
            for cl, e in by_cluster.items()
        },
        "overall_benchmark_stats": _stats(all_deltas),
    }
    # Top-10 closest
    finished = [
        r
        for r in results
        if r.get("kind") == "catalog" and r.get("delta_et") is not None
    ]
    finished.sort(key=lambda r: abs(r["delta_et"]))
    summary["top10_closest"] = [
        {"bike": f"{r['manufacturer']} {r['model']}", "delta": r["delta_et"]}
        for r in finished[:10]
    ]
    if finished[:10]:
        import statistics

        summary["top10_mean_abs"] = statistics.mean(
            abs(r["delta_et"]) for r in finished[:10]
        )
    return summary


def _print_summary(s):
    print("\n=== REFERENCES ===")
    for label, et in s.get("references", {}).items():
        targets = {"K5": 10.0334, "R1": 10.2859, "Hayabusa": 10.4712}
        t = targets.get(label, 0)
        print(f"  {label:10} ET={et:.4f}  target={t:.4f}  Δ={et - t:+.4f}")
    print(
        f"\nTotal catalog: {s['total_bikes']}  errors: {s['errors']}  DNF: {s['dnf']}"
    )
    print("\n=== OVERALL BENCHMARK STATS ===")
    o = s["overall_benchmark_stats"]
    if o:
        print(
            f"  N={o['n']}  mean|Δ|={o['mean_abs_delta']:.3f}s  median|Δ|={o['median_abs_delta']:.3f}s  bias={o['bias']:+.3f}s"
        )
        print(
            f"  within ±0.10s: {o['within_0.10']} ({100 * o['within_0.10'] / o['n']:.0f}%)"
        )
        print(
            f"  within ±0.20s: {o['within_0.20']} ({100 * o['within_0.20'] / o['n']:.0f}%)"
        )
        print(
            f"  within ±0.50s: {o['within_0.50']} ({100 * o['within_0.50'] / o['n']:.0f}%)"
        )
        print(
            f"  within ±1.00s: {o['within_1.00']} ({100 * o['within_1.00'] / o['n']:.0f}%)"
        )
    if "top10_mean_abs" in s:
        print(f"  top-10 mean|Δ| = {s['top10_mean_abs']:.4f}s")
    print("\n=== CLUSTER BIASES ===")
    for cl, c in sorted(s["clusters"].items()):
        st = c.get("stats") or {}
        if st:
            print(
                f"  {cl:22} bikes={c['bikes']:3d}  N={st['n']:2d}  mean|Δ|={st['mean_abs_delta']:6.3f}s  bias={st['bias']:+6.3f}s"
            )
        else:
            print(f"  {cl:22} bikes={c['bikes']:3d}  (no benchmarks)")


if __name__ == "__main__":
    out = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "reports/sweep_et_2026-04-24_post_smallcc_fix.json"
    )
    sys.exit(run_sweep(out))
