"""
MotoQuant Pro — Drag Essentials Catalog (July 2026)
====================================================
Seeds the three most-requested real-world drag-prep part families that the
catalog was missing entirely, plus a V2-cruiser nitrous family and verified
Trask M8 turbo kits.

THREE NEW PART CATEGORIES (idempotently inserted into parts_categories by
this module — they are NOT in schema.SEED_PARTS_CATEGORIES, so a fresh
seed_all() must call seed_drag_essentials() to get them):

1. lowering_kit  (6 parts) — the #1 real-world drag mod. Lowering the bike
   drops the combined CoG, suppressing wheelie and letting the rider use
   more throttle off the line. Products: Soupy's Performance adjustable
   links (Hayabusa / ZX-14 / ZX-4RR), Brock's Performance front-end
   lowering straps. Physics: negative chassis.cog_height_mm delta
   (-15 to -55 mm on a 550 mm default CoG).

2. air_shifter   (4 parts) — the Pro Street standard. CO2/air-actuated
   shift cylinder + ignition kill gives full-throttle clutchless shifts
   faster than any strain-gauge quickshifter. Products: MPS Racing (3
   kits incl. the RPM-window automatic) + Schnitz Racing. Physics:
   drivetrain.air_shifter=True + absolute total_shift_time_ms override
   (40-55 ms vs the 100 ms stock default) via param_overrides.

3. lockup_clutch (3 parts) — MTC Engineering multi-stage lock-up clutches
   (Hayabusa Gen1/Gen2, ZX-14). Centrifugal arms add clamp force with RPM
   so the clutch can be soft at launch and fully locked down-track.
   Physics: clutch.clutch_type -> "multistage" (the ClutchModel
   CLUTCH_MULTISTAGE branch adds centrifugal clamp F_cent ~ (rpm -
   engage_rpm)^2 on top of spring preload) + heavier springs via
   param_multipliers on clutch.spring_preload_n.
   NOTE (honest gap): MTC also lists ZX-12R (00-05) and vintage GS1100/
   GS1150 applications, but neither platform is in the bike catalog yet,
   so those SKUs are deliberately NOT seeded (parts must stay reachable).

PLUS, in existing categories:

4. nitrous (4 parts) — V2-CRUISER family closing the "no nitrous for
   Harley M8 / Indian Thunderstroke-PowerPlus" gap: NX (Nitrous Express)
   V-Twin Piranha wet kit, NX Softail dry plate kit, DynoTune Harley/
   Victory EFI single- and twin-bottle systems.

5. boost_kit (2 parts) — verified Harley M8-specific Trask turbo kits
   (Assault + Tornado). Complements the widened generic Trask V-twin kit
   in drag_specific.py (displacement_max_cc 1750 -> 1950 so M8 114/117 at
   1868/1923 cc actually match).

SUB-500cc DRAG HARDWARE — DATA GAP (unchanged from Apr 30, 2026):
Research again found NO verifiable bolt-on wheelie bars or swingarm
extensions for the Apache RR 310 / Duke 390 / RE 650 class. Indian
drag builds in this class use one-off local fabrication with no public
product pages or prices. Per CLAUDE.md hygiene ("honest physics
validation > apparent accuracy") nothing is invented here; close this
via the Pune/Narhe partnership round.

PHYSICS NOTE (measured on K5/Hayabusa references, July 2026)
------------------------------------------------------------
- air_shifter parts are LIVE: total_shift_time_ms 45 ms moves K5 ET
  -0.054 s through the production bridge + RK4 path.
- lockup_clutch parts are currently ET-NEUTRAL: physics.py's slip phase
  only special-cases CLUTCH_SLIDER; "multistage" falls through to the
  generic clutch-capacity cap, which does not bind on stock-power bikes
  (the documented "clutch-type dispatch" dead-knob). The seeded params
  are the physically correct ones and go live when that dispatch is
  wired.
- lowering_kit CoG deltas are physically correct but currently score
  slightly POSITIVE ET (less load transfer, and the wheelie limit is
  not the binding constraint at fixed launch RPM — raising the Hayabusa
  CoG +55 mm "gains" -0.11 s). Real-world lowering pays off by allowing
  harder launches; until the wheelie constraint binds, ROI tooling will
  rank these parts negative. Same applies to the two pre-existing
  lowering parts in premium_universal.py. Do NOT fake a negative delta
  here — fix the physics, not the data.

Sourcing / pricing
------------------
All products verified against live retailer/manufacturer listings
(July 2026): soupysperformance.com, brocksperformance.com,
mpsracing.com, store.schnitzracing.com, mtceng.com, dynotunenitrous.com,
traskperformance.com, Summit/Amazon listings. USD MSRP converted to
landed INR via the documented import formula
(usd * 84 * 1.30 duty * 1.18 GST + 1500 freight); entries whose USD
price is an interpolation between verified sibling SKUs carry
"price_estimated": True in specs. Accuracy +/-15%.
"""

from motoquant.database.seed_catalogs import _create_parts_batch

# New categories introduced by this module. Mirrors the
# (name, display_name, affects_params) tuple shape of
# schema.SEED_PARTS_CATEGORIES / MotoQuantDB._seed_parts_categories.
NEW_CATEGORIES = [
    ("lowering_kit", "Lowering Kit", '["chassis", "suspension"]'),
    ("air_shifter", "Air Shifter", '["drivetrain"]'),
    ("lockup_clutch", "Lockup Clutch", '["clutch", "drivetrain"]'),
]

# Manufacturer aliases: the live DB canonicalised "Indian Motorcycle" ->
# "Indian" (2026-06-13 merge patch), but fresh seeds from older specs may
# still create "Indian Motorcycle". Fitment matching is an exact
# case-insensitive set-membership test, so listing both is safe and covers
# both DB states.
_INDIAN_ALIASES = ["Indian", "Indian Motorcycle"]


def _ensure_categories(db) -> int:
    """Idempotently insert this module's new parts categories."""
    created = 0
    for name, display, affects in NEW_CATEGORIES:
        cur = db._conn.execute(
            """INSERT OR IGNORE INTO parts_categories (name, display_name, affects_params)
               VALUES (?, ?, ?)""",
            (name, display, affects),
        )
        created += cur.rowcount if cur.rowcount > 0 else 0
    db._conn.commit()
    return created


def seed_drag_essentials(db) -> int:
    """
    Seeds lowering kits, air shifters, lockup clutches, V2-cruiser nitrous
    and Trask M8 turbo kits. Returns count of parts successfully created.
    """
    _ensure_categories(db)

    parts = []

    # ══════════════════════════════════════════════════════════════
    # LOWERING KITS (6 parts) — NEW CATEGORY
    # ══════════════════════════════════════════════════════════════
    parts.extend(
        [
            {
                "category": "lowering_kit",
                "brand": "Soupy's Performance",
                "model_name": "Adjustable Lowering Links — Hayabusa (99-2025)",
                "part_number": "SOUPY-LL-BUSA",
                "specs": {
                    "type": "adjustable_links",
                    "max_drop_inches": 4.0,
                    "material": "CNC aluminum / stainless hardware",
                    "msrp_usd": 199,
                },
                "param_deltas": {
                    # Rear lowered ~2" at a typical drag setting; combined
                    # bike+rider CoG drops ~40 mm from the 550 mm default.
                    "chassis.cog_height_mm": -40.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1280,
                        "displacement_max_cc": 1360,
                        "categories": ["sport"],
                    },
                    "description": (
                        "Soupy's fully adjustable rear lowering links; "
                        "Hayabusa Gen 1/2/3 (1299-1340cc); stock to -4in "
                        "rear drop for wheelie suppression off the line."
                    ),
                },
                "price_inr": 27000,
                "availability": "import_only",
                "retailer": "Soupy's Performance (USA)",
                "delivery_days": 21,
            },
            {
                "category": "lowering_kit",
                "brand": "Soupy's Performance",
                "model_name": "Adjustable Lowering Links — ZX-14 / ZZR1400",
                "part_number": "SOUPY-LL-ZX14",
                "specs": {
                    "type": "adjustable_links",
                    "max_drop_inches": 4.0,
                    "material": "CNC aluminum / stainless hardware",
                    "msrp_usd": 127,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -40.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1350,
                        "displacement_max_cc": 1450,
                        "categories": ["sport"],
                    },
                    "description": (
                        "Soupy's adjustable rear lowering links; Kawasaki "
                        "ZX-14/ZX-14R/ZZR1400; stock to -4in rear drop."
                    ),
                },
                "price_inr": 17900,
                "availability": "import_only",
                "retailer": "Soupy's Performance (USA)",
                "delivery_days": 21,
            },
            {
                "category": "lowering_kit",
                "brand": "Soupy's Performance",
                "model_name": "Adjustable Lowering Links — ZX-4R / ZX-4RR",
                "part_number": "SOUPY-LL-ZX4RR",
                "specs": {
                    "type": "adjustable_links",
                    "max_drop_inches": 1.5,
                    "material": "CNC aluminum / stainless hardware",
                    "msrp_usd": 135,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -20.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 395,
                        "displacement_max_cc": 405,
                        "categories": ["sport"],
                    },
                    "description": (
                        "Soupy's adjustable lowering links kit, up to 1.5in "
                        "lower; Kawasaki ZX-4R/ZX-4RR 399cc I4."
                    ),
                },
                "price_inr": 18900,
                "availability": "import_only",
                "retailer": "Soupy's Performance (USA)",
                "delivery_days": 21,
            },
            {
                "category": "lowering_kit",
                "brand": "Brock's Performance",
                "model_name": "Front End Lowering Strap",
                "part_number": "BP-930242",
                "specs": {
                    "type": "front_strap",
                    "webbing_rating_lbs": 1800,
                    "msrp_usd": 44.99,
                },
                "param_deltas": {
                    # Preloads the fork ~1-1.5" — modest CoG drop, main gain
                    # is anti-'hammer' consistency on launch.
                    "chassis.cog_height_mm": -15.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 740,
                        "displacement_max_cc": 1360,
                        "categories": ["sport"],
                    },
                    "description": (
                        "Brock's front-end lowering strap (SKU 930242); "
                        "Gen 1 Hayabusa, 01-02 GSX-R1000, GSX-R750/1100 "
                        "with conventional brake mounts; preloads the fork "
                        "to stop launch 'hammer' and level the chassis."
                    ),
                },
                "price_inr": 7300,
                "availability": "import_only",
                "retailer": "Brock's Performance (USA)",
                "delivery_days": 21,
            },
            {
                "category": "lowering_kit",
                "brand": "Brock's Performance",
                "model_name": "Radial-Mount Front End Lowering Kit",
                "part_number": "BP-STRAP-RADIAL",
                "specs": {
                    "type": "front_strap_bracket_kit",
                    "webbing_rating_lbs": 1800,
                    "msrp_usd": 130,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -15.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki", "Kawasaki", "Honda"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 950,
                        "displacement_max_cc": 1450,
                        "categories": ["sport"],
                    },
                    "description": (
                        "Brock's strap + radial-caliper bracket kit; "
                        "Hayabusa 08+, GSX-R1000, ZX-10R/ZX-14R, CBR1000RR "
                        "(radial-mount front brakes)."
                    ),
                },
                "price_inr": 18200,
                "availability": "import_only",
                "retailer": "Brock's Performance (USA)",
                "delivery_days": 21,
            },
            {
                "category": "lowering_kit",
                "brand": "Soupy's Performance",
                "model_name": "Complete Lowering Kit Front & Rear — Hayabusa",
                "part_number": "SOUPY-KIT-BUSA-FR",
                "specs": {
                    "type": "front_rear_kit",
                    "max_drop_inches": 4.0,
                    "msrp_usd": 250,
                    "price_estimated": True,
                },
                "param_deltas": {
                    # Front + rear dropped together at a full drag setting.
                    "chassis.cog_height_mm": -55.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1280,
                        "displacement_max_cc": 1360,
                        "categories": ["sport"],
                    },
                    "description": (
                        "Soupy's front + rear lowering kit for Hayabusa "
                        "1999-2025; the full drag stance — biggest CoG "
                        "drop in the catalog."
                    ),
                },
                "price_inr": 33700,
                "availability": "import_only",
                "retailer": "Soupy's Performance (USA)",
                "delivery_days": 21,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # AIR SHIFTERS (4 parts) — NEW CATEGORY
    # ══════════════════════════════════════════════════════════════
    parts.extend(
        [
            {
                "category": "air_shifter",
                "brand": "MPS Racing",
                "model_name": "Sport Bike Air Shifter with Engine Kill",
                "part_number": "MPS-AS-KILL",
                "specs": {
                    "type": "electric_over_air",
                    "actuation": "button",
                    "includes": "DOT bottle, shift cylinder, kill box, valve, gauge",
                    "msrp_usd": 366.45,
                },
                "param_overrides": {
                    "drivetrain.air_shifter": True,
                    "drivetrain.total_shift_time_ms": 55,
                },
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport", "naked", "muscle"],
                        "displacement_min_cc": 400,
                    },
                    "description": (
                        "MPS electric-over-air shifter with gen-2 ignition "
                        "kill; full-throttle button shifts ~55 ms; universal "
                        "sport-bike kit (shifter bracketry fabricated to fit)."
                    ),
                },
                "price_inr": 48700,
                "availability": "import_only",
                "retailer": "MPS Racing (USA)",
                "delivery_days": 30,
            },
            {
                "category": "air_shifter",
                "brand": "MPS Racing",
                "model_name": "Air Shifter with RSR Air Shift Module",
                "part_number": "MPS-AS-RSR",
                "specs": {
                    "type": "electric_over_air",
                    "actuation": "button + RSR kill module",
                    "includes": "DOT bottle, SS cylinder, electric valve, RSR module",
                    "msrp_usd": 499,
                },
                "param_overrides": {
                    "drivetrain.air_shifter": True,
                    "drivetrain.total_shift_time_ms": 45,
                },
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport", "naked", "muscle"],
                        "displacement_min_cc": 400,
                    },
                    "description": (
                        "MPS air shifter with the RSR air-shift module — "
                        "cleaner kill timing than the classic kill box; "
                        "~45 ms shifts, drag-strip standard."
                    ),
                },
                "price_inr": 65800,
                "availability": "import_only",
                "retailer": "MPS Racing (USA)",
                "delivery_days": 30,
            },
            {
                "category": "air_shifter",
                "brand": "Schnitz Racing",
                "model_name": "Sport Bike Air Shifter Kit",
                "part_number": "SCHNITZ-AS-SPORT",
                "specs": {
                    "type": "electric_over_air",
                    "actuation": "button",
                    "msrp_usd": 350,
                    "price_estimated": True,
                },
                "param_overrides": {
                    "drivetrain.air_shifter": True,
                    "drivetrain.total_shift_time_ms": 55,
                },
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport", "naked", "muscle"],
                        "displacement_min_cc": 400,
                    },
                    "description": (
                        "Schnitz complete air shifter kit with shifter "
                        "brackets for easy install on nearly any sport bike; "
                        "push-button clutchless shifts without lifting."
                    ),
                },
                "price_inr": 46600,
                "availability": "import_only",
                "retailer": "Schnitz Racing (USA)",
                "delivery_days": 30,
            },
            {
                "category": "air_shifter",
                "brand": "MPS Racing",
                "model_name": "Automatic Air Shifter Kit (RPM-Activated)",
                "part_number": "MPS-AS-AUTO",
                "specs": {
                    "type": "automatic_rpm_window",
                    "actuation": "RPM switch — hands stay on the bars",
                    "msrp_usd": 600,
                    "price_estimated": True,
                },
                "param_overrides": {
                    "drivetrain.air_shifter": True,
                    "drivetrain.total_shift_time_ms": 40,
                },
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport", "naked", "muscle"],
                        "displacement_min_cc": 600,
                    },
                    "description": (
                        "MPS automatic air shifter — fires at a preset RPM "
                        "window every gear, ~40 ms; Pro Street consistency "
                        "tool (no rider shift-point variance)."
                    ),
                },
                "price_inr": 78800,
                "availability": "import_only",
                "retailer": "MPS Racing (USA)",
                "delivery_days": 30,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # LOCKUP CLUTCHES (3 parts) — NEW CATEGORY
    # ══════════════════════════════════════════════════════════════
    parts.extend(
        [
            {
                "category": "lockup_clutch",
                "brand": "MTC Engineering",
                "model_name": "Multistage Lock-Up Clutch — Hayabusa (99-21)",
                "part_number": "MTC-MS-BUSA",
                "specs": {
                    "type": "multi_stage_lockup",
                    "stages": "adjustable counterweight arms",
                    "msrp_usd": 1500,
                    "price_estimated": True,
                },
                "param_overrides": {
                    # ClutchModel CLUTCH_MULTISTAGE branch: centrifugal clamp
                    # F_cent ~ (rpm - engage_rpm)^2 stacks on spring preload —
                    # exactly a lockup's behaviour (soft launch, locked at RPM).
                    "clutch.clutch_type": "multistage",
                    "clutch.engage_rpm": 4200,
                },
                "param_multipliers": {
                    "clutch.spring_preload_n": 1.20,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1280,
                        "displacement_max_cc": 1360,
                        "categories": ["sport"],
                    },
                    "description": (
                        "MTC multistage lock-up clutch for Suzuki Hayabusa "
                        "(1999-2021); counterweight arms add clamp with RPM "
                        "— the proven drag-launch clutch."
                    ),
                },
                "price_inr": 195000,
                "availability": "import_only",
                "retailer": "MTC Engineering (USA)",
                "delivery_days": 40,
            },
            {
                "category": "lockup_clutch",
                "brand": "MTC Engineering",
                "model_name": "Gen II Multistage Clutch — Hayabusa (99-26)",
                "part_number": "MTC-GEN2-BUSA",
                "specs": {
                    "type": "multi_stage_lockup_gen2",
                    "stages": "engine-RPM-driven, quicker reaction",
                    "msrp_usd": 2397,
                },
                "param_overrides": {
                    "clutch.clutch_type": "multistage",
                    "clutch.engage_rpm": 4000,
                },
                "param_multipliers": {
                    "clutch.spring_preload_n": 1.30,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1280,
                        "displacement_max_cc": 1360,
                        "categories": ["sport"],
                    },
                    "description": (
                        "MTC Gen II multistage clutch for Hayabusa Gen 1-3; "
                        "runs on engine RPM for quicker reaction and "
                        "pass-to-pass repeatability; $2,397 retail no-core."
                    ),
                },
                "price_inr": 310000,
                "availability": "import_only",
                "retailer": "MTC Engineering (USA)",
                "delivery_days": 40,
            },
            {
                "category": "lockup_clutch",
                "brand": "MTC Engineering",
                "model_name": "Gen II Multistage Lockup — Kawasaki ZX-14 (12-24)",
                "part_number": "MTC-GEN2-ZX14",
                "specs": {
                    "type": "multi_stage_lockup_gen2",
                    "stages": "engine-RPM-driven, quicker reaction",
                    "msrp_usd": 2397,
                    "price_estimated": True,
                },
                "param_overrides": {
                    "clutch.clutch_type": "multistage",
                    "clutch.engage_rpm": 4000,
                },
                "param_multipliers": {
                    "clutch.spring_preload_n": 1.30,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1350,
                        "displacement_max_cc": 1450,
                        "categories": ["sport"],
                        "year_min": 2012,
                    },
                    "description": (
                        "MTC Gen II multistage lock-up for Kawasaki ZX-14R "
                        "2012-2024; same arm-driven clamp curve as the "
                        "Hayabusa Gen II unit."
                    ),
                },
                "price_inr": 310000,
                "availability": "import_only",
                "retailer": "MTC Engineering (USA)",
                "delivery_days": 40,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # V2-CRUISER NITROUS (4 parts) — existing 'nitrous' category
    # ══════════════════════════════════════════════════════════════
    parts.extend(
        [
            {
                "category": "nitrous",
                "brand": "Nitrous Express",
                "model_name": "NX V-Twin Piranha Wet Nitrous Kit",
                "part_number": "NX-60022P",
                "specs": {
                    "shot_hp": 25,
                    "type": "wet",
                    "bottle_size_lb": 2.5,
                    "jetting_range_hp": "10-45",
                    "msrp_usd": 680,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 25,
                    "chassis.dry_mass_kg": 4.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson", *_INDIAN_ALIASES],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 800,
                        "displacement_max_cc": 1950,
                        "categories": ["cruiser", "muscle", "touring"],
                    },
                    "description": (
                        "Nitrous Express V-Twin Piranha wet system, 2.5 lb "
                        "bottle, jetted 10-45 hp; Harley/Indian big-twin "
                        "cruisers (conservative 25-shot modelled)."
                    ),
                },
                "price_inr": 89100,
                "availability": "import_only",
                "retailer": "Nitrous Express (USA)",
                "delivery_days": 35,
            },
            {
                "category": "nitrous",
                "brand": "Nitrous Express",
                "model_name": "Harley Softail Dry Nitrous Plate Kit",
                "part_number": "NX-62110-2.5P",
                "specs": {
                    "shot_hp": 30,
                    "type": "dry_plate",
                    "bottle_size_lb": 2.5,
                    "msrp_usd": 600,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 30,
                    "chassis.dry_mass_kg": 4.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1440,
                        "displacement_max_cc": 1950,
                        "categories": ["cruiser", "muscle", "touring"],
                        "year_min": 2001,
                    },
                    "description": (
                        "NX dry nitrous plate kit (62110-2.5P) for 2001+ "
                        "Harley Softail Twin Cam / M8 big twins; plate "
                        "mounts under the throttle body."
                    ),
                },
                "price_inr": 78800,
                "availability": "import_only",
                "retailer": "Nitrous Express (USA)",
                "delivery_days": 35,
            },
            {
                "category": "nitrous",
                "brand": "DynoTune",
                "model_name": "Harley/Victory EFI Nitrous System — Single Bottle",
                "part_number": "DT-HD-EFI-1B",
                "specs": {
                    "shot_hp": 40,
                    "max_shot_hp": 80,
                    "type": "wet_efi",
                    "bottle_count": 1,
                    "msrp_usd": 549,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 40,
                    "chassis.dry_mass_kg": 4.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson", *_INDIAN_ALIASES],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 950,
                        "displacement_max_cc": 1950,
                        "categories": ["cruiser", "muscle", "touring"],
                    },
                    "description": (
                        "DynoTune complete bolt-on EFI wet system for "
                        "Harley/Indian V-twins, single bottle, jettable to "
                        "80 hp (40-shot modelled as the safe street tune)."
                    ),
                },
                "price_inr": 72200,
                "availability": "import_only",
                "retailer": "DynoTune Nitrous (USA)",
                "delivery_days": 30,
            },
            {
                "category": "nitrous",
                "brand": "DynoTune",
                "model_name": "Harley EFI Nitrous System — Twin Bottle",
                "part_number": "DT-HD-EFI-2B",
                "specs": {
                    "shot_hp": 50,
                    "max_shot_hp": 80,
                    "type": "wet_efi",
                    "bottle_count": 2,
                    "msrp_usd": 650,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 50,
                    "chassis.dry_mass_kg": 6.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson", *_INDIAN_ALIASES],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1950,
                        "categories": ["cruiser", "muscle", "touring"],
                    },
                    "description": (
                        "DynoTune twin-bottle EFI wet system for big-twin "
                        "cruisers; symmetric saddlebag-area bottle mounts, "
                        "50-shot modelled."
                    ),
                },
                "price_inr": 85200,
                "availability": "import_only",
                "retailer": "DynoTune Nitrous (USA)",
                "delivery_days": 30,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # HARLEY M8 TURBO KITS (2 parts) — existing 'boost_kit' category
    # (complements the widened generic Trask kit in drag_specific.py)
    # ══════════════════════════════════════════════════════════════
    parts.extend(
        [
            {
                "category": "boost_kit",
                "brand": "Trask Performance",
                "model_name": "Assault Turbo System — Harley M8",
                "part_number": "TRASK-ASSAULT-M8",
                "specs": {
                    "boost_psi": 8.0,
                    "type": "turbo",
                    "compressor_size": "Garrett G-series",
                    "tuner": "ThunderMax ECM included",
                    "msrp_usd": 7600,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 75,
                    "engine.peak_torque_nm": 90,
                    "chassis.dry_mass_kg": 12.0,
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1740,
                        "displacement_max_cc": 1950,
                        "categories": ["cruiser", "touring"],
                        "year_min": 2017,
                    },
                    "description": (
                        "Trask Assault turbo for 2017+ Harley M8 107/114/117 "
                        "Softail & Touring; 100% bolt-on at 8 psi on 91 "
                        "octane, +40-50% rear-wheel power; $7,600 complete "
                        "with ThunderMax."
                    ),
                },
                "price_inr": 980000,
                "availability": "import_only",
                "retailer": "Trask Performance (USA)",
                "delivery_days": 75,
            },
            {
                "category": "boost_kit",
                "brand": "Trask Performance",
                "model_name": "Tornado Turbo Performance Kit — Harley M8",
                "part_number": "TRASK-TORNADO-M8",
                "specs": {
                    "boost_psi": 6.0,
                    "type": "turbo",
                    "finish": "all-black",
                    "msrp_usd": 5800,
                    "price_estimated": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 55,
                    "engine.peak_torque_nm": 70,
                    "chassis.dry_mass_kg": 11.0,
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1740,
                        "displacement_max_cc": 1950,
                        "categories": ["cruiser", "touring"],
                        "year_min": 2017,
                    },
                    "description": (
                        "Trask Tornado turbo performance kit for '17-23 "
                        "Harley M8; the street-tier kit below the Assault "
                        "(tuner purchased separately)."
                    ),
                },
                "price_inr": 748000,
                "availability": "import_only",
                "retailer": "Trask Performance (USA)",
                "delivery_days": 75,
            },
        ]
    )

    return _create_parts_batch(db, parts, label="Drag Essentials Parts")
