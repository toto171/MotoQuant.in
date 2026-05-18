# Catalog Expansion — 2026-05-18 (Monday, Tenth Pass)

**Agent:** catalog-expansion (A1)
**Date:** 2026-05-18
**Previous catalog size:** 409 bikes
**New catalog size:** 412 bikes
**Bikes added this pass:** 3

---

## Bikes Added

### 1. KTM 890 Duke (2020-2023)
- **Spec source:** KTM official EU spec sheet (archived 2024-01) + Cycle World first ride review 2020
- **Engine:** 889cc LC8c parallel twin, DOHC liquid-cooled, 105 hp @ 8,000 rpm, 92 Nm @ 6,500 rpm
- **Gearbox:** 6-speed, Tier-1 entry "duke 890" in gear_ratios.py confirmed ([2.625, 1.941, 1.580, 1.346, 1.185, 1.071], F15/R42)
- **Dry mass:** 166 kg (3 kg lighter than 890 R at 169 kg)
- **Sim ET:** 11.093s @ 209.1 km/h trap — within mid-twin cluster bias band (MCN road test ~11.0s)
- **Cluster:** `mid_twin_500_700` / naked mid-cc
- **Rationale:** Distinct from the 890 R (121 hp vs 105 hp) already in catalog; popular sub-₹10L naked in India; Tier-1 gear data confirmed.

### 2. Honda CB500X (2019-2024)
- **Spec source:** Honda official CB500X EU spec sheet 2019+ + Honda service manual 61MFG00 + MCN CB500X long-term test 2019
- **Engine:** 471cc parallel twin, DOHC liquid-cooled, 47 hp @ 8,600 rpm, 43.2 Nm @ 6,500 rpm
- **Gearbox:** 6-speed, same cassette as CB500F (PC64 platform): [2.750, 1.857, 1.444, 1.200, 1.035, 0.925], F15/R41, 520-pitch
- **Dry mass:** 197 kg (heavier than CB500F at 189 kg due to adventure setup)
- **Front tire:** 110/80R19 (19-inch wheel — distinct from CB500F 17-inch)
- **Sim ET:** 14.009s @ 157.5 km/h trap — entry-twin range, physically plausible for 47 hp / 197 kg
- **Cluster:** `entry_200_300` (adjacent to CB500F class)
- **Rationale:** Adventure variant not previously in catalog; distinct mass + 19-inch wheel aero profile from CB500F; CB500X is one of Honda's best-selling middleweight adventure bikes globally.

### 3. Suzuki GSX-S750 (2015-2021, GSR750 platform)
- **Spec source:** Suzuki official GSX-S750 spec sheet 2017+ + Suzuki service manual 99500-36160-03E + Motorcycle Consumer News GSX-S750 road test Nov 2017 (ET 11.4s @ 194 km/h)
- **Engine:** 749cc inline-4 (GSXR750 K5/K6 derived, detuned), DOHC liquid-cooled, 114 hp @ 10,500 rpm, 81 Nm @ 9,000 rpm
- **Gearbox:** 6-speed, NEW cassette distinct from GSX-R750 K5/K6 per Suzuki service manual 99500-36160-03E: [2.615, 1.882, 1.500, 1.261, 1.103, 0.966], F16/R45, 520-pitch
- **Dry mass:** 193 kg
- **Sim ET:** 11.256s @ 208.8 km/h trap — MCN test 11.4s, sim within documented cluster bias band
- **Cluster:** `litre_sport_600_1000` (750cc naked)
- **Rationale:** Clear catalog gap — 749cc naked segment absent (GSX-R750 superbike present but not the street-naked derivative); direct SERP competitor to MT-07, Z750, CB750 Hornet class.

---

## Validation Gates

| Gate | Result |
|------|--------|
| `pytest tests/test_scraper.py` | 80 passed ✓ |
| `pytest tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py` | 91 passed ✓ |
| K5 baseline | 10.0334s (unchanged) ✓ |
| R1 baseline | 10.2859s (unchanged) ✓ |
| Hayabusa baseline | 10.4712s (unchanged) ✓ |
| KTM 890 Duke ET in [4.0, 26.0]s | 11.093s ✓ |
| Honda CB500X ET in [4.0, 26.0]s | 14.009s ✓ |
| Suzuki GSX-S750 ET in [4.0, 26.0]s | 11.256s ✓ |

---

## Notes

- No DISPATCH_INBOX escalations required — all three bikes have authoritative spec sources.
- CB500X 19-inch front wheel tire notation (110/80R19) will generate cosmetic tire-format warnings in the validator (adventure non-ZR notation) — same as the Hero Xtreme 200S 4V `100/80-17` carry-forward from May-4 session. Not a blocking issue.
- GSX-S750 gear ratios are from a distinct cassette (not inherited from GSX-R750 K5/K6); cited to Suzuki service manual for traceability.
- Catalog is now at 412 bikes (was 409 entering this pass).
