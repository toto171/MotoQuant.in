"""Surrogate v2 training-data generator — catalog-wide, resumable, numpy-only.

The v1 numpy surrogate was trained on Sobol perturbations of the K5 reference
config only, so 261/501 catalog bikes sat outside its FEATURE_BOUNDS envelope
at STOCK and the Build Optimizer fell back to full RK4 sims (minutes per job).

v2 samples the real catalog instead:
  * one STOCK sample for every current bike_configs row (production
    db_row_to_config path — exactly what /api/* simulates),
  * dense local PERTURBATIONS around a cluster-stratified subset of base
    bikes, covering the Build Optimizer's reachable space (parts scale
    power/torque + dyno curve together, trim mass, tweak aero/tires/final
    drive; venues move altitude),
  * a held-out EVAL set of catalog bikes (stock + a "+20% power / -8 kg"
    build) that never enters training.

Resumable by design (Cowork sandbox kills shells at 45 s): `plan` writes a
deterministic task list; each `run --budget N` call completes as many pending
tasks as fit in N seconds (multiprocessing across cores) and appends an
atomic shard; `merge` folds shards into one training .npz.

Usage:
    python scripts/surrogate_v2_gen.py plan   [--workdir /tmp/mq/surr-data]
    python scripts/surrogate_v2_gen.py run    [--budget 30] [--workdir ...]
    python scripts/surrogate_v2_gen.py status [--workdir ...]
    python scripts/surrogate_v2_gen.py merge  [--workdir ...] [--out artifacts/surrogate/motoquant_surrogate_v2.npz]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SEED = 42
N_EVAL_BIKES = 25
N_PERTURB_BASES = 120
PERTURB_PER_BASE = 28
PERTURB_PER_OTHER = 12  # light coverage around every non-base, non-eval bike
# Proof/anchor bikes that must be perturbation bases (never eval-held-out).
ANCHOR_NAME_TOKENS = ("hayabusa", "gsx-r 1000", "yzf-r1", "duke 390", "yzf-r15")

DB_PATH = str(Path(__file__).resolve().parent.parent / "motoquant.db")


# ──────────────────────────────────────────────────────────────────────
# Config loading (production path) + perturbation
# ──────────────────────────────────────────────────────────────────────
def _load_rows():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT bc.*, bm.id AS bmid, bm.model_name, bm.category,
                  bm.displacement_cc, bm.peak_power_hp AS bm_hp,
                  m.name AS manufacturer
           FROM bike_configs bc
           JOIN bike_models bm ON bc.bike_model_id = bm.id
           JOIN manufacturers m ON bm.manufacturer_id = m.id
           WHERE bc.is_current = 1"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _config_for_row(row):
    from motoquant.database.bridge import db_row_to_config

    return db_row_to_config(row, name=f"{row['manufacturer']} {row['model_name']}")


def _cluster_for_row(row, cfg):
    from motoquant.category_profiles import derive_category_tag

    return derive_category_tag(
        manufacturer=row["manufacturer"],
        model_name=row["model_name"],
        displacement_cc=row.get("displacement_cc"),
        peak_power_hp=row.get("bm_hp") or cfg.engine.peak_power_hp,
        stroke_type=getattr(cfg.engine, "stroke_type", 4),
        category=row.get("category"),
        cylinders=getattr(cfg.engine, "cylinder_count", None),
    )


def apply_knobs(cfg, knobs):
    """Mutate a deep copy of cfg the way parts/venues actually reach it."""
    from motoquant.models import DynoCurve

    c = copy.deepcopy(cfg)
    s = float(knobs.get("power_scale", 1.0))
    if abs(s - 1.0) > 1e-9:
        c.engine.peak_power_hp *= s
        c.engine.peak_torque_nm *= s
        if c.engine.dyno_curve is not None:
            dc = c.engine.dyno_curve
            c.engine.dyno_curve = DynoCurve(
                rpm=dc.rpm.copy(),
                torque_nm=dc.torque_nm * s,
                is_at_wheel=dc.is_at_wheel,
            )
    md = float(knobs.get("mass_delta_kg", 0.0))
    if abs(md) > 1e-9:
        c.chassis.dry_mass_kg = max(80.0, c.chassis.dry_mass_kg + md)
    c.aero.cd *= float(knobs.get("cd_scale", 1.0))
    c.aero.frontal_area_m2 *= float(knobs.get("area_scale", 1.0))
    c.tires.mu_peak = min(1.90, c.tires.mu_peak * float(knobs.get("mu_scale", 1.0)))
    c.tires.rear_rolling_radius_m *= float(knobs.get("radius_scale", 1.0))
    fs = float(knobs.get("final_scale", 1.0))
    if abs(fs - 1.0) > 1e-9:
        eff = c.drivetrain.final_ratio * fs
        # physics reads the final_ratio property (sprockets win when set);
        # zero the teeth so the scaled ratio is what the sim actually uses.
        c.drivetrain.final_drive_ratio = eff
        c.drivetrain.front_sprocket = 0
        c.drivetrain.rear_sprocket = 0
    if "altitude_m" in knobs:
        c.environment.altitude_m = float(knobs["altitude_m"])
    if "reaction_ms" in knobs:
        c.staging.reaction_time_ms = float(knobs["reaction_ms"])
    return c


def _draw_knobs(rng):
    u = rng.random()
    if u < 0.10:
        s = rng.uniform(0.92, 1.0)
    elif u < 0.50:
        s = rng.uniform(1.0, 1.15)
    elif u < 0.80:
        s = rng.uniform(1.15, 1.35)
    else:
        s = rng.uniform(1.35, 1.62)
    return {
        "power_scale": round(s, 4),
        "mass_delta_kg": round(rng.uniform(-25.0, 10.0), 2),
        "cd_scale": round(rng.uniform(0.85, 1.15), 4),
        "area_scale": round(rng.uniform(0.93, 1.07), 4),
        "mu_scale": round(rng.uniform(0.96, 1.12), 4),
        "radius_scale": round(rng.uniform(0.97, 1.03), 4),
        "final_scale": round(rng.uniform(0.87, 1.18), 4),
        "altitude_m": round(
            rng.uniform(0.0, 1300.0)
            if rng.random() < 0.7
            else rng.uniform(1300.0, 2500.0),
            1,
        ),
        "reaction_ms": round(rng.uniform(50.0, 550.0), 1),
    }


# ──────────────────────────────────────────────────────────────────────
# plan
# ──────────────────────────────────────────────────────────────────────
def cmd_plan(workdir: Path):
    from motoquant.analysis.surrogate_data import (
        BASE_FEATURE_NAMES,
        _extract_nominal_features,
    )

    rows = _load_rows()
    rng = np.random.default_rng(SEED)
    bikes = []
    for row in sorted(rows, key=lambda r: r["bmid"]):
        try:
            cfg = _config_for_row(row)
            cluster = _cluster_for_row(row, cfg)
            feat = _extract_nominal_features(cfg)
            bikes.append(
                {
                    "bmid": row["bmid"],
                    "name": f"{row['manufacturer']} {row['model_name']}",
                    "cluster": cluster,
                    "stock_base": [float(feat[k]) for k in BASE_FEATURE_NAMES],
                }
            )
        except Exception as exc:  # noqa: BLE001 — skip unloadable rows, log them
            print(f"  ! skip bmid={row['bmid']}: {exc}")

    by_cluster: dict[str, list[dict]] = {}
    for b in bikes:
        by_cluster.setdefault(b["cluster"], []).append(b)

    def _is_anchor(b):
        n = b["name"].lower()
        return any(t in n for t in ANCHOR_NAME_TOKENS)

    # eval picks: stratified across clusters, never anchors
    eval_ids: set[int] = set()
    cluster_names = sorted(by_cluster)
    quota = {
        c: max(1, round(N_EVAL_BIKES * len(by_cluster[c]) / len(bikes)))
        for c in cluster_names
    }
    while sum(quota.values()) > N_EVAL_BIKES:
        big = max(quota, key=lambda c: quota[c])
        quota[big] -= 1
    for c in cluster_names:
        cands = [b for b in by_cluster[c] if not _is_anchor(b)]
        rng.shuffle(cands)
        for b in cands[: quota[c]]:
            eval_ids.add(b["bmid"])

    # perturbation bases: stratified, excludes eval, force-includes anchors
    base_ids: set[int] = {b["bmid"] for b in bikes if _is_anchor(b)}
    bquota = {
        c: max(3, round(N_PERTURB_BASES * len(by_cluster[c]) / len(bikes)))
        for c in cluster_names
    }
    for c in cluster_names:
        cands = [
            b
            for b in by_cluster[c]
            if b["bmid"] not in eval_ids and b["bmid"] not in base_ids
        ]
        rng.shuffle(cands)
        for b in cands[: bquota[c]]:
            base_ids.add(b["bmid"])

    tasks = []
    tid = 0
    for b in bikes:  # stock pass first — envelope/eval anchors land early
        kind = "stock_eval" if b["bmid"] in eval_ids else "stock"
        tasks.append({"tid": tid, "bmid": b["bmid"], "kind": kind, "knobs": {}})
        tid += 1
    for b in bikes:
        if b["bmid"] in eval_ids:
            tasks.append(
                {
                    "tid": tid,
                    "bmid": b["bmid"],
                    "kind": "mod_eval",
                    "knobs": {"power_scale": 1.20, "mass_delta_kg": -8.0},
                }
            )
            tid += 1
    # interleave perturbations round-robin so partial runs stay balanced
    base_list = [b for b in bikes if b["bmid"] in base_ids]
    streams = []
    for b in base_list:
        brng = np.random.default_rng(SEED + b["bmid"])
        streams.append([_draw_knobs(brng) for _ in range(PERTURB_PER_BASE)])
    for k in range(PERTURB_PER_BASE):
        for b, st in zip(base_list, streams):
            tasks.append(
                {"tid": tid, "bmid": b["bmid"], "kind": "perturb", "knobs": st[k]}
            )
            tid += 1
    # light perturbation coverage around EVERY remaining bike (neither base
    # nor eval) so no catalog bike is stock-only in training. Disjoint rng
    # stream (SEED + 7_000_000 + bmid) keeps base-bike draws unchanged —
    # this reproduces the v2/v2.1 datasets exactly (the v2 run did this via
    # a sandbox-side plan extension that never got committed).
    others = [
        b for b in bikes if b["bmid"] not in base_ids and b["bmid"] not in eval_ids
    ]
    ostreams = []
    for b in others:
        orng = np.random.default_rng(SEED + 7_000_000 + b["bmid"])
        ostreams.append([_draw_knobs(orng) for _ in range(PERTURB_PER_OTHER)])
    for k in range(PERTURB_PER_OTHER):
        for b, st in zip(others, ostreams):
            tasks.append(
                {"tid": tid, "bmid": b["bmid"], "kind": "perturb", "knobs": st[k]}
            )
            tid += 1

    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "plan.json").write_text(
        json.dumps(
            {
                "seed": SEED,
                "bikes": bikes,
                "eval_ids": sorted(eval_ids),
                "base_ids": sorted(base_ids),
                "tasks": tasks,
            }
        )
    )
    nclusters = {c: len(v) for c, v in sorted(by_cluster.items())}
    print(
        f"plan: {len(bikes)} bikes, {len(tasks)} tasks "
        f"({len(eval_ids)} eval bikes, {len(base_ids)} perturb bases)"
    )
    print("clusters:", nclusters)


# ──────────────────────────────────────────────────────────────────────
# run (resumable chunk)
# ──────────────────────────────────────────────────────────────────────
_W_ROWS = None


def _winit():
    global _W_ROWS
    _W_ROWS = {r["bmid"]: r for r in _load_rows()}


def _wrun(task):
    from motoquant.analysis.surrogate_data import (
        FEATURE_NAMES,
        _extract_nominal_features,
    )
    from motoquant.physics import MotoQuantEngine

    try:
        row = _W_ROWS[task["bmid"]]
        cfg = apply_knobs(_config_for_row(row), task["knobs"])
        feat = _extract_nominal_features(cfg)
        fvec = [float(feat[k]) for k in FEATURE_NAMES]
        res = MotoQuantEngine(cfg).run()
        et, trap = res.time_quarter, res.speed_quarter
        ok = (
            et is not None
            and trap is not None
            and np.isfinite(et)
            and np.isfinite(trap)
            and 4.0 < et < 35.0
            and 5.0 < trap < 120.0
        )
        return (task["tid"], fvec, float(et or 0.0), float(trap or 0.0), bool(ok))
    except Exception:  # noqa: BLE001 — a failed sim is just a dead task
        return (task["tid"], [0.0] * 21, 0.0, 0.0, False)


def _done_tids(workdir: Path) -> set[int]:
    done = set()
    for f in sorted((workdir / "shards").glob("shard_*.npz")):
        try:
            done.update(np.load(f)["tid"].tolist())
        except Exception:  # noqa: BLE001 — half-written shard from a killed call
            print(f"  ! unreadable shard {f.name} — ignoring")
    return done


def cmd_run(workdir: Path, budget: float):
    import multiprocessing as mp

    t0 = time.perf_counter()
    plan = json.loads((workdir / "plan.json").read_text())
    done = _done_tids(workdir)
    pending = [t for t in plan["tasks"] if t["tid"] not in done]
    if not pending:
        print("ALL DONE")
        return
    nproc = max(1, os.cpu_count() or 1)
    out = []
    with mp.Pool(nproc, initializer=_winit) as pool:
        for r in pool.imap_unordered(_wrun, pending, chunksize=1):
            out.append(r)
            if time.perf_counter() - t0 > budget:
                pool.terminate()
                break
    if out:
        shard = workdir / "shards" / f"shard_{int(time.time() * 1000)}.npz"
        tmp = shard.with_suffix(".tmp.npz")
        np.savez(
            tmp,
            tid=np.array([r[0] for r in out], dtype=np.int64),
            X=np.array([r[1] for r in out], dtype=np.float64),
            et=np.array([r[2] for r in out], dtype=np.float64),
            trap=np.array([r[3] for r in out], dtype=np.float64),
            ok=np.array([r[4] for r in out], dtype=bool),
        )
        os.replace(tmp, shard)
    n_done = len(done) + len(out)
    print(
        f"chunk: +{len(out)} ({sum(1 for r in out if r[4])} ok) in "
        f"{time.perf_counter() - t0:.1f}s | total {n_done}/{len(plan['tasks'])}"
    )


def cmd_status(workdir: Path):
    plan = json.loads((workdir / "plan.json").read_text())
    done = _done_tids(workdir)
    by_kind: dict[str, list[int]] = {}
    for t in plan["tasks"]:
        by_kind.setdefault(t["kind"], []).append(t["tid"])
    for k, tids in sorted(by_kind.items()):
        nd = sum(1 for x in tids if x in done)
        print(f"  {k:<10} {nd}/{len(tids)}")
    print(f"TOTAL {len(done)}/{len(plan['tasks'])}")


# ──────────────────────────────────────────────────────────────────────
# merge
# ──────────────────────────────────────────────────────────────────────
def cmd_merge(workdir: Path, out: Path):
    from motoquant.analysis.surrogate_data import (
        EXTRA_FEATURE_NAMES,
        FEATURE_NAMES,
        _extras_from_config,
    )

    plan = json.loads((workdir / "plan.json").read_text())
    tmeta = {t["tid"]: t for t in plan["tasks"]}
    bike_of = {b["bmid"]: b for b in plan["bikes"]}

    # Shards written before the 26-feature schema landed carry 21-wide rows
    # (a strict prefix); complete them with the real per-bike structural
    # extras — they are config constants, untouched by every knob.
    extras_cache: dict[int, list[float]] = {}

    def _full_width(bmid: int, fv):
        if len(fv) == len(FEATURE_NAMES):
            return list(fv)
        if bmid not in extras_cache:
            row = _MERGE_ROWS[bmid]
            ex = _extras_from_config(_config_for_row(row))
            extras_cache[bmid] = [ex[k] for k in EXTRA_FEATURE_NAMES]
        return list(fv) + extras_cache[bmid]

    global _MERGE_ROWS
    _MERGE_ROWS = {r["bmid"]: r for r in _load_rows()}
    seen: set[int] = set()
    rows = []
    for f in sorted((workdir / "shards").glob("shard_*.npz")):
        try:
            d = np.load(f)
        except Exception:  # noqa: BLE001
            continue
        for i in range(len(d["tid"])):
            tid = int(d["tid"][i])
            if tid in seen or not bool(d["ok"][i]):
                continue
            seen.add(tid)
            t = tmeta[tid]
            rows.append(
                (
                    tid,
                    t["bmid"],
                    t["kind"],
                    bike_of[t["bmid"]]["cluster"],
                    _full_width(t["bmid"], d["X"][i]),
                    float(d["et"][i]),
                    float(d["trap"][i]),
                )
            )
    rows.sort(key=lambda r: r[0])
    X = np.array([r[4] for r in rows], dtype=np.float64)
    np.savez_compressed(
        out,
        X=X.astype(np.float32),
        y_et=np.array([r[5] for r in rows], dtype=np.float32),
        y_trap=np.array([r[6] for r in rows], dtype=np.float32),
        feature_names=np.array(FEATURE_NAMES),
        kind=np.array([r[2] for r in rows]),
        bmid=np.array([r[1] for r in rows], dtype=np.int64),
        cluster=np.array([r[3] for r in rows]),
        stock_base_all=np.array(
            [b["stock_base"] for b in plan["bikes"]], dtype=np.float64
        ),
        meta=np.array([len(rows), SEED, 0.0]),
    )
    kinds = {}
    for r in rows:
        kinds[r[2]] = kinds.get(r[2], 0) + 1
    print(f"merged {len(rows)} ok rows -> {out}  kinds={kinds}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["plan", "run", "status", "merge"])
    ap.add_argument("--workdir", default="/tmp/mq/surr-data")
    ap.add_argument("--budget", type=float, default=30.0)
    ap.add_argument("--out", default="artifacts/surrogate/motoquant_surrogate_v2.npz")
    a = ap.parse_args()
    wd = Path(a.workdir)
    (wd / "shards").mkdir(parents=True, exist_ok=True)
    if a.cmd == "plan":
        cmd_plan(wd)
    elif a.cmd == "run":
        cmd_run(wd, a.budget)
    elif a.cmd == "status":
        cmd_status(wd)
    else:
        cmd_merge(wd, Path(a.out))


if __name__ == "__main__":
    main()
