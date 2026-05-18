# SEO Audit — 2026-05-18 (seventh pass)

## Run history today

| Pass | Slot      | Scope |
|------|-----------|-------|
| 1    | morning   | 9 WebSearch queries on India buyer-intent; tweaks on `/simulator`, `/bikes`, R15 blog, Hayabusa-vs-ZX-14R blog, root layout. |
| 2    | afternoon | Catalog-driven mining for May 2026 adds; tweaks on `/pricing`, `/features`, blog layout. |
| 3    | evening   | NS400Z marked done; +5 opps; +3 marketing-content escalations. |
| 4    | late evening | +2 opps (Hunter 350, validation-authority); `/docs/physics`, `/docs/validation`, `/about`, `/whitepaper` keyword expansion. |
| 5    | night     | +4 opps (3 new bikes + database-pattern); `/bikes` H1 rewrite; `/features`, `/pricing` keyword expansion. |
| 6    | late-night | ZX-4R marked done; +3 opps; simulator keyword expansion; FAQ + landing-tile entity injection. |
| 7    | this run  | +5 opps from fresh-gap WebSearch; on-page edits on `/simulator`, `/features`, R15 blog, StructuredData FAQ. |

## Pass 7 scope (this run)

Six prior passes saturated metadata on every server-rendered surface owned by this agent. Pass 7 targets fresh SERP gaps not yet logged in `data/seo_opportunities.json`:

1. **Honda Hornet 2.0 vs Pulsar NS200 drag** — carblogindia documents a head-to-head where the NS200 wins both rounds; the SERP is dominated by YouTube and spec-comparison pages, with no physics-based written analysis. High India volume.
2. **Kawasaki Ninja 400 quarter mile India** — ~12.98s @ 102 mph published globally (FastestLaps, AccelerationTimes, MotoStatz); India-assembled at Chakan since 2018; no India-specific drag piece exists. Pairs with the existing ZX-4R post.
3. **Honda CBR150R quarter mile** — Honda 2026 spec: 149.2cc / 16.32 PS / top-speed 136 km/h / 0–100 ~13s. SE Asia + India 149cc fully-faired segment leader. SERP has spec pages with empty quarter-mile cells.
4. **Kari Motor Speedway drag racing** — per Wikipedia the Kari site hosted drag racing in the late 1990s before B. Vijay Kumar built the permanent F3 circuit in 2002. Nobody is currently surfacing this dual identity for drag intent. Tamil Nadu / Coimbatore tuner outreach hook.
5. **ECU flash motorcycle India cost** — SERP is international tuners (Brock's, Woolich, 2 Wheel DynoWorks) with USD pricing. India buyer-funnel gap: no cost-per-tenth comparison of Powertronic (India), Bazzaz, Dynojet PCV, and Woolich on common Indian bikes.

## WebSearch queries (this pass)

| # | Query | Key finding |
|---|---|---|
| 1 | honda cbr150r quarter mile time india 2026 drag | No instrumented ET in SERP; spec pages only. |
| 2 | best ecu flash motorcycle india cost gains 2026 | SERP = international tuners, USD pricing, no India-specific cost-per-tenth comparison. |
| 3 | kari motor speedway coimbatore drag racing motorcycle | Wikipedia confirms drag-racing heritage at the Kari site (late 1990s, pre-circuit). |
| 4 | budh international circuit drag racing motorcycle quarter mile 2026 | No drag events documented; BIC is a road-racing venue. Confirms our existing BIC framing is correct. |
| 5 | cost per tenth motorcycle drag racing mods budget | SERP is US/NHRA Pro Mod content; no India-budget cost-per-tenth content. Defensible angle for ECU-flash post. |
| 6 | honda hornet 2.0 vs pulsar ns200 quarter mile drag race india | Carblogindia + MotorBeam confirm NS200 wins; SERP is YouTube + spec compare. |
| 7 | "quarter mile calculator" motorcycle physics simulator 2026 | Competitors all use power-to-weight formula; physics-based differentiator confirmed. |
| 8 | kawasaki ninja 400 quarter mile time india drag | ~12.98s/102 mph global, India-assembled, no India-specific drag piece. |

## Opportunities added (5 new, priorities 29–33)

| P | Keyword | Vol (IN) | Target | Action |
|---|---|---|---|---|
| 29 | honda hornet 2.0 vs pulsar ns200 drag | high | /blog/...ns200-vs-apache-rtr-200... | create-blog-later |
| 30 | kawasaki ninja 400 quarter mile india | med-high | /bikes | create-blog-later |
| 31 | honda cbr150r quarter mile | med | /bikes | create-blog-later |
| 32 | kari motor speedway drag racing | low-med | /simulator?venue=kari | tweak-existing |
| 33 | ecu flash motorcycle india cost | med-high | /features | tweak-existing |

Total in `data/seo_opportunities.json` after pass: **33 opportunities**, **11 escalations**.

## On-page edits (4 files)

1. **`web/app/simulator/layout.js`** — keywords array 20 → 24 entries. Added `kawasaki ninja 400 quarter mile india`, `honda hornet 2.0 drag`, `honda cbr150r drag time`, `kari motor speedway drag`. Title / description / canonical untouched.

2. **`web/app/features/layout.js`** — keywords array 15 → 18 entries. Added `hornet 2.0 vs ns200 drag`, `kawasaki ninja 400 india drag`, `ecu flash cost india motorcycle`. Title / description / canonical untouched.

3. **`web/app/blog/why-your-r15-wont-hit-14s/page.js`** — keywords array 8 → 10 entries. Added `r15 vs ns200 drag`, `r15 vs hornet 2.0` to capture the 150cc-vs-200cc comparison cluster. Title / description / canonical / H1 untouched.

4. **`web/app/StructuredData.js`** — Indian drag-strips FAQ answer expanded with Kari's drag heritage (per Wikipedia: "hosted drag events in the late 1990s before the permanent circuit was built"). Bike count / venue list / structure unchanged.

## Escalations queued (2 new)

- **marketing-content**: Kawasaki Ninja 400 vs Ninja ZX-4R quarter-mile physics — parallel twin vs inline-four at 400cc. Architecture-pair post format (similar to MT-125/XSR125).
- **marketing-content**: ECU flash India cost — Powertronic vs Bazzaz vs Dynojet PCV vs Woolich, by cost-per-tenth on common Indian bikes. B2B Pro-tier buyer-funnel content; unique to MotoQuant because of the catalog + sim.

## Verification

- JSON syntax valid (`json.load` parse OK; 33 opportunities, 11 escalations).
- All 4 edited files have balanced braces and brackets.
- "342 bikes" claim preserved on every surface touched.
- Canonical URLs untouched; no slug changes.
- StructuredData schema structure unchanged (text-only edit inside one FAQ answer).
- No `/blog/*` index, `/sitemap.js`, or main blog post structural edits — marketing-content owns those.
- Anti-slop phrase scan: clean (none of "delve into", "navigating the complex", "in today's fast-paced", "embark on", "leverage", "robust", "seamless", "harness" appear in any edited file).
- All factual claims sourced: Hornet vs NS200 from carblogindia + MotorBeam; Ninja 400 ET from FastestLaps + AccelerationTimes + MotoStatz; CBR150R specs from mototechindia + Wikipedia + BikeWale; Kari drag heritage from Wikipedia (en.wikipedia.org/wiki/Kari_Motor_Speedway).
