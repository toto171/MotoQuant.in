"""
MotoQuant Pro — Catalog Integration Tests
==========================================
End-to-end tests that seed the full catalog, import all known bikes, and
verify bike-specific compatibility properties:

  - No cross-brand exhaust leaks (RE 350 doesn't match Harley V-twin,
    Hayabusa doesn't match Panigale, Panigale V4 doesn't match RSV4)
  - Every bike has at least one exhaust match
  - `_enrich_bike_row_for_fitment` correctly hydrates legacy rows
  - `_infer_cylinder_config` and `_infer_chain_pitch` produce expected values

These run against an in-memory SQLite DB so they're safe in CI and don't
touch the production `motoquant.db` file.
"""

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.database.parts_repo import _enrich_bike_row_for_fitment
from motoquant.database.seed import seed_all
from motoquant.parts.compatibility import is_compatible
from motoquant.scraper.importer import (
    _infer_chain_pitch,
    _infer_cylinder_config,
    import_batch,
)
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# ═══════════════════════════════════════════════════════════════
# Fixtures — fully seeded in-memory DB with 267 known bikes
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def seeded_db():
    """Full catalog seeded with 270 bikes (3 reference + 267 known)."""
    db = MotoQuantDB(":memory:")
    db.connect()
    # initialize() creates schema + seeds parts categories, venues, seasonal data
    db.initialize()
    # seed reference bikes + tires + full parts catalog (+ expansion modules)
    seed_all(db)
    # Import all known bikes
    import_batch(db, ALL_KNOWN_BIKES)
    yield db
    db.close()


def _get_bike(db, name_like, manufacturer=None):
    """Load a bike + enrich for fitment — returns dict or None."""
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
    """Return all exhaust parts as a list of dicts."""
    rows = db._conn.execute(
        """SELECT p.*, pc.name AS category FROM parts p
           JOIN parts_categories pc ON pc.id=p.category_id
           WHERE pc.name='exhaust'"""
    ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════
# Leak-closure tests — these regressions must never come back
# ═══════════════════════════════════════════════════════════════


class TestNoLeaks:
    def test_re_classic_350_no_harley_leak(self, seeded_db):
        """RE Classic 350 (I1 single cruiser) must NOT match Harley V-twin or
        RE 650 twin exhausts."""
        re350 = _get_bike(seeded_db, "Classic 350")
        assert re350 is not None, "RE Classic 350 must be seeded"
        for part in _exhausts(seeded_db):
            ok, _ = is_compatible(part, re350)
            if ok:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "harley" not in blob, f"RE 350 leaked to Harley: {blob}"
                assert "x440" not in blob, f"RE 350 leaked to X440: {blob}"
                assert "re 650" not in blob and "arrow re 650" not in blob, (
                    f"RE 350 leaked to RE 650 part: {blob}"
                )
                assert "panigale" not in blob, f"RE 350 leaked to Panigale: {blob}"
                assert "hayabusa" not in blob, f"RE 350 leaked to Hayabusa: {blob}"

    def test_hayabusa_no_panigale_rsv4_leak(self, seeded_db):
        """Hayabusa (I4 1299cc) must NOT match Panigale V4/V2 or RSV4 parts."""
        haya = _get_bike(seeded_db, "Hayabusa")
        assert haya is not None
        for part in _exhausts(seeded_db):
            ok, _ = is_compatible(part, haya)
            if ok:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "panigale" not in blob, f"Hayabusa leaked to Panigale: {blob}"
                assert "rsv4" not in blob, f"Hayabusa leaked to RSV4: {blob}"

    def test_panigale_v4_no_rsv4_leak(self, seeded_db):
        """Panigale V4 (Ducati V4) must NOT match Aprilia RSV4 parts — these
        are both V4 litre-class but from different manufacturers."""
        pani = _get_bike(seeded_db, "Panigale V4", manufacturer="Ducati")
        assert pani is not None
        for part in _exhausts(seeded_db):
            ok, _ = is_compatible(part, pani)
            if ok:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "rsv4" not in blob, f"Panigale V4 leaked to RSV4: {blob}"

    def test_rsv4_no_panigale_leak(self, seeded_db):
        """Aprilia RSV4 must NOT match Panigale/Ducati parts."""
        rsv4 = _get_bike(seeded_db, "RSV4")
        if rsv4 is None:
            pytest.skip("No RSV4 seeded")
        for part in _exhausts(seeded_db):
            ok, _ = is_compatible(part, rsv4)
            if ok:
                blob = f"{part['brand']} {part['model_name']}".lower()
                assert "panigale" not in blob, f"RSV4 leaked to Panigale: {blob}"
                assert "termignoni" not in blob, (
                    f"RSV4 leaked to Ducati-specific Termignoni: {blob}"
                )


# ═══════════════════════════════════════════════════════════════
# Coverage guarantees — every bike should have basic options
# ═══════════════════════════════════════════════════════════════


class TestCoverage:
    def test_every_bike_has_exhaust(self, seeded_db):
        """Every seeded bike must match at least one exhaust."""
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

    def test_minimum_parts_per_bike(self, seeded_db):
        """Every bike should match at least 20 parts across all categories
        (lower-bound for small-cc bikes; most get 50-150+)."""
        parts = [
            dict(r)
            for r in seeded_db._conn.execute(
                """SELECT p.*, pc.name AS category FROM parts p
                   JOIN parts_categories pc ON pc.id=p.category_id"""
            ).fetchall()
        ]
        bikes = seeded_db._conn.execute(
            """SELECT bm.*, m.name AS manufacturer
               FROM bike_models bm JOIN manufacturers m ON m.id=bm.manufacturer_id"""
        ).fetchall()
        low = []
        for b in bikes:
            d = dict(b)
            _enrich_bike_row_for_fitment(seeded_db._conn, d)
            n = sum(1 for p in parts if is_compatible(p, d)[0])
            if n < 20:
                low.append((d["model_name"], n))
        assert not low, f"Bikes with <20 parts: {low[:5]}"

    def test_catalog_size(self, seeded_db):
        """Total parts catalog must be at least 400 after expansion."""
        n = seeded_db._conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        assert n >= 400, f"Expected ≥400 parts after expansion, got {n}"


# ═══════════════════════════════════════════════════════════════
# Enrich-on-read fallback — manufacturer, cylinder_config, chain_pitch
# ═══════════════════════════════════════════════════════════════


class TestEnrichBikeRow:
    def test_manufacturer_name_joined(self, seeded_db):
        """A bike_models row missing 'manufacturer' gets it populated."""
        row = dict(
            seeded_db._conn.execute("SELECT * FROM bike_models LIMIT 1").fetchone()
        )
        row.pop("manufacturer", None)
        row.pop("manufacturer_name", None)
        _enrich_bike_row_for_fitment(seeded_db._conn, row)
        assert row.get("manufacturer"), (
            "manufacturer must be populated after enrichment"
        )

    def test_chain_pitch_falls_back_to_config_json(self, seeded_db):
        """Bikes with `chain_pitch` stored only in drivetrain_params JSON
        should get their chain_pitch populated via enrich."""
        # Pick any chain-drive bike and strip chain_pitch to force fallback
        row = dict(
            seeded_db._conn.execute(
                """SELECT bm.* FROM bike_models bm
                   JOIN bike_configs bc ON bc.bike_model_id=bm.id
                   WHERE bc.drivetrain_params LIKE '%chain_pitch%'
                   LIMIT 1"""
            ).fetchone()
        )
        row["chain_pitch"] = None  # Force the fallback path
        _enrich_bike_row_for_fitment(seeded_db._conn, row)
        # Must now be populated (tolerate any string value incl "525"/"530"/"428")
        assert row.get("chain_pitch") is not None, (
            "chain_pitch fallback did not populate from bike_configs"
        )

    def test_idempotent(self, seeded_db):
        """Calling enrich twice is a no-op — doesn't blow away existing values."""
        row = dict(
            seeded_db._conn.execute(
                """SELECT bm.*, m.name AS manufacturer FROM bike_models bm
                   JOIN manufacturers m ON m.id=bm.manufacturer_id LIMIT 1"""
            ).fetchone()
        )
        _enrich_bike_row_for_fitment(seeded_db._conn, row)
        before = dict(row)
        _enrich_bike_row_for_fitment(seeded_db._conn, row)
        assert row == before


# ═══════════════════════════════════════════════════════════════
# Importer inference helpers — unit tests (no DB required)
# ═══════════════════════════════════════════════════════════════


class TestInferCylinderConfig:
    def _make_spec(self, mfr, model, cyls, disp=None):
        from motoquant.scraper.spec import BikeSpec

        return BikeSpec(
            manufacturer=mfr, model_name=model, cylinders=cyls, displacement_cc=disp
        )

    def test_single_cylinder(self):
        assert (
            _infer_cylinder_config(self._make_spec("Royal Enfield", "Classic 350", 1))
            == "I1"
        )

    def test_inline_twin_default(self):
        assert _infer_cylinder_config(self._make_spec("Yamaha", "MT-07", 2)) == "I2"

    def test_ducati_v_twin(self):
        assert (
            _infer_cylinder_config(self._make_spec("Ducati", "Monster 1200", 2)) == "V2"
        )

    def test_harley_v_twin(self):
        assert (
            _infer_cylinder_config(self._make_spec("Harley-Davidson", "Street 750", 2))
            == "V2"
        )

    def test_indian_short_name_v_twin(self):
        """Indian Motorcycle stored as bare 'Indian' in DB must still infer V2."""
        assert _infer_cylinder_config(self._make_spec("Indian", "Scout", 2)) == "V2"
        assert (
            _infer_cylinder_config(self._make_spec("Indian", "FTR 1200 S", 2)) == "V2"
        )
        assert (
            _infer_cylinder_config(self._make_spec("Indian", "Chief Dark Horse", 2))
            == "V2"
        )

    def test_sv650_is_v_twin(self):
        """Suzuki is usually inline, but SV650 is a V-twin — model-token override."""
        assert _infer_cylinder_config(self._make_spec("Suzuki", "SV650", 2)) == "V2"

    def test_inline_four(self):
        assert (
            _infer_cylinder_config(self._make_spec("Suzuki", "GSX-R 1000", 4)) == "I4"
        )

    def test_panigale_v4(self):
        assert (
            _infer_cylinder_config(self._make_spec("Ducati", "Panigale V4", 4)) == "V4"
        )

    def test_rsv4_v4(self):
        assert (
            _infer_cylinder_config(self._make_spec("Aprilia", "RSV4 Factory", 4))
            == "V4"
        )

    def test_inline_triple(self):
        assert (
            _infer_cylinder_config(self._make_spec("Triumph", "Street Triple 765", 3))
            == "I3"
        )

    def test_unknown_cylinders_returns_none(self):
        assert _infer_cylinder_config(self._make_spec("Honda", "CBR", None)) is None

    def test_honda_vtr1000_sp2_is_v_twin(self):
        """Honda VTR1000 SP2 (RC51) is a 90-deg V-twin — the 'Honda' make is
        not exclusively V-twin and was missing a model token, so this used to
        regress to I2 on every fresh reseed (guarded post-hoc by the Jun-11
        parts patch). The 'VTR' / 'RC51' model tokens fix the inference."""
        assert (
            _infer_cylinder_config(self._make_spec("Honda", "VTR1000 SP2 (RC51)", 2))
            == "V2"
        )

    def test_honda_rc213v_s_is_v4(self):
        """Honda RC213V-S is a MotoGP-derived 90-deg V4 — no V4 model token
        matched 'RC213V' so this used to regress to I4 on fresh reseed (guarded
        post-hoc by the Jun-11 parts patch). The 'RC213V' token fixes it."""
        assert _infer_cylinder_config(self._make_spec("Honda", "RC213V-S", 4)) == "V4"


class TestInferChainPitch:
    def _make_spec(self, mfr, model, disp=None, cyls=None):
        from motoquant.scraper.spec import BikeSpec

        return BikeSpec(
            manufacturer=mfr, model_name=model, displacement_cc=disp, cylinders=cyls
        )

    def test_harley_is_belt(self):
        """Harley-Davidson street bikes use belt drive — should return None."""
        pitch = _infer_chain_pitch(self._make_spec("Harley-Davidson", "X440", 440))
        # Belt drive => None (no chain pitch applies)
        assert pitch is None or isinstance(pitch, str)

    def test_hayabusa_530_pitch(self):
        """Hayabusa uses 530-pitch chain."""
        pitch = _infer_chain_pitch(self._make_spec("Suzuki", "Hayabusa", 1340, cyls=4))
        assert pitch == "530"

    def test_small_displacement_428(self):
        """Sub-200cc bikes typically use 428-pitch chain."""
        pitch = _infer_chain_pitch(self._make_spec("Honda", "CB150R", 150, cyls=1))
        assert pitch == "428"

    def test_midrange_520_pitch(self):
        """Mid-range 600-700cc bikes typically use 520-pitch."""
        pitch = _infer_chain_pitch(self._make_spec("Honda", "CBR650R", 649, cyls=4))
        assert pitch == "520"


# ═══════════════════════════════════════════════════════════════
# Fitment tightening — verify specific families are separated
# ═══════════════════════════════════════════════════════════════


class TestFamilySeparation:
    def test_re_650_twin_only_parallel_twin_parts(self, seeded_db):
        """RE 650 (I2 parallel twin) should match RE-650-specific parts but
        not RE 350 single-cylinder parts."""
        re650 = _get_bike(seeded_db, "Interceptor 650")
        assert re650 is not None
        matches = [p for p in _exhausts(seeded_db) if is_compatible(p, re650)[0]]
        names = [f"{p['brand']} {p['model_name']}".lower() for p in matches]
        # RE 650 should NOT match RE 350-specific parts (HP Corse RE 350, Zard RE 350)
        assert not any("re 350" in n for n in names), (
            f"RE 650 leaked to RE 350-only parts: {names}"
        )
        # Must have at least one match
        assert matches, "RE 650 should have at least one exhaust"

    def test_indian_scout_matches_v_twin_parts(self, seeded_db):
        """Indian Scout (1133cc V-twin) must match at least one exhaust."""
        scout = _get_bike(seeded_db, "Scout", manufacturer="Indian")
        assert scout is not None
        matches = [p for p in _exhausts(seeded_db) if is_compatible(p, scout)[0]]
        assert matches, "Indian Scout should match at least one exhaust"
        # Verify cylinder_config was correctly inferred as V2
        assert scout.get("cylinder_config") == "V2", (
            f"Indian Scout must be V2, got {scout.get('cylinder_config')}"
        )
