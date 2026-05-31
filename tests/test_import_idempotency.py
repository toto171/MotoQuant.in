"""
MotoQuant Pro — Import Idempotency Regression Tests (2026-05-31)
================================================================
Guards the de-duplication fix in ``bike_repo.create_model`` / ``create_config``.

Root cause of the bug these tests pin: the
``UNIQUE(manufacturer_id, model_name, model_code, year_from)`` index cannot dedupe
rows whose ``model_code`` is NULL, because SQLite treats NULLs as DISTINCT in UNIQUE
constraints. Most catalog bikes have a NULL ``model_code``, so repeated
``import --known-bikes`` runs re-inserted the same bikes and inflated the catalog to
796 rows / 301 phantom duplicates (e.g. ``Norden 901 Expedition`` ×10).

Every test below drives the REAL repository path and must FAIL if the fix is reverted.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motoquant.database import MotoQuantDB
from motoquant.database.bike_repo import _normalize_model_name
from motoquant.defaults import gsxr1000_k5


@pytest.fixture
def db():
    path = os.path.join("/tmp", f"mq_idem_{os.getpid()}.db")
    database = MotoQuantDB(path)
    database.initialize()
    yield database
    database.close()
    try:
        os.unlink(path)
    except OSError:
        pass


class TestCreateModelIdempotent:
    def test_null_code_year_suffix_not_duplicated(self, db):
        """The exact failure shape: NULL model_code + year-suffixed name, imported
        ten times, must collapse to ONE row (this is the Norden 901 Expedition bug)."""
        mfr = db.bikes.get_or_create_manufacturer("Husqvarna")
        ids = [
            db.bikes.create_model(
                manufacturer_id=mfr,
                model_name="Norden 901 Expedition (2025)",
                model_code=None,
                year_from=2025,
                year_to=2025,
                category="adventure",
            )
            for _ in range(10)
        ]
        assert len(set(ids)) == 1, "ten imports should reuse a single row"
        assert db.bikes.count_models() == 1

    def test_distinct_generations_preserved(self, db):
        """Same normalized name but different year ranges are distinct generations
        and must stay as separate rows — the fix must not over-collapse."""
        mfr = db.bikes.get_or_create_manufacturer("Suzuki")
        a = db.bikes.create_model(
            manufacturer_id=mfr, model_name="GSX-R 1000 (2003-2004)",
            year_from=2003, year_to=2004,
        )
        b = db.bikes.create_model(
            manufacturer_id=mfr, model_name="GSX-R 1000 (2007-2008)",
            year_from=2007, year_to=2008,
        )
        assert a != b
        assert db.bikes.count_models() == 2
        # Re-importing the first generation reuses its row, not a third.
        a2 = db.bikes.create_model(
            manufacturer_id=mfr, model_name="GSX-R 1000 (2003-2004)",
            year_from=2003, year_to=2004,
        )
        assert a2 == a
        assert db.bikes.count_models() == 2

    def test_suffix_variant_collapses(self, db):
        """'Foo (2025)' and 'Foo' with the same year range are the same bike."""
        mfr = db.bikes.get_or_create_manufacturer("TestMoto")
        a = db.bikes.create_model(
            manufacturer_id=mfr, model_name="Zoomer 500 (2025)",
            year_from=2025, year_to=2025,
        )
        b = db.bikes.create_model(
            manufacturer_id=mfr, model_name="Zoomer 500",
            year_from=2025, year_to=2025,
        )
        assert a == b
        assert db.bikes.count_models() == 1

    def test_differing_model_code_same_bike_collapses(self, db):
        """Same bike re-scraped with a different model_code must not duplicate
        (the Yezdi Adventure 'Adv' vs 'BG6-ADV' case)."""
        mfr = db.bikes.get_or_create_manufacturer("Yezdi")
        a = db.bikes.create_model(
            manufacturer_id=mfr, model_name="Adventure (2022-2026)",
            model_code="Adv", year_from=2022, year_to=2026,
        )
        b = db.bikes.create_model(
            manufacturer_id=mfr, model_name="Adventure (2022-2026)",
            model_code="BG6-ADV", year_from=2022, year_to=2026,
        )
        assert a == b
        assert db.bikes.count_models() == 1


class TestUpsertConfigIdempotent:
    def test_reimport_same_spec_one_model_one_config(self, db):
        """upsert_from_config twice with the same BikeConfig => 1 model, 1 config,
        no version churn (this is the daily autonomous-import path)."""
        cfg = gsxr1000_k5()
        m1, c1 = db.bikes.upsert_from_config(cfg)
        m2, c2 = db.bikes.upsert_from_config(cfg)
        assert m1 == m2
        assert c1 == c2
        assert db.bikes.count_models() == 1
        assert db.bikes.count_configs() == 1
        assert db.bikes.get_current_config(m1)["version"] == 1

    def test_changed_spec_creates_new_version(self, db):
        """A genuine spec change must still version — idempotency must not freeze
        legitimate updates."""
        cfg = gsxr1000_k5()
        m1, c1 = db.bikes.upsert_from_config(cfg)
        cfg.engine.peak_power_hp = 999.0
        m2, c2 = db.bikes.upsert_from_config(cfg)
        assert m1 == m2
        assert c2 != c1
        assert db.bikes.count_configs() == 2
        assert db.bikes.get_current_config(m1)["version"] == 2


class TestNormalizeHelper:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Norden 901 Expedition (2025)", "norden 901 expedition"),
            ("GSX-R 1000 (2003-2004)", "gsx-r 1000"),
            ("YZF-R1  4C8", "yzf-r1 4c8"),
            ("Hayabusa", "hayabusa"),
            (None, ""),
            ("Ninja ZX-10R (2021-24)", "ninja zx-10r"),
        ],
    )
    def test_normalize(self, raw, expected):
        assert _normalize_model_name(raw) == expected
