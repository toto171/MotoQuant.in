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

    def __init__(self, weights, biases, feat_mean, feat_std, tgt_mean, tgt_std,
                 feature_names, meta=None):
        self._W = weights
        self._b = biases
        self._fm = feat_mean
        self._fs = feat_std
        self._tm = tgt_mean
        self._ts = tgt_std
        self.feature_names = list(feature_names)
        self.meta = meta
        self._backend = "numpy"

    @classmethod
    def load(cls, path: str | Path) -> NumpySurrogate:
        d = np.load(str(path), allow_pickle=False)
        n = int(d["n_layers"][0])
        W = [d[f"W{i}"].astype(np.float64) for i in range(n)]
        b = [d[f"b{i}"].astype(np.float64) for i in range(n)]
        return cls(
            W, b,
            d["feat_mean"].astype(np.float64), d["feat_std"].astype(np.float64),
            d["tgt_mean"].astype(np.float64), d["tgt_std"].astype(np.float64),
            [str(s) for s in d["feature_names"]],
            d["meta"] if "meta" in d.files else None,
        )

    def predict(self, X):
        """X: (n,21) or (21,). Returns (et_s array, trap_mps array)."""
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        a = (X - self._fm) / self._fs
        for W, b in zip(self._W[:-1], self._b[:-1]):
            a = np.maximum(0.0, a @ W + b)          # ReLU hidden layers
        out = (a @ self._W[-1] + self._b[-1]) * self._ts + self._tm  # identity head
        return out[:, 0], out[:, 1]

    def predict_config(self, config):
        from .surrogate_data import config_to_feature_vector
        et, trap = self.predict(config_to_feature_vector(config).reshape(1, -1))
        return float(et[0]), float(trap[0])

    @property
    def is_fitted(self) -> bool:
        return True

    @property
    def backend(self) -> str:
        return self._backend
