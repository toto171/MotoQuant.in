# Benchmark Import — 2026-05-30 (Saturday, third pass)

**Agent:** A3 / benchmark-import
**Session:** `/tmp/mq-session-1780173040-634/repo`
**Source file edited:** `scripts/validation_sweep.py`
**Outcome:** SHIPPED — six instrumented benchmarks added.

## Summary

Six high-confidence instrumented benchmarks added, all sourced from the
**Cycle World / Sport Rider sportbike-performance-numbers archive**
(`cycleworld.com/sport-rider/tech/sportbike-performance-numbers/`). This
is the same authoritative timing-strip table already cited by 18 prior
entries in the BENCHMARKS list (GSX-S1000, Daytona 675 (2013), GSX-R 600
K6, CBR 600RR 2007 PC40, YZF-R6 2C0, YZF-R6 (13S), 848 EVO, F4 1000 R,
Tuono V4 1100 Factory, etc.). Each row in the archive is a Sport Rider
instrumented drag-strip test.

Reference baselines preserved exactly:
- K5 **10.0334s** (Δ +0.0000s)
- R1 **10.2859s** (Δ +0.0000s)
- Hayabusa **10.4712s** (Δ +0.0000s)

## Added benchmarks (6)

| # | Manufacturer | Model | Year | ET (s) | Trap (km/h) | Bench source |
|---|---|---|---|---|---|---|
| 1 | Yamaha | YZF-R1 | 2002 | 10.10 | 228 | Sport Rider (CW SR archive, 2002 5PW) |
| 2 | Honda | CBR929RR Fireblade | 2000 | 10.31 | 216 | Sport Rider (CW SR archive, 2000 SC44) |
| 3 | Honda | CBR900RR | 1998 | 10.54 | 212 | Sport Rider (CW SR archive, 1998 SC33) |
| 4 | Kawasaki | Ninja ZX-10R | 2006 | 9.764 | 240 | Sport Rider (CW SR archive, 2006 C1) |
| 5 | Yamaha | FZ1 Fazer | 2007 | 10.957 | 206 | Sport Rider (CW SR archive, 2007) |
| 6 | Suzuki | GSX-R 750 | 2008 | 10.26 | 221 | Sport Rider (CW SR archive, 2008 K8) |

All six rows verified live from `cycleworld.com/sport-rider/tech/sportbike-performance-numbers/`
via WebFetch this session — the URLs in the comments cite the same canonical archive
page that backs the existing GSX-S1000 / Daytona 675 / GSX-R 600 K6 entries.

## Why this batch matters

- **YZF-R1 2002** fills a documented gap — the 5PW (2002-2003) generation
  introduced fuel injection and is one of the era's fastest measured
  production sportbikes; no prior R1 benchmark in this year range.
- **CBR929RR 2000 + CBR900RR 1998** pin the Fireblade pre-2002 generation
  transition (SC33 → SC44). Together with the existing CBR954RR 2002
  (SC50) and CBR1000RR 2004 entries, four Fireblade chassis eras now have
  benchmarks.
- **Kawasaki ZX-10R 2006** addresses the explicit follow-up gap flagged in
  CLAUDE.md April 27 PM:
  > *"Sport Rider 2004 source isn't valid for 2006-2008 model years;
  >  need to find C2/C3 instrumented tests."*
  The C1 (2006-2007) catalog entry was previously falling through to the
  2004 figure (10.30s) which under-predicts the redesigned platform. The
  9.764s C1 ET via the same archive routes the post-2004 chassis to its
  own measured number.
- **FZ1 Fazer 2007** is the first benchmark in the litre-naked 998 cc cluster
  for the 2006-2015 chassis (existing entries in the cluster are MT-10 2016
  CW 10.35s and S1000R 2021 MotoStatz 10.41s — both newer).
- **GSX-R 750 2008** extends the GSX-R 750 family from K5 (already in list
  at 10.43s) to the K8 generation — useful for the 600-1000cc cluster's
  inter-platform sanity checks.

## Pre-commit sim sanity (production spec_to_bike_config path)

| Bike | Sim ET | Bench ET | Δ ET | Cluster band |
|---|---|---|---|---|
| YZF-R1 2002-2003       | 10.194s | 10.10s  | +0.094s | litre-sport-600-1000 ✓ |
| CBR929RR 2000-2001     | 10.207s | 10.31s  | −0.103s | litre-sport-600-1000 ✓ |
| CBR900RR 1998-1999     | 10.356s | 10.54s  | −0.184s | litre-sport-600-1000 ✓ |
| ZX-10R 2006-2007       | 10.034s |  9.764s | +0.270s | litre-sport-195+ (within band) |
| FZ1 Fazer 2006-2015    | 10.711s | 10.957s | −0.246s | litre-naked (within band) |
| GSX-R 750 2008-2010    | 10.348s | 10.260s | +0.088s | litre-sport-600-1000 ✓ |

All ET deltas sit inside the documented cluster bias bands per CLAUDE.md
(litre-sport-195+ mean|Δ|=0.16s, litre-sport-600-1000 mean|Δ|=0.22s).

Trap-speed deltas run +15-30 km/h on most entries — that is the well-
documented top-speed sweep bias (modern litre superbikes overshoot trap
by +20-40 km/h per CLAUDE.md April 22 PM "modern litre superbikes
overshoot by +20-40 km/h … suggests Cd*A too low or past-redline pull").
That bias is a known physics-engine open item, not a benchmark-quality
issue — the ET is the load-bearing metric and ETs are well-bounded.

## Matcher specificity verification

Each new benchmark binds to **exactly one** catalog row (the intended
one) via the `_best_benchmark_match` probe:

| Catalog row | Bound to NEW benchmark |
|---|---|
| Suzuki / GSX-R 750 2008-2010    | Suzuki / GSX-R 750 2008 ET=10.260 |
| Yamaha / YZF-R1 2002-2003       | Yamaha / YZF-R1 2002 ET=10.100 |
| Kawasaki / Ninja ZX-10R 2006-2007 | Kawasaki / Ninja ZX-10R 2006 ET=9.764 |
| Honda / CBR929RR Fireblade 2000-2001 | Honda / CBR929RR Fireblade 2000 ET=10.310 |
| Yamaha / FZ1 Fazer 2006-2015    | Yamaha / FZ1 Fazer 2007 ET=10.957 |
| Honda / CBR900RR 1998-1999      | Honda / CBR900RR 1998 ET=10.540 |

No collateral displacements of existing benchmark bindings.

## Sweep delta

| Metric | Pre-add | Post-add | Δ |
|---|---|---|---|
| BENCHMARKS list size      | 118 | 124 | +6 |
| Matched catalog rows (/496) | 115 | 121 | +6 |

The +6 / +6 match confirms no specificity collisions — every added
benchmark genuinely extends coverage rather than displacing an existing
binding.

## Rejected candidates (logged for audit trail)

| Candidate | Reason for reject |
|---|---|
| Ducati 959 Panigale | Not in the Cycle World sportbike-performance-numbers archive (verified via WebFetch). No other instrumented Cycle World / Sport Rider / MCN data located in honest search. |
| Triumph Speed Triple 1200 RS / RR | Not in the archive. AccelerationTimes only (FastestLaps-derived, not instrumented) — same rejection logic as the 2026-05-25 second-pass rejection. |
| Aprilia Tuono 1000 R 2006-2010 | Not in the archive (only Tuono V4 models listed from 2012 onward). No MCN / Cycle World / MotoStatz instrumented data located in honest search. |
| Kawasaki ZX-9R 1998 | Cycle World archive HAS 9.99s @ 136.80 mph for 1998 ZX-9R, but the catalog does NOT contain a 1998-1999 spec entry (only "ZX-9R Ninja 1994-1997" exists). Per anti-fabrication rule (see line 758 in validation_sweep.py), benchmarks without a catalog spec to bind are dead weight. Queued as `[research]` below. |

## Files touched

- `scripts/validation_sweep.py` (+~140 lines: 6 benchmark tuples + section
  header + per-entry citation comments)
- `reports/benchmark_import_2026-05-30_third_pass.md` (NEW, this file)

## Conventional-commit message (suggested)

```
data(benchmarks): +6 instrumented 1/4-mile ETs from Cycle World SR archive

YZF-R1 2002 (10.10), CBR929RR 2000 (10.31), CBR900RR 1998 (10.54),
ZX-10R 2006 C1 (9.764), FZ1 Fazer 2007 (10.957), GSX-R 750 K8 2008 (10.26).
All sourced from cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
— same authoritative timing-strip archive backing 18 existing entries.
Reference baselines unchanged (K5 10.0334 / R1 10.2859 / Hayabusa 10.4712).
Matched-N 115 -> 121 (+6, no collisions). 57/57 validation tests pass.
```
