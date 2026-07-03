"""
MotoQuant Pro — Thin-Brand Exhaust Depth (July 2026)
=====================================================
Seeds 12 REAL exhaust systems for the four thinnest exhaust brands in the
catalog (pre-seed coverage: MV Agusta 0, CFMoto 0, QJ Motor 0, Moto Guzzi 1,
Triumph 5 — mostly cruiser generics):

  Triumph   (4): SC-Project SC1-R GT + CR-T (Speed Triple 1200 RS/RR),
                 Zard Racing slip-on (Rocket 3 R / GT / Storm 2020+),
                 Arrow Veloce full system (Trident 660).
  MV Agusta (2): SC-Project SC1-R (F3 800 / Brutale 800 platform),
                 SC-Project CR-T M2 (Brutale 1000 RR, PN M09-T68C).
  Moto Guzzi(2): Akrapovic Slip-On Line Titanium (V85 TT, $871 verified),
                 Mistral Special Parts homologated silencers (V85 TT Euro5).
  CFMoto    (3): Akrapovic Slip-On Line Carbon (450SR/450NK, $546 verified),
                 Yoshimura AT2 stainless slip-on (450SS/450NK),
                 LeoVince LV One EVO (800NK Advanced/Sport, $545 verified).
  Triumph Rocket 3 pre-2020 Zard 3-into-1 exists but the catalog carries
  only 2020+ Rocket 3 generations, so only the 2020+ slip-on is seeded.

QJ MOTOR — DATA GAP (honest): no major exhaust brand publishes a verified
SRK 400 system with public pricing (only unbranded AliExpress cans).
Nothing seeded; revisit when SC-Project/Akrapovic list the platform.

All products verified against live listings July 2026 (shop.sc-project.com,
sc-project.us, motomachines/motowheels Zard listings, arrow.it + EU dealers,
akrapovic.com + RevZilla/Cycle Gear, mistralspecialparts.it,
yoshimura-rd.com, leovince.com). USD/EUR converted to landed INR via the
documented import formula (usd * 84 * 1.30 * 1.18 + 1500); entries with
interpolated pricing carry "price_estimated": True. Accuracy +/-15%.

Fitment: tight family-tier (manufacturer + engine_configs + displacement
bounds + categories) so e.g. the Speed Triple 1200 silencer cannot leak to
the Tiger 1200 (same 1160cc I3, different category).
"""

from motoquant.database.seed_catalogs import _create_parts_batch


def seed_euro_brand_exhausts(db) -> int:
    """
    Seeds exhaust systems for Triumph / MV Agusta / Moto Guzzi / CFMoto.
    Returns count of parts successfully created.
    """
    parts = [
        # ── TRIUMPH ─────────────────────────────────────────────────
        {
            "category": "exhaust",
            "brand": "SC-Project",
            "model_name": "SC1-R GT Carbon — Speed Triple 1200 RS/RR",
            "part_number": "SCP-T25A-102C",
            "specs": {
                "type": "slip_on",
                "material": "carbon_fiber",
                "homologation": "Euro 5",
                "msrp_usd": 905,
            },
            "param_deltas": {
                "engine.peak_power_hp": 4.5,
                "engine.peak_torque_nm": 3.0,
                "chassis.dry_mass_kg": -3.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["Triumph"],
                    "engine_configs": ["I3"],
                    "displacement_min_cc": 1150,
                    "displacement_max_cc": 1170,
                    "categories": ["naked", "sport"],
                },
                "description": (
                    "SC-Project SC1-R GT carbon silencer (T25A-102C) for "
                    "Triumph Speed Triple 1200 RS/RR 2021-2025; Euro 5 "
                    "homologated MotoGP-derived end can."
                ),
            },
            "price_inr": 118000,
            "availability": "import_only",
            "retailer": "SC-Project (EU)",
            "delivery_days": 40,
        },
        {
            "category": "exhaust",
            "brand": "SC-Project",
            "model_name": "CR-T Titanium — Speed Triple 1200 RS/RR",
            "part_number": "SCP-T25-D38",
            "specs": {
                "type": "slip_on_race",
                "material": "titanium",
                "homologation": "racing only",
                "msrp_usd": 1100,
                "price_estimated": True,
            },
            "param_deltas": {
                "engine.peak_power_hp": 6.0,
                "engine.peak_torque_nm": 4.0,
                "chassis.dry_mass_kg": -4.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["Triumph"],
                    "engine_configs": ["I3"],
                    "displacement_min_cc": 1150,
                    "displacement_max_cc": 1170,
                    "categories": ["naked", "sport"],
                },
                "description": (
                    "SC-Project CR-T race silencer for Triumph Speed Triple "
                    "1200 RS/RR; Moto2-replica can, track/strip use."
                ),
            },
            "price_inr": 143200,
            "availability": "import_only",
            "retailer": "SC-Project (EU)",
            "delivery_days": 40,
        },
        {
            "category": "exhaust",
            "brand": "Zard",
            "model_name": "Racing Slip-On Stainless — Rocket 3 (2020+)",
            "part_number": "ZTPH502SSR",
            "specs": {
                "type": "slip_on_kit",
                "material": "stainless_steel",
                "homologation": "racing / road-legal variants",
                "msrp_usd": 1914,
            },
            "param_deltas": {
                "engine.peak_power_hp": 5.0,
                "engine.peak_torque_nm": 6.0,
                # The stock triple-outlet cans on the Rocket 3 are enormous.
                "chassis.dry_mass_kg": -8.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["Triumph"],
                    "engine_configs": ["I3"],
                    "displacement_min_cc": 2400,
                    "displacement_max_cc": 2500,
                    "categories": ["naked", "cruiser"],
                    "year_min": 2020,
                },
                "description": (
                    "Zard racing slip-on kit for Triumph Rocket 3 R / GT / "
                    "Storm 2020-2025 (PN ZTPH502SSR family); big mass "
                    "saving over the stock cans on the 2.5L triple."
                ),
            },
            "price_inr": 248000,
            "availability": "import_only",
            "retailer": "Zard Officine Italiane (EU)",
            "delivery_days": 45,
        },
        {
            "category": "exhaust",
            "brand": "Arrow",
            "model_name": "Veloce Full System Dark Aluminum — Trident 660",
            "part_number": "ARROW-71001VAN",
            "specs": {
                "type": "full_system",
                "material": "aluminum_dark / SS headers",
                "homologation": "racing (de-cat)",
                "msrp_usd": 1178,
            },
            "param_deltas": {
                "engine.peak_power_hp": 6.0,
                "engine.peak_torque_nm": 4.0,
                "chassis.dry_mass_kg": -4.5,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["Triumph"],
                    "engine_configs": ["I3"],
                    "displacement_min_cc": 655,
                    "displacement_max_cc": 665,
                    "categories": ["naked"],
                },
                "description": (
                    "Arrow 71001VAN full racing system with Veloce dark "
                    "aluminium silencer for Triumph Trident 660 2021-2024; "
                    "de-cat competition line."
                ),
            },
            "price_inr": 153000,
            "availability": "import_only",
            "retailer": "Arrow Special Parts (EU)",
            "delivery_days": 35,
        },
        # ── MV AGUSTA ───────────────────────────────────────────────
        {
            "category": "exhaust",
            "brand": "SC-Project",
            "model_name": "SC1-R Carbon — F3 800 / Brutale 800",
            "part_number": "SCP-SC1R-MV-B3",
            "specs": {
                "type": "slip_on",
                "material": "carbon_fiber",
                "homologation": "Euro 4 street legal",
                "msrp_usd": 1050,
                "price_estimated": True,
            },
            "param_deltas": {
                "engine.peak_power_hp": 4.0,
                "engine.peak_torque_nm": 2.5,
                "chassis.dry_mass_kg": -2.5,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["MV Agusta"],
                    "engine_configs": ["I3"],
                    "displacement_min_cc": 670,
                    "displacement_max_cc": 805,
                    "categories": ["sport", "naked"],
                },
                "description": (
                    "SC-Project SC1-R carbon silencer for the MV Agusta "
                    "B3 triple platform — F3 800, F3 RR, Brutale 800 / "
                    "Dragster (675-800cc I3)."
                ),
            },
            "price_inr": 137000,
            "availability": "import_only",
            "retailer": "SC-Project (EU)",
            "delivery_days": 40,
        },
        {
            "category": "exhaust",
            "brand": "SC-Project",
            "model_name": "CR-T M2 Carbon — Brutale 1000 RR",
            "part_number": "SCP-M09-T68C",
            "specs": {
                "type": "slip_on_race",
                "material": "carbon_fiber / titanium",
                "homologation": "racing only",
                "msrp_usd": 1700,
                "price_estimated": True,
            },
            "param_deltas": {
                "engine.peak_power_hp": 6.5,
                "engine.peak_torque_nm": 4.0,
                "chassis.dry_mass_kg": -4.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["MV Agusta"],
                    "engine_configs": ["I4"],
                    "displacement_min_cc": 990,
                    "displacement_max_cc": 1010,
                    "categories": ["naked"],
                },
                "description": (
                    "SC-Project CR-T M2 (M09-T68C), direct Moto2 descendant, "
                    "for MV Agusta Brutale 1000 RR / Serie Oro / Assen "
                    "2019-2024."
                ),
            },
            "price_inr": 220000,
            "availability": "import_only",
            "retailer": "SC-Project (EU)",
            "delivery_days": 40,
        },
        # ── MOTO GUZZI ──────────────────────────────────────────────
        {
            "category": "exhaust",
            "brand": "Akrapovic",
            "model_name": "Slip-On Line Titanium — V85 TT",
            "part_number": "S-MG8SO1-HFTT",
            "specs": {
                "type": "slip_on",
                "material": "titanium",
                "homologation": "street legal",
                "msrp_usd": 871,
            },
            "param_deltas": {
                "engine.peak_power_hp": 3.0,
                "engine.peak_torque_nm": 2.0,
                "chassis.dry_mass_kg": -2.5,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["Moto Guzzi"],
                    "engine_configs": ["V2"],
                    "displacement_min_cc": 840,
                    "displacement_max_cc": 865,
                    "categories": ["adventure"],
                },
                "description": (
                    "Akrapovic Slip-On Line titanium (S-MG8SO1-HFTT) for "
                    "Moto Guzzi V85 TT 2019-2024 transverse V2."
                ),
            },
            "price_inr": 114000,
            "availability": "import_only",
            "retailer": "Akrapovic (EU)",
            "delivery_days": 35,
        },
        {
            "category": "exhaust",
            "brand": "Mistral Special Parts",
            "model_name": "Homologated Silencer — V85 TT Euro5",
            "part_number": "MISTRAL-V85TT-E5",
            "specs": {
                "type": "slip_on",
                "material": "stainless_steel",
                "homologation": "Euro 5",
                "msrp_usd": 490,
                "price_estimated": True,
            },
            "param_deltas": {
                "engine.peak_power_hp": 2.5,
                "engine.peak_torque_nm": 1.8,
                "chassis.dry_mass_kg": -2.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["Moto Guzzi"],
                    "engine_configs": ["V2"],
                    "displacement_min_cc": 840,
                    "displacement_max_cc": 865,
                    "categories": ["adventure"],
                },
                "description": (
                    "Mistral Special Parts hand-crafted homologated "
                    "silencer for Moto Guzzi V85 TT Euro5 — the Guzzi "
                    "specialist marque."
                ),
            },
            "price_inr": 64600,
            "availability": "import_only",
            "retailer": "Mistral Special Parts (Italy)",
            "delivery_days": 40,
        },
        # ── CFMOTO ──────────────────────────────────────────────────
        {
            "category": "exhaust",
            "brand": "Akrapovic",
            "model_name": "Slip-On Line Carbon — 450SR / 450NK",
            "part_number": "AK-CF450-SO-C",
            "specs": {
                "type": "slip_on",
                "material": "carbon_fiber",
                "homologation": "racing",
                "msrp_usd": 546,
            },
            "param_deltas": {
                "engine.peak_power_hp": 2.5,
                "engine.peak_torque_nm": 1.5,
                "chassis.dry_mass_kg": -2.5,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["CFMoto"],
                    "engine_configs": ["I2"],
                    "displacement_min_cc": 440,
                    "displacement_max_cc": 460,
                    "categories": ["sport", "naked"],
                },
                "description": (
                    "Akrapovic Slip-On Line carbon for CFMoto 450SR / 450NK "
                    "2024-2026 ($546 verified at Cycle Gear); first factory-"
                    "listed Akrapovic for the brand."
                ),
            },
            "price_inr": 71800,
            "availability": "import_only",
            "retailer": "Akrapovic via Cycle Gear (USA)",
            "delivery_days": 30,
        },
        {
            "category": "exhaust",
            "brand": "Yoshimura",
            "model_name": "AT2 Stainless Slip-On — 450SS / 450NK",
            "part_number": "YOSH-19450BP520",
            "specs": {
                "type": "slip_on",
                "material": "stainless_steel",
                "homologation": "works finish, closed course",
                "msrp_usd": 419,
                "price_estimated": True,
            },
            "param_deltas": {
                "engine.peak_power_hp": 2.0,
                "engine.peak_torque_nm": 1.2,
                "chassis.dry_mass_kg": -2.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["CFMoto"],
                    "engine_configs": ["I2"],
                    "displacement_min_cc": 440,
                    "displacement_max_cc": 460,
                    "categories": ["sport", "naked"],
                },
                "description": (
                    "Yoshimura AT2 stainless slip-on (19450BP520) for "
                    "CFMoto 450SS/450SR + 450NK 2023-2024."
                ),
            },
            "price_inr": 55500,
            "availability": "import_only",
            "retailer": "Yoshimura R&D (USA)",
            "delivery_days": 30,
        },
        {
            "category": "exhaust",
            "brand": "LeoVince",
            "model_name": "LV One EVO — 800NK Advanced / Sport",
            "part_number": "LV-14444E",
            "specs": {
                "type": "slip_on",
                "material": "stainless_steel / carbon cap",
                "homologation": "racing",
                "msrp_usd": 545,
            },
            "param_deltas": {
                "engine.peak_power_hp": 3.0,
                "engine.peak_torque_nm": 2.0,
                "chassis.dry_mass_kg": -2.5,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["CFMoto"],
                    "engine_configs": ["I2"],
                    "displacement_min_cc": 790,
                    "displacement_max_cc": 810,
                    "categories": ["naked"],
                },
                "description": (
                    "LeoVince LV One EVO slip-on for CFMoto 800NK "
                    "Advanced/Sport 2023-2024 (KTM LC8c-derived 799cc I2)."
                ),
            },
            "price_inr": 71700,
            "availability": "import_only",
            "retailer": "LeoVince (USA)",
            "delivery_days": 30,
        },
        {
            "category": "exhaust",
            "brand": "SC-Project",
            "model_name": "CR-T Carbon — Brutale 800 Dragster (race)",
            "part_number": "SCP-M02-38C",
            "specs": {
                "type": "slip_on_race",
                "material": "carbon_fiber",
                "homologation": "racing only",
                "msrp_usd": 1150,
                "price_estimated": True,
            },
            "param_deltas": {
                "engine.peak_power_hp": 5.0,
                "engine.peak_torque_nm": 3.0,
                "chassis.dry_mass_kg": -3.0,
            },
            "fitment_rules": {
                "tier": "family",
                "match": {
                    "manufacturers": ["MV Agusta"],
                    "engine_configs": ["I3"],
                    "displacement_min_cc": 670,
                    "displacement_max_cc": 805,
                    "categories": ["naked"],
                },
                "description": (
                    "SC-Project CR-T race can (M02-38C lineage) for MV "
                    "Agusta Brutale / Dragster 675-800 triples; loud, "
                    "light, strip-focused."
                ),
            },
            "price_inr": 149800,
            "availability": "import_only",
            "retailer": "SC-Project (EU)",
            "delivery_days": 40,
        },
    ]

    return _create_parts_batch(db, parts, label="Euro Thin-Brand Exhausts")
