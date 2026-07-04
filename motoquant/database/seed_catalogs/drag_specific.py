"""
MotoQuant Pro — Drag-Specific Performance Parts Catalog
========================================================
Seeds ~60 drag-focused performance parts across 6 categories:
  - Nitrous oxide systems (10 parts): small-cc through litre-class
  - Boost kits: turbo & supercharger (10 parts): litre-class sport, Harley, BMW, Ducati
  - Clutch kits: slipper & heavy-duty (10 parts): sport I4, V-twin, V4
  - Fuel systems: ECU-safe & race-fuel ready (8 parts): litre-class & turbo combos
  - Air filters: race-grade (10 parts): sport, commuter, cruiser segments
  - Quickshifters: electronic shift (10 parts): universal + model-specific

Fitment rules use tight `manufacturers` + `engine_configs` + displacement bounds
to prevent cross-segment leaks (e.g., Hayabusa nitrous ≠ Pulsar 200 nitrous).
All parts include realistic drag-physics parameter deltas (HP, mass, weight distribution).

Price range: ₹3k–₹10L depending on category and complexity.
"""

from motoquant.database.seed_catalogs import _create_parts_batch


def seed_drag_specific(db) -> int:
    """
    Seeds drag-specific performance parts across 6 categories.
    Returns count of parts created.
    """
    parts = []

    # ══════════════════════════════════════════════════════════════
    # NITROUS OXIDE SYSTEMS (10 parts)
    # ══════════════════════════════════════════════════════════════

    # Universal small-cc systems (150–400cc, all configs)
    parts.extend(
        [
            {
                "category": "nitrous",
                "brand": "NOS",
                "model_name": "NOS Wet System 20-Shot Commuter Kit",
                "part_number": "NOS-WET-20-COMMUTER",
                "specs": {
                    "shot_hp": 20,
                    "type": "wet",
                    "bottle_size_kg": 1.0,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 20,
                    "chassis.dry_mass_kg": 3.5,  # bottle weight
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "KTM",
                            "Bajaj",
                            "TVS",
                            "Yamaha",
                            "Honda",
                            "Hero",
                        ],
                        "engine_configs": ["I1", "I2"],
                        "displacement_min_cc": 150,
                        "displacement_max_cc": 400,
                    },
                    "description": "NOS wet 20-shot for small-cc Indian commuters; ECU-safe (boosts 20hp, bottle 3.5kg)",
                },
                "price_inr": 18000,
                "availability": "order",
                "retailer": "NOS India",
                "delivery_days": 14,
            },
            {
                "category": "nitrous",
                "brand": "NOS",
                "model_name": "NOS Wet System 40-Shot Mid-Size Kit",
                "part_number": "NOS-WET-40-MID",
                "specs": {
                    "shot_hp": 40,
                    "type": "wet",
                    "bottle_size_kg": 1.5,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 40,
                    "chassis.dry_mass_kg": 4.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "KTM",
                            "Kawasaki",
                            "Suzuki",
                            "Honda",
                            "Yamaha",
                        ],
                        "engine_configs": ["I2", "I3"],
                        "displacement_min_cc": 400,
                        "displacement_max_cc": 800,
                    },
                    "description": "NOS wet 40-shot for 400-800cc I2/I3 bikes; street/strip legal",
                },
                "price_inr": 28000,
                "availability": "in_stock",
                "retailer": "NOS India",
                "delivery_days": 0,
            },
            {
                "category": "nitrous",
                "brand": "NOS",
                "model_name": "NOS Wet System 60-Shot Litre+ Kit",
                "part_number": "NOS-WET-60-LITRE",
                "specs": {
                    "shot_hp": 60,
                    "type": "wet",
                    "bottle_size_kg": 2.0,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 60,
                    "chassis.dry_mass_kg": 5.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki", "Yamaha", "Honda", "Kawasaki"],
                        "engine_configs": ["I4", "I3"],
                        "displacement_min_cc": 800,
                        "displacement_max_cc": 1350,
                    },
                    "description": "NOS wet 60-shot for litre-class I4 sport bikes; bolt-on fit",
                },
                "price_inr": 35000,
                "availability": "order",
                "retailer": "NOS Performance",
                "delivery_days": 10,
            },
        ]
    )

    # ZEX dry systems (sport 400–800cc I4/V4)
    parts.extend(
        [
            {
                "category": "nitrous",
                "brand": "ZEX",
                "model_name": "ZEX Dry System 30-Shot Sport 400-600",
                "part_number": "ZEX-DRY-30-SPORT",
                "specs": {
                    "shot_hp": 30,
                    "type": "dry",
                    "bottle_size_kg": 1.2,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 30,
                    "chassis.dry_mass_kg": 3.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki", "Honda", "Yamaha", "Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 400,
                        "displacement_max_cc": 650,
                    },
                    "description": "ZEX dry 30-shot for sport 400-650cc inline-fours (no fuel mod needed)",
                },
                "price_inr": 32000,
                "availability": "order",
                "retailer": "ZEX Asia",
                "delivery_days": 21,
            },
        ]
    )

    # Holley & Nitrous Express premium litre systems
    parts.extend(
        [
            {
                "category": "nitrous",
                "brand": "Holley",
                "model_name": "Holley Sniper 75-Shot Hayabusa Direct",
                "part_number": "HOLLEY-SNIPER-75-GSXR",
                "specs": {
                    "shot_hp": 75,
                    "type": "direct_port",
                    "bottle_size_kg": 2.5,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 75,
                    "chassis.dry_mass_kg": 5.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1299,
                        "displacement_max_cc": 1341,
                        "categories": ["sport"],
                    },
                    "description": "Holley Sniper 75-shot direct-port for Suzuki Hayabusa litre-class drag",
                },
                "price_inr": 65000,
                "availability": "order",
                "retailer": "Holley Performance",
                "delivery_days": 30,
            },
            {
                "category": "nitrous",
                "brand": "Nitrous Express",
                "model_name": "Nitrous Express Wet 50-Shot R1 Kit",
                "part_number": "NX-WET-50-R1",
                "specs": {
                    "shot_hp": 50,
                    "type": "wet",
                    "bottle_size_kg": 1.8,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 50,
                    "chassis.dry_mass_kg": 4.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 998,
                        "displacement_max_cc": 1008,
                    },
                    "description": "Nitrous Express wet 50-shot for Yamaha R1 litre-class sport",
                },
                "price_inr": 42000,
                "availability": "import_only",
                "retailer": "Nitrous Express USA",
                "delivery_days": 45,
            },
        ]
    )

    # Small-cc ECU-safe system (for Indian market drag prep)
    parts.extend(
        [
            {
                "category": "nitrous",
                "brand": "Schnitz Racing",
                "model_name": "Schnitz Racing NX 50-Shot Indian Market Kit",
                "part_number": "SCHNITZ-NX-50-INDIA",
                "specs": {
                    "shot_hp": 50,
                    "type": "wet",
                    "bottle_size_kg": 1.6,
                    "fuel_type": "pump_gas",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 50,
                    "chassis.dry_mass_kg": 4.3,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "Royal Enfield",
                            "Hero",
                            "Bajaj",
                            "TVS",
                            "Yamaha",
                        ],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 300,
                        "displacement_max_cc": 650,
                    },
                    "description": "Schnitz NX 50-shot for Indian 300-650cc twins; ECU-safe lean-burn compatible",
                },
                "price_inr": 38000,
                "availability": "order",
                "retailer": "Schnitz Racing India",
                "delivery_days": 7,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # BOOST KITS: TURBO & SUPERCHARGER (10 parts)
    # ══════════════════════════════════════════════════════════════

    # Suzuki Hayabusa specialized turbo
    parts.extend(
        [
            {
                "category": "boost_kit",
                "brand": "Velocity Turbo",
                "model_name": "Velocity Turbo Stage 1 Hayabusa Kit",
                "part_number": "VT-STAGE1-GSXR",
                "specs": {
                    "boost_psi": 6.5,
                    "type": "turbo",
                    "compressor_size": "GT2560R",
                    "intercooler": "air_to_air",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 100,
                    "engine.peak_torque_nm": 85,
                    "chassis.dry_mass_kg": 8.5,  # turbo assembly + intercooler
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1299,
                        "displacement_max_cc": 1341,
                    },
                    "description": "Velocity Stage 1 turbo kit for Hayabusa; +100 hp, 6.5 psi boost, drag-proven",
                },
                "price_inr": 350000,
                "availability": "order",
                "retailer": "Velocity Turbo USA",
                "delivery_days": 60,
            },
            {
                "category": "boost_kit",
                "brand": "ORP",
                "model_name": "ORP Twin-Turbo Hayabusa Drag Kit",
                "part_number": "ORP-TT-GSXR-DRAG",
                "specs": {
                    "boost_psi": 12.0,
                    "type": "twin_turbo",
                    "compressor_size": "GT2560R x2",
                    "intercooler": "air_to_air_dual",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 180,
                    "engine.peak_torque_nm": 150,
                    "chassis.dry_mass_kg": 15.0,
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1299,
                        "displacement_max_cc": 1341,
                        "categories": ["sport"],
                    },
                    "description": "ORP twin-turbo for Hayabusa drag racing only; +180 hp, 12 psi, competition-grade",
                },
                "price_inr": 800000,
                "availability": "import_only",
                "retailer": "ORP Turbo USA",
                "delivery_days": 90,
            },
        ]
    )

    # Yamaha R1 / MT-10 turbo
    parts.extend(
        [
            {
                "category": "boost_kit",
                "brand": "HKS",
                "model_name": "HKS Turbo Kit Yamaha R1 / MT-10",
                "part_number": "HKS-R1-TURBO",
                "specs": {
                    "boost_psi": 7.0,
                    "type": "turbo",
                    "compressor_size": "GT3037",
                    "intercooler": "air_to_air",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 95,
                    "engine.peak_torque_nm": 80,
                    "chassis.dry_mass_kg": 9.0,
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 998,
                        "displacement_max_cc": 1008,
                    },
                    "description": "HKS turbo kit for Yamaha R1/MT-10 litre-class; +95 hp, street-legal capable",
                },
                "price_inr": 320000,
                "availability": "import_only",
                "retailer": "HKS Japan",
                "delivery_days": 75,
            },
        ]
    )

    # Ducati Panigale V4 supercharger
    parts.extend(
        [
            {
                "category": "boost_kit",
                "brand": "Garrett",
                "model_name": "Garrett G25 Turbo Ducati Panigale V4",
                "part_number": "GARRETT-G25-PANI-V4",
                "specs": {
                    "boost_psi": 6.0,
                    "type": "turbo",
                    "compressor_size": "G25",
                    "intercooler": "liquid_cooled",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 85,
                    "engine.peak_torque_nm": 70,
                    "chassis.dry_mass_kg": 9.5,
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1103,
                        "displacement_max_cc": 1108,
                    },
                    "description": "Garrett turbo for Ducati Panigale V4 drag prep; +85 hp, liquid-cooled IC",
                },
                "price_inr": 400000,
                "availability": "import_only",
                "retailer": "Garrett Europe",
                "delivery_days": 80,
            },
        ]
    )

    # BMW S1000RR supercharger (realistic for drag)
    parts.extend(
        [
            {
                "category": "boost_kit",
                "brand": "TTS Supercharger",
                "model_name": "TTS Supercharger BMW S1000RR",
                "part_number": "TTS-SC-S1000RR",
                "specs": {
                    "boost_psi": 5.0,
                    "type": "supercharger",
                    "compressor_size": "Lysholm screw",
                    "intercooler": "air_to_air",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 60,
                    "engine.peak_torque_nm": 50,
                    "chassis.dry_mass_kg": 7.5,
                },
                "param_overrides": {"forced_induction.boost_type": "supercharger"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 999,
                        "displacement_max_cc": 1001,
                    },
                    "description": "TTS supercharger for BMW S1000RR; +60 hp, parasitic loss offset by instant spool",
                },
                "price_inr": 450000,
                "availability": "import_only",
                "retailer": "TTS Performance Germany",
                "delivery_days": 85,
            },
        ]
    )

    # Harley & Indian small-bore turbo (chain-drive V-twin emphasis)
    parts.extend(
        [
            {
                "category": "boost_kit",
                "brand": "Trask Performance",
                "model_name": "Trask Turbo System Harley / Indian V-Twin",
                "part_number": "TRASK-VT-TURBO",
                "specs": {
                    "boost_psi": 7.5,
                    "type": "turbo",
                    "compressor_size": "GT3540",
                    "intercooler": "liquid",
                },
                "param_deltas": {
                    "engine.peak_power_hp": 85,
                    "engine.peak_torque_nm": 90,
                    "chassis.dry_mass_kg": 10.0,
                },
                "param_overrides": {"forced_induction.boost_type": "turbo"},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        # "Indian" = canonical DB manufacturer name post the
                        # 2026-06-13 merge; "Indian Motorcycle" kept as alias
                        # for fresh seeds from older specs.
                        "manufacturers": [
                            "Harley-Davidson",
                            "Indian",
                            "Indian Motorcycle",
                        ],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 800,
                        # 1950 (was 1750) so Harley M8 114/117 (1868/1923cc)
                        # and Indian Thunderstroke/PowerPlus (1768-1890cc)
                        # actually match — Trask sells M8 + Indian kits.
                        "displacement_max_cc": 1950,
                    },
                    "description": "Trask turbo for Harley/Indian V-twins incl. M8 114/117 (belt-drive OK); +85 hp, drag-prepped",
                },
                "price_inr": 380000,
                "availability": "order",
                "retailer": "Trask Performance USA",
                "delivery_days": 75,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CLUTCH KITS: SLIPPER & HEAVY-DUTY (10 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "clutch_kit",
                "brand": "Suter Racing",
                "model_name": "Suter Racing Slipper Clutch Litre I4 Universal",
                "part_number": "SUTER-SLIP-I4-LITRE",
                "specs": {
                    "type": "slipper",
                    "engagement_rpm": 6500,
                    "material": "carbon_sintered",
                },
                "param_overrides": {"clutch.slipper_ratio": 0.35},
                "param_multipliers": {"clutch.spring_preload_n": 1.25},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki", "Honda", "Yamaha", "Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1000,
                        "displacement_max_cc": 1350,
                    },
                    "description": "Suter slipper for litre-class I4 sport; prevents backtorque wheel-lift at 0.35 ratio",
                },
                "price_inr": 68000,
                "availability": "order",
                "retailer": "Suter Racing EU",
                "delivery_days": 35,
            },
            {
                "category": "clutch_kit",
                "brand": "STM Evoluzione",
                "model_name": "STM Evoluzione Slipper Ducati V4 Panigale",
                "part_number": "STM-SLIP-PANI-V4",
                "specs": {
                    "type": "slipper",
                    "engagement_rpm": 6800,
                    "material": "carbon_sintered",
                },
                "param_overrides": {"clutch.slipper_ratio": 0.32},
                "param_multipliers": {"clutch.spring_preload_n": 1.30},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                    "description": "STM slipper for Ducati Panigale V4 drag; 0.32 ratio for light wheelies, peak capacity 30% up",
                },
                "price_inr": 72000,
                "availability": "import_only",
                "retailer": "STM Italy",
                "delivery_days": 40,
            },
            {
                "category": "clutch_kit",
                "brand": "EBC Brakes",
                "model_name": "EBC CK Clutch Kit Sport 600-1000cc",
                "part_number": "EBC-CK-SPORT",
                "specs": {
                    "type": "heavy_duty",
                    "engagement_rpm": 5500,
                    "material": "kevlar_organic",
                },
                "param_multipliers": {"clutch.spring_preload_n": 1.18},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "Suzuki",
                            "Honda",
                            "Yamaha",
                            "Kawasaki",
                            "Aprilia",
                        ],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1000,
                    },
                    "description": "EBC heavy-duty for 600-1000cc sport I4; 18% torque bump, smooth dragging engagement",
                },
                "price_inr": 32000,
                "availability": "in_stock",
                "retailer": "EBC Brakes India",
                "delivery_days": 0,
            },
        ]
    )

    # Harley & Indian V-twin clutches (drag-specific)
    parts.extend(
        [
            {
                "category": "clutch_kit",
                "brand": "Rekluse Core Manual",
                "model_name": "Rekluse Core Manual Harley V-Twin",
                "part_number": "REKLUSE-CORE-HD",
                "specs": {
                    "type": "heavy_duty",
                    "engagement_rpm": 3500,
                    "material": "organic_sintered",
                },
                "param_multipliers": {"clutch.spring_preload_n": 1.22},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Harley-Davidson", "Indian Motorcycle"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 800,
                        "displacement_max_cc": 1750,
                    },
                    "description": "Rekluse Core Manual for Harley/Indian V-twins; drag-tuned for low-RPM grip, 22% capacity",
                },
                "price_inr": 55000,
                "availability": "import_only",
                "retailer": "Rekluse USA",
                "delivery_days": 45,
            },
        ]
    )

    # KTM / Husqvarna small-cc clutches
    parts.extend(
        [
            {
                "category": "clutch_kit",
                "brand": "Hinson BTL",
                "model_name": "Hinson BTL Slipper KTM 390 / Husqvarna 401",
                "part_number": "HINSON-BTL-KTM-390",
                "specs": {
                    "type": "slipper",
                    "engagement_rpm": 5000,
                    "material": "carbon",
                },
                "param_overrides": {"clutch.slipper_ratio": 0.40},
                "param_multipliers": {"clutch.spring_preload_n": 1.15},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        # KTM 390 / Husqvarna 401 are I1 singles, not V2
                        # (patch_2026_06_11 C) — a ['V2'] filter matched nothing.
                        "manufacturers": ["KTM", "Husqvarna"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 375,
                        "displacement_max_cc": 410,
                    },
                    "description": "Hinson BTL slipper for KTM 390 / Husqvarna 401; 0.40 ratio lets small singles wheelie safely",
                },
                "price_inr": 38000,
                "availability": "order",
                "retailer": "Hinson USA",
                "delivery_days": 30,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # FUEL SYSTEMS (8 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "fuel_system",
                "brand": "Injector Dynamics",
                "model_name": "Injector Dynamics ID725 Set (x4) Litre I4",
                "part_number": "ID-ID725-x4",
                "specs": {
                    "flow_cc_min": 725,
                    "pressure_bar": 3.5,
                    "fuel_type": "pump_gas",
                    "mount": "top_feed",
                },
                "param_multipliers": {"engine.peak_power_hp": 1.03},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki", "Honda", "Yamaha", "Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1000,
                        "displacement_max_cc": 1350,
                    },
                    "description": "ID725 injectors for litre-class I4 drag prep; 45% flow bump, works with stock fuel rail",
                },
                "price_inr": 45000,
                "availability": "order",
                "retailer": "Injector Dynamics USA",
                "delivery_days": 25,
            },
            {
                "category": "fuel_system",
                "brand": "Injector Dynamics",
                "model_name": "Injector Dynamics ID1050X Turbo Set",
                "part_number": "ID-ID1050X-TURBO",
                "specs": {
                    "flow_cc_min": 1050,
                    "pressure_bar": 4.5,
                    "fuel_type": "pump_gas|e85",
                    "mount": "top_feed",
                },
                "param_multipliers": {"engine.peak_power_hp": 1.04},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "Suzuki",
                            "Honda",
                            "Yamaha",
                            "Kawasaki",
                            "Ducati",
                            "BMW",
                        ],
                        "engine_configs": ["I4", "V4"],
                        "displacement_min_cc": 1000,
                        "displacement_max_cc": 1350,
                    },
                    "description": "ID1050X for turbo/supercharger builds; 100% flow capacity, 4.5 bar rated, E85-capable",
                },
                "price_inr": 65000,
                "availability": "order",
                "retailer": "Injector Dynamics USA",
                "delivery_days": 30,
            },
            {
                "category": "fuel_system",
                "brand": "Walbro",
                "model_name": "Walbro 450 LPH Fuel Pump",
                "part_number": "WALBRO-450",
                "specs": {
                    "flow_lph": 450,
                    "pressure_bar": 4.0,
                    "fuel_type": "pump_gas|e85",
                    "voltage": 12,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport", "naked"],
                        "displacement_min_cc": 600,
                    },
                    "description": "Walbro 450 for drag prep sport bikes; 35% flow over stock, drag-strip proven",
                },
                "price_inr": 22000,
                "availability": "in_stock",
                "retailer": "Walbro Asia",
                "delivery_days": 5,
            },
            {
                "category": "fuel_system",
                "brand": "Aeromotive",
                "model_name": "Aeromotive A1000 Drag Fuel Regulator",
                "part_number": "AERO-A1000-REG",
                "specs": {
                    "pressure_bar": "3.5-7.0",
                    "flow_lph": 1000,
                    "fuel_type": "pump_gas|e85|race_fuel",
                    "adjustable": True,
                },
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport"],
                        "displacement_min_cc": 800,
                    },
                    "description": "Aeromotive A1000 drag regulator; adjust 3.5–7 bar on track, works with turbo boost",
                },
                "price_inr": 28000,
                "availability": "order",
                "retailer": "Aeromotive USA",
                "delivery_days": 20,
            },
            {
                "category": "fuel_system",
                "brand": "Bazzaz",
                "model_name": "Bazzaz BKN Fuel Map Controller",
                "part_number": "BAZZAZ-BKN",
                "specs": {
                    "type": "fuel_map_ecu",
                    "channels": 16,
                    "wireless": True,
                    "fuel_type": "pump_gas|e85",
                },
                "param_multipliers": {"engine.peak_power_hp": 1.015},
                "fitment_rules": {
                    "tier": "category",
                    "match": {
                        "categories": ["sport", "naked"],
                        "displacement_min_cc": 400,
                    },
                    "description": "Bazzaz BKN fuel map; 16-channel wireless tuning, drag dyno-friendly for power builds",
                },
                "price_inr": 35000,
                "availability": "order",
                "retailer": "Bazzaz USA",
                "delivery_days": 15,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # AIR FILTERS: RACE-GRADE (10 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "air_filter",
                "brand": "BMC",
                "model_name": "BMC Race Hi-Flow RFD-180 Hayabusa",
                "part_number": "BMC-RFD180-GSXR",
                "specs": {
                    "type": "race_cone",
                    "material": "cotton_paper",
                    "diameter_mm": 180,
                    "flow_improvement": 0.028,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.028},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1299,
                        "displacement_max_cc": 1341,
                    },
                    "description": "BMC Hi-Flow cone filter for Hayabusa; +2.8% peak power, drag-legal",
                },
                "price_inr": 8500,
                "availability": "in_stock",
                "retailer": "BMC India",
                "delivery_days": 2,
            },
            {
                "category": "air_filter",
                "brand": "K&N",
                "model_name": "K&N Power Kit RC-2910 Yamaha R1",
                "part_number": "KN-RC2910-R1",
                "specs": {
                    "type": "race_kit",
                    "material": "cotton",
                    "diameter_mm": 152,
                    "flow_improvement": 0.025,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 998,
                        "displacement_max_cc": 1008,
                    },
                    "description": "K&N Power Kit for Yamaha R1; +2.5% power, reusable/washable filter",
                },
                "price_inr": 7200,
                "availability": "in_stock",
                "retailer": "K&N India",
                "delivery_days": 3,
            },
            {
                "category": "air_filter",
                "brand": "DNA",
                "model_name": "DNA Stage 2 Sport Cone Filter I4 600+",
                "part_number": "DNA-STAGE2-I4",
                "specs": {
                    "type": "cone",
                    "material": "foam",
                    "diameter_mm": 165,
                    "flow_improvement": 0.032,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.032},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda", "Suzuki", "Yamaha", "Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1350,
                    },
                    "description": "DNA Stage 2 foam cone for sport I4 600cc+; +3.2% peak power, oil service every 3k km",
                },
                "price_inr": 6800,
                "availability": "in_stock",
                "retailer": "DNA India",
                "delivery_days": 2,
            },
            {
                "category": "air_filter",
                "brand": "Sprint Filter",
                "model_name": "Sprint Filter P08 Ducati V4 Panigale",
                "part_number": "SPRINT-P08-PANI",
                "specs": {
                    "type": "race_cone",
                    "material": "polyurethane",
                    "diameter_mm": 145,
                    "flow_improvement": 0.030,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.030},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                    "description": "Sprint Filter P08 for Ducati Panigale V4; +3.0% power, drag-track compatible",
                },
                "price_inr": 9200,
                "availability": "order",
                "retailer": "Sprint Filter EU",
                "delivery_days": 20,
            },
            {
                "category": "air_filter",
                "brand": "MWR Pro Filter",
                "model_name": "MWR Pro Filter KTM 390 / Husqvarna 401",
                "part_number": "MWR-PRO-KTM390",
                "specs": {
                    "type": "cone",
                    "material": "cotton_paper",
                    "diameter_mm": 120,
                    "flow_improvement": 0.020,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.020},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        # KTM 390 / Husqvarna 401 are I1 singles, not V2
                        # (patch_2026_06_11 C) — a ['V2'] filter matched nothing.
                        "manufacturers": ["KTM", "Husqvarna"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 375,
                        "displacement_max_cc": 410,
                    },
                    "description": "MWR Pro cone for KTM 390 / Husqvarna 401; +2.0% peak power, small-cc drag legal",
                },
                "price_inr": 4200,
                "availability": "order",
                "retailer": "MWR Racing EU",
                "delivery_days": 30,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # QUICKSHIFTERS: ELECTRONIC GEAR SHIFTS (10 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "quickshifter",
                "brand": "Healtech",
                "model_name": "Healtech iQSE-1 Universal I4 Sport",
                "part_number": "HEALTECH-IQSE1-I4",
                "specs": {
                    "type": "strain_gauge",
                    "cut_time_ms": 50,
                    "bidirectional": True,
                    "wireless": False,
                },
                "param_overrides": {
                    "drivetrain.quickshifter": True,
                    "drivetrain.total_shift_time_ms": 50,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda", "Suzuki", "Yamaha", "Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1350,
                    },
                    "description": "Healtech iQSE-1 for sport I4; 50 ms cut, strain-gauge, bi-directional shift + blip",
                },
                "price_inr": 18000,
                "availability": "in_stock",
                "retailer": "Healtech EU",
                "delivery_days": 7,
            },
            {
                "category": "quickshifter",
                "brand": "Translogic",
                "model_name": "Translogic IntelliShift Sport I4",
                "part_number": "TL-INTELLI-I4",
                "specs": {
                    "type": "pressure_sensor",
                    "cut_time_ms": 55,
                    "bidirectional": True,
                    "wireless": False,
                },
                "param_overrides": {
                    "drivetrain.quickshifter": True,
                    "drivetrain.total_shift_time_ms": 55,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "Honda",
                            "Suzuki",
                            "Yamaha",
                            "Kawasaki",
                            "Aprilia",
                        ],
                        "engine_configs": ["I4", "V4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1000,
                    },
                    "description": "Translogic IntelliShift for sport I4/V4; 55 ms shift cut, pressure-sensor based",
                },
                "price_inr": 16500,
                "availability": "order",
                "retailer": "Translogic USA",
                "delivery_days": 14,
            },
            {
                "category": "quickshifter",
                "brand": "Dynojet",
                "model_name": "Dynojet QEM Quickshifter Universal I4",
                "part_number": "DJ-QEM-I4",
                "specs": {
                    "type": "strain_gauge",
                    "cut_time_ms": 48,
                    "bidirectional": True,
                    "wireless": True,
                    "pairs_with": "PowerCommander PCV",
                },
                "param_overrides": {
                    "drivetrain.quickshifter": True,
                    "drivetrain.total_shift_time_ms": 48,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda", "Suzuki", "Yamaha", "Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1350,
                    },
                    "description": "Dynojet QEM for litre I4 drag; 48 ms cut, wireless tunable, synergy with PowerCommander",
                },
                "price_inr": 22000,
                "availability": "order",
                "retailer": "Dynojet USA",
                "delivery_days": 20,
            },
            {
                "category": "quickshifter",
                "brand": "GP-Tech",
                "model_name": "GP-Tech Quickshifter Ducati V4",
                "part_number": "GPTECH-QS-V4",
                "specs": {
                    "type": "strain_gauge",
                    "cut_time_ms": 52,
                    "bidirectional": True,
                    "wireless": False,
                },
                "param_overrides": {
                    "drivetrain.quickshifter": True,
                    "drivetrain.total_shift_time_ms": 52,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                    "description": "GP-Tech QS for Ducati V4 Panigale; 52 ms shift, Ducati-specific harness",
                },
                "price_inr": 20000,
                "availability": "order",
                "retailer": "GP-Tech Racing EU",
                "delivery_days": 25,
            },
            {
                "category": "quickshifter",
                "brand": "RapidBike",
                "model_name": "RapidBike QS4 USB Quickshifter",
                "part_number": "RB-QS4-USB",
                "specs": {
                    "type": "pressure_sensor",
                    "cut_time_ms": 60,
                    "bidirectional": True,
                    "wireless": True,
                    "tuning_interface": "USB",
                },
                "param_overrides": {
                    "drivetrain.quickshifter": True,
                    "drivetrain.total_shift_time_ms": 60,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda", "Yamaha", "Suzuki", "Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1000,
                    },
                    "description": "RapidBike QS4 for sport I4; 60 ms shift, USB tuning, wireless sync",
                },
                "price_inr": 19000,
                "availability": "order",
                "retailer": "RapidBike EU",
                "delivery_days": 18,
            },
            {
                "category": "quickshifter",
                "brand": "HM Quickshifter",
                "model_name": "HM Quickshifter V-Twin Cruiser 1000cc+",
                "part_number": "HM-QS-VT",
                "specs": {
                    "type": "strain_gauge",
                    "cut_time_ms": 70,
                    "bidirectional": True,
                    "wireless": False,
                },
                "param_overrides": {
                    "drivetrain.quickshifter": True,
                    "drivetrain.total_shift_time_ms": 70,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "Harley-Davidson",
                            "Indian Motorcycle",
                            "Triumph",
                        ],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1000,
                        "displacement_max_cc": 1750,
                    },
                    "description": "HM QS for cruiser V-twins; 70 ms shift (slower torque ramp), drag-street hybrid",
                },
                "price_inr": 21000,
                "availability": "import_only",
                "retailer": "HM Racing USA",
                "delivery_days": 35,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CREATE PARTS IN DATABASE
    # ══════════════════════════════════════════════════════════════

    return _create_parts_batch(db, parts, label="Drag-Specific Parts")
