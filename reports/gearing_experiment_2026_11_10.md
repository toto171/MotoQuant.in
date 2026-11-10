# Sourced gearing for small bikes: measured, not applied

**Result.** Replacing inferred gearing with manufacturers' published figures for
53 catalog bikes makes overall accuracy slightly worse (weighted mean error
0.2495 → 0.2525 s on 263 matched benchmarks) and worse on the bikes it touches
(0.411 → 0.447 s). The published gearing is right; the model around it is tuned
to the wrong gearing. Applying it properly means re-tuning the small-bike
classes, which is an accuracy epoch of its own. Until then the catalog keeps its
current gearing, and the sourced figures are kept in
[`gearing_research_2026_11_10.json`](gearing_research_2026_11_10.json).

## What was found

Most bikes under 500 cc have no primary ratio in their catalog entry, so the
importer falls back to a lookup default of about 1.85–1.9, a figure typical of
litre superbikes. Owner's and service manuals give 2.0–3.7 for these bikes. The
research read manufacturer documents for 34 model families; 21 were confirmed
by a manufacturer document (9 of them by two independent sources) and became 32
entries covering 53 catalog bikes. Each entry names its document. Where a manual
prints a final-drive ratio but no sprocket teeth, the entry uses a sprocket pair
with that exact ratio and says so.

## The experiment

Same code and catalog, one change: the sourced gearing overrides everything the
importer infers for those 53 bikes. Both runs used the full benchmark sweep
(`scripts/phys_weighted_sweep.py`, epoch rules, Rust core). Of the 53 bikes, 25
have a benchmark.

Instrumented benchmarks (full weight), simulated minus measured quarter-mile
time:

| Bike | Measured | Before | After |
|---|---|---|---|
| Kawasaki Ninja 300 | 14.10 s | −0.05 | −0.01 |
| Yamaha YZF-R3 | 14.00 s | +0.41 | −0.19 |
| Honda CB500F | 13.36 s | +0.43 | +0.14 |
| Kawasaki Z400 | 13.34 s | +0.37 | +0.24 |
| KTM 390 Duke (2024) | 13.30 s | +0.36 | +0.16 |
| KTM Duke 390 (2017) | 14.00 s | −0.39 | −0.37 |
| TVS Apache RTR 200 4V | 18.10 s | +0.64 | +0.60 |
| KTM RC 390 | 13.16 s | +0.24 | +0.26 |
| KTM Duke 250 | 15.50 s | −0.16 | −0.21 |
| KTM Duke 200 | 16.10 s | −0.08 | −0.27 |
| Honda CBR300R | 15.79 s | +0.10 | −0.73 |
| Yamaha YZF-R25 (Indonesia) | 15.50 s | +0.38 | −0.69 |
| Yamaha MT-25 | 15.60 s | +0.16 | −0.69 |

Seven bikes get closer, six get further away, and three of those swing from
slightly slow to about 0.7 s too quick. Those three are 250–300 cc bikes whose
old gearing was far too tall (CBR300R: primary 1.9 against Honda's 2.807). The
class settings for 200–400 cc bikes were fitted while every one of them carried
that tall gearing, so they hold the bikes back to compensate. Fix the gearing
alone and the compensation shows.

## What applying it needs

1. Put the 32 entries into the importer as a table that overrides inferred
   gearing (a draft is in the research file's `sourced_gearing` block).
2. Re-tune the affected class profiles (`entry_200_300`, `single_300_500`,
   `mid_twin_300_500`) from neutral with `scripts/tune_cluster_knobs.py`, under
   the epoch rules in `docs/adr/0002-pinned-reference-baselines.md`, including the dry-mass
   monotonicity checks.
3. Accept only if the weighted error and the error on high-confidence
   small-bike benchmarks both improve. Then regenerate everything that caches
   the physics (regression snapshot, stock leaderboard, instant-estimate model,
   browser fixtures).

Owner: open; tracked as a starter issue.
