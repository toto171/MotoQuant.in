# Production agent library

Twelve specialised agents that the master scheduler dispatches for routine work. Each is a self-contained markdown prompt template designed to be passed to an `Agent` tool call.

## Agents

| File | Agent | When |
|---|---|---|
| `catalog-expansion.md` | A1 | Mon (default) — adds 1-3 new bikes to the catalog |
| `physics-calibration.md` | A2 | Wed (default) or on Dragy upload — tunes per-cluster knobs |
| `benchmark-import.md` | A3 | Tue (default) — adds new validated ETs to BENCHMARKS |
| `marketing-content.md` | A4 | Mon/Fri (default) — drafts a blog post |
| `seo-keyword.md` | A5 | Mon (default) — surfaces keyword opportunities + on-page tweaks |
| `competitive-intel.md` | A6 | Tue (default) — refreshes data/competitive_landscape.md + market_signals.json |
| `product-prioritisation.md` | A7 | Thu (default) — re-ranks Phase 6/7 carry-forward |
| `customer-support.md` | A8 | Thu (default) — triages bike_suggestions, drafts responses |
| `technical-debt-pass.md` | A9 | Wed/Sat alternating — narrow refactor PR |
| `performance-monitor.md` | A10 | Sun (default) — Lighthouse + Railway latency drift report |
| `growth-experiments.md` | A11 | Fri (default) — proposes one A/B-able UI/copy variant |
| `partnership-outreach.md` | A12 | Fri biweekly — drafts outreach email templates |

Plus 2 meta-agents:

| File | Agent | When |
|---|---|---|
| `self-review.md` | M1 | Sun (default) — weekly STATUS.md digest + scheduler weight tuning |
| `incident-postmortem.md` | M2 | On INCIDENT — root-cause analysis |

## Output convention

Each agent writes deliverables to a specific path in the repo (declared in its prompt's "Deliverable" section). Common patterns:

- Code changes → directly into source tree (e.g. `motoquant/scraper/known_bikes.py`)
- Reports → `reports/<agent>_YYYY-MM-DD.md`
- Data updates → `data/<topic>.json`
- Drafts → `web/app/blog/<slug>/page.js`, `outreach/templates/<topic>.md`

The master_scheduler reads each agent's deliverable section to auto-build the postflight `--files` list.

## Style guide for prompts

- **Front-load the goal** — first sentence states the deliverable.
- **List both the focus AND the don't-do.** LLM agents drift toward over-engineering without a clear "leave alone" list.
- **Cap word count.** Each agent should produce something concrete in <2 hours of equivalent human effort.
- **Always reference CLAUDE.md** — it's the project bible.
- **Always specify a deliverable file path.** No "report findings" — write them somewhere.
- **Always include a "what to escalate" section.** When the agent should defer to a human via DISPATCH_INBOX.
