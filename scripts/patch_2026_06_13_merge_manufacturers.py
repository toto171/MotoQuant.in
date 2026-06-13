#!/usr/bin/env python3
"""Merge duplicate Indian / Indian Motorcycle manufacturer rows (idempotent).

The catalog held two manufacturer rows for one brand: "Indian" (the form most
known_bikes specs use -- 6 bikes) and "Indian Motorcycle" (full brand name --
1 bike). manufacturers.name has no UNIQUE, so a fresh import minted both,
splitting one make across two ids. Both the DB row count and the source specs
favour "Indian" 6:1, so "Indian" is kept as canonical (per the briefing: keep
whichever the catalog uses most, decided by row counts).

What the patch does, idempotently (rows resolved by NAME, not id; second run is
a no-op):
  1. re-point every bike_models.manufacturer_id FK from the orphan onto canonical
  2. record the orphan name as an alias on the surviving row, so a future import
     of the orphan spelling resolves back here (get_or_create_manufacturer reads
     manufacturers.aliases) instead of re-splitting
  3. canonicalise parts.fitment_rules: any manufacturers list that names the
     orphan spelling is rewritten to the canonical spelling. parts compatibility
     matches the manufacturer string EXACTLY (parts/compatibility.py), so without
     this the merged bikes would silently lose every fitment whose rule used the
     orphan spelling. This preserves behaviour exactly -- which exhaust fits which
     bike is still gated by the rule displacement/engine_config constraints.
  4. delete the now-orphaned manufacturer row.

The only FK to manufacturers is bike_models.manufacturer_id
(tire_models.manufacturer_id points at the separate tire_manufacturers table).

Usage: MOTOQUANT_DB=/path/to/motoquant.db python3 scripts/patch_2026_06_13_merge_manufacturers.py
"""

import json
import os
import sqlite3
import sys

CANONICAL_NAME = "Indian"
ORPHAN_NAME = "Indian Motorcycle"


def _mfr_id(conn, name):
    row = conn.execute(
        "SELECT id FROM manufacturers WHERE name = ?", (name,)
    ).fetchone()
    return row[0] if row else None


def _bike_count(conn, mfr_id):
    if mfr_id is None:
        return 0
    return conn.execute(
        "SELECT COUNT(*) FROM bike_models WHERE manufacturer_id = ?", (mfr_id,)
    ).fetchone()[0]


def _canonicalise_parts_rules(conn):
    """Rewrite ORPHAN_NAME -> CANONICAL_NAME in every parts.fitment_rules
    manufacturers list (nested under match{} or flat). Returns rows changed.

    parts/compatibility.py matches the bike manufacturer string EXACTLY, so once
    the merged bikes all carry CANONICAL_NAME, any rule that named ORPHAN_NAME
    would silently stop matching them. Rewriting the rules keeps every fitment.
    """
    changed = 0
    rows = conn.execute(
        "SELECT id, fitment_rules FROM parts "
        "WHERE fitment_rules IS NOT NULL AND fitment_rules LIKE ?",
        (f"%{ORPHAN_NAME}%",),
    ).fetchall()
    for pid, fr in rows:
        try:
            d = json.loads(fr)
        except (ValueError, TypeError):
            continue
        if not isinstance(d, dict):
            continue
        touched = False
        match = d.get("match") if isinstance(d.get("match"), dict) else None
        for container in (match, d):
            if not isinstance(container, dict):
                continue
            mans = container.get("manufacturers")
            if isinstance(mans, list) and ORPHAN_NAME in mans:
                replaced = [CANONICAL_NAME if m == ORPHAN_NAME else m for m in mans]
                deduped = []
                for m in replaced:
                    if m not in deduped:
                        deduped.append(m)
                if deduped != mans:
                    container["manufacturers"] = deduped
                    touched = True
        if touched:
            conn.execute(
                "UPDATE parts SET fitment_rules = ? WHERE id = ?", (json.dumps(d), pid)
            )
            changed += 1
    return changed


def merge(db_path):
    """Return the number of changes applied (0 means already-merged / no-op)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        canonical_id = _mfr_id(conn, CANONICAL_NAME)
        orphan_id = _mfr_id(conn, ORPHAN_NAME)
        print(f"DB: {db_path}")
        print("Before:")
        print(
            f"  {CANONICAL_NAME!r}: id={canonical_id} bikes={_bike_count(conn, canonical_id)}"
        )
        print(f"  {ORPHAN_NAME!r}: id={orphan_id} bikes={_bike_count(conn, orphan_id)}")
        changes = 0

        if orphan_id is None:
            print(f"  [no-op] orphan {ORPHAN_NAME!r} not present -- already merged.")
        elif canonical_id is None:
            conn.execute(
                "UPDATE manufacturers SET name = ? WHERE id = ?",
                (CANONICAL_NAME, orphan_id),
            )
            changes += 1
            print(
                f"  [rename] {ORPHAN_NAME!r} (id={orphan_id}) -> {CANONICAL_NAME!r} (canonical row absent)"
            )
        else:
            moved = conn.execute(
                "UPDATE bike_models SET manufacturer_id = ? WHERE manufacturer_id = ?",
                (canonical_id, orphan_id),
            ).rowcount
            if moved:
                changes += 1
                print(
                    f"  [repoint] {moved} bike_models row(s) {orphan_id} -> {canonical_id}"
                )

            arow = conn.execute(
                "SELECT aliases FROM manufacturers WHERE id = ?", (canonical_id,)
            ).fetchone()
            aliases = json.loads(arow[0]) if arow and arow[0] else []
            if ORPHAN_NAME not in aliases:
                aliases.append(ORPHAN_NAME)
                conn.execute(
                    "UPDATE manufacturers SET aliases = ? WHERE id = ?",
                    (json.dumps(aliases), canonical_id),
                )
                changes += 1
                print(f"  [alias] added {ORPHAN_NAME!r} to {CANONICAL_NAME!r}.aliases")

            conn.execute("DELETE FROM manufacturers WHERE id = ?", (orphan_id,))
            changes += 1
            print(f"  [delete] manufacturer id={orphan_id} ({ORPHAN_NAME!r})")

        rules_fixed = _canonicalise_parts_rules(conn)
        if rules_fixed:
            changes += rules_fixed
            print(
                f"  [parts] canonicalised {ORPHAN_NAME!r} -> {CANONICAL_NAME!r} in {rules_fixed} fitment rule(s)"
            )

        conn.commit()

        canonical_id = _mfr_id(conn, CANONICAL_NAME)
        orphan_id = _mfr_id(conn, ORPHAN_NAME)
        print("After:")
        print(
            f"  {CANONICAL_NAME!r}: id={canonical_id} bikes={_bike_count(conn, canonical_id)}"
        )
        print(f"  {ORPHAN_NAME!r}: id={orphan_id} (None == merged)")

        orphaned_bikes = conn.execute(
            "SELECT COUNT(*) FROM bike_models bm LEFT JOIN manufacturers m "
            "ON bm.manufacturer_id = m.id WHERE m.id IS NULL"
        ).fetchone()[0]
        if orphaned_bikes:
            raise SystemExit(
                f"ABORT: {orphaned_bikes} bike_models row(s) have a dangling manufacturer_id."
            )
        fk_problems = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_problems:
            raise SystemExit(f"ABORT: foreign_key_check found problems: {fk_problems}")
        leftover = conn.execute(
            "SELECT COUNT(*) FROM parts WHERE fitment_rules LIKE ?",
            (f'%"{ORPHAN_NAME}"%',),
        ).fetchone()[0]
        print(f"  parts still naming {ORPHAN_NAME!r} in a rule: {leftover}")
        print(f"Summary: {changes} change(s) applied.")
        return changes
    finally:
        conn.close()


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    if not os.path.exists(db_path):
        sys.exit(f"DB not found: {db_path}")
    merge(db_path)


if __name__ == "__main__":
    main()
