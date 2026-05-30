# Benchmark Import — 2026-05-30 (Saturday, fourth pass)

**Agent:** A3 / benchmark-import
**Session:** `/tmp/mq-session-1780180253-673/repo`
**Source file edited:** `scripts/validation_sweep.py`
**Outcome:** SHIPPED — four instrumented benchmarks added.

## Summary

Four high-confidence instrumented benchmarks added, all sourced from the
**Cycle World / Sport Rider sportbike-performance-numbers archive**
(`cycleworld.com/sport-rider/tech/sportbike-performance-numbers/`). This
is the same authoritative timing-strip table already cited by 24+ prior
entries in the BENCHMARKS list and the source of all six entries in the
third pass earlier today. Verified live via WebFetch this session — the
URLs in the comments cite the same canonical archive page.

This fourth pass targets catalog rows where no prior benchmark existed
(verified via `_best_benchmark_match` collision probe pre-edit). All four
chosen bikes are litre-class V-twin / V4 / I4 platforms covering era gaps
the prior 3 passes left open.

Reference baselines preserved exactly:
- K5 **10.0334s** (Δ +0.0000s)
- R1 **10.2859s** (Δ +0.0000s)
- Hayabusa **10.4712s** (Δ +0.0000s)

## Added benchmarks (4)

| # | Manufacturer | Model | Year | ET (s) | Trap (km/h) | Bench source |
|---|---|---|---|---|---|---|
| 1 | Aprilia | RSV Mille | 2002 | 10.71 | 208 | Sport Rider (CW SR archive, 2002) |
| 2 | Aprilia | Tuono 1000 R | 2007 | 11.048 | 203 | Sport Rider (CW SR archive, 2007) |
| 3 | Honda | VTR1000 SP2 | 2005 | 10.44 | 215 | Sport Rider (CW SR archive, 2005 SP-2) |
| 4 | Ducati | 999 | 2003 | 10.29 | 215 | Sport Rider (CW SR archive, 2003) |

## Why this batch matters

- **Aprilia RSV Mille 2002** is the FIRST benchmark for the 2001-2004 Aprilia
  RSV Mille catalog row. Previously the litre-V-twin sport sub-cluster
  was carried only by Ducati 1098/1199/1299 entries — adding the Rotax-V2
  RSV Mille gives the cluster a non-Italian-L-twin reference point. Note:
  the RSV4 family (V4, 2010+) is separately covered.
- **Aprilia Tuono 1000 R 2007** is the FIRST benchmark for the 2006-2010
  Tuono 1000 R catalog row. Pairs naturally with the RSV Mille entry to
  pin the litre-V-twin faired-vs-naked aero delta within a single platform
  (RSV ~10.71s, Tuono ~11.05s — Δ +0.34s, consistent with the upright
  riding position + handlebar-fairing aero penalty). Distinct from
  existing Tuono V4 1100 Factory 2016 (10.30s) and Tuono V4 R APRC 2012
  entries — three Tuono generations now have benchmarks (1000 V2 / V4
  1000 / V4 1100).
- **Honda VTR1000 SP2 (RC51) 2005** is the FIRST benchmark for the 2002-2006
  Honda VTR1000 SP2 catalog row. The RC51 is Nicky Hayden's AMA Superbike
  homologation platform and the SP-2 (post-2002 SP-1) is the better-running
  version. Cluster-consistent at 10.44s for a litre-90°-V-twin sport-
  homologation special. Distinct from the CBR954RR 2002 (also a Honda
  litre-sport but I4 platform — separate engine architecture).
- **Ducati 999 2003** is the FIRST benchmark for the 2003-2006 Ducati 999
  catalog row. The 999 replaced the 998 in the Superbike lineage and
  preceded the 1098 (already benched at CW 2007 10.40s); this entry
  completes the modern-Ducati-Superbike-V2 progression of 999 → 1098 →
  1198 → 1199/1299. The 999R variant (2005) at 10.10s in the archive
  could in principle be added later when the catalog gets a 999R spec row.

## Pre-commit sim sanity (production spec_to_bike_config path)

| Bike | Sim ET | Bench ET | Δ ET | Cluster band |
|---|---|---|---|---|
| Aprilia RSV Mille 2001-2004     | 10.438s | 10.710s | −0.272s | litre-sport-600-1000 ✓ |
| Aprilia Tuono 1000 R 2006-2010  | 10.681s | 11.048s | −0.367s | litre-sport-600-1000 ✓ |
| Honda VTR1000 SP2 (RC51) 2002-2006 | 10.572s | 10.440s | +0.132s | litre-sport-600-1000 ✓ |
| Ducati 999 2003-2006            | 10.371s | 10.290s | +0.081s | litre-sport-600-1000 ✓ |

All four ET deltas sit inside the documented litre-sport-600-1000
cluster bias band (mean|Δ|=0.22s per CLAUDE.md April 27 PM cluster
metrics). Two slightly negative (sim faster than bench) and two slightly
positive (sim slower than bench) — the cluster centres nicely around
zero with the new additions, no systematic skew introduced.

## Matcher specificity verification

Each new benchmark binds to **exactly one** catalog row via the
`_best_benchmark_match` probe (post-edit fresh-import verified):

| Catalog row | Bound to NEW benchmark |
|---|---|
| Aprilia / RSV Mille 2001-2004        | RSV Mille 2002 ET=10.71 |
| Aprilia / Tuono 1000 R 2006-2010     | Tuono 1000 R 2007 ET=11.048 |
| Honda / VTR1000 SP2 (RC51) 2002-2006 | VTR1000 SP2 2005 ET=10.44 |
| Ducati / 999 2003-2006               | 999 2003 ET=10.29 |

The Honda RC51 entry uses the 2-token model string `VTR1000 SP2` (matching
the CW source's naming) rather than the catalog's full 4-token
`VTR1000 SP2 (RC51)`. The matcher's word-boundary tokenizer correctly
matches "VTR1000 SP2" tokens against "VTR1000 SP2 (RC51)" catalog spec
(verified via `_model_match` direct probe and `_best_benchmark_match`
end-to-end probe).

The Ducati 999 entry uses the 1-token model string `999`. Verified via
collision probe: no other catalog Ducati matches the model token `999`
(e.g., 1199 / 1299 / 999R are tokenized distinctly).

No collateral displacements of existing benchmark bindings — all prior
24+ Cycle-World-sourced entries still bind to their original catalog rows.

## Sweep delta

| Metric | Pre-add | Post-add | Δ |
|---|---|---|---|
| BENCHMARKS list size      | 124 | 128 | +4 |
| Matched catalog rows (/496) | 121 | 125 | +4 |

The +4 / +4 match confirms no specificity collisions — every added
benchmark genuinely extends coverage rather than displacing an existing
binding.

## Rejected candidates (logged for audit trail)

| Candidate | Reason for reject |
|---|---|
| Honda CB1000R | CW archive has 2011 CB1000R 11.13s but catalog only has the 2021-2024 Neo Sports Café CB1000R (different chassis & engine tune); no year-bind valid. |
| Honda CBR954RR Fireblade | Already has a benchmark (10.49s from second pass, Motorcycle Consumer News). CW archive's 10.26/10.23 @ 137.57 mph for 2002 are slightly tighter but no reason to displace a verified entry. |
| BMW K1200S | CW archive has 2005 K1200S 10.30s @ 137.5 mph, but BMW K1200S not in current catalog (only K1300S is). Would need catalog-expansion agent to add K1200S spec first. |
| BMW K1200R | Same situation — CW archive has 2005 K1200R 10.40s but no K1200R catalog row. |
| Suzuki SV1000S | CW archive has 2003 SV1000S 10.82s and 2006 11.202s, but Suzuki SV1000S not in current catalog. |
| Ducati 1198 | CW archive has 2009 1198 10.01s + 2010 1198S 10.02s + 2011 1198 10.40s, but Ducati 1198 not in current catalog (only 1098/1199/1299 sport progression is). |
| Kawasaki ZX-11 / ZX-12R | CW archive has 1997 ZX-11 10.25s + 2001 ZX-12R 9.95s + 2005 ZX-12R 10.17s but neither in current catalog. |
| Ducati Desmosedici RR | CW archive has 2010 Desmosedici RR 9.49s but limited-production race-replica not in catalog. |
| Kawasaki Concours 14 | CW archive has 2008 Concours 14 10.52s but not in catalog. |
| Suzuki GSX-S750 | CW archive has 2015 GSX-S750 11.52s but the catalog Suzuki GSX-S750 spec needs cross-checking before binding (deferred — may collide with GSX-S1000 entries). |
| Honda CBR1100XX Super Blackbird | CW archive has 1997 CBR1100XX 10.43s + 1999 10.40s @ 136.14 mph (excellent instrumented data), but catalog does NOT contain a CBR1100XX spec entry. Per anti-fabrication rule, benchmarks without a catalog spec to bind are dead weight. Carried-forward from third pass — needs catalog-expansion agent to add CBR1100XX first. |

## Files touched

- `scripts/validation_sweep.py` (+~90 lines: 4 benchmark tuples + section
  header + per-entry citation comments + fourth-pass end marker)
- `reports/benchmark_import_2026-05-30_fourth_pass.md` (NEW, this file)

## Conventional-commit message (suggested)

```
data(benchmarks): +4 instrumented 1/4-mile ETs from Cycle World SR archive

RSV Mille 2002 (10.71), Tuono 1000 R 2007 (11.048), VTR1000 SP2 2005 (10.44),
Ducati 999 2003 (10.29). All sourced from
cycleworld.com/sport-rider/tech/sportbike-performance-numbers/ — same
authoritative timing-strip archive backing 24+ existing entries.
Reference baselines unchanged (K5 10.0334 / R1 10.2859 / Hayabusa 10.4712).
Matched-N 121 -> 125 (+4, no collisions). All 4 catalog rows previously
had no benchmark binding; cluster bias bands respected.
```
