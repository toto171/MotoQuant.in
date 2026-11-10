#!/usr/bin/env python3
"""tune_epoch3_2026_11_03.py — 2026-10 physics epoch, ROUND 3 retune.

Round 2 (scripts/tune_epoch2_2026_10_29.py, reports/acc_epoch2_2026_10_29.json)
verified the launch physics (combined bike + rider CoG wheelie limit, drag
pitch moment, tyre heat balance, strip rollout geometry, per-row timing
convention) but its retune failed the published ET metric (c): 0.3427 vs
0.2629. The round-2 verifier's diagnosis: with neutral knobs the launch is
~0.3 s too fast on nearly every bike, a near-UNIFORM offset — the model holds
the launch exactly on the ~1.1 g wheelie ceiling, while magazine 60-ft times
(~1.9 s from the beam) imply ~0.8 g. Round 2's ``launch_rpm_factor`` (a
fraction of redline) turned that uniform bias into per-bike scatter.

Round 3 adds ONE physical knob, ``CategoryProfile.wheelie_margin`` (0.65-1.0,
1.0 = bit-identical no-op): the fraction of the system wheelie ceiling the
rider holds in 1st gear (motoquant/physics.py run loop; mirrored in the Rust
core, resolved-config schema 5). This script retunes every cluster FROM
NEUTRAL over (``mu_peak_scale`` 0.97-1.10, ``wheelie_margin`` 0.65-1.00) with
``launch_rpm_factor`` RETIRED (None everywhere), using round 2's machinery
unchanged — per-row timing convention, objective w|d|_ET + 0.01 s/(km/h) x
w|d|_trap, grouped 5-fold CV, one-standard-error rule toward the most neutral
knob set, the HARD dry-mass monotonicity gate (+-10 kg, zero tolerance) with
constrained re-selection, the thin-cluster donor guard — by loading the
round-2 tuner by file path and swapping its knob-space hooks (``theta_of``,
``family_points``, ``ndist``, ``complexity_pt``, ``FAMILIES``).

Subcommands (same CLI shape as round 2)
--------------------------------------
measure --out JSON [--root PATH] [--thetas JSON | --neutral]
        [--uniform-margin M] [--head-json JSON] [--no-topspeed] [--gate]
    Round-2 ``measure`` (metrics a/b/c, trap, 60 ft, top speed, references);
    ``--gate`` runs the round-3 gate: dry mass AND rider mass +-10 kg, at
    the default environment and at sea level / 15 C, plus the litre
    traction-above-2nd audit. ``--uniform-margin`` sets every profile's
    wheelie_margin on top of the thetas (exploration only).
tune --out JSON [--lam 0.01] [--folds 5] [--grid-cache PKL]
refs --out JSON
report --out JSON --head-published JSON --inputs NAME=PATH ... [--notes JSON]
    stages: head, neutral, r2_tuned, tuned (+ tune, refs, alt_*).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import multiprocessing as mp
import pickle
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


#: The round-2 tuner (which itself loads round 1's helpers). Its knob-space
#: hooks are swapped below; everything else is reused as-is so round 3
#: measures exactly the way round 2 did.
T2 = _load_module("_epoch_r2_tuner", HERE / "tune_epoch2_2026_10_29.py")
TE = T2.TE
CTX = TE.CTX

# ── knob plumbing: wheelie_margin joins the managed knob set ────────────────
if "wheelie_margin" not in TE.KNOBS:
    TE.KNOBS = TE.KNOBS + ("wheelie_margin",)
T2.KNOBS = TE.KNOBS
TE.NEUTRAL["wheelie_margin"] = 1.0  # shared dict (T2.NEUTRAL is TE.NEUTRAL)
NEUTRAL = TE.NEUTRAL

# ── Physical bounds (the search space) ──────────────────────────────────────
#
# mu_peak_scale 0.97-1.10: effective launch grip within -3 / +10 % of the
#     importer's rated rubber (prefer 1.0 — rated rubber — when flat). Round 2
#     sat on its 0.95 floor, making clusters traction-limited (rider-mass
#     inversions); the floor is raised so grip cannot stand in for the rider's
#     wheelie modulation.
# wheelie_margin 0.65-1.00: fraction of the combined bike + rider wheelie
#     ceiling the rider holds in 1st gear. 1.0 = riding on the balance point
#     (the round-2 physics); magazine 60 ft of ~1.9 s from the beam implies a
#     mean launch near 0.8 g against a ~1.1 g ceiling (~0.7-0.75). Below 0.65
#     no competent test launch is described.
# launch_rpm_factor: RETIRED as a bias corrector (None = the StagingModel
#     default). It survives ONLY as the "margin+lr" family (rated rubber,
#     a margin, and a clutch-dump rpm 0.45-0.75 x redline): the 1-SE rule
#     keeps it out unless the CV shows a clear gain, and the constrained
#     (gate-feasible) re-selection may use it — a launch held below the
#     torque plateau is torque-limited and therefore mass-SENSITIVE, the one
#     physical way out of the wheelie-ballast inversions of the lightest
#     200+ hp bikes (BMW HP4 Race), which invert at neutral already.
MU_GRID = [round(0.97 + 0.01 * k, 2) for k in range(14)]  # 0.97 .. 1.10
WM_GRID = [round(0.65 + 0.01 * k, 2) for k in range(36)]  # 0.65 .. 1.00
MU_BOUNDS = (0.97, 1.10)
WM_BOUNDS = (0.65, 1.00)
LR_GRID_4T = T2.LR_GRID_4T[1:]  # 0.45 .. 0.75 (0.025 steps)
#: Knob-space point: (mu_peak_scale, wheelie_margin, launch_rpm_factor).
NEUTRAL_PT = (1.0, 1.0, None)

FAMILIES = ("neutral", "grip", "margin", "grip+margin", "margin+lr")

REF_TAG = TE.REF_TAG
REF_TARGETS = TE.REF_TARGETS
K5_T60_BAND = TE.K5_T60_BAND
REF_FLAT = TE.REF_FLAT
ROLLOUT_1FT = T2.ROLLOUT_1FT
LITRE_TAGS = T2.LITRE_TAGS
MIN_FIT_ROWS = T2.MIN_FIT_ROWS
MIN_FIT_GROUPS = T2.MIN_FIT_GROUPS
EPS_S = T2.EPS_S
THIN_DONORS = T2.THIN_DONORS
HEADLINE = T2.HEADLINE
#: Round-3 report criterion: NO litre bike traction-limited above 2nd gear.
TRACTION_ABOVE_2ND_MAX = 0.0
#: A rider-mass / sea-level inversion this small (s) is classed as
#: wheelie-ballast physics (the extra mass lowers / shifts the system CoG and
#: raises the 1st-gear ceiling) — reported, not gated.
BALLAST_MAX_S = 0.010


def theta_of(tag: str, mu: float, wm: float, lr=None) -> dict:
    t = TE.neutral_theta(tag)
    t["mu_peak_scale"] = mu
    t["wheelie_margin"] = wm
    t["launch_rpm_factor"] = lr
    return t


def family_points(fam: str, tag: str) -> list:
    if fam == "neutral":
        return [NEUTRAL_PT]
    if fam == "grip":
        return [(mu, 1.0, None) for mu in MU_GRID]
    if fam == "margin":
        return [(1.0, wm, None) for wm in WM_GRID]
    if fam == "grip+margin+lr":  # gate-escape family (see cmd_tune)
        if tag == "two_stroke":
            return []
        return [(mu, wm, lr) for mu in MU_GRID for wm in WM_GRID for lr in LR_GRID_4T]
    if fam == "margin+lr":
        if tag == "two_stroke":  # a two-stroke launches on its pipe
            return []
        return [(1.0, wm, lr) for wm in WM_GRID for lr in LR_GRID_4T]
    return [(mu, wm, None) for mu in MU_GRID for wm in WM_GRID]


def ndist(pt) -> float:
    """Distance from physical neutrality (tie-break inside the flat band):
    a grip change costs twice a margin change (rated rubber is the stronger
    prior; the margin is the mechanism this round adds); any set launch rpm
    costs more than either."""
    mu, wm, lr = pt
    d = 2.0 * abs(mu - 1.0) + abs(1.0 - wm)
    if lr is not None:
        d += 1.0 + abs(lr - 0.55)
    return d


def complexity_pt(pt) -> int:
    mu, wm, lr = pt
    return int(mu != 1.0) + int(wm != 1.0) + int(lr is not None)


def _pkey(pt) -> str:
    return f"{pt[0]:.2f}|{pt[1]:.2f}|{pt[2]}"


def insample_profile(tag: str, rows: list, grid: dict, lam: float) -> dict:
    idx = list(range(len(rows)))
    out = {}
    for pt, res in grid.items():
        q = TE.objective_parts([rows[j] for j in idx], [res[j] for j in idx], lam)
        out[_pkey(pt)] = {
            "J": round(q["J"], 4),
            "et_w_mean_abs": round(q["et_w_mean_abs"], 4),
            "et_w_bias": round(q["et_w_bias"], 4),
            "trap_w_bias": round(q["trap_w_bias"], 2),
        }
    return out


def _grid_job(job):
    tag, pt = job
    TE.set_knobs(tag, theta_of(tag, *pt))
    try:
        res = [
            sim_quarter(TE.cfg_for(r["i"]), r["rollout_m"])[:3]
            for r in ROWS_BY_TAG[tag]
        ]
    finally:
        TE.set_knobs(tag, None)
    return (tag, pt, res)


ROWS_BY_TAG = T2.ROWS_BY_TAG
sim_quarter = T2.sim_quarter
pool_map = T2.pool_map

# swap the round-2 tuner's knob-space hooks (module globals, read at call time)
T2.theta_of = theta_of
T2.family_points = family_points
T2.ndist = ndist
T2.complexity_pt = complexity_pt
T2.FAMILIES = FAMILIES
T2.MU_GRID = MU_GRID
T2.TRACTION_ABOVE_2ND_MAX = TRACTION_ABOVE_2ND_MAX


# ── gate (round 3: dry + rider mass, default env + sea level) ───────────────


def _gate_worker_all(i):
    return T2.mono()._catalog_worker((i, False, False, T2.mono().ALL_PROBES))


def gate_catalog_all(indices, procs: int) -> dict:
    """Every probe of scripts/check_mass_monotonicity.py on ``indices`` with
    the current in-process knobs: the dry-mass default-env gate (hard) and
    the rider / sea-level probes (reported)."""
    rows = pool_map(_gate_worker_all, list(indices), procs)
    summ = T2.mono().summarize_catalog(rows)
    out = {
        "n": summ["n"],
        "errors": summ["errors"],
        "dry_default_env": {
            "inversions": summ["inversions"],
            "inverted": [
                {
                    "name": r["name"],
                    "cluster": r["cluster"],
                    "kind": r["inversions"],
                    "et": r["et"],
                    "et_plus10": r["et_plus"],
                    "et_minus10": r["et_minus"],
                }
                for r in rows
                if r.get("inversions")
            ],
        },
        "probes": {},
    }
    for probe, ps in summ["probes"].items():
        big = [x for x in ps["inverted"] if x["size_s"] >= BALLAST_MAX_S]
        out["probes"][probe] = {
            "n": ps["n"],
            "inversions": ps["inversions"],
            "n_at_or_above_ballast_max": len(big),
            "ballast_max_s": BALLAST_MAX_S,
            "max_size_s": max((x["size_s"] for x in ps["inverted"]), default=0.0),
            "inverted": ps["inverted"],
        }
    return out


def round3_gate(procs: int) -> dict:
    by_tag = T2.catalog_indices_by_tag()
    litre = sorted(i for t in LITRE_TAGS for i in by_tag.get(t, []))
    t0 = time.time()
    g_l = T2.gate_catalog(litre, procs, with_fractions=True)
    allg = gate_catalog_all(range(len(CTX["specs"])), procs)
    refs = T2.mono().probe_references(with_fractions=True)
    ref_out = {}
    for label, block in refs.items():
        base = next(r for r in block["rows"] if r["delta_kg"] == 0.0)
        ref_out[label] = {
            "monotone": block["monotone"],
            "et_by_delta_kg": {str(r["delta_kg"]): r["et"] for r in block["rows"]},
            "probes": block.get("probes"),
            "traction_frac_gear3plus": T2.traction_above_2nd(base.get("limiters")),
            "limiters": base.get("limiters"),
        }
    return {
        "references": ref_out,
        "catalog": {
            "n": allg["n"],
            "inversions": allg["dry_default_env"]["inversions"],
            "errors": allg["errors"],
            "inverted": allg["dry_default_env"]["inverted"],
        },
        "probes": allg["probes"],
        "litre_traction_above_2nd": g_l["traction_above_2nd"],
        "wall_s": round(time.time() - t0, 1),
    }


# ── measure ─────────────────────────────────────────────────────────────────


def cmd_measure(args) -> None:
    TE.setup_root(args.root)
    if args.labels_json:
        CTX["benchmarks"] = T2.load_head(args.labels_json)[0]
        CTX["labels_from"] = args.labels_json
    if args.neutral:
        thetas = T2.neutral_thetas()
    else:
        thetas = T2.load_thetas(args.thetas)
    if args.uniform_margin is not None:
        thetas = {
            tag: {**(thetas.get(tag) or TE.current_theta(tag))}
            for tag in CTX["cp"]._PROFILES
        }
        for tag in thetas:
            thetas[tag]["wheelie_margin"] = args.uniform_margin
    res = T2.measure(
        T2.SCORINGS,
        args.procs,
        thetas=thetas,
        head=T2.load_head(args.head_json),
        topspeed=not args.no_topspeed,
        gate=False,
    )
    if args.gate:
        res["mass_gate"] = round3_gate(args.procs)
    res["residual_sd"] = residual_sd(res)
    Path(args.out).write_text(json.dumps(res, indent=1))
    b = T2._brief(res) if not args.gate else _brief3(res)
    print(json.dumps(b, indent=1))


def _brief3(res: dict) -> dict:
    g = res.pop("mass_gate")
    b = T2._brief(res)
    res["mass_gate"] = g
    b["mass_gate"] = {
        "refs_monotone": {k: v["monotone"] for k, v in g["references"].items()},
        "catalog_dry_inversions": g["catalog"]["inversions"],
        "inverted": [x["name"] for x in g["catalog"]["inverted"]],
        "probes": {
            k: (v["inversions"], round(v["max_size_s"] * 1000, 2))
            for k, v in g["probes"].items()
        },
        "litre_traction_above_2nd_max": g["litre_traction_above_2nd"]["max"],
        "litre_traction_above_2nd_n_any": g["litre_traction_above_2nd"]["n_any"],
    }
    return b


def _wsd(rows) -> float | None:
    """Weighted standard deviation of the ET residual (s)."""
    rs = [r for r in rows if r.get("delta") is not None]
    W = sum(r["weight"] for r in rs)
    if W <= 0 or len(rs) < 2:
        return None
    m = sum(r["weight"] * r["delta"] for r in rs) / W
    return round(math.sqrt(sum(r["weight"] * (r["delta"] - m) ** 2 for r in rs) / W), 4)


def residual_sd(res: dict) -> dict:
    """Weighted residual SD per cluster — current taxonomy and HEAD's
    membership — for every scoring (the scatter a constant cannot fix)."""
    out = {}
    for name, sc in res["scorings"].items():
        rows = sc["rows"]
        by_cur: dict = {}
        by_head: dict = {}
        for r in rows:
            by_cur.setdefault(r["cluster"], []).append(r)
            by_head.setdefault(
                r.get("head_cluster") or "(not in HEAD catalog)", []
            ).append(r)
        out[name] = {
            "overall": _wsd(rows),
            "clusters": {k: _wsd(v) for k, v in sorted(by_cur.items())},
            "clusters_head_membership": {
                k: _wsd(v) for k, v in sorted(by_head.items())
            },
        }
    return out


# ── tuning ──────────────────────────────────────────────────────────────────


def no_worse_than_neutral(tried) -> dict | None:
    neu = next((t for t in tried if t["point"] == list(NEUTRAL_PT)), None)
    if neu is None:
        return None
    base = {x["name"]: x for x in neu["inverted"]}
    for t in tried:
        ok = all(
            x["name"] in base
            and set(x["kind"]) <= set(base[x["name"]]["kind"])
            and T2._inv_size(x) <= T2._inv_size(base[x["name"]]) + 1e-12
            for x in t["inverted"]
        )
        if ok:
            return t
    return None


#: Selection-gate mode. "full": dry hard + rider / sea-level probes below
#: BALLAST_MAX_S; when no grid / escape point passes, a cluster falls back
#: to the hard dry-mass gate alone ("full" False) and the record says so.
GATE_MODE = {"full": True}


def _rows_verdict(rows) -> dict:
    """Round-3 SELECTION gate over catalog-worker rows (all probes): the dry-
    mass default-env probe must be inversion-free with no negative step
    (hard), and the rider-mass / sea-level probes may only show inversions
    smaller than BALLAST_MAX_S (wheelie-ballast sized)."""
    margins = [
        (min(r["et_plus"] - r["et"], r["et"] - r["et_minus"]), r["name"])
        for r in rows
        if None not in (r.get("et"), r.get("et_plus"), r.get("et_minus"))
    ]
    inverted = []
    for r in rows:
        if r.get("inversions"):
            inverted.append(
                {
                    "name": r["name"],
                    "cluster": r.get("cluster"),
                    "kind": r["inversions"],
                    "et": r["et"],
                    "et_plus10": r["et_plus"],
                    "et_minus10": r["et_minus"],
                }
            )
        for probe in ("rider", "sea_dry", "sea_rider") if GATE_MODE["full"] else ():
            q = r.get(f"probe_{probe}")
            if not q or not q["inversions"]:
                continue
            size = max(
                (q["et"] - q["et_plus"])
                if None not in (q["et"], q["et_plus"])
                else 0.0,
                (q["et_minus"] - q["et"])
                if None not in (q["et"], q["et_minus"])
                else 0.0,
            )
            if size >= BALLAST_MAX_S:
                inverted.append(
                    {
                        "name": r["name"],
                        "cluster": r.get("cluster"),
                        "kind": q["inversions"],
                        "probe": probe,
                        "size_s": round(size, 5),
                        "et": q["et"],
                        "et_plus10": q["et_plus"],
                        "et_minus10": q["et_minus"],
                    }
                )
    worst = min(margins) if margins else (None, None)
    return {
        "n": len(rows),
        "inversions": len(inverted),
        "errors": sum(1 for r in rows if "error" in r),
        "min_margin_s": round(worst[0], 5) if worst[0] is not None else None,
        "min_margin_bike": worst[1],
        "inverted": inverted,
    }


def _gate_rows_worker(i):
    return T2.mono()._catalog_worker((i, False, False, T2.mono().ALL_PROBES))


def gate_selection(indices, procs) -> dict:
    return _rows_verdict(pool_map(_gate_rows_worker, list(indices), procs))


def _gate_tag(tag, pt, procs, cat_by_tag):
    TE.set_knobs(tag, theta_of(tag, *pt))
    try:
        return gate_selection(cat_by_tag.get(tag, []), procs)
    finally:
        TE.set_knobs(tag, None)


def _tried(fam, pt, g):
    return {
        "family": fam,
        "point": list(pt),
        "inversions": g["inversions"],
        "inverted": g["inverted"],
        "min_margin_s": g["min_margin_s"],
        "min_margin_bike": g["min_margin_bike"],
    }


def _screen_indices(tag, tried, cat_idx) -> list:
    """Catalog bikes of the cluster that inverted on any tried candidate."""
    names = {x["name"] for t in tried for x in t["inverted"]}
    specs = CTX["specs"]
    return [
        i for i in cat_idx if f"{specs[i].manufacturer} {specs[i].model_name}" in names
    ]


def _feas_job(job):
    """(point, ok under the full round-3 gate, ok under the dry gate, min dry
    step). ``probes`` ("dry",) = the cheap screen (no rider / sea runs)."""
    tag, pt, idx, probes = job
    TE.set_knobs(tag, theta_of(tag, *pt))
    try:
        rows = [T2.mono()._catalog_worker((i, False, False, probes)) for i in idx]
    finally:
        TE.set_knobs(tag, None)
    GATE_MODE["full"] = False
    try:
        dry = _rows_verdict(rows)
    finally:
        GATE_MODE["full"] = True
    full = _rows_verdict(rows)
    return pt, T2._gate_ok(full), T2._gate_ok(dry), dry["min_margin_s"]


def feasible_points_par(tag, points, screen_idx, cat_idx, procs, gate="full") -> dict:
    """Parallel twin of the round-2 ``feasible_points``: the points whose knob
    set passes the selection gate on the cluster's WHOLE catalog population.
    ``gate`` "full" = the round-3 gate (dry hard + rider / sea-level probes
    below BALLAST_MAX_S), "dry" = the hard dry-mass gate alone. The bikes
    that inverted on a tried candidate are screened first."""
    probes = T2.mono().ALL_PROBES if gate == "full" else ("dry",)
    k = 1 if gate == "full" else 2  # index of the verdict in _feas_job's tuple
    with mp.get_context("fork").Pool(procs) as pool:
        if screen_idx:
            scr = pool.map(
                _feas_job, [(tag, p, screen_idx, probes) for p in points], chunksize=4
            )
            surv = [r[0] for r in scr if r[k]]
        else:
            surv = list(points)
        res = pool.map(
            _feas_job, [(tag, p, cat_idx, probes) for p in surv], chunksize=2
        )
    return {
        "points": {
            r[0]: {"min_margin_s": round(r[3], 5) if r[3] is not None else None}
            for r in res
            if r[k]
        },
        "gate": gate,
        "n_grid": len(points),
        "n_screen_pass": len(surv),
    }


def _add_points(tag, grids, pts, args) -> None:
    pts = [q for q in pts if q not in grids[tag]]
    if not pts:
        return
    with mp.get_context("fork").Pool(args.procs) as pool:
        for _t, pt, res in pool.imap_unordered(
            _grid_job, [(tag, q) for q in pts], chunksize=2
        ):
            grids[tag][pt] = res


def _feasible_with_escape(tag, grids, screen, cat_idx, args, rec) -> dict:
    """Gate-feasible points, in this order: the regular grid under the full
    round-3 gate; the gate ESCAPE — the whole (grip x margin x launch rpm)
    box, the "grip+margin+lr" family admitted ONLY here — under the full
    gate; then, when no point anywhere passes the rider / sea-level probes,
    the regular grid and the escape under the HARD dry-mass gate alone
    (``rec['gate_fallback']``)."""
    regular = list(grids[tag])
    esc = (
        []
        if tag == "two_stroke"
        else [p for p in family_points("grip+margin+lr", tag) if p not in grids[tag]]
    )
    log = []
    for gate in ("full", "dry"):
        for name, pts in (("grid", regular), ("escape", esc)):
            if not pts:
                continue
            f = feasible_points_par(tag, pts, screen, cat_idx, args.procs, gate=gate)
            log.append(
                {
                    "stage": name,
                    "gate": gate,
                    "n_points": len(pts),
                    "n_screen_pass": f["n_screen_pass"],
                    "n_feasible": len(f["points"]),
                }
            )
            print(
                f"  feasible {tag} {name}/{gate}: {len(f['points'])} of {len(pts)}",
                flush=True,
            )
            if f["points"]:
                if name == "escape":
                    _add_points(tag, grids, f["points"], args)
                    T2.FAMILIES = T2.FAMILIES + ("grip+margin+lr",)
                if gate == "dry":
                    rec["gate_fallback"] = (
                        "no grid or escape point passes the rider-mass / "
                        f"sea-level probes (< {BALLAST_MAX_S * 1000:.0f} ms); "
                        "selected on the HARD dry-mass gate alone (the probes "
                        "are reported)"
                    )
                rec["feasibility_log"] = log
                return {
                    "points": f["points"],
                    "n_grid": sum(x["n_points"] for x in log),
                    "n_screen_pass": sum(x["n_screen_pass"] for x in log),
                }
    rec["feasibility_log"] = log
    return {
        "points": {},
        "n_grid": sum(x["n_points"] for x in log),
        "n_screen_pass": sum(x["n_screen_pass"] for x in log),
    }


def cmd_tune(args) -> None:
    TE.setup_root(None)
    rows = T2.bind_rows("epoch", CTX["benchmarks"])
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
        if thin:
            pts = [NEUTRAL_PT]
        else:
            pts = list(
                dict.fromkeys(p for f in FAMILIES for p in family_points(f, tag))
            )
        jobs += [(tag, pt) for pt in pts]
    t0 = time.time()
    grids: dict = {tag: {} for tag in by_tag}
    cache = Path(args.grid_cache) if args.grid_cache else None
    if cache is not None and cache.exists():
        grids = pickle.loads(cache.read_bytes())
    else:
        with mp.get_context("fork").Pool(args.procs) as pool:
            for tag, pt, res in pool.imap_unordered(_grid_job, jobs, chunksize=4):
                grids[tag][pt] = res
        if cache is not None:
            cache.write_bytes(pickle.dumps(grids))
    grid_wall = round(time.time() - t0, 1)
    print(f"grid: {len(jobs)} knob sets, {grid_wall}s", flush=True)

    cat_by_tag = T2.catalog_indices_by_tag()
    clusters = {}
    for tag, rs in sorted(by_tag.items(), key=lambda kv: -len(kv[1])):
        rec = {**info[tag], "k": None}
        rec["neutral_insample"] = TE._r(
            TE.objective_parts(rs, grids[tag][NEUTRAL_PT], args.lam)
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
        # families with no grid point for this tag (2T: margin+lr) drop out
        T2.FAMILIES = tuple(f for f in FAMILIES if family_points(f, tag))
        sel = T2.cv_select(tag, rs, grids[tag], args.lam, args.folds)
        rec.update(sel)
        rec["k"] = args.folds
        rec["insample_grid"] = insample_profile(tag, rs, grids[tag], args.lam)
        tried = []
        chosen = None
        for fam in sel["candidate_order"]:
            pt = tuple(sel["families"][fam]["point"])
            if any(t["point"] == list(pt) for t in tried):
                continue
            g = _gate_tag(tag, pt, args.procs, cat_by_tag)
            tried.append(_tried(fam, pt, g))
            print(
                f"  gate {tag:22} {fam:11} {pt} -> {g['inversions']} inversions, "
                f"min margin {g['min_margin_s']}",
                flush=True,
            )
            if T2._gate_ok(g):
                chosen = (fam, pt)
                break
        rec["gate_tried"] = tried
        if chosen is None:
            cat_idx = cat_by_tag.get(tag, [])
            screen = _screen_indices(tag, tried, cat_idx)
            feas = _feasible_with_escape(tag, grids, screen, cat_idx, args, rec)
            rec["feasible"] = {
                "n_feasible": len(feas["points"]),
                "n_grid": feas["n_grid"],
                "n_screen_pass": feas["n_screen_pass"],
                "points": {
                    _pkey(p): v for p, v in sorted(feas["points"].items(), key=str)
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
                csel = T2.cv_select(
                    tag,
                    rs,
                    grids[tag],
                    args.lam,
                    args.folds,
                    allowed=set(feas["points"]),
                )
                T2.FAMILIES = tuple(f for f in FAMILIES if family_points(f, tag))
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
            f"{tag:22} n={len(rs):3} g={info[tag]['n_groups']:3} "
            f"sel={rec['selected']:11} pt={chosen[1]} "
            + " ".join(
                f"{f}={sel['families'][f]['cv']['J']:.3f}"
                f"(+-{sel['families'][f]['cv_se']:.3f})@{tuple(sel['families'][f]['point'])}"
                for f in sel["families"]
            ),
            flush=True,
        )
    # thin clusters: donor's selected knobs (guarded) or neutral
    for tag, rec in clusters.items():
        if rec.get("selected") != "thin":
            continue
        donor = THIN_DONORS.get(tag)
        th = TE._clean(TE.neutral_theta(tag))
        pt = NEUTRAL_PT
        rec["donor"] = None
        if donor and donor in clusters and clusters[donor].get("theta"):
            dth = dict(clusters[donor]["theta"])
            dth["cd_floor"] = TE.neutral_theta(tag)["cd_floor"]
            dpt = (
                dth["mu_peak_scale"],
                dth["wheelie_margin"],
                dth["launch_rpm_factor"],
            )
            T2._ensure_point(tag, dpt, dth, by_tag[tag], grids)
            j_donor = TE.objective_parts(by_tag[tag], grids[tag][dpt], args.lam)["J"]
            j_neutral = TE.objective_parts(by_tag[tag], grids[tag][pt], args.lam)["J"]
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
        T2._ensure_point(tag, pt, th, by_tag[tag], grids)
        rec["selected_insample"] = TE._r(
            TE.objective_parts(by_tag[tag], grids[tag][pt], args.lam)
        )
        TE.set_knobs(tag, th)
        try:
            g = gate_selection(cat_by_tag.get(tag, []), args.procs)
        finally:
            TE.set_knobs(tag, None)
        rec["gate_tried"] = [_tried("donor" if rec.get("donor") else "neutral", pt, g)]
    for tag in sorted(set(cat_by_tag) - set(clusters) - {REF_TAG}):
        th = TE._clean(TE.neutral_theta(tag))
        TE.set_knobs(tag, th)
        try:
            g = gate_selection(cat_by_tag[tag], args.procs)
        finally:
            TE.set_knobs(tag, None)
        clusters[tag] = {
            "n_rows": 0,
            "n_groups": 0,
            "thin": True,
            "selected": "unbound",
            "theta": th,
            "point": list(NEUTRAL_PT),
            "gate_tried": [{"family": "neutral", "point": list(NEUTRAL_PT), **g}],
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
        "wm_grid": WM_GRID,
        "lr_grid_4t_margin_lr_family": LR_GRID_4T,
        "launch_rpm_factor": (
            "retired as a bias corrector; only the 'margin+lr' family (1-SE / "
            "gate-feasible constrained selection) may set it"
        ),
        "point_order": ["mu_peak_scale", "wheelie_margin", "launch_rpm_factor"],
        "bounds": {
            "mu_peak_scale": MU_BOUNDS,
            "wheelie_margin": WM_BOUNDS,
            "launch_rpm_factor": T2.LR_BOUNDS,
        },
        "families": FAMILIES,
        "ndist": "2*|mu-1| + |1-wm| (+1 + |lr-0.55| if lr set); tie-break inside eps",
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


def ref_eval(mu: float, wm: float) -> dict:
    TE.set_knobs(REF_TAG, theta_of(REF_TAG, mu, wm))
    try:
        row = {"mu_peak_scale": mu, "wheelie_margin": wm}
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
    """Minimax fit of the frozen reference profile over (mu_peak_scale,
    wheelie_margin) in the same physical bounds (launch_rpm_factor None):
    minimise max_i |ET_i - pub_i| / tol_i; within REF_FLAT of the optimum
    the most neutral point wins; the winner must keep the references
    mass-monotone (dry -20..+20 kg)."""
    TE.setup_root(None)
    scan = [ref_eval(mu, wm) for wm in WM_GRID for mu in MU_GRID]
    m_star = min(r["max_norm_miss"] for r in scan)
    flat = [r for r in scan if r["max_norm_miss"] <= m_star + REF_FLAT]
    order = sorted(
        flat,
        key=lambda r: (
            ndist((r["mu_peak_scale"], r["wheelie_margin"], None)),
            r["max_norm_miss"],
        ),
    )
    gate_log = []
    best = None
    for cand in order:
        TE.set_knobs(
            REF_TAG, theta_of(REF_TAG, cand["mu_peak_scale"], cand["wheelie_margin"])
        )
        try:
            g = T2.gate_references(with_fractions=True)
        finally:
            TE.set_knobs(REF_TAG, None)
        ok = all(v["monotone"] for v in g.values())
        gate_log.append(
            {
                "mu_peak_scale": cand["mu_peak_scale"],
                "wheelie_margin": cand["wheelie_margin"],
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
    best_by_wm = {}
    for wm in WM_GRID:
        cand = [r for r in scan if r["wheelie_margin"] == wm]
        best_by_wm[f"{wm:.2f}"] = min(
            cand, key=lambda r: (r["max_norm_miss"], abs(r["mu_peak_scale"] - 1.0))
        )
    neutral = next(
        r for r in scan if r["mu_peak_scale"] == 1.0 and r["wheelie_margin"] == 1.0
    )
    out = {
        "tag": REF_TAG,
        "targets": {
            k: {"et_s": v[0], "trap_kmh": v[1], "tol_s": v[2], "source": v[3]}
            for k, v in REF_TARGETS.items()
        },
        "k5_t60_band_s": K5_T60_BAND,
        "k5_t60_band_note": (
            "the old 1.8-2.1 s test band was timed from FIRST MOTION; both the "
            "beam (1-ft rollout) and the first-motion 60 ft are reported"
        ),
        "bounds": {"mu_peak_scale": MU_BOUNDS, "wheelie_margin": WM_BOUNDS},
        "objective": (
            "minimax: min over (mu_peak_scale, wheelie_margin) inside the physical "
            "bounds of max_i |ET_i - pub_i| / tol_i (tol = tests/test_validation.py "
            "bands); within REF_FLAT of the optimum the most neutral point wins; "
            "the winner must keep all three references mass-monotone (-20..+20 kg)"
        ),
        "flat_band": REF_FLAT,
        "neutral": neutral,
        "best": best,
        "gate_log": gate_log,
        "best_by_wheelie_margin": best_by_wm,
        "scan": scan,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    show = {
        k: {
            kk: (
                round(v[kk]["et_s"], 4),
                round(v[kk]["t60_s"], 3),
                round(v[kk]["t60_first_motion_s"], 3),
                round(v[kk]["trap_kmh"], 1),
            )
            for kk in REF_TARGETS
        }
        | {
            "max_norm_miss": round(v["max_norm_miss"], 3),
            "pt": (v["mu_peak_scale"], v["wheelie_margin"]),
        }
        for k, v in {"neutral": neutral, "best": best}.items()
        if v
    }
    print(json.dumps(show, indent=1))


# ── report ──────────────────────────────────────────────────────────────────

STAGES = {
    "head": "HEAD 0bd0ea2: physics + data + knobs as published 2026-08-08",
    "r2_tuned": "round 2 (1c487f0): round-2 physics + data + round-2 knobs (rejected)",
    "neutral": "round-3 physics (wheelie_margin) + round-2 data, neutral knobs",
    "tuned": "round-3 physics + round-2 data + round-3 knobs (this report)",
}


def _decomposition(inp: dict) -> dict:
    out = {}
    for metric in ("a_epoch_current_row", "c_legacy_head_row"):
        chain = [
            ("head", "HEAD model"),
            ("r2_tuned", "round-2 physics + data + round-2 knobs"),
            ("neutral", "round-3 neutral (== round-2 physics, neutral knobs)"),
            ("tuned", "+ round-3 retune (wheelie_margin + grip)"),
        ]
        prev = None
        steps = []
        for name, desc in chain:
            if name not in inp or metric not in inp[name]["scorings"]:
                continue
            v = T2._wd(inp[name], metric)
            steps.append(
                {
                    "stage": name,
                    "desc": desc,
                    "w_mean_abs": v,
                    "w_bias": T2._wb(inp[name], metric),
                    "delta_w_mean_abs": None if prev is None else round(v - prev, 4),
                }
            )
            prev = v
        out[metric] = {"metric": metric, "chain": steps}
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
            "wm_grid",
            "launch_rpm_factor",
            "bounds",
            "families",
            "ndist",
            "n_grid_sims",
        )
        if k in tune
    }
    out["gate_min_margin_s"] = T2.GATE_MIN_MARGIN_S
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
            ig = c["insample_grid"]
            # the margin profile at rated grip and the grip profile at no
            # margin (lr None); the full grid is in the scratch tune output
            rec["insample_profile_margin_at_mu_1.00"] = {
                k.split("|")[1]: v
                for k, v in ig.items()
                if k.startswith("1.00|") and k.endswith("|None")
            }
            rec["insample_profile_grip_at_wm_1.00"] = {
                k.split("|")[0]: v for k, v in ig.items() if k.endswith("|1.00|None")
            }
        cl[tag] = rec
    out["clusters"] = cl
    return out


def _compact_refs(r: dict) -> dict:
    keep = (
        "tag",
        "targets",
        "k5_t60_band_s",
        "k5_t60_band_note",
        "bounds",
        "objective",
        "flat_band",
        "neutral",
        "best",
        "gate_log",
    )
    out = {k: r[k] for k in keep if k in r}
    out["best_by_wheelie_margin"] = {
        k: {
            "mu_peak_scale": v["mu_peak_scale"],
            "max_norm_miss": round(v["max_norm_miss"], 4),
            "et": {kk: round(v[kk]["et_s"], 4) for kk in REF_TARGETS},
        }
        for k, v in r.get("best_by_wheelie_margin", {}).items()
    }
    return out


def _bands_vs_head(t: dict, head: dict) -> dict:
    out = {}
    for name in ("a_epoch_current_row", "c_legacy_head_row"):
        tb = t["scorings"][name]["bands"]
        hb = head["scorings"]["c_legacy_head_row"]["bands"]
        out[name] = {
            k: {"tuned": tb.get(k), "head_published_c": hb.get(k)}
            for k in ("within_0.10s", "within_0.20s", "within_0.50s")
        }
    return out


def _residual_sd_vs_head(inp: dict) -> dict:
    """Weighted residual SD per cluster on metric (c), HEAD membership."""
    out = {}
    for name in ("head", "r2_tuned", "neutral", "tuned"):
        if name in inp:
            sd = inp[name].get("residual_sd") or residual_sd(inp[name])
            c = sd.get("c_legacy_head_row")
            if c is not None:
                out[name] = {
                    "overall": c["overall"],
                    "clusters_head_membership": c["clusters_head_membership"],
                }
    return out


_R2_ACCEPTANCE = T2._acceptance


def _acceptance3(t: dict, head: dict, refs: dict | None) -> dict:
    acc = _R2_ACCEPTANCE(t, head, refs)
    g = t.get("mass_gate", {})
    c = t["scorings"]["c_legacy_head_row"]
    a = t["scorings"][HEADLINE]
    hb = head["scorings"]["c_legacy_head_row"]["bands"]
    acc["trap_bias_kmh"]["pass_below_5"] = abs(c["trap_overall"]["w_bias_kmh"]) < 5.0
    acc["topspeed_mean_abs_kmh"]["pass_below_15"] = (
        acc["topspeed_mean_abs_kmh"]["value"] or 99
    ) < 15.0
    acc["mass_probes"] = {
        k: {
            "inversions": v["inversions"],
            "max_size_ms": round(v["max_size_s"] * 1000, 2),
            "n_at_or_above_10ms": v["n_at_or_above_ballast_max"],
            "bikes": [
                f"{x['name']} ({x['cluster']}) {x['size_s'] * 1000:.2f} ms"
                for x in v["inverted"]
            ],
        }
        for k, v in g.get("probes", {}).items()
    }
    acc["mass_probes_references"] = {
        k: {p: pv["monotone"] for p, pv in (v.get("probes") or {}).items()}
        for k, v in g.get("references", {}).items()
    }
    ltr = g.get("litre_traction_above_2nd", {})
    acc["litre_traction_above_2nd"] = {
        "max_share_gear3plus": ltr.get("max"),
        "n_any": ltr.get("n_any"),
        "pass_none": (ltr.get("n_any") or 0) == 0,
    }
    acc["within_0.20s"] = {
        "c": c["bands"]["within_0.20s"],
        "a": a["bands"]["within_0.20s"],
        "head_published_c": hb["within_0.20s"],
    }
    acc["within_0.10s"] = {
        "c": c["bands"]["within_0.10s"],
        "a": a["bands"]["within_0.10s"],
        "head_published_c": hb["within_0.10s"],
    }
    acc["k5_t60"]["band_note"] = "the 1.8-2.1 s band is a FIRST-MOTION band"
    acc["k5_t60"]["first_motion_in_band"] = (
        K5_T60_BAND[0] < t["references"]["K5"]["t60_first_motion_s"] < K5_T60_BAND[1]
    )
    return acc


def cmd_report(args) -> None:
    T2.STAGES = STAGES
    T2._decomposition = _decomposition
    T2._compact_tune = _compact_tune
    T2._compact_refs = _compact_refs
    T2._acceptance = _acceptance3
    T2.cmd_report(args)
    out = json.loads(Path(args.out).read_text())
    inp = {}
    for kv in args.inputs:
        name, path = kv.split("=", 1)
        inp[name] = json.loads(Path(path).read_text())
    out["_doc"] = (
        "2026-10 physics epoch ROUND 3 retune (scripts/tune_epoch3_2026_11_03.py): "
        "round-2 physics + ONE new knob, CategoryProfile.wheelie_margin (the share "
        "of the system wheelie ceiling the rider holds in 1st gear; resolved-config "
        "schema 5), launch_rpm_factor retired. Same structure as "
        "reports/acc_epoch2_2026_10_29.json: top-level 'clusters'/'overall' use the "
        "epoch headline (round-2 labels, epoch binding + weights, per-row timing); "
        "'headline' carries (a), (b) legacy rules on the same labels and (c) the "
        "EXACT published 2026-08-08 metric (HEAD 0bd0ea2 labels, legacy binding + "
        "weights). Trap in km/h (sim - published), 60 ft in s."
    )
    out["bands_vs_head"] = _bands_vs_head(inp["tuned"], inp["head"])
    out["residual_sd_vs_head"] = _residual_sd_vs_head(inp)
    out["residual_sd"] = inp["tuned"].get("residual_sd")
    for k, v in inp.items():
        if k.startswith("alt_") and k in out.get("conservative_alternatives", {}):
            sd = (v.get("residual_sd") or residual_sd(v)).get("c_legacy_head_row", {})
            alt = out["conservative_alternatives"][k]
            alt["residual_sd_c_head_membership"] = sd.get("clusters_head_membership")
            alt["mass_probes"] = {
                pk: {
                    "inversions": pv["inversions"],
                    "max_size_ms": round(pv["max_size_s"] * 1000, 2),
                    "bikes": [
                        f"{x['name']} ({x['cluster']}) {x['size_s'] * 1000:.2f} ms"
                        for x in pv["inverted"]
                    ],
                }
                for pk, pv in v.get("mass_gate", {}).get("probes", {}).items()
            }
            alt["clusters_c"] = {
                cl: T2._st(cv)
                for cl, cv in v["scorings"]["c_legacy_head_row"]["clusters"].items()
            }
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out} (round-3 extras added)")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--out", required=True)
    m.add_argument("--root", default=None)
    m.add_argument("--thetas", default=None)
    m.add_argument("--neutral", action="store_true")
    m.add_argument("--uniform-margin", type=float, default=None)
    m.add_argument("--head-json", default=None)
    m.add_argument("--labels-json", default=None)
    m.add_argument("--no-topspeed", action="store_true")
    m.add_argument("--gate", action="store_true")
    m.add_argument("--procs", type=int, default=mp.cpu_count())
    t = sub.add_parser("tune")
    t.add_argument("--out", required=True)
    t.add_argument("--lam", type=float, default=0.01)
    t.add_argument("--folds", type=int, default=5)
    t.add_argument("--grid-cache", default=None)
    t.add_argument("--procs", type=int, default=mp.cpu_count())
    r = sub.add_parser("refs")
    r.add_argument("--out", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--out", required=True)
    rp.add_argument("--head-published", required=True)
    rp.add_argument("--inputs", nargs="+", required=True)
    rp.add_argument("--notes", default=None)
    args = ap.parse_args(argv)
    {
        "measure": cmd_measure,
        "tune": cmd_tune,
        "refs": cmd_refs,
        "report": cmd_report,
    }[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
