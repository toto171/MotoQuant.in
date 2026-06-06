"""Train a torch-free, numpy-servable MLP surrogate from a SurrogateDataset .npz.

Exports MLP weights (indexed keys, no pickled objects) to surrogate_numpy.npz so
the lean API backend (numpy-only; no torch/sklearn/xgboost) can serve
/api/surrogate/predict via a pure-numpy forward pass — see
motoquant/analysis/surrogate_numpy.py. sklearn is a TRAIN-TIME-only dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA = Path("artifacts/surrogate/motoquant_surrogate_v1_1k5.npz")
OUT = Path("surrogate_numpy.npz")
HIDDEN = (96, 64)


def main() -> None:
    d = np.load(DATA, allow_pickle=True)
    X = d["X"].astype(np.float64)
    y = np.column_stack([d["y_et"], d["y_trap"]]).astype(np.float64)  # [et_s, trap_mps]
    feat_names = [str(s) for s in d["feature_names"]]

    rng = np.random.default_rng(42)
    idx = rng.permutation(len(X))
    ntest = max(1, len(X) // 6)
    te, tr = idx[:ntest], idx[ntest:]
    Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]

    fmean, fstd = Xtr.mean(0), Xtr.std(0)
    fstd[fstd == 0] = 1.0
    tmean, tstd = ytr.mean(0), ytr.std(0)
    tstd[tstd == 0] = 1.0

    from sklearn.neural_network import MLPRegressor

    mlp = MLPRegressor(
        hidden_layer_sizes=HIDDEN,
        activation="relu",
        solver="adam",
        alpha=1e-4,
        max_iter=4000,
        early_stopping=True,
        n_iter_no_change=40,
        random_state=42,
    )
    mlp.fit((Xtr - fmean) / fstd, (ytr - tmean) / tstd)

    Ws = [w.astype(np.float32) for w in mlp.coefs_]
    bs = [b.astype(np.float32) for b in mlp.intercepts_]

    def fwd(Xq):
        a = (Xq - fmean) / fstd
        for W, b in zip(Ws[:-1], bs[:-1]):
            a = np.maximum(0.0, a @ W + b)
        return (a @ Ws[-1] + bs[-1]) * tstd + tmean

    pe = fwd(Xte)
    mae_et = float(np.mean(np.abs(pe[:, 0] - yte[:, 0])) * 1000)
    mae_trap = float(np.mean(np.abs((pe[:, 1] - yte[:, 1]) * 3.6)))
    print(
        f"test MAE: ET={mae_et:.1f} ms  trap={mae_trap:.2f} km/h  (n_test={ntest}, layers={len(Ws)})"
    )

    out = {
        "n_layers": np.array([len(Ws)]),
        "feat_mean": fmean.astype(np.float32),
        "feat_std": fstd.astype(np.float32),
        "tgt_mean": tmean.astype(np.float32),
        "tgt_std": tstd.astype(np.float32),
        "feature_names": np.array(feat_names),
        "meta": np.array([len(X), ntest, mae_et, mae_trap], dtype=np.float64),
    }
    for i, (W, b) in enumerate(zip(Ws, bs)):
        out[f"W{i}"] = W
        out[f"b{i}"] = b
    np.savez(OUT, **out)
    import shutil

    shutil.copy(OUT, "artifacts/surrogate/surrogate_numpy.npz")
    print(f"exported {OUT} ({OUT.stat().st_size} bytes)")

    import motoquant
    from motoquant.analysis.surrogate_data import config_to_feature_vector

    for name, fn in [
        ("K5", motoquant.gsxr1000_k5),
        ("R1", motoquant.yzfr1_4c8),
        ("Busa", motoquant.hayabusa_gen1),
    ]:
        fv = config_to_feature_vector(fn()).reshape(1, -1).astype(np.float64)
        p = fwd(fv)
        phys = motoquant.MotoQuantEngine(fn()).run().time_quarter
        print(
            f"  {name}: surrogate ET={p[0, 0]:.3f}s trap={p[0, 1] * 3.6:.1f} | physics={phys:.3f}s | d={p[0, 0] - phys:+.3f}"
        )


if __name__ == "__main__":
    main()
