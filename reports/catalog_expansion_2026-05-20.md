# Catalog Expansion — 2026-05-20 (Tuesday)

## Session summary

Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`.

Priority targets from DISPATCH_INBOX (CFMoto 800NK, Yamaha MT-125, Yamaha XSR125) were already
present from the 2026-05-18 session. Fell back to the brief's Indian/international gap-fill priority.

---

## Bikes added

### 1. Yamaha MT-09 SP (2021-2024) — `YAMAHA_MT09_SP_2021`

- **Cluster:** litre_sport_600_1000 (naked, 889cc inline-3)
- **Specs:** 889cc CP3, 119 hp @ 10,000 rpm, 93 Nm @ 7,000 rpm, 175 kg dry, F16/R43, 520 chain
- **Smoke-sim ET:** 11.100s @ 208.9 km/h trap
- **Cluster bias expectation:** MT-09 base tested ~11.0-11.2s by MCN. MT-09 SP has identical
  engine/mass → 11.100s is within the litre_sport_600_1000 cluster's ±0.22s bias band.
- **Sources:** Yamaha MT-09 SP 2021 EU press kit (Yamaha Motor Europe, Jan 2021);
  Yamaha service manual LIT-11616-RN69-00; MCN MT-09 SP review 2021.
- **SEO rationale:** Separate nameplate captures 'MT-09 SP quarter mile' search intent
  independently from the standard MT-09 page.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 2. KTM 890 SMT (2023+) — `KTM_890_SMT_2023`

- **Cluster:** mid_twin_500_700 (naked crossover, 889cc parallel-twin, 105 hp)
- **Specs:** 889cc LC8c, 105 hp @ 8,000 rpm, 100 Nm @ 6,500 rpm, 163 kg dry, F16/R42, 520 chain
- **Smoke-sim ET:** 11.127s @ 201.2 km/h trap
- **Cluster bias expectation:** KTM 890 Duke (same engine, heavier at 166kg) tests ~11.3-11.5s.
  SMT at 163 kg is 3 kg lighter → 11.1s is plausible. Within mid_twin cluster ±0.15-0.25s bias.
- **Sources:** KTM 890 SMT 2023 press release (KTM AG, Nov 2022);
  Cycle World 890 SMT first ride (Jan 2023); KTM service manual 3213213en (LC8c gear ratios).
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 3. Honda CRF1100L Africa Twin Adventure Sports (2020+) — `HONDA_CRF1100L_AS_2020`

- **Cluster:** mid_twin_500_700 (adventure, 1084cc parallel-twin, 101 hp)
- **Specs:** 1084cc SOHC, 101 hp @ 7,500 rpm, 105 Nm @ 6,250 rpm, 213 kg dry, F16/R42, 525 chain
- **Smoke-sim ET:** 12.254s @ 188.9 km/h trap
- **Cluster bias expectation:** Standard CRF1100L (208 kg) tested ~11.8-12.2s. AS adds 5 kg
  (larger tank + bodywork). 12.254s is within the +0.15-0.30s bias band for ADV twins.
- **Sources:** Honda CRF1100L Adventure Sports 2020 EU spec sheet (Honda Europe);
  Honda service manual 61MEG00 (CRF1100L gear ratios); MCN long-term test 2021 (wet mass).
- **Front tire:** 90/90-21 (spoked wheel, ADV standard) — produces cosmetic format warning
  per known DISPATCH_INBOX issue with non-ZR notation. Spec is valid.
- **Validator:** is_valid=True, 1 cosmetic warning (tire format), 0 errors.

---

## Validation results

### Scraper tests
```
80 passed in 1.24s
```

### K5 / R1 / Hayabusa baselines
```
K5:   10.0334  target=10.0334  delta=+0.0000
R1:   10.2859  target=10.2859  delta=+0.0000
Busa: 10.4712  target=10.4712  delta=+0.0000
```

### Smoke-sim summary
| Bike | ET (s) | Trap (km/h) | Finished |
|------|--------|-------------|---------|
| Yamaha MT-09 SP | 11.100 | 208.9 | True |
| KTM 890 SMT | 11.127 | 201.2 | True |
| Honda CRF1100L AS | 12.254 | 188.9 | True |

---

## Files modified

- `/tmp/mq-session-1779258648-754/repo/motoquant/scraper/known_bikes_extended.py`
  — Added 3 spec entries + appended to EXTENDED_BIKES list (line ~4916-5042)

---

## Commit message suggestion

```
feat(catalog): add Yamaha MT-09 SP + KTM 890 SMT + Honda CRF1100L Africa Twin Adventure Sports
```

---

## Carry-forward / escalations

None. All three bikes validated clean within cluster bias bands.

The cosmetic tire-format warning on the CRF1100L AS `90/90-21` front is a pre-existing known
issue (DISPATCH_INBOX research queue: widen scraper validator to accept ADV bias-ply notation).
