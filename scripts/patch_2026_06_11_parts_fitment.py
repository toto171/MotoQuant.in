#!/usr/bin/env python3
"""
MotoQuant Pro — Parts fitment data patch (2026-06-11 part-picker audit).

FOLDED 2026-07-04: the CONTENT fixes below (A Hayabusa manufacturer, C KTM390/
Husq401 I1, D VMAX categories, E Duke390 window, F supersport/commuter category
normalisation, H/I/K/L/M/N per-part fixes, plus the mass-multiplier fix P) are
now emitted directly by the seed sources, so a fresh seed_all() reproduces the
patched state without this script (regression-guarded by
tests/test_seed_integrity.py). NOT folded: the `excluded_bike_ids` blocklist
(pass J) references hardcoded production bike IDs that are NOT stable across
seeds (a fresh import_batch assigns different IDs), so it cannot be folded
losslessly — this script remains the production mechanism for that one fix, and
runs as a no-op against an already-patched motoquant.db.

Idempotent: every change is expressed as a target state; re-running prints
"already applied" no-ops. Run from repo root:

    python3 scripts/patch_2026_06_11_parts_fitment.py            # patches motoquant.db
    MOTOQUANT_DB=/path/to.db python3 scripts/patch_2026_06_11_parts_fitment.py

Root causes fixed (full audit in the 2026-06-11 parts session report):
  A. 9 parts seeded with manufacturer "Kawasaki" for SUZUKI Hayabusa-named
     parts (indian_retailer_depth batch) — unreachable since seeding.
  B. Bogus chain_pitch constraints copy-pasted onto exhaust/intake rules
     (530 on ZX-10R/RSV4/M1000RR/Panigale exhausts; 520 on the SHAFT-drive
     R1250GS) — unreachable.
  C. KTM 390 / Husqvarna 401 parts constrained to engine_configs ["V2"]
     (they are I1 singles) — unreachable.
  D. VMAX 1700 exhausts constrained to categories ["cruiser"] but the DB
     correctly stores the VMAX as "naked" — unreachable.
  E. Duke 390 ECU tune displacement window 390-391 vs the real 373/399cc —
     unreachable.
  F. Invalid category tokens: "supersport" (97 rules) and "commuter"
     (11 rules) are not bike_models.category values (valid set: adventure,
     cruiser, muscle, naked, scooter, sport, sport_touring, touring).
     Solo-invalid lists made 3 parts unreachable; mixed lists carry dead
     tokens. supersport->sport (deduped), commuter dropped (the
     displacement/engine windows already scope those parts).
  G. universal-tier rules carrying a match{} block THE ENGINE IGNORES:
     5 chain/sprocket parts (incl. a Hayabusa 530 rear sprocket) matched
     ALL 501 bikes, including 428-pitch commuters and belt cruisers.
     tier -> family so the chain_pitch/displacement constraints apply.
  H. Woolich "YZF-R1 4C8" flashes matched Suzuki Hayabusas (and not the
     R1: min_cc 1000 > 998!); "Hayabusa Gen1" flash matched Yamaha FZR1000;
     CBR1000RR flash matched the V4 RC213V-S and V2 VTR1000 SP2. Model-
     specific ECU flashes now pinned to their actual platform.
  I. Akrapovic "Full System Panigale" (V2 1150-1299) matched the Monster
     1200 — categories ["sport"] added.
  J. ZX-10R-NAMED bolt-ons (PCV / K&N / Showa / Ferodo / Termignoni)
     matched the supercharged Ninja H2 / H2R / Z H2 / H2 SX (998cc I4
     window) — excluded_bike_ids added (family-generic 1000cc parts
     intentionally keep matching the H2 platform).
  K. Dead "model_name" constraint key on part 122 (the engine never reads
     it) — removed; the remaining Bajaj 199-201cc window is the real rule.
  L. Exhaust coverage gap: 31 bikes (new ADV/touring/cruiser additions) had
     ZERO exhaust options. SuperTrapp Slip-On Universal (#185, literally a
     universal clamp-on, "verify fit" already in its description) widened to
     adventure/touring/cruiser/muscle; S&S Grand National + V&H Hi-Output
     V-twin systems (#68/#69) widened to touring (Indian baggers).
  M. Low Rider ST window 1860-1880 vs the DB's correct 1923cc (117ci) M-8.
  N. V&H Scout system said "Indian Motorcycle"; manufacturers table says
     "Indian" — both accepted now.
"""

import json
import os
import sqlite3
import sys

DB = os.environ.get("MOTOQUANT_DB", "motoquant.db")

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

# H2-platform 998cc bikes that ZX-10R-named parts must not match.
H2_FAMILY_BIKE_IDS = [45, 117, 299, 328, 334, 4584]

changed = 0
noop = 0


def load_rules(conn, pid):
    row = conn.execute("SELECT fitment_rules FROM parts WHERE id=?", (pid,)).fetchone()
    if row is None or not row[0]:
        return None
    return json.loads(row[0])


def save_rules(conn, pid, rules, why):
    global changed
    conn.execute(
        "UPDATE parts SET fitment_rules=? WHERE id=?",
        (json.dumps(rules), pid),
    )
    changed += 1
    print(f"  [fix] part {pid}: {why}")


def patch_match(conn, pid, why, **kv):
    """Set match keys to given values (None deletes the key)."""
    global noop
    rules = load_rules(conn, pid)
    if rules is None:
        print(f"  [skip] part {pid} missing/ruleless ({why})")
        return
    m = rules.setdefault("match", {})
    dirty = False
    for k, v in kv.items():
        if v is None:
            if k in m:
                del m[k]
                dirty = True
        elif m.get(k) != v:
            m[k] = v
            dirty = True
    if dirty:
        save_rules(conn, pid, rules, why)
    else:
        noop += 1


def patch_top(conn, pid, why, **kv):
    global noop
    rules = load_rules(conn, pid)
    if rules is None:
        print(f"  [skip] part {pid} missing/ruleless ({why})")
        return
    dirty = False
    for k, v in kv.items():
        if v is None:
            if k in rules:
                del rules[k]
                dirty = True
        elif rules.get(k) != v:
            rules[k] = v
            dirty = True
    if dirty:
        save_rules(conn, pid, rules, why)
    else:
        noop += 1


def rename_part(conn, pid, old_sub, new_sub, why):
    global changed, noop
    row = conn.execute("SELECT model_name FROM parts WHERE id=?", (pid,)).fetchone()
    if row is None:
        return
    name = row[0]
    if old_sub in name:
        conn.execute(
            "UPDATE parts SET model_name=? WHERE id=?",
            (name.replace(old_sub, new_sub), pid),
        )
        changed += 1
        print(f"  [fix] part {pid}: {why}")
    else:
        noop += 1


def main():
    global changed, noop
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print(f"Patching {DB}")

    # ── A. "Kawasaki Hayabusa" -> Suzuki (9 parts, unreachable since seed) ──
    for pid in (472, 488, 504, 517, 525, 533, 542, 547, 552):
        patch_match(
            conn,
            pid,
            "Hayabusa part: manufacturers Kawasaki -> Suzuki",
            manufacturers=["Suzuki"],
        )
        rename_part(
            conn,
            pid,
            "Kawasaki Hayabusa",
            "Suzuki Hayabusa",
            "model_name Kawasaki Hayabusa -> Suzuki Hayabusa",
        )

    # ── B. bogus chain_pitch on exhaust/intake rules ──
    # 473 Termignoni ZX-10R (530 vs real 520/525), 474 LeoVince RSV4 (530 vs 520),
    # 475 HP Corse M1000RR (530 vs 520), 476 Remus R1250GS (520 on a SHAFT bike),
    # 469 Arrow Panigale V4R (530 vs 520/525) + window 1100-1110 misses the 998 V4R.
    for pid in (473, 474, 475, 476):
        patch_match(
            conn, pid, "exhaust rule: drop irrelevant chain_pitch", chain_pitch=None
        )
    patch_match(
        conn,
        469,
        "Arrow Panigale V4/V4R: drop pitch, widen to the V4 family window",
        chain_pitch=None,
        displacement_min_cc=990,
        displacement_max_cc=1110,
    )

    # ── C. KTM 390 / Husqvarna 401 are I1 singles, not V2 ──
    for pid in (346, 356):
        patch_match(
            conn, pid, "KTM390/Husq401: engine_configs V2 -> I1", engine_configs=["I1"]
        )

    # ── D. VMAX 1700 is catalogued as 'naked' ──
    for pid in (323, 324):
        patch_match(
            conn,
            pid,
            "VMAX 1700: drop categories (DB stores it as naked)",
            categories=None,
        )

    # ── E. Duke 390 ECU: engine is 373/399cc, not 390 ──
    patch_match(
        conn,
        123,
        "Duke 390 tune: window 390-391 -> 370-400",
        displacement_min_cc=370,
        displacement_max_cc=400,
    )

    # ── M. Low Rider ST is the 117ci (1923cc) M-8 ──
    patch_match(
        conn,
        477,
        "Low Rider ST: window 1860-1880 -> 1900-1940",
        displacement_min_cc=1900,
        displacement_max_cc=1940,
    )

    # ── N. Indian Motorcycle vs 'Indian' manufacturer name ──
    patch_match(
        conn,
        478,
        "Scout system: accept manufacturer name 'Indian'",
        manufacturers=["Indian", "Indian Motorcycle"],
    )

    # ── F. invalid category tokens across the catalog ──
    print("  [pass] normalising invalid rule categories (supersport/commuter)…")
    for row in conn.execute(
        "SELECT id, fitment_rules FROM parts WHERE fitment_rules IS NOT NULL"
    ):
        rules = json.loads(row["fitment_rules"])
        m = rules.get("match") or {}
        cats = m.get("categories")
        if not cats:
            continue
        fixed = []
        for c in cats:
            if c == "supersport":
                c = "sport"
            if c in VALID_BIKE_CATEGORIES and c not in fixed:
                fixed.append(c)
        if fixed == cats:
            continue
        if fixed:
            m["categories"] = fixed
        else:
            # solo-invalid list (e.g. ["commuter"]) — the displacement /
            # engine_config window is the real constraint; drop categories.
            del m["categories"]
        save_rules(
            conn, row["id"], rules, f"categories {cats} -> {fixed or '(removed)'}"
        )

    # ── G. universal tier with ignored match{} -> family ──
    for pid in (496, 497, 500, 501, 502):
        rules = load_rules(conn, pid)
        if rules and rules.get("tier") == "universal" and rules.get("match"):
            rules["tier"] = "family"
            save_rules(
                conn,
                pid,
                rules,
                "universal-with-match -> family (constraints now enforced)",
            )
        else:
            noop += 1

    # ── H. model-specific ECU flashes pinned to their platform ──
    for pid in (46, 47):
        patch_match(
            conn,
            pid,
            "R1 4C8 flash: Yamaha I4 990-1010 sport",
            manufacturers=["Yamaha"],
            engine_configs=["I4"],
            displacement_min_cc=990,
            displacement_max_cc=1010,
            categories=["sport"],
        )
    patch_match(
        conn,
        48,
        "Hayabusa Gen1 flash: Suzuki I4 1290-1310 sport",
        manufacturers=["Suzuki"],
        engine_configs=["I4"],
        displacement_min_cc=1290,
        displacement_max_cc=1310,
        categories=["sport"],
    )
    patch_match(
        conn,
        119,
        "CBR1000RR flash: I4 only (not RC213V-S V4 / VTR1000 V2)",
        engine_configs=["I4"],
    )
    # GSX-R 1000 K5 flashes had the same loose rule (Suzuki+Yamaha 1000cc+) —
    # they matched the Hayabusa but NOT the 999cc K5 they are named for.
    for pid in (44, 45):
        patch_match(
            conn,
            pid,
            "GSX-R1000 K5 flash: Suzuki I4 985-1010 sport",
            manufacturers=["Suzuki"],
            engine_configs=["I4"],
            displacement_min_cc=985,
            displacement_max_cc=1010,
            categories=["sport"],
        )
    # 'Yamaha India' / 'Honda India' are not manufacturers-table names; the
    # RD flash kit was silently skipping the R15/CB350 class it targets.
    patch_match(
        conn,
        53,
        "RD Indian flash kit: real manufacturer names",
        manufacturers=["Bajaj", "TVS", "Hero", "Yamaha", "Honda"],
    )

    # BMC Race Air Filter claimed +2.2 hp on EVERY sport bike with no
    # displacement floor — +12% power on an R15 V4 from an air filter. The
    # small-cc classes are served by the dedicated BMC FM-Series Small-cc
    # part; the race filter is the >=300cc item.
    patch_match(conn, 88, "BMC Race Air Filter: 300cc+ floor", displacement_min_cc=300)

    # ── I. Panigale V2 full system is for the sport bodywork line ──
    patch_match(
        conn, 178, "Akrapovic Panigale V2: categories [sport]", categories=["sport"]
    )

    # ── J. ZX-10R-named parts must not match the supercharged H2 platform ──
    for pid in (473, 492, 509, 521, 530):
        patch_top(
            conn,
            pid,
            "ZX-10R-named part: exclude H2/H2R/Z H2/H2 SX",
            excluded_bike_ids=H2_FAMILY_BIKE_IDS,
        )

    # ── K. dead 'model_name' constraint key (engine never reads it) ──
    patch_match(
        conn, 122, "drop unsupported 'model_name' constraint key", model_name=None
    )

    # ── L. exhaust coverage for ADV/touring/cruiser additions ──
    patch_match(
        conn,
        185,
        "SuperTrapp universal slip-on: + adventure/touring/cruiser/muscle",
        categories=[
            "sport",
            "naked",
            "sport_touring",
            "adventure",
            "touring",
            "cruiser",
            "muscle",
        ],
    )
    for pid in (68, 69):
        patch_match(
            conn,
            pid,
            "V2 cruiser full system: + touring (baggers)",
            categories=["cruiser", "touring"],
        )

    # ── P. phantom whole-bike mass reductions on core-seed exhausts ──
    # seed.py generated param_multipliers {"chassis.dry_mass_kg": 5/(wt+5)}
    # — a ratio meant for the EXHAUST SUBSYSTEM applied to TOTAL dry mass.
    # Part 56 turned a 215 kg Hayabusa into 116.8 kg; sims/ROI have been
    # crediting full systems with ~0.8 s since the original seed (the May-1
    # CLAUDE.md ROI smoke test even recorded "Δ ET 0.832s" as a pass).
    # Replaced with honest absolute savings vs typical stock system weights
    # (litre full ~10.5-11 kg, 600 full ~10 kg, cruiser duals ~14 kg,
    # muffler-only slip-on ~4.5 kg, small-cc ~2.7-6.2 kg), consistent with
    # the deltas the rest of the catalog already uses (e.g. -3.9 kg for the
    # Termignoni ZX-10R full system).
    MASS_FIX = {
        56: -6.8,  # Racing Full System Hayabusa (wt 4.2)
        57: -7.2,  # R-77 Hayabusa Full Titanium (3.8)
        58: -6.9,  # Hayabusa Pro-Race Full System (4.1)
        59: -4.7,  # R-77 1000cc Full Stainless (5.8)
        60: -6.0,  # GP-M4 Full Titanium 1000cc (4.5)
        61: -5.3,  # M-2 Full System 1000cc (5.2)
        62: -6.6,  # CR-M Full System 1000cc (3.9)
        63: -4.8,  # R-77 600cc Full Stainless (5.2)
        64: -6.2,  # Racing 600cc Full Titanium (3.8)
        65: -2.7,  # Slip-On Sport Titanium (1.8)
        66: -2.0,  # M-1 Slip-On Stainless (2.5)
        67: -2.9,  # LV-10 Slip-On Titanium (1.6)
        68: -7.5,  # Grand National Cruiser Full (6.5, stock duals ~14)
        69: -7.3,  # Hi-Output 2-into-1 Cruiser (7.2)
        70: -2.5,  # Racing Slip-On 300cc+ (1.2)
        71: -1.8,  # Powercore IV Silencer Small-cc (0.9)
        72: -3.0,  # Indian 400cc Street Full System (3.2)
    }
    for pid, delta_kg in MASS_FIX.items():
        row = conn.execute(
            "SELECT param_deltas, param_multipliers FROM parts WHERE id=?", (pid,)
        ).fetchone()
        if row is None:
            continue
        mult = json.loads(row["param_multipliers"]) if row["param_multipliers"] else {}
        if "chassis.dry_mass_kg" not in mult:
            noop += 1
            continue
        del mult["chassis.dry_mass_kg"]
        deltas = json.loads(row["param_deltas"]) if row["param_deltas"] else {}
        deltas["chassis.dry_mass_kg"] = delta_kg
        conn.execute(
            "UPDATE parts SET param_deltas=?, param_multipliers=? WHERE id=?",
            (json.dumps(deltas), json.dumps(mult) if mult else None, pid),
        )
        changed += 1
        print(f"  [fix] part {pid}: mass multiplier -> honest delta {delta_kg} kg")

    # ── O. bike engine-config metadata corrections ──
    # RC213V-S is a 90-degree V4 (stored I4 since import); VTR1000 SP2 is a
    # 90-degree V2 (stored I2). cylinder_config is compatibility metadata —
    # physics reads the torque curve, not this string — so this is safe and
    # makes engine_configs constraints honest for both bikes.
    for bid, wrong, right in ((333, "I4", "V4"), (199, "I2", "V2")):
        row = conn.execute(
            "SELECT cylinder_config FROM bike_models WHERE id=?", (bid,)
        ).fetchone()
        if row and row[0] == wrong:
            conn.execute(
                "UPDATE bike_models SET cylinder_config=? WHERE id=?", (right, bid)
            )
            changed += 1
            print(f"  [fix] bike {bid}: cylinder_config {wrong} -> {right}")
        else:
            noop += 1
        cfg = conn.execute(
            "SELECT id, engine_params FROM bike_configs WHERE bike_model_id=? AND is_current=1",
            (bid,),
        ).fetchone()
        if cfg and cfg["engine_params"]:
            ep = json.loads(cfg["engine_params"])
            if ep.get("cylinder_config") == wrong:
                ep["cylinder_config"] = right
                conn.execute(
                    "UPDATE bike_configs SET engine_params=? WHERE id=?",
                    (json.dumps(ep), cfg["id"]),
                )
                changed += 1
                print(
                    f"  [fix] bike {bid} config blob: cylinder_config {wrong} -> {right}"
                )
            else:
                noop += 1

    conn.commit()

    # ── verification summary ──
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from motoquant.database.parts_repo import _enrich_bike_row_for_fitment
    from motoquant.parts.compatibility import is_compatible

    bikes = [dict(r) for r in conn.execute("SELECT * FROM bike_models")]
    for b in bikes:
        _enrich_bike_row_for_fitment(conn, b)
    parts = [
        dict(r)
        for r in conn.execute(
            """SELECT p.*, pc.name AS category_name FROM parts p
           JOIN parts_categories pc ON pc.id=p.category_id"""
        )
    ]
    unreachable = []
    no_exhaust = 0
    counts = []
    for b in bikes:
        n = 0
        has_ex = False
        for p in parts:
            if is_compatible(p, b)[0]:
                n += 1
                if p["category_name"] == "exhaust":
                    has_ex = True
        counts.append(n)
        if not has_ex:
            no_exhaust += 1
    matched = set()
    for p in parts:
        for b in bikes:
            if is_compatible(p, b)[0]:
                matched.add(p["id"])
                break
    unreachable = [p["id"] for p in parts if p["id"] not in matched]
    counts.sort()
    print(f"\nSummary: {changed} changes applied, {noop} already-applied no-ops")
    print(
        f"  parts-per-bike min/median/max: {counts[0]}/{counts[len(counts) // 2]}/{counts[-1]}"
    )
    print(f"  bikes with no exhaust: {no_exhaust}")
    print(f"  unreachable parts: {len(unreachable)} {unreachable}")
    conn.close()


if __name__ == "__main__":
    main()
