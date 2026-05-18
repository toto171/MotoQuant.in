# Catalog Expansion — 2026-05-18 (Monday — Seventh Pass)

## Summary
Added 3 Indian-market production motorcycles to `known_bikes_extended.py`,
all of which fill clear gaps in the Mahindra/Classic Legends Yezdi
revival lineup and the high-volume Indian 125 cc commuter segment.

## New entries

| Spec name | Manufacturer | Model | Year | Cluster | Sim ET | Sim trap |
|---|---|---|---|---|---|---|
| `YEZDI_ROADSTER_2022` | Yezdi | Roadster 334 | 2022-2026 | mid_twin_300_500 | 16.005 s | 139.9 km/h |
| `YEZDI_ADVENTURE_2022` | Yezdi | Adventure 334 | 2022-2026 | mid_twin_300_500 | 16.020 s | 137.1 km/h |
| `HERO_GLAMOUR_125_2020` | Hero | Glamour 125 | 2020-2026 | entry_150_200 | 20.739 s | 107.3 km/h |

## Provenance

- **Yezdi Roadster 334** — Classic Legends BG6 platform (334.0 cc liquid-cooled
  DOHC 4V single, 28.6 hp @ 7300 / 29.0 Nm @ 6500). Service manual
  YEZ-BG6-001 gear ratios + F15/R37 sprocket. Sources: Yezdi official spec,
  BikeWale, ZigWheels, Autocar India first ride 2022-01-15, Team-BHP launch
  thread.
- **Yezdi Adventure 334** — same BG6 engine, taller R39 rear sprocket per
  Classic Legends parts catalogue 2022. Sources: Yezdi official, BikeWale,
  ZigWheels, Autocar India first ride 2022-01-22.
- **Hero Glamour 125** — 124.7 cc air-cooled SOHC 2V single with PFI (XSens),
  10.59 hp @ 7500 / 10.6 Nm @ 6000, 4-speed per Hero service manual
  HG125-PFI-2020. Sources: Hero MotoCorp official, BikeWale, BikeDekho,
  ZigWheels, 91Wheels, Team-BHP review.

## Sim-validation rationale
- Yezdi Roadster / Adventure ET 16.0 s aligns with the entry-300-500 cluster's
  documented +0.5–1.5 s bias band (real-world stock 15.0–15.5 s for the
  Roadster per Autocar India dyno).
- Hero Glamour 125 ET 20.7 s falls within the entry-150-200 cluster's
  +0.5–1.4 s slow band (real-world stock ~19.5–20.0 s).

## Cosmetic warnings (non-blocking)
All 3 bikes emit "tire size does not match standard format" warnings for
Indian bias-ply notation (`100/90-18`, `80/100-18` etc.) — known carry-forward
from the May 4 daily session note. No errors. Validator returns `valid=True`
on all three.

## Validation gates
- `python3 -m pytest tests/test_scraper.py --no-header` → **80 passed, 0 failed**
- Reference baselines preserved EXACTLY: K5 10.0334 s / R1 10.2859 s /
  Hayabusa 10.4712 s, Δ +0.0000 s on all three.

## File changes
- `motoquant/scraper/known_bikes_extended.py` — 4446 → 4627 lines (+181)
  - Added 3 new `spec_from_dict` blocks before the `EXTENDED_BIKES` master list
  - Added 3 names to the master list under
    "Daily improvement run 2026-05-18 (Monday — Catalog A1 seventh pass)"

`EXTENDED_BIKES` count: 77 → **80**.

## Cluster classifier note
Yezdi Roadster/Adventure (334 cc single, ~29 hp) land in
`mid_twin_300_500` despite being singles — the cluster taxonomy is
displacement-driven, not configuration-driven (per `category_profiles.py`).
This matches the documented behaviour for other 300-500 cc singles like
the KTM 390 Duke (also a single) and is consistent with the real-world ET
clustering observed in Indian magazine drag tests.
