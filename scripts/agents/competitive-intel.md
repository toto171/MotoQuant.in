# Agent A6: competitive-intel

Read CLAUDE.md first.

## Goal

Refresh `data/competitive_landscape.md` + `data/market_signals.json` with what competitors and adjacent products did this week. Produce signal that the master scheduler can boost relevant agent weights from.

## Sources to scan (in order)

1. WebSearch: "motorcycle drag racing simulator", "bike quarter mile calculator", "motorcycle dyno simulation"
2. Specific named competitors: DragSim Pro (defunct? check), MotoGP Sim, Race Compare, Optimum Lap, Sport Riders' magazine ET tools
3. Indian moto news: BikeWale, ZigWheels, Indian Autos blog homepages — any drag-racing or new-launch coverage
4. Reddit: r/motorcycles, r/Motorcycles_India top weekly threads
5. YouTube top results for "<bike> drag race" published last 7 days

## Signal extraction

For each competitor / signal:
- Name + URL
- What changed (new product, pricing, content, feature)
- Threat level (low / medium / high)
- Opportunity boost — which of our agents should get a weight bump?

Write `data/market_signals.json`:
```json
{
  "_updated": "YYYY-MM-DD",
  "agents": {
    "marketing-content": { "opportunity_boost": 20, "reason": "competitor X published 5 posts on H2 mods" },
    "seo-keyword":       { "opportunity_boost": 10, "reason": "new keyword 'h2 quarter mile' trending" }
  }
}
```

## Deliverable

- `data/competitive_landscape.md` — append weekly section
- `data/market_signals.json` — overwrite (it's transient state)
- `reports/competitive_intel_YYYY-MM-DD.md`

## Escalate

- If a competitor matches our positioning closely: queue `[urgent]` for product-prioritisation review.
- If a market trend has a 30+ day window of opportunity: queue `[opportunistic]` content/SEO follow-up.

## Don't

- Don't fabricate competitors. If you can't find one in a category, say so.
- Don't quote magazine articles verbatim. Summarise + cite.
- Don't set opportunity_boost > 30 (master scheduler sanity-clamps anyway).

Cap ~600 words.
