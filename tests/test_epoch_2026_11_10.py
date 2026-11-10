"""Regression tests for the 2026-11-10 duplicate-bike epoch.

Seven motorcycles were entered twice with overlapping year ranges and
conflicting data; one row per bike now survives and the two Fireblade SP
generations are disjoint. These tests pin

  * the sourced values the surviving rows carry (the dry-vs-kerb mass convention
    above all), through the production importer path;
  * scripts/patch_2026_11_10_epoch.py on a database that still HOLDS the
    duplicates (rows re-pointed or deleted, nothing orphaned, idempotent);
  * the shipped database: one row per spec, no overlapping-year duplicates.

The spec-level "no overlapping years" guard lives in
tests/test_catalog_no_duplicates.py::TestNoOverlappingYearDuplicates.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import itertools
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from motoquant.database import MotoQuantDB
from motoquant.scraper.importer import import_batch, spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

ROOT = Path(__file__).resolve().parent.parent
_YEAR_SUFFIX = re.compile(r"\s*\(\d{4}(?:-\d{4})?\)\s*$")


def _strip_year(name):
    return _YEAR_SUFFIX.sub("", name or "").strip()


def _spec(manufacturer, model, year_from=None):
    hits = [
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == manufacturer
        and _strip_year(s.model_name) == model
        and (year_from is None or s.year_from == year_from)
    ]
    assert len(hits) == 1, [(s.model_name, s.year_from) for s in hits]
    return hits[0]


@pytest.fixture(scope="module")
def patch_module():
    path = ROOT / "scripts" / "patch_2026_11_10_epoch.py"
    spec = importlib.util.spec_from_file_location("patch_2026_11_10_epoch", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 1. Sourced values on the surviving rows (production importer path) ───────


@pytest.mark.parametrize(
    "manufacturer,model,year_from,year_to",
    [
        ("Royal Enfield", "Continental GT 650", 2018, 2024),
        ("Royal Enfield", "Interceptor 650", 2018, 2024),
        ("Royal Enfield", "Super Meteor 650", 2023, 2026),
        ("Honda", "Hornet 2.0", 2020, 2026),
        ("Aprilia", "Tuono 457", 2025, 2026),
        ("TVS", "Raider 125", 2021, 2026),
        ("Suzuki", "V-Strom SX 250", 2022, 2026),
    ],
)
def test_collapsed_pair_year_range(manufacturer, model, year_from, year_to):
    s = _spec(manufacturer, model)
    assert (s.year_from, s.year_to) == (year_from, year_to)


@pytest.mark.parametrize(
    "manufacturer,model,year_from,dry_kg",
    [
        # dry-convention figures (the removed rows' 202 kg was a kerb weight)
        ("Royal Enfield", "Continental GT 650", 2018, 182.0),
        ("Royal Enfield", "Interceptor 650", 2018, 181.0),
        ("Suzuki", "V-Strom SX 250", 2022, 155.0),
        ("Aprilia", "Tuono 457", 2025, 159.0),
        ("Honda", "CBR1000RR-R Fireblade SP", 2020, 183.0),
        # published kerb weights recorded as WET: the importer derives wet - 25
        ("Honda", "CBR1000RR-R Fireblade SP", 2024, 201.0 - 25.0),
        ("Honda", "Hornet 2.0", 2020, 142.0 - 25.0),
        ("Royal Enfield", "Super Meteor 650", 2023, 241.0 - 25.0),
    ],
)
def test_dry_mass_follows_the_dry_convention(manufacturer, model, year_from, dry_kg):
    cfg = spec_to_bike_config(_spec(manufacturer, model, year_from))
    assert cfg.chassis.dry_mass_kg == pytest.approx(dry_kg)


@pytest.mark.parametrize(
    "manufacturer,model,year_from",
    [
        ("Honda", "CBR1000RR-R Fireblade SP", 2024),
        ("Honda", "Hornet 2.0", 2020),
        ("Royal Enfield", "Super Meteor 650", 2023),
    ],
)
def test_kerb_figures_are_stored_as_wet_not_dry(manufacturer, model, year_from):
    """A kerb weight in dry_mass_kg makes the importer add fluids and fuel on
    top of it (~20-25 kg double-counted). These three record it as wet."""
    s = _spec(manufacturer, model, year_from)
    assert s.dry_mass_kg is None and s.wet_mass_kg


def test_sourced_wheelbases_and_tyre():
    assert _spec("Royal Enfield", "Continental GT 650").wheelbase_mm == 1398.0
    assert _spec("Royal Enfield", "Interceptor 650").wheelbase_mm == 1398.0
    assert _spec("Honda", "CBR1000RR-R Fireblade SP", 2024).wheelbase_mm == 1455.0
    assert _spec("TVS", "Raider 125").rear_tire_size == "100/90-17"
    assert _spec("TVS", "Raider 125").wheelbase_mm == 1326.0


def test_fireblade_sp_generations_keep_their_own_data():
    old, new = (
        _spec("Honda", "CBR1000RR-R Fireblade SP", 2020),
        _spec("Honda", "CBR1000RR-R Fireblade SP", 2024),
    )
    assert (old.year_from, old.year_to) == (2020, 2023)
    assert (new.year_from, new.year_to) == (2024, 2025)
    # The contested power figure was NOT adjudicated: each row keeps its own.
    assert (old.peak_power_hp, new.peak_power_hp) == (217.0, 215.0)


# ── 2. The patch on a database that still holds the duplicates ───────────────


@pytest.fixture(scope="module")
def duplicated_db(patch_module):
    """A real-schema DB holding each surviving bike AND a re-created duplicate
    (the removed row's natural key), plus a saved run and a tire fitment
    hanging off every duplicate."""
    tmp = Path(tempfile.mkdtemp()) / "dup.db"
    db = MotoQuantDB(str(tmp))
    db.connect()
    db.initialize()
    survivors, losers = [], []
    for mfr, model, (lose_code, lose_year), (
        keep_code,
        keep_year,
    ) in patch_module.DUPLICATES:
        keep = _spec(mfr, model, keep_year)
        assert keep.model_code == keep_code
        survivors.append(keep)
        losers.append(
            dataclasses.replace(
                keep,
                model_name=model,
                model_code=lose_code,
                year_from=lose_year,
                year_to=lose_year + 1,
                dry_mass_kg=(keep.dry_mass_kg or keep.wet_mass_kg) + 20.0,
                wet_mass_kg=None,
            )
        )
    out = import_batch(db, survivors + losers)
    assert out["errors"] == 0
    conn = db.conn
    tire_mfr = conn.execute(
        "INSERT INTO tire_manufacturers (name) VALUES ('TestTyreCo')"
    ).lastrowid
    tire_id = conn.execute(
        "INSERT INTO tire_models (manufacturer_id, model_name, compound_type, "
        "position, size_designation) VALUES (?, 'T', 'sport', 'rear', '130/70-17')",
        (tire_mfr,),
    ).lastrowid
    loser_ids = []
    for mfr, model, (lose_code, lose_year), _keep in patch_module.DUPLICATES:
        row = conn.execute(
            "SELECT bm.id FROM bike_models bm JOIN manufacturers m ON "
            "m.id = bm.manufacturer_id WHERE m.name = ? AND bm.year_from = ? "
            "AND bm.model_code IS ? AND bm.model_name LIKE ?",
            (mfr, lose_year, lose_code, model + "%"),
        ).fetchone()
        assert row is not None, (mfr, model)
        loser_ids.append(row[0])
        cfg_id = conn.execute(
            "SELECT id FROM bike_configs WHERE bike_model_id = ?", (row[0],)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO sim_runs (bike_config_id, et_quarter_s, notes) "
            "VALUES (?, 14.0, ?)",
            (cfg_id, f"{mfr} {model}"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO bike_tire_fitments (bike_model_id, "
            "tire_model_id, position) VALUES (?, ?, 'rear')",
            (row[0], tire_id),
        )
    conn.commit()
    n_before = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    db.close()
    first = patch_module.apply(str(tmp), verbose=False)
    second = patch_module.apply(str(tmp), verbose=False)
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    yield conn, loser_ids, n_before, first, second
    conn.close()
    shutil.rmtree(tmp.parent, ignore_errors=True)


def test_patch_removes_every_duplicate(duplicated_db, patch_module):
    conn, loser_ids, n_before, first, _second = duplicated_db
    n = len(patch_module.DUPLICATES)
    assert n_before == 2 * n
    assert first["duplicates"]["bikes_removed"] == n
    assert conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0] == n
    marks = ",".join("?" * len(loser_ids))
    assert (
        conn.execute(
            f"SELECT COUNT(*) FROM bike_models WHERE id IN ({marks})", loser_ids
        ).fetchone()[0]
        == 0
    )


def test_patch_leaves_no_orphans(duplicated_db):
    conn, loser_ids, _n, _first, _second = duplicated_db
    marks = ",".join("?" * len(loser_ids))
    for table in ("bike_configs", "bike_tire_fitments"):
        n = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE bike_model_id IN ({marks})", loser_ids
        ).fetchone()[0]
        assert n == 0, table
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    for table, col in (
        ("dyno_curves", "bike_config_id"),
        ("sim_runs", "bike_config_id"),
    ):
        n = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {col} NOT IN "
            "(SELECT id FROM bike_configs)"
        ).fetchone()[0]
        assert n == 0, table
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM data_provenance WHERE entity_type = 'bike_config' "
            "AND entity_id NOT IN (SELECT id FROM bike_configs)"
        ).fetchone()[0]
        == 0
    )


def test_patch_repoints_saved_runs_to_the_surviving_bike(duplicated_db, patch_module):
    conn, _loser_ids, _n, first, _second = duplicated_db
    n = len(patch_module.DUPLICATES)
    assert first["duplicates"]["runs_repointed"] == n
    rows = conn.execute(
        "SELECT sr.notes, m.name AS mfr, bm.model_name, bm.model_code FROM sim_runs sr "
        "JOIN bike_configs bc ON bc.id = sr.bike_config_id "
        "JOIN bike_models bm ON bm.id = bc.bike_model_id "
        "JOIN manufacturers m ON m.id = bm.manufacturer_id"
    ).fetchall()
    assert len(rows) == n
    keep_codes = {(d[0], d[1]): d[3][0] for d in patch_module.DUPLICATES}
    for r in rows:
        assert r["notes"] == f"{r['mfr']} {_strip_year(r['model_name'])}"
        assert r["model_code"] == keep_codes[(r["mfr"], _strip_year(r["model_name"]))]


def test_patch_sets_survivor_years_and_name_from_the_spec(duplicated_db, patch_module):
    conn, _loser_ids, _n, _first, _second = duplicated_db
    for mfr, model, _lose, (keep_code, keep_year) in patch_module.DUPLICATES:
        spec = _spec(mfr, model, keep_year)
        row = conn.execute(
            "SELECT bm.* FROM bike_models bm JOIN manufacturers m ON "
            "m.id = bm.manufacturer_id WHERE m.name = ? AND bm.model_code = ? "
            "AND bm.model_name LIKE ?",
            (mfr, keep_code, model + "%"),
        ).fetchone()
        assert (row["year_from"], row["year_to"]) == (spec.year_from, spec.year_to)
        assert row["model_name"] == f"{model} ({spec.year_from}-{spec.year_to})"
        dry = spec.dry_mass_kg if spec.dry_mass_kg else spec.wet_mass_kg - 25.0
        assert row["dry_mass_kg"] == pytest.approx(dry)


def test_patch_is_idempotent(duplicated_db, patch_module):
    _conn, _loser_ids, _n, _first, second = duplicated_db
    assert patch_module.total_changes(second) == 0


# ── 3. The shipped database ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def shipped_copy(patch_module):
    src = ROOT / "motoquant.db"
    if not src.exists():
        pytest.skip("no motoquant.db")
    tmp = Path(tempfile.mkdtemp()) / "t.db"
    shutil.copy(src, tmp)
    result = patch_module.apply(str(tmp), verbose=False)
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    yield conn, result
    conn.close()
    shutil.rmtree(tmp.parent, ignore_errors=True)


def test_shipped_db_already_carries_the_patch(shipped_copy, patch_module):
    _conn, result = shipped_copy
    assert patch_module.total_changes(result) == 0


def test_shipped_db_has_one_row_per_spec(shipped_copy):
    conn, _result = shipped_copy
    n = conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0]
    # the 3 hand-curated reference bikes are not in ALL_KNOWN_BIKES
    assert n == len(ALL_KNOWN_BIKES) + 3


def test_shipped_db_has_no_overlapping_year_duplicates(shipped_copy):
    conn, _result = shipped_copy
    rows = conn.execute(
        "SELECT m.name AS mfr, bm.model_name, bm.year_from, bm.year_to "
        "FROM bike_models bm JOIN manufacturers m ON m.id = bm.manufacturer_id"
    ).fetchall()
    families: dict = {}
    for r in rows:
        key = (r["mfr"].lower(), _strip_year(r["model_name"]).lower())
        families.setdefault(key, []).append(r)
    # The plain 848 mis-named "848 EVO" (rename queued) is the one known overlap;
    # see tests/test_catalog_no_duplicates.py::KNOWN_OVERLAPS.
    known = {("ducati", "848 evo")}
    overlaps = [
        (key, a["year_from"], a["year_to"], b["year_from"], b["year_to"])
        for key, group in families.items()
        if key not in known
        for a, b in itertools.combinations(group, 2)
        if a["year_from"] is not None
        and b["year_from"] is not None
        and min(a["year_to"] or a["year_from"], b["year_to"] or b["year_from"])
        >= max(a["year_from"], b["year_from"])
    ]
    assert overlaps == []
