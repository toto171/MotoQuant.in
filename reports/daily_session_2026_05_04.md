# Daily Improvement — Monday, May 4, 2026 (Catalog Expansion Day)

**Scheduled task:** `motoquant-daily-improvement`
**Today's rotating focus:** Monday — Catalog Expansion
**Status:** ✅ COMPLETE — committed + pushed.
**Reference baselines preserved EXACTLY:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s (Δ +0.0000s on all three, both pre-run and post-run).

---

## What changed

Two new bikes added to `motoquant/scraper/known_bikes_extended.py`:

### 1. KTM 1390 Super Duke R EVO (2024-2026)
- 1350 cc 75° V-twin LC8 EVO, 110 × 71 mm bore × stroke, 13.5:1 CR
- 190 hp @ 10,000 rpm, 145 Nm @ 8,000 rpm
- Direct successor to the 1290 Super Duke R EVO using the **same chassis,
  same transmission cassette, and same final drive** (per KTM 2024 press
  kit — "the 1390 inherits the 1290 EVO platform with new pistons +
  crankshaft"). Gear ratios `[2.500, 1.857, 1.538, 1.300, 1.148, 1.000]`,
  17F/41R sprockets, 525 chain — copied verbatim from the existing
  1290 Super Duke R entry. Only bore (108→110 mm), displacement (1301→1350
  cc), and power/torque are bumped.
- Sources: KTM official 2024 technical data sheet (ktm.com), MCN 2024
  launch test, Cycle World 2024 first-ride.
- DB id `341`. Smoke sim: **ET 10.225s @ 237.3 km/h trap** — well within
  the litre-naked cluster's documented +0.15 to +0.30s bias band; MCN
  recorded 9.95s for the real bike, so Δ = +0.275s, consistent with
  cluster.

### 2. Hero Xtreme 200S 4V (2023-2026)
- 199.6 cc oil-cooled single, 4-valve head (replaces the older 2-valve
  Xtreme 200S with a Karizma-derived 4V head)
- 19.1 hp @ 8,500 rpm, 17.35 Nm @ 6,500 rpm
- Standard 5-speed Hero 200cc commuter cassette, 14F/42R, 428 chain
- Aero values calibrated against existing 200cc commuter peers in the
  catalog (Cd=0.78 — between Pulsar NS200 @ 0.80 and Bajaj 220F @ 0.83;
  FA=0.46 m² — close to TVS Apache RTR 200 @ 0.45)
- Sources: Hero MotoCorp official spec sheet (heromotocorp.com),
  91Wheels review database, ZigWheels spec table.
- DB id `342`. Smoke sim: **ET 17.400s @ 125.1 km/h trap** — falls in
  the documented entry-200-300 cluster (+0.5–1.4s slow vs 16.5s real-world
  benchmarks). Realistic for the cluster.

---

## Files touched

| File | Δ lines | Reason |
|---|---|---|
| `motoquant/scraper/known_bikes_extended.py` | +97 / -0 (261 → 358 lines) | Two new `spec_from_dict(...)` blocks + 2 names appended to `EXTENDED_BIKES` list |
| `motoquant.db` | binary +2 bike_models rows + 2 bike_configs rows | New bike inserts + reseed of all 333 importer-derived configs |
| `web/app/page.js` | 3 sed swaps | Headline-stats drift: 334 → 336 (3 occurrences) |
| `web/app/blog/how-the-motoquant-physics-engine-works/page.js` | 1 sed swap | Blog-post bike count: 334 → 336 |
| `README.md` | 1 sed swap | Phase 2 stats line: 334 → 336 |
| `reports/daily_session_2026_05_04.md` | new | This file |
| `CLAUDE.md` | +1 paragraph at line 3 | Surgical prepend per CLAUDE.md hygiene |

---

## Verification

| Check | Result |
|---|---|
| Reference baselines (K5 / R1 / Hayabusa) | **PASS — Δ +0.0000s on all three** |
| `python3 scripts/audit_headline_stats.py` | **CLEAN** — all headlines in sync (336/562/232/861/20/79) post-patch |
| `python3 -m pytest tests/test_scraper.py -q` | **80/80 PASS** |
| Focused subset (test_scraper + test_validation + test_two_stroke + test_compatibility + test_category_dispatch) | **193/193 PASS** in 13.71s |
| `tests/test_physics_invariants.py` (Saturday's Hypothesis suite) | **7/7 PASS** in 21.21s — monotonicity invariants still hold |
| `tests/test_catalog_integration.py` | 26 pass / 1 fail = pre-existing `test_rsv4_no_panigale_leak` (carry-forward; not a regression) |

---

## Hygiene notes for next run

1. **`import_batch` FK-error duplicates regressed (caught & fixed).** First
   re-import attempt (`python3 -m motoquant.run import --known-bikes`) fired
   `Imported: 36 / Errors: 297` and bloated `bike_models` from 334 → 369
   with 35 phantom duplicate rows whose `model_name` carries an extra
   `(year-year)` suffix that doesn't exist on the existing rows. This is
   the same WS-A April 27 idempotency bug flagged in CLAUDE.md ("WS-A
   bike-import had FK errors on 266 retry attempts"). Worked around today
   by `git checkout HEAD -- motoquant.db` and re-running the importer
   directly on the 2-bike list (`import_batch(db, [KTM_1390..., HERO_XTREME...])`)
   which inserted exactly 2 rows with zero errors. Fix proper:
   `bike_repo.create_model` upsert should match on
   `(manufacturer_id, normalized_model_name)` ignoring year-suffix
   variants — currently the lenient fallback in the connection layer
   doesn't catch the year-suffix case.

2. **Dead-knob carry-forwards from CLAUDE.md still open** — none touched
   today (per Monday focus): wheelie-bar sub-500cc gap, parts #469 + #472
   invalid `tier: model` fitment_rules, INR pricing on 7 drag-prep
   specialty parts.

3. **Tire-size format warnings on Hero Xtreme 200S 4V** are cosmetic.
   Indian commuter tires use the older `100/80-17` / `130/70-17` format
   (no Z-rated load index, no R prefix). The validator's strict
   `\d+/\d+ZR\d+` regex only flags this as a warning — does not block
   import. Consider widening the validator to accept `100/80-17` as
   valid bias-ply notation in a future Saturday test-hardening pass.

