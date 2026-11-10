"""Headline columns: the two branches' rules reconciled (port, 2026-11).

Two independent fixes touched the ``bike_models`` headline columns:

* one branch made them a copy of the physics blob and re-syncs them after every
  reseed (``scripts/patch_2026_10_24_config_sync.py``,
  ``BikeRepository.sync_headline_specs``) - a listed figure must be the one the
  simulation uses;
* the other found that the blob fills a missing bore / stroke / compression
  ratio / wheelbase / seat height with the reference GSX-R1000's value, and
  stores NULL instead (``scripts/patch_2026_11_10_catalog_fixes.py``,
  ``extract_headline_specs(config, spec=...)``).

Left as they were, each script undid the other on every run of the re-seed
chain. The sync is now spec-aware, so both write the same thing. These tests
pin that agreement on the production path (real schema, importer, both patch
scripts) and fail if either side goes back to its old rule.
"""

from __future__ import annotations

import importlib.util
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from motoquant.database import MotoQuantDB
from motoquant.database.bridge import (
    SPEC_ONLY_HEADLINE_FIELDS,
    db_row_to_config,
    extract_headline_specs,
)
from motoquant.defaults import gsxr1000_k5
from motoquant.scraper.importer import import_batch
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

ROOT = Path(__file__).resolve().parent.parent
K5 = gsxr1000_k5()


def _load(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name[:-3] + "_port", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _spec(model_fragment, year=None, mfr=None):
    for s in ALL_KNOWN_BIKES:
        if (
            model_fragment.lower() in s.model_name.lower()
            and (year is None or s.year_from == year)
            and (mfr is None or s.manufacturer == mfr)
        ):
            return s
    raise LookupError(model_fragment)


@pytest.fixture()
def unsynced_db():
    """A real-schema DB whose headline columns carry the reference bike's
    defaults, as every catalog row did before the fix."""
    tmpdir = Path(tempfile.mkdtemp())
    path = tmpdir / "h.db"
    db = MotoQuantDB(str(path))
    db.connect()
    db.initialize()
    specs = [_spec("800X"), _spec("Monkey 125"), _spec("ZX-6R", 2024)]
    assert import_batch(db, specs)["errors"] == 0
    db.conn.execute(
        "UPDATE bike_models SET seat_height_mm = ?, bore_mm = ?, stroke_mm = ?, "
        "compression_ratio = ?",
        (
            K5.chassis.seat_height_mm,
            K5.engine.bore_mm,
            K5.engine.stroke_mm,
            K5.engine.compression_ratio,
        ),
    )
    db.conn.commit()
    db.close()
    yield path, specs
    shutil.rmtree(tmpdir, ignore_errors=True)


def _rows(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = {r["model_name"]: dict(r) for r in conn.execute("SELECT * FROM bike_models")}
    conn.close()
    return rows


def _row_like(rows, fragment):
    return next(v for k, v in rows.items() if fragment in k)


def test_config_sync_stores_null_not_the_reference_default(unsynced_db):
    path, _specs = unsynced_db
    sync = _load("patch_2026_10_24_config_sync.py")
    first = sync.apply(str(path))
    assert first["headline_models_updated"] == 3
    rows = _rows(path)
    kove = _row_like(rows, "800X")
    spec = _spec("800X")
    assert spec.bore_mm is None and spec.seat_height_mm is None
    for col in ("bore_mm", "stroke_mm", "compression_ratio", "seat_height_mm"):
        assert kove[col] is None, col
    # a figure the spec does carry is still written, and equals the physics
    monkey, mspec = _row_like(rows, "Monkey 125"), _spec("Monkey 125")
    assert monkey["bore_mm"] == mspec.bore_mm
    assert monkey["compression_ratio"] == mspec.compression_ratio
    # bore x stroke that contradicts the displacement is not listed
    zx6r = _row_like(rows, "ZX-6R")
    assert zx6r["bore_mm"] is None and zx6r["stroke_mm"] is None
    assert zx6r["displacement_cc"] == _spec("ZX-6R", 2024).displacement_cc
    assert all(v == 0 for v in sync.apply(str(path)).values())


def test_sync_and_catalog_fixes_agree_in_either_order(unsynced_db):
    """Whichever script runs first, the other finds nothing left to change -
    the property the re-seed chain's 'second run reports zero' rests on."""
    path, _specs = unsynced_db
    sync = _load("patch_2026_10_24_config_sync.py")
    fixes = _load("patch_2026_11_10_catalog_fixes.py")
    other = path.with_name("other.db")
    shutil.copy(path, other)

    sync.apply(str(path))
    after_sync = _rows(path)
    assert fixes.apply(str(path), verbose=False)["headline"]["bikes_changed"] == 0

    assert fixes.apply(str(other), verbose=False)["headline"]["bikes_changed"] == 3
    again = sync.apply(str(other))
    assert again["headline_models_updated"] == 0, again
    after_fixes = _rows(other)
    for name, row in after_sync.items():
        for col in SPEC_ONLY_HEADLINE_FIELDS:
            assert row[col] == after_fixes[name][col], (name, col)


def test_stored_headline_figures_equal_the_physics_blob(unsynced_db):
    """NULL replaces a borrowed default; it never replaces a real figure with
    a different one. Every non-NULL column is the blob's value."""
    path, _specs = unsynced_db
    _load("patch_2026_10_24_config_sync.py").apply(str(path))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    checked = 0
    for cfg_row in conn.execute("SELECT * FROM bike_configs WHERE is_current = 1"):
        model = conn.execute(
            "SELECT * FROM bike_models WHERE id = ?", (cfg_row["bike_model_id"],)
        ).fetchone()
        blob = extract_headline_specs(db_row_to_config(dict(cfg_row)))
        for col, val in blob.items():
            if model[col] is None and col in SPEC_ONLY_HEADLINE_FIELDS:
                continue
            assert model[col] == pytest.approx(val), (model["model_name"], col)
            checked += 1
    conn.close()
    assert checked >= 3 * (len(blob) - len(SPEC_ONLY_HEADLINE_FIELDS))


def test_bike_without_a_spec_keeps_the_plain_blob_copy():
    """The three hand-curated reference bikes have no ALL_KNOWN_BIKES spec:
    their own figures live in the config, and the sync must keep writing them
    (seat height 810 mm IS the GSX-R1000's seat height)."""
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    model_id, _cfg_id = db.bikes.upsert_from_config(
        K5, manufacturer_name="Suzuki", model_code="K5"
    )
    db.conn.execute(
        "UPDATE bike_models SET seat_height_mm = NULL, bore_mm = NULL WHERE id = ?",
        (model_id,),
    )
    changed = db.bikes.sync_headline_specs(model_id, K5)
    assert changed == ["bore_mm", "seat_height_mm"]
    row = db.bikes.get_model(model_id)
    assert row["seat_height_mm"] == K5.chassis.seat_height_mm
    assert row["bore_mm"] == K5.engine.bore_mm
    db.close()
