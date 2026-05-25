# Benchmark Import — 2026-05-25 (Eighth Pass / Null Delivery)

**Agent:** benchmark-import (A3, session 1779741032-639)
**Date:** 2026-05-25

---

## Summary

**Zero new benchmarks added.** This is a defensible null delivery — the
BENCHMARKS list has been exhaustively worked over by seven prior passes in
this same session (2026-05-24 and 2026-05-25), growing from ~74 to 108
entries. The remaining unbenchmarked bikes either lack instrumented published
data or were already investigated and explicitly rejected by earlier passes.

BENCHMARKS count: **108 (unchanged)**.

Reference baselines unchanged: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s.

---

## Why No New Adds

### 1. Prior passes exhausted the primary sources

The seven prior passes in this session queried MotoStatz, Cycle World,
Sport Rider, MCN, and MotorBikeCatalog. They added 20+ entries and
explicitly investigated and rejected:

| Bike | Reason for rejection |
|------|---------------------|
| Speed Triple 1200 RS | No instrumented test found (Cycle World / MotoStatz / MCN checked) |
| Honda CB1000R | Only ProfessCars/MotorBikeCatalog calculated estimates — no Dragy/timing-strip |
| Kawasaki Z900RS | MotoStatz article has ET but no named instrument in article body |
| Ducati Diavel 1198cc | MotoStatz confirmed Dragy + 10.46s but the 1198cc variant is not in catalog |
| Triumph Tuono 660 | MotoStatz article checked; no quarter-mile time found |
| Kawasaki ZX-6R 636 (2009+) | Rejected in sixth pass |
| MT-09 (third gen) | Already in list from CW 2021; not a gap |
| Yamaha XSR700 | Rejected in sixth pass |
| Honda CBR1000RR 2017-19 | Rejected in sixth pass |
| Ducati Streetfighter V4 | Already in list from CW 2020 |
| Suzuki GSX-R750 (2008-2010) | Rejected in sixth pass |
| Suzuki Katana (2019) | Rejected in sixth pass |

### 2. Remaining gaps require live web access

Bikes still unbenchmarked that are likely to have instrumented data
somewhere (but cannot be located without live search):

- **Kawasaki Ninja ZX-10RR** (2021-2024, 214hp) — almost certainly tested
  by Cycle World, but the exact ET/trap is not in my training data with
  sufficient precision to cite.
- **Ducati 959 Panigale** (2016-2019, 157hp) — likely in Sport Rider's
  sportbike-performance-numbers table, but the specific row number is
  uncertain.
- **Royal Enfield Interceptor 650** — MotoStatz may have a Dragy test;
  the figure ~14.0s appears in my training corpus but without a specific
  URL or "Dragy" instrument citation I can confirm.

These three bikes should be the primary targets for a future pass with
live WebSearch enabled.

---

## DISPATCH_INBOX Research: entry_150_200 DERIVED Benchmarks

_Responding to: "## INSTRUCTION — 2026-05-20 — research: verify entry_150_200
DERIVED benchmarks"_

### Current DERIVED entries in the entry_150_200 / entry_200_300 clusters

| Bike | DERIVED ET | Physics sim ET | Delta | Assessment |
|------|-----------|---------------|-------|------------|
| TVS Apache RTR 200 4V | 15.90s | ~19.3s | −3.4s | Likely too optimistic |
| Yamaha MT-15 | 15.80s | ~19.1s | −3.3s | Likely too optimistic |
| Yamaha MT-03 | 14.05s | — | — | Different class (321cc) |
| Honda CB350RS | 15.50s | — | — | 350cc single |

### Analysis

The instrumented R15 V4 (17.62s MotoStatz, same 155cc 18.4hp class) is the
best cross-reference. The R15 V4 has marginally more power than the
Apache RTR 200 4V (18.4hp vs 20.2hp at 8500rpm) but less displacement
(155cc vs 197cc).

Physics reasoning:
- Apache RTR 200 4V: 197cc, 20.2hp, ~148kg wet → P/W = 135 hp/tonne
- R15 V4: 155cc, 18.4hp, ~142kg wet → P/W = 129 hp/tonne
- Apache has ~5% higher P/W. Expected ET delta: −0.2 to −0.5s vs R15 V4.
- Expected Apache instrumented ET: approximately **17.1s – 17.4s**, not 15.9s.

The DERIVED 15.90s figure comes from 0-100 km/h × 1.6 multiplier. For the
Apache RTR 200 4V, typical Indian magazine 0-100 km/h is ~9.7s, giving
9.7 × 1.6 = 15.5s — already optimistic because the multiplier assumes a
well-paved track with a professional launcher, not a raw Indian strip
launch.

### Recommendation

Replace or flag the two DERIVED entries as follows:

1. **TVS Apache RTR 200 4V (2016):** Update comment to `"DERIVED — likely
   optimistic; instrumented estimate ~17.1s based on R15 V4 cross-reference
   (MotoStatz 2020). ±1.0s uncertainty."` Do NOT update the numeric ET
   without a real source — the physics model calibration should flag this
   cluster as needing external data, not absorb a wrong correction.

2. **Yamaha MT-15 (2019):** The MT-15 shares the YZF-R15 engine (155cc,
   18.4hp). Its DERIVED 15.80s is similarly suspect. Expected instrumented
   ET: approximately **17.5s – 18.0s** by analogy with the R15 V4 (same
   engine, slightly different aero/geometry). Update comment similarly.

**Action taken this pass:** No benchmark numeric changes made — per
DISPATCH_INBOX instruction "Don't act yet — write findings to outbox." This
report constitutes the outbox finding. A follow-up pass with live WebSearch
should search Indian Autos Mag, BikeDekho, or MMRT timeslips for these
bikes before any numeric update.

---

## Candidates for Next Pass (live WebSearch required)

Priority order for next benchmark-import agent with WebSearch enabled:

1. **Kawasaki Ninja ZX-10RR** (2021-2024) — Cycle World / Sport Rider
2. **Royal Enfield Interceptor 650** (2018-2024) — MotoStatz (confirm Dragy)
3. **Ducati 959 Panigale** (2016-2019) — Sport Rider performance table
4. **TVS Apache RTR 200 4V** — Indian Autos Mag / BikeDekho / MMRT timeslip
5. **Yamaha MT-15 V2** — same sources as Apache

---

## Files Touched

None (null delivery — no BENCHMARKS edits made).
