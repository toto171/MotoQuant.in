#!/usr/bin/env python3
"""phys_weighted_sweep.py — resumable, chunked, WEIGHTED benchmark sweep.

Runs the 502-bike catalog sweep in disk-persisted chunks (sandbox 45s cap),
matches benchmarks via the same score-and-pick logic as sweep_with_clusters,
and computes per-cluster + overall WEIGHTED mean|Δ| / bias.

Source weights: instrumented 1.0 / magazine 0.7 / aggregator 0.5 /
forum 0.3 / DERIVED 0.1.

Usage:
  python scripts/phys_weighted_sweep.py run   STATE_DIR [CHUNK_SIZE]   # advance one chunk
  python scripts/phys_weighted_sweep.py report STATE_DIR OUT_JSON      # summarise (all chunks done)
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
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from scripts.sweep_with_clusters import _model_specificity_score, _wb_match, cluster_for
from scripts.validation_sweep import BENCHMARKS


def source_weight(src: str) -> float:
    s = (src or "").lower()
    if "derived" in s or "0-100" in s:
        return 0.1
    if any(k in s for k in ("forum", "timeslip", "hdforums")):
        return 0.3
    # instrumented signals
    if any(
        k in s
        for k in (
            "timing-strip",
            "instrumented",
            "dragy",
            "consumer news",
            "mcn",
            "don canet",
            "carlsbad",
        )
    ):
        return 1.0
    # aggregator
    if any(
        k in s
        for k in (
            "fastestlaps",
            "motorbikecatalog",
            "motorbike catalog",
            "accelerationtimes",
            "bikewale",
            "motostatz",
        )
    ):
        return 0.5
    # default magazine (cycle world / sport rider w/o explicit timing-strip)
    if any(k in s for k in ("cycle world", "sport rider", "motorcyclist", "magazine")):
        return 0.7
    return 0.5  # unknown -> aggregator-tier


def _bench_map():
    bm = {}
    for bmfr, bmodel, byear, tgt_et, tgt_trap, src in BENCHMARKS:
        bm.setdefault((bmfr.lower(), bmodel.lower()), []).append(
            (byear, tgt_et, tgt_trap, src)
        )
    return bm


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
            r = MotoQuantEngine(cfg).run(use_adaptive_dt=False, max_time=26.0)
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
                    "finished": bool(r.finished_quarter),
                    "sim_et": float(r.time_quarter) if r.finished_quarter else None,
                    "sim_trap_kmh": float(r.speed_quarter * 3.6)
                    if r.finished_quarter
                    else None,
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
        f"chunk {start}-{end} done in {time.time() - t0:.1f}s; next={end}/{len(ALL_KNOWN_BIKES)}"
    )
    return 0


def report(state_dir, out_json):
    sd = Path(state_dir)
    rows = []
    for cf in sorted(sd.glob("chunk_*.json")):
        rows.extend(json.loads(cf.read_text()))
    bm = _bench_map()
    by_cluster = {}
    overall = []
    # reference baselines
    from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

    refs = {}
    for label, fn in [
        ("K5", gsxr1000_k5),
        ("R1", yzfr1_4c8),
        ("Hayabusa", hayabusa_gen1),
    ]:
        r = MotoQuantEngine(fn()).run(use_adaptive_dt=False, max_time=26.0)
        refs[label] = round(float(r.time_quarter), 4)

    for rec in rows:
        if rec.get("error") or rec.get("sim_et") is None:
            continue
        cl = cluster_for(
            rec["manufacturer"],
            rec["model"],
            rec["disp_cc"],
            rec["power_hp"],
            rec["stroke_type"],
            rec["category"],
        )
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
                best = chosen
                best_score = sc
                best_in = True
            elif e_in == best_in and sc > best_score:
                best = chosen
                best_score = sc
        ent = by_cluster.setdefault(cl, [])
        if best is not None:
            te, tt, src = best
            d = rec["sim_et"] - te
            w = source_weight(src)
            ent.append((d, w, src))
            overall.append((d, w))

    def wstats(items):
        if not items:
            return {}
        W = sum(w for _, w, *_ in items) or 1e-9
        wabs = sum(abs(d) * w for d, w, *_ in items) / W
        wbias = sum(d * w for d, w, *_ in items) / W
        import statistics as st

        raw_abs = st.mean([abs(d) for d, *_ in items])
        return {
            "n": len(items),
            "w_sum": round(W, 2),
            "w_mean_abs": round(wabs, 4),
            "w_bias": round(wbias, 4),
            "raw_mean_abs": round(raw_abs, 4),
        }

    out = {
        "references": refs,
        "n_bikes_swept": len(rows),
        "clusters": {cl: wstats(items) for cl, items in sorted(by_cluster.items())},
        "overall": wstats([(d, w) for d, w in overall]),
    }
    Path(out_json).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        sys.exit(run_chunk(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120))
    elif cmd == "report":
        sys.exit(report(sys.argv[2], sys.argv[3]))
