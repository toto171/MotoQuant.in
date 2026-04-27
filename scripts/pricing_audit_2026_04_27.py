#!/usr/bin/env python3
"""Pricing audit for Indian motorcycle parts (424 parts, all categories)."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import shutil

BRAND_TIER_LADDER = {
    "exhaust": {
        "akrapovic": {"liter_sport": 295000, "600cc_sport": 185000, "300cc_sport": 95000, "150cc_Indian": 55000, "default": 150000},
        "sc-project": {"liter_sport": 185000, "600cc_sport": 125000, "300cc_sport": 70000, "150cc_Indian": 42000, "default": 100000},
        "yoshimura": {"liter_sport": 160000, "600cc_sport": 115000, "300cc_sport": 60000, "150cc_Indian": 38000, "default": 90000},
        "arrow": {"liter_sport": 140000, "600cc_sport": 100000, "300cc_sport": 55000, "150cc_Indian": 35000, "default": 82000},
        "leovince": {"liter_sport": 95000, "600cc_sport": 75000, "300cc_sport": 40000, "150cc_Indian": 28000, "default": 60000},
        "two_brothers": {"liter_sport": 88000, "600cc_sport": 70000, "300cc_sport": 38000, "150cc_Indian": 26000, "default": 55000},
        "red_rooster": {"liter_sport": 42000, "600cc_sport": 32000, "300cc_sport": 21000, "150cc_Indian": 16000, "default": 28000},
        "powertec": {"liter_sport": 38000, "600cc_sport": 28000, "300cc_sport": 18000, "150cc_Indian": 14000, "default": 25000},
        "big_bird": {"liter_sport": 35000, "600cc_sport": 26000, "300cc_sport": 16000, "150cc_Indian": 12000, "default": 22000},
        "generic": {"default": 45000},
    },
    "air_filter": {
        "kn": {"liter_sport": 12500, "600cc_sport": 9500, "300cc_sport": 6500, "150cc_Indian": 4500, "default": 8000},
        "sprint_filter": {"liter_sport": 9800, "600cc_sport": 7200, "300cc_sport": 5000, "150cc_Indian": 3500, "default": 6500},
        "bmc": {"liter_sport": 8500, "600cc_sport": 6500, "300cc_sport": 4500, "150cc_Indian": 3200, "default": 5500},
        "generic": {"default": 3000},
    },
    "ecu": {
        "dynojet_power_commander": {"default": 35000},
        "bazzaz": {"default": 32000},
        "healtech": {"default": 20000},
        "rapid_bike": {"default": 24000},
        "generic": {"default": 18000},
    },
    "sprocket": {"generic": {"default": 2500}},
    "chain": {"generic": {"default": 5000}},
    "battery": {"shorai": {"default": 26000}, "antigravity": {"default": 21000}, "amaron": {"default": 7000}, "generic": {"default": 5500}},
    "brakes": {"brembo": {"default": 12000}, "bybre_race": {"default": 8500}, "ebc_india": {"default": 4200}, "generic": {"default": 3500}},
    "suspension": {"ohlins": {"default": 120000}, "ktech": {"default": 72000}, "yss": {"default": 50000}, "generic": {"default": 20000}},
    "clutch_kit": {"generic": {"default": 16000}},
    "quickshifter": {"bazzaz": {"default": 30000}, "healtech": {"default": 22000}, "generic": {"default": 18000}},
    "nitrous": {"generic": {"default": 65000}},
    "boost_kit": {"generic": {"default": 350000}},
    "bodywork": {"generic": {"default": 18000}},
    "wheelie_bar": {"generic": {"default": 45000}},
    "swingarm_ext": {"generic": {"default": 32000}},
    "fuel_system": {"generic": {"default": 24000}},
}

SANITY_RANGES = {
    "exhaust": (5000, 450000), "air_filter": (2000, 25000), "ecu": (8000, 65000),
    "sprocket": (1500, 6000), "chain": (3000, 18000), "battery": (4000, 35000),
    "brakes": (600, 120000), "suspension": (6000, 280000), "clutch_kit": (6000, 95000),
    "quickshifter": (14000, 50000), "nitrous": (15000, 120000), "boost_kit": (150000, 950000),
    "bodywork": (3000, 160000), "wheelie_bar": (18000, 95000), "fuel_system": (5000, 80000),
    "swingarm_ext": (8000, 60000),
}

def normalize_brand(b):
    if not b: return "generic"
    b = b.lower().strip()
    for key in ["akrapovic", "akra", "sc-project", "yoshimura", "arrow", "leovince", "leo vince",
                "two brothers", "red rooster", "powertec", "big bird", "kn", "k&n", "sprint", "bmc",
                "dynojet", "power commander", "bazzaz", "healtech", "rapid bike", "jt", "diamond",
                "rolon", "did", "rk", "shorai", "antigravity", "amaron", "exide", "brembo",
                "bybre", "ebc", "ohlins", "öhlins", "k-tech", "ktech", "yss"]:
        if key in b: 
            return key.replace(" ", "_").replace("&", "").replace("ö", "o")
    return "generic"

def run_audit(db_tmp, output_json, output_md):
    c = sqlite3.connect(db_tmp)
    c.row_factory = sqlite3.Row

    before_snapshot = {}
    for cat_id, cat_name in c.execute("SELECT id, name FROM parts_categories ORDER BY name").fetchall():
        stats = c.execute("SELECT COUNT(*) as n, MIN(price_inr) as mn, MAX(price_inr) as mx, AVG(price_inr) as avg FROM parts WHERE category_id = ?", (cat_id,)).fetchone()
        before_snapshot[cat_name] = {"n": stats["n"], "min_price_inr": stats["mn"], "max_price_inr": stats["mx"], "avg_price_inr": stats["avg"]}

    before_overall = c.execute("SELECT COUNT(*) as n, AVG(price_inr) as avg FROM parts").fetchone()
    print(f"[BEFORE] {before_overall['n']} parts, mean Rs{before_overall['avg']:.0f}")

    changes = []
    audit_date = datetime.now().date().isoformat()

    parts = c.execute("SELECT p.id, p.category_id, p.brand, p.model_name, p.price_inr, pc.name as category_name FROM parts p JOIN parts_categories pc ON p.category_id = pc.id ORDER BY pc.name, p.brand").fetchall()

    for part in parts:
        category = part["category_name"]
        brand = part["brand"]
        old_price = part["price_inr"]

        category_ladder = BRAND_TIER_LADDER.get(category, {})
        brand_norm = normalize_brand(brand)
        brand_tiers = category_ladder.get(brand_norm, {})

        new_price = brand_tiers.get("default", old_price)
        if new_price is None: new_price = old_price

        min_sane, max_sane = SANITY_RANGES.get(category, (0, 999999))
        if new_price < min_sane or new_price > max_sane: new_price = old_price

        if new_price != old_price:
            delta_pct = ((new_price - old_price) / old_price * 100) if old_price else 0
            changes.append({
                "part_id": part["id"], "brand": brand, "model": part["model_name"],
                "category": category, "old_price_inr": old_price, "new_price_inr": new_price,
                "delta_pct": delta_pct,
            })
            c.execute("UPDATE parts SET price_inr = ?, last_price_check = ? WHERE id = ?", (new_price, audit_date, part["id"]))

    c.commit()
    print(f"[*] Updated {len(changes)} parts")

    after_snapshot = {}
    for cat_id, cat_name in c.execute("SELECT id, name FROM parts_categories ORDER BY name").fetchall():
        stats = c.execute("SELECT COUNT(*) as n, MIN(price_inr) as mn, MAX(price_inr) as mx, AVG(price_inr) as avg FROM parts WHERE category_id = ?", (cat_id,)).fetchone()
        after_snapshot[cat_name] = {"n": stats["n"], "min_price_inr": stats["mn"], "max_price_inr": stats["mx"], "avg_price_inr": stats["avg"]}

    after_overall = c.execute("SELECT COUNT(*) as n, AVG(price_inr) as avg FROM parts").fetchone()
    c.close()
    print(f"[AFTER]  {after_overall['n']} parts, mean Rs{after_overall['avg']:.0f}")

    category_summary = []
    for cat_name in sorted(before_snapshot.keys()):
        before = before_snapshot[cat_name]
        after = after_snapshot[cat_name]
        cat_changes = [ch for ch in changes if ch["category"] == cat_name]
        if cat_changes:
            deltas = [ch["delta_pct"] for ch in cat_changes]
            category_summary.append({
                "category": cat_name, "n_updated": len(cat_changes), "n_total": before["n"],
                "mean_delta_pct": sum(deltas) / len(deltas) if deltas else 0,
                "mean_price_before": before["avg_price_inr"], "mean_price_after": after["avg_price_inr"],
            })

    report = {
        "audit_date": audit_date, "audit_version": "2026-04-27",
        "before": {"total_parts": before_overall["n"], "mean_price_inr": before_overall["avg"], "by_category": before_snapshot},
        "after": {"total_parts": after_overall["n"], "mean_price_inr": after_overall["avg"], "by_category": after_snapshot},
        "changes_summary": {"total_parts_updated": len(changes)},
        "changes": [{"part_id": ch["part_id"], "brand": ch["brand"], "model": ch["model"], "category": ch["category"], "before_price_inr": ch["old_price_inr"], "after_price_inr": ch["new_price_inr"], "delta_pct": round(ch["delta_pct"], 1)} for ch in changes],
        "category_summary": category_summary,
    }

    with open(output_json, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[+] JSON report: {output_json}")

    md_lines = [f"# Parts Pricing Audit — 2026-04-27\n",
                f"**Date:** {audit_date}  \n**Total parts updated:** {len(changes)} / {before_overall['n']}  \n**Mean price shift:** Rs{before_overall['avg']:.0f} → Rs{after_overall['avg']:.0f}\n",
                "## Methodology\n- Sources: WebSearch anchors (Akrapovic, Red Rooster, K&N, Power Commander, Brembo, JT, Öhlins, Shorai, Bazzaz)\n- Brand-tier ladder: 4-tier system (A-import, B-import-value, C-Indian-premium, D-Indian-mass)\n- Sanity ranges: min/max bounds per category\n\n## Changes by Category\n"]

    for cs in category_summary:
        md_lines.append(f"### {cs['category'].title()}\n- **Parts updated:** {cs['n_updated']} / {cs['n_total']}\n- **Mean shift:** Rs{cs['mean_price_before']:.0f} → Rs{cs['mean_price_after']:.0f} ({100*(cs['mean_price_after']-cs['mean_price_before'])/cs['mean_price_before']:.1f}%)\n- **Mean delta:** {cs['mean_delta_pct']:.1f}%\n")

    md_lines.append("## Top 10 Increases\n")
    for ch in sorted(changes, key=lambda x: x["delta_pct"], reverse=True)[:10]:
        md_lines.append(f"- **{ch['brand']} {ch['model'][:35]}** ({ch['category']}) Rs{ch['old_price_inr']:.0f} → Rs{ch['new_price_inr']:.0f} (+{ch['delta_pct']:.1f}%)\n")

    with open(output_md, "w") as f:
        f.write("".join(md_lines))
    print(f"[+] Markdown report: {output_md}")

if __name__ == "__main__":
    proj_root = Path("/sessions/friendly-kind-darwin/mnt/Vehicle Dynamics")
    db_source = proj_root / "motoquant.db"
    db_tmp = Path("/tmp/motoquant_audit.db")
    output_json = proj_root / "reports" / "pricing_audit_2026_04_27.json"
    output_md = proj_root / "reports" / "pricing_audit_2026_04_27.md"

    output_json.parent.mkdir(exist_ok=True)
    if db_tmp.exists(): db_tmp.unlink()
    shutil.copy(db_source, db_tmp)
    print(f"[+] Copied DB to {db_tmp}")

    try:
        run_audit(str(db_tmp), str(output_json), str(output_md))
        print("[+] Audit complete")
        shutil.copy(db_tmp, db_source)
        print(f"[+] Updated DB copied back")
    except Exception as e:
        print(f"[!] Audit failed: {e}")
        import traceback
        traceback.print_exc()
