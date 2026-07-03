#!/usr/bin/env python3
"""
MotoQuant Pro — sprocket specifications.position patch (2026-07-03 audit).

14 of 59 sprocket parts (ids 266-274, 494, 495, 498, 499, 501) were seeded
without a ``specifications.position`` key, so the build-optimizer knapsack's
position-exclusivity (``roi._knapsack_group_key``) degraded each of them to a
singleton group — two *front* sprockets could co-select in one build.  Every
affected part carries the position verbatim in its model name
("520 Front Sprocket 13T Pro", "JT 530 Rear Sprocket 42T ...").

This script stamps ``position`` from the model name onto any sprocket part
missing it.  Idempotent: a second run reports 0 updates.  A code-side
name-regex fallback also lives in ``roi._sprocket_positions`` as
belt-and-braces for fresh seeds.

Run from repo root:

    python3 scripts/patch_2026_07_03_sprocket_position.py            # motoquant.db
    MOTOQUANT_DB=/path/to.db python3 scripts/patch_2026_07_03_sprocket_position.py
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys

_POS_RE = re.compile(r"\b(front|rear)\s+sprocket\b", re.IGNORECASE)


def patch(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.model_name, p.specifications
              FROM parts p
              JOIN parts_categories c ON p.category_id = c.id
             WHERE c.name = 'sprocket'
             ORDER BY p.id
            """
        ).fetchall()

        updated, already_ok, unresolvable = [], 0, []
        for r in rows:
            try:
                specs = json.loads(r["specifications"]) if r["specifications"] else {}
            except (ValueError, TypeError):
                specs = {}
            if not isinstance(specs, dict):
                specs = {}
            if specs.get("position") in ("front", "rear"):
                already_ok += 1
                continue
            m = _POS_RE.search(r["model_name"] or "")
            if not m:
                unresolvable.append((r["id"], r["model_name"]))
                continue
            specs["position"] = m.group(1).lower()
            conn.execute(
                "UPDATE parts SET specifications = ? WHERE id = ?",
                (json.dumps(specs), r["id"]),
            )
            updated.append((r["id"], r["model_name"], specs["position"]))
        conn.commit()
        return {
            "total_sprockets": len(rows),
            "already_ok": already_ok,
            "updated": updated,
            "unresolvable": unresolvable,
        }
    finally:
        conn.close()


def main() -> int:
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found at {db_path}", file=sys.stderr)
        return 1
    summary = patch(db_path)
    print(
        f"sprocket position patch — {db_path}\n"
        f"  total sprocket parts : {summary['total_sprockets']}\n"
        f"  already had position : {summary['already_ok']}\n"
        f"  updated              : {len(summary['updated'])}"
    )
    for pid, name, pos in summary["updated"]:
        print(f"    #{pid:<4} {name!r} -> {pos}")
    if summary["unresolvable"]:
        print("  UNRESOLVABLE (no front/rear token in name): ")
        for pid, name in summary["unresolvable"]:
            print(f"    #{pid:<4} {name!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
