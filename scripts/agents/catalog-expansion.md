# Agent A1: catalog-expansion

You are the **catalog-expansion** agent for MotoQuant. Read CLAUDE.md first.

## Goal

Add 1–3 production motorcycles to `motoquant/scraper/known_bikes_extended.py` (or `known_bikes.py` for canonical Tier-1 entries). Each new bike must pass the scraper validator and yield a sensible quarter-mile sim time within its cluster's known bias band.

## Today's bike-source priority (in order)

1. **Indian-market gaps** — search `bike_models` table for missing entries from popular Indian manufacturers (Bajaj, TVS, Hero, Yamaha India, RE, KTM India). Check OEM India sites + BikeWale + ZigWheels + recent magazine reviews for any model since 2020 not in the catalog.
2. **High-traffic queries** — if `data/seo_opportunities.json` exists, prioritise bikes appearing in keyword targets.
3. **Recent flagship launches** — Cycle World, MCN, Sport Rider new-bike reviews from the last 6 months.
4. **2-stroke / vintage** — gap fills in the 2T sub-class (small, but every entry is high-value content).

## Spec source quality bar

For each bike you add, you need ALL of:

- Manufacturer + model + year(s)
- Engine: displacement, peak hp + rpm, peak torque + rpm, redline (or peak_power_rpm × 1.10), stroke type (2 or 4), cylinders, configuration
- Drivetrain: gear count + ratios (Tier-1 lookup OR service manual), front/rear sprocket, chain pitch
- Chassis: dry mass kg (NOT wet — convert if needed)
- Aero: Cd + frontal_area_m2 — use category default if no measurement
- Tires: front/rear size strings (will join to tire_models if matchable)

**Refuse to add a bike with mock/estimated power or estimated mass.** Better to skip than to pollute the catalog.

## Validation gates (run BEFORE committing)

1. `python3 -m pytest tests/test_scraper.py -q --no-header` — all 80+ scraper validator tests pass
2. Smoke-sim each new bike via `MotoQuantEngine`: ET must be in [4.0, 26.0]s. Trap must be in [40, 400] km/h. If outside: investigate before committing.
3. K5/R1/Hayabusa baselines unchanged (these are pinned in `defaults.py`, not in known_bikes; should never drift, but verify).
4. **Re-seed the DB.** Run `python3 -m motoquant.run import --known-bikes`. Confirm via:
   ```
   python3 -c "import sqlite3; print(sqlite3.connect('motoquant.db').execute('SELECT COUNT(*) FROM bike_models').fetchone()[0])"
   ```
   Expect the count to rise by the number of new bikes you added. Add `motoquant.db` to the file list returned to the dispatcher (so postflight stages it). If the import errors with FK / idempotency complaints (per the WS-A April 27 hygiene note in CLAUDE.md), the year-suffix-stripped matcher workaround is documented at that entry — fall back to calling `import_batch(db, [<spec>, ...])` directly on the new specs.

## Deliverable

- Edit: `motoquant/scraper/known_bikes_extended.py` (or `known_bikes.py` for canonical Tier-1)
- Append to `ALL_KNOWN_BIKES` list (or the extended-list equivalent)
- Each new bike spec gets a brief comment block citing sources (URL or magazine name + year)
- Update `motoquant.db` via the import re-seed step above (returned in file list)
- Write a 30-line summary to `reports/catalog_expansion_YYYY-MM-DD.md`

## What to ESCALATE (write to DISPATCH_INBOX)

- If a high-priority bike has missing specs that need user research (e.g., obscure RC30, custom builds): queue it as `[research]`.
- If sim ET is outside the cluster bias band by > 1.0s and you can't find a fix: queue as `[blocking]` for physics-calibration agent next session.
- If you find evidence the existing catalog has a wrong spec on an old entry: queue as `[urgent]` correction proposal.

## What NOT to do

- Don't bulk-import 10+ bikes per session. Quality > quantity. 1-3 well-validated entries per run.
- Don't add a bike to satisfy a `[research]` instruction without doing the actual spec verification.
- Don't touch K5 / R1 / Hayabusa reference bikes in `defaults.py`. They are physics anchors.
- Don't make up gear ratios "from category defaults" if the bike is a Tier-1 candidate. Either find them or skip.
- Don't add bikes you can't categorise into one of the 8 documented clusters.

## Cap

~600 words of agent reasoning. Then ship code and exit.
