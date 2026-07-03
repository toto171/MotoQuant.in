"""
World-market / current-year expansion batch (July 2026 session).

Eight bikes closing world-catalog gaps: the new Chinese performance wave
(Kove 450RR I4 supersport, Benda LFC 700 I4 cruiser, QJ Motor SRK 800 RC,
CFMoto 1250TR-G, Zontes GK350), two current-year Japanese refreshes
(Kawasaki Ninja 1100SX, Honda CBR600RR EU/JDM reintroduction) and the
Philippines drag-scene staple Suzuki Raider R150 Fi.

Sourced from manufacturer spec sheets + EU/US press (MCN, Visordown,
Bennetts BikeSocial, RevZilla, Ultimate Motorcycling, Rider Magazine,
autoevolution spec archives). Chinese-brand numbers come from manufacturer
sheets cross-checked against EU distributor pages and EU press launches —
confidence per-field is flagged honestly in the comments; judgment-call
fields (cd, frontal_area_m2) are estimated against comparable bikes already
in the catalog with reasoning inline.

Kept as a separate module per the file-write truncation hygiene note
(CLAUDE.md). Wired into ALL_KNOWN_BIKES by the orchestrator — this module
only defines specs + benchmark rows, it does NOT self-register.

Exports:
    WORLD_EXPANSION_BIKES   — list[BikeSpec] (8 entries)
    ET_BENCHMARKS           — instrumented quarter-mile rows (see note)
    TOPSPEED_BENCHMARKS     — measured / factory-claim top-speed rows
"""

from __future__ import annotations

from .bikez import spec_from_dict

# ── Kove 450RR (2023-2026 — Chinese lightweight I4 supersport) ──────────────
# Kove Moto's (Chongqing Xianyou Technology) 443 cc inline-four supersport —
# the first Chinese I4 sportsbike sold in the US/EU, aimed squarely at the
# Kawasaki ZX-4RR. China launch mid-2023; EU homologated version launched for
# 2025 (MCN, Dec 2024). Steel trellis frame, fully-adjustable suspension,
# ram-air airbox (+~3 hp above 150 km/h per Kove).
# Power: EU launch spec 52 kW (69.7 hp) @ 13,500 rpm / 39 Nm @ 10,500 rpm
# (MCN Dec 2024); Kove's own China sheet lists 49 kW @ 13,250 / 38 Nm @
# 11,000 static (no ram-air) — we carry the EU homologation figure.
# Gearbox is a 6-speed; the internal cassette ratios and final-drive sprocket
# teeth are NOT published anywhere findable (no EN service manual circulates
# yet) — gear_ratios/sprockets deliberately OMITTED so the importer's Tier-2
# sport-category defaults apply rather than fabricated numbers.
# Sources:
#   - Kove Moto official 450RR spec page (kovemoto.com index.php?c=show&id=73):
#     443 cc I4 DOHC 16 v, 59.0 x 40.5 mm, 12.9:1, 165 kg curb, 220 km/h,
#     120/70R17 F / 160/60R17 R, wheelbase 1385 mm, 14 L tank
#   - MCN "Inline-four Kove 450RR sportsbike launched for 2025" (Dec 2024):
#     52 kW @ 13,500 rpm / 39 Nm @ 10,500 rpm EU spec, 165 kg, ram-air
#   - Bristol Motorcycles (UK distributor) + chinamotorworld.com spec sheets
#     corroborate mass/geometry/CR
KOVE_450RR_2023 = spec_from_dict(
    {
        "manufacturer": "Kove",
        "model_name": "450RR (2023-2026)",
        "model_code": "450RR_2023",
        "year_from": 2023,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 443,  # 443 cc I4 — bore/stroke-consistent
        # (59.0^2 x pi/4 x 40.5 x 4 = 443 cc)
        "bore_mm": 59.0,
        "stroke_mm": 40.5,
        "compression_ratio": 12.9,  # 12.9:1 — Kove spec sheet
        "cylinders": 4,
        "peak_power_hp": 69.7,  # 52 kW @ 13,500 rpm — EU homologation
        # per MCN Dec 2024 (China static sheet
        # says 49 kW @ 13,250; ram-air +3 hp)
        "peak_power_rpm": 13500,
        "peak_torque_nm": 39.0,  # 39 Nm @ 10,500 rpm — MCN EU spec
        "peak_torque_rpm": 10500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 16-valve
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.75, 2.0, 1.667, 1.444, 1.304, 1.208],
        "primary_ratio": 1.9,
        # gear_ratios + sprockets OMITTED — no service-manual cassette or OEM
        # tooth counts published for the 450RR as of Jul 2026 (the 13/49 pair
        # floating around is the single-cylinder 450 RALLY, a different bike).
        # Importer Tier-2 sport defaults apply; revisit when an EN manual ships.
        "dry_mass_kg": 154.0,  # 165 kg curb (Kove spec, all fluids
        # + 14 L fuel) − 10.4 kg fuel − ~0.6 kg
        # misc ≈ 154 kg dry
        "wet_mass_kg": 165.0,
        "wheelbase_mm": 1385.0,  # Kove spec sheet
        "fuel_capacity_l": 14.0,
        "front_tire_size": "120/70R17",
        "rear_tire_size": "160/60R17",
        "cd": 0.63,  # ESTIMATE: full-fairing lightweight
        # supersport; ref ZX-4RR @ 0.64 —
        # 450RR is slightly narrower/lower
        "frontal_area_m2": 0.41,  # ESTIMATE: ref ZX-4RR @ 0.40; the
        # Kove's taller screen adds a touch
    },
    source_name="spec_sheet",
)


# ── Benda LFC 700 (2022-2026 — the world's first inline-four cruiser) ───────
# Zhejiang Benda's power cruiser built around a 676 cc DOHC 16 v inline-four
# in a cast-aluminium frame (engine as stressed member) with the widest OE
# rear tyre on any production bike (310/35R18). China launch 2022; EU launch
# 2024/25 (MCN/Visordown tests); US launch 2025/26 via Keeway America.
# Genuinely drag-relevant novelty: long 1720 mm wheelbase + fat rear contact
# patch is a launch-friendly geometry, but 287 kg kerb blunts it.
# Power: EU/US homologation 84 hp @ 10,300 rpm / 60 Nm @ 8,600 rpm (Keeway
# America + MCN + autoevolution agree; Visordown's Euro5+ tester made 86 hp;
# China-market "High-Power" variant claims 92.5 hp @ 11,000 — NOT used here).
# Gearbox 6-speed, O-ring chain final drive; internal ratios and sprocket
# teeth unpublished — OMITTED (Tier-2 cruiser defaults apply).
# Sources:
#   - Keeway America LFC 700 product page (keewayamerica.com/products/lfc-700)
#   - autoevolution "2025 Benda LFC 700 Specs": 676 cc, 67.0 x 48.0 mm,
#     84 hp @ 10,300 / 60 Nm @ 8,600, 633 lb (287 kg) curb, 67.7 in
#     (1720 mm) wheelbase, 130/60R19 F / 310/35R18 R
#   - MCN "Benda LFC 700 review" (2025): "this side of the king-sized BMW
#     R18" wheelbase quote, 84.4 bhp, chain drive, slipper clutch
#   - Visordown "Benda LFC 700 (2025) review": MEASURED vmax 113 mph
#     (182 km/h), 0-62 mph 6.08 s, kerb 287 kg
#   - Ultimate Motorcycling "2026 Benda LFC700 First Look" (Nov 2025):
#     Brembo brakes, KYB suspension, cast-aluminium frame
BENDA_LFC_700_2022 = spec_from_dict(
    {
        "manufacturer": "Benda",
        "model_name": "LFC 700 (2022-2026)",
        "model_code": "LFC700_2022",
        "year_from": 2022,
        "year_to": 2026,
        "category": "cruiser",
        "displacement_cc": 676,  # 676 cc I4 (Benda BD700 engine) —
        # 67.0^2 x pi/4 x 48.0 x 4 = 677 cc ✓
        "bore_mm": 67.0,
        "stroke_mm": 48.0,
        "compression_ratio": 11.4,  # autoevolution spec sheet (sources
        # range 11.4-11.6 across variants)
        "cylinders": 4,
        "peak_power_hp": 84.0,  # 84 hp @ 10,300 rpm — EU/US spec
        # (Keeway America + MCN + autoevolution;
        # China High-Power variant 92.5 hp not used)
        "peak_power_rpm": 10300,
        "peak_torque_nm": 60.0,  # 60 Nm @ 8,600 rpm
        "peak_torque_rpm": 8600,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 16-valve
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.2, 1.6, 1.222, 1.0, 0.833, 0.722],
        "primary_ratio": 1.92,
        # gear_ratios + sprockets OMITTED — unpublished (no EN service manual);
        # Visordown notes "the gearing is too short" but gives no numbers.
        # O-ring chain final drive confirmed (MCN 2025). Tier-2 cruiser
        # defaults apply.
        "dry_mass_kg": 275.0,  # 287 kg kerb (Visordown/autoevolution)
        # − ~11 kg fuel (≈15 L, tank size not
        # published) − ~1 kg misc ≈ 275 kg dry
        "wet_mass_kg": 287.0,
        "wheelbase_mm": 1720.0,  # 67.7 in — autoevolution; longest in
        # class ("this side of the R18" — MCN)
        "front_tire_size": "130/60R19",
        "rear_tire_size": "310/35R18",  # widest OE rear tyre on any
        # production bike
        "cd": 0.80,  # ESTIMATE: long-low feet-forward
        # cruiser, no fairing; ref Indian Sport
        # Chief @ 0.78 (has quarter-fairing) —
        # naked LFC slightly worse
        "frontal_area_m2": 0.58,  # ESTIMATE: rider sits low IN the bike
        # (690 mm class seat) — smaller than the
        # Sport Chief's 0.62 upright pose
    },
    source_name="spec_sheet",
)


# ── QJ Motor SRK 800 RC (2023-2026 — Chinese I4 middleweight supersport) ────
# Qianjiang's fully-faired supersport on the 778 cc DOHC 16 v inline-four
# (same platform as the SRK 800 naked and the track-focused SRK 800 RR).
# Debuted late 2023, EU/UK deliveries 2024-25. The RC is the road-biased
# faired variant — 123 hp, Pirelli Angel GT rubber, conventional bars.
# Gearbox 6-speed; internal ratios and sprocket teeth unpublished — OMITTED
# (Tier-2 sport defaults apply). Compression ratio unpublished — OMITTED.
# Sources:
#   - autoevolution "2025 QJMotor SRK 800 RC Specs" (page covers 2023-on):
#     778 cc I4, 67.0 x 55.2 mm (= 778 cc ✓), 123 hp @ 12,000 rpm /
#     78 Nm @ 10,000 rpm, 445 lb (202 kg) curb, 55.5 in (1410 mm) wheelbase,
#     120/70ZR17 F / 180/55ZR17 R (Pirelli Angel GT)
#   - qjmotor.co.uk SRK 800 / SRK 800 RR platform pages (UK importer MotoGB)
#     corroborate the 778 cc I4 output figures
#   - Bennetts BikeSocial "QJMotor SRK800RR (2025) Technical Review" for
#     platform background (RR sibling: 205 kg curb)
QJMOTOR_SRK_800_RC_2023 = spec_from_dict(
    {
        "manufacturer": "QJ Motor",
        "model_name": "SRK 800 RC (2023-2026)",
        "model_code": "SRK800RC_2023",
        "year_from": 2023,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 778,  # 67.0^2 x pi/4 x 55.2 x 4 = 778 cc ✓
        "bore_mm": 67.0,
        "stroke_mm": 55.2,
        # compression_ratio OMITTED — not published for the RC
        "cylinders": 4,
        "peak_power_hp": 123.0,  # 123 hp @ 12,000 rpm — autoevolution
        # (UK importer lists ~125 hp for the
        # RR sibling — same platform)
        "peak_power_rpm": 12000,
        "peak_torque_nm": 78.0,  # 78 Nm @ 10,000 rpm
        "peak_torque_rpm": 10000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.75, 2.0, 1.667, 1.444, 1.304, 1.208],
        "primary_ratio": 1.9,
        # gear_ratios + sprockets OMITTED — unpublished; Tier-2 sport defaults.
        "dry_mass_kg": 189.0,  # 202 kg curb (autoevolution) − ~12 kg
        # fuel (tank size unpublished, ~16 L
        # class-typical) − ~1 kg ≈ 189 kg dry
        "wet_mass_kg": 202.0,
        "wheelbase_mm": 1410.0,  # 55.5 in — autoevolution
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.62,  # ESTIMATE: full-fairing middleweight
        # supersport, road-spec screen; between
        # CBR600RR-2013 (0.61) and ZX-4RR (0.64)
        "frontal_area_m2": 0.46,  # ESTIMATE: physically larger than a
        # 600 (ref CBR600RR-2013 @ 0.38,
        # Ninja 1000SX @ 0.53); wide fairing
    },
    source_name="spec_sheet",
)


# ── CFMoto 1250TR-G (2021-2026 — flagship KTM-derived V2 grand tourer) ──────
# CFMoto's flagship grand tourer around the 1279 cc 75° V-twin co-developed
# with KTM (LC8 architecture from the CFMoto-KTM joint venture; CFMoto builds
# LC8 engines in Hangzhou). Biggest, most powerful production bike from a
# Chinese brand at launch (2021, China; SE-Asia/export markets 2022+).
# Semi-active electronic suspension, Brembo brakes, 22.7 L tank.
# Gearbox 6-speed, chain final drive; internal ratios / sprocket teeth are
# not published in any EN source — OMITTED (Tier-2 touring defaults apply).
# Sources:
#   - CFMoto global product page (cfmoto.com/global/motorcycles/tr-g/1250tr-g)
#   - Bennetts BikeSocial "Official: CFMoto launches KTM-powered 1250 tourer"
#     (Sep 2020): 1279 cc V-twin, 140 hp / 120 Nm, KTM-derived LC8
#   - bikereview.com.au "New Model: CFMOTO 1250TR-G Grand Tourer": 108.0 x
#     69.8 mm (= 1279 cc ✓), 12.5:1, 105 kW (140 hp) @ 8,500 rpm /
#     120 Nm @ 7,000 rpm, 6-speed, slipper clutch, chain drive
#   - autoevolution "2024 CFMOTO 1250TR-G Specs": 300 kg curb, 1482 mm
#     wheelbase, 120/70ZR17 F / 190/55ZR17 R, 22.7 L, seat 820 mm
#   - CFMoto Malaysia launch PR (cfmotomalaysia.com.my) corroborates output
CFMOTO_1250TR_G_2021 = spec_from_dict(
    {
        "manufacturer": "CFMoto",
        "model_name": "1250TR-G (2021-2026)",
        "model_code": "1250TRG_2021",
        "year_from": 2021,
        "year_to": 2026,
        "category": "touring",
        "displacement_cc": 1279,  # 108.0^2 x pi/4 x 69.8 x 2 = 1279 cc ✓
        # (KTM LC8-derived V2, CFMoto heads/map)
        "bore_mm": 108.0,
        "stroke_mm": 69.8,
        "compression_ratio": 12.5,  # bikereview.com.au spec table
        "cylinders": 2,  # 75° V-twin (LC8 architecture)
        "peak_power_hp": 140.0,  # 105 kW @ 8,500 rpm — CFMoto spec
        "peak_power_rpm": 8500,
        "peak_torque_nm": 120.0,  # 120 Nm @ 7,000 rpm — CFMoto spec
        "peak_torque_rpm": 7000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 8-valve (LC8)
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.6, 1.947, 1.619, 1.4, 1.25, 1.148],
        "primary_ratio": 1.7,
        # gear_ratios + sprockets OMITTED — unpublished for the TR-G's
        # CFMoto-built box (do NOT assume KTM 1290 GT internals; only the
        # engine architecture is shared). Tier-2 touring defaults apply.
        "dry_mass_kg": 282.0,  # 300 kg curb (autoevolution) − 16.8 kg
        # fuel (22.7 L x 0.74) − ~1 kg ≈ 282 dry
        "wet_mass_kg": 300.0,
        "wheelbase_mm": 1482.0,  # autoevolution + motoplanete agree
        "seat_height_mm": 820.0,
        "fuel_capacity_l": 22.7,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.72,  # ESTIMATE: full touring fairing +
        # tall electric screen shields rider
        # (better than naked 0.80 class);
        # ref Ninja 1000SX half-fairing @ 0.65 —
        # the TR-G's bulk + barn-door screen
        # costs more drag
        "frontal_area_m2": 0.62,  # ESTIMATE: big GT with panniers-ready
        # width; ref Tenere 700 Rally @ 0.62,
        # Sport Chief @ 0.62
    },
    source_name="spec_sheet",
)


# ── Zontes GK350 (2022-2026 — neo-retro café single) ────────────────────────
# Guangdong Tayo's (Zontes) neo-retro "sport café" naked on their 348 cc
# liquid-cooled DOHC 4 v single (ZT350 engine family shared with 350R/350T/
# 350D). Sold in EU/UK ("ZT350-GK") and India (GK350). Distinctive full-LED
# retro-square styling, KYB suspension, 17 L tank.
# Bore/stroke NOT published in any findable source (Zontes UK sheet omits
# it) — OMITTED; validator consistency check simply skips.
# Gearbox 6-speed w/ slipper clutch; ratios/sprockets unpublished — OMITTED.
# Sources:
#   - zontes.co.uk ZT350-GK product page: 348 cc single, 28.5 kW, 6-speed,
#     slipper clutch, 17 L
#   - BikeWale / ZigWheels India spec tables (GK350): 38.2 bhp @ 9,500 rpm /
#     32.8 Nm @ 7,500 rpm, 188 kg kerb, 1380 mm wheelbase, 120/70-17 F /
#     160/60-17 R, CR 12.3:1
#   - Cycle World "Zontes ZT350 Details Revealed" for platform background
ZONTES_GK350_2022 = spec_from_dict(
    {
        "manufacturer": "Zontes",
        "model_name": "GK350 (2022-2026)",
        "model_code": "ZT350GK_2022",
        "year_from": 2022,
        "year_to": 2026,
        "category": "naked",  # neo-retro café — upright, unfaired
        "displacement_cc": 348,
        # bore/stroke OMITTED — not published (Zontes does not release them)
        "compression_ratio": 12.3,  # India spec tables
        "cylinders": 1,
        "peak_power_hp": 38.2,  # 38.2 bhp (28.5 kW) @ 9,500 rpm
        "peak_power_rpm": 9500,
        "peak_torque_nm": 32.8,  # 32.8 Nm @ 7,500 rpm
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 4-valve single (ZT350 family)
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.6, 1.882, 1.562, 1.333, 1.192, 1.095],
        "primary_ratio": 1.85,
        # gear_ratios + sprockets OMITTED — unpublished; Tier-2 naked defaults.
        "dry_mass_kg": 174.0,  # 188 kg kerb − 12.6 kg fuel (17 L x
        # 0.74) − ~1 kg ≈ 174 kg dry
        "wet_mass_kg": 188.0,
        "wheelbase_mm": 1380.0,
        "fuel_capacity_l": 17.0,
        "front_tire_size": "120/70R17",
        "rear_tire_size": "160/60R17",
        "cd": 0.76,  # ESTIMATE: upright naked with tiny
        # flyscreen; naked category band
        # 0.72-0.80 (ref SRK 400 naked @ 0.80,
        # Ninja 1000SX faired @ 0.65)
        "frontal_area_m2": 0.50,  # ESTIMATE: mid-size naked, wide bars
        # (ref SRK 400 @ 0.50)
    },
    source_name="spec_sheet",
)


# ── Kawasaki Ninja 1100SX (2025-2026 — stroked Ninja 1000SX successor) ──────
# The 2025 replacement for the Ninja 1000SX already in the catalog (that
# entry's year band 2020-2026 covers the run-out; this is the distinct new
# model). Engine stroked 56.0 → 59.0 mm for 1,099 cc; longer primary
# reduction plus taller 5th/6th internal ratios (gears 1-4 carried over);
# final drive one tooth larger at the rear (F15/R42 vs the 1000SX's F15/R41
# — RevZilla/Kawasaki press). Output 100.5 kW (134 hp) @ 9,000 rpm /
# 113 Nm @ 7,600 rpm. Bodywork/chassis carried over (wheelbase 1440 mm).
# gear_ratios OMITTED: Kawasaki publishes only 1st (2.600) and 6th (1.069)
# in press material — the new 5th is not verifiable anywhere findable, and
# fabricating one gear is worse than deferring the whole cassette to the
# Tier-2 lookup. Revisit when the ZXT02 service manual circulates.
# Sources:
#   - Kawasaki EU Ninja 1100SX EICMA/product page (kawasaki.eu): 1,099 cc,
#     77.0 x 59.0 mm, 11.8:1, 6-speed, curb 235 kg, 1440 mm wheelbase
#   - Ultimate Motorcycling "2025 Kawasaki Ninja 1100SX ABS First Look"
#     (Dec 2024): 134 hp @ 9,000 rpm / 83.2 lb-ft (112.8 Nm) @ 7,600 rpm,
#     11.8:1, taller 5th+6th
#   - Bennetts BikeSocial "Ninja 1100SX (2025) Review": ratios span 2.600
#     (1st) to 1.069 (6th); 120/70R17 F / 190/50R17 R
#   - RevZilla "2025 Ninja 1100SX first look": longer primary ratio, taller
#     5th/6th, final drive shorter via one-tooth-larger rear sprocket
KAWASAKI_NINJA_1100SX_2025 = spec_from_dict(
    {
        "manufacturer": "Kawasaki",
        "model_name": "Ninja 1100SX (2025-2026)",
        "model_code": "NINJA1100SX_2025",
        "year_from": 2025,
        "year_to": 2026,
        "category": "sport",  # half-faired sport-tourer (same
        # classification as the 1000SX entry)
        "displacement_cc": 1099,  # 77.0^2 x pi/4 x 59.0 x 4 = 1099 cc ✓
        "bore_mm": 77.0,
        "stroke_mm": 59.0,  # stroked from the 1000SX's 56.0 mm
        "compression_ratio": 11.8,
        "cylinders": 4,
        "peak_power_hp": 134.0,  # 100.5 kW @ 9,000 rpm — Kawasaki EU
        # (down 1,000 rpm vs 1000SX's peak;
        # lower rev limit, more midrange)
        "peak_power_rpm": 9000,
        "peak_torque_nm": 113.0,  # 112.8 Nm @ 7,600 rpm
        "peak_torque_rpm": 7600,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.6, 2.0, 1.667, 1.444, 1.296, 1.185],
        "primary_ratio": 1.6,
        # gear_ratios OMITTED — only 1st 2.600 / 6th 1.069 published; new 5th
        # unverifiable (see block comment). Sprockets ARE verified:
        "front_sprocket": 15,
        "rear_sprocket": 42,  # one tooth up on the 1000SX's F15/R41
        # per RevZilla/Kawasaki press
        "chain_pitch": "520",  # carried over from Ninja 1000SX
        "dry_mass_kg": 221.0,  # 235 kg curb − 14.1 kg fuel (19 L x
        # 0.74) ≈ 221 kg dry (same math as the
        # catalog's Ninja 1000SX entry)
        "wet_mass_kg": 235.0,
        "wheelbase_mm": 1440.0,  # unchanged from 1000SX
        "seat_height_mm": 835.0,
        "fuel_capacity_l": 19.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/50ZR17",
        "cd": 0.65,  # same half-fairing bodywork family as
        # the catalog's Ninja 1000SX (0.65) —
        # carried over per Kawasaki (only the
        # screen gained a taller position)
        "frontal_area_m2": 0.53,  # carried-over bodywork; ref Ninja
        # 1000SX @ 0.53, panniers not fitted
    },
    source_name="spec_sheet",
)


# ── Honda CBR600RR (2024-2026 — EU/world reintroduction, 8BL-PC40) ──────────
# Honda's 2024 European/world-market reintroduction of the CBR600RR —
# distinct from the catalog's "CBR 600RR" (2007-2012) and "CBR 600RR
# (2013-2020)" entries. Same PC40 599 cc I4 architecture (67.0 x 42.5 mm)
# revised for Euro5+ with RBW throttle, winglets, IMU cornering ABS, 9-level
# TC and standard quickshifter. JDM code 8BL-PC40 (since Jan 2024).
# EU homologation 89 kW (119 hp) @ 14,250 rpm / 63 Nm @ 11,500 rpm.
# Gearbox: PC40 6-speed cassette carried over unchanged since 2007 —
# ratios from the Honda PC40 service manual; final drive 16/43 (the taller
# 2013-2020 catalog entry ran 15/42; the 2020+ JDM/EU refresh standardised
# F16/R43, matching the Tier-1 lookup's 2003-2020 window), #525 chain.
# Sources:
#   - Honda News (hondanews.com) "2024 Honda CBR600RR Specifications"
#   - MCN "2024 Honda CBR600RR review": 119 bhp, 193 kg kerb, wheelbase
#     shortened 5 mm to 1,370 mm, quickshifter standard
#   - motorbikecatalog 2024 8BL-PC40 (JDM) spec page: 89 kW @ 14,250,
#     63 Nm @ 11,500, 12.2:1, 18 L tank, 120/70ZR17 / 180/55ZR17
#   - Honda PC40 service manual (61MFJ00): gear ratios 2.750 / 2.000 /
#     1.667 / 1.444 / 1.304 / 1.208, primary 2.111 (76/36)
HONDA_CBR600RR_2024 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "CBR600RR (2024-2026)",
        "model_code": "8BL-PC40",
        "year_from": 2024,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 599,  # 67.0^2 x pi/4 x 42.5 x 4 = 599 cc ✓
        "bore_mm": 67.0,
        "stroke_mm": 42.5,
        "compression_ratio": 12.2,
        "cylinders": 4,
        "peak_power_hp": 119.0,  # 89 kW @ 14,250 rpm — EU/JDM spec
        # (US 2024 carb-map makes slightly less)
        "peak_power_rpm": 14250,
        "peak_torque_nm": 63.0,  # 63 Nm @ 11,500 rpm
        "peak_torque_rpm": 11500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # PC40 cassette unchanged since 2007 — Honda PC40 service manual
        "gear_ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "primary_ratio": 2.111,  # 76/36 — PC40 service manual
        "front_sprocket": 16,
        "rear_sprocket": 43,  # F16/R43 — 2020+ JDM/EU final drive
        "chain_pitch": "525",
        "dry_mass_kg": 179.0,  # 193 kg kerb (MCN/Honda EU, incl. 18 L
        # fuel) − 13.3 kg fuel − ~0.7 kg ≈ 179
        "wet_mass_kg": 193.0,
        "wheelbase_mm": 1370.0,  # shortened 5 mm vs prior gen — MCN
        "seat_height_mm": 820.0,
        "fuel_capacity_l": 18.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.60,  # ESTIMATE: 2024 aero package adds
        # winglets + smoother fairing vs the
        # 2013 gen (catalog entry @ 0.61)
        "frontal_area_m2": 0.40,  # ESTIMATE: 600 supersport, slightly
        # wider than the 2013 gen's 0.38 due
        # to winglets
    },
    source_name="spec_sheet",
)


# ── Suzuki Raider R150 Fi (2017-2026 — Philippines drag-scene staple) ───────
# Suzuki Philippines' fuel-injected evolution of the Raider R150 underbone
# (FU150 platform — the same DOHC 4 v 147.3 cc single as the Indonesian
# Satria F150 Fi). THE entry-level drag bike of the Philippine scene ("king
# of underbones"); carb version sold 2004-2018, Fi from 2017. 428 chain
# pitch per the SE-Asia underbone pattern (ref Honda RS150R / Yamaha Y15ZR
# entries). 6-speed; internal cassette ratios not published in the owner-
# facing spec sheet — OMITTED (Tier-2 defaults); sprockets ARE verified.
# Sources:
#   - Suzuki Philippines official spec sheet (mc.suzuki.com.ph
#     RAIDER-150-FI.pdf): 147.3 cc DOHC 4 v single, 62.0 x 48.8 mm, 11.5:1,
#     13.6 kW (18.2 hp) @ 10,000 rpm / 13.8 Nm @ 8,500 rpm, 6-speed,
#     curb 109 kg, wheelbase 1,280 mm, 70/90-17 F / 80/90-17 R, 4 L tank,
#     seat 765 mm
#   - Webike Japan Raider R150 parts/spec page + Suzuki PH parts catalog
#     (FU150SC): OEM sprockets F14/R43, 428 chain
#   - ZigWheels PH spec table corroborates output/mass
SUZUKI_RAIDER_R150_FI_2017 = spec_from_dict(
    {
        "manufacturer": "Suzuki",
        "model_name": "Raider R150 Fi (2017-2026)",
        "model_code": "FU150_FI",
        "year_from": 2017,
        "year_to": 2026,
        "category": "sport",  # underbone sport (hyperunderbone) —
        # same classification as RS150R/Y15ZR
        "displacement_cc": 147.3,
        "bore_mm": 62.0,
        "stroke_mm": 48.8,
        "compression_ratio": 11.5,
        "cylinders": 1,
        "peak_power_hp": 18.2,  # 13.6 kW @ 10,000 rpm — Suzuki PH spec
        "peak_power_rpm": 10000,
        "peak_torque_nm": 13.8,  # 13.8 Nm @ 8,500 rpm
        "peak_torque_rpm": 8500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.75, 2.0, 1.667, 1.444, 1.304, 1.208],
        "primary_ratio": 1.9,
        # gear_ratios OMITTED — Suzuki PH publishes no cassette table for the
        # Fi (Tier-2 defaults apply); sprockets are OEM-verified:
        "front_sprocket": 14,
        "rear_sprocket": 43,  # F14/R43 — Suzuki PH parts catalog
        "chain_pitch": "428",  # SE-Asia underbone standard
        "dry_mass_kg": 105.0,  # 109 kg curb − 3.0 kg fuel (4 L x
        # 0.74) − ~1 kg ≈ 105 kg dry
        "wet_mass_kg": 109.0,
        "wheelbase_mm": 1280.0,
        "seat_height_mm": 765.0,
        "fuel_capacity_l": 4.0,
        "front_tire_size": "70/90-17",  # PH bias-ply notation (validator
        # emits a cosmetic format warning,
        # same as the RS150R entry)
        "rear_tire_size": "80/90-17",
        "cd": 0.71,  # ESTIMATE: underbone with small
        # cowl, very slim (675 mm wide); ref
        # RS150R/Y15ZR @ 0.72 — Raider is the
        # lowest/slimmest of the class
        "frontal_area_m2": 0.42,  # ESTIMATE: ref RS150R @ 0.44;
        # Raider is narrower and lower
    },
    source_name="spec_sheet",
)


# Master list — the orchestrator wires this into ALL_KNOWN_BIKES
WORLD_EXPANSION_BIKES = [
    KOVE_450RR_2023,
    BENDA_LFC_700_2022,
    QJMOTOR_SRK_800_RC_2023,
    CFMOTO_1250TR_G_2021,
    ZONTES_GK350_2022,
    KAWASAKI_NINJA_1100SX_2025,
    HONDA_CBR600RR_2024,
    SUZUKI_RAIDER_R150_FI_2017,
]


# ── Benchmarks ───────────────────────────────────────────────────────────────
# ET_BENCHMARKS: (manufacturer_substr, model_substr, year_hint, target_et_s,
#                 trap_kmh, source_label)
# HONESTY NOTE (Jul 2026): NO instrumented quarter-mile test exists yet for
# any of these exact model-years in the searched archives (Cycle World / MCN /
# Visordown / Fast Bikes / Motorcyclist / Bennetts). Near-misses deliberately
# excluded per the "do NOT fabricate or derive" policy:
#   - Benda LFC 700: Visordown 2025 MEASURED 0-62 mph 6.08 s + vmax 113 mph —
#     but no standing-quarter figure (0-60 is not an ET).
#   - CBR600RR: motorbikecatalog's 11.1 s figure for the 2024 8BL-PC40 is
#     that site's own simulation (DERIVED-class), and MotoStatz's 10.92 s @
#     131 mph CBR600RR row is generation-ambiguous — both excluded.
#   - Ninja 1100SX: only the 1000SX (different model, already in catalog)
#     has published instrumented numbers.
ET_BENCHMARKS: list[tuple] = []

# TOPSPEED_BENCHMARKS: (manufacturer_substr, model_substr, year_hint,
#                       target_kmh, source)
TOPSPEED_BENCHMARKS: list[tuple] = [
    # Kove publishes 220 km/h for the 450RR (spec sheet; repeated by MCN in
    # the Dec 2024 EU launch story) — manufacturer claim, not a Vbox run.
    ("Kove", "450RR", 2023, 220.0, "factory claim (Kove spec sheet / MCN 2024)"),
    # Visordown's 2025 road test MEASURED 113 mph (182 km/h) against Benda's
    # own 100 mph claim — we pin the measured figure.
    ("Benda", "LFC 700", 2022, 182.0, "Visordown 2025 (measured, 113 mph)"),
]
