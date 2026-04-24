"""
MotoQuant Pro — DNN Surrogate Model (Phase 4A)
===============================================
4-layer MLP trained on the same Sobol-sampled dataset as the XGBoost surrogate
(Phase 4B), but with significantly more model capacity to capture the complex
nonlinear physics interactions that XGBoost's piecewise-linear trees miss.

Architecture
------------
  Input  : 21 features (14 base + 7 derived — see surrogate_data.FEATURE_NAMES)
  Hidden : Linear(21→256) → BN → ReLU → Dropout
           Linear(256→512) → BN → ReLU → Dropout
           Linear(512→512) → BN → ReLU → Dropout
           Linear(512→256) → BN → ReLU → Dropout
  Output : Two independent heads — one for ET, one for trap speed
  Loss   : Huber loss (δ=0.5s) — robust to the few remaining outlier configs

Key design decisions
--------------------
* **Feature + target normalisation** baked into the model: inference only needs
  raw feature values (not normalised ones).  The StandardScaler parameters are
  stored alongside the model weights.
* **Two-head architecture**: sharing a backbone but using separate output neurons
  lets the ET and trap-speed losses scale independently.
* **PyTorch primary, sklearn fallback**: if ``torch`` is not installed, the
  class transparently uses ``sklearn.neural_network.MLPRegressor`` — same
  interface, slightly lower accuracy and no GPU support.

Hardware note
-------------
MSI Delta 15 (Ryzen 9, RX 6700M 10 GB):
  * CPU training: ~90–120 s for 300 epochs on 50 k samples
  * GPU (ROCm/CUDA): ~10–20 s

Install PyTorch (user's machine) for GPU acceleration::

    pip install torch   # CPU-only
    # or for CUDA:
    pip install torch --index-url https://download.pytorch.org/whl/cu121

Usage
-----
    from motoquant.analysis.surrogate_dnn import DNNSurrogate
    from motoquant.analysis.surrogate_data import SurrogateDataset

    ds = SurrogateDataset.load("surrogate_data.npz")
    train_ds, test_ds = ds.split(test_fraction=0.15)

    model = DNNSurrogate()
    model.fit(*train_ds.to_arrays())
    metrics = model.evaluate(*test_ds.to_arrays())
    metrics.print_report()
    model.save("surrogate_dnn.pkl")

    # Fast inference
    model = DNNSurrogate.load("surrogate_dnn.pkl")
    et, trap = model.predict_config(gsxr1000_k5())
"""

from __future__ import annotations

import logging
import time
import warnings
from pathlib import Path

import numpy as np

from ..models import BikeConfig
from .surrogate_data import FEATURE_NAMES, SurrogateDataset, config_to_feature_vector
from .surrogate_xgb import SurrogateMetrics, _check_array_shapes

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Torch detection
# ─────────────────────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    logger.info(
        "PyTorch not found — DNNSurrogate will use sklearn MLPRegressor fallback. "
        "For GPU acceleration: pip install torch"
    )


# ─────────────────────────────────────────────────────────────────
# PyTorch model definition
# ─────────────────────────────────────────────────────────────────

if _TORCH_AVAILABLE:

    class _MLPBackbone(nn.Module):
        """Shared feature-extraction backbone for the two-head MLP."""

        def __init__(
            self,
            n_in: int,
            hidden_dims: tuple[int, ...] = (256, 512, 512, 256),
            dropout: float = 0.15,
        ) -> None:
            super().__init__()
            layers: list[nn.Module] = []
            prev = n_in
            for h in hidden_dims:
                layers += [
                    nn.Linear(prev, h),
                    nn.BatchNorm1d(h),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout),
                ]
                prev = h
            self.backbone = nn.Sequential(*layers)
            self.head_et = nn.Linear(prev, 1)
            self.head_trap = nn.Linear(prev, 1)

        def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            feat = self.backbone(x)
            return self.head_et(feat).squeeze(-1), self.head_trap(feat).squeeze(-1)


# ─────────────────────────────────────────────────────────────────
# DNNSurrogate
# ─────────────────────────────────────────────────────────────────


class DNNSurrogate:
    """
    4-layer MLP surrogate for motorcycle quarter-mile ET + trap speed prediction.

    Uses PyTorch if available (recommended), otherwise falls back to
    ``sklearn.neural_network.MLPRegressor`` automatically.

    Parameters
    ----------
    hidden_dims  : tuple of hidden layer widths (default: 256-512-512-256)
    dropout      : dropout probability applied after each hidden layer
    device       : torch device string ("cpu", "cuda", "mps").  None = auto-detect.
    """

    def __init__(
        self,
        hidden_dims: tuple[int, ...] = (256, 512, 512, 256),
        dropout: float = 0.15,
        device: str | None = None,
    ) -> None:
        self.hidden_dims = hidden_dims
        self.dropout = dropout
        self._is_fitted = False
        self._feature_names = FEATURE_NAMES[:]
        self._n_train: int = 0
        self._train_elapsed_s: float = 0.0
        self._backend: str = "torch" if _TORCH_AVAILABLE else "sklearn"

        # Normalisation stats (set during fit)
        self._X_mean: np.ndarray | None = None
        self._X_std: np.ndarray | None = None
        self._et_mean: float = 0.0
        self._et_std: float = 1.0
        self._trap_mean: float = 0.0
        self._trap_std: float = 1.0

        if _TORCH_AVAILABLE:
            if device is None:
                if torch.cuda.is_available():
                    device = "cuda"
                elif (
                    hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                ):
                    device = "mps"
                else:
                    device = "cpu"
            self._device = torch.device(device)
            self._model: _MLPBackbone | None = None
        else:
            self._device = None
            self._model = None
            self._sklearn_et = None
            self._sklearn_trap = None

    # ── Fitting ──────────────────────────────────────────────────

    def fit(
        self,
        X: np.ndarray,
        y_et: np.ndarray,
        y_trap: np.ndarray,
        epochs: int = 300,
        batch_size: int = 512,
        lr: float = 1e-3,
        patience: int = 25,
        verbose: bool = True,
    ) -> DNNSurrogate:
        """
        Train the DNN surrogate.

        Parameters
        ----------
        X          : (n, 21) feature matrix
        y_et       : (n,) ET labels in seconds
        y_trap     : (n,) trap speed labels in m/s
        epochs     : maximum training epochs
        batch_size : mini-batch size
        lr         : initial learning rate (Adam)
        patience   : early stopping patience (epochs without val improvement)
        verbose    : print epoch progress every 10 epochs
        """
        _check_array_shapes(X, y_et, y_trap)
        t0 = time.perf_counter()

        # Normalise features
        self._X_mean = X.mean(axis=0).astype(np.float32)
        self._X_std = np.where(X.std(axis=0) > 1e-8, X.std(axis=0), 1.0).astype(
            np.float32
        )
        X_n = ((X - self._X_mean) / self._X_std).astype(np.float32)

        # Normalise targets (Z-score)
        self._et_mean = float(y_et.mean())
        self._et_std = float(y_et.std()) or 1.0
        self._trap_mean = float(y_trap.mean())
        self._trap_std = float(y_trap.std()) or 1.0
        y_et_n = ((y_et - self._et_mean) / self._et_std).astype(np.float32)
        y_trap_n = ((y_trap - self._trap_mean) / self._trap_std).astype(np.float32)

        # Train/val split (10% val)
        rng = np.random.default_rng(0)
        n = len(X_n)
        val_idx = rng.choice(n, size=max(1, int(n * 0.10)), replace=False)
        train_mask = np.ones(n, dtype=bool)
        train_mask[val_idx] = False

        if _TORCH_AVAILABLE:
            self._fit_torch(
                X_n,
                y_et_n,
                y_trap_n,
                train_mask,
                val_idx,
                epochs,
                batch_size,
                lr,
                patience,
                verbose,
            )
        else:
            self._fit_sklearn(X_n, y_et_n, y_trap_n, train_mask, val_idx)

        self._is_fitted = True
        self._n_train = int(train_mask.sum())
        self._train_elapsed_s = time.perf_counter() - t0
        logger.info(
            "DNNSurrogate (%s) fitted on %d samples in %.1fs",
            self._backend,
            self._n_train,
            self._train_elapsed_s,
        )
        return self

    def _fit_torch(
        self,
        X_n,
        y_et_n,
        y_trap_n,
        train_mask,
        val_idx,
        epochs,
        batch_size,
        lr,
        patience,
        verbose,
    ) -> None:
        """PyTorch training loop."""
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        n_in = X_n.shape[1]
        self._model = _MLPBackbone(n_in, self.hidden_dims, self.dropout).to(
            self._device
        )

        X_tr = torch.tensor(X_n[train_mask]).to(self._device)
        et_tr = torch.tensor(y_et_n[train_mask]).to(self._device)
        trap_tr = torch.tensor(y_trap_n[train_mask]).to(self._device)
        X_val = torch.tensor(X_n[val_idx]).to(self._device)
        et_val = torch.tensor(y_et_n[val_idx]).to(self._device)
        trap_val = torch.tensor(y_trap_n[val_idx]).to(self._device)

        ds = TensorDataset(X_tr, et_tr, trap_tr)
        loader = DataLoader(ds, batch_size=batch_size, shuffle=True)

        opt = torch.optim.Adam(self._model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            opt, T_max=epochs, eta_min=lr * 0.01
        )
        huber = nn.HuberLoss(delta=0.5)

        best_val = float("inf")
        best_state = None
        no_improve = 0

        for epoch in range(1, epochs + 1):
            self._model.train()
            for xb, etb, trapb in loader:
                opt.zero_grad()
                et_pred, trap_pred = self._model(xb)
                loss = huber(et_pred, etb) + huber(trap_pred, trapb)
                loss.backward()
                nn.utils.clip_grad_norm_(self._model.parameters(), 1.0)
                opt.step()
            scheduler.step()

            # Validation
            self._model.eval()
            with torch.no_grad():
                et_p, trap_p = self._model(X_val)
                val_loss = (huber(et_p, et_val) + huber(trap_p, trap_val)).item()

            if val_loss < best_val - 1e-6:
                best_val = val_loss
                best_state = {k: v.clone() for k, v in self._model.state_dict().items()}
                no_improve = 0
            else:
                no_improve += 1

            if verbose and epoch % 25 == 0:
                # Compute MAE in original scale for readability
                et_mae_ms = (
                    torch.abs(et_p * self._et_std - et_val * self._et_std).mean().item()
                ) * 1000
                print(
                    f"  Epoch {epoch:>3}/{epochs}  val_loss={val_loss:.4f}  "
                    f"ET MAE≈{et_mae_ms:.0f} ms  lr={scheduler.get_last_lr()[0]:.2e}"
                )

            if no_improve >= patience:
                if verbose:
                    print(f"  Early stop at epoch {epoch} (patience={patience})")
                break

        if best_state is not None:
            self._model.load_state_dict(best_state)
        self._model.eval()

    def _fit_sklearn(self, X_n, y_et_n, y_trap_n, train_mask, val_idx) -> None:
        """sklearn MLPRegressor fallback training."""
        from sklearn.neural_network import MLPRegressor

        X_tr = X_n[train_mask]
        params = {
            "hidden_layer_sizes": self.hidden_dims,
            "activation": "relu",
            "solver": "adam",
            "alpha": 5e-4,  # L2 regularisation
            "learning_rate_init": 1e-3,
            "max_iter": 500,
            "early_stopping": True,
            "validation_fraction": 0.10,
            "n_iter_no_change": 25,
            "random_state": 0,
            "verbose": True,
        }
        self._sklearn_et = MLPRegressor(**params)
        self._sklearn_trap = MLPRegressor(**params)

        print("  Training ET model (sklearn MLP)...")
        self._sklearn_et.fit(X_tr, y_et_n[train_mask])
        print("  Training trap speed model (sklearn MLP)...")
        self._sklearn_trap.fit(X_tr, y_trap_n[train_mask])

    # ── Prediction ───────────────────────────────────────────────

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Predict ET and trap speed for a feature matrix.

        Returns
        -------
        y_et_pred   : (n,) predicted ET in seconds
        y_trap_pred : (n,) predicted trap speed in m/s
        """
        self._check_fitted()
        X = np.atleast_2d(X).astype(np.float32)
        X_n = (X - self._X_mean) / self._X_std

        if _TORCH_AVAILABLE and self._backend == "torch":
            import torch

            self._model.eval()
            with torch.no_grad():
                xt = torch.tensor(X_n).to(self._device)
                et_n, trap_n = self._model(xt)
                et_n = et_n.cpu().numpy()
                trap_n = trap_n.cpu().numpy()
        else:
            et_n = self._sklearn_et.predict(X_n)
            trap_n = self._sklearn_trap.predict(X_n)

        et = (et_n * self._et_std + self._et_mean).astype(np.float32)
        trap = (trap_n * self._trap_std + self._trap_mean).astype(np.float32)
        return et, trap

    def predict_config(self, config: BikeConfig) -> tuple[float, float]:
        """End-to-end prediction from a live BikeConfig."""
        self._check_fitted()
        x = config_to_feature_vector(config).reshape(1, -1)
        et_arr, trap_arr = self.predict(x)
        return float(et_arr[0]), float(trap_arr[0])

    # ── Evaluation ───────────────────────────────────────────────

    def evaluate(
        self, X: np.ndarray, y_et: np.ndarray, y_trap: np.ndarray
    ) -> SurrogateMetrics:
        """Compute accuracy metrics on a held-out test set."""
        self._check_fitted()
        _check_array_shapes(X, y_et, y_trap)

        t_start = time.perf_counter()
        n_inf = min(200, len(X))
        for i in range(n_inf):
            self.predict(X[i : i + 1])
        inf_us = (time.perf_counter() - t_start) / n_inf * 1e6

        et_pred, trap_pred = self.predict(X)
        et_err = np.abs(et_pred - y_et)
        trap_err = np.abs(trap_pred - y_trap)

        def r2(y_true, y_pred):
            ss_res = float(np.sum((y_true - y_pred) ** 2))
            ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
            return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        return SurrogateMetrics(
            et_mae_s=float(np.mean(et_err)),
            et_rmse_s=float(np.sqrt(np.mean(et_err**2))),
            et_r2=r2(y_et, et_pred),
            et_within_50ms=float(np.mean(et_err <= 0.050)),
            et_within_100ms=float(np.mean(et_err <= 0.100)),
            et_max_error_s=float(np.max(et_err)),
            trap_mae_mps=float(np.mean(trap_err)),
            trap_rmse_mps=float(np.sqrt(np.mean(trap_err**2))),
            trap_r2=r2(y_trap, trap_pred),
            trap_within_1kmh=float(np.mean(trap_err <= (1.0 / 3.6))),
            n_test=len(y_et),
            inference_us=inf_us,
        )

    # ── Persistence ──────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Serialize model + normalisation stats to a .pkl file."""
        import joblib

        self._check_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict = {
            "backend": self._backend,
            "hidden_dims": self.hidden_dims,
            "dropout": self.dropout,
            "feature_names": self._feature_names,
            "n_train": self._n_train,
            "train_elapsed_s": self._train_elapsed_s,
            "X_mean": self._X_mean,
            "X_std": self._X_std,
            "et_mean": self._et_mean,
            "et_std": self._et_std,
            "trap_mean": self._trap_mean,
            "trap_std": self._trap_std,
            "version": "1.0",
        }

        if self._backend == "torch" and _TORCH_AVAILABLE:
            import io

            import torch

            buf = io.BytesIO()
            torch.save(self._model.state_dict(), buf)
            payload["torch_state_dict"] = buf.getvalue()
            payload["n_in"] = self._X_mean.shape[0]
        else:
            payload["sklearn_et"] = self._sklearn_et
            payload["sklearn_trap"] = self._sklearn_trap

        joblib.dump(payload, path, compress=3)
        logger.info("DNNSurrogate (%s) saved to %s", self._backend, path)

    @classmethod
    def load(cls, path: str | Path) -> DNNSurrogate:
        """Load a DNNSurrogate saved by :meth:`save`."""
        import joblib

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"DNN surrogate model not found: {path}")
        payload = joblib.load(path)

        inst = cls.__new__(cls)
        inst.hidden_dims = tuple(payload.get("hidden_dims", (256, 512, 512, 256)))
        inst.dropout = float(payload.get("dropout", 0.15))
        inst._is_fitted = True
        inst._feature_names = list(payload.get("feature_names", FEATURE_NAMES))
        inst._n_train = int(payload.get("n_train", 0))
        inst._train_elapsed_s = float(payload.get("train_elapsed_s", 0.0))
        inst._X_mean = payload["X_mean"]
        inst._X_std = payload["X_std"]
        inst._et_mean = float(payload["et_mean"])
        inst._et_std = float(payload["et_std"])
        inst._trap_mean = float(payload["trap_mean"])
        inst._trap_std = float(payload["trap_std"])
        inst._backend = payload.get("backend", "sklearn")

        if inst._backend == "torch":
            if not _TORCH_AVAILABLE:
                warnings.warn(
                    "Model was saved with PyTorch but torch is not installed. "
                    "Install with: pip install torch"
                )
                inst._model = None
                inst._sklearn_et = None
                inst._sklearn_trap = None
                inst._device = None
                inst._is_fitted = False
            else:
                import io

                import torch

                n_in = int(payload["n_in"])
                inst._model = _MLPBackbone(n_in, inst.hidden_dims, inst.dropout)
                buf = io.BytesIO(payload["torch_state_dict"])
                state = torch.load(buf, map_location="cpu")
                inst._model.load_state_dict(state)
                inst._model.eval()
                inst._device = torch.device("cpu")
                inst._sklearn_et = None
                inst._sklearn_trap = None
        else:
            inst._model = None
            inst._device = None
            inst._sklearn_et = payload.get("sklearn_et")
            inst._sklearn_trap = payload.get("sklearn_trap")

        logger.info(
            "DNNSurrogate (%s) loaded from %s (trained on %d samples)",
            inst._backend,
            path,
            inst._n_train,
        )
        return inst

    # ── Helpers ───────────────────────────────────────────────────

    def _check_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                "DNNSurrogate is not fitted. Call fit() or load() first."
            )

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def n_train(self) -> int:
        return self._n_train

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def train_elapsed_s(self) -> float:
        return self._train_elapsed_s

    def __repr__(self) -> str:
        status = (
            f"fitted on {self._n_train:,} samples [{self._backend}]"
            if self._is_fitted
            else "not fitted"
        )
        return f"DNNSurrogate(hidden={self.hidden_dims}, {status})"


# ─────────────────────────────────────────────────────────────────
# Convenience pipeline
# ─────────────────────────────────────────────────────────────────


def train_dnn_surrogate(
    dataset: SurrogateDataset,
    test_fraction: float = 0.15,
    hidden_dims: tuple[int, ...] = (256, 512, 512, 256),
    dropout: float = 0.15,
    epochs: int = 300,
    batch_size: int = 512,
    lr: float = 1e-3,
    patience: int = 25,
    verbose: bool = True,
    seed: int = 0,
) -> tuple[DNNSurrogate, SurrogateMetrics]:
    """
    One-shot pipeline: split → fit DNNSurrogate → return (model, metrics).

    Parameters match ``DNNSurrogate.__init__`` and ``DNNSurrogate.fit``.
    """

    train_ds, test_ds = dataset.split(test_fraction=test_fraction, seed=seed)
    X_tr, y_et_tr, y_trap_tr = train_ds.to_arrays()
    X_te, y_et_te, y_trap_te = test_ds.to_arrays()

    model = DNNSurrogate(hidden_dims=hidden_dims, dropout=dropout)
    model.fit(
        X_tr,
        y_et_tr,
        y_trap_tr,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        patience=patience,
        verbose=verbose,
    )
    metrics = model.evaluate(X_te, y_et_te, y_trap_te)
    return model, metrics
