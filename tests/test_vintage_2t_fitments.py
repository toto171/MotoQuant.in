"""
Tests for scripts/seed_vintage_2t_fitments.py (roadmap A3-17).

The 3 vintage two-stroke bikes below shipped with ZERO tire fitments in the
catalog (the July-3 query-driven planner closed every other 2T bike). This
verifies the standalone seed script gives each of them period-correct OEM
front + rear fitments, is idempotent, and produces validator-acceptable sizes.

Runs against a temp COPY of the checked-in motoquant.db (the vintage bikes live
in the catalog DB, not in seed_all()'s reference set). Skips if the DB is absent.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from motoquant.database.connection import MotoQuantDB
from motoquant.scraper.validator import TIRE_SIZE_RE
from scripts.seed_vintage_2t_fitments import (
    TIRES,
    _resolve_bikes,
    seed_vintage_2t_fitments,
)

DB_PATH = Path(__file__).resolve().parent.parent / "motoquant.db"

# (manufacturer, model-name LIKE pattern) for the three target bikes.
TARGETS = [
    ("Suzuki", "GT750%"),
    ("Kawasaki", "%H2 Mach IV%"),
    ("Yezdi", "250 Classic%"),
]

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="production motoquant.db not present in this checkout",
)


def _fresh_copy() -> str:
    path = tempfile.mktemp(suffix=".db")
    shutil.copy(DB_PATH, path)
    return path


def _oem_fitments(conn, bike_id: int) -> list:
    return conn.execute(
        "SELECT btf.position, btf.is_default, tm.size_designation, tm.construction "
        "FROM bike_tire_fitments btf JOIN tire_models tm ON btf.tire_model_id = tm.id "
        "WHERE btf.bike_model_id = ? AND btf.fitment_type = 'oem' "
        "ORDER BY btf.position",
        (bike_id,),
    ).fetchall()


def _reset_targets(conn) -> None:
    """Restore the pre-seed 'before = 0 fitments' state on a temp copy.

    The production motoquant.db now ships WITH the vintage-2T fitments applied
    (this script ran during its heavy-tail reseed), so the 0->2 and idempotency
    assertions must first strip the target bikes' fitments + the script's own
    OE bias-ply tires. This keeps the test valid whether or not the checked-in
    DB already carries the rows.
    """
    for mfr, pattern in TARGETS:
        for bike_id, _name in _resolve_bikes(conn, mfr, pattern):
            conn.execute(
                "DELETE FROM bike_tire_fitments WHERE bike_model_id = ?", (bike_id,)
            )
    # Remove the three OE bias-ply tires this script seeds (its own naming),
    # so a fresh run re-creates exactly +3 tires / +6 fitments.
    conn.execute("DELETE FROM tire_models WHERE model_name LIKE 'OE Bias-Ply%'")
    conn.commit()


@pytest.fixture(scope="module")
def seeded_db():
    """Temp copy of the catalog DB with the vintage-2T seed applied once."""
    path = _fresh_copy()
    db = MotoQuantDB(path)
    stats = seed_vintage_2t_fitments(db)
    yield db, stats
    db.close()
    if os.path.exists(path):
        os.remove(path)


def test_targets_resolve_and_get_front_and_rear_oem(seeded_db):
    """Each target bike now has exactly one OEM front + one OEM rear fitment."""
    db, _ = seeded_db
    conn = db.connect()
    for mfr, pattern in TARGETS:
        matches = _resolve_bikes(conn, mfr, pattern)
        assert matches, f"no bike matched {mfr} {pattern!r}"
        for bike_id, name in matches:
            positions = [r[0] for r in _oem_fitments(conn, bike_id)]
            assert "front" in positions, f"{name} (id {bike_id}) has no OEM front tyre"
            assert "rear" in positions, f"{name} (id {bike_id}) has no OEM rear tyre"


def test_oem_fitments_are_default(seeded_db):
    """Invariant (test_tire_fitments): every OEM fitment is is_default=1."""
    db, _ = seeded_db
    conn = db.connect()
    for mfr, pattern in TARGETS:
        for bike_id, name in _resolve_bikes(conn, mfr, pattern):
            for pos, is_default, size, constr in _oem_fitments(conn, bike_id):
                assert is_default == 1, f"{name} {pos} OEM fitment is not is_default=1"
                assert constr == "bias", f"{name} {pos} tyre not marked bias-ply"


def test_seeded_sizes_pass_validator(seeded_db):
    """Every seeded size_designation is accepted by the spec tire-size validator."""
    db, _ = seeded_db
    conn = db.connect()
    seen = set()
    for mfr, pattern in TARGETS:
        for bike_id, _name in _resolve_bikes(conn, mfr, pattern):
            for _pos, _d, size, _c in _oem_fitments(conn, bike_id):
                seen.add(size)
                assert TIRE_SIZE_RE.match(size), f"validator rejects size {size!r}"
    # Sanity: the three expected metric-dash sizes are present.
    assert {"90/90-19", "110/90-18", "90/90-16"} <= seen


def test_previously_zero_then_front_plus_rear():
    """Before: 0 fitments. After one run: front + rear (2) per target bike."""
    path = _fresh_copy()
    try:
        db = MotoQuantDB(path)
        conn = db.connect()
        _reset_targets(conn)
        for mfr, pattern in TARGETS:
            for bike_id, name in _resolve_bikes(conn, mfr, pattern):
                n = conn.execute(
                    "SELECT COUNT(*) FROM bike_tire_fitments WHERE bike_model_id = ?",
                    (bike_id,),
                ).fetchone()[0]
                assert n == 0, f"{name} was expected to start with 0 fitments, had {n}"
        seed_vintage_2t_fitments(db)
        for mfr, pattern in TARGETS:
            for bike_id, name in _resolve_bikes(conn, mfr, pattern):
                n = conn.execute(
                    "SELECT COUNT(*) FROM bike_tire_fitments WHERE bike_model_id = ?",
                    (bike_id,),
                ).fetchone()[0]
                assert n == 2, f"{name} expected 2 fitments after seed, had {n}"
        db.close()
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_idempotent_no_duplicate_rows():
    """Running the seed twice adds nothing on the second pass."""
    path = _fresh_copy()
    try:
        db = MotoQuantDB(path)
        conn = db.connect()
        _reset_targets(conn)

        def counts():
            t = conn.execute("SELECT COUNT(*) FROM tire_models").fetchone()[0]
            f = conn.execute("SELECT COUNT(*) FROM bike_tire_fitments").fetchone()[0]
            return t, f

        base = counts()
        s1 = seed_vintage_2t_fitments(db)
        after1 = counts()
        s2 = seed_vintage_2t_fitments(db)
        after2 = counts()

        assert s1["fitments_inserted"] == 6
        assert after1 == (base[0] + 3, base[1] + 6)  # +3 tires, +6 fitments
        assert s2["fitments_inserted"] == 0
        assert s2["fitments_existing"] == 6
        assert after2 == after1  # second run is a pure no-op
        db.close()
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_tire_template_sizes_are_the_three_expected():
    """Guard the metric-dash equivalents used by the script."""
    assert TIRES["front_19"]["size"] == "90/90-19"
    assert TIRES["rear_18"]["size"] == "110/90-18"
    assert TIRES["both_16"]["size"] == "90/90-16"
    # Period bias-ply grip stays in the honest 0.95-1.05 band via mu_peak=1.00.
    assert TIRES["both_16"]["vintage"] == "3.25-16"
