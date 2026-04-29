#!/usr/bin/env python3
"""benchmark_sweep.py — fast iterative sweep that ONLY runs bikes which
have a matching real-world benchmark in BENCHMARKS. Used during the
category-flavoured-physics rewrite (April 30, 2026) to keep the dev loop
under 30 s per iteration.

Honors source-quality weights (instrumented=1.0, magazine=0.5, forum=0.2,
derived=0.1) when computing cluster mean|Δ| and bias.

Usage::
    python scripts/benchmark_sweep.py [out.json]
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from scripts.sweep_with_clusters import cluster_for
from scripts.validation_sweep import BENCHMARKS


def _wb_match(pattern: str, spec_str: str) -> bool:
    tokens = [t for t in re.split(r"[\s\-\.]+", pattern.lower()) if t]
    spec_tokens = {t for t in re.split(r"[\s\-\.]+", spec_str.lower()) if t}
    return all(t in spec_tokens for t in tokens)


# Source-quality weights (April 30 decision: weighted by source quality).
# Heuristic: parse the source string for keywords. Anything containing
# "DERIVED" or "0-100" or "estimated" is heuristically-derived.
def _source_quality(src: str) -> tuple[float, str]:
    """Return (weight, label)."""
    s = src.lower()
    if "derived" in s or "0-100" in s or "estimated" in s:
        return (0.1, "derived")
    if "forum" in s or "community" in s or "logged" in s or "timeslip" in s:
        # Owner timeslip / forum claim — better than derived but not lab
        return (0.3, "forum_or_timeslip")
    if any(k in s for k in ("instrumented", "motostatz", "dragy", "vbox")):
        return (1.0, "instrumented")
    if any(k in s for k in ("cycle world", "sport rider", "mcn", "consumer news")):
        return (0.7, "magazine")
    if any(k in s for k in ("fastestlaps", "motorbikecatalog", "bikewale", "accelerationtimes")):
        return (0.5, "aggregator")
    return (0.4, "unknown")


def find_spec_for_benchmark(mfr: str, model: str, year: int):
    for spec in ALL_KNOWN_BIKES:
        if spec.manufacturer.lower() != mfr.lower():
            continue
        if not _wb_match(model, spec.model_name):
            continue
        if year < spec.year_from or year > (spec.year_to or spec.year_from + 3):
            continue
        return spec
    return None


def run_sweep(out_path: str | None):
    rows = []
    t0 = time.time()

    # References (always run, never quality-weighted)
    ref_targets = {"K5": 9.97, "R1": 10.30, "Hayabusa": 10.40}
    refs = {}
    for label, fn in [("K5", gsxr1000_k5), ("R1", yzfr1_4c8), ("Hayabusa", hayabusa_gen1)]:
        cfg = fn()
        r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
        refs[label] = {
            "sim": float(r.time_quarter) if r.finished_quarter else None,
            "target": ref_targets[label],
            "delta": (float(r.time_quarter) - ref_targets[label]) if r.finished_quarter else None,
        }

    matched_count = 0
    for mfr, model, byear, tgt_et, tgt_trap, src in BENCHMARKS:
        spec = find_spec_for_benchmark(mfr, model, byear)
        if spec is None:
            continue
        try:
            cfg = spec_to_bike_config(spec)
            r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
            if not r.finished_quarter:
                continue
            cluster = cluster_for(
                spec.manufacturer, spec.model_name,
                spec.displacement_cc, spec.peak_power_hp,
                getattr(spec, "stroke_type", 4) or 4,
                getattr(spec, "category", None),
            )
            qweight, qlabel = _source_quality(src)
            row = {
                "mfr": spec.manufacturer,
                "model": spec.model_name,
                "year": byear,
                "cluster": cluster,
                "category_tag": getattr(cfg, "category_tag", None),
                "sim_et": round(float(r.time_quarter), 4),
                "tgt_et": float(tgt_et),
                "delta": round(float(r.time_quarter) - tgt_et, 4),
                "weight": qweight,
                "qlabel": qlabel,
                "src": src,
            }
            rows.append(row)
            matched_count += 1
        except Exception as exc:
            rows.append({
                "mfr": spec.manufacturer,
                "model": spec.model_name,
                "year": byear,
                "error": f"{type(exc).__name__}: {exc}"[:200],
            })

    took = time.time() - t0
    summary = _summarize(rows, refs)
    out = {"took_s": took, "refs": refs, "rows": rows, "summary": summary}

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(out, f, indent=1)

    _print(summary, refs, took, matched_count)
    return out


def _summarize(rows, refs):
    by_cluster: dict[str, dict] = {}
    overall_signed = []
    overall_abs = []
    overall_w = []
    for r in rows:
        if r.get("error"):
            continue
        cl = r["cluster"]
        ent = by_cluster.setdefault(cl, {"n": 0, "signed": [], "abs": [], "w": []})
        ent["n"] += 1
        ent["signed"].append(r["delta"])
        ent["abs"].append(abs(r["delta"]))
        ent["w"].append(r["weight"])
        overall_signed.append(r["delta"])
        overall_abs.append(abs(r["delta"]))
        overall_w.append(r["weight"])

    def _w_stats(vals_signed, vals_abs, weights):
        if not vals_signed:
            return {}
        n = len(vals_signed)
        sum_w = sum(weights)
        if sum_w <= 0:
            return {}
        wmean_signed = sum(v * w for v, w in zip(vals_signed, weights)) / sum_w
        wmean_abs = sum(v * w for v, w in zip(vals_abs, weights)) / sum_w
        # Unweighted for comparison
        return {
            "n": n,
            "weighted_bias": wmean_signed,
            "weighted_mean_abs": wmean_abs,
            "raw_bias": sum(vals_signed) / n,
            "raw_mean_abs": sum(vals_abs) / n,
            "within_0.05": sum(1 for x in vals_abs if x <= 0.05),
            "within_0.10": sum(1 for x in vals_abs if x <= 0.10),
            "within_0.20": sum(1 for x in vals_abs if x <= 0.20),
        }

    return {
        "by_cluster": {
            cl: _w_stats(e["signed"], e["abs"], e["w"]) for cl, e in by_cluster.items()
        },
        "overall": _w_stats(overall_signed, overall_abs, overall_w),
    }


def _print(summary, refs, took, matched):
    print(f"\nbenchmark_sweep — matched {matched} bikes in {took:.1f}s")
    print("\n=== REFERENCES ===")
    for label, info in refs.items():
        if info["sim"] is None:
            print(f"  {label:10}  (DNF)")
            continue
        print(f"  {label:10} ET={info['sim']:.4f}  target={info['target']:.2f}  Δ={info['delta']:+.4f}")
    o = summary["overall"]
    if o:
        print("\n=== OVERALL ===")
        print(f"  N={o['n']}  weighted bias={o['weighted_bias']:+.3f}s  weighted |Δ|={o['weighted_mean_abs']:.3f}s")
        print(f"             raw bias={o['raw_bias']:+.3f}s   raw |Δ|={o['raw_mean_abs']:.3f}s")
        print(f"  within ±0.05s: {o['within_0.05']}/{o['n']}")
        print(f"  within ±0.10s: {o['within_0.10']}/{o['n']}")
        print(f"  within ±0.20s: {o['within_0.20']}/{o['n']}")
    print("\n=== BY CLUSTER (weighted) ===")
    for cl, st in sorted(summary["by_cluster"].items()):
        if not st:
            continue
        print(f"  {cl:24} N={st['n']:3d}  wb={st['weighted_bias']:+6.3f}s  w|Δ|={st['weighted_mean_abs']:6.3f}s  raw|Δ|={st['raw_mean_abs']:6.3f}s")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_sweep(out_path)
