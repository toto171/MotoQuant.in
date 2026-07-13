"""
test_environmental_surface.py
=============================
Pins the track-surface accuracy fix (July 2 2026).

Before this fix ``EnvironmentalModel.grip_multiplier`` / ``rr_multiplier`` were
computed but never wired into the physics loop, and the API stored the venue's
grip on a phantom ``surface_grip_multiplier`` attribute that nothing read — so
choosing a wet / salt / dry-lake-bed venue had *zero* effect on the predicted
ET. These tests would fail if the wiring is ever removed again.

Invariants:
  1. asphalt (the reference surface) is bit-identical to the shipped baselines,
     so the 502-bike sweep and K5/R1/Busa references never move.
  2. low-grip / high-rolling-resistance surfaces (wet, salt, dry lake bed) are
     strictly slower than asphalt.
  3. a prepped-concrete drag strip is at least as quick as asphalt (it must not
     be *slower*, which is the backwards result the old 0.94 constant produced).
"""

from __future__ import annotations

import motoquant
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

_BASELINES = {
    "K5": (gsxr1000_k5, 9.9331),
    "R1": (yzfr1_4c8, 10.1436),
    "Hayabusa": (hayabusa_gen1, 10.3633),
}


def _et(cfg) -> float:
    return motoquant.MotoQuantEngine(cfg).run().time_quarter


def test_asphalt_baselines_unchanged():
    """Wiring the surface knob must not move the asphalt reference baselines."""
    for name, (fn, target) in _BASELINES.items():
        et = _et(fn())
        assert abs(et - target) < 1e-4, f"{name} moved: {et:.4f} vs {target}"


def test_low_grip_surfaces_are_slower_than_asphalt():
    """Wet / salt / dry-lake-bed launch traction is worse → ET must rise."""
    base = _et(hayabusa_gen1())
    for surface in ("wet", "salt", "dry_lake_bed", "damp"):
        cfg = hayabusa_gen1()
        cfg.environment.track_surface = surface
        et = _et(cfg)
        assert et > base + 0.05, (
            f"{surface} ET {et:.4f} not meaningfully slower than asphalt {base:.4f} "
            f"— surface grip knob is dead again"
        )


def test_prepped_concrete_not_slower_than_asphalt():
    """The catalog's only concrete venues are prepped drag strips; they must
    never come out *slower* than a plain asphalt airstrip (the backwards result
    the old raw-concrete 0.94 factor produced)."""
    base = _et(hayabusa_gen1())
    cfg = hayabusa_gen1()
    cfg.environment.track_surface = "concrete"
    assert _et(cfg) <= base + 1e-6


def test_rolling_resistance_scales_with_surface():
    """RollingResistanceModel must apply the surface factor (salt = 1.35×)."""
    from motoquant.submodels.rolling_resistance import RollingResistanceModel

    cfg = hayabusa_gen1()
    base = RollingResistanceModel(cfg, 1.0).force(50.0, 40.0, cfg.chassis.total_mass_kg)
    salt = RollingResistanceModel(cfg, 1.35).force(
        50.0, 40.0, cfg.chassis.total_mass_kg
    )
    assert abs(salt - base * 1.35) < 1e-6


def test_environment_has_no_phantom_grip_field_write():
    """The API must set the real ``track_surface`` field, not a dead attribute.

    Guards against re-introducing the ``surface_grip_multiplier`` phantom write:
    a fresh EnvironmentParams should not carry that attribute."""
    from motoquant.models import EnvironmentParams

    env = EnvironmentParams()
    assert not hasattr(env, "surface_grip_multiplier"), (
        "surface_grip_multiplier is a dead field — venue grip must flow through "
        "track_surface + EnvironmentalModel instead"
    )
