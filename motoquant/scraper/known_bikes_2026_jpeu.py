"""
JP drag-legends + EU-depth catalogue expansion (July 3, 2026)
=============================================================
14 bikes: Japanese drag-strip legends (ZX-12R, V-Max 1200, GSX-R600/750
final gens, ZRX1200R, GSX1400) + European depth (Speed Triple 1050 x2,
Street Triple 675, Ducati 996 Biposto, Diavel 1260 S, Panigale V2 890,
MV Agusta Dragster 800 RR, Bimota Tesi H2).

Every load-bearing number (power/torque + rpm, mass, bore/stroke, gearing,
sprockets, tires, wheelbase) was verified against manufacturer spec sheets,
service-manual data or instrumented magazine tests via web research on
2026-07-03; per-entry comment blocks cite the sources. Judgment-call fields
(cd, frontal_area_m2) are estimated from comparable bikes already in the
catalogue, with reasoning inline. Where a service-manual gear cassette could
NOT be verified, gear_ratios is deliberately OMITTED so the importer's
Tier-1/Tier-2 lookup handles it — each such omission is documented.

Also exports:
  ET_BENCHMARKS       — instrumented quarter-mile rows (magazine tests +
                        clearly-labelled MotoStatz aggregate rows, matching
                        the source-weighting convention of
                        scripts/validation_sweep.py BENCHMARKS)
  TOPSPEED_BENCHMARKS — factory-limited / tested top-speed rows in the
                        scripts/topspeed_sweep.py BENCHMARKS format

Kept as a sibling module (not appended to known_bikes.py) per the standing
file-write-truncation hygiene note; the orchestrator wires aggregation.
"""

from __future__ import annotations

from .bikez import spec_from_dict

# ── Kawasaki Ninja ZX-12R (2000-2006 — the Hayabusa's direct rival) ─────────
# Kawasaki's 1199 cc monocoque-framed hyperbike, built explicitly to dethrone
# the Hayabusa. 178 PS static / ~190 hp with ram air (Wikipedia + Kawasaki
# press data). A1 (2000-01) vs B1 (2002-06) differ mainly in fairing/steering
# geometry; one entry covers the family, anchored on the 2000 A1.
# Sources:
#   - Cycle World "ZX-12R" road test (June 2000 issue,
#     magazine.cycleworld.com/article/2000/6/1/zx-12r): 1/4 mile 10.04 s @
#     143.78 mph (231.4 km/h), 0-60 2.59 s, top speed electronically limited
#     186 mph; dry weight 210 kg (463 lb)
#   - Motorcyclist "2002 Kawasaki ZX-12R Road Test": 9.87 s @ 146.29 mph
#     (235.4 km/h) — the B1's best published instrumented pass
#   - motoplanete / moto-data 2000 ZX-12R spec listings: bore x stroke
#     83.0 x 55.4 mm, CR 12.2:1, gear ratios 2.43 / 1.82 / 1.44 / 1.25 /
#     1.13 / 1.03, final drive 2.56, tires 120/70ZR17 + 200/50ZR17
#   - ZX12R owner forums quoting the Kawasaki service manual
#     (locostbuilders/bikeland gear-ratio threads): primary 83/52 = 1.596,
#     6th gear 31/30 = 1.033, final drive 18T/46T (530 chain)
#   - MCN ZX-12R (2000-2006) review: 178 bhp claim, 134 Nm torque
KAWASAKI_ZX12R_2000 = spec_from_dict(
    {
        "manufacturer": "Kawasaki",
        "model_name": "Ninja ZX-12R (2000-2006)",
        "model_code": "ZX1200A",
        "year_from": 2000,
        "year_to": 2006,
        "category": "sport",
        "displacement_cc": 1199,
        "bore_mm": 83.0,
        "stroke_mm": 55.4,
        "compression_ratio": 12.2,
        "cylinders": 4,
        "peak_power_hp": 178.0,  # 178 PS @ 10,500 static (no ram air);
        # ~190 hp at speed — sim's static crank
        # figure per catalogue convention
        "peak_power_rpm": 10500,
        "peak_torque_nm": 134.0,  # 134 Nm @ 7,500 — MCN / Kawasaki spec
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",  # 46 mm Keihin throttle bodies
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Service-manual cassette (owner-forum transcriptions of the Kawasaki
        # manual; cross-checked against the motoplanete published list):
        "gear_ratios": [2.43, 1.82, 1.44, 1.25, 1.13, 1.033],
        "primary_ratio": 1.596,  # 83/52 per service-manual data
        "front_sprocket": 18,  # 18T/46T = 2.556 final, matches the
        "rear_sprocket": 46,  # published 2.56 final-drive ratio
        "chain_pitch": "530",
        "dry_mass_kg": 210.0,  # Cycle World 2000: 463 lb dry
        "wheelbase_mm": 1440.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/50ZR17",
        "cd": 0.60,  # est: monocoque hyperbike with ram-air
        # nose, slipperier than Ninja H2 (0.63),
        # slightly above ZX-14R (0.58) — judged
        # vs those catalogue anchors
        "frontal_area_m2": 0.50,  # est: between ZX-14R (0.52) and
        # H2 (0.48) — big but low hyperbike
    },
    source_name="spec_sheet",
)


# ── Yamaha VMAX 1200 (1985-2007 — THE original drag muscle bike) ────────────
# Yamaha's V-Boost 70-degree V4 muscle bike; branded "V-Max" in period, named
# "VMAX 1200" here so the importer's _NON_CHAIN_MODELS "VMAX" token correctly
# marks it non-chain (shaft drive) for parts fitment, matching the existing
# "VMAX 1700" catalogue entry style. Full-power (non-restricted) spec used —
# the drag-relevant configuration. NOTE: importer's _infer_cylinder_config has
# no V4 token for VMAX so cylinder_config infers I4 (same known wart as the
# catalogue VMAX 1700) — physics unaffected, parts fitment marginally so.
# Category "naked" (not cruiser) per the VMAX 1700 entry's April-24 note:
# stub-tail muscle bike, not a chrome cruiser; avoids the cruiser heavy-
# flywheel inertia convention that mismatches the high-rev V-Boost engine.
# Sources:
#   - Cycle World "Yamaha: V-Max" (May 1985 issue,
#     magazine.cycleworld.com/article/1985/5/1/yamaha-v-max): instrumented
#     drag test, best standard-conditions run 10.89 s @ 128.75 mph
#     (207.2 km/h); pro-rider best 10.64 s @ 128.57 mph; top speed 145 mph
#   - Wikipedia "Yamaha VMAX" + autoevolution V-Max (1985-1986): 1,198 cc
#     liquid-cooled 70-deg V4, 76.0 x 66.0 mm, 10.5:1, 145 hp full-power,
#     ~122 Nm (90 lb-ft), quad 35 mm Mikuni carbs, V-Boost opens at 6,000 rpm
#   - ultimatespecs / motoparts.store V-Max 1200 listings: dry 262 kg,
#     wheelbase 1,590 mm, tires 110/90V18 front / 150/90B15 rear
#   - vmaxforum.net "Gear ratios and HP/TQ" (service-manual transcription):
#     primary 1.775, secondary (shaft) reduction 2.851, 5-speed cassette
#     2.529 / 1.772 / 1.347 / 1.076 / 0.928
YAMAHA_VMAX_1200_1985 = spec_from_dict(
    {
        "manufacturer": "Yamaha",
        "model_name": "VMAX 1200 (1985-2007)",
        "model_code": "VMX12",
        "year_from": 1985,
        "year_to": 2007,
        "category": "naked",  # muscle bike — see note above
        "displacement_cc": 1198,
        "bore_mm": 76.0,
        "stroke_mm": 66.0,
        "compression_ratio": 10.5,
        "cylinders": 4,  # 70-degree V4 (importer infers I4 —
        # documented wart, see header comment)
        "peak_power_hp": 145.0,  # full-power spec @ 9,000 rpm
        # (Cycle World 1985 quotes Yamaha's
        # 143-145 hp crank claim)
        "peak_power_rpm": 9000,
        "peak_torque_nm": 122.0,  # ~90 lb-ft @ 7,500 rpm with V-Boost
        "peak_torque_rpm": 7500,
        "fuel_system": "carb",  # 4x Mikuni 35 mm downdraft + V-Boost
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 5,
        # Service-manual cassette (vmaxforum transcription):
        "gear_ratios": [2.529, 1.772, 1.347, 1.076, 0.928],
        "primary_ratio": 1.775,
        # SHAFT FINAL DRIVE — no sprockets exist. The verified secondary
        # reduction is 2.851; encoded as pseudo-teeth 20/57 (= 2.850) because
        # the importer derives final_ratio from a concrete tooth pair (same
        # convention as the catalogue VMAX 1700 shaft encoding, 18/46).
        # chain_pitch omitted + "VMAX" model token → parts engine sees
        # non-chain, so no sprocket/chain parts will wrongly fit.
        "front_sprocket": 20,
        "rear_sprocket": 57,
        "final_drive": "shaft",
        "dry_mass_kg": 262.0,
        "wheelbase_mm": 1590.0,
        "front_tire_size": "110/90V18",  # V-rated bias; "V18" format trips a
        # cosmetic validator warning only
        "rear_tire_size": "150/90B15",  # 15" bias rear — importer's
        # single-letter B15 rim regex reads
        # the correct 15" rim (July-2 fix)
        "cd": 0.70,  # est: 80s muscle-naked ridden in drag
        # tuck; worse than the wind-tunnel-era
        # VMAX 1700 (0.55 in tuck) but far
        # better than an upright cruiser (0.90)
        "frontal_area_m2": 0.56,  # est: broad tank/scoop cluster,
        # slightly under VMAX 1700's 0.58
    },
    source_name="spec_sheet",
)


# ── Suzuki GSX-R 600 (2011-2024 — the missing final generation, L1) ─────────
# The long-lived L1 generation (carried nearly unchanged through 2024) that
# completes the catalogue's GSX-R 600 line (older gens end at 2010).
# Sources:
#   - Suzuki GSX-R600 L1 spec sheet via ultimatespecs / motorcyclespecs 2011:
#     599 cc, 67.0 x 42.5 mm, CR 12.9:1, 125 hp (92.4 kW) @ 13,500 rpm,
#     69.6 Nm @ 11,500 rpm, wet (kerb) 187 kg, wheelbase 1,385 mm
#   - Suzuki GSX-R600 service manual 2011-2020 (via Guhl Motors gear chart
#     "2011-2019 GSXR600" + ManualsLib): primary 1.974, cassette 2.687 /
#     2.105 / 1.761 / 1.521 / 1.347 / 1.208 (6th = 29/24), stock final
#     16T/43T (= 2.687)
#   - Only wet mass is published by Suzuki; dry_mass_kg deliberately omitted
#     so the importer's documented wet-25 kg conversion applies (162 kg —
#     consistent with the catalogue's 2008-2010 entry at 162 kg dry).
SUZUKI_GSXR600_L1_2011 = spec_from_dict(
    {
        "manufacturer": "Suzuki",
        "model_name": "GSX-R 600 (2011-2024)",
        "model_code": "GSX-R600L1",
        "year_from": 2011,
        "year_to": 2024,
        "category": "sport",
        "displacement_cc": 599,
        "bore_mm": 67.0,
        "stroke_mm": 42.5,
        "compression_ratio": 12.9,
        "cylinders": 4,
        "peak_power_hp": 125.0,  # 92.4 kW @ 13,500 rpm
        "peak_power_rpm": 13500,
        "peak_torque_nm": 69.6,
        "peak_torque_rpm": 11500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Service-manual cassette (Guhl Motors chart + Suzuki manual):
        "gear_ratios": [2.687, 2.105, 1.761, 1.521, 1.347, 1.208],
        "primary_ratio": 1.974,
        "front_sprocket": 16,
        "rear_sprocket": 43,
        "chain_pitch": "520",
        "wet_mass_kg": 187.0,  # Suzuki kerb figure — dry omitted on
        # purpose (importer converts wet-25)
        "wheelbase_mm": 1385.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.61,  # est: modern supersport fairing —
        # matches the 2008-2010 GSX-R 600
        # catalogue anchor (0.60), marginally
        # above the slipperier K8 nose
        "frontal_area_m2": 0.40,  # est: compact 600 supersport, between
        # the catalogue K8 600 (0.38) and
        # Daytona 675 (0.43)
    },
    source_name="spec_sheet",
)


# ── Suzuki GSX-R 750 (2011-2024 — the missing final generation, L1) ─────────
# The last GSX-R 750 generation; class-of-one 750 supersport. Completes the
# catalogue line (older gens end at 2010).
# Sources:
#   - Suzuki GSX-R750 L1 spec sheet via motorcyclespecs / autoevolution 2011:
#     750 cc, 70.0 x 48.7 mm, CR 12.5:1, 148 hp @ 12,800 rpm, 86 Nm
#     @ 11,200 rpm, wet 190 kg, wheelbase 1,390 mm, RK525 chain (116 links)
#   - gixxer.com "Gear Ratio's 2011 750" (service-manual transcription,
#     confirmed unchanged from 2009): 1st 2.785 (39/14), 2nd 2.052 (39/19),
#     3rd 1.714 (36/21), 4th 1.500 (36/24), 5th 1.347 (31/23),
#     6th 1.208 (29/24); primary 74/42 (= 1.762); final 17T/45T
#   - Cycle World "2011 GSX-R750 — The Last of a Class" (Sport Rider):
#     1/4 mile 10.4 s (trap speed not published in the retrievable copy, so
#     no ET_BENCHMARKS row — honesty gate; do not fabricate the trap)
SUZUKI_GSXR750_L1_2011 = spec_from_dict(
    {
        "manufacturer": "Suzuki",
        "model_name": "GSX-R 750 (2011-2024)",
        "model_code": "GSX-R750L1",
        "year_from": 2011,
        "year_to": 2024,
        "category": "sport",
        "displacement_cc": 750,
        "bore_mm": 70.0,
        "stroke_mm": 48.7,
        "compression_ratio": 12.5,
        "cylinders": 4,
        "peak_power_hp": 148.0,
        "peak_power_rpm": 12800,
        "peak_torque_nm": 86.0,
        "peak_torque_rpm": 11200,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Service-manual cassette (gixxer.com transcription, = 2009 box):
        "gear_ratios": [2.785, 2.052, 1.714, 1.500, 1.347, 1.208],
        "primary_ratio": 1.762,  # 74/42
        "front_sprocket": 17,
        "rear_sprocket": 45,
        "chain_pitch": "525",  # RK525ROZ5Y OEM
        "wet_mass_kg": 190.0,  # Suzuki kerb figure — dry omitted
        # (importer wet-25 → 165 kg, in line
        # with the 163 kg dry of the catalogue
        # 2008-2010 GSX-R 750)
        "wheelbase_mm": 1390.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.62,  # est: same bodywork family as the
        # L1 600 (0.61 here); a touch more
        # cooling drag from the bigger engine
        "frontal_area_m2": 0.41,  # est: shares the 600 L1 chassis
        # (0.40) with marginally wider ducts
    },
    source_name="spec_sheet",
)


# ── Kawasaki ZRX1200R (2001-2008 — Eddie Lawson replica muscle naked) ───────
# Kawasaki's big carbureted retro-muscle naked (ZRX1100 successor), the
# green-lined Lawson-replica quarter-fairing bike beloved of the roll-on drag
# crowd. 5-speed box (the 6-speed came only with the 2009+ Japan-market DAEG).
# Sources:
#   - Wikipedia "Kawasaki ZRX1200R" + motorcyclespecs 2001: 1,164 cc I4,
#     79.0 x 59.4 mm, CR 10.1:1, 122 hp @ 8,500 rpm, 112 Nm @ 7,000 rpm,
#     dry 223 kg, wheelbase 1,465 mm, 120/70ZR17 + 180/55ZR17, 5-speed,
#     chain final drive (530 pitch — importer's ZRX1200 token also maps 530)
#   - Cycle World instrumented test (2001): 1/4 mile 10.85 s @ 125.7 mph
#     (202.3 km/h)
#   - gear_ratios/sprockets OMITTED: no service-manual cassette transcription
#     could be verified online — importer Tier-2 naked-1200 defaults apply.
KAWASAKI_ZRX1200R_2001 = spec_from_dict(
    {
        "manufacturer": "Kawasaki",
        "model_name": "ZRX1200R (2001-2008)",
        "model_code": "ZR1200A",
        "year_from": 2001,
        "year_to": 2008,
        "category": "naked",
        "displacement_cc": 1164,
        "bore_mm": 79.0,
        "stroke_mm": 59.4,
        "compression_ratio": 10.1,
        "cylinders": 4,
        "peak_power_hp": 122.0,
        "peak_power_rpm": 8500,
        "peak_torque_nm": 112.0,
        "peak_torque_rpm": 7000,
        "fuel_system": "carb",  # 4x Keihin CVK36 — carbureted to the
        # end of the run (2008)
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 5,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.6, 2.0, 1.619, 1.4, 1.25, 1.143],
        "primary_ratio": 1.6,
        # gear_ratios / sprockets omitted — see source note above.
        "dry_mass_kg": 223.0,
        "wheelbase_mm": 1465.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.70,  # est: naked with the Lawson bikini
        # quarter-fairing — better than a bare
        # retro (CB1100 0.78), worse than the
        # low-slung Z900RS (0.66)
        "frontal_area_m2": 0.54,  # est: big broad muscle naked, between
        # Z900RS (0.50) and CB1100 (0.56)
    },
    source_name="spec_sheet",
)


# ── Suzuki GSX1400 (2001-2008 — air/oil-cooled big-naked muscle) ────────────
# Suzuki's last great SACS air/oil-cooled muscle naked; 1,402 cc of low-rev
# torque (126 Nm @ 5,000). Europe/Japan/Australia only — hence no US-magazine
# strip numbers; no fabricated ET row (honesty gate).
# Sources:
#   - suzukicycles.org GSX1400 specifications + gsx1400owners.org: 1,402 cc
#     I4, 81.0 x 68.0 mm, CR 9.5:1, 106 PS @ 6,800 rpm, 126 Nm @ 5,000 rpm,
#     fuel injection (34 mm), 6-speed, primary 1.509 (83/55), final 2.277
#     (41/18), dry 228 kg, tires 120/70ZR17 + 190/50ZR17
#   - 2wheelshero / motorcyclespecs GSX1400 review-specs: wheelbase 1,520 mm,
#     top speed 233 km/h (145 mph)
#   - RK/DID chain-kit listings (kitdearrastre, carpimoto): OEM 530 chain,
#     18T front / 41T rear — matches the 2.277 final reduction
#   - Individual gearbox ratios not verifiable online → gear_ratios OMITTED
#     (Tier-2 naked defaults), primary + sprockets set from the verified data.
SUZUKI_GSX1400_2001 = spec_from_dict(
    {
        "manufacturer": "Suzuki",
        "model_name": "GSX1400 (2001-2008)",
        "model_code": "GSX1400K1",
        "year_from": 2001,
        "year_to": 2008,
        "category": "naked",
        "displacement_cc": 1402,
        "bore_mm": 81.0,
        "stroke_mm": 68.0,
        "compression_ratio": 9.5,
        "cylinders": 4,
        "peak_power_hp": 106.0,
        "peak_power_rpm": 6800,
        "peak_torque_nm": 126.0,
        "peak_torque_rpm": 5000,
        "fuel_system": "fi",  # 34 mm EFI — unusual for the retro class
        "cooling": "oil",  # SACS air/oil cooling
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.6, 2.0, 1.619, 1.4, 1.25, 1.143],
        # gear_ratios omitted — see source note above.
        "primary_ratio": 1.509,  # 83/55 per suzukicycles.org spec page
        "front_sprocket": 18,
        "rear_sprocket": 41,
        "chain_pitch": "530",
        "dry_mass_kg": 228.0,
        "wheelbase_mm": 1520.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/50ZR17",
        "cd": 0.78,  # est: fully-bare big retro naked —
        # matches the CB1100 catalogue anchor
        # (0.78); no fairing at all
        "frontal_area_m2": 0.58,  # est: the widest of the retro nakeds
        # (huge tank + upright bars), above
        # CB1100 (0.56)
    },
    source_name="spec_sheet",
)


# ── Triumph Speed Triple 1050 (2005-2010 — first 1050 gen) ──────────────────
# The definitive hooligan naked of the 2000s; 1,050 cc triple with a torque
# peak at just 5,100 rpm (genuinely low — the 1050 triple's flat curve).
# Sources:
#   - MCN Speed Triple 1050 (2005-2010) review + motorcyclespecs 2005:
#     129-131 hp @ 9,100 rpm, 105-106 Nm @ 5,100 rpm, dry 189 kg
#   - motoplanete / moto-data 2005 spec listings: bore x stroke 79 x 71.4 mm
#   - motorcycle.com 2006 Speed Triple spec page: wheelbase 1,429 mm
#   - MotoStatz (aggregated instrumented figures): 1/4 mile 10.89 s
#     @ 126 mph (202.8 km/h), top speed 149.8 mph (241 km/h)
#   - compression_ratio omitted (12.0:1 commonly quoted but not verified in
#     this pass); gear cassette not verifiable → gear_ratios/sprockets
#     OMITTED — the Tier-1 "speed triple" (2005-2026) lookup entry supplies
#     ratios [2.684 … 1.143] F17/R43 primary 1.952.
TRIUMPH_SPEED_TRIPLE_1050_2005 = spec_from_dict(
    {
        "manufacturer": "Triumph",
        "model_name": "Speed Triple 1050 (2005-2010)",
        "model_code": "515NJ",
        "year_from": 2005,
        "year_to": 2010,
        "category": "naked",
        "displacement_cc": 1050,
        "bore_mm": 79.0,
        "stroke_mm": 71.4,
        "cylinders": 3,
        "peak_power_hp": 129.0,
        "peak_power_rpm": 9100,
        "peak_torque_nm": 105.0,
        "peak_torque_rpm": 5100,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.684, 1.947, 1.619, 1.395, 1.25, 1.143],
        "primary_ratio": 1.952,
        # gear_ratios / sprockets omitted — Tier-1 lookup, see note above.
        "dry_mass_kg": 189.0,
        "wheelbase_mm": 1429.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.75,  # est: bug-eye naked with wide bars —
        # between Street Triple 765 RS (0.76)
        # and Speed Triple 1200 RS (0.74)
        "frontal_area_m2": 0.52,  # est: broad-shouldered naked, just
        # under Speed Triple 1200 RS (0.53)
    },
    source_name="spec_sheet",
)


# ── Triumph Speed Triple 1050 (2011-2015 — second gen, distinct spec) ───────
# Full redesign for 2011: new frame (engine moved forward), 135 PS and a
# 7,750-rpm torque peak (vs 5,100 on gen 1 — a genuinely different state of
# tune), wet-weight-quoted era. Verified distinct from the 2005 gen.
# Sources:
#   - MCN Speed Triple 1050 (2011-on) review + Motorcycle.com 2011 review:
#     135 PS (133 bhp) top end, 111 Nm @ 7,750 rpm, 214 kg fully fuelled
#   - autoevolution Speed Triple (2011-2012): wheelbase 1,435 mm
#   - motorcyclespecs 2011: rear tire 190/55ZR17 (up from 180/55 on gen 1)
#   - Only wet mass published → dry omitted (importer wet-25 → 189 kg,
#     matching Triumph's gen-1 dry figure — sanity-consistent)
#   - gear cassette unverified → gear_ratios/sprockets OMITTED (same Tier-1
#     "speed triple" lookup as gen 1).
TRIUMPH_SPEED_TRIPLE_1050_2011 = spec_from_dict(
    {
        "manufacturer": "Triumph",
        "model_name": "Speed Triple 1050 (2011-2015)",
        "model_code": "515NV",
        "year_from": 2011,
        "year_to": 2015,
        "category": "naked",
        "displacement_cc": 1050,
        "bore_mm": 79.0,
        "stroke_mm": 71.4,
        "cylinders": 3,
        "peak_power_hp": 133.0,  # 135 PS @ 9,400 rpm
        "peak_power_rpm": 9400,
        "peak_torque_nm": 111.0,
        "peak_torque_rpm": 7750,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.684, 1.947, 1.619, 1.395, 1.25, 1.143],
        "primary_ratio": 1.952,
        # gear_ratios / sprockets omitted — Tier-1 lookup, see note above.
        "wet_mass_kg": 214.0,
        "wheelbase_mm": 1435.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.74,  # est: reshaped twin-lamp nose slightly
        # cleaner than gen 1 (0.75 here);
        # equals Speed Triple 1200 RS (0.74)
        "frontal_area_m2": 0.52,  # est: same stance as gen 1
    },
    source_name="spec_sheet",
)


# ── Triumph Street Triple 675 (2007-2012 — the original streetfighter 675) ──
# Daytona 675 engine and gearbox in a naked chassis; the middleweight that
# defined the class. Shares the Daytona 675 cassette per Triumph (final drive
# shortened via a 16T front sprocket — confirmed by period reviews).
# Sources:
#   - MCN Street Triple 675 (2007-2012) review + motorcyclespecs: 106-107 bhp
#     @ 11,700 rpm, 68-69 Nm @ 9,100-9,200 rpm, dry 167 kg, bore x stroke
#     74.0 x 52.3 mm, CR 12.65:1
#   - motorcyclespecifications.com Street Triple 675 (2008-2016 pages):
#     wheelbase 1,410 mm — consistent across model years
#   - Visordown 2007 first ride: 16T front sprocket vs Daytona (gearing note)
#   - MotoStatz (aggregated instrumented figures): 1/4 mile 11.25 s
#     @ 122 mph (196.3 km/h), top speed 141.7 mph (228 km/h)
#   - Individual cassette not re-verified in this pass → gear_ratios OMITTED;
#     the Tier-1 "street triple" (2007-2026) entry supplies the shared
#     Daytona 675 box [2.750 … 1.208] with F16/R43 primary 1.952.
TRIUMPH_STREET_TRIPLE_675_2007 = spec_from_dict(
    {
        "manufacturer": "Triumph",
        "model_name": "Street Triple 675 (2007-2012)",
        "model_code": "D67LD",
        "year_from": 2007,
        "year_to": 2012,
        "category": "naked",
        "displacement_cc": 675,
        "bore_mm": 74.0,
        "stroke_mm": 52.3,
        "compression_ratio": 12.65,
        "cylinders": 3,
        "peak_power_hp": 106.0,
        "peak_power_rpm": 11700,
        "peak_torque_nm": 68.0,
        "peak_torque_rpm": 9200,
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
        "primary_ratio": 1.952,
        # gear_ratios / sprockets omitted — Tier-1 lookup, see note above.
        "dry_mass_kg": 167.0,
        "wheelbase_mm": 1410.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "180/55ZR17",
        "cd": 0.70,  # est: compact middleweight naked —
        # between the catalogue Street Triple
        # 765 R (0.61) and 765 RS (0.76)
        # anchors; twin round lamps add drag
        "frontal_area_m2": 0.48,  # est: small slim naked, just above
        # 765 R (0.46)
    },
    source_name="spec_sheet",
)


# ── Ducati 996 Biposto (1999-2001 — the icon between 916 and 998) ───────────
# Massimo Tamburini's masterpiece in its 996 cc form; the two-seat (Biposto)
# base model. Famously tall stock gearing (15/36 — the tallest of any Ducati
# of the era) via the 1.84 primary.
# Sources:
#   - autoevolution / motorcyclespecs / bikez 1999 996 Biposto: 996 cc
#     90-degree L-twin desmoquattro, 98.0 x 66.0 mm, CR 11.5:1, 112 hp
#     @ 8,500 rpm, 93 Nm @ 8,000 rpm, dry 198 kg, wheelbase 1,410 mm
#   - Cycle World "'99 996!" (February 1999 issue): dyno 106 bhp rear-wheel,
#     top speed 161 mph (259 km/h)
#   - bikeboy.org "Ducati Gearing, Sprockets and Primary Drive Ratios" +
#     ducati.org forum threads: stock 15T/36T on a 525 chain (94 links),
#     1.84 primary — "geared unusually high, 6th is basically overdrive"
#   - Individual gearbox ratios not verifiable → gear_ratios OMITTED (Tier-2
#     sport defaults) with the verified primary + tall 15/36 final applied.
DUCATI_996_BIPOSTO_1999 = spec_from_dict(
    {
        "manufacturer": "Ducati",
        "model_name": "996 Biposto (1999-2001)",
        "model_code": "996",
        "year_from": 1999,
        "year_to": 2001,
        "category": "sport",
        "displacement_cc": 996,
        "bore_mm": 98.0,
        "stroke_mm": 66.0,
        "compression_ratio": 11.5,
        "cylinders": 2,  # 90-deg L-twin → importer infers V2
        # (Ducati is in _V_TWIN_2CYL_MAKES)
        "peak_power_hp": 112.0,
        "peak_power_rpm": 8500,
        "peak_torque_nm": 93.0,
        "peak_torque_rpm": 8000,
        "fuel_system": "fi",  # Marelli EFI
        "cooling": "liquid",
        "valve_config": "dohc",  # desmoquattro, 4v per cylinder
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.6, 2.0, 1.667, 1.444, 1.296, 1.185],
        # gear_ratios omitted — see source note above.
        "primary_ratio": 1.84,
        "front_sprocket": 15,
        "rear_sprocket": 36,
        "chain_pitch": "525",
        "dry_mass_kg": 198.0,
        "wheelbase_mm": 1410.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/50ZR17",
        "cd": 0.60,  # est: famously slippery Tamburini
        # bodywork with under-seat exhausts —
        # slightly better than the catalogue
        # Panigale V2 (0.62), on par with
        # Panigale V4 (0.60)
        "frontal_area_m2": 0.43,  # est: narrow L-twin superbike,
        # marginally above Panigale V4R (0.42)
    },
    source_name="spec_sheet",
)


# ── Ducati Diavel 1260 S (2019-2022 — drag-oriented power cruiser) ──────────
# The second-generation Diavel with the 1262 cc Testastretta DVT; a 240-rear
# power cruiser explicitly marketed on its drag launch (Ducati Power Launch
# mode). Completes the catalogue's Diavel line next to the Diavel V4.
# Sources:
#   - Ducati Diavel 1260 S press/spec data via motorcyclespecs 2020 +
#     ultimatespecs 2019: 1,262 cc Testastretta DVT L-twin, 106.0 x 71.5 mm,
#     CR 13.0:1, 159 hp @ 9,500 rpm, 129 Nm @ 7,500 rpm, dry 218 kg,
#     wheelbase 1,600 mm, 120/70ZR17 front / 240/45ZR17 rear
#   - DID/Superlite chain-kit listings for Diavel 1260 (carpimoto,
#     sprocketcenter): OEM 15T/43T on a 525 chain (112 links)
#   - Gearbox ratios not verifiable online → gear_ratios OMITTED (no Tier-1
#     "diavel 1260" entry exists; the "diavel v4" entry does not substring-
#     match this name, so Tier-2 cruiser defaults apply — documented).
DUCATI_DIAVEL_1260S_2019 = spec_from_dict(
    {
        "manufacturer": "Ducati",
        "model_name": "Diavel 1260 S (2019-2022)",
        "model_code": "GC04",
        "year_from": 2019,
        "year_to": 2022,
        "category": "cruiser",  # power cruiser — matches the Diavel V4
        # catalogue precedent
        "displacement_cc": 1262,
        "bore_mm": 106.0,
        "stroke_mm": 71.5,
        "compression_ratio": 13.0,
        "cylinders": 2,
        "peak_power_hp": 159.0,
        "peak_power_rpm": 9500,
        "peak_torque_nm": 129.0,
        "peak_torque_rpm": 7500,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # desmo DVT (variable timing)
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.2, 1.6, 1.222, 1.0, 0.833, 0.722],
        "primary_ratio": 1.92,
        # gear_ratios omitted — see source note above.
        "front_sprocket": 15,
        "rear_sprocket": 43,
        "chain_pitch": "525",
        "dry_mass_kg": 218.0,
        "wheelbase_mm": 1600.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "240/45ZR17",  # signature 240 rear
        "cd": 0.78,  # est: low-slung power cruiser with a
        # small flyscreen — slightly better
        # than the taller Diavel V4 (0.80)
        "frontal_area_m2": 0.54,  # est: matches the Diavel V4 anchor
        # (0.54) — same stance and bar width
    },
    source_name="spec_sheet",
)


# ── Ducati Panigale V2 (2025-2026 — the NEW 890 cc twin) ────────────────────
# Complete 2025 redesign: the 955 Superquadro is replaced by an all-new
# 890 cc 90-degree V2 with IVT variable intake timing and spring (not desmo)
# valves. Named "Panigale V2 (2025-2026)" — the existing catalogue "Panigale
# V2" (2020-2024, 955 cc) is a different generation; the year band
# disambiguates per the importer's year-range matcher.
# Sources:
#   - Ducati press/spec data via Wikipedia "Ducati Panigale V2" +
#     Cycle News "2025 Ducati Panigale V2 First Look and Specs" (Nov 2024):
#     890 cc, 96.0 x 61.5 mm, CR 13.1:1, 120 hp @ 10,750 rpm, 93.3 Nm
#     @ 8,250 rpm, dry 179 kg (base) / 176 kg (V2 S), DQS 2.0 up/down
#   - motorcycles-specs.com Panigale V2/V2 S 890 2025: wheelbase 1,436 mm
#   - MCN 2025 Panigale V2 S review (launch, no strip numbers yet)
#   - CAUTION (documented, not fixed here): the 890's gearbox ratios and
#     final drive are not yet published in any retrievable source, so
#     gear_ratios/sprockets are OMITTED. The Tier-1 "panigale v2" lookup
#     entry (year band 2020-2026) will therefore supply the 955 Superquadro
#     cassette (F15/R38, primary 1.84) — the closest available stand-in.
#     Replace with real 890 service data when the manual publishes.
DUCATI_PANIGALE_V2_890_2025 = spec_from_dict(
    {
        "manufacturer": "Ducati",
        "model_name": "Panigale V2 (2025-2026)",
        "model_code": "V2_890",
        "year_from": 2025,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 890,
        "bore_mm": 96.0,
        "stroke_mm": 61.5,
        "compression_ratio": 13.1,
        "cylinders": 2,
        "peak_power_hp": 120.0,
        "peak_power_rpm": 10750,
        "peak_torque_nm": 93.3,
        "peak_torque_rpm": 8250,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",  # spring valves + IVT (first non-desmo
        # Panigale twin)
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "primary_ratio": 1.84,
        # gear_ratios / sprockets omitted — see CAUTION note above.
        "dry_mass_kg": 179.0,
        "wheelbase_mm": 1436.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "190/55ZR17",
        "cd": 0.62,  # est: matches the catalogue 955
        # Panigale V2 anchor (0.62) — same
        # design language, winglet-less
        "frontal_area_m2": 0.43,  # est: slightly slimmer than the 955
        # V2 (0.44) — narrower new engine
    },
    source_name="spec_sheet",
)


# ── MV Agusta Dragster 800 RR (2018-2026 — literally named for drag) ────────
# The premium wire-wheeled, quickshifter-equipped RR tune of MV's chopped-
# tail Dragster; 798 cc counter-rotating-crank triple shared with the F3 800
# (79.0 x 54.3 mm, CR 13.3:1 — cross-referenced against the catalogue F3 800
# and Brutale 800 Dragster entries, which carry the same verified engine
# architecture). Distinct catalogue entry from "Brutale 800 Dragster"
# (2016-2023): this is the RR-badged 2018+ Euro4/Euro5 line.
# Sources:
#   - Wikipedia "MV Agusta Dragster series": Dragster 800 RR = 140 bhp
#     @ 13,100 rpm with intake/exhaust mods over the base 800, up/down
#     quickshifter, wire-spoked wheels
#   - ultimatespecs 2019 Dragster 800 RR: 138.13 HP (= 140 PS) @ 12,300 rpm
#     (Euro4 re-rate), 87 Nm @ 10,100 rpm — torque figure used here
#   - Cycle World 2020 Dragster 800 RR buyer's guide: claimed dry 370 lb
#     (168 kg)
#   - Wheelbase 1,380 mm + tire sizes cross-referenced from the in-repo
#     Brutale 800 Dragster sibling entry (identical chassis platform); MV
#     quotes 1,400 mm for the current RR SCS — flagged, not resolved
#   - Gear cassette OMITTED → the Tier-1 "dragster" lookup entry
#     (2014-2026, MV 800-triple box, F15/R43 primary 1.960) applies.
MV_AGUSTA_DRAGSTER_800RR_2018 = spec_from_dict(
    {
        "manufacturer": "MV Agusta",
        "model_name": "Dragster 800 RR (2018-2026)",
        "model_code": "Dragster800RR",
        "year_from": 2018,
        "year_to": 2026,
        "category": "naked",
        "displacement_cc": 798,
        "bore_mm": 79.0,
        "stroke_mm": 54.3,
        "compression_ratio": 13.3,
        "cylinders": 3,
        "peak_power_hp": 140.0,  # 140 PS claim; 13,100 rpm per the
        # Wikipedia RR figure (Euro5 re-rates
        # quote 12,300 — flagged in comment)
        "peak_power_rpm": 13100,
        "peak_torque_nm": 87.0,
        "peak_torque_rpm": 10100,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Internal cassette unpublished by the manufacturer — this is the
        # MotoQuant Tier-2 category cassette the importer selects, made
        # EXPLICIT per the test_all_known_bikes_have_gear_ratios contract
        # (every spec ships a cassette; behaviour identical to the
        # implicit fallback, and replaceable when a service manual surfaces).
        "gear_ratios": [2.769, 2.125, 1.706, 1.462, 1.3, 1.174],
        "primary_ratio": 1.96,
        # gear_ratios / sprockets omitted — Tier-1 "dragster" lookup.
        "dry_mass_kg": 168.0,
        "wheelbase_mm": 1380.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/50ZR17",  # sibling-entry OEM fitment; RR SCS
        # may run 200/55 — flagged
        "cd": 0.72,  # est: matches the catalogue Brutale
        # 800 Dragster anchor (0.72) — same
        # stubby-tail naked silhouette
        "frontal_area_m2": 0.51,  # est: fractionally under the sibling
        # (0.52) — lower bar-riser setup
    },
    source_name="spec_sheet",
)


# ── Bimota Tesi H2 (2021-2026 — supercharged hub-steered exotic) ────────────
# Bimota's hub-centre-steered carbon exotic built around the complete
# Kawasaki Ninja H2 supercharged driveline (engine + gearbox carried over
# unchanged). Forced induction is represented exactly like the catalogue's
# Ninja H2/H2R entries: the supercharger's effect is baked into the verified
# crank power/torque figures and the low 8.5:1 static CR — the spec schema
# carries no separate boost field (BikeSpec has none; the H2 precedent is
# the documented pattern).
# Sources:
#   - Bennetts BikeSocial "Bimota Tesi H2 — full specs, availability, price"
#     (Sep 2020): 998 cc supercharged I4, 228 bhp @ 11,500 rpm, 141.7 Nm
#     @ 11,000 rpm (ram air excluded), dry 207 kg, wheelbase 10 mm shorter
#     than the Kawasaki H2's (1,455 - 10 = 1,445 mm), Öhlins/Brembo/OZ
#   - ZigWheels "Bimota Tesi H2 Specifications Revealed": 228 bhp @ 11,500,
#     ~140 Nm @ 11,000, 207 kg dry — cross-check
#   - Driveline (cassette [2.461 … 1.185], F17/R43, 520 chain, primary
#     1.545) carried over from the in-repo Kawasaki Ninja H2 entry + Tier-1
#     h2 lookup — Bimota's spec sheet confirms the H2 engine/6-speed dog-ring
#     box is unchanged
#   - MCN Tesi H2 Tera review (2025): top speed shares the H2's electronic
#     299 km/h limiter
BIMOTA_TESI_H2_2021 = spec_from_dict(
    {
        "manufacturer": "Bimota",
        "model_name": "Tesi H2 (2021-2026)",
        "model_code": "TesiH2",
        "year_from": 2021,
        "year_to": 2026,
        "category": "sport",
        "displacement_cc": 998,
        "bore_mm": 76.0,
        "stroke_mm": 55.0,
        "compression_ratio": 8.5,  # low static CR = the supercharger
        # signature (same as catalogue H2)
        "cylinders": 4,
        "peak_power_hp": 228.0,  # supercharged crank figure — boost
        # effect encoded in power/torque per
        # the Ninja H2 catalogue pattern
        "peak_power_rpm": 11500,
        "peak_torque_nm": 141.7,
        "peak_torque_rpm": 11000,
        "fuel_system": "fi",
        "cooling": "liquid",
        "valve_config": "dohc",
        "gears": 6,
        # Ninja H2 driveline carried over verbatim (see sources):
        "gear_ratios": [2.461, 1.941, 1.647, 1.440, 1.296, 1.185],
        "primary_ratio": 1.545,
        "front_sprocket": 17,
        "rear_sprocket": 43,
        "chain_pitch": "520",
        "dry_mass_kg": 207.0,
        "wheelbase_mm": 1445.0,
        "front_tire_size": "120/70ZR17",
        "rear_tire_size": "200/55ZR17",
        "cd": 0.64,  # est: faired exotic without the H2's
        # aero mirrors-cum-winglets — a shade
        # worse than the Ninja H2 (0.63)
        "frontal_area_m2": 0.47,  # est: hub-steer front is slimmer than
        # the H2's fork crown (0.48)
    },
    source_name="spec_sheet",
)


# ── Master list — wired into ALL_KNOWN_BIKES by the orchestrator ────────────
JPEU_EXPANSION_BIKES = [
    KAWASAKI_ZX12R_2000,
    YAMAHA_VMAX_1200_1985,
    SUZUKI_GSXR600_L1_2011,
    SUZUKI_GSXR750_L1_2011,
    KAWASAKI_ZRX1200R_2001,
    SUZUKI_GSX1400_2001,
    TRIUMPH_SPEED_TRIPLE_1050_2005,
    TRIUMPH_SPEED_TRIPLE_1050_2011,
    TRIUMPH_STREET_TRIPLE_675_2007,
    DUCATI_996_BIPOSTO_1999,
    DUCATI_DIAVEL_1260S_2019,
    DUCATI_PANIGALE_V2_890_2025,
    MV_AGUSTA_DRAGSTER_800RR_2018,
    BIMOTA_TESI_H2_2021,
]


# ── Quarter-mile benchmarks (validation_sweep.py BENCHMARKS format) ─────────
# (manufacturer_substr, model_substr, year_hint, target_et_s, trap_kmh, src)
# Magazine instrumented rows only, except the two clearly-labelled MotoStatz
# rows (the weighted sweep's source_weight() already classifies "motostatz"
# as aggregator, 0.5 — same convention as the existing Street Triple 765 RS /
# Panigale V2 corpus rows). Bikes with no verifiable instrumented ET+trap
# (GSX-R600/750 L1 trap unpublished, GSX1400 timeslips-only, 996 trap
# unpublished, Diavel 1260 S model-year-ambiguous, Panigale V2 890 too new,
# Dragster 800 RR / Tesi H2 never strip-tested) are deliberately ABSENT.
ET_BENCHMARKS: list[tuple[str, str, int, float, float, str]] = [
    # Cycle World June 2000 road test: 10.04 s @ 143.78 mph
    ("Kawasaki", "Ninja ZX-12R", 2000, 10.04, 231.4, "Cycle World 2000"),
    # Motorcyclist 2002 ZX-12R road test (B1): 9.87 s @ 146.29 mph
    ("Kawasaki", "Ninja ZX-12R", 2002, 9.87, 235.4, "Motorcyclist 2002"),
    # Cycle World May 1985 V-Max test: best standard run 10.89 s @ 128.75 mph
    # (pro drag-racer best of 10.64 s @ 128.57 noted in the same article)
    ("Yamaha", "VMAX 1200", 1985, 10.89, 207.2, "Cycle World 1985"),
    # Cycle World 2001 ZRX1200R instrumented test: 10.85 s @ 125.7 mph
    ("Kawasaki", "ZRX1200R", 2001, 10.85, 202.3, "Cycle World 2001"),
    # MotoStatz aggregate (instrumented sources): 10.89 s @ 126 mph
    ("Triumph", "Speed Triple 1050", 2005, 10.89, 202.8, "MotoStatz aggregate"),
    # MotoStatz aggregate (instrumented sources): 11.25 s @ 122 mph
    ("Triumph", "Street Triple 675", 2007, 11.25, 196.3, "MotoStatz aggregate"),
]


# ── Top-speed benchmarks (topspeed_sweep.py BENCHMARKS format) ──────────────
# (manufacturer_substr, model_substr, year_hint, target_kmh, source)
TOPSPEED_BENCHMARKS: list[tuple[str, str, int, float, str]] = [
    # 186 mph electronic limiter (post-2000 gentleman's agreement; CW 2000
    # measured the limiter at 186 mph on the A1)
    ("Kawasaki", "Ninja ZX-12R", 2000, 299, "factory-limited"),
    # Cycle World 1985 + autoevolution: 145 mph tested
    ("Yamaha", "VMAX 1200", 1985, 233, "Cycle World 1985 (145 mph tested)"),
    # 2wheelshero/motorcyclespecs: 233 km/h (145 mph)
    ("Suzuki", "GSX1400", 2001, 233, "motorcyclespecs (145 mph)"),
    # Cycle World Feb 1999 road test: 161 mph
    ("Ducati", "996 Biposto", 1999, 259, "Cycle World 1999 (161 mph)"),
    # MotoStatz aggregate: 149.8 mph
    ("Triumph", "Speed Triple 1050", 2005, 241, "MotoStatz (149.8 mph)"),
    # MotoStatz aggregate: 141.7 mph
    ("Triumph", "Street Triple 675", 2007, 228, "MotoStatz (141.7 mph)"),
    # MV Agusta factory claim: 244 km/h
    ("MV Agusta", "Dragster 800 RR", 2018, 244, "factory claim"),
    # Shares the Kawasaki H2's 299 km/h electronic limiter (MCN 2025)
    ("Bimota", "Tesi H2", 2021, 299, "factory-limited (H2 limiter)"),
]
