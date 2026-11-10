"""2026-11 epoch round 3: the 1st-gear launch wheelie margin.

``CategoryProfile.wheelie_margin`` is the share of the combined bike + rider
wheelie ceiling the rider holds over the launch — from rest to the 60-ft line
(motoquant/physics.py run loop; Rust core resolved-config schema 5). These tests drive the production
engine (MotoQuantEngine, and the native core when it is built) and pin:

* margin 1.0 is BIT-IDENTICAL to the round-2 tree (1c487f0) — golden ETs
  captured from a worktree of that commit with its own profile knobs;
* margin < 1 slows wheelie-limited (high-power) launches, roughly uniformly,
  and leaves a power-limited bike untouched;
* the capped ceiling binds only before the 60-ft line;
* a heavier bike is still never quicker (dry mass +-10 kg) at margin 0.8;
* the native core reproduces the margin exactly.
"""

from __future__ import annotations

import dataclasses
import statistics

import pytest

from motoquant import category_profiles as cp
from motoquant.constants import SIXTY_FOOT_M, G
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.physics import MotoQuantEngine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

#: Golden (ET s, finish speed m/s, 60 ft s) from the round-2 tree with its own
#: checked-in profiles (python3 -I golden.py /tmp/<worktree of 1c487f0>).
R2_GOLDEN = {
    "gsxr1000_k5": (9.830941722483225, 66.25423670038211, 1.723646556708523),
    "yzfr1_4c8": (10.159185892348502, 64.12004381984471, 1.7942601201562085),
    "hayabusa_gen1": (10.44612029310401, 64.08520501353743, 1.875334713093443),
    "Yamaha|YZF-R6|2017": (10.826317100475737, 58.523657986553125, 1.7146348639981726),
    "Kawasaki|Ninja ZX-10R|2021": (
        10.681521432089442,
        66.95094693167077,
        2.0300979145707907,
    ),
    "Ducati|1199 Panigale|2012": (
        9.395338602957088,
        71.64766294253337,
        1.5914678578476211,
    ),
    "KTM|Duke 390|2017": (13.610928454490141, 42.256661966216605, 1.864121360553876),
    "Royal Enfield|Classic 350|2021": (
        18.29334275406355,
        31.116321953122018,
        2.6421124512973995,
    ),
}

#: The round-2 checked-in knob values (category_profiles.py at 1c487f0).
R2_PROFILE_KNOBS = {
    cp.CATEGORY_LITRE_SPORT_195P: {"mu_peak_scale": 1.05, "launch_rpm_factor": 0.475},
    cp.CATEGORY_LITRE_SPORT_600_1000: {
        "mu_peak_scale": 0.95,
        "launch_rpm_factor": 0.50,
    },
    cp.CATEGORY_SPORT_TWIN_600_1300: {
        "mu_peak_scale": 0.95,
        "launch_rpm_factor": 0.475,
    },
    cp.CATEGORY_OTHER: {"mu_peak_scale": 0.95, "launch_rpm_factor": None},
    cp.CATEGORY_SINGLE_300_500: {"mu_peak_scale": 1.0, "launch_rpm_factor": None},
    cp.CATEGORY_ENTRY_200_300: {"mu_peak_scale": 1.0, "launch_rpm_factor": None},
    cp.CATEGORY_ENTRY_150_200: {"mu_peak_scale": 1.0, "launch_rpm_factor": None},
    cp.CATEGORY_REFERENCE_LITRE_195P: {
        "mu_peak_scale": 0.95,
        "launch_rpm_factor": 0.45,
    },
}

_COMMON_NEUTRAL = {
    "over_clutch_factor": 0.0,
    "max_engine_decel_rads2": 0.0,
    "launch_floor_factor": 0.0,
    "mu_peak_override": None,
    "parasitic_mult": 1.0,
}


def _spec(key: str):
    mfr, model, year = key.split("|")
    for s in ALL_KNOWN_BIKES:
        if s.manufacturer == mfr and s.model_name == model and s.year_from == int(year):
            return s
    raise LookupError(key)


def _cfg(key: str):
    refs = {
        "gsxr1000_k5": gsxr1000_k5,
        "yzfr1_4c8": yzfr1_4c8,
        "hayabusa_gen1": hayabusa_gen1,
    }
    if key in refs:
        return refs[key]()
    return spec_to_bike_config(_spec(key))


def _engine(cfg, cls=MotoQuantEngine, **knobs):
    """Engine built while the bike's profile carries ``knobs`` (the tyre
    model bakes the profile grip scale in at construction, so the swap must
    happen before the engine exists; the knobs stay on the engine)."""
    if not knobs:
        return cls(cfg)
    tag = cfg.category_tag or cp.CATEGORY_UNKNOWN
    key = tag if tag in cp._PROFILES else cp.CATEGORY_UNKNOWN
    saved = cp._PROFILES[key]
    cp._PROFILES[key] = dataclasses.replace(saved, **knobs)
    try:
        eng = cls(cfg)
        eng._profile = cp._PROFILES[key]
    finally:
        cp._PROFILES[key] = saved
    return eng


# ── margin 1.0 == round 2, bit for bit ─────────────────────────────────────


@pytest.mark.parametrize("key", sorted(R2_GOLDEN))
def test_margin_one_is_bit_identical_to_round2(key):
    cfg = _cfg(key)
    knobs = R2_PROFILE_KNOBS.get(MotoQuantEngine(cfg)._profile.name)
    assert knobs is not None, key
    r = _engine(cfg, **_COMMON_NEUTRAL, **knobs, wheelie_margin=1.0).run()
    et, v, t60 = R2_GOLDEN[key]
    assert float(r.time_quarter) == et
    assert float(r.speed_quarter) == v
    assert float(r.time_60ft) == t60


def test_default_margin_is_the_no_op():
    assert cp.CategoryProfile().wheelie_margin == 1.0


@pytest.mark.parametrize("tag", sorted(cp._PROFILES))
def test_shipped_margins_inside_physical_range(tag):
    m = cp._PROFILES[tag].wheelie_margin
    assert 0.65 <= m <= 1.0, (tag, m)


# ── margin < 1: slows wheelie-limited launches, roughly uniformly ──────────

LITRE_SAMPLE = (
    "gsxr1000_k5",
    "yzfr1_4c8",
    "hayabusa_gen1",
    "Kawasaki|Ninja ZX-10R|2021",
    "Ducati|1199 Panigale|2012",
    "Yamaha|YZF-R6|2017",
)


def _neutral_knobs(**extra):
    return {
        **_COMMON_NEUTRAL,
        "mu_peak_scale": 1.0,
        "launch_rpm_factor": None,
        **extra,
    }


def test_margin_slows_wheelie_limited_launches_roughly_uniformly():
    deltas = []
    for key in LITRE_SAMPLE:
        cfg = _cfg(key)
        base = _engine(cfg, **_neutral_knobs(wheelie_margin=1.0)).run()
        cap = _engine(cfg, **_neutral_knobs(wheelie_margin=0.8)).run()
        d = float(cap.time_quarter) - float(base.time_quarter)
        assert d > 0.1, (key, d)  # every high-power launch is slowed
        assert float(cap.time_60ft) > float(base.time_60ft), key
        deltas.append(d)
    # roughly uniform: the spread is small next to the shift itself
    assert statistics.pstdev(deltas) < 0.5 * statistics.mean(deltas), deltas


def test_power_limited_bike_is_untouched():
    """A 350 cc single never reaches 0.8 x its wheelie ceiling: identical."""
    cfg = _cfg("Royal Enfield|Classic 350|2021")
    a = _engine(cfg, **_neutral_knobs(wheelie_margin=1.0)).run()
    b = _engine(cfg, **_neutral_knobs(wheelie_margin=0.8)).run()
    assert float(a.time_quarter) == float(b.time_quarter)
    assert float(a.speed_quarter) == float(b.speed_quarter)


def test_capped_ceiling_binds_only_over_the_launch():
    cfg = _cfg("Kawasaki|Ninja ZX-10R|2021")
    eng = _engine(cfg, **_neutral_knobs(wheelie_margin=0.8))
    r = eng.run()
    on_cap = {"launch": 0, "later": 0}
    for i in range(len(r.t)):
        if r.traction_pct[i] >= 100.0 - 1e-9:
            continue
        aw = eng.max_accel_before_wheelie(
            float(r.v[i]), float(r.t[i]), float(r.F_drag[i])
        )
        if abs(r.a[i] * G - 0.8 * aw) < 1e-3:
            on_cap["launch" if r.x[i] < SIXTY_FOOT_M else "later"] += 1
    assert on_cap["launch"] > 100  # the launch rides the capped ceiling ...
    assert on_cap["later"] == 0  # ... and nothing past the 60-ft line does


def test_past_the_sixty_foot_line_the_full_ceiling_applies():
    """With the margin the bike reaches the 60-ft line later and slower, and
    from there it is ridden to its own (full) ceiling: some step past the
    line sits on the uncapped ceiling."""
    cfg = _cfg("gsxr1000_k5")
    eng = _engine(cfg, **_neutral_knobs(wheelie_margin=0.8))
    r = eng.run()
    hits = 0
    for i in range(len(r.t)):
        if r.x[i] < SIXTY_FOOT_M or r.traction_pct[i] >= 100.0 - 1e-9:
            continue
        aw = eng.max_accel_before_wheelie(
            float(r.v[i]), float(r.t[i]), float(r.F_drag[i])
        )
        hits += abs(r.a[i] * G - aw) < 1e-3
    assert hits > 100


@pytest.mark.parametrize(
    "key", [k for k in LITRE_SAMPLE if k != "Ducati|1199 Panigale|2012"]
)
def test_mass_monotone_at_margin(key):
    """(The 1199 Panigale is excluded: it is dry-mass inverted at NEUTRAL
    knobs already — traction-limited in 1st/2nd gear; the shipped
    sport-twin profile is selected to clear it, tests/test_epoch3_tune_profiles.)"""
    ets = []
    for dm in (-10.0, 0.0, 10.0):
        cfg = _cfg(key)
        cfg.chassis.dry_mass_kg += dm
        ets.append(
            float(_engine(cfg, **_neutral_knobs(wheelie_margin=0.8)).run().time_quarter)
        )
    assert ets[0] < ets[1] < ets[2], (key, ets)


# ── native mirror ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("wm", (0.65, 0.8, 0.95))
def test_native_reproduces_the_margin(wm):
    native = pytest.importorskip("motoquant.native")
    if not native.available():
        pytest.skip("native core not built")
    for key in ("hayabusa_gen1", "Kawasaki|Ninja ZX-10R|2021"):
        cfg = _cfg(key)
        a = _engine(cfg, **_neutral_knobs(wheelie_margin=wm)).run()
        b = _engine(
            cfg, cls=native.NativeEngine, **_neutral_knobs(wheelie_margin=wm)
        ).run()
        assert float(a.time_quarter) == float(b.time_quarter)
        assert float(a.speed_quarter) == float(b.speed_quarter)


def test_resolved_config_carries_the_margin():
    native = pytest.importorskip("motoquant.native")
    eng = _engine(hayabusa_gen1(), wheelie_margin=0.77)
    d = native.resolve_engine(eng)
    assert d["schema"] == native.SCHEMA_VERSION == 5
    assert d["wheelie"]["margin"] == 0.77
    assert d["wheelie"]["margin_window_m"] == SIXTY_FOOT_M
