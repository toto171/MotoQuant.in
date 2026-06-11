"""Train the numpy-servable MLP surrogate — now 100% numpy at TRAIN time too.

Exports MLP weights (indexed keys, no pickled objects) to an .npz the lean API
backend serves via motoquant/analysis/surrogate_numpy.py (numpy-only forward
pass, no torch/sklearn/xgboost anywhere).

v2 changes (June 2026):
  * trainer is hand-rolled numpy Adam — the old sklearn.MLPRegressor
    dependency is gone, so the artifact can be regenerated on the same lean
    environment that serves it;
  * trains on the catalog-wide v2 dataset (scripts/surrogate_v2_gen.py):
    one stock sample per bike_configs row + dense perturbations around 146
    cluster-stratified base bikes;
  * rows flagged kind in {stock_eval, mod_eval} are excluded from training
    AND validation — they are the end-to-end holdout;
  * the artifact now embeds its own training envelope (env_min/env_max over
    all sampled rows incl. catalog stock, padded 0.5%) which
    api._check_envelope / build_optimizer._check_envelope prefer over the
    static FEATURE_BOUNDS table.

Usage:
    python scripts/train_surrogate_numpy.py \
        --data /tmp/mq/surr-data/motoquant_surrogate_v2.npz \
        --out  artifacts/surrogate/surrogate_numpy.npz \
        --hidden 128,64 --epochs 600 --restarts 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EVAL_KINDS = {"stock_eval", "mod_eval"}


def _mlp_init(rng, sizes):
    Ws, bs = [], []
    for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
        Ws.append(rng.normal(0.0, np.sqrt(2.0 / fan_in), (fan_in, fan_out)))
        bs.append(np.zeros(fan_out))
    return Ws, bs


def _forward(Ws, bs, X):
    acts = [X]
    a = X
    for W, b in zip(Ws[:-1], bs[:-1]):
        a = np.maximum(0.0, a @ W + b)
        acts.append(a)
    acts.append(a @ Ws[-1] + bs[-1])
    return acts


def _train_once(
    Xtr, ytr, Xva, yva, hidden, epochs, seed, lr0=2e-3, l2=1e-5, batch=64, patience=80
):
    rng = np.random.default_rng(seed)
    sizes = [Xtr.shape[1], *hidden, ytr.shape[1]]
    Ws, bs = _mlp_init(rng, sizes)
    mW = [np.zeros_like(w) for w in Ws]
    vW = [np.zeros_like(w) for w in Ws]
    mb = [np.zeros_like(b) for b in bs]
    vb = [np.zeros_like(b) for b in bs]
    b1, b2, eps = 0.9, 0.999, 1e-8
    t = 0
    best = (np.inf, None, None, -1)
    n = len(Xtr)
    for ep in range(epochs):
        lr = lr0 * 0.5 * (1.0 + np.cos(np.pi * ep / max(1, epochs)))
        idx = rng.permutation(n)
        for s0 in range(0, n, batch):
            bidx = idx[s0 : s0 + batch]
            Xb, yb = Xtr[bidx], ytr[bidx]
            acts = _forward(Ws, bs, Xb)
            delta = 2.0 * (acts[-1] - yb) / len(Xb)  # dMSE/dout
            gW = [None] * len(Ws)
            gb = [None] * len(bs)
            for li in range(len(Ws) - 1, -1, -1):
                gW[li] = acts[li].T @ delta + l2 * Ws[li]
                gb[li] = delta.sum(axis=0)
                if li > 0:
                    delta = (delta @ Ws[li].T) * (acts[li] > 0)
            t += 1
            corr = (1 - b1**t, 1 - b2**t)
            for li in range(len(Ws)):
                mW[li] = b1 * mW[li] + (1 - b1) * gW[li]
                vW[li] = b2 * vW[li] + (1 - b2) * gW[li] ** 2
                Ws[li] -= lr * (mW[li] / corr[0]) / (np.sqrt(vW[li] / corr[1]) + eps)
                mb[li] = b1 * mb[li] + (1 - b1) * gb[li]
                vb[li] = b2 * vb[li] + (1 - b2) * gb[li] ** 2
                bs[li] -= lr * (mb[li] / corr[0]) / (np.sqrt(vb[li] / corr[1]) + eps)
        pv = _forward(Ws, bs, Xva)[-1]
        va = float(np.mean(np.abs(pv[:, 0] - yva[:, 0])))  # standardized ET MAE
        if va < best[0] - 1e-5:
            best = (va, [w.copy() for w in Ws], [b.copy() for b in bs], ep)
        elif ep - best[3] > patience:
            break
    return best


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="/tmp/mq/surr-data/motoquant_surrogate_v2.npz")
    ap.add_argument("--out", default="artifacts/surrogate/surrogate_numpy.npz")
    ap.add_argument("--hidden", default="128,64")
    ap.add_argument("--epochs", type=int, default=600)
    ap.add_argument("--restarts", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val-frac", type=float, default=0.15)
    a = ap.parse_args()
    hidden = tuple(int(x) for x in a.hidden.split(","))

    d = np.load(a.data, allow_pickle=False)
    X_all = d["X"].astype(np.float64)
    y_all = np.column_stack([d["y_et"], d["y_trap"]]).astype(np.float64)
    feat_names = [str(s) for s in d["feature_names"]]
    kind = (
        np.array([str(s) for s in d["kind"]])
        if "kind" in d.files
        else np.array(["sample"] * len(X_all))
    )

    train_mask = ~np.isin(kind, list(EVAL_KINDS))
    X, y = X_all[train_mask], y_all[train_mask]

    rng = np.random.default_rng(a.seed)
    idx = rng.permutation(len(X))
    nva = max(1, int(len(X) * a.val_frac))
    va_i, tr_i = idx[:nva], idx[nva:]
    Xtr, Xva, ytr, yva = X[tr_i], X[va_i], y[tr_i], y[va_i]

    fmean, fstd = Xtr.mean(0), Xtr.std(0)
    fstd[fstd == 0] = 1.0
    tmean, tstd = ytr.mean(0), ytr.std(0)
    tstd[tstd == 0] = 1.0
    Xtr_s, Xva_s = (Xtr - fmean) / fstd, (Xva - fmean) / fstd
    ytr_s, yva_s = (ytr - tmean) / tstd, (yva - tmean) / tstd

    t0 = time.perf_counter()
    best = (np.inf, None, None, -1)
    for r in range(a.restarts):
        cand = _train_once(
            Xtr_s, ytr_s, Xva_s, yva_s, hidden, a.epochs, a.seed + 1000 * r
        )
        print(f"  restart {r}: val std-MAE(et)={cand[0]:.4f} (best epoch {cand[3]})")
        if cand[0] < best[0]:
            best = cand
    Ws = [w.astype(np.float32) for w in best[1]]
    bs = [b.astype(np.float32) for b in best[2]]
    print(
        f"trained in {time.perf_counter() - t0:.1f}s, layers={len(Ws)} hidden={hidden}"
    )

    def fwd(Xq):
        aq = (np.asarray(Xq, dtype=np.float64) - fmean) / fstd
        for W, b in zip(Ws[:-1], bs[:-1]):
            aq = np.maximum(0.0, aq @ W + b)
        return (aq @ Ws[-1] + bs[-1]) * tstd + tmean

    pv = fwd(Xva)
    err_et = pv[:, 0] - yva[:, 0]
    err_tr = (pv[:, 1] - yva[:, 1]) * 3.6
    mae_et = float(np.mean(np.abs(err_et)) * 1000)
    rmse_et = float(np.sqrt(np.mean(err_et**2)) * 1000)
    r2_et = float(1 - np.sum(err_et**2) / np.sum((yva[:, 0] - yva[:, 0].mean()) ** 2))
    mae_trap = float(np.mean(np.abs(err_tr)))
    print(
        f"holdout (n={nva}): ET MAE={mae_et:.1f}ms RMSE={rmse_et:.1f}ms R2={r2_et:.4f} | trap MAE={mae_trap:.2f} km/h"
    )

    # Envelope: min/max over EVERY sampled row (training + the catalog-stock
    # eval rows — those are real, expected inputs), padded 0.5% per side.
    span = X_all.max(0) - X_all.min(0)
    env_min = X_all.min(0) - 0.005 * span
    env_max = X_all.max(0) + 0.005 * span

    out = {
        "n_layers": np.array([len(Ws)]),
        "feat_mean": fmean.astype(np.float32),
        "feat_std": fstd.astype(np.float32),
        "tgt_mean": tmean.astype(np.float32),
        "tgt_std": tstd.astype(np.float32),
        "feature_names": np.array(feat_names),
        "env_min": env_min.astype(np.float32),
        "env_max": env_max.astype(np.float32),
        "meta": np.array([len(X), nva, mae_et, mae_trap], dtype=np.float64),
        "meta_json": np.array(
            [
                json.dumps(
                    {
                        "version": 2,
                        "trained": time.strftime("%Y-%m-%d"),
                        "data": str(a.data),
                        "n_train": int(len(tr_i)),
                        "n_val": int(nva),
                        "hidden": list(hidden),
                        "val_mae_et_ms": round(mae_et, 1),
                        "val_rmse_et_ms": round(rmse_et, 1),
                        "val_r2_et": round(r2_et, 4),
                        "val_mae_trap_kmh": round(mae_trap, 2),
                    }
                )
            ]
        ),
    }
    for i, (W, b) in enumerate(zip(Ws, bs)):
        out[f"W{i}"] = W
        out[f"b{i}"] = b
    outp = Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    np.savez(outp, **out)
    print(f"exported {outp} ({outp.stat().st_size} bytes)")

    import motoquant

    for name, fn in [
        ("K5", motoquant.gsxr1000_k5),
        ("R1", motoquant.yzfr1_4c8),
        ("Busa", motoquant.hayabusa_gen1),
    ]:
        from motoquant.analysis.surrogate_data import config_to_feature_vector

        fv = config_to_feature_vector(fn()).reshape(1, -1).astype(np.float64)
        p = fwd(fv)
        phys = motoquant.MotoQuantEngine(fn()).run().time_quarter
        print(
            f"  {name}: surrogate ET={p[0, 0]:.3f}s trap={p[0, 1] * 3.6:.1f} | physics={phys:.3f}s | d={p[0, 0] - phys:+.3f}"
        )


if __name__ == "__main__":
    main()
