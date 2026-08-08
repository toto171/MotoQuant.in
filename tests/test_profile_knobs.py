"""
test_profile_knobs.py
=====================
Pins the July 3, 2026 CategoryProfile knob wiring — ``mu_peak_override``,
``launch_rpm_factor`` and ``cd_floor`` (the track_surface pattern: knobs
that were declared in the profile dataclass but never read by physics).

Two invariant classes:

1. NO-OP AT DEFAULTS — every registered profile ships
   ``mu_peak_override=None``, ``launch_rpm_factor=None`` and
   ``cd_floor=0.25`` (below every catalog Cd: min effective Cd across all
   502 specs is ~0.276 after the rider model's 0.92 race-crouch factor).
   Wiring the knobs must therefore leave the pinned reference baselines
   bit-identical.

2. LIVENESS — each knob, when set to a non-default value on a synthetic
   profile, MUST move the ET.  This is the whole point of the wiring: the
   knobs can never silently go dead again.  If a refactor disconnects a
   knob, the corresponding test here fails loudly.
"""

from __future__ import annotations

import dataclasses

import motoquant
from motoquant import category_profiles as cp
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

_SYNTH_TAG = "test_synth_profile_knobs"

_BASELINES = {
    "K5": (gsxr1000_k5, 9.9331),
    "R1": (yzfr1_4c8, 10.1436),
    "Hayabusa": (hayabusa_gen1, 10.3633),
}


def _et(cfg) -> float:
    return motoquant.MotoQuantEngine(cfg).run().time_quarter


def _et_with_profile(**knobs) -> float:
    """Run K5 under a synthetic profile cloned from litre_sport_195p with
    the given knob overrides, cleaning up the registry afterwards."""
    prof = dataclasses.replace(
        cp.get_profile(cp.CATEGORY_LITRE_SPORT_195P), name=_SYNTH_TAG, **knobs
    )
    cp._PROFILES[_SYNTH_TAG] = prof
    try:
        cfg = gsxr1000_k5()
        cfg.category_tag = _SYNTH_TAG
        return _et(cfg)
    finally:
        cp._PROFILES.pop(_SYNTH_TAG, None)


# ─────────────────────────────────────────────────────────────────────────
# 1. No-op at default values
# ─────────────────────────────────────────────────────────────────────────


def test_reference_baselines_unchanged():
    """Wiring the three knobs must not move the reference baselines."""
    for name, (fn, target) in _BASELINES.items():
        et = _et(fn())
        assert abs(et - target) < 1e-4, f"{name} moved: {et:.4f} vs {target}"


def test_default_knob_values_are_bit_identical():
    """A profile with the knobs explicitly at their shipped defaults must
    reproduce the stock K5 ET *exactly* (bit-identical, not just close)."""
    base = _et(gsxr1000_k5())
    explicit = _et_with_profile(
        mu_peak_override=None, launch_rpm_factor=None, cd_floor=0.25
    )
    assert explicit == base, (
        f"default knob values changed the trajectory: {explicit!r} vs {base!r}"
    )


# July 6, 2026: the full-corpus recalibration (3-bike-pin retired) armed
# mu_peak_override on two profiles. July 13, 2026: the traction-cap epoch
# re-centered every cluster with the new multiplicative mu_peak_scale knob
# (grids vs the 277-match weighted corpus; see category_profiles.py inline
# rationale) and moved single_300_500's override 1.10 → 1.18.
# Any OTHER profile arming a knob must still be a conscious, test-updating
# change — that is this guard's job.
ACTIVE_MU_OVERRIDES = {
    "sport_twin_600_1300": 1.31,
    "single_300_500": 1.18,
}

ACTIVE_MU_SCALES = {
    "litre_sport_195p": 1.08,
    "litre_sport_600_1000": 1.07,
    "sport_twin_600_1300": 1.085,
    "mid_twin_500_700": 1.14,
    # 2026-08-08 crank-semantics retune (see category_profiles.py comments
    # + reports/session_2026_08_08_full_night_run.md): mid_twin_300_500
    # 1.12 -> 1.20, small_i4_screamer 1.30 -> 1.00 (the 1.30 was fit to the
    # pre-instrumented optimistic ZX-25R row), entry_200_300 newly active
    # at 1.12. Final weighted sweep: w|d| 0.2721 -> 0.2645, bias +0.0089.
    "mid_twin_300_500": 1.20,
    "two_stroke": 1.15,
    "cruiser_1300p": 1.20,
    "other": 1.15,
    "small_i4_screamer": 1.00,
    "entry_200_300": 1.12,
}

# July 17, 2026: the LIVE CategoryProfile knob inventory, pinned as an exact
# set. The six dead knobs (tuck_transition_time_s, cd_ceiling, pacejka_C,
# load_sensitivity_k, engine_inertia_mult, chain_efficiency_override) were
# DELETED that day — zero consumers; intended values recorded in
# reports/session_2026_07_10_physics_foundations_review.md; re-wiring any of
# them is epoch-gated (ADR-0002). Adding a profile field — or resurrecting a
# deleted one — must consciously update this set AND wire + liveness-test it.
LIVE_PROFILE_KNOBS = {
    "over_clutch_factor",
    "max_engine_decel_rads2",
    "launch_floor_factor",
    "cd_floor",
    "mu_peak_override",
    "mu_peak_scale",
    "parasitic_mult",
    "launch_rpm_factor",
}


def test_profile_field_inventory_is_exact():
    """CategoryProfile carries EXACTLY the live knobs plus name/notes —
    no dead fields may accumulate again (KNOWN_TRAPS T11 pattern)."""
    actual = {f.name for f in dataclasses.fields(cp.CategoryProfile)}
    assert actual == LIVE_PROFILE_KNOBS | {"name", "notes"}, (
        f"CategoryProfile field drift: unexpected {actual - LIVE_PROFILE_KNOBS - {'name', 'notes'}}, "
        f"missing {(LIVE_PROFILE_KNOBS | {'name', 'notes'}) - actual}"
    )


def test_every_registered_profile_ships_expected_knob_values():
    """Guard: only the calibrated profiles listed in ACTIVE_MU_OVERRIDES /
    ACTIVE_MU_SCALES set the wired grip knobs to an active value, and to
    exactly the calibrated numbers. If a future calibration pass activates
    another one, this test forces that change to be made consciously (with
    a weighted-sweep gate) rather than slipping in silently."""
    for tag, prof in cp._PROFILES.items():
        expected_mu = ACTIVE_MU_OVERRIDES.get(tag)
        assert prof.mu_peak_override == expected_mu, (
            f"{tag}: mu_peak_override {prof.mu_peak_override} != {expected_mu}"
        )
        expected_scale = ACTIVE_MU_SCALES.get(tag, 1.0)
        assert prof.mu_peak_scale == expected_scale, (
            f"{tag}: mu_peak_scale {prof.mu_peak_scale} != {expected_scale}"
        )
        assert prof.launch_rpm_factor is None, f"{tag}: launch_rpm_factor active"
        # 0.276 = catalog minimum effective Cd (0.30 × 0.92 race crouch);
        # any floor below that is structurally inert.
        assert prof.cd_floor < 0.276, f"{tag}: cd_floor {prof.cd_floor} is active"


def test_mu_peak_scale_moves_et():
    """Liveness for the July-13 epoch knob: scaling grip down must slow a
    traction-limited litre bike substantially (production engine path)."""
    base = _et(gsxr1000_k5())
    low_grip = _et_with_profile(mu_peak_scale=0.80)
    assert low_grip > base + 0.3, (
        f"mu_peak_scale is dead: {low_grip:.4f} vs base {base:.4f}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 2. Liveness — non-default values must move the ET
# ─────────────────────────────────────────────────────────────────────────


def test_mu_peak_override_moves_et():
    """Lower grip must slow a traction-limited litre bike substantially."""
    base = _et(gsxr1000_k5())
    low_grip = _et_with_profile(mu_peak_override=0.85)
    assert low_grip > base + 0.5, (
        f"mu_peak_override is dead: {low_grip:.4f} vs base {base:.4f}"
    )


def test_launch_rpm_factor_moves_et():
    """Launching at 30% of redline must bog the launch and move the ET."""
    base = _et(gsxr1000_k5())
    bogged = _et_with_profile(launch_rpm_factor=0.30)
    assert abs(bogged - base) > 0.1, (
        f"launch_rpm_factor is dead: {bogged:.4f} vs base {base:.4f}"
    )


def test_cd_floor_moves_et():
    """A floor above the config's effective Cd must add drag and slow the
    bike (K5 tuck Cd*A ≈ 0.30 × A; a 1.2 floor quadruples the drag area)."""
    base = _et(gsxr1000_k5())
    draggy = _et_with_profile(cd_floor=1.2)
    assert draggy > base + 0.1, f"cd_floor is dead: {draggy:.4f} vs base {base:.4f}"
