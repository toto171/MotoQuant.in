"""
test_epoch_physics_reference_profile.py
========================================
2026-10 physics epoch, item 1: the three pinned reference bikes are decoupled
from the catalog's ``litre_sport_195p`` cluster.

Before the epoch the references (defaults.py K5 / R1 4C8 / Hayabusa Gen1)
shared ``litre_sport_195p`` with ~30 catalog bikes, so any catalog retune of
that cluster silently moved the pinned baselines. They now carry the frozen
``reference_litre_195p`` profile. These tests pin the MECHANISM (who reads
which profile), not ET values — the reference profile is tuned against the
references' published figures in a later pass.
"""

from __future__ import annotations

import dataclasses

import pytest

import motoquant
from motoquant import category_profiles as cp
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8

REFS = (gsxr1000_k5, yzfr1_4c8, hayabusa_gen1)


def _et(cfg) -> float:
    return motoquant.MotoQuantEngine(cfg).run().time_quarter


@pytest.mark.parametrize("factory", REFS, ids=lambda f: f.__name__)
def test_references_carry_the_frozen_reference_profile(factory):
    cfg = factory()
    assert cfg.category_tag == cp.CATEGORY_REFERENCE_LITRE_195P
    eng = motoquant.MotoQuantEngine(cfg)
    assert eng._profile.name == cp.CATEGORY_REFERENCE_LITRE_195P


def test_reference_profile_is_registered_and_never_derived():
    assert cp.CATEGORY_REFERENCE_LITRE_195P in cp.ALL_CATEGORIES
    assert cp.get_profile(cp.CATEGORY_REFERENCE_LITRE_195P).name == (
        cp.CATEGORY_REFERENCE_LITRE_195P
    )
    # The taxonomy can never route a catalog bike onto the reference profile:
    # sweep a grid of (cc, hp, stroke, category, cylinders) inputs.
    seen = set()
    for st in (2, 4):
        for cat in ("sport", "naked", "cruiser", "touring", "adventure", None):
            for cc in (125, 155, 250, 390, 650, 999, 1299, 1800):
                for hp in (15, 45, 75, 120, 180, 200, 230):
                    for cyl in (None, 1, 2, 3, 4):
                        seen.add(
                            cp.derive_category_tag(
                                manufacturer="x",
                                model_name="y",
                                displacement_cc=cc,
                                peak_power_hp=hp,
                                stroke_type=st,
                                category=cat,
                                cylinders=cyl,
                            )
                        )
    assert cp.CATEGORY_REFERENCE_LITRE_195P not in seen
    assert cp.CATEGORY_LITRE_SPORT_195P in seen  # the catalog cluster still exists


def test_catalog_cluster_retune_does_not_move_a_reference():
    """Retuning litre_sport_195p (the catalog cluster) must leave the K5 ET
    bit-identical, while the same retune on the reference profile moves it —
    proving the decoupling is real in the production engine path."""
    base = _et(gsxr1000_k5())
    orig_cat = cp._PROFILES[cp.CATEGORY_LITRE_SPORT_195P]
    orig_ref = cp._PROFILES[cp.CATEGORY_REFERENCE_LITRE_195P]
    try:
        cp._PROFILES[cp.CATEGORY_LITRE_SPORT_195P] = dataclasses.replace(
            orig_cat, mu_peak_scale=orig_cat.mu_peak_scale * 0.8
        )
        assert _et(gsxr1000_k5()) == base
        cp._PROFILES[cp.CATEGORY_REFERENCE_LITRE_195P] = dataclasses.replace(
            orig_ref, mu_peak_scale=orig_ref.mu_peak_scale * 0.8
        )
        assert _et(gsxr1000_k5()) > base + 0.1
    finally:
        cp._PROFILES[cp.CATEGORY_LITRE_SPORT_195P] = orig_cat
        cp._PROFILES[cp.CATEGORY_REFERENCE_LITRE_195P] = orig_ref
