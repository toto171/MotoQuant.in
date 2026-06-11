"""Pure-numpy MLP surrogate — torch/sklearn/xgboost-free inference.

Loads MLP weights exported by ``scripts/train_surrogate_numpy.py`` (indexed-key
.npz) and runs a numpy forward pass (~1 ms). Drop-in for the API's surrogate
serving: exposes ``predict(X) -> (et_s, trap_mps)`` and
``predict_config(cfg) -> (et_s, trap_mps)`` matching XGBSurrogate / DNNSurrogate,
so /api/surrogate/* works on the lean backend where numpy is the only ML dep.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class NumpySurrogate:
    """Feed-forward ReLU MLP evaluated in pure numpy (no torch/sklearn/xgboost)."""

    def __init__(
        self,
        weights,
        biases,
        feat_mean,
        feat_std,
        tgt_mean,
        tgt_std,
        feature_names,
        meta=None,
        env_min=None,
        env_max=None,
    ):
        self._W = weights
        self._b = biases
        self._fm = feat_mean
        self._fs = feat_std
        self._tm = tgt_mean
        self._ts = tgt_std
        self.feature_names = list(feature_names)
        self.meta = meta
        self._env_min = env_min
        self._env_max = env_max
        self._backend = "numpy"

    @classmethod
    def load(cls, path: str | Path) -> NumpySurrogate:
        d = np.load(str(path), allow_pickle=False)
        n = int(d["n_layers"][0])
        W = [d[f"W{i}"].astype(np.float64) for i in range(n)]
        b = [d[f"b{i}"].astype(np.float64) for i in range(n)]
        return cls(
            W,
            b,
            d["feat_mean"].astype(np.float64),
            d["feat_std"].astype(np.float64),
            d["tgt_mean"].astype(np.float64),
            d["tgt_std"].astype(np.float64),
            [str(s) for s in d["feature_names"]],
            d["meta"] if "meta" in d.files else None,
            # v2 artifacts embed their training envelope; v1 files simply
            # lack the keys and fall back to the static FEATURE_BOUNDS check.
            d["env_min"].astype(np.float64) if "env_min" in d.files else None,
            d["env_max"].astype(np.float64) if "env_max" in d.files else None,
        )

    def predict(self, X):
        """X: (n, n_features) or (n_features,). Returns (et_s, trap_mps) arrays.

        Feature schemas are append-only (v1 = 21, v2 = 26 with the v1 features
        as a strict prefix), so a WIDER vector than this model was trained on
        is safely truncated to the model's own width.
        """
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        if X.shape[1] > len(self._fm):
            X = X[:, : len(self._fm)]
        a = (X - self._fm) / self._fs
        for W, b in zip(self._W[:-1], self._b[:-1]):
            a = np.maximum(0.0, a @ W + b)  # ReLU hidden layers
        out = (a @ self._W[-1] + self._b[-1]) * self._ts + self._tm  # identity head
        return out[:, 0], out[:, 1]

    def predict_config(self, config):
        from .surrogate_data import config_to_feature_vector

        et, trap = self.predict(config_to_feature_vector(config).reshape(1, -1))
        return float(et[0]), float(trap[0])

    @property
    def n_features(self) -> int:
        """Input width this model was trained on (21 for v1, 26 for v2)."""
        return int(len(self._fm))

    @property
    def envelope(self):
        """Per-feature training envelope as (env_min, env_max) arrays.

        Returns None for v1 artifacts that predate embedded envelopes —
        callers should then fall back to surrogate_data.FEATURE_BOUNDS.
        """
        if self._env_min is None or self._env_max is None:
            return None
        return self._env_min, self._env_max

    @property
    def is_fitted(self) -> bool:
        return True

    @property
    def backend(self) -> str:
        return self._backend
