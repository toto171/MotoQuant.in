# Catalog Expansion 2026-05-31 (Sunday)

## Bikes added (3)

1. **Aprilia Tuono 457 (2025-2026)** — Indian-market mid-twin naked sibling of RS 457. 457.3 cc parallel twin / 47.6 hp / 43.5 Nm. F15/R43, 520 chain, 6-speed cassette. Kerb 159 kg (dry 148). Targets KTM 390 Duke / MT-03 segment. Sources: Aprilia press kit Nov 2024 EICMA, MCN first-ride Jan 2025, Cycle World Feb 2025, Aprilia service manual TUO457-EU.
2. **BMW F 900 GS (2024-2026)** — 2024 mid-ADV refresh, replaces F 850 GS. 895 cc parallel twin / 105 hp / 93 Nm. F16/R41, 525 chain, 21"/17" spoke pair. Kerb 219 kg (dry 198, -14 kg vs F 850 GS). Sources: BMW Motorrad press kit Sep 2023, MCN Feb 2024, Cycle World Apr 2024, BMW service manual 0K01-K81.
3. **CFMoto 675SR-R (2024-2026)** — CFMoto's first inline-triple flagship sport. 675 cc DOHC triple (76.0 × 49.6 mm) / 95 hp / 68 Nm. F15/R45, 520 chain. Kerb 198 kg (dry 186). Daytona 660 / Trident 660 competitor. Sources: CFMoto press kit Nov 2023 EICMA, MCN May 2024, Cycle World Aug 2024, CFMoto service manual CF800-3US.

## Validation

- `python3 -m pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py` → **200/200 passed in 11.80s**
- Reference baselines preserved (postflight will re-verify K5/R1/Hayabusa).
- Smoke sim results (default Aamby Valley ISA):
  - Aprilia Tuono 457: ET=13.160s, trap=172.9 km/h, 60ft=2.416s — within mid_twin_300_500 cluster +0.5s bias band
  - BMW F 900 GS: ET=12.083s, trap=193.5 km/h, 60ft=2.353s — within mid_twin_500_700 cluster bias band
  - CFMoto 675SR-R: ET=11.323s, trap=214.4 km/h, 60ft=2.205s — within litre_sport_600_1000 cluster bias band

## DB re-seed

- `python3 -m motoquant.run import --known-bikes` returned `Imported: 499, Errors: 0, Total: 799` (was 796 → +3 net).
- Confirmed via `SELECT model_name LIKE` for each new entry. Note: Tuono 457 now has 2 entries (one prior 2024 entry sat in DB; ours is 2025-2026 distinct row). Year-suffix-bearing `model_name` shows the documented WS-A April 27 hygiene quirk but no FK errors raised.

## Files touched

- `motoquant/scraper/known_bikes_extended.py` — 3 new spec blocks (+222 lines) + EXTENDED_BIKES list updated
- `motoquant.db` — re-seeded (+3 bike_models rows, tire_fitments rebuilt to 1487)
- `reports/catalog_expansion_2026-05-31.md` — this file

## Notes / Carry-forward

- Tuono 457 prior duplicate row hints existing DB entry from earlier session — both kept; no constraint violation. Worth a future dedup pass that strips year-suffix from `model_name` before upsert (the long-standing `bike_repo.create_model` carry-forward).
- No high-priority research escalations queued.
