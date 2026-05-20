"""
MotoQuant Pro — Adventure & Cruiser Exhaust Catalog Expansion
==============================================================
Seeds 27 bike-specific exhaust parts filling 22 large-displacement ADV/cruiser
bikes that were missing exhaust options in the main parts catalog.

Coverage (22 bikes):
  ADVENTURE TWINS/TRIPLES:
    - Suzuki V-Strom 650 / 1050 (I2)
    - Kawasaki Versys 650 / 1000 (I2/I4)
    - BMW F850GS / R1200GS / R1250GS (I2/boxer)
    - Moto Guzzi V85 TT (V2)
    - Triumph Tiger 900 Rally / Tiger 1200 GT Pro (I3)
    - Husqvarna Norden 901 (I2)
    - Honda CRF1100L Africa Twin (I2)
    - Yamaha Super Tenere XT1200Z (I2)
    - KTM 1290 Super Adventure R (V2)

  CRUISER BIG-BORE:
    - Honda Rebel 1100 (I2)
    - Indian Scout (I2 V-twin)
    - Indian FTR 1200 S (I2 V-twin)
    - Indian Chief Dark Horse (I2 V-twin)
    - Yamaha VMAX 1700 (I4)
    - Triumph Rocket 3 R (I3)
    - Benelli 502C (I2)

Fitment rules use tight `manufacturers` + `engine_configs` + displacement bounds
to prevent cross-brand/cross-segment leaks. No chain_pitch constraints (not needed
for ADV/cruiser exhausts; all these bikes are chain-drive except HD/Indian belt-drive,
which is handled by manufacturer-level rules).

Parts count: 27 exhausts (slip-on + full-system variants per bike/brand pairing).
Price range: ₹18,000–₹2,50,000 depending on brand/material tier.
"""


from motoquant.database.seed_catalogs import _create_parts_batch


def seed_adv_cruiser_exhausts(db) -> int:
    """
    Seeds adventure & cruiser exhaust parts.
    Returns count of parts created.
    """
    parts = []

    # ══════════════════════════════════════════════════════════════
    # ADVENTURE TWINS (I2, 600-1050cc)
    # ══════════════════════════════════════════════════════════════

    # Suzuki V-Strom 650 (DL650) — 645cc I2
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project CR-M Full System V-Strom 650",
                "part_number": "SCP-CRM-VS650-FS",
                "specs": {
                    "type": "full_system",
                    "material": "carbon_fiber",
                    "weight_kg": 3.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 6.5,
                    "engine.peak_torque_nm": 4.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 650,
                        "categories": ["adventure", "touring"],
                    },
                    "description": "SC-Project carbon full system for Suzuki V-Strom 650 I2 twin",
                },
                "price_inr": 185000,
                "availability": "import_only",
                "retailer": "SC-Project Europe",
                "delivery_days": 45,
            },
            {
                "category": "exhaust",
                "brand": "Arrow",
                "model_name": "Arrow Aluminum Slip-On V-Strom 650",
                "part_number": "AR-VS650-SLIP",
                "specs": {"type": "slip_on", "material": "aluminum", "weight_kg": 1.9},
                "param_deltas": {
                    "engine.peak_power_hp": 3.2,
                    "engine.peak_torque_nm": 2.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 650,
                        "categories": ["adventure", "touring"],
                    },
                    "description": "Arrow aluminum slip-on for Suzuki V-Strom 650 ADV twin",
                },
                "price_inr": 58000,
                "availability": "order",
                "retailer": "Arrow India",
                "delivery_days": 21,
            },
        ]
    )

    # Suzuki V-Strom 1050 (DL1050) — 1037cc I2
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Titanium Slip-On V-Strom 1050",
                "part_number": "AK-VS1050-SLIP-TI",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.1},
                "param_deltas": {
                    "engine.peak_power_hp": 4.5,
                    "engine.peak_torque_nm": 3.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1030,
                        "displacement_max_cc": 1050,
                        "categories": ["adventure", "touring"],
                    },
                    "description": "Akrapovic titanium slip-on for Suzuki V-Strom 1050 litre ADV",
                },
                "price_inr": 95000,
                "availability": "order",
                "retailer": "Akrapovic India",
                "delivery_days": 35,
            },
        ]
    )

    # Kawasaki Versys 650 (ER-6f based) — 649cc I2
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "LeoVince",
                "model_name": "LeoVince LV-10 Full System Versys 650",
                "part_number": "LV-VER650-FS",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 4.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 5.2,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                        "categories": ["adventure", "touring"],
                    },
                    "description": "LeoVince stainless full system for Kawasaki Versys 650 ADV",
                },
                "price_inr": 72000,
                "availability": "order",
                "retailer": "LeoVince India",
                "delivery_days": 28,
            },
        ]
    )

    # Kawasaki Versys 1000 (1043cc I4)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project CR-T Full System Versys 1000",
                "part_number": "SCP-CRT-VER1K-FS",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 4.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8.0,
                    "engine.peak_torque_nm": 5.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1040,
                        "displacement_max_cc": 1050,
                        "categories": ["adventure", "touring"],
                    },
                    "description": "SC-Project titanium full system for Kawasaki Versys 1000 I4 ADV",
                },
                "price_inr": 195000,
                "availability": "import_only",
                "retailer": "SC-Project Europe",
                "delivery_days": 50,
            },
        ]
    )

    # BMW F850GS (853cc I2 parallel twin)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project CR-M Full System F850GS",
                "part_number": "SCP-CRM-F850GS-FS",
                "specs": {
                    "type": "full_system",
                    "material": "carbon",
                    "weight_kg": 3.7,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 6.8,
                    "engine.peak_torque_nm": 4.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 850,
                        "displacement_max_cc": 860,
                        "categories": ["adventure"],
                    },
                    "description": "SC-Project carbon full system for BMW F850GS I2 ADV",
                },
                "price_inr": 180000,
                "availability": "import_only",
                "retailer": "SC-Project Europe",
                "delivery_days": 45,
            },
        ]
    )

    # BMW R1200GS & R1250GS (boxer twins, stored as I2)
    # R1200GS = 1170cc, R1250GS = 1254cc
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Titanium Slip-On R1200/R1250GS",
                "part_number": "AK-R12GS-SLIP-TI",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.4},
                "param_deltas": {
                    "engine.peak_power_hp": 5.5,
                    "engine.peak_torque_nm": 3.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1160,
                        "displacement_max_cc": 1260,
                        "categories": ["adventure"],
                    },
                    "description": "Akrapovic titanium slip-on for BMW R1200/R1250GS boxer twins",
                },
                "price_inr": 125000,
                "availability": "order",
                "retailer": "Akrapovic India",
                "delivery_days": 35,
            },
            {
                "category": "exhaust",
                "brand": "Remus",
                "model_name": "Remus Stainless Full System R1200GS",
                "part_number": "REM-R1200GS-FS",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 5.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.8,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1160,
                        "displacement_max_cc": 1175,
                        "categories": ["adventure"],
                    },
                    "description": "Remus stainless full system for BMW R1200GS twin-turbo boxer",
                },
                "price_inr": 95000,
                "availability": "order",
                "retailer": "Remus Germany",
                "delivery_days": 40,
            },
        ]
    )

    # Moto Guzzi V85 TT (853cc V2)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Agostini",
                "model_name": "Agostini Full System Moto Guzzi V85 TT",
                "part_number": "AGO-V85TT-FS",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 5.1,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 5.5,
                    "engine.peak_torque_nm": 4.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Moto Guzzi"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 850,
                        "displacement_max_cc": 860,
                        "categories": ["adventure"],
                    },
                    "description": "Agostini stainless full system for Moto Guzzi V85 TT adventure V2",
                },
                "price_inr": 68000,
                "availability": "order",
                "retailer": "Agostini Italy",
                "delivery_days": 35,
            },
        ]
    )

    # Triumph Tiger 900 Rally (I3, 888cc)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Titanium Slip-On Tiger 900",
                "part_number": "AK-TIGER900-SLIP-TI",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.3},
                "param_deltas": {
                    "engine.peak_power_hp": 5.0,
                    "engine.peak_torque_nm": 3.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Triumph"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 885,
                        "displacement_max_cc": 895,
                        "categories": ["adventure"],
                    },
                    "description": "Akrapovic titanium slip-on for Triumph Tiger 900 Rally I3 ADV",
                },
                "price_inr": 115000,
                "availability": "order",
                "retailer": "Akrapovic India",
                "delivery_days": 35,
            },
            {
                "category": "exhaust",
                "brand": "HP Corse",
                "model_name": "HP Corse Slip-On Tiger 900 Rally",
                "part_number": "HPC-TIGER900-SLIP",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.2},
                "param_deltas": {
                    "engine.peak_power_hp": 4.8,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Triumph"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 885,
                        "displacement_max_cc": 895,
                        "categories": ["adventure"],
                    },
                    "description": "HP Corse titanium slip-on for Triumph Tiger 900 Rally ADV",
                },
                "price_inr": 105000,
                "availability": "order",
                "retailer": "HP Corse Italy",
                "delivery_days": 40,
            },
        ]
    )

    # Triumph Tiger 1200 GT Pro (I3, 1160cc)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Racing Full System Tiger 1200",
                "part_number": "AK-TIGER1200-FS-TI",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 4.1,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 9.5,
                    "engine.peak_torque_nm": 6.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Triumph"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 1155,
                        "displacement_max_cc": 1165,
                        "categories": ["adventure"],
                    },
                    "description": "Akrapovic titanium full system for Triumph Tiger 1200 GT I3 litre ADV",
                },
                "price_inr": 215000,
                "availability": "import_only",
                "retailer": "Akrapovic Europe",
                "delivery_days": 45,
            },
        ]
    )

    # Husqvarna Norden 901 (I2, 889cc)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project CR-M Full System Norden 901",
                "part_number": "SCP-CRM-NORDEN-FS",
                "specs": {
                    "type": "full_system",
                    "material": "carbon",
                    "weight_kg": 3.9,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 7.2,
                    "engine.peak_torque_nm": 4.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Husqvarna"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 885,
                        "displacement_max_cc": 895,
                        "categories": ["adventure"],
                    },
                    "description": "SC-Project carbon full system for Husqvarna Norden 901 I2 ADV",
                },
                "price_inr": 175000,
                "availability": "import_only",
                "retailer": "SC-Project Europe",
                "delivery_days": 45,
            },
        ]
    )

    # Honda CRF1100L Africa Twin (1084cc I2)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Titanium Full System Africa Twin",
                "part_number": "AK-AFTATWIN-FS-TI",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 4.3,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8.5,
                    "engine.peak_torque_nm": 5.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1080,
                        "displacement_max_cc": 1090,
                        "categories": ["adventure"],
                    },
                    "description": "Akrapovic titanium full system for Honda CRF1100L Africa Twin I2 litre ADV",
                },
                "price_inr": 225000,
                "availability": "import_only",
                "retailer": "Akrapovic Europe",
                "delivery_days": 50,
            },
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project Slip-On Africa Twin",
                "part_number": "SCP-AFTATWIN-SLIP",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.5},
                "param_deltas": {
                    "engine.peak_power_hp": 5.0,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1080,
                        "displacement_max_cc": 1090,
                        "categories": ["adventure"],
                    },
                    "description": "SC-Project titanium slip-on for Honda CRF1100L Africa Twin ADV",
                },
                "price_inr": 125000,
                "availability": "order",
                "retailer": "SC-Project Europe",
                "delivery_days": 40,
            },
        ]
    )

    # Yamaha Super Tenere XT1200Z (1199cc I2)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Titanium Slip-On Super Tenere XT1200",
                "part_number": "AK-TENERE1200-SLIP-TI",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.4},
                "param_deltas": {
                    "engine.peak_power_hp": 5.2,
                    "engine.peak_torque_nm": 3.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1195,
                        "displacement_max_cc": 1205,
                        "categories": ["adventure", "touring"],
                    },
                    "description": "Akrapovic titanium slip-on for Yamaha XT1200Z Super Tenere I2 litre tourer",
                },
                "price_inr": 135000,
                "availability": "order",
                "retailer": "Akrapovic India",
                "delivery_days": 35,
            },
        ]
    )

    # KTM 1290 Super Adventure R (1301cc V2)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project CR-T Full System KTM 1290 SAR",
                "part_number": "SCP-CRT-1290SAR-FS",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 4.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 10.2,
                    "engine.peak_torque_nm": 7.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1295,
                        "displacement_max_cc": 1310,
                        "categories": ["adventure"],
                    },
                    "description": "SC-Project titanium full system for KTM 1290 Super Adventure R V2 litre ADV",
                },
                "price_inr": 245000,
                "availability": "import_only",
                "retailer": "SC-Project Europe",
                "delivery_days": 50,
            },
            {
                "category": "exhaust",
                "brand": "HP Corse",
                "model_name": "HP Corse Slip-On 1290 Super Adventure",
                "part_number": "HPC-1290SAR-SLIP",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.6},
                "param_deltas": {
                    "engine.peak_power_hp": 6.5,
                    "engine.peak_torque_nm": 4.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["KTM"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1295,
                        "displacement_max_cc": 1310,
                        "categories": ["adventure"],
                    },
                    "description": "HP Corse titanium slip-on for KTM 1290 Super Adventure R V2",
                },
                "price_inr": 155000,
                "availability": "order",
                "retailer": "HP Corse Italy",
                "delivery_days": 40,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CRUISER BIG-BORE (V2 & I4, 1000cc+)
    # ══════════════════════════════════════════════════════════════

    # Honda Rebel 1100 (1084cc I2 parallel twin)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Vance & Hines",
                "model_name": "Vance & Hines Hi-Output Rebel 1100",
                "part_number": "VH-REBEL1100-HO",
                "specs": {
                    "type": "full_system",
                    "material": "steel_chrome",
                    "weight_kg": 6.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.5,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1080,
                        "displacement_max_cc": 1090,
                        "categories": ["cruiser"],
                    },
                    "description": "Vance & Hines Hi-Output full system for Honda Rebel 1100 I2 cruiser",
                },
                "price_inr": 75000,
                "availability": "in_stock",
                "retailer": "Vance & Hines India",
                "delivery_days": 0,
            },
            {
                "category": "exhaust",
                "brand": "Two Brothers Racing",
                "model_name": "Two Brothers M-2 Slip-On Rebel 1100",
                "part_number": "TBR-REBEL1100-M2",
                "specs": {"type": "slip_on", "material": "aluminum", "weight_kg": 2.8},
                "param_deltas": {
                    "engine.peak_power_hp": 2.8,
                    "engine.peak_torque_nm": 1.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1080,
                        "displacement_max_cc": 1090,
                        "categories": ["cruiser"],
                    },
                    "description": "Two Brothers M-2 slip-on for Honda Rebel 1100 cruiser twin",
                },
                "price_inr": 42000,
                "availability": "in_stock",
                "retailer": "Two Brothers India",
                "delivery_days": 0,
            },
        ]
    )

    # Indian Scout (1133cc V-twin, belt-drive, 60° V2)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "S&S Cycle",
                "model_name": "S&S Cycle Grand National Full System Scout",
                "part_number": "SS-SCOUT-GN",
                "specs": {
                    "type": "full_system",
                    "material": "chrome_steel",
                    "weight_kg": 7.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 6.5,
                    "engine.peak_torque_nm": 5.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Indian"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1130,
                        "displacement_max_cc": 1140,
                        "categories": ["cruiser"],
                    },
                    "description": "S&S Cycle Grand National full system for Indian Scout V-twin cruiser",
                },
                "price_inr": 125000,
                "availability": "import_only",
                "retailer": "S&S Cycle USA",
                "delivery_days": 50,
            },
            {
                "category": "exhaust",
                "brand": "Cobra USA",
                "model_name": "Cobra Speedster Slip-On Scout",
                "part_number": "COBRA-SCOUT-SLIP",
                "specs": {"type": "slip_on", "material": "steel", "weight_kg": 3.2},
                "param_deltas": {
                    "engine.peak_power_hp": 3.5,
                    "engine.peak_torque_nm": 2.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Indian"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1130,
                        "displacement_max_cc": 1140,
                        "categories": ["cruiser"],
                    },
                    "description": "Cobra Speedster slip-on for Indian Scout V-twin",
                },
                "price_inr": 48000,
                "availability": "order",
                "retailer": "Cobra USA",
                "delivery_days": 35,
            },
        ]
    )

    # Indian FTR 1200 S (1203cc V-twin, chain-drive)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "S&S Cycle",
                "model_name": "S&S Cycle Slip-On FTR 1200",
                "part_number": "SS-FTR1200-SLIP",
                "specs": {"type": "slip_on", "material": "steel", "weight_kg": 3.0},
                "param_deltas": {
                    "engine.peak_power_hp": 4.0,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Indian"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1190,
                        "displacement_max_cc": 1220,
                        "categories": ["cruiser", "muscle", "naked", "sport"],
                    },
                    "description": "S&S Cycle slip-on for Indian FTR 1200 S performance cruiser",
                },
                "price_inr": 68000,
                "availability": "import_only",
                "retailer": "S&S Cycle USA",
                "delivery_days": 45,
            },
            {
                "category": "exhaust",
                "brand": "Vance & Hines",
                "model_name": "Vance & Hines 2-into-1 FTR 1200",
                "part_number": "VH-FTR1200-2IN1",
                "specs": {"type": "full_system", "material": "steel", "weight_kg": 6.5},
                "param_deltas": {
                    "engine.peak_power_hp": 5.8,
                    "engine.peak_torque_nm": 4.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Indian"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1190,
                        "displacement_max_cc": 1220,
                        "categories": ["cruiser", "muscle", "naked", "sport"],
                    },
                    "description": "Vance & Hines 2-into-1 full system for Indian FTR 1200 S V-twin",
                },
                "price_inr": 95000,
                "availability": "order",
                "retailer": "Vance & Hines India",
                "delivery_days": 40,
            },
        ]
    )

    # Indian Chief Dark Horse (1890cc V-twin Thunderstroke 111, belt-drive)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "S&S Cycle",
                "model_name": "S&S Cycle Tracer Grand National Chief Dark Horse",
                "part_number": "SS-CHIEF-GN-TRACE",
                "specs": {
                    "type": "full_system",
                    "material": "steel_chrome",
                    "weight_kg": 7.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8.5,
                    "engine.peak_torque_nm": 8.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Indian"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1880,
                        "displacement_max_cc": 1900,
                        "categories": ["cruiser"],
                    },
                    "description": "S&S Cycle Tracer Grand National full system for Indian Chief Dark Horse V-twin",
                },
                "price_inr": 185000,
                "availability": "import_only",
                "retailer": "S&S Cycle USA",
                "delivery_days": 55,
            },
            {
                "category": "exhaust",
                "brand": "Rinehart",
                "model_name": "Rinehart Racing Full System Chief",
                "part_number": "RH-CHIEF-FS",
                "specs": {"type": "full_system", "material": "steel", "weight_kg": 7.5},
                "param_deltas": {
                    "engine.peak_power_hp": 7.8,
                    "engine.peak_torque_nm": 7.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Indian"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1880,
                        "displacement_max_cc": 1900,
                        "categories": ["cruiser"],
                    },
                    "description": "Rinehart Racing full system for Indian Chief Dark Horse Thunderstroke 111",
                },
                "price_inr": 165000,
                "availability": "import_only",
                "retailer": "Rinehart USA",
                "delivery_days": 50,
            },
        ]
    )

    # Yamaha VMAX 1700 (1679cc I4 muscle bike)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Two Brothers Racing",
                "model_name": "Two Brothers M-1 Full System VMAX 1700",
                "part_number": "TBR-VMAX1700-M1FS",
                "specs": {
                    "type": "full_system",
                    "material": "aluminum",
                    "weight_kg": 5.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 7.5,
                    "engine.peak_torque_nm": 5.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1670,
                        "displacement_max_cc": 1690,
                        "categories": ["cruiser"],
                    },
                    "description": "Two Brothers M-1 full system for Yamaha VMAX 1700 I4 muscle cruiser",
                },
                "price_inr": 128000,
                "availability": "import_only",
                "retailer": "Two Brothers USA",
                "delivery_days": 45,
            },
            {
                "category": "exhaust",
                "brand": "LCE Racing",
                "model_name": "LCE Drag Exhaust VMAX 1700",
                "part_number": "LCE-VMAX1700-DRAG",
                "specs": {"type": "full_system", "material": "steel", "weight_kg": 6.2},
                "param_deltas": {
                    "engine.peak_power_hp": 6.8,
                    "engine.peak_torque_nm": 4.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1670,
                        "displacement_max_cc": 1690,
                        "categories": ["cruiser"],
                    },
                    "description": "LCE Racing drag exhaust for Yamaha VMAX 1700 muscle muscle-bike",
                },
                "price_inr": 105000,
                "availability": "import_only",
                "retailer": "LCE Racing",
                "delivery_days": 50,
            },
        ]
    )

    # Triumph Rocket 3 R (2458cc I3 triple muscle-bike)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Agency Power",
                "model_name": "Agency Power Full System Rocket 3",
                "part_number": "AP-ROCKET3-FS",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 5.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 12.0,
                    "engine.peak_torque_nm": 10.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Triumph"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 2450,
                        "displacement_max_cc": 2470,
                        "categories": ["cruiser"],
                    },
                    "description": "Agency Power titanium full system for Triumph Rocket 3 R triple muscle-bike",
                },
                "price_inr": 250000,
                "availability": "import_only",
                "retailer": "Agency Power USA",
                "delivery_days": 55,
            },
            {
                "category": "exhaust",
                "brand": "Toce Performance",
                "model_name": "Toce Performance Slip-On Rocket 3",
                "part_number": "TOCE-ROCKET3-SLIP",
                "specs": {"type": "slip_on", "material": "titanium", "weight_kg": 2.8},
                "param_deltas": {
                    "engine.peak_power_hp": 6.5,
                    "engine.peak_torque_nm": 5.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Triumph"],
                        "engine_configs": ["I3"],
                        "displacement_min_cc": 2450,
                        "displacement_max_cc": 2470,
                        "categories": ["cruiser"],
                    },
                    "description": "Toce Performance titanium slip-on for Triumph Rocket 3 R muscle triple",
                },
                "price_inr": 165000,
                "availability": "import_only",
                "retailer": "Toce Performance USA",
                "delivery_days": 50,
            },
        ]
    )

    # Kawasaki Vulcan S (649cc I2 parallel twin cruiser)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Two Brothers Racing",
                "model_name": "Two Brothers M-2 Full System Vulcan S",
                "part_number": "TBR-VULCAN-S-M2",
                "specs": {
                    "type": "full_system",
                    "material": "aluminum",
                    "weight_kg": 4.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.8,
                    "engine.peak_torque_nm": 2.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 645,
                        "displacement_max_cc": 655,
                        "categories": ["cruiser"],
                    },
                    "description": "Two Brothers M-2 full system for Kawasaki Vulcan S I2 cruiser twin",
                },
                "price_inr": 68000,
                "availability": "order",
                "retailer": "Two Brothers India",
                "delivery_days": 25,
            },
        ]
    )

    # Benelli 502C (500cc I2 cruiser twin)
    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "FMF Racing",
                "model_name": "FMF Powercore IV Benelli 502C",
                "part_number": "FMF-502C-SLIP",
                "specs": {"type": "slip_on", "material": "aluminum", "weight_kg": 1.5},
                "param_deltas": {
                    "engine.peak_power_hp": 2.2,
                    "engine.peak_torque_nm": 1.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Benelli"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 495,
                        "displacement_max_cc": 510,
                        "categories": ["cruiser"],
                    },
                    "description": "FMF Powercore IV slip-on for Benelli 502C I2 cruiser twin",
                },
                "price_inr": 32000,
                "availability": "order",
                "retailer": "FMF Asia",
                "delivery_days": 20,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CREATE PARTS IN DATABASE
    # ══════════════════════════════════════════════════════════════

    return _create_parts_batch(db, parts, label="ADV/Cruiser Exhausts")
