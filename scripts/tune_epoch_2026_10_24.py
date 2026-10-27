#!/usr/bin/env python3
"""tune_epoch_2026_10_24.py — 2026-10 physics-epoch joint ET + trap retune.

The 2026-10 epoch (ADR-0002) changed the physics (no double-counted slip
inertia, soft-cut limiter, continuous slip ratio, 1-ft rollout timing,
energy-consistent launch floor, 4T crank recal 1.00 + rated-power cap) and the
catalog data (no sport Cd x0.55, real drive types, corrected specs, epoch
benchmark binding). This script re-centres the per-cluster CategoryProfile
knobs against a JOINT objective and measures the result honestly.

All simulation goes through ``motoquant.engine_select.make_engine`` (the Rust
core when available — bit-identical to the Python reference, ~50x faster).

Subcommands
-----------
measure --out JSON [--root PATH] [--policy epoch|legacy|both] [--no-topspeed]
    Weighted ET + trap sweep (same binding/weights as the published sweep,
    rules taken from THIS checkout's scripts/sweep_lib.py), the top-speed
    sweep (scripts/topspeed_sweep.py matching) and the three references.
    ``--root`` points at another checkout (e.g. a ``git worktree`` of HEAD)
    whose physics + catalog + benchmark corpus are measured instead — the
    binding RULES always come from this checkout, so rule and model changes
    can be separated.

tune --out JSON [--lam 0.01] [--folds 5] [--procs 4]
    Per-cluster joint retune with grouped k-fold cross-validation and a
    one-standard-error preference for neutral knobs (see ``tune_cluster``).

refs --out JSON
    Fit the frozen ``reference_litre_195p`` profile to the references'
    published figures (separate from the catalog fit).

Objective (per cluster)::

    J = w|d|_ET  +  lam * w|d|_trap        (s;  trap in km/h, lam in s per km/h)

with the corpus source weights (instrumented 1.0 / magazine 0.7 / aggregator
0.5 / forum 0.3 / derived-estimate 0.1). ``lam = 0.01`` s per km/h: the
corpus residual scales are ~0.26 s (ET) vs ~15 km/h (trap) — a noise-ratio
of ~0.017 s/km/h — and published trap figures carry extra measurement
convention noise (66-ft speed-trap average vs instantaneous finish speed,
mph/km/h transcription) that ET does not, so the trap term is weighted at
~0.6x its residual-scale ratio: it breaks ties in the directions ET cannot
see without overriding the ET headline.
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

#: Physically neutral value of every knob (no rider model, rated rubber,
#: modelled parasitics, no floor, launch at the StagingModel default).
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

# category_tag -> report cluster label (dashes), mirrors
# scripts/sweep_with_clusters.TAG_TO_CLUSTER.
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
    """Source weight function of a rule set."""
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

    vs = _load_module("_epoch_root_validation_sweep", root / "scripts/validation_sweep.py")
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
    """Cached BikeConfig of catalog spec ``i`` (None if the importer raises)."""
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
    """One row per catalog bike bound to an ET benchmark under ``policy``."""
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
    rows = [
        r for r in rows if r.get("sim_trap") is not None and r.get("target_trap")
    ]
    if not rows:
        return {"n": 0}
    W = sum(r["weight"] for r in rows) or 1e-9
    d = [r["sim_trap"] - r["target_trap"] for r in rows]
    return {
        "n": len(rows),
        "w_mean_abs_kmh": round(sum(abs(x) * r["weight"] for x, r in zip(d, rows)) / W, 2),
        "w_bias_kmh": round(sum(x * r["weight"] for x, r in zip(d, rows)) / W, 2),
        "raw_mean_abs_kmh": round(statistics.mean(abs(x) for x in d), 2),
        "w_bias_pct": round(
            100
            * sum(x / r["target_trap"] * r["weight"] for x, r in zip(d, rows))
            / W,
            2,
        ),
    }


def within_bands(rows: list[dict]) -> dict:
    d = [abs(r["sim_et"] - r["target_et"]) for r in rows if r.get("sim_et") is not None]
    return {f"within_{b:.2f}s": sum(1 for x in d if x <= b) for b in (0.05, 0.10, 0.20, 0.50, 1.00)}


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
    by = {}
    for r in rows:
        by.setdefault(r["cluster"], []).append(r)
    return {
        "overall": wstats(rows),
        "trap_overall": trap_stats(rows),
        "bands": within_bands(rows),
        "clusters": {
            cl: {**wstats(v), "trap": trap_stats(v)} for cl, v in sorted(by.items())
        },
        "by_weight": {
            str(w): wstats([r for r in rows if r["weight"] == w])
            for w in sorted({r["weight"] for r in rows}, reverse=True)
        },
    }


def measure(policies, procs: int, topspeed: bool = True) -> dict:
    out = {
        "root": str(CTX["root"]),
        "motoquant_path": str(Path(sys.modules["motoquant"].__file__).parent),
        "engine": CTX["engine_name"],
        "n_bikes_catalog": len(CTX["specs"]),
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
    res = measure(policies, args.procs, topspeed=not args.no_topspeed)
    Path(args.out).write_text(json.dumps(res, indent=1))
    brief = {
        "engine": res["engine"],
        "references": {k: v["et_s"] for k, v in res["references"].items()},
    }
    for p in policies:
        brief[p] = {
            "overall": res[p]["overall"],
            "trap": res[p]["trap_overall"],
        }
    if "topspeed" in res:
        brief["topspeed"] = res["topspeed"]["summary"]
    print(json.dumps(brief, indent=1))


# ── Tuning ──────────────────────────────────────────────────────────────────

#: Coarse search grids (mu_peak_scale is pattern-refined to 0.005 afterwards).
GRIDS = {
    "mu_peak_scale": [round(0.60 + 0.04 * k, 3) for k in range(21)],
    "launch_rpm_factor": [None, 0.5, 0.6, 0.7, 0.8, 0.9],
    "launch_floor_factor": [0.0, 0.7, 0.85, 1.0],
    # (over_clutch_factor, max_engine_decel_rads2) searched JOINTLY: the
    # extra back-torque is min(headroom * oc, decel * I_e), so either one at
    # zero makes the other inert and a 1-D search could never leave (0, 0).
    "over_clutch": [(0.0, 0.0)]
    + [(oc, de) for oc in (0.2, 0.4, 0.6) for de in (100.0, 400.0, 1600.0)],
    "parasitic_mult": [round(0.5 + 0.1 * k, 2) for k in range(11)],
}

LAUNCH = ("launch_rpm_factor", "launch_floor_factor", "over_clutch")

#: name -> (fitted knobs, start point, warm-start family)
FAMILIES = {
    "neutral": ((), "neutral", None),
    "current": ((), "current", None),
    "grip": (("mu_peak_scale",), "neutral", None),
    "current+grip": (("mu_peak_scale",), "current", None),
    "grip+launch": (("mu_peak_scale", *LAUNCH), "neutral", "grip"),
    "full": (("mu_peak_scale", *LAUNCH, "parasitic_mult"), "neutral", "grip+launch"),
}
FAMILY_ORDER = ("neutral", "current", "grip", "current+grip", "grip+launch", "full")

MIN_FIT_ROWS = 8  # thinner clusters keep neutral knobs (not fitted)
EPS_S = 0.001  # objective improvements below this are noise -> prefer neutral


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
        return 1.0 + abs(v - 0.7)
    return abs(v - n)


def complexity(theta: dict) -> int:
    """Number of non-neutral (live-meaning) knobs in ``theta``."""
    c = 0
    c += theta["mu_peak_scale"] != 1.0
    c += theta["mu_peak_override"] is not None
    c += bool(theta["over_clutch_factor"] and theta["max_engine_decel_rads2"])
    c += bool(theta["launch_floor_factor"])
    c += theta["launch_rpm_factor"] is not None
    c += theta["parasitic_mult"] != 1.0
    return int(c)


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


def refine_mu(ev: ClusterEval, cur: dict, idx, eps: float) -> dict:
    """Pattern search on mu_peak_scale (steps 0.02 / 0.01 / 0.005); a move
    that does not beat the incumbent by eps/4 goes toward 1.0 or not at all."""
    for step in (0.02, 0.01, 0.005):
        for _ in range(40):
            c = cur["mu_peak_scale"]
            cands = [c, round(c - step, 4), round(c + step, 4)]
            scored = [(ev.J(_with(cur, "mu_peak_scale", v), idx), v) for v in cands]
            jb = min(s for s, _ in scored)
            ok = [v for s, v in scored if s <= jb + eps / 4]
            v = min(ok, key=lambda v: (abs(v - 1.0), v))
            if v == c:
                break
            cur = _with(cur, "mu_peak_scale", v)
    return cur


def cd_fit(ev: ClusterEval, start: dict, fit, idx, eps: float = EPS_S, max_pass: int = 4) -> dict:
    """Coordinate descent over the coarse grids; within ``eps`` of the best
    value the most-neutral one wins (honesty over fit)."""
    cur = dict(start)
    for _ in range(max_pass):
        changed = False
        for k in fit:
            vals = list(GRIDS[k])
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
    if "mu_peak_scale" in fit:
        cur = refine_mu(ev, cur, idx, eps)
    return cur


def make_folds(rows: list[dict], k: int, seed: int = 20261024) -> list[list[int]]:
    """Grouped k-fold: bikes bound to the SAME benchmark row stay together
    (no leakage of a shared target across folds)."""
    keys = sorted({r["bench_key"] for r in rows})
    rnd = random.Random(seed)
    rnd.shuffle(keys)
    k = max(2, min(k, len(keys)))
    fold_of = {key: n % k for n, key in enumerate(keys)}
    return [[j for j, r in enumerate(rows) if fold_of[r["bench_key"]] == f] for f in range(k)]


def _clean(theta: dict) -> dict:
    return {k: theta[k] for k in KNOBS}


def tune_cluster(args) -> dict:
    tag, rows, lam, k = args
    t0 = time.time()
    ev = ClusterEval(tag, rows, lam)
    all_idx = list(range(len(rows)))
    starts = {"neutral": neutral_theta(tag), "current": current_theta(tag)}
    out = {"tag": tag, "n_rows": len(rows), "families": {}}
    thin = len(rows) < MIN_FIT_ROWS
    folds = make_folds(rows, k)
    out["n_groups"] = len({r["bench_key"] for r in rows})
    out["k"] = len(folds)
    fold_fits: dict = {}
    full_fits: dict = {}
    for fam in FAMILY_ORDER:
        fit, start_name, warm = FAMILIES[fam]
        base = starts[start_name]
        # full-data fit (for thin clusters: in-sample information only)
        th_full = cd_fit(ev, full_fits.get(warm, base), fit, all_idx) if fit else base
        full_fits[fam] = th_full
        ins = ev.parts(th_full, all_idx)
        rec = {
            "theta": _clean(th_full),
            "complexity": complexity(th_full),
            "insample": {kk: round(v, 4) for kk, v in ins.items()},
        }
        if not thin:
            oof = [None] * len(rows)
            fold_J = []
            fts = []
            for f, test in enumerate(folds):
                tset = set(test)
                train = [j for j in all_idx if j not in tset]
                if fit:
                    th = cd_fit(ev, fold_fits.get((warm, f), base), fit, train)
                else:
                    th = base
                fold_fits[(fam, f)] = th
                fts.append(_clean(th))
                res = ev.res(th)
                for j in test:
                    oof[j] = res[j]
                fold_J.append(objective_parts([rows[j] for j in test], [res[j] for j in test], lam)["J"])
            cvp = objective_parts(rows, oof, lam)
            rec["cv"] = {kk: round(v, 4) for kk, v in cvp.items()}
            rec["cv_fold_J"] = [round(x, 4) for x in fold_J]
            rec["cv_se"] = round(statistics.stdev(fold_J) / math.sqrt(len(fold_J)), 4) if len(fold_J) > 1 else 0.0
            rec["fold_thetas"] = fts
            rec["oof"] = [
                (o[0] if o[0] is None else round(o[0], 4), o[1] if o[1] is None else round(o[1], 2))
                for o in oof
            ]
        out["families"][fam] = rec
    # ── selection ────────────────────────────────────────────────────────
    fams = out["families"]
    if thin:
        out["selected"] = "neutral"
        out["selection_rule"] = f"n_rows {len(rows)} < {MIN_FIT_ROWS}: not fitted (neutral knobs)"
    else:
        best = min(FAMILY_ORDER, key=lambda f: fams[f]["cv"]["J"])
        thr = fams[best]["cv"]["J"] + fams[best]["cv_se"]
        elig = [f for f in FAMILY_ORDER if fams[f]["cv"]["J"] <= thr]
        sel = min(elig, key=lambda f: (fams[f]["complexity"], fams[f]["cv"]["J"]))
        out["selected"] = sel
        out["selection_rule"] = (
            f"1-SE: best CV '{best}' J={fams[best]['cv']['J']:.4f} + SE {fams[best]['cv_se']:.4f}"
            f" -> simplest eligible of {elig}"
        )
    out["theta"] = fams[out["selected"]]["theta"]
    out["n_evals"] = ev.n_evals
    out["n_sims"] = ev.n_evals * len(rows)
    out["wall_s"] = round(time.time() - t0, 1)
    return out


def apply_thetas(thetas: dict) -> None:
    for tag, th in thetas.items():
        set_knobs(tag, th)


def cmd_tune(args) -> None:
    setup_root(None)
    rows = bind_rows(args.policy)
    for r in rows:
        cfg_for(r["i"])  # build configs before forking
    by_tag: dict = {}
    for r in rows:
        by_tag.setdefault(r["tag"], []).append(r)
    jobs = sorted(by_tag.items(), key=lambda kv: -len(kv[1]))
    jobs = [(tag, rs, args.lam, args.folds) for tag, rs in jobs if not args.only or tag in args.only]
    t0 = time.time()
    if args.procs > 1:
        with mp.get_context("fork").Pool(args.procs) as pool:
            results = list(pool.imap_unordered(tune_cluster, jobs))
    else:
        results = [tune_cluster(j) for j in jobs]
    results.sort(key=lambda r: -r["n_rows"])
    out = {
        "policy": args.policy,
        "lam_s_per_kmh": args.lam,
        "folds": args.folds,
        "min_fit_rows": MIN_FIT_ROWS,
        "eps_s": EPS_S,
        "grids": dict(GRIDS),
        "wall_s": round(time.time() - t0, 1),
        "clusters": {r["tag"]: r for r in results},
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    for r in results:
        f = r["families"]
        line = f"{r['tag']:22} n={r['n_rows']:3} sel={r['selected']:13} "
        for fam in FAMILY_ORDER:
            cv = f[fam].get("cv", {}).get("J")
            line += f"{fam}={cv if cv is not None else f[fam]['insample']['J']:.3f} "
        print(line, flush=True)
        print("   theta:", {k: v for k, v in r["theta"].items() if v != NEUTRAL[k]}, f"({r['wall_s']}s, {r['n_evals']} evals)")


# ── Frozen reference profile ────────────────────────────────────────────────

REF_TAG = "reference_litre_195p"
#: label -> (published ET s, published trap km/h, weight, source)
REF_TARGETS = {
    "K5": (9.97, 233.0, 1.0, "Sport Rider GSX-R1000 K5 test (tests/test_validation.py)"),
    "R1": (10.30, 238.0, 0.7, "Sport Rider 2004 YZF-R1 (benchmark corpus row)"),
    "Hayabusa": (
        10.40,
        235.0,
        0.5,
        "stock Gen1 owner/magazine range 10.2-10.5 s, midpoint (test_validation)",
    ),
}


def ref_scan(mus) -> list[dict]:
    out = []
    for mu in mus:
        set_knobs(REF_TAG, {"mu_peak_scale": mu})
        row = {"mu_peak_scale": mu}
        A = W = 0.0
        for label, fn in CTX["refs"].items():
            et, trap, t60 = sim_quarter(fn())
            te, _tt, w, _src = REF_TARGETS[label]
            row[label] = {"et_s": et, "trap_kmh": trap, "t60_s": t60}
            A += w * abs(et - te)
            W += w
        row["w_mean_abs"] = A / W
        out.append(row)
    set_knobs(REF_TAG, None)
    return out


def cmd_refs(args) -> None:
    setup_root(None)
    mus = [round(0.70 + 0.005 * k, 3) for k in range(int((1.12 - 0.70) / 0.005) + 1)]
    scan = ref_scan(mus)
    best = min(scan, key=lambda r: (round(r["w_mean_abs"], 6), abs(r["mu_peak_scale"] - 1.0)))
    per_bike = {}
    for label in REF_TARGETS:
        te = REF_TARGETS[label][0]
        b = min(scan, key=lambda r: abs(r[label]["et_s"] - te))
        per_bike[label] = {"mu_for_exact_match": b["mu_peak_scale"], "et_s": b[label]["et_s"]}
    out = {
        "tag": REF_TAG,
        "targets": {k: {"et_s": v[0], "trap_kmh": v[1], "weight": v[2], "source": v[3]} for k, v in REF_TARGETS.items()},
        "objective": "sum(w*|ET_sim - ET_pub|)/sum(w), mu_peak_scale only (1 knob, 3 targets)",
        "best": best,
        "per_bike_mu_for_exact_match": per_bike,
        "scan": scan,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({"best": best, "per_bike": per_bike}, indent=1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--out", required=True)
    m.add_argument("--root", default=None)
    m.add_argument("--policy", default="both", choices=("epoch", "legacy", "both"))
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
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
