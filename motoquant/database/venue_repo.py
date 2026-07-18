"""
MotoQuant Pro — Venue Repository
================================
CRUD for drag strips, airstrips, and road closure venues.
Handles seasonal weather normals and environment construction.
"""

import sqlite3

from ..models import EnvironmentParams
from .bridge import seasonal_to_environment, venue_row_to_environment


class VenueRepository:
    """Repository for drag racing venues and their environmental data."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ────────────────────────────────────────────
    # Venue CRUD
    # ────────────────────────────────────────────

    def create(self, name: str, altitude_m: float, **kwargs) -> int:
        """Create a venue. Returns venue ID."""
        cols = ["name", "altitude_m"]
        vals = [name, altitude_m]
        for k, v in kwargs.items():
            cols.append(k)
            vals.append(v)
        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(cols)
        cur = self._conn.execute(
            f"INSERT OR IGNORE INTO venues ({col_str}) VALUES ({placeholders})",
            vals,
        )
        self._conn.commit()
        # rowcount is 0 when INSERT OR IGNORE hit the UNIQUE constraint; lastrowid
        # would keep the previous successful insert's rowid and never read 0 here.
        if cur.rowcount == 0:
            row = self._conn.execute(
                "SELECT id FROM venues WHERE name = ?", (name,)
            ).fetchone()
            return row["id"] if row else 0
        return cur.lastrowid

    def get(self, venue_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM venues WHERE id = ?", (venue_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_by_name(self, name: str) -> dict | None:
        """Look up by name or short_name."""
        row = self._conn.execute(
            "SELECT * FROM venues WHERE name = ? OR short_name = ?",
            (name, name),
        ).fetchone()
        return dict(row) if row else None

    def list_all(self, country: str = None, active_only: bool = True) -> list[dict]:
        """List all venues, optionally filtered."""
        conditions = []
        params = []
        if active_only:
            conditions.append("is_active = 1")
        if country:
            conditions.append("country = ?")
            params.append(country)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self._conn.execute(
            f"SELECT * FROM venues WHERE {where} ORDER BY name",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def list_indian_venues(self) -> list[dict]:
        """Shorthand for Indian venues."""
        return self.list_all(country="India")

    # ────────────────────────────────────────────
    # Seasonal data
    # ────────────────────────────────────────────

    def get_seasonal(self, venue_id: int, month: int) -> dict | None:
        """Get seasonal weather normals for a venue and month."""
        row = self._conn.execute(
            "SELECT * FROM venue_seasonal WHERE venue_id = ? AND month = ?",
            (venue_id, month),
        ).fetchone()
        return dict(row) if row else None

    def get_all_seasonal(self, venue_id: int) -> list[dict]:
        """Get all 12 months of seasonal data for a venue."""
        rows = self._conn.execute(
            "SELECT * FROM venue_seasonal WHERE venue_id = ? ORDER BY month",
            (venue_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def set_seasonal(
        self,
        venue_id: int,
        month: int,
        avg_temp_c: float,
        avg_humidity_pct: float,
        avg_pressure_hpa: float,
        avg_wind_speed_ms: float = 1.5,
        prevailing_wind_deg: float = 0.0,
        avg_track_temp_c: float = None,
        avg_density_alt_ft: float = None,
        temp_std_c: float = 3.0,
        humidity_std_pct: float = 10.0,
        pressure_std_hpa: float = 5.0,
    ):
        """Insert or update seasonal weather data for a venue/month."""
        if avg_track_temp_c is None:
            avg_track_temp_c = avg_temp_c + 5.0  # Rough estimate

        self._conn.execute(
            """INSERT OR REPLACE INTO venue_seasonal
               (venue_id, month, avg_temp_c, avg_humidity_pct,
                avg_pressure_hpa, avg_wind_speed_ms, prevailing_wind_deg,
                avg_track_temp_c, avg_density_alt_ft,
                temp_std_c, humidity_std_pct, pressure_std_hpa)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                venue_id,
                month,
                avg_temp_c,
                avg_humidity_pct,
                avg_pressure_hpa,
                avg_wind_speed_ms,
                prevailing_wind_deg,
                avg_track_temp_c,
                avg_density_alt_ft,
                temp_std_c,
                humidity_std_pct,
                pressure_std_hpa,
            ),
        )
        self._conn.commit()

    # ────────────────────────────────────────────
    # Environment construction
    # ────────────────────────────────────────────

    def to_environment(
        self,
        venue_id: int,
        month: int = None,
        weather_record_id: int = None,
    ) -> EnvironmentParams | None:
        """
        Build an EnvironmentParams for a venue.

        Priority:
          1. Specific weather_record_id (live or historical snapshot)
          2. Seasonal average for the given month
          3. Annual average (month=None → average all seasonal data)
          4. Venue defaults (altitude + standard atmosphere)
        """
        venue = self.get(venue_id)
        if venue is None:
            return None

        # Priority 1: specific weather record
        if weather_record_id is not None:
            wr = self._conn.execute(
                "SELECT * FROM weather_records WHERE id = ?",
                (weather_record_id,),
            ).fetchone()
            if wr:
                return venue_row_to_environment(venue, dict(wr))

        # Priority 2: seasonal average for the month
        if month is not None:
            seasonal = self.get_seasonal(venue_id, month)
            if seasonal:
                return seasonal_to_environment(venue, seasonal)

        # Priority 3: annual average
        all_seasonal = self.get_all_seasonal(venue_id)
        if all_seasonal:
            # Average across all available months
            avg = {
                "avg_temp_c": sum(s["avg_temp_c"] for s in all_seasonal)
                / len(all_seasonal),
                "avg_humidity_pct": sum(s["avg_humidity_pct"] for s in all_seasonal)
                / len(all_seasonal),
                "avg_pressure_hpa": sum(s["avg_pressure_hpa"] for s in all_seasonal)
                / len(all_seasonal),
                "avg_wind_speed_ms": sum(s["avg_wind_speed_ms"] for s in all_seasonal)
                / len(all_seasonal),
                "prevailing_wind_deg": all_seasonal[0]["prevailing_wind_deg"],
                "avg_track_temp_c": sum(s["avg_track_temp_c"] for s in all_seasonal)
                / len(all_seasonal),
                "avg_density_alt_ft": sum(s["avg_density_alt_ft"] for s in all_seasonal)
                / len(all_seasonal),
            }
            return seasonal_to_environment(venue, avg)

        # Priority 4: just altitude + standard atmosphere
        return EnvironmentParams(
            venue_name=venue["name"],
            altitude_m=venue["altitude_m"],
        )

    def best_da_month(self, venue_id: int) -> dict | None:
        """
        Find the month with the lowest density altitude (best for performance)
        at a given venue.
        """
        row = self._conn.execute(
            """SELECT * FROM venue_seasonal
               WHERE venue_id = ?
               ORDER BY avg_density_alt_ft ASC
               LIMIT 1""",
            (venue_id,),
        ).fetchone()
        return dict(row) if row else None

    def worst_da_month(self, venue_id: int) -> dict | None:
        """
        Find the month with the highest density altitude (worst for performance).
        """
        row = self._conn.execute(
            """SELECT * FROM venue_seasonal
               WHERE venue_id = ?
               ORDER BY avg_density_alt_ft DESC
               LIMIT 1""",
            (venue_id,),
        ).fetchone()
        return dict(row) if row else None

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM venues").fetchone()
        return row["c"]
