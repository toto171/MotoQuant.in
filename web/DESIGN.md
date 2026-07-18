# MotoQuant Web — "IGNITION" Design System (v5, July 2026)

> The orange cockpit identity, rebuilt flagship on the v4 structural
> architecture. This file is THE authority — when it disagrees with old
> page code, with `REDESIGN.md` (Cockpit v3) or with v4 (STAGED) remnants,
> this spec wins. Every page agent reads this FIRST.
>
> v5 = v4's simplicity (timeslip artifact, two-pane workbench, tool-first
> IA, no decoration chrome) re-voiced in the brand's real identity:
> **MotoQuant_Identity_Kit** (the "redline Q" mark, Ink #0A0A0B, Signal
> #FF5E1F, Space Grotesk 700). Web, app and logo speak one voice.

## 0. The idea

**The digital timeslip, in cockpit orange.** Drag racing has exactly one
sacred artifact: the printed slip the timing booth hands you after a run.
The whole site reads like that slip — carbon-ink night, ruled mono numbers,
one signal-orange accent (the needle past redline), generous space, zero
chrome. The seven-segment timing-board numerals return for hero figures:
strip scoreboards are OUR pixel font.

Audience: the Indian drag scene — mobile-first riders on R15s, Dukes,
Pulsars and Hayabusas, Instagram/WhatsApp-native, budget-conscious (₹),
racing at Aamby Valley / MMRT / BIC / Kari. They want their number, what
to buy to lower it, and a slip to share. The interface must be simple
enough to use one-handed on a phone at a strip at midnight.

What stays removed (complexity budget, since v4): boot sequences, HUD
corner brackets, scroll-scrubbed manifestos, canvas backdrops,
hold-to-launch gates, scroll-replay telemetry. What replaces them:
typography, whitespace, and three signal colors used with discipline.

## 1. Non-negotiable constraints (inherited, still binding)

1. **`next build` must pass.** Client `useSearchParams()` sits inside
   `<Suspense>` (or reads `window.location` post-mount).
2. **Stat-audit token shapes survive** (`scripts/audit_headline_stats.py`):
   `num: 541, label: 'BIKES'`-style objects, `NNN bikes|parts|tires|venues`,
   `NNN-bike catalog`, `numberOfItems: NNN`, baseline prose. Canonical
   numbers (July-13 2026 epoch): **541 bikes · 254 tires · 593 parts · 20
   venues · 4393 tests · 15 sub-models · 250 benchmarks (277 matched) · 74
   within ±0.10s · 137 within ±0.20s · ±0.009s top-10 · +0.017s bias ·
   K5 9.9331s / R1 10.1436s / Hayabusa 10.3633s**. Do NOT invent or alter
   counts — reuse existing constants. Landing TOP10 == docs/validation.
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
asphalt: 0 #050506 (page)  1 #0A0A0B (kit Ink / timeslip)  2 #111113 (card)
         3 #1A1A1D (input)  4 #27272A (hover lines)
accent:  DEFAULT #FF5E1F (Signal — THE brand color)  bright #FF8F57 (hover)
         deep #CC4000 (borders/pressed)
signal:  go #22C55E (success / faster / PB)   stage #F59E0B (running /
         warning / ESTIMATED)                 foul #EF4444 (error / slower)
mint:    #00FFB2 (PRO/Studio tier chips ONLY)
```

Text: headings `text-white`, body `text-white/65`, hints `text-white/40`.
Text on accent fills: `text-asphalt-0` (near-black). Legacy aliases:
`ink-0..4 → asphalt`, `brand.orange→accent`, `brand.orangeLight→bright`,
`brand.orangeDeep→deep`, `brand.green/amber/red→signal`, `brand.accent→mint`.

Color discipline (the kit rule): **orange is reserved for the moving
part(s)** — the primary action, live data, at most one accent detail per
viewport. Signal colors ONLY carry meaning (status, delta, tier), never
decoration. Everything static is white or ink.

### 2.2 Type

- **Display: Space Grotesk** (`--font-display`, weights 500/600/700) — the
  identity kit's wordmark face. Headings are **sentence case**, never
  uppercase: h1 `font-display font-bold text-4xl md:text-6xl
  tracking-tight`; h2 `text-3xl md:text-4xl font-bold tracking-tight`;
  card titles `text-lg md:text-xl font-semibold`. Orange lives INSIDE the
  heading as a `text-accent` (or `.text-gradient-orange`) span on the one
  load-bearing word — the QUANT pattern from the lockup.
- **Body: Inter** (`--font-inter`) — never uppercase, `text-white/65`.
- **Data: JetBrains Mono** (`--font-jetbrains-mono`) — ALL numbers, always
  `tabular-nums`. The label voice stays `.label-mono` (10px mono uppercase
  tracked). HERO numbers (headline ETs, marquee stats) render on the
  restored seven-segment `ScoreboardDigits`/`ScoreboardCounter` (default
  orange); table/inline numbers stay plain mono.

Rule of thumb: if it's a **number the rider cares about**, it's mono (or
seven-seg when it's the hero of its panel). If it's a **section name**,
it's Space Grotesk sentence case. Everything else is quiet Inter.

### 2.3 Space, radius, borders

Sections `py-16 md:py-24`; containers `max-w-6xl px-6` (workbenches
`max-w-[1400px]`). Cards `rounded-xl p-5 md:p-6`; buttons/inputs
`rounded-xl`. Borders `border-white/8`; hover `border-white/20`; focus
ring `accent`. Grids `gap-4 md:gap-6`. Never more than two stacked
surface levels.

## 3. CSS component layer (same class NAMES as v3 — new skin)

Untouched pages (≈50 blog posts) re-skin automatically because the class
API is stable. Implementations change; names don't.

- `.card` — `rounded-xl border border-white/8 bg-asphalt-2/80`.
- `.card-hover` — border-white/20 + subtle lift; reduced-motion-safe.
- `.btn-primary` — **signal-orange fill, black text**, `h-11 rounded-xl
  font-display text-sm font-bold` (sentence case); hover `accent-bright`.
- `.btn-ghost` — white/12 border, white/85 text; hover border-white/30.
- `.btn-danger` — signal-foul tinted outline.
- `.btn-running` — signal-stage tinted (amber = staged/running), hover
  flips to foul (stop affordance).
- `.btn-sm`, `.input-base` (asphalt-3, orange focus ring), `.label-mono`,
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
- `.text-gradient-orange` — the heading-accent gradient (orange).

## 4. Signature elements: GaugeMark + StageDots

`components/GaugeMark.js` — the identity kit "redline Q" as an inline SVG
(`{size, ring, className}`). THE brand mark: nav lockup (GaugeMark +
"MOTOQUANT" in Space Grotesk 700, MOTO white / QUANT orange), footer, and
anywhere the brand signs its work. Kit rules: never rotate the mark; the
315° needle axis is the identity; orange only on the moving parts.

### StageDots

`components/StageDots.js` — three 6px dots (stage · stage · go): two
`signal-stage`, one `signal-go`. Props: `{ animate=false, className }`.
Static by default; `animate` runs ONE amber→amber→green light-up sequence
on first view (opacity keyframes only, reduced-motion renders static).
Used as: section eyebrows (dots + `.label-mono` text), list bullets,
loading accents. GaugeMark signs the brand; StageDots marks sections —
use these two instead of inventing new ornaments.

## 5. Shared components — keep-API list (re-skin internals ONLY)

`Reveal/Stagger/StaggerItem/Counter`, `ActionButton`, `SimProgress`,
`Skeleton*`, `BikePicker`, `LocationPicker`, `CommandPalette`, `TierBadge`
(+`UpgradeCTA`), `SuggestBikeForm`, `AuthProvider`, `ChatPanel`,
`BuildOptimizer`, `EcuAutotune`, `SimulatorWidget` (KEEP the
`bikeIdMap` catalog-ID self-heal), `AccuracyExplorer`, `SiteNav`,
`SiteFooter`, `MobileToolBar`, `PageHero`, `CodeComment`,
`ScoreboardDigits`/`ScoreboardCounter`.

- **`ScoreboardDigits`** keeps its exact props (`value,h,color,ghost,
  className,label`) and renders the **seven-segment SVG numerals**
  (hand-rolled polygons, unlit ghost segments, zero font assets) — the
  v4 "clean mono digits" swap was never shipped; v5 restored the
  scoreboard face for hero figures (see §2.2). Default `color` is the
  signal orange `#FF5E1F`.
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

- **SiteNav** (fixed, `bg-asphalt-0/85 backdrop-blur`): brand lockup =
  GaugeMark + "MotoQuant" wordmark in Space Grotesk 700 (`font-display`,
  Moto white / Quant orange — per §4). Links:
  Simulator · Optimize · Autotune · Bikes · Leaderboard · Pricing ·
  Resources ▾ (Validation, Docs, Blog, Whitepaper, Features, About). ⌘K
  search button, auth chip, volt CTA "Run a sim". Keep the 1024-1126px
  width fixes (collapse CTA label, hide ⌘K hint in lg..xl band). Mobile:
  drawer + MobileToolBar (5 tools, safe-area).
- **SiteFooter**: 4 columns (Product/Data/Company/Legal), baselines line
  (`K5 9.9331s · R1 10.1436s · Hayabusa 10.3633s` — always the CURRENT
  pinned references, §1.2), "Built in India" + beta note. Quiet — no glow.
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
5. `og-image.png` regenerated via `scripts/audit_headline_stats.py
   --regen-og` (OG-card ownership moved to the audit script in 81c10b8;
   `scripts/generate_brand_assets.py` no longer exists). The card is
   evergreen by design — mark, lockup, tagline, v(t) curve, domain; no
   counts or accuracy figures baked in.
