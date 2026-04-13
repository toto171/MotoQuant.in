"""
MotoQuant Pro — Tire Repository
===============================
CRUD for the tire library — the most sim-critical component database.

Pacejka coefficients, thermal models, and friction data are the #1 driver
of simulation accuracy. This repo enforces confidence tracking rigorously.
"""

import json
import sqlite3
from typing import List, Optional, Dict, Any

from ..models import TireParams


class TireRepository:
    """Repository for tire models and their simulation parameters."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ────────────────────────────────────────────
    # Tire Manufacturers
    # ────────────────────────────────────────────

    def get_or_create_manufacturer(self, name: str, country: str = None) -> int:
        row = self._conn.execute(
            "SELECT id FROM tire_manufacturers WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["id"]
        cur = self._conn.execute(
            "INSERT INTO tire_manufacturers (name, country) VALUES (?, ?)",
            (name, country),
        )
        self._conn.commit()
        return cur.lastrowid

    # ────────────────────────────────────────────
    # Tire CRUD
    # ────────────────────────────────────────────

    def create(
        self,
        manufacturer_name: str,
        model_name: str,
        size_designation: str,
        compound_type: str = "sport",
        position: str = "rear",
        **kwargs,
    ) -> int:
        """
        Create a tire model entry.

        All Pacejka, friction, thermal, and physical params passed as kwargs.
        """
        mfr_id = self.get_or_create_manufacturer(manufacturer_name)

        cols = ["manufacturer_id", "model_name", "size_designation",
                "compound_type", "position"]
        vals = [mfr_id, model_name, size_designation, compound_type, position]

        # Parse size designation
        parts = size_designation.replace("ZR", "/").replace("R", "/").split("/")
        if len(parts) >= 2:
            try:
                kwargs.setdefault("width_mm", int(parts[0]))
            except ValueError:
                pass
            try:
                rest = parts[1].split("-") if "-" in parts[1] else parts[1:]
                if len(rest) >= 1:
                    kwargs.setdefault("aspect_ratio", int(rest[0]))
                if len(rest) >= 2:
                    kwargs.setdefault("rim_diameter_inch", int(rest[1]))
                elif len(parts) >= 3:
                    kwargs.setdefault("rim_diameter_inch", int(parts[2]))
            except (ValueError, IndexError):
                pass

        for k, v in kwargs.items():
            cols.append(k)
            vals.append(v)

        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(cols)

        cur = self._conn.execute(
            f"INSERT OR REPLACE INTO tire_models ({col_str}) VALUES ({placeholders})",
            vals,
        )
        self._conn.commit()
        return cur.lastrowid

    def get(self, tire_id: int) -> Optional[dict]:
        row = self._conn.execute(
            """SELECT tm.*, tmfr.name as manufacturer_name
               FROM tire_models tm
               JOIN tire_manufacturers tmfr ON tmfr.id = tm.manufacturer_id
               WHERE tm.id = ?""",
            (tire_id,),
        ).fetchone()
        return dict(row) if row else None

    def search(
        self,
        manufacturer: str = None,
        compound_type: str = None,
        position: str = None,
        size: str = None,
        min_mu_peak: float = None,
        available_india: bool = None,
        limit: int = 50,
    ) -> List[dict]:
        """Search tire models with filters."""
        conditions = []
        params = []

        if manufacturer:
            conditions.append("tmfr.name LIKE ?")
            params.append(f"%{manufacturer}%")
        if compound_type:
            conditions.append("tm.compound_type = ?")
            params.append(compound_type)
        if position:
            conditions.append("(tm.position = ? OR tm.position = 'both')")
            params.append(position)
        if size:
            conditions.append("tm.size_designation LIKE ?")
            params.append(f"%{size}%")
        if min_mu_peak is not None:
            conditions.append("tm.mu_peak >= ?")
            params.append(min_mu_peak)
        if available_india is not None:
            conditions.append("tm.available_india = ?")
            params.append(1 if available_india else 0)

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self._conn.execute(
            f"""SELECT tm.*, tmfr.name as manufacturer_name
                FROM tire_models tm
                JOIN tire_manufacturers tmfr ON tmfr.id = tm.manufacturer_id
                WHERE {where}
                ORDER BY tm.mu_peak DESC
                LIMIT ?""",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def to_tire_params(
        self,
        tire_id: int,
        is_rear: bool = True,
        pressure_psi: float = None,
    ) -> Optional[TireParams]:
        """
        Convert a tire_models row to a TireParams dataclass
        suitable for injection into a BikeConfig.
        """
        row = self.get(tire_id)
        if row is None:
            return None

        kwargs = {}

        if is_rear:
            kwargs["rear_model"] = f"{row['manufacturer_name']} {row['model_name']}"
            kwargs["rear_size"] = row["size_designation"]
            if row["rolling_radius_m"]:
                kwargs["rear_rolling_radius_m"] = row["rolling_radius_m"]
            if pressure_psi:
                kwargs["rear_pressure_psi"] = pressure_psi
            elif row.get("drag_pressure_psi"):
                kwargs["rear_pressure_psi"] = row["drag_pressure_psi"]
            elif row.get("recommended_psi"):
                kwargs["rear_pressure_psi"] = row["recommended_psi"]
            if row.get("mass_kg"):
                kwargs["rear_mass_kg"] = row["mass_kg"]
            if row.get("inertia_kgm2"):
                kwargs["rear_inertia_kgm2"] = row["inertia_kgm2"]
        else:
            kwargs["front_size"] = row["size_designation"]
            if row["rolling_radius_m"]:
                kwargs["front_rolling_radius_m"] = row["rolling_radius_m"]
            if pressure_psi:
                kwargs["front_pressure_psi"] = pressure_psi
            elif row.get("recommended_psi"):
                kwargs["front_pressure_psi"] = row["recommended_psi"]
            if row.get("mass_kg"):
                kwargs["front_mass_kg"] = row["mass_kg"]
            if row.get("inertia_kgm2"):
                kwargs["front_inertia_kgm2"] = row["inertia_kgm2"]

        # Friction and Pacejka
        for field in ["mu_peak", "mu_slide", "load_sensitivity_k",
                      "pacejka_B", "pacejka_C", "pacejka_D", "pacejka_E"]:
            if row.get(field) is not None:
                kwargs[field] = row[field]

        # Thermal
        for field in ["optimal_temp_c", "reversion_temp_c", "thermal_conductivity",
                      "tread_mass_kg", "specific_heat"]:
            if row.get(field) is not None:
                mapped = "specific_heat_rubber" if field == "specific_heat" else field
                kwargs[mapped] = row[field]

        # Rolling resistance
        for field in ["crr_base", "crr_speed_coeff", "crr_temp_coeff"]:
            if row.get(field) is not None:
                kwargs[field] = row[field]

        # Growth
        if row.get("growth_coeff") is not None:
            kwargs["growth_coeff"] = row["growth_coeff"]
        if row.get("construction"):
            kwargs["tire_construction"] = row["construction"]

        return TireParams(**kwargs)

    # ────────────────────────────────────────────
    # Grip comparison  (drag-focused analysis)
    # ────────────────────────────────────────────

    def rank_by_grip(
        self,
        position: str = "rear",
        compound_type: str = None,
        limit: int = 20,
    ) -> List[dict]:
        """
        Rank tires by effective grip potential (mu_peak weighted by confidence).
        """
        conditions = ["tm.mu_peak IS NOT NULL"]
        params = []

        if position:
            conditions.append("(tm.position = ? OR tm.position = 'both')")
            params.append(position)
        if compound_type:
            conditions.append("tm.compound_type = ?")
            params.append(compound_type)

        where = " AND ".join(conditions)

        rows = self._conn.execute(
            f"""SELECT tm.*, tmfr.name as manufacturer_name,
                       tm.mu_peak * COALESCE(tm.confidence, 0.5) as weighted_grip
                FROM tire_models tm
                JOIN tire_manufacturers tmfr ON tmfr.id = tm.manufacturer_id
                WHERE {where}
                ORDER BY weighted_grip DESC
                LIMIT ?""",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    # ────────────────────────────────────────────
    # Price comparison (Indian market)
    # ────────────────────────────────────────────

    def rank_by_value(
        self,
        position: str = "rear",
        limit: int = 20,
    ) -> List[dict]:
        """
        Rank tires by grip-per-rupee (value metric for Indian market).
        """
        rows = self._conn.execute(
            """SELECT tm.*, tmfr.name as manufacturer_name,
                      CASE WHEN tm.price_inr > 0
                           THEN tm.mu_peak / (tm.price_inr / 1000.0)
                           ELSE 0 END as grip_per_1k_inr
               FROM tire_models tm
               JOIN tire_manufacturers tmfr ON tmfr.id = tm.manufacturer_id
               WHERE tm.mu_peak IS NOT NULL
                 AND tm.price_inr > 0
                 AND tm.available_india = 1
                 AND (tm.position = ? OR tm.position = 'both')
               ORDER BY grip_per_1k_inr DESC
               LIMIT ?""",
            (position, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM tire_models").fetchone()
        return row["c"]
