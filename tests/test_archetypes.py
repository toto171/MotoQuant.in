"""
Tests for the bike_archetypes feature: schema migration, seed integrity,
fuzzy resolver, and runner delta application.

Each test builds its own isolated /tmp DB to avoid setUpClass state-sharing
quirks observed under `python -m unittest` runner. Slightly slower but
fully deterministic.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from typing import Any


# Ensure project root on sys.path so `import motoquant.*` works during direct
# invocation (`python -m unittest tests.test_archetypes`).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _build_minimal_db() -> str:
    """Build a minimal SQLite DB with just enough schema for archetype tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE manufacturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE bike_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id),
            model_name TEXT NOT NULL,
            peak_power_hp REAL,
            peak_torque_nm REAL,
            UNIQUE(manufacturer_id, model_name)
        );
        """
    )
    conn.execute("INSERT INTO manufacturers(name) VALUES ('Suzuki')")
    conn.execute("INSERT INTO manufacturers(name) VALUES ('Kawasaki')")
    conn.execute(
        """INSERT INTO bike_models(manufacturer_id, model_name, peak_power_hp, peak_torque_nm)
           VALUES ((SELECT id FROM manufacturers WHERE name='Suzuki'),
                   'Hayabusa (2008-2012)', 197.0, 155.0)"""
    )
    conn.execute(
        """INSERT INTO bike_models(manufacturer_id, model_name, peak_power_hp, peak_torque_nm)
           VALUES ((SELECT id FROM manufacturers WHERE name='Kawasaki'),
                   'Ninja H2 (2015-2023)', 228.0, 141.7)"""
    )
    conn.commit()

    from scripts.patch_2026_04_29 import ARCHETYPES_DDL
    for stmt in ARCHETYPES_DDL.strip().split(";"):
        s = stmt.strip()
        if s:
            conn.execute(s)
    conn.commit()
    conn.close()
    return path


class _FakeDB:
    """Minimal MotoQuantDB stand-in: the seed + resolver code only needs `_conn`."""
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")


def _seeded_db():
    """Build + seed a temp DB and return (path, FakeDB-handle, n_inserted).

    Uses ONE connection for the whole test lifecycle — avoids any
    cross-connection visibility issues we saw under the unittest runner
    where new connections briefly couldn't see freshly-committed rows.
    """
    path = _build_minimal_db()
    db = _FakeDB(path)
    from motoquant.database.seed_archetypes import seed_archetypes
    n = seed_archetypes(db)
    db._conn.commit()
    return path, db, n


class _ArchetypeTestBase(unittest.TestCase):
    def setUp(self):
        self.db_path, self.db, self.first_insert_count = _seeded_db()

    def tearDown(self):
        try:
            self.db._conn.close()
        except Exception:
            pass
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


class TestArchetypeSeed(_ArchetypeTestBase):
    """Confirms seed_archetypes inserts all 5 rows correctly."""

    def test_seed_inserts_five_archetypes(self) -> None:
        self.assertEqual(
            self.first_insert_count, 5,
            "Initial seed should insert exactly 5 archetypes",
        )

    def test_seed_is_idempotent(self) -> None:
        """Re-running seed_archetypes adds zero rows (UNIQUE constraint)."""
        from motoquant.database.seed_archetypes import seed_archetypes
        n_again = seed_archetypes(self.db)
        self.assertEqual(n_again, 0, "Re-run should be a no-op")
        total = self.db._conn.execute(
            "SELECT COUNT(*) FROM bike_archetypes"
        ).fetchone()[0]
        self.assertEqual(total, 5)

    def test_archetype_names_present(self) -> None:
        names = {r["name"] for r in self.db._conn.execute(
            "SELECT name FROM bike_archetypes"
        ).fetchall()}
        self.assertIn("TTS Stage 2 Turbo Hayabusa", names)
        self.assertIn("Velocity Racing 5-sec Turbo Hayabusa", names)
        self.assertIn("Bonneville H2 Carbon Track Edition", names)
        self.assertIn("Schnitz Nitrous Hayabusa", names)
        self.assertIn("Ron Ayers RAW Turbo Hayabusa", names)

    def test_archetype_deltas_are_sane(self) -> None:
        """Cross-check a few critical numbers haven't drifted."""
        rows = {r["name"]: r for r in self.db._conn.execute(
            """SELECT name, power_multiplier, peak_power_hp_override,
                      mass_delta_kg, is_homologation
               FROM bike_archetypes"""
        ).fetchall()}

        tts = rows["TTS Stage 2 Turbo Hayabusa"]
        self.assertGreater(tts["power_multiplier"], 1.5,
                           "TTS Stage 2 should ~double stock power")
        self.assertEqual(tts["is_homologation"], 0, "TTS is street-eligible")

        velocity = rows["Velocity Racing 5-sec Turbo Hayabusa"]
        self.assertGreater(velocity["power_multiplier"], 2.5,
                           "Velocity should triple stock for ~600 hp build")
        self.assertEqual(velocity["is_homologation"], 1,
                         "Velocity 5-sec is track-only")

        bonneville = rows["Bonneville H2 Carbon Track Edition"]
        self.assertEqual(bonneville["peak_power_hp_override"], 310.0,
                         "Bonneville H2 explicitly overrides to H2R-spec power")
        self.assertLess(bonneville["mass_delta_kg"], -20.0,
                        "Bonneville H2 strips mass for top-speed runs")


class TestArchetypeResolver(_ArchetypeTestBase):
    """Confirms resolver.resolve_archetype handles short forms + typos."""

    def _resolve(self, name: str):
        from motoquant.llm.resolver import resolve_archetype
        return resolve_archetype(name, self.db)

    def test_exact_name_match(self) -> None:
        arc_id, base_id = self._resolve("TTS Stage 2 Turbo Hayabusa")
        self.assertIsNotNone(arc_id)
        self.assertIsNotNone(base_id)

    def test_alias_short_form(self) -> None:
        arc_id, base_id = self._resolve("TTS turbo Hayabusa")
        self.assertIsNotNone(arc_id, "Alias 'TTS turbo Hayabusa' should resolve")

    def test_velocity_alias(self) -> None:
        arc_id, _ = self._resolve("Velocity 5-sec Hayabusa")
        self.assertIsNotNone(arc_id)

    def test_bonneville_alias(self) -> None:
        arc_id, _ = self._resolve("Bonneville H2")
        self.assertIsNotNone(arc_id)

    def test_nitrous_alias(self) -> None:
        arc_id, _ = self._resolve("nitrous Hayabusa")
        self.assertIsNotNone(arc_id)

    def test_unknown_returns_none(self) -> None:
        arc_id, base_id = self._resolve("not a real archetype xyz")
        self.assertIsNone(arc_id)
        self.assertIsNone(base_id)

    def test_empty_string_returns_none(self) -> None:
        arc_id, base_id = self._resolve("")
        self.assertIsNone(arc_id)
        self.assertIsNone(base_id)


class TestArchetypeRunnerApplication(_ArchetypeTestBase):
    """Confirms runner._apply_archetype mutates BikeConfig dataclass correctly."""

    def _make_stub_config(self) -> Any:
        """Build a minimal config object with the attribute paths the helper touches."""
        class _Engine:
            peak_power_hp = 197.0
            peak_torque_nm = 155.0
            dyno_curve = None
        class _Chassis:
            dry_mass_kg = 220.0
        class _Aero:
            cd = 0.55
            frontal_area_m2 = 0.55
        class _Drivetrain:
            front_sprocket = 18
            rear_sprocket = 40
            chain_pitch = "530"
        class _Tires:
            mu_peak = 1.30
        class _Config:
            engine = _Engine()
            chassis = _Chassis()
            aero = _Aero()
            drivetrain = _Drivetrain()
            tires = _Tires()
        return _Config()

    def _make_stub_parsed(self, archetype_id: int) -> Any:
        from motoquant.llm.parse_query import ParsedSimRequest
        return ParsedSimRequest(
            raw_query="how fast is a TTS Hayabusa",
            bike_name="Hayabusa",
            bike_id=1,
            archetype_id=archetype_id,
        )

    def test_tts_archetype_scales_power(self) -> None:
        from motoquant.llm.runner import _apply_archetype
        from motoquant.llm.resolver import resolve_archetype

        arc_id, _ = resolve_archetype("TTS Stage 2 Turbo Hayabusa", self.db)
        self.assertIsNotNone(arc_id)

        cfg = self._make_stub_config()
        original_hp = cfg.engine.peak_power_hp
        original_mass = cfg.chassis.dry_mass_kg

        _apply_archetype(cfg, self._make_stub_parsed(arc_id), self.db)

        # TTS = 1.85x power
        self.assertAlmostEqual(cfg.engine.peak_power_hp, original_hp * 1.85, places=1)
        # +14 kg from turbo plumbing
        self.assertAlmostEqual(cfg.chassis.dry_mass_kg, original_mass + 14.0, places=1)
        # Sprocket override 18/40
        self.assertEqual(cfg.drivetrain.front_sprocket, 18)
        self.assertEqual(cfg.drivetrain.rear_sprocket, 40)
        # Drag-radial mu
        self.assertAlmostEqual(cfg.tires.mu_peak, 1.65, places=2)

    def test_bonneville_uses_power_override(self) -> None:
        """Bonneville H2 sets peak_power_hp_override to 310 (replaces stock)."""
        from motoquant.llm.runner import _apply_archetype
        from motoquant.llm.resolver import resolve_archetype

        arc_id, _ = resolve_archetype("Bonneville H2 Carbon Track Edition", self.db)
        self.assertIsNotNone(arc_id)

        cfg = self._make_stub_config()
        cfg.engine.peak_power_hp = 228.0  # H2 stock
        _apply_archetype(cfg, self._make_stub_parsed(arc_id), self.db)
        # Override to 310 (× 1.0 multiplier)
        self.assertAlmostEqual(cfg.engine.peak_power_hp, 310.0, places=1)

    def test_no_archetype_id_is_noop(self) -> None:
        """If archetype_id is None the helper must not touch config."""
        from motoquant.llm.runner import _apply_archetype
        from motoquant.llm.parse_query import ParsedSimRequest

        cfg = self._make_stub_config()
        original_hp = cfg.engine.peak_power_hp

        parsed = ParsedSimRequest(
            raw_query="stock Hayabusa",
            bike_name="Hayabusa",
            bike_id=1,
            archetype_id=None,
        )
        _apply_archetype(cfg, parsed, self.db)
        self.assertEqual(cfg.engine.peak_power_hp, original_hp)


if __name__ == "__main__":
    unittest.main()
