#!/usr/bin/env python3
"""
Normalise parts.fitment_rules JSON to the schema motoquant/parts/compatibility.py
expects.

Two long-standing bugs in the seed catalogs caused the FitmentMatch engine to
silently reject ~125 of the 555 catalog parts (warning: "Invalid tier: model"
or "tier 'family' has no match constraints; treating as universal"):

1. tier: "model" — not a valid FitmentTier (valid: exact / family / category /
   universal). The seed scripts emitted "model" intending "exact-ish family"
   but the dataclass enum rejects it. Result: every Akrapovic/SC-Project/Arrow
   slip-on for the litre superbikes was being treated as Invalid tier and
   dropped from compatibility checks entirely.

2. Flat constraint schema — the seed scripts placed manufacturers/displacement
   bounds/engine_configs at the top level of the rules dict, but FitmentRules.
   from_dict expects them nested under "match": {...}. So even rules with the
   correct tier had no constraints surface to the matcher and got treated as
   universal-fit (the warning we saw on every is_compatible() call). Result:
   recommend was returning over-broad part lists for every bike.

Migration:
- tier: "model"  → tier: "family"  (family is correct semantic for these:
                                      they constrain manufacturer + displacement
                                      window + cylinder config)
- flat fields    → nested under "match": {...}
- model_keywords → dropped (FitmentMatch doesn't have a corresponding field;
                              the manufacturer + displacement + engine_config
                              constraints already pin the model tightly)

Idempotent: walks every parts row, only writes back if the rules actually
changed shape. Re-running on an already-migrated DB is a no-op.

Usage:
    MOTOQUANT_DB=motoquant.db python scripts/patch_2026_04_30_fitment_normalize.py
"""

import copy
import json
import os
import sqlite3
import sys

VALID_TIERS = {"exact", "family", "category", "universal"}
NESTED_FIELDS = {
    "manufacturers",
    "engine_configs",
    "displacement_min_cc",
    "displacement_max_cc",
    "categories",
    "year_min",
    "year_max",
    "chain_pitch",
    "stroke_type",
}
DROP_FIELDS = {"model_keywords"}


def normalize(rules):
    """Return (normalized_rules, change_log).

    change_log is a list of human-readable strings describing what changed.
    Empty list means nothing changed (idempotent — caller skips the UPDATE).
    """
    if not isinstance(rules, dict):
        return rules, []
    out = copy.deepcopy(rules)
    changes = []

    # 1. Fix invalid / missing tier
    tier = out.get("tier")
    if tier == "model":
        out["tier"] = "family"
        changes.append("tier: model -> family")
    elif tier not in VALID_TIERS:
        out["tier"] = "family"
        changes.append(f"tier: {tier!r} -> family")

    # 2. Drop unsupported flat fields
    for fld in list(out.keys()):
        if fld in DROP_FIELDS:
            out.pop(fld)
            changes.append(f"dropped {fld!r}")

    # 3. Move flat constraints under nested "match"
    match = out.get("match")
    if not isinstance(match, dict):
        match = {}
    moved = []
    for fld in list(out.keys()):
        if fld in NESTED_FIELDS:
            match[fld] = out.pop(fld)
            moved.append(fld)
    if moved:
        out["match"] = match
        changes.append(f"moved {len(moved)} fields into match: {sorted(moved)}")
    elif match:
        out["match"] = match

    return out, changes


def main():
    db_path = os.environ.get("MOTOQUANT_DB", "motoquant.db")
    print(f"Patching {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")

    n_total = 0
    n_changed = 0
    n_unchanged = 0
    n_malformed = 0
    sample_changes = []

    for r in conn.execute("SELECT id, brand, model_name, fitment_rules FROM parts"):
        n_total += 1
        if not r["fitment_rules"]:
            n_unchanged += 1
            continue
        try:
            rules = json.loads(r["fitment_rules"])
        except Exception as e:  # noqa: BLE001
            n_malformed += 1
            print(f"  malformed JSON on part {r['id']}: {e}")
            continue
        new_rules, change_log = normalize(rules)
        if not change_log:
            n_unchanged += 1
            continue
        conn.execute(
            "UPDATE parts SET fitment_rules = ?, updated_at = datetime('now', 'utc') WHERE id = ?",
            (json.dumps(new_rules), r["id"]),
        )
        n_changed += 1
        if len(sample_changes) < 5:
            sample_changes.append(
                {
                    "id": r["id"],
                    "brand": r["brand"],
                    "model_name": r["model_name"],
                    "changes": change_log,
                }
            )

    conn.commit()
    conn.close()

    print()
    print("=" * 60)
    print(f"Total parts:      {n_total}")
    print(f"Unchanged:        {n_unchanged}")
    print(f"Updated:          {n_changed}")
    print(f"Malformed (skip): {n_malformed}")
    print("=" * 60)
    print("\nSample transformations:")
    for s in sample_changes:
        print(f"  id={s['id']}  {s['brand']} {s['model_name']}")
        for c in s["changes"]:
            print(f"    - {c}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
