"""
MotoQuant Pro — Bike Suggestions Repository
===========================================
Stores user-submitted bike addition requests from the web form at
``motoquant.in/bikes`` (and the matching ``POST /api/bikes/suggest`` endpoint).

Workflow
--------
    web form → POST /api/bikes/suggest → repo.create(...)
        ↓
    (human review later)
        ↓
    repo.mark_reviewed() / mark_added() / mark_rejected()

Plausibility-check bounds roughly match the scraper validator envelope
(``motoquant/scraper/validator.py``). Out-of-bounds submissions are still
stored — we set ``flagged_out_of_bounds = 1`` so they can be triaged
instead of silently dropped.
"""

import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

# Loose physical bounds for plausibility. Anything outside these is stored but
# flagged. These are intentionally wider than the scraper validator since user
# submissions may be for obscure or custom bikes.
BOUNDS = {
    "year": (1960, 2099),
    "displacement_cc": (50.0, 3500.0),
    "peak_power_hp": (1.0, 450.0),
    "dry_mass_kg": (40.0, 500.0),
}

VALID_STATUSES = ("pending", "reviewed", "added", "rejected")


def _out_of_bounds(field: str, value: float | int | None) -> bool:
    """Return True if ``value`` is outside the plausible range for ``field``."""
    if value is None:
        return False
    lo, hi = BOUNDS[field]
    return not (lo <= value <= hi)


def check_plausibility(
    year: int | None,
    displacement_cc: float | None,
    peak_power_hp: float | None,
    dry_mass_kg: float | None,
) -> list[str]:
    """Return a list of plausibility-violation messages (empty if all OK)."""
    issues: list[str] = []
    pairs = [
        ("year", year),
        ("displacement_cc", displacement_cc),
        ("peak_power_hp", peak_power_hp),
        ("dry_mass_kg", dry_mass_kg),
    ]
    for name, val in pairs:
        if _out_of_bounds(name, val):
            lo, hi = BOUNDS[name]
            issues.append(f"{name}={val} out of bounds [{lo}, {hi}]")
    return issues


class BikeSuggestionsRepository:
    """CRUD for the ``bike_suggestions`` table."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ──────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────

    def create(
        self,
        make: str,
        model: str,
        *,
        year: int | None = None,
        displacement_cc: float | None = None,
        peak_power_hp: float | None = None,
        dry_mass_kg: float | None = None,
        category: str | None = None,
        notes: str | None = None,
        submitter_email: str | None = None,
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Store a new bike suggestion.

        Returns a dict: ``{id, flagged_out_of_bounds, issues}``.
        ``issues`` is a list of plausibility-violation messages (empty on clean
        submissions). Out-of-bounds rows are still stored, but flagged.
        """
        if not make or not make.strip():
            raise ValueError("make must be non-empty")
        if not model or not model.strip():
            raise ValueError("model must be non-empty")

        issues = check_plausibility(
            year=year,
            displacement_cc=displacement_cc,
            peak_power_hp=peak_power_hp,
            dry_mass_kg=dry_mass_kg,
        )
        flagged = 1 if issues else 0

        cur = self._conn.execute(
            """INSERT INTO bike_suggestions
               (make, model, year, displacement_cc, peak_power_hp, dry_mass_kg,
                category, notes, submitter_email, source_url,
                flagged_out_of_bounds, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (
                make.strip(),
                model.strip(),
                year,
                displacement_cc,
                peak_power_hp,
                dry_mass_kg,
                (category or "").strip() or None,
                (notes or "").strip() or None,
                (submitter_email or "").strip() or None,
                (source_url or "").strip() or None,
                flagged,
            ),
        )
        self._conn.commit()

        if issues:
            logger.info(
                "Bike suggestion stored with plausibility flags: %s %s -- %s",
                make,
                model,
                "; ".join(issues),
            )

        return {
            "id": cur.lastrowid,
            "flagged_out_of_bounds": bool(flagged),
            "issues": issues,
        }

    # ──────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────

    def get(self, suggestion_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM bike_suggestions WHERE id = ?", (suggestion_id,)
        ).fetchone()
        return dict(row) if row else None

    def list(
        self,
        *,
        status: str | None = None,
        flagged_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """List suggestions, newest first."""
        conditions = []
        params: list[Any] = []
        if status:
            if status not in VALID_STATUSES:
                raise ValueError(
                    f"status must be one of {VALID_STATUSES}, got {status!r}"
                )
            conditions.append("status = ?")
            params.append(status)
        if flagged_only:
            conditions.append("flagged_out_of_bounds = 1")

        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self._conn.execute(
            f"""SELECT * FROM bike_suggestions
                WHERE {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self, *, status: str | None = None) -> int:
        if status is None:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM bike_suggestions"
            ).fetchone()
        else:
            if status not in VALID_STATUSES:
                raise ValueError(
                    f"status must be one of {VALID_STATUSES}, got {status!r}"
                )
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM bike_suggestions WHERE status = ?",
                (status,),
            ).fetchone()
        return row["c"]

    # ──────────────────────────────────────────────
    # Status transitions
    # ──────────────────────────────────────────────

    def _set_status(self, suggestion_id: int, new_status: str) -> bool:
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"status must be one of {VALID_STATUSES}, got {new_status!r}"
            )
        cur = self._conn.execute(
            """UPDATE bike_suggestions
               SET status = ?, reviewed_at = datetime('now', 'utc')
               WHERE id = ?""",
            (new_status, suggestion_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def mark_reviewed(self, suggestion_id: int) -> bool:
        return self._set_status(suggestion_id, "reviewed")

    def mark_added(self, suggestion_id: int) -> bool:
        return self._set_status(suggestion_id, "added")

    def mark_rejected(self, suggestion_id: int) -> bool:
        return self._set_status(suggestion_id, "rejected")
