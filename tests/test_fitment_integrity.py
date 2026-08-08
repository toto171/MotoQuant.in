"""OEM tire-fitment integrity (2026-08-08 audit §3.3b).

Pins the two halves of the fitment fix, plus the shipped-DB cleanup:

1. `seed.pick_oem_tire` filters candidate compounds through an ALLOWLIST
   (`seed.OEM_COMPOUNDS`). The old denylist ('race', 'drag_dot',
   'drag_slick') did not name the catalog's 'drag' compound, and since
   fallback candidates are ordered mu_peak DESC those 1.85-mu drag slicks
   WON the ±20 mm fallback — the shipped DB asserted drag rubber as the
   factory fitment for 24 bikes.

2. `TireRepository.link_bike_fitment(is_default=True)` SUPERSEDES the
   previous default for the same (bike, position). It used
   INSERT OR REPLACE against a UNIQUE key that includes the tire, so a
   changed pick appended a second is_default=1 row instead of replacing
   the first — 77 such groups had accumulated.

3. `scripts/patch_2026_08_08_fitment_integrity.py` cleans that damage out
   of the shipped motoquant.db.

Every test drives the production code path (real repository class, real
seeder, real patch script) per the AGENTS.md regression-test rule, and
fails if the production fix is reverted. The shipped DB is only ever read;
the patch is exercised against a TEMP COPY.
"""

import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "motoquant.db"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from motoquant.database.connection import MotoQuantDB  # noqa: E402
from motoquant.database.seed import (  # noqa: E402
    OEM_COMPOUNDS,
    seed_bike_tire_fitments,
)

# ── the two invariants, as SQL ──────────────────────────────────────────
_COMPOUND_PLACEHOLDERS = ", ".join("?" * len(OEM_COMPOUNDS))

SQL_NON_OEM_COMPOUND_DEFAULTS = f"""
    SELECT btf.bike_model_id, btf.position, tm.compound_type
    FROM bike_tire_fitments btf
    JOIN tire_models tm ON tm.id = btf.tire_model_id
    WHERE btf.fitment_type = 'oem' AND btf.is_default = 1
      AND tm.compound_type NOT IN ({_COMPOUND_PLACEHOLDERS})
"""

SQL_DUPLICATE_DEFAULTS = """
    SELECT bike_model_id, position, COUNT(*) AS n
    FROM bike_tire_fitments
    WHERE fitment_type = 'oem' AND is_default = 1
    GROUP BY bike_model_id, position
    HAVING COUNT(*) > 1
"""


def _violations(conn):
    """(non-OEM-compound default rows, duplicate-default groups)."""
    bad = conn.execute(SQL_NON_OEM_COMPOUND_DEFAULTS, sorted(OEM_COMPOUNDS)).fetchall()
    dupes = conn.execute(SQL_DUPLICATE_DEFAULTS).fetchall()
    return [tuple(r) for r in bad], [tuple(r) for r in dupes]


class _TempDBMixin:
    def _tmp_path(self, suffix=".db"):
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.close()
        self.addCleanup(lambda p=tmp.name: Path(p).unlink(missing_ok=True))
        return tmp.name


class TestFreshSeedProducesCleanFitments(_TempDBMixin, unittest.TestCase):
    """Production path: seed_bike_tire_fitments on a fresh DB."""

    # A rear size no street tire matches exactly — it can only be resolved by
    # the ±20 mm fallback, which is exactly where the drag slick used to win.
    REAR_SIZE = "200/60ZR17"

    def _fresh_db(self):
        db = MotoQuantDB(self._tmp_path())
        db.connect()
        db.initialize()

        # Street rubber that legitimately answers the fallback (width 190,
        # within 20 mm of 200) …
        self.street_id = db.tires.create(
            manufacturer_name="Bridgestone",
            model_name="Battlax Hypersport S23",
            size_designation="190/55ZR17",
            compound_type="sport",
            position="rear",
            mu_peak=1.39,
            width_mm=190,
            aspect_ratio=55,
            rim_diameter_inch=17,
        )
        # … and a drag slick that beats it on mu_peak, so any mu-ordered
        # candidate list hands it over first. The whole defect in one row.
        self.drag_id = db.tires.create(
            manufacturer_name="M&H",
            model_name="Racemaster 5.5/18",
            size_designation="180/55ZR17",
            compound_type="drag",
            position="rear",
            mu_peak=1.85,
            width_mm=180,
            aspect_ratio=55,
            rim_diameter_inch=17,
        )

        mfr_id = db.bikes.get_or_create_manufacturer("Ducati")
        self.bike_id = db.bikes.create_model(
            manufacturer_id=mfr_id,
            model_name="Panigale V4 (fitment fixture)",
            year_from=2020,
            year_to=2024,
            category="sport",
        )
        # Only tire_params is read by the seeder; the other param blobs are
        # NOT NULL, so fill them with empty objects.
        blob_cols = [
            "chassis_params",
            "engine_params",
            "forced_induction_params",
            "drivetrain_params",
            "clutch_params",
            "aero_params",
            "suspension_params",
            "braking_params",
            "wheelie_params",
            "rider_params",
            "parasitic_params",
            "staging_params",
        ]
        db.conn.execute(
            f"""INSERT INTO bike_configs
                  (bike_model_id, config_name, is_current, tire_params,
                   {", ".join(blob_cols)})
                VALUES (?, 'stock', 1, ?, {", ".join(["'{}'"] * len(blob_cols))})""",
            (self.bike_id, json.dumps({"rear_size": self.REAR_SIZE})),
        )
        db.conn.commit()
        return db

    def test_seed_never_picks_drag_rubber_as_oem(self):
        db = self._fresh_db()
        seed_bike_tire_fitments(db)

        bad, dupes = _violations(db.conn)
        self.assertEqual(bad, [], f"drag/race compound seeded as OEM default: {bad}")
        self.assertEqual(dupes, [], f"duplicate OEM defaults: {dupes}")

        picked = db.conn.execute(
            """SELECT tire_model_id FROM bike_tire_fitments
               WHERE bike_model_id = ? AND position = 'rear'""",
            (self.bike_id,),
        ).fetchall()
        self.assertEqual(
            [r["tire_model_id"] for r in picked],
            [self.street_id],
            "fallback must resolve to the street tire, not the higher-mu slick",
        )
        db.close()

    def test_reseed_after_pick_changes_supersedes_instead_of_duplicating(self):
        """The ~7-rows-per-seed-run growth path, end to end."""
        db = self._fresh_db()
        seed_bike_tire_fitments(db)

        # A grippier street tire lands in the catalog, so the fallback's
        # mu-ordered first hit changes on the next run.
        better_id = db.tires.create(
            manufacturer_name="Michelin",
            model_name="Power 5",
            size_designation="190/55ZR17",
            compound_type="sport",
            position="rear",
            mu_peak=1.42,
            width_mm=190,
            aspect_ratio=55,
            rim_diameter_inch=17,
        )
        seed_bike_tire_fitments(db)

        rows = db.conn.execute(
            """SELECT tire_model_id, is_default FROM bike_tire_fitments
               WHERE bike_model_id = ? AND position = 'rear'
                 AND fitment_type = 'oem'""",
            (self.bike_id,),
        ).fetchall()
        self.assertEqual(
            [(r["tire_model_id"], r["is_default"]) for r in rows],
            [(better_id, 1)],
            "a changed pick must supersede the old OEM row, not append to it",
        )

        bad, dupes = _violations(db.conn)
        self.assertEqual(bad, [])
        self.assertEqual(dupes, [])
        db.close()


class TestLinkBikeFitmentSupersedes(_TempDBMixin, unittest.TestCase):
    """Unit-pins the repository contract the seeder relies on."""

    def setUp(self):
        self.db = MotoQuantDB(self._tmp_path())
        self.db.connect()
        self.db.initialize()
        self.addCleanup(self.db.close)

        def tire(name, size, compound, mu):
            return self.db.tires.create(
                manufacturer_name="Fixture",
                model_name=name,
                size_designation=size,
                compound_type=compound,
                position="rear",
                mu_peak=mu,
            )

        self.tire_a = tire("A", "180/55ZR17", "sport", 1.30)
        self.tire_b = tire("B", "190/55ZR17", "sport", 1.40)
        mfr_id = self.db.bikes.get_or_create_manufacturer("Fixture Motors")
        self.bike_id = self.db.bikes.create_model(
            manufacturer_id=mfr_id, model_name="Fixture One", category="sport"
        )

    def _rows(self, fitment_type=None):
        sql = """SELECT tire_model_id, fitment_type, is_default
                 FROM bike_tire_fitments
                 WHERE bike_model_id = ? AND position = 'rear'"""
        params = [self.bike_id]
        if fitment_type:
            sql += " AND fitment_type = ?"
            params.append(fitment_type)
        return [
            (r["tire_model_id"], r["fitment_type"], r["is_default"])
            for r in self.db.conn.execute(sql + " ORDER BY id", params)
        ]

    def test_default_supersedes_previous_same_type_default(self):
        self.db.tires.link_bike_fitment(self.bike_id, self.tire_a, "rear", "oem", True)
        self.db.tires.link_bike_fitment(self.bike_id, self.tire_b, "rear", "oem", True)
        self.assertEqual(
            self._rows("oem"),
            [(self.tire_b, "oem", 1)],
            "the superseded pick must not survive as a second OEM fitment",
        )

    def test_relinking_the_same_tire_is_idempotent(self):
        first = self.db.tires.link_bike_fitment(
            self.bike_id, self.tire_a, "rear", "oem", True
        )
        second = self.db.tires.link_bike_fitment(
            self.bike_id, self.tire_a, "rear", "oem", True
        )
        self.assertEqual(first, second, "upsert must preserve the row id")
        self.assertEqual(self._rows("oem"), [(self.tire_a, "oem", 1)])

    def test_non_default_link_supersedes_nothing(self):
        """A second OEM option (market/trim variant) is still expressible."""
        self.db.tires.link_bike_fitment(self.bike_id, self.tire_a, "rear", "oem", True)
        self.db.tires.link_bike_fitment(self.bike_id, self.tire_b, "rear", "oem", False)
        self.assertEqual(
            self._rows("oem"),
            [(self.tire_a, "oem", 1), (self.tire_b, "oem", 0)],
        )

    def test_default_demotes_other_types_without_deleting_them(self):
        self.db.tires.link_bike_fitment(
            self.bike_id, self.tire_a, "rear", "recommended", True
        )
        self.db.tires.link_bike_fitment(self.bike_id, self.tire_b, "rear", "oem", True)
        self.assertEqual(
            self._rows(),
            [(self.tire_a, "recommended", 0), (self.tire_b, "oem", 1)],
            "a differing-type default is demoted, never dropped",
        )

    def test_same_tire_in_two_types_still_yields_one_default(self):
        """The demote must key on the row, not on the tire id."""
        self.db.tires.link_bike_fitment(
            self.bike_id, self.tire_a, "rear", "recommended", True
        )
        self.db.tires.link_bike_fitment(self.bike_id, self.tire_a, "rear", "oem", True)
        self.assertEqual(
            self._rows(),
            [(self.tire_a, "recommended", 0), (self.tire_a, "oem", 1)],
        )


class TestShippedDBIsClean(_TempDBMixin, unittest.TestCase):
    """The shipped catalog, with the 2026-08-08 patch applied to a TEMP COPY.

    Reads the tracked motoquant.db and never writes to it. Once the patch has
    been applied to the tracked DB this stays green — the patch is a no-op on
    an already-clean catalog.
    """

    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise unittest.SkipTest("motoquant.db not present")

    def test_no_drag_oem_defaults_and_no_duplicate_defaults(self):
        from patch_2026_08_08_fitment_integrity import apply

        tmp = self._tmp_path()
        shutil.copy(DB_PATH, tmp)
        result = apply(tmp, verbose=False)

        self.assertEqual(result["groups_still_damaged"], 0)
        self.assertEqual(result["fk_violations"], 0)

        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row
        bad, dupes = _violations(conn)
        conn.close()
        self.assertEqual(bad, [], f"shipped DB asserts non-street OEM rubber: {bad}")
        self.assertEqual(dupes, [], f"shipped DB has duplicate OEM defaults: {dupes}")

    def test_patch_is_idempotent(self):
        from patch_2026_08_08_fitment_integrity import apply

        tmp = self._tmp_path()
        shutil.copy(DB_PATH, tmp)
        apply(tmp, verbose=False)
        second = apply(tmp, verbose=False)
        self.assertEqual(second["groups_repaired"], 0)
        self.assertEqual(second["rows_deleted"], 0)


if __name__ == "__main__":
    unittest.main()
