"""
MotoQuant Pro — Simulation Run Repository
=========================================
Archive simulation results with full traceability back to
bike config, venue, weather conditions, and applied parts.
"""

import json
import sqlite3


class SimRunRepository:
    """Repository for simulation run result archival."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def record(
        self,
        bike_config_id: int,
        et_quarter_s: float,
        trap_speed_kmh: float,
        venue_id: int = None,
        weather_record_id: int = None,
        et_eighth_s: float = None,
        speed_eighth_kmh: float = None,
        time_60ft_s: float = None,
        speed_60ft_kmh: float = None,
        time_330ft_s: float = None,
        time_1000ft_s: float = None,
        sim_version: str = None,
        dt_s: float = 0.001,
        distance_m: float = 402.336,
        split_times: dict = None,
        time_series_path: str = None,
        applied_parts: list[int] = None,
        notes: str = None,
    ) -> int:
        """Store a simulation result."""
        cur = self._conn.execute(
            """INSERT INTO sim_runs
               (bike_config_id, venue_id, weather_record_id,
                et_quarter_s, trap_speed_kmh, et_eighth_s, speed_eighth_kmh,
                time_60ft_s, speed_60ft_kmh, time_330ft_s, time_1000ft_s,
                sim_version, dt_s, distance_m,
                split_times_json, time_series_path, applied_parts, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                bike_config_id,
                venue_id,
                weather_record_id,
                et_quarter_s,
                trap_speed_kmh,
                et_eighth_s,
                speed_eighth_kmh,
                time_60ft_s,
                speed_60ft_kmh,
                time_330ft_s,
                time_1000ft_s,
                sim_version,
                dt_s,
                distance_m,
                json.dumps(split_times) if split_times else None,
                time_series_path,
                json.dumps(applied_parts) if applied_parts else None,
                notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get(self, run_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM sim_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row else None

    def history(
        self,
        bike_config_id: int = None,
        venue_id: int = None,
        limit: int = 50,
    ) -> list[dict]:
        """Query run history with optional filters."""
        conditions = []
        params = []
        if bike_config_id is not None:
            conditions.append("bike_config_id = ?")
            params.append(bike_config_id)
        if venue_id is not None:
            conditions.append("venue_id = ?")
            params.append(venue_id)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self._conn.execute(
            f"""SELECT * FROM sim_runs
                WHERE {where}
                ORDER BY created_at DESC LIMIT ?""",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def best_et(self, bike_config_id: int) -> dict | None:
        """Get the best (lowest) ET run for a config."""
        row = self._conn.execute(
            """SELECT * FROM sim_runs
               WHERE bike_config_id = ? AND et_quarter_s IS NOT NULL
               ORDER BY et_quarter_s ASC LIMIT 1""",
            (bike_config_id,),
        ).fetchone()
        return dict(row) if row else None

    def leaderboard(
        self,
        venue_id: int = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Overall leaderboard (best ET per config).
        """
        venue_filter = ""
        params = []
        if venue_id is not None:
            venue_filter = "AND sr.venue_id = ?"
            params.append(venue_id)

        rows = self._conn.execute(
            f"""SELECT sr.*, bm.model_name, m.name as manufacturer_name
                FROM sim_runs sr
                JOIN bike_configs bc ON bc.id = sr.bike_config_id
                JOIN bike_models bm ON bm.id = bc.bike_model_id
                JOIN manufacturers m ON m.id = bm.manufacturer_id
                WHERE sr.et_quarter_s IS NOT NULL {venue_filter}
                GROUP BY sr.bike_config_id
                HAVING sr.et_quarter_s = MIN(sr.et_quarter_s)
                ORDER BY sr.et_quarter_s ASC
                LIMIT ?""",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM sim_runs").fetchone()
        return row["c"]
