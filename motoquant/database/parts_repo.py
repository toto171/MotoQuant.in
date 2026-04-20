"""
MotoQuant Pro — Parts Repository
================================
CRUD for drag-relevant performance parts with Indian market pricing.

Each part specifies exact simulation-parameter changes (overrides, deltas,
multipliers) so the sim can compute the ET impact of any modification.
"""

import json
import sqlite3
from typing import Any

from ..models import BikeConfig
from .bridge import apply_part_to_config


def _enrich_bike_row_for_fitment(conn: sqlite3.Connection, bike_row: dict) -> dict:
    """
    Populate bike_row fields that the compatibility engine needs but which
    aren't on the bike_models row alone:
      - manufacturer name (joined from manufacturers table)
      - cylinder_config, chain_pitch (from bike_configs JSON blobs,
        for legacy rows that pre-date the cylinder_config column)

    Mutates and returns bike_row. Safe to call multiple times — each lookup
    is skipped when the field is already populated.
    """
    bike_id = bike_row.get("id")
    if bike_id is None:
        return bike_row

    # Manufacturer name lookup
    if not bike_row.get("manufacturer") and not bike_row.get("manufacturer_name"):
        mfr_id = bike_row.get("manufacturer_id")
        if mfr_id is not None:
            mfr_row = conn.execute(
                "SELECT name FROM manufacturers WHERE id = ?", (mfr_id,)
            ).fetchone()
            if mfr_row is not None:
                bike_row["manufacturer"] = mfr_row["name"]

    # Only dig into bike_configs JSON if cylinder_config / chain_pitch / stroke_type missing
    needs_cyl = bike_row.get("cylinder_config") in (None, "")
    needs_pitch = bike_row.get("chain_pitch") in (None, "")
    needs_stroke = bike_row.get("stroke_type") in (None, "")
    if not (needs_cyl or needs_pitch or needs_stroke):
        return bike_row

    cfg_row = conn.execute(
        """SELECT engine_params, drivetrain_params
           FROM bike_configs
           WHERE bike_model_id = ? AND is_current = 1
           LIMIT 1""",
        (bike_id,),
    ).fetchone()
    if cfg_row is None:
        return bike_row

    ep = None
    if cfg_row["engine_params"]:
        try:
            ep = json.loads(cfg_row["engine_params"])
        except (json.JSONDecodeError, TypeError):
            ep = None

    if needs_cyl and ep is not None:
        bike_row["cylinder_config"] = ep.get("cylinder_config")
    if needs_stroke and ep is not None:
        # stroke_type defaults to 4 (canonical 4-stroke) if unset, so that
        # legacy 4T fitment rules without stroke_type filters still match.
        bike_row["stroke_type"] = ep.get("stroke_type", 4)
    if needs_pitch and cfg_row["drivetrain_params"]:
        try:
            dp = json.loads(cfg_row["drivetrain_params"])
            bike_row["chain_pitch"] = dp.get("chain_pitch")
        except (json.JSONDecodeError, TypeError):
            pass
    return bike_row


class PartsRepository:
    """Repository for performance parts with sim-parameter impact tracking."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ────────────────────────────────────────────
    # CRUD
    # ────────────────────────────────────────────

    def create(
        self,
        category_name: str,
        brand: str,
        model_name: str,
        specifications: dict,
        part_number: str = None,
        fitment_rules: dict = None,
        compatible_bike_ids: list[int] = None,
        fitment_universal: bool = False,
        fitment_notes: str = None,
        param_overrides: dict = None,
        param_deltas: dict = None,
        param_multipliers: dict = None,
        price_inr: float = None,
        price_usd: float = None,
        mrp_inr: float = None,
        retailer: str = None,
        retailer_url: str = None,
        availability: str = "in_stock",
        estimated_delivery_days: int = None,
    ) -> int:
        """Create a part entry with simulation impact parameters."""
        # Resolve category ID
        cat_row = self._conn.execute(
            "SELECT id FROM parts_categories WHERE name = ?", (category_name,)
        ).fetchone()
        if cat_row is None:
            raise ValueError(f"Unknown parts category: {category_name}")
        category_id = cat_row["id"]

        cur = self._conn.execute(
            """INSERT OR REPLACE INTO parts
               (category_id, brand, model_name, part_number,
                fitment_rules, compatible_bikes, fitment_universal, fitment_notes,
                specifications, param_overrides, param_deltas, param_multipliers,
                price_inr, price_usd, mrp_inr,
                retailer, retailer_url, availability,
                estimated_delivery_days, last_price_check)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))""",
            (
                category_id,
                brand,
                model_name,
                part_number,
                json.dumps(fitment_rules) if fitment_rules else None,
                json.dumps(compatible_bike_ids) if compatible_bike_ids else None,
                1 if fitment_universal else 0,
                fitment_notes,
                json.dumps(specifications),
                json.dumps(param_overrides) if param_overrides else None,
                json.dumps(param_deltas) if param_deltas else None,
                json.dumps(param_multipliers) if param_multipliers else None,
                price_inr,
                price_usd,
                mrp_inr,
                retailer,
                retailer_url,
                availability,
                estimated_delivery_days,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get(self, part_id: int) -> dict | None:
        row = self._conn.execute(
            """SELECT p.*, pc.name as category_name, pc.display_name as category_display
               FROM parts p
               JOIN parts_categories pc ON pc.id = p.category_id
               WHERE p.id = ?""",
            (part_id,),
        ).fetchone()
        return dict(row) if row else None

    def search(
        self,
        category: str = None,
        brand: str = None,
        name_contains: str = None,
        bike_model_id: int = None,
        max_price_inr: float = None,
        available_only: bool = False,
        include_incompatible: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        """
        Search parts with filters.
        If bike_model_id is given, filters by compatibility (unless include_incompatible=True).
        """
        conditions = []
        params = []

        if category:
            conditions.append("pc.name = ?")
            params.append(category)
        if brand:
            conditions.append("p.brand LIKE ?")
            params.append(f"%{brand}%")
        if name_contains:
            conditions.append("(p.model_name LIKE ? OR p.brand LIKE ?)")
            params.extend([f"%{name_contains}%", f"%{name_contains}%"])
        if max_price_inr is not None:
            conditions.append("p.price_inr <= ?")
            params.append(max_price_inr)
        if available_only:
            conditions.append("p.availability = 'in_stock'")

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self._conn.execute(
            f"""SELECT p.*, pc.name as category_name, pc.display_name as category_display
                FROM parts p
                JOIN parts_categories pc ON pc.id = p.category_id
                WHERE {where}
                ORDER BY p.brand, p.model_name
                LIMIT ?""",
            params + [limit],
        ).fetchall()

        result = [dict(r) for r in rows]

        # If bike_model_id given, filter by compatibility
        if bike_model_id is not None and not include_incompatible:
            from ..parts.compatibility import is_compatible
            bike_row = self._conn.execute(
                "SELECT * FROM bike_models WHERE id = ?", (bike_model_id,)
            ).fetchone()
            if bike_row:
                bike_row = dict(bike_row)
                _enrich_bike_row_for_fitment(self._conn, bike_row)
                result = [r for r in result if is_compatible(r, bike_row)[0]]

        return result

    def list_categories(self) -> list[dict]:
        """List all parts categories."""
        rows = self._conn.execute(
            "SELECT * FROM parts_categories ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_compatible_for_bike(
        self,
        bike_model_id: int,
        category: str = None,
    ) -> list[dict]:
        """
        List all parts compatible with a given bike.
        Each row includes 'fitment_reason' key explaining why it fits.
        """
        from ..parts.compatibility import is_compatible

        # Load bike
        bike_row = self._conn.execute(
            "SELECT * FROM bike_models WHERE id = ?", (bike_model_id,)
        ).fetchone()
        if bike_row is None:
            return []
        bike_row = dict(bike_row)
        _enrich_bike_row_for_fitment(self._conn, bike_row)

        # Search parts
        conditions = []
        params = []
        if category:
            conditions.append("pc.name = ?")
            params.append(category)

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self._conn.execute(
            f"""SELECT p.*, pc.name as category_name, pc.display_name as category_display
                FROM parts p
                JOIN parts_categories pc ON pc.id = p.category_id
                WHERE {where}
                ORDER BY p.brand, p.model_name""",
            params,
        ).fetchall()

        result = []
        for row in rows:
            row_dict = dict(row)
            compatible, reason = is_compatible(row_dict, bike_row)
            if compatible:
                row_dict["fitment_reason"] = reason
                result.append(row_dict)

        return result

    # ────────────────────────────────────────────
    # Simulation impact
    # ────────────────────────────────────────────

    def apply_to_config(self, part_id: int, config: BikeConfig) -> BikeConfig:
        """
        Apply a part's modifications to a BikeConfig.
        Returns a new BikeConfig with the part's changes applied.
        """
        part = self.get(part_id)
        if part is None:
            raise ValueError(f"Part {part_id} not found")
        return apply_part_to_config(config, part)

    def apply_multiple(self, part_ids: list[int], config: BikeConfig) -> BikeConfig:
        """Apply multiple parts sequentially. Returns modified config."""
        for pid in part_ids:
            config = self.apply_to_config(pid, config)
        return config

    def estimate_build_cost(
        self,
        part_ids: list[int],
        currency: str = "inr",
    ) -> dict[str, Any]:
        """
        Calculate total cost of a parts list.

        Returns:
            {
                "total": float,
                "currency": str,
                "parts": [{"name": ..., "price": ..., "available": ...}],
                "unavailable_count": int,
            }
        """
        price_col = "price_inr" if currency == "inr" else "price_usd"
        total = 0.0
        parts_list = []
        unavailable = 0

        for pid in part_ids:
            part = self.get(pid)
            if part is None:
                continue
            price = part.get(price_col) or 0.0
            total += price
            available = part.get("availability", "unknown") == "in_stock"
            if not available:
                unavailable += 1
            parts_list.append(
                {
                    "id": pid,
                    "name": f"{part['brand']} {part['model_name']}",
                    "category": part["category_display"],
                    "price": price,
                    "available": available,
                }
            )

        return {
            "total": total,
            "currency": currency.upper(),
            "parts": parts_list,
            "unavailable_count": unavailable,
        }

    # ────────────────────────────────────────────
    # Sprocket ratio calculator (common drag mod)
    # ────────────────────────────────────────────

    def find_sprocket_combos(
        self,
        bike_model_id: int = None,
        target_ratio_min: float = None,
        target_ratio_max: float = None,
    ) -> list[dict]:
        """
        Find available front+rear sprocket combinations.
        Useful for gearing optimization.
        """
        front_parts = self.search(category="sprocket", bike_model_id=bike_model_id)
        rear_parts = self.search(category="sprocket", bike_model_id=bike_model_id)

        combos = []
        for fp in front_parts:
            specs_f = (
                json.loads(fp["specifications"])
                if isinstance(fp["specifications"], str)
                else fp["specifications"]
            )
            if specs_f.get("position") != "front":
                continue
            teeth_f = specs_f.get("teeth")
            if not teeth_f:
                continue

            for rp in rear_parts:
                specs_r = (
                    json.loads(rp["specifications"])
                    if isinstance(rp["specifications"], str)
                    else rp["specifications"]
                )
                if specs_r.get("position") != "rear":
                    continue
                teeth_r = specs_r.get("teeth")
                if not teeth_r:
                    continue

                ratio = teeth_r / teeth_f
                if target_ratio_min and ratio < target_ratio_min:
                    continue
                if target_ratio_max and ratio > target_ratio_max:
                    continue

                cost = (fp.get("price_inr") or 0) + (rp.get("price_inr") or 0)
                combos.append(
                    {
                        "front_teeth": teeth_f,
                        "rear_teeth": teeth_r,
                        "ratio": round(ratio, 3),
                        "front_part": fp["brand"] + " " + fp["model_name"],
                        "rear_part": rp["brand"] + " " + rp["model_name"],
                        "total_cost_inr": cost,
                    }
                )

        combos.sort(key=lambda x: x["ratio"])
        return combos

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM parts").fetchone()
        return row["c"]
