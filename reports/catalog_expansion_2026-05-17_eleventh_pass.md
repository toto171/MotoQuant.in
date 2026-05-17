# Catalog Expansion — 2026-05-17 (Sunday — Catalog A1 eleventh pass)

## Summary
Added 3 Indian-market commuter / commuter-sport gap-fills, focused on the
entry-150-200 cc cluster — all sub-cluster gaps that the prior 10 passes
left untouched and that fill out the TVS / Honda / Yamaha India lineup.

## Bikes added (all to `motoquant/scraper/known_bikes_extended.py`)

### 1. TVS Apache RTR 160 2V (2018-2026)
- **Engine:** 159.7 cc air-cooled SOHC 2-valve single, FI, 15.31 hp @ 8400, 13.9 Nm @ 7000
- **Drivetrain:** 5-spd, 14F/43R, 428 chain (TVS RTR 2V family service-manual cassette,
  shared with already-cataloged RTR 180 2V)
- **Chassis:** 131 kg dry, 1300 mm WB, 90/90-17 F / 110/80-17 R, Cd 0.81 / A 0.44 m²
- **Sources:** TVS official spec page, TVS owner manual PDF, ZigWheels,
  BikeWale, Times Bull review, BikeDekho
- **Why:** TVS's longest-running RTR commuter (2018-current), distinct
  platform from the already-cataloged oil-cooled 4V variant.
- **Smoke sim:** ET **17.983s** / trap **118.3 km/h** — within
  entry-150-200 cluster's documented +0.5–1.4s slow band.

### 2. Honda Unicorn 160 BS6 (2020-2026)
- **Engine:** 162.71 cc air-cooled SOHC 2-valve single, FI, 13.27 hp @ 7500, 14.58 Nm @ 5500
- **Drivetrain:** 5-spd, 15F/45R, 428 chain (Honda KP2A service-manual cassette,
  shared with already-cataloged CB Hornet 160R — only sprocket sizing differs)
- **Chassis:** 130 kg dry, 1336 mm WB, 80/100-17 F / 110/80-17 R, Cd 0.78 / A 0.43 m²
- **Sources:** Honda 2W India, BikeWale, ZigWheels, 91Wheels,
  2Wheelerspares OEM kit listing (15F/45R per Honda kit "128 15 45")
- **Why:** Same KP2A engine as Hornet but milder commuter tune + taller
  rear sprocket. Distinct product class.
- **Smoke sim:** ET **18.547s** / trap **113.7 km/h**.

### 3. Yamaha FZ-S FI V3 (2019-2026)
- **Engine:** 149 cc air-cooled SOHC 2-valve single, PGM-FI, 12.23 hp @ 7250, 13.3 Nm @ 5500
- **Drivetrain:** 5-spd, 14F/42R, 428 chain (Yamaha FZ 149 cc 5-speed cassette,
  shared FZ V2/V3 transmission per service-manual cross-ref)
- **Chassis:** 127 kg dry, 1330 mm WB, 100/80-17 F / 140/60-17 R, Cd 0.79 / A 0.44 m²
- **Sources:** Yamaha India spec page, Team-BHP, ZigWheels, BikeDekho,
  91Wheels, TheBikeJunction, Bikes24
- **Why:** Legacy "old FZ" SOHC engine (57x58mm) is distinct from the
  newer DOHC liquid-cooled engine in the 2021+ FZ-X.
- **Smoke sim:** ET **19.678s** / trap **110.4 km/h**.

## Validation

### Validator (`validate_spec`)
All 3 specs: `valid=True`, `errors=[]`. Two cosmetic warnings each
(Indian bias-ply tire-format notation `100/80-17` instead of
`100/80ZR17`) — same documented carry-forward as Hero Xtreme 200S 4V
in the May-4 entry. Open item: widen the scraper validator to accept
Indian bias-ply tire notation (already on the carry-forward list).

### Focused test subset
`test_scraper + test_validation + test_two_stroke + test_compatibility +
test_category_dispatch` = **193/193 passed in 13.12s**.

### Reference baselines (preserved EXACTLY)
- K5: 10.0334s (Δ +0.0000s)
- R1: 10.2859s (Δ +0.0000s)
- Hayabusa: 10.4712s (Δ +0.0000s)

## Catalog state
- `EXTENDED_BIKES` count: 54 → **57**
- File length: 2940 → 3122 lines (+182, well under file-write
  truncation threshold)

## Escalations to DISPATCH_INBOX.md
None. All three pass cleanly with cosmetic-only warnings.

## Carry-forward (unchanged from prior passes)
- (a) Widen scraper validator to accept Indian bias-ply `100/80-17`
      tire notation (queued for separate validator pass)
- (b) WS-A `bike_repo.create_model` year-suffix matching fix
- All prior carry-forwards from May-4 / earlier 5/17 passes.
