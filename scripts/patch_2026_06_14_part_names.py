#!/usr/bin/env python3
"""Idempotent migration: strip leading brand prefix from parts.model_name.

Fixes the duplicate-manufacturer display bug (UI renders ``{brand} {model_name}``
and many rows stored the brand inside model_name → "Akrapovic Akrapovic ..."). Uses
the exact same normalize_model_name helper the seed insert path now calls, so a
fresh seed and this migration converge. Safe to re-run (second run = 0 changes).

    MOTOQUANT_DB=motoquant.db python3 scripts/patch_2026_06_14_part_names.py
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from motoquant.database.parts_repo import normalize_model_name  # noqa: E402


def main() -> int:
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, brand, model_name FROM parts").fetchall()
    changed = 0
    for r in rows:
        new = normalize_model_name(r["brand"], r["model_name"])
        if new != (r["model_name"] or ""):
            conn.execute(
                "UPDATE parts SET model_name = ? WHERE id = ?", (new, r["id"])
            )
            changed += 1
    conn.commit()
    # Report residual duplicates (should be 0 after a run)
    rows2 = conn.execute("SELECT brand, model_name FROM parts").fetchall()
    resid = sum(
        1
        for r in rows2
        if r["brand"]
        and r["model_name"]
        and r["model_name"].strip().lower().startswith(r["brand"].strip().lower())
        and normalize_model_name(r["brand"], r["model_name"]) != r["model_name"].strip()
    )
    conn.close()
    print(f"part-name normalize: {changed} rows changed, {len(rows)} scanned")
    print(f"  residual brand-prefixed names needing strip: {resid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
