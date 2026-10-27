#!/usr/bin/env python3
"""tune_cluster_knobs.py — per-cluster CategoryProfile knob tuner (July 6, 2026).

Replaces the 3-bike-baseline tuning regime: the objective is the FULL weighted
benchmark corpus (same matching + source weights as phys_weighted_sweep.py),
evaluated per cluster so a candidate knob-set re-sims only the bikes it can
affect. Profiles are runtime-looked-up, so no DB reseed is needed between
candidate evaluations.

Binding + weights delegate to scripts/sweep_lib (bind_benchmark_for_record,
the ONE binding implementation). ``MQ_RULES=epoch`` (default, the 2026-10
headline rules) or ``MQ_RULES=legacy`` (pre-epoch binding + classifier)
selects the rule set. Simulations use motoquant.engine_select.make_engine
(the Rust core when built and current — bit-identical, ~50x faster).

For the joint ET + trap retune with cross-validation see
scripts/tune_epoch_2026_10_24.py; this script stays the quick per-cluster
grid probe.

Usage:
  python scripts/tune_cluster_knobs.py baseline OUT_JSON
      Sim every benchmark-matched bike once with current profiles; write the
      per-bike residual table (bike, cluster, sim_et, target_et, delta, weight,
      source) plus per-cluster weighted stats.

  python scripts/tune_cluster_knobs.py grid CLUSTER GRID_JSON [OUT_JSON]
      GRID_JSON is a JSON list of knob-override dicts, e.g.
        [{"parasitic_mult": 1.1}, {"parasitic_mult": 1.2, "cd_floor": 0.30}]
      Each candidate is applied to _PROFILES[CLUSTER] and the cluster's matched
      bikes are re-simmed. Reports weighted mean|d| / bias per candidate.
"""

import json
import logging
import multiprocessing as mp
import os
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from motoquant import category_profiles as cp  # noqa: E402
from motoquant.engine_select import make_engine  # noqa: E402
from motoquant.scraper.importer import spec_to_bike_config  # noqa: E402
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from scripts.phys_weighted_sweep import RULES, _bench_map  # noqa: E402
from scripts.sweep_lib import bind_benchmark_for_record  # noqa: E402
from scripts.sweep_with_clusters import cluster_for  # noqa: E402

# Map sweep-cluster labels (dashes) -> category_tag (underscores)
CLUSTER_TO_TAG = {
    "litre-sport-195+": cp.CATEGORY_LITRE_SPORT_195P,
    "litre-sport-600-1000": cp.CATEGORY_LITRE_SPORT_600_1000,
    "mid-twin-500-700": cp.CATEGORY_MID_TWIN_500_700,
    "mid-twin-300-500": cp.CATEGORY_MID_TWIN_300_500,
    "entry-200-300": cp.CATEGORY_ENTRY_200_300,
    "entry-150-200": cp.CATEGORY_ENTRY_150_200,
    "two-stroke": cp.CATEGORY_TWO_STROKE,
    "cruiser-1300+": cp.CATEGORY_CRUISER_1300P,
    "other": cp.CATEGORY_OTHER,
    "sport-twin-600-1300": cp.CATEGORY_SPORT_TWIN_600_1300,
    "small-i4-screamer": cp.CATEGORY_SMALL_I4_SCREAMER,
    "single-300-500": cp.CATEGORY_SINGLE_300_500,
}


def _rules() -> str:
    rules = os.environ.get("MQ_RULES", "epoch").strip().lower() or "epoch"
    if rules not in RULES:
        raise SystemExit(f"MQ_RULES={rules!r}: expected one of {sorted(RULES)}")
    return rules


def build_matches(rules=None):
    """Benchmark-bind every spec (knob-independent). Returns match rows."""
    rules = rules or _rules()
    policy, wfn = RULES[rules]
    bm = _bench_map()
    matches = []
    for i, spec in enumerate(ALL_KNOWN_BIKES):
        hit = bind_benchmark_for_record(
            spec.manufacturer,
            spec.model_name,
            spec.year_from,
            spec.year_to,
            bm,
            policy=policy,
            weight_fn=wfn,
        )
        if hit is None:
            continue
        te, tt, src = hit
        cl = cluster_for(
            spec.manufacturer,
            spec.model_name,
            spec.displacement_cc,
            spec.peak_power_hp,
            getattr(spec, "stroke_type", 4) or 4,
            getattr(spec, "category", None),
            cylinders=getattr(spec, "cylinders", None),
        )
        matches.append(
            {
                "i": i,
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "cluster": cl,
                "target_et": te,
                "target_trap": tt,
                "weight": wfn(src),
                "source": src,
            }
        )
    return matches


def _apply_overrides(overrides_by_tag):
    for tag, kv in overrides_by_tag.items():
        prof = cp._PROFILES[tag]
        for k, v in kv.items():
            if not hasattr(prof, k):
                raise KeyError(f"unknown knob {k!r} on profile {tag}")
            setattr(prof, k, v)


def _sim_one(args):
    i, overrides_by_tag = args
    _apply_overrides(overrides_by_tag)
    spec = ALL_KNOWN_BIKES[i]
    try:
        cfg = spec_to_bike_config(spec)
        r = make_engine(cfg).run(use_adaptive_dt=False, max_time=26.0)
        if not r.finished_quarter:
            return (i, None)
        return (i, (float(r.time_quarter), float(r.speed_quarter * 3.6)))
    except Exception:
        return (i, None)


def sim_batch(indices, overrides_by_tag=None, procs=4):
    overrides_by_tag = overrides_by_tag or {}
    args = [(i, overrides_by_tag) for i in indices]
    with mp.Pool(procs) as pool:
        return dict(pool.map(_sim_one, args))


def wstats(rows):
    if not rows:
        return {}
    W = sum(r["weight"] for r in rows) or 1e-9
    wabs = sum(abs(r["delta"]) * r["weight"] for r in rows) / W
    wbias = sum(r["delta"] * r["weight"] for r in rows) / W
    raw = sum(abs(r["delta"]) for r in rows) / len(rows)
    out = {
        "n": len(rows),
        "w_sum": round(W, 2),
        "w_mean_abs": round(wabs, 4),
        "w_bias": round(wbias, 4),
        "raw_mean_abs": round(raw, 4),
    }
    tr = [r for r in rows if r.get("trap_delta") is not None]
    if tr:
        WT = sum(r["weight"] for r in tr) or 1e-9
        out["trap_w_mean_abs_kmh"] = round(
            sum(abs(r["trap_delta"]) * r["weight"] for r in tr) / WT, 2
        )
        out["trap_w_bias_kmh"] = round(
            sum(r["trap_delta"] * r["weight"] for r in tr) / WT, 2
        )
    return out


def _scored(m, res):
    et, trap = res
    return {
        **m,
        "sim_et": round(et, 4),
        "sim_trap": round(trap, 2),
        "delta": round(et - m["target_et"], 4),
        "trap_delta": round(trap - m["target_trap"], 2) if m["target_trap"] else None,
    }


def cmd_baseline(out_json):
    matches = build_matches()
    ets = sim_batch([m["i"] for m in matches])
    rows = []
    for m in matches:
        res = ets.get(m["i"])
        if res is None:
            continue
        rows.append(_scored(m, res))
    by_cluster = {}
    for r in rows:
        by_cluster.setdefault(r["cluster"], []).append(r)
    out = {
        "rules": _rules(),
        "overall": wstats(rows),
        "clusters": {cl: wstats(v) for cl, v in sorted(by_cluster.items())},
        "rows": sorted(rows, key=lambda r: -abs(r["delta"]) * r["weight"]),
    }
    Path(out_json).write_text(json.dumps(out, indent=1))
    print(
        json.dumps({"overall": out["overall"], "clusters": out["clusters"]}, indent=1)
    )


def cmd_grid(cluster, grid_json, out_json=None):
    tag = CLUSTER_TO_TAG[cluster]
    grid = json.loads(
        Path(grid_json).read_text() if Path(grid_json).exists() else grid_json
    )
    matches = [m for m in build_matches() if m["cluster"] == cluster]
    if not matches:
        print(f"no matched bikes in cluster {cluster}")
        return
    results = []
    for cand in grid:
        ets = sim_batch([m["i"] for m in matches], {tag: cand})
        rows = []
        for m in matches:
            res = ets.get(m["i"])
            if res is None:
                continue
            rows.append(_scored(m, res))
        st = wstats(rows)
        results.append({"overrides": cand, **st})
        print(json.dumps(results[-1]))
    if out_json:
        Path(out_json).write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "baseline":
        cmd_baseline(sys.argv[2])
    elif cmd == "grid":
        cmd_grid(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        print(__doc__)
        sys.exit(1)
