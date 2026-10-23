#!/usr/bin/env python3
"""
Native-core parity harness — proves the Rust engine reproduces the Python
reference (motoquant/physics.py) on every path that matters.

Sections (each case runs Python AND native in the same worker process and
compares every SimResult channel element-by-element, plus splits/ET/trap):

  references  the 3 pinned bikes (K5 / R1 / Hayabusa): fixed, adaptive, top speed
  catalog     EVERY current bike_config in motoquant.db (db_row_to_config), fixed dt
  adaptive    every catalog bike again with use_adaptive_dt=True
  topspeed    run_top_speed() on a catalog sample (Python's own plateau logic)
  stress      boosted (turbo / SC roots / SC centrifugal / N2O), curve-less 2T and
              4T curves, every clutch type, every track surface, head/tail/cross
              wind + ram air, gradient, speed limiters, at-wheel vs crank dyno,
              extreme rider mass, every category profile, patched profile knobs,
              dt variants, time caps, a never-locking clutch (adaptive array growth)
  bench       serial wall-time: Python vs native (resolve+run) vs pure Rust run

Target: worst |dET| <= 1e-9 s everywhere (the same bit-identical bar as
scripts/check_baselines.py). Exit 0 on pass, 1 on any parity failure.

    python scripts/check_native_parity.py                   # full run
    python scripts/check_native_parity.py --quick           # refs + 40-bike sample
    python scripts/check_native_parity.py --report PATH     # JSON report path
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import math
import multiprocessing as mp
import os
import platform
import sqlite3
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import motoquant as mq  # noqa: E402
from motoquant import native  # noqa: E402
from motoquant.category_profiles import get_profile  # noqa: E402
from motoquant.database.bridge import db_row_to_config  # noqa: E402
from motoquant.models import DynoCurve  # noqa: E402
from motoquant.physics import MotoQuantEngine  # noqa: E402

TOL_S = 1e-9
CHANNELS = (
    "t", "x", "v", "a", "rpm", "gear", "slip", "traction_pct", "N_front",
    "N_rear", "F_drive", "F_drag", "F_rr", "T_tire", "T_clutch", "P_boost",
    "power_kw", "r_eff",
)  # fmt: skip
SPLITS = (
    "time_60ft", "speed_60ft", "time_330ft", "speed_330ft", "time_eighth",
    "speed_eighth", "time_1000ft", "speed_1000ft", "time_quarter",
    "speed_quarter", "finished_quarter", "max_distance_m", "elapsed_time_s",
)  # fmt: skip
REFS = ("gsxr1000_k5", "yzfr1_4c8", "hayabusa_gen1")
PROFILE_TAGS = (
    "litre_sport_195p", "litre_sport_600_1000", "sport_twin_600_1300",
    "mid_twin_500_700", "mid_twin_300_500", "single_300_500",
    "small_i4_screamer", "entry_200_300", "entry_150_200", "two_stroke",
    "cruiser_1300p", "other", "unknown",
)  # fmt: skip


# ═══════════════════════════════════════════
# Catalog loading
# ═══════════════════════════════════════════


def load_catalog_rows(db_path: Path) -> list[tuple[str, dict]]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT bc.*, bm.model_name AS _model_name, bm.year_from AS _year_from "
        "FROM bike_configs bc JOIN bike_models bm ON bm.id = bc.bike_model_id "
        "WHERE bc.is_current = 1 ORDER BY bc.bike_model_id"
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        d = dict(r)
        label = f"{d.pop('_model_name')}|{d.pop('_year_from')}#{d['bike_model_id']}"
        out.append((label, d))
    return out


def cfg_from_row(row: dict, label: str):
    return db_row_to_config(row, name=label.split("|")[0])


# ═══════════════════════════════════════════
# Comparison core (runs inside workers)
# ═══════════════════════════════════════════


def _cmp_simresults(rp, rn) -> dict:
    out = {"len_py": len(rp.t), "len_native": len(rn.t)}
    n = min(len(rp.t), len(rn.t))
    worst = {}
    first_div = None
    for ch in CHANNELS:
        a = np.asarray(getattr(rp, ch))[:n].astype(np.float64)
        b = np.asarray(getattr(rn, ch))[:n].astype(np.float64)
        neq = ~((a == b) | (np.isnan(a) & np.isnan(b)))
        if neq.any():
            i = int(np.flatnonzero(neq)[0])
            if first_div is None or i < first_div[0]:
                first_div = (i, ch)
            with np.errstate(invalid="ignore"):
                worst[ch] = float(np.nanmax(np.abs(a - b)))
    out["channel_max_abs"] = worst
    out["first_divergence"] = (
        None if first_div is None else {"step": first_div[0], "channel": first_div[1]}
    )
    out["channels_identical"] = (not worst) and len(rp.t) == len(rn.t)
    sp = {}
    for k in SPLITS:
        pv, nv = getattr(rp, k), getattr(rn, k)
        if isinstance(pv, (bool, np.bool_)):
            sp[k] = bool(pv) == bool(nv)
        else:
            sp[k] = float(pv) == float(nv)
    out["splits_identical"] = all(sp.values())
    out["dET"] = abs(float(rp.time_quarter) - float(rn.time_quarter))
    out["dtrap"] = abs(float(rp.speed_quarter) - float(rn.speed_quarter))
    out["et_py"] = float(rp.time_quarter)
    out["et_native"] = float(rn.time_quarter)
    out["finished"] = bool(rp.finished_quarter)
    out["dt_final_equal"] = float(rp.dt) == float(rn.dt)
    return out


def _patch_profile(eng, patch):
    if patch:
        eng._profile = dataclasses.replace(eng._profile, **patch)


def run_case(case: dict) -> dict:
    """Execute one case dict → result dict. Never raises."""
    label = case["label"]
    mode = case.get("mode", "fixed")
    t0 = time.perf_counter()
    res = {"label": label, "section": case["section"], "mode": mode}
    try:
        cfg = case["cfg"] if "cfg" in case else cfg_from_row(case["row"], label)
        dt = case.get("dt", 0.001)
        kwargs = case.get("kwargs", {})
        patch = case.get("profile_patch")
        py_exc = nat_exc = None
        rp = rn = None

        py_eng = MotoQuantEngine(copy.deepcopy(cfg), dt=dt)
        _patch_profile(py_eng, patch)
        nat_eng = native.NativeEngine(copy.deepcopy(cfg), dt=dt)
        _patch_profile(nat_eng, patch)

        tp = time.perf_counter()
        try:
            if mode == "topspeed":
                rp = py_eng.run_top_speed(**kwargs)
            else:
                rp = py_eng.run(use_adaptive_dt=(mode == "adaptive"), **kwargs)
        except Exception as exc:  # noqa: BLE001
            py_exc = f"{type(exc).__name__}: {exc}"
        tn = time.perf_counter()
        try:
            if mode == "topspeed":
                rn = nat_eng.run_top_speed(**kwargs)
            else:
                rn = nat_eng.run(use_adaptive_dt=(mode == "adaptive"), **kwargs)
        except Exception as exc:  # noqa: BLE001
            nat_exc = f"{type(exc).__name__}: {exc}"
        te = time.perf_counter()
        res["t_py_s"] = tn - tp
        res["t_native_s"] = te - tn

        if py_exc or nat_exc:
            res["py_exception"] = py_exc
            res["native_exception"] = nat_exc
            same = (
                py_exc is not None
                and nat_exc is not None
                and py_exc.split(":")[0] == nat_exc.split(":")[0]
            )
            res["ok"] = same
            res["dET"] = 0.0 if same else math.inf
            return res

        if mode == "topspeed":
            c = _cmp_simresults(rp.full_sim, rn.full_sim)
            ts = {}
            for f in (
                "terminal_velocity_ms",
                "time_to_terminal_s",
                "distance_to_terminal_m",
                "terminal_power_kw",
                "terminal_gear",
                "terminal_rpm",
                "reached_plateau",
            ):
                ts[f] = getattr(rp, f) == getattr(rn, f)
            ts["lsr_splits"] = rp.lsr_splits == rn.lsr_splits
            c["topspeed_fields_identical"] = all(ts.values())
            c["d_terminal_v"] = abs(rp.terminal_velocity_ms - rn.terminal_velocity_ms)
            c["terminal_kmh"] = rp.terminal_velocity_kmh
            c["ok"] = (
                c["channels_identical"]
                and c["topspeed_fields_identical"]
                and c["d_terminal_v"] <= TOL_S
            )
        else:
            c = _cmp_simresults(rp, rn)
            c["ok"] = c["dET"] <= TOL_S and c["dtrap"] <= TOL_S
        res.update(c)
    except Exception as exc:  # noqa: BLE001 — harness bug, report loudly
        res["ok"] = False
        res["harness_error"] = f"{type(exc).__name__}: {exc}"
        res["traceback"] = traceback.format_exc()
    res["wall_s"] = time.perf_counter() - t0
    return res


# ═══════════════════════════════════════════
# Stress variants
# ═══════════════════════════════════════════


def _mut(cfg, fn):
    c = copy.deepcopy(cfg)
    fn(c)
    return c


def _set(path_vals):
    def fn(c):
        for path, val in path_vals.items():
            obj = c
            parts = path.split(".")
            for p in parts[:-1]:
                obj = getattr(obj, p)
            setattr(obj, parts[-1], val)

    return fn


def build_stress_cases(catalog: list[tuple[str, dict]]) -> list[dict]:
    busa = mq.hayabusa_gen1()
    k5 = mq.gsxr1000_k5()

    # Pick representative catalog bikes by predicate.
    picks = {}
    for label, row in catalog:
        eng = json.loads(row["engine_params"] or "{}")
        drv = json.loads(row["drivetrain_params"] or "{}")
        if "two_stroke" not in picks and eng.get("stroke_type") == 2:
            picks["two_stroke"] = (label, row)
        if "limiter" not in picks and drv.get("speed_limiter_kmh"):
            picks["limiter"] = (label, row)
        if "shaft" not in picks and drv.get("drive_type") == "shaft":
            picks["shaft"] = (label, row)
        if "small" not in picks and (eng.get("displacement_cc") or 999) < 200 and eng.get(
            "stroke_type", 4
        ) == 4:
            picks["small"] = (label, row)
        if "crank_dyno" not in picks and (eng.get("dyno_curve") or {}).get(
            "is_at_wheel"
        ) is False:
            picks["crank_dyno"] = (label, row)
    bases = {"busa": ("Hayabusa Gen1 (ref)", busa), "k5": ("GSX-R K5 (ref)", k5)}
    for k, (label, row) in picks.items():
        bases[k] = (label, cfg_from_row(row, label))

    cases: list[dict] = []

    def add(label, cfg, mode="fixed", **extra):
        cases.append({"section": "stress", "label": label, "cfg": cfg, "mode": mode, **extra})

    def both(label, cfg, **extra):
        add(label + " [fixed]", cfg, "fixed", **extra)
        add(label + " [adaptive]", cfg, "adaptive", **extra)

    # ── forced induction ──
    fi_variants = {
        "turbo 1.0bar a2a": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 1.0,
            "forced_induction.turbo_spool_time_s": 0.6,
            "forced_induction.prespool_boost_bar": 0.3,
            "forced_induction.intercooler_type": "a2a",
            "forced_induction.intercooler_effectiveness": 0.7,
        },
        "turbo 1.6bar no-IC": {
            "forced_induction.boost_type": "turbo",
            "forced_induction.target_boost_bar": 1.6,
            "forced_induction.turbo_spool_time_s": 0.03,
        },
        "sc_roots 0.5bar": {
            "forced_induction.boost_type": "sc_roots",
            "forced_induction.target_boost_bar": 0.5,
        },
        "sc_centrifugal 0.8bar": {
            "forced_induction.boost_type": "sc_centrifugal",
            "forced_induction.target_boost_bar": 0.8,
        },
        "n2o 1x50hp": {
            "forced_induction.boost_type": "n2o",
            "forced_induction.n2o_hp_per_stage": 50.0,
            "forced_induction.n2o_stages": 1,
        },
        "n2o 2x75hp ramp0.05": {
            "forced_induction.boost_type": "n2o",
            "forced_induction.n2o_hp_per_stage": 75.0,
            "forced_induction.n2o_stages": 2,
            "forced_induction.n2o_ramp_duration_s": 0.05,
        },
    }
    for bname in ("busa", "small", "two_stroke"):
        if bname not in bases:
            continue
        blabel, bcfg = bases[bname]
        for vname, pv in fi_variants.items():
            both(f"{bname}: {vname}", _mut(bcfg, _set(pv)))

    # ── clutch types / thermal ──
    for bname in ("busa", "small"):
        if bname not in bases:
            continue
        _, bcfg = bases[bname]
        for vname, pv in {
            "slider engage 3000": {"clutch.clutch_type": "slider", "clutch.engage_rpm": 3000.0},
            "slider engage 6500": {"clutch.clutch_type": "slider", "clutch.engage_rpm": 6500.0},
            "multistage": {"clutch.clutch_type": "multistage"},
            "slipper": {"clutch.clutch_type": "slipper"},
            "lockup fade 90C": {"clutch.fade_temp_c": 90.0, "clutch.thermal_mass_jk": 60.0},
            "weak clutch": {"clutch.spring_preload_n": 250.0},
        }.items():
            both(f"{bname}: clutch {vname}", _mut(bcfg, _set(pv)))

    # ── never-locking clutch: stalls to max_time (adaptive array growth) ──
    stall = _mut(busa, _set({"clutch.clutch_type": "slider", "clutch.engage_rpm": 99999.0}))
    both("busa: slider never engages (stall to max_time)", stall)

    # ── track surfaces ──
    for surf in ("concrete", "prepped", "wet", "damp", "dusty", "salt", "dry_lake_bed", "gravel?"):
        both(f"busa: surface {surf}", _mut(busa, _set({"environment.track_surface": surf})))

    # ── wind / ram air / gradient / environment ──
    for vname, pv in {
        "headwind 6m/s": {"environment.wind_speed_ms": 6.0, "environment.wind_direction_deg": 0.0},
        "tailwind 6m/s": {"environment.wind_speed_ms": 6.0, "environment.wind_direction_deg": 180.0},
        "crosswind 45deg": {"environment.wind_speed_ms": 9.0, "environment.wind_direction_deg": 45.0},
        "ram air 0.6 + headwind": {
            "aero.ram_air_efficiency": 0.6,
            "environment.wind_speed_ms": 4.0,
        },
        "ram air 0.8": {"aero.ram_air_efficiency": 0.8},
        "uphill 3%": {"environment.track_gradient_pct": 3.0},
        "downhill 3%": {"environment.track_gradient_pct": -3.0},
        "altitude 2200m 40C 80%RH": {
            "environment.altitude_m": 2200.0,
            "environment.ambient_temp_c": 40.0,
            "environment.relative_humidity_pct": 80.0,
            "environment.track_temp_c": 58.0,
        },
        "cold 4C": {"environment.ambient_temp_c": 4.0, "environment.track_temp_c": 6.0},
        "track_temp None (ambient+5 path)": {"environment.track_temp_c": None},
        "VHT prep fresh": {"tires.track_prep_type": "vht", "tires.track_prep_passes": 3},
        "rubber prep": {"tires.track_prep_type": "rubber_buildup", "tires.track_prep_passes": 50},
    }.items():
        both(f"busa: {vname}", _mut(busa, _set(pv)))

    # ── speed limiters ──
    both("busa: limiter 140 km/h (engages in the 1/4)", _mut(busa, _set({"drivetrain.speed_limiter_kmh": 140.0})))
    both("busa: limiter 0 (treated as none)", _mut(busa, _set({"drivetrain.speed_limiter_kmh": 0.0})))
    add("busa: limiter 140 km/h topspeed", _mut(busa, _set({"drivetrain.speed_limiter_kmh": 140.0})), "topspeed")
    if "limiter" in bases:
        lab, bc = bases["limiter"]
        add(f"catalog limiter bike {lab} topspeed", bc, "topspeed")
        both(f"catalog limiter bike {lab}", bc)

    # ── dyno: at-wheel vs crank, curve-less fallbacks ──
    def flip_wheel(c):
        dc = c.engine.dyno_curve
        c.engine.dyno_curve = DynoCurve(rpm=dc.rpm, torque_nm=dc.torque_nm, is_at_wheel=not dc.is_at_wheel)

    for bname in ("busa", "k5", "crank_dyno"):
        if bname in bases and bases[bname][1].engine.dyno_curve is not None:
            both(f"{bname}: dyno is_at_wheel flipped", _mut(bases[bname][1], flip_wheel))
    both("busa: no dyno (parabolic 4T)", _mut(busa, _set({"engine.dyno_curve": None})))
    if "two_stroke" in bases:
        _, tcfg = bases["two_stroke"]
        for vname, pv in {
            "2T curve-less default": {"engine.dyno_curve": None},
            "2T curve-less powervalve": {"engine.dyno_curve": None, "engine.powervalve": True},
            "2T curve-less 1cyl <200cc": {
                "engine.dyno_curve": None,
                "engine.cylinder_count": 1,
                "engine.displacement_cc": 124.0,
                "engine.powervalve": False,
            },
            "2T curve-less 1cyl 250cc": {
                "engine.dyno_curve": None,
                "engine.cylinder_count": 1,
                "engine.displacement_cc": 249.0,
                "engine.powervalve": False,
            },
            "2T curve-less 2cyl": {"engine.dyno_curve": None, "engine.cylinder_count": 2, "engine.powervalve": False},
            "2T curve-less 3cyl": {"engine.dyno_curve": None, "engine.cylinder_count": 3, "engine.powervalve": False},
            "2T curve-less tuned None": {"engine.dyno_curve": None, "engine.tuned_rpm": None},
        }.items():
            both(vname, _mut(tcfg, _set(pv)))

    # ── rider mass, chassis, aero, parasitic, engine temp ──
    for vname, pv in {
        "rider 40kg": {"chassis.rider_mass_kg": 40.0},
        "rider 150kg": {"chassis.rider_mass_kg": 150.0},
        "wheelie bar": {"wheelie.wheelie_bar": True, "wheelie.bar_length_mm": 600.0},
        "counter-rotating crank": {"engine.counter_rotating": True},
        "high CoG short wheelbase": {"chassis.cog_height_mm": 720.0, "chassis.wheelbase_mm": 1300.0},
        "belly pan + upright": {"aero.belly_pan": True, "aero.rider_position": "upright"},
        "race crouch, high lift": {"aero.rider_position": "race", "aero.cl": 0.3},
        "no alternator, e-pump, -5hp parasitic": {
            "parasitic.alternator_present": False,
            "parasitic.water_pump_electric": True,
            "parasitic.parasitic_delta_hp": 5.0,
        },
        "coolant 60C": {"engine.coolant_temp_c": 60.0},
        "coolant 105C": {"engine.coolant_temp_c": 105.0},
        "fuel 60 g/s": {"chassis.fuel_consumption_gs": 60.0},
        "chain -> shaft": {"drivetrain.drive_type": "shaft"},
        "two-step 9500": {"staging.two_step": True, "staging.launch_rpm": 9500.0},
        "tuck 0s": {"rider.tuck_transition_time_s": 0.0},
        "reversion-prone tire": {"tires.reversion_temp_c": 45.0, "tires.burnout_end_temp_c": 90.0},
    }.items():
        both(f"busa: {vname}", _mut(busa, _set(pv)))
    for bname in ("shaft", "small", "two_stroke", "crank_dyno"):
        if bname in bases:
            lab, bc = bases[bname]
            both(f"{bname} base: {lab}", bc)

    # ── every category profile on two different bikes ──
    for tag in PROFILE_TAGS + (None,):
        for bname in ("busa", "small"):
            if bname in bases:
                both(f"{bname}: category_tag={tag}", _mut(bases[bname][1], _set({"category_tag": tag})))

    # ── patched profile knobs (launch_rpm_factor, over-clutch on a litre bike) ──
    both("busa: profile launch_rpm_factor=0.6", copy.deepcopy(busa), profile_patch={"launch_rpm_factor": 0.6})
    both(
        "busa: profile over-clutch 0.4/300/floor1.0",
        copy.deepcopy(busa),
        profile_patch={"over_clutch_factor": 0.4, "max_engine_decel_rads2": 300.0, "launch_floor_factor": 1.0},
    )

    # ── dt / horizon variants ──
    add("busa: dt 0.5ms", copy.deepcopy(busa), "fixed", dt=0.0005)
    add("busa: dt 2ms", copy.deepcopy(busa), "fixed", dt=0.002)
    add("busa: dt 2ms adaptive", copy.deepcopy(busa), "adaptive", dt=0.002)
    both("busa: max_time 4s (time cap)", copy.deepcopy(busa), kwargs={"max_time": 4.0})
    both("busa: distance 1000m", copy.deepcopy(busa), kwargs={"distance": 1000.0, "max_time": 60.0})
    both("busa: distance 60ft", copy.deepcopy(busa), kwargs={"distance": 18.288})
    add("busa: run_top_speed custom window", copy.deepcopy(busa), "topspeed",
        kwargs={"plateau_accel": 0.2, "plateau_window_s": 0.5, "max_time": 60.0})
    both("busa: distance 0 (both raise)", copy.deepcopy(busa), kwargs={"distance": 0.0})
    return cases


# ═══════════════════════════════════════════
# Benchmark (serial, main process)
# ═══════════════════════════════════════════


def bench(catalog, n_bikes: int = 20, repeats: int = 3) -> dict:
    mc = native._require_core()
    cfgs = [("K5", mq.gsxr1000_k5()), ("R1", mq.yzfr1_4c8()), ("Busa", mq.hayabusa_gen1())]
    step = max(1, len(catalog) // n_bikes)
    for label, row in catalog[::step][:n_bikes]:
        cfgs.append((label, cfg_from_row(row, label)))
    rows = []
    for adaptive in (False, True):
        tp = tn = tr = 0.0
        steps = 0
        for _, cfg in cfgs:
            best_p = best_n = best_r = math.inf
            payload = native.resolved_json(native.resolve_config(cfg))
            for _ in range(repeats):
                t0 = time.perf_counter()
                MotoQuantEngine(cfg).run(use_adaptive_dt=adaptive)
                t1 = time.perf_counter()
                native.run_native(cfg, use_adaptive_dt=adaptive)
                t2 = time.perf_counter()
                out = mc.simulate(payload, 402.336, 26.0, adaptive, False)
                t3 = time.perf_counter()
                best_p = min(best_p, t1 - t0)
                best_n = min(best_n, t2 - t1)
                best_r = min(best_r, t3 - t2)
            tp += best_p
            tn += best_n
            tr += best_r
            steps += out["steps"]
        k = len(cfgs)
        rows.append(
            {
                "mode": "adaptive" if adaptive else "fixed",
                "bikes": k,
                "python_ms_per_sim": 1000 * tp / k,
                "native_end_to_end_ms_per_sim": 1000 * tn / k,
                "native_rust_only_ms_per_sim": 1000 * tr / k,
                "speedup_end_to_end": tp / tn,
                "speedup_rust_only": tp / tr,
                "mean_steps": steps / k,
            }
        )
    # Resolve cost alone (Python side of the native path).
    t0 = time.perf_counter()
    for _, cfg in cfgs:
        native.resolve_config(cfg)
    rows.append({"mode": "resolve_only", "ms_per_config": 1000 * (time.perf_counter() - t0) / len(cfgs)})
    return {"cases": rows, "note": "best-of-%d wall time, serial, single core" % repeats}


# ═══════════════════════════════════════════
# Driver
# ═══════════════════════════════════════════


def summarize(results: list[dict]) -> dict:
    out = {}
    for sec in sorted({r["section"] for r in results}):
        rs = [r for r in results if r["section"] == sec]
        dets = [r.get("dET", 0.0) for r in rs if "dET" in r]
        dtraps = [r.get("dtrap", 0.0) for r in rs if "dtrap" in r]
        out[sec] = {
            "cases": len(rs),
            "ok": sum(1 for r in rs if r.get("ok")),
            "failed": [r["label"] + f" ({r.get('mode')})" for r in rs if not r.get("ok")],
            "worst_dET_s": max(dets) if dets else 0.0,
            "worst_dtrap_ms": max(dtraps) if dtraps else 0.0,
            "over_tol": sum(1 for d in dets if d > TOL_S),
            "channels_bit_identical": sum(1 for r in rs if r.get("channels_identical")),
            "both_raised": sum(1 for r in rs if r.get("py_exception") and r.get("ok")),
            "py_time_s": sum(r.get("t_py_s", 0.0) for r in rs),
            "native_time_s": sum(r.get("t_native_s", 0.0) for r in rs),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="refs + a 40-bike sample (CI-sized)")
    ap.add_argument("--topspeed-sample", type=int, default=80, help="catalog bikes for top-speed mode (0 = all)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--no-bench", action="store_true")
    ap.add_argument("--db", default=str(ROOT / "motoquant.db"))
    ap.add_argument("--report", default=str(ROOT / "reports" / "native_parity_2026-10-23.json"))
    args = ap.parse_args()

    if not native.available():
        print("FAIL: motoquant_core not importable — run `make native` first.", file=sys.stderr)
        return 2
    info = native.native_info()
    print(f"native core {info.get('version')}  schema {info['schema']}  exp_impl={info.get('exp_impl')}  exact={info.get('exact')}")

    catalog = load_catalog_rows(Path(args.db))
    if args.quick:
        step = max(1, len(catalog) // 40)
        catalog_run = catalog[::step][:40]
    else:
        catalog_run = catalog

    cases: list[dict] = []
    for f in REFS:
        cfg = getattr(mq, f)()
        for mode in ("fixed", "adaptive", "topspeed"):
            cases.append({"section": "references", "label": f, "cfg": cfg, "mode": mode})
    for label, row in catalog_run:
        cases.append({"section": "catalog", "label": label, "row": row, "mode": "fixed"})
    for label, row in catalog_run:
        cases.append({"section": "adaptive", "label": label, "row": row, "mode": "adaptive"})
    ts = catalog_run if (args.topspeed_sample == 0 or args.quick) else catalog_run[:: max(1, len(catalog_run) // args.topspeed_sample)]
    if args.quick:
        ts = ts[:8]
    for label, row in ts:
        cases.append({"section": "topspeed", "label": label, "row": row, "mode": "topspeed"})
    stress = build_stress_cases(catalog)
    if args.quick:
        stress = stress[::6]
    cases.extend(stress)

    print(f"running {len(cases)} cases on {args.workers} workers ...", flush=True)
    t0 = time.perf_counter()
    ctx = mp.get_context("fork")
    results = []
    with ctx.Pool(args.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(run_case, cases, chunksize=2), 1):
            results.append(r)
            if not r.get("ok"):
                print(f"  MISMATCH [{r['section']}] {r['label']} ({r['mode']}): "
                      f"dET={r.get('dET')} first_div={r.get('first_divergence')} "
                      f"py_exc={r.get('py_exception')} nat_exc={r.get('native_exception')} "
                      f"err={r.get('harness_error')}", flush=True)
            if i % 100 == 0:
                print(f"  {i}/{len(cases)} done ({time.perf_counter() - t0:.0f}s)", flush=True)
    elapsed = time.perf_counter() - t0

    summary = summarize(results)
    worst = max((r.get("dET", 0.0) for r in results), default=0.0)
    worst_trap = max((r.get("dtrap", 0.0) for r in results), default=0.0)
    n_fail = sum(1 for r in results if not r.get("ok"))
    n_bit = sum(1 for r in results if r.get("channels_identical"))
    print()
    for sec, s in summary.items():
        print(f"  {sec:11s} {s['ok']:4d}/{s['cases']:<4d} ok  worst|dET|={s['worst_dET_s']:.3e}s  "
              f"over-tol={s['over_tol']}  bit-identical={s['channels_bit_identical']}  "
              f"py={s['py_time_s']:.1f}s native={s['native_time_s']:.1f}s")
    print(f"\n  ALL: {len(results) - n_fail}/{len(results)} ok, worst |dET| = {worst:.3e} s, "
          f"worst |dtrap| = {worst_trap:.3e} m/s, channel-bit-identical {n_bit}/{len(results)} "
          f"({elapsed:.0f}s)")

    report = {
        "generated": "2026-10-23",
        "tolerance_s": TOL_S,
        "host": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "native": info,
        "elapsed_s": elapsed,
        "summary": summary,
        "worst_dET_s": worst,
        "worst_dtrap_ms": worst_trap,
        "cases_total": len(results),
        "cases_failed": n_fail,
        "channels_bit_identical": n_bit,
        "results": sorted(
            [{k: v for k, v in r.items() if k != "traceback" or not r.get("ok")} for r in results],
            key=lambda r: (r["section"], r["label"], r["mode"]),
        ),
    }
    if not args.no_bench:
        print("\n  benchmarking (serial) ...", flush=True)
        report["bench"] = bench(catalog)
        for row in report["bench"]["cases"]:
            print("   ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(f"\n  report -> {os.path.relpath(args.report, ROOT)}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
