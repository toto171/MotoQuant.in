#!/usr/bin/env python3
"""phys_weighted_sweep.py — resumable, chunked, WEIGHTED benchmark sweep.

Runs the catalog sweep in disk-persisted chunks, binds each catalog bike to a
benchmark through ``scripts.sweep_lib.bind_benchmark_for_record`` (the ONE
binding implementation), and computes per-cluster + overall WEIGHTED
mean|Δ| / bias for ET and trap speed.

Simulations run on ``motoquant.engine_select.make_engine`` — the Rust core
when it is built and current (bit-identical to the Python reference, ~50x
faster), the Python reference otherwise.

Two rule sets are reported (2026-10 data epoch):

* ``epoch`` (the headline): epoch binding (highest-weight in-range entry;
  out-of-year only via ``SAME_PLATFORM_FALLBACKS``) + epoch source weights
  (``sweep_lib.source_weight``).
* ``legacy``: the pre-epoch binding (first in-range entry, else the group's
  first entry whatever its year) + the pre-epoch classifier
  (``sweep_lib.source_quality_legacy``). Reproduces the 2026-08-08 published
  headline on 2026-08-08 data, so a metric change can always be separated
  from a model change.

Source weights: instrumented 1.0 / magazine 0.7 / aggregator 0.5 /
forum 0.3 / DERIVED-or-estimate 0.1.

Usage:
  python scripts/phys_weighted_sweep.py run    STATE_DIR [CHUNK_SIZE]  # advance one chunk
  python scripts/phys_weighted_sweep.py report STATE_DIR OUT_JSON       # summarise (all chunks done)
"""

import json
import logging
import statistics
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from motoquant.engine_select import engine_class, make_engine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from scripts.sweep_lib import (
    bind_benchmark_for_record,
    build_bench_map,
    source_quality_legacy,
    source_weight,  # noqa: F401  (canonical classifier; re-exported)
)
from scripts.sweep_with_clusters import cluster_for
from scripts.validation_sweep import BENCHMARKS

# NOTE (roadmap A4-27): source_weight was previously defined locally here and
# diverged from scripts.sweep_lib.source_quality. The two are unified onto
# scripts.sweep_lib as the single source of truth; this module re-exports the
# canonical scalar weight (still callable as phys_weighted_sweep.source_weight).
# See tests/test_sweep_source_weight.py.
#
# 2026-10: the inline copy of the LEGACY binding that lived in report() is
# gone — binding now delegates to sweep_lib.bind_benchmark_for_record for
# BOTH rule sets, so there is exactly one binding implementation.

#: rule-set name -> (binding policy, scalar source-weight function)
RULES = {
    "epoch": ("epoch", source_weight),
    "legacy": ("legacy", lambda s: source_quality_legacy(s)[0]),
}
HEADLINE_RULES = "epoch"


def _bench_map():
    """BENCHMARKS grouped by (manufacturer, model) — the input shape of
    ``sweep_lib.bind_benchmark_for_record`` (also reused by
    scripts/gen_accuracy_viz_data.py)."""
    return build_bench_map(BENCHMARKS)


def bind(rec, bm, rules=HEADLINE_RULES):
    """Bind one swept record to a benchmark under ``rules``.

    Returns ``(tgt_et, tgt_trap, src, weight)`` or ``None``.
    """
    policy, wfn = RULES[rules]
    hit = bind_benchmark_for_record(
        rec["manufacturer"],
        rec["model"],
        rec.get("year_from"),
        rec.get("year_to"),
        bm,
        policy=policy,
        weight_fn=wfn,
    )
    if hit is None:
        return None
    te, tt, src = hit
    return (te, tt, src, wfn(src))


def run_chunk(state_dir, chunk_size):
    sd = Path(state_dir)
    sd.mkdir(parents=True, exist_ok=True)
    prog = sd / "progress.json"
    start = 0
    if prog.exists():
        start = json.loads(prog.read_text()).get("next", 0)
    end = min(start + chunk_size, len(ALL_KNOWN_BIKES))
    if start >= len(ALL_KNOWN_BIKES):
        print(f"DONE all {len(ALL_KNOWN_BIKES)} bikes already swept.")
        return 0
    rows = []
    t0 = time.time()
    for i in range(start, end):
        spec = ALL_KNOWN_BIKES[i]
        try:
            cfg = spec_to_bike_config(spec)
            r = make_engine(cfg).run(use_adaptive_dt=False, max_time=26.0)
            fin = bool(r.finished_quarter)
            t60 = getattr(r, "time_60ft", None)
            rows.append(
                {
                    "i": i,
                    "manufacturer": spec.manufacturer,
                    "model": spec.model_name,
                    "year_from": spec.year_from,
                    "year_to": spec.year_to,
                    "disp_cc": spec.displacement_cc,
                    "power_hp": spec.peak_power_hp,
                    "stroke_type": getattr(spec, "stroke_type", 4) or 4,
                    "category": getattr(spec, "category", None),
                    "cylinders": getattr(spec, "cylinders", None),
                    "finished": fin,
                    "sim_et": float(r.time_quarter) if fin else None,
                    "sim_trap_kmh": float(r.speed_quarter * 3.6) if fin else None,
                    "sim_t60": float(t60) if fin and t60 is not None else None,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "i": i,
                    "manufacturer": spec.manufacturer,
                    "model": spec.model_name,
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )
    # append to chunk file
    (sd / f"chunk_{start:04d}.json").write_text(json.dumps(rows))
    prog.write_text(json.dumps({"next": end, "total": len(ALL_KNOWN_BIKES)}))
    print(
        f"chunk {start}-{end} done in {time.time() - t0:.1f}s "
        f"[{engine_class().__name__}]; next={end}/{len(ALL_KNOWN_BIKES)}"
    )
    return 0


def wstats(items):
    """ET weighted stats over ``(delta_s, weight, ...)`` tuples."""
    if not items:
        return {}
    W = sum(w for _, w, *_ in items) or 1e-9
    return {
        "n": len(items),
        "w_sum": round(W, 2),
        "w_mean_abs": round(sum(abs(d) * w for d, w, *_ in items) / W, 4),
        "w_bias": round(sum(d * w for d, w, *_ in items) / W, 4),
        "raw_mean_abs": round(statistics.mean([abs(d) for d, *_ in items]), 4),
    }


def trap_wstats(items):
    """Trap weighted stats (km/h) over ``(delta_kmh, weight)`` tuples."""
    if not items:
        return {}
    W = sum(w for _, w in items) or 1e-9
    return {
        "n": len(items),
        "w_mean_abs_kmh": round(sum(abs(d) * w for d, w in items) / W, 2),
        "w_bias_kmh": round(sum(d * w for d, w in items) / W, 2),
        "raw_mean_abs_kmh": round(statistics.mean([abs(d) for d, _ in items]), 2),
    }


def score_rows(rows, rules=HEADLINE_RULES):
    """Bind + score swept rows under one rule set."""
    bm = _bench_map()
    by_cluster: dict = {}
    trap_by_cluster: dict = {}
    overall = []
    trap_overall = []
    for rec in rows:
        if rec.get("error") or rec.get("sim_et") is None:
            continue
        hit = bind(rec, bm, rules)
        if hit is None:
            continue
        te, tt, src, w = hit
        cl = cluster_for(
            rec["manufacturer"],
            rec["model"],
            rec["disp_cc"],
            rec["power_hp"],
            rec["stroke_type"],
            rec["category"],
            cylinders=rec.get("cylinders"),
        )
        d = rec["sim_et"] - te
        by_cluster.setdefault(cl, []).append((d, w, src))
        overall.append((d, w))
        if tt and rec.get("sim_trap_kmh") is not None:
            dt = rec["sim_trap_kmh"] - tt
            trap_by_cluster.setdefault(cl, []).append((dt, w))
            trap_overall.append((dt, w))
    return {
        "binding_policy": RULES[rules][0],
        "clusters": {cl: wstats(items) for cl, items in sorted(by_cluster.items())},
        "overall": wstats(overall),
        "trap_clusters": {
            cl: trap_wstats(items) for cl, items in sorted(trap_by_cluster.items())
        },
        "trap_overall": trap_wstats(trap_overall),
    }


def report(state_dir, out_json):
    sd = Path(state_dir)
    rows = []
    for cf in sorted(sd.glob("chunk_*.json")):
        rows.extend(json.loads(cf.read_text()))
    # reference baselines
    from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

    refs = {}
    for label, fn in [
        ("K5", gsxr1000_k5),
        ("R1", yzfr1_4c8),
        ("Hayabusa", hayabusa_gen1),
    ]:
        r = make_engine(fn()).run(use_adaptive_dt=False, max_time=26.0)
        refs[label] = round(float(r.time_quarter), 4)

    head = score_rows(rows, HEADLINE_RULES)
    out = {
        "references": refs,
        "engine": engine_class().__name__,
        "n_bikes_swept": len(rows),
        "rules": HEADLINE_RULES,
        "clusters": head["clusters"],
        "overall": head["overall"],
        "trap_clusters": head["trap_clusters"],
        "trap_overall": head["trap_overall"],
        "by_rules": {name: score_rows(rows, name) for name in RULES},
    }
    Path(out_json).write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {
                "references": refs,
                "engine": out["engine"],
                **{
                    name: {"overall": v["overall"], "trap": v["trap_overall"]}
                    for name, v in out["by_rules"].items()
                },
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        sys.exit(run_chunk(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120))
    elif cmd == "report":
        sys.exit(report(sys.argv[2], sys.argv[3]))
