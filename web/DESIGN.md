# MotoQuant Web — "STAGED" Design System (v4, July 2026)

> Ground-up visual rebuild. This file is THE authority for the v4 site —
> when it disagrees with old page code or with `REDESIGN.md` (Cockpit v3,
> now historical), this spec wins. Every page agent reads this FIRST.

## 0. The idea

**The digital timeslip.** Drag racing has exactly one sacred artifact: the
printed slip the timing booth hands you after a run. The whole site now
reads like that slip — dark asphalt, ruled mono numbers, one volt-green
accent (the green light you launch on), generous space, zero chrome.

Audience: the Indian drag scene — mobile-first riders on R15s, Dukes,
Pulsars and Hayabusas, Instagram/WhatsApp-native, budget-conscious (₹),
racing at Aamby Valley / MMRT / BIC / Kari. They want their number, what
to buy to lower it, and a slip to share. The interface must be simple
enough to use one-handed on a phone at a strip at midnight.

What v4 removes (complexity budget): boot sequences, HUD corner brackets,
scroll-scrubbed manifestos, canvas backdrops, hold-to-launch gates,
seven-segment SVG fonts, scroll-replay telemetry. What replaces them:
typography, whitespace, and three signal colors used with discipline.

## 1. Non-negotiable constraints (inherited, still binding)

1. **`next build` must pass.** Client `useSearchParams()` sits inside
   `<Suspense>` (or reads `window.location` post-mount).
2. **Stat-audit token shapes survive** (`scripts/audit_headline_stats.py`):
   `num: 541, label: 'BIKES'`-style objects, `NNN bikes|parts|tires|venues`,
   `NNN-bike catalog`, `numberOfItems: NNN`, `K5=10.0334s` / `K5 … 10.0334s`
   prose. Canonical numbers (July 2026): **541 bikes · 254 tires · 593
   parts · 20 venues · 4393 tests · 15 sub-models · 221 benchmarks · 82
   within ±0.10s · 137 within ±0.20s · ±0.006s top-10 · +0.021s bias ·
   K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s**. Do NOT invent counts.
   Landing TOP10 == docs/validation TOP10.
3. **Palette bans**: no `gray-*`, no raw Tailwind `orange-N`/`lime-N`, no
   inline hex backgrounds in components. Use `asphalt-*`, `accent`,
   `signal-*`, `white/N` only (legacy `ink-*`/`brand-*` aliases exist so
   untouched pages re-skin — new code never uses them).
4. **Route template stays opacity-only** (`app/template.js`).
5. **Reduced motion**: every animation checks `prefers-reduced-motion`
   (Reveal/Stagger handle it globally; bespoke effects check themselves).
6. **Mobile first-class**: no horizontal overflow, tap targets ≥ 44px,
   sticky bottom `MobileToolBar` survives on tool routes.
7. **Same-origin `/api` rewrite** is architectural — never fetch Render
   directly from the browser (except AuthProvider's documented
   `API_URL_DIRECT` surfaces). `lib/api.js` job-polling resilience
   (fallback, restart-recovery, backoff, abort) survives untouched.
8. **`delta_et_s` sign**: negative = faster = `signal-go` green;
   positive = slower = `signal-foul` red. Trap-speed deltas: positive =
   faster = green.
9. **Honesty**: no fabricated testimonials, ratings, or numbers. DERIVED
   benchmarks stay flagged. "Free during beta" stays accurate.

## 2. Tokens

### 2.1 Color — `tailwind.config.js`

```
asphalt: 0 #07090C (page)  1 #0B0E13  2 #10141B (card)  3 #171C25 (input)
         4 #232A37 (hover lines)
accent:  DEFAULT #C9F231 (volt — THE brand color)  bright #DBFF57 (hover)
         deep #9CBE1E (borders/pressed)
signal:  go #34D97B (success / faster / PB)   stage #FFB224 (running /
         warning / ESTIMATED)                 foul #FF5A48 (error / slower)
mint:    #6FE3B2 (PRO/Studio tier chips ONLY)
```

Text: headings `text-white`, body `text-white/65`, hints `text-white/40`.
Text on accent fills: `text-asphalt-0` (near-black). Legacy aliases:
`ink-0..4 → asphalt`, `brand.orange→accent`, `brand.orangeLight→bright`,
`brand.orangeDeep→deep`, `brand.green/amber/red→signal`, `brand.accent→mint`.

Color discipline: **volt appears once or twice per viewport** — the primary
action and at most one accent detail. Signal colors ONLY carry meaning
(status, delta, tier), never decoration. Everything else is white-on-asphalt.

### 2.2 Type

- **Display: Barlow Condensed** (`--font-display`, weights 500/600/700) —
  motorsport-livery DNA. Headings are UPPERCASE, tight leading:
  h1 `font-display font-bold uppercase text-5xl md:text-7xl leading-[0.95]
  tracking-[-0.01em]`; h2 `text-4xl md:text-5xl` same treatment; card
  titles `text-xl md:text-2xl font-semibold uppercase`.
- **Body: Inter** (`--font-inter`) — never uppercase, `text-white/65`.
- **Data: JetBrains Mono** (`--font-jetbrains-mono`) — ALL numbers, always
  `tabular-nums`. ETs/traps/₹/stats are mono, sized big, weight 500-700.
  The label voice stays `.label-mono` (10px mono uppercase tracked).

Rule of thumb: if it's a **number the rider cares about**, it's mono and
big. If it's a **section name**, it's condensed uppercase. Everything else
is quiet Inter.

### 2.3 Space, radius, borders

Sections `py-16 md:py-24`; containers `max-w-6xl px-6` (workbenches
`max-w-[1400px]`). Cards `rounded-xl p-5 md:p-6` (v4 is squarer than v3 —
`rounded-2xl` only on heroes/modals). Borders `border-white/8`; hover
`border-white/20`; focus ring `accent`. Grids `gap-4 md:gap-6`. Never more
than two stacked surface levels.

## 3. CSS component layer (same class NAMES as v3 — new skin)

Untouched pages (≈50 blog posts) re-skin automatically because the class
API is stable. Implementations change; names don't.

- `.card` — `rounded-xl border border-white/8 bg-asphalt-2/80`.
- `.card-hover` — border-white/20 + subtle lift; reduced-motion-safe.
- `.btn-primary` — **volt fill, near-black text**, `h-11 rounded-lg
  font-display font-bold uppercase tracking-wide`; hover `accent-bright`.
- `.btn-ghost` — white/12 border, white/85 text; hover border-white/30.
- `.btn-danger` — signal-foul tinted outline.
- `.btn-running` — signal-stage tinted (amber = staged/running), hover
  flips to foul (stop affordance).
- `.btn-sm`, `.input-base` (asphalt-3, volt focus ring), `.label-mono`,
  `.skeleton` (shimmer, reduced-motion freezes) — same APIs.

New v4 classes:
- `.timeslip` — the signature result surface: `bg-asphalt-1` with
  perforated (dashed-gradient) top & bottom edges, mono ruled rows
  (`.timeslip-row` = `flex justify-between border-b border-dashed
  border-white/10 py-2 font-mono text-sm`). Used for sim results, /r/[id],
  leaderboard detail.
- `.chip` — `inline-flex h-6 items-center rounded px-2 font-mono text-[10px]
  uppercase tracking-[0.2em]` + tint variants (`.chip-go/.chip-stage/
  .chip-foul/.chip-volt/.chip-mint`).
- `.delta-down` / `.delta-up` — mono delta chips (down=green=faster ET,
  up=red=slower).
- `.centerline` — horizontal dashed divider with a center gap (the strip's
  centerline); section separator.
- `.text-gradient-orange` — kept as alias, now a volt gradient.

## 4. Signature element: StageDots

`components/StageDots.js` — three 6px dots (stage · stage · go): two
`signal-stage`, one `signal-go`. Props: `{ animate=false, className }`.
Static by default; `animate` runs ONE amber→amber→green light-up sequence
on first view (opacity keyframes only, reduced-motion renders static).
Used as: section eyebrows (dots + `.label-mono` text), list bullets,
loading accents. This is the ONLY decorative motif — use it instead of
inventing new ornaments.

## 5. Shared components — keep-API list (re-skin internals ONLY)

`Reveal/Stagger/StaggerItem/Counter`, `ActionButton`, `SimProgress`,
`Skeleton*`, `BikePicker`, `LocationPicker`, `CommandPalette`, `TierBadge`
(+`UpgradeCTA`), `SuggestBikeForm`, `AuthProvider`, `ChatPanel`,
`BuildOptimizer`, `EcuAutotune`, `SimulatorWidget` (KEEP the
`bikeIdMap` catalog-ID self-heal), `AccuracyExplorer`, `SiteNav`,
`SiteFooter`, `MobileToolBar`, `PageHero`, `CodeComment`,
`ScoreboardDigits`/`ScoreboardCounter`.

- **`ScoreboardDigits`** keeps its exact props (`value,h,color,ghost,
  className,label`) but now renders **clean mono digits** (JetBrains,
  tabular, weight 700, sized off `h`) — no more seven-segment SVG. Default
  `color` becomes `#FFFFFF`; callers passing legacy orange get volt via a
  small in-component remap of the old default hex.
- **`PageHero`** keeps its props (`kicker,badge,title,sub,stats,align,
  children`) — new skin: StageDots+label-mono kicker, condensed uppercase
  title, mono stat row, volt glow REPLACED by a plain `.centerline` under
  the header. Kicker copy shifts from "engine-log" voice to plain labels
  (e.g. "MOTORCYCLE DATABASE").
- **`CodeComment`** keeps API; renders as `.label-mono` line with StageDots
  prefix (no blink cursor).
- **`SimProgress`** keeps API (`active,progress,stage,label,compact,edge,
  onStop`); bar fill = volt, running text = signal-stage, cold-start
  escalation caption kept verbatim.

**Delete after landing rebuild** (no other importers): `TronGrid`,
`BootSequence`, `HudFrame` (also unmount from `template.js` if present),
`ManifestoScrub`, `PhysicsDial`, `ChristmasTree`, `LaunchControl`,
`TelemetryHUD`, `SectionRail`.

**Never touch**: `lib/api.js`, `lib/useAsyncTask.js`, `lib/telemetry.js`
logic; `app/api/wake/route.js`; `next.config.js`; `vercel.json` crons.

## 6. Page shell

- **SiteNav** (fixed, `bg-asphalt-0/85 backdrop-blur`): wordmark
  "MOTOQUANT" in Barlow Condensed 700 + a 3-dot StageDots mark. Links:
  Simulator · Optimize · Autotune · Bikes · Leaderboard · Pricing ·
  Resources ▾ (Validation, Docs, Blog, Whitepaper, Features, About). ⌘K
  search button, auth chip, volt CTA "Run a sim". Keep the 1024-1126px
  width fixes (collapse CTA label, hide ⌘K hint in lg..xl band). Mobile:
  drawer + MobileToolBar (5 tools, safe-area).
- **SiteFooter**: 4 columns (Product/Data/Company/Legal), baselines line
  (`K5 10.0334s · R1 10.2859s · Hayabusa 10.4712s`), "Built in India" +
  beta note. Quiet — no glow.
- **template.js**: unchanged concept (opacity fade only); drop the HudFrame
  mount if one exists there.

## 7. Page directions (function is frozen; layout/skin is new)

- **`/` Landing** (full rewrite, ~½ current length): ① Hero — left:
  StageDots eyebrow, H1 "KNOW YOUR TIME BEFORE YOU STAGE", one-line sub
  (physics sim · 541 bikes · Indian strips · free during beta), CTAs
  [Run a sim → /simulator] [Browse 541 bikes → /bikes]; right (lg+):
  live `SimulatorWidget` in a `.card`. Backdrop: single static
  radial volt tint ≤6% + vertical centerline — no canvas, no boot, no
  scroll-scrub. ② Stat strip (6 mono stats, audit shapes). ③ "How it
  works" — 3 steps (Pick your bike / Set your strip / Get your slip)
  ending in a mini `.timeslip`. ④ Tool cards (Simulator, Build Optimizer
  ₹, ECU Autotune, AI Chat deep-link) + row links (Bikes DB,
  Leaderboard). ⑤ Proof — 4 accuracy tiles + TOP10 table (== docs/
  validation) + 3 reference-baseline cards + link /validation. ⑥ "Built
  for the Indian strip" — venues, INR parts, Dragy import, WhatsApp
  share. ⑦ Short FAQ (from faqSchema copy). ⑧ CTA band. KEEP: EXP-001/
  EXP-018 variant hooks (read `?variant`/`?exp18` the same way),
  telemetry calls, `id="main"`, skip-link target, JSON-LD via layout.
- **`/simulator`**: restyle IN PLACE — this is a 2000-line stateful
  workbench; change classes/layout containers/copy, never handlers,
  state, effects, or fetch logic. Two-pane lg+ (left inputs stack, right
  sticky results), results render as `.timeslip`. Keep: all 5 job ops,
  Live/Manual toggle, share links, save-run, Dragy/dyno upload, ChatPanel
  tab, EXP-003.
- **`/optimize` + `/autotune`**: PageHero + the re-skinned tool component,
  two-column card layout, results with `.delta-*` chips (negative ET delta
  = green). Budget presets as `.chip`s.
- **`/bikes`**: search + facet dropdowns unchanged logic; cards become
  clean spec rows (name condensed, numbers mono); pagination; suggest-a-
  bike modal.
- **`/bikes/[id]`**: spec sheet as ruled mono tables; CTAs to simulator/
  optimizer with `?bike_id=`; keep generateMetadata layout untouched.
- **`/leaderboard`**: rows as timeslip strips (rank, bike, ET mono-large,
  trap, venue chip) linking to `/r/[id]`; venue filter; house reference
  runs when empty.
- **`/r/[id]`**: THE showcase — full-page `.timeslip`: header
  "MOTOQUANT TIMING ASSOC · OFFICIAL SLIP", venue/date, giant mono ET,
  split rows (60ft/330/⅛/1000ft/¼), trap, share button. WhatsApp-first.
- **`/validation`**: PageHero + re-skinned AccuracyExplorer (volt/signal
  palette swap inside the SVGs; same data + a11y tables).
- **`/login` `/account` `/pricing`**: same flows/endpoints/states;
  cleaner single-card auth, account as stacked cards (Garage table mono),
  pricing matrix with mint tier chips; beta ribbon logic kept.
- **Content pages** (`/features /about /whitepaper /docs/* /blog /terms
  /privacy`): inherit new shell + PageHero automatically; light copy/skin
  pass only. Blog POST bodies untouched (audit tokens live there).
- **`error.js` / `not-found.js`**: red-light theme retained but minimal —
  StageDots with the red lit, mono caption, product routes.

## 8. Motion doctrine (the simplicity contract)

Entrance: `Reveal`/`Stagger` opacity+12px only, ≤0.6s. Signature: ONE
StageDots light-up per page (hero). Progress: SimProgress bars are the
only continuous animation. Hover: border/color + ≤2% scale on buttons.
NOTHING else animates. No parallax, no scroll-driven values, no canvas,
no springs on decorative elements. `prefers-reduced-motion` disables all
of the above (bars still fill — that's information).

## 9. Verification gates

1. `npm run verify` + `npm run build` green (all routes).
2. `python scripts/audit_headline_stats.py` → "in sync".
3. Grep gates: no `gray-`, no `bg-[#`, no `text-orange-` in app/ or
   components/; no imports of deleted components anywhere.
4. Playwright (or manual) pass: every key route renders at 1440 and 390
   with zero console errors and zero horizontal overflow; progress bars
   move; Stop works; share/save work.
5. `og-image.png` + icons regenerated to the volt/asphalt brand via
   `scripts/generate_brand_assets.py` (update its token constants).
