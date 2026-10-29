#!/usr/bin/env python3
"""tune_epoch2_2026_10_29.py — 2026-10 physics epoch, ROUND 2 retune.

Round 1 (scripts/tune_epoch_2026_10_24.py, reports/acc_epoch_2026_10_24.json)
was rejected: it matched litre ETs with ``mu_peak_scale`` < 1, which left the
litre bikes traction-limited for most of the run, where a heavier bike is
FASTER (the pinned K5 got quicker as dry mass rose). Round 2 fixed the launch
physics (combined bike + rider CoG wheelie limit, drag pitch moment, tyre heat
balance, strip rollout geometry) and the benchmark timing data (per-source
timing convention, gearing / mass corrections). This script retunes the
CategoryProfile knobs FROM NEUTRAL under physical bounds and a HARD
mass-monotonicity gate, and measures the result honestly.

It reuses the round-1 tuner's model loading / statistics helpers (imported by
file path) and adds:

* per-row TIMING CONVENTION — every benchmark row is scored against the sim
  timed the way that row was timed (``sweep_lib.timing_convention``: strip /
  N.A. magazine / Dragy rows from the 1-ft rollout, Indonesian Racelogic rows
  from first motion, ``run(rollout_m=0.0)``);
* PHYSICAL BOUNDS — ``mu_peak_scale`` 0.95-1.15 (prefer 1.0 when flat) and
  ``launch_rpm_factor`` None or 0.45-0.75 x redline (4T clutch-dump rpm; a
  two-stroke launches on its pipe, which the StagingModel default already
  does, so 2T clusters only get None). No class rubber overrides, no
  over-clutch / floor / parasitic fudges (none is newly live in round 2);
* exhaustive grid evaluation (every (mu, launch rpm) pair is simulated once
  on every bound bike of the cluster), grouped 5-fold CV over benchmark rows
  and the one-standard-error rule toward the simplest knob set;
* the HARD GATE: the selected knob set of every cluster must leave its whole
  catalog population mass-monotone at +-10 kg with ZERO tolerance
  (``check_mass_monotonicity``'s catalog worker, spec path). Candidates are
  gated in preference order; when no family's choice passes, the CV is re-run
  over the gate-FEASIBLE grid points only (constrained selection). The litre
  bikes' traction-limited share above 2nd gear is reported per bike;
* thin clusters take a documented donor's knobs only when those do not make
  the cluster's own rows worse than neutral (the donor guard);
* the published-metric comparison on the HEAD 0bd0ea2 benchmark LABELS
  (legacy binding + legacy weights, the exact 2026-08-08 metric) and a
  cluster table with membership held fixed at HEAD's taxonomy.

Subcommands
-----------
head-dump --root HEAD_TREE --out JSON
    Dump HEAD's benchmark corpus (labels) and HEAD's cluster membership
    (keyed by catalog manufacturer / model / year_from) from a checkout of
    0bd0ea2. Run it in its own process (it imports that tree's motoquant).

measure --out JSON [--root PATH] [--thetas JSON | --neutral] [--head-json JSON]
        [--labels-json JSON] [--no-topspeed] [--gate]
    Score the model of ``--root`` (default: this checkout) under several
    metrics at once (see ``SCORINGS``): (a) epoch rules on the current
    labels, (b) legacy rules on the current labels, (c) the published
    legacy metric on the HEAD labels — each with per-row timing and with a
    uniform 1-ft rollout — plus trap, 60 ft, top speed, the references and
    (this checkout only) the mass-monotonicity gate.

tune --out JSON [--lam 0.01] [--folds 5] [--grid-cache PKL]
    Grid + CV + 1-SE + gate retune of every cluster (epoch rules, current
    labels, per-row timing). ``--grid-cache`` keeps the (knob-set x row)
    sims of THIS code state in a scratch pickle (lambda sensitivity re-runs
    reuse it; delete it after any physics / catalog / routing change).

refs --out JSON
    Fit the frozen ``reference_litre_195p`` profile to the references'
    published figures inside the same physical bounds.

report --out JSON --inputs NAME=PATH ... [--notes JSON]
    Assemble reports/acc_epoch2_2026_10_29.json from measure / tune / refs
    outputs: stages head, head_curlabels, r1_tuned, r1_neutral, hyb_neutral,
    neutral, tuned (see ``STAGES``), tune, lam_*, refs, alt_* (knob
    alternatives measured with --thetas).
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import math
import multiprocessing as mp
import os
import pickle
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


#: The round-1 tuner — model loading (``setup_root``), knob plumbing and the
#: statistics helpers are shared so the two rounds measure identically.
TE = _load_module("_epoch_r1_tuner", HERE / "tune_epoch_2026_10_24.py")
RULES = TE.RULES  # THIS checkout's scripts/sweep_lib.py (binding + timing)
CTX = TE.CTX
KNOBS = TE.KNOBS
NEUTRAL = TE.NEUTRAL
MAX_TIME_S = TE.MAX_TIME_S
DNF_ET_S = TE.DNF_ET_S

# ── Physical bounds (the search space) ──────────────────────────────────────
#
# mu_peak_scale 0.95-1.15: effective launch grip within -5 / +15 % of the
#     importer's rated rubber. Round 2's launch is WHEELIE-limited on every
#     litre bike (combined bike + rider CoG), so a grip scale < 1 no longer
#     has a "rider modulating the wheelie" meaning — the sim's wheelie limit
#     does that; the floor 0.95 only allows for a strip that is not prepped.
#     > 1 = prepped drag-strip surface / rubber better than the class default.
# launch_rpm_factor None or 0.45-0.75 x redline: the clutch-dump rpm. None =
#     the StagingModel default (peak-torque rpm). Magazine testers launch
#     litre bikes at ~6-8k rpm with the clutch slipping to keep the front
#     down (0.45-0.60 of a 13-14k redline); electronic launch controls hold
#     ~0.55-0.75. A two-stroke launches on its pipe (the importer's default
#     already does), so 2T clusters search None only.
MU_GRID = [round(0.95 + 0.01 * k, 2) for k in range(21)]  # 0.95 .. 1.15
#: 0.025 steps: the ET response to the clutch-dump rpm is steep where the
#: launch rpm drops below the torque plateau (litre_sport_195p: bias +0.25 s
#: at 0.45 vs -0.10 s at 0.50 on the 0.05 grid), so the 0.05 grid could not
#: centre a cluster; CV guards the finer grid against over-fitting.
LR_GRID_4T = [None] + [round(0.45 + 0.025 * k, 3) for k in range(13)]  # .45-.75
LR_GRID_2T = [None]
MU_BOUNDS = (0.95, 1.15)
LR_BOUNDS = (0.45, 0.75)

FAMILIES = ("neutral", "grip", "launch", "grip+lr")
MIN_FIT_ROWS = 8  # a cluster needs >= 8 bound bikes ...
MIN_FIT_GROUPS = 6  # ... and >= 6 distinct benchmark rows to be fitted
EPS_S = 0.001  # within this of the best in-sample J the most neutral wins
#: Thin clusters: tag -> donor tag whose SELECTED knobs they share (None =
#: neutral). cruiser_1300p <- other: heavy torque-rich road bikes launch
#: alike (round 1 and the 2026-06-11 calibration kept the two identical);
#: small_i4_screamer: n=2 bikes, nothing to share.
#: mid_twin_500_700: after the round-2 routing moved the 599 cc supersports
#: out it has 7 bound bikes (cruiser / ADV twins) — below the fit threshold,
#: and no fitted cluster shares its character (neutral).
THIN_DONORS = {
    "cruiser_1300p": "other",
    "small_i4_screamer": None,
    "mid_twin_500_700": None,
}

#: A SELECTED knob set must leave every catalog bike of its cluster with
#: ET(-10 kg) <= ET(0) <= ET(+10 kg) with no tolerance at all (the probe's own
#: 1e-4 s tolerance would accept a bike that is 0.03 ms quicker 10 kg
#: lighter-is-slower; selection does not).
GATE_MIN_MARGIN_S = 0.0

#: Litre clusters audited for "traction-limited above 2nd gear".
LITRE_TAGS = ("litre_sport_195p", "litre_sport_600_1000", "reference_litre_195p")
#: "a small fraction": share of gear >= 3 steps that are traction-limited.
TRACTION_ABOVE_2ND_MAX = 0.05

ROLLOUT_1FT = RULES.ROLLOUT_1FT_M
REF_TAG = TE.REF_TAG
REF_TARGETS = TE.REF_TARGETS
K5_T60_BAND = TE.K5_T60_BAND
REF_FLAT = TE.REF_FLAT

#: The metrics ``measure`` scores in one pass: name -> (labels, policy, timing)
#: labels "current" = this checkout's (or --root's) corpus, "head" = 0bd0ea2.
#: timing "row" = each row's own convention, "1ft" = everything at the 1-ft
#: rollout (the sim's default output).
SCORINGS = {
    "a_epoch_current_row": ("current", "epoch", "row"),
    "a_epoch_current_1ft": ("current", "epoch", "1ft"),
    "b_legacy_current_row": ("current", "legacy", "row"),
    "c_legacy_head_row": ("head", "legacy", "row"),
    "c_legacy_head_1ft": ("head", "legacy", "1ft"),
}
HEADLINE = "a_epoch_current_row"


# ── simulation ──────────────────────────────────────────────────────────────


def _has_rollout() -> bool:
    """Does the model under test's ``run()`` take ``rollout_m`` (HEAD does not:
    its ETs are timed from first motion)?"""
    if "has_rollout" not in CTX:
        eng = CTX["make_engine"](CTX["refs"]["K5"]())
        CTX["has_rollout"] = "rollout_m" in inspect.signature(eng.run).parameters
    return CTX["has_rollout"]


#: Strip speed traps average over the last 66 ft before the finish line.
TRAP_66FT_M = 66 * 0.3048


def _trap_66ft(r, distance_m: float):
    """66-ft-average trap speed (km/h): 66 ft / (t(D) - t(D - 66 ft)) — what a
    drag-strip speed trap reports; ``speed_quarter`` is the instantaneous
    speed AT the line (what a GPS meter reports). None if unavailable."""
    f = getattr(r, "time_speed_at", None)
    if f is None:
        return None
    a, b = f(distance_m - TRAP_66FT_M), f(distance_m)
    if a is None or b is None or b[0] <= a[0]:
        return None
    return TRAP_66FT_M / (b[0] - a[0]) * 3.6


def sim_quarter(cfg, rollout_m: float) -> tuple:
    """(et_s, trap_kmh, t60_s, trap66_kmh) — all None on a DNF / exception.
    ``trap_kmh`` is the instantaneous finish speed (the published metric);
    ``trap66_kmh`` the 66-ft-average strip trap (report-only sensitivity)."""
    try:
        eng = CTX["make_engine"](cfg)
        if _has_rollout():
            r = eng.run(use_adaptive_dt=False, max_time=MAX_TIME_S, rollout_m=rollout_m)
        else:
            r = eng.run(use_adaptive_dt=False, max_time=MAX_TIME_S)
    except Exception:
        return (None, None, None, None)
    if not r.finished_quarter:
        return (None, None, None, None)
    t60 = getattr(r, "time_60ft", None)
    return (
        float(r.time_quarter),
        float(r.speed_quarter * 3.6),
        float(t60) if t60 is not None and t60 > 0 else None,
        _trap_66ft(r, 402.336),
    )


def _sim_pair(key):
    i, ro = key
    cfg = TE.cfg_for(i)
    return (key, sim_quarter(cfg, ro) if cfg is not None else (None,) * 4)


def pool_map(fn, items, procs: int):
    items = list(items)
    if procs <= 1 or len(items) < 8:
        return [fn(x) for x in items]
    with mp.get_context("fork").Pool(procs) as pool:
        return pool.map(fn, items, chunksize=max(1, len(items) // (procs * 8)))


# ── binding ─────────────────────────────────────────────────────────────────


def _head_key(mfr, model, year_from) -> str:
    return f"{(mfr or '').lower()}|{(model or '').lower()}|{year_from}"


def bind_rows(policy: str, benchmarks, head_members: dict | None = None) -> list:
    """One row per catalog bike bound under ``policy`` (THIS checkout's
    ``sweep_lib.bind_benchmark_for_record``), with the row's timing
    convention (THIS checkout's ``sweep_lib.timing_convention_meta``)."""
    cp = CTX["cp"]
    wfn = TE.weight_fn(policy)
    bench_map = RULES.build_bench_map(benchmarks)
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
        timing, basis = RULES.timing_convention_meta(src)
        hk = _head_key(spec.manufacturer, spec.model_name, spec.year_from)
        rows.append(
            {
                "i": i,
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "year_from": spec.year_from,
                "tag": tag,
                "cluster": TE.TAG_TO_CLUSTER.get(tag, "other"),
                "head_cluster": (head_members or {}).get(hk),
                "target_et": float(te),
                "target_trap": float(tt) if tt else None,
                "weight": float(wfn(src)),
                "source": src,
                "bench_key": f"{spec.manufacturer.lower()}|{byear}|{te}|{tt}|{src}",
                "bench_year": byear,
                "in_range": bool(in_range),
                "timing": timing,
                "timing_basis": basis,
                "rollout_m": RULES.TIMING_ROLLOUT_M[timing],
            }
        )
    return rows


def _rollout_for(row: dict, timing_mode: str) -> float:
    return row["rollout_m"] if timing_mode == "row" else ROLLOUT_1FT


# ── statistics ──────────────────────────────────────────────────────────────


def summarise(rows: list[dict]) -> dict:
    """TE.summarise (current taxonomy) + the same table keyed by HEAD's
    cluster membership + per-timing-convention stats."""
    out = TE.summarise(rows)
    by_head: dict = {}
    for r in rows:
        by_head.setdefault(r.get("head_cluster") or "(not in HEAD catalog)", []).append(
            r
        )
    out["clusters_head_membership"] = {
        cl: {**TE.wstats(v), "trap": TE.trap_stats(v), "t60": TE.t60_stats(v)}
        for cl, v in sorted(by_head.items())
    }
    by_tm: dict = {}
    for r in rows:
        by_tm.setdefault(r["timing"], []).append(r)
    out["by_timing"] = {k: TE.wstats(v) for k, v in sorted(by_tm.items())}
    # 66-ft-average strip trap (sensitivity: what a beam trap would read)
    t66 = [
        {**r, "sim_trap": r["sim_trap66"]}
        for r in rows
        if r.get("sim_trap66") is not None
    ]
    out["trap66_overall"] = TE.trap_stats(t66)
    return out


def run_refs() -> dict:
    out = {}
    for label, fn in CTX["refs"].items():
        et, trap, t60, trap66 = sim_quarter(fn(), ROLLOUT_1FT)
        et0, _tr0, t600, _t66 = (
            sim_quarter(fn(), 0.0) if _has_rollout() else (et, None, t60, None)
        )
        out[label] = {
            "et_s": round(et, 4) if et is not None else None,
            "et_s_full": et,
            "trap_kmh": round(trap, 2) if trap is not None else None,
            "t60_s": round(t60, 4) if t60 is not None else None,
            "trap66_kmh": round(trap66, 2) if trap66 is not None else None,
            "et_first_motion_s": round(et0, 4) if et0 is not None else None,
            "t60_first_motion_s": round(t600, 4) if t600 is not None else None,
        }
    return out


# ── HEAD dump ───────────────────────────────────────────────────────────────


def cmd_head_dump(args) -> None:
    root = Path(args.root).resolve()
    TE.setup_root(root)
    swc = _load_module("_head_swc", root / "scripts" / "sweep_with_clusters.py")
    members = {}
    for s in CTX["specs"]:
        members[_head_key(s.manufacturer, s.model_name, s.year_from)] = swc.cluster_for(
            s.manufacturer,
            s.model_name,
            s.displacement_cc,
            s.peak_power_hp,
            getattr(s, "stroke_type", 4) or 4,
            getattr(s, "category", None),
            cylinders=getattr(s, "cylinders", None),
        )
    out = {
        "root": str(root),
        "n_benchmarks": len(CTX["benchmarks"]),
        "benchmarks": [list(b) for b in CTX["benchmarks"]],
        "n_catalog": len(CTX["specs"]),
        "membership": members,
    }
    Path(args.out).write_text(json.dumps(out, indent=0))
    print(f"wrote {args.out}: {out['n_benchmarks']} benchmarks, {len(members)} bikes")


def load_head(path: str | None) -> tuple:
    if not path:
        return None, {}
    d = json.loads(Path(path).read_text())
    return [tuple(b) for b in d["benchmarks"]], d["membership"]


# ── mass-monotonicity gate ──────────────────────────────────────────────────

_MONO = None


def mono():
    """scripts/check_mass_monotonicity.py, loaded by path (this checkout)."""
    global _MONO
    if _MONO is None:
        _MONO = _load_module("_epoch2_mono", HERE / "check_mass_monotonicity.py")
    return _MONO


def _gate_worker(args):
    idx, with_fractions = args
    return mono()._catalog_worker((idx, False, with_fractions))


def traction_above_2nd(limiters: dict | None) -> float | None:
    """Share of gear >= 3 integration steps that are traction-limited."""
    if not limiters:
        return None
    steps = trac = 0.0
    for g, v in limiters.items():
        if g == "all" or int(g) < 3:
            continue
        steps += v["steps"]
        trac += v["steps"] * v["traction_frac"]
    return round(trac / steps, 4) if steps else 0.0


def gate_catalog(indices, procs: int, with_fractions: bool = False) -> dict:
    """Mass-monotonicity (+-10 kg, spec path) over catalog bikes ``indices``
    with the CURRENT in-process profile knobs (inherited by fork)."""
    rows = pool_map(_gate_worker, [(i, with_fractions) for i in indices], procs)
    inv = [r for r in rows if r.get("inversions")]
    errs = [r for r in rows if "error" in r]
    margins = [
        (min(r["et_plus"] - r["et"], r["et"] - r["et_minus"]), r["name"])
        for r in rows
        if None not in (r.get("et"), r.get("et_plus"), r.get("et_minus"))
    ]
    worst = min(margins) if margins else (None, None)
    out = {
        "n": len(rows),
        "inversions": len(inv),
        "errors": len(errs),
        # smallest ET step over the +-10 kg probe (s); < 0 = an inversion
        "min_margin_s": round(worst[0], 5) if worst[0] is not None else None,
        "min_margin_bike": worst[1],
        "inverted": [
            {
                "name": r["name"],
                "cluster": r["cluster"],
                "et": r["et"],
                "et_plus10": r["et_plus"],
                "et_minus10": r["et_minus"],
                "kind": r["inversions"],
            }
            for r in inv
        ],
    }
    if with_fractions:
        tr = []
        for r in rows:
            f = traction_above_2nd(r.get("limiters"))
            if f is not None:
                tr.append(
                    {
                        "name": r["name"],
                        "cluster": r["cluster"],
                        "traction_frac_gear3plus": f,
                        "traction_frac_all": r["limiters"]["all"]["traction_frac"],
                        "wheelie_frac_all": r["limiters"]["all"]["wheelie_frac"],
                        "wheelie_frac_g1": r["limiters"]
                        .get("1", {})
                        .get("wheelie_frac"),
                    }
                )
        out["traction_above_2nd"] = {
            "n": len(tr),
            "max": max((t["traction_frac_gear3plus"] for t in tr), default=None),
            "n_above_threshold": sum(
                1 for t in tr if t["traction_frac_gear3plus"] > TRACTION_ABOVE_2ND_MAX
            ),
            "n_any": sum(1 for t in tr if t["traction_frac_gear3plus"] > 0),
            "threshold": TRACTION_ABOVE_2ND_MAX,
            "bikes": tr,
        }
    return out


def gate_references(with_fractions: bool = True) -> dict:
    res = mono().probe_references(with_fractions=with_fractions)
    out = {}
    for label, block in res.items():
        base = next(r for r in block["rows"] if r["delta_kg"] == 0.0)
        out[label] = {
            "monotone": block["monotone"],
            "et_by_delta_kg": {str(r["delta_kg"]): r["et"] for r in block["rows"]},
            "traction_frac_gear3plus": traction_above_2nd(base.get("limiters")),
            "limiters": base.get("limiters"),
        }
    return out


def catalog_indices_by_tag() -> dict:
    by: dict = {}
    for i in range(len(CTX["specs"])):
        cfg = TE.cfg_for(i)
        if cfg is not None:
            by.setdefault(cfg.category_tag, []).append(i)
    return by


# ── measure ─────────────────────────────────────────────────────────────────


def measure(
    scorings: dict,
    procs: int,
    thetas=None,
    head=None,
    topspeed: bool = True,
    gate: bool = False,
) -> dict:
    head_bench, head_members = head if head else (None, {})
    for tag, th in (thetas or {}).items():
        TE.set_knobs(tag, th)
    out = {
        "root": str(CTX["root"]),
        "motoquant_path": str(Path(sys.modules["motoquant"].__file__).parent),
        "engine": CTX["engine_name"],
        "has_rollout": _has_rollout(),
        "labels_from": CTX.get("labels_from", "root"),
        "n_bikes_catalog": len(CTX["specs"]),
        "thetas_applied": thetas or {},
        "references": run_refs(),
        "scorings": {},
    }
    bound = {}
    for name, (labels, policy, timing) in scorings.items():
        if labels == "head" and head_bench is None:
            continue
        bench = head_bench if labels == "head" else CTX["benchmarks"]
        bound[name] = (bind_rows(policy, bench, head_members), timing)
    need = sorted(
        {(r["i"], _rollout_for(r, tm)) for rows, tm in bound.values() for r in rows}
    )
    for i, _ in need:
        TE.cfg_for(i)  # build configs before forking
    t0 = time.time()
    sims = dict(pool_map(_sim_pair, need, procs))
    out["quarter_wall_s"] = round(time.time() - t0, 1)
    out["n_quarter_sims"] = len(need)
    for name, (rows, tm) in bound.items():
        for r in rows:
            et, trap, t60, trap66 = sims[(r["i"], _rollout_for(r, tm))]
            r["rollout_used_m"] = _rollout_for(r, tm)
            r["sim_trap66"] = round(trap66, 2) if trap66 is not None else None
            r["sim_et"] = round(et, 4) if et is not None else None
            r["sim_trap"] = round(trap, 2) if trap is not None else None
            r["sim_t60"] = round(t60, 4) if t60 is not None else None
            r["delta"] = round(et - r["target_et"], 4) if et is not None else None
        labels, policy, timing = scorings[name]
        out["scorings"][name] = {
            "labels": labels,
            "policy": policy,
            "timing": timing,
            **summarise(rows),
            "rows": rows,
        }
    if topspeed:
        ts_rows = TE.bind_topspeed()
        t0 = time.time()
        tsr = dict(pool_map(TE._sim_topspeed, sorted({r["i"] for r in ts_rows}), procs))
        out["topspeed_wall_s"] = round(time.time() - t0, 1)
        for r in ts_rows:
            res = tsr.get(r["i"])
            if res is None:
                r["sim_kmh"] = None
                continue
            r["sim_kmh"] = round(res[0], 1)
            r["reached_plateau"] = res[1]
            r["delta_kmh"] = round(res[0] - r["target_kmh"], 1)
        out["topspeed"] = {"summary": TE.ts_summary(ts_rows), "scored": ts_rows}
    if gate:
        t0 = time.time()
        by_tag = catalog_indices_by_tag()
        litre = sorted(i for t in LITRE_TAGS for i in by_tag.get(t, []))
        rest = sorted(set(range(len(CTX["specs"]))) - set(litre))
        g_l = gate_catalog(litre, procs, with_fractions=True)
        g_r = gate_catalog(rest, procs, with_fractions=False)
        out["mass_gate"] = {
            "references": gate_references(),
            "catalog": {
                "n": g_l["n"] + g_r["n"],
                "inversions": g_l["inversions"] + g_r["inversions"],
                "errors": g_l["errors"] + g_r["errors"],
                "inverted": g_l["inverted"] + g_r["inverted"],
            },
            "litre_traction_above_2nd": g_l["traction_above_2nd"],
            "wall_s": round(time.time() - t0, 1),
        }
    return out


def _brief(res: dict) -> dict:
    b = {
        "engine": res["engine"],
        "references": {
            k: (v["et_s"], v["t60_s"], v["trap_kmh"])
            for k, v in res["references"].items()
        },
    }
    for name, s in res["scorings"].items():
        b[name] = {
            "n": s["overall"].get("n"),
            "w|d|": s["overall"].get("w_mean_abs"),
            "bias": s["overall"].get("w_bias"),
            "trap_bias": s["trap_overall"].get("w_bias_kmh"),
            "trap|d|": s["trap_overall"].get("w_mean_abs_kmh"),
        }
    if "topspeed" in res:
        b["topspeed"] = res["topspeed"]["summary"]
    if "mass_gate" in res:
        g = res["mass_gate"]
        b["mass_gate"] = {
            "refs_monotone": {k: v["monotone"] for k, v in g["references"].items()},
            "catalog_inversions": g["catalog"]["inversions"],
            "inverted": [x["name"] for x in g["catalog"]["inverted"]],
            "litre_traction_above_2nd_max": g["litre_traction_above_2nd"]["max"],
        }
    return b


def load_thetas(path: str | None) -> dict:
    if not path:
        return {}
    d = json.loads(Path(path).read_text())
    if isinstance(d.get("clusters"), dict):
        th = {tag: c["theta"] for tag, c in d["clusters"].items()}
        if isinstance(d.get("reference"), dict) and d["reference"].get("theta"):
            th[REF_TAG] = d["reference"]["theta"]
        return th
    if "thetas" in d:
        return d["thetas"]
    if d.get("neutral_all"):
        return {tag: dict(NEUTRAL) for tag in d.get("tags", [])}
    return d


def neutral_thetas() -> dict:
    """Every profile at physically neutral knobs (cd_floor kept)."""
    return {tag: TE.neutral_theta(tag) for tag in CTX["cp"]._PROFILES}


def cmd_measure(args) -> None:
    TE.setup_root(args.root)
    if args.labels_json:
        # score the --root model against ANOTHER tree's corpus as the
        # "current" labels (a head-dump JSON of that tree)
        CTX["benchmarks"] = load_head(args.labels_json)[0]
        CTX["labels_from"] = args.labels_json
    thetas = neutral_thetas() if args.neutral else load_thetas(args.thetas)
    res = measure(
        SCORINGS,
        args.procs,
        thetas=thetas,
        head=load_head(args.head_json),
        topspeed=not args.no_topspeed,
        gate=args.gate,
    )
    Path(args.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(_brief(res), indent=1))


# ── tuning ──────────────────────────────────────────────────────────────────

ROWS_BY_TAG: dict = {}


def lr_grid(tag: str) -> list:
    return LR_GRID_2T if tag == "two_stroke" else LR_GRID_4T


def theta_of(tag: str, mu: float, lr) -> dict:
    t = TE.neutral_theta(tag)
    t["mu_peak_scale"] = mu
    t["launch_rpm_factor"] = lr
    return t


def _grid_job(job):
    tag, mu, lr = job
    TE.set_knobs(tag, theta_of(tag, mu, lr))
    try:
        res = [
            sim_quarter(TE.cfg_for(r["i"]), r["rollout_m"])[:3]
            for r in ROWS_BY_TAG[tag]
        ]
    finally:
        TE.set_knobs(tag, None)
    return (tag, mu, lr, res)


def family_points(fam: str, tag: str) -> list:
    if fam == "neutral":
        return [(1.0, None)]
    if fam == "grip":
        return [(mu, None) for mu in MU_GRID]
    if fam == "launch":
        return [(1.0, lr) for lr in lr_grid(tag)]
    return [(mu, lr) for mu in MU_GRID for lr in lr_grid(tag)]


def ndist(pt) -> float:
    """Distance from physical neutrality (tie-break inside the flat band)."""
    mu, lr = pt
    d = abs(mu - 1.0)
    if lr is not None:
        d += 1.0 + abs(lr - 0.55)  # any set launch rpm costs more than grip
    return d


def complexity_pt(pt) -> int:
    mu, lr = pt
    return int(mu != 1.0) + int(lr is not None)


def pick(points, Jf, eps: float = EPS_S):
    """argmin J over ``points``; within ``eps`` of the best the most neutral."""
    scored = [(Jf(p), p) for p in points]
    jb = min(s for s, _ in scored)
    ok = [p for s, p in scored if s <= jb + eps]
    return min(ok, key=ndist)


def cv_select(
    tag: str, rows: list, grid: dict, lam: float, k: int, allowed=None
) -> dict:
    """Grouped k-fold CV per family + 1-SE rule toward the simplest.

    ``allowed`` (a set of grid points) restricts every fit — in every fold
    and on the full data — to those points (the gate-feasible set); a family
    with no allowed point is dropped."""

    def parts(pt, idx):
        res = grid[pt]
        return TE.objective_parts([rows[j] for j in idx], [res[j] for j in idx], lam)

    def J(pt, idx):
        return parts(pt, idx)["J"]

    all_idx = list(range(len(rows)))
    folds = TE.make_folds(rows, k)
    fams = {}
    for fam in FAMILIES:
        pts = family_points(fam, tag)
        if allowed is not None:
            pts = [p for p in pts if p in allowed]
            if not pts:
                continue
        full = pick(pts, lambda p: J(p, all_idx))
        oof = [None] * len(rows)
        fold_J = []
        fold_pts = []
        for test in folds:
            ts = set(test)
            train = [j for j in all_idx if j not in ts]
            p = pick(pts, lambda p: J(p, train))
            fold_pts.append(p)
            for j in test:
                oof[j] = grid[p][j]
            fold_J.append(
                TE.objective_parts(
                    [rows[j] for j in test], [grid[p][j] for j in test], lam
                )["J"]
            )
        cv = TE.objective_parts(rows, oof, lam)
        fams[fam] = {
            "point": list(full),
            "complexity": complexity_pt(full),
            "insample": TE._r(parts(full, all_idx)),
            "cv": TE._r(cv),
            "cv_fold_J": [round(x, 4) for x in fold_J],
            "cv_se": (
                round(statistics.stdev(fold_J) / math.sqrt(len(fold_J)), 4)
                if len(fold_J) > 1
                else 0.0
            ),
            "fold_points": [list(p) for p in fold_pts],
        }
    present = [f for f in FAMILIES if f in fams]
    best = min(present, key=lambda f: fams[f]["cv"]["J"])
    thr = fams[best]["cv"]["J"] + fams[best]["cv_se"]
    elig = [f for f in present if fams[f]["cv"]["J"] <= thr]
    order = sorted(elig, key=lambda f: (fams[f]["complexity"], fams[f]["cv"]["J"]))
    rest = sorted(
        (f for f in present if f not in elig),
        key=lambda f: (fams[f]["cv"]["J"], fams[f]["complexity"]),
    )
    return {
        "families": fams,
        "best_cv": best,
        "eligible_1se": elig,
        "candidate_order": order + rest,
        "selection_rule": (
            f"1-SE: best CV '{best}' J={fams[best]['cv']['J']:.4f} + SE "
            f"{fams[best]['cv_se']:.4f} -> simplest eligible of {elig}"
        ),
    }


def insample_profile(tag: str, rows: list, grid: dict, lam: float) -> dict:
    """In-sample J / ET / trap over the whole grid (for the report)."""
    idx = list(range(len(rows)))
    out = {}
    for pt, res in grid.items():
        p = TE.objective_parts([rows[j] for j in idx], [res[j] for j in idx], lam)
        out[f"{pt[0]:.2f}|{pt[1]}"] = {
            "J": round(p["J"], 4),
            "et_w_mean_abs": round(p["et_w_mean_abs"], 4),
            "et_w_bias": round(p["et_w_bias"], 4),
            "trap_w_bias": round(p["trap_w_bias"], 2),
        }
    return out


def _gate_ok(g: dict) -> bool:
    """Selection gate: no inversion AND no negative step at all."""
    m = g.get("min_margin_s")
    return g["inversions"] == 0 and (m is None or m >= GATE_MIN_MARGIN_S)


def feasible_points(tag, grid, tried, cat_idx, args) -> dict:
    """Every grid point whose knob set leaves the cluster's whole catalog
    population mass-monotone (+-10 kg). Bikes that inverted on any tried
    candidate are screened first; survivors get the full-population gate."""
    names = {x["name"] for t in tried for x in t["inverted"]}
    specs = CTX["specs"]
    inv_idx = [
        i for i in cat_idx if f"{specs[i].manufacturer} {specs[i].model_name}" in names
    ]
    feas = {}
    n_screen_pass = 0
    for pt in grid:
        TE.set_knobs(tag, theta_of(tag, *pt))
        try:
            g = gate_catalog(inv_idx, 1) if inv_idx else {"inversions": 0}
            if not _gate_ok(g):
                continue
            n_screen_pass += 1
            full = gate_catalog(cat_idx, args.procs)
        finally:
            TE.set_knobs(tag, None)
        if _gate_ok(full):
            feas[pt] = {
                "min_margin_s": full["min_margin_s"],
                "min_margin_bike": full["min_margin_bike"],
            }
    return {"points": feas, "n_grid": len(grid), "n_screen_pass": n_screen_pass}


def _inv_size(x: dict) -> float:
    return max(
        x["et"] - x["et_plus10"] if "+10kg faster" in x["kind"] else 0.0,
        x["et_minus10"] - x["et"] if "-10kg slower" in x["kind"] else 0.0,
    )


def no_worse_than_neutral(tried) -> dict | None:
    """The first tried candidate (preference order) whose inversions are all
    present at neutral too, in the same direction and no larger — none of
    them knob-made. The fallback when no grid point is gate-feasible."""
    neu = next((t for t in tried if t["point"] == [1.0, None]), None)
    if neu is None:
        return None
    base = {x["name"]: x for x in neu["inverted"]}
    for t in tried:
        ok = all(
            x["name"] in base
            and set(x["kind"]) <= set(base[x["name"]]["kind"])
            and _inv_size(x) <= _inv_size(base[x["name"]]) + 1e-12
            for x in t["inverted"]
        )
        if ok:
            return t
    return None


def _ensure_point(tag, pt, theta, rows, grids) -> None:
    """Simulate ``theta`` on the cluster's rows if the grid lacks ``pt``."""
    if pt in grids[tag]:
        return
    TE.set_knobs(tag, theta)
    try:
        grids[tag][pt] = [
            sim_quarter(TE.cfg_for(r["i"]), r["rollout_m"])[:3] for r in rows
        ]
    finally:
        TE.set_knobs(tag, None)


def cmd_tune(args) -> None:
    TE.setup_root(None)
    rows = bind_rows("epoch", CTX["benchmarks"])
    for r in rows:
        TE.cfg_for(r["i"])
    by_tag: dict = {}
    for r in rows:
        by_tag.setdefault(r["tag"], []).append(r)
    ROWS_BY_TAG.clear()
    ROWS_BY_TAG.update(by_tag)
    info = {}
    jobs = []
    for tag, rs in by_tag.items():
        n_groups = len({r["bench_key"] for r in rs})
        thin = len(rs) < MIN_FIT_ROWS or n_groups < MIN_FIT_GROUPS
        info[tag] = {"n_rows": len(rs), "n_groups": n_groups, "thin": thin}
        pts = [(1.0, None)] if thin else family_points("grip+lr", tag)
        if (1.0, None) not in pts:
            pts.append((1.0, None))
        jobs += [(tag, mu, lr) for mu, lr in pts]
    t0 = time.time()
    grids: dict = {tag: {} for tag in by_tag}
    cache = Path(args.grid_cache) if args.grid_cache else None
    if cache is not None and cache.exists():
        # a scratch cache of THIS code state's grid (delete it after any
        # physics / catalog / routing change)
        grids = pickle.loads(cache.read_bytes())
    else:
        with mp.get_context("fork").Pool(args.procs) as pool:
            for tag, mu, lr, res in pool.imap_unordered(_grid_job, jobs, chunksize=4):
                grids[tag][(mu, lr)] = res
        if cache is not None:
            cache.write_bytes(pickle.dumps(grids))
    grid_wall = round(time.time() - t0, 1)
    print(f"grid: {len(jobs)} knob sets, {grid_wall}s", flush=True)

    # neutral gate population per tag (spec path, every catalog bike)
    cat_by_tag = catalog_indices_by_tag()
    clusters = {}
    for tag, rs in sorted(by_tag.items(), key=lambda kv: -len(kv[1])):
        rec = {**info[tag], "k": None}
        neutral_pt = (1.0, None)
        rec["neutral_insample"] = TE._r(
            TE.objective_parts(rs, grids[tag][neutral_pt], args.lam)
        )
        if info[tag]["thin"]:
            rec["selected"] = "thin"
            rec["selection_rule"] = (
                f"thin cluster (n_rows {len(rs)}, n_groups {info[tag]['n_groups']}; "
                f"need >= {MIN_FIT_ROWS} rows and >= {MIN_FIT_GROUPS} benchmark "
                "rows): not fitted — donor knobs or neutral (THIN_DONORS)"
            )
            clusters[tag] = rec
            continue
        sel = cv_select(tag, rs, grids[tag], args.lam, args.folds)
        rec.update(sel)
        rec["k"] = args.folds
        rec["insample_grid"] = insample_profile(tag, rs, grids[tag], args.lam)
        # gate the candidates in preference order; first zero-inversion wins
        tried = []
        chosen = None
        for fam in sel["candidate_order"]:
            pt = tuple(sel["families"][fam]["point"])
            if any(t["point"] == list(pt) for t in tried):
                continue
            TE.set_knobs(tag, theta_of(tag, *pt))
            try:
                g = gate_catalog(cat_by_tag.get(tag, []), args.procs)
            finally:
                TE.set_knobs(tag, None)
            tried.append(
                {
                    "family": fam,
                    "point": list(pt),
                    "inversions": g["inversions"],
                    "inverted": g["inverted"],
                    "min_margin_s": g["min_margin_s"],
                    "min_margin_bike": g["min_margin_bike"],
                }
            )
            print(
                f"  gate {tag:22} {fam:8} {pt} -> {g['inversions']} inversions, "
                f"min margin {g['min_margin_s']}"
            )
            if _gate_ok(g):
                chosen = (fam, pt)
                break
        rec["gate_tried"] = tried
        if chosen is None:
            # No family's unconstrained choice is inversion-free: re-run the
            # CV with every fit restricted to the gate-FEASIBLE grid points
            # (constrained selection — the gate is a hard constraint).
            cat_idx = cat_by_tag.get(tag, [])
            feas = feasible_points(tag, grids[tag], tried, cat_idx, args)
            rec["feasible"] = {
                "n_feasible": len(feas["points"]),
                "n_grid": feas["n_grid"],
                "n_screen_pass": feas["n_screen_pass"],
                "points": {
                    f"{p[0]:.2f}|{p[1]}": v
                    for p, v in sorted(feas["points"].items(), key=str)
                },
            }
            nwn = no_worse_than_neutral(tried)
            rec["no_worse_than_neutral_alternative"] = nwn and {
                "family": nwn["family"],
                "point": nwn["point"],
                "insample": TE._r(
                    TE.objective_parts(rs, grids[tag][tuple(nwn["point"])], args.lam)
                ),
                "inverted": nwn["inverted"],
            }
            rec["unconstrained"] = {
                k: sel[k]
                for k in (
                    "best_cv",
                    "eligible_1se",
                    "candidate_order",
                    "selection_rule",
                )
            }
            if feas["points"]:
                csel = cv_select(
                    tag,
                    rs,
                    grids[tag],
                    args.lam,
                    args.folds,
                    allowed=set(feas["points"]),
                )
                rec["constrained"] = csel
                fam = csel["candidate_order"][0]
                chosen = (fam, tuple(csel["families"][fam]["point"]))
                rec["gate_note"] = (
                    "no unconstrained family choice is inversion-free; selected by "
                    "CV + 1-SE over the gate-feasible grid points only "
                    f"({len(feas['points'])} of {feas['n_grid']})"
                )
                print(f"  constrained {tag}: {csel['selection_rule']} -> {chosen}")
        if chosen is None:
            # no grid point is inversion-free: keep the best candidate that
            # makes no inversion worse than neutral does (physics-level), else
            # the 1-SE choice; say so.
            nwn = no_worse_than_neutral(tried)
            if nwn is not None:
                chosen = (nwn["family"], tuple(nwn["point"]))
            else:
                fam = sel["candidate_order"][0]
                chosen = (fam, tuple(sel["families"][fam]["point"]))
            rec["gate_note"] = (
                "no grid point is inversion-free on this cluster's catalog "
                "population; selected the first candidate that makes no "
                "inversion worse than neutral (physics-level, reported)"
            )
        rec["selected"] = chosen[0]
        rec["point"] = list(chosen[1])
        rec["theta"] = TE._clean(theta_of(tag, *chosen[1]))
        rec["selected_insample"] = TE._r(
            TE.objective_parts(rs, grids[tag][chosen[1]], args.lam)
        )
        clusters[tag] = rec
        print(
            f"{tag:22} n={len(rs):3} g={info[tag]['n_groups']:3} sel={rec['selected']:8} "
            f"pt={chosen[1]} "
            + " ".join(
                f"{f}={sel['families'][f]['cv']['J']:.3f}"
                f"(+-{sel['families'][f]['cv_se']:.3f})"
                for f in FAMILIES
            ),
            flush=True,
        )
    # thin clusters: donor's selected knobs or neutral
    for tag, rec in clusters.items():
        if rec.get("selected") != "thin":
            continue
        donor = THIN_DONORS.get(tag)
        th = TE._clean(TE.neutral_theta(tag))
        pt = (1.0, None)
        rec["donor"] = None
        if donor and donor in clusters and clusters[donor].get("theta"):
            dth = dict(clusters[donor]["theta"])
            dth["cd_floor"] = TE.neutral_theta(tag)["cd_floor"]
            dpt = (dth["mu_peak_scale"], dth["launch_rpm_factor"])
            _ensure_point(tag, dpt, dth, by_tag[tag], grids)
            j_donor = TE.objective_parts(by_tag[tag], grids[tag][dpt], args.lam)["J"]
            j_neutral = TE.objective_parts(by_tag[tag], grids[tag][pt], args.lam)["J"]
            # Guard: a thin cluster inherits its donor's knobs only when they
            # do not make the cluster's own rows WORSE than neutral (the
            # donor is a prior, not a licence to degrade the cluster).
            if j_donor <= j_neutral:
                th, pt, rec["donor"] = dth, dpt, donor
            else:
                rec["donor_rejected"] = {
                    "donor": donor,
                    "point": list(dpt),
                    "insample_J_donor": round(j_donor, 4),
                    "insample_J_neutral": round(j_neutral, 4),
                    "rule": "donor knobs worsen the thin cluster's own rows -> neutral",
                }
        rec["theta"] = th
        rec["point"] = list(pt)
        _ensure_point(tag, pt, th, by_tag[tag], grids)
        rec["selected_insample"] = TE._r(
            TE.objective_parts(by_tag[tag], grids[tag][pt], args.lam)
        )
        TE.set_knobs(tag, th)
        try:
            g = gate_catalog(cat_by_tag.get(tag, []), args.procs)
        finally:
            TE.set_knobs(tag, None)
        rec["gate_tried"] = [
            {
                "family": "donor" if rec.get("donor") else "neutral",
                "point": list(pt),
                "inversions": g["inversions"],
                "inverted": g["inverted"],
                "min_margin_s": g["min_margin_s"],
                "min_margin_bike": g["min_margin_bike"],
            }
        ]
    # profiles with no bound bike at all (gate them at neutral for the record)
    for tag in sorted(set(cat_by_tag) - set(clusters)):
        th = TE._clean(TE.neutral_theta(tag))
        TE.set_knobs(tag, th)
        try:
            g = gate_catalog(cat_by_tag[tag], args.procs)
        finally:
            TE.set_knobs(tag, None)
        clusters[tag] = {
            "n_rows": 0,
            "n_groups": 0,
            "thin": True,
            "selected": "unbound",
            "theta": th,
            "point": [1.0, None],
            "gate_tried": [{"family": "neutral", "point": [1.0, None], **g}],
        }
    out = {
        "policy": "epoch",
        "labels": "current",
        "timing": "row",
        "lam_s_per_kmh": args.lam,
        "folds": args.folds,
        "min_fit_rows": MIN_FIT_ROWS,
        "min_fit_groups": MIN_FIT_GROUPS,
        "eps_s": EPS_S,
        "thin_donors": THIN_DONORS,
        "mu_grid": MU_GRID,
        "lr_grid_4t": LR_GRID_4T,
        "lr_grid_2t": LR_GRID_2T,
        "bounds": {"mu_peak_scale": MU_BOUNDS, "launch_rpm_factor": LR_BOUNDS},
        "families": FAMILIES,
        "grid_wall_s": grid_wall,
        "n_grid_sims": sum(len(v) * len(by_tag[t]) for t, v in grids.items()),
        "wall_s": round(time.time() - t0, 1),
        "clusters": clusters,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    for tag, rec in clusters.items():
        print(
            f"   {tag:22} theta:",
            {k: v for k, v in rec["theta"].items() if v != NEUTRAL[k]},
            f"donor={rec.get('donor')!r}" if "donor" in rec else "",
        )


# ── frozen reference profile ────────────────────────────────────────────────


def ref_eval(mu: float, lr) -> dict:
    TE.set_knobs(REF_TAG, theta_of(REF_TAG, mu, lr))
    try:
        row = {"mu_peak_scale": mu, "launch_rpm_factor": lr}
        worst = tot = 0.0
        for label, fn in CTX["refs"].items():
            et, trap, t60, _t66 = sim_quarter(fn(), ROLLOUT_1FT)
            et0, _tr0, t600, _t660 = sim_quarter(fn(), 0.0)
            te, tt, tol, _src = REF_TARGETS[label]
            row[label] = {
                "et_s": et,
                "trap_kmh": trap,
                "t60_s": t60,
                "et_first_motion_s": et0,
                "t60_first_motion_s": t600,
                "et_norm_miss": abs(et - te) / tol,
                "trap_miss_kmh": trap - tt,
            }
            worst = max(worst, abs(et - te) / tol)
            tot += abs(et - te) / tol
        row["max_norm_miss"] = worst
        row["mean_norm_miss"] = tot / len(CTX["refs"])
        row["all_within_tol"] = worst <= 1.0
        row["k5_t60_rollout_ok"] = K5_T60_BAND[0] < row["K5"]["t60_s"] < K5_T60_BAND[1]
        row["k5_t60_first_motion_ok"] = (
            K5_T60_BAND[0] < row["K5"]["t60_first_motion_s"] < K5_T60_BAND[1]
        )
        row["order_ok"] = (
            row["K5"]["et_s"] < row["R1"]["et_s"] < row["Hayabusa"]["et_s"]
        )
        row["traps_within_10kmh"] = all(
            abs(row[k]["trap_miss_kmh"]) < 10.0 for k in REF_TARGETS
        )
    finally:
        TE.set_knobs(REF_TAG, None)
    return row


def cmd_refs(args) -> None:
    """Minimax fit (as round 1): minimise max_i |ET_i - pub_i| / tol_i over
    (mu_peak_scale, launch_rpm_factor) inside the physical bounds; within
    REF_FLAT of the optimum the most neutral point wins. The winner must keep
    the references mass-monotone (the gate)."""
    TE.setup_root(None)
    scan = [ref_eval(mu, lr) for lr in LR_GRID_4T for mu in MU_GRID]
    m_star = min(r["max_norm_miss"] for r in scan)
    flat = [r for r in scan if r["max_norm_miss"] <= m_star + REF_FLAT]
    order = sorted(
        flat,
        key=lambda r: (
            ndist((r["mu_peak_scale"], r["launch_rpm_factor"])),
            r["max_norm_miss"],
        ),
    )
    gate_log = []
    best = None
    for cand in order:
        TE.set_knobs(
            REF_TAG, theta_of(REF_TAG, cand["mu_peak_scale"], cand["launch_rpm_factor"])
        )
        try:
            g = gate_references(with_fractions=True)
        finally:
            TE.set_knobs(REF_TAG, None)
        ok = all(v["monotone"] for v in g.values())
        gate_log.append(
            {
                "mu_peak_scale": cand["mu_peak_scale"],
                "launch_rpm_factor": cand["launch_rpm_factor"],
                "monotone": {k: v["monotone"] for k, v in g.items()},
                "traction_frac_gear3plus": {
                    k: v["traction_frac_gear3plus"] for k, v in g.items()
                },
            }
        )
        if ok:
            best = dict(cand)
            best["mass_gate"] = g
            break
    best_by_lr = {}
    for lr in LR_GRID_4T:
        cand = [r for r in scan if r["launch_rpm_factor"] == lr]
        best_by_lr[str(lr)] = min(
            cand, key=lambda r: (r["max_norm_miss"], abs(r["mu_peak_scale"] - 1.0))
        )
    neutral = next(
        r for r in scan if r["mu_peak_scale"] == 1.0 and r["launch_rpm_factor"] is None
    )
    out = {
        "tag": REF_TAG,
        "targets": {
            k: {"et_s": v[0], "trap_kmh": v[1], "tol_s": v[2], "source": v[3]}
            for k, v in REF_TARGETS.items()
        },
        "k5_t60_band_s": K5_T60_BAND,
        "bounds": {"mu_peak_scale": MU_BOUNDS, "launch_rpm_factor": LR_BOUNDS},
        "objective": (
            "minimax: min over (mu_peak_scale, launch_rpm_factor) inside the "
            "physical bounds of max_i |ET_i - pub_i| / tol_i (tol = "
            "tests/test_validation.py bands); within REF_FLAT of the optimum the "
            "most neutral point wins; the winner must keep all three references "
            "mass-monotone (-20..+20 kg)"
        ),
        "flat_band": REF_FLAT,
        "neutral": neutral,
        "best": best,
        "gate_log": gate_log,
        "best_by_launch_rpm_factor": best_by_lr,
        "scan": scan,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    show = {
        k: {
            kk: (
                round(v[kk]["et_s"], 4),
                round(v[kk]["t60_s"], 3),
                round(v[kk]["trap_kmh"], 1),
            )
            for kk in REF_TARGETS
        }
        | {"max_norm_miss": round(v["max_norm_miss"], 3)}
        for k, v in {"neutral": neutral, "best": best}.items()
        if v
    }
    print(json.dumps(show, indent=1))
    print(
        "best by lr:",
        {
            k: (v["mu_peak_scale"], round(v["max_norm_miss"], 3))
            for k, v in best_by_lr.items()
        },
    )


# ── report assembly ─────────────────────────────────────────────────────────

_ST_KEYS = ("n", "w_sum", "w_mean_abs", "w_bias", "raw_mean_abs")

#: report stage name -> description (``report --inputs NAME=measure.json``)
STAGES = {
    "head": "HEAD 0bd0ea2: physics + data + knobs as published 2026-08-08",
    "head_curlabels": "HEAD 0bd0ea2 model scored on the round-2 benchmark labels",
    "r1_tuned": "round 1 (4a683eb): epoch physics + data + round-1 knobs (rejected)",
    "r1_neutral": "round-1 physics + round-1 data, neutral knobs",
    "hyb_neutral": "round-2 physics + round-1 catalog data, neutral knobs",
    "neutral": "round-2 physics + round-2 data, neutral knobs",
    "tuned": "round-2 physics + round-2 data + round-2 knobs (this report)",
}


def _st(v: dict) -> dict:
    return {k: v[k] for k in _ST_KEYS if k in v}


def _scoring_headline(sc: dict) -> dict:
    return {
        "labels": sc["labels"],
        "policy": sc["policy"],
        "timing": sc["timing"],
        "overall": sc["overall"],
        "trap": sc["trap_overall"],
        "trap66": sc.get("trap66_overall"),
        "t60": sc.get("t60"),
        "bands": sc["bands"],
        "by_timing": sc.get("by_timing"),
    }


def _headlines(m: dict) -> dict:
    return {name: _scoring_headline(sc) for name, sc in m["scorings"].items()}


def _wd(m: dict, name: str) -> float:
    return m["scorings"][name]["overall"]["w_mean_abs"]


def _wb(m: dict, name: str) -> float:
    return m["scorings"][name]["overall"]["w_bias"]


def _decomposition(inp: dict) -> dict:
    """Chain HEAD -> round-2 tuned on ONE metric at a time, so each step's
    delta is one change: labels/binding, physics, data, retune."""
    out = {}
    for metric in ("a_epoch_current_row", "c_legacy_head_row"):
        d = {"metric": metric}
        chain = [
            ("head_curlabels" if metric.startswith("a") else "head", "HEAD model"),
            ("r1_neutral", "round-1 physics + data (neutral)"),
            ("hyb_neutral", "+ round-2 physics (round-1 data, neutral)"),
            ("neutral", "+ round-2 data (neutral)"),
            ("tuned", "+ round-2 retune"),
        ]
        prev = None
        steps = []
        for name, desc in chain:
            if name not in inp:
                continue
            v = _wd(inp[name], metric)
            steps.append(
                {
                    "stage": name,
                    "desc": desc,
                    "w_mean_abs": v,
                    "w_bias": _wb(inp[name], metric),
                    "delta_w_mean_abs": None if prev is None else round(v - prev, 4),
                }
            )
            prev = v
        d["chain"] = steps
        out[metric] = d
    if "head" in inp and "head_curlabels" in inp and "tuned" in inp:
        h, hc, t = inp["head"], inp["head_curlabels"], inp["tuned"]
        out["labels_binding_timing"] = {
            "note": (
                "metric change measured on a FIXED model: the published metric "
                "(c: HEAD labels, legacy binding + weights) vs the epoch headline "
                "(a: round-2 labels, epoch binding + weights, per-row timing)"
            ),
            "on_head_model": round(
                _wd(hc, "a_epoch_current_row") - _wd(h, "c_legacy_head_row"), 4
            ),
            "on_tuned_model": round(
                _wd(t, "a_epoch_current_row") - _wd(t, "c_legacy_head_row"), 4
            ),
            "of_which_timing_per_row_vs_1ft_tuned": round(
                _wd(t, "a_epoch_current_row") - _wd(t, "a_epoch_current_1ft"), 4
            ),
        }
        out["published_to_new"] = {
            "from": "HEAD, published metric (c): 0.2629",
            "to_c": "round-2 tuned, published metric (c)",
            "delta_c": round(
                _wd(t, "c_legacy_head_row") - _wd(h, "c_legacy_head_row"), 4
            ),
            "to_a": "round-2 tuned, epoch headline (a)",
            "delta_a": round(
                _wd(t, "a_epoch_current_row") - _wd(h, "c_legacy_head_row"), 4
            ),
        }
    return out


def _cluster_table_head_membership(inp: dict, head_pub: dict) -> dict:
    """Per-cluster stats with membership held FIXED at HEAD's taxonomy, on
    the published metric (c), for HEAD (as published) / neutral / tuned."""
    out = {}
    names = set(head_pub)
    for k in ("neutral", "tuned", "r1_tuned"):
        if k in inp:
            names |= set(
                inp[k]["scorings"]["c_legacy_head_row"]["clusters_head_membership"]
            )
    for cl in sorted(names):
        row = {"head_published": _st(head_pub.get(cl, {}))}
        for k in ("r1_tuned", "neutral", "tuned"):
            if k in inp:
                v = inp[k]["scorings"]["c_legacy_head_row"][
                    "clusters_head_membership"
                ].get(cl, {})
                row[k] = _st(v) | {"trap": v.get("trap"), "t60": v.get("t60")}
        out[cl] = row
    return out


def _acceptance(t: dict, head: dict, refs: dict | None) -> dict:
    c = t["scorings"]["c_legacy_head_row"]
    a = t["scorings"][HEADLINE]
    pub = head["scorings"]["c_legacy_head_row"]["overall"]["w_mean_abs"]
    pub_trap = head["scorings"]["c_legacy_head_row"]["trap_overall"]["w_bias_kmh"]
    g = t.get("mass_gate", {})
    ts = t.get("topspeed", {}).get("summary", {})
    bad_cl = {
        cl: v["w_bias"]
        for cl, v in a["clusters"].items()
        if abs(v.get("w_bias", 0)) > 0.25
    }
    ref_ok = {}
    for label, v in t["references"].items():
        te, _tt, tol, _src = REF_TARGETS[label]
        ref_ok[label] = abs(v["et_s"] - te) <= tol
    return {
        "et_published_metric_c": {
            "value": c["overall"]["w_mean_abs"],
            "published_head": pub,
            "delta": round(c["overall"]["w_mean_abs"] - pub, 4),
            "pass_le_published": c["overall"]["w_mean_abs"] <= pub,
            "pass_within_0.005": c["overall"]["w_mean_abs"] <= pub + 0.005,
        },
        "et_epoch_headline_a": a["overall"]["w_mean_abs"],
        "bias": {
            "a": a["overall"]["w_bias"],
            "c": c["overall"]["w_bias"],
            "pass_abs_le_0.02_a": abs(a["overall"]["w_bias"]) <= 0.02,
            "pass_abs_le_0.02_c": abs(c["overall"]["w_bias"]) <= 0.02,
        },
        "trap_bias_kmh": {
            "a": a["trap_overall"]["w_bias_kmh"],
            "c": c["trap_overall"]["w_bias_kmh"],
            "published_head_c": pub_trap,
            "pass_clearly_below": abs(c["trap_overall"]["w_bias_kmh"]) < pub_trap / 2,
        },
        "topspeed_mean_abs_kmh": {
            "value": ts.get("mean_abs_delta_kmh"),
            "published_head": 28.1,
            "pass_clearly_below": (ts.get("mean_abs_delta_kmh") or 99) < 28.1 / 1.5,
        },
        "mass_inversions": {
            "catalog": g.get("catalog", {}).get("inversions"),
            "references_monotone": {
                k: v["monotone"] for k, v in g.get("references", {}).items()
            },
            "pass_zero": g.get("catalog", {}).get("inversions") == 0
            and all(v["monotone"] for v in g.get("references", {}).values()),
        },
        "litre_traction_above_2nd": {
            "max_share_gear3plus": g.get("litre_traction_above_2nd", {}).get("max"),
            "threshold": TRACTION_ABOVE_2ND_MAX,
        },
        "references_in_band": ref_ok,
        "k5_t60": {
            "rollout_1ft_s": t["references"]["K5"]["t60_s"],
            "first_motion_s": t["references"]["K5"]["t60_first_motion_s"],
            "band_s": K5_T60_BAND,
        },
        "clusters_bias_beyond_0.25_epoch_headline": bad_cl,
        "refs_fit_all_within_tol": (refs or {}).get("best", {}).get("all_within_tol"),
    }


def _compact_refs(r: dict) -> dict:
    keep = (
        "tag",
        "targets",
        "k5_t60_band_s",
        "bounds",
        "objective",
        "flat_band",
        "neutral",
        "best",
        "gate_log",
        "best_by_launch_rpm_factor",
    )
    out = {k: r[k] for k in keep if k in r}
    out["scan_summary"] = [
        {
            "mu_peak_scale": x["mu_peak_scale"],
            "launch_rpm_factor": x["launch_rpm_factor"],
            "max_norm_miss": round(x["max_norm_miss"], 4),
            "et": {k: round(x[k]["et_s"], 4) for k in REF_TARGETS},
            "t60": {k: round(x[k]["t60_s"], 4) for k in REF_TARGETS},
        }
        for x in r.get("scan", [])
        if x["mu_peak_scale"] in (0.95, 1.0, 1.05, 1.15)
    ]
    return out


def _compact_tune(tune: dict) -> dict:
    out = {
        k: tune[k]
        for k in (
            "policy",
            "labels",
            "timing",
            "lam_s_per_kmh",
            "folds",
            "min_fit_rows",
            "min_fit_groups",
            "eps_s",
            "thin_donors",
            "mu_grid",
            "lr_grid_4t",
            "lr_grid_2t",
            "bounds",
            "families",
            "n_grid_sims",
        )
        if k in tune
    }
    out["gate_min_margin_s"] = GATE_MIN_MARGIN_S
    cl = {}
    for tag, c in tune["clusters"].items():
        rec = {
            k: c.get(k)
            for k in (
                "n_rows",
                "n_groups",
                "selected",
                "selection_rule",
                "point",
                "theta",
                "donor",
                "donor_rejected",
                "selected_insample",
                "neutral_insample",
                "gate_tried",
                "gate_note",
                "feasible",
                "no_worse_than_neutral_alternative",
                "unconstrained",
                "best_cv",
                "eligible_1se",
            )
            if k in c
        }
        if "families" in c:
            rec["cv"] = {
                f: {
                    "point": v["point"],
                    "J": v["cv"]["J"],
                    "et_w_mean_abs": v["cv"]["et_w_mean_abs"],
                    "et_w_bias": v["cv"]["et_w_bias"],
                    "se": v["cv_se"],
                    "fold_J": v["cv_fold_J"],
                    "fold_points": v["fold_points"],
                    "insample_J": v["insample"]["J"],
                    "complexity": v["complexity"],
                }
                for f, v in c["families"].items()
            }
        if "constrained" in c:
            rec["constrained_cv"] = {
                "selection_rule": c["constrained"]["selection_rule"],
                "families": {
                    f: {
                        "point": v["point"],
                        "J": v["cv"]["J"],
                        "se": v["cv_se"],
                        "et_w_bias": v["cv"]["et_w_bias"],
                    }
                    for f, v in c["constrained"]["families"].items()
                },
            }
        if "insample_grid" in c:
            # the launch-rpm profile at rated grip and the grip profile at the
            # default launch (the full grid is in the scratch tune output)
            ig = c["insample_grid"]
            rec["insample_profile_mu_1.00"] = {
                k.split("|")[1]: v for k, v in ig.items() if k.startswith("1.00|")
            }
            rec["insample_profile_lr_None"] = {
                k.split("|")[0]: v for k, v in ig.items() if k.endswith("|None")
            }
        cl[tag] = rec
    out["clusters"] = cl
    return out


def cmd_report(args) -> None:
    inp = {}
    for kv in args.inputs:
        name, path = kv.split("=", 1)
        inp[name] = json.loads(Path(path).read_text())
    t = inp["tuned"]
    a = t["scorings"][HEADLINE]
    head_pub = json.loads(Path(args.head_published).read_text())
    out = {
        "_doc": (
            "2026-10 physics epoch ROUND 2 retune (scripts/tune_epoch2_2026_10_29.py). "
            "Top-level 'references'/'n_bikes_swept'/'clusters'/'overall' keep the "
            "reports/acc_final_2026_08_08.json shape and use the epoch headline: "
            "round-2 labels, epoch binding + epoch source weights, every row scored "
            "under its own timing convention (1-ft rollout or first motion). "
            "'headline' carries (a) that metric, (b) legacy rules on the same "
            "labels and (c) the EXACT published 2026-08-08 metric (HEAD 0bd0ea2 "
            "labels, legacy binding + weights). Trap in km/h (sim - published; "
            "sim = instantaneous finish speed, 'trap66' = 66-ft strip-trap "
            "average), 60 ft in s."
        ),
        "references": {k: v["et_s"] for k, v in t["references"].items()},
        "references_full": t["references"],
        "n_bikes_swept": t["n_bikes_catalog"],
        "engine": t["engine"],
        "rules": "epoch",
        "timing": "row",
        "clusters": {cl: _st(v) for cl, v in a["clusters"].items()},
        "overall": a["overall"],
        "trap_overall": a["trap_overall"],
        "trap66_overall": a.get("trap66_overall"),
        "trap_clusters": {cl: v.get("trap") for cl, v in a["clusters"].items()},
        "t60_overall": a.get("t60"),
        "t60_clusters": {cl: v.get("t60") for cl, v in a["clusters"].items()},
        "bands": a["bands"],
        "by_weight": a["by_weight"],
        "by_timing": a.get("by_timing"),
        "by_rules": {
            "epoch": {
                **_scoring_headline(a),
                "clusters": {cl: _st(v) for cl, v in a["clusters"].items()},
            },
            "legacy": {
                **_scoring_headline(t["scorings"]["b_legacy_current_row"]),
                "clusters": {
                    cl: _st(v)
                    for cl, v in t["scorings"]["b_legacy_current_row"][
                        "clusters"
                    ].items()
                },
            },
        },
        "headline": _headlines(t),
        "clusters_head_membership_published_metric": _cluster_table_head_membership(
            inp, head_pub["clusters"]
        ),
        "topspeed": t["topspeed"]["summary"],
        "topspeed_scored": t["topspeed"]["scored"],
        "mass_gate": t.get("mass_gate"),
    }
    out["old_vs_new"] = {
        name: {
            "desc": desc,
            "engine": inp[name]["engine"],
            "root": inp[name]["root"],
            "references": {k: v["et_s"] for k, v in inp[name]["references"].items()},
            "headline": _headlines(inp[name]),
            "topspeed": inp[name].get("topspeed", {}).get("summary"),
        }
        for name, desc in STAGES.items()
        if name in inp
    }
    out["decomposition"] = _decomposition(inp)
    if "tune" in inp:
        out["tuning"] = _compact_tune(inp["tune"])
    lam = {k: v for k, v in inp.items() if k.startswith("lam_")}
    if lam:
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
            for k, v in lam.items()
        }
    if "refs" in inp:
        out["reference_fit"] = _compact_refs(inp["refs"])
    alts = {k: v for k, v in inp.items() if k.startswith("alt_")}
    if alts:
        out["conservative_alternatives"] = {
            k: {
                "thetas_applied": v.get("thetas_applied"),
                "headline": {
                    n: {
                        "overall": sc["overall"],
                        "trap": sc["trap_overall"],
                    }
                    for n, sc in v["scorings"].items()
                },
                "mass_gate": {
                    "catalog_inversions": v.get("mass_gate", {})
                    .get("catalog", {})
                    .get("inversions"),
                    "inverted": v.get("mass_gate", {})
                    .get("catalog", {})
                    .get("inverted"),
                    "litre_traction_above_2nd_max": v.get("mass_gate", {})
                    .get("litre_traction_above_2nd", {})
                    .get("max"),
                },
                "references": {kk: vv["et_s"] for kk, vv in v["references"].items()},
            }
            for k, v in alts.items()
        }
    out["acceptance"] = _acceptance(t, inp["head"], inp.get("refs"))
    if args.notes:
        out["notes"] = json.loads(Path(args.notes).read_text())
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")
    print(json.dumps(out["acceptance"], indent=1))


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("head-dump")
    h.add_argument("--root", required=True)
    h.add_argument("--out", required=True)
    h.set_defaults(fn=cmd_head_dump)
    m = sub.add_parser("measure")
    m.add_argument("--out", required=True)
    m.add_argument("--root", default=None)
    m.add_argument("--thetas", default=None)
    m.add_argument("--neutral", action="store_true", help="every profile neutral")
    m.add_argument("--head-json", default=None)
    m.add_argument(
        "--labels-json", default=None, help="head-dump JSON used as 'current' labels"
    )
    m.add_argument("--procs", type=int, default=min(4, os.cpu_count() or 1))
    m.add_argument("--no-topspeed", action="store_true")
    m.add_argument("--gate", action="store_true", help="also run the mass gate")
    m.set_defaults(fn=cmd_measure)
    t = sub.add_parser("tune")
    t.add_argument("--out", required=True)
    t.add_argument("--lam", type=float, default=0.01)
    t.add_argument("--folds", type=int, default=5)
    t.add_argument("--procs", type=int, default=min(4, os.cpu_count() or 1))
    t.add_argument("--grid-cache", default=None, help="scratch pickle of the grid")
    t.set_defaults(fn=cmd_tune)
    rf = sub.add_parser("refs")
    rf.add_argument("--out", required=True)
    rf.set_defaults(fn=cmd_refs)
    rp = sub.add_parser("report")
    rp.add_argument("--out", required=True)
    rp.add_argument("--inputs", nargs="+", required=True, help="NAME=PATH ...")
    rp.add_argument(
        "--head-published",
        default=str(REPO / "reports" / "acc_final_2026_08_08.json"),
        help="the published 2026-08-08 report (per-cluster HEAD table)",
    )
    rp.add_argument("--notes", default=None, help="JSON file merged in as 'notes'")
    rp.set_defaults(fn=cmd_report)
    args = ap.parse_args(argv)
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
