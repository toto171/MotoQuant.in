"""Regression pin for scripts/patch_2026_07_13_scrape_data.py (July-10, 2026
web-scrape data application: parts INR/USD reprice, discontinued flags,
fictional-brand honesty renames, and tire family status/pricing).

WHY THIS FILE WAS REWRITTEN (2026-08-08)
----------------------------------------
The previous version copied the *shipped* ``motoquant.db`` — which already has
this patch applied — ran the patch against the copy, and then asserted values
that were already true before the run. Sixteen of its seventeen tests were
therefore **vacuous**: they stayed green even if every mutation function in the
patch were deleted, because the shipped DB supplied the expected state on its
own. (Weekly audit 2026-07-25, §3.4.) Only the idempotency test had any teeth,
and only against the trivial "second run does nothing" half of the contract.

WHAT THIS FILE DOES NOW
-----------------------
On a throwaway copy of the DB it **constructs pre-patch state** for a
representative sample of each of the six mutation classes — reversing prices to
a sentinel, un-flagging a discontinued part and a discontinued tire, restoring
the fictional brand names, nulling an applied tire price — then drives the
patch's real ``main(db_path=...)`` and asserts:

  (a) each action reports exactly the number of rows that were reverted as
      ``changed`` (the rest of the catalog is already at target ⇒ ``noop``),
  (b) every reverted row is carried to its documented target state, and
  (c) a second run is a full no-op (0 changes in every action).

Delete any ``_apply_*`` body and the corresponding (a) + (b) assertions go red.

Negative controls (``TestScrapeDataPatchGuards``) additionally pin the two
"decline to act" branches — an unexpected brand/name is reported and skipped
rather than overwritten, and a tire with conflicting scraped price points is
left alone.

The repo's shipped ``motoquant.db`` is never written: every mutation runs
against a temp copy, and the one place the pristine file is read opens it with
``mode=ro``.
"""

from __future__ import annotations

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
import patch_2026_07_13_scrape_data as patch_mod  # noqa: E402

# ── The patch's own inputs, loaded once ──────────────────────────────────
_PARTS_JSON = json.loads(patch_mod.PARTS_JSON.read_text(encoding="utf-8"))["parts"]
_TIRES_JSON = json.loads(patch_mod.TIRES_JSON.read_text(encoding="utf-8"))[
    "tire_families"
]

# ── Sentinels written to build the pre-patch state. Chosen so they cannot
#    collide with any real catalogue value (no scraped price is Rs 1). ─────
_STALE_DATE = "2000-01-01"
_STALE_PRICE_INR = 1.0
_STALE_RETAILER = "PRE-PATCH sentinel retailer"
_STALE_RETAILER_URL = "https://pre-patch-sentinel.invalid/listing"
_STALE_AVAILABILITY = "in_stock"


def _qualifies_for_inr_reprice(p: dict) -> bool:
    """Mirrors action 1's gate — used only to *select* a sample that the patch
    is guaranteed to act on. Nothing is asserted from this; if it ever drifts
    from the patch, the sample simply stops changing and the tests fail loudly.
    """
    return (
        p.get("price_inr") is not None
        and patch_mod._is_http(p.get("source_url"))
        and p.get("found") is not False
    )


def _qualifies_for_usd_reprice(p: dict) -> bool:
    """Mirrors action 2's gate — sample selection only (see above)."""
    return (
        p["id"] not in patch_mod.EXCLUDE_USD_REPRICE_IDS
        and p.get("price_usd") is not None
        and p.get("price_inr") is None
        and patch_mod._is_http(p.get("source_url"))
        and p.get("found") is not False
    )


# Three parts per price action; all six discontinued ids; one rename per
# fictional brand; both rows of a discontinued tire family plus one row of a
# not-found family; two unambiguously-priced tires.
_A1_SAMPLE = [
    p for p in _PARTS_JSON if _qualifies_for_inr_reprice(p) and p.get("retailer")
][:3]
_A2_SAMPLE = [p for p in _PARTS_JSON if _qualifies_for_usd_reprice(p)][:3]
_A4_SAMPLE = [
    next(f for f in patch_mod.FICTIONAL_BRAND_RENAMES if f["old_brand"] == brand)
    for brand in ("ClutchCo", "Regina Pro", "Sprocket Specialists")
]
_DISCONTINUED_TIRE_FAMILY = next(
    f for f in _TIRES_JSON if f.get("status") == "discontinued" and f.get("tire_ids")
)
_NOT_FOUND_TIRE_FAMILY = next(
    f for f in _TIRES_JSON if f.get("status") == "not_found" and f.get("tire_ids")
)
_A5_SAMPLE_IDS = list(_DISCONTINUED_TIRE_FAMILY["tire_ids"]) + [
    _NOT_FOUND_TIRE_FAMILY["tire_ids"][0]
]

# Spot-checked tire prices, provenance straight out of tires_web_data.json:
#   5  — Michelin Road 6 190/55ZR17, IndiaMART (Torque Block, Bengaluru).
#        A 4-row family, resolved to this row by normalised size match.
#   20 — MRF Revz FB, IndiaMART. Single-row family, so the price maps by
#        family identity alone.
_A6_SAMPLE = {5: 28500.0, 20: 8990.0}

_EXPECTED_CHANGED = {
    "inr_reprice": len(_A1_SAMPLE),
    "usd_reprice": len(_A2_SAMPLE),
    "discontinued": len(patch_mod.DISCONTINUED_PART_IDS),
    "fictional_brand_renames": len(_A4_SAMPLE),
    "tire_family_status": len(_A5_SAMPLE_IDS),
    "tire_prices": len(_A6_SAMPLE),
}


def _tire_status_tag(family: dict) -> str:
    """The audit-trail suffix action 5 appends for this family."""
    if family.get("status") == "discontinued":
        return patch_mod._DISCONTINUED_TAG_FMT.format(
            successor=family.get("successor") or "none specified"
        )
    return patch_mod._NOT_FOUND_TAG


def _copy_shipped_db() -> str:
    """A throwaway copy of the shipped catalogue. The original is never opened
    for writing anywhere in this module."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    shutil.copyfile(DB_PATH, tmp.name)
    return tmp.name


def _rw_conn(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _ro_conn(path) -> sqlite3.Connection:
    """Read-only URI connection — cannot rewrite pages of the tracked DB."""
    conn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


class TestScrapeDataPatchMutates(unittest.TestCase):
    """Builds pre-patch state, then proves the patch reaches target state.

    Every assertion here fails if the corresponding ``_apply_*`` function stops
    mutating — which is exactly what the old version of this file could not
    detect.
    """

    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise unittest.SkipTest(f"{DB_PATH} not present")
        cls.db_path = _copy_shipped_db()

        conn = _rw_conn(cls.db_path)
        # Snapshot the (already-patched) target state for the rows whose
        # target value is a derived quantity rather than a literal in the
        # patch or the scrape JSON — action 2's landed cost, and the tire
        # prices. Snapshot BEFORE reverting.
        cls.expected_usd_landed = {
            p["id"]: conn.execute(
                "SELECT price_inr FROM parts WHERE id = ?", (p["id"],)
            ).fetchone()["price_inr"]
            for p in _A2_SAMPLE
        }
        cls._revert_to_pre_patch_state(conn)
        conn.commit()
        conn.close()

        cls.first_summary = patch_mod.main(db_path=cls.db_path)
        cls.second_summary = patch_mod.main(db_path=cls.db_path)

    @classmethod
    def tearDownClass(cls):
        Path(cls.db_path).unlink(missing_ok=True)

    # ── pre-patch state construction ────────────────────────────────────
    @classmethod
    def _revert_to_pre_patch_state(cls, conn: sqlite3.Connection) -> None:
        # action 1 — stale price / retailer / URL / check-date
        for p in _A1_SAMPLE:
            conn.execute(
                "UPDATE parts SET price_inr = ?, retailer = ?, retailer_url = ?, "
                "last_price_check = ? WHERE id = ?",
                (
                    _STALE_PRICE_INR,
                    _STALE_RETAILER,
                    _STALE_RETAILER_URL,
                    _STALE_DATE,
                    p["id"],
                ),
            )
        # action 2 — never priced at all (the genuine pre-patch shape for a
        # USD-only SKU: no INR figure, no USD figure recorded)
        for p in _A2_SAMPLE:
            conn.execute(
                "UPDATE parts SET price_inr = NULL, price_usd = NULL, "
                "last_price_check = ? WHERE id = ?",
                (_STALE_DATE, p["id"]),
            )
        # action 3 — un-flag every discontinued SKU
        conn.executemany(
            "UPDATE parts SET availability = ? WHERE id = ?",
            [(_STALE_AVAILABILITY, pid) for pid in patch_mod.DISCONTINUED_PART_IDS],
        )
        # action 4 — restore the fictional brand + name
        for fix in _A4_SAMPLE:
            conn.execute(
                "UPDATE parts SET brand = ?, model_name = ? WHERE id = ?",
                (fix["old_brand"], fix["old_name"], fix["id"]),
            )
        # action 5 — mark the tire available again and strip the audit tag
        for family in (_DISCONTINUED_TIRE_FAMILY, _NOT_FOUND_TIRE_FAMILY):
            tag = _tire_status_tag(family)
            for tid in family["tire_ids"]:
                if tid not in _A5_SAMPLE_IDS:
                    continue
                row = conn.execute(
                    "SELECT data_source FROM tire_models WHERE id = ?", (tid,)
                ).fetchone()
                conn.execute(
                    "UPDATE tire_models SET available_india = 1, data_source = ? "
                    "WHERE id = ?",
                    ((row["data_source"] or "").replace(tag, ""), tid),
                )
        # action 6 — un-price the tire
        conn.executemany(
            "UPDATE tire_models SET price_inr = NULL WHERE id = ?",
            [(tid,) for tid in _A6_SAMPLE],
        )

    def _conn(self):
        return _rw_conn(self.db_path)

    # ── (a) the patch reports exactly the reverted rows as changed ───────
    def test_each_action_changes_exactly_the_reverted_rows(self):
        """The sharpest single assertion in this file.

        Every other row in the catalogue is already at target, so ``changed``
        must equal the sample size for each action. A deleted mutation reads
        0; an over-broad mutation reads more than the sample."""
        self.assertNotIn("error", self.first_summary)
        for action, expected in _EXPECTED_CHANGED.items():
            with self.subTest(action=action):
                self.assertEqual(
                    self.first_summary[action]["changed"],
                    expected,
                    f"action {action!r} changed "
                    f"{self.first_summary[action]['changed']} rows, expected "
                    f"exactly the {expected} reverted to pre-patch state",
                )

    def test_no_action_reported_unexpected_problems(self):
        """Reverting to pre-patch state must not trip any of the patch's
        "decline to act" guards. ``tire_prices`` is the one action with
        legitimate problem lines: its deliberate conflict skips, pinned in
        ``TestScrapeDataPatchGuards``."""
        for action in patch_mod._ACTION_ORDER:
            if action == "tire_prices":
                continue
            with self.subTest(action=action):
                self.assertEqual(
                    self.first_summary[action]["problems"],
                    [],
                    f"action {action!r} reported problems",
                )
        s = self.first_summary["tire_prices"]
        self.assertEqual(len(s["problems"]), s["conflict_skipped"])

    def test_target_totals_still_cover_the_documented_row_counts(self):
        """changed + noop is the number of qualifying rows and does not depend
        on how many were reverted — the counts SCRAPE_REPORT.md documents."""
        expected_totals = {
            "inr_reprice": 72,
            "usd_reprice": 210,
            "discontinued": 6,
            "fictional_brand_renames": 25,
            "tire_family_status": 48,
            "tire_prices": 19,
        }
        for key, expected in expected_totals.items():
            with self.subTest(action=key):
                s = self.first_summary[key]
                self.assertEqual(s["changed"] + s["noop"], expected)

    # ── (b) target state per action ─────────────────────────────────────
    def test_inr_reprice_writes_the_scraped_india_price_and_source(self):
        conn = self._conn()
        for p in _A1_SAMPLE:
            with self.subTest(part=p["id"]):
                row = conn.execute(
                    "SELECT price_inr, retailer, retailer_url, last_price_check "
                    "FROM parts WHERE id = ?",
                    (p["id"],),
                ).fetchone()
                self.assertEqual(row["price_inr"], round(float(p["price_inr"]), 2))
                self.assertEqual(row["retailer"], p["retailer"])
                self.assertEqual(row["retailer_url"], p["source_url"])
                self.assertEqual(row["last_price_check"], patch_mod.PATCH_DATE)
                self.assertNotEqual(row["retailer"], _STALE_RETAILER)
        conn.close()

    def test_usd_reprice_lands_a_duty_inclusive_inr_price(self):
        """Action 2 must run the USD figure through the project's landed-cost
        helper, not merely multiply by the FX rate: the result carries GST +
        courier (+ import duty where implied), so it is strictly above the raw
        sticker conversion."""
        conn = self._conn()
        for p in _A2_SAMPLE:
            with self.subTest(part=p["id"]):
                row = conn.execute(
                    "SELECT price_inr, price_usd, last_price_check "
                    "FROM parts WHERE id = ?",
                    (p["id"],),
                ).fetchone()
                sticker = float(p["price_usd"]) * patch_mod.USD_TO_INR_RATE
                self.assertIsNotNone(
                    row["price_inr"], "price_inr left NULL — action 2 did not run"
                )
                self.assertEqual(row["price_inr"], self.expected_usd_landed[p["id"]])
                self.assertGreater(
                    row["price_inr"],
                    sticker,
                    "price_inr is at or below the raw USD x rate conversion — "
                    "the landed-cost helper was bypassed",
                )
                self.assertEqual(row["price_usd"], round(float(p["price_usd"]), 2))
                self.assertEqual(row["last_price_check"], patch_mod.PATCH_DATE)
        conn.close()

    def test_discontinued_flag_is_reapplied(self):
        conn = self._conn()
        for pid in patch_mod.DISCONTINUED_PART_IDS:
            with self.subTest(part=pid):
                row = conn.execute(
                    "SELECT availability FROM parts WHERE id = ?", (pid,)
                ).fetchone()
                self.assertEqual(row["availability"], "discontinued")
        conn.close()

    def test_fictional_brands_are_renamed_back_to_honest_names(self):
        conn = self._conn()
        for fix in _A4_SAMPLE:
            with self.subTest(part=fix["id"]):
                row = conn.execute(
                    "SELECT brand, model_name FROM parts WHERE id = ?", (fix["id"],)
                ).fetchone()
                self.assertEqual(row["brand"], fix["new_brand"])
                self.assertEqual(row["model_name"], fix["new_name"])
        for brand in ("ClutchCo", "Regina Pro", "Sprocket Specialists"):
            with self.subTest(brand=brand):
                n = conn.execute(
                    "SELECT COUNT(*) FROM parts WHERE brand = ?", (brand,)
                ).fetchone()[0]
                self.assertEqual(n, 0, f"{brand} rows survived the rename")
        conn.close()

    def test_no_duplicate_generic_brand_names(self):
        """The rename must not collide with pre-existing Generic rows."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT model_name, COUNT(*) c FROM parts WHERE brand = 'Generic' "
            "GROUP BY model_name HAVING COUNT(*) > 1"
        ).fetchall()
        self.assertEqual([tuple(r) for r in rows], [])
        conn.close()

    def test_tire_family_status_is_reflagged_and_retagged(self):
        conn = self._conn()
        for family in (_DISCONTINUED_TIRE_FAMILY, _NOT_FOUND_TIRE_FAMILY):
            tag = _tire_status_tag(family)
            for tid in family["tire_ids"]:
                if tid not in _A5_SAMPLE_IDS:
                    continue
                with self.subTest(tire=tid):
                    row = conn.execute(
                        "SELECT available_india, data_source FROM tire_models "
                        "WHERE id = ?",
                        (tid,),
                    ).fetchone()
                    self.assertEqual(row["available_india"], 0)
                    self.assertIn(tag, row["data_source"] or "")
                    # exactly one tag, not a duplicate appended on re-run
                    self.assertEqual((row["data_source"] or "").count(tag), 1)
        conn.close()

    def test_tire_prices_are_reapplied_from_the_scraped_values(self):
        conn = self._conn()
        for tid, expected in _A6_SAMPLE.items():
            with self.subTest(tire=tid):
                row = conn.execute(
                    "SELECT price_inr FROM tire_models WHERE id = ?", (tid,)
                ).fetchone()
                self.assertEqual(row["price_inr"], expected)
        conn.close()

    # ── (c) idempotency ─────────────────────────────────────────────────
    def test_second_run_is_fully_idempotent(self):
        self.assertNotIn("error", self.second_summary)
        self.assertEqual(self.second_summary["total_changed"], 0)
        for action in patch_mod._ACTION_ORDER:
            with self.subTest(action=action):
                self.assertEqual(
                    self.second_summary[action]["changed"],
                    0,
                    f"action {action!r} was not idempotent on the second run",
                )

    def test_no_foreign_key_violations(self):
        self.assertNotIn("foreign_key_violations", self.first_summary)
        self.assertNotIn("foreign_key_violations", self.second_summary)


class TestScrapeDataPatchGuards(unittest.TestCase):
    """Negative controls: the patch's two documented 'decline to act' branches.

    Uses its own DB copy so the deliberately-corrupted rows cannot leak into
    the mutation tests above.
    """

    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise unittest.SkipTest(f"{DB_PATH} not present")
        cls.db_path = _copy_shipped_db()
        cls.guarded = _A4_SAMPLE[0]
        cls.unexpected_brand = "Some Third-Party Rebrand"
        cls.unexpected_name = "Renamed By Someone Else"
        cls.conflict_tire_id = 195  # Apollo Alpha H1 — two disagreeing prices
        cls.conflict_sentinel = 12345.0

        conn = _rw_conn(cls.db_path)
        conn.execute(
            "UPDATE parts SET brand = ?, model_name = ? WHERE id = ?",
            (cls.unexpected_brand, cls.unexpected_name, cls.guarded["id"]),
        )
        conn.execute(
            "UPDATE tire_models SET price_inr = ? WHERE id = ?",
            (cls.conflict_sentinel, cls.conflict_tire_id),
        )
        conn.commit()
        conn.close()

        cls.summary = patch_mod.main(db_path=cls.db_path)

    @classmethod
    def tearDownClass(cls):
        Path(cls.db_path).unlink(missing_ok=True)

    def test_unexpected_brand_is_reported_and_left_alone(self):
        """A row whose brand/name matches neither the fictional original nor
        the honest replacement must be reported, not silently overwritten —
        someone else edited it and the patch has no mandate."""
        s = self.summary["fictional_brand_renames"]
        self.assertEqual(s["changed"], 0)
        self.assertEqual(len(s["problems"]), 1)
        self.assertIn(str(self.guarded["id"]), s["problems"][0])

        conn = _rw_conn(self.db_path)
        row = conn.execute(
            "SELECT brand, model_name FROM parts WHERE id = ?", (self.guarded["id"],)
        ).fetchone()
        conn.close()
        self.assertEqual(row["brand"], self.unexpected_brand)
        self.assertEqual(row["model_name"], self.unexpected_name)

    def test_conflicting_tire_price_points_are_not_arbitrated(self):
        """Two retailers quoting different prices for one tire is ambiguity the
        patch must decline to resolve — it may not pick one, and it may not
        clobber whatever is already recorded."""
        s = self.summary["tire_prices"]
        self.assertEqual(s["conflict_skipped"], 7)
        self.assertEqual(s["no_unique_row_match_skipped"], 20)
        self.assertEqual(len(s["problems"]), s["conflict_skipped"])

        conn = _rw_conn(self.db_path)
        row = conn.execute(
            "SELECT price_inr FROM tire_models WHERE id = ?", (self.conflict_tire_id,)
        ).fetchone()
        conn.close()
        self.assertEqual(row["price_inr"], self.conflict_sentinel)

    def test_excluded_usd_ids_are_never_repriced(self):
        """The 7 hard-excluded ids (proxy prices on found=false SKUs, or no
        source_url) must be untouched relative to the pristine catalogue."""
        pristine = _ro_conn(DB_PATH)
        patched = _rw_conn(self.db_path)
        for pid in sorted(patch_mod.EXCLUDE_USD_REPRICE_IDS):
            with self.subTest(part=pid):
                before = pristine.execute(
                    "SELECT price_inr, last_price_check FROM parts WHERE id = ?",
                    (pid,),
                ).fetchone()
                after = patched.execute(
                    "SELECT price_inr, last_price_check FROM parts WHERE id = ?",
                    (pid,),
                ).fetchone()
                self.assertEqual(after["price_inr"], before["price_inr"])
                self.assertEqual(after["last_price_check"], before["last_price_check"])
                self.assertNotEqual(after["last_price_check"], patch_mod.PATCH_DATE)
        pristine.close()
        patched.close()

    def test_current_tire_family_is_left_available(self):
        """Action 5 only touches discontinued / not_found families; a 'current'
        one keeps available_india = 1."""
        conn = _rw_conn(self.db_path)
        row = conn.execute(
            "SELECT available_india FROM tire_models WHERE id = 195"
        ).fetchone()
        conn.close()
        self.assertEqual(row["available_india"], 1)


if __name__ == "__main__":
    unittest.main()
