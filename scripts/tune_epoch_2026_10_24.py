#!/usr/bin/env python3
"""tune_epoch_2026_10_24.py — 2026-10 physics-epoch joint ET + trap retune.

The 2026-10 epoch (ADR-0002) changed the physics (no double-counted slip
inertia, soft-cut limiter, continuous slip ratio, 1-ft rollout timing,
energy-consistent launch floor, 4T crank recal 1.00 + rated-power cap, shaft
efficiency 0.93) and the catalog data (no sport Cd x0.55, real drive types,
corrected specs, epoch benchmark binding + weights). This script re-centres
the per-cluster CategoryProfile knobs against a JOINT objective, fits the
frozen reference profile separately, and measures the result honestly.

All simulation goes through ``motoquant.engine_select.make_engine`` (the Rust
core when available — bit-identical to the Python reference, ~50x faster).

Subcommands
-----------
measure --out JSON [--root PATH] [--policy epoch|legacy|both] [--thetas JSON]
        [--no-topspeed]
    Weighted ET + trap sweep (binding + weights from THIS checkout's
    scripts/sweep_lib.py, under the epoch and/or legacy rules), the top-speed
    sweep (scripts/topspeed_sweep.py matching) and the three references.
    ``--root`` measures another checkout's physics + catalog + benchmark
    corpus (e.g. a ``git worktree`` of HEAD, or a hybrid tree) — the binding
    RULES always come from this checkout, so rule and model changes can be
    separated. ``--thetas`` applies knob overrides ({tag: {knob: value}}, or a
    ``tune`` output) before measuring, so a candidate retune can be scored
    without editing motoquant/category_profiles.py.

tune --out JSON [--lam 0.01] [--folds 5] [--policy epoch]
    Per-cluster joint retune with grouped k-fold cross-validation and a
    one-standard-error preference for the simplest (most neutral) knob set;
    thin clusters inherit a documented donor or stay neutral (see
    ``THIN_DONORS``).

refs --out JSON
    Fit the frozen ``reference_litre_195p`` profile to the references'
    published figures (separate from the catalog fit).

report --out JSON --inputs NAME=PATH ...
    Assemble reports/acc_epoch_2026_10_24.json from the measure/tune/refs
    outputs (see ``cmd_report``).

Objective (per cluster)::

    J = w|d|_ET  +  lam * w|d|_trap        (s; trap in km/h, lam in s per km/h)

with the corpus source weights (instrumented 1.0 / magazine 0.7 / aggregator
0.5 / forum 0.3 / derived-estimate 0.1). ``lam = 0.01`` s per km/h, i.e. a
1 km/h trap error costs as much as a 0.01 s ET error. Justification: what the
two terms can be trusted to resolve. Published ET figures from different
outlets for the same bike typically agree to ~0.1-0.2 s, published traps to
~5-10 km/h (66-ft speed-trap average vs instantaneous finish speed, GPS vs
light beams, mph/km/h transcription) — a noise ratio of ~0.02 s per km/h; the
corpus residual scales (ET ~0.26 s vs trap ~15 km/h at HEAD) give ~0.017.
Weighting trap at ~half its noise-equivalent lets it break ties in the
directions ET cannot see (top end vs launch) without overriding the ET
headline. The launch knobs tuned here barely move trap, so the selection is
insensitive to lam over 0-0.03 (``tune --lam`` sensitivity runs are recorded
in the report).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import math
import multiprocessing as mp
import os
import random
import statistics
import sys
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

#: Knobs this script reads/writes on a CategoryProfile.
KNOBS = (
    "over_clutch_factor",
    "max_engine_decel_rads2",
    "launch_floor_factor",
    "mu_peak_override",
    "mu_peak_scale",
    "parasitic_mult",
    "launch_rpm_factor",
    "cd_floor",
)

#: Physically neutral value of every knob: rated rubber, modelled
#: parasitics, no over-clutching, no launch floor, launch at the
#: StagingModel default (peak-torque rpm; the importer's pipe rpm for 2T).
NEUTRAL = {
    "over_clutch_factor": 0.0,
    "max_engine_decel_rads2": 0.0,
    "launch_floor_factor": 0.0,
    "mu_peak_override": None,
    "mu_peak_scale": 1.0,
    "parasitic_mult": 1.0,
    "launch_rpm_factor": None,
    "cd_floor": 0.25,
}

# category_tag -> report cluster label (dashes); mirrors
# scripts/sweep_with_clusters.TAG_TO_CLUSTER (pinned equal by
# tests/test_epoch_tune_scripts.py). Kept local because --root must import
# motoquant from the measured tree, not from this checkout.
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

MAX_TIME_S = 26.0
DNF_ET_S = 30.0  # scored ET for a DNF while tuning (a large, finite penalty)

# ── Binding rules: always THIS checkout's sweep_lib (by file path) ──────────


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RULES = _load_module("_epoch_rules_sweep_lib", HERE / "sweep_lib.py")


def weight_fn(policy: str):
    """Scalar source-weight function of a rule set."""
    if policy == "legacy":
        return lambda s: RULES.source_quality_legacy(s)[0]
    return RULES.source_weight


# ── Model under test (this checkout, or --root) ─────────────────────────────

CTX: dict = {}


def setup_root(root: Path | None) -> None:
    """Import the physics + catalog + benchmark corpus of ``root``."""
    root = Path(root or REPO).resolve()
    for p in (str(root / "scripts"), str(root)):
        if p in sys.path:
            sys.path.remove(p)
        sys.path.insert(0, p)
    from motoquant import category_profiles as cp
    from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
    from motoquant.scraper.importer import spec_to_bike_config
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    try:
        from motoquant.engine_select import engine_class, make_engine
    except ImportError:  # pre-Rust checkouts
        from motoquant import MotoQuantEngine as _E

        def make_engine(cfg, dt=0.001):
            return _E(cfg, dt=dt)

        def engine_class():
            return _E

    vs = _load_module(
        "_epoch_root_validation_sweep", root / "scripts/validation_sweep.py"
    )
    ts = _load_module("_epoch_root_topspeed_sweep", root / "scripts/topspeed_sweep.py")
    CTX.update(
        root=root,
        cp=cp,
        specs=ALL_KNOWN_BIKES,
        spec_to_bike_config=spec_to_bike_config,
        make_engine=make_engine,
        engine_name=engine_class().__name__,
        benchmarks=list(vs.BENCHMARKS),
        ts_benchmarks=list(ts.BENCHMARKS),
        refs={"K5": gsxr1000_k5, "R1": yzfr1_4c8, "Hayabusa": hayabusa_gen1},
        cfgs={},
    )
    CTX["base_knobs"] = {
        tag: {k: getattr(p, k) for k in KNOBS if hasattr(p, k)}
        for tag, p in cp._PROFILES.items()
    }


def cfg_for(i: int):
    """Cached BikeConfig of catalog spec ``i`` (None if the importer raises).

    Safe to cache: profile knobs are looked up when an engine is constructed
    (never baked into the config) and engines do not mutate their config
    (verified on 77 catalog configs: pickled bytes identical after run() +
    run_top_speed())."""
    cfgs = CTX["cfgs"]
    if i not in cfgs:
        try:
            cfgs[i] = CTX["spec_to_bike_config"](CTX["specs"][i])
        except Exception:
            cfgs[i] = None
    return cfgs[i]


def set_knobs(tag: str, knobs: dict | None) -> None:
    """Reset ``tag``'s profile to its checked-in values, then apply ``knobs``."""
    prof = CTX["cp"]._PROFILES[tag]
    for k, v in CTX["base_knobs"][tag].items():
        setattr(prof, k, v)
    for k, v in (knobs or {}).items():
        if not hasattr(prof, k):
            raise KeyError(f"unknown knob {k!r} on profile {tag}")
        setattr(prof, k, v)


def load_thetas(path: str | None) -> dict:
    """{tag: {knob: value}} from a plain mapping or a ``tune`` output."""
    if not path:
        return {}
    d = json.loads(Path(path).read_text())
    if "clusters" in d and isinstance(d["clusters"], dict):
        return {tag: c["theta"] for tag, c in d["clusters"].items()}
    if "thetas" in d:
        return d["thetas"]
    return d


def sim_quarter(cfg) -> tuple:
    """(et_s | None, trap_kmh | None, t60_s | None) on the selected engine."""
    try:
        r = CTX["make_engine"](cfg).run(use_adaptive_dt=False, max_time=MAX_TIME_S)
    except Exception:
        return (None, None, None)
    if not r.finished_quarter:
        return (None, None, None)
    t60 = getattr(r, "time_60ft", None)
    return (
        float(r.time_quarter),
        float(r.speed_quarter * 3.6),
        float(t60) if t60 is not None else None,
    )


def _sim_index(i: int):
    cfg = cfg_for(i)
    return (i, sim_quarter(cfg) if cfg is not None else (None, None, None))


def _sim_topspeed(i: int):
    cfg = cfg_for(i)
    if cfg is None:
        return (i, None)
    try:
        ts = CTX["make_engine"](cfg).run_top_speed(max_time=90.0)
        return (i, (float(ts.terminal_velocity_kmh), bool(ts.reached_plateau)))
    except Exception:
        return (i, None)


def pool_map(fn, items, procs: int):
    items = list(items)
    if procs <= 1 or len(items) < 8:
        return [fn(x) for x in items]
    ctx = mp.get_context("fork")
    with ctx.Pool(procs) as pool:
        return pool.map(fn, items, chunksize=max(1, len(items) // (procs * 8)))


# ── Benchmark binding ───────────────────────────────────────────────────────


def bind_rows(policy: str) -> list[dict]:
    """One row per catalog bike bound to an ET benchmark under ``policy``
    (``sweep_lib.bind_benchmark_for_record`` — the ONE binding
    implementation; the rule set's own source weights)."""
    cp = CTX["cp"]
    wfn = weight_fn(policy)
    bench_map = RULES.build_bench_map(CTX["benchmarks"])
    rows = []
    for i, spec in enumerate(CTX["specs"]):
        hit = RULES.bind_benchmark_for_record(
            spec.manufacturer,
            spec.model_name,
            spec.year_from,
            spec.year_to,
            bench_map,
            policy=policy,
            with_meta=True,
            weight_fn=wfn,
        )
        if hit is None:
            continue
        te, tt, src, byear, in_range = hit
        tag = cp.derive_category_tag(
            manufacturer=spec.manufacturer,
            model_name=spec.model_name,
            displacement_cc=spec.displacement_cc,
            peak_power_hp=spec.peak_power_hp,
            stroke_type=getattr(spec, "stroke_type", 4) or 4,
            category=getattr(spec, "category", None),
            cylinders=getattr(spec, "cylinders", None),
        )
        rows.append(
            {
                "i": i,
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "tag": tag,
                "cluster": TAG_TO_CLUSTER.get(tag, "other"),
                "target_et": float(te),
                "target_trap": float(tt) if tt else None,
                "weight": float(wfn(src)),
                "source": src,
                "bench_key": f"{spec.manufacturer.lower()}|{byear}|{te}|{tt}|{src}",
                "bench_year": byear,
                "in_range": bool(in_range),
            }
        )
    return rows


def bind_topspeed() -> list[dict]:
    """scripts/topspeed_sweep.py::_match over the catalog (year = year_from)."""
    specs = CTX["specs"]
    wb = RULES.wb_match
    out = []
    for mfr, mdl, yr, target, src in CTX["ts_benchmarks"]:
        cands = [
            (i, s)
            for i, s in enumerate(specs)
            if mfr.lower() in s.manufacturer.lower() and wb(mdl, s.model_name)
        ]
        if not cands:
            continue
        cands.sort(key=lambda c: abs((c[1].year_from or 0) - yr))
        i, s = cands[0]
        out.append(
            {
                "benchmark": f"{mfr} {mdl} ({yr})",
                "target_kmh": float(target),
                "source": src,
                "i": i,
                "bike_match": f"{s.manufacturer} {s.model_name}",
            }
        )
    return out


# ── Statistics ──────────────────────────────────────────────────────────────


def wstats(rows: list[dict]) -> dict:
    """ET weighted stats (keys match reports/acc_final_2026_08_08.json)."""
    rows = [r for r in rows if r.get("sim_et") is not None]
    if not rows:
        return {"n": 0}
    W = sum(r["weight"] for r in rows) or 1e-9
    d = [r["sim_et"] - r["target_et"] for r in rows]
    return {
        "n": len(rows),
        "w_sum": round(W, 2),
        "w_mean_abs": round(sum(abs(x) * r["weight"] for x, r in zip(d, rows)) / W, 4),
        "w_bias": round(sum(x * r["weight"] for x, r in zip(d, rows)) / W, 4),
        "raw_mean_abs": round(statistics.mean(abs(x) for x in d), 4),
    }


def trap_stats(rows: list[dict]) -> dict:
    """Trap weighted stats (km/h) over rows that carry a trap target."""
    rows = [r for r in rows if r.get("sim_trap") is not None and r.get("target_trap")]
    if not rows:
        return {"n": 0}
    W = sum(r["weight"] for r in rows) or 1e-9
    d = [r["sim_trap"] - r["target_trap"] for r in rows]
    return {
        "n": len(rows),
        "w_mean_abs_kmh": round(
            sum(abs(x) * r["weight"] for x, r in zip(d, rows)) / W, 2
        ),
        "w_bias_kmh": round(sum(x * r["weight"] for x, r in zip(d, rows)) / W, 2),
        "raw_mean_abs_kmh": round(statistics.mean(abs(x) for x in d), 2),
        "w_bias_pct": round(
            100 * sum(x / r["target_trap"] * r["weight"] for x, r in zip(d, rows)) / W,
            2,
        ),
    }


def within_bands(rows: list[dict]) -> dict:
    d = [abs(r["sim_et"] - r["target_et"]) for r in rows if r.get("sim_et") is not None]
    return {
        f"within_{b:.2f}s": sum(1 for x in d if x <= b)
        for b in (0.05, 0.10, 0.20, 0.50, 1.00)
    }


def t60_stats(rows: list[dict]) -> dict:
    t = [r["sim_t60"] for r in rows if r.get("sim_t60")]
    if not t:
        return {}
    return {"mean_s": round(statistics.mean(t), 3), "min_s": round(min(t), 3)}


def ts_summary(scored: list[dict]) -> dict:
    sc = [s for s in scored if s.get("sim_kmh") is not None]
    if not sc:
        return {"benchmarks_matched": 0}
    ad = sorted(abs(s["delta_kmh"]) for s in sc)
    return {
        "benchmarks_matched": len(sc),
        "mean_abs_delta_kmh": round(statistics.mean(ad), 1),
        "median_abs_delta_kmh": round(ad[len(ad) // 2], 1),
        "bias_kmh": round(statistics.mean(s["delta_kmh"] for s in sc), 1),
        "within_10_kmh": sum(1 for x in ad if x <= 10),
        "within_20_kmh": sum(1 for x in ad if x <= 20),
        "within_30_kmh": sum(1 for x in ad if x <= 30),
        "plateau_count": sum(1 for s in sc if s.get("reached_plateau")),
    }


def run_refs() -> dict:
    out = {}
    for label, fn in CTX["refs"].items():
        et, trap, t60 = sim_quarter(fn())
        out[label] = {
            "et_s": round(et, 4) if et is not None else None,
            "et_s_full": et,
            "trap_kmh": round(trap, 2) if trap is not None else None,
            "t60_s": round(t60, 4) if t60 is not None else None,
        }
    return out


def summarise(rows: list[dict]) -> dict:
    by: dict = {}
    for r in rows:
        by.setdefault(r["cluster"], []).append(r)
    return {
        "overall": wstats(rows),
        "trap_overall": trap_stats(rows),
        "t60": t60_stats(rows),
        "bands": within_bands(rows),
        "clusters": {
            cl: {**wstats(v), "trap": trap_stats(v), "t60": t60_stats(v)}
            for cl, v in sorted(by.items())
        },
        "by_weight": {
            str(w): wstats([r for r in rows if r["weight"] == w])
            for w in sorted({r["weight"] for r in rows}, reverse=True)
        },
    }


def measure(policies, procs: int, topspeed: bool = True, thetas=None) -> dict:
    for tag, th in (thetas or {}).items():
        set_knobs(tag, th)
    out = {
        "root": str(CTX["root"]),
        "motoquant_path": str(Path(sys.modules["motoquant"].__file__).parent),
        "engine": CTX["engine_name"],
        "n_bikes_catalog": len(CTX["specs"]),
        "thetas_applied": thetas or {},
        "references": run_refs(),
    }
    bound = {p: bind_rows(p) for p in policies}
    need = sorted({r["i"] for rows in bound.values() for r in rows})
    t0 = time.time()
    sims = dict(pool_map(_sim_index, need, procs))
    out["quarter_wall_s"] = round(time.time() - t0, 1)
    for p, rows in bound.items():
        for r in rows:
            et, trap, t60 = sims[r["i"]]
            r["sim_et"] = round(et, 4) if et is not None else None
            r["sim_trap"] = round(trap, 2) if trap is not None else None
            r["sim_t60"] = round(t60, 4) if t60 is not None else None
            r["delta"] = round(et - r["target_et"], 4) if et is not None else None
        out[p] = {**summarise(rows), "rows": rows}
    if topspeed:
        ts_rows = bind_topspeed()
        t0 = time.time()
        tsr = dict(pool_map(_sim_topspeed, sorted({r["i"] for r in ts_rows}), procs))
        out["topspeed_wall_s"] = round(time.time() - t0, 1)
        for r in ts_rows:
            res = tsr.get(r["i"])
            if res is None:
                r["sim_kmh"] = None
                continue
            r["sim_kmh"] = round(res[0], 1)
            r["reached_plateau"] = res[1]
            r["delta_kmh"] = round(res[0] - r["target_kmh"], 1)
        out["topspeed"] = {"summary": ts_summary(ts_rows), "scored": ts_rows}
    return out


def cmd_measure(args) -> None:
    setup_root(args.root)
    policies = ["epoch", "legacy"] if args.policy == "both" else [args.policy]
    res = measure(
        policies,
        args.procs,
        topspeed=not args.no_topspeed,
        thetas=load_thetas(args.thetas),
    )
    Path(args.out).write_text(json.dumps(res, indent=1))
    brief = {
        "engine": res["engine"],
        "references": {k: v["et_s"] for k, v in res["references"].items()},
    }
    for p in policies:
        brief[p] = {"overall": res[p]["overall"], "trap": res[p]["trap_overall"]}
    if "topspeed" in res:
        brief["topspeed"] = res["topspeed"]["summary"]
    print(json.dumps(brief, indent=1))


# ── Tuning ──────────────────────────────────────────────────────────────────
#
# Search bounds are PHYSICAL, not just numerical:
#   mu_peak_scale 0.80-1.20 — effective launch grip within +/-20 % of the
#       importer's rated rubber. < 1 encodes a launch that does not reach
#       the tyre's peak (wheelie/clutch modulation by a test rider; the sim's
#       wheelie limit does not bind — CLAUDE.md 2026-07-03 finding); > 1 a
#       prepped surface or rubber better than the importer's class default.
#   mu_peak_override 1.00-1.40 — a cluster-wide rubber class (discards the
#       per-bike rated rubber, so it counts double in ``complexity``).
#   launch_rpm_factor — None (StagingModel default: peak-torque rpm; the
#       importer's pipe rpm for 2T) or a fraction of redline: 4T 0.45-0.80
#       (real clutch-dump rpm; the importer's own EngineParams.launch_rpm is
#       0.55 x redline for >=400 cc but is dead because two_step=False), 2T
#       0.85-0.95 (on the pipe).
#   launch_floor_factor 0 / 0.85 / 1.0 x peak-torque (2T: tuned) rpm.
#   (over_clutch_factor, max_engine_decel_rads2) searched JOINTLY — the
#       extra back-torque is min(headroom * oc, decel * I_e), so either at
#       zero makes the other inert. Since the epoch's energy-consistent floor
#       they only act when launch rpm sits above the floor.
#   parasitic_mult 0.7-1.3 — +/-30 % on the modelled parasitic power.

MU_GRID = [round(0.80 + 0.02 * k, 2) for k in range(21)]
GRIDS_4T = {
    "mu_peak_scale": MU_GRID,
    "mu_peak_override": [round(1.00 + 0.02 * k, 2) for k in range(21)],
    "launch_rpm_factor": [None, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80],
    "launch_floor_factor": [0.0, 0.85, 1.0],
    "over_clutch": [(0.0, 0.0)]
    + [(oc, de) for oc in (0.2, 0.4, 0.6) for de in (100.0, 400.0, 1600.0)],
    "parasitic_mult": [round(0.7 + 0.1 * k, 1) for k in range(7)],
}
GRIDS_2T = {**GRIDS_4T, "launch_rpm_factor": [None, 0.85, 0.90, 0.95]}
MU_REFINE_STEP = 0.01

LAUNCH = ("launch_rpm_factor", "launch_floor_factor", "over_clutch")

#: family -> (fitted knobs, warm-start family). All fits start from NEUTRAL.
FAMILIES = {
    "neutral": ((), None),
    "grip": (("mu_peak_scale",), None),
    "rubber": (("mu_peak_override",), None),
    "launch": (("launch_rpm_factor",), None),
    "grip+lr": (("mu_peak_scale", "launch_rpm_factor"), "grip"),
    "grip+launch": (("mu_peak_scale", *LAUNCH), "grip+lr"),
    "full": (("mu_peak_scale", *LAUNCH, "parasitic_mult"), "grip+launch"),
}
FAMILY_ORDER = tuple(FAMILIES)
#: Report-only family: the checked-in (pre-epoch-tuned) knobs. Never
#: selectable — selecting it would mean not retuning at all.
REPORT_ONLY = ("current",)

MIN_FIT_ROWS = 8  # thinner clusters are not fitted (see THIN_DONORS)
MIN_FIT_GROUPS = 6  # ... nor clusters with fewer distinct benchmark rows
EPS_S = 0.001  # objective improvements below this are noise -> prefer neutral

#: Thin clusters (n < MIN_FIT_ROWS rows or < MIN_FIT_GROUPS benchmark rows):
#: tag -> donor tag whose SELECTED knobs they share, or None = neutral.
#: cruiser_1300p <- other: heavy, torque-rich road bikes (VMAX / Rocket 3 /
#:     muscle cruisers vs the big standards and tourers in "other") launch
#:     the same way; the 2026-06-11 calibration kept the two identical for
#:     that reason (category_profiles.py cruiser note).
#: small_i4_screamer -> neutral: n=2 (ZX-25R / ZX-4RR, the latter a 0.1-
#:     weight prose estimate); every knob is inert on its power-limited
#:     launch (ET bias moves < 0.11 s across mu 0.80-1.05 and launch rpm
#:     0.6-0.9) — there is nothing to share and nothing to fit.
THIN_DONORS = {"cruiser_1300p": "other", "small_i4_screamer": None}


def grids_for(tag: str) -> dict:
    return GRIDS_2T if tag == "two_stroke" else GRIDS_4T


def _get(theta: dict, k: str):
    if k == "over_clutch":
        return (theta["over_clutch_factor"], theta["max_engine_decel_rads2"])
    return theta[k]


def _with(theta: dict, k: str, v) -> dict:
    t = dict(theta)
    if k == "over_clutch":
        t["over_clutch_factor"], t["max_engine_decel_rads2"] = float(v[0]), float(v[1])
    else:
        t[k] = v
    return t


def _ndist(k: str, v) -> float:
    """Distance of a knob value from physical neutrality (tie-break key)."""
    if k == "over_clutch":
        return v[0] + v[1] / 4000.0
    n = NEUTRAL[k]
    if v is None:
        return 0.0 if n is None else 1.0
    if n is None:
        # launch_rpm_factor: closest to the importer's documented 0.55;
        # mu_peak_override: closest to the 1.40 sport class default.
        return 1.0 + abs(v - (0.55 if k == "launch_rpm_factor" else 1.40))
    return abs(v - n)


def complexity(theta: dict) -> float:
    """Number of non-neutral (live-meaning) knobs in ``theta``; a cluster-wide
    mu override counts double (it discards per-bike rated rubber)."""
    c = 0.0
    c += theta["mu_peak_scale"] != 1.0
    c += 2 * (theta["mu_peak_override"] is not None)
    c += bool(theta["over_clutch_factor"] and theta["max_engine_decel_rads2"])
    c += bool(theta["launch_floor_factor"])
    c += theta["launch_rpm_factor"] is not None
    c += theta["parasitic_mult"] != 1.0
    return c


def neutral_theta(tag: str) -> dict:
    t = dict(NEUTRAL)
    t["cd_floor"] = CTX["base_knobs"][tag]["cd_floor"]
    return t


def current_theta(tag: str) -> dict:
    return dict(CTX["base_knobs"][tag])


def objective_parts(rows, res, lam: float) -> dict:
    W = A = B = WT = AT = BT = 0.0
    for r, (et, trap, _t60) in zip(rows, res):
        w = r["weight"]
        e = et if et is not None else DNF_ET_S
        W += w
        A += w * abs(e - r["target_et"])
        B += w * (e - r["target_et"])
        if r["target_trap"] and trap is not None:
            WT += w
            AT += w * abs(trap - r["target_trap"])
            BT += w * (trap - r["target_trap"])
    et_abs = A / W if W else 0.0
    tr_abs = AT / WT if WT else 0.0
    return {
        "J": et_abs + lam * tr_abs,
        "et_w_mean_abs": et_abs,
        "et_w_bias": B / W if W else 0.0,
        "trap_w_mean_abs": tr_abs,
        "trap_w_bias": BT / WT if WT else 0.0,
        "w_sum": W,
    }


class ClusterEval:
    """Memoised per-cluster evaluator: a knob set is simulated once on ALL of
    the cluster's bikes, so every CV fold reuses it."""

    def __init__(self, tag: str, rows: list[dict], lam: float):
        self.tag, self.rows, self.lam = tag, rows, lam
        self.cache: dict = {}
        self.n_evals = 0

    def res(self, theta: dict) -> list:
        key = tuple(
            (k, round(theta[k], 6) if isinstance(theta[k], float) else theta[k])
            for k in KNOBS
        )
        hit = self.cache.get(key)
        if hit is None:
            set_knobs(self.tag, theta)
            try:
                hit = [sim_quarter(cfg_for(r["i"])) for r in self.rows]
            finally:
                set_knobs(self.tag, None)
            self.cache[key] = hit
            self.n_evals += 1
        return hit

    def parts(self, theta: dict, idx) -> dict:
        res = self.res(theta)
        return objective_parts(
            [self.rows[j] for j in idx], [res[j] for j in idx], self.lam
        )

    def J(self, theta: dict, idx) -> float:
        return self.parts(theta, idx)["J"]


def refine_mu(ev: ClusterEval, cur: dict, k: str, idx, eps: float) -> dict:
    """Pattern search on a grip knob at MU_REFINE_STEP; a move that does not
    beat the incumbent by eps/4 goes toward neutrality or not at all."""
    if cur[k] is None:
        return cur
    centre = 1.0 if k == "mu_peak_scale" else 1.40
    lo, hi = (0.80, 1.20) if k == "mu_peak_scale" else (1.00, 1.40)
    step = MU_REFINE_STEP
    for _ in range(40):
        c = cur[k]
        cands = [c] + [
            round(v, 4) for v in (c - step, c + step) if lo - 1e-9 <= v <= hi + 1e-9
        ]
        scored = [(ev.J(_with(cur, k, v), idx), v) for v in cands]
        jb = min(s for s, _ in scored)
        ok = [v for s, v in scored if s <= jb + eps / 4]
        v = min(ok, key=lambda v: (abs(v - centre), v))
        if v == c:
            break
        cur = _with(cur, k, v)
    return cur


def cd_fit(ev, start: dict, fit, idx, grids: dict, eps: float = EPS_S, passes=4):
    """Coordinate descent over the coarse grids; within ``eps`` of the best
    value the most-neutral one wins (honesty over fit). Grip knobs are then
    pattern-refined."""
    cur = dict(start)
    for _ in range(passes):
        changed = False
        for k in fit:
            vals = list(grids[k])
            if _get(cur, k) not in vals:
                vals.append(_get(cur, k))
            scored = [(ev.J(_with(cur, k, v), idx), v) for v in vals]
            jb = min(s for s, _ in scored)
            ok = [v for s, v in scored if s <= jb + eps]
            v = min(ok, key=lambda v: _ndist(k, v))
            if v != _get(cur, k):
                cur = _with(cur, k, v)
                changed = True
        if not changed:
            break
    for k in ("mu_peak_scale", "mu_peak_override"):
        if k in fit:
            cur = refine_mu(ev, cur, k, idx, eps)
    return cur


def make_folds(rows: list[dict], k: int, seed: int = 20261024) -> list[list[int]]:
    """Grouped k-fold: bikes bound to the SAME benchmark row stay together
    (no leakage of a shared target across folds)."""
    keys = sorted({r["bench_key"] for r in rows})
    rnd = random.Random(seed)
    rnd.shuffle(keys)
    k = max(2, min(k, len(keys)))
    fold_of = {key: n % k for n, key in enumerate(keys)}
    return [
        [j for j, r in enumerate(rows) if fold_of[r["bench_key"]] == f]
        for f in range(k)
    ]


def _clean(theta: dict) -> dict:
    return {k: theta[k] for k in KNOBS}


def _r(d: dict) -> dict:
    return {k: round(v, 4) for k, v in d.items()}


def tune_cluster(args) -> dict:
    tag, rows, lam, k = args
    t0 = time.time()
    ev = ClusterEval(tag, rows, lam)
    grids = grids_for(tag)
    all_idx = list(range(len(rows)))
    base = neutral_theta(tag)
    n_groups = len({r["bench_key"] for r in rows})
    thin = len(rows) < MIN_FIT_ROWS or n_groups < MIN_FIT_GROUPS
    out = {"tag": tag, "n_rows": len(rows), "n_groups": n_groups, "families": {}}
    cur = current_theta(tag)
    out["families"]["current"] = {
        "theta": _clean(cur),
        "complexity": complexity(cur),
        "insample": _r(ev.parts(cur, all_idx)),
        "report_only": True,
    }
    folds = make_folds(rows, k)
    out["k"] = len(folds)
    fold_fits: dict = {}
    full_fits: dict = {}
    for fam in FAMILY_ORDER:
        fit, warm = FAMILIES[fam]
        th_full = (
            cd_fit(ev, full_fits.get(warm, base), fit, all_idx, grids) if fit else base
        )
        full_fits[fam] = th_full
        rec = {
            "theta": _clean(th_full),
            "complexity": complexity(th_full),
            "insample": _r(ev.parts(th_full, all_idx)),
        }
        if not thin:
            oof = [None] * len(rows)
            fold_J = []
            fts = []
            for f, test in enumerate(folds):
                tset = set(test)
                train = [j for j in all_idx if j not in tset]
                if fit:
                    th = cd_fit(ev, fold_fits.get((warm, f), base), fit, train, grids)
                else:
                    th = base
                fold_fits[(fam, f)] = th
                fts.append(_clean(th))
                res = ev.res(th)
                for j in test:
                    oof[j] = res[j]
                fold_J.append(
                    objective_parts(
                        [rows[j] for j in test], [res[j] for j in test], lam
                    )["J"]
                )
            rec["cv"] = _r(objective_parts(rows, oof, lam))
            rec["cv_fold_J"] = [round(x, 4) for x in fold_J]
            rec["cv_se"] = (
                round(statistics.stdev(fold_J) / math.sqrt(len(fold_J)), 4)
                if len(fold_J) > 1
                else 0.0
            )
            rec["fold_thetas"] = fts
        out["families"][fam] = rec
    # ── selection ────────────────────────────────────────────────────────
    fams = out["families"]
    if thin:
        out["selected"] = "thin"
        out["selection_rule"] = (
            f"thin cluster (n_rows {len(rows)}, n_groups {n_groups}; need >= "
            f"{MIN_FIT_ROWS} rows and >= {MIN_FIT_GROUPS} benchmark rows): "
            "not fitted — donor knobs or neutral (THIN_DONORS)"
        )
        out["theta"] = None  # resolved by cmd_tune from THIN_DONORS
    else:
        best = min(FAMILY_ORDER, key=lambda f: fams[f]["cv"]["J"])
        thr = fams[best]["cv"]["J"] + fams[best]["cv_se"]
        elig = [f for f in FAMILY_ORDER if fams[f]["cv"]["J"] <= thr]
        sel = min(elig, key=lambda f: (fams[f]["complexity"], fams[f]["cv"]["J"]))
        out["selected"] = sel
        out["selection_rule"] = (
            f"1-SE: best CV '{best}' J={fams[best]['cv']['J']:.4f} + SE "
            f"{fams[best]['cv_se']:.4f} -> simplest eligible of {elig}"
        )
        out["theta"] = fams[sel]["theta"]
    out["n_evals"] = ev.n_evals
    out["n_sims"] = ev.n_evals * len(rows)
    out["wall_s"] = round(time.time() - t0, 1)
    return out


def cmd_tune(args) -> None:
    setup_root(None)
    rows = bind_rows(args.policy)
    for r in rows:
        cfg_for(r["i"])  # build configs before forking
    by_tag: dict = {}
    for r in rows:
        by_tag.setdefault(r["tag"], []).append(r)
    jobs = sorted(by_tag.items(), key=lambda kv: -len(kv[1]))
    jobs = [
        (tag, rs, args.lam, args.folds)
        for tag, rs in jobs
        if not args.only or tag in args.only
    ]
    t0 = time.time()
    if args.procs > 1:
        with mp.get_context("fork").Pool(args.procs) as pool:
            results = list(pool.imap_unordered(tune_cluster, jobs))
    else:
        results = [tune_cluster(j) for j in jobs]
    results.sort(key=lambda r: -r["n_rows"])
    res_by = {r["tag"]: r for r in results}
    # thin clusters: donor's selected knobs, or neutral
    for r in results:
        if r["theta"] is not None:
            continue
        donor = THIN_DONORS.get(r["tag"])
        if donor and donor in res_by and res_by[donor]["theta"] is not None:
            th = dict(res_by[donor]["theta"])
            th["cd_floor"] = neutral_theta(r["tag"])["cd_floor"]
            r["theta"] = th
            r["donor"] = donor
        else:
            r["theta"] = _clean(neutral_theta(r["tag"]))
            r["donor"] = None
        ev = ClusterEval(r["tag"], by_tag[r["tag"]], args.lam)
        r["thin_insample"] = _r(ev.parts(r["theta"], list(range(r["n_rows"]))))
    out = {
        "policy": args.policy,
        "lam_s_per_kmh": args.lam,
        "folds": args.folds,
        "min_fit_rows": MIN_FIT_ROWS,
        "min_fit_groups": MIN_FIT_GROUPS,
        "eps_s": EPS_S,
        "thin_donors": THIN_DONORS,
        "grids_4t": GRIDS_4T,
        "grids_2t": GRIDS_2T,
        "mu_refine_step": MU_REFINE_STEP,
        "wall_s": round(time.time() - t0, 1),
        "clusters": res_by,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    for r in results:
        f = r["families"]
        line = f"{r['tag']:22} n={r['n_rows']:3} g={r['n_groups']:3} sel={r['selected']:12} "
        for fam in ("current", *FAMILY_ORDER):
            v = f[fam].get("cv", {}).get("J", f[fam]["insample"]["J"])
            line += f"{fam}={v:.3f} "
        print(line, flush=True)
        print(
            "   theta:",
            {k: v for k, v in r["theta"].items() if v != NEUTRAL[k]},
            f"donor={r.get('donor')!r}" if "donor" in r else "",
            f"({r['wall_s']}s, {r['n_evals']} evals)",
        )


# ── Frozen reference profile ────────────────────────────────────────────────

REF_TAG = "reference_litre_195p"
#: label -> (published ET s, published trap km/h, ET tolerance s, source).
#: The tolerances are the references' documented acceptance bands in
#: tests/test_validation.py (K5 +/-0.10 s of 9.97; R1 +/-0.20 s of 10.3;
#: Hayabusa 10.1-10.7 s owner/magazine range -> centre 10.40 +/- 0.30).
REF_TARGETS = {
    "K5": (
        9.97,
        233.0,
        0.10,
        "Sport Rider GSX-R1000 K5 test (tests/test_validation.py)",
    ),
    "R1": (10.30, 238.0, 0.20, "Sport Rider 2004 YZF-R1 (tests/test_validation.py)"),
    "Hayabusa": (
        10.40,
        235.0,
        0.30,
        "stock Gen1 owner/magazine range 10.1-10.7 s (tests/test_validation.py)",
    ),
}
#: K5 60-ft realistic band (tests/test_validation.py::test_k5_sixty_foot).
K5_T60_BAND = (1.8, 2.1)
#: Candidate launch rpm fractions. None = StagingModel default (peak-torque
#: rpm, the physically neutral value); 0.615 = the curated K5
#: staging.launch_rpm (8000 / 13000 redline; R1 7500/12500 = 0.60, Hayabusa
#: 7000/11000 = 0.636) that two_step=False leaves dead; 0.55 = the importer's
#: >=400 cc EngineParams.launch_rpm convention.
REF_LR = [None, 0.55, 0.60, 0.615, 0.65, 0.70]
REF_MU = [round(0.85 + 0.001 * k, 3) for k in range(251)]  # 0.850-1.100
#: "Flat" band on the minimax objective (normalised units; 0.05 = 5 ms on
#: K5): within it the neutral launch rpm (None) wins, then the curated one.
REF_FLAT = 0.05


def ref_eval(theta: dict) -> dict:
    set_knobs(REF_TAG, theta)
    try:
        row = {k: theta[k] for k in theta}
        A = W = 0.0
        worst = 0.0
        for label, fn in CTX["refs"].items():
            et, trap, t60 = sim_quarter(fn())
            te, _tt, tol, _src = REF_TARGETS[label]
            row[label] = {"et_s": et, "trap_kmh": trap, "t60_s": t60}
            A += abs(et - te) / tol
            W += 1.0
            worst = max(worst, abs(et - te) / tol)
        row["max_norm_miss"] = worst
        row["mean_norm_miss"] = A / W
        row["all_within_tol"] = worst <= 1.0
        row["k5_t60_ok"] = K5_T60_BAND[0] < row["K5"]["t60_s"] < K5_T60_BAND[1]
        row["order_ok"] = (
            row["K5"]["et_s"] < row["R1"]["et_s"] < row["Hayabusa"]["et_s"]
        )
    finally:
        set_knobs(REF_TAG, None)
    return row


def cmd_refs(args) -> None:
    """Minimax fit: minimise the largest tolerance-normalised ET miss
    max_i |ET_i - pub_i| / tol_i over mu_peak_scale x launch_rpm_factor (a
    Chebyshev fit — each figure counts in units of its own documented
    uncertainty, so the instrumented K5 figure is held 2-3x tighter than the
    R1 magazine figure and the Hayabusa owner range). Within REF_FLAT of the
    optimum the neutral launch rpm wins (honesty over fit)."""
    setup_root(None)
    scan = [
        ref_eval({"mu_peak_scale": mu, "launch_rpm_factor": lr})
        for lr in REF_LR
        for mu in REF_MU
    ]
    best_by_lr = {}
    for lr in REF_LR:
        cand = [r for r in scan if r["launch_rpm_factor"] == lr]
        best_by_lr[str(lr)] = min(
            cand, key=lambda r: (r["max_norm_miss"], abs(r["mu_peak_scale"] - 1.0))
        )
    m_star = min(v["max_norm_miss"] for v in best_by_lr.values())
    flat = [v for v in best_by_lr.values() if v["max_norm_miss"] <= m_star + REF_FLAT]
    best = min(
        flat,
        key=lambda r: (
            r["launch_rpm_factor"] is not None,
            abs((r["launch_rpm_factor"] or 0.615) - 0.615),
            r["max_norm_miss"],
        ),
    )
    current = ref_eval(
        {
            "mu_peak_scale": CTX["base_knobs"][REF_TAG]["mu_peak_scale"],
            "launch_rpm_factor": CTX["base_knobs"][REF_TAG]["launch_rpm_factor"],
        }
    )
    out = {
        "tag": REF_TAG,
        "targets": {
            k: {"et_s": v[0], "trap_kmh": v[1], "tol_s": v[2], "source": v[3]}
            for k, v in REF_TARGETS.items()
        },
        "k5_t60_band_s": K5_T60_BAND,
        "objective": (
            "minimax: min over (mu_peak_scale, launch_rpm_factor) of "
            "max_i |ET_i - pub_i| / tol_i (tol = tests/test_validation.py "
            "bands); within REF_FLAT of the optimum the neutral launch rpm "
            "(None) wins, then the curated 0.615"
        ),
        "flat_band": REF_FLAT,
        "current": current,
        "best": best,
        "best_by_launch_rpm_factor": best_by_lr,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {
                "current": current,
                "best": best,
                "best_by_lr": {
                    k: (v["mu_peak_scale"], round(v["max_norm_miss"], 3))
                    for k, v in best_by_lr.items()
                },
            },
            indent=1,
        )
    )


# ── Report assembly ─────────────────────────────────────────────────────────


def _headline(m: dict, policy: str) -> dict:
    p = m.get(policy)
    if not p:
        return {}
    return {
        "overall": p["overall"],
        "trap": p["trap_overall"],
        "t60": p.get("t60"),
        "bands": p["bands"],
    }


def _clusters(m: dict, policy: str) -> dict:
    return {
        cl: {
            k: v[k]
            for k in ("n", "w_sum", "w_mean_abs", "w_bias", "raw_mean_abs")
            if k in v
        }
        | {"trap": v.get("trap"), "t60": v.get("t60")}
        for cl, v in m[policy]["clusters"].items()
    }


def cmd_report(args) -> None:
    """Assemble the epoch accuracy report from named measure/tune/refs
    outputs: head, dataepoch, physepoch, untuned, tuned (measure), tune,
    refs, plus optional lam_* (tune) and conservative_* (measure)."""
    inp = {}
    for kv in args.inputs:
        name, path = kv.split("=", 1)
        inp[name] = json.loads(Path(path).read_text())
    tuned = inp["tuned"]
    out = {
        "_doc": (
            "2026-10 physics + data epoch, retuned (scripts/tune_epoch_2026_10_24.py). "
            "Top-level 'references'/'n_bikes_swept'/'clusters'/'overall' keep the "
            "reports/acc_final_2026_08_08.json shape and use the EPOCH rules "
            "(epoch binding + epoch source weights); 'by_rules' carries both rule "
            "sets. Trap in km/h (sim - published), 60 ft in s."
        ),
        "references": {k: v["et_s"] for k, v in tuned["references"].items()},
        "references_full": tuned["references"],
        "n_bikes_swept": tuned["n_bikes_catalog"],
        "engine": tuned["engine"],
        "rules": "epoch",
        "clusters": {
            cl: {
                k: v[k]
                for k in ("n", "w_sum", "w_mean_abs", "w_bias", "raw_mean_abs")
                if k in v
            }
            for cl, v in tuned["epoch"]["clusters"].items()
        },
        "overall": tuned["epoch"]["overall"],
        "trap_overall": tuned["epoch"]["trap_overall"],
        "trap_clusters": {
            cl: v.get("trap") for cl, v in tuned["epoch"]["clusters"].items()
        },
        "t60_clusters": {
            cl: v.get("t60") for cl, v in tuned["epoch"]["clusters"].items()
        },
        "bands": tuned["epoch"]["bands"],
        "by_weight": tuned["epoch"]["by_weight"],
        "by_rules": {
            p: {**_headline(tuned, p), "clusters": _clusters(tuned, p)}
            for p in ("epoch", "legacy")
        },
        "topspeed": tuned["topspeed"]["summary"],
        "topspeed_scored": tuned["topspeed"]["scored"],
    }
    # ── old vs new + decomposition ──────────────────────────────────────
    stages = [
        ("head", "pre-epoch 0bd0ea2: physics + data + knobs as published 2026-08-08"),
        (
            "dataepoch",
            "pre-epoch physics (0bd0ea2, shaft_efficiency 0.85) + epoch data",
        ),
        (
            "physepoch",
            "epoch physics (+shaft 0.93) + pre-epoch data (0bd0ea2), knobs untuned",
        ),
        ("untuned", "epoch physics + epoch data, knobs untuned"),
        ("tuned", "epoch physics + epoch data + epoch knobs (this report)"),
    ]
    comp = {}
    for name, desc in stages:
        if name not in inp:
            continue
        m = inp[name]
        comp[name] = {
            "desc": desc,
            "engine": m["engine"],
            "references": {k: v["et_s"] for k, v in m["references"].items()},
            "epoch_rules": _headline(m, "epoch"),
            "legacy_rules": _headline(m, "legacy"),
            "topspeed": m.get("topspeed", {}).get("summary"),
        }
    out["old_vs_new"] = comp

    def wd(name, pol):
        return inp[name][pol]["overall"]["w_mean_abs"]

    def wb(name, pol):
        return inp[name][pol]["overall"]["w_bias"]

    dec = {}
    if all(n in inp for n in ("head", "untuned", "tuned")):
        dec["rule_change_on_head_model"] = {
            "w_mean_abs": round(wd("head", "epoch") - wd("head", "legacy"), 4),
            "w_bias": round(wb("head", "epoch") - wb("head", "legacy"), 4),
            "note": "same HEAD model, epoch vs legacy binding + weights (metric change)",
        }
        for pol in ("legacy", "epoch"):
            d = {
                "model_change_untuned": round(wd("untuned", pol) - wd("head", pol), 4),
                "retune": round(wd("tuned", pol) - wd("untuned", pol), 4),
                "total_model_change": round(wd("tuned", pol) - wd("head", pol), 4),
            }
            if "dataepoch" in inp and "physepoch" in inp:
                d["data_only"] = round(wd("dataepoch", pol) - wd("head", pol), 4)
                d["physics_only"] = round(wd("physepoch", pol) - wd("head", pol), 4)
                d["data_x_physics_interaction"] = round(
                    wd("untuned", pol)
                    - wd("dataepoch", pol)
                    - wd("physepoch", pol)
                    + wd("head", pol),
                    4,
                )
            dec[f"model_change_under_{pol}_rules_w_mean_abs"] = d
        dec["headline_published_to_new"] = {
            "from": "HEAD, legacy rules (published 2026-08-08: 0.2629)",
            "to": "tuned, epoch rules",
            "w_mean_abs": round(wd("tuned", "epoch") - wd("head", "legacy"), 4),
            "of_which_rules": round(wd("head", "epoch") - wd("head", "legacy"), 4),
            "of_which_model": round(wd("tuned", "epoch") - wd("head", "epoch"), 4),
        }
    out["decomposition"] = dec
    # ── tuning record ───────────────────────────────────────────────────
    tune = inp.get("tune")
    if tune:
        out["tuning"] = {
            "policy": tune["policy"],
            "lam_s_per_kmh": tune["lam_s_per_kmh"],
            "folds": tune["folds"],
            "min_fit_rows": tune["min_fit_rows"],
            "min_fit_groups": tune["min_fit_groups"],
            "thin_donors": tune["thin_donors"],
            "grids_4t": tune["grids_4t"],
            "grids_2t": tune["grids_2t"],
            "clusters": {
                tag: {
                    "n_rows": c["n_rows"],
                    "n_groups": c["n_groups"],
                    "selected": c["selected"],
                    "selection_rule": c["selection_rule"],
                    "donor": c.get("donor"),
                    "theta": c["theta"],
                    "cv": {
                        f: {
                            "J": v.get("cv", {}).get("J"),
                            "et_w_mean_abs": v.get("cv", {}).get("et_w_mean_abs"),
                            "et_w_bias": v.get("cv", {}).get("et_w_bias"),
                            "se": v.get("cv_se"),
                            "insample_J": v["insample"]["J"],
                            "complexity": v["complexity"],
                            "theta": {
                                k: x for k, x in v["theta"].items() if x != NEUTRAL[k]
                            },
                        }
                        for f, v in c["families"].items()
                    },
                }
                for tag, c in tune["clusters"].items()
            },
        }
    lam_runs = {k: v for k, v in inp.items() if k.startswith("lam_")}
    if lam_runs:
        out["lambda_sensitivity"] = {
            k: {
                "lam_s_per_kmh": v["lam_s_per_kmh"],
                "selected": {
                    tag: {
                        "family": c["selected"],
                        "theta": {
                            kk: x for kk, x in c["theta"].items() if x != NEUTRAL[kk]
                        },
                    }
                    for tag, c in v["clusters"].items()
                },
            }
            for k, v in lam_runs.items()
        }
    if "refs" in inp:
        r = inp["refs"]
        out["reference_fit"] = {
            k: r[k]
            for k in (
                "tag",
                "targets",
                "k5_t60_band_s",
                "objective",
                "flat_band",
                "current",
                "best",
                "best_by_launch_rpm_factor",
            )
        }
    cons = {k: v for k, v in inp.items() if k.startswith("conservative_")}
    if cons:
        out["conservative_alternatives"] = {
            k: {
                "root": v["root"],
                "engine": v["engine"],
                "thetas_applied": v.get("thetas_applied"),
                "epoch_rules": _headline(v, "epoch"),
                "legacy_rules": _headline(v, "legacy"),
                "topspeed": v.get("topspeed", {}).get("summary"),
                "references": {kk: vv["et_s"] for kk, vv in v["references"].items()},
            }
            for k, v in cons.items()
        }
    if args.notes:
        out["notes"] = json.loads(Path(args.notes).read_text())
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--out", required=True)
    m.add_argument("--root", default=None)
    m.add_argument("--policy", default="both", choices=("epoch", "legacy", "both"))
    m.add_argument("--thetas", default=None)
    m.add_argument("--procs", type=int, default=min(4, os.cpu_count() or 1))
    m.add_argument("--no-topspeed", action="store_true")
    m.set_defaults(fn=cmd_measure)
    t = sub.add_parser("tune")
    t.add_argument("--out", required=True)
    t.add_argument("--lam", type=float, default=0.01)
    t.add_argument("--folds", type=int, default=5)
    t.add_argument("--policy", default="epoch", choices=("epoch", "legacy"))
    t.add_argument("--procs", type=int, default=min(4, os.cpu_count() or 1))
    t.add_argument("--only", nargs="*", default=None, help="restrict to these tags")
    t.set_defaults(fn=cmd_tune)
    rf = sub.add_parser("refs")
    rf.add_argument("--out", required=True)
    rf.set_defaults(fn=cmd_refs)
    rp = sub.add_parser("report")
    rp.add_argument("--out", required=True)
    rp.add_argument("--inputs", nargs="+", required=True, help="NAME=PATH ...")
    rp.add_argument("--notes", default=None, help="JSON file merged in as 'notes'")
    rp.set_defaults(fn=cmd_report)
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
