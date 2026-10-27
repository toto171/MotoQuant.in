"""
test_epoch_physics_launch_floor.py
==================================
2026-10 physics epoch, item 7: energy-consistent launch floor.

Over-clutching transmits more than the engine's steady torque by drawing on
the flywheel (engine + basket inertia). The launch-floor clamp then reset
omega_e back up to the floor every step, so that extra torque was delivered
for the whole slip phase without the flywheel ever losing energy — "torque
from nothing" (+45..+100 % on the over-clutch clusters; audit 2026-10-23).

Now, when the clamp binds, the transmitted torque is the value that lands
omega_e exactly on the floor: engine torque + the flywheel energy actually
released on the way down. Consequences pinned here:
  * launching AT the floor (the 4T default: launch = peak-torque rpm = floor),
    over-clutching contributes exactly nothing — bit-identical ET;
  * launching ABOVE the floor, the flywheel's stored energy is real and
    over-clutching still helps.
"""

from __future__ import annotations

import dataclasses

import motoquant
from motoquant import category_profiles as cp
from motoquant.defaults import hayabusa_gen1

_TAG = "test_epoch_launch_floor"


def _et(torque_limited: bool = False, **knobs) -> float:
    if torque_limited:
        knobs.setdefault("mu_peak_scale", 3.0)  # lift the traction cap
    prof = dataclasses.replace(
        cp.get_profile(cp.CATEGORY_REFERENCE_LITRE_195P), name=_TAG, **knobs
    )
    cp._PROFILES[_TAG] = prof
    try:
        cfg = hayabusa_gen1()
        cfg.category_tag = _TAG
        if torque_limited:
            cfg.wheelie.wheelie_bar = True  # and the wheelie cap
            cfg.wheelie.bar_length_mm = 2000.0
        return motoquant.MotoQuantEngine(cfg).run().time_quarter
    finally:
        cp._PROFILES.pop(_TAG, None)


def test_over_clutch_adds_nothing_when_launching_at_the_floor():
    floor_only = _et(torque_limited=True, launch_floor_factor=1.0)
    over = _et(
        torque_limited=True,
        launch_floor_factor=1.0,
        over_clutch_factor=0.6,
        max_engine_decel_rads2=3000.0,
    )
    # No flywheel energy above the floor → the over-clutch extra is fully
    # refunded every step. (Pre-fix this was ~0.4 s faster.)
    assert over == floor_only


def test_over_clutch_spends_real_flywheel_energy_above_the_floor():
    # Launch at 0.9 x redline (9,900 rpm), ABOVE the 8,500 rpm peak-torque
    # floor: the engine starts with stored flywheel energy, and over-clutching
    # spends it while pulling the engine down onto the torque peak — a
    # genuine gain on a torque-limited launch. (Pulling it BELOW the torque
    # peak is honestly a loss: the flywheel energy released is smaller than
    # the torque given up at the low floor.)
    common = {
        "torque_limited": True,
        "launch_floor_factor": 1.0,
        "launch_rpm_factor": 0.9,
    }
    no_oc = _et(**common)
    oc = _et(**common, over_clutch_factor=0.6, max_engine_decel_rads2=3000.0)
    assert oc < no_oc - 0.005


def test_transmitted_torque_never_exceeds_engine_torque_at_the_floor():
    """Channel-level energy check on the production path: while the engine
    is held at the floor (rpm channel == floor rpm), the drive force implies
    a clutch torque no larger than what the engine makes there."""
    prof = dataclasses.replace(
        cp.get_profile(cp.CATEGORY_REFERENCE_LITRE_195P),
        name=_TAG,
        launch_floor_factor=1.0,
        over_clutch_factor=0.6,
        max_engine_decel_rads2=3000.0,
        mu_peak_scale=3.0,  # lift the traction cap so F_drive is torque-limited
    )
    cp._PROFILES[_TAG] = prof
    try:
        cfg = hayabusa_gen1()
        cfg.category_tag = _TAG
        cfg.wheelie.wheelie_bar = True
        cfg.wheelie.bar_length_mm = 2000.0  # and the wheelie cap
        eng = motoquant.MotoQuantEngine(cfg)
        r = eng.run(rollout_m=0.0)
        floor_rpm = cfg.engine.peak_torque_rpm
        held = (abs(r.rpm - floor_rpm) < 1e-6) & (r.t > 0.15) & (r.traction_pct < 99.0)
        assert held.sum() > 100
        i_total = cfg.drivetrain.overall_ratio(0)
        for i in list(map(int, held.nonzero()[0]))[::50]:
            t_clutch = r.F_drive[i] * r.r_eff[i] / (i_total * eng.eta_dt)
            t_engine = eng.engine_torque(floor_rpm, r.t[i]) * eng.ram_air_power_mult(
                r.v[i]
            )
            assert t_clutch <= t_engine * (1 + 1e-9), (r.t[i], t_clutch, t_engine)
    finally:
        cp._PROFILES.pop(_TAG, None)
