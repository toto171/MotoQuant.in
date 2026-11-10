"""
test_epoch2_physics_cog.py
==========================
2026-10 physics epoch, round 2: the wheelie limit and the load transfer act
at the COMBINED bike + rider centre of mass (motoquant/submodels/cog.py), the
wheelie cap is applied before the traction check, and aerodynamic drag adds
its pitch moment.

Round 1 used the bike-only ``chassis.cog_height_mm`` (540 mm on the K5) as if
it were the system CoG: the wheelie ceiling sat at ~1.35-1.5 g, never bound,
and a sub-1.0 grip retune then left litre bikes traction-limited for the
whole run — where acceleration RISES with mass. These tests pin the
composition, the regime (wheelie-limited launch, not traction-limited above
2nd gear at neutral grip) and mass monotonicity on the references.

"Neutral" runs use the legacy ``unknown`` profile, whose knobs are the
back-compat no-ops (mu_peak_scale 1.0, no launch knobs), so they test the
physics independent of any fitted CategoryProfile value.
"""

from __future__ import annotations

import copy

import numpy as np
import pytest

import motoquant
from motoquant.constants import RIDER_COG_ABOVE_SEAT_PER_STATURE, G
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.submodels.cog import rider_cog_height_m, system_cog

REFS = (gsxr1000_k5, yzfr1_4c8, hayabusa_gen1)


def _neutral(cfg):
    cfg = copy.deepcopy(cfg)
    cfg.category_tag = "unknown"
    return cfg


def _run(cfg, **kw):
    return motoquant.MotoQuantEngine(cfg).run(**kw)


# ── composition ────────────────────────────────────────────────────────────


def test_system_cog_composition_matches_the_documented_formula():
    cfg = gsxr1000_k5()
    c = cfg.chassis
    m_bike = c.dry_mass_kg + c.fluid_mass_kg
    m_rider = c.rider_mass_kg
    h_rider = (
        c.seat_height_mm - cfg.suspension.static_sag_mm
    ) / 1000.0 + RIDER_COG_ABOVE_SEAT_PER_STATURE * cfg.rider.height_cm / 100.0
    assert rider_cog_height_m(cfg) == h_rider
    cog = system_cog(cfg)
    h = (m_bike * c.cog_height_mm / 1000.0 + m_rider * h_rider) / (m_bike + m_rider)
    assert cog.height_m == pytest.approx(h, abs=1e-15)
    assert cog.rider_shift_frac == pytest.approx(m_rider / (m_bike + m_rider))
    assert cog.l_f_m == pytest.approx(
        c.wheelbase_mm / 1000.0 * (1 - c.front_weight_pct)
    )
    # A sport rider sits ~0.95-1.0 m up: the system CoG is well above the
    # bike-only 540 mm, in the 0.6-0.7 m band of a litre bike + rider.
    assert 0.95 < h_rider < 1.02
    assert 0.62 < cog.height_m < 0.70
    # The engine and both sub-models use exactly this geometry.
    eng = motoquant.MotoQuantEngine(cfg)
    for obj in (eng._wt, eng._wheelie):
        assert (obj.L, obj.h, obj.L_f, obj.rider_shift_frac) == (
            cog.wheelbase_m,
            cog.height_m,
            cog.l_f_m,
            cog.rider_shift_frac,
        )


def test_anthropometric_offset_is_the_documented_crouch_value():
    # 0.20 m above the seat for a 1.75 m rider (constants.py derivation).
    assert RIDER_COG_ABOVE_SEAT_PER_STATURE * 1.75 == pytest.approx(0.20, abs=0.005)


def test_mass_moves_the_cog_the_right_way():
    base = system_cog(gsxr1000_k5())
    heavy_rider = gsxr1000_k5()
    heavy_rider.chassis.rider_mass_kg += 20.0
    heavy_bike = gsxr1000_k5()
    heavy_bike.chassis.dry_mass_kg += 20.0
    tall = gsxr1000_k5()
    tall.rider.height_cm = 195.0
    assert system_cog(heavy_rider).height_m > base.height_m  # high mass added
    assert system_cog(heavy_bike).height_m < base.height_m  # low mass added
    assert system_cog(tall).height_m > base.height_m
    # longitudinal position is a property of the bike, not of the masses
    assert system_cog(heavy_rider).l_f_m == base.l_f_m == system_cog(heavy_bike).l_f_m


def test_swingarm_extension_moves_only_the_rear_axle():
    base = system_cog(gsxr1000_k5())
    ext = gsxr1000_k5()
    ext.chassis.swingarm_extension_mm = 152.4
    cog = system_cog(ext)
    assert cog.l_f_m == base.l_f_m
    assert cog.wheelbase_m == pytest.approx(base.wheelbase_m + 0.1524)
    # rear axle -> CoG grows by the FULL extension (was front_weight_pct of it)
    assert ext.chassis.L_r == pytest.approx(gsxr1000_k5().chassis.L_r + 0.1524)


def test_invalid_geometry_is_refused():
    cfg = gsxr1000_k5()
    cfg.chassis.cog_height_mm = 0.0
    with pytest.raises(ValueError):
        system_cog(cfg)


# ── the wheelie limit and the load transfer ───────────────────────────────


def test_rider_lean_moves_only_the_riders_mass_share():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    cfg = eng.cfg
    w = eng._wheelie
    a0 = w.max_accel(0.0, 0.0, eng.m_total)  # t=0: full launch lean
    lean = cfg.rider.cog_offset(0.0) * w.rider_shift_frac
    expect = G * (w.L - (w.L_f - lean)) / w.h * 0.985  # non-counter-rotating
    assert a0 == pytest.approx(expect, rel=1e-12)
    assert lean == pytest.approx(0.08 * w.rider_shift_frac)


def test_drag_pitch_moment_unloads_the_front():
    eng = motoquant.MotoQuantEngine(gsxr1000_k5())
    m = eng.m_total
    f = 600.0
    nf0, nr0 = eng.weight_transfer(3.0, 0.0, 5.0)
    nf1, nr1 = eng.weight_transfer(3.0, 0.0, 5.0, f)
    boost = 1.0 + (eng._wt.anti_squat_frac - 1.0) * 0.15
    assert nr1 - nr0 == pytest.approx(f * eng.h / eng.L * boost, rel=1e-12)
    assert nf0 - nf1 == pytest.approx(f * eng.h / eng.L * boost, rel=1e-12)
    aw0 = eng.max_accel_before_wheelie(0.0, 5.0)
    aw1 = eng.max_accel_before_wheelie(0.0, 5.0, f)
    assert aw0 - aw1 == pytest.approx(f / m * 0.985, rel=1e-12)


@pytest.mark.parametrize("factory", REFS, ids=lambda f: f.__name__)
def test_litre_launch_is_wheelie_limited_at_neutral_grip(factory):
    eng = motoquant.MotoQuantEngine(_neutral(factory()))
    r = eng.run()
    # the launch (after the chain-slack window) up to 1.5 s
    idx = np.flatnonzero((r.t > 0.1) & (r.t < 1.5))
    a = r.a[idx] * G
    aw = np.array(
        [eng.max_accel_before_wheelie(r.v[i], r.t[i], r.F_drag[i]) for i in idx]
    )
    on_limit = np.abs(a - aw) < 1e-3
    assert on_limit.mean() > 0.95, on_limit.mean()
    # front wheel just touching, rear tyre NOT at its limit
    assert np.all(r.traction_pct[idx] < 100.0)
    assert np.all(r.N_front[idx] < 0.06 * eng.m_total * G)
    # the ceiling sits at the ~1.0-1.2 g a 200 hp litre bike pulls
    assert 1.0 * G < aw.mean() < 1.2 * G


@pytest.mark.parametrize("factory", REFS, ids=lambda f: f.__name__)
def test_litre_bikes_are_not_traction_limited_above_second_gear(factory):
    r = _run(_neutral(factory()))
    upper = r.gear >= 3
    assert upper.any()
    assert not np.any(r.traction_pct[upper] >= 100.0 - 1e-9)


def test_rear_load_never_exceeds_the_bikes_weight():
    """The wheelie cap now precedes the load transfer, so the rear load is the
    one at the acceleration the bike actually makes (it was computed from the
    UNcapped demand — above the whole bike's weight on a wheelie-limited
    launch)."""
    for factory in REFS:
        cfg = _neutral(factory())
        r = _run(cfg)
        weight = cfg.chassis.total_mass_kg * G
        assert r.N_rear.max() <= weight * 1.000001


# ── mass and CoG monotonicity ──────────────────────────────────────────────


@pytest.mark.parametrize("factory", REFS, ids=lambda f: f.__name__)
@pytest.mark.parametrize("neutral", (False, True), ids=("profile", "neutral"))
def test_references_are_mass_monotone(factory, neutral):
    """+-10 kg dry mass on each pinned reference: more mass is slower. Runs
    with the references' own (fitted) profile AND neutral knobs — a retune
    that re-creates the round-1 inversion fails here."""
    ets = []
    for dm in (-10.0, 0.0, 10.0):
        cfg = factory()
        if neutral:
            cfg = _neutral(cfg)
        cfg.chassis.dry_mass_kg += dm
        ets.append(_run(cfg).time_quarter)
    assert ets[0] < ets[1] < ets[2], ets


@pytest.mark.parametrize(
    "factory", (hayabusa_gen1, gsxr1000_k5), ids=lambda f: f.__name__
)
def test_raising_the_cog_is_slower_at_neutral_grip(factory):
    """CLAUDE.md (July 2026): 'Hayabusa CoG +55 mm GAINS 0.113 s' — the
    wheelie limit never bound. Now a higher CoG wheelies sooner."""
    ets = []
    for dh in (-55.0, 0.0, 55.0):
        cfg = _neutral(factory())
        cfg.chassis.cog_height_mm += dh
        ets.append(_run(cfg).time_quarter)
    assert ets[0] < ets[1] < ets[2], ets


@pytest.mark.parametrize(
    "factory", (hayabusa_gen1, gsxr1000_k5), ids=lambda f: f.__name__
)
def test_longer_swingarm_quickens_a_wheelie_limited_launch_on_slicks(factory):
    """A 6-in swingarm extension moves the rear axle back -> higher wheelie
    ceiling. On drag-slick grip that is a quicker 60 ft; on street rubber a
    long-wheelbase bike can trade the wheelie limit for the traction limit
    (smaller load transfer h/L) — why the two come together on drag bikes."""

    def run(ext):
        cfg = _neutral(factory())
        cfg.tires.mu_peak = 1.8
        cfg.chassis.swingarm_extension_mm = ext
        return _run(cfg)

    base, r = run(0.0), run(152.4)
    assert r.time_60ft < base.time_60ft - 0.03
    assert r.time_quarter < base.time_quarter
