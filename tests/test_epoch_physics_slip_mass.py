"""
test_epoch_physics_slip_mass.py
===============================
2026-10 physics epoch, item 2: the engine + clutch-basket inertia is NOT part
of the vehicle's effective mass while the clutch slips.

During slip run() integrates omega_e separately (d_omega_e = T_net / I_e);
counting (I_e + I_basket)·(i_total / r_w)² in m_eff as well was a phantom
~53 kg (K5) / ~74 kg (Hayabusa) in first gear for the whole launch
(reports/audit_core_2026_10_23_partial.md). The tests reconstruct the mass the
loop actually used from the published channels (a = (F_drive - F_drag - F_rr
- F_gradient) / m_eff on flat ground), so they fail if the fix is reverted.
"""

from __future__ import annotations

import numpy as np

import motoquant
from motoquant.constants import G
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1


def _used_mass(r, i):
    a = r.a[i] * G
    return (r.F_drive[i] - r.F_drag[i] - r.F_rr[i]) / a


def test_effective_mass_slipping_is_wheels_only():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    m = eng.m_total
    slipping = eng._drivetrain.effective_mass_slipping(m)
    locked = eng.effective_mass(0)
    tire = eng.cfg.tires
    r_w = tire.rear_rolling_radius_m
    r_f = tire.front_rolling_radius_m or r_w
    expect = m + tire.rear_inertia_kgm2 / r_w**2 + tire.front_inertia_kgm2 / r_f**2
    assert slipping == expect
    # The engine term in first gear is tens of kg on a litre bike.
    assert locked - slipping > 40.0


def test_run_uses_slipping_mass_until_lock_then_full_mass():
    cfg = hayabusa_gen1()
    eng = motoquant.MotoQuantEngine(cfg)
    r = eng.run(rollout_m=0.0)
    m_slip = eng._drivetrain.effective_mass_slipping(cfg.chassis.total_mass_kg)
    # Early launch: clutch slipping (rpm held, not tied to wheel speed),
    # positive acceleration. t in (0.2, 0.6) s avoids the chain-slack window.
    idx = np.flatnonzero((r.t > 0.2) & (r.t < 0.6))
    used = np.array([_used_mass(r, i) for i in idx])
    # fuel burn changes m by < 0.1 kg over this window
    assert np.all(np.abs(used - m_slip) < 0.2), (used.min(), used.max(), m_slip)
    # Late in the run the clutch is locked: the full gear mass applies.
    i = int(np.searchsorted(r.t, 8.0))
    g = int(r.gear[i]) - 1
    full = eng.effective_mass(g)
    assert abs(_used_mass(r, i) - full) < 0.5


def test_lighter_bike_has_a_quicker_60ft():
    """Mass-sign sanity the audit found broken: with the phantom slip-phase
    mass, -10 kg on the K5 made the 60 ft SLOWER (+5 ms)."""
    base = motoquant.MotoQuantEngine(gsxr1000_k5()).run()
    light = gsxr1000_k5()
    light.chassis.dry_mass_kg -= 10.0
    r = motoquant.MotoQuantEngine(light).run()
    assert r.time_60ft < base.time_60ft
    assert r.time_quarter < base.time_quarter
