#!/usr/bin/env python3
"""tune_cluster_knobs.py — per-cluster CategoryProfile knob tuner (July 6, 2026).

Replaces the 3-bike-baseline tuning regime: the objective is the FULL weighted
benchmark corpus (same matching + source weights as phys_weighted_sweep.py),
evaluated per cluster so a candidate knob-set re-sims only the bikes it can
affect. Profiles are runtime-looked-up, so no DB reseed is needed between
candidate evaluations.

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
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from motoquant import (
    MotoQuantEngine,  # noqa: E402
    category_profiles as cp,  # noqa: E402
)
from motoquant.scraper.importer import spec_to_bike_config  # noqa: E402
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from scripts.sweep_lib import source_weight  # noqa: E402
from scripts.sweep_with_clusters import (  # noqa: E402
    _model_specificity_score,
    _wb_match,
    cluster_for,
)
from scripts.validation_sweep import BENCHMARKS  # noqa: E402

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


def _bench_map():
    bm = {}
    for bmfr, bmodel, byear, tgt_et, tgt_trap, src in BENCHMARKS:
        bm.setdefault((bmfr.lower(), bmodel.lower()), []).append(
            (byear, tgt_et, tgt_trap, src)
        )
    return bm


def build_matches():
    """Benchmark-match every spec (knob-independent). Returns match rows."""
    bm = _bench_map()
    matches = []
    for i, spec in enumerate(ALL_KNOWN_BIKES):
        m_lo = spec.manufacturer.lower()
        mod_lo = spec.model_name.lower()
        yf = spec.year_from or 0
        yt = spec.year_to or yf
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
        if best is None:
            continue
        te, tt, src = best
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
                "weight": source_weight(src),
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
        r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
        return (i, float(r.time_quarter) if r.finished_quarter else None)
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
    return {
        "n": len(rows),
        "w_sum": round(W, 2),
        "w_mean_abs": round(wabs, 4),
        "w_bias": round(wbias, 4),
        "raw_mean_abs": round(raw, 4),
    }


def cmd_baseline(out_json):
    matches = build_matches()
    ets = sim_batch([m["i"] for m in matches])
    rows = []
    for m in matches:
        et = ets.get(m["i"])
        if et is None:
            continue
        rows.append(
            {**m, "sim_et": round(et, 4), "delta": round(et - m["target_et"], 4)}
        )
    by_cluster = {}
    for r in rows:
        by_cluster.setdefault(r["cluster"], []).append(r)
    out = {
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
            et = ets.get(m["i"])
            if et is None:
                continue
            rows.append({**m, "delta": et - m["target_et"]})
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
