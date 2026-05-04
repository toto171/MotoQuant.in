"""
Extended catalogue — high-power / homologation-special OEM bikes that
augment the main `known_bikes.py` ALL_KNOWN_BIKES list.

Sourced from manufacturer press kits + magazine instrumented tests.
Kept as a separate module so the giant known_bikes.py doesn't keep
hitting the file-write truncation bug during edits.

Wired into ALL_KNOWN_BIKES via known_bikes.py importing EXTENDED_BIKES
and concatenating into the master list.
"""

from __future__ import annotations

from .bikez import spec_from_dict


# ── Norton V4SV (2022-current) ───────────────────────────────────────
# Hand-built English exotic; 1200cc 72° V4, 200 hp, 193 kg dry.
# Source: Norton Motorcycles press kit + Visordown 2022 review.
NORTON_V4SV_2022 = spec_from_dict(
    {
        "manufacturer": "Norton",
        "model_name": "V4SV",
        "model_code": "V4SV",
        "year_from": 2022,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 1200,
        "bore_mm": 82.0,
        "stroke_mm": 56.8,
        "compression_ratio": 13.6,
        "cylinders": 4,
        "peak_power_hp": 200.0,
        "peak_power_rpm": 12500,
        "peak_torque_nm": 125.0,
        "peak_torque_rpm": 9500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        "gear_ratios": [2.385, 1.842, 1.526, 1.318, 1.190, 1.083],
        "front_sprocket": 16,
        "rear_sprocket": 41,
        "chain_pitch": "525",
        "dry_mass_kg": 193.0,
        "wheelbase_mm": 1430.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/55ZR17",
        "cd": 0.62,
        "frontal_area_m2": 0.45,
    },
    source_name="spec_sheet",
)


# ── BMW HP4 Race (2017-2018 — limited 750-unit run) ─────────────────
# Carbon mainframe + carbon wheels. 215 hp / 146 kg dry. Track-only.
# Source: BMW Motorrad press release 2017 + MCN test.
BMW_HP4_RACE_2017 = spec_from_dict(
    {
        "manufacturer": "BMW",
        "model_name": "HP4 Race",
        "model_code": "K72",
        "year_from": 2017,
        "year_to": 2018,
        "category": "sport",
        "displacement_cc": 999,
        "bore_mm": 80.0,
        "stroke_mm": 49.7,
        "compression_ratio": 13.7,
        "cylinders": 4,
        "peak_power_hp": 215.0,
        "peak_power_rpm": 13900,
        "peak_torque_nm": 120.0,
        "peak_torque_rpm": 10000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        "gear_ratios": [2.647, 2.091, 1.727, 1.500, 1.333, 1.214],
        "front_sprocket": 17,
        "rear_sprocket": 45,
        "chain_pitch": "520",
        "dry_mass_kg": 146.0,
        "wheelbase_mm": 1432.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/55ZR17",
        "cd": 0.55,
        "frontal_area_m2": 0.42,
    },
    source_name="spec_sheet",
)


# ── Aprilia RSV4 1100 Factory FW1A (2025+) ──────────────────────────
# Homologation special, 1099cc V4, 217 hp + 200+ kit pieces. Limited run.
# Source: Aprilia Racing press release 2025.
APRILIA_RSV4_FACTORY_FW1A_2025 = spec_from_dict(
    {
        "manufacturer": "Aprilia",
        "model_name": "RSV4 1100 Factory FW1A",
        "model_code": "FW1A",
        "year_from": 2025,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 1099,
        "bore_mm": 81.0,
        "stroke_mm": 53.3,
        "compression_ratio": 13.6,
        "cylinders": 4,
        "peak_power_hp": 220.0,
        "peak_power_rpm": 13200,
        "peak_torque_nm": 125.0,
        "peak_torque_rpm": 11000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        "gear_ratios": [2.286, 1.840, 1.583, 1.421, 1.292, 1.192],
        "front_sprocket": 16,
        "rear_sprocket": 41,
        "chain_pitch": "525",
        "dry_mass_kg": 168.0,
        "wheelbase_mm": 1439.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/55ZR17",
        "cd": 0.55,
        "frontal_area_m2": 0.42,
    },
    source_name="spec_sheet",
)


# ── MV Agusta F4 RC (2017-2019 — homologation 250 units) ────────────
# 998cc inline-4, 212 hp street / 222 hp with race kit. 175 kg dry.
# Source: MV Agusta press release 2017.
MV_AGUSTA_F4_RC_2017 = spec_from_dict(
    {
        "manufacturer": "MV Agusta",
        "model_name": "F4 RC",
        "model_code": "F4RC",
        "year_from": 2017,
        "year_to": 2019,
        "category": "sport",
        "displacement_cc": 998,
        "bore_mm": 79.0,
        "stroke_mm": 50.9,
        "compression_ratio": 13.4,
        "cylinders": 4,
        "peak_power_hp": 212.0,
        "peak_power_rpm": 13600,
        "peak_torque_nm": 115.0,
        "peak_torque_rpm": 9300,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        "gear_ratios": [2.273, 1.789, 1.500, 1.318, 1.214, 1.130],
        "front_sprocket": 16,
        "rear_sprocket": 41,
        "chain_pitch": "525",
        "dry_mass_kg": 175.0,
        "wheelbase_mm": 1430.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/55ZR17",
        "cd": 0.58,
        "frontal_area_m2": 0.43,
    },
    source_name="spec_sheet",
)


# ── Honda RC213V-S (2015-2016 — MotoGP-derived 213 units worldwide) ─
# Honda's $190k MotoGP-bike-for-the-street. 999cc V4. 159 hp street /
# 215 hp with optional race kit. Carbon dry-clutch + Brembo.
# Source: Honda press kit 2015 + Cycle World long-term review.
HONDA_RC213V_S_2015 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "RC213V-S",
        "model_code": "SC75",
        "year_from": 2015,
        "year_to": 2016,
        "category": "sport",
        "displacement_cc": 999,
        "bore_mm": 81.0,
        "stroke_mm": 48.5,
        "compression_ratio": 13.0,
        "cylinders": 4,
        "peak_power_hp": 215.0,  # with race kit; street is 159
        "peak_power_rpm": 14000,
        "peak_torque_nm": 118.0,
        "peak_torque_rpm": 11500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        "gear_ratios": [2.250, 1.750, 1.471, 1.273, 1.143, 1.045],
        "front_sprocket": 16,
        "rear_sprocket": 39,
        "chain_pitch": "520",
        "dry_mass_kg": 160.0,
        "wheelbase_mm": 1465.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.56,
        "frontal_area_m2": 0.42,
    },
    source_name="spec_sheet",
)


# ── Kawasaki Z H2 SX SE+ (2024-current) ─────────────────────────────
# Supercharged sport-tourer. 998cc inline-4, 200 hp, 267 kg wet.
# Source: Kawasaki Motors press release 2024.
KAWASAKI_Z_H2_SX_SE_PLUS_2024 = spec_from_dict(
    {
        "manufacturer": "Kawasaki",
        "model_name": "Ninja H2 SX SE+",
        "model_code": "ZX1002",
        "year_from": 2024,
        "year_to": 2026,
        "category": "touring",
        "displacement_cc": 998,
        "bore_mm": 76.0,
        "stroke_mm": 55.0,
        "compression_ratio": 11.2,
        "cylinders": 4,
        "peak_power_hp": 200.0,
        "peak_power_rpm": 11000,
        "peak_torque_nm": 137.3,
        "peak_torque_rpm": 8500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        "gear_ratios": [2.706, 2.143, 1.762, 1.524, 1.348, 1.214],
        "front_sprocket": 17,
        "rear_sprocket": 42,
        "chain_pitch": "525",
        "dry_mass_kg": 248.0,  # wet 267 - ~19 fuel = 248 dry-ish
        "wheelbase_mm": 1480.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.56,
        "frontal_area_m2": 0.50,
    },
    source_name="spec_sheet",
)


# Master list — exported back to known_bikes.py
# ── KTM 1390 Super Duke R EVO (2024-2026) ────────────────────────────
# 1350cc 75° V-twin LC8 EVO, 190 hp at 10000 rpm, 145 Nm at 8000 rpm.
# Direct successor to the 1290 Super Duke R EVO using the SAME chassis,
# transmission cassette, and final drive (per KTM "the 1390 inherits the
# 1290 EVO platform with new pistons + crankshaft" — KTM 2024 press kit).
# So gear ratios + sprockets + chain pitch match the 1290 entry exactly;
# only bore (108→110 mm), displacement (1301→1350 cc), and power/torque
# are bumped.
# Sources: KTM official 2024 technical data sheet (ktm.com), MCN 2024
# launch test, Cycle World 2024 first-ride.
KTM_1390_SUPERDUKE_R_EVO_2024 = spec_from_dict(
    {
        "manufacturer": "KTM",
        "model_name": "1390 Super Duke R EVO",
        "model_code": "1390EVO",
        "year_from": 2024,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 1350,
        "bore_mm": 110.0,
        "stroke_mm": 71.0,
        "compression_ratio": 13.5,
        "cylinders": 2,
        "peak_power_hp": 190.0,
        "peak_power_rpm": 10000,
        "peak_torque_nm": 145.0,
        "peak_torque_rpm": 8000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # SAME cassette as 1290 Super Duke R EVO — KTM 2024 press kit
        # confirms transmission carryover.
        "gear_ratios": [2.500, 1.857, 1.538, 1.300, 1.148, 1.000],
        "front_sprocket": 17,
        "rear_sprocket": 41,
        "chain_pitch": "525",
        "dry_mass_kg": 200.0,  # 211 kg wet - ~11 kg fuel = ~200 dry
        "wheelbase_mm": 1497.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/55ZR17",
        "cd": 0.74,        # naked litre median; ref KTM 1290 SDR @ 0.73
        "frontal_area_m2": 0.55,  # marginally wider than 1290 (0.54)
    },
    source_name="spec_sheet",
)


# ── Hero Xtreme 200S 4V (2023-2026 — Indian commuter sport) ─────────
# 199.6cc oil-cooled single, 4-valve head, 19.1 hp @ 8500, 17.35 Nm @
# 6500. Half-faired commuter with sport-naked ergonomics. The "200S
# 4V" replaces the older 2-valve Xtreme 200S with a Karizma-derived
# 4V head — bumps power ~3 hp over the 2V variant.
# Sources: Hero MotoCorp official spec sheet (heromotocorp.com),
# 91Wheels review database, ZigWheels spec table.
HERO_XTREME_200S_4V_2023 = spec_from_dict(
    {
        "manufacturer": "Hero",
        "model_name": "Xtreme 200S 4V",
        "model_code": "X200S4V",
        "year_from": 2023,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 199.6,
        "bore_mm": 67.0,
        "stroke_mm": 56.5,
        "compression_ratio": 9.8,
        "cylinders": 1,
        "peak_power_hp": 19.1,
        "peak_power_rpm": 8500,
        "peak_torque_nm": 17.35,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "sohc",
        "gears": 5,
        # Standard 5-speed Hero 200cc commuter cassette — same as
        # Karizma R / 200cc Xtreme platform (Hero service manual).
        "gear_ratios": [3.182, 1.778, 1.318, 1.045, 0.875],
        "front_sprocket": 14,
        "rear_sprocket": 42,
        "chain_pitch": "428",
        "dry_mass_kg": 158.0,  # 165 kg kerb - ~7 kg fuel = ~158 dry
        "wheelbase_mm": 1335.0,
        "front_tire_size": "100/80-17",
        "rear_tire_size": "130/70-17",
        "cd": 0.78,        # half-faired commuter; ref Pulsar 220F @ 0.83, NS200 @ 0.80
        "frontal_area_m2": 0.46,  # ref TVS Apache RTR 200 @ 0.45
    },
    source_name="spec_sheet",
)


# Master list — exported back to known_bikes.py
EXTENDED_BIKES = [
    NORTON_V4SV_2022,
    BMW_HP4_RACE_2017,
    APRILIA_RSV4_FACTORY_FW1A_2025,
    MV_AGUSTA_F4_RC_2017,
    HONDA_RC213V_S_2015,
    KAWASAKI_Z_H2_SX_SE_PLUS_2024,
    # ── Daily improvement run 2026-05-04 (Monday — Catalog) ──
    KTM_1390_SUPERDUKE_R_EVO_2024,
    HERO_XTREME_200S_4V_2023,
]
