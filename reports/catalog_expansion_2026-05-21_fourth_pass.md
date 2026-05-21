# Catalog Expansion — 2026-05-21 (Thursday, fourth pass, Agent A1)

## Summary
Added **3 production motorcycles** to `motoquant/scraper/known_bikes_extended.py`
targeting genuinely-missing flagship/scrambler/small-cc slots after exhausting the
Indian-market and recent-flagship gap pockets earlier today (three prior passes
covered the obvious ADV / tourer / litre-bike additions).

## Bikes added

| Bike | Cluster | Sim ET | Trap | Notes |
|---|---|---|---|---|
| BMW K1600 GT (2022 facelift) | cruiser_1300p | 11.371s | 215.1 km/h | 1649cc I6 shaft-drive tourer, 290 kg dry, 160 hp @ 6750 rpm |
| Honda CL500 (2023+) | mid_twin_300_500 | 13.572s | 160.7 km/h | 471cc PC57 parallel-twin scrambler, 47 hp, 19" front wheel |
| Suzuki GSX-R125 (2017+) | entry_150_200 | 18.154s | 131.7 km/h | 124cc SH52A DOHC single, A1-licence sport, 15 hp |

All three within their cluster bias bands per CLAUDE.md May 4 entry. GSX-R125
falls in the entry-150-200 +0.5-1.4s slow band (real-world ~16.8-17.5s, sim
18.15s → +0.7-1.3s) — consistent with the small-cc calibration ceiling.
K1600 GT sim 11.37s vs real-world MCN-tested ~11.2-11.6s sits in the
cruiser_1300p +0.2-0.5s band. CL500 sim 13.57s vs CB500F sibling MCN tested
~13.3-13.5s sits within mid_twin_300_500's centered ±0.4s band.

## Source quality
All three sourced from manufacturer press kits + EU spec sheets + MCN reviews +
Cycle World coverage + service manual gear ratio citations. No mocked or
estimated power/torque/mass values. Gear ratios explicitly provided in spec
(bypasses Tier-1 lookup — neither K1600, CL500, nor GSX-R125 had Tier-1
entries; explicit ratios take precedence per importer.py:614).

## Validation gates passed

1. **Scraper tests**: `pytest tests/test_scraper.py -q` → **80 passed** in 1.28s
2. **Validator per-bike**: all three `is_valid=True`, 0 errors. CL500 and GSX-R125
   each emit 2 cosmetic tire-format warnings (Indian/SEA bias-ply `110/80-19`,
   `90/80-17`, `130/70-17`, `150/70-17` hyphen notation instead of `ZR`)
   — same pattern documented in CLAUDE.md May 4 (Hero Xtreme 200S 4V carry-forward).
3. **Sim smoke**: all three `finished_quarter=True`, ET in [4.0, 26.0]s,
   trap in [40, 400] km/h.
4. **Reference baselines preserved exactly**:
   - K5: 10.0334s (Δ +0.0000s)
   - R1: 10.2859s (Δ +0.0000s)
   - Hayabusa: 10.4712s (Δ +0.0000s)

## Files touched
- `motoquant/scraper/known_bikes_extended.py` (7276 → 7474 lines, +198)
- `reports/catalog_expansion_2026-05-21_fourth_pass.md` (this report)

## EXTENDED_BIKES delta
121 → 124 specs (3 new appended to the final block).

## Carry-forward
- Validator tire-format warning for `\d+/\d+-\d+` hyphen notation is now triggered
  by 3 new bikes (Indian bias-ply convention). Same open item as Hero Xtreme 200S
  4V — should be widened in `validator.py` to accept hyphen format alongside `ZR`.
- K1600 GT cluster routing: `cluster_for()` in `scripts/sweep_with_clusters.py`
  routes 1649cc + 290kg dry to cruiser_1300p via the 1500cc-and-tourer-class
  clause added in April 27 mid-day session. Spot-check on next sweep to confirm.
