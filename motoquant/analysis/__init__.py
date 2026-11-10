"""
MotoQuant — Analysis Package (Phase 4)
======================================
Higher-level analytical tools that sit on top of the physics engine:

  roi           — Parts Return-on-Investment engine: ranks every part in the
                  catalog by ET gain per rupee, finds the best build within
                  a budget constraint, and reports cost-per-tenth breakdowns.

  bayesian_opt  — Bayesian optimization engine: explores continuous parameter
                  space (power, mass, aero, gearing, tires) within a budget
                  constraint using BoTorch + Expected Improvement acquisition.
                  Faster discovery of non-obvious tuning combinations.

  sobol         — Global Sensitivity Analysis via Sobol indices: quantifies
                  which simulation parameters drive the most quarter-mile
                  variance.  Uses SALib (Saltelli sampling + Jansen estimator).

  surrogate_data — Sobol-sampled training data generator (Phase 4B): runs the
                  full physics engine on N quasi-random BikeConfig instances and
                  collects (features, ET, trap speed) training pairs.

  surrogate_xgb  — XGBoost baseline surrogate model (Phase 4B): <1 ms
                  ET + trap speed prediction from a 14-dimensional feature
                  vector.  Replaces the physics engine for real-time UI sliders.

Public surface (importable from `motoquant.analysis`):
  PartROIResult, BuildROIResult, compute_parts_roi, find_best_build
  OptimizationResult, BayesianBuildOptimizer, optimize_build
  SobolResult, compute_sobol_indices, DEFAULT_PARAM_BOUNDS
  FEATURE_NAMES, SurrogateDataset, generate_training_data, config_to_feature_vector
  XGBSurrogate, SurrogateMetrics, train_surrogate
"""

from .bayesian_opt import (
    BayesianBuildOptimizer,
    OptimizationResult,
    optimize_build,
)
from .recommendations import (
    BuildProfile,
    BuildRecommendation,
    UpgradePath,
    generate_upgrade_path,
    get_category_upgrade_order,
    recommend_build,
)
from .roi import (
    BuildROIResult,
    PartROIResult,
    compute_parts_roi,
    find_best_build,
)
from .sobol import (
    DEFAULT_PARAM_BOUNDS,
    SobolParamSpec,
    SobolResult,
    compute_sobol_indices,
)
from .surrogate_data import (
    FEATURE_NAMES,
    SurrogateDataset,
    config_to_feature_vector,
    generate_training_data,
)
from .surrogate_dnn import (
    DNNSurrogate,
    train_dnn_surrogate,
)
from .surrogate_xgb import (
    SurrogateMetrics,
    XGBSurrogate,
    train_surrogate,
)

__all__ = [
    # ROI
    "PartROIResult",
    "BuildROIResult",
    "compute_parts_roi",
    "find_best_build",
    # Bayesian Optimization
    "OptimizationResult",
    "BayesianBuildOptimizer",
    "optimize_build",
    # Sobol
    "SobolResult",
    "SobolParamSpec",
    "compute_sobol_indices",
    "DEFAULT_PARAM_BOUNDS",
    # Surrogate data (Phase 4B)
    "FEATURE_NAMES",
    "SurrogateDataset",
    "generate_training_data",
    "config_to_feature_vector",
    # Surrogate model XGBoost (Phase 4B)
    "XGBSurrogate",
    "SurrogateMetrics",
    "train_surrogate",
    # Surrogate model DNN (Phase 4A)
    "DNNSurrogate",
    "train_dnn_surrogate",
    # Smart Recommendations (Phase 4)
    "BuildProfile",
    "BuildRecommendation",
    "UpgradePath",
    "recommend_build",
    "generate_upgrade_path",
    "get_category_upgrade_order",
]
