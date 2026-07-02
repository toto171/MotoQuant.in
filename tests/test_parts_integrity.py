"""Parts-catalog data-integrity guards (2026-07-02 audit).

These run against the live motoquant.db and pin invariants that silent
data bugs violate:

1. Sprockets REPLACE the stock part, so front/rear_sprocket must be set via
   param_overrides (absolute), never param_deltas (additive). Five parts in
   indian_retailer_depth.py used deltas, so applying a "16T front" to a
   stock-17 bike produced 33 teeth — corrupting every ROI/optimizer gearing
   number for those parts.
2. No part may reference a param path that does not exist on BikeConfig
   (the bridge canary): a typo'd path silently no-ops.
"""

import json
import sqlite3
from pathlib import Path

import pytest

# Resolve the REAL production catalog explicitly (not $MOTOQUANT_DB): these
# tests validate the shipped motoquant.db, and other test modules
# (test_api.py) transiently repoint MOTOQUANT_DB at a tmp DB during the same
# pytest session.
_REPO_DB = Path(__file__).resolve().parent.parent / "motoquant.db"


@pytest.fixture(scope="module")
def conn():
    if not _REPO_DB.exists():
        pytest.skip(f"{_REPO_DB} not present")
    c = sqlite3.connect(f"file:{_REPO_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def _all_parts(conn):
    return conn.execute(
        "SELECT id, brand, model_name, param_overrides, param_deltas FROM parts"
    ).fetchall()


class TestSprocketsUseOverrides:
    def test_no_sprocket_teeth_in_param_deltas(self, conn):
        offenders = []
        for r in _all_parts(conn):
            pd = json.loads(r["param_deltas"]) if r["param_deltas"] else {}
            for k in pd:
                if "front_sprocket" in k or "rear_sprocket" in k:
                    offenders.append(f"{r['id']} {r['brand']} {r['model_name']}")
        assert not offenders, (
            "sprocket teeth must be absolute (param_overrides), never additive "
            "(param_deltas) — offenders: " + ", ".join(offenders)
        )

    def test_sprocket_override_applies_absolutely(self, conn):
        # applying a 16T front sprocket to the K5 (stock 17) must yield 16
        import warnings

        warnings.filterwarnings("ignore")
        from motoquant.database import bridge
        from motoquant.defaults import gsxr1000_k5

        row = conn.execute(
            "SELECT * FROM parts WHERE param_overrides LIKE '%front_sprocket%' LIMIT 1"
        ).fetchone()
        if not row:
            pytest.skip("no front-sprocket part in catalog")
        part = dict(row)
        want = json.loads(part["param_overrides"])["drivetrain.front_sprocket"]
        cfg = bridge.apply_part_to_config(gsxr1000_k5(), part)
        assert cfg.drivetrain.front_sprocket == want


class TestNoDeadParamPaths:
    def test_every_param_path_exists_on_config(self, conn):
        """apply_part_to_config warns on unknown paths; assert none warn."""
        import warnings

        from motoquant.database import bridge
        from motoquant.defaults import gsxr1000_k5

        base = gsxr1000_k5()
        dead = []
        for r in _all_parts(conn):
            part = dict(r)
            if not (part.get("param_overrides") or part.get("param_deltas")):
                continue
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                try:
                    bridge.apply_part_to_config(base, part)
                except Exception:
                    continue
                for warning in w:
                    msg = str(warning.message).lower()
                    if "path" in msg or "invalid" in msg or "unknown" in msg:
                        dead.append(f"{r['id']} {r['brand']}: {warning.message}")
        assert not dead, (
            "parts with invalid param paths (silent no-ops):\n" + "\n".join(dead[:20])
        )
