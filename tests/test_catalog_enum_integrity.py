"""
Catalog enum integrity (2026-07-25 audit).

KNOWN_TRAPS T16: an enum-ish string field either validates at construction or
silently takes a wrong branch. The 2026-07-13 hardening did the right thing and
made ``ForcedInductionModel`` raise on an unknown ``boost_type`` — but the
catalog data was never migrated to match, so part 340 ("TTS Supercharger BMW
S1000RR", INR 450,000) kept shipping ``boost_type: "supercharger"``, a value
that is not in ``VALID_BOOST_TYPES``.

The result was a live production failure: every simulation including that part
returned HTTP 422, and the part was silently dropped from every ROI/optimizer
result. Verified against the shipped DB before the fix:

    part 340 -> HTTP 422 "sets invalid boost_type 'supercharger'"
    part 138 -> HTTP 200  (a valid sibling)

Hardening one side of a contract without migrating the data is the failure
mode; this test closes it by asserting the catalog satisfies the enum the
engine now enforces. It scans the real shipped DB, so it fails on any future
part that reintroduces the class.
"""

from __future__ import annotations

import json
import os
import sqlite3
import unittest

_DB = os.environ.get("MOTOQUANT_CATALOG_DB", "motoquant.db")


def _catalog_rows():
    if not os.path.exists(_DB):
        return None
    conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    try:
        return conn.execute(
            "SELECT id, brand, model_name, param_overrides, param_deltas "
            "FROM parts WHERE param_overrides IS NOT NULL OR param_deltas IS NOT NULL"
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        conn.close()


class TestBoostTypeEnum(unittest.TestCase):
    def setUp(self):
        self.rows = _catalog_rows()
        if self.rows is None:
            self.skipTest("no seeded catalog available")

    def test_every_part_declares_a_valid_boost_type(self):
        from motoquant.submodels.forced_induction import VALID_BOOST_TYPES

        offenders = []
        for pid, brand, name, overrides, deltas in self.rows:
            for blob in (overrides, deltas):
                if not blob:
                    continue
                try:
                    parsed = json.loads(blob)
                except (TypeError, ValueError):
                    continue
                bt = parsed.get("forced_induction.boost_type")
                if bt is not None and bt not in VALID_BOOST_TYPES:
                    offenders.append(
                        f"part {pid} ({brand} {name}): boost_type={bt!r} "
                        f"not in {sorted(VALID_BOOST_TYPES)}"
                    )
        self.assertEqual(
            offenders,
            [],
            "Catalog part(s) declare a boost_type the engine rejects at "
            "construction, so every simulation including them 422s:\n  "
            + "\n  ".join(offenders),
        )

    def test_no_new_boosted_parts_ship_without_a_boost_target(self):
        """A boosted part with no target pressure gets the boosted-DA floor
        with zero modelled boost.

        These seven are a KNOWN, PRE-EXISTING gap recorded by the 2026-07-25
        audit, not a regression. They are not inert — each carries a
        substantial crank-power delta (+55 to +180 hp), so the part still
        moves ET; what is missing is the boost *dynamics* (spool, the
        density-altitude interaction). Closing it properly needs each kit's
        real published boost pressure, and the honest-data contract forbids
        inventing those numbers, so they are recorded rather than guessed.

        This test therefore guards against GROWTH: a new boosted SKU must
        ship a target, and any of these seven that gains one should be
        removed from the list.
        """
        from motoquant.submodels.forced_induction import VALID_BOOST_TYPES

        known_gap = {336, 337, 338, 339, 341, 581, 582}
        missing, closed = [], []
        for pid, brand, name, overrides, _deltas in self.rows:
            if not overrides:
                continue
            try:
                parsed = json.loads(overrides)
            except (TypeError, ValueError):
                continue
            bt = parsed.get("forced_induction.boost_type")
            # n2o meters via n2o_hp_per_stage, not a manifold pressure target.
            if bt in (None, "na", "n2o") or bt not in VALID_BOOST_TYPES:
                continue
            has_target = bool(parsed.get("forced_induction.target_boost_bar"))
            if not has_target and pid not in known_gap:
                missing.append(f"part {pid} ({brand} {name}): {bt} with no target")
            elif has_target and pid in known_gap:
                closed.append(pid)

        self.assertEqual(
            missing,
            [],
            "NEW boosted part(s) ship without a target pressure — add the "
            "kit's real published boost, do not guess:\n  " + "\n  ".join(missing),
        )
        self.assertEqual(
            closed,
            [],
            f"Part(s) {closed} now declare a boost target — remove them from "
            "known_gap so the list stays honest.",
        )


if __name__ == "__main__":
    unittest.main()
