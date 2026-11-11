"""
MotoQuant — Database Connection Manager
=======================================
Handles SQLite connection lifecycle, schema initialization, migrations,
and provides a single entry-point (MotoQuantDB) for all repository access.
"""

import re
import sqlite3
import threading
from pathlib import Path

from .schema import (
    SCHEMA_VERSION,
    SEED_PARTS_CATEGORIES,
    SEED_SEASONAL_DATA,
    SEED_VENUES,
    TABLES_DDL,
)

# -- Catalog generation counter ------------------------------------------------
# Process-wide integer that changes whenever a catalog table is written at
# runtime. API-side caches (serialized catalog responses, parsed fitment rules,
# stock-baseline sims) key on it, so a write invalidates all of them at once.
# It is NOT derived from the DB file's mtime: WAL writes do not move that until
# a checkpoint. Writes through THIS process's MotoQuantDB connections bump it
# via the authorizer below; writes made through any other connection (another
# process, or a plain sqlite3.connect) are caught by folding ``PRAGMA
# data_version`` into the token returned by :func:`catalog_token`.
CATALOG_TABLES = frozenset(
    {
        "bike_models",
        "bike_configs",
        "manufacturers",
        "parts",
        "parts_categories",
        "part_prices",
        "tire_models",
        "tire_manufacturers",
        "bike_tire_fitments",
        "venues",
        "venue_seasonal",
    }
)
_catalog_generation = 0
_catalog_generation_lock = threading.Lock()


def catalog_generation() -> int:
    """Current catalog generation (monotonically increasing within a process)."""
    return _catalog_generation


def catalog_token(conn: "sqlite3.Connection | None") -> tuple:
    """Opaque freshness token for catalog-derived caches.

    ``(generation, data_version)``: the generation moves on every write made
    through a MotoQuantDB connection or an explicit bump; ``PRAGMA
    data_version`` moves whenever a DIFFERENT connection (another process, a
    script, a plain ``sqlite3.connect``) commits to the same database file.
    Compare for equality only.
    """
    dv = None
    if conn is not None:
        try:
            dv = conn.execute("PRAGMA data_version").fetchone()[0]
        except sqlite3.Error:
            dv = None
    return (_catalog_generation, dv)


def bump_catalog_generation() -> int:
    """Mark every catalog-derived cache stale. Returns the new generation."""
    global _catalog_generation
    with _catalog_generation_lock:
        _catalog_generation += 1
        return _catalog_generation


# A statement that may write: INSERT, UPDATE, DELETE or REPLACE anywhere in
# the text (covers "INSERT OR REPLACE", "WITH ... UPDATE", scripts).
_WRITE_SQL = re.compile(r"\b(?:INSERT|UPDATE|DELETE|REPLACE)\b", re.IGNORECASE)
_CATALOG_TABLE_SQL = re.compile(
    r"\b(?:" + "|".join(sorted(CATALOG_TABLES)) + r")\b", re.IGNORECASE
)


def _bump_if_catalog_write(sql: str) -> None:
    """Mark catalog caches stale before a statement that may write a catalog
    table. Conservative: a write that merely mentions a catalog table (say an
    INSERT INTO sim_runs ... SELECT FROM bike_configs) also bumps, which costs
    a cache refill and nothing else."""
    if (
        isinstance(sql, str)
        and _WRITE_SQL.search(sql)
        and _CATALOG_TABLE_SQL.search(sql)
    ):
        bump_catalog_generation()


class _CatalogTrackingCursor(sqlite3.Cursor):
    def execute(self, sql, parameters=(), /):
        _bump_if_catalog_write(sql)
        return super().execute(sql, parameters)

    def executemany(self, sql, seq_of_parameters, /):
        _bump_if_catalog_write(sql)
        return super().executemany(sql, seq_of_parameters)

    def executescript(self, sql_script, /):
        _bump_if_catalog_write(sql_script)
        return super().executescript(sql_script)


class CatalogTrackingConnection(sqlite3.Connection):
    """Connection that marks catalog caches stale when it writes the catalog.

    Writes made through other connections (another process, the CLI) change
    ``PRAGMA data_version``, which :func:`catalog_token` already checks; a
    connection's own writes do not, so this class looks at the SQL instead.

    This used to be an SQLite authorizer callback. That deadlocked: the API
    shares one connection across threads, SQLite calls the authorizer while
    holding the connection mutex, and the callback needs the GIL, which another
    thread can hold while it waits for that same mutex (for example while it
    reads column values). Concurrent requests hung the API until Render
    restarted it. No Python code may run under the SQLite mutex, so the check
    runs here, before SQLite sees the statement.
    """

    def cursor(self, factory=_CatalogTrackingCursor):
        return super().cursor(factory)

    def execute(self, sql, parameters=(), /):
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql, seq_of_parameters, /):
        return self.cursor().executemany(sql, seq_of_parameters)

    def executescript(self, sql_script, /):
        return self.cursor().executescript(sql_script)


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

        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
            # Threads share this connection: a cached prepared statement would
            # be shared too, and two threads stepping one statement is misuse.
            cached_statements=0,
            factory=CatalogTrackingConnection,
        )
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
        # Wait up to 5 s for a lock instead of failing instantly with "database
        # is locked" (default busy_timeout is 0). The API shares one connection
        # across request + job-worker threads (see docs/KNOWN_TRAPS.md T14); this
        # lets concurrent writers queue on the lock rather than error out. It is
        # a mitigation, not a substitute for per-thread/pooled connections at
        # scale (see docs/ROADMAP.md P0-3).
        self._conn.execute("PRAGMA busy_timeout=5000")
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

        # v2 → v3: bike_suggestions table
        # The CREATE TABLE statement is idempotent in TABLES_DDL, so no-op here —
        # but we bump the version so older DB files get their schema_meta updated.

        # v3 → v4: part_prices table (live Indian-market retailer pricing layer)
        if from_version < 4:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS part_prices (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_id    INTEGER NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
                    retailer   TEXT    NOT NULL,
                    source_url TEXT    NOT NULL,
                    price_inr  REAL,
                    in_stock   INTEGER NOT NULL DEFAULT 1,
                    fetched_at TEXT    NOT NULL DEFAULT (datetime('now','utc')),
                    created_at TEXT    DEFAULT (datetime('now','utc')),
                    UNIQUE(part_id, retailer)
                );
                CREATE INDEX IF NOT EXISTS idx_part_prices_part  ON part_prices(part_id);
                CREATE INDEX IF NOT EXISTS idx_part_prices_fetch ON part_prices(fetched_at);
                """
            )

        # v5 -> v6: category_tag on bike_configs (per-cluster physics tag,
        # persisted so the DB sim path matches the spec-path sweep)
        if from_version < 6:
            try:
                conn.execute("ALTER TABLE bike_configs ADD COLUMN category_tag TEXT")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise

    def _seed_parts_categories(self):
        """Insert parts categories if not present. Also prunes the retired
        'tire' pseudo-category from older DBs (tires are managed in tire_models,
        not parts — the category was only ever empty)."""
        conn = self.conn
        # Insert only the rows that are missing. ``INSERT OR IGNORE`` into an
        # AUTOINCREMENT table advances ``sqlite_sequence`` even when the row is
        # ignored, so re-running it on every open rewrote the database file:
        # any read-only CLI command left the tracked motoquant.db modified.
        # The same guard is on the venue and seasonal seeds below.
        present = {r[0] for r in conn.execute("SELECT name FROM parts_categories")}
        for name, display, affects in SEED_PARTS_CATEGORIES:
            if name in present:
                continue
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
        present = {r[0] for r in conn.execute("SELECT name FROM venues")}
        for venue in SEED_VENUES:
            if venue.get("name") in present:
                continue
            cols = ", ".join(venue.keys())
            placeholders = ", ".join(["?"] * len(venue))
            conn.execute(
                f"INSERT OR IGNORE INTO venues ({cols}) VALUES ({placeholders})",
                tuple(venue.values()),
            )

    def _seed_seasonal_data(self):
        """Insert seasonal weather normals for seeded venues."""
        conn = self.conn
        present = {
            (r[0], r[1])
            for r in conn.execute("SELECT venue_id, month FROM venue_seasonal")
        }
        for venue_name, months in SEED_SEASONAL_DATA.items():
            row = conn.execute(
                "SELECT id FROM venues WHERE name = ?", (venue_name,)
            ).fetchone()
            if row is None:
                continue
            venue_id = row["id"]
            for month, vals in months.items():
                if (venue_id, month) in present:
                    continue
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


def connect(db_path=None):
    """
    Convenience helper: open a connection to the MotoQuant DB and return it.
    Uses MOTOQUANT_DB env var if db_path is None, defaulting to motoquant.db.
    """
    import os as _os

    path = db_path or _os.environ.get("MOTOQUANT_DB", "motoquant.db")
    db = MotoQuantDB(path)
    return db.conn


def row_conn(db_path=None) -> sqlite3.Connection:
    """``connect()`` with ``sqlite3.Row`` as the row factory — the exact shape
    the optional-accounts layer (auth) needs. Centralised so the row-factory
    (and any future per-request connection tuning) lives in one place instead
    of being copy-pasted into every module's ``_get_conn``.
    """
    conn = connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
