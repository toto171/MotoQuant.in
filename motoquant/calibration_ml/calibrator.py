"""
Calibrator -- 3-target XGBoost regression on bike spec + measurement.

Schema v2: 3 targets (cd_factor dropped). Calibrator.version=2.

Architecture: 3 separate XGBRegressor models, one per correction factor.
Easier to debug + tune individually than multi-output. Saves to a single
.pkl via pickle.

Lifecycle:
    cal = Calibrator()
    cal.fit(dataset.X, dataset.Y)
    cal.evaluate(test_X, test_Y) -> CalibratorMetrics
    cal.predict_correction(bike_config, measured) -> CorrectionTargets
    cal.save("calibrator.pkl")
    cal2 = Calibrator.load("calibrator.pkl")

Falls back to scikit-learn GradientBoostingRegressor if XGBoost is not
installed, so unit tests can run without the heavyweight dep. Production
training should always use XGBoost (faster + better on this size).
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .features import FEATURE_DIM, FEATURE_NAMES, MeasuredRun, extract_features
from .targets import CorrectionTargets

__all__ = [
    "Calibrator",
    "CalibratorMetrics",
    "DEFAULT_XGB_PARAMS",
    "DEFAULT_SKLEARN_PARAMS",
    "TARGET_NAMES",
    "train_calibrator",
]


# Schema v2: cd_factor removed.
TARGET_NAMES: list[str] = [
    "mu_peak_factor",
    "peak_torque_factor",
    "inertia_factor",
]


# Tuned for ~1k-50k row datasets. Bump n_estimators if R2 plateaus.
DEFAULT_XGB_PARAMS: dict[str, Any] = {
    "n_estimators": 300,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
    "objective": "reg:squarederror",
    "random_state": 42,
}


# Fallback for environments without XGBoost (CI, smoke tests).
DEFAULT_SKLEARN_PARAMS: dict[str, Any] = {
    "n_estimators": 100,
    "max_depth": 5,
    "learning_rate": 0.08,
    "subsample": 0.85,
    "random_state": 42,
}


# ── Metrics ─────────────────────────────────────────────────────────


@dataclass
class CalibratorMetrics:
    """Per-target evaluation metrics."""

    mae: dict[str, float] = field(default_factory=dict)
    rmse: dict[str, float] = field(default_factory=dict)
    r2: dict[str, float] = field(default_factory=dict)
    n_test: int = 0

    def summary(self) -> str:
        lines = [
            f"Test set: N={self.n_test}",
            f"{'Target':<22s} {'MAE':>8s} {'RMSE':>8s} {'R2':>9s}",
        ]
        for t in TARGET_NAMES:
            lines.append(
                f"  {t:<20s} {self.mae.get(t, 0):>8.4f} "
                f"{self.rmse.get(t, 0):>8.4f} {self.r2.get(t, 0):>+9.4f}"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mae": dict(self.mae),
            "rmse": dict(self.rmse),
            "r2": dict(self.r2),
            "n_test": self.n_test,
        }


# ── Backend selection ──────────────────────────────────────────────


def _make_regressor(hyperparams: dict[str, Any]) -> tuple[Any, str]:
    """Build a regressor instance + return ('xgb' | 'sklearn') tag."""
    try:
        from xgboost import XGBRegressor

        return XGBRegressor(**hyperparams), "xgb"
    except ImportError:
        try:
            from sklearn.ensemble import GradientBoostingRegressor

            # XGB-only kwargs that sklearn doesn't accept
            blocked = {"colsample_bytree", "objective"}
            sk_params = {
                k: v for k, v in hyperparams.items() if k not in blocked
            }
            return GradientBoostingRegressor(**sk_params), "sklearn"
        except ImportError as e:
            raise ImportError(
                "Need either xgboost or scikit-learn installed. Run: "
                "pip install xgboost --break-system-packages "
                "(or scikit-learn for the lighter fallback)"
            ) from e


# ── Calibrator ─────────────────────────────────────────────────────


class Calibrator:
    """3 XGB (or sklearn) regressors -- one per correction target (schema v2)."""

    def __init__(
        self,
        models: dict[str, Any] | None = None,
        feature_names: list[str] | None = None,
        target_names: list[str] | None = None,
        hyperparams: dict[str, Any] | None = None,
        backend: str = "auto",
        version: int = 2,
    ):
        self.models = models or {}
        self.feature_names = feature_names or list(FEATURE_NAMES)
        self.target_names = target_names or list(TARGET_NAMES)
        self.hyperparams = hyperparams or dict(DEFAULT_XGB_PARAMS)
        self.backend = backend  # 'auto' | 'xgb' | 'sklearn'
        self.version = version  # 2 = schema v2 (3 targets, 24 features)

    @property
    def is_trained(self) -> bool:
        return len(self.models) == len(self.target_names)

    def fit(self, X: np.ndarray, Y: np.ndarray) -> Calibrator:
        """Train one regressor per target."""
        if X.shape[1] != FEATURE_DIM:
            raise ValueError(
                f"X has {X.shape[1]} features but FEATURE_DIM={FEATURE_DIM}"
            )
        if Y.shape[1] != len(self.target_names):
            raise ValueError(
                f"Y has {Y.shape[1]} targets but expected {len(self.target_names)}"
            )
        if X.shape[0] != Y.shape[0]:
            raise ValueError("X and Y row counts differ")

        chosen_backend: str | None = None
        for i, name in enumerate(self.target_names):
            if self.backend == "sklearn":
                from sklearn.ensemble import GradientBoostingRegressor

                blocked = {"colsample_bytree", "objective"}
                sk_params = {
                    k: v for k, v in self.hyperparams.items() if k not in blocked
                }
                model, tag = GradientBoostingRegressor(**sk_params), "sklearn"
            else:
                model, tag = _make_regressor(self.hyperparams)
            chosen_backend = tag
            model.fit(X, Y[:, i])
            self.models[name] = model
        if chosen_backend:
            self.backend = chosen_backend
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict an (N, 3) correction matrix."""
        if not self.is_trained:
            raise RuntimeError("Calibrator is not trained. Call fit() first.")
        out = np.zeros((X.shape[0], len(self.target_names)), dtype=np.float32)
        for i, name in enumerate(self.target_names):
            out[:, i] = self.models[name].predict(X)
        return out

    def predict_correction(
        self, bike_config: Any, measured: MeasuredRun
    ) -> CorrectionTargets:
        """Convenience: features + predict + return CorrectionTargets."""
        x = extract_features(bike_config, measured).reshape(1, -1)
        y = self.predict(x)[0]
        return CorrectionTargets.from_array(y)

    def evaluate(
        self, X_test: np.ndarray, Y_test: np.ndarray
    ) -> CalibratorMetrics:
        """Per-target MAE, RMSE, and R^2."""
        preds = self.predict(X_test)
        m = CalibratorMetrics(n_test=int(len(X_test)))
        for i, name in enumerate(self.target_names):
            true = Y_test[:, i].astype(np.float64)
            pred = preds[:, i].astype(np.float64)
            err = pred - true
            m.mae[name] = float(np.mean(np.abs(err)))
            m.rmse[name] = float(np.sqrt(np.mean(err**2)))
            ss_res = float(np.sum(err**2))
            ss_tot = float(np.sum((true - true.mean()) ** 2))
            m.r2[name] = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0
        return m

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "models": self.models,
                    "feature_names": self.feature_names,
                    "target_names": self.target_names,
                    "hyperparams": self.hyperparams,
                    "backend": self.backend,
                    "version": self.version,
                },
                f,
            )

    @classmethod
    def load(cls, path: str) -> Calibrator:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        # Handle both formats:
        #   - pickled Calibrator instance (from run_calibrator_training.py direct dump)
        #   - pickled dict (from Calibrator.save())
        if isinstance(obj, cls):
            return obj
        return cls(**obj)


# ── One-shot training ─────────────────────────────────────────────


def train_calibrator(
    dataset: Any,
    *,
    test_fraction: float = 0.15,
    hyperparams: dict[str, Any] | None = None,
    backend: str = "auto",
    seed: int = 42,
) -> tuple[Calibrator, CalibratorMetrics]:
    """One-shot: split -> fit -> evaluate. Returns (model, test_metrics)."""
    if dataset.n < 10:
        raise ValueError(
            f"Dataset too small ({dataset.n} rows). Need at least 10."
        )
    rng = np.random.default_rng(seed)
    idx = rng.permutation(dataset.n)
    n_test = max(1, int(dataset.n * test_fraction))
    test_idx = idx[:n_test]
    train_idx = idx[n_test:]

    cal = Calibrator(hyperparams=hyperparams, backend=backend)
    cal.fit(dataset.X[train_idx], dataset.Y[train_idx])
    metrics = cal.evaluate(dataset.X[test_idx], dataset.Y[test_idx])
    return cal, metrics
