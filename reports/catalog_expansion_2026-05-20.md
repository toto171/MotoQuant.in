# Catalog Expansion — 2026-05-20 (Wednesday, tenth pass)

## Summary
Added 2 production motorcycles to `motoquant/scraper/known_bikes_extended.py`,
filling (a) the BMW M-series adventure-sport gap (M 1000 XR, 210 hp flagship)
and (b) the Kawasaki Ninja 1000SX 2020+ generation gap (existing catalog ended
at 2019). Catalog count: **376 → 378 bikes**.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Notes |
|---|---|---|---|---|---|
| BMW M 1000 XR | 2024-2026 | `litre_sport_195p` | 10.224s | 252.8 | Within expected 10.0-10.8s band for 210 hp class |
| Kawasaki Ninja 1000SX | 2020-2026 | `litre_sport_600_1000` | 10.723s | 226.8 | MCN class benchmark ~10.6-11.2s; squarely in band |

All 2 sim ETs inside [4.0, 26.0]s and trap inside [40, 400] km/h gates.
K5/R1/Hayabusa reference baselines preserved EXACTLY (`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**BMW M 1000 XR** — BMW Motorrad press release "World premiere: the new BMW M
1000 XR." 2023-11-07 (bmwmotorrad.com); BMW M 1000 XR specification sheet 2024
(bmwmotorrad.com/en/models/sport/m1000xr/2024/specs); MCN first ride 2024;
Cycle World 2024 first ride; Bennetts 2024 confirming 226 kg kerb + 210 hp.
Gear ratios from BMW M 1000 R owner's manual 01498053618 (K67 6-speed unit
confirmed shared across M 1000 R / M 1000 RR / M 1000 XR per BMW press
release). Final drive F17/R47 per BMW M 1000 XR spec sheet.

**Kawasaki Ninja 1000SX** — Kawasaki Motors USA press release 2019-09-26
("2020 Kawasaki Ninja 1000SX Launched"); Kawasaki Ninja 1000SX spec sheet 2022
(kawasaki.com/en-us/motorcycle/ninja/ninja-1000sx/2022-ninja-1000sx/specs); MCN
review 2020; Cycle World first ride 2019; BikeWale spec table 2022. Gear ratios
from Kawasaki service manual ZXT00W 2020, section 11, table 11-9 — confirmed
identical to ZX1000G (2011-2019) unit via Kawasaki PN cross-reference.

## Physics/cluster analysis

**BMW M 1000 XR** (litre_sport_195p):
- 999cc K67 I4, 210 hp — same engine as M 1000 R (207 kg dry, ~10.1s sim ET).
- M 1000 XR is 213 kg dry + taller F17/R47 gearing (vs M 1000 R F17/R45).
- Extra mass + taller gearing produces 10.224s ET, within litre_sport_195p band.
- Trap 252.8 km/h consistent with 210 hp class at ISA conditions.
- Cluster bias band for litre_sport_195p: mean |Δ| ≈ 0.16s, bias −0.035s.

**Kawasaki Ninja 1000SX** (litre_sport_600_1000):
- 1043cc DOHC I4, 140 hp — same engine as Ninja 1000 ZX1000G (2011-2019).
- 2020+ SX is 221 kg dry (vs ~225 kg for older variant). Same cassette + drive.
- Sim ET 10.723s consistent with MCN/Cycle World tests (10.6-11.2s class range).
- Cluster bias band for litre_sport_600_1000: mean |Δ| ≈ 0.22s, bias −0.15s.

## Validation gates

- `python3 -m pytest tests/test_scraper.py` → **80 passed** (zero warnings on new entries)
- Baselines (drift < 0.001s):
  - K5: 10.0334s (target 10.0334, drift 0.0000s) ✓
  - R1: 10.2859s (target 10.2859, drift 0.0000s) ✓
  - Hayabusa: 10.4712s (target 10.4712, drift 0.0000s) ✓
- Import batch: imported=2 / errors=0

## Candidates researched but not added

- **KTM 990 Duke (2024)**: New LC8e 947cc parallel twin. Could not source Tier-1
  gear ratios for the new gearbox (the "super duke 990" Tier-1 in gear_ratios.py
  covers the 2005-2013 LC8 V-twin — a completely different engine). Skipped per
  CLAUDE.md constraint against fabricating gear ratios for Tier-1 candidates.

- **Kawasaki Eliminator 500 (2023)**: Same bike as Eliminator 450 in different
  markets — the global "Eliminator" is the BR450 (451cc EX500P). Eliminator 450
  already in catalog; no distinct 500cc variant to add.

- **Ducati Panigale V4 SP2 (2022+)**: Mass delta from standard V4 is only ~3 kg
  (BST carbon wheels). Panigale V4 and V4 2025 both already cataloged.
  Insufficient differentiation to justify the entry.

## Open carry-forward

- KTM 990 Duke (2024): add when LC8e Tier-1 gear ratios sourced from the 2024
  service manual (ktm.com tech docs or a teardown report with PN cross-reference).
- No new dispatch escalations.
