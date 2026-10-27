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

    def test_every_boosted_part_declares_its_boost(self):
        """A boosted part with no boost amount delivers no boost.

        A turbo/supercharger with ``target_boost_bar`` 0 (or a nitrous kit
        whose ``n2o_hp_per_stage * n2o_stages`` is 0) builds zero
        forced-induction power: all it gets is the boosted density-altitude
        floor. The 2026-07-25 audit recorded seven such turbo kits
        (336-339, 341, 581, 582) as a known gap; the October 2026 core audit
        found three nitrous kits (100, 141, 142) with no ``n2o_stages`` too.

        Both are closed by ``scripts/patch_2026_10_24_parts_data.py`` (and the
        seed sources): each turbo kit's ``target_boost_bar`` is its own
        catalogued ``specifications.boost_psi`` (psi x 0.0689476, no invented
        figures), each nitrous kit runs one stage of its rated shot, and the
        kits' old ``engine.peak_power_hp`` deltas (which the bridge never
        applied to a boosted part) are gone. There is no allowlist any more:
        every boosted SKU must declare its boost.
        """
        from motoquant.submodels.forced_induction import VALID_BOOST_TYPES

        pressure_types = VALID_BOOST_TYPES - {"na", "n2o"}
        offenders = []
        for pid, brand, name, overrides, _deltas in self.rows:
            if not overrides:
                continue
            try:
                parsed = json.loads(overrides)
            except (TypeError, ValueError):
                continue
            bt = parsed.get("forced_induction.boost_type")
            if bt in pressure_types:
                bar = parsed.get("forced_induction.target_boost_bar") or 0.0
                if not bar > 0:
                    offenders.append(
                        f"part {pid} ({brand} {name}): {bt} with target_boost_bar={bar}"
                    )
            elif bt == "n2o":
                shot = parsed.get("forced_induction.n2o_hp_per_stage") or 0.0
                stages = parsed.get("forced_induction.n2o_stages") or 0
                if not shot * stages > 0:
                    offenders.append(
                        f"part {pid} ({brand} {name}): n2o with "
                        f"n2o_hp_per_stage={shot} x n2o_stages={stages}"
                    )

        self.assertEqual(
            offenders,
            [],
            "Boosted part(s) declare no boost amount, so they deliver zero "
            "forced-induction power — add the kit's real published boost / "
            "shot, do not guess:\n  " + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
