"""
MotoQuant — Parts Repository
============================
CRUD for drag-relevant performance parts with Indian market pricing.

Each part specifies exact simulation-parameter changes (overrides, deltas,
multipliers) so the sim can compute the ET impact of any modification.
"""

import json
import sqlite3
from typing import Any

from ..models import BikeConfig
from .bridge import apply_part_to_config


def enrich_bike_row_for_fitment(conn: sqlite3.Connection, bike_row: dict) -> dict:
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


# Back-compat alias: tests and scripts/patch_2026_06_11_parts_fitment.py
# import the historical underscore name.
_enrich_bike_row_for_fitment = enrich_bike_row_for_fitment


def normalize_model_name(brand: str | None, model_name: str | None) -> str:
    """Strip a leading, exactly-matching brand prefix from a part's model name.

    Many catalog rows stored model_name WITH the brand baked in
    ("Nitrous Express NX Dual-Stage 60 HP Kit", brand="Nitrous Express"),
    so any UI rendering ``{brand} {model_name}`` printed the brand twice
    ("Nitrous Express Nitrous Express NX..."). Stripping at the data layer
    fixes every surface (web sim/optimize/tune + desktop) at once. Idempotent;
    never returns empty (keeps the original if stripping would empty it).
    """
    if not brand or not model_name:
        return model_name or ""
    b = brand.strip()
    m = model_name.strip()
    if m.lower().startswith(b.lower()):
        rest = m[len(b) :].lstrip(" -:\u2013\u2014\t")
        if rest:
            return rest
    return m


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
        # NOTE: model_name is intentionally NOT normalized here — the fresh
        # seed_all() path (used by in-memory catalog-integration tests) relies
        # on the original brand-prefixed names for leak-detection assertions.
        # Brand de-duplication for DISPLAY is handled at the data layer by
        # scripts/patch_2026_06_14_part_names.py (run in the DB-regen chain) and
        # defensively in the UI via partLabel() (web lib/api.js + desktop api.ts).
        # Resolve category ID
        cat_row = self._conn.execute(
            "SELECT id FROM parts_categories WHERE name = ?", (category_name,)
        ).fetchone()
        if cat_row is None:
            raise ValueError(f"Unknown parts category: {category_name}")
        category_id = cat_row["id"]

        col_names = (
            "category_id",
            "brand",
            "model_name",
            "part_number",
            "fitment_rules",
            "compatible_bikes",
            "fitment_universal",
            "fitment_notes",
            "specifications",
            "param_overrides",
            "param_deltas",
            "param_multipliers",
            "price_inr",
            "price_usd",
            "mrp_inr",
            "retailer",
            "retailer_url",
            "availability",
            "estimated_delivery_days",
        )
        col_vals = (
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
        )

        # ID-preserving upsert on UNIQUE(brand, part_number). INSERT OR REPLACE
        # would DELETE+re-INSERT with a new id, silently wiping any part_prices
        # history (cascades) and dangling sim_runs.applied_parts references to
        # the old id. Only dedupe when part_number is set — a NULL part_number
        # can't collide on the UNIQUE (SQLite treats NULLs as distinct), so
        # those fall through to a plain INSERT as before.
        existing = None
        if part_number is not None:
            existing = self._conn.execute(
                "SELECT id FROM parts WHERE brand = ? AND part_number = ?",
                (brand, part_number),
            ).fetchone()
        if existing:
            part_id = existing["id"] if hasattr(existing, "keys") else existing[0]
            assignments = ", ".join(f"{c} = ?" for c in col_names)
            self._conn.execute(
                f"UPDATE parts SET {assignments}, last_price_check = date('now') "
                "WHERE id = ?",
                [*col_vals, part_id],
            )
            self._conn.commit()
            return part_id

        placeholders = ", ".join(["?"] * len(col_names))
        cur = self._conn.execute(
            f"INSERT INTO parts ({', '.join(col_names)}, last_price_check) "
            f"VALUES ({placeholders}, date('now'))",
            col_vals,
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

        # When filtering by bike compatibility, the SQL LIMIT must NOT be
        # applied before the compatibility filter: with the catalog ordered
        # by brand, a pre-filter LIMIT silently drops every compatible part
        # whose brand sorts after the cut (the June-11 audit found the
        # optimizer never saw ~2/3 of the catalog because of this). Fetch
        # all matching rows first, filter, then honour `limit`.
        filtering_by_bike = bike_model_id is not None and not include_incompatible

        sql = f"""SELECT p.*, pc.name as category_name, pc.display_name as category_display
                FROM parts p
                JOIN parts_categories pc ON pc.id = p.category_id
                WHERE {where}
                ORDER BY p.brand, p.model_name"""
        if filtering_by_bike:
            rows = self._conn.execute(sql, params).fetchall()
        else:
            rows = self._conn.execute(sql + " LIMIT ?", params + [limit]).fetchall()

        result = [dict(r) for r in rows]

        # If bike_model_id given, filter by compatibility
        if filtering_by_bike:
            from ..parts.compatibility import is_compatible

            bike_row = self._conn.execute(
                "SELECT * FROM bike_models WHERE id = ?", (bike_model_id,)
            ).fetchone()
            if bike_row:
                bike_row = dict(bike_row)
                enrich_bike_row_for_fitment(self._conn, bike_row)
                result = [r for r in result if is_compatible(r, bike_row)[0]]
            result = result[: limit if limit is not None else len(result)]

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
        enrich_bike_row_for_fitment(self._conn, bike_row)

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
