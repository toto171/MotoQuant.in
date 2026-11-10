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

Binding + source weights come from ``phys_weighted_sweep.bind`` (->
``sweep_lib.bind_benchmark_for_record``), under the headline rule set by
default (``--rules legacy`` reproduces a pre-epoch dataset). Each row is
scored under its benchmark's timing convention
(``sweep_lib.timing_convention``) when the sweep stored the matching run.

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

from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402
from motoquant.engine_select import make_engine  # noqa: E402
from scripts.phys_weighted_sweep import (  # noqa: E402
    HEADLINE_RULES,
    RULES,
    _bench_map,
    bind,
)
from scripts.sweep_lib import (  # noqa: E402
    bind_benchmark_for_record,
    sim_et_for_convention,
    source_quality,
    source_quality_legacy,
    timing_convention,
)
from scripts.sweep_with_clusters import cluster_for  # noqa: E402

# Human labels for the cluster keys the sweep emits (cluster_for() returns
# hyphenated keys).
CLUSTER_LABELS = {
    "litre-sport-195+": "Litre hyper-sport (195 hp+)",
    "litre-sport-600-1000": "600-1000 sport (I4/triple)",
    # Taxonomy v2 (July 6, 2026) — cylinder-aware clusters
    "sport-twin-600-1300": "Sport twins (600-1300cc)",
    "small-i4-screamer": "Small-cc I4 screamers",
    "single-300-500": "Singles (300-500cc)",
    "mid-twin-500-700": "Mid twins (500-700cc)",
    "mid-twin-300-500": "Mid twins (300-500cc)",
    "entry-200-300": "Entry (200-300cc)",
    "entry-150-200": "Entry (150-200cc)",
    "two-stroke": "Two-stroke",
    "cruiser-1300+": "Cruiser (1300cc+)",
    "other": "Other",
    "unknown": "Other",
}


def bind_record(rec, bm, rules=HEADLINE_RULES):
    """Bind one swept record under ``rules`` — the SAME binding + source
    weights the published sweep uses (``phys_weighted_sweep.bind`` ->
    ``sweep_lib.bind_benchmark_for_record``; one implementation, 2026-10
    epoch policy by default). Returns ``(real_et, real_trap, src, weight)``
    or ``None``.

    Before 2026-10 round 2 this script carried its own copy of the LEGACY
    binding (first in-range entry, else the group's first entry whatever its
    year) and then scored it with the EPOCH weights — a mixed rule set the
    sweep never used, so the /validation explorer could disagree with the
    headline it sits next to.
    """
    return bind(rec, bm, rules)


def quality_label(src, rules=HEADLINE_RULES):
    """The source-quality label matching ``rules``' weights."""
    if rules == "legacy":
        return source_quality_legacy(src)[1]
    return source_quality(src)[1]


def _match_benchmark(rec, bm, policy="legacy"):
    """Legacy-rule binding helper, kept as a thin delegate to
    ``sweep_lib.bind_benchmark_for_record`` (no logic of its own) for
    callers that compare against the pre-epoch rule
    (tests/test_epoch_tune_scripts.py). ``main()`` does not use it — it binds
    through :func:`bind_record`. Returns ``(real_et, real_trap, src)`` or
    ``None``."""
    return bind_benchmark_for_record(
        rec["manufacturer"],
        rec["model"],
        rec.get("year_from"),
        rec.get("year_to"),
        bm,
        policy=policy,
    )


def scored_sim_et(rec, src):
    """``(sim_et, fell_back)`` — the record's sim ET under the benchmark's
    timing convention (``sweep_lib.timing_convention``): a ``first_motion``
    row is scored on the record's ``sim_et_first_motion`` run when the sweep
    stored one. A sweep that only ran the default 1-ft rollout has no such
    run; the row then falls back to ``sim_et`` with ``fell_back=True`` and
    :func:`main` reports how many rows did (the output schema is unchanged)."""
    et = sim_et_for_convention(rec, src)
    if et is None:
        return rec["sim_et"], timing_convention(src) != "rollout_1ft"
    return et, False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default="/tmp/mq_sweep")
    ap.add_argument("--out", default="web/app/validation/accuracy_data.json")
    ap.add_argument("--stamp", default="2026-07-04", help="dataset date label")
    ap.add_argument(
        "--rules",
        default=HEADLINE_RULES,
        choices=sorted(RULES),
        help="binding + source-weight rule set (default: the headline rules)",
    )
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
    fell_back = 0
    for rec in rows:
        if rec.get("error") or rec.get("sim_et") is None:
            continue
        hit = bind_record(rec, bm, args.rules)
        if hit is None:
            continue
        real_et, real_trap, src, w = hit
        et, fb = scored_sim_et(rec, src)
        fell_back += fb
        sim_et = round(float(et), 4)
        delta = round(sim_et - real_et, 4)
        qual = quality_label(src, args.rules)
        cl = cluster_for(
            rec["manufacturer"],
            rec["model"],
            rec["disp_cc"],
            rec["power_hp"],
            rec["stroke_type"],
            rec["category"],
            cylinders=rec.get("cylinders"),
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
        r = make_engine(fn()).run(use_adaptive_dt=False, max_time=26.0)
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
    if fell_back:
        print(
            f"WARNING: {fell_back} first-motion benchmark rows were scored on the "
            "default 1-ft-rollout sim (the sweep stored no sim_et_first_motion)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
