"""
MotoQuant — Two-Stroke Specific Parts Catalog
=============================================
Seeds ~40 two-stroke-specific parts across 7 sub-categories:
  - Expansion chambers (pipes): FMF / DEP / Tyga / Jolly Moto / JL / Arrow (10 parts)
  - Reed valves: VForce 3/4, Boyesen RAD Valve, Moto Tassinari (6 parts)
  - Powervalve ECU / controller upgrades: Zeeltronic RAVE/YPVS controllers (5 parts)
  - Jet kits & carb rejetting: Dynojet Stage 1/2/3 for 2T (5 parts)
  - Head mods: squish band machining, compression bumps (4 parts)
  - 2T-specific ignition (Zeeltronic programmable, Vape CDI, HPI stator) (4 parts)
  - 2T carb upgrades (Keihin PWK, Mikuni TMX) (4 parts)

All parts target the 20 2-stroke bikes seeded in `known_bikes.py`:
  RD350/RD400/RD500LC/RZV500R/RX100/RX135/RXZ135/TZR250 (Yamaha)
  RGV250/RG500/GT750 (Suzuki)
  KR-1S/H2 Mach IV (Kawasaki)
  NSR250R/CR500R (Honda)
  RS125/RS250 (Aprilia)
  KTM 300 EXC / 250 SX
  Yezdi 250

Fitment rules use `manufacturers` + `engine_configs` + displacement bounds. Many
fitment blocks include `stroke_type_filter: 2` as a description hint — the runtime
fitment engine does not yet check this field, but `engine_configs` filters I1/I2
inherently separate 2T from 4T since no family overlaps on the exact match set.

Price range: ₹4k (jet kit) – ₹75k (full expansion chamber + silencer).
"""

from motoquant.database.seed_catalogs import _create_parts_batch


def seed_two_stroke(db) -> int:
    """
    Seeds 2-stroke-specific performance parts.
    Returns count of parts created.
    """
    parts = []

    # ══════════════════════════════════════════════════════════════
    # EXPANSION CHAMBERS (10 parts)
    # Pipe tuning is THE single biggest mod for a 2T — shifts torque peak
    # RPM and widens powerband. Param deltas: +peak_power_hp, +peak_torque_nm,
    # and engine.tuned_rpm bump (upshift pipe = higher RPM peak).
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            # --- Yamaha RD / RZ / RX series (air-cooled & LC twins) ---
            {
                "category": "exhaust",
                "brand": "Jim Lomas (JL)",
                "model_name": "JL Expansion Chambers RD350/RD400",
                "part_number": "JL-RD-350-400",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "stroke_type": 2,
                    "config": "twin_pipe",
                    "silencer": "aluminium_stinger",
                    "weight_kg": 7.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 9,
                    "engine.peak_torque_nm": 5,
                    "chassis.dry_mass_kg": -3.5,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 8200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 330,
                        "displacement_max_cc": 410,
                        "stroke_type": 2,
                    },
                    "description": "JL pipes for air-cooled RD350/400 twins; race-spec, tuned_rpm pushed to 8200",
                },
                "price_inr": 42000,
                "availability": "import_only",
                "retailer": "Jim Lomas UK",
                "delivery_days": 30,
            },
            {
                "category": "exhaust",
                "brand": "Tyga Performance",
                "model_name": "Tyga Expansion Chambers RD500LC / RZV500R",
                "part_number": "TYG-RD500-QUAD",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "quad_pipe_v4",
                    "stroke_type": 2,
                    "weight_kg": 11.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 22,
                    "engine.peak_torque_nm": 10,
                    "chassis.dry_mass_kg": -5.0,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 10200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4", "V4"],
                        "displacement_min_cc": 495,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Tyga quad-pipe set for RD500LC / RZV500R V4 2T; full race, 10k tuned peak",
                },
                "price_inr": 75000,
                "availability": "import_only",
                "retailer": "Tyga Thailand",
                "delivery_days": 21,
            },
            {
                "category": "exhaust",
                "brand": "Jolly Moto",
                "model_name": "Jolly Moto Chambers RX100 / RX135 / RXZ",
                "part_number": "JM-YAM-RX-100-135",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "single_pipe",
                    "stroke_type": 2,
                    "weight_kg": 3.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4,
                    "engine.peak_torque_nm": 2,
                    "chassis.dry_mass_kg": -1.5,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 8000,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 95,
                        "displacement_max_cc": 140,
                        "stroke_type": 2,
                    },
                    "description": "Jolly Moto pipe for Yamaha RX100/RX135/RXZ135 singles; drag-scene staple",
                },
                "price_inr": 14000,
                "availability": "in_stock",
                "retailer": "Jolly Moto India",
                "delivery_days": 5,
            },
            # --- Aprilia / Honda / Kawasaki / Suzuki 250 GP replica twins ---
            {
                "category": "exhaust",
                "brand": "Arrow",
                "model_name": "Arrow Expansion Chambers RS250 / RGV250 / NSR250",
                "part_number": "ARR-GP250-PIPE",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "stainless_steel",
                    "config": "twin_pipe",
                    "stroke_type": 2,
                    "weight_kg": 5.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8,
                    "engine.peak_torque_nm": 4,
                    "chassis.dry_mass_kg": -2.8,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 11200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia", "Honda", "Suzuki"],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Arrow GP-spec pipes for 250 V-twin 2T (RS250 / RGV250 / NSR250); 11.2k tuned peak",
                },
                "price_inr": 55000,
                "availability": "import_only",
                "retailer": "Arrow Europe",
                "delivery_days": 25,
            },
            {
                "category": "exhaust",
                "brand": "DEP Pipes",
                "model_name": "DEP S7 Expansion Chamber Aprilia RS125",
                "part_number": "DEP-S7-RS125",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "single_pipe",
                    "stroke_type": 2,
                    "weight_kg": 3.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 6,
                    "engine.peak_torque_nm": 3,
                    "chassis.dry_mass_kg": -1.8,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 11500,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 120,
                        "displacement_max_cc": 135,
                        "stroke_type": 2,
                    },
                    "description": "DEP S7 pipe for Aprilia RS125; race-spec, 11.5k tuned peak",
                },
                "price_inr": 22000,
                "availability": "import_only",
                "retailer": "DEP UK",
                "delivery_days": 14,
            },
            # --- Kawasaki triples & parallel twins ---
            {
                "category": "exhaust",
                "brand": "Higgspeed",
                "model_name": "Higgspeed Triple Chambers H2 Mach IV",
                "part_number": "HIG-KAW-H2-750",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "triple_pipe",
                    "stroke_type": 2,
                    "weight_kg": 12.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 15,
                    "engine.peak_torque_nm": 8,
                    "chassis.dry_mass_kg": -6.0,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 8200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 740,
                        "displacement_max_cc": 760,
                        "stroke_type": 2,
                    },
                    "description": "Higgspeed 3-pipe set for Kawasaki H2 Mach IV 750 triple 2T; widow-maker tamer",
                },
                "price_inr": 68000,
                "availability": "import_only",
                "retailer": "Higgspeed Cycles",
                "delivery_days": 35,
            },
            {
                "category": "exhaust",
                "brand": "Tyga Performance",
                "model_name": "Tyga Expansion Chambers KR-1S",
                "part_number": "TYG-KAW-KR1S",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "twin_pipe",
                    "stroke_type": 2,
                    "weight_kg": 5.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 7,
                    "engine.peak_torque_nm": 4,
                    "chassis.dry_mass_kg": -2.5,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 11000,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Tyga pipes for KR-1S 250 parallel twin 2T",
                },
                "price_inr": 52000,
                "availability": "import_only",
                "retailer": "Tyga Thailand",
                "delivery_days": 21,
            },
            # --- Suzuki RG500 / GT750 ---
            {
                "category": "exhaust",
                "brand": "Moto Carrera",
                "model_name": "Moto Carrera Quad Pipes RG500 Gamma",
                "part_number": "MC-SUZ-RG500",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "quad_pipe_square_four",
                    "stroke_type": 2,
                    "weight_kg": 11.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 20,
                    "engine.peak_torque_nm": 10,
                    "chassis.dry_mass_kg": -5.5,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 10200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4", "V4"],
                        "displacement_min_cc": 495,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Moto Carrera quad pipes for RG500 Gamma square-four 2T; GP-derived",
                },
                "price_inr": 72000,
                "availability": "import_only",
                "retailer": "Moto Carrera Italy",
                "delivery_days": 28,
            },
            # --- Suzuki GT750 water-cooled triple ---
            {
                "category": "exhaust",
                "brand": "MAC Exhaust",
                "model_name": "MAC 3-into-3 Expansion Chambers GT750",
                "part_number": "MAC-GT750-TRIPLE",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "triple_pipe",
                    "stroke_type": 2,
                    "weight_kg": 10.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 10,
                    "engine.peak_torque_nm": 6,
                    "chassis.dry_mass_kg": -5.0,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 7200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 725,
                        "displacement_max_cc": 760,
                        "stroke_type": 2,
                    },
                    "description": "MAC 3-pipe set for Suzuki GT750 water-cooled triple 2T; vintage-resto drag",
                },
                "price_inr": 62000,
                "availability": "import_only",
                "retailer": "MAC Exhaust USA",
                "delivery_days": 30,
            },
            # --- Yamaha TZR250 3MA reverse-cylinder ---
            {
                "category": "exhaust",
                "brand": "Tyga Performance",
                "model_name": "Tyga Expansion Chambers TZR250 3MA",
                "part_number": "TYG-YAM-TZR250-3MA",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "twin_pipe_reverse",
                    "stroke_type": 2,
                    "weight_kg": 5.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8,
                    "engine.peak_torque_nm": 4,
                    "chassis.dry_mass_kg": -2.5,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 11000,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Tyga pipes for Yamaha TZR250 3MA reverse-cylinder 2T parallel twin",
                },
                "price_inr": 54000,
                "availability": "import_only",
                "retailer": "Tyga Thailand",
                "delivery_days": 21,
            },
            # --- Yezdi 250 Classic (Indian heritage 2T twin) ---
            {
                "category": "exhaust",
                "brand": "Jolly Moto",
                "model_name": "Jolly Moto Chambers Yezdi 250 Classic",
                "part_number": "JM-YEZDI-250",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "twin_pipe",
                    "stroke_type": 2,
                    "weight_kg": 6.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4,
                    "engine.peak_torque_nm": 3,
                    "chassis.dry_mass_kg": -2.2,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 7500,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yezdi", "Ideal Jawa"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 240,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Jolly Moto pipes for Yezdi 250 Classic I2 2T twin — Indian classic drag",
                },
                "price_inr": 16500,
                "availability": "in_stock",
                "retailer": "Jolly Moto India",
                "delivery_days": 5,
            },
            # --- Motocross / enduro: KTM 300 EXC, 250 SX, CR500R ---
            {
                "category": "exhaust",
                "brand": "FMF Racing",
                "model_name": "FMF Gnarly Pipe KTM 300 EXC / 250 SX",
                "part_number": "FMF-GNARLY-KTM-300",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "single_pipe_low_mid",
                    "stroke_type": 2,
                    "weight_kg": 2.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3,
                    "engine.peak_torque_nm": 2,
                    "chassis.dry_mass_kg": -0.8,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 7800,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 310,
                        "stroke_type": 2,
                    },
                    "description": "FMF Gnarly for KTM 300 EXC / 250 SX; broad enduro powerband, low-mid bias",
                },
                "price_inr": 36000,
                "availability": "in_stock",
                "retailer": "FMF India",
                "delivery_days": 7,
            },
            {
                "category": "exhaust",
                "brand": "FMF Racing",
                "model_name": "FMF Fatty Pipe Honda CR500R",
                "part_number": "FMF-FATTY-CR500",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "single_pipe",
                    "stroke_type": 2,
                    "weight_kg": 3.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 5,
                    "engine.peak_torque_nm": 3,
                    "chassis.dry_mass_kg": -0.8,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 7200,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 480,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "FMF Fatty for CR500R MX 2T; wakes the beast — 7.2k peak",
                },
                "price_inr": 38000,
                "availability": "order",
                "retailer": "FMF Racing USA",
                "delivery_days": 14,
            },
            # --- Honda NS400R V3 2T (1985-1987 GP-derived street triple) ---
            {
                "category": "exhaust",
                "brand": "Tyga Performance",
                "model_name": "Tyga Expansion Chambers Honda NS400R",
                "part_number": "TYGA-NS400R-EX",
                "specs": {
                    "type": "expansion_chamber",
                    "material": "mild_steel",
                    "config": "triple_pipe",
                    "stroke_type": 2,
                    "weight_kg": 9.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8,
                    "engine.peak_torque_nm": 4,
                    "chassis.dry_mass_kg": -3.5,
                },
                "param_overrides": {
                    "engine.expansion_chamber": True,
                    "engine.tuned_rpm": 9800,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 380,
                        "displacement_max_cc": 400,
                        "stroke_type": 2,
                    },
                    "description": "Tyga triple-pipe set for Honda NS400R 90° V3 2T; race-spec, 9.8k peak",
                },
                "price_inr": 78000,
                "availability": "import_only",
                "retailer": "Tyga Performance Thailand",
                "delivery_days": 30,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # REED VALVES (6 parts)
    # VForce / Boyesen reed cages improve mid-range fill on case-reed 2T
    # engines. Multiplier applied to peak_power_hp (+2–4%).
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "air_filter",  # mapped to air/intake category
                "brand": "Moto Tassinari",
                "model_name": "VForce 4 Reed Cage KTM 250/300",
                "part_number": "MT-VF4-KTM-300",
                "specs": {
                    "type": "reed_valve",
                    "material": "carbon_fibre_petals",
                    "cage": "vforce_4_multi_stage",
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.035,
                    "engine.peak_torque_nm": 1.030,
                },
                "param_overrides": {"engine.reed_valve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 310,
                        "stroke_type": 2,
                    },
                    "description": "VForce 4 multi-stage reeds for KTM 250/300 2T; +3.5% power, wider powerband",
                },
                "price_inr": 17500,
                "availability": "in_stock",
                "retailer": "Moto Tassinari USA",
                "delivery_days": 10,
            },
            {
                "category": "air_filter",
                "brand": "Boyesen",
                "model_name": "Boyesen RAD Valve Honda CR500R",
                "part_number": "BOY-RAD-CR500",
                "specs": {
                    "type": "reed_valve",
                    "material": "fibreglass_petals",
                    "cage": "boyesen_rad_dual_stage",
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.030,
                    "engine.peak_torque_nm": 1.025,
                },
                "param_overrides": {"engine.reed_valve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 480,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Boyesen RAD dual-stage reeds for CR500R; smoother throttle response + power",
                },
                "price_inr": 13500,
                "availability": "order",
                "retailer": "Boyesen USA",
                "delivery_days": 12,
            },
            {
                "category": "air_filter",
                "brand": "Moto Tassinari",
                "model_name": "VForce 3 Reed Cage RGV250 / NSR250",
                "part_number": "MT-VF3-GP250",
                "specs": {
                    "type": "reed_valve",
                    "material": "carbon_fibre_petals",
                    "cage": "vforce_3",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.030},
                "param_overrides": {"engine.reed_valve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki", "Honda"],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "VForce 3 for RGV250 / NSR250 V-twin 2T; throttle response + top-end",
                },
                "price_inr": 19500,
                "availability": "import_only",
                "retailer": "Moto Tassinari USA",
                "delivery_days": 15,
            },
            {
                "category": "air_filter",
                "brand": "Boyesen",
                "model_name": "Boyesen Super Stock Reeds RD350 / RD400",
                "part_number": "BOY-SS-RD-400",
                "specs": {
                    "type": "reed_valve",
                    "material": "fibreglass",
                    "cage": "boyesen_super_stock",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "param_overrides": {"engine.reed_valve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 330,
                        "displacement_max_cc": 410,
                        "stroke_type": 2,
                    },
                    "description": "Boyesen replacement reeds for RD350/RD400 twins",
                },
                "price_inr": 9500,
                "availability": "import_only",
                "retailer": "Boyesen USA",
                "delivery_days": 14,
            },
            {
                "category": "air_filter",
                "brand": "VForce",
                "model_name": "VForce 3 Reed Cage Aprilia RS125",
                "part_number": "VF3-RS125",
                "specs": {
                    "type": "reed_valve",
                    "material": "carbon_fibre_petals",
                    "cage": "vforce_3",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.030},
                "param_overrides": {"engine.reed_valve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 120,
                        "displacement_max_cc": 135,
                        "stroke_type": 2,
                    },
                    "description": "VForce 3 for Aprilia RS125; crisp throttle, +3% power",
                },
                "price_inr": 15500,
                "availability": "import_only",
                "retailer": "VForce EU",
                "delivery_days": 14,
            },
            {
                "category": "air_filter",
                "brand": "Barikit",
                "model_name": "Barikit Reed Kit RX100 / RX135",
                "part_number": "BAR-REED-RX",
                "specs": {
                    "type": "reed_valve",
                    "material": "stainless_petals",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.020},
                "param_overrides": {"engine.reed_valve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 95,
                        "displacement_max_cc": 140,
                        "stroke_type": 2,
                    },
                    "description": "Barikit reed upgrade for RX100/RX135 — drag-scene mod",
                },
                "price_inr": 3500,
                "availability": "in_stock",
                "retailer": "Moto Madras Parts",
                "delivery_days": 4,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # POWERVALVE / RAVE / YPVS CONTROLLER UPGRADES (5 parts)
    # Zeeltronic / Nova Racing controllers override stock powervalve
    # opening curves — widens the powerband meaningfully (simulated as
    # small peak_power bump + powervalve override True).
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "ecu",
                "brand": "Zeeltronic",
                "model_name": "Zeeltronic PPV-YZR YPVS Controller RD500LC / TZR250",
                "part_number": "ZT-PPV-YPVS",
                "specs": {
                    "type": "programmable_powervalve_controller",
                    "valve_system": "YPVS",
                    "compatible": ["RD500LC", "RZV500R", "TZR250"],
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.025,
                    "engine.peak_torque_nm": 1.030,
                },
                "param_overrides": {"engine.powervalve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "year_min": 1983,
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2", "V4"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Zeeltronic YPVS controller for Yamaha 2T with powervalve; wider mid-range",
                },
                "price_inr": 28000,
                "availability": "order",
                "retailer": "Zeeltronic Slovenia",
                "delivery_days": 14,
            },
            {
                "category": "ecu",
                "brand": "Zeeltronic",
                "model_name": "Zeeltronic RAVE Controller Aprilia RS125 / RS250",
                "part_number": "ZT-PPV-RAVE",
                "specs": {
                    "type": "programmable_powervalve_controller",
                    "valve_system": "RAVE",
                    "compatible": ["RS125", "RS250"],
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.030,
                    "engine.peak_torque_nm": 1.025,
                },
                "param_overrides": {"engine.powervalve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["I1", "V2"],
                        "displacement_min_cc": 120,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Zeeltronic RAVE controller for Aprilia RS125/RS250; programmable opening curve",
                },
                "price_inr": 24000,
                "availability": "order",
                "retailer": "Zeeltronic Slovenia",
                "delivery_days": 14,
            },
            {
                "category": "ecu",
                "brand": "Zeeltronic",
                "model_name": "Zeeltronic RC-Valve Controller NSR250R MC21",
                "part_number": "ZT-PPV-RCV-MC21",
                "specs": {
                    "type": "programmable_powervalve_controller",
                    "valve_system": "HPP_RC_Valve",
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.030,
                    "engine.peak_torque_nm": 1.030,
                },
                "param_overrides": {"engine.powervalve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Zeeltronic RC Valve controller for NSR250R MC21 V-twin 2T",
                },
                "price_inr": 26000,
                "availability": "order",
                "retailer": "Zeeltronic Slovenia",
                "delivery_days": 14,
            },
            {
                "category": "ecu",
                "brand": "Nova Racing",
                "model_name": "Nova SAPC Powervalve Controller RGV250 VJ22",
                "part_number": "NOVA-SAPC-RGV-VJ22",
                "specs": {
                    "type": "powervalve_controller",
                    "valve_system": "SAPC",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.035},
                "param_overrides": {"engine.powervalve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Nova SAPC controller for RGV250 VJ22; race-proven",
                },
                "price_inr": 22000,
                "availability": "import_only",
                "retailer": "Nova Racing UK",
                "delivery_days": 21,
            },
            {
                "category": "ecu",
                "brand": "Zeeltronic",
                "model_name": "Zeeltronic KIPS Controller KR-1S",
                "part_number": "ZT-PPV-KIPS",
                "specs": {
                    "type": "programmable_powervalve_controller",
                    "valve_system": "KIPS",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "param_overrides": {"engine.powervalve": True},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Zeeltronic KIPS controller for Kawasaki KR-1S 250",
                },
                "price_inr": 24000,
                "availability": "order",
                "retailer": "Zeeltronic Slovenia",
                "delivery_days": 14,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # JET KITS / CARB REJET (5 parts)
    # Dynojet 2T Stage 1/2/3 — main + pilot jets, needle, slide.
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "fuel_system",
                "brand": "Dynojet",
                "model_name": "Dynojet Stage 2 Jet Kit RD350 / RD400",
                "part_number": "DJ-2T-RD-400",
                "specs": {
                    "type": "jet_kit",
                    "stage": 2,
                    "carb": "Mikuni_VM_28mm",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 330,
                        "displacement_max_cc": 410,
                        "stroke_type": 2,
                    },
                    "description": "Dynojet Stage 2 jet kit for RD350/RD400; pairs with expansion chambers",
                },
                "price_inr": 6500,
                "availability": "import_only",
                "retailer": "Dynojet USA",
                "delivery_days": 14,
            },
            {
                "category": "fuel_system",
                "brand": "Dynojet",
                "model_name": "Dynojet Stage 3 Jet Kit RGV250",
                "part_number": "DJ-2T-RGV-250",
                "specs": {
                    "type": "jet_kit",
                    "stage": 3,
                    "carb": "Mikuni_TM_32mm",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.030},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "Dynojet Stage 3 for RGV250; race-tuned + K&N filter needed",
                },
                "price_inr": 7800,
                "availability": "import_only",
                "retailer": "Dynojet USA",
                "delivery_days": 14,
            },
            {
                "category": "fuel_system",
                "brand": "JD Jetting",
                "model_name": "JD Jetting Kit KTM 250 SX / 300 EXC",
                "part_number": "JDJ-KTM-300",
                "specs": {
                    "type": "jet_kit",
                    "stage": 2,
                    "carb": "Keihin_PWK_38mm",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.020},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 310,
                        "stroke_type": 2,
                    },
                    "description": "JD Jetting for KTM 2T — adjustable needle for altitude compensation",
                },
                "price_inr": 5500,
                "availability": "order",
                "retailer": "JD Jetting USA",
                "delivery_days": 10,
            },
            {
                "category": "fuel_system",
                "brand": "Dynojet",
                "model_name": "Dynojet Stage 2 Jet Kit Aprilia RS125",
                "part_number": "DJ-2T-RS125",
                "specs": {
                    "type": "jet_kit",
                    "stage": 2,
                    "carb": "Dellorto_VHSB_34mm",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 120,
                        "displacement_max_cc": 135,
                        "stroke_type": 2,
                    },
                    "description": "Dynojet Stage 2 for RS125 Dellorto; pairs with DEP pipe",
                },
                "price_inr": 5900,
                "availability": "import_only",
                "retailer": "Dynojet EU",
                "delivery_days": 18,
            },
            {
                "category": "fuel_system",
                "brand": "RD Stuff",
                "model_name": "RD Stuff Performance Jet Kit RX100 / RX135",
                "part_number": "RDS-JET-RX",
                "specs": {
                    "type": "jet_kit",
                    "stage": 1,
                    "carb": "Mikuni_VM_20mm",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.018},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 95,
                        "displacement_max_cc": 140,
                        "stroke_type": 2,
                    },
                    "description": "RD Stuff jet kit for RX100/RX135 — Indian drag-scene standard",
                },
                "price_inr": 2800,
                "availability": "in_stock",
                "retailer": "RD Stuff India",
                "delivery_days": 3,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # HEAD MODS / COMPRESSION BUMPS (4 parts)
    # Machined squish-band, domed inserts — raises compression
    # (1.0 pt typical). Uses param_deltas on compression_ratio.
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "ecu",  # engine-section category — head mod maps here
                "brand": "Millennium Technologies",
                "model_name": "Mill-Tek Race Head KTM 300",
                "part_number": "MILL-KTM-300-HEAD",
                "specs": {
                    "type": "cylinder_head",
                    "squish_band_deg": 12,
                    "compression_bump": 1.2,
                    "stroke_type": 2,
                },
                "param_deltas": {"engine.compression_ratio": 1.2},
                "param_multipliers": {
                    "engine.peak_power_hp": 1.025,
                    "engine.peak_torque_nm": 1.030,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 310,
                        "stroke_type": 2,
                    },
                    "description": "Mill-Tek race head for KTM 300 — higher compression, optimized squish",
                },
                "price_inr": 21000,
                "availability": "order",
                "retailer": "Millennium Technologies USA",
                "delivery_days": 18,
            },
            {
                "category": "ecu",
                "brand": "Wiseco",
                "model_name": "Wiseco High-Comp Head Insert RD350",
                "part_number": "WIS-HEAD-RD-350",
                "specs": {
                    "type": "head_insert",
                    "compression_bump": 1.0,
                    "stroke_type": 2,
                },
                "param_deltas": {"engine.compression_ratio": 1.0},
                "param_multipliers": {"engine.peak_power_hp": 1.020},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 330,
                        "displacement_max_cc": 410,
                        "stroke_type": 2,
                    },
                    "description": "Wiseco high-compression head inserts for RD350/RD400",
                },
                "price_inr": 12500,
                "availability": "order",
                "retailer": "Wiseco USA",
                "delivery_days": 14,
            },
            {
                "category": "ecu",
                "brand": "Athena",
                "model_name": "Athena Big-Bore Head CR500R",
                "part_number": "ATH-CR500-HEAD",
                "specs": {
                    "type": "cylinder_head_big_bore",
                    "compression_bump": 1.0,
                    "stroke_type": 2,
                },
                "param_deltas": {"engine.compression_ratio": 1.0},
                "param_multipliers": {
                    "engine.peak_power_hp": 1.030,
                    "engine.peak_torque_nm": 1.040,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 480,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Athena big-bore head for CR500R — pairs with FMF Fatty",
                },
                "price_inr": 18500,
                "availability": "import_only",
                "retailer": "Athena Italy",
                "delivery_days": 21,
            },
            {
                "category": "ecu",
                "brand": "TM Racing",
                "model_name": "TM Race Head RGV250",
                "part_number": "TM-RGV250-HEAD",
                "specs": {
                    "type": "cylinder_head",
                    "compression_bump": 0.8,
                    "stroke_type": 2,
                },
                "param_deltas": {"engine.compression_ratio": 0.8},
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I2", "V2"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "TM race-spec head for RGV250 — V-twin 2T optimization",
                },
                "price_inr": 24500,
                "availability": "import_only",
                "retailer": "TM Racing Italy",
                "delivery_days": 25,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # 2T IGNITION UPGRADES (4 parts)
    # CDI / programmable ignition — timing curves that sharpen torque.
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "ecu",
                "brand": "Vape",
                "model_name": "Vape Digital CDI Ignition RD350 / RD400",
                "part_number": "VAPE-RD-CDI",
                "specs": {
                    "type": "cdi_ignition",
                    "programmable": True,
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.020,
                    "engine.peak_torque_nm": 1.015,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 330,
                        "displacement_max_cc": 410,
                        "stroke_type": 2,
                    },
                    "description": "Vape CDI for RD350/RD400 — replaces aging points + coils",
                },
                "price_inr": 28000,
                "availability": "import_only",
                "retailer": "Vape Germany",
                "delivery_days": 18,
            },
            {
                "category": "ecu",
                "brand": "HPI Racing",
                "model_name": "HPI Racing Stator + CDI RS125 / RS250",
                "part_number": "HPI-STATOR-RS-GP",
                "specs": {
                    "type": "race_stator_cdi_combo",
                    "programmable": True,
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["I1", "V2"],
                        "displacement_min_cc": 120,
                        "displacement_max_cc": 260,
                        "stroke_type": 2,
                    },
                    "description": "HPI race stator + CDI for RS125/RS250 — programmable timing",
                },
                "price_inr": 32000,
                "availability": "import_only",
                "retailer": "HPI Racing France",
                "delivery_days": 21,
            },
            {
                "category": "ecu",
                "brand": "Rex's Speed Shop",
                "model_name": "Rex's Ignition Upgrade CR500R",
                "part_number": "REX-CR500-IGN",
                "specs": {"type": "programmable_cdi", "stroke_type": 2},
                "param_multipliers": {"engine.peak_power_hp": 1.020},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 480,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Rex's Speed Shop programmable CDI for CR500R",
                },
                "price_inr": 19500,
                "availability": "import_only",
                "retailer": "Rex's Speed Shop USA",
                "delivery_days": 21,
            },
            {
                "category": "ecu",
                "brand": "Vape",
                "model_name": "Vape CDI Ignition RX100 / RX135",
                "part_number": "VAPE-RX-CDI",
                "specs": {"type": "cdi_ignition", "stroke_type": 2},
                "param_multipliers": {"engine.peak_power_hp": 1.015},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 95,
                        "displacement_max_cc": 140,
                        "stroke_type": 2,
                    },
                    "description": "Vape-style upgrade CDI for RX100/RX135 singles",
                },
                "price_inr": 8500,
                "availability": "order",
                "retailer": "Vape India",
                "delivery_days": 10,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # 2T CARBURETOR UPGRADES (4 parts)
    # Keihin PWK / Mikuni TMX flat-slide carbs — flow improvement.
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "fuel_system",
                "brand": "Keihin",
                "model_name": "Keihin PWK 38 Carburetor KTM 300 EXC",
                "part_number": "KEI-PWK-38-KTM",
                "specs": {
                    "type": "carburetor",
                    "diameter_mm": 38,
                    "slide_type": "flat",
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.030,
                    "engine.peak_torque_nm": 1.025,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 245,
                        "displacement_max_cc": 310,
                        "stroke_type": 2,
                    },
                    "description": "Keihin PWK 38 flat-slide for KTM 300 EXC; better throttle response",
                },
                "price_inr": 18500,
                "availability": "order",
                "retailer": "Keihin USA",
                "delivery_days": 12,
            },
            {
                "category": "fuel_system",
                "brand": "Mikuni",
                "model_name": "Mikuni TMX 38 Flat-Slide Carb CR500R",
                "part_number": "MIK-TMX-38-CR500",
                "specs": {
                    "type": "carburetor",
                    "diameter_mm": 38,
                    "slide_type": "flat",
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.035,
                    "engine.peak_torque_nm": 1.030,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 480,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Mikuni TMX 38 flat-slide for CR500R — big-bore 2T race-ready",
                },
                "price_inr": 22000,
                "availability": "import_only",
                "retailer": "Mikuni Japan",
                "delivery_days": 18,
            },
            {
                "category": "fuel_system",
                "brand": "Keihin",
                "model_name": "Keihin PWK 28 Carb Kit RS125",
                "part_number": "KEI-PWK-28-RS125",
                "specs": {
                    "type": "carburetor",
                    "diameter_mm": 28,
                    "slide_type": "flat",
                    "stroke_type": 2,
                },
                "param_multipliers": {"engine.peak_power_hp": 1.025},
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 120,
                        "displacement_max_cc": 135,
                        "stroke_type": 2,
                    },
                    "description": "Keihin PWK 28 for Aprilia RS125 — superior to stock Dellorto at high RPM",
                },
                "price_inr": 15500,
                "availability": "import_only",
                "retailer": "Keihin USA",
                "delivery_days": 14,
            },
            {
                "category": "fuel_system",
                "brand": "Mikuni",
                "model_name": "Mikuni VM 34 Twin Carbs RD500LC / RZV500R",
                "part_number": "MIK-VM-34-RD500",
                "specs": {
                    "type": "carburetor_set",
                    "quantity": 4,
                    "diameter_mm": 34,
                    "slide_type": "round",
                    "stroke_type": 2,
                },
                "param_multipliers": {
                    "engine.peak_power_hp": 1.025,
                    "engine.peak_torque_nm": 1.020,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4", "V4"],
                        "displacement_min_cc": 495,
                        "displacement_max_cc": 510,
                        "stroke_type": 2,
                    },
                    "description": "Mikuni VM 34 quad carbs for RD500LC / RZV500R",
                },
                "price_inr": 45000,
                "availability": "import_only",
                "retailer": "Mikuni Japan",
                "delivery_days": 21,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CREATE PARTS IN DATABASE
    # ══════════════════════════════════════════════════════════════

    return _create_parts_batch(db, parts, label="Two-Stroke Parts")
