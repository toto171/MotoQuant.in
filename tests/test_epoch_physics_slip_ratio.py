"""
test_epoch_physics_slip_ratio.py
================================
2026-10 physics epoch, item 4: slip_ratio is continuous at the traction limit.

Below the limit slip = 0.05·F/F_max (→ 0.05 at the limit). The traction-
limited branch used to restart at 0 (0.1·excess/F_max), so a spinning tyre
read less slip — and generated less friction heat in the tyre thermal model —
than a gripping one (K5: median slip 0.009 while clipped).
"""

from __future__ import annotations

import numpy as np

import motoquant
from motoquant.defaults import gsxr1000_k5


def _traction_limited_k5(mu_peak: float):
    """The K5 on rubber that leaves it traction-limited for part of the run.

    Epoch round 2: the stock reference is WHEELIE-limited off the line (the
    composed bike + rider CoG) and not traction-limited above 2nd gear, so the
    continuity property is exercised on a deliberately low-grip twin. The
    legacy 'unknown' profile carries neutral grip knobs (its defaults are a
    back-compat anchor), so mu_peak here is the tyre's actual peak.
    """
    cfg = gsxr1000_k5()
    cfg.category_tag = "unknown"
    cfg.tires.mu_peak = mu_peak
    return motoquant.MotoQuantEngine(cfg).run()


def _crossing_run():
    """A run that is traction-limited AND has samples just below the limit."""
    for mu in (1.10, 1.20, 1.05, 1.15, 1.25):
        r = _traction_limited_k5(mu)
        clipped = r.traction_pct >= 100.0 - 1e-9
        below = (~clipped) & (r.traction_pct > 99.0)
        if clipped.sum() > 500 and below.any():
            return r
    raise AssertionError("no grip level crosses the traction limit both ways")


def test_slip_never_drops_when_traction_limited():
    r = _crossing_run()
    clipped = r.traction_pct >= 100.0 - 1e-9
    assert clipped.sum() > 500
    assert r.slip[clipped].min() >= 0.05 - 1e-12
    assert r.slip.max() <= 0.3 + 1e-12
    gripping = ~clipped & (r.F_drive > 0)
    assert r.slip[gripping].max() <= 0.05 + 1e-12


def test_slip_is_continuous_across_the_limit():
    """Approaching the limit from either side gives the same slip."""
    r = _crossing_run()
    clipped = r.traction_pct >= 100.0 - 1e-9
    below = (~clipped) & (r.traction_pct > 99.0)
    assert below.any()
    # just below the limit slip -> 0.05; just above it starts at 0.05 too
    assert abs(r.slip[below].max() - 0.05) < 0.002
    assert abs(r.slip[clipped].min() - 0.05) < 0.002
    # and the published channel has no zero-slip hole during wheelspin
    assert not np.any(r.slip[clipped] < 0.04)
