"""
MotoQuant Pro — Database Connection Manager
==========================================
Handles SQLite connection lifecycle, schema initialization, migrations,
and provides a single entry-point (MotoQuantDB) for all repository access.
"""

import sqlite3
from pathlib import Path

from .schema import (
    SCHEMA_VERSION,
    SEED_PARTS_CATEGORIES,
    SEED_SEASONAL_DATA,
    SEED_VENUES,
    TABLES_DDL,
)


class MotoQuantDB:
    """
    Central database facade.

    Usage:
        db = MotoQuantDB("motoquant.db")
        db.initialize()
        db.bikes.search(...)
        db.tires.list_compounds(...)
        db.venues.get(...)
        db.weather.fetch_live(...)
        db.parts.search(...)
    """

    def __init__(self, db_path: str = "motoquant.db"):
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

        # Repositories (lazy-initialized after connect)
        self._bikes = None
        self._tires = None
        self._venues = None
        self._weather = None
        self._parts = None
        self._sim_runs = None
        self._bike_suggestions = None

    # ────────────────────────────────────────────
    # Connection lifecycle
    # ────────────────────────────────────────────

    def connect(self) -> sqlite3.Connection:
        """Open (or return existing) SQLite connection with optimal pragmas."""
        if self._conn is not None:
            return self._conn

        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        # WAL mode is optimal but fails on some network/FUSE-mounted filesystems.
        # Silently fall back to DELETE journal mode if WAL is unavailable.
        try:
            row = self._conn.execute("PRAGMA journal_mode=WAL").fetchone()
            if row and row[0] != "wal":
                raise sqlite3.OperationalError("WAL not accepted by filesystem")
        except sqlite3.OperationalError:
            self._conn.execute("PRAGMA journal_mode=DELETE")

        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA cache_size=-64000")  # 64 MB
        return self._conn

    def close(self):
        """Close connection and reset repositories."""
        if self._conn:
            self._conn.close()
            self._conn = None
        self._bikes = None
        self._tires = None
        self._venues = None
        self._weather = None
        self._parts = None
        self._sim_runs = None
        self._bike_suggestions = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn

    # ────────────────────────────────────────────
    # Schema initialization & migration
    # ────────────────────────────────────────────

    def initialize(self):
        """Create all tables, seed reference data, and set schema version."""
        conn = self.conn

        # Create tables
        conn.executescript(TABLES_DDL)

        # Check current schema version
        try:
            row = conn.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            ).fetchone()
            current_version = int(row["value"]) if row else 0
        except sqlite3.OperationalError:
            current_version = 0

        if current_version < SCHEMA_VERSION:
            self._run_migrations(current_version, SCHEMA_VERSION)
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )

        # Seed reference data (idempotent)
        self._seed_parts_categories()
        self._seed_venues()
        self._seed_seasonal_data()

        conn.commit()

    def _run_migrations(self, from_version: int, to_version: int):
        """Run incremental migrations."""
        conn = self.conn

        # v1 → v2: Add fitment_rules column to parts table
        if from_version < 2:
            try:
                conn.execute("ALTER TABLE parts ADD COLUMN fitment_rules TEXT")
            except sqlite3.OperationalError as e:
                # Column already exists (idempotent)
                if "duplicate column name" not in str(e).lower():
                    raise

        # v2 → v3: bike_suggestions table (added for /api/bikes/suggest endpoint)
        # The CREATE TABLE statement is idempotent in TABLES_DDL, so no-op here —
        # but we bump the version so older DB files get their schema_meta updated.

    def _seed_parts_categories(self):
        """Insert parts categories if not present. Also prunes the retired
        'tire' pseudo-category from older DBs (tires are managed in tire_models,
        not parts — the category was only ever empty)."""
        conn = self.conn
        for name, display, affects in SEED_PARTS_CATEGORIES:
            conn.execute(
                """INSERT OR IGNORE INTO parts_categories (name, display_name, affects_params)
                   VALUES (?, ?, ?)""",
                (name, display, affects),
            )
        # Retire stale "tire" category if it exists AND is empty (parts in it
        # would block the delete via FK — that scenario is impossible by design
        # but we still guard against it rather than silently dropping data).
        tire_row = conn.execute(
            "SELECT id FROM parts_categories WHERE name = 'tire'"
        ).fetchone()
        if tire_row is not None:
            n_parts = conn.execute(
                "SELECT COUNT(*) FROM parts WHERE category_id = ?",
                (tire_row["id"],),
            ).fetchone()[0]
            if n_parts == 0:
                conn.execute(
                    "DELETE FROM parts_categories WHERE id = ?", (tire_row["id"],)
                )

    def _seed_venues(self):
        """Insert Indian drag venues if not present."""
        conn = self.conn
        for venue in SEED_VENUES:
            cols = ", ".join(venue.keys())
            placeholders = ", ".join(["?"] * len(venue))
            conn.execute(
                f"INSERT OR IGNORE INTO venues ({cols}) VALUES ({placeholders})",
                tuple(venue.values()),
            )

    def _seed_seasonal_data(self):
        """Insert seasonal weather normals for seeded venues."""
        conn = self.conn
        for venue_name, months in SEED_SEASONAL_DATA.items():
            row = conn.execute(
                "SELECT id FROM venues WHERE name = ?", (venue_name,)
            ).fetchone()
            if row is None:
                continue
            venue_id = row["id"]
            for month, vals in months.items():
                (
                    avg_t,
                    avg_h,
                    avg_p,
                    avg_w,
                    pw_deg,
                    trk_t,
                    da_ft,
                    t_std,
                    h_std,
                    p_std,
                ) = vals
                conn.execute(
                    """INSERT OR IGNORE INTO venue_seasonal
                       (venue_id, month, avg_temp_c, avg_humidity_pct,
                        avg_pressure_hpa, avg_wind_speed_ms, prevailing_wind_deg,
                        avg_track_temp_c, avg_density_alt_ft,
                        temp_std_c, humidity_std_pct, pressure_std_hpa)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        venue_id,
                        month,
                        avg_t,
                        avg_h,
                        avg_p,
                        avg_w,
                        pw_deg,
                        trk_t,
                        da_ft,
                        t_std,
                        h_std,
                        p_std,
                    ),
                )

    # ────────────────────────────────────────────
    # Repository accessors
    # ────────────────────────────────────────────

    @property
    def bikes(self):
        """Bike model & config repository."""
        if self._bikes is None:
            from .bike_repo import BikeRepository

            self._bikes = BikeRepository(self.conn)
        return self._bikes

    @property
    def tires(self):
        """Tire library repository."""
        if self._tires is None:
            from .tire_repo import TireRepository

            self._tires = TireRepository(self.conn)
        return self._tires

    @property
    def venues(self):
        """Venue repository."""
        if self._venues is None:
            from .venue_repo import VenueRepository

            self._venues = VenueRepository(self.conn)
        return self._venues

    @property
    def weather(self):
        """Weather data repository (live + historical)."""
        if self._weather is None:
            from .weather_repo import WeatherRepository

            self._weather = WeatherRepository(self.conn)
        return self._weather

    @property
    def parts(self):
        """Parts pricing repository."""
        if self._parts is None:
            from .parts_repo import PartsRepository

            self._parts = PartsRepository(self.conn)
        return self._parts

    @property
    def sim_runs(self):
        """Simulation run archive."""
        if self._sim_runs is None:
            from .sim_repo import SimRunRepository

            self._sim_runs = SimRunRepository(self.conn)
        return self._sim_runs

    @property
    def bike_suggestions(self):
        """User-submitted bike suggestion repository."""
        if self._bike_suggestions is None:
            from .bike_suggestions_repo import BikeSuggestionsRepository

            self._bike_suggestions = BikeSuggestionsRepository(self.conn)
        return self._bike_suggestions

    # ────────────────────────────────────────────
    # Utility
    # ────────────────────────────────────────────

    def stats(self) -> dict:
        """Return row counts for all major tables."""
        tables = [
            "manufacturers",
            "bike_models",
            "bike_configs",
            "dyno_curves",
            "tire_manufacturers",
            "tire_models",
            "venues",
            "weather_records",
            "venue_seasonal",
            "parts",
            "sim_runs",
            "data_provenance",
        ]
        counts = {}
        for t in tables:
            try:
                row = self.conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()
                counts[t] = row["c"]
            except sqlite3.OperationalError:
                counts[t] = 0
        return counts

    def vacuum(self):
        """Reclaim disk space."""
        self.conn.execute("VACUUM")

    @property
    def path(self) -> Path:
        return self._db_path
