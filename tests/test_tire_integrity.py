"""Tire-catalog integrity — duplicate-title guards (July 6, 2026).

Pins the two halves of the tire-dedup fix:

1. The shipped motoquant.db contains no notation-duplicate tire rows —
   no two rows share (manufacturer, model_name, position, normalized
   physical size). Five such rows (MRF Zapper / IRC GP-110 / Bridgestone
   Battlax bias-vs-radial notation twins) were merged by
   scripts/patch_2026_07_06_tire_dedup.py.

2. TireRepository.create() normalizes size notation before matching, so a
   re-seed that writes '100/90R17' against an existing '100/90-17' row
   updates the existing row instead of minting a duplicate.

Both tests drive the production code path (real repo DB / real repository
class), per the CLAUDE.md regression-test rule.
"""

import collections
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from motoquant.database.tire_repo import TireRepository

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "motoquant.db"


class TestNoDuplicateTireTitles(unittest.TestCase):
    def test_no_notation_duplicate_rows(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT t.id, m.name AS mfr, t.model_name, t.position,
                      t.size_designation
               FROM tire_models t
               JOIN tire_manufacturers m ON m.id = t.manufacturer_id"""
        ).fetchall()
        conn.close()
        groups = collections.defaultdict(list)
        for r in rows:
            key = (
                r["mfr"].lower(),
                r["model_name"].strip().lower(),
                r["position"],
                TireRepository.normalize_size_designation(r["size_designation"]),
            )
            groups[key].append(r["id"])
        dupes = {k: v for k, v in groups.items() if len(v) > 1}
        self.assertEqual(
            dupes,
            {},
            f"duplicate tire rows (same mfr+name+position+physical size): {dupes}",
        )


class TestCreateNormalizesSizeNotation(unittest.TestCase):
    def setUp(self):
        # Work on a throwaway copy so the repo DB is never dirtied and the
        # schema (incl. the UNIQUE constraint) is the production one.
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        shutil.copyfile(DB_PATH, self._tmp.name)
        self._conn = sqlite3.connect(self._tmp.name)
        self._conn.row_factory = sqlite3.Row
        self.repo = TireRepository(self._conn)

    def tearDown(self):
        self._conn.close()
        Path(self._tmp.name).unlink(missing_ok=True)

    def test_notation_variant_updates_existing_row(self):
        first = self.repo.create(
            "TestBrand", "UnitTest Grip", "100/90-17", position="front"
        )
        again_radial = self.repo.create(
            "TestBrand", "UnitTest Grip", "100/90R17", position="front"
        )
        again_zr = self.repo.create(
            "TestBrand", "UnitTest Grip", "100/90ZR17", position="front"
        )
        self.assertEqual(first, again_radial)
        self.assertEqual(first, again_zr)
        n = self._conn.execute(
            "SELECT COUNT(*) FROM tire_models WHERE model_name='UnitTest Grip'"
        ).fetchone()[0]
        self.assertEqual(n, 1)

    def test_different_physical_size_still_creates_new_row(self):
        a = self.repo.create(
            "TestBrand", "UnitTest Grip2", "180/55ZR17", position="rear"
        )
        b = self.repo.create(
            "TestBrand", "UnitTest Grip2", "190/50ZR17", position="rear"
        )
        self.assertNotEqual(a, b)

    def test_normalizer_canonical_forms(self):
        norm = TireRepository.normalize_size_designation
        self.assertEqual(norm("100/90-17"), norm("100/90R17"))
        self.assertEqual(norm("100/90ZR17"), norm("100/90B17"))
        self.assertNotEqual(norm("100/90-17"), norm("100/90-19"))
        # exotic drag sizes compare stably without being mangled
        self.assertEqual(norm("26x8.5R15"), norm("26x8.5R15 "))


if __name__ == "__main__":
    unittest.main()
