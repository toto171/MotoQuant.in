#!/usr/bin/env python3
"""
Mass-monotonicity probe — "more mass is never faster" (2026-10 epoch, round 2).

A heavier bike with the same engine, rubber and geometry must not run a
quicker quarter mile. The round-1 retune broke that invariant: sub-1.0 grip
scales left litre bikes traction-limited for most of the run, where
``a = (mu*N_r - F_aero - F_rr) / m_eff`` RISES with chassis mass (the rotating
inertia does not scale with it), so the pinned K5 got faster as dry mass rose
126 -> 186 kg. This script is the reusable gate the physics agent, the tuner
and CI use to catch that class of regression.

What it measures (through ``engine_select.make_engine`` — the Rust core when
it is built and current, else the Python reference; the two are bit-identical):

* the three pinned references at dry mass -20/-10/0/+10/+20 kg — ET, 60 ft
  and trap at each step, flagged when ET is not strictly increasing;
* every ``ALL_KNOWN_BIKES`` spec via ``spec_to_bike_config`` at -10 / 0 /
  +10 kg dry mass — an inversion is ``ET(+10) < ET(0) - tol`` or
  ``ET(-10) > ET(0) + tol`` (tol 1e-4 s);
* per-gear limiter fractions on the stock run: the share of integration steps
  in each gear that are traction-limited (``traction_pct`` == 100, the rear
  tyre's force cap binds) and wheelie-limited (the net acceleration sits on
  ``max_accel_before_wheelie``).

``--neutral`` re-runs everything with every CategoryProfile grip / launch knob
set neutral (``mu_peak_scale`` 1.0, ``mu_peak_override`` None,
``launch_rpm_factor`` None, no over-clutch, no launch floor) through an
in-process override of ``category_profiles._PROFILES`` — the physics with no
fitted knobs at all. Use :func:`neutral_profiles` as a context manager from
other scripts.

    python scripts/check_mass_monotonicity.py               # tuned knobs
    python scripts/check_mass_monotonicity.py --neutral     # neutral knobs
    python scripts/check_mass_monotonicity.py --refs-only --json /tmp/m.json

Exit 0 = no inversion; 1 = at least one (the offending bikes are listed);
``--report-only`` always exits 0.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

TOL_S = 1e-4
REF_DELTAS = (-20.0, -10.0, 0.0, 10.0, 20.0)
CATALOG_DELTA = 10.0
REFERENCES = {
    "K5": "gsxr1000_k5",
    "R1": "yzfr1_4c8",
    "Hayabusa": "hayabusa_gen1",
}


# ── neutral-knob override ──────────────────────────────────────────────────


def _neutral(p):
    return dataclasses.replace(
        p,
        mu_peak_scale=1.0,
        mu_peak_override=None,
        launch_rpm_factor=None,
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
    )


@contextlib.contextmanager
def neutral_profiles(enabled: bool = True):
    """Temporarily replace every CategoryProfile with its neutral twin (grip
    and launch knobs at their no-op values). Engines built inside the block
    see the neutral profile; the original table is restored on exit."""
    from motoquant import category_profiles as cp

    if not enabled:
        yield
        return
    saved = dict(cp._PROFILES)
    try:
        for k, p in saved.items():
            cp._PROFILES[k] = _neutral(p)
        yield
    finally:
        cp._PROFILES.clear()
        cp._PROFILES.update(saved)


# ── single runs ────────────────────────────────────────────────────────────


def _with_dry_mass(cfg, delta_kg: float):
    c = copy.deepcopy(cfg)
    c.chassis.dry_mass_kg = c.chassis.dry_mass_kg + delta_kg
    return c


def limiter_fractions(eng, sim) -> dict:
    """Per-gear share of steps that are traction-limited / wheelie-limited.

    traction-limited: the rear tyre's force cap binds (traction_pct == 100).
    wheelie-limited: the net acceleration equals the wheelie ceiling (within
    1e-3 m/s^2; the ceiling is re-evaluated with the engine's own method).
    """
    from motoquant.constants import G

    n = len(sim.t)
    out = {}
    if n == 0:
        return out
    a_ms2 = sim.a * G
    gears = np.asarray(sim.gear)
    trac = np.asarray(sim.traction_pct) >= 100.0 - 1e-9
    wl = np.zeros(n, dtype=bool)
    for i in range(n):
        if trac[i]:
            continue
        aw = eng.max_accel_before_wheelie(
            float(sim.v[i]), float(sim.t[i]), float(sim.F_drag[i])
        )
        wl[i] = abs(a_ms2[i] - aw) < 1e-3
    for g in sorted({int(x) for x in gears}):
        m = gears == g
        cnt = int(m.sum())
        out[str(g)] = {
            "steps": cnt,
            "traction_frac": round(float(trac[m].sum()) / cnt, 4),
            "wheelie_frac": round(float(wl[m].sum()) / cnt, 4),
        }
    out["all"] = {
        "steps": n,
        "traction_frac": round(float(trac.sum()) / n, 4),
        "wheelie_frac": round(float(wl.sum()) / n, 4),
    }
    return out


def run_one(cfg, *, with_fractions: bool = False) -> dict:
    from motoquant.engine_select import make_engine

    eng = make_engine(cfg)
    sim = eng.run()
    row = {
        "finished": bool(sim.finished_quarter),
        "et": float(sim.time_quarter) if sim.finished_quarter else None,
        "t60": float(sim.time_60ft) if sim.time_60ft > 0 else None,
        "trap_kmh": float(sim.speed_quarter * 3.6) if sim.finished_quarter else None,
        "tire_temp_max_c": float(np.max(sim.T_tire)) if len(sim.T_tire) else None,
        "tire_temp_end_c": float(sim.T_tire[-1]) if len(sim.T_tire) else None,
    }
    if with_fractions:
        row["limiters"] = limiter_fractions(eng, sim)
    return row


# ── references ─────────────────────────────────────────────────────────────


def probe_references(deltas=REF_DELTAS, with_fractions: bool = True) -> dict:
    import motoquant.defaults as d

    out = {}
    for label, fn in REFERENCES.items():
        base = getattr(d, fn)()
        rows = []
        for dm in deltas:
            r = run_one(
                _with_dry_mass(base, dm), with_fractions=with_fractions and dm == 0
            )
            r["delta_kg"] = dm
            r["dry_mass_kg"] = base.chassis.dry_mass_kg + dm
            rows.append(r)
        ets = [r["et"] for r in rows]
        monotone = all(
            a is not None and b is not None and b > a + TOL_S
            for a, b in zip(ets, ets[1:])
        )
        out[label] = {"rows": rows, "monotone": monotone}
    return out


# ── catalog ────────────────────────────────────────────────────────────────


def _catalog_worker(args):
    idx, neutral, with_fractions = args
    from motoquant.category_profiles import get_profile  # noqa: F401
    from motoquant.scraper.importer import spec_to_bike_config
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    spec = ALL_KNOWN_BIKES[idx]
    with neutral_profiles(neutral):
        try:
            cfg = spec_to_bike_config(spec)
            base = run_one(cfg, with_fractions=with_fractions)
            plus = run_one(_with_dry_mass(cfg, CATALOG_DELTA))
            minus = run_one(_with_dry_mass(cfg, -CATALOG_DELTA))
        except Exception as exc:  # report, never hide
            return {
                "i": idx,
                "name": f"{spec.manufacturer} {spec.model_name}",
                "error": f"{type(exc).__name__}: {exc}"[:200],
            }
    row = {
        "i": idx,
        "name": f"{spec.manufacturer} {spec.model_name}",
        "cluster": cfg.category_tag,
        "et": base["et"],
        "t60": base["t60"],
        "trap_kmh": base["trap_kmh"],
        "et_plus": plus["et"],
        "et_minus": minus["et"],
        "tire_temp_max_c": base["tire_temp_max_c"],
    }
    if with_fractions:
        row["limiters"] = base.get("limiters")
    inv = []
    if base["et"] is not None and plus["et"] is not None:
        if plus["et"] < base["et"] - TOL_S:
            inv.append("+10kg faster")
    if base["et"] is not None and minus["et"] is not None:
        if minus["et"] > base["et"] + TOL_S:
            inv.append("-10kg slower")
    row["inversions"] = inv
    return row


def probe_catalog(
    neutral: bool = False,
    workers: int | None = None,
    limit: int | None = None,
    with_fractions: bool = True,
) -> list[dict]:
    from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

    n = len(ALL_KNOWN_BIKES) if limit is None else min(limit, len(ALL_KNOWN_BIKES))
    jobs = [(i, neutral, with_fractions) for i in range(n)]
    workers = workers or os.cpu_count() or 1
    if workers <= 1:
        return [_catalog_worker(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_catalog_worker, jobs, chunksize=4))


def summarize_catalog(rows: list[dict]) -> dict:
    inv = [r for r in rows if r.get("inversions")]
    by_cluster: dict[str, int] = {}
    for r in inv:
        by_cluster[r["cluster"]] = by_cluster.get(r["cluster"], 0) + 1
    errors = [r for r in rows if "error" in r]
    temps = [r["tire_temp_max_c"] for r in rows if r.get("tire_temp_max_c") is not None]
    trac = [
        r["limiters"]["all"]["traction_frac"]
        for r in rows
        if r.get("limiters") and "all" in r["limiters"]
    ]
    return {
        "n": len(rows),
        "errors": len(errors),
        "inversions": len(inv),
        "inversions_plus": sum(1 for r in inv if "+10kg faster" in r["inversions"]),
        "inversions_minus": sum(1 for r in inv if "-10kg slower" in r["inversions"]),
        "by_cluster": dict(sorted(by_cluster.items())),
        "tire_temp_max_c": {
            "median": float(np.median(temps)) if temps else None,
            "max": float(np.max(temps)) if temps else None,
        },
        "traction_frac_median": float(np.median(trac)) if trac else None,
    }


# ── CLI ────────────────────────────────────────────────────────────────────


def _fmt(x, nd=4):
    return (
        "  -   "
        if x is None or (isinstance(x, float) and math.isnan(x))
        else f"{x:.{nd}f}"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--neutral", action="store_true", help="neutral grip/launch knobs")
    ap.add_argument("--refs-only", action="store_true", help="skip the catalog sweep")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None, help="first N catalog bikes")
    ap.add_argument("--json", default=None, help="write the full result here")
    ap.add_argument("--report-only", action="store_true", help="always exit 0")
    ap.add_argument(
        "--no-fractions", action="store_true", help="skip limiter fractions"
    )
    args = ap.parse_args(argv)

    from motoquant.engine_select import engine_class

    result: dict = {"neutral": bool(args.neutral), "engine": None}
    with neutral_profiles(args.neutral):
        result["engine"] = engine_class().__name__
        refs = probe_references(with_fractions=not args.no_fractions)
    result["references"] = refs
    print(f"engine={result['engine']}  knobs={'neutral' if args.neutral else 'tuned'}")
    for label, block in refs.items():
        tag = "monotone" if block["monotone"] else "INVERTED"
        print(f"  {label:9s} [{tag}]")
        for r in block["rows"]:
            print(
                f"    dry {r['dry_mass_kg']:6.1f} kg  ET {_fmt(r['et'])}  "
                f"60ft {_fmt(r['t60'])}  trap {_fmt(r['trap_kmh'], 1)} km/h  "
                f"Ttire max {_fmt(r['tire_temp_max_c'], 1)} C"
            )
        lim = block["rows"][REF_DELTAS.index(0.0)].get("limiters")
        if lim:
            parts = [
                f"g{g}: T{v['traction_frac']:.2f}/W{v['wheelie_frac']:.2f}"
                for g, v in lim.items()
                if g != "all"
            ]
            print("    limiters (traction/wheelie step share): " + "  ".join(parts))

    bad = sum(0 if b["monotone"] else 1 for b in refs.values())
    if not args.refs_only:
        rows = probe_catalog(
            neutral=args.neutral,
            workers=args.workers,
            limit=args.limit,
            with_fractions=not args.no_fractions,
        )
        summ = summarize_catalog(rows)
        result["catalog"] = rows
        result["catalog_summary"] = summ
        print(
            f"catalog: {summ['n']} bikes, {summ['inversions']} inversions "
            f"(+10 faster {summ['inversions_plus']}, -10 slower "
            f"{summ['inversions_minus']}), errors {summ['errors']}"
        )
        if summ["by_cluster"]:
            print(
                "  by cluster: "
                + ", ".join(f"{k} {v}" for k, v in summ["by_cluster"].items())
            )
        print(
            f"  tyre max temp median {_fmt(summ['tire_temp_max_c']['median'], 1)} C, "
            f"max {_fmt(summ['tire_temp_max_c']['max'], 1)} C; median traction-limited "
            f"share {_fmt(summ['traction_frac_median'], 3)}"
        )
        for r in rows:
            if r.get("inversions"):
                print(
                    f"  INV {r['name']:<45s} {r['cluster']:<22s} "
                    f"ET {_fmt(r['et'])} +10 {_fmt(r['et_plus'])} -10 {_fmt(r['et_minus'])}"
                    f"  ({', '.join(r['inversions'])})"
                )
        bad += summ["inversions"]

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(result, fh, indent=1)
    if args.report_only:
        return 0
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
