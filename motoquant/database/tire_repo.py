"""
MotoQuant — Tire Repository
===========================
CRUD for the tire library — the most sim-critical component database.

Pacejka coefficients, thermal models, and friction data are the #1 driver
of simulation accuracy. This repo enforces confidence tracking rigorously.
"""

import sqlite3

from ..models import TireParams


class TireRepository:
    """Repository for tire models and their simulation parameters."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        # Rows with id <= this watermark are never overwritten by create().
        # Set by seed_all() while it re-seeds a populated catalog, so curated
        # patch data (availability flags, prices, size notation) survives a
        # `db seed` on the shipped DB. None = no protection.
        self.protect_ids_upto: int | None = None

    # ────────────────────────────────────────────
    # Tire Manufacturers
    # ────────────────────────────────────────────

    @staticmethod
    def normalize_size_designation(size: str) -> str:
        """Collapse tire-size notation variants onto one canonical form.

        '100/90-17', '100/90R17', '100/90ZR17' and '100/90B17' all describe
        the same physical size (construction/speed-rating markers are not
        sizes). Returns e.g. '100/90/17'. Non-standard strings are returned
        lowercased/stripped so exotic drag sizes ('26x8.5R15') still compare
        stably.
        """
        import re

        s = (size or "").strip().upper()
        m = re.match(r"^(\d+)\s*/\s*(\d+)\s*(?:Z?R|B|-)\s*(\d+)$", s)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        return re.sub(r"\s+", "", s.lower())

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
        update_existing: bool = True,
        **kwargs,
    ) -> int:
        """
        Create a tire model entry.

        All Pacejka, friction, thermal, and physical params passed as kwargs.
        An existing row for the same (manufacturer, model, physical size) is
        updated in place unless ``update_existing`` is False or the row is
        protected by ``protect_ids_upto`` — then it is returned untouched.
        """
        mfr_id = self.get_or_create_manufacturer(manufacturer_name)

        cols = [
            "manufacturer_id",
            "model_name",
            "size_designation",
            "compound_type",
            "position",
        ]
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

        # ID-preserving upsert. INSERT OR REPLACE would DELETE the conflicting
        # row (on UNIQUE(manufacturer_id, model_name, size_designation)) and
        # re-INSERT with a NEW autoincrement id — which (a) trips the
        # un-cascaded FK from bike_tire_fitments once any fitment references
        # the tire (crashing a second seed_all()), and (b) orphans/renumbers
        # tires the rest of the time. Match the id-preserving pattern used by
        # bike_repo.create_model().
        #
        # July 6, 2026: the size match is NOTATION-NORMALIZED. Bike specs mix
        # bias ('100/90-17'), radial ('100/90R17') and speed-rated ('ZR')
        # notation for the same physical size; exact-string matching minted 5
        # duplicate tire rows (Zapper/GP-110/Battlax) that showed up as
        # duplicate titles in the web tire pickers. normalize_size_designation
        # collapses the notation before comparison so re-seeds converge on
        # one row per (manufacturer, model, position, physical size).
        existing = None
        norm_target = self.normalize_size_designation(size_designation)
        for cand in self._conn.execute(
            """SELECT id, size_designation FROM tire_models
               WHERE manufacturer_id = ? AND model_name = ?""",
            (mfr_id, model_name),
        ).fetchall():
            cand_size = cand["size_designation"] if hasattr(cand, "keys") else cand[1]
            if self.normalize_size_designation(cand_size) == norm_target:
                existing = cand
                break
        if existing:
            tire_id = existing["id"] if hasattr(existing, "keys") else existing[0]
            protected = (
                self.protect_ids_upto is not None and tire_id <= self.protect_ids_upto
            )
            if not update_existing or protected:
                return tire_id
            set_cols = [c for c in cols if c not in ("manufacturer_id",)]
            set_vals = [v for c, v in zip(cols, vals) if c not in ("manufacturer_id",)]
            assignments = ", ".join(f"{c} = ?" for c in set_cols)
            self._conn.execute(
                f"UPDATE tire_models SET {assignments} WHERE id = ?",
                [*set_vals, tire_id],
            )
            self._conn.commit()
            return tire_id

        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(cols)
        cur = self._conn.execute(
            f"INSERT INTO tire_models ({col_str}) VALUES ({placeholders})",
            vals,
        )
        self._conn.commit()
        return cur.lastrowid

    def get(self, tire_id: int) -> dict | None:
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
    ) -> list[dict]:
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
    ) -> TireParams | None:
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
        for field in [
            "mu_peak",
            "mu_slide",
            "load_sensitivity_k",
            "pacejka_B",
            "pacejka_C",
            "pacejka_D",
            "pacejka_E",
        ]:
            if row.get(field) is not None:
                kwargs[field] = row[field]

        # Thermal
        for field in [
            "optimal_temp_c",
            "reversion_temp_c",
            "thermal_conductivity",
            "tread_mass_kg",
            "specific_heat",
        ]:
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
    ) -> list[dict]:
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
    ) -> list[dict]:
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

    # ────────────────────────────────────────────
    # Bike-tire fitments
    # ────────────────────────────────────────────

    def link_bike_fitment(
        self,
        bike_model_id: int,
        tire_model_id: int,
        position: str,
        fitment_type: str = "oem",
        is_default: bool = False,
        notes: str = None,
    ) -> int:
        """Link a tire to a bike as an OEM / recommended / drag_prep fitment.

        `is_default=True` means "this is THE tire selected by default for this
        (bike, position)" — singular by contract. Linking a default therefore
        SUPERSEDES the previous one:

        * the previous default of the SAME fitment_type is **deleted** — a
          superseded pick is not a second OEM fitment, and both the API
          bike-detail route and `bikes --fitments` list every row by
          fitment_type (the API does not even select is_default), so demoting
          it would leave the table still asserting a tire the factory never
          fitted;
        * a default of a DIFFERENT fitment_type is demoted to is_default=0 —
          it stays a real recommendation, it just is not the default any more.

        To register a second legitimate OEM option (a market/trim variant),
        pass is_default=False; nothing is superseded then.

        Do NOT revert to INSERT OR REPLACE: its conflict target INCLUDES the
        tire id, so a different tire in the same slot appends a second
        is_default=1 row instead of superseding — and OR REPLACE renumbers
        row ids (same class of bug fixed in `create()` above). Root-cause
        history: scripts/patch_2026_08_08_fitment_integrity.py.
        """
        # Id-preserving upsert on the table's UNIQUE key.
        existing = self._conn.execute(
            """SELECT id FROM bike_tire_fitments
               WHERE bike_model_id = ? AND tire_model_id = ?
                 AND position = ? AND fitment_type = ?""",
            (bike_model_id, tire_model_id, position, fitment_type),
        ).fetchone()
        if existing is not None:
            fitment_id = existing["id"] if hasattr(existing, "keys") else existing[0]
            self._conn.execute(
                "UPDATE bike_tire_fitments SET is_default = ?, notes = ? WHERE id = ?",
                (1 if is_default else 0, notes, fitment_id),
            )
        else:
            cur = self._conn.execute(
                """INSERT INTO bike_tire_fitments
                   (bike_model_id, tire_model_id, position, fitment_type,
                    is_default, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    bike_model_id,
                    tire_model_id,
                    position,
                    fitment_type,
                    1 if is_default else 0,
                    notes,
                ),
            )
            fitment_id = cur.lastrowid

        if is_default:
            # Supersede the previous same-type default for this slot.
            self._conn.execute(
                """DELETE FROM bike_tire_fitments
                   WHERE bike_model_id = ? AND position = ? AND fitment_type = ?
                     AND is_default = 1 AND id != ?""",
                (bike_model_id, position, fitment_type, fitment_id),
            )
            # Keep "one default per (bike, position)" true across types.
            self._conn.execute(
                """UPDATE bike_tire_fitments SET is_default = 0
                   WHERE bike_model_id = ? AND position = ?
                     AND is_default = 1 AND id != ?""",
                (bike_model_id, position, fitment_id),
            )

        self._conn.commit()
        return fitment_id

    def tire_to_params(self, tire_model_id: int) -> TireParams | None:
        """
        Convert a tire_model DB row to a TireParams object ready for simulation.

        Fetches the tire by ID, builds a TireParams using DB values.
        For missing fields (rolling_radius_m is nullable), computes from size_designation
        or falls back to base defaults.

        Returns None if tire not found.
        """
        row = self.get(tire_model_id)
        if row is None:
            return None

        # Compute rolling radius if missing
        rolling_radius_m = row.get("rolling_radius_m")
        if rolling_radius_m is None:
            # Compute from size_designation: e.g. "190/55ZR17"
            # width_mm, aspect_ratio, rim_diameter_inch
            # rolling_radius_m = (rim_in * 25.4/2 + width_mm * aspect) / 1000
            try:
                width_mm = row.get("width_mm")
                aspect_ratio = row.get("aspect_ratio")
                rim_in = row.get("rim_diameter_inch")

                if width_mm and aspect_ratio and rim_in:
                    # rolling_radius_m = (rim_in * 25.4/2 + width_mm * aspect/100) / 1000
                    rim_radius_mm = rim_in * 25.4 / 2
                    sidewall_mm = width_mm * (aspect_ratio / 100.0)
                    rolling_radius_m = (rim_radius_mm + sidewall_mm) / 1000.0
            except (TypeError, ZeroDivisionError):
                rolling_radius_m = None

        # Build kwargs for TireParams, all fields optional
        kwargs = {}

        # Rear-focused fields (since drag is rear-biased)
        kwargs["rear_model"] = f"{row['manufacturer_name']} {row['model_name']}"
        kwargs["rear_size"] = row["size_designation"]
        if rolling_radius_m:
            kwargs["rear_rolling_radius_m"] = rolling_radius_m

        # Pressure: prefer drag_pressure_psi, then recommended_psi
        if row.get("drag_pressure_psi"):
            kwargs["rear_pressure_psi"] = row["drag_pressure_psi"]
        elif row.get("recommended_psi"):
            kwargs["rear_pressure_psi"] = row["recommended_psi"]

        # Mass and inertia
        if row.get("mass_kg"):
            kwargs["rear_mass_kg"] = row["mass_kg"]
        if row.get("inertia_kgm2"):
            kwargs["rear_inertia_kgm2"] = row["inertia_kgm2"]

        # Friction and Pacejka
        for field in [
            "mu_peak",
            "mu_slide",
            "load_sensitivity_k",
            "pacejka_B",
            "pacejka_C",
            "pacejka_D",
            "pacejka_E",
        ]:
            if row.get(field) is not None:
                kwargs[field] = row[field]

        # Thermal
        for field in [
            "optimal_temp_c",
            "reversion_temp_c",
            "thermal_conductivity",
            "tread_mass_kg",
        ]:
            if row.get(field) is not None:
                kwargs[field] = row[field]

        # Special mapping for specific_heat
        if row.get("specific_heat") is not None:
            kwargs["specific_heat_rubber"] = row["specific_heat"]

        # Rolling resistance
        for field in ["crr_base", "crr_speed_coeff", "crr_temp_coeff"]:
            if row.get(field) is not None:
                kwargs[field] = row[field]

        # Growth and construction
        if row.get("growth_coeff") is not None:
            kwargs["growth_coeff"] = row["growth_coeff"]
        if row.get("construction"):
            kwargs["tire_construction"] = row["construction"]

        return TireParams(**kwargs)

    def get_bike_fitments(
        self, bike_model_id: int, position: str = None, fitment_type: str = None
    ) -> list:
        """Get all tire fitments for a bike model."""
        sql = """
            SELECT btf.*, tm.manufacturer_id, tm.model_name, tm.compound_type,
                   tm.size_designation, tm.mu_peak, tm.price_inr,
                   tmfr.name as tire_manufacturer
            FROM bike_tire_fitments btf
            JOIN tire_models tm ON btf.tire_model_id = tm.id
            JOIN tire_manufacturers tmfr ON tm.manufacturer_id = tmfr.id
            WHERE btf.bike_model_id = ?
        """
        params = [bike_model_id]
        if position:
            sql += " AND btf.position = ?"
            params.append(position)
        if fitment_type:
            sql += " AND btf.fitment_type = ?"
            params.append(fitment_type)
        sql += " ORDER BY btf.fitment_type, btf.position"
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
