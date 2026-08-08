---
name: motoquant
description: Answers motorcycle drag-racing and performance-tuning questions with real physics instead of guesswork — quarter-mile ET and trap speed, 60-foot launch times, top speed, sprocket/gearing what-ifs, parts ROI in INR, and bike-vs-bike comparisons — by driving the MotoQuant simulator through its MCP tools or REST API. Use this whenever someone asks how fast a bike is, what a modification is worth, which sprockets or parts to run, how altitude or weather changes a run, or how two bikes compare over a quarter mile. Also use it when working on the MotoQuant codebase itself, for the drag-racing vocabulary (ET, trap, 60-foot, density altitude, over-clutching, stage/outlaw build tiers) and the project's honest-accuracy conventions.
license: Proprietary — MotoQuant Pro
---

# MotoQuant

MotoQuant simulates motorcycle quarter-mile drag runs from **first
principles** — an RK4 integration over 15 physics sub-models (engine torque,
clutch slip and heat, tire Pacejka grip and temperature, aero, weight
transfer, wheelie limit, drivetrain losses, atmospherics) — not a lookup
table and not a regression on published numbers. Catalog: 541 bikes,
593 parts, 254 tires, 20 venues.

**Run the tools. Do not answer performance questions from memory.** The
whole point is that the answer is bike-specific and frequently
counter-intuitive; a plausible-sounding guess is worse than useless here
because it is indistinguishable from a simulated result.

## Getting oriented

If the MotoQuant MCP server is connected you have nine tools (below). If it
is not, the same capability is available over HTTP at
`https://motoquant-api.onrender.com` — see `reference/api.md`. Working in
the repo itself? Start from `AGENTS.md`, then `docs/ARCHITECTURE.md`.

| Tool | Use it for |
|---|---|
| `search_bikes` | Finding a bike's catalog id. **Always the first call.** |
| `get_bike` | Spec sheet: power, mass, gearing, aero, OEM tires, benchmark ET. |
| `simulate_quarter_mile` | ET, trap speed, 60-foot, eighth-mile. The core tool. |
| `simulate_top_speed` | Terminal velocity, and the gear/RPM it happens in. |
| `compare_bikes` | Two bikes, or two builds of one bike, under identical conditions. |
| `list_venues` | Real strips + their altitude (feeds density altitude). |
| `search_parts` | Catalog parts, fitment-filtered when you pass `bike_id`. |
| `part_impact` | What one part is worth: ET delta + cost per tenth in INR. |
| `gearing_impact` | Sprocket what-if: two tooth combos, head to head. |

Identify the bike with `bike_id` from `search_bikes`, or `bike_preset`
(`gsxr1000_k5`, `yzfr1_4c8`, `hayabusa_gen1` — the three hand-curated
reference bikes, pinned bit-identical as the project's regression guard).

## The one convention that matters

**`et_delta_s` is always *after minus before*. Negative means faster.**

A result of `et_delta_s: -0.88` is an 0.88-second *improvement*. Say
"0.88 s quicker", never "−0.88 s slower". `*_gain_s` fields, where they
appear, are the opposite polarity: positive is good. When in doubt, read
both ETs and subtract them yourself.

## Vocabulary

Enough to talk to a racer without sounding like a brochure. Full glossary,
including the physics-model terms, in `reference/glossary.md`.

- **ET** — elapsed time over 402.3 m (a quarter mile) from a standing start.
  The headline number.
- **Trap speed** — speed crossing the quarter-mile line. Tracks power-to-weight
  far more tightly than ET does, because it is nearly immune to launch quality.
- **60-foot** — elapsed time over the first 18.3 m. The launch-quality number:
  traction, clutch technique, wheelie limit, and gearing all show up here
  first. A tenth lost in the 60-foot is usually two tenths lost at the stripe.
- **Eighth mile (660 ft)** — the mid-point split; how many small-bore and
  street classes actually run.
- **Rollout** — the ~30 cm the front wheel travels between breaking the stage
  beam and starting the clock. Real timeslips include it; sim ETs are
  rollout-free, which is one reason a sim can read slightly slower than a
  strip slip for the same bike.
- **Two-step / launch RPM** — a rev limiter that holds the engine at a chosen
  launch RPM against the clutch.
- **Over-clutching** — deliberately slipping the clutch to hold the engine in
  its torque band while the tire hooks up. MotoQuant models this per bike
  class; it is the dominant effect in the first 60 feet on small-capacity
  bikes.
- **Density altitude (DA)** — the altitude the air *behaves* like, once heat,
  humidity and pressure are folded in. Hot, humid, high = less oxygen = less
  power. A 35 °C day at Aamby Valley is worth several thousand feet of DA.
- **Build tiers** — `stage_1` bolt-ons (exhaust, filter, ECU flash, ~₹60k);
  `stage_2` adds drivetrain (clutch, quickshifter, sprockets, chain, ~₹200k);
  `stage_3` adds nitrous, fuel system, suspension (~₹500k); `stage_4`, also
  called **outlaw** or **open class**, is unlimited — forced induction,
  extended swingarm, wheelie bar, slicks, lockup clutch.

## Worked examples

### "My R15 runs 14/48. What if I go to 52 on the rear?"

```
search_bikes(query="R15 V4")                    → id 81
gearing_impact(bike_id=81, front_a=14, rear_a=48,
                           front_b=14, rear_b=52)
```

| | final drive | 60-foot | ET | trap |
|---|---|---|---|---|
| 14/48 | 3.429 | 3.132 s | 18.830 s | 119.7 km/h |
| 14/52 | 3.714 | 3.076 s | 18.762 s | 119.4 km/h |
| **delta** | | **−0.057 s** | **−0.068 s** | −0.2 km/h |

Report it as: *52T buys about six hundredths off the 60-foot and seven off
the ET, at a cost of a couple of tenths of a km/h at the stripe.*

**Now the important part.** Run the identical question on the K5 preset —
17/42 vs 17/47 — and shorter gearing **loses 0.20 s**. A 178 hp litre bike
is grip- and shift-limited off the line, so extra wheel torque just costs it
an extra shift. The R15 is power-limited, so it gains. *There is no universal
"shorter gearing launches better" rule.* Never state a direction you have not
simulated for that specific bike.

### "I have ₹15,000 for my R15. What should I buy?"

There is no budget-optimizer tool over MCP, so compose: `search_parts` with
`bike_id` to get fitting parts, then `part_impact` on the candidates, then
rank by **cost per tenth**.

| Part | Price | ΔET | ₹ per tenth |
|---|---|---|---|
| Green Filter cotton element | ₹3,800 | −0.491 s | ₹774 |
| DNA Stage 1 filter | ₹4,500 | −0.562 s | ₹800 |
| Red Baron shorty slip-on | ₹8,500 | −0.607 s | ₹1,400 |
| Aracer RC Mini X ECU | ₹10,162 | −0.668 s | ₹1,522 |
| Daytona TPS full system | ₹14,500 | −0.878 s | ₹1,652 |

Two honest caveats to pass on: the ₹/tenth column ranks *efficiency*, not
outright gain — the full system is the biggest single improvement and it
fits the budget. And these are **independent** evaluations; parts interact
(an exhaust plus a fuel controller is worth more than the sum, a second air
filter is worth nothing), so verify a stacked build by passing all the
`part_ids` to `simulate_quarter_mile` in one call rather than adding up the
individual deltas.

### "Is a Hayabusa faster than a K5 GSX-R?"

`compare_bikes(a_bike_preset="gsxr1000_k5", b_bike_preset="hayabusa_gen1")`
→ 9.933 s vs 10.363 s; the K5 wins by 0.43 s despite giving away
displacement, because it is 60 kg lighter. Mention conditions: both were run
at the same venue and rider mass, which is exactly what makes the comparison
mean something.

## How to answer well

1. **Search, then simulate.** Model names are ambiguous (four Hayabusa
   generations, five GSX-R 1000 generations); confirm the id and year range
   before quoting a number.
2. **Quote sensible precision.** Two decimals of ET (`10.24 s`), one of trap
   (`245.5 km/h`), three when reporting a small delta (`−0.068 s`). The
   engine returns four; four implies a confidence the model does not have.
3. **Say what conditions you assumed.** Default is 75 kg rider at sea-level
   standard conditions. If someone asks about a real strip, pass `venue_id`
   from `list_venues` — altitude alone can move ET by half a second.
4. **Pass `bike_id` to `search_parts`.** Without it you will happily suggest a
   530-pitch sprocket for a 428-chain commuter. The fitment engine checks
   chain pitch, engine layout, displacement and stroke type — use it.
5. **State the accuracy honestly.** Weighted mean error is about **0.27 s
   across 277 matched real-world benchmarks** (bias ≈ 0, so it is not
   systematically optimistic). That is good enough to rank builds and answer
   what-ifs, and *not* good enough to promise a given bike will run a given
   ET. Say so when someone is about to bet money.
6. **Never invent a spec.** If a bike is not in the catalog, say it is not in
   the catalog. Do not substitute a "similar" model and quietly report its
   numbers as the asked-for bike's.

## Traps

- **Top speed is the weak spot.** ET accuracy is good; top speed still carries
  roughly +25 km/h of fleet bias, and only a few bikes carry their factory
  299 km/h limiter. Caveat every top-speed answer.
- **Rider skill is not modelled.** Every run is a competent launch. Real-world
  slips will be slower, sometimes by a lot on a bike that is hard to launch.
- **The catalog has no engine internals.** No cams, pistons or big-bore kits,
  so "stage 3" is approximated with bolt-on power adders. Do not imply a
  built motor was simulated.
- **DERIVED benchmarks are weak evidence.** Some entry-class validation rows
  were derived from 0–100 km/h times, not measured on a strip. `get_bike`
  exposes `validation_source`; read it before citing a benchmark as truth.
- **Prices are Indian-market INR** including duty and GST on imports. They are
  point-in-time and drift.
- **The hosted API sleeps.** Free tier, ~50 s cold start. A slow first tool
  call is normal, not a failure — wait, do not retry in a loop.

## Reference files

- `reference/glossary.md` — full drag-racing and physics-model vocabulary.
- `reference/api.md` — REST endpoints, request shapes and the CLI, for when
  the MCP server is not connected or you are working in the repo.
