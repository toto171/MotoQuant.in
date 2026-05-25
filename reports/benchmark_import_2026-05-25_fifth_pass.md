# Benchmark Import — 2026-05-25 (Fifth Pass)

**Agent:** benchmark-import (A5)
**Session:** 1779712234-644

---

## Summary

Added **1 high-confidence MotoStatz Dragy instrumented benchmark** to
`scripts/validation_sweep.py::BENCHMARKS`. BENCHMARKS count: 102 → **103**.

Reference baselines preserved exactly: K5 10.0334s / R1 10.2859s /
Hayabusa 10.4712s, Δ +0.0000s on all three.

---

## Benchmark Added

| Field | Value |
|---|---|
| Manufacturer | Ducati |
| Model | Monster 937 |
| Year hint | 2023 |
| ET | 11.33 s |
| Trap | 118 mph / 190 km/h |
| Source | MotoStatz 2023 (Dragy, stock instrumented) |
| URL | https://motostatz.com/ducati-monster-top-speed-acceleration/ |
| Catalog entry | `DUCATI_MONSTER_937` 2021-2026 (937 cc Testastretta L-twin) |

**Source verification:** WebFetch of the MotoStatz article (published March 2026)
confirmed: (a) the Ducati Monster 937/950 is the test bike, (b) the word "Dragy"
is explicitly named as the measurement device, (c) the bike is stock configuration,
(d) SS/QM result is 11.33s @ 118 mph. This is the same MotoStatz/Dragy source bar
already used by 10+ entries in this list (Street Triple 765 RS, Panigale V2, RS 660,
890 Duke R, 790 Duke, XSR900, CBR 600RR PC40B, Ninja 1000SX, BMW S1000R, CBR650R).

**Pre-commit sim validation:**

| Bike | Sim ET | Benchmark ET | Δ |
|------|--------|--------------|---|
| Ducati Monster 937 2021-2026 | 11.127s | 11.33s | −0.203s |

Delta of −0.203s is within ±0.21s — acceptable for the naked-litre cluster
(current cluster mean|Δ| ≈ 0.199s per fourth-pass report).

---

## Candidate Investigated and Rejected

### Kawasaki Z900RS (2018-2026)

MotoStatz article `motostatz.com/kawasaki-z900rs-top-speed-acceleration/` (Aug 2022)
quotes 11.35s @ 120.7 mph. WebFetch confirmed the exact numbers but found **no named
measurement instrument** in the article text — no Dragy, no GPS logger, no timing
strip, no methodology statement. Sim ET for Z900RS is 11.337s (Δ = −0.013s vs
potential 11.35 benchmark) — the delta is excellent, but without a named instrument
the source cannot clear the instrumented-only bar. Rejected per project policy.

The Z900RS is a strong research target for a future pass: if a separate Dragy-named
source surfaces (e.g. a forum timeslip with explicit Dragy screenshots, or a MCN
instrumented road test), it could be added with high confidence.

---

## Reference Baselines (post-edit)

| Bike | Sim ET | Target | Δ |
|------|--------|--------|---|
| Suzuki GSX-R 1000 K5 | 10.0334s | 10.0334s | +0.0000 ✓ |
| Yamaha YZF-R1 4C8 | 10.2859s | 10.2859s | +0.0000 ✓ |
| Suzuki Hayabusa Gen1 | 10.4712s | 10.4712s | +0.0000 ✓ |

---

## Files Modified

- `scripts/validation_sweep.py` — 1 new BENCHMARKS entry appended at lines ~579-608
  with full citation comment and fifth-pass section header

---

## Suggested Commit Message

```
benchmark: +1 Dragy entry (Ducati Monster 937, MotoStatz 2023)
```
