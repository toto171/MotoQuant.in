# MotoQuant Surrogate Artifacts

## Files

| Name                                    | What it is                           | Size    |
|-----------------------------------------|--------------------------------------|---------|
| `motoquant_surrogate_v1_1k5.npz`        | Training dataset (features + labels) | 128 KB  |
| `motoquant_surrogate_v1_1k5.pkl`        | Fitted XGBoost model (ET + trap)     | 1.3 MB  |

## How the v1 baseline was trained

```bash
# 1. Generate Sobol-sampled training data from the GSX-R 1000 K5 template
python -m motoquant.run analysis surrogate generate \
  --n-samples 1500 \
  --seed 42 \
  --output artifacts/surrogate/motoquant_surrogate_v1_1k5.npz

# 2. Fit XGBoost surrogate (ET regressor + trap-speed regressor)
python -m motoquant.run analysis surrogate train \
  --data     artifacts/surrogate/motoquant_surrogate_v1_1k5.npz \
  --model-out artifacts/surrogate/motoquant_surrogate_v1_1k5.pkl
```

## v1 quality (test-set, 225 held-out samples)

| Metric              | ET        | Trap speed   |
|---------------------|-----------|--------------|
| MAE                 | 534.6 ms  | 6.93 km/h    |
| RMSE                | 713.6 ms  | 9.27 km/h    |
| R²                  | 0.9516    | 0.9445       |
| Within ±50 ms / ±1 km/h | 5.8 % | 12.0 %       |

Inference latency: **~1–3 ms per prediction** (≈ 130–400× faster than running the
full 15-sub-model physics engine, which takes ~400 ms).

Sanity check on the three reference baselines:

| Bike     | Surrogate ET | Physics ET | Δ         |
|----------|--------------|------------|-----------|
| GSX-R K5 | 10.499 s     | 10.034 s   | +0.465 s  |
| R1 4C8   | 10.609 s     | 10.286 s   | +0.323 s  |
| Hayabusa | 10.850 s     | 10.472 s   | +0.378 s  |

All three within one MAE of the truth — the model has learned the dominant
variance but lacks the samples to nail the tails.

## Why the v1 uses 1 500 samples

1 500 Sobol-sampled runs is the largest volume that completes in a reasonable
time on CI-class hardware (~12 minutes at ~2 sims/s). It's enough to ship a
usable artifact so the `motoquant analysis surrogate predict` CLI works
end-to-end, but **it is not the production-accuracy model**.

## Production training (your workstation)

Re-run on local hardware with 10–50 k samples for production accuracy. The
Phase 4A CLAUDE.md spec targets **MAE < 50 ms** on ET, which empirically needs
somewhere around 30–50 k samples.

```bash
python -m motoquant.run analysis surrogate generate \
  --n-samples 30000 \
  --seed 42 \
  --output artifacts/surrogate/motoquant_surrogate_v2_30k.npz

python -m motoquant.run analysis surrogate train \
  --data     artifacts/surrogate/motoquant_surrogate_v2_30k.npz \
  --model-out artifacts/surrogate/motoquant_surrogate_v2_30k.pkl
```

Expected wall-clock on a modern 8-core CPU: ~100 min generate + ~30 s train.

## Use from Python

```python
from motoquant.analysis.surrogate_xgb import XGBSurrogate
from motoquant.analysis.surrogate_data import config_to_feature_vector
from motoquant.defaults import gsxr1000_k5

surr = XGBSurrogate.load("artifacts/surrogate/motoquant_surrogate_v1_1k5.pkl")
cfg = gsxr1000_k5()
features = config_to_feature_vector(cfg).reshape(1, -1)
et_s, trap_mps = surr.predict(features)
print(f"ET = {et_s[0]:.3f}s  trap = {trap_mps[0] * 3.6:.1f} km/h")
```
