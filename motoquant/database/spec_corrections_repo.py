"""
MotoQuant Pro — Spec Corrections Repository
============================================
Stores user-submitted corrections to individual spec fields on bike_model rows.

Workflow
--------
    bike detail page → POST /api/specs/correct → repo.create(...)
          ↓
    (admin review)
          ↓
    repo.approve() or repo.reject()

Approving a correction does NOT automatically mutate bike_models — that
deliberate step stays in human hands to prevent crowd-sourced breakage of
calibrated baselines.  The calibrator can read approved corrections to
weight bikes by data quality; the admin CLI / dashboard applies them to
the catalog after verification.
"""

import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

# ─── Allowed field names ───────────────────────────────────────────────────
# These are the only fields a user can propose a correction for.
# Headline columns live on bike_models; physics sub-fields live on
# bike_configs JSON blobs.  We expose a curated flat list so the frontend
# can populate a dropdown and the API can validate in O(1).

VALID_CORRECTION_FIELDS: frozenset[str] = frozenset(
    {
        # bike_models headline columns
        "peak_power_hp",
        "peak_torque_nm",
        "peak_power_rpm",
        "peak_torque_rpm",
        "displacement_cc",
        "bore_mm",
        "stroke_mm",
        "compression_ratio",
        "dry_mass_kg",
        "wet_mass_kg",
        "cylinder_count",
        "wheelbase_mm",
        "seat_height_mm",
        "fuel_capacity_l",
        # bike_configs drivetrain sub-fields
        "front_sprocket",
        "rear_sprocket",
        "gear_ratios",
        # bike_configs engine sub-fields
        "redline_rpm",
        # bike_configs aero sub-fields
        "cd",
        "frontal_area_m2",
        # data quality annotation
        "data_source",
    }
)

VALID_STATUSES = ("pending", "approved", "rejected")

# Human-readable labels shown in the web form dropdown
FIELD_LABELS: dict[str, str] = {
    "peak_power_hp": "Peak Power (hp)",
    "peak_torque_nm": "Peak Torque (Nm)",
    "peak_power_rpm": "Peak Power RPM",
    "peak_torque_rpm": "Peak Torque RPM",
    "displacement_cc": "Displacement (cc)",
    "bore_mm": "Bore (mm)",
    "stroke_mm": "Stroke (mm)",
    "compression_ratio": "Compression Ratio",
    "dry_mass_kg": "Dry Mass (kg)",
    "wet_mass_kg": "Wet Mass (kg)",
    "cylinder_count": "Cylinder Count",
    "wheelbase_mm": "Wheelbase (mm)",
    "seat_height_mm": "Seat Height (mm)",
    "fuel_capacity_l": "Fuel Capacity (L)",
    "front_sprocket": "Front Sprocket (teeth)",
    "rear_sprocket": "Rear Sprocket (teeth)",
    "gear_ratios": "Gear Ratios (JSON list)",
    "redline_rpm": "Redline (rpm)",
    "cd": "Drag Coefficient (Cd)",
    "frontal_area_m2": "Frontal Area (m²)",
    "data_source": "Data Source",
}


class SpecCorrectionsRepository:
    """CRUD for the ``spec_corrections`` table."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ──────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────

    def create(
        self,
        bike_model_id: int,
        field_name: str,
        proposed_value: str,
        *,
        current_value: str | None = None,
        source_url: str | None = None,
        submitter_email: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Store a new spec correction proposal.

        Parameters
        ----------
        bike_model_id:
            ID of the bike_model row being corrected.
        field_name:
            Must be in VALID_CORRECTION_FIELDS.
        proposed_value:
            String representation of the corrected value.
        current_value:
            Snapshot of the current DB value (optional; populated by the API
            layer to create an audit trail).
        source_url:
            URL of the supporting evidence (magazine scan, service-manual PDF, etc.)
        submitter_email:
            Optional return address for follow-up questions.
        notes:
            Free-form context.

        Returns
        -------
        dict with ``id`` and ``status``.

        Raises
        ------
        ValueError
            If field_name is not in VALID_CORRECTION_FIELDS.
        """
        if field_name not in VALID_CORRECTION_FIELDS:
            raise ValueError(
                f"field_name {field_name!r} is not a correctable field. "
                f"Valid choices: {sorted(VALID_CORRECTION_FIELDS)}"
            )
        if not proposed_value or not proposed_value.strip():
            raise ValueError("proposed_value must be non-empty")

        # Verify the bike exists
        row = self._conn.execute(
            "SELECT id FROM bike_models WHERE id = ?", (bike_model_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"bike_model_id={bike_model_id} not found")

        cur = self._conn.execute(
            """INSERT INTO spec_corrections
               (bike_model_id, field_name, current_value, proposed_value,
                source_url, submitter_email, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (
                bike_model_id,
                field_name,
                (current_value or "").strip() or None,
                proposed_value.strip(),
                (source_url or "").strip() or None,
                (submitter_email or "").strip() or None,
                (notes or "").strip() or None,
            ),
        )
        self._conn.commit()

        logger.info(
            "Spec correction #%d created: bike_model_id=%d field=%s",
            cur.lastrowid,
            bike_model_id,
            field_name,
        )
        return {"id": cur.lastrowid, "status": "pending"}

    # ──────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────

    def get(self, correction_id: int) -> dict | None:
        """Return a single spec correction by ID, or None if not found."""
        row = self._conn.execute(
            "SELECT * FROM spec_corrections WHERE id = ?", (correction_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_pending(
        self,
        *,
        bike_model_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Return pending corrections, optionally filtered by bike."""
        conditions = ["status = 'pending'"]
        params: list[Any] = []
        if bike_model_id is not None:
            conditions.append("bike_model_id = ?")
            params.append(bike_model_id)
        where = " AND ".join(conditions)
        rows = self._conn.execute(
            f"""SELECT sc.*, bm.model_name,
                       m.name AS manufacturer_name
                FROM spec_corrections sc
                JOIN bike_models bm ON sc.bike_model_id = bm.id
                JOIN manufacturers m ON bm.manufacturer_id = m.id
                WHERE {where}
                ORDER BY sc.created_at DESC, sc.id DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
        return [dict(r) for r in rows]

    def list(
        self,
        *,
        status: str | None = None,
        bike_model_id: int | None = None,
        field_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Return corrections with optional filters."""
        conditions: list[str] = []
        params: list[Any] = []
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValueError(
                    f"status must be one of {VALID_STATUSES}, got {status!r}"
                )
            conditions.append("sc.status = ?")
            params.append(status)
        if bike_model_id is not None:
            conditions.append("sc.bike_model_id = ?")
            params.append(bike_model_id)
        if field_name is not None:
            conditions.append("sc.field_name = ?")
            params.append(field_name)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self._conn.execute(
            f"""SELECT sc.*, bm.model_name,
                       m.name AS manufacturer_name
                FROM spec_corrections sc
                JOIN bike_models bm ON sc.bike_model_id = bm.id
                JOIN manufacturers m ON bm.manufacturer_id = m.id
                WHERE {where}
                ORDER BY sc.created_at DESC, sc.id DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self, *, status: str | None = None) -> int:
        """Count corrections, optionally filtered by status."""
        if status is None:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM spec_corrections"
            ).fetchone()
        else:
            if status not in VALID_STATUSES:
                raise ValueError(
                    f"status must be one of {VALID_STATUSES}, got {status!r}"
                )
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM spec_corrections WHERE status = ?",
                (status,),
            ).fetchone()
        return row["c"]

    # ──────────────────────────────────────────────
    # Status transitions
    # ──────────────────────────────────────────────

    def _set_status(self, correction_id: int, new_status: str) -> bool:
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"status must be one of {VALID_STATUSES}, got {new_status!r}"
            )
        cur = self._conn.execute(
            """UPDATE spec_corrections
               SET status = ?, reviewed_at = datetime('now', 'utc')
               WHERE id = ?""",
            (new_status, correction_id),
        )
        self._conn.commit()
        found = cur.rowcount > 0
        if found:
            logger.info(
                "Spec correction #%d → %s", correction_id, new_status
            )
        return found

    def approve(self, correction_id: int) -> bool:
        """Mark a correction as approved.  Returns True if the row was found."""
        return self._set_status(correction_id, "approved")

    def reject(self, correction_id: int) -> bool:
        """Mark a correction as rejected.  Returns True if the row was found."""
        return self._set_status(correction_id, "rejected")
