"""
MotoQuant — Weather Repository
==============================
Live weather API integration + historical record storage.

Supports:
  - OpenWeatherMap API (free tier: current weather by lat/lon)
  - Manual weather entry (from trackside measurements)
  - Historical record queries (for DA trend analysis)
  - Density altitude computation with full psychrometric model

API key management: set OPENWEATHERMAP_API_KEY environment variable,
or pass directly to fetch_live().
"""

import json
import math
import os
import sqlite3
from datetime import datetime, timezone

from ..models import EnvironmentParams

# ────────────────────────────────────────────
# Atmospheric physics (standalone, no external deps)
# ────────────────────────────────────────────


def compute_air_density(
    temp_c: float,
    humidity_pct: float,
    pressure_hpa: float,
    altitude_m: float,
) -> float:
    """
    Compute air density (kg/m³) from atmospheric conditions.
    Uses barometric formula with humidity correction.
    """
    T_K = temp_c + 273.15
    g = 9.80665
    M = 0.0289644
    R = 8.31447
    L = 0.0065

    # Pressure at altitude
    P_sea = pressure_hpa * 100.0
    P_alt = P_sea * (1.0 - L * altitude_m / 288.15) ** (g * M / (R * L))

    # Saturation vapor pressure (August-Roche-Magnus)
    e_sat = 610.78 * math.exp(17.27 * temp_c / (temp_c + 237.3))
    e = e_sat * humidity_pct / 100.0

    # Virtual temperature
    T_virtual = T_K / (1.0 - 0.378 * e / max(P_alt, 1.0))

    return P_alt / (287.058 * T_virtual)


def compute_density_altitude(
    temp_c: float,
    humidity_pct: float,
    pressure_hpa: float,
    altitude_m: float,
) -> float:
    """Compute density altitude in feet."""
    rho = compute_air_density(temp_c, humidity_pct, pressure_hpa, altitude_m)
    rho_sl = 1.225
    if rho <= 0:
        return 0.0
    da_m = 44330.0 * (1.0 - (rho / rho_sl) ** 0.234969)
    return da_m * 3.28084


def compute_vapor_pressure(temp_c: float, humidity_pct: float) -> float:
    """Compute actual vapor pressure (hPa)."""
    e_sat = 6.1078 * math.exp(17.27 * temp_c / (temp_c + 237.3))
    return e_sat * humidity_pct / 100.0


def compute_dew_point(temp_c: float, humidity_pct: float) -> float:
    """Compute dew point temperature (°C)."""
    a = 17.27
    b = 237.7
    gamma = (a * temp_c / (b + temp_c)) + math.log(max(humidity_pct, 1) / 100.0)
    return (b * gamma) / (a - gamma)


def compute_power_correction(
    temp_c: float,
    pressure_hpa: float,
    humidity_pct: float,
    altitude_m: float,
) -> float:
    """
    SAE J607 power correction factor.
    Returns a multiplier < 1.0 for conditions worse than standard.
    Standard: 15°C, 1013.25 hPa, 0% humidity, sea level.
    """
    rho = compute_air_density(temp_c, humidity_pct, pressure_hpa, altitude_m)
    rho_std = 1.225
    return (rho / rho_std) ** 0.5  # Simplified SAE correction


class WeatherRepository:
    """Repository for weather records and live API access."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ────────────────────────────────────────────
    # Live API  (OpenWeatherMap)
    # ────────────────────────────────────────────

    def fetch_live(
        self,
        venue_id: int,
        api_key: str = None,
        track_temp_c: float = None,
    ) -> int | None:
        """
        Fetch current weather for a venue from OpenWeatherMap API.

        Returns the weather_record_id of the stored record, or None on failure.
        Requires `requests` package (gracefully handles import failure).
        """
        try:
            import requests
        except ImportError:
            return None

        if api_key is None:
            api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return None

        # Get venue coordinates
        venue = self._conn.execute(
            "SELECT * FROM venues WHERE id = ?", (venue_id,)
        ).fetchone()
        if venue is None or venue["latitude"] is None:
            return None

        lat, lon = venue["latitude"], venue["longitude"]
        altitude = venue["altitude_m"]

        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "units": "metric",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return None

        # Parse response
        temp_c = data.get("main", {}).get("temp", 25.0)
        humidity = data.get("main", {}).get("humidity", 50.0)
        pressure = data.get("main", {}).get("pressure", 1013.25)
        wind_speed = data.get("wind", {}).get("speed", 0.0)
        wind_deg = data.get("wind", {}).get("deg", 0.0)
        wind_gust = data.get("wind", {}).get("gust", 0.0)
        dew_point = compute_dew_point(temp_c, humidity)

        # Estimate track temp if not provided
        if track_temp_c is None:
            # Simple model: track ≈ air temp + solar heating offset
            track_temp_c = temp_c + 8.0  # Rough daytime estimate

        # Compute derived values
        rho = compute_air_density(temp_c, humidity, pressure, altitude)
        da_ft = compute_density_altitude(temp_c, humidity, pressure, altitude)
        vp = compute_vapor_pressure(temp_c, humidity)
        pcf = compute_power_correction(temp_c, pressure, humidity, altitude)

        # Store
        record_id = self.record(
            venue_id=venue_id,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            source="openweathermap",
            ambient_temp_c=temp_c,
            relative_humidity_pct=humidity,
            barometric_pressure_hpa=pressure,
            dew_point_c=dew_point,
            wind_speed_ms=wind_speed,
            wind_direction_deg=wind_deg,
            wind_gust_ms=wind_gust,
            track_temp_c=track_temp_c,
            density_altitude_ft=da_ft,
            air_density_kgm3=rho,
            vapor_pressure_hpa=vp,
            power_correction_factor=pcf,
            raw_response=json.dumps(data),
        )

        return record_id

    # ────────────────────────────────────────────
    # Manual / historical record entry
    # ────────────────────────────────────────────

    def record(
        self,
        venue_id: int,
        ambient_temp_c: float,
        relative_humidity_pct: float,
        barometric_pressure_hpa: float,
        recorded_at: str = None,
        source: str = "manual",
        dew_point_c: float = None,
        wind_speed_ms: float = 0.0,
        wind_direction_deg: float = 0.0,
        wind_gust_ms: float = None,
        track_temp_c: float = None,
        density_altitude_ft: float = None,
        air_density_kgm3: float = None,
        vapor_pressure_hpa: float = None,
        power_correction_factor: float = None,
        raw_response: str = None,
    ) -> int:
        """
        Store a weather record with auto-computed derived fields.
        """
        if recorded_at is None:
            recorded_at = datetime.now(timezone.utc).isoformat()

        # Get venue altitude for computations
        venue = self._conn.execute(
            "SELECT altitude_m FROM venues WHERE id = ?", (venue_id,)
        ).fetchone()
        altitude_m = venue["altitude_m"] if venue else 0.0

        # Auto-compute derived values if not provided
        if dew_point_c is None:
            dew_point_c = compute_dew_point(ambient_temp_c, relative_humidity_pct)
        if air_density_kgm3 is None:
            air_density_kgm3 = compute_air_density(
                ambient_temp_c,
                relative_humidity_pct,
                barometric_pressure_hpa,
                altitude_m,
            )
        if density_altitude_ft is None:
            density_altitude_ft = compute_density_altitude(
                ambient_temp_c,
                relative_humidity_pct,
                barometric_pressure_hpa,
                altitude_m,
            )
        if vapor_pressure_hpa is None:
            vapor_pressure_hpa = compute_vapor_pressure(
                ambient_temp_c,
                relative_humidity_pct,
            )
        if power_correction_factor is None:
            power_correction_factor = compute_power_correction(
                ambient_temp_c,
                barometric_pressure_hpa,
                relative_humidity_pct,
                altitude_m,
            )
        if track_temp_c is None:
            track_temp_c = ambient_temp_c + 5.0

        cur = self._conn.execute(
            """INSERT INTO weather_records
               (venue_id, recorded_at, source,
                ambient_temp_c, relative_humidity_pct, barometric_pressure_hpa,
                dew_point_c, wind_speed_ms, wind_direction_deg, wind_gust_ms,
                track_temp_c, density_altitude_ft, air_density_kgm3,
                vapor_pressure_hpa, power_correction_factor, raw_response)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                venue_id,
                recorded_at,
                source,
                ambient_temp_c,
                relative_humidity_pct,
                barometric_pressure_hpa,
                dew_point_c,
                wind_speed_ms,
                wind_direction_deg,
                wind_gust_ms,
                track_temp_c,
                density_altitude_ft,
                air_density_kgm3,
                vapor_pressure_hpa,
                power_correction_factor,
                raw_response,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ────────────────────────────────────────────
    # Queries
    # ────────────────────────────────────────────

    def get(self, record_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM weather_records WHERE id = ?", (record_id,)
        ).fetchone()
        return dict(row) if row else None

    def latest(self, venue_id: int) -> dict | None:
        """Get the most recent weather record for a venue."""
        row = self._conn.execute(
            """SELECT * FROM weather_records
               WHERE venue_id = ?
               ORDER BY recorded_at DESC LIMIT 1""",
            (venue_id,),
        ).fetchone()
        return dict(row) if row else None

    def history(
        self,
        venue_id: int,
        from_date: str = None,
        to_date: str = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query historical weather records for a venue."""
        conditions = ["venue_id = ?"]
        params = [venue_id]

        if from_date:
            conditions.append("recorded_at >= ?")
            params.append(from_date)
        if to_date:
            conditions.append("recorded_at <= ?")
            params.append(to_date)

        where = " AND ".join(conditions)
        rows = self._conn.execute(
            f"""SELECT * FROM weather_records
                WHERE {where}
                ORDER BY recorded_at DESC
                LIMIT ?""",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def da_trend(self, venue_id: int, limit: int = 365) -> list[dict]:
        """
        Get density altitude trend data for plotting.
        Returns [{recorded_at, density_altitude_ft, power_correction_factor}].
        """
        rows = self._conn.execute(
            """SELECT recorded_at, density_altitude_ft, power_correction_factor,
                      ambient_temp_c, relative_humidity_pct
               FROM weather_records
               WHERE venue_id = ? AND density_altitude_ft IS NOT NULL
               ORDER BY recorded_at DESC
               LIMIT ?""",
            (venue_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def to_environment(self, record_id: int) -> EnvironmentParams | None:
        """Convert a weather record to EnvironmentParams for simulation."""
        wr = self.get(record_id)
        if wr is None:
            return None

        venue = self._conn.execute(
            "SELECT * FROM venues WHERE id = ?", (wr["venue_id"],)
        ).fetchone()
        if venue is None:
            return None

        from .bridge import venue_row_to_environment

        return venue_row_to_environment(dict(venue), wr)

    def count(self, venue_id: int = None) -> int:
        if venue_id is not None:
            row = self._conn.execute(
                "SELECT COUNT(*) as c FROM weather_records WHERE venue_id = ?",
                (venue_id,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) as c FROM weather_records"
            ).fetchone()
        return row["c"]
