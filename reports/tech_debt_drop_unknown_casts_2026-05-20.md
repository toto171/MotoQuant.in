# Technical-Debt Pass — Drop gratuitous `as unknown as` casts in desktop pages

**Date:** 2026-05-20
**Agent:** technical-debt-pass
**Source finding:** `reports/cleanup_subagent_5_types.md` items #6 and #7 (TS type assertions)

## Goal

Eliminate the two `as unknown as` double-casts in the desktop pages by tightening the surrounding types so the compiler is satisfied without an assertion. These casts existed as workarounds for guessed-not-known field shapes and erased information about types that the project already declares.

## Success criteria

- [x] `desktop/src/pages/BuildPage.tsx:80` — remove `(bike as unknown as { peak_power_hp?: number }).peak_power_hp` and read `bike.peak_power_hp` directly through the typed `BikeSummary` interface.
- [x] `desktop/src/pages/SimulatePage.tsx:213` — remove `result.splits as unknown as Record<string, number>` by typing `exportSimPdf`'s `splits` parameter as the existing `Splits` interface.
- [x] No runtime behavior change (both `as unknown as` casts erase to nothing in compiled JS).
- [x] K5 / R1 / Hayabusa baselines preserved exactly (10.0334 / 10.2859 / 10.4712 s).
- [x] No Python test regressions: `test_power_boost_regression` 10/10 green; `test_scraper + test_validation` 111/111 green.

## Why these are safe

### BuildPage.tsx — `bike.peak_power_hp` direct read

- `bike` is `useState<BikeSummary | null>` (line 32).
- `if (!bike) return;` at line 74 narrows to `BikeSummary`.
- `BikeSummary.peak_power_hp` is declared `number | null` in `desktop/src/types/api.ts:16`.
- `bike.peak_power_hp ?? 100` yields `number` cleanly — no cast required.

The original double-cast `as unknown as { peak_power_hp?: number }` was a relic from a time when `BikeSummary` didn't carry `peak_power_hp`. The field has been on the interface for months; the cast was simply never cleaned up.

### SimulatePage.tsx — `splits: Splits`

- `exportSimPdf`'s body reads only the 5 fixed keys `"60ft_s"`, `"330ft_s"`, `"660ft_s"`, `"1000ft_s"`, `"1320ft_s"`.
- These are the exact 5 fields declared on `Splits` (`desktop/src/types/api.ts:198–204`).
- The original `Record<string, number>` typing was strictly weaker — it lost the key set and forced the double-cast at the only call site.
- Typing the parameter as `Splits` removes the cast and makes typos like `data.splits["60_ft"]` (note the underscore) a compile error rather than a silent `undefined`.

## Metric (before → after)

| Metric                                | Before | After |
|---------------------------------------|--------|-------|
| `as unknown as` casts in pages/       | 2      | 0     |
| LOC delta                             | —      | +7 / -5 (net +2, mostly a comment) |
| Files touched                         | —      | 2     |
| `BikeSummary` field accesses through a cast | 1   | 0     |
| `Splits` callers that lose key information  | 1   | 0     |
| K5 / R1 / Hayabusa baseline drift     | —      | 0.0000 s on all three |
| `test_power_boost_regression`         | 10/10  | 10/10 |
| `test_scraper + test_validation`      | 111/111 | 111/111 |

## Verification performed

```bash
# Baseline preservation
python3 -c "import motoquant; ..."
# → K5: 10.0334s / R1: 10.2859s / Hayabusa: 10.4712s ✓

# Focused test suite
pytest tests/test_power_boost_regression.py -q
# → 10 passed

pytest tests/test_scraper.py tests/test_validation.py -q
# → 111 passed
```

TypeScript compile not run locally (no `node_modules` in this sandbox session). Pre-push hook `.github/workflows/web-verify.yml` and the desktop CI matrix will pick up any type drift on push.

## Files touched

- `/tmp/mq-session-1779301832-641/repo/desktop/src/pages/BuildPage.tsx`
- `/tmp/mq-session-1779301832-641/repo/desktop/src/pages/SimulatePage.tsx`

## Commit summary

```
refactor(desktop): drop gratuitous `as unknown as` casts in BuildPage + SimulatePage
```

## Carry-forward / not touched

The remaining items in `cleanup_subagent_5_types.md` worth a follow-up pass:

- **Item #4** — `[extra: string]: unknown` index signatures on `BikeDetail`, `Venue`, `Tire`, `PartsCategory`, `Part`. Higher risk because the API may actually return extras the UI tolerates; needs a server-side audit before tightening to `never`.
- **Item #5** — `Part.compatible_bikes?: unknown; fitment_rules?: unknown;`. Needs a peek at the actual API response to know whether to drop the fields or type them properly.
- **`cleanup_subagent_1_dedup.md` item #2** — Seed-catalog `seed_*()` boilerplate. Higher risk (touches 6 catalog files) — should be a dedicated pass with its own report.
