#!/usr/bin/env python3
"""
MotoQuant Pro — residual seed-drift cleanup (2026-07-04).

Companion to the A3-15 "fold patch fixes into seed sources" pass. The seed
SOURCES (motoquant/database/seed.py + seed_catalogs/*.py) now emit clean
fitment_rules, so a fresh ``seed_all()`` no longer produces the invalid
``supersport`` / ``commuter`` category tokens that ``patch_2026_06_11`` (pass F)
normalises. A handful of rows in an already-deployed ``motoquant.db`` may still
carry those stale tokens if that DB predates the fold and never had the June-11
patch re-run against it (the task flagged prod ids 174/186/190/194/195 with
``supersport`` and 329 with ``commuter``).

This script cleans those residual rows so a live DB matches what a fresh seed
now produces. It reproduces exactly the F-pass normalisation:

    * ``supersport`` -> ``sport`` (de-duplicated)
    * ``commuter`` dropped (not a bike_models.category; the displacement /
      engine-config window is the real constraint)
    * if the categories list becomes empty, the ``categories`` key is removed

It is CONTENT-based (scans every part for the stale tokens) rather than
ID-based, so it is robust to the part-ID reshuffling that happens between
independently-seeded databases. Idempotent: a second run reports 0 updates.
Safe to run twice.

Run from repo root (I — the operator — run this against motoquant.db; the
authoring session only tests it against a /tmp copy):

    python3 scripts/patch_2026_07_04_residual_seed_drift.py            # motoquant.db
    MOTOQUANT_DB=/path/to.db python3 scripts/patch_2026_07_04_residual_seed_drift.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys

# The 8 valid bike_models.category values. supersport/commuter are NOT here.
VALID_BIKE_CATEGORIES = {
    "adventure",
    "cruiser",
    "muscle",
    "naked",
    "scooter",
    "sport",
    "sport_touring",
    "touring",
}


def clean_categories(cats: list) -> list:
    """Apply the June-11 F-pass normalisation to one categories list.

    Returns the cleaned list (possibly empty). ``supersport`` -> ``sport``
    (de-duped); every token not in VALID_BIKE_CATEGORIES (e.g. ``commuter``)
    is dropped.
    """
    out: list[str] = []
    for c in cats:
        if c == "supersport":
            c = "sport"
        if c in VALID_BIKE_CATEGORIES and c not in out:
            out.append(c)
    return out


def normalize_rules(rules: dict) -> tuple[dict, bool]:
    """Return (rules, changed). Only the match.categories list is touched."""
    if not isinstance(rules, dict):
        return rules, False
    match = rules.get("match")
    if not isinstance(match, dict):
        return rules, False
    cats = match.get("categories")
    if not cats:
        return rules, False
    fixed = clean_categories(cats)
    if fixed == cats:
        return rules, False
    if fixed:
        match["categories"] = fixed
    else:
        # solo-invalid list (e.g. ["commuter"]) — drop the categories key; the
        # displacement / engine-config window remains the real constraint.
        del match["categories"]
    return rules, True


def main() -> int:
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found at {db_path}", file=sys.stderr)
        return 1
    print(f"Cleaning residual seed drift in {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # WAL is rejected on some mounted filesystems — mirror the other patches.
    try:
        conn.execute("PRAGMA journal_mode=DELETE")
    except sqlite3.DatabaseError:
        pass

    n_total = 0
    n_changed = 0
    changes = []
    for r in conn.execute(
        "SELECT id, brand, model_name, fitment_rules FROM parts "
        "WHERE fitment_rules IS NOT NULL"
    ):
        n_total += 1
        try:
            rules = json.loads(r["fitment_rules"])
        except (ValueError, TypeError):
            continue
        cats_before = (rules.get("match") or {}).get("categories")
        new_rules, changed = normalize_rules(rules)
        if not changed:
            continue
        conn.execute(
            "UPDATE parts SET fitment_rules = ? WHERE id = ?",
            (json.dumps(new_rules), r["id"]),
        )
        n_changed += 1
        cats_after = (new_rules.get("match") or {}).get("categories")
        changes.append((r["id"], r["brand"], r["model_name"], cats_before, cats_after))

    conn.commit()
    conn.close()

    print("=" * 60)
    print(f"Parts scanned : {n_total}")
    print(f"Rows cleaned  : {n_changed}")
    print("=" * 60)
    for pid, brand, name, before, after in changes:
        print(f"  #{pid} [{brand}] {name}: {before} -> {after or '(removed)'}")
    if n_changed == 0:
        print("No residual supersport/commuter drift found — already clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
