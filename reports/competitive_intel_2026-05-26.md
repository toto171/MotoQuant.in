# Competitive Intel — 2026-05-26 (Tuesday)

**Agent:** competitive-intel
**Run:** weekly scan
**Working dir:** /tmp/mq-session-1779755434-680/repo

## Scope of scan

Four WebSearch passes:
1. Generic "motorcycle drag racing simulator quarter mile calculator 2026"
2. India-qualified "bike quarter mile simulator india physics 2026"
3. Named-product "DragSim Pro motorcycle simulator" (verify it's defunct / overlapping)
4. Indian drag scene "Valley Run drag race Aamby Valley 2026 results india motorcycle"
5. Site-restricted Reddit pass — returned no hits (Reddit drag-racing-sim conversation is too niche to index)

## Headline finding

**No new direct competitor surfaced this week.** Three months running, the head-on threat surface remains the same:
- US legacy calculator tools (XCceleration, RobRobinette, Wallace, DragCalc, AJ Designer) — dominate generic SERPs, none India-aware, none per-bike, none INR.
- Motion Software DragSim5 — desktop, paid, Windows-only legacy. Closest functional analogue but different market and different price point.
- No Indian-built equivalent observed.

This is the same picture as the 2026-05-19 product-prioritisation report and consistent with the `seo_opportunities.json` `_competitor_signal` field: the defensible angle remains *physics-based + per-bike + India-first + INR ROI*.

## What's new vs prior scans

- **FIRGELLI Engineering** has shipped a blog-format quarter-mile ET calculator with "interactive tool + diagram + formulas + worked examples". Worth studying for content pattern — they're combining tool + SEO blog post in one page, which is exactly the format our `/blog/*` posts could adopt for the simulator embeds.
- **Valley Run 2026** ran April 3-5 (Summer edition). SERPs still mostly 2024 coverage; 2026 results haven't widely indexed. This is a content opportunity — a tie-in post would land in a clean SERP.
- **Ultraviolette F99** (10.712s Valley Run 2024, fastest Indian-manufacturer ET) is *not in our catalog*. Adding it covers the Indian-EV-flagship slot before any OEM ships a competing microsite.

## Opportunity boosts queued

Written to `data/market_signals.json`:

| Agent | Boost | Reason |
|---|---|---|
| marketing-content | +12 | Valley Run 2026 + F99 narrative tie-in untouched |
| seo-keyword | +10 | "valley run 2026 results", "ultraviolette f99 quarter mile" uncontested |
| partnership-outreach | +5 | Elite Octane has no software-partner mention |
| catalog-expansion | +3 | Add Ultraviolette F99 to the 342-bike catalog |

Master scheduler will pick these up on next read.

## Escalations

None this week. No competitor matches our positioning closely enough to warrant a `[urgent]` product-prioritisation review. The trend windows above are >30 days but boost values are conservative — no `[opportunistic]` dispatch needed beyond the agents{} signals.

## Don't-do recommendations

- Don't try to outrank US legacy calculator domains on generic "quarter mile calculator" keywords. Stay on India-qualified long-tails.
- Don't position content against DragSim5 by name (different market, different price point, no measurable user overlap).
- Don't add F99 to catalog by faking the spec — Ultraviolette publishes peak power / mass / aero figures; use those + Valley Run timing for benchmark seed only.

## Files written

- `data/competitive_landscape.md` (created; weekly section appended)
- `data/market_signals.json` (overwritten — transient state)
- `reports/competitive_intel_2026-05-26.md` (this file)

## Sources

- https://www.motionsoftware.com/dragsim5.htm
- https://dragcalc.com/
- https://xcceleration.com/et.calculator.html
- https://robrobinette.com/et.htm
- https://www.firgelliauto.com/blogs/engineering-calculators/quarter-mile-et-calculator-trap-speed
- https://eliteoctane.com/valley.html
- https://eliteoctane.com/events.html
- https://www.autocarindia.com/motor-sports-news/valley-run-dates-announced-for-2025-summer-edition-434907
- https://leangp.com/en/
