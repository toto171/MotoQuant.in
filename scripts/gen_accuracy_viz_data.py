#!/usr/bin/env python3
"""gen_accuracy_viz_data.py -- per-bike real-vs-sim dataset for the website.

The weighted sweep (`phys_weighted_sweep.py report`) collapses every matched
benchmark into cluster aggregates, so the per-bike pairs a scatter plot needs
are thrown away. This script re-runs the SAME matching against the sweep's
chunk output and emits one row per matched (bike, benchmark) pair:

    { make, model, year, real_et, sim_et, delta, abs_delta, real_trap,
      sim_trap, cluster, source, weight, quality }

plus the cluster + overall aggregates (identical numbers to acc_final) and the
three reference baselines, so the frontend can render a real-vs-sim scatter,
a residual distribution, a per-cluster breakdown, and a best-predictions table
from ONE committed file.

Usage:
    # 1) run the weighted sweep so chunk_*.json exist (default /tmp/mq_sweep):
    MOTOQUANT_DB=motoquant.db python scripts/phys_weighted_sweep.py run /tmp/mq_sweep 800
    # 2) emit the viz dataset:
    MOTOQUANT_DB=motoquant.db python scripts/gen_accuracy_viz_data.py \
        --state-dir /tmp/mq_sweep --out web/app/validation/accuracy_data.json
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from motoquant import MotoQuantEngine  # noqa: E402
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402
from scripts.phys_weighted_sweep import _bench_map, source_weight  # noqa: E402
from scripts.sweep_lib import source_quality  # noqa: E402
from scripts.sweep_with_clusters import (  # noqa: E402
    _model_specificity_score,
    _wb_match,
    cluster_for,
)

# Human labels for the cluster keys the sweep emits (cluster_for() returns
# hyphenated keys).
CLUSTER_LABELS = {
    "litre-sport-195+": "Litre hyper-sport (195 hp+)",
    "litre-sport-600-1000": "600-1000 sport",
    "mid-twin-500-700": "Mid twins (500-700cc)",
    "mid-twin-300-500": "Mid twins (300-500cc)",
    "entry-200-300": "Entry (200-300cc)",
    "entry-150-200": "Entry (150-200cc)",
    "two-stroke": "Two-stroke",
    "cruiser-1300+": "Cruiser (1300cc+)",
    "other": "Other",
    "unknown": "Other",
}


def _match_benchmark(rec, bm):
    """Mirror phys_weighted_sweep.report()'s per-row best-benchmark pick."""
    m_lo = rec["manufacturer"].lower()
    mod_lo = rec["model"].lower()
    yf = rec.get("year_from") or 0
    yt = rec.get("year_to") or yf
    best = None
    best_score = -1
    best_in = False
    for (bmf, bmod), entries in bm.items():
        if not (_wb_match(bmf, m_lo) and _wb_match(bmod, mod_lo)):
            continue
        in_e = None
        for byear, te, tt, src in entries:
            if yf <= byear <= yt or (not yt and yf == byear):
                in_e = (te, tt, src)
                break
        fb = (entries[0][1], entries[0][2], entries[0][3])
        chosen = in_e if in_e is not None else fb
        e_in = in_e is not None
        sc = _model_specificity_score(bmod)
        if e_in and not best_in:
            best, best_score, best_in = chosen, sc, True
        elif e_in == best_in and sc > best_score:
            best, best_score = chosen, sc
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default="/tmp/mq_sweep")
    ap.add_argument("--out", default="web/app/validation/accuracy_data.json")
    ap.add_argument("--stamp", default="2026-07-04", help="dataset date label")
    args = ap.parse_args()

    sd = Path(args.state_dir)
    chunks = sorted(sd.glob("chunk_*.json"))
    if not chunks:
        print(f"ERROR: no chunk_*.json in {sd} -- run phys_weighted_sweep first")
        return 1
    rows = []
    for cf in chunks:
        rows.extend(json.loads(cf.read_text()))

    bm = _bench_map()
    bikes = []
    by_cluster: dict[str, list] = {}
    for rec in rows:
        if rec.get("error") or rec.get("sim_et") is None:
            continue
        best = _match_benchmark(rec, bm)
        if best is None:
            continue
        real_et, real_trap, src = best
        sim_et = round(float(rec["sim_et"]), 4)
        delta = round(sim_et - real_et, 4)
        w = source_weight(src)
        _, qual = source_quality(src)
        cl = cluster_for(
            rec["manufacturer"],
            rec["model"],
            rec["disp_cc"],
            rec["power_hp"],
            rec["stroke_type"],
            rec["category"],
        )
        bikes.append(
            {
                "make": rec["manufacturer"],
                "model": rec["model"],
                "year": rec.get("year_from"),
                "disp_cc": rec["disp_cc"],
                "real_et": round(float(real_et), 3),
                "sim_et": sim_et,
                "delta": delta,
                "abs_delta": round(abs(delta), 4),
                "real_trap": real_trap,
                "sim_trap": round(float(rec.get("sim_trap_kmh") or 0), 1),
                "cluster": cl,
                "cluster_label": CLUSTER_LABELS.get(cl, cl),
                "source": src,
                "weight": w,
                "quality": qual,
            }
        )
        by_cluster.setdefault(cl, []).append((delta, w))

    def wstats(items):
        if not items:
            return {}
        W = sum(w for _, w in items) or 1e-9
        return {
            "n": len(items),
            "w_mean_abs": round(sum(abs(d) * w for d, w in items) / W, 4),
            "w_bias": round(sum(d * w for d, w in items) / W, 4),
            "raw_mean_abs": round(st.mean([abs(d) for d, _ in items]), 4),
        }

    refs = {}
    for label, fn in [
        ("K5", gsxr1000_k5),
        ("R1", yzfr1_4c8),
        ("Hayabusa", hayabusa_gen1),
    ]:
        r = MotoQuantEngine(fn()).run(use_adaptive_dt=False, max_time=26.0)
        refs[label] = round(float(r.time_quarter), 4)

    allitems = [(b["delta"], b["weight"]) for b in bikes]

    def within(t):
        return sum(1 for b in bikes if b["abs_delta"] <= t)

    n = len(bikes)
    bikes.sort(key=lambda b: b["abs_delta"])
    out = {
        "generated": args.stamp,
        "references": refs,
        "n_matched": n,
        "overall": wstats(allitems),
        "distribution": {
            "within_0_05": within(0.05),
            "within_0_10": within(0.10),
            "within_0_20": within(0.20),
            "within_0_50": within(0.50),
            "within_1_00": within(1.00),
        },
        "clusters": {
            cl: {**wstats(items), "label": CLUSTER_LABELS.get(cl, cl)}
            for cl, items in sorted(by_cluster.items(), key=lambda kv: -len(kv[1]))
        },
        "bikes": bikes,
    }
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1))
    print(
        f"wrote {outp}: {n} matched bikes | overall |d|={out['overall']['w_mean_abs']}s "
        f"bias={out['overall']['w_bias']:+.4f}s | "
        f"within 0.10s={out['distribution']['within_0_10']} 0.20s={out['distribution']['within_0_20']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
