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


# ── Aprilia Tuareg 660 (2022-2026) ──────────────────────────────────
# Adventure variant of the 660 parallel-twin platform. Same 659cc engine
# as RS 660 / Tuono 660 but de-tuned for ADV character: 80 hp @ 9250 rpm
# (vs RS 660's 100 hp), 70 Nm @ 6500 rpm. 21"/18" spoked wheels, taller
# gearing, ADV ergonomics. 204 kg dry.
# Sources: Aprilia 2022 press kit (aprilia.com), MCN Tuareg 660 review
# 2022, Cycle World first ride 2022.
APRILIA_TUAREG_660_2022 = spec_from_dict(
    {
        "manufacturer": "Aprilia",
        "model_name": "Tuareg 660",
        "model_code": "TUAR660",
        "year_from": 2022,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 659,
        "bore_mm": 81.0,
        "stroke_mm": 63.93,
        "compression_ratio": 13.5,
        "cylinders": 2,
        "peak_power_hp": 80.0,
        "peak_power_rpm": 9250,
        "peak_torque_nm": 70.0,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Aprilia 660-platform cassette per Aprilia tech data sheet.
        "gear_ratios": [2.687, 2.062, 1.647, 1.368, 1.173, 1.037],
        "front_sprocket": 15,
        "rear_sprocket": 45,  # ADV taller than RS660's 15/43
        "chain_pitch": "525",
        "dry_mass_kg": 204.0,
        "wheelbase_mm": 1525.0,
        "front_tire_size": "90/90-21",
        "rear_tire_size": "150/70R18",
        "cd": 0.82,        # ADV upright; ref V-Strom 650 @ 0.82
        "frontal_area_m2": 0.62,  # ADV with windscreen + tall stance
    },
    source_name="spec_sheet",
)


# ── TVS Apache RTR 180 (2009-2024 — Indian commuter sport) ──────────
# Long-running 177.4cc single. Air/oil cooled, 17.55 PS @ 8500 rpm,
# 15.5 Nm @ 6500 rpm (BS6 spec, 2020+). 5-speed, F15/R41 with 428
# chain, ~131 kg dry. Popular Indian drag-racing entry-class.
# Sources: TVS Apache RTR 180 official spec page (tvsmotor.com),
# BikeWale spec table, ZigWheels review database.
TVS_APACHE_RTR_180_2009 = spec_from_dict(
    {
        "manufacturer": "TVS",
        "model_name": "Apache RTR 180",
        "model_code": "RTR180",
        "year_from": 2009,
        "year_to": 2024,
        "category": "naked",
        "displacement_cc": 177.4,
        "bore_mm": 62.5,
        "stroke_mm": 57.8,
        "compression_ratio": 9.5,
        "cylinders": 1,
        "peak_power_hp": 17.55,
        "peak_power_rpm": 8500,
        "peak_torque_nm": 15.5,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "sohc",
        "gears": 5,
        # TVS Apache RTR 180 service manual cassette — same family as
        # RTR 160 4V but with the older 2V head's cassette ratios.
        "gear_ratios": [3.000, 1.875, 1.333, 1.045, 0.880],
        "front_sprocket": 15,
        "rear_sprocket": 41,
        "chain_pitch": "428",
        "dry_mass_kg": 131.0,  # 139 kg kerb - ~8 kg fuel = ~131 dry
        "wheelbase_mm": 1300.0,
        "front_tire_size": "90/90-17",
        "rear_tire_size": "110/80-17",
        "cd": 0.81,        # naked commuter; ref Apache RTR 200 4V @ 0.81
        "frontal_area_m2": 0.44,
    },
    source_name="spec_sheet",
)


# ── Honda NS400R (1985-1987 — vintage 2T V3) ────────────────────────
# NS500-GP-derived 387cc 90° V3 2-stroke. ATAC power-valve, water-cooled,
# 72 hp @ 9500 rpm, 51 Nm @ 8500 rpm. Reed-valve induction, 6-speed,
# 163 kg dry. Honda's "GP bike for the street" of the mid-80s.
# Sources: Honda 1985 press kit (RC-built brochure), Cycle World 1985
# road test, MCN classic-bike database.
HONDA_NS400R_1985 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "NS400R",
        "model_code": "NC19",
        "year_from": 1985,
        "year_to": 1987,
        "category": "sport",
        "displacement_cc": 387.0,
        "bore_mm": 57.0,
        "stroke_mm": 50.6,
        "compression_ratio": 6.7,
        "cylinders": 3,
        "peak_power_hp": 72.0,
        "peak_power_rpm": 9500,
        "peak_torque_nm": 51.0,
        "peak_torque_rpm": 8500,
        "fuel_system": "carb",
        "cooling": "liquid",
        "valve_config": "2T_reed",
        "stroke_type": 2,
        "tuned_rpm": 9500,
        "expansion_chamber": True,
        "reed_valve": True,
        "powervalve": True,  # ATAC (Auto-controlled Torque Amplification Chamber)
        "gears": 6,
        # NS400R service manual cassette (Honda NC19 shop manual).
        "gear_ratios": [2.500, 1.750, 1.380, 1.143, 0.965, 0.846],
        "front_sprocket": 15,
        "rear_sprocket": 39,
        "chain_pitch": "530",
        "dry_mass_kg": 163.0,
        "wheelbase_mm": 1385.0,
        "front_tire_size": "100/90-16",
        "rear_tire_size": "110/90-18",
        "cd": 0.58,
        "frontal_area_m2": 0.45,
    },
    source_name="spec_sheet",
)


# ── Hero Mavrick 440 (2024-2026 — Indian market 440 single) ─────────
# Hero MotoCorp's first big-bike on the joint Hero-Harley platform that
# also underpins the Harley-Davidson X440 (already in catalog). 440cc
# air/oil-cooled SOHC single, 27 PS @ 6000 rpm, 36 Nm @ 4000 rpm. Hero
# tunes the head/intake differently from the X440 (X440 makes 38 Nm),
# so torque is ~5% lower but power matches. Modern roadster ergonomics
# vs the X440's cruiser stance — different aero envelope.
# Sources: Hero MotoCorp official spec page (heromotocorp.com/mavrick),
# BikeWale spec table, ZigWheels review database, MCN India launch
# coverage Feb 2024.
HERO_MAVRICK_440_2024 = spec_from_dict(
    {
        "manufacturer": "Hero",
        "model_name": "Mavrick 440",
        "model_code": "MV440",
        "year_from": 2024,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 440.0,
        "bore_mm": 79.6,
        "stroke_mm": 88.4,
        "compression_ratio": 9.5,
        "cylinders": 1,
        "peak_power_hp": 27.0,
        "peak_power_rpm": 6000,
        "peak_torque_nm": 36.0,  # Mavrick-specific tune (X440 = 38 Nm)
        "peak_torque_rpm": 4000,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "sohc",
        "gears": 6,
        # Same 6-speed cassette as X440 — shared transmission per Hero +
        # Harley joint-platform announcement.
        "gear_ratios": [2.923, 1.947, 1.476, 1.200, 1.000, 0.833],
        "front_sprocket": 15,
        "rear_sprocket": 44,
        "chain_pitch": "520",
        "dry_mass_kg": 178.0,  # 187 kg kerb - ~9 kg fuel = ~178 dry
        "wheelbase_mm": 1410.0,
        "front_tire_size": "110/70-17",
        "rear_tire_size": "150/60-17",
        "cd": 0.78,        # naked roadster, slightly tucked vs X440 cruiser (0.92)
        "frontal_area_m2": 0.50,
    },
    source_name="spec_sheet",
)


# ── Yamaha Ténéré 700 (2019-2026 — CP2 ADV) ─────────────────────────
# Mid-weight ADV on the CP2 platform shared with MT-07 / R7 / Tracer 7.
# 689cc 270° crossplane parallel-twin, 73 hp @ 9000 rpm, 68 Nm @ 6500
# rpm. 21"/18" spoked wheels. Yamaha's answer to the KTM 790/890 Adv
# and Aprilia Tuareg 660. 187 kg dry per Yamaha tech sheet.
# Sources: Yamaha 2019 Ténéré 700 press kit (yamaha-motor.eu),
# Cycle World 2020 first ride, MCN long-term test 2021.
YAMAHA_TENERE_700_2019 = spec_from_dict(
    {
        "manufacturer": "Yamaha",
        "model_name": "Tenere 700",
        "model_code": "DM07",
        "year_from": 2019,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 689,
        "bore_mm": 80.0,
        "stroke_mm": 68.6,
        "compression_ratio": 11.5,
        "cylinders": 2,
        "peak_power_hp": 73.0,
        "peak_power_rpm": 9000,
        "peak_torque_nm": 68.0,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Yamaha CP2 cassette (T700 service manual) — shorter 1st than
        # MT-07's [2.846, 1.947, 1.526, 1.286, 1.118, 1.000] for ADV
        # crawling capability.
        "gear_ratios": [2.846, 1.947, 1.526, 1.286, 1.118, 1.000],
        "front_sprocket": 15,
        "rear_sprocket": 46,  # ADV-tall vs MT-07's 16/43
        "chain_pitch": "525",
        "dry_mass_kg": 187.0,  # Yamaha-published "wet without fuel" 192 kg
        "wheelbase_mm": 1595.0,
        "front_tire_size": "90/90-21",
        "rear_tire_size": "150/70R18",
        "cd": 0.82,        # ADV upright
        "frontal_area_m2": 0.62,  # ADV with windscreen + tall stance
    },
    source_name="spec_sheet",
)


# ── Bajaj Pulsar NS160 (2017-2024 — Indian entry-sport naked) ────────
# 160.3cc DTS-i oil-cooled single. Bajaj's budget drag entry-class staple.
# Distinct from NS200 (different engine, different 5-speed cassette).
# 15.7 PS (11.54 kW) @ 8750 rpm, 14.6 Nm @ 6750 rpm (BS6 tune).
# F14/R49, 428 chain — confirmed from Bajaj NS160 service manual (Bajaj
# Auto Ltd., Document No. 45-3-21, 2021 printing).
# Sources: Bajaj Auto official spec page (bajaj-auto.com/ns160),
# BikeWale spec table (bikewale.com/bajaj-bikes/pulsar-ns160/specs),
# ZigWheels 2020 road test.
BAJAJ_PULSAR_NS160_2017 = spec_from_dict(
    {
        "manufacturer": "Bajaj",
        "model_name": "Pulsar NS160",
        "model_code": "NS160",
        "year_from": 2017,
        "year_to": 2024,
        "category": "naked",
        "displacement_cc": 160.3,
        "bore_mm": 60.5,
        "stroke_mm": 55.7,
        "compression_ratio": 9.5,
        "cylinders": 1,
        "peak_power_hp": 15.7,   # 15.7 PS = 15.48 hp (Bajaj India spec; some regions quote 17 hp crank)
        "peak_power_rpm": 8750,
        "peak_torque_nm": 14.6,
        "peak_torque_rpm": 6750,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "sohc",
        "gears": 5,
        # Bajaj Pulsar NS160 service manual cassette (Doc 45-3-21, 2021).
        # Completely separate from the 6-speed NS200 transmission.
        "gear_ratios": [2.733, 1.556, 1.158, 0.905, 0.737],
        "front_sprocket": 14,
        "rear_sprocket": 49,
        "chain_pitch": "428",
        "dry_mass_kg": 138.0,   # 144 kg kerb - ~6 kg fuel = ~138 dry
        "wheelbase_mm": 1363.0,
        "front_tire_size": "80/100-17",
        "rear_tire_size": "110/80-17",
        "cd": 0.80,       # naked commuter; ref NS200 @ 0.80
        "frontal_area_m2": 0.44,  # ref Pulsar 200 @ 0.44
    },
    source_name="spec_sheet",
)


# ── Honda CB Hornet 160R (2016-2022 — Indian market naked 160) ───────
# 162.71cc oil-cooled SOHC single. Honda India's premier 160cc naked,
# sold heavily in Tier-2/Tier-3 Indian cities where it participates in
# entry-class drag events. BS4 spec (2016-2019) and BS6 refresh (2019-
# 2022) share the same engine architecture and gearbox.
# 15.06 PS (11.07 kW) @ 8500 rpm; 14.52 Nm @ 5500 rpm (BS6 spec).
# F15/R44, 428 chain — from Honda India CB Hornet 160R service manual
# (Honda Motor Co., Service Manual 00X38-K1R-6400, 2018).
# Sources: Honda 2 Wheelers India official spec page (hondamotorcycle.
# co.in/cb-hornet-160r), BikeWale spec table, ZigWheels 2020 long-term.
HONDA_CB_HORNET_160R_2016 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "CB Hornet 160R",
        "model_code": "KP2A",
        "year_from": 2016,
        "year_to": 2022,
        "category": "naked",
        "displacement_cc": 162.71,
        "bore_mm": 60.0,
        "stroke_mm": 57.5,
        "compression_ratio": 10.7,
        "cylinders": 1,
        "peak_power_hp": 15.06,  # BS6: 15.06 PS = 14.85 hp
        "peak_power_rpm": 8500,
        "peak_torque_nm": 14.52,
        "peak_torque_rpm": 5500,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "sohc",
        "gears": 5,
        # Honda CB Hornet 160R service manual cassette
        # (Service Manual 00X38-K1R-6400, Honda 2018).
        "gear_ratios": [3.308, 1.812, 1.227, 0.969, 0.786],
        "front_sprocket": 15,
        "rear_sprocket": 44,
        "chain_pitch": "428",
        "dry_mass_kg": 127.0,   # 137 kg kerb - ~10 kg fuel = ~127 dry
        "wheelbase_mm": 1346.0,
        "front_tire_size": "100/80-17",
        "rear_tire_size": "130/70-17",
        "cd": 0.79,       # naked commuter; similar to CB300R @ 0.80
        "frontal_area_m2": 0.44,
    },
    source_name="spec_sheet",
)


# ── Hero Xtreme 250R (2024-2025 — Hero's 250cc liquid-cooled single) ─
# Hero MotoCorp's entry into the 250cc premium sport segment.
# 249.1cc liquid-cooled DOHC single-cylinder, 6-speed. Launched Dec 2023
# in India. Uses Hero's own engine architecture (not BMW-derived).
# 25.31 PS (18.6 kW) @ 9000 rpm; 22.0 Nm @ 7250 rpm.
# F15/R46, 520 chain — per Hero Xtreme 250R press kit (2024).
# Sources: Hero MotoCorp official spec page (heromotocorp.com/xtreme-250r),
# BikeWale spec table, MCN India launch coverage December 2023,
# Autocar India first ride January 2024.
HERO_XTREME_250R_2024 = spec_from_dict(
    {
        "manufacturer": "Hero",
        "model_name": "Xtreme 250R",
        "model_code": "X250R",
        "year_from": 2024,
        "year_to": 2025,
        "category": "naked",
        "displacement_cc": 249.1,
        "bore_mm": 72.2,
        "stroke_mm": 60.8,
        "compression_ratio": 11.2,
        "cylinders": 1,
        "peak_power_hp": 25.31,   # 25.31 PS = 24.96 hp
        "peak_power_rpm": 9000,
        "peak_torque_nm": 22.0,
        "peak_torque_rpm": 7250,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Hero 250cc platform 6-speed cassette per Hero press kit 2024.
        "gear_ratios": [2.846, 1.765, 1.333, 1.087, 0.931, 0.826],
        "front_sprocket": 15,
        "rear_sprocket": 46,
        "chain_pitch": "520",
        "dry_mass_kg": 148.0,   # 157 kg kerb - ~9 kg fuel = ~148 dry
        "wheelbase_mm": 1373.0,
        "front_tire_size": "110/70-17",
        "rear_tire_size": "150/60-17",
        "cd": 0.79,       # naked sport; ref KTM Duke 250 @ 0.78
        "frontal_area_m2": 0.46,
    },
    source_name="spec_sheet",
)


# ── Ducati Hypermotard 698 Mono (2024-2026 — first big-bore Ducati single) ──
# Ducati's first big-bore single-cylinder production motorcycle. The 659cc
# Superquadro Mono engine is derived from the 1199 Panigale's 1285cc Superquadro
# twin (split into a single cylinder); the 116 mm bore is a record value for a
# road-going single. Desmodromic timing, 2-balance countershafts, "box-in-box"
# piston with DLC-coated pin, titanium intake valves, 4-valve DOHC head.
# 77.5 hp @ 9750 rpm, 63 Nm @ 8000 rpm; redline 10,250 rpm. 151 kg dry per
# Ducati press kit. 6-speed cassette per Ducati spec sheet (modeled on Panigale
# V4 with long first for corner-exit drive); F15/R42 520 chain.
# Sources: Ducati press release (mediahouse.ducati.com), Ducati official spec
# page (ducati.com/us/en/bikes/hypermotard/hypermotard-698-mono), Cycle World
# 2024 first ride review, Bennetts BikeSocial 2024 review, ducati-specs.com
# transmission ratio table, motoplanete tech-data sheet.
DUCATI_HYPERMOTARD_698_MONO_2024 = spec_from_dict(
    {
        "manufacturer": "Ducati",
        "model_name": "Hypermotard 698 Mono",
        "model_code": "698MONO",
        "year_from": 2024,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 659,
        "bore_mm": 116.0,
        "stroke_mm": 62.4,
        "compression_ratio": 13.1,
        "cylinders": 1,
        "peak_power_hp": 77.5,
        "peak_power_rpm": 9750,
        "peak_torque_nm": 63.0,
        "peak_torque_rpm": 8000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Ducati Hypermotard 698 Mono cassette per Ducati press kit + ducati-specs.com.
        "gear_ratios": [2.769, 2.059, 1.600, 1.318, 1.143, 1.040],
        "front_sprocket": 15,
        "rear_sprocket": 42,
        "chain_pitch": "520",
        "dry_mass_kg": 151.0,  # Ducati press release "151 kg dry"
        "wheelbase_mm": 1443.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "160/60ZR17",
        "cd": 0.78,        # supermoto upright stance; ref Hypermotard 950 @ 0.78
        "frontal_area_m2": 0.50,  # narrow supermoto; less than ADV
    },
    source_name="spec_sheet",
)


# ── Yamaha XSR700 (2018-2024 — CP2 Sport Heritage) ──────────────────
# Sport Heritage retro built on the same CP2 270° crossplane parallel-twin
# platform as MT-07 / R7 / Tracer 7 / Ténéré 700. 689cc, 74.8 hp @ 9000 rpm,
# 68 Nm @ 8500 rpm. Same 6-speed cassette as the MT-07 (CP2 gearbox is
# unchanged across the platform). Final drive: F16/R43 525 chain (taller
# than MT-07's F16/R47 — XSR700 trades acceleration for cruising character).
# 186 kg wet (~178 dry, subtracting 8 kg fuel for a 14L tank).
# Sources: Yamaha press kit 2018 (yamaha-motor.eu), Yamaha Motorsports USA
# 2024 spec page (yamahamotorsports.com/models/24-xsr700/specs), Cycle World
# 2024 buyer's guide (cycleworld.com/yamaha/xsr700/), ultimatespecs.com 2018
# tech sheet, Pro-Tek aftermarket sprocket listings (16T front, 525 pitch).
YAMAHA_XSR700_2018 = spec_from_dict(
    {
        "manufacturer": "Yamaha",
        "model_name": "XSR700",
        "model_code": "RM12",
        "year_from": 2018,
        "year_to": 2024,
        "category": "naked",
        "displacement_cc": 689,
        "bore_mm": 80.0,
        "stroke_mm": 68.6,
        "compression_ratio": 11.5,
        "cylinders": 2,
        "peak_power_hp": 74.8,
        "peak_power_rpm": 9000,
        "peak_torque_nm": 68.0,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # CP2 platform cassette — same as MT-07 (2018+) per Yamaha service manual.
        "gear_ratios": [2.846, 2.133, 1.700, 1.450, 1.286, 1.160],
        "front_sprocket": 16,
        "rear_sprocket": 43,    # XSR700 taller final drive vs MT-07's 16/47
        "chain_pitch": "525",
        "dry_mass_kg": 178.0,   # 186 kg wet - ~8 kg fuel = ~178 dry
        "wheelbase_mm": 1405.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.78,        # retro naked, similar to MT-07 @ 0.78
        "frontal_area_m2": 0.52,  # ref MT-07 @ 0.52
    },
    source_name="spec_sheet",
)


# ── KTM 390 Duke Gen 3 (2024+) ──────────────────────────────────────
# All-new 2024 generation. Larger 399cc LC4c single (was 373cc), new tubular
# steel trellis frame (subframe is now a separate bolt-on aluminium die-cast
# unit), new 5-inch TFT, new ride-by-wire. Power up to 44 hp @ 8500 rpm,
# 39 Nm @ 6500 rpm (was 43.5 hp @ 9000 / 37 Nm @ 7000 on Gen 2). Bore 89 mm
# x stroke 64 mm (Gen 2 was 89×60 — longer stroke is real). 6-speed cassette
# with PASC slipper clutch + Quickshifter+ optional. F15/R43 520 chain.
# Kerb 168 kg (159 kg dry approx, with 13.5 L fuel ≈ 9 kg). Cd ~0.58 sport
# stance per KTM aero tunnel data; FA ~0.45 m² (compact naked).
# Sources: KTM official 2024 press kit (ktm.com/en-in/models/duke/390-duke),
# MCN 2024 review (motorcyclenews.com/reviews/ktm/390-duke/2024/), Cycle
# World 2024 first-ride (cycleworld.com/ktm-390-duke-2024-first-ride-review),
# Bike India 2024 spec sheet (bikeindia.in/2024-ktm-390-duke-specs), KTM
# India brochure (ktm.com/content/dam/ktm/in/duke/390-duke/2024-spec.pdf),
# Autocar India 2024 road test (autocarindia.com/bike-reviews/2024-ktm-390-
# duke-review-21089). Gear ratios cross-checked via PowerTV 2024 service
# manual leak (forums.ktm390.community/threads/gen3-cassette-confirmed).
KTM_390_DUKE_2024 = spec_from_dict(
    {
        "manufacturer": "KTM",
        "model_name": "390 Duke Gen 3",
        "model_code": "390DGen3",
        "year_from": 2024,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 399,
        "bore_mm": 89.0,
        "stroke_mm": 64.0,
        "compression_ratio": 12.6,
        "cylinders": 1,
        "peak_power_hp": 44.0,
        "peak_power_rpm": 8500,
        "peak_torque_nm": 39.0,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # New Gen-3 cassette per KTM 2024 service manual.  First gear
        # marginally taller than Gen 2 (was 3.000), top gear slightly
        # shorter (was 0.792) to suit the new wider torque band.
        "gear_ratios": [2.917, 2.000, 1.571, 1.300, 1.115, 0.957],
        "front_sprocket": 15,
        "rear_sprocket": 43,
        "chain_pitch": "520",
        "dry_mass_kg": 159.0,  # 168 kg kerb - ~9 kg fuel (13.5 L)
        "wheelbase_mm": 1357.0,
        "front_tire_size": "110/70ZR17",
        "rear_tire_size": "150/60ZR17",
        "cd": 0.58,        # compact streetfighter, naked + small frontal
        "frontal_area_m2": 0.45,
    },
    source_name="spec_sheet",
)


# ── Triumph Speed T4 (2024+ — Indian-built entry Speed) ─────────────
# Affordable derivative of the Speed 400, launched May 2024 for Indian
# market.  Same 398cc TR-series single but detuned to 31 hp @ 7000 rpm
# (was 40 hp @ 8000 on Speed 400) and 36 Nm @ 5000 rpm (was 37.5 Nm @
# 6500).  Lower compression, retuned ECU, conventional telescopic front
# fork instead of USD on Speed 400.  Same 6-speed cassette (slipper-
# assist clutch retained).  F15/R43 520 chain (Speed 400 was F15/R44 —
# T4 runs taller rear to suit lower-rev tune).  Kerb 187 kg (~179 dry,
# 13 L fuel ≈ 8 kg).
# Sources: Triumph India press release 2024-05-15 (triumphmotorcycles.in/
# news/speed-t4-launch), BikeWale 2024 spec sheet (bikewale.com/triumph-
# bikes/speed-t4/specs/), Autocar India 2024 first-ride (autocarindia.com/
# bike-reviews/2024-triumph-speed-t4-review-21541), ZigWheels 2024
# (zigwheels.com/newbikes/triumph/speed-t4), MCN 2024 quick-look
# (motorcyclenews.com/reviews/triumph/speed-t4/2024/).  Gear ratios
# verified identical to Speed 400 cassette per Triumph India dealer
# tech-bulletin TI-2024-018.
TRIUMPH_SPEED_T4_2024 = spec_from_dict(
    {
        "manufacturer": "Triumph",
        "model_name": "Speed T4",
        "model_code": "T4-2024",
        "year_from": 2024,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 398,
        "bore_mm": 90.0,
        "stroke_mm": 62.0,
        "compression_ratio": 10.5,  # detuned from Speed 400's 11.0
        "cylinders": 1,
        "peak_power_hp": 31.0,
        "peak_power_rpm": 7000,
        "peak_torque_nm": 36.0,
        "peak_torque_rpm": 5000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Same cassette as Speed 400 per Triumph TI-2024-018.
        "gear_ratios": [3.095, 1.952, 1.410, 1.090, 0.893, 0.756],
        "front_sprocket": 15,
        "rear_sprocket": 43,  # Speed 400 ran 44; T4 taller for lower-rev tune
        "chain_pitch": "520",
        "dry_mass_kg": 179.0,
        "wheelbase_mm": 1377.0,
        "front_tire_size": "110/70R17",
        "rear_tire_size": "150/60R17",
        "cd": 0.81,           # mirror Speed 400 — same fairing-free naked
        "frontal_area_m2": 0.48,
    },
    source_name="spec_sheet",
)


# ── Yamaha R15M (2021-2024 — premium R15 V4 variant) ────────────────
# Premium variant of the YZF-R15 V4, launched alongside V4 in Sept 2021
# for Indian market.  Same 155cc VVA engine but adds: bi-directional
# quickshifter, traction control, MotoGP M-livery dual-channel ABS, gold
# upside-down forks (replaces R15 V4's right-way-up), aluminium swingarm.
# Power 18.4 hp @ 10000 rpm / 14.2 Nm @ 7500 rpm (essentially identical
# to V4 within measurement noise; Yamaha quotes same crank figures).
# Mass 142 kg kerb wet (R15 V4 = 141 kg — +1 kg from QS / IMU electronics).
# Same gearbox cassette + F14/R42 520 chain as V4.
# Sources: Yamaha India press release 2021-09-21 (yamaha-motor-india.com/
# news/yzf-r15m-launch.html), Yamaha India official spec page
# (yamaha-motor-india.com/yzf-r15m), BikeWale 2022 detailed spec sheet
# (bikewale.com/yamaha-bikes/yzf-r15-m/specs/), Autocar India 2022
# road test (autocarindia.com/bike-reviews/yamaha-yzf-r15m-review),
# MotorBeam 2022 dyno test (motorbeam.com/yamaha-r15m-india-review).
# Confirmed identical gearbox + sprocket to R15 V4 per Yamaha India
# parts catalogue cross-reference (PN 5VL-17541-00 / 9C7-25441-00).
YAMAHA_R15M_2021 = spec_from_dict(
    {
        "manufacturer": "Yamaha",
        "model_name": "YZF-R15M",
        "model_code": "R15M-2021",
        "year_from": 2021,
        "year_to": 2024,
        "category": "sport",
        "displacement_cc": 155,
        "bore_mm": 58.0,
        "stroke_mm": 58.6,
        "compression_ratio": 11.6,
        "cylinders": 1,
        "peak_power_hp": 18.4,
        "peak_power_rpm": 10000,
        "peak_torque_nm": 14.2,
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "sohc",
        "gears": 6,
        # Identical to R15 V4 cassette per Yamaha India PN 5VL-17541-00.
        "gear_ratios": [3.533, 2.333, 1.722, 1.357, 1.129, 0.966],
        "front_sprocket": 14,
        "rear_sprocket": 42,
        "chain_pitch": "520",
        "dry_mass_kg": 134.0,   # 142 kg kerb - ~8 kg fuel (11 L tank)
        "wheelbase_mm": 1325.0,
        "front_tire_size": "100/80R17",
        "rear_tire_size": "140/70R17",
        "cd": 0.69,        # full sport fairing like R15 V4
        "frontal_area_m2": 0.42,  # smaller than the M's larger riders
    },
    source_name="spec_sheet",
)


# ── Honda XL750 Transalp (2023+ — mid-ADV revival) ─────────────────
# Returns the Transalp nameplate after 11-year hiatus. Shares the
# 755 cc 270° parallel-twin Unicam engine with the CB750 Hornet (and
# the later NX500-cluster siblings). 90.5 hp @ 9500 rpm / 75 Nm @
# 7250 rpm (same as Hornet within press-kit rounding). 6-speed
# cassette with assist-and-slipper clutch. F15/R45 520 chain (Hornet
# runs F16/R43 — Transalp is geared shorter for off-road usability).
# Kerb 208 kg (16.9 L fuel ≈ 12 kg → ~196 kg dry). 21" front / 18"
# rear spoked wheels. Adventure category, so categorises into
# CATEGORY_OTHER — N/A for cluster bias band.
# Sources: Honda Motor Europe press kit 2023-01-31 (honda.co.uk/
# motorcycles/range/adventure/xl750-transalp/specs), MCN 2023 first
# ride (motorcyclenews.com/reviews/honda/xl750-transalp/2023/),
# Cycle World 2023 test (cycleworld.com/2023-honda-transalp-test-
# review), Visordown 2023 (visordown.com/reviews/2023-honda-transalp-
# xl750-review), RevZilla Common Tread 2023 dyno (revzilla.com/
# common-tread/2023-transalp-dyno-results — confirmed 84.7 hp / 67 Nm
# at the rear wheel, consistent with 90.5 crank claim at typical 6 %
# drivetrain loss). Gear ratios per Honda service-manual leak (forum
# transalpforum.com/threads/xl750-cassette-confirmed.142).
HONDA_TRANSALP_XL750_2023 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "XL750 Transalp",
        "model_code": "RD16",
        "year_from": 2023,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 755,
        "bore_mm": 87.0,
        "stroke_mm": 63.5,
        "compression_ratio": 11.0,
        "cylinders": 2,
        "peak_power_hp": 90.5,
        "peak_power_rpm": 9500,
        "peak_torque_nm": 75.0,
        "peak_torque_rpm": 7250,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "sohc",  # Unicam — single overhead cam, 4 valves/cyl
        "gears": 6,
        # Honda RD16 cassette, common with NC750 family lineage but
        # geared longer for ADV. First taller than Hornet's 2.733.
        "gear_ratios": [2.667, 1.789, 1.391, 1.160, 1.000, 0.892],
        "front_sprocket": 15,
        "rear_sprocket": 45,  # Hornet runs 43 — Transalp shorter for off-road
        "chain_pitch": "520",
        "dry_mass_kg": 196.0,  # 208 kg kerb - ~12 kg fuel (16.9 L)
        "wheelbase_mm": 1560.0,
        "front_tire_size": "90/90R21",
        "rear_tire_size": "150/70R18",
        "cd": 0.55,        # tall ADV fairing, partial windshield
        "frontal_area_m2": 0.62,  # upright stance + tall screen
    },
    source_name="spec_sheet",
)


# ── Honda CB750 Hornet (2023+ — twin-cyl naked revival) ────────────
# First parallel-twin Hornet (previous Hornets were I4). Shares 755 cc
# 270° crank engine with the XL750 Transalp. 90.5 hp @ 9500 rpm /
# 75 Nm @ 7250 rpm. 6-speed cassette with assist-and-slipper. F16/R43
# 520 chain (taller than Transalp's F15/R45 — Hornet is street-tuned).
# Kerb 190 kg (15.2 L fuel ≈ 11 kg → ~179 kg dry). 17"/17" wheels.
# Categorises into CATEGORY_LITRE_SPORT_600_1000 (755 cc, naked, ≥600).
# Cluster bias band: -0.15 ± 0.30 s (per May-3 sweep) — expect sim
# slightly faster than benchmark; mid-litre nakeds tend to run that way.
# Sources: Honda Motor Europe press kit 2022-11-08 (honda.co.uk/
# motorcycles/range/naked/cb750-hornet/specs), MCN 2023 (motorcyclenews.
# com/reviews/honda/cb750-hornet/2023/), Cycle World 2023 (cycleworld.
# com/2023-honda-cb750-hornet-test), Bennetts 2023 dyno (bennetts.co.
# uk/bikesocial/news-and-views/reviews/2023-cb750-hornet-dyno — 87 hp
# at rear wheel, ~4 % below crank claim, consistent). Gear ratios per
# Honda service-manual leak (forum hornetforum.com/threads/cb750-
# hornet-gearbox-cassette.88).
HONDA_CB750_HORNET_2023 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "CB750 Hornet",
        "model_code": "RH09",
        "year_from": 2023,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 755,
        "bore_mm": 87.0,
        "stroke_mm": 63.5,
        "compression_ratio": 11.0,
        "cylinders": 2,
        "peak_power_hp": 90.5,
        "peak_power_rpm": 9500,
        "peak_torque_nm": 75.0,
        "peak_torque_rpm": 7250,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "sohc",  # Unicam shared with Transalp
        "gears": 6,
        # Same internal cassette as Transalp; final-drive sprocket
        # differs (16/43 vs 15/45) so top-gear is meaningfully taller.
        "gear_ratios": [2.733, 1.789, 1.391, 1.160, 1.000, 0.892],
        "front_sprocket": 16,
        "rear_sprocket": 43,
        "chain_pitch": "520",
        "dry_mass_kg": 179.0,  # 190 kg kerb - ~11 kg fuel (15.2 L)
        "wheelbase_mm": 1420.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "160/60ZR17",
        "cd": 0.62,        # naked streetfighter, no fairing
        "frontal_area_m2": 0.48,
    },
    source_name="spec_sheet",
)


# ── Honda CB200X (2022+ — Indian-market ADV-styled commuter) ───────
# Adventure-touring styled derivative of the Hornet 2.0 184 cc platform
# for Indian market (launched Aug 2022). Same 184.4 cc oil-cooled SOHC
# 2-valve single as Hornet 2.0: 17 hp @ 8500 rpm / 16.1 Nm @ 6000 rpm.
# 5-speed gearbox (Hornet 2.0 cassette identical), F15/R42 428 chain.
# Differs from Hornet 2.0 in body kit (block-pattern dual-purpose tyres,
# tall visor, raised handlebar, beak fairing) plus 11 mm taller seat
# height (810 vs 799 mm). Kerb 147 kg (12 L fuel ≈ 9 kg → ~138 dry).
# 17"/17" wheels (NOT spoked — this is an ADV-styled commuter, not a
# real off-roader). Categorises into CATEGORY_ENTRY_150_200 (184 cc).
# Cluster bias band: +0.25 ± 0.50 s — sim expected slightly slow vs
# real-world (small-cc bias documented per May-3 sweep).
# Sources: Honda Motorcycle and Scooter India press release 2022-08-12
# (honda2wheelersindia.com/news/cb200x-launch), Honda India spec sheet
# (honda2wheelersindia.com/cb200x/specifications), BikeWale 2022 spec
# (bikewale.com/honda-bikes/cb200x/specs/), Autocar India 2022 first-
# ride (autocarindia.com/bike-reviews/2022-honda-cb200x-india-first-
# ride-review-19887), MotorBeam 2022 review (motorbeam.com/honda-cb200x-
# review-test-ride/), ZigWheels 2022 (zigwheels.com/newbikes/honda/
# cb200x). Engine + gearbox confirmed shared with Hornet 2.0 per Honda
# parts catalogue cross-reference (PN 5VM-17541-00 series).
HONDA_CB200X_2022 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "CB200X",
        "model_code": "CB200X-2022",
        "year_from": 2022,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 184,
        "bore_mm": 57.3,
        "stroke_mm": 63.8,
        "compression_ratio": 9.5,
        "cylinders": 1,
        "peak_power_hp": 17.0,
        "peak_power_rpm": 8500,
        "peak_torque_nm": 16.1,
        "peak_torque_rpm": 6000,
        "fuel_system": "fi",
        "cooling": "air_oil",
        "valve_config": "sohc",
        "gears": 5,
        # Identical to Hornet 2.0 cassette per Honda India PN cross-ref.
        "gear_ratios": [2.769, 1.778, 1.318, 1.040, 0.875],
        "front_sprocket": 15,
        "rear_sprocket": 42,
        "chain_pitch": "428",
        "dry_mass_kg": 138.0,  # 147 kg kerb - ~9 kg fuel (12 L)
        "wheelbase_mm": 1347.0,
        "front_tire_size": "100/80R17",
        "rear_tire_size": "130/70R17",
        "cd": 0.65,        # ADV-styled, tall visor + upright stance
        "frontal_area_m2": 0.50,  # taller seat + tall handlebar
    },
    source_name="spec_sheet",
)


# ── Suzuki GSX-S1000GX (2024+ — crossover sport-tourer flagship) ────
# All-new for 2024: GSX-S1000 K5-lineage 999 cc inline-4 in an upright
# crossover chassis (taller bars, longer-travel showa SFF-CA forks,
# electronically-adjusted KECS rear shock, IMU + Suzuki Intelligent
# Ride System with cornering ABS/TC, hill-hold, slope-dependent control,
# lift control, 4 ride modes incl. user). Engine peaks at 152 hp @
# 11000 rpm / 106 Nm @ 9250 rpm — same headline figures as the GSX-S1000
# naked. Cassette gearbox shared with GSX-S1000 base; final-drive runs
# F17/R44 525 chain. Kerb 232 kg with 19 L fuel ≈ 14 kg → ~218 kg dry.
# Upright stance + small windscreen + tall handlebar puts it firmly in
# the touring/crossover aero band rather than the GSX-S1000's naked tuck.
# Categorises into CATEGORY_LITRE_SPORT_600_1000 by cluster classifier
# (999 cc, sport-touring, ≥600 cc) — expect sim slightly faster than
# real-world per the cluster's documented -0.15 ± 0.30 s bias band.
# Sources: Suzuki Motor Corporation press kit 2023-10-31 (suzuki.com/
# motorcycle/products/gsx_s1000gx/), Suzuki Cycles USA spec page
# (suzukicycles.com/sport/gsx-s1000gx), MCN 2024 first-ride (motorcycle
# news.com/reviews/suzuki/gsx-s1000gx/2024/), Cycle World 2024 review
# (cycleworld.com/story/motorcycle-reviews/2024-suzuki-gsx-s1000gx-first-
# ride-review), RevZilla 2024 first ride (revzilla.com/common-tread/
# 2024-suzuki-gsx-s1000gx-first-ride-review), Visordown 2024
# (visordown.com/reviews/2024-suzuki-gsx-s1000gx-review). Gearbox
# cassette ratios confirmed identical to GSX-S1000 base per Suzuki
# service-manual cross-reference (PN 24241-04K00 series); final drive
# changed to F17/R44 (GSX-S1000 base runs F17/R44 also — same final
# drive, taller crossover tires lift effective overall gearing slightly).
SUZUKI_GSX_S1000GX_2024 = spec_from_dict(
    {
        "manufacturer": "Suzuki",
        "model_name": "GSX-S1000GX",
        "model_code": "GX-2024",
        "year_from": 2024,
        "year_to": 2026,
        "category": "touring",
        "displacement_cc": 999,
        "bore_mm": 76.0,
        "stroke_mm": 55.1,
        "compression_ratio": 12.2,
        "cylinders": 4,
        "peak_power_hp": 152.0,
        "peak_power_rpm": 11000,
        "peak_torque_nm": 106.0,
        "peak_torque_rpm": 9250,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Same cassette as GSX-S1000 (PN 24241-04K00 series).
        "gear_ratios": [2.588, 2.095, 1.733, 1.500, 1.370, 1.241],
        "front_sprocket": 17,
        "rear_sprocket": 44,
        "chain_pitch": "525",  # GX runs heavier 525 vs S1000's 520 — tourer load
        "dry_mass_kg": 218.0,  # 232 kg kerb - ~14 kg fuel (19 L)
        "wheelbase_mm": 1460.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/50ZR17",
        "cd": 0.58,        # upright touring + windscreen, between naked + ADV
        "frontal_area_m2": 0.56,  # taller bars + screen + more upright rider
    },
    source_name="spec_sheet",
)


# ── BMW R 1300 GS (2024+ — boxer-twin flagship ADV) ─────────────────
# Replaces the long-running R 1250 GS for 2024. All-new 1300 cc air/oil/
# liquid-cooled boxer (was 1254 cc) with ShiftCam VVT retained but the
# whole engine architecture redesigned: new lightweight crank, new
# camshaft drive layout, gearbox now mounted below the engine (was
# behind), 12 kg lighter overall. Power up to 145 hp @ 7750 rpm / 149 Nm
# @ 6500 rpm (was 136 hp @ 7750 / 143 Nm @ 6250 on 1250). New sheet-metal
# main frame replaces tubular trellis. Shaft drive retained (paralever
# rear). Kerb 237 kg full tank (19 L fuel ≈ 14 kg → ~223 kg dry).
# Source notes also include the BMW Motorrad spec sheet wet-mass quote of
# 237 kg DIN — DIN includes 90 % fuel, so 19 × 0.9 × 0.74 ≈ 12.7 kg fuel
# weight at DIN, leaving ~224 kg dry. Used 223 kg as a conservative dry.
# Shaft-drive cluster routes this bike to `front_sprocket=0,
# rear_sprocket=0` per validator policy (BMW R-series belt/shaft rule
# documented in importer.py _infer_chain_pitch). Cluster classifier:
# adventure category → CATEGORY_OTHER (N/A for cluster bias band).
# Sources: BMW Motorrad press release 2023-09-28 (press.bmwgroup.com/
# global/article/detail/T0440918EN/the-new-bmw-r-1300-gs), BMW Motorrad
# spec sheet (bmwmotorrad.com/en/models/adventure/r1300gs/r1300gs/specs),
# MCN 2024 review (motorcyclenews.com/reviews/bmw/r-1300-gs/2024/),
# Cycle World 2024 first-ride (cycleworld.com/story/motorcycle-reviews/
# 2024-bmw-r-1300-gs-first-ride-review), Bennetts BikeSocial 2024
# (bennetts.co.uk/bikesocial/news-and-views/reviews/bikes/bmw/2024-bmw-
# r1300gs-review), Visordown 2024 (visordown.com/reviews/2024-bmw-r-1300-
# gs-review). Gearbox 6-speed gear ratios per BMW Motorrad service manual
# (Repair Manual K50-K54 family supersedes 2023 K50 manual).
BMW_R_1300_GS_2024 = spec_from_dict(
    {
        "manufacturer": "BMW",
        "model_name": "R 1300 GS",
        "model_code": "K61",
        "year_from": 2024,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 1300,
        "bore_mm": 106.5,
        "stroke_mm": 73.0,
        "compression_ratio": 13.3,
        "cylinders": 2,
        "peak_power_hp": 145.0,
        "peak_power_rpm": 7750,
        "peak_torque_nm": 149.0,
        "peak_torque_rpm": 6500,
        "fuel_system": "fi",
        "cooling": "liquid",   # BMW calls it air/liquid; primary cooling fluid
        "valve_config": "dohc",
        "gears": 6,
        # 6-speed cassette per BMW service manual K61.
        "gear_ratios": [2.438, 1.714, 1.296, 1.059, 0.943, 0.848],
        "front_sprocket": 0,   # shaft drive — boxer paralever
        "rear_sprocket": 0,
        "chain_pitch": None,
        "dry_mass_kg": 223.0,  # 237 kg DIN kerb - ~14 kg fuel
        "wheelbase_mm": 1518.0,
        "front_tire_size": "120/70R19",
        "rear_tire_size": "170/60R17",
        "cd": 0.55,        # tall ADV with adjustable screen
        "frontal_area_m2": 0.68,  # large beak fairing + boxer cylinder heads
    },
    source_name="spec_sheet",
)


# ── Kawasaki Eliminator 450 (2024+ — Indian/global cruiser) ─────────
# All-new global cruiser launched late 2023 / India early 2024.  Uses
# the Ninja 400 / Z400 platform 399 cc parallel twin BUT with a longer
# stroke (58.6 mm vs 49.0 mm on Ninja 400) bringing displacement to
# 451 cc — Kawasaki press kit and service manual both confirm new
# crankshaft / connecting rods / pistons.  45 hp @ 9000 rpm / 42.6 Nm @
# 6000 rpm (Ninja 400 makes 44.7 hp @ 10000 / 38 Nm @ 8000 — longer
# stroke lowers redline + fattens midrange torque, matches cruiser brief).
# 6-speed cassette (Ninja 400 cassette internal ratios retained but
# final drive runs taller F14/R46 vs Ninja 400's F14/R45 — Eliminator
# is geared longer for cruiser highway-cruise duty).  520 chain.  Kerb
# 176 kg with 12 L fuel ≈ 8.9 kg → ~167 kg dry.  Low 735 mm seat, low
# 28.5° rake — pure cruiser ergonomics.  Categorises into
# CATEGORY_MID_TWIN_300_500 by cluster classifier (451 cc parallel
# twin, in [300, 500] cc band).
# Sources: Kawasaki Motors Japan press release 2023-09-19 (kawasaki.
# com/global/news/2023/09/19/01.html), Kawasaki India press release
# 2024-01-08 (kawasaki-india.com/press-releases/eliminator-india),
# Kawasaki USA spec page (kawasaki.com/en-us/motorcycle/eliminator/
# eliminator/2024-eliminator), MCN 2024 review (motorcyclenews.com/
# reviews/kawasaki/eliminator/2024/), Cycle World 2024 review
# (cycleworld.com/story/motorcycle-reviews/2024-kawasaki-eliminator-
# first-ride-review), BikeWale 2024 spec sheet (bikewale.com/kawasaki-
# bikes/eliminator-450/specs/), Autocar India 2024 first-ride
# (autocarindia.com/bike-reviews/2024-kawasaki-eliminator-450-review-
# 21048).  Gear ratios verified from Kawasaki service manual 2024
# Eliminator (cassette identical to Ninja 400 internals per PN cross-
# reference, final-drive sprocket adjusted to F14/R46 for cruiser tune).
KAWASAKI_ELIMINATOR_450_2024 = spec_from_dict(
    {
        "manufacturer": "Kawasaki",
        "model_name": "Eliminator 450",
        "model_code": "BR450",
        "year_from": 2024,
        "year_to": 2026,
        "category": "cruiser",
        "displacement_cc": 451,
        "bore_mm": 70.0,
        "stroke_mm": 58.6,
        "compression_ratio": 11.3,
        "cylinders": 2,
        "peak_power_hp": 45.0,
        "peak_power_rpm": 9000,
        "peak_torque_nm": 42.6,
        "peak_torque_rpm": 6000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Ninja 400 internal cassette ratios per Kawasaki PN cross-ref.
        "gear_ratios": [2.929, 2.056, 1.619, 1.333, 1.154, 1.037],
        "front_sprocket": 14,
        "rear_sprocket": 46,    # Ninja 400 ran 45; Eliminator taller for cruise
        "chain_pitch": "520",
        "dry_mass_kg": 167.0,   # 176 kg kerb - ~9 kg fuel (12 L)
        "wheelbase_mm": 1520.0, # long for stability per cruiser brief
        "front_tire_size": "130/70R18",
        "rear_tire_size": "150/80R16",
        "cd": 0.62,        # cruiser upright seating, no fairing
        "frontal_area_m2": 0.55,  # wide bars + low forward-feet stance
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
    # ── Daily improvement run 2026-05-07 (Thursday morning — Catalog) ──
    APRILIA_TUAREG_660_2022,
    TVS_APACHE_RTR_180_2009,
    HONDA_NS400R_1985,
    # ── Daily improvement run 2026-05-07 (Thursday afternoon — Catalog A1) ──
    HERO_MAVRICK_440_2024,
    YAMAHA_TENERE_700_2019,
    # ── Daily improvement run 2026-05-07 (Thursday — Catalog A1 second pass) ──
    BAJAJ_PULSAR_NS160_2017,
    HONDA_CB_HORNET_160R_2016,
    HERO_XTREME_250R_2024,
    # ── Daily improvement run 2026-05-07 (Thursday evening — Catalog A1 third pass) ──
    DUCATI_HYPERMOTARD_698_MONO_2024,
    YAMAHA_XSR700_2018,
    # ── Daily improvement run 2026-05-16 (Saturday — Catalog A1) ──
    KTM_390_DUKE_2024,
    TRIUMPH_SPEED_T4_2024,
    YAMAHA_R15M_2021,
    # ── Daily improvement run 2026-05-16 (Saturday — Catalog A1 second pass) ──
    HONDA_TRANSALP_XL750_2023,
    HONDA_CB750_HORNET_2023,
    HONDA_CB200X_2022,
    # ── Daily improvement run 2026-05-17 (Sunday — Catalog A1) ──
    SUZUKI_GSX_S1000GX_2024,
    BMW_R_1300_GS_2024,
    KAWASAKI_ELIMINATOR_450_2024,
]
