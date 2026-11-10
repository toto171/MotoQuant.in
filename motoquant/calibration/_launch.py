"""
Shared motion-onset estimation for GPS / ECU run detection.

Run detectors find the first sample whose speed reaches a small threshold
(~0.8 m/s).  Re-zeroing the clock at that sample drops the time the vehicle
spent accelerating up to the threshold (~0.1 s) plus the sampling quantisation,
so measured elapsed times read quicker than the vehicle's real motion-onset ET.

Uploaded runs are therefore re-zeroed at the back-extrapolated moment of
motion onset (v = 0).  That is the convention every overlay / calibration
simulation uses: ``run(rollout_m=0.0)`` times the run from rest, with no
1-ft rollout, so a GPS / ECU log and the simulation are compared like with
like (see calibrator._Objective, the API's Dragy overlay and the CLI overlay).
"""

from __future__ import annotations

import numpy as np

# Samples at/after the threshold crossing used for the linear v(t) fit.
_FIT_SAMPLES = 3
# Speed below which a sample is definitely stationary (m/s).
_STATIONARY_MS = 0.05
# How far back from the threshold crossing motion onset can lie: the fit is
# clamped to the last stationary sample inside this look-back, else to the
# look-back itself.  Bounded in time AND in samples so a crafted log (thousands
# of staged windows, or repeated / non-monotonic timestamps) costs O(1) per
# launch, never O(file length) — the run detectors are linear in the file.
_MAX_LEAD_S = 1.0
_MAX_LOOKBACK_SAMPLES = 2048


def launch_origin_time(t: np.ndarray, v: np.ndarray, launch_idx: int) -> float:
    """
    Motion-onset time t0 (v = 0) for a run whose first at/above-threshold sample
    is ``launch_idx``.

    Fits v = a (t - t0) through up to three samples starting at ``launch_idx``.
    t0 is clamped to [last stationary sample within the previous second (else
    one second before the crossing), t[launch_idx]]; it falls back to
    t[launch_idx] when the fitted slope is not positive, the fit is not finite
    or fewer than two samples are available.
    """
    t_li = float(t[launch_idx])
    lo = t_li - _MAX_LEAD_S
    start = max(0, launch_idx - _MAX_LOOKBACK_SAMPLES)
    recent = (t[start:launch_idx] >= lo) & (v[start:launch_idx] < _STATIONARY_MS)
    still = np.flatnonzero(recent)
    if len(still):
        lo = float(t[start + int(still[-1])])
    k = min(_FIT_SAMPLES, len(t) - launch_idx)
    if k < 2:
        return t_li
    tt, vv = t[launch_idx : launch_idx + k], v[launch_idx : launch_idx + k]
    span = float(tt[-1] - tt[0])
    if not (span > 0.0) or not np.all(np.isfinite(vv)):
        return t_li  # repeated timestamps / gaps: no slope to fit
    # Least-squares slope of v(t) (closed form; same line np.polyfit(deg=1) fits).
    tc = tt - tt.mean()
    denom = float(np.dot(tc, tc))
    if not (denom > 0.0):
        return t_li
    a = float(np.dot(tc, vv - vv.mean())) / denom
    if not (a > 0.0) or not np.isfinite(a):
        return t_li
    t0 = float(tt[0] - vv[0] / a)
    return min(max(t0, lo), t_li)


def launch_slice(
    t: np.ndarray, v: np.ndarray, launch_idx: int, end_idx: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """
    ``(t, v)`` of a run from ``launch_idx`` (through ``end_idx`` inclusive, or to
    the end), with time re-zeroed at motion onset and a virtual ``v = 0`` sample
    prepended at t = 0 when onset precedes the first sample.
    """
    t0 = launch_origin_time(t, v, launch_idx)
    stop = None if end_idx is None else end_idx + 1
    t_s, v_s = t[launch_idx:stop], v[launch_idx:stop]
    if t0 < t_s[0]:
        t_s = np.concatenate([[t0], t_s])
        v_s = np.concatenate([[0.0], v_s])
    return t_s - t0, v_s.copy()
