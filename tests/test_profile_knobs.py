"""
test_profile_knobs.py
=====================
Pins the July 3, 2026 CategoryProfile knob wiring — ``mu_peak_override``,
``launch_rpm_factor`` and ``cd_floor`` (the track_surface pattern: knobs
that were declared in the profile dataclass but never read by physics).

Two invariant classes:

1. NO-OP AT DEFAULTS — the knobs at their default values (
   ``mu_peak_override=None``, ``launch_rpm_factor=None``,
   ``cd_floor=0.25`` — below every catalog Cd: min effective Cd across all
   502 specs is ~0.276 after the rider model's 0.92 race-crouch factor)
   are bit-identical no-ops. Since the 2026-10/11 epoch a few profiles arm
   ``launch_rpm_factor`` / ``wheelie_margin``; the exact armed set is
   pinned below.

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
    "K5": (gsxr1000_k5, 10.0436),
    "R1": (yzfr1_4c8, 10.1092),
    "Hayabusa": (hayabusa_gen1, 10.1100),
}


def _et(cfg) -> float:
    return motoquant.MotoQuantEngine(cfg).run().time_quarter


def _et_with_profile(**knobs) -> float:
    """Run K5 under a synthetic profile cloned from the profile the K5
    actually runs (reference_litre_195p since the 2026-10 epoch — it was
    litre_sport_195p before) with the given knob overrides, cleaning up the
    registry afterwards."""
    prof = dataclasses.replace(
        cp.get_profile(gsxr1000_k5().category_tag), name=_SYNTH_TAG, **knobs
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
#
# 2026-10/11 accuracy epoch (ADR-0002; reports/acc_epoch3_2026_11_03.json,
# reports/acc_final_2026_11_05.json): every grip knob was re-selected FROM
# NEUTRAL. The shipped set arms NO mu_peak_override and NO mu_peak_scale
# (all rated rubber, 1.0); the class bias correctors of 2026-07/08 (1.08 /
# 1.31 / 1.18 ...) are history. The launch is instead shaped by the round-3
# wheelie_margin knob (+ one gate-constrained launch_rpm_factor), pinned
# below.
ACTIVE_MU_OVERRIDES: dict[str, float] = {}

ACTIVE_MU_SCALES: dict[str, float] = {}

# Round-3 launch knobs. litre_sport_195p 0.69 = the CV choice shipped by
# OWNER DECISION 2026-11-05 ('alt_litre195_margin') over the gate escape.
ACTIVE_WHEELIE_MARGINS = {
    "litre_sport_195p": 0.69,
    "litre_sport_600_1000": 0.72,
    "sport_twin_600_1300": 0.75,
    "two_stroke": 0.66,
    "other": 0.66,
    "reference_litre_195p": 0.72,
}

ACTIVE_LAUNCH_RPM_FACTORS = {
    # gate-constrained 'margin+lr' choice (1199 Panigale mass inversion)
    "sport_twin_600_1300": 0.50,
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
    # 2026-10/11 epoch round 3: wired in physics.py (and the Rust core,
    # schema 5); liveness-tested below.
    "wheelie_margin",
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
        expected_lr = ACTIVE_LAUNCH_RPM_FACTORS.get(tag)
        assert prof.launch_rpm_factor == expected_lr, (
            f"{tag}: launch_rpm_factor {prof.launch_rpm_factor} != {expected_lr}"
        )
        expected_margin = ACTIVE_WHEELIE_MARGINS.get(tag, 1.0)
        assert prof.wheelie_margin == expected_margin, (
            f"{tag}: wheelie_margin {prof.wheelie_margin} != {expected_margin}"
        )
        # 0.276 = catalog minimum effective Cd (0.30 × 0.92 race crouch);
        # any floor below that is structurally inert.
        assert prof.cd_floor < 0.276, f"{tag}: cd_floor {prof.cd_floor} is active"


def test_mu_peak_scale_moves_et():
    """Liveness for the July-13 epoch knob: scaling grip down must slow a
    litre bike substantially (production engine path). Since the 2026-10/11
    epoch the K5 launch is wheelie-limited (combined bike + rider CoG
    ceiling), so grip binds over less of the pass: x0.80 now costs ~0.25 s
    (it cost >0.3 s when the launch was traction-limited). The threshold is
    a liveness bound, not an accuracy band."""
    base = _et(gsxr1000_k5())
    low_grip = _et_with_profile(mu_peak_scale=0.80)
    assert low_grip > base + 0.15, (
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


def test_wheelie_margin_moves_et():
    """Liveness for the round-3 epoch knob: holding a smaller share of the
    wheelie ceiling to the 60-ft line must slow the wheelie-limited K5
    launch; riding the full ceiling (1.0) must be quicker than the shipped
    reference margin."""
    base = _et(gsxr1000_k5())
    timid = _et_with_profile(wheelie_margin=0.50)
    full = _et_with_profile(wheelie_margin=1.0)
    assert timid > base + 0.05, (
        f"wheelie_margin is dead (timid): {timid:.4f} vs base {base:.4f}"
    )
    assert full < base - 0.01, (
        f"wheelie_margin is dead (full ceiling): {full:.4f} vs base {base:.4f}"
    )
