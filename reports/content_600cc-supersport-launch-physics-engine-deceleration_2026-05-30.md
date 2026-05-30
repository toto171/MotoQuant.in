# Content Report — 600cc Supersport Calibration Story (2026-05-30)

## Agent
A4 marketing-content

## Slug
`600cc-supersport-launch-physics-engine-deceleration`

## URL
https://www.motoquant.in/blog/600cc-supersport-launch-physics-engine-deceleration

## Title
Why 600cc Supersports Were Running 200ms Slow in Our Sim

## Topic priority resolution
Today's `reports/physics_calibration_2026-05-30.md` shipped a substantive
cluster-level fix (`max_engine_decel_rads2` 150 → 600 on the
`mid_twin_500_700` profile, cluster bias collapsed from +0.207s to +0.029s,
mean |Δ| 0.211s → 0.130s). Per the prompt's priority list this beats a
single-bike deep-dive on today's catalog adds (KLR 650 / Tiger 900 GT Pro /
CRF250L — all already covered or low-traffic). The "what changed and why"
angle is the strongest play.

## Target keywords
Primary:
- `600cc supersport quarter mile`
- `yzf r6 quarter mile bias`
- `motoquant physics calibration`

Secondary:
- `gsx-r 600 k6 simulator accuracy`
- `cbr600rr 2013 quarter mile`
- `engine deceleration launch physics`
- `clutch slip phase 600cc inline four`
- `crankshaft inertia 600cc inline four`
- `max engine decel rads2`

## Expected traffic notes
- Genuinely high-intent technical query: people search "why is my sim slow"
  or "GSX-R 600 quarter mile time" and end up here.
- Tail-heavy: each individual long-tail keyword (e.g. `gsx-r 600 k6
  simulator accuracy`) is low volume but combined the set should pull a
  steady technical-credibility tier of traffic.
- Doubles as a credibility piece for power users — first-principles
  physics + before/after benchmark tables + open carry-forwards is the
  exact pattern that wins B2B Pro Studio leads.
- Internal-linking play: 600cc supersport content gets a dedicated cluster
  (GSX-R 600 K8 post + this calibration post + future per-bike R6/CBR
  deep-dives) which Google rewards.

## Internal-link plan
Outbound from this post:
1. `/blog/suzuki-gsx-r600-k8-quarter-mile-physics` (sister 600cc post)
2. `/blog/how-the-motoquant-physics-engine-works` (engine-detail backup)
3. `/blog/the-physics-of-a-perfect-launch` (launch-phase deep dive)
4. `/blog/how-to-tune-for-mmrt-chennai` (sea-level strip = where 600cc
   supersports hit Sport Rider numbers)
5. `/bikes` (catalog)
6. `/pricing` (commercial CTA)

Future inbound additions (next sessions):
- The GSX-R 600 K8 post should be back-linked to this calibration post
  (mention "updated 30 May 2026 — re-baselined per cluster fix").
- Any per-bike R6 or CBR600RR deep-dive should link here as the
  validation-band justification.

## Word count
~2,150 words in `CONTENT` array (under the 1500-2500 target band).

## Source verification
Every factual claim cross-referenced to `reports/physics_calibration_2026-05-30.md`:

| Claim in post | Source |
|---|---|
| 8 bikes / 7-of-8 sim-slow / +0.207s bias | Report § "Worst per-bike deltas" |
| Per-bike before/after deltas in second table | Report § "Per-Bike Verification" |
| max_engine_decel_rads2 probe results (150→1200 sweep) | Report § "Hypothesis" |
| Why 150 was wrong / crank inertia ~0.0065 kg·m² | Report § "Why this knob is the right physics lever" + inertia bands documented in physics.py |
| K5 / R1 / Hayabusa preservation | Report § "K5/R1/Hayabusa Preservation Proof" |
| Top-10 mean |Δ| 11.4ms → 9.4ms | Report § "Top-10 |Δ| Check" |
| Cross-cluster regression max +8ms on litre-sport-600-1000 | Report § "Before/After Cluster Bias Table" |
| Recommendations for cruiser-1300+ cluster next | Report § "Recommendations for Next Sessions" item 1 |
| Open items: mu_peak_override + chain_efficiency_override wiring | Report § "Recommendations" item 4 |

Engine-inertia numbers (Z650 ~4.8 kg crank / 0.011 kg·m²; R6 ~2.4 kg crank
/ 0.0065 kg·m²; supersport instantaneous ~1800 rad/s² during clutch
engagement) are physics-engineering ballpark estimates consistent with
public dyno-bench writeups; not directly cited from a magazine but flagged
in the post as "approximate" / "roughly" so the reader knows the precision
band.

## Validation gates passed
- [x] `npx prettier --check` on both new files + modified sitemap + modified
      blog/page.js — `All matched files use Prettier code style!`
- [x] Anti-slop phrase scan returns zero matches: `delve / navigating /
      fast-paced / game-changer / unleash / unlock the potential / the
      realm of / it's important to note / the world of motorcycling`
- [x] Sitemap entry added with priority 0.86 (above suzuki-gsx-r600-k8
      at 0.84 — fresh content gets a bump)
- [x] Blog index POSTS array prepended (most-recent-first ordering)
- [x] Blog index keywords array extended with 6 calibration-specific
      long-tails

## Files touched
1. `web/app/blog/600cc-supersport-launch-physics-engine-deceleration/page.js` (NEW)
2. `web/app/blog/600cc-supersport-launch-physics-engine-deceleration/layout.js` (NEW)
3. `web/app/sitemap.js` (added route)
4. `web/app/blog/page.js` (added POSTS entry + 6 keywords)
5. `reports/content_600cc-supersport-launch-physics-engine-deceleration_2026-05-30.md` (this report)

## Outcome
Production-ready blog post shipped. ~2150 words, 13 min read, 2 inline
data-tables, 2 callouts, 6 internal links (4 to other blog posts, 1 to
/bikes, 1 to /pricing), simulator CTA wired to a working bike slug
(`yamaha-yzf-r6-13s-2008`). Prettier clean, anti-slop clean.
