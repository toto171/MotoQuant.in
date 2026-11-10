"""
MotoQuant — Bike Repository
===========================
CRUD operations for manufacturers, bike models, and bike configs.
Handles BikeConfig ↔ DB conversion via the bridge module.
"""

import json
import math
import re
import sqlite3

import numpy as np

from ..config_io import dyno_from_dict
from ..models import BikeConfig, DynoCurve, EnvironmentParams
from .bridge import (
    DB_COLUMN_TO_SECTION,
    _deserialize_section,
    _serialize_section,
    compute_data_completeness,
    config_to_db_row,
    db_row_to_config,
    extract_dyno_curve,
    extract_headline_specs,
)

_YEAR_SUFFIX_RE = re.compile(
    r"\s*\((?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)?\d{2,4})?\)\s*$"
)

# Collapses an accidentally DOUBLED trailing year-range
# ("Classic 650 (2025-2026) (2025-2026)" -> "Classic 650 (2025-2026)").
# Matches only names ending in TWO ranges, so the 489 correct single-range
# names are never touched. Idempotent.
_DOUBLED_YEAR_RE = re.compile(
    r"(\((?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)?\d{2,4})?\))"
    r"\s*\((?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)?\d{2,4})?\)\s*$"
)


def _norm_model(s: str) -> str:
    """Strip a trailing ``(YYYY-YYYY)`` year-range suffix from a model name.

    Importers stamp specs like ``"1390 Super Duke R EVO (2024-2026)"`` while
    older DB rows are stored bare as ``"1390 Super Duke R EVO"``. Normalising
    both sides before comparison keeps the lenient upsert from minting phantom
    duplicates on every re-import.
    """
    if not s:
        return s
    return _YEAR_SUFFIX_RE.sub("", s.strip())


def _json_equivalent(a, b, rel_tol: float = 1e-12, abs_tol: float = 1e-12) -> bool:
    """Structural JSON equality with a float tolerance (ULP-level noise)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(
            _json_equivalent(a[k], b[k], rel_tol, abs_tol) for k in a
        )
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(
            _json_equivalent(x, y, rel_tol, abs_tol) for x, y in zip(a, b)
        )
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
    return a == b


def _param_blobs_equivalent(stored: str | None, new: str | None, db_col: str) -> bool:
    """True when two bike_configs param blobs describe the same physics.

    The stored blob is round-tripped through its dataclass first, which drops
    keys of fields that no longer exist (the bridge ignores them on read too),
    then compared to the new blob with a ULP-level float tolerance.
    """
    if stored == new:
        return True
    if stored is None or new is None:
        return False
    try:
        section = DB_COLUMN_TO_SECTION[db_col]
        normalised = json.loads(
            _serialize_section(_deserialize_section(stored, section))
        )
        return _json_equivalent(normalised, json.loads(new))
    except (KeyError, TypeError, ValueError):
        return False


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
        # The importer's year-band auto-suffix appended a range to specs that
        # already carried one, producing 16 doubled names ("X (2025-2026)
        # (2025-2026)") visible on /bikes and in the pickers. Collapse to a
        # single range here — the one chokepoint for every bike insert.
        model_name = _DOUBLED_YEAR_RE.sub(r"\1", model_name)
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

        # Pre-insert year-suffix check: the UNIQUE constraint is keyed on the
        # literal `model_name` string, so the bare-vs-suffixed variants of the
        # same bike (e.g. `"GSX-R 750"` vs `"GSX-R 750 (1985-1987)"`) do NOT
        # collide and INSERT OR IGNORE would mint a phantom row. Match in
        # Python on the normalised form first and short-circuit to the existing
        # id if any sibling row already covers this bike.
        # Keep the FULL year range in the identity so distinct generations
        # (e.g. GSX-R 1000 2001-2002 vs 2003-2004, which share the year-stripped
        # name "GSX-R 1000") are NOT collapsed, while bare-vs-suffixed and
        # NULL-model_code re-imports of the SAME bike (same manufacturer, same
        # normalised name, same year range) reuse the existing row instead of
        # minting a phantom duplicate.
        normalised_incoming = _norm_model(model_name)
        for r in self._conn.execute(
            """SELECT id, model_name FROM bike_models
               WHERE manufacturer_id = ?
                 AND COALESCE(year_from, -1) = COALESCE(?, -1)
                 AND COALESCE(year_to,   -1) = COALESCE(?, -1)""",
            (manufacturer_id, year_from, year_to),
        ).fetchall():
            if _norm_model(r["model_name"]) == normalised_incoming:
                return r["id"]

        cur = self._conn.execute(
            f"INSERT OR IGNORE INTO bike_models ({col_str}) VALUES ({placeholders})",
            vals,
        )
        self._conn.commit()

        if cur.rowcount == 0:
            # Already existed (UNIQUE constraint on manufacturer+model+code+year hit).
            # NB: rowcount is 0 for an ignored INSERT OR IGNORE; lastrowid is NOT — it
            # keeps the previous successful insert's rowid, so testing it misfires.
            # Try strict 4-key match first (matches the UNIQUE constraint exactly).
            row = self._conn.execute(
                """SELECT id FROM bike_models
                   WHERE manufacturer_id = ? AND model_name = ?
                   AND model_code IS ? AND year_from IS ?""",
                (manufacturer_id, model_name, model_code, year_from),
            ).fetchone()
            if row:
                return row["id"]
            # Lenient fallback: a row with the same (manufacturer, model_name) exists
            # but model_code/year_from differ slightly (e.g. spec says K8/2008, DB stores
            # the same bike with K8/None or different year_from). Pick the closest year.
            candidates = self._conn.execute(
                """SELECT id, model_code, year_from FROM bike_models
                   WHERE manufacturer_id = ? AND model_name = ?
                   ORDER BY (year_from IS NULL), ABS(COALESCE(year_from, 0) - ?)""",
                (manufacturer_id, model_name, year_from or 0),
            ).fetchall()
            if candidates:
                return candidates[0]["id"]
            # Truly missing — return 0 as before (caller handles)
            return 0

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
        # Serialize parameter blocks up front so identical re-imports can short-circuit.
        row_data = config_to_db_row(config)

        # ── Idempotency guard ──
        # Daily spec re-imports call this with byte-identical params. Without this
        # check every run would append a new version (+ a duplicate dyno curve),
        # bloating the DB indefinitely. If the current version already holds
        # identical params, reuse it — no new version, no duplicate dyno curve.
        _PARAM_COLS = (
            "chassis_params",
            "engine_params",
            "forced_induction_params",
            "drivetrain_params",
            "clutch_params",
            "tire_params",
            "aero_params",
            "suspension_params",
            "braking_params",
            "wheelie_params",
            "rider_params",
            "parasitic_params",
            "staging_params",
        )
        # Match ANY existing version with identical params (not only the current
        # one). This keeps re-imports fully idempotent even when the source list
        # carries two conflicting specs for the same bike (a few do, e.g. Versys
        # 650 / Yezdi Adventure) — otherwise the two specs would ping-pong the
        # "current" flag and append a new version on every pass. If a match is
        # found, make it current and reuse it instead of inserting a duplicate.
        #
        # The comparison is SEMANTIC, not byte-for-byte (October 2026 audit):
        # stored blobs that still carry keys of since-removed dataclass fields
        # (AeroParams.headwind_ms/crosswind_ms) or differ only in the last ULP
        # of a regenerated float never matched, so every `db seed` minted a
        # phantom new version of the reference bikes. And the category_tag
        # — which selects the physics CategoryProfile at runtime — was not
        # compared at all, so a taxonomy-only re-derive never persisted via
        # the import path; it is now written onto the reused row.
        for ev in self._conn.execute(
            "SELECT id, category_tag, "
            + ", ".join(_PARAM_COLS)
            + " FROM bike_configs WHERE bike_model_id = ? AND config_name = ?",
            (bike_model_id, config_name),
        ).fetchall():
            if all(_param_blobs_equivalent(ev[c], row_data[c], c) for c in _PARAM_COLS):
                self._conn.execute(
                    "UPDATE bike_configs SET is_current = (id = ?)"
                    " WHERE bike_model_id = ? AND config_name = ?",
                    (ev["id"], bike_model_id, config_name),
                )
                new_tag = row_data.get("category_tag")
                if new_tag and new_tag != ev["category_tag"]:
                    self._conn.execute(
                        "UPDATE bike_configs SET category_tag = ? WHERE id = ?",
                        (new_tag, ev["id"]),
                    )
                self._conn.commit()
                return ev["id"]

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

        cur = self._conn.execute(
            """INSERT INTO bike_configs
               (bike_model_id, version, is_current, config_name,
                chassis_params, engine_params, forced_induction_params,
                drivetrain_params, clutch_params, tire_params, aero_params,
                suspension_params, braking_params, wheelie_params,
                rider_params, parasitic_params, staging_params, category_tag,
                source, source_url, confidence, notes)
               VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                row_data.get("category_tag"),
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

    def sync_headline_specs(self, bike_model_id: int, config: BikeConfig) -> list[str]:
        """Rewrite the bike_models headline columns from ``config``.

        The headline columns (bore/stroke/CR/rpm points/wheelbase/...) are a
        searchable copy of the physics blob. Paths that rewrite only the blob
        leave them stale, so /api/bikes showed rpm/wheelbase figures the sim
        does not use (e.g. V-Strom SX 250 wheelbase 1355 vs 1440 in physics).
        Returns the names of the columns that changed (empty = already in
        sync). Idempotent.
        """
        current = self._conn.execute(
            "SELECT * FROM bike_models WHERE id = ?", (bike_model_id,)
        ).fetchone()
        if current is None:
            return []
        changed = {}
        for col, val in extract_headline_specs(config).items():
            old = current[col]
            if isinstance(val, (int, float)) and isinstance(old, (int, float)):
                same = math.isclose(float(old), float(val), rel_tol=1e-9, abs_tol=1e-9)
            else:
                same = old == val
            if not same:
                changed[col] = val
        if changed:
            assignments = ", ".join(f"{c} = ?" for c in changed)
            self._conn.execute(
                f"UPDATE bike_models SET {assignments}, "
                "updated_at = datetime('now','utc') WHERE id = ?",
                [*changed.values(), bike_model_id],
            )
            self._conn.commit()
        return sorted(changed)

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

        # The engine_params JSON blob is the single source of truth for the
        # torque curve — it is what /api/simulate (db_row_to_config), the
        # golden snapshot and every reseed/patch read and write. The
        # dyno_curves table is a derived copy written once at insert time and
        # never refreshed by reseeds, so preferring it here made CLI, chat and
        # NL sims run a stale curve (508 of 541 bikes, up to 2.28 s off the
        # API for the same bike — October 2026 audit). Fall back to the table
        # ONLY for a legacy blob that carries no curve at all.
        dyno_override = None
        engine_blob = config_row.get("engine_params")
        blob_has_curve = False
        if engine_blob:
            try:
                blob_has_curve = json.loads(engine_blob).get("dyno_curve") is not None
            except (json.JSONDecodeError, TypeError, AttributeError):
                blob_has_curve = False
        if not blob_has_curve:
            dyno_override = self._dyno_curve_from_table(config_id)

        return db_row_to_config(
            config_row,
            name=name,
            environment=environment,
            dyno_override=dyno_override,
        )

    def _dyno_curve_from_table(self, config_id: int) -> DynoCurve | None:
        """Latest dyno_curves row for a config (legacy / analysis copy)."""
        row = self._conn.execute(
            """SELECT * FROM dyno_curves
               WHERE bike_config_id = ?
               ORDER BY confidence DESC, created_at DESC, id DESC
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
        """Load the dyno curve for a config — the one its physics runs on.

        Reads the config's engine_params blob (the source of truth, see
        ``to_config``); the dyno_curves table is consulted only for a legacy
        blob without a curve.
        """
        row = self._conn.execute(
            "SELECT engine_params FROM bike_configs WHERE id = ?", (config_id,)
        ).fetchone()
        if row is not None and row["engine_params"]:
            try:
                dc = json.loads(row["engine_params"]).get("dyno_curve")
            except (json.JSONDecodeError, TypeError, AttributeError):
                dc = None
            if dc is not None:
                return dyno_from_dict(dc)
        return self._dyno_curve_from_table(config_id)

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
        """Record provenance for a specific data field.

        Idempotent: an identical record (same entity, field, source and notes)
        is not inserted twice, so re-running a seed does not grow the table.
        """
        if self._conn.execute(
            """SELECT 1 FROM data_provenance
               WHERE entity_type = ? AND entity_id = ? AND field_path = ?
                 AND source_type = ? AND source_url IS ? AND confidence = ?
                 AND notes IS ?
               LIMIT 1""",
            (
                entity_type,
                entity_id,
                field_path,
                source_type,
                source_url,
                confidence,
                notes,
            ),
        ).fetchone():
            return
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
        """Set the known quarter-mile benchmark for a bike model.

        A no-op (no updated_at churn) when the row already holds these values.
        """
        self._conn.execute(
            """UPDATE bike_models
               SET validation_et_s = ?, validation_trap_kmh = ?,
                   validation_source = ?, data_quality = 'track_validated',
                   updated_at = datetime('now','utc')
               WHERE id = ?
                 AND (validation_et_s IS NOT ? OR validation_trap_kmh IS NOT ?
                      OR validation_source IS NOT ?
                      OR data_quality IS NOT 'track_validated')""",
            (et_s, trap_kmh, source, model_id, et_s, trap_kmh, source),
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
