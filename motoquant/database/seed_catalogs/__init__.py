"""
motoquant.database.seed_catalogs
=================================
Modular catalog expansion sub-package.

Each ``seed_<name>(db)`` function builds a list of part dicts and then calls
``_create_parts_batch()`` to insert them.  The helper centralises the
try/except-per-row pattern and the ``db.parts.create()`` kwargs so individual
catalog files only need to supply the data.

Part dict schema (all keys are optional unless noted):
    category*       str   parts_categories.name
    brand*          str
    model_name*     str
    part_number     str
    specs           dict  → specifications column
    param_deltas    dict
    param_overrides dict
    param_multipliers dict
    fitment_rules   dict  (description sub-key → fitment_notes)
    price_inr       float
    availability    str   default "order"
    retailer        str
    delivery_days   int   → estimated_delivery_days
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motoquant.database.connection import MotoQuantDB

logger = logging.getLogger(__name__)


def _create_parts_batch(
    db: "MotoQuantDB",
    parts: list[dict],
    label: str = "parts",
) -> int:
    """Insert *parts* into the DB via ``db.parts.create()``.

    Each dict in *parts* is mapped to the full ``db.parts.create()`` signature.
    Failures are logged per-row and do not abort the batch.

    Args:
        db:     MotoQuantDB instance (must have ``.parts`` repo attached).
        parts:  List of part-spec dicts (see module docstring for key schema).
        label:  Human-readable name used in the summary log line.

    Returns:
        Number of parts successfully inserted.
    """
    count = 0
    for part in parts:
        try:
            db.parts.create(
                category_name=part["category"],
                brand=part["brand"],
                model_name=part["model_name"],
                part_number=part.get("part_number"),
                specifications=part.get("specs"),
                param_deltas=part.get("param_deltas"),
                param_overrides=part.get("param_overrides"),
                param_multipliers=part.get("param_multipliers"),
                fitment_rules=part.get("fitment_rules"),
                price_inr=part.get("price_inr"),
                fitment_notes=part.get("fitment_rules", {}).get("description"),
                mrp_inr=part.get("price_inr"),
                availability=part.get("availability", "order"),
                retailer=part.get("retailer"),
                estimated_delivery_days=part.get("delivery_days"),
            )
            count += 1
            logger.info("Created: %s %s", part["brand"], part["model_name"])
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to create %s %s: %s",
                part["brand"],
                part["model_name"],
                exc,
            )

    logger.info("%s: %d parts seeded", label, count)
    return count
