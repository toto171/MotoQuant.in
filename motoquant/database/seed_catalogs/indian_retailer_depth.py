"""
MotoQuant Pro — Indian Retailer Depth Parts Catalog
====================================================
Seeds ~85 high-depth Indian-market performance parts across 14 categories:
  - Exhausts (20 parts): slip-on + full systems for Indian 200-650cc platforms
  - Air filters (12 parts): K&N, BMC, DNA, Sprint Filter (commuter to litre)
  - Sprockets & chains (10 parts): JT, IRC, RK, Diamond, Rolon (428-530 pitch)
  - ECU / piggyback (12 parts): Power Commander, Bazzaz, Healtech, Aracer RC mini
  - Suspension (10 parts): KYB, Showa, YSS, K-Tech, Öhlins (importable)
  - Brakes (10 parts): Brembo, Bybre, EBC, Ferodo, Galfer (pads + rotors)
  - Battery (8 parts): Shorai, Antigravity, Amaron, Exide, Yuasa (lithium/lead)
  - Clutch (6 parts): Surflex, EBC, Newfren, Barnett slipper/heavy-duty
  - Quickshifter (5 parts): Translogic, Healtech, SP Engineering, Nextshift
  - Fuel system (5 parts): Bosch fuel pump, Radium regulators, Aeromotive (turbocharged)

Price range: ₹2k–₹3L+ depending on brand prestige and import duty on premium European brands.
All fitment rules use tight `manufacturers` + `engine_configs` + displacement + `chain_pitch`
to prevent cross-segment leaks (e.g., R15 filters ≠ Hayabusa filters, RE 650 ≠ RE 350 parts).

# REGISTERED in motoquant/database/seed.py:seed_all() (Apr 27, 2026 orchestrator merge)
"""

from motoquant.database.seed_catalogs import _create_parts_batch


def seed_indian_retailer_depth(db) -> int:
    """
    Seeds deep Indian-market retailer parts across 14 categories.
    Returns count of parts created.
    """
    parts = []

    # ══════════════════════════════════════════════════════════════
    # EXHAUSTS — SLIP-ON & FULL SYSTEMS (20 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "exhaust",
                "brand": "Red Rooster Performance",
                "model_name": "RRP Slip-On Yamaha R15 V4 (155cc)",
                "part_number": "RRP-EX-R15V4-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "stainless_steel",
                    "weight_kg": 1.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.2,
                    "chassis.dry_mass_kg": -2.4,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 145,
                        "displacement_max_cc": 165,
                        "chain_pitch": "428",
                    },
                },
                "price_inr": 17500,
                "mrp_inr": 20000,
                "retailer": "Red Rooster Performance",
                "retailer_url": "https://redrooster.com/exhausts/r15",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "exhaust",
                "brand": "KustomHub",
                "model_name": "KustomHub Full System Bajaj Pulsar NS200 (200cc)",
                "part_number": "KH-EX-NS200-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 3.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 2.8,
                    "chassis.dry_mass_kg": -3.1,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Bajaj"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 195,
                        "displacement_max_cc": 210,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 22500,
                "mrp_inr": 26000,
                "retailer": "KustomHub",
                "retailer_url": "https://customhub.in/exhausts",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Slip-On Royal Enfield Interceptor 650",
                "part_number": "AKR-RE650-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "titanium",
                    "weight_kg": 2.1,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.5,
                    "engine.peak_torque_nm": 2.8,
                    "chassis.dry_mass_kg": -2.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 58000,
                "mrp_inr": 68000,
                "retailer": "Powertec (Akrapovic Official)",
                "retailer_url": "https://powertec.in/akrapovic",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "exhaust",
                "brand": "Arrow",
                "model_name": "Arrow Full System Ducati Panigale V4R (1103cc)",
                "part_number": "ARR-PANI-V4R-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 4.1,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 9.2,
                    "engine.peak_torque_nm": 4.5,
                    "chassis.dry_mass_kg": -4.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        # Widened to the full V4 window (patch_2026_06_11 B): the
                        # 1100 floor missed the 998cc Panigale V4R this is named for.
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 185000,
                "mrp_inr": 215000,
                "retailer": "Performance Racing Store (Arrow Official)",
                "retailer_url": "https://performanceracing.in/arrow",
                "availability": "order",
                "estimated_delivery_days": 28,
            },
            {
                "category": "exhaust",
                "brand": "SC-Project",
                "model_name": "SC-Project CR-M Full Yamaha YZF-R1 (998cc)",
                "part_number": "SCP-R1-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "carbon_fiber",
                    "weight_kg": 3.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8.5,
                    "engine.peak_torque_nm": 4.2,
                    "chassis.dry_mass_kg": -3.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 195000,
                "mrp_inr": 225000,
                "retailer": "Performance Racing Store (SC-Project Official)",
                "retailer_url": "https://performanceracing.in/sc-project",
                "availability": "import_only",
                "estimated_delivery_days": 21,
            },
            {
                "category": "exhaust",
                "brand": "Yoshimura",
                "model_name": "Yoshimura Race Full System Suzuki GSX-R1000 (999cc)",
                "part_number": "YSM-GSXR1K-RACE",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 3.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 12.0,
                    "engine.peak_torque_nm": 5.5,
                    "chassis.dry_mass_kg": -4.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 145000,
                "mrp_inr": 165000,
                "retailer": "Motoworld Bangalore",
                "retailer_url": "https://motoworld.in/yoshimura",
                "availability": "order",
                "estimated_delivery_days": 28,
            },
            {
                "category": "exhaust",
                "brand": "Two Brothers Racing",
                "model_name": "Two Brothers Slip-On Suzuki Hayabusa (1299cc)",
                "part_number": "TBR-HAYABUSA-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "titanium",
                    "weight_kg": 3.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 6.5,
                    "engine.peak_torque_nm": 3.2,
                    "chassis.dry_mass_kg": -3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 125000,
                "mrp_inr": 145000,
                "retailer": "Big Bird Performance (Bangalore)",
                "retailer_url": "https://bigbirdperformance.com",
                "availability": "order",
                "estimated_delivery_days": 21,
            },
            {
                "category": "exhaust",
                "brand": "Termignoni",
                "model_name": "Termignoni Full System Kawasaki ZX-10R (998cc)",
                "part_number": "TRM-ZX10R-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 4.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 10.5,
                    "engine.peak_torque_nm": 5.0,
                    "chassis.dry_mass_kg": -3.9,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 175000,
                "mrp_inr": 205000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in/termignoni",
                "availability": "order",
                "estimated_delivery_days": 25,
            },
            {
                "category": "exhaust",
                "brand": "LeoVince",
                "model_name": "LeoVince LV One Aprilia RSV4 Factory (1000cc)",
                "part_number": "LEO-RSV4-LVONE",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 3.6,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 8.8,
                    "engine.peak_torque_nm": 4.1,
                    "chassis.dry_mass_kg": -3.9,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 165000,
                "mrp_inr": 190000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in/leovince",
                "availability": "import_only",
                "estimated_delivery_days": 35,
            },
            {
                "category": "exhaust",
                "brand": "HP Corse",
                "model_name": "HP Corse Slip-On BMW M1000RR (999cc)",
                "part_number": "HPC-M1KRR-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "stainless_steel",
                    "weight_kg": 3.2,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 5.5,
                    "engine.peak_torque_nm": 2.8,
                    "chassis.dry_mass_kg": -3.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 155000,
                "mrp_inr": 180000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 28,
            },
            {
                "category": "exhaust",
                "brand": "Remus",
                "model_name": "Remus Slip-On BMW R1250GS (1254cc)",
                "part_number": "REM-R1250GS-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "stainless_steel",
                    "weight_kg": 2.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.2,
                    "engine.peak_torque_nm": 2.5,
                    "chassis.dry_mass_kg": -2.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 1245,
                        "displacement_max_cc": 1265,
                    },
                },
                "price_inr": 95000,
                "mrp_inr": 110000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 21,
            },
            {
                "category": "exhaust",
                "brand": "S&S Cycle",
                "model_name": "S&S Cycle Slip-On Harley-Davidson Low Rider ST (1868cc)",
                "part_number": "SAS-LRST-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "chrome",
                    "weight_kg": 4.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.2,
                    "engine.peak_torque_nm": 3.8,
                    "chassis.dry_mass_kg": -2.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        # Low Rider ST is the 117ci (1923cc) M-8 — the 1860-1880
                        # window missed it. Widened per patch_2026_06_11 M.
                        "manufacturers": ["Harley-Davidson", "HD", "Harley"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1900,
                        "displacement_max_cc": 1940,
                        "chain_pitch": None,
                    },
                },
                "price_inr": 125000,
                "mrp_inr": 145000,
                "retailer": "Harley-Davidson India",
                "retailer_url": "https://harley-davidson.in",
                "availability": "order",
                "estimated_delivery_days": 35,
            },
            {
                "category": "exhaust",
                "brand": "Vance & Hines",
                "model_name": "Vance & Hines Hi-Output 2-into-1 Indian Scout Bobber (1133cc)",
                "part_number": "VAH-SCOUT-HIO",
                "specs": {
                    "type": "full_system",
                    "material": "steel",
                    "weight_kg": 5.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.5,
                    "engine.peak_torque_nm": 2.9,
                    "chassis.dry_mass_kg": -1.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        # The manufacturers table stores this brand as bare
                        # 'Indian' — accept both so the Scout matches
                        # (patch_2026_06_11 N).
                        "manufacturers": ["Indian", "Indian Motorcycle"],
                        "engine_configs": ["V2"],
                        "displacement_min_cc": 1120,
                        "displacement_max_cc": 1150,
                        "chain_pitch": None,
                    },
                },
                "price_inr": 95000,
                "mrp_inr": 110000,
                "retailer": "Import Distributor",
                "retailer_url": "https://importdist.in",
                "availability": "order",
                "estimated_delivery_days": 42,
            },
            {
                "category": "exhaust",
                "brand": "Akrapovic",
                "model_name": "Akrapovic Full System Honda CB350H'ness (350cc)",
                "part_number": "AKR-CB350-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "titanium",
                    "weight_kg": 2.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.8,
                    "engine.peak_torque_nm": 2.2,
                    "chassis.dry_mass_kg": -2.7,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 345,
                        "displacement_max_cc": 360,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 48000,
                "mrp_inr": 55000,
                "retailer": "Powertec (Akrapovic Official)",
                "retailer_url": "https://powertec.in/akrapovic",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "exhaust",
                "brand": "TFC",
                "model_name": "TFC Full System TVS Apache RR 310",
                "part_number": "TFC-APACHE310-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "stainless_steel",
                    "weight_kg": 2.8,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.2,
                    "chassis.dry_mass_kg": -2.5,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["TVS"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 305,
                        "displacement_max_cc": 315,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 24500,
                "mrp_inr": 28000,
                "retailer": "TFC",
                "retailer_url": "https://tfcexhausts.in",
                "availability": "in_stock",
                "estimated_delivery_days": 5,
            },
            {
                "category": "exhaust",
                "brand": "Daytona Sports",
                "model_name": "Daytona Full System Hero Xtreme 160R (160cc)",
                "part_number": "DYS-XTREME160-FULL",
                "specs": {
                    "type": "full_system",
                    "material": "mild_steel",
                    "weight_kg": 2.5,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.8,
                    "chassis.dry_mass_kg": -1.9,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Hero"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 155,
                        "displacement_max_cc": 165,
                        "chain_pitch": "428",
                    },
                },
                "price_inr": 9500,
                "mrp_inr": 11000,
                "retailer": "Daytona Sports (Chennai)",
                "retailer_url": "https://daytonasports.in",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "exhaust",
                "brand": "Trishul",
                "model_name": "Trishul Slip-On Honda CB300R (286cc)",
                "part_number": "TSL-CB300R-SLP",
                "specs": {
                    "type": "slip_on",
                    "material": "stainless_steel",
                    "weight_kg": 1.9,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 2.1,
                    "chassis.dry_mass_kg": -2.1,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 280,
                        "displacement_max_cc": 300,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 16500,
                "mrp_inr": 19000,
                "retailer": "Trishul (Pune)",
                "retailer_url": "https://trishul.in",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # AIR FILTERS (12 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "air_filter",
                "brand": "K&N",
                "model_name": "K&N Air Filter Yamaha R15 V4 (155cc)",
                "part_number": "KAN-R15V4-RF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 58,
                    "height_mm": 65,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 0.8,
                    "chassis.dry_mass_kg": -0.15,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 145,
                        "displacement_max_cc": 165,
                    },
                },
                "price_inr": 3200,
                "mrp_inr": 3800,
                "retailer": "K&N India Direct",
                "retailer_url": "https://kanfilters.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "air_filter",
                "brand": "BMC",
                "model_name": "BMC Air Filter Bajaj Pulsar NS200 (200cc)",
                "part_number": "BMC-NS200-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 65,
                    "height_mm": 75,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.2,
                    "chassis.dry_mass_kg": -0.18,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Bajaj"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 195,
                        "displacement_max_cc": 210,
                    },
                },
                "price_inr": 4100,
                "mrp_inr": 4900,
                "retailer": "Performance Racing Store (BMC Official)",
                "retailer_url": "https://performanceracing.in/bmc",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "air_filter",
                "brand": "K&N",
                "model_name": "K&N Air Filter Royal Enfield Interceptor 650 (650cc)",
                "part_number": "KAN-RE650-RF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 76,
                    "height_mm": 102,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 2.1,
                    "chassis.dry_mass_kg": -0.25,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                    },
                },
                "price_inr": 6800,
                "mrp_inr": 8000,
                "retailer": "K&N India Direct",
                "retailer_url": "https://kanfilters.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "air_filter",
                "brand": "DNA",
                "model_name": "DNA Air Filter Yamaha YZF-R1 (998cc)",
                "part_number": "DNA-R1-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 82,
                    "height_mm": 115,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.5,
                    "chassis.dry_mass_kg": -0.32,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 8900,
                "mrp_inr": 10500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "import_only",
                "estimated_delivery_days": 12,
            },
            {
                "category": "air_filter",
                "brand": "Sprint Filter",
                "model_name": "Sprint Filter Air Filter Suzuki GSX-R1000 (999cc)",
                "part_number": "SPR-GSXR1K-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 82,
                    "height_mm": 115,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.8,
                    "chassis.dry_mass_kg": -0.30,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 9200,
                "mrp_inr": 10800,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "air_filter",
                "brand": "ProRam",
                "model_name": "ProRam Intake System Suzuki Hayabusa (1299cc)",
                "part_number": "PRM-HAYABUSA-INT",
                "specs": {
                    "type": "full_intake",
                    "material": "aluminum",
                    "diameter_mm": 89,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.2,
                    "chassis.dry_mass_kg": -0.45,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 18500,
                "mrp_inr": 22000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 28,
            },
            {
                "category": "air_filter",
                "brand": "K&N",
                "model_name": "K&N Air Filter Honda CB300R (286cc)",
                "part_number": "KAN-CB300R-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 68,
                    "height_mm": 85,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 0.9,
                    "chassis.dry_mass_kg": -0.20,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 280,
                        "displacement_max_cc": 300,
                    },
                },
                "price_inr": 3500,
                "mrp_inr": 4200,
                "retailer": "K&N India Direct",
                "retailer_url": "https://kanfilters.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "air_filter",
                "brand": "Pipercross",
                "model_name": "Pipercross Air Filter Ducati Panigale V4R (1103cc)",
                "part_number": "PCR-PANIV4R-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 80,
                    "height_mm": 110,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.2,
                    "chassis.dry_mass_kg": -0.35,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 12500,
                "mrp_inr": 14800,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "air_filter",
                "brand": "BMC",
                "model_name": "BMC Air Filter TVS Apache RR 310 (312cc)",
                "part_number": "BMC-APACHE310-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 72,
                    "height_mm": 92,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.5,
                    "chassis.dry_mass_kg": -0.22,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["TVS"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 305,
                        "displacement_max_cc": 315,
                    },
                },
                "price_inr": 4500,
                "mrp_inr": 5400,
                "retailer": "Performance Racing Store (BMC Official)",
                "retailer_url": "https://performanceracing.in",
                "availability": "in_stock",
                "estimated_delivery_days": 4,
            },
            {
                "category": "air_filter",
                "brand": "K&N",
                "model_name": "K&N Air Filter Kawasaki ZX-10R (998cc)",
                "part_number": "KAN-ZX10R-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 82,
                    "height_mm": 115,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.6,
                    "chassis.dry_mass_kg": -0.32,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 9100,
                "mrp_inr": 10700,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "import_only",
                "estimated_delivery_days": 14,
            },
            {
                "category": "air_filter",
                "brand": "DNA",
                "model_name": "DNA Air Filter BMW M1000RR (999cc)",
                "part_number": "DNA-M1KRR-AF",
                "specs": {
                    "type": "reusable_cotton",
                    "diameter_mm": 82,
                    "height_mm": 115,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.4,
                    "chassis.dry_mass_kg": -0.30,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 9800,
                "mrp_inr": 11500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # SPROCKETS & CHAINS (10 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "sprocket",
                "brand": "JT Sprockets",
                "model_name": "JT 520 Front Sprocket 16T Indian Small-cc",
                "part_number": "JTS-520-F16",
                "specs": {
                    "pitch": "520",
                    "teeth": 16,
                    "material": "aluminum",
                    "position": "front",  # patch_2026_07_03
                },
                "param_overrides": {
                    "drivetrain.front_sprocket": 16,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha", "Bajaj", "TVS", "KTM", "Kawasaki"],
                        "displacement_min_cc": 150,
                        "displacement_max_cc": 400,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 2200,
                "mrp_inr": 2600,
                "retailer": "JT Sprockets India",
                "retailer_url": "https://jtsprockets.in",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "sprocket",
                "brand": "JT Sprockets",
                "model_name": "JT 530 Front Sprocket 17T Litre Sport",
                "part_number": "JTS-530-F17",
                "specs": {
                    "pitch": "530",
                    "teeth": 17,
                    "material": "aluminum",
                    "position": "front",  # patch_2026_07_03
                },
                "param_overrides": {
                    "drivetrain.front_sprocket": 17,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": [
                            "Yamaha",
                            "Suzuki",
                            "Honda",
                            "Kawasaki",
                            "BMW",
                            "Ducati",
                            "Aprilia",
                        ],
                        "displacement_min_cc": 900,
                        "displacement_max_cc": 1350,
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 3100,
                "mrp_inr": 3700,
                "retailer": "JT Sprockets India",
                "retailer_url": "https://jtsprockets.in",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "chain",
                "brand": "IRC",
                "model_name": "IRC 520 Chain Pro Street 120L",
                "part_number": "IRC-520-120-PS",
                "specs": {
                    "pitch": "520",
                    "length_links": 120,
                    "type": "o_ring",
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.35,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 8500,
                "mrp_inr": 10000,
                "retailer": "IRC India (KTM OEM Partner)",
                "retailer_url": "https://ircindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "chain",
                "brand": "RK Excel",
                "model_name": "RK Excel 530 Chain GB O-Ring 120L",
                "part_number": "RKE-530-120-GB",
                "specs": {
                    "pitch": "530",
                    "length_links": 120,
                    "type": "o_ring",
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.40,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 11500,
                "mrp_inr": 13500,
                "retailer": "RK Excel India Distributor",
                "retailer_url": "https://rkexcelindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 4,
            },
            {
                "category": "sprocket",
                "brand": "Diamond Chain",
                "model_name": "Diamond Chain 428 Rear Sprocket 45T Small-cc",
                "part_number": "DC-428-R45",
                "specs": {
                    "pitch": "428",
                    "teeth": 45,
                    "material": "steel",
                    "position": "rear",  # patch_2026_07_03
                },
                "param_overrides": {
                    "drivetrain.rear_sprocket": 45,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha", "Bajaj", "Hero", "Honda", "TVS"],
                        "displacement_min_cc": 100,
                        "displacement_max_cc": 250,
                        "chain_pitch": "428",
                    },
                },
                "price_inr": 1800,
                "mrp_inr": 2100,
                "retailer": "Diamond Chain Distributor",
                "retailer_url": "https://diamondchain.in",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "sprocket",
                "brand": "Rolon",
                "model_name": "Rolon 520 Rear Sprocket 43T Mid-cc",
                "part_number": "ROL-520-R43",
                "specs": {
                    "pitch": "520",
                    "teeth": 43,
                    "material": "steel",
                    "position": "rear",  # patch_2026_07_03
                },
                "param_overrides": {
                    "drivetrain.rear_sprocket": 43,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki", "Suzuki", "Honda"],
                        "displacement_min_cc": 400,
                        "displacement_max_cc": 700,
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 2500,
                "mrp_inr": 2900,
                "retailer": "Rolon India",
                "retailer_url": "https://rolonsprockets.in",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "chain",
                "brand": "Daido Kogyo",
                "model_name": "Daido Kogyo 530 Chain VX2 O-Ring 120L",
                "part_number": "DAI-530-120-VX2",
                "specs": {
                    "pitch": "530",
                    "length_links": 120,
                    "type": "o_ring",
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.38,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 13200,
                "mrp_inr": 15500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "sprocket",
                "brand": "JT Sprockets",
                "model_name": "JT 530 Rear Sprocket 42T Litre Sport (Hayabusa Gearing)",
                "part_number": "JTS-530-R42",
                "specs": {
                    "pitch": "530",
                    "teeth": 42,
                    "material": "aluminum",
                    "position": "rear",  # patch_2026_07_03
                },
                "param_overrides": {
                    "drivetrain.rear_sprocket": 42,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "displacement_min_cc": 900,
                        "displacement_max_cc": 1350,
                        "chain_pitch": "530",
                    },
                },
                "price_inr": 4200,
                "mrp_inr": 4900,
                "retailer": "JT Sprockets India",
                "retailer_url": "https://jtsprockets.in",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "chain",
                "brand": "LIPL (Lipi)",
                "model_name": "LIPL 520 Chain Standard 120L",
                "part_number": "LIP-520-120-STD",
                "specs": {
                    "pitch": "520",
                    "length_links": 120,
                    "type": "standard",
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.33,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "chain_pitch": "520",
                    },
                },
                "price_inr": 6500,
                "mrp_inr": 7800,
                "retailer": "LIPL India",
                "retailer_url": "https://liplchains.in",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # ECU / PIGGYBACK (12 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "ecu",
                "brand": "Power Commander",
                "model_name": "Power Commander V Yamaha R15 V4 (155cc)",
                "part_number": "PCV-R15V4",
                "specs": {
                    "type": "piggyback_ecu",
                    "channels": 6,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.8,
                    "engine.peak_torque_nm": 1.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I1"],
                        "displacement_min_cc": 145,
                        "displacement_max_cc": 165,
                    },
                },
                "price_inr": 28000,
                "mrp_inr": 32000,
                "retailer": "Performance Racing Store (Dynojet Official)",
                "retailer_url": "https://performanceracing.in/dynojet",
                "availability": "order",
                "estimated_delivery_days": 10,
            },
            {
                "category": "ecu",
                "brand": "Bazzaz",
                "model_name": "Bazzaz Z-Fi Fuel Controller Suzuki Hayabusa (1299cc)",
                "part_number": "BAZ-HAYABUSA-ZFI",
                "specs": {
                    "type": "piggyback_fuel",
                    "channels": 8,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.2,
                    "engine.peak_torque_nm": 2.1,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 52000,
                "mrp_inr": 61000,
                "retailer": "Performance Racing Store (Bazzaz Official)",
                "retailer_url": "https://performanceracing.in/bazzaz",
                "availability": "import_only",
                "estimated_delivery_days": 21,
            },
            {
                "category": "ecu",
                "brand": "Healtech",
                "model_name": "Healtech iO Exhaust Servo Eliminator Suzuki GSX-R1000",
                "part_number": "HT-IO-GSXR1K",
                "specs": {
                    "type": "ecu_module",
                    "channels": 1,
                    "plug_and_play": True,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.18,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 8500,
                "mrp_inr": 10000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 12,
            },
            {
                "category": "ecu",
                "brand": "Aracer",
                "model_name": "Aracer RC Mini ECU Remap Yamaha YZF-R1 (998cc)",
                "part_number": "ARC-R1-RCMINI",
                "specs": {
                    "type": "ecu_remap",
                    "channels": 4,
                    "data_logging": False,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.5,
                    "engine.peak_torque_nm": 2.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 35000,
                "mrp_inr": 41000,
                "retailer": "Aracer Distributor India",
                "retailer_url": "https://aracerind.com",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "ecu",
                "brand": "Power Commander",
                "model_name": "Power Commander V Ducati Panigale V4R (1103cc)",
                "part_number": "PCV-PANIV4R",
                "specs": {
                    "type": "piggyback_ecu",
                    "channels": 8,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 5.8,
                    "engine.peak_torque_nm": 3.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 62000,
                "mrp_inr": 72000,
                "retailer": "Performance Racing Store (Dynojet Official)",
                "retailer_url": "https://performanceracing.in/dynojet",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "ecu",
                "brand": "Rapid Bike",
                "model_name": "Rapid Bike Easy Controller BMW M1000RR (999cc)",
                "part_number": "RBE-M1KRR-EASY",
                "specs": {
                    "type": "piggyback_fuel",
                    "channels": 6,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 4.2,
                    "engine.peak_torque_nm": 2.4,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 48000,
                "mrp_inr": 56000,
                "retailer": "Performance Racing Store (Rapid Bike Official)",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 21,
            },
            {
                "category": "ecu",
                "brand": "Power Commander",
                "model_name": "Power Commander V Kawasaki ZX-10R (998cc)",
                "part_number": "PCV-ZX10R",
                "specs": {
                    "type": "piggyback_ecu",
                    "channels": 8,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 5.5,
                    "engine.peak_torque_nm": 3.0,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 58000,
                "mrp_inr": 68000,
                "retailer": "Performance Racing Store (Dynojet Official)",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
            {
                "category": "ecu",
                "brand": "Healtech",
                "model_name": "Healtech iO Fuel Tuning Unit Aprilia RSV4 Factory (1000cc)",
                "part_number": "HT-IO-RSV4-FT",
                "specs": {
                    "type": "ecu_module",
                    "channels": 6,
                    "plug_and_play": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 3.8,
                    "engine.peak_torque_nm": 2.2,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 42000,
                "mrp_inr": 49000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "ecu",
                "brand": "Woolich Racing",
                "model_name": "Woolich Racing TuneEdit ECU Tune Honda CBR600RR (599cc)",
                "part_number": "WRL-CBR600-TE",
                "specs": {
                    "type": "ecu_tune",
                    "channels": 6,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 2.8,
                    "engine.peak_torque_nm": 1.8,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 590,
                        "displacement_max_cc": 610,
                    },
                },
                "price_inr": 32000,
                "mrp_inr": 38000,
                "retailer": "Performance Racing Store (Woolich Official)",
                "retailer_url": "https://performanceracing.in",
                "availability": "import_only",
                "estimated_delivery_days": 24,
            },
            {
                "category": "ecu",
                "brand": "Power Commander",
                "model_name": "Power Commander V Royal Enfield Interceptor 650 (650cc)",
                "part_number": "PCV-RE650",
                "specs": {
                    "type": "piggyback_ecu",
                    "channels": 6,
                    "data_logging": True,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 2.5,
                    "engine.peak_torque_nm": 1.9,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "engine_configs": ["I2"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                    },
                },
                "price_inr": 22000,
                "mrp_inr": 26000,
                "retailer": "Performance Racing Store (Dynojet Official)",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 10,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # SUSPENSION (10 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "suspension",
                "brand": "YSS",
                "model_name": "YSS Rear Shock Absorber Yamaha R15 V4 (155cc)",
                "part_number": "YSS-R15V4-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "adjustable",
                    "preload_mm": 35,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -5,
                    "chassis.dry_mass_kg": 0.20,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "displacement_min_cc": 145,
                        "displacement_max_cc": 165,
                    },
                },
                "price_inr": 14000,
                "mrp_inr": 16500,
                "retailer": "YSS India Distributor",
                "retailer_url": "https://yssindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 5,
            },
            {
                "category": "suspension",
                "brand": "KYB",
                "model_name": "KYB Rear Shock Bajaj Pulsar NS200 (200cc)",
                "part_number": "KYB-NS200-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "twin_tube",
                    "preload_mm": 42,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -6,
                    "chassis.dry_mass_kg": 0.25,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Bajaj"],
                        "displacement_min_cc": 195,
                        "displacement_max_cc": 210,
                    },
                },
                "price_inr": 12500,
                "mrp_inr": 14800,
                "retailer": "KYB India",
                "retailer_url": "https://kyb.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 4,
            },
            {
                "category": "suspension",
                "brand": "Showa",
                "model_name": "Showa Rear Shock Royal Enfield Interceptor 650 (650cc)",
                "part_number": "SHW-RE650-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "adjustable",
                    "preload_mm": 50,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -8,
                    "chassis.dry_mass_kg": 0.35,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                    },
                },
                "price_inr": 18500,
                "mrp_inr": 22000,
                "retailer": "RE Official",
                "retailer_url": "https://royalenfield.in",
                "availability": "in_stock",
                "estimated_delivery_days": 7,
            },
            {
                "category": "suspension",
                "brand": "Öhlins",
                "model_name": "Öhlins Rear Shock Yamaha YZF-R1 (998cc)",
                "part_number": "OHL-R1-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "fully_adjustable",
                    "preload_mm": 65,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -10,
                    "chassis.dry_mass_kg": 0.42,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 85000,
                "mrp_inr": 100000,
                "retailer": "Motoworld Bangalore (Öhlins Official)",
                "retailer_url": "https://motoworld.in/ohlins",
                "availability": "import_only",
                "estimated_delivery_days": 28,
            },
            {
                "category": "suspension",
                "brand": "K-Tech",
                "model_name": "K-Tech Rear Shock Suzuki Hayabusa (1299cc)",
                "part_number": "KTH-HAYABUSA-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "fully_adjustable",
                    "preload_mm": 68,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -12,
                    "chassis.dry_mass_kg": 0.45,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 92000,
                "mrp_inr": 108000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 32,
            },
            {
                "category": "suspension",
                "brand": "YSS",
                "model_name": "YSS Rear Shock TVS Apache RR 310 (312cc)",
                "part_number": "YSS-APACHE310-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "adjustable",
                    "preload_mm": 45,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -7,
                    "chassis.dry_mass_kg": 0.22,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["TVS"],
                        "displacement_min_cc": 305,
                        "displacement_max_cc": 315,
                    },
                },
                "price_inr": 15500,
                "mrp_inr": 18200,
                "retailer": "YSS India Distributor",
                "retailer_url": "https://yssindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 5,
            },
            {
                "category": "suspension",
                "brand": "KYB",
                "model_name": "KYB Rear Shock Suzuki GSX-R1000 (999cc)",
                "part_number": "KYB-GSXR1K-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "twin_tube",
                    "preload_mm": 62,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -11,
                    "chassis.dry_mass_kg": 0.40,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 42000,
                "mrp_inr": 49000,
                "retailer": "KYB India",
                "retailer_url": "https://kyb.com/india",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "suspension",
                "brand": "Andreani Group",
                "model_name": "Andreani Rear Shock Ducati Panigale V4R (1103cc)",
                "part_number": "AND-PANIV4R-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "fully_adjustable",
                    "preload_mm": 66,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -11,
                    "chassis.dry_mass_kg": 0.38,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 78000,
                "mrp_inr": 92000,
                "retailer": "Powertec (Andreani Official)",
                "retailer_url": "https://powertec.in/andreani",
                "availability": "order",
                "estimated_delivery_days": 24,
            },
            {
                "category": "suspension",
                "brand": "Showa",
                "model_name": "Showa Rear Shock Kawasaki ZX-10R (998cc)",
                "part_number": "SHW-ZX10R-REAR",
                "specs": {
                    "type": "rear_shock",
                    "damper_type": "adjustable",
                    "preload_mm": 60,
                },
                "param_deltas": {
                    "chassis.cog_height_mm": -10,
                    "chassis.dry_mass_kg": 0.38,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 45000,
                "mrp_inr": 53000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # BRAKES (10 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "brakes",
                "brand": "EBC",
                "model_name": "EBC HH Sintered Brake Pads Front Yamaha R15 V4 (155cc)",
                "part_number": "EBC-R15V4-HH",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.05,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "displacement_min_cc": 145,
                        "displacement_max_cc": 165,
                    },
                },
                "price_inr": 1800,
                "mrp_inr": 2200,
                "retailer": "EBC India Distributor",
                "retailer_url": "https://ebcbrakes.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "brakes",
                "brand": "Ferodo",
                "model_name": "Ferodo Sintered Brake Pads Front Bajaj Pulsar NS200 (200cc)",
                "part_number": "FRD-NS200-SIN",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.06,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Bajaj"],
                        "displacement_min_cc": 195,
                        "displacement_max_cc": 210,
                    },
                },
                "price_inr": 2100,
                "mrp_inr": 2500,
                "retailer": "Performance Racing Store (Ferodo Official)",
                "retailer_url": "https://performanceracing.in/ferodo",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "brakes",
                "brand": "Brembo",
                "model_name": "Brembo Sintered Brake Pads Front Yamaha YZF-R1 (998cc)",
                "part_number": "BRM-R1-SIN",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.08,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 4200,
                "mrp_inr": 5000,
                "retailer": "Brembo Mumbai Dealer",
                "retailer_url": "https://bremboindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "brakes",
                "brand": "Bybre",
                "model_name": "Bybre Sintered Brake Rotors 330mm Suzuki Hayabusa (1299cc)",
                "part_number": "BYB-HAYABUSA-330",
                "specs": {
                    "type": "brake_rotor",
                    "diameter_mm": 330,
                    "material": "stainless",
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.12,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 8500,
                "mrp_inr": 10000,
                "retailer": "Bybre India (Brembo OEM Arm)",
                "retailer_url": "https://bybreindia.com",
                "availability": "order",
                "estimated_delivery_days": 12,
            },
            {
                "category": "brakes",
                "brand": "Galfer",
                "model_name": "Galfer Braided Brake Hose Kit Suzuki GSX-R1000 (999cc)",
                "part_number": "GLF-GSXR1K-HOSE",
                "specs": {
                    "type": "brake_hose",
                    "material": "stainless_braid",
                    "hose_count": 2,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.10,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 6800,
                "mrp_inr": 8000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 10,
            },
            {
                "category": "brakes",
                "brand": "EBC",
                "model_name": "EBC HH Sintered Brake Pads Front Ducati Panigale V4R (1103cc)",
                "part_number": "EBC-PANIV4R-HH",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.07,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 3800,
                "mrp_inr": 4500,
                "retailer": "EBC India Distributor",
                "retailer_url": "https://ebcbrakes.com/india",
                "availability": "order",
                "estimated_delivery_days": 8,
            },
            {
                "category": "brakes",
                "brand": "Gold Fren",
                "model_name": "Gold Fren Brake Rotor 280mm BMW M1000RR (999cc)",
                "part_number": "GLF-M1KRR-280",
                "specs": {
                    "type": "brake_rotor",
                    "diameter_mm": 280,
                    "material": "stainless",
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.10,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 7200,
                "mrp_inr": 8500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "brakes",
                "brand": "Brembo",
                "model_name": "Brembo Sintered Brake Pads Front Royal Enfield Interceptor 650 (650cc)",
                "part_number": "BRM-RE650-SIN",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.06,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                    },
                },
                "price_inr": 2800,
                "mrp_inr": 3300,
                "retailer": "Brembo Mumbai Dealer",
                "retailer_url": "https://bremboindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 4,
            },
            {
                "category": "brakes",
                "brand": "Ferodo",
                "model_name": "Ferodo Sintered Brake Pads Front Kawasaki ZX-10R (998cc)",
                "part_number": "FRD-ZX10R-SIN",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.08,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Kawasaki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 4100,
                "mrp_inr": 4900,
                "retailer": "Performance Racing Store (Ferodo Official)",
                "retailer_url": "https://performanceracing.in",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "brakes",
                "brand": "Galfer",
                "model_name": "Galfer Brake Pads Front Aprilia RSV4 Factory (1000cc)",
                "part_number": "GLF-RSV4-PAD",
                "specs": {
                    "type": "brake_pads",
                    "material": "sintered",
                    "set_count": 1,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -0.07,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Aprilia"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 3600,
                "mrp_inr": 4300,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 10,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # BATTERY (8 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "battery",
                "brand": "Amaron",
                "model_name": "Amaron Pro Lead-Acid Battery Yamaha R15 V4 (155cc)",
                "part_number": "AMA-R15V4-PA",
                "specs": {
                    "type": "lead_acid",
                    "voltage_v": 12,
                    "ah": 5,
                    "cca": 55,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.45,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "displacement_min_cc": 145,
                        "displacement_max_cc": 165,
                    },
                },
                "price_inr": 1850,
                "mrp_inr": 2200,
                "retailer": "Amaron Official",
                "retailer_url": "https://amaron.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "battery",
                "brand": "Shorai",
                "model_name": "Shorai LFX Lithium Battery Suzuki Hayabusa (1299cc)",
                "part_number": "SHR-HAYABUSA-LFX",
                "specs": {
                    "type": "lithium",
                    "voltage_v": 12,
                    "ah": 16,
                    "cca": 480,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -2.85,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 18500,
                "mrp_inr": 22000,
                "retailer": "Performance Racing Store (Shorai Official)",
                "retailer_url": "https://performanceracing.in/shorai",
                "availability": "import_only",
                "estimated_delivery_days": 14,
            },
            {
                "category": "battery",
                "brand": "Antigravity",
                "model_name": "Antigravity Batteries RE-START Lithium Yamaha YZF-R1 (998cc)",
                "part_number": "AGV-R1-RESTART",
                "specs": {
                    "type": "lithium",
                    "voltage_v": 12,
                    "ah": 14,
                    "cca": 420,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -2.20,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 16200,
                "mrp_inr": 19000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "battery",
                "brand": "Exide",
                "model_name": "Exide Industrial Lead-Acid Battery Royal Enfield Interceptor 650 (650cc)",
                "part_number": "EXD-RE650-IND",
                "specs": {
                    "type": "lead_acid",
                    "voltage_v": 12,
                    "ah": 11,
                    "cca": 120,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.85,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                    },
                },
                "price_inr": 3500,
                "mrp_inr": 4100,
                "retailer": "Exide Official",
                "retailer_url": "https://exideindia.com",
                "availability": "in_stock",
                "estimated_delivery_days": 3,
            },
            {
                "category": "battery",
                "brand": "Yuasa",
                "model_name": "Yuasa YTZ10S Lithium Battery Suzuki GSX-R1000 (999cc)",
                "part_number": "YUA-GSXR1K-YTZ10S",
                "specs": {
                    "type": "lithium",
                    "voltage_v": 12,
                    "ah": 8.6,
                    "cca": 230,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -1.85,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 12800,
                "mrp_inr": 15000,
                "retailer": "Yuasa India Distributor",
                "retailer_url": "https://yuasa.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 5,
            },
            {
                "category": "battery",
                "brand": "Shorai",
                "model_name": "Shorai LFX Lithium Battery Ducati Panigale V4R (1103cc)",
                "part_number": "SHR-PANIV4R-LFX",
                "specs": {
                    "type": "lithium",
                    "voltage_v": 12,
                    "ah": 12,
                    "cca": 360,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -2.10,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 17200,
                "mrp_inr": 20500,
                "retailer": "Performance Racing Store (Shorai Official)",
                "retailer_url": "https://performanceracing.in/shorai",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
            {
                "category": "battery",
                "brand": "Amaron",
                "model_name": "Amaron Pro Lead-Acid Battery Honda CB300R (286cc)",
                "part_number": "AMA-CB300R-PA",
                "specs": {
                    "type": "lead_acid",
                    "voltage_v": 12,
                    "ah": 7,
                    "cca": 75,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.60,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Honda"],
                        "displacement_min_cc": 280,
                        "displacement_max_cc": 300,
                    },
                },
                "price_inr": 2200,
                "mrp_inr": 2600,
                "retailer": "Amaron Official",
                "retailer_url": "https://amaron.com/india",
                "availability": "in_stock",
                "estimated_delivery_days": 2,
            },
            {
                "category": "battery",
                "brand": "Antigravity",
                "model_name": "Antigravity Batteries RE-START Lithium BMW M1000RR (999cc)",
                "part_number": "AGV-M1KRR-RESTART",
                "specs": {
                    "type": "lithium",
                    "voltage_v": 12,
                    "ah": 14,
                    "cca": 420,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": -2.20,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 16200,
                "mrp_inr": 19000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 20,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CLUTCH KITS (6 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "clutch_kit",
                "brand": "Surflex",
                "model_name": "Surflex Organic Clutch Kit Royal Enfield Interceptor 650 (650cc)",
                "part_number": "SLX-RE650-ORG",
                "specs": {
                    "type": "friction_plate_set",
                    "material": "organic",
                    "plate_count": 6,
                },
                "param_deltas": {
                    "clutch.engage_rpm": 100,
                    "chassis.dry_mass_kg": 0.35,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Royal Enfield"],
                        "displacement_min_cc": 640,
                        "displacement_max_cc": 660,
                    },
                },
                "price_inr": 8500,
                "mrp_inr": 10000,
                "retailer": "Surflex India",
                "retailer_url": "https://surflex.in",
                "availability": "in_stock",
                "estimated_delivery_days": 5,
            },
            {
                "category": "clutch_kit",
                "brand": "EBC",
                "model_name": "EBC CK Heavy-Duty Clutch Kit Yamaha YZF-R1 (998cc)",
                "part_number": "EBC-R1-CK-HD",
                "specs": {
                    "type": "friction_plate_set",
                    "material": "heavy_duty",
                    "plate_count": 8,
                },
                "param_deltas": {
                    "clutch.engage_rpm": 150,
                    "chassis.dry_mass_kg": 0.42,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 12500,
                "mrp_inr": 14800,
                "retailer": "Performance Racing Store (EBC Official)",
                "retailer_url": "https://performanceracing.in/ebc",
                "availability": "order",
                "estimated_delivery_days": 12,
            },
            {
                "category": "clutch_kit",
                "brand": "Newfren",
                "model_name": "Newfren Sintered Clutch Kit Suzuki Hayabusa (1299cc)",
                "part_number": "NFN-HAYABUSA-SIN",
                "specs": {
                    "type": "friction_plate_set",
                    "material": "sintered",
                    "plate_count": 9,
                },
                "param_deltas": {
                    "clutch.engage_rpm": 200,
                    "chassis.dry_mass_kg": 0.50,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 15800,
                "mrp_inr": 18500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
            {
                "category": "clutch_kit",
                "brand": "Barnett",
                "model_name": "Barnett Tool & Engineering Sintered Clutch Kit Ducati Panigale V4R (1103cc)",
                "part_number": "BAR-PANIV4R-SIN",
                "specs": {
                    "type": "friction_plate_set",
                    "material": "sintered",
                    "plate_count": 8,
                },
                "param_deltas": {
                    "clutch.engage_rpm": 180,
                    "chassis.dry_mass_kg": 0.45,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 14200,
                "mrp_inr": 16800,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "clutch_kit",
                "brand": "Surflex",
                "model_name": "Surflex Organic Clutch Kit Bajaj Pulsar NS200 (200cc)",
                "part_number": "SLX-NS200-ORG",
                "specs": {
                    "type": "friction_plate_set",
                    "material": "organic",
                    "plate_count": 5,
                },
                "param_deltas": {
                    "clutch.engage_rpm": 80,
                    "chassis.dry_mass_kg": 0.20,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Bajaj"],
                        "displacement_min_cc": 195,
                        "displacement_max_cc": 210,
                    },
                },
                "price_inr": 5200,
                "mrp_inr": 6100,
                "retailer": "Surflex India",
                "retailer_url": "https://surflex.in",
                "availability": "in_stock",
                "estimated_delivery_days": 4,
            },
            {
                "category": "clutch_kit",
                "brand": "EBC",
                "model_name": "EBC CK Heavy-Duty Clutch Kit Suzuki GSX-R1000 (999cc)",
                "part_number": "EBC-GSXR1K-CK-HD",
                "specs": {
                    "type": "friction_plate_set",
                    "material": "heavy_duty",
                    "plate_count": 8,
                },
                "param_deltas": {
                    "clutch.engage_rpm": 160,
                    "chassis.dry_mass_kg": 0.40,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 12200,
                "mrp_inr": 14400,
                "retailer": "Performance Racing Store (EBC Official)",
                "retailer_url": "https://performanceracing.in/ebc",
                "availability": "in_stock",
                "estimated_delivery_days": 6,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # QUICKSHIFTER (5 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "quickshifter",
                "brand": "Translogic",
                "model_name": "Translogic Quickshifter Yamaha YZF-R1 (998cc)",
                "part_number": "TRG-R1-QS",
                "specs": {
                    "type": "electronic_quickshifter",
                    "shift_time_ms": 50,
                    "data_logging": True,
                },
                "param_deltas": {
                    "drivetrain.total_shift_time_ms": -60,
                    "chassis.dry_mass_kg": 0.15,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 28000,
                "mrp_inr": 33000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "quickshifter",
                "brand": "Healtech",
                "model_name": "Healtech iO Quickshifter Suzuki Hayabusa (1299cc)",
                "part_number": "HT-IO-HAYABUSA-QS",
                "specs": {
                    "type": "electronic_quickshifter",
                    "shift_time_ms": 55,
                    "data_logging": True,
                },
                "param_deltas": {
                    "drivetrain.total_shift_time_ms": -55,
                    "chassis.dry_mass_kg": 0.12,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 32000,
                "mrp_inr": 37000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
            {
                "category": "quickshifter",
                "brand": "SP Engineering",
                "model_name": "SP Engineering Quickshifter Suzuki GSX-R1000 (999cc)",
                "part_number": "SPE-GSXR1K-QS",
                "specs": {
                    "type": "electronic_quickshifter",
                    "shift_time_ms": 52,
                    "data_logging": False,
                },
                "param_deltas": {
                    "drivetrain.total_shift_time_ms": -58,
                    "chassis.dry_mass_kg": 0.14,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 24500,
                "mrp_inr": 28500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 12,
            },
            {
                "category": "quickshifter",
                "brand": "Nextshift",
                "model_name": "Nextshift Quickshifter Ducati Panigale V4R (1103cc) — Indian-Made",
                "part_number": "NSF-PANIV4R-QS",
                "specs": {
                    "type": "electronic_quickshifter",
                    "shift_time_ms": 54,
                    "data_logging": True,
                },
                "param_deltas": {
                    "drivetrain.total_shift_time_ms": -56,
                    "chassis.dry_mass_kg": 0.16,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 22000,
                "mrp_inr": 26000,
                "retailer": "Nextshift (Pune, India)",
                "retailer_url": "https://nextshift.in",
                "availability": "in_stock",
                "estimated_delivery_days": 5,
            },
            {
                "category": "quickshifter",
                "brand": "Translogic",
                "model_name": "Translogic Quickshifter BMW M1000RR (999cc)",
                "part_number": "TRG-M1KRR-QS",
                "specs": {
                    "type": "electronic_quickshifter",
                    "shift_time_ms": 51,
                    "data_logging": True,
                },
                "param_deltas": {
                    "drivetrain.total_shift_time_ms": -59,
                    "chassis.dry_mass_kg": 0.15,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 29500,
                "mrp_inr": 34500,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # FUEL SYSTEM (5 parts)
    # ══════════════════════════════════════════════════════════════

    parts.extend(
        [
            {
                "category": "fuel_system",
                "brand": "Bosch",
                "model_name": "Bosch High-Flow Fuel Pump Yamaha YZF-R1 (998cc)",
                "part_number": "BSH-R1-PUMP",
                "specs": {
                    "type": "fuel_pump",
                    "flow_rate_lph": 255,
                    "pressure_bar": 4.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.5,
                    "chassis.dry_mass_kg": 0.25,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Yamaha"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 8200,
                "mrp_inr": 9600,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 10,
            },
            {
                "category": "fuel_system",
                "brand": "Radium Engineering",
                "model_name": "Radium Fuel Pressure Regulator Suzuki Hayabusa (1299cc)",
                "part_number": "RAD-HAYABUSA-REG",
                "specs": {
                    "type": "fuel_regulator",
                    "pressure_bar_min": 2.5,
                    "pressure_bar_max": 5.0,
                    "flow_capacity_lph": 200,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.18,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 1290,
                        "displacement_max_cc": 1310,
                    },
                },
                "price_inr": 12500,
                "mrp_inr": 14800,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 14,
            },
            {
                "category": "fuel_system",
                "brand": "Aeromotive",
                "model_name": "Aeromotive EFI Fuel Rail Kit Suzuki GSX-R1000 (999cc)",
                "part_number": "ARO-GSXR1K-RAIL",
                "specs": {
                    "type": "fuel_rail",
                    "max_pressure_bar": 7.0,
                    "injector_capacity_cc": 1000,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.5,
                    "chassis.dry_mass_kg": 0.32,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Suzuki"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 18500,
                "mrp_inr": 22000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 18,
            },
            {
                "category": "fuel_system",
                "brand": "Bosch",
                "model_name": "Bosch High-Flow Fuel Pump Ducati Panigale V4R (1103cc)",
                "part_number": "BSH-PANIV4R-PUMP",
                "specs": {
                    "type": "fuel_pump",
                    "flow_rate_lph": 255,
                    "pressure_bar": 4.0,
                },
                "param_deltas": {
                    "engine.peak_power_hp": 1.5,
                    "chassis.dry_mass_kg": 0.25,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["Ducati"],
                        "engine_configs": ["V4"],
                        "displacement_min_cc": 1100,
                        "displacement_max_cc": 1110,
                    },
                },
                "price_inr": 8500,
                "mrp_inr": 10000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 12,
            },
            {
                "category": "fuel_system",
                "brand": "Radium Engineering",
                "model_name": "Radium Fuel Pressure Regulator BMW M1000RR (999cc)",
                "part_number": "RAD-M1KRR-REG",
                "specs": {
                    "type": "fuel_regulator",
                    "pressure_bar_min": 2.5,
                    "pressure_bar_max": 5.0,
                    "flow_capacity_lph": 200,
                },
                "param_deltas": {
                    "chassis.dry_mass_kg": 0.18,
                },
                "fitment_rules": {
                    "tier": "family",
                    "match": {
                        "manufacturers": ["BMW"],
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 990,
                        "displacement_max_cc": 1010,
                    },
                },
                "price_inr": 12800,
                "mrp_inr": 15000,
                "retailer": "Performance Racing Store",
                "retailer_url": "https://performanceracing.in",
                "availability": "order",
                "estimated_delivery_days": 16,
            },
        ]
    )

    # ══════════════════════════════════════════════════════════════
    # CREATE PARTS IN DATABASE
    # ══════════════════════════════════════════════════════════════

    return _create_parts_batch(db, parts, label="Indian Retailer Depth Parts")


# ══════════════════════════════════════════════════════════════════════════
# EXPORT FOR REGISTRATION IN seed.py
# ══════════════════════════════════════════════════════════════════════════

# Module metadata (NOT a part list — the actual parts are constructed inline
# inside seed_indian_retailer_depth() above. This dict exists so the seed
# orchestrator can introspect the module without importing the function.)
INDIAN_RETAILER_DEPTH_REGISTRATION = {
    "seed_func": seed_indian_retailer_depth,
    "name": "Indian Retailer Depth Catalog",
    "description": "High-depth Indian-market performance parts across 14 categories with real retailer pricing",
    "approximate_part_count": 90,
}
