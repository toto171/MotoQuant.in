"""
MotoQuant Pro — Bike Repository
===============================
CRUD operations for manufacturers, bike models, and bike configs.
Handles BikeConfig ↔ DB conversion via the bridge module.
"""

import json
import sqlite3

import numpy as np

from ..models import BikeConfig, DynoCurve, EnvironmentParams
from .bridge import (
    compute_data_completeness,
    config_to_db_row,
    db_row_to_config,
    extract_dyno_curve,
    extract_headline_specs,
)


class BikeRepository:
    """Repository for bike models and their simulation configs."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ────────────────────────────────────────────
    # Manufacturers
    # ────────────────────────────────────────────

    def get_or_create_manufacturer(self, name: str, country: str = None) -> int:
        """Get manufacturer ID, creating if necessary."""
        row = self._conn.execute(
            "SELECT id FROM manufacturers WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["id"]

        # Check aliases
        rows = self._conn.execute(
            "SELECT id, aliases FROM manufacturers WHERE aliases IS NOT NULL"
        ).fetchall()
        for r in rows:
            aliases = json.loads(r["aliases"]) if r["aliases"] else []
            if name.lower() in [a.lower() for a in aliases]:
                return r["id"]

        cur = self._conn.execute(
            "INSERT INTO manufacturers (name, country) VALUES (?, ?)",
            (name, country),
        )
        self._conn.commit()
        return cur.lastrowid

    def list_manufacturers(self) -> list[dict]:
        """List all manufacturers with bike counts."""
        rows = self._conn.execute("""
            SELECT m.id, m.name, m.country, COUNT(b.id) as bike_count
            FROM manufacturers m
            LEFT JOIN bike_models b ON b.manufacturer_id = m.id
            GROUP BY m.id
            ORDER BY m.name
        """).fetchall()
        return [dict(r) for r in rows]

    # ────────────────────────────────────────────
    # Bike Models (identity + headline specs)
    # ────────────────────────────────────────────

    def create_model(
        self,
        manufacturer_id: int,
        model_name: str,
        model_code: str = None,
        year_from: int = None,
        year_to: int = None,
        category: str = "sport",
        subcategory: str = None,
        data_source: str = "estimated",
        **headline_specs,
    ) -> int:
        """Create a new bike model entry. Returns model ID."""
        cols = [
            "manufacturer_id",
            "model_name",
            "model_code",
            "year_from",
            "year_to",
            "category",
            "subcategory",
            "data_source",
        ]
        vals = [
            manufacturer_id,
            model_name,
            model_code,
            year_from,
            year_to,
            category,
            subcategory,
            data_source,
        ]

        for k, v in headline_specs.items():
            cols.append(k)
            vals.append(v)

        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(cols)

        cur = self._conn.execute(
            f"INSERT OR IGNORE INTO bike_models ({col_str}) VALUES ({placeholders})",
            vals,
        )
        self._conn.commit()

        if cur.lastrowid == 0:
            # Already existed
            row = self._conn.execute(
                """SELECT id FROM bike_models
                   WHERE manufacturer_id = ? AND model_name = ?
                   AND model_code IS ? AND year_from IS ?""",
                (manufacturer_id, model_name, model_code, year_from),
            ).fetchone()
            return row["id"] if row else 0

        return cur.lastrowid

    def get_model(self, model_id: int) -> dict | None:
        """Get a bike model by ID."""
        row = self._conn.execute(
            """SELECT bm.*, m.name as manufacturer_name
               FROM bike_models bm
               JOIN manufacturers m ON m.id = bm.manufacturer_id
               WHERE bm.id = ?""",
            (model_id,),
        ).fetchone()
        return dict(row) if row else None

    def search(
        self,
        manufacturer: str = None,
        name_contains: str = None,
        category: str = None,
        displacement_min: float = None,
        displacement_max: float = None,
        power_min: float = None,
        year_from: int = None,
        year_to: int = None,
        data_quality: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        Search bike models with filters.

        Returns list of dicts with manufacturer_name joined.
        """
        conditions = []
        params = []

        if manufacturer:
            conditions.append("m.name LIKE ?")
            params.append(f"%{manufacturer}%")
        if name_contains:
            conditions.append("(bm.model_name LIKE ? OR bm.model_code LIKE ?)")
            params.extend([f"%{name_contains}%", f"%{name_contains}%"])
        if category:
            conditions.append("bm.category = ?")
            params.append(category)
        if displacement_min is not None:
            conditions.append("bm.displacement_cc >= ?")
            params.append(displacement_min)
        if displacement_max is not None:
            conditions.append("bm.displacement_cc <= ?")
            params.append(displacement_max)
        if power_min is not None:
            conditions.append("bm.peak_power_hp >= ?")
            params.append(power_min)
        if year_from is not None:
            conditions.append("(bm.year_to IS NULL OR bm.year_to >= ?)")
            params.append(year_from)
        if year_to is not None:
            conditions.append("(bm.year_from IS NULL OR bm.year_from <= ?)")
            params.append(year_to)
        if data_quality:
            conditions.append("bm.data_quality = ?")
            params.append(data_quality)

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = self._conn.execute(
            f"""SELECT bm.*, m.name as manufacturer_name
                FROM bike_models bm
                JOIN manufacturers m ON m.id = bm.manufacturer_id
                WHERE {where}
                ORDER BY m.name, bm.model_name, bm.year_from
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
        return [dict(r) for r in rows]

    # ────────────────────────────────────────────
    # Bike Configs (full simulation parameter sets)
    # ────────────────────────────────────────────

    def create_config(
        self,
        bike_model_id: int,
        config: BikeConfig,
        config_name: str = "stock",
        source: str = "spec_sheet",
        source_url: str = None,
        confidence: float = 0.5,
        notes: str = None,
    ) -> int:
        """
        Store a full BikeConfig as a versioned config row.
        Returns config ID.
        """
        # Determine next version number
        row = self._conn.execute(
            """SELECT COALESCE(MAX(version), 0) as max_v
               FROM bike_configs
               WHERE bike_model_id = ? AND config_name = ?""",
            (bike_model_id, config_name),
        ).fetchone()
        next_version = row["max_v"] + 1

        # Mark all previous versions as non-current
        self._conn.execute(
            """UPDATE bike_configs SET is_current = 0
               WHERE bike_model_id = ? AND config_name = ?""",
            (bike_model_id, config_name),
        )

        # Serialize parameter blocks
        row_data = config_to_db_row(config)

        cur = self._conn.execute(
            """INSERT INTO bike_configs
               (bike_model_id, version, is_current, config_name,
                chassis_params, engine_params, forced_induction_params,
                drivetrain_params, clutch_params, tire_params, aero_params,
                suspension_params, braking_params, wheelie_params,
                rider_params, parasitic_params, staging_params,
                source, source_url, confidence, notes)
               VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                bike_model_id,
                next_version,
                config_name,
                row_data["chassis_params"],
                row_data["engine_params"],
                row_data["forced_induction_params"],
                row_data["drivetrain_params"],
                row_data["clutch_params"],
                row_data["tire_params"],
                row_data["aero_params"],
                row_data["suspension_params"],
                row_data["braking_params"],
                row_data["wheelie_params"],
                row_data["rider_params"],
                row_data["parasitic_params"],
                row_data["staging_params"],
                source,
                source_url,
                confidence,
                notes,
            ),
        )
        config_id = cur.lastrowid

        # Store dyno curve separately (for cross-bike analysis)
        dyno_data = extract_dyno_curve(config)
        if dyno_data:
            self._conn.execute(
                """INSERT INTO dyno_curves
                   (bike_config_id, curve_type, is_at_wheel,
                    rpm_points, torque_values, num_points, source, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    config_id,
                    dyno_data["curve_type"],
                    dyno_data["is_at_wheel"],
                    dyno_data["rpm_points"],
                    dyno_data["torque_values"],
                    dyno_data["num_points"],
                    source,
                    confidence,
                ),
            )

        # Update data completeness on the model
        completeness = compute_data_completeness(config)
        self._conn.execute(
            "UPDATE bike_models SET data_completeness = ?, updated_at = datetime('now','utc') WHERE id = ?",
            (completeness, bike_model_id),
        )

        self._conn.commit()
        return config_id

    def get_config(self, config_id: int) -> dict | None:
        """Get a bike config row by ID."""
        row = self._conn.execute(
            "SELECT * FROM bike_configs WHERE id = ?", (config_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_current_config(
        self, bike_model_id: int, config_name: str = "stock"
    ) -> dict | None:
        """Get the current (latest) config for a model."""
        row = self._conn.execute(
            """SELECT * FROM bike_configs
               WHERE bike_model_id = ? AND config_name = ? AND is_current = 1""",
            (bike_model_id, config_name),
        ).fetchone()
        return dict(row) if row else None

    def to_config(
        self,
        config_id: int,
        environment: EnvironmentParams | None = None,
    ) -> BikeConfig | None:
        """
        Load a bike_configs row and reconstruct a full BikeConfig
        ready for simulation.
        """
        config_row = self.get_config(config_id)
        if config_row is None:
            return None

        # Get the model name
        model = self.get_model(config_row["bike_model_id"])
        name = f"{model['manufacturer_name']} {model['model_name']}"
        if model.get("model_code"):
            name += f" {model['model_code']}"

        # Check for a separate dyno curve
        dyno_row = self._conn.execute(
            """SELECT * FROM dyno_curves
               WHERE bike_config_id = ?
               ORDER BY created_at DESC LIMIT 1""",
            (config_id,),
        ).fetchone()

        dyno_override = None
        if dyno_row:
            rpm = np.array(json.loads(dyno_row["rpm_points"]))
            torque = np.array(json.loads(dyno_row["torque_values"]))
            dyno_override = DynoCurve(
                rpm=rpm,
                torque_nm=torque,
                is_at_wheel=bool(dyno_row["is_at_wheel"]),
            )

        return db_row_to_config(
            config_row,
            name=name,
            environment=environment,
            dyno_override=dyno_override,
        )

    # ────────────────────────────────────────────
    # Convenience: upsert from BikeConfig
    # ────────────────────────────────────────────

    def upsert_from_config(
        self,
        config: BikeConfig,
        manufacturer_name: str = None,
        model_code: str = None,
        year_from: int = None,
        year_to: int = None,
        category: str = "sport",
        source: str = "spec_sheet",
        confidence: float = 0.7,
    ) -> tuple[int, int]:
        """
        High-level: store a BikeConfig, auto-creating manufacturer and model.

        Parses the config.name to extract manufacturer if not provided.
        Returns (bike_model_id, bike_config_id).
        """
        # Parse name for manufacturer
        if manufacturer_name is None:
            parts = config.name.split(" ", 1)
            manufacturer_name = parts[0] if parts else "Unknown"

        mfr_id = self.get_or_create_manufacturer(manufacturer_name)

        # Derive model name from config.name minus manufacturer
        model_name = config.name
        if config.name.lower().startswith(manufacturer_name.lower()):
            model_name = config.name[len(manufacturer_name) :].strip()

        # Extract headline specs
        specs = extract_headline_specs(config)

        model_id = self.create_model(
            manufacturer_id=mfr_id,
            model_name=model_name,
            model_code=model_code,
            year_from=year_from,
            year_to=year_to,
            category=category,
            **specs,
        )

        config_id = self.create_config(
            bike_model_id=model_id,
            config=config,
            source=source,
            confidence=confidence,
        )

        return model_id, config_id

    # ────────────────────────────────────────────
    # Dyno curve analysis
    # ────────────────────────────────────────────

    def get_dyno_curve(self, config_id: int) -> DynoCurve | None:
        """Load the dyno curve for a config."""
        row = self._conn.execute(
            """SELECT * FROM dyno_curves
               WHERE bike_config_id = ?
               ORDER BY confidence DESC, created_at DESC
               LIMIT 1""",
            (config_id,),
        ).fetchone()
        if row is None:
            return None
        return DynoCurve(
            rpm=np.array(json.loads(row["rpm_points"])),
            torque_nm=np.array(json.loads(row["torque_values"])),
            is_at_wheel=bool(row["is_at_wheel"]),
        )

    def compare_dyno_curves(self, config_ids: list[int]) -> dict[int, DynoCurve]:
        """Load dyno curves for multiple configs (for comparison plots)."""
        result = {}
        for cid in config_ids:
            curve = self.get_dyno_curve(cid)
            if curve is not None:
                result[cid] = curve
        return result

    # ────────────────────────────────────────────
    # Provenance
    # ────────────────────────────────────────────

    def add_provenance(
        self,
        entity_id: int,
        field_path: str,
        source_type: str,
        confidence: float,
        entity_type: str = "bike_config",
        source_url: str = None,
        notes: str = None,
    ):
        """Record provenance for a specific data field."""
        self._conn.execute(
            """INSERT INTO data_provenance
               (entity_type, entity_id, field_path, source_type,
                source_url, confidence, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                entity_type,
                entity_id,
                field_path,
                source_type,
                source_url,
                confidence,
                notes,
            ),
        )
        self._conn.commit()

    def set_validation_benchmark(
        self,
        model_id: int,
        et_s: float,
        trap_kmh: float,
        source: str,
    ):
        """Set the known quarter-mile benchmark for a bike model."""
        self._conn.execute(
            """UPDATE bike_models
               SET validation_et_s = ?, validation_trap_kmh = ?,
                   validation_source = ?, data_quality = 'track_validated',
                   updated_at = datetime('now','utc')
               WHERE id = ?""",
            (et_s, trap_kmh, source, model_id),
        )
        self._conn.commit()

    def update_data_source(self, model_id: int, data_source: str) -> bool:
        """
        Set the data_source label on a bike_model row.

        Valid values: 'verified_service_manual', 'magazine_test', 'estimated',
                      'user_submitted_pending', 'user_submitted_verified'.
        Returns True if the row was found and updated.
        """
        valid = {
            "verified_service_manual",
            "magazine_test",
            "estimated",
            "user_submitted_pending",
            "user_submitted_verified",
        }
        if data_source not in valid:
            raise ValueError(
                f"data_source must be one of {sorted(valid)}, got {data_source!r}"
            )
        cur = self._conn.execute(
            """UPDATE bike_models
               SET data_source = ?, updated_at = datetime('now','utc')
               WHERE id = ?""",
            (data_source, model_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    # ────────────────────────────────────────────
    # Counts
    # ────────────────────────────────────────────

    def count_models(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM bike_models").fetchone()
        return row["c"]

    def count_configs(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM bike_configs").fetchone()
        return row["c"]
