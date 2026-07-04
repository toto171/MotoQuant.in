"""
China-brand performance-wave expansion (July 2026 — roadmap GAP-1).

Six current-generation Chinese-brand bikes that fill genuine catalog gaps and
are DISTINCT from the Chinese bikes already present (Kove 450RR I4 sport, QJ
SRK 800 RC I4 sport, Zontes GK350 single, Benda LFC 700 I4 cruiser, CFMoto
800NK naked — all in known_bikes_2026_world.py / known_bikes_extended.py):

    Kove 800X            — 799 cc parallel-twin ADV
    Kove 450 Rally       — 449 cc single dual-sport / rally
    QJ Motor SRK 921     — 921 cc inline-4 litre naked
    Zontes 703F          — 699 cc inline-triple ADV
    Benda Chinchilla 500 — 475.6 cc V-twin cruiser (BELT final drive)
    CFMoto 800MT Sport   — 799 cc parallel-twin ADV (KTM LC8c-derived)

Every spec here uses only web-verified figures supplied for this pass; fields
not verified (bore/stroke, compression, wheelbase, internal gear cassette
where no service manual circulates) are OMITTED so the importer's Tier-2
category defaults apply rather than fabricated numbers. Judgment-call aero
fields (cd, frontal_area_m2) are ESTIMATED against comparable catalog bikes
with the reasoning inline, matching the known_bikes_2026_world.py convention.

Mass convention (mirrors known_bikes_2026_world.py + importer priority at
importer.py:724 — the sim consumes ``dry_mass_kg`` and adds a 75 kg rider
separately): store ``wet_mass_kg`` = the manufacturer kerb/wet figure and
``dry_mass_kg`` = kerb − fuel − misc. Where the source figure is a DRY weight
it is stored directly as ``dry_mass_kg`` with ``wet_mass_kg`` = dry + fuel.

Gear cassettes are made EXPLICIT (Tier-2 category defaults surfaced as real
values) per the tests/test_scraper.py::test_all_known_bikes_have_gear_ratios
contract — every spec must ship a >=4-gear cassette; behaviour is identical to
the implicit importer fallback and each cassette is replaceable when a service
manual surfaces.

Kept as a separate module per the file-write truncation hygiene note
(CLAUDE.md). Wired into ALL_KNOWN_BIKES by known_bikes.py — this module only
defines specs, it does NOT self-register. No instrumented quarter-mile tests
exist for any of these exact model-years in the searched archives (Cycle
World / MCN / Visordown / Fast Bikes / MotoStatz), so the benchmark lists are
honestly empty.

Exports:
    CHINA_EXPANSION_BIKES  — list[BikeSpec] (6 entries)
    ET_BENCHMARKS          — [] (no instrumented quarter-mile found — honest)
    TOPSPEED_BENCHMARKS    — [] (deferred; factory claims not emitted here)
"""

from __future__ import annotations

from .bikez import spec_from_dict

# ── Kove 800X (2023-2026 — 799 cc parallel-twin adventure) ──────────────────
# Kove Moto's middleweight ADV on their 799 cc DOHC parallel-twin. Notably
# light for the class. Sold in EU/UK + India. 21"/18" spoked wheels, off-road
# biased ergonomics.
# Verified figures (this pass): 799 cc I2, 94 hp @ 9000 rpm, 80 Nm @ 7500 rpm,
# ~185 kg wet (Kove kerb), chain drive, 90/90-21 F / 140/80-18 R, ADV.
# bore/stroke, compression, wheelbase, sprocket teeth and internal cassette
# NOT verified this pass — OMITTED (importer Tier-2 adventure defaults apply).
KOVE_800X_2023 = spec_from_dict(
    {
        "manufacturer": "Kove",
        "model_name": "800X (2023-2026)",
        "model_code": "800X_2023",
        "year_from": 2023,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 799,
        "cylinders": 2,  # parallel-twin (I2)
        "peak_power_hp": 94.0,  # 94 hp @ 9000 rpm
        "peak_power_rpm": 9000,
        "peak_torque_nm": 80.0,  # 80 Nm @ 7500 rpm
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished — Tier-2 adventure cassette made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract.
        "gear_ratios": [2.6, 1.947, 1.619, 1.4, 1.25, 1.148],
        "primary_ratio": 1.9,
        # sprocket teeth OMITTED — not verified; Tier-2 adventure final drive.
        "final_drive": "chain",
        "dry_mass_kg": 174.0,  # ~185 kg wet (Kove kerb) − ~10.4 kg fuel
        # (~14 L x 0.74) − ~0.6 kg misc ≈ 174 kg dry
        "wet_mass_kg": 185.0,  # manufacturer kerb (verified this pass)
        "front_tire_size": "90/90-21",
        "rear_tire_size": "140/80-18",
        "cd": 0.56,  # ESTIMATE: tall ADV with small screen + 21" front,
        # upright/exposed rider; adventure band (ref
        # Tenere-class ADV ~0.55-0.58)
        "frontal_area_m2": 0.60,  # ESTIMATE: tall/wide ADV, wide bars + big
        # tank (ref Tenere 700 Rally @ 0.62)
    },
    source_name="spec_sheet",
)


# ── Kove 450 Rally (2023-2026 — 449 cc single rally/dual-sport) ─────────────
# The Dakar-replica single that put Kove on the map. 449 cc DOHC single, very
# tall rally ergonomics, 21"/18" spoked wheels, big fuel range.
# Verified figures (this pass): 449 cc single, 51 hp @ 9000 rpm, 39 Nm @
# 7000 rpm, 155 kg kerb, 520 chain with 13T front / 51T rear, 90/90-21 F /
# 140/80-18 R, adventure/dual-sport.
# bore/stroke, compression, wheelbase, internal cassette NOT verified —
# OMITTED. Sprockets ARE verified (13/51 → final drive 3.923).
KOVE_450_RALLY_2023 = spec_from_dict(
    {
        "manufacturer": "Kove",
        "model_name": "450 Rally (2023-2026)",
        "model_code": "450RALLY_2023",
        "year_from": 2023,
        "year_to": 2026,
        "category": "adventure",  # rally / dual-sport single
        "displacement_cc": 449,
        "cylinders": 1,  # single cylinder
        "peak_power_hp": 51.0,  # 51 hp @ 9000 rpm
        "peak_power_rpm": 9000,
        "peak_torque_nm": 39.0,  # 39 Nm @ 7000 rpm
        "peak_torque_rpm": 7000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished — Tier-2 cassette made EXPLICIT per the
        # test_all_known_bikes_have_gear_ratios contract.
        "gear_ratios": [2.75, 2.0, 1.667, 1.444, 1.304, 1.208],
        "primary_ratio": 2.0,
        "front_sprocket": 13,  # verified OEM sprockets 13/51 (520 chain)
        "rear_sprocket": 51,
        "chain_pitch": "520",
        "final_drive": "chain",
        "dry_mass_kg": 146.0,  # 155 kg kerb − ~8.5 kg fuel (rally tank
        # residual) − ~0.5 kg misc ≈ 146 kg dry
        "wet_mass_kg": 155.0,  # manufacturer kerb (verified this pass)
        "front_tire_size": "90/90-21",
        "rear_tire_size": "140/80-18",
        "cd": 0.60,  # ESTIMATE: very tall rally bodywork + knobby
        # stance is draggy but the bike is narrow —
        # high cd, moderate frontal
        "frontal_area_m2": 0.55,  # ESTIMATE: slim single, tall screen (below
        # the wide twin-ADVs' 0.60)
    },
    source_name="spec_sheet",
)


# ── QJ Motor SRK 921 (2025-2026 — 921 cc inline-4 litre naked) ──────────────
# Qianjiang's flagship naked on a new 921 cc DOHC inline-four (distinct from
# the 778 cc SRK 800 platform already in the catalog). Big, heavy, torque-rich
# litre naked aimed at the Z900 / Street Triple class.
# Verified figures (this pass): 921 cc I4, 127 hp @ 10000 rpm, 93 Nm @
# 8000 rpm, 217 kg dry, chain drive, 120/70ZR17 F / 190/55ZR17 R, naked.
# bore/stroke, compression, wheelbase, sprockets, internal cassette NOT
# verified — OMITTED (Tier-2 naked defaults apply).
QJMOTOR_SRK_921_2025 = spec_from_dict(
    {
        "manufacturer": "QJ Motor",
        "model_name": "SRK 921 (2025-2026)",
        "model_code": "SRK921_2025",
        "year_from": 2025,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 921,
        "cylinders": 4,  # inline-4
        "peak_power_hp": 127.0,  # 127 hp @ 10000 rpm
        "peak_power_rpm": 10000,
        "peak_torque_nm": 93.0,  # 93 Nm @ 8000 rpm
        "peak_torque_rpm": 8000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished — Tier-2 naked cassette made EXPLICIT
        # per the test_all_known_bikes_have_gear_ratios contract.
        "gear_ratios": [2.6, 1.882, 1.562, 1.333, 1.192, 1.095],
        "primary_ratio": 1.6,
        "final_drive": "chain",
        "dry_mass_kg": 217.0,  # 217 kg DRY (verified this pass) — stored
        # directly per the mass convention
        "wet_mass_kg": 231.0,  # dry + ~14 kg fuel (~18 L class-typical)
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.58,  # ESTIMATE: big litre naked, tiny flyscreen,
        # wide bars; naked band 0.55-0.62 (ref
        # SRK 400 naked @ 0.80 is smaller/boxier;
        # a litre naked with a fuller tank is slicker)
        "frontal_area_m2": 0.55,  # ESTIMATE: large litre naked, upright rider,
        # wide bars
    },
    source_name="spec_sheet",
)


# ── Zontes 703F (2024-2026 — 699 cc inline-triple adventure) ────────────────
# Zontes' first triple: a 699 cc DOHC inline-three in an adventure-tourer
# (703F faired ADV; 703RR is the sport sibling). Notable as one of very few
# Chinese-brand triples.
# Verified figures (this pass): 699 cc I3, 96 hp @ 10000 rpm, 76 Nm @
# 7500 rpm, 228 kg wet, 525 chain, 90/90-21 F / 150/70-18 R, adventure.
# bore/stroke, compression, wheelbase, sprockets, internal cassette NOT
# verified — OMITTED (Tier-2 adventure defaults apply).
ZONTES_703F_2024 = spec_from_dict(
    {
        "manufacturer": "Zontes",
        "model_name": "703F (2024-2026)",
        "model_code": "703F_2024",
        "year_from": 2024,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 699,
        "cylinders": 3,  # inline-triple (I3)
        "peak_power_hp": 96.0,  # 96 hp @ 10000 rpm
        "peak_power_rpm": 10000,
        "peak_torque_nm": 76.0,  # 76 Nm @ 7500 rpm
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished — Tier-2 adventure cassette made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract.
        "gear_ratios": [2.6, 1.947, 1.619, 1.4, 1.25, 1.148],
        "primary_ratio": 1.8,
        "chain_pitch": "525",  # verified 525 pitch (teeth not published)
        "final_drive": "chain",
        "dry_mass_kg": 214.0,  # 228 kg wet − ~13.3 kg fuel (~18 L x 0.74)
        # − ~0.7 kg misc ≈ 214 kg dry
        "wet_mass_kg": 228.0,  # manufacturer wet figure (verified this pass)
        "front_tire_size": "90/90-21",
        "rear_tire_size": "150/70-18",
        "cd": 0.55,  # ESTIMATE: faired adventure-tourer with a
        # touring screen; adventure band (ref
        # Kove 800X @ 0.56, a touch slicker with
        # its full fairing)
        "frontal_area_m2": 0.60,  # ESTIMATE: tall/wide ADV, 21" front, wide
        # bars (ref Tenere 700 Rally @ 0.62)
    },
    source_name="spec_sheet",
)


# ── Benda Chinchilla 500 (2024-2026 — 475.6 cc V-twin cruiser, BELT) ────────
# Zhejiang Benda's small bobber-style cruiser on a 475.6 cc V-twin with BELT
# final drive (unusual for a Chinese cruiser; matches the low-maintenance
# bobber brief). Low, feet-forward, fat 16" rubber.
# Verified figures (this pass): 475.6 cc V2, 47 hp @ 9000 rpm, 42 Nm @
# 7200 rpm, 215 kg kerb, BELT final drive, 150/80-16 F / 180/65-16 R, cruiser.
# bore/stroke, compression, wheelbase, belt pulley teeth, internal cassette
# NOT verified — OMITTED. BELT expressed via the front/rear_sprocket == 0
# sentinel (importer._build_drivetrain_from_spec:802) so the sim consumes the
# researched belt final-drive ratio (Tier-2 cruiser default 2.4) rather than a
# fabricated chain ratio. NOTE: the importer infers cylinder_config = I2 for a
# 2-cylinder Benda (no V-twin make token) — a cosmetic parts-fitment quirk,
# physics-neutral for the drag sim (cylinder COUNT = 2 is what drives inertia).
BENDA_CHINCHILLA_500_2024 = spec_from_dict(
    {
        "manufacturer": "Benda",
        "model_name": "Chinchilla 500 (2024-2026)",
        "model_code": "CHINCHILLA500_2024",
        "year_from": 2024,
        "year_to": 2026,
        "category": "cruiser",
        "displacement_cc": 475.6,
        "cylinders": 2,  # V-twin (V2) — importer infers I2 (cosmetic)
        "peak_power_hp": 47.0,  # 47 hp @ 9000 rpm
        "peak_power_rpm": 9000,
        "peak_torque_nm": 42.0,  # 42 Nm @ 7200 rpm
        "peak_torque_rpm": 7200,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished — small-cruiser Tier-2 cassette made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract. A
        # SHORT first gear (2.6) is used deliberately: small-displacement
        # cruisers (Rebel 500 class) run first-gear-overall ~11-13, not the
        # ~10 of the litre LFC 700 / Indian 101 Scout cruiser cassette — the
        # taller ratio bogged the 47 hp launch and slowed the sim ~0.6 s.
        "gear_ratios": [2.6, 1.85, 1.4, 1.15, 0.97, 0.85],
        "primary_ratio": 1.9,
        # BELT final drive: front/rear_sprocket == 0 is the documented
        # shaft/belt sentinel (importer routes to _shaft_belt_final_drive →
        # Tier-2 cruiser belt default 2.4). Pulley teeth not published.
        "front_sprocket": 0,
        "rear_sprocket": 0,
        "final_drive": "belt",
        "dry_mass_kg": 203.0,  # 215 kg kerb − ~11.5 kg fuel (~15.5 L x
        # 0.74) − ~0.5 kg misc ≈ 203 kg dry
        "wet_mass_kg": 215.0,  # manufacturer kerb (verified this pass)
        "front_tire_size": "150/80-16",
        "rear_tire_size": "180/65-16",
        "cd": 0.74,  # ESTIMATE: low bobber cruiser, feet-forward,
        # upright torso in clean air; cruiser band
        # (ref Iron 883 @ 0.80 — the Chinchilla is
        # lower/slimmer, a touch slicker)
        "frontal_area_m2": 0.55,  # ESTIMATE: physically small low cruiser
        # (ref Iron 883 @ 0.55)
    },
    source_name="spec_sheet",
)


# ── CFMoto 800MT Sport (2022-2026 — 799 cc parallel-twin ADV, LC8c) ─────────
# The road-biased "Sport" trim of CFMoto's 800MT adventure-tourer on the KTM
# LC8c-derived 799 cc parallel-twin (CFMoto builds LC8c engines in Hangzhou).
# DISTINCT from the CFMoto 800NK naked already in the catalog — same engine
# family, ADV chassis + full touring fairing. 19"/17" cast wheels (Sport trim;
# the "Touring" trim gets a 21" spoked front).
# Verified figures (this pass): 799 cc I2 (LC8c-derived), 94 hp @ 9000 rpm,
# 77 Nm @ 7500 rpm, 231 kg kerb, 520 chain with 15T front / 45T rear,
# 110/80 R19 F / 150/70 R17 R, adventure.
# bore/stroke, compression, wheelbase, internal cassette NOT verified —
# OMITTED. Sprockets ARE verified (15/45 → final drive 3.0).
CFMOTO_800MT_SPORT_2022 = spec_from_dict(
    {
        "manufacturer": "CFMoto",
        "model_name": "800MT Sport (2022-2026)",
        "model_code": "800MT_SPORT_2022",
        "year_from": 2022,
        "year_to": 2026,
        "category": "adventure",
        "displacement_cc": 799,
        "cylinders": 2,  # parallel-twin (I2, KTM LC8c architecture)
        "peak_power_hp": 94.0,  # 94 hp @ 9000 rpm
        "peak_power_rpm": 9000,
        "peak_torque_nm": 77.0,  # 77 Nm @ 7500 rpm
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished — Tier-2 adventure cassette made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract.
        # (Do NOT assume KTM 790 Adv internals — only the engine architecture
        # is shared; CFMoto builds its own box.)
        "gear_ratios": [2.6, 1.947, 1.619, 1.4, 1.25, 1.148],
        "primary_ratio": 1.9,
        "front_sprocket": 15,  # verified OEM sprockets 15/45 (520 chain)
        "rear_sprocket": 45,
        "chain_pitch": "520",
        "final_drive": "chain",
        "dry_mass_kg": 217.0,  # 231 kg kerb − ~13.3 kg fuel (~18 L x 0.74)
        # − ~0.7 kg misc ≈ 217 kg dry
        "wet_mass_kg": 231.0,  # manufacturer kerb (verified this pass)
        "front_tire_size": "110/80 R19",
        "rear_tire_size": "150/70 R17",
        "cd": 0.55,  # ESTIMATE: adventure-tourer with full touring
        # fairing + adjustable screen; adventure band
        # (ref Kove 800X @ 0.56, slicker with its
        # bigger fairing)
        "frontal_area_m2": 0.60,  # ESTIMATE: tall/wide ADV tourer, 19" front,
        # wide bars (ref Tenere 700 Rally @ 0.62)
    },
    source_name="spec_sheet",
)


# Master list — known_bikes.py wires this into ALL_KNOWN_BIKES.
CHINA_EXPANSION_BIKES = [
    KOVE_800X_2023,
    KOVE_450_RALLY_2023,
    QJMOTOR_SRK_921_2025,
    ZONTES_703F_2024,
    BENDA_CHINCHILLA_500_2024,
    CFMOTO_800MT_SPORT_2022,
]


# ── Benchmarks ───────────────────────────────────────────────────────────────
# No instrumented quarter-mile test (Cycle World / MCN / Visordown / Fast
# Bikes / MotoStatz Dragy) exists for any of these exact model-years in the
# searched archives — honest empty over fabrication. The two instrumented
# benchmark rows shipped this pass (BMW S 1000 RR ShiftCam, Kawasaki ZX-6R
# 636 2024-2025) target bikes ALREADY in the catalog and live directly in
# scripts/validation_sweep.py::BENCHMARKS.
ET_BENCHMARKS: list[tuple] = []
TOPSPEED_BENCHMARKS: list[tuple] = []
