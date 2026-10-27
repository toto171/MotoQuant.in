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


def test_slip_never_drops_when_traction_limited():
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    clipped = r.traction_pct >= 100.0 - 1e-9
    assert clipped.sum() > 500  # the K5 launch is traction-limited
    assert r.slip[clipped].min() >= 0.05 - 1e-12
    assert r.slip.max() <= 0.3 + 1e-12
    gripping = ~clipped & (r.F_drive > 0)
    assert r.slip[gripping].max() <= 0.05 + 1e-12


def test_slip_is_continuous_across_the_limit():
    """Approaching the limit from either side gives the same slip."""
    r = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    clipped = r.traction_pct >= 100.0 - 1e-9
    below = (~clipped) & (r.traction_pct > 99.0)
    assert below.any()
    # just below the limit slip -> 0.05; just above it starts at 0.05 too
    assert abs(r.slip[below].max() - 0.05) < 0.002
    assert abs(r.slip[clipped].min() - 0.05) < 0.002
    # and the published channel has no zero-slip hole during wheelspin
    assert not np.any(r.slip[clipped] < 0.04)
