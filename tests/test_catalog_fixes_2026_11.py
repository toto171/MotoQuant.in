"""Regression tests for the November 2026 ET-neutral catalog fixes.

Covers: Tier-1 gear-table None padding, headline specs borrowed from the K5
defaults, fitments whose tire position contradicts the slot, loop-generated
placeholder parts, the known-wrong Tier-1 gear matches (documented, not fixed),
and the patch script that carries the data fixes to the shipped database.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from motoquant import MotoQuantEngine
from motoquant.database import MotoQuantDB
from motoquant.database.bridge import (
    bore_stroke_matches_displacement,
    extract_headline_specs,
)
from motoquant.database.seed import seed_all
from motoquant.database.tire_repo import tire_position_fits_slot
from motoquant.defaults import gsxr1000_k5
from motoquant.scraper import gear_ratios as G
from motoquant.scraper.importer import import_batch, spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

ROOT = Path(__file__).resolve().parent.parent
K5 = gsxr1000_k5()


def _spec(model_fragment, year=None, mfr=None):
    for s in ALL_KNOWN_BIKES:
        if (
            model_fragment.lower() in s.model_name.lower()
            and (year is None or s.year_from == year)
            and (mfr is None or s.manufacturer == mfr)
        ):
            return s
    raise LookupError(model_fragment)


# ── 1. Gear table ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "entry", G._DB, ids=[f"{e['mfr']}|{e['model']}|{e['year']}" for e in G._DB]
)
def test_tier1_entries_are_positive_floats_strictly_descending(entry):
    r = entry["ratios"]
    assert all(isinstance(x, float) and x > 0 for x in r), r
    assert all(a > b for a, b in zip(r, r[1:])), r


@pytest.mark.parametrize(
    "mfr,model,year",
    [
        ("Yamaha", "FZ-X", 2021),
        ("Honda", "Hornet 2.0", 2020),
        ("Bajaj", "Pulsar 220F", 2007),
        ("TVS", "Apache RTR 200 4V", 2016),
        ("TVS", "Apache RTR 160 4V", 2018),
        ("Triumph", "Speed 400", 2023),
        ("Hero", "Xtreme 160R", 2020),
    ],
)
def test_spec_without_own_cassette_builds_and_runs(mfr, model, year):
    base = next(
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == mfr and s.model_name == model and s.year_from == year
    )
    spec = dataclasses.replace(base, gear_ratios=None, gears=None)
    lu_ratios = G.lookup_gear_ratios(
        mfr, model, year, spec.category, spec.displacement_cc, None
    )[0]
    assert None not in lu_ratios
    cfg = spec_to_bike_config(spec)
    assert len(cfg.drivetrain.gear_ratios) == len(lu_ratios)
    assert all(g > 0 for g in cfg.drivetrain.gear_ratios)
    res = MotoQuantEngine(cfg).run(max_time=3.0)
    assert res.x[-1] > 10.0


# ── 2. Headline specs ────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def imported_db():
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    specs = [
        _spec("Monkey 125"),
        _spec("R 18", mfr="BMW"),
        _spec("800X"),
        _spec("ZX-6R", 2024),
    ]
    out = import_batch(db, specs)
    assert out["errors"] == 0
    yield db
    db.close()


def _row(db, like):
    return db._conn.execute(
        "SELECT * FROM bike_models WHERE model_name LIKE ?", (like,)
    ).fetchone()


def test_headline_seat_height_is_not_borrowed_from_k5(imported_db):
    for like in ("Monkey 125%", "R 18%", "800X%"):
        row = _row(imported_db, like)
        spec_seat = {
            "Monkey 125%": _spec("Monkey 125").seat_height_mm,
            "R 18%": _spec("R 18", mfr="BMW").seat_height_mm,
            "800X%": _spec("800X").seat_height_mm,
        }[like]
        if spec_seat is None:
            assert row["seat_height_mm"] is None, like
        else:
            assert row["seat_height_mm"] == spec_seat, like
        assert row["seat_height_mm"] != K5.chassis.seat_height_mm or spec_seat == (
            K5.chassis.seat_height_mm
        )


def test_headline_bore_stroke_not_k5_when_spec_has_none(imported_db):
    spec = _spec("800X")
    assert spec.bore_mm is None
    row = _row(imported_db, "800X%")
    assert row["bore_mm"] is None and row["stroke_mm"] is None
    assert row["compression_ratio"] is None


def test_headline_bore_stroke_nulled_when_inconsistent_with_displacement(imported_db):
    spec = _spec("ZX-6R", 2024)
    assert not bore_stroke_matches_displacement(
        spec.bore_mm, spec.stroke_mm, spec.cylinders, spec.displacement_cc
    )
    row = _row(imported_db, "ZX-6R%2024%")
    assert row["bore_mm"] is None and row["stroke_mm"] is None
    assert row["displacement_cc"] == spec.displacement_cc


def test_extract_headline_specs_null_in_null_out_and_config_unchanged():
    spec = _spec("800X")
    cfg = spec_to_bike_config(spec)
    # Physics still gets a usable (defaulted) config...
    assert cfg.chassis.seat_height_mm == K5.chassis.seat_height_mm
    # ...while the displayed headline carries only what the spec stated.
    h = extract_headline_specs(cfg, spec=spec)
    assert h["seat_height_mm"] is None and h["wheelbase_mm"] is None
    # Without a spec the old behaviour (config values) is preserved.
    assert extract_headline_specs(cfg)["seat_height_mm"] == K5.chassis.seat_height_mm


# ── 3. Fitment positions ─────────────────────────────────────────────────────


def test_tire_position_fits_slot_rules():
    assert tire_position_fits_slot("rear", "rear")
    assert tire_position_fits_slot("both", "front")
    assert tire_position_fits_slot(None, "rear")
    assert not tire_position_fits_slot("front", "rear")
    assert not tire_position_fits_slot("rear", "front")


def test_link_bike_fitment_rejects_front_tire_in_rear_slot():
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    seed_all(db)
    front = db._conn.execute(
        "SELECT id FROM tire_models WHERE position = 'front' LIMIT 1"
    ).fetchone()[0]
    bike = db._conn.execute("SELECT id FROM bike_models LIMIT 1").fetchone()[0]
    with pytest.raises(ValueError, match="front-position"):
        db.tires.link_bike_fitment(bike, front, "rear", fitment_type="drag_prep")
    db.close()


def test_fresh_seed_has_no_position_mismatched_fitments():
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    seed_all(db)
    bad = db._conn.execute(
        "SELECT COUNT(*) FROM bike_tire_fitments f JOIN tire_models t "
        "ON t.id = f.tire_model_id WHERE t.position IN ('front','rear') "
        "AND t.position != f.position"
    ).fetchone()[0]
    assert bad == 0
    db.close()


# ── 4. Placeholder parts ─────────────────────────────────────────────────────

_GENERATED_SUSPENSION = re.compile(r"^SUSP-[^-]+-\d+$")


def test_fresh_seed_has_no_loop_generated_suspension_placeholders():
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    seed_all(db)
    rows = db._conn.execute("SELECT part_number, model_name FROM parts").fetchall()
    bad = [
        tuple(r)
        for r in rows
        if _GENERATED_SUSPENSION.match(r[0] or "")
        or re.search(r" V\d+$", r[1] or "")
        and (r[0] or "").startswith("SUSP-")
    ]
    assert bad == []
    db.close()


# ── 6. Known-wrong Tier-1 gear matches (documented; the epoch lane fixes them) ─

# bike -> the Tier-1 key it resolves to today (None = no Tier-1 hit). The gearing
# verifier found each of these resolves to a DIFFERENT model's entry (substring
# match) or misses its own entry on a year range. Changing the resolution moves
# catalog ETs, so it is not a free fix.
#
# 2026-11-10 epoch: a whole-token matcher that fixes these was built and measured
# together with the inferred-primary gearing rules it only makes sense with, and
# the package FAILED its accuracy gate (it made the sub-400 cc high-confidence
# benchmarks worse and no physically plausible retune recovered them), so it was
# not shipped. Evidence, the gate table and the prototype diff are in
# reports/session_2026_11_10_epoch.md. These pins therefore still describe
# today's (known-wrong) behaviour; when a later epoch fixes the matcher the
# expectations change and the diff makes that visible.
KNOWN_MISMATCHES = {
    ("Kawasaki", "Ninja ZX-10RR", 2021): ("kawasaki", "zx-10r"),
    ("Honda", "CBR250RR (Indonesia)", 2017): ("honda", "cbr 250r"),
    ("Bajaj", "Pulsar NS200 BS6", 2020): ("bajaj", "pulsar ns 200"),
    ("TVS", "Apache RTR 160 4V", 2018): ("tvs", "apache rtr 160"),
    ("TVS", "Apache RTR 160 2V", 2018): ("tvs", "apache rtr 160"),
    ("Bajaj", "Pulsar NS200", 2012): None,  # NS 200 Tier-1 entry starts in 2017
}


@pytest.mark.parametrize("key", list(KNOWN_MISMATCHES), ids=lambda k: f"{k[0]} {k[1]}")
def test_known_wrong_tier1_resolution_is_pinned(key):
    mfr, model, year = key
    spec = next(
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == mfr and s.model_name == model and s.year_from == year
    )
    ratios, front, rear, primary, conf = G.lookup_gear_ratios(
        mfr, model, year, spec.category, spec.displacement_cc, spec.gears
    )
    expected = KNOWN_MISMATCHES[key]
    if expected is None:
        assert conf < 0.5, "expected a Tier-2 fallback (no Tier-1 entry for this year)"
        return
    entry = next(
        e
        for e in G._DB
        if e["mfr"] == expected[0].lower().replace(" ", "_")
        and e["model"] == expected[1]
        and e["year"][0] <= year <= e["year"][1]
    )
    assert conf == 0.75
    assert ratios == [r for r in entry["ratios"] if r is not None]
    assert primary == entry.get("primary", 1.700)


# ── Patch script on a copy of the shipped database ───────────────────────────


@pytest.fixture(scope="module")
def patched_copy():
    src = ROOT / "motoquant.db"
    if not src.exists():
        pytest.skip("no motoquant.db")
    tmp = Path(tempfile.mkdtemp()) / "t.db"
    shutil.copy(src, tmp)
    path = ROOT / "scripts" / "patch_2026_11_10_catalog_fixes.py"
    spec = importlib.util.spec_from_file_location("patch_2026_11_10", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    first = mod.apply(str(tmp), verbose=False)
    second = mod.apply(str(tmp), verbose=False)
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    yield conn, mod, first, second
    conn.close()
    shutil.rmtree(tmp.parent, ignore_errors=True)


def test_patch_is_idempotent(patched_copy):
    _conn, mod, _first, second = patched_copy
    assert mod.total_changes(second) == 0


def test_patched_db_has_no_k5_seat_height_unless_spec_says_so(patched_copy):
    conn, _mod, _f, _s = patched_copy
    n = conn.execute(
        "SELECT COUNT(*) FROM bike_models WHERE seat_height_mm = 810 "
        "AND id NOT IN (1, 2, 3)"
    ).fetchone()[0]
    spec_810 = sum(1 for s in ALL_KNOWN_BIKES if s.seat_height_mm == 810)
    assert n <= spec_810


def test_patched_db_bore_stroke_consistent_with_displacement(patched_copy):
    conn, _mod, _f, _s = patched_copy
    for r in conn.execute(
        "SELECT id, bore_mm, stroke_mm, cylinder_count, displacement_cc FROM bike_models"
    ):
        assert bore_stroke_matches_displacement(
            r["bore_mm"], r["stroke_mm"], r["cylinder_count"], r["displacement_cc"]
        ), r["id"]


def test_patched_db_fitments_match_their_slot(patched_copy):
    conn, _mod, _f, _s = patched_copy
    bad = conn.execute(
        "SELECT f.id FROM bike_tire_fitments f JOIN tire_models t ON t.id = f.tire_model_id "
        "WHERE t.position IN ('front','rear') AND t.position != f.position"
    ).fetchall()
    assert bad == []


def test_patched_db_has_no_placeholder_suspension_parts(patched_copy):
    conn, _mod, _f, _s = patched_copy
    n = conn.execute(
        "SELECT COUNT(*) FROM parts WHERE part_number GLOB 'SUSP-*-[0-9]*'"
    ).fetchone()[0]
    assert n == 0
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_patch_leaves_physics_blobs_untouched(patched_copy):
    conn, _mod, _f, _s = patched_copy
    orig = sqlite3.connect(ROOT / "motoquant.db")
    q = "SELECT bike_model_id, version, engine_params, chassis_params, drivetrain_params FROM bike_configs ORDER BY id"
    assert [tuple(r) for r in conn.execute(q)] == orig.execute(q).fetchall()
    orig.close()


# ── 7. Remaining generated placeholder parts (2026-11-10, final sync lane) ──────

# Real brand names stamped onto invented products by seed.py template loops.
_SYNTHETIC_NAME = re.compile(
    r"(Performance Air Filter V\d+|Performance Filter Pro \d+|Advanced Fuel System \d+"
    r"|(Caliper|pad|rotor) V\d+$|Fairing V\d+$)"
)
_SYNTHETIC_PN = re.compile(
    r"^(AF-PERF-V\d+|AF-PRO-\d+|FS-ADV-\d+|BRK-[A-Z]{3}-\d+|BW-[A-Z]{3}-\d+)$"
)

_REMOVED_KEYS = [
    ("K&N", "AF-PERF-V2"), ("HiFlow", "AF-PRO-11"), ("Brembo", "BRK-BRE-4"),
    ("SBS", "BRK-SBS-9"), ("Catalyst", "BW-CAT-3"), ("Hotbodies", "BW-HOT-6"),
    ("Holley", "FS-ADV-5"), ("Translogic", "QS-TRA-5"), ("Shift Assist", "QS-SHI-9"),
    ("Enersys", "BATT-ENE-6"), ("Interstate", "BATT-INT-8"),
]  # fmt: skip


def _fresh_seed_parts():
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    seed_all(db)
    rows = [
        tuple(r)
        for r in db._conn.execute("SELECT brand, part_number, model_name FROM parts")
    ]
    db.close()
    return rows


def test_fresh_seed_has_no_template_stamped_parts():
    rows = _fresh_seed_parts()
    bad = [
        r
        for r in rows
        if _SYNTHETIC_PN.match(r[1] or "") or _SYNTHETIC_NAME.search(r[2] or "")
    ]
    # the real 'Panigale V4' / 'V85 TT' style model names must not trip the guard
    assert bad == []
    keys = {(r[0], r[1]) for r in rows}
    for k in _REMOVED_KEYS + [tuple(x) for x in _patch_module().SYNTHETIC_PARTS]:
        assert tuple(k) not in keys, k


def _patch_module():
    path = ROOT / "scripts" / "patch_2026_11_10_catalog_fixes.py"
    spec = importlib.util.spec_from_file_location("patch_2026_11_10_b", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_shipped_db_has_no_template_stamped_parts():
    src = ROOT / "motoquant.db"
    if not src.exists():
        pytest.skip("no motoquant.db")
    conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    rows = conn.execute("SELECT brand, part_number, model_name FROM parts").fetchall()
    conn.close()
    bad = [
        r
        for r in rows
        if _SYNTHETIC_PN.match(r[1] or "") or _SYNTHETIC_NAME.search(r[2] or "")
    ]
    assert bad == []
    keys = {(r[0], r[1]) for r in rows}
    for k in _patch_module().SYNTHETIC_PARTS:
        assert tuple(k) not in keys, k


def test_shipped_db_parts_equal_fresh_seed_parts():
    """`db init` + `db seed` yields exactly the parts set the shipped DB carries."""
    src = ROOT / "motoquant.db"
    if not src.exists():
        pytest.skip("no motoquant.db")
    conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    shipped = {
        (r[0], r[1]) for r in conn.execute("SELECT brand, part_number FROM parts")
    }
    conn.close()
    fresh = {(r[0], r[1]) for r in _fresh_seed_parts()}
    assert shipped == fresh, (
        f"only in shipped: {sorted(shipped - fresh)[:10]}; "
        f"only in fresh seed: {sorted(fresh - shipped)[:10]}"
    )


def _scratch_copy_of_shipped_db():
    src = ROOT / "motoquant.db"
    if not src.exists():
        pytest.skip("no motoquant.db")
    tmpdir = Path(tempfile.mkdtemp())
    tmp = tmpdir / "t.db"
    shutil.copy(src, tmp)
    return tmpdir, tmp


def test_patch_removes_synthetic_parts_and_their_prices():
    """Re-insert the synthetic rows (with a price row each) into a copy of the
    shipped DB, then prove the patch deletes them. The shipped DB is already
    clean, so without the re-insert this test could not fail."""
    mod = _patch_module()
    keys = [tuple(k) for k in mod.SYNTHETIC_PARTS]
    assert keys
    tmpdir, tmp = _scratch_copy_of_shipped_db()
    try:
        conn = sqlite3.connect(tmp)
        cat = conn.execute("SELECT id FROM parts_categories LIMIT 1").fetchone()[0]
        for brand, pn in keys:
            cur = conn.execute(
                "INSERT INTO parts (category_id, brand, model_name, part_number, "
                "specifications) VALUES (?, ?, 'synthetic test row', ?, '{}')",
                (cat, brand, pn),
            )
            conn.execute(
                "INSERT INTO part_prices (part_id, retailer, source_url, price_inr) "
                "VALUES (?, 'synthetic-test', 'https://example.invalid', 1.0)",
                (cur.lastrowid,),
            )
        conn.commit()
        conn.close()
        first = mod.apply(str(tmp), verbose=False)
        second = mod.apply(str(tmp), verbose=False)
        assert first["parts"]["parts_removed"] == len(keys)
        assert second["parts"]["parts_removed"] == 0
        assert mod.total_changes(second) == 0
        conn = sqlite3.connect(tmp)
        for brand, pn in keys:
            assert (
                conn.execute(
                    "SELECT COUNT(*) FROM parts WHERE brand=? AND part_number=?",
                    (brand, pn),
                ).fetchone()[0]
                == 0
            )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM part_prices WHERE retailer = 'synthetic-test'"
            ).fetchone()[0]
            == 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM part_prices "
                "WHERE part_id NOT IN (SELECT id FROM parts)"
            ).fetchone()[0]
            == 0
        )
        conn.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


_WHEELIE_BAR_NUMBERS = ("WB-8IN", "WB-10IN", "WB-12IN")


def _wheelie_bar_brands(conn):
    q = "SELECT part_number, brand FROM parts WHERE part_number IN (?, ?, ?)"
    return sorted((r[0], r[1]) for r in conn.execute(q, _WHEELIE_BAR_NUMBERS))


def test_unbranded_wheelie_bars_are_labelled_generic():
    """The three fabricated bars carry no invented maker name, in the shipped
    DB and in a fresh seed, and exist exactly once each."""
    expected = sorted((pn, "Generic") for pn in _WHEELIE_BAR_NUMBERS)
    src = ROOT / "motoquant.db"
    if src.exists():
        conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
        assert _wheelie_bar_brands(conn) == expected
        conn.close()
    fresh = sorted(
        (r[1], r[0]) for r in _fresh_seed_parts() if r[1] in _WHEELIE_BAR_NUMBERS
    )
    assert fresh == expected


def test_patch_relabels_old_wheelie_bar_brands():
    """Put the old brand names back on a copy of the shipped DB and prove the
    patch relabels them; then prove it removes an old-brand duplicate when the
    Generic row already exists (a seed run on an unpatched DB)."""
    mod = _patch_module()
    old = {pn: brand for brand, pn in mod.GENERIC_RELABEL}
    assert sorted(old) == sorted(_WHEELIE_BAR_NUMBERS)
    tmpdir, tmp = _scratch_copy_of_shipped_db()
    try:
        conn = sqlite3.connect(tmp)
        for pn, brand in old.items():
            conn.execute(
                "UPDATE parts SET brand = ? WHERE brand = 'Generic' AND part_number = ?",
                (brand, pn),
            )
        conn.commit()
        n_before = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        conn.close()
        first = mod.apply(str(tmp), verbose=False)
        second = mod.apply(str(tmp), verbose=False)
        assert first["relabel"]["parts_relabelled"] == 3
        assert mod.total_changes(second) == 0
        conn = sqlite3.connect(tmp)
        assert _wheelie_bar_brands(conn) == sorted(
            (pn, "Generic") for pn in _WHEELIE_BAR_NUMBERS
        )
        assert conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0] == n_before
        # duplicate case: an old-brand copy beside the Generic row
        cat = conn.execute(
            "SELECT category_id FROM parts WHERE part_number = 'WB-8IN'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO parts (category_id, brand, model_name, part_number, "
            "specifications) VALUES (?, ?, 'dup', 'WB-8IN', '{}')",
            (cat, old["WB-8IN"]),
        )
        conn.commit()
        conn.close()
        third = mod.apply(str(tmp), verbose=False)
        assert third["relabel"]["parts_relabelled"] == 1
        conn = sqlite3.connect(tmp)
        assert _wheelie_bar_brands(conn) == sorted(
            (pn, "Generic") for pn in _WHEELIE_BAR_NUMBERS
        )
        assert conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0] == n_before
        conn.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
