"""
MotoQuant Pro -- Phase B: per-bike ML calibrator
================================================

Schema v2: 3 targets, 24 features (cd_factor dropped, tire_compound_code
removed, 4 other dead features fixed).

Closes the residual ET-bias gap that physics alone can't (per-bike spec
quirks: tire grip aging, exact crank-vs-wheel power, engine-inertia
uncertainty). Learns 3 multiplicative correction factors:

    mu_peak_factor     tire grip override
    peak_torque_factor crank/wheel power scaling
    inertia_factor     engine inertia override

Architecture
------------
    CorrectionTargets   the 3-dim label space the model predicts (v2)
    MeasuredRun         the real-world quarter-mile telemetry payload
    extract_features    BikeConfig + MeasuredRun -> 24-dim feature vector (v2)
    SyntheticDataset    perturb-and-resimulate training pairs
    Calibrator          3 XGB regressors (one per correction target, v2)

Two data paths
--------------
1. Synthetic (start here, ship in week 1) -- perturb known bikes inside
   plausible param ranges, train inverse mapping. Bootstraps a working
   model from zero real data.
2. Real Dragy uploads (week 2+, accumulates over months) -- every run
   uploaded via `calibrate import-dragy` is logged into the
   calibration_runs table and used to retrain.

Why XGBoost (not LSTM/Transformer): this is a tabular regression on
~24 features. XGBoost dominates on this size (sub-10k rows). The
existing surrogate pipeline (motoquant.analysis.surrogate_xgb) uses
the same backend and benchmarks well -- copy that recipe here.
"""

from .calibrator import (
    Calibrator,
    CalibratorMetrics,
    DEFAULT_SKLEARN_PARAMS,
    DEFAULT_XGB_PARAMS,
    TARGET_NAMES,
    train_calibrator,
)
from .features import (
    FEATURE_DIM,
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    MeasuredRun,
    extract_features,
    feature_dict,
)
from .synthetic import (
    ENV_PERTURBATION,
    PERTURBATION_RANGES,
    SyntheticDataset,
    default_base_configs,
    generate_dataset,
    generate_one,
)
from .targets import CorrectionTargets

__all__ = [
    "Calibrator",
    "CalibratorMetrics",
    "CorrectionTargets",
    "DEFAULT_SKLEARN_PARAMS",
    "DEFAULT_XGB_PARAMS",
    "ENV_PERTURBATION",
    "FEATURE_DIM",
    "FEATURE_NAMES",
    "FEATURE_SCHEMA_VERSION",
    "MeasuredRun",
    "PERTURBATION_RANGES",
    "SyntheticDataset",
    "TARGET_NAMES",
    "default_base_configs",
    "extract_features",
    "feature_dict",
    "generate_dataset",
    "generate_one",
    "train_calibrator",
]
