"""
Audit a trained Calibrator (schema v2): structure, hold-out metrics,
feature importance, sanity predictions on the K5/R1/Hayabusa baselines,
and behavior under intentionally-biased measurements.

Schema v2: 3 targets (mu_peak_factor, peak_torque_factor, inertia_factor).
cd_factor has been removed -- it was unlearnable (R²=-0.06) and was actively
harming the other targets.

Run on the machine where xgboost is installed:
    python scripts/audit_calibrator.py calibrator.pkl calibration_data.npz

Output is plain text, ~80 lines, suitable for pasting back into a chat.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np

from motoquant.calibration_ml import (
    Calibrator,
    CorrectionTargets,
    FEATURE_NAMES,
    MeasuredRun,
    SyntheticDataset,
    TARGET_NAMES,
)
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.physics import MotoQuantEngine


def _hr(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("calibrator", help="Path to calibrator .pkl")
    p.add_argument("dataset", help="Path to training .npz")
    p.add_argument(
        "--seed", type=int, default=42, help="Held-out split seed (default 42)"
    )
    p.add_argument(
        "--test-fraction", type=float, default=0.15, help="Held-out fraction (default 0.15)"
    )
    args = p.parse_args(argv)

    cal = Calibrator.load(args.calibrator)
    ds = SyntheticDataset.load(args.dataset)
    print(f"Loaded calibrator (backend={cal.backend} v{cal.version}) from {args.calibrator}")
    print(f"Loaded dataset N={ds.n} from {args.dataset}")
    print(f"Schema: {len(cal.target_names)} targets: {cal.target_names}")
    print(f"Features: {len(cal.feature_names)} features (FEATURE_DIM={len(FEATURE_NAMES)})")

    # --- Held-out evaluation ---------------------------------------------------
    rng = np.random.default_rng(args.seed)
    idx = rng.permutation(ds.n)
    n_test = max(1, int(ds.n * args.test_fraction))
    test_idx = idx[:n_test]
    metrics = cal.evaluate(ds.X[test_idx], ds.Y[test_idx])
    _hr(f"HELD-OUT EVALUATION (N={n_test}, fraction={args.test_fraction})")
    print(metrics.summary())

    # --- Feature variance check (dead-feature detector) ----------------------
    _hr("FEATURE VARIANCE CHECK (zero-variance = dead feature)")
    X_test = ds.X[test_idx]
    for i, name in enumerate(FEATURE_NAMES):
        std = float(np.std(X_test[:, i]))
        flag = "DEAD" if std < 0.01 else "ok"
        if flag == "DEAD":
            print(f"  [DEAD] {name:30s} std={std:.6f}")
    n_dead = sum(1 for i in range(len(FEATURE_NAMES)) if np.std(X_test[:, i]) < 0.01)
    if n_dead == 0:
        print("  All features have variance > 0.01 (no dead features).")
    else:
        print(f"  {n_dead} dead feature(s) detected. Retrain after fixing.")

    # --- Feature importance (top-5 per target) --------------------------------
    _hr("FEATURE IMPORTANCE (top-5 per target)")
    for name in TARGET_NAMES:
        model = cal.models.get(name)
        if model is None:
            print(f"  {name}: model not found in calibrator")
            continue
        imp = getattr(model, "feature_importances_", None)
        if imp is None:
            print(f"  {name}: (no feature_importances_ on {type(model).__name__})")
            continue
        feat_names = cal.feature_names if len(cal.feature_names) == len(imp) else FEATURE_NAMES
        order = np.argsort(imp)[::-1][:5]
        print(f"  {name}:")
        for i in order:
            fname = feat_names[i] if i < len(feat_names) else f"feat_{i}"
            print(f"    {fname:28s}  {imp[i] * 100:5.2f}%")

    # --- Identity sanity: baseline measurement -> near-identity correction ---
    _hr("SANITY: baseline-K5/R1/Hayabusa measurement -> corrections")
    print("(Measurement = stock sim. Identity correction (~1.0) is the right answer.)")
    for label, factory, target in [
        ("K5", gsxr1000_k5, 10.0334),
        ("R1", yzfr1_4c8, 10.2859),
        ("Hayabusa", hayabusa_gen1, 10.4712),
    ]:
        cfg = factory()
        sim = MotoQuantEngine(cfg).run()
        m = MeasuredRun(
            et_s=float(sim.time_quarter),
            trap_kmh=float(sim.speed_quarter) * 3.6,
            sixty_ft_s=float(sim.time_60ft),
        )
        ct = cal.predict_correction(cfg, m)
        print(
            f"  {label:10s} measured={m.et_s:.3f}s  ->  "
            f"mu={ct.mu_peak_factor:.3f}  "
            f"T={ct.peak_torque_factor:.3f}  I={ct.inertia_factor:.3f}"
        )

    # --- Closed-loop sanity: biased measurement -> applied correction --------
    _hr("CLOSED-LOOP: bias the measurement, apply correction, check residual")
    print("(For slow/fast/normal K5, predict corrections, apply, re-sim.")
    print(" Residual = |corrected_sim_et - measured_et|. Smaller is better.)")
    cfg = gsxr1000_k5()
    for tag, m in [
        ("slow (10.50s)", MeasuredRun(et_s=10.50, trap_kmh=232.0, sixty_ft_s=1.72)),
        ("fast ( 9.70s)", MeasuredRun(et_s=9.70, trap_kmh=248.0, sixty_ft_s=1.55)),
        ("normal(10.05s)", MeasuredRun(et_s=10.05, trap_kmh=240.0, sixty_ft_s=1.65)),
    ]:
        ct = cal.predict_correction(cfg, m)
        new_et = MotoQuantEngine(ct.apply(cfg)).run().time_quarter
        residual = abs(new_et - m.et_s)
        print(
            f"  {tag:20s} corrections mu={ct.mu_peak_factor:.3f} "
            f"T={ct.peak_torque_factor:.3f} I={ct.inertia_factor:.3f}  "
            f"-> sim={new_et:.3f}s  residual={residual:.3f}s"
        )

    # --- Reference-baseline preservation gate --------------------------------
    _hr("REFERENCE BASELINES (must be untouched -- identity correction)")
    all_ok = True
    for label, factory, target in [
        ("K5", gsxr1000_k5, 10.0334),
        ("R1", yzfr1_4c8, 10.2859),
        ("Hayabusa", hayabusa_gen1, 10.4712),
    ]:
        cfg = CorrectionTargets().apply(factory())  # identity
        et = MotoQuantEngine(cfg).run().time_quarter
        delta = et - target
        flag = "OK" if abs(delta) < 0.01 else "DRIFT"
        if flag != "OK":
            all_ok = False
        print(f"  {label:10s} ET={et:.4f}s  target={target:.4f}s  delta={delta:+.4f}s  [{flag}]")
    if all_ok:
        print("\n  All baselines preserved. PASS.")
    else:
        print("\n  BASELINE DRIFT DETECTED. FAIL.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
