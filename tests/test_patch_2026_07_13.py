"""Regression pin for scripts/patch_2026_07_13_scrape_data.py (July-10, 2026
web-scrape data application: parts INR/USD reprice, discontinued flags,
fictional-brand honesty renames, and tire family status/pricing).

Copies the shipped motoquant.db to a throwaway temp file, drives the
patch's real ``main(db_path=...)`` against the copy twice (never a
re-implementation of its logic — per the CLAUDE.md regression-test rule,
this must fail if the production patch regresses), and pins:

  1. idempotency — the second run reports 0 total changes, and 0 changes
     per individual action.
  2. a handful of spot values after the first run, chosen to cover each of
     the six actions: an INR reprice, a USD->INR landed-cost reprice, a
     discontinued-availability flag, a fictional-brand rename (and that no
     ClutchCo-branded row survives), a tire family status flag, and a
     tire price application.

The repo's shipped motoquant.db is never touched — every assertion runs
against the temp copy.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "motoquant.db"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import patch_2026_07_13_scrape_data as patch_mod  # noqa: E402


class TestScrapeDataPatchIdempotent(unittest.TestCase):
    """Runs the real patch twice against a throwaway DB copy."""

    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise unittest.SkipTest(f"{DB_PATH} not present")
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        shutil.copyfile(DB_PATH, tmp.name)
        cls.db_path = tmp.name

        cls.first_summary = patch_mod.main(db_path=cls.db_path)
        cls.second_summary = patch_mod.main(db_path=cls.db_path)

    @classmethod
    def tearDownClass(cls):
        Path(cls.db_path).unlink(missing_ok=True)

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── idempotency ────────────────────────────────────────────────
    # NOTE: these tests copy the repo's shipped motoquant.db, which itself
    # gets this patch applied for real as part of shipping it — so by the
    # time this test file runs in CI, "first run" may already be a no-op
    # against an already-patched source DB. Assertions here therefore pin
    # target-state INVARIANTS (changed + noop == the fixed count of
    # qualifying rows derived from the scrape JSON, which does not depend
    # on whether the source DB started patched or not) rather than
    # "changed > 0", which would be true only on a pristine pre-patch DB.
    def test_first_run_reaches_expected_target_counts(self):
        self.assertNotIn("error", self.first_summary)
        expected_totals = {
            "inr_reprice": 72,
            "usd_reprice": 210,
            "discontinued": 6,
            "fictional_brand_renames": 25,
            "tire_family_status": 48,
            "tire_prices": 19,
        }
        for key, expected in expected_totals.items():
            s = self.first_summary[key]
            self.assertEqual(
                s["changed"] + s["noop"],
                expected,
                f"action {key!r}: changed+noop == {s['changed'] + s['noop']}, "
                f"expected {expected} qualifying rows",
            )

    def test_second_run_is_fully_idempotent(self):
        self.assertNotIn("error", self.second_summary)
        self.assertEqual(self.second_summary["total_changed"], 0)
        for key in patch_mod._ACTION_ORDER:
            self.assertEqual(
                self.second_summary[key]["changed"],
                0,
                f"action {key!r} was not idempotent on the second run",
            )

    def test_no_foreign_key_violations(self):
        self.assertNotIn("foreign_key_violations", self.first_summary)
        self.assertNotIn("foreign_key_violations", self.second_summary)

    # ── action 1: INR reprice ──────────────────────────────────────
    def test_part_527_inr_reprice_applied(self):
        """EBC HH Sintered Brake Pads (Panigale V4R) — confirmed India
        retail listing, Rs 3,800 (DB) -> Rs 24,000 (web, motomillion.com)."""
        row = (
            self._conn()
            .execute("SELECT price_inr, last_price_check FROM parts WHERE id = 527")
            .fetchone()
        )
        self.assertEqual(row["price_inr"], 24000.0)
        self.assertEqual(row["last_price_check"], "2026-07-13")

    # ── action 2: USD-only reprice via the landed-cost helper ──────
    def test_usd_only_part_gets_landed_cost_and_keeps_usd(self):
        """Part 1 (Driven Racing 520 Front Sprocket 14T) is USD-only
        ($35, drivenracing.com) with no INR listing — must be converted
        through estimate_landing_cost_inr, not left null."""
        row = (
            self._conn()
            .execute(
                "SELECT price_inr, price_usd, last_price_check FROM parts WHERE id = 1"
            )
            .fetchone()
        )
        self.assertIsNotNone(row["price_inr"])
        self.assertGreater(row["price_inr"], 0)
        self.assertEqual(row["price_usd"], 35.0)
        self.assertEqual(row["last_price_check"], "2026-07-13")

    def test_excluded_usd_ids_not_repriced_by_action_2(self):
        """The 7 hard-excluded ids (proxy prices on found=false SKUs, or no
        source_url) must not have been touched by the USD reprice pass. They
        already carry a (pre-existing, un-web-verified) price_inr on the
        shipped catalog, so the signal this patch didn't touch them is
        last_price_check staying at its pre-patch value rather than being
        stamped 2026-07-13."""
        conn_orig = sqlite3.connect(DB_PATH)
        conn_orig.row_factory = sqlite3.Row
        conn_patched = self._conn()
        for pid in sorted(patch_mod.EXCLUDE_USD_REPRICE_IDS):
            before = conn_orig.execute(
                "SELECT price_inr, last_price_check FROM parts WHERE id = ?", (pid,)
            ).fetchone()
            after = conn_patched.execute(
                "SELECT price_inr, last_price_check FROM parts WHERE id = ?", (pid,)
            ).fetchone()
            self.assertEqual(
                after["price_inr"],
                before["price_inr"],
                f"part {pid} price_inr changed despite exclusion",
            )
            self.assertEqual(
                after["last_price_check"],
                before["last_price_check"],
                f"part {pid} last_price_check changed despite exclusion",
            )
            self.assertNotEqual(after["last_price_check"], "2026-07-13")
        conn_orig.close()

    # ── action 3: discontinued parts ───────────────────────────────
    def test_part_51_marked_discontinued(self):
        row = (
            self._conn()
            .execute("SELECT availability FROM parts WHERE id = 51")
            .fetchone()
        )
        self.assertEqual(row["availability"], "discontinued")

    def test_all_discontinued_ids_flagged(self):
        conn = self._conn()
        for pid in patch_mod.DISCONTINUED_PART_IDS:
            row = conn.execute(
                "SELECT availability FROM parts WHERE id = ?", (pid,)
            ).fetchone()
            self.assertEqual(row["availability"], "discontinued", f"part {pid}")

    # ── action 4: fictional-brand honesty renames ──────────────────
    def test_clutchco_brand_is_gone(self):
        n = (
            self._conn()
            .execute("SELECT COUNT(*) FROM parts WHERE brand = 'ClutchCo'")
            .fetchone()[0]
        )
        self.assertEqual(n, 0)

    def test_regina_pro_and_sprocket_specialists_brands_are_gone(self):
        conn = self._conn()
        for brand in ("Regina Pro", "Sprocket Specialists"):
            n = conn.execute(
                "SELECT COUNT(*) FROM parts WHERE brand = ?", (brand,)
            ).fetchone()[0]
            self.assertEqual(n, 0, f"{brand} rows still present")

    def test_renamed_parts_now_generic_with_class_names(self):
        conn = self._conn()
        for fix in patch_mod.FICTIONAL_BRAND_RENAMES:
            row = conn.execute(
                "SELECT brand, model_name FROM parts WHERE id = ?", (fix["id"],)
            ).fetchone()
            self.assertEqual(row["brand"], "Generic")
            self.assertEqual(row["model_name"], fix["new_name"])

    def test_no_duplicate_generic_brand_names(self):
        """The rename must not have collided with pre-existing Generic-brand
        rows or with each other."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT model_name, COUNT(*) c FROM parts WHERE brand = 'Generic' "
            "GROUP BY model_name HAVING COUNT(*) > 1"
        ).fetchall()
        self.assertEqual(list(rows), [])

    # ── action 5: tire family status ───────────────────────────────
    def test_tire_4_pilot_power_3_marked_unavailable_and_tagged(self):
        """Michelin Pilot Power 3 (family incl. tire id 4) is discontinued
        per the scrape (superseded by Power RS then Power 5)."""
        row = (
            self._conn()
            .execute(
                "SELECT available_india, data_source FROM tire_models WHERE id = 4"
            )
            .fetchone()
        )
        self.assertEqual(row["available_india"], 0)
        self.assertIn("scrape 2026-07-10: discontinued", row["data_source"])

    def test_not_found_family_tagged(self):
        """Maxxis Insane (tire id 161) — status 'not_found' in the scrape."""
        row = (
            self._conn()
            .execute(
                "SELECT available_india, data_source FROM tire_models WHERE id = 161"
            )
            .fetchone()
        )
        self.assertEqual(row["available_india"], 0)
        self.assertIn("scrape 2026-07-10: not found as named", row["data_source"])

    def test_current_family_tire_row_untouched(self):
        """Apollo Alpha H1 (tire id 195) is status='current' — action 5 must
        not touch its available_india flag."""
        row = (
            self._conn()
            .execute("SELECT available_india FROM tire_models WHERE id = 195")
            .fetchone()
        )
        self.assertEqual(row["available_india"], 1)

    # ── action 6: tire prices ───────────────────────────────────────
    def test_tire_price_conflict_left_untouched(self):
        """Tire 195 (Apollo Alpha H1) has two disagreeing India price
        points in the scrape (Rs 6,710 vs Rs 4,399 for the same single-row
        family) — the patch must decline to pick one."""
        row = (
            self._conn()
            .execute("SELECT price_inr FROM tire_models WHERE id = 195")
            .fetchone()
        )
        self.assertIsNone(row["price_inr"])

    def test_tire_price_summary_counts_are_consistent(self):
        # conflict_skipped / no_unique_row_match_skipped are derived purely
        # from the scrape JSON + DB row sizes, not from any row's current
        # price_inr — stable regardless of whether the source DB already
        # had this patch applied.
        s = self.first_summary["tire_prices"]
        self.assertEqual(s["conflict_skipped"], 7)
        self.assertEqual(s["no_unique_row_match_skipped"], 20)
        self.assertEqual(len(s["problems"]), s["conflict_skipped"])


if __name__ == "__main__":
    unittest.main()
