"""
MotoQuant — US-Market Drag-Icon Expansion (July 2026)
=====================================================
12 curated US-market drag icons: Harley-Davidson Milwaukee-Eight Softails,
Evolution Sportsters, Indian PowerPlus / SpeedPlus / Thunderstroke cruisers,
the Buell XB12R, the EBR 1190RX, and the pre-Hayabusa king CBR1100XX.

Entry format follows the canonical template (INDIAN_SPORT_CHIEF_2023 in
known_bikes_extended.py): module-level VAR = spec_from_dict({...},
source_name="spec_sheet") with a source-cited comment block above each entry.

Belt-drive convention (per the Sport Chief template): front_sprocket /
rear_sprocket carry the REAL belt-pulley tooth counts so final_drive_ratio
is physically correct; chain_pitch is omitted (the importer's
_infer_chain_pitch returns None for Harley-Davidson / Buell; "Indian" make
falls through to displacement rules — a known cosmetic parts-fitment quirk
shared with the existing Sport Chief entry, NOT fixed here per file-ownership
rules).

Benchmark policy (module exports at the bottom):
  - ET_BENCHMARKS rows ONLY where a verified instrumented magazine test with
    BOTH ET and trap speed was found. Verified-ET-but-no-trap tests are
    documented in comments and deliberately NOT emitted (the cluster sweep
    calls float(tgt_trap), so a None trap would crash it).
  - TOPSPEED_BENCHMARKS allows factory / period-archive claims per the
    existing topspeed_sweep.py source conventions.
"""

from __future__ import annotations

from .bikez import spec_from_dict

# ── Harley-Davidson Breakout 117 (2023-2026 — FXBR drag-style Softail) ──────
# The long/low factory drag-custom of the Softail line, re-launched for 2023
# with the Milwaukee-Eight 117 (previously CVO-only). 240-section rear tire,
# 21" front, raked-out stance. Cluster: cruiser_1300p (1923 cc V2).
# Sources:
#   - H-D 2023 press/spec sheet (FXBR): ME-117 1,923 cc, bore 4.075 in
#     (103.5 mm) x stroke 4.5 in (114.3 mm), CR 10.2:1, 101 hp (75 kW)
#     @ 4,750 rpm (EU homologation figure; US sheet lists torque only),
#     167 Nm (123 lb-ft) @ 3,500 rpm, curb 683 lb, wheelbase 66.7 in,
#     tires 130/60B21 / 240/40R18 (Michelin Scorcher 11).
#   - Cycle World "2023 Harley-Davidson Breakout 117 Review" (2023):
#     confirms bore/stroke/CR, measured 94.2 rear-wheel hp @ 4,790 rpm /
#     118.0 lb-ft @ 3,250 rpm on the CW dyno (consistent with the ~101 hp
#     crank claim).
#   - H-D media-kit spec PDFs (breakout-114.pdf and my21 Softail family):
#     6-speed Cruise Drive, primary chain 34/46, final belt 32/66, overall
#     ratios 9.311 / 6.454 / 4.793 / 3.882 / 3.307 / 2.790 — internal
#     cassette derived by dividing out primary (1.353) x final (2.0625):
#     [3.337, 2.313, 1.718, 1.391, 1.185, 1.000]. Shared across the whole
#     M8 Softail family (Breakout / Fat Bob / Street Bob / Low Rider S).
HD_BREAKOUT_117_2023 = spec_from_dict(
    {
        "manufacturer": "Harley-Davidson",
        "model_name": "Breakout 117 (2023-2026)",
        "model_code": "FXBR_2023",
        "year_from": 2023,
        "year_to": 2026,
        "category": "cruiser",  # factory drag-custom Softail
        "displacement_cc": 1923,  # Milwaukee-Eight 117 (117 ci)
        "bore_mm": 103.5,  # 4.075 in — H-D spec
        "stroke_mm": 114.3,  # 4.5 in — shared M8 stroke
        "compression_ratio": 10.2,  # H-D spec (ME-117)
        "cylinders": 2,  # 45° V-twin, 4v/cyl pushrod
        "peak_power_hp": 101.0,  # 75 kW @ 4,750 — H-D EU spec
        "peak_power_rpm": 4750,
        "peak_torque_nm": 167.0,  # 123 lb-ft @ 3,500 — H-D claim
        "peak_torque_rpm": 3500,
        "fuel_system": "fi",  # ESPFI
        "cooling": "oil",  # air-cooled w/ precision oil-
        # cooled heads (M8 standard)
        "valve_config": "ohv",  # pushrod, 4 valves per cylinder
        "gears": 6,
        # 6-speed Cruise Drive internals derived from H-D media-kit overall
        # ratios (9.311..2.790) / (primary 34/46 x belt 32/66) — see header
        "gear_ratios": [3.337, 2.313, 1.718, 1.391, 1.185, 1.000],
        "primary_ratio": 1.353,  # chain primary 34/46 — H-D spec
        # BELT final drive — pulley teeth per H-D media kit (32/66 = 2.0625).
        # chain_pitch omitted (belt; importer infers None for H-D).
        "front_sprocket": 32,  # transmission belt pulley
        "rear_sprocket": 66,  # rear wheel belt pulley
        "dry_mass_kg": 291.0,  # curb 683 lb (309.8 kg) minus
        # 18.9 L fuel (~14.2 kg) + oil
        # (~4.5 kg) — H-D quotes curb only
        "wet_mass_kg": 310.0,  # 683 lb in running order
        "wheelbase_mm": 1695.0,  # 66.7 in — H-D spec
        "front_tire_size": "130/60B21",  # 21" front — Michelin Scorcher 11
        "rear_tire_size": "240/40R18",  # 240-section drag-style rear
        "cd": 0.82,  # JUDGMENT: no fairing, raked-out
        # rider triangle, arms high/forward;
        # slightly worse than Sport Chief's
        # 0.78 (no quarter fairing)
        "frontal_area_m2": 0.60,  # JUDGMENT: low seat (26.2") drops
        # torso vs Chief-class 0.62 despite
        # wide bars
    },
    source_name="spec_sheet",
)


# ── Harley-Davidson Fat Bob 114 (2018-2026 — FXFBS power bobber) ────────────
# The aggressive twin-headlight power bobber of the 2018 Softail relaunch.
# Cluster: cruiser_1300p (1868 cc V2).
# Sources:
#   - H-D 2018 spec sheet (FXFBS): ME-114 1,868 cc, bore 4.016 in (102 mm)
#     x stroke 4.5 in (114.3 mm), CR 10.5:1, 118 lb-ft (160 Nm) @ 3,500 rpm,
#     running order 676 lb, wheelbase 63.6 in, tires 150/80-16 / 180/70-16
#     (Dunlop D429F/D429, bias).
#   - MCN "Harley-Davidson Fat Bob FXFB (2018-on) Review": 94 bhp / 114 lb-ft
#     claimed (EU homologation power figure; H-D US publishes torque only).
#   - Cycle World "2018 Softail Fat Bob 114 Dyno" (2018): 82.32 rear-wheel hp
#     @ 4,660 rpm / 111.39 lb-ft @ 2,260 rpm — consistent with ~94 hp crank.
#   - Gearing identical to Breakout 117 above (shared M8 Softail Cruise
#     Drive; H-D my21 fat-bob-114.pdf lists the same 34/46 + 32/66 + overall
#     9.311..2.790 set).
HD_FAT_BOB_114_2018 = spec_from_dict(
    {
        "manufacturer": "Harley-Davidson",
        "model_name": "Fat Bob 114 (2018-2026)",
        "model_code": "FXFBS_2018",
        "year_from": 2018,
        "year_to": 2026,
        "category": "cruiser",  # power bobber, inverted fork
        "displacement_cc": 1868,  # Milwaukee-Eight 114 (114 ci)
        "bore_mm": 102.0,  # 4.016 in — H-D spec
        "stroke_mm": 114.3,  # 4.5 in
        "compression_ratio": 10.5,  # H-D spec (ME-114)
        "cylinders": 2,  # 45° V-twin, 4v/cyl pushrod
        "peak_power_hp": 94.0,  # EU homologation via MCN review
        "peak_power_rpm": 5020,  # H-D EU sheet power peak
        "peak_torque_nm": 160.0,  # 118 lb-ft @ 3,500 — H-D 2018 spec
        "peak_torque_rpm": 3500,
        "fuel_system": "fi",
        "cooling": "oil",  # precision oil-cooled M8 heads
        "valve_config": "ohv",
        "gears": 6,
        # Shared M8 Softail Cruise Drive cassette (see Breakout 117 header)
        "gear_ratios": [3.337, 2.313, 1.718, 1.391, 1.185, 1.000],
        "primary_ratio": 1.353,  # chain primary 34/46
        "front_sprocket": 32,  # belt pulleys 32/66 — H-D spec
        "rear_sprocket": 66,
        "dry_mass_kg": 292.0,  # running order 676 lb (306.6 kg)
        # minus 13.6 L fuel (~10.2 kg) +
        # oil (~4.5 kg)
        "wet_mass_kg": 307.0,  # 676 lb in running order
        "wheelbase_mm": 1615.0,  # 63.6 in — H-D spec
        "front_tire_size": "150/80B16",  # fat 16" front — Dunlop D429F
        "rear_tire_size": "180/70B16",  # H-D spec (180/70-16 bias)
        "cd": 0.80,  # JUDGMENT: flat drag-style bars,
        # slight forward lean (better than
        # mini-ape Street Bob 0.85)
        "frontal_area_m2": 0.62,  # JUDGMENT: wide bars + fat front
        # tire + upright torso
    },
    source_name="spec_sheet",
)


# ── Harley-Davidson Street Bob 114 (2021-2026 — FXBBS mini-ape bobber) ──────
# Lightest Milwaukee-Eight Softail; got the 114 upgrade for MY2021.
# Cluster: cruiser_1300p (1868 cc V2).
# Sources:
#   - H-D my21 media-kit spec PDF (street-bob-114.pdf, FXBBS): ME-114,
#     CR 10.5:1, 119 lb-ft (161 Nm) @ 3,000 rpm, 655 lb as tested (H-D
#     "running order"; rideapart quotes 659 lb), wheelbase 64.2 in, tires
#     100/90B19 / 150/80B16, primary 34/46, belt 32/66, overall ratios
#     9.311..2.790 (same M8 Softail Cruise Drive as above).
#   - Power: H-D EU homologation 94 hp @ 5,020 rpm (same state of tune as
#     Fat Bob 114 — shared airbox/cam/exhaust spec on the 114 Softails).
HD_STREET_BOB_114_2021 = spec_from_dict(
    {
        "manufacturer": "Harley-Davidson",
        "model_name": "Street Bob 114 (2021-2026)",
        "model_code": "FXBBS_2021",
        "year_from": 2021,
        "year_to": 2026,
        "category": "cruiser",  # stripped bobber, mini-ape bars
        "displacement_cc": 1868,
        "bore_mm": 102.0,
        "stroke_mm": 114.3,
        "compression_ratio": 10.5,  # H-D my21 spec sheet
        "cylinders": 2,
        "peak_power_hp": 94.0,  # EU homologation (114 Softail
        # shared tune)
        "peak_power_rpm": 5020,
        "peak_torque_nm": 161.0,  # 119 lb-ft @ 3,000 — H-D my21 spec
        "peak_torque_rpm": 3000,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "ohv",
        "gears": 6,
        # Shared M8 Softail Cruise Drive cassette (see Breakout 117 header)
        "gear_ratios": [3.337, 2.313, 1.718, 1.391, 1.185, 1.000],
        "primary_ratio": 1.353,
        "front_sprocket": 32,  # belt pulleys 32/66
        "rear_sprocket": 66,
        "dry_mass_kg": 283.0,  # 655 lb (297 kg) running order
        # minus 13.2 L fuel + oil
        "wet_mass_kg": 297.0,  # 655 lb in running order
        "wheelbase_mm": 1630.0,  # 64.2 in — H-D spec
        "front_tire_size": "100/90B19",  # 19" laced front — H-D spec
        "rear_tire_size": "150/80B16",
        "cd": 0.85,  # JUDGMENT: mini-ape bars lift the
        # rider's arms/torso into the wind —
        # worst aero of the Softail batch
        "frontal_area_m2": 0.63,  # JUDGMENT: raised arms increase
        # projected area vs Fat Bob's 0.62
    },
    source_name="spec_sheet",
)


# ── Harley-Davidson Low Rider S 117 (2022-2026 — FXLRS club-style) ──────────
# The West-Coast club-style performance Softail; MY2022 moved it from the
# 114 to the ME-117 with Screamin' Eagle Heavy Breather intake.
# Cluster: cruiser_1300p (1923 cc V2).
# Sources:
#   - H-D 2022 spec sheet (specifications_fxlrs_us.pdf): ME-117, bore
#     103.5 mm x stroke 114.3 mm, CR 10.2:1, claimed 103 hp + 125 lb-ft
#     (169 Nm) @ 3,500 rpm, 679 lb running order, wheelbase 63.6 in,
#     tires 110/90B19 / 180/70B16.
#   - Ultimate Motorcycling "2022 Low Rider S Review" (Jun 2022): confirms
#     the 103 hp / 125 lb-ft claim and 679 lb curb.
#   - Cycle World "2022 Low Rider S Dyno Test": 94.76 rear-wheel hp
#     @ 4,750 rpm / 115.13 lb-ft @ 3,200 rpm (consistent w/ 103 hp crank).
#   - Gearing: same M8 Softail Cruise Drive + 34/46 primary + 32/66 belt
#     (H-D my21/my22 media-kit low-rider-s PDFs).
HD_LOW_RIDER_S_117_2022 = spec_from_dict(
    {
        "manufacturer": "Harley-Davidson",
        "model_name": "Low Rider S 117 (2022-2026)",
        "model_code": "FXLRS_2022",
        "year_from": 2022,
        "year_to": 2026,
        "category": "cruiser",  # club-style performance cruiser
        "displacement_cc": 1923,
        "bore_mm": 103.5,
        "stroke_mm": 114.3,
        "compression_ratio": 10.2,
        "cylinders": 2,
        "peak_power_hp": 103.0,  # H-D claim (Screamin' Eagle
        # Heavy Breather + hotter tune
        # than the Breakout's 101 hp)
        "peak_power_rpm": 4750,  # CW dyno power peak rpm
        "peak_torque_nm": 169.0,  # 125 lb-ft @ 3,500 — H-D claim
        "peak_torque_rpm": 3500,
        "fuel_system": "fi",
        "cooling": "oil",
        "valve_config": "ohv",
        "gears": 6,
        # Shared M8 Softail Cruise Drive cassette (see Breakout 117 header)
        "gear_ratios": [3.337, 2.313, 1.718, 1.391, 1.185, 1.000],
        "primary_ratio": 1.353,
        "front_sprocket": 32,  # belt pulleys 32/66
        "rear_sprocket": 66,
        "dry_mass_kg": 289.0,  # 679 lb (308 kg) running order
        # minus 18.9 L fuel + oil
        "wet_mass_kg": 308.0,  # 679 lb in running order
        "wheelbase_mm": 1615.0,  # 63.6 in — H-D 2022 spec
        "front_tire_size": "110/90B19",  # H-D spec (Michelin Scorcher 31)
        "rear_tire_size": "180/70B16",
        "cd": 0.78,  # JUDGMENT: moto-bar + small
        # headlight cowl gives a slight
        # tuck vs bare Softails (matches
        # Sport Chief quarter-fairing 0.78)
        "frontal_area_m2": 0.62,  # JUDGMENT: wide moto bar, upright
    },
    source_name="spec_sheet",
)


# ── Harley-Davidson Iron 883 (2016-2022 — XL883N Evolution Sportster) ───────
# The blacked-out entry Sportster; 2016 refresh added cartridge forks +
# emulsion shocks (drivetrain unchanged: rubber-mount Evolution 883, FI
# since 2007). Kept in production through the 2022 Sportster Evo run-out.
# Sub-1300 cruiser — NOT in the cruiser_1300p cluster.
# Sources:
#   - H-D my16/my21 spec sheets (XL883N): Evolution 883 cc, bore 3.0 in
#     (76.2 mm) x stroke 3.811 in (96.8 mm), CR 9.0:1, 53.8 lb-ft (72.9 Nm)
#     @ 3,750 rpm, running order 562 lb, wheelbase 59.6 in, tires
#     100/90B19 57H / 150/80B16 77H (Michelin Scorcher 31).
#   - motorcycle.com 2016 Iron 883 spec page: 53 hp @ 5,750 rpm (H-D does
#     not publish power for Sportsters; this is the spec-DB consensus that
#     matches EU homologation and rear-wheel dyno ~46 hp).
#   - H-D my21 media-kit iron-883.pdf: primary chain 34/57 (1.676), final
#     belt 29/68 (2.345), overall ratios 10.410 / 7.436 / 5.531 / 4.584 /
#     3.931 — internal 5-speed derived: [2.648, 1.892, 1.407, 1.166, 1.000].
HD_IRON_883_2016 = spec_from_dict(
    {
        "manufacturer": "Harley-Davidson",
        "model_name": "Iron 883 (2016-2022)",
        "model_code": "XL883N_2016",
        "year_from": 2016,
        "year_to": 2022,
        "category": "cruiser",  # blacked-out bobber Sportster
        "displacement_cc": 883,  # Evolution 883, air-cooled
        "bore_mm": 76.2,  # 3.0 in — H-D spec
        "stroke_mm": 96.8,  # 3.811 in — shared Evo stroke
        "compression_ratio": 9.0,  # H-D spec (883 Evo)
        "cylinders": 2,  # 45° V-twin, 2v/cyl pushrod
        "peak_power_hp": 53.0,  # spec-DB consensus @ 5,750 (H-D
        # publishes torque only)
        "peak_power_rpm": 5750,
        "peak_torque_nm": 72.9,  # 53.8 lb-ft @ 3,750 — H-D claim
        "peak_torque_rpm": 3750,
        "fuel_system": "fi",  # ESPFI since 2007
        "cooling": "air",  # classic air-cooled Evolution
        "valve_config": "ohv",  # pushrod, 2 valves per cylinder
        "gears": 5,
        # 5-speed internals derived from H-D media-kit overall ratios
        # (10.410..3.931) / (primary 34/57 x belt 29/68) — see header
        "gear_ratios": [2.648, 1.892, 1.407, 1.166, 1.000],
        "primary_ratio": 1.676,  # chain primary 34/57 (883-specific;
        # the 1200 runs 38/57)
        "front_sprocket": 29,  # belt pulleys 29/68 — H-D my21 spec
        "rear_sprocket": 68,
        "dry_mass_kg": 247.0,  # H-D "as shipped" 545 lb
        "wet_mass_kg": 255.0,  # 562 lb in running order
        "wheelbase_mm": 1514.0,  # 59.6 in — H-D spec
        "front_tire_size": "100/90B19",
        "rear_tire_size": "150/80B16",
        "cd": 0.80,  # JUDGMENT: low solo seat + drag
        # bar, small frontal silhouette but
        # no bodywork at all
        "frontal_area_m2": 0.55,  # JUDGMENT: physically small bike
        # (26" seat) — well below the big-
        # twin cruisers' 0.60-0.64
    },
    source_name="spec_sheet",
)


# ── Harley-Davidson Forty-Eight (2016-2022 — XL1200X fat-front Sportster) ───
# 1200 Evolution Sportster with the 130-section 16" fat front + peanut tank.
# 2016 refresh shares the Iron 883's suspension update. Sub-1300 cruiser.
# Sources:
#   - H-D my16 spec sheet (XL1200X): Evolution 1202 cc, bore 3.5 in
#     (88.9 mm) x stroke 3.811 in (96.8 mm), CR 10.0:1, 70.8-71 lb-ft
#     (96 Nm) @ 3,500 rpm (2016+ intake/exhaust rev), running order 551 lb,
#     wheelbase 59.3 in, tires 130/90B16 73H / 150/80B16 77H (Michelin
#     Scorcher 31).
#   - motorcycle.com / ultimatespecs 2016 Forty-Eight pages: 66 hp @ ~5,500
#     rpm (spec-DB consensus; H-D publishes torque only for Sportsters).
#   - Gearing: same Sportster 5-speed internals as the Iron 883 (shared
#     XL gearbox — H-D spec overall 1st 9.315 = 1.500 primary x 2.648 x
#     2.345 belt); primary chain 38/57 (1.500 — 1200-specific), final belt
#     29/68 (motorcyclespecifications.com XL1200X sheets, all years).
HD_FORTY_EIGHT_2016 = spec_from_dict(
    {
        "manufacturer": "Harley-Davidson",
        "model_name": "Forty-Eight (2016-2022)",
        "model_code": "XL1200X_2016",
        "year_from": 2016,
        "year_to": 2022,
        "category": "cruiser",  # fat-front bobber Sportster
        "displacement_cc": 1202,  # Evolution 1200, air-cooled
        "bore_mm": 88.9,  # 3.5 in — H-D spec
        "stroke_mm": 96.8,  # 3.811 in
        "compression_ratio": 10.0,  # H-D spec (1200 Evo, 2016+)
        "cylinders": 2,  # 45° V-twin, 2v/cyl pushrod
        "peak_power_hp": 66.0,  # spec-DB consensus @ ~5,500 (H-D
        # publishes torque only)
        "peak_power_rpm": 5500,
        "peak_torque_nm": 96.0,  # 70.8 lb-ft @ 3,500 — H-D claim
        "peak_torque_rpm": 3500,
        "fuel_system": "fi",
        "cooling": "air",
        "valve_config": "ohv",
        "gears": 5,
        # Shared XL 5-speed internals (see Iron 883 header)
        "gear_ratios": [2.648, 1.892, 1.407, 1.166, 1.000],
        "primary_ratio": 1.500,  # chain primary 38/57 (1200 Evo)
        "front_sprocket": 29,  # belt pulleys 29/68
        "rear_sprocket": 68,
        "dry_mass_kg": 244.0,  # 551 lb (250 kg) running order
        # minus the tiny 7.9 L peanut tank
        # (~6 kg fuel) — H-D quotes curb
        "wet_mass_kg": 250.0,  # 551 lb in running order
        "wheelbase_mm": 1506.0,  # 59.3 in — H-D spec
        "front_tire_size": "130/90B16",  # fat 16" front — signature look
        "rear_tire_size": "150/80B16",
        "cd": 0.80,  # JUDGMENT: low slammed stance,
        # wide low bars — same tier as Iron
        "frontal_area_m2": 0.56,  # JUDGMENT: slightly above Iron 883
        # (fat front wheel + wider bars)
    },
    source_name="spec_sheet",
)


# ── Indian Challenger (2020-2026 — PowerPlus 108 fixed-fairing bagger) ──────
# Indian's Road Glide fighter: frame-mounted fairing bagger around the
# liquid-cooled PowerPlus 108. Platform data shared with the existing
# INDIAN_SPORT_CHIEF_2023 entry where its cited sources say shared (the
# Sport Chief service-manual/CW citations name the Challenger explicitly
# for the 6-speed cassette, primary and belt pulleys).
# Cluster: cruiser_1300p (1768 cc V2, 122 hp).
# Sources:
#   - Indian Motorcycle 2020 Challenger spec sheet: PowerPlus 108
#     1,768 cc 60° V-twin, bore 4.251 in (108 mm) x stroke 3.799 in
#     (96.5 mm), CR 11.0:1, 122 hp @ 5,500 rpm, 128 lb-ft (173.6 Nm)
#     @ 3,800 rpm, weight 796 lb empty tank / 831 lb full of fuel,
#     wheelbase 65.7 in, tires Metzeler Cruisetec 130/60B19 / 180/60R16.
#   - MCN "Indian Challenger (2020-on) Review": confirms 122 bhp @ 5,500;
#     notes top speed restricted to an indicated 112 mph.
#   - Gearing: 6-speed cassette [3.025, 2.105, 1.667, 1.395, 1.214, 1.063]
#     + belt pulleys F30/R72 + primary 1.521 reused from the Sport Chief
#     template entry (Indian service manual 9928660: cassette "IDENTICAL to
#     Challenger / Chief Dark Horse / Roadmaster"; Cycle World "Sport Chief
#     vs Challenger Dyno Test" Mar 2023: F30/R72 + primary 1.521 confirmed).
#   - ET note (NOT emitted as a benchmark row): Cycle World's Feb-2020
#     "Challenger Dark Horse vs Road Glide Special" comparison measured a
#     12.72 s quarter-mile (Road Glide 13.78 s) but published NO trap speed,
#     so the row is withheld per the trap-required tuple format. A future
#     pass that recovers the trap can add:
#     ("Indian", "Challenger", 2020, 12.72, <trap>, "Cycle World 2020").
INDIAN_CHALLENGER_2020 = spec_from_dict(
    {
        "manufacturer": "Indian",
        "model_name": "Challenger (2020-2026)",
        "model_code": "Challenger_2020",
        "year_from": 2020,
        "year_to": 2026,
        "category": "cruiser",  # fixed-fairing performance bagger
        "displacement_cc": 1768,  # PowerPlus 108 (108 ci) — NOT the
        # 1890 cc Thunderstroke
        "bore_mm": 108.0,
        "stroke_mm": 96.5,
        "compression_ratio": 11.0,
        "cylinders": 2,  # 60° V-twin, liquid-cooled
        "peak_power_hp": 122.0,  # Indian claim @ 5,500
        "peak_power_rpm": 5500,
        "peak_torque_nm": 173.6,  # 128 lb-ft @ 3,800 — Indian claim
        "peak_torque_rpm": 3800,
        "fuel_system": "fi",  # ride-by-wire
        "cooling": "liquid",
        "valve_config": "sohc",  # SOHC 4v/cyl (PowerPlus)
        "gears": 6,
        # PowerPlus-family 6-speed per Indian service manual 9928660 (via
        # the Sport Chief template entry — cassette explicitly shared)
        "gear_ratios": [3.025, 2.105, 1.667, 1.395, 1.214, 1.063],
        "primary_ratio": 1.521,  # CW Sport Chief/Challenger dyno test
        "front_sprocket": 30,  # belt pulleys F30/R72 (Gates
        # Polychain — belt, chain_pitch
        # omitted per template convention)
        "rear_sprocket": 72,
        "dry_mass_kg": 356.0,  # Indian "empty tank" 796 lb
        # (361 kg) minus residual fluids
        # margin (~5 kg oil/coolant stay in
        # the sim's fluid budget)
        "wet_mass_kg": 377.0,  # 831 lb full of fuel — Indian spec
        "wheelbase_mm": 1668.0,  # 65.7 in — Indian spec
        "front_tire_size": "130/60B19",  # Metzeler Cruisetec — Indian OEM
        "rear_tire_size": "180/60R16",
        "cd": 0.70,  # JUDGMENT: frame-mounted full
        # fairing + tall screen shields the
        # rider (best aero of the cruiser
        # batch; touring-class 0.68-0.72)
        "frontal_area_m2": 0.66,  # JUDGMENT: big bagger frontal —
        # fairing + bags + upright rider
    },
    source_name="spec_sheet",
)


# ── Indian 101 Scout (2025-2026 — SpeedPlus 1250 flagship sport cruiser) ────
# Flagship of the all-new 2025 Scout platform (steel tube frame). The
# 101 Scout gets the up-tuned SpeedPlus 1250: 111 hp vs 105 on the rest of
# the line, plus fully-adjustable suspension + dual Brembos.
# Sub-1300 cruiser — NOT in the cruiser_1300p cluster.
# Sources:
#   - Indian Motorcycle 2025 101 Scout spec sheet: SpeedPlus 1250
#     liquid-cooled 60° V-twin, 1,250 cc, bore 4.094 in (104 mm) x stroke
#     2.898 in (73.6 mm), CR 12.5:1, 111 hp @ 7,250 rpm, 82 lb-ft
#     (111.2 Nm) @ 6,300 rpm, dry 529 lb / curb 549 lb, wheelbase 61.5 in,
#     tires 130/60B19 / 150/80B16, 6-speed, belt final drive.
#   - Ultimate Motorcycling "2025 Indian 101 Scout Review" (Nov 2025) +
#     Cycle World 101 Scout Buyer's Guide: confirm 111 hp / 82 lb-ft /
#     549 lb curb.
#   - gear_ratios OMITTED: Indian does not publish the SpeedPlus 1250
#     internal cassette and no service-manual scan surfaced in research —
#     the importer's Tier-2 cruiser defaults handle gearing. Belt pulley
#     counts also unpublished; sprockets omitted so Tier-2 supplies the
#     final drive (documented fallback).
INDIAN_101_SCOUT_2025 = spec_from_dict(
    {
        "manufacturer": "Indian",
        "model_name": "101 Scout (2025-2026)",
        "model_code": "Scout_101_2025",
        "year_from": 2025,
        "year_to": 2026,
        "category": "cruiser",  # performance sport cruiser
        "displacement_cc": 1250,  # SpeedPlus 1250 (new for 2025 —
        # replaces the 1,133 cc Scout V2)
        "bore_mm": 104.0,
        "stroke_mm": 73.6,
        "compression_ratio": 12.5,
        "cylinders": 2,  # 60° V-twin, liquid-cooled
        "peak_power_hp": 111.0,  # Indian claim @ 7,250 (101-spec
        # tune; standard Scouts get 105)
        "peak_power_rpm": 7250,
        "peak_torque_nm": 111.2,  # 82 lb-ft @ 6,300 — Indian claim
        "peak_torque_rpm": 6300,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 4v/cyl (SpeedPlus)
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.2, 1.6, 1.222, 1.0, 0.833, 0.722],
        "primary_ratio": 1.92,
        # gear_ratios + belt pulleys omitted — not published (see header);
        # Tier-2 cruiser defaults apply
        "dry_mass_kg": 240.0,  # 529 lb dry — Indian spec
        "wet_mass_kg": 249.0,  # 549 lb curb — Indian spec
        "wheelbase_mm": 1562.0,  # 61.5 in — Indian spec
        "front_tire_size": "130/60B19",  # 19" cast front — Indian spec
        "rear_tire_size": "150/80B16",
        "cd": 0.76,  # JUDGMENT: low seat (26.8") +
        # moto bar, no fairing; between
        # Sport Chief 0.78 and sport bikes
        "frontal_area_m2": 0.58,  # JUDGMENT: compact mid-size
        # cruiser, narrower than the big
        # twins (0.60-0.66)
    },
    source_name="spec_sheet",
)


# ── Indian Chief Bobber Dark Horse (2022-2026 — Thunderstroke 116 bobber) ───
# The blacked-out big-bore bobber of the 2022 Chief-platform relaunch
# (63rd-anniversary Chief line). Thunderstroke 116 air-cooled 49° V-twin —
# the TS116 variant (the non-Dark-Horse base Chief Bobber runs the TS111,
# hence this entry models the Dark Horse per the task's TS116 target).
# Cluster: cruiser_1300p (1890 cc V2).
# Sources:
#   - Indian Motorcycle 2022 spec sheet (Chief Bobber Dark Horse):
#     Thunderstroke 116, 1,890 cc, bore 4.063 in (103.2 mm) x stroke
#     4.449 in (113 mm), CR 11.0:1, 120 lb-ft (162.7 Nm) @ 2,900 rpm,
#     wet 670 lb, wheelbase 64 in, 16" wire wheels w/ Pirelli Night Dragon
#     130/90B16 front / 180/65B16 rear, seat 26 in.
#   - Women Riders Now "2022 Indian Chief review": "approximately 79
#     horsepower" for the TS116 (Indian publishes torque only; rear-wheel
#     dynos read ~79 hp — consistent with an ~86 hp crank estimate, we
#     carry the published 79 @ ~4,500 rpm as the conservative claim).
#   - Gearing: 6-speed cassette + primary 1.521 + belt F30/R72 reused from
#     the Sport Chief template entry — Indian service manual 9928660 covers
#     the shared Chief-family gearbox (the Sport Chief IS a Chief-platform
#     variant; cassette cited as identical to Chief Dark Horse).
INDIAN_CHIEF_BOBBER_DH_2022 = spec_from_dict(
    {
        "manufacturer": "Indian",
        "model_name": "Chief Bobber Dark Horse (2022-2026)",
        "model_code": "Chief_Bobber_DH_2022",
        "year_from": 2022,
        "year_to": 2026,
        "category": "cruiser",  # big-bore bobber, mini-ape bars
        "displacement_cc": 1890,  # Thunderstroke 116 (116 ci),
        # air-cooled — NOT the PowerPlus
        "bore_mm": 103.2,
        "stroke_mm": 113.0,
        "compression_ratio": 11.0,
        "cylinders": 2,  # 49° V-twin, air-cooled
        "peak_power_hp": 79.0,  # dyno-consensus claim (Indian
        # publishes torque only for TS116)
        "peak_power_rpm": 4500,
        "peak_torque_nm": 162.7,  # 120 lb-ft @ 2,900 — Indian claim
        "peak_torque_rpm": 2900,
        "fuel_system": "fi",
        "cooling": "air",  # classic air-cooled w/ big fins
        "valve_config": "ohv",  # pushrod 2v/cyl (Thunderstroke)
        "gears": 6,
        # Chief-family 6-speed per Indian service manual 9928660 (via the
        # Sport Chief template entry — same platform gearbox)
        "gear_ratios": [3.025, 2.105, 1.667, 1.395, 1.214, 1.063],
        "primary_ratio": 1.521,
        "front_sprocket": 30,  # belt pulleys F30/R72 (belt —
        # chain_pitch omitted)
        "rear_sprocket": 72,
        "dry_mass_kg": 288.0,  # wet 670 lb (304 kg) minus 15.1 L
        # fuel (~11.3 kg) + oil (~4.5 kg)
        "wet_mass_kg": 304.0,  # 670 lb wet — Indian claim
        "wheelbase_mm": 1626.0,  # 64 in — Indian spec (Chief
        # platform, same as Sport Chief)
        "front_tire_size": "130/90B16",  # Pirelli Night Dragon, 16" wire
        "rear_tire_size": "180/65B16",
        "cd": 0.86,  # JUDGMENT: mini-ape bars + bolt-
        # upright rider — worst aero of the
        # batch (vs Chief Dark Horse-class
        # 0.85 in the template comments)
        "frontal_area_m2": 0.64,  # JUDGMENT: raised arms + wide
        # 16" front + big air-cooled engine
    },
    source_name="spec_sheet",
)


# ── Buell XB12R Firebolt (2004-2010 — fuel-in-frame sport V-twin) ───────────
# Erik Buell's mass-centralised sportbike: fuel-in-frame aluminium beam,
# oil-in-swingarm, 21°/52-in geometry, perimeter front brake, and the
# Thunderstorm 1203 (Sportster-1200-derived, hotter cams/heads).
# Sources:
#   - Buell 2004-2010 spec sheets (via motorcycle.com spec pages +
#     autoevolution archives): Thunderstorm 1,203 cc 45° air/oil/fan-cooled
#     V-twin, bore 3.5 in (88.9 mm) x stroke 3.812 in (96.8 mm), CR 10.0:1,
#     103 hp @ 6,800 rpm, 84 lb-ft (113.9 Nm) @ 6,000 rpm, dry 179 kg,
#     wheelbase 52.0 in (1,321 mm), tires 120/70ZR17 / 180/55ZR17,
#     14.5 L fuel-in-frame.
#   - Drivetrain (motorcycle.com 2004-2010 spec pages): 5-speed
#     [2.688, 1.850, 1.433, 1.181, 1.000], primary 1.500 (57/38), final
#     drive aramid belt 2.407 (F27/R65 pulleys) — belt, chain_pitch omitted
#     (importer infers None for make "Buell").
#   - ET note (NOT emitted): the widely-quoted 11.4 s standing quarter is a
#     spec-archive figure (autoevolution/MCN panel) with no terminal speed
#     and no verifiable magazine data panel accessible this session — row
#     withheld per the instrumented-test-only rule.
BUELL_XB12R_2004 = spec_from_dict(
    {
        "manufacturer": "Buell",
        "model_name": "XB12R Firebolt (2004-2010)",
        "model_code": "XB12R_2004",
        "year_from": 2004,
        "year_to": 2010,
        "category": "sport",  # clip-on sportbike ergonomics
        "displacement_cc": 1203,  # Thunderstorm 1203 (Sportster-
        # 1200-derived, hotter tune)
        "bore_mm": 88.9,
        "stroke_mm": 96.8,
        "compression_ratio": 10.0,
        "cylinders": 2,  # 45° V-twin, air/oil/fan-cooled
        "peak_power_hp": 103.0,  # Buell claim @ 6,800
        "peak_power_rpm": 6800,
        "peak_torque_nm": 113.9,  # 84 lb-ft @ 6,000 — Buell claim
        "peak_torque_rpm": 6000,
        "fuel_system": "fi",  # Buell DDFI-II/III
        "cooling": "air",  # air/oil + electric fan
        "valve_config": "ohv",  # pushrod 2v/cyl
        "gears": 5,
        # 5-speed per Buell spec sheets (motorcycle.com 2004-2010 pages)
        "gear_ratios": [2.688, 1.850, 1.433, 1.181, 1.000],
        "primary_ratio": 1.500,  # chain primary 57/38
        "front_sprocket": 27,  # belt pulleys F27/R65 (2.407) —
        # aramid belt, chain_pitch omitted
        "rear_sprocket": 65,
        "dry_mass_kg": 179.0,  # Buell claim (fuel-in-frame,
        # famously light)
        "wet_mass_kg": 193.0,  # dry + 14.5 L fuel + oil
        "wheelbase_mm": 1321.0,  # 52.0 in — shortest in class
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.64,  # JUDGMENT: bikini half-fairing
        # only — the rider's shoulders/arms
        # sit in clean air (worse than full
        # -fairing reps 0.55-0.60, better
        # than naked twins 0.70+). First-
        # pass 0.62/0.44 simmed a 218 km/h
        # trap — implausible for 103 hp
        # (real XB12s trap ~182-193);
        # widened to match the bike's
        # roomy, upright-for-a-sportbike
        # stance
        "frontal_area_m2": 0.48,  # JUDGMENT: short but WIDE (fuel-
        # in-frame spine + wide clip-ons);
        # rider sits proud of the low
        # screen — above race-rep 0.42-
        # 0.44, below naked 0.50+
    },
    source_name="spec_sheet",
)


# ── EBR 1190RX (2014-2016 — 185 hp American superbike) ──────────────────────
# Erik Buell Racing's homologation-grade superbike: ET-V2 1190 72° V-twin,
# fuel-in-frame, perimeter front brake, 419 lb / 185 hp.
# Sources:
#   - EBR 2014 press/spec sheet (via Roadracing World "EBR Introduces
#     419-Pound, 185-Horsepower 1190RX" + totalmotorcycle 2014 1190RX
#     spec page): ET-V2 1,190 cc 72° liquid-cooled V-twin, bore 106 mm x
#     stroke 67.5 mm, CR 13.4:1, 185 hp @ 10,600 rpm, 101.6-102 lb-ft
#     (138 Nm) @ 8,200 rpm, wet-no-fuel 419 lb (190 kg), wheelbase 55.5 in
#     (1,410 mm), tires 120/70ZR17 / 190/55ZR17.
#   - Drivetrain (EBR spec sheet via totalmotorcycle/EBR owner's manual
#     excerpts): primary GEAR drive 36/65 (1.806), 6-speed
#     [2.46, 1.75, 1.38, 1.17, 1.04, 0.96], 520 Z-ring CHAIN, sprockets
#     F16/R41. NOTE: importer's _infer_chain_pitch has no EBR rule and
#     will tag 1190 cc as "525" — cosmetic parts-fitment quirk only
#     (pitch mm identical); flagged, not fixed (file-ownership rule).
#   - ET note (NOT emitted): the 10.04 s quarter-mile circulating for the
#     1190RX traces to aggregators (zeroto60times/hotcars), not to an
#     accessible magazine data panel — row withheld.
EBR_1190RX_2014 = spec_from_dict(
    {
        "manufacturer": "EBR",
        "model_name": "1190RX (2014-2016)",
        "model_code": "EBR_1190RX_2014",
        "year_from": 2014,
        "year_to": 2016,
        "category": "sport",  # full-fairing superbike
        "displacement_cc": 1190,  # ET-V2 1190
        "bore_mm": 106.0,
        "stroke_mm": 67.5,
        "compression_ratio": 13.4,
        "cylinders": 2,  # 72° V-twin ("1190" token maps
        # to V2 in the importer)
        "peak_power_hp": 185.0,  # EBR claim @ 10,600
        "peak_power_rpm": 10600,
        "peak_torque_nm": 138.0,  # 101.6 lb-ft @ 8,200 — EBR claim
        "peak_torque_rpm": 8200,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 4v/cyl
        "gears": 6,
        # 6-speed per EBR spec sheet (see header)
        "gear_ratios": [2.46, 1.75, 1.38, 1.17, 1.04, 0.96],
        "primary_ratio": 1.806,  # gear primary 36/65
        "front_sprocket": 16,  # 520 Z-ring chain, F16/R41
        "rear_sprocket": 41,
        "chain_pitch": "520",  # documentation only — importer
        # re-infers (525 for 1190 cc; see
        # header note)
        "dry_mass_kg": 190.0,  # EBR "wet, no fuel" 419 lb —
        # closest published figure to dry
        "wet_mass_kg": 203.0,  # + 17 L fuel
        "wheelbase_mm": 1410.0,  # 55.5 in — EBR spec
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.59,  # JUDGMENT: modern full-fairing
        # superbike; V-twin is narrow but
        # the fairing is stubby — litre-
        # sport band (0.55-0.62)
        "frontal_area_m2": 0.42,  # JUDGMENT: compact superbike,
        # full race tuck
    },
    source_name="spec_sheet",
)


# ── Honda CBR1100XX Super Blackbird (1997-1998 — the pre-Hayabusa king) ─────
# The bike built to dethrone the ZZ-R1100: world's fastest production
# motorcycle 1997-1998 until the Hayabusa. This entry models the CARBURETED
# first generation (1997-1998, 4x 42 mm CV carbs) — the best-documented gen
# with clean period instrumented tests; the 1999+ PGM-FI gen differs (FI,
# 24 L tank, taller gearing).
# Sources:
#   - Honda 1997 spec sheet (via motorcyclespecs 1997/1998 CBR1100XX
#     pages + bikez 1997): 1,137 cc DOHC I4, bore 79 mm x stroke 58 mm,
#     CR 11.0:1, 164 hp @ 9,500 rpm, 124 Nm @ 7,250 rpm, dry 223 kg,
#     wheelbase 1,490 mm, tires 120/70ZR17 / 180/55ZR17, 22 L tank.
#   - Honda service manual gearing (via motorcyclespecifications.com
#     CBR1100XX 1998 sheet): primary 1.571 (88/56), 6-speed
#     [2.769 (36/13), 2.000 (32/16), 1.579 (30/19), 1.333 (28/21),
#     1.167 (28/24), 1.042 (25/24)], final 2.647 (F17/R45), 530 chain.
#   - Cycle World 1997 road test (republished as the Sport Rider archive
#     "1997 Honda CBR1100XX Road Test"): quarter-mile 10.27 s @ 136 mph
#     with 10.30/10.31 backup runs — the SAME figure a prior MotoQuant
#     benchmark-import session independently vetted as "the cleanest
#     instrumented test in the archive" (validation_sweep.py pass-9 notes)
#     while flagging the model as missing from the catalog. This entry
#     closes that carry-forward.
HONDA_CBR1100XX_1997 = spec_from_dict(
    {
        "manufacturer": "Honda",
        "model_name": "CBR1100XX Super Blackbird (1997-1998)",
        "model_code": "CBR1100XX_1997",
        "year_from": 1997,
        "year_to": 1998,
        "category": "sport",  # hypersport / sport-tourer
        "displacement_cc": 1137,
        "bore_mm": 79.0,
        "stroke_mm": 58.0,
        "compression_ratio": 11.0,
        "cylinders": 4,  # inline-4, liquid-cooled
        "peak_power_hp": 164.0,  # Honda claim @ 9,500 (carb gen)
        "peak_power_rpm": 9500,
        "peak_torque_nm": 124.0,  # Honda claim @ 7,250
        "peak_torque_rpm": 7250,
        "fuel_system": "carb",  # 4x 42 mm Keihin CV (1997-98
        # gen; 1999+ went PGM-FI)
        "cooling": "liquid",
        "valve_config": "dohc",  # DOHC 16v
        "gears": 6,
        # Honda service-manual cassette (see header for tooth counts)
        "gear_ratios": [2.769, 2.000, 1.579, 1.333, 1.167, 1.042],
        "primary_ratio": 1.571,  # 88/56
        "front_sprocket": 17,  # F17/R45, 530 chain
        "rear_sprocket": 45,
        "chain_pitch": "530",
        "dry_mass_kg": 223.0,  # Honda claim (carb gen)
        "wet_mass_kg": 246.0,  # + 22 L fuel + fluids
        "wheelbase_mm": 1490.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.55,  # JUDGMENT: the class aero
        # benchmark of its era — pointed
        # nose, flush bodywork, famously
        # slick; floor of the catalog's
        # 0.55-0.95 motorcycle band
        "frontal_area_m2": 0.48,  # JUDGMENT: bigger than a race
        # rep (sport-tourer scale, tall
        # screen) — cf. existing litre
        # sports ~0.42-0.46
    },
    source_name="spec_sheet",
)


# ── Master list — aggregated by the orchestrator ─────────────────────────────
US_EXPANSION_BIKES = [
    HD_BREAKOUT_117_2023,
    HD_FAT_BOB_114_2018,
    HD_STREET_BOB_114_2021,
    HD_LOW_RIDER_S_117_2022,
    HD_IRON_883_2016,
    HD_FORTY_EIGHT_2016,
    INDIAN_CHALLENGER_2020,
    INDIAN_101_SCOUT_2025,
    INDIAN_CHIEF_BOBBER_DH_2022,
    BUELL_XB12R_2004,
    EBR_1190RX_2014,
    HONDA_CBR1100XX_1997,
]


# ── ET benchmarks (instrumented magazine tests ONLY, ET + trap both) ─────────
# Format matches scripts/validation_sweep.py BENCHMARKS:
#   (manufacturer_substr, model_substr, year_hint, target_et_s, trap_kmh,
#    source_label)
# Withheld-but-verified ETs (trap speed unpublished — see the entry comment
# blocks above): Indian Challenger CW-2020 12.72 s. Rejected as
# non-instrumented/aggregator-grade: Buell XB12R 11.4 s (spec-archive),
# EBR 1190RX 10.04 s (zeroto60times/hotcars aggregation), M8 Softail and
# Evolution Sportster forum/simulator times. No accessible instrumented
# quarter-mile was found this session for the Harley Softail/Sportster
# entries, the 101 Scout, or the Chief Bobber Dark Horse — honest absence
# over fabrication.
ET_BENCHMARKS: list[tuple[str, str, int, float, float, str]] = [
    # Cycle World 1997 road test (Sport Rider archive republication):
    # 10.27 s @ 136 mph (218.9 km/h), backed by 10.30/10.31 repeat runs.
    # Independently pre-vetted by the 2026-05-25 benchmark-import session
    # ("cleanest instrumented test in the archive" — validation_sweep.py
    # pass-9 rejection notes, held back only because the model was not yet
    # in the catalog).
    ("Honda", "CBR1100XX", 1997, 10.27, 218.9, "Cycle World 1997"),
]


# ── Top-speed benchmarks ─────────────────────────────────────────────────────
# Format matches scripts/topspeed_sweep.py BENCHMARKS:
#   (manufacturer_substr, model_substr, year_hint, target_kmh, source)
# Factory/period-archive claims allowed per the existing source conventions.
# Withheld: Indian Challenger (sources conflict — MCN says limited to an
# indicated 112 mph, 2023-era coverage says governed at 125 mph); Harley
# M8 Softails / Sportsters / Chief (no credible published figure found).
TOPSPEED_BENCHMARKS: list[tuple[str, str, int, float, str]] = [
    # Period road tests clocked the carb Blackbird at 176-179 mph (fastest
    # production bike 1997-98; Sport Rider measured 176.1-178.5 mph across
    # tests). 285 km/h = ~177 mph, mid-band of the published range.
    ("Honda", "CBR1100XX", 1997, 285, "period road tests (176-179 mph)"),
    # Spec-archive figure (autoevolution XB12R panels): 249 km/h — gearing
    # check: 5th 1.00 x primary 1.500 x belt 2.407 at the 7,500 rpm
    # rev ceiling = ~243 km/h, so 249 is the drag-vs-gearing-limited claim.
    ("Buell", "XB12R", 2004, 249, "factory claim (spec archive)"),
    # EBR's published claim for the 1190RX: ~189 mph (304 km/h) — echoed
    # in Motorcyclist/Roadracing World launch coverage.
    ("EBR", "1190RX", 2014, 304, "factory claim (~189 mph)"),
]
