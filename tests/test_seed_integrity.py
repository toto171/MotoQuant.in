"""
MotoQuant Pro — Seed Integrity Tests (fold-back regression guard)
=================================================================
The DB pipeline used to be "seed_all() -> then run patch scripts". The manual
patch scripts (patch_2026_04_30_fitment_normalize / patch_2026_06_11_parts_fitment
/ patch_2026_07_03_sprocket_position) fixed real compatibility bugs that the seed
SOURCES still carried — so a *fresh* seed silently resurrected them.

As of 2026-07-04 those patch corrections are folded back into the seed sources
(motoquant/database/seed.py + seed_catalogs/*.py). This module is the regression
guard proving that a fresh ``seed_all()`` stays clean WITHOUT any patch scripts
being run afterwards:

  (a) no fitment_rules carry the invalid ``supersport`` / ``commuter`` category
      tokens, no rule uses the invalid ``tier: "model"``, and no rule leaves
      constraints "flat" (un-nested, i.e. outside the ``match`` block);
  (b) no cross-brand exhaust leaks (the same invariants as
      tests/test_catalog_integration.py — RE 350 vs RE 650/Harley, Hayabusa vs
      Panigale/RSV4, Panigale V4 vs RSV4);
  (c) coverage sanity — every seeded bike still has at least one exhaust and the
      catalog is at least its current size.

Runs against an in-memory SQLite DB so it never touches the production
``motoquant.db`` file. If any of these fail, a patch fix has regressed out of
the seed sources and a fresh seed would ship the old bug.
"""

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.database.parts_repo import _enrich_bike_row_for_fitment
from motoquant.database.seed import seed_all
from motoquant.parts.compatibility import is_compatible
from motoquant.scraper.importer import import_batch
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# Invalid category tokens the June-11 F-pass normalises away. These are NOT
# bike_models.category values (valid: adventure/cruiser/muscle/naked/scooter/
# sport/sport_touring/touring), so a rule carrying them either matches nothing
# (solo) or carries a dead token.
INVALID_CATEGORY_TOKENS = {"supersport", "commuter"}

# Constraint keys that MUST live nested under fitment_rules["match"], never at
# the top level (the flat-schema bug patch_2026_04_30 normalised).
NESTED_CONSTRAINT_KEYS = {
    "manufacturers",
    "engine_configs",
    "displacement_min_cc",
    "displacement_max_cc",
    "categories",
    "year_min",
    "year_max",
    "chain_pitch",
    "stroke_type",
}

# Floor for the catalog size — the current fresh-seed part count. Additions are
# fine (the floor still holds); a drop means parts silently vanished.
# 594 -> 593 on 2026-07-06: the duplicate Walbro 450 LPH Fuel Pump row
# (seed.py + drag_specific.py both seeded one) was merged into a single part.
MIN_CATALOG_PARTS = 593


@pytest.fixture(scope="module")
def seeded_db():
    """Full catalog seeded from sources ONLY — no patch scripts run."""
    db = MotoQuantDB(":memory:")
    db.connect()
    db.initialize()
    seed_all(db)
    import_batch(db, ALL_KNOWN_BIKES)
    yield db
    db.close()


def _all_parts(db):
    return [
        dict(r)
        for r in db._conn.execute(
            """SELECT p.*, pc.name AS category FROM parts p
               JOIN parts_categories pc ON pc.id = p.category_id"""
        ).fetchall()
    ]


def _all_rules(db):
    """Yield (part_dict, parsed_fitment_rules) for every part with rules."""
    import json

    for p in _all_parts(db):
        raw = p.get("fitment_rules")
        if not raw:
            continue
        yield p, json.loads(raw)


def _get_bike(db, name_like, manufacturer=None):
    q = """SELECT bm.*, m.name AS manufacturer
           FROM bike_models bm JOIN manufacturers m ON m.id=bm.manufacturer_id
           WHERE bm.model_name LIKE ?"""
    params = [f"%{name_like}%"]
    if manufacturer:
        q += " AND m.name=?"
        params.append(manufacturer)
    q += " LIMIT 1"
    row = db._conn.execute(q, params).fetchone()
    if row is None:
        return None
    d = dict(row)
    _enrich_bike_row_for_fitment(db._conn, d)
    return d


def _exhausts(db):
    return [p for p in _all_parts(db) if p["category"] == "exhaust"]


# ═══════════════════════════════════════════════════════════════
# (a) Fold-integrity — the patch normalisations must hold on a fresh seed
# ═══════════════════════════════════════════════════════════════


class TestNoInvalidCategoryTokens:
    def test_no_supersport_or_commuter(self, seeded_db):
        """No fitment rule may carry 'supersport' or 'commuter' categories
        (patch_2026_06_11 F, folded into the seed sources)."""
        offenders = []
        for p, rules in _all_rules(seeded_db):
            cats = (rules.get("match") or {}).get("categories") or []
            bad = INVALID_CATEGORY_TOKENS.intersection(cats)
            if bad:
                offenders.append((p["id"], p["brand"], p["model_name"], sorted(bad)))
        assert not offenders, (
            f"{len(offenders)} parts still carry invalid category tokens: "
            f"{offenders[:5]}"
        )


class TestNoInvalidTier:
    def test_no_tier_model(self, seeded_db):
        """No rule may use the invalid tier 'model' (patch_2026_04_30 → 'family')."""
        offenders = [
            (p["id"], p["model_name"])
            for p, rules in _all_rules(seeded_db)
            if rules.get("tier") == "model"
        ]
        assert not offenders, f"parts with tier=='model': {offenders[:5]}"

    def test_all_tiers_valid(self, seeded_db):
        """Every tier must be one of the four valid FitmentTier values."""
        valid = {"exact", "family", "category", "universal"}
        offenders = [
            (p["id"], p["model_name"], rules.get("tier"))
            for p, rules in _all_rules(seeded_db)
            if rules.get("tier") not in valid
        ]
        assert not offenders, f"parts with invalid tier: {offenders[:5]}"


class TestNoFlatConstraints:
    def test_constraints_are_nested_under_match(self, seeded_db):
        """Constraint keys must be nested under 'match', never flat at the top
        level (patch_2026_04_30 normalised the flat-schema bug)."""
        offenders = []
        for p, rules in _all_rules(seeded_db):
            flat = NESTED_CONSTRAINT_KEYS.intersection(rules.keys())
            if flat:
                offenders.append((p["id"], p["model_name"], sorted(flat)))
        assert not offenders, (
            f"{len(offenders)} parts have flat (un-nested) constraints: {offenders[:5]}"
        )

    def test_no_model_keywords(self, seeded_db):
        """The unsupported 'model_keywords' / 'model_name' constraint keys must
        not survive (patch_2026_04_30 dropped them; patch_2026_06_11 K removed a
        dead 'model_name' key)."""
        offenders = []
        for p, rules in _all_rules(seeded_db):
            match = rules.get("match") or {}
            dead = {"model_keywords", "model_name"}.intersection(match.keys())
            dead |= {"model_keywords"}.intersection(rules.keys())
            if dead:
                offenders.append((p["id"], p["model_name"], sorted(dead)))
        assert not offenders, f"parts with dead constraint keys: {offenders[:5]}"


class TestSprocketPositionStamped:
    def test_every_sprocket_has_position(self, seeded_db):
        """Every sprocket must carry specifications.position (patch_2026_07_03)
        so the build-optimizer position-exclusivity knapsack groups it."""
        import json

        offenders = []
        for p in _all_parts(seeded_db):
            if p["category"] != "sprocket":
                continue
            specs = json.loads(p.get("specifications") or "{}")
            if specs.get("position") not in ("front", "rear"):
                offenders.append((p["id"], p["model_name"], specs.get("position")))
        assert not offenders, (
            f"{len(offenders)} sprockets missing specifications.position: "
            f"{offenders[:5]}"
        )


# ═══════════════════════════════════════════════════════════════
# (b) No cross-brand leaks — same invariants as test_catalog_integration,
#     verified on a fresh seed with NO patch scripts run
# ═══════════════════════════════════════════════════════════════


class TestFreshSeedNoLeaks:
    def test_re_classic_350_no_harley_or_650_leak(self, seeded_db):
        re350 = _get_bike(seeded_db, "Classic 350")
        assert re350 is not None, "RE Classic 350 must be seeded"
        for part in _exhausts(seeded_db):
            if is_compatible(part, re350)[0]:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "harley" not in blob, f"RE 350 leaked to Harley: {blob}"
                assert "x440" not in blob, f"RE 350 leaked to X440: {blob}"
                assert "re 650" not in blob and "arrow re 650" not in blob, (
                    f"RE 350 leaked to RE 650 part: {blob}"
                )
                assert "panigale" not in blob, f"RE 350 leaked to Panigale: {blob}"
                assert "hayabusa" not in blob, f"RE 350 leaked to Hayabusa: {blob}"

    def test_hayabusa_no_panigale_rsv4_leak(self, seeded_db):
        haya = _get_bike(seeded_db, "Hayabusa")
        assert haya is not None
        for part in _exhausts(seeded_db):
            if is_compatible(part, haya)[0]:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "panigale" not in blob, f"Hayabusa leaked to Panigale: {blob}"
                assert "rsv4" not in blob, f"Hayabusa leaked to RSV4: {blob}"

    def test_panigale_v4_no_rsv4_leak(self, seeded_db):
        pani = _get_bike(seeded_db, "Panigale V4", manufacturer="Ducati")
        assert pani is not None
        for part in _exhausts(seeded_db):
            if is_compatible(part, pani)[0]:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "rsv4" not in blob, f"Panigale V4 leaked to RSV4: {blob}"

    def test_rsv4_no_panigale_leak(self, seeded_db):
        rsv4 = _get_bike(seeded_db, "RSV4")
        if rsv4 is None:
            pytest.skip("No RSV4 seeded")
        for part in _exhausts(seeded_db):
            if is_compatible(part, rsv4)[0]:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "panigale" not in blob, f"RSV4 leaked to Panigale: {blob}"
                assert "termignoni" not in blob, (
                    f"RSV4 leaked to Ducati-specific Termignoni: {blob}"
                )


# ═══════════════════════════════════════════════════════════════
# (c) Coverage sanity — a fresh seed must not shrink coverage
# ═══════════════════════════════════════════════════════════════


class TestFreshSeedCoverage:
    def test_catalog_at_least_current_size(self, seeded_db):
        n = seeded_db._conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        assert n >= MIN_CATALOG_PARTS, (
            f"catalog shrank: {n} parts (< floor {MIN_CATALOG_PARTS})"
        )

    def test_every_bike_has_exhaust(self, seeded_db):
        exhausts = _exhausts(seeded_db)
        bikes = seeded_db._conn.execute(
            """SELECT bm.*, m.name AS manufacturer
               FROM bike_models bm JOIN manufacturers m ON m.id=bm.manufacturer_id"""
        ).fetchall()
        missing = []
        for b in bikes:
            d = dict(b)
            _enrich_bike_row_for_fitment(seeded_db._conn, d)
            if not any(is_compatible(p, d)[0] for p in exhausts):
                missing.append(f"{d['manufacturer']} {d['model_name']}")
        assert not missing, (
            f"{len(missing)} bikes have zero exhaust options: {missing[:5]}"
        )
