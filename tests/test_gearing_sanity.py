"""
test_gearing_sanity.py
======================
Parametric sanity checks over ALL_KNOWN_BIKES gear cassette data.

Rules
-----
1. top-gear ratio < 1.40 (catches data-entry TOP_GEAR_CRITICAL bugs like the
   old GSX-R 600 K6 at 1.407; the real-world range for any street/race bike
   is < 1.35, with documented exceptions noted below).
2. 1st-gear ratio >= 1.50 (floor for any production geared motorcycle; even
   adventure/touring bikes with short 1st gears are >= 1.8 — the 1.50 floor
   is a generous sanity bound to catch impossible values like 0.9 in 1st).
3. Gear count 4, 5, or 6 (3-speed and 7-speed exist as genuine edge cases
   in very old or racing-only machines; none are in ALL_KNOWN_BIKES today).
4. Gear ratios are strictly descending (each gear < previous).
5. No ratio <= 0 (negative or zero would crash the physics engine).

Known documented exceptions to rule 1 (top_gear >= 1.30):
- Suzuki Hayabusa (all gens): 6th = 1.304 — highway hyperbike, by design
- Honda CBR 600RR (PC40): 6th = 1.315 — close-ratio race gearbox, by design

These are explicitly whitelisted by (manufacturer_fragment, model_fragment).
"""

from __future__ import annotations

# Use -B flag equivalent by ensuring we read from source, not .pyc
import sys

import pytest


def _fresh_import(mod_path: str):
    """Import a module from source, bypassing .pyc cache."""
    if mod_path in sys.modules:
        del sys.modules[mod_path]
    import importlib.util

    spec_obj = importlib.util.find_spec(mod_path)
    if spec_obj is None:
        raise ImportError(mod_path)
    importlib.util.source_from_spec(spec_obj) if hasattr(spec_obj, "origin") else None
    mod = importlib.import_module(mod_path)
    return mod


from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# ── Whitelist: bikes whose top gear is legitimately >= 1.30 ──────────────────
# Each entry is (manufacturer_fragment, model_fragment) — both case-insensitive
TOP_GEAR_WHITELIST: list[tuple[str, str]] = [
    ("suzuki", "hayabusa"),  # Gen1/2/3: 6th = 1.304 (confirmed service manual)
    ("honda", "cbr 600rr"),  # PC40 close-ratio race box: 6th = 1.315
    ("honda", "cbr600rr"),  # alternate model_name spelling
]


def _is_whitelisted(spec) -> bool:
    mfr = spec.manufacturer.lower()
    mdl = spec.model_name.lower()
    return any(mf in mfr and ml in mdl for mf, ml in TOP_GEAR_WHITELIST)


# Build parametrize list: only bikes that actually have gear_ratios set
_SPECS_WITH_RATIOS = [
    s
    for s in ALL_KNOWN_BIKES
    if s.gear_ratios
    and len(s.gear_ratios) >= 2
    and all(r is not None for r in s.gear_ratios)
]


def _spec_id(spec) -> str:
    return f"{spec.manufacturer} {spec.model_name} ({spec.year_from})"


# ── Test 1: top-gear ratio < 1.40 ────────────────────────────────────────────
@pytest.mark.parametrize("spec", _SPECS_WITH_RATIOS, ids=_spec_id)
def test_top_gear_below_1_40(spec):
    """Top-gear internal ratio must be < 1.40 for any bike without a whitelist entry.

    Threshold is 1.40 (not 1.10) because many legitimate close-ratio gearboxes
    sit in the 1.10-1.30 range. 1.40+ is a clear data-entry error — no
    production gearbox in the catalog should exceed this.
    Whitelisted exceptions (Hayabusa 1.304, CBR600RR PC40 1.315) are documented.
    """
    top = spec.gear_ratios[-1]
    if _is_whitelisted(spec):
        pytest.skip(f"Whitelisted: {spec.model_name} top={top:.3f}")
    assert top < 1.40, (
        f"{spec.manufacturer} {spec.model_name} ({spec.year_from}): "
        f"top-gear={top:.3f} >= 1.40 — likely data-entry error. "
        f"Check service manual for correct 6th-gear ratio."
    )


# ── Test 2: first-gear ratio >= 1.50 ─────────────────────────────────────────
@pytest.mark.parametrize("spec", _SPECS_WITH_RATIOS, ids=_spec_id)
def test_first_gear_above_1_50(spec):
    """1st-gear ratio must be >= 1.50.

    Even the most extreme overdrive 1st gears (adventure bikes with short 1st
    for trail use) stay above 2.0. The 1.50 floor catches impossible values
    (< 1.0 would mean 1st gear is an overdrive, which is never true for a
    motorcycle).
    """
    first = spec.gear_ratios[0]
    assert first >= 1.50, (
        f"{spec.manufacturer} {spec.model_name} ({spec.year_from}): "
        f"1st-gear={first:.3f} < 1.50 — physically impossible. "
        f"Check service manual."
    )


# ── Test 3: gear count in expected range ────────────────────────────────────
@pytest.mark.parametrize("spec", _SPECS_WITH_RATIOS, ids=_spec_id)
def test_gear_count_4_to_6(spec):
    """ALL_KNOWN_BIKES should only contain 4-, 5-, or 6-speed transmissions.

    3-speed and 7-speed are genuine edge cases that do not appear in this
    catalog. If a new bike is added with an unusual gear count, it should
    be explicitly reviewed and this whitelist updated.
    """
    n = len(spec.gear_ratios)
    assert n in (4, 5, 6), (
        f"{spec.manufacturer} {spec.model_name} ({spec.year_from}): "
        f"{n}-speed transmission is outside expected range 4-6. "
        f"If correct, add a documented exception to this test."
    )


# ── Test 4: ratios are strictly descending ────────────────────────────────────
@pytest.mark.parametrize("spec", _SPECS_WITH_RATIOS, ids=_spec_id)
def test_ratios_strictly_descending(spec):
    """Each successive gear ratio must be lower than the previous.

    This is a fundamental mechanical property: higher gear = lower ratio.
    A non-descending sequence indicates copy-paste errors or swapped entries.
    """
    ratios = spec.gear_ratios
    for i in range(len(ratios) - 1):
        assert ratios[i] > ratios[i + 1], (
            f"{spec.manufacturer} {spec.model_name} ({spec.year_from}): "
            f"gear {i + 1}={ratios[i]:.3f} <= gear {i + 2}={ratios[i + 1]:.3f} "
            f"— ratios must be strictly descending."
        )


# ── Test 5: no non-positive ratio ────────────────────────────────────────────
@pytest.mark.parametrize("spec", _SPECS_WITH_RATIOS, ids=_spec_id)
def test_no_nonpositive_ratio(spec):
    """All gear ratios must be positive numbers."""
    for i, r in enumerate(spec.gear_ratios, 1):
        assert r > 0, (
            f"{spec.manufacturer} {spec.model_name} ({spec.year_from}): "
            f"gear {i} ratio={r} <= 0 — physically impossible."
        )
