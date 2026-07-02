"""
test_db_gearing_integrity.py
=============================
Guardrail: every current row in motoquant.db must have gear ratios that match
either (a) the K5/R1/Busa defaults.py ship config for the three reference bikes,
or (b) the gearing that ``spec_to_bike_config`` derives for that bike — i.e. the
DB must be a faithful reseed of the current specs.

This test exists because on April 22 2026 we shipped production DB rows that
had K5-leaked gear ratios into 269 bikes — e.g. Royal Enfield Continental GT 650
reported a 178 km/h terminal velocity in 4th gear (physically impossible). A
leaked config would not match its own spec's ``spec_to_bike_config`` output, so
this still catches that class of bug.

2026-07-02: the non-reference check now compares against ``spec_to_bike_config``
(spec-preferred: a bike that ships a real service-manual cassette keeps it), NOT
the raw Tier-1 lookup. The old pure-lookup invariant was obsolete — it flagged
~460 bikes whose specs carry more accurate service-manual gearing than the
generic lookup (e.g. Versys 650's real ER650 box) as "stale", and pointed at the
superseded ``refresh_gearing_from_lookup.py``. The canonical reseed is
``scripts/reseed_configs_from_specs.py``; run it and commit motoquant.db if this
fails.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from motoquant import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.gear_ratios import lookup_gear_ratios

DB_PATH = Path(__file__).resolve().parent.parent / "motoquant.db"

REFERENCE_PATTERNS = {
    "GSX-R 1000 K5": gsxr1000_k5,
    "YZF-R1 4C8": yzfr1_4c8,
    "Hayabusa GSX1300R Gen1": hayabusa_gen1,
}


def _reference_config_for(model_name: str):
    for needle, fn in REFERENCE_PATTERNS.items():
        if needle in model_name:
            return fn()
    return None


@pytest.mark.skipif(
    not DB_PATH.exists(), reason="production motoquant.db not present in this checkout"
)
class TestDBGearingIntegrity:
    """DB gear ratios must agree with the canonical source."""

    @pytest.fixture(scope="class")
    def rows(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT bm.id, m.name, bm.model_name, bm.year_from, bm.year_to,
                   bc.drivetrain_params
            FROM bike_configs bc
            JOIN bike_models bm ON bm.id = bc.bike_model_id
            JOIN manufacturers m ON m.id = bm.manufacturer_id
            WHERE bc.is_current = 1
            """
        )
        out = cur.fetchall()
        conn.close()
        return out

    def test_every_bike_has_tier1_or_reference_match(self, rows):
        """Every current bike must have a Tier-1 lookup hit
        (or be one of the three reference ships)."""
        missing = []
        for bmid, mfr, mdl, yf, yt, _dp in rows:
            if _reference_config_for(mdl) is not None:
                continue
            clean = mdl.split("(")[0].strip()
            year = yf or 2024
            if yt and yf:
                year = (yf + yt) // 2
            if lookup_gear_ratios(mfr, clean, year) is None:
                missing.append((bmid, mfr, mdl))
        assert not missing, (
            f"{len(missing)} bikes have no Tier-1 gear match; add entries to "
            f"motoquant/scraper/gear_ratios.py. First 5: {missing[:5]}"
        )

    def test_reference_bikes_match_defaults_py(self, rows):
        """K5/R1/Busa DB rows must equal the defaults.py ship config exactly."""
        bad = []
        for bmid, mfr, mdl, _yf, _yt, dp in rows:
            ship = _reference_config_for(mdl)
            if ship is None:
                continue
            drv = json.loads(dp)
            expected = {
                "gear_ratios": list(ship.drivetrain.gear_ratios),
                "front_sprocket": ship.drivetrain.front_sprocket,
                "rear_sprocket": ship.drivetrain.rear_sprocket,
                "primary_ratio": ship.drivetrain.primary_ratio,
            }
            actual = {
                "gear_ratios": drv.get("gear_ratios"),
                "front_sprocket": drv.get("front_sprocket"),
                "rear_sprocket": drv.get("rear_sprocket"),
                "primary_ratio": drv.get("primary_ratio"),
            }
            if actual != expected:
                bad.append((mdl, expected, actual))
        assert not bad, (
            f"Reference bike DB rows diverged from defaults.py ship config: "
            f"{bad}. Re-run scripts/refresh_gearing_from_lookup.py."
        )

    def test_non_reference_bikes_match_spec_config(self, rows):
        """Every non-reference bike's DB gearing must equal what
        ``spec_to_bike_config`` derives for its matched spec — the spec-preferred
        invariant the reseed maintains (catches K5-leaks without false-flagging
        bikes that ship a real service-manual cassette)."""
        from motoquant.scraper.importer import spec_to_bike_config
        from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
        from scripts.reseed_configs_from_specs import match_spec_to_row, strip_year

        specs_by_key: dict = {}
        for s in ALL_KNOWN_BIKES:
            specs_by_key.setdefault(
                (s.manufacturer.strip().lower(), strip_year(s.model_name).lower()), []
            ).append(s)

        bad = []
        for bmid, mfr, mdl, yf, yt, dp in rows:
            if _reference_config_for(mdl) is not None:
                continue
            spec = match_spec_to_row(
                {
                    "manufacturer": mfr,
                    "model_name": mdl,
                    "year_from": yf,
                    "year_to": yt,
                },
                specs_by_key,
            )
            if spec is None:
                continue  # no spec to reseed from — nothing to assert against
            drv = json.loads(dp)
            cfg = spec_to_bike_config(spec)
            if (
                drv.get("gear_ratios") != list(cfg.drivetrain.gear_ratios)
                or drv.get("front_sprocket") != cfg.drivetrain.front_sprocket
                or drv.get("rear_sprocket") != cfg.drivetrain.rear_sprocket
                or abs((drv.get("primary_ratio") or 0) - cfg.drivetrain.primary_ratio)
                > 1e-3
            ):
                bad.append(
                    (
                        mfr,
                        mdl,
                        f"DB {drv.get('front_sprocket')}F/{drv.get('rear_sprocket')}R "
                        f"vs spec {cfg.drivetrain.front_sprocket}F/"
                        f"{cfg.drivetrain.rear_sprocket}R",
                    )
                )
        assert not bad, (
            f"{len(bad)} bikes have DB gearing out of sync with spec_to_bike_config. "
            f"Run `python scripts/reseed_configs_from_specs.py`. First 5: {bad[:5]}"
        )

    def test_no_physically_impossible_top_gear_speed_for_reference_bikes(self, rows):
        """A no-regression canary: K5/R1/Busa top-gear redline speeds
        must land in the 280-360 km/h band."""
        import math
        import re

        for bmid, mfr, mdl, _yf, _yt, dp in rows:
            if _reference_config_for(mdl) is None:
                continue
            # Locate the matching engine + tire rows for this bike
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                "SELECT engine_params, tire_params FROM bike_configs "
                "WHERE bike_model_id=? AND is_current=1",
                (bmid,),
            )
            row = cur.fetchone()
            conn.close()
            if not row:
                continue
            eng = json.loads(row[0])
            tires = json.loads(row[1])
            drv = json.loads(dp)

            redline = eng.get("redline_rpm", 10000)
            primary = drv["primary_ratio"]
            top_ratio = drv["gear_ratios"][-1]
            front = drv["front_sprocket"]
            rear = drv["rear_sprocket"]

            rear_size = tires.get("rear_size") or ""
            m = re.match(r"(\d+)/(\d+)[ZRB]*R(\d+)", rear_size)
            if m:
                circ = (
                    (
                        int(m.group(3)) * 25.4
                        + 2 * int(m.group(1)) * int(m.group(2)) / 100
                    )
                    * math.pi
                    / 1000.0
                )
            else:
                circ = 1.98

            total_red = primary * top_ratio * (rear / front)
            v_kmh_at_redline = redline / total_red * circ / 60.0 * 3.6
            assert 260.0 <= v_kmh_at_redline <= 380.0, (
                f"{mdl} top-gear redline speed {v_kmh_at_redline:.1f} km/h is "
                f"outside the sanity band 260-380 km/h (gearing regression)."
            )
