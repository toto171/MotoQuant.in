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
from scripts.sweep_lib import (
    bind_benchmark_for_record,
    build_bench_map,
    model_specificity_score as _model_specificity_score,  # noqa: F401  (re-export, pinned by tests)
    wb_match as _wb_match,  # noqa: F401  (re-export)
)
from scripts.validation_sweep import BENCHMARKS


def cluster_for(
    manufacturer, model_name, disp_cc, power_hp, stroke_type, category, cylinders=None
):
    """Report-side cluster label. Delegates to the canonical taxonomy in
    motoquant.category_profiles.derive_category_tag (single source of truth
    since July 6, 2026 — previously this function mirrored it by hand and the
    two could drift). Pass ``cylinders`` for the v2 cylinder-aware clusters;
    None reproduces the July-3 taxonomy.
    """
    from motoquant.category_profiles import derive_category_tag

    tag = derive_category_tag(
        manufacturer=manufacturer,
        model_name=model_name,
        displacement_cc=disp_cc,
        peak_power_hp=power_hp,
        stroke_type=stroke_type,
        category=category,
        cylinders=cylinders,
    )
    return TAG_TO_CLUSTER.get(tag, "other")


# category_tag (underscores, physics dispatch) -> report cluster label (dashes)
TAG_TO_CLUSTER = {
    "two_stroke": "two-stroke",
    "cruiser_1300p": "cruiser-1300+",
    "litre_sport_195p": "litre-sport-195+",
    "litre_sport_600_1000": "litre-sport-600-1000",
    "sport_twin_600_1300": "sport-twin-600-1300",
    "small_i4_screamer": "small-i4-screamer",
    "single_300_500": "single-300-500",
    "mid_twin_500_700": "mid-twin-500-700",
    "mid_twin_300_500": "mid-twin-300-500",
    "entry_200_300": "entry-200-300",
    "entry_150_200": "entry-150-200",
    "other": "other",
    "unknown": "other",
}


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
                    cylinders=getattr(spec, "cylinders", None),
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
    # 2026-05-25): for each catalog row, pick the *most-specific* in-range
    # benchmark (out-of-range fallback). Logic lives in
    # sweep_lib.bind_benchmark_for_record, shared with the other drivers.
    bench_map = build_bench_map(BENCHMARKS)

    for rec in results:
        if rec.get("kind") != "catalog" or rec.get("error"):
            continue
        best_match = bind_benchmark_for_record(
            rec["manufacturer"],
            rec["model"],
            rec.get("year_from"),
            rec.get("year_to"),
            bench_map,
        )
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
        targets = {"K5": 9.9331, "R1": 10.1436, "Hayabusa": 10.3633}
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
