# MotoQuant Web — Cockpit v3 Redesign Spec (July 2026)

> Working spec for the July 2026 full-site revamp. Every page agent reads this
> FIRST. It encodes the design language, the shared component APIs, the
> progress-feedback doctrine, and the constraints that must survive verbatim.
> When this spec and old page code disagree, the spec wins.

## 0. Non-negotiable constraints

1. **`next build` must pass** (static prerender). Any client component using
   `useSearchParams()` must sit inside `<Suspense>` (or read
   `window.location` post-mount like BuildOptimizer does).
2. **Stat-audit regexes** (`scripts/audit_headline_stats.py`) must keep
   matching. The guarded copy tokens are: `NNN bikes|motorcycles`,
   `NNN parts`, `NNN tires`, `NNN venues`, `NNNN tests`, `NN benchmarks`,
   `NNN-bike catalog`, `NNN-part library`, the object shapes
   `num: NNN, label: 'BIKES'|'PARTS'` / `num: 'NNN', label: 'Parts'|'Catalog bikes'`,
   `numberOfItems: NNN`, and the baseline forms `K5=10.0334s`-style on the
   landing page and `K5 … 10.0334s` prose in blog posts. Keep those token
   shapes when rewording copy around them. Do NOT invent new counts.
3. **Palette bans**: no `gray-*`, no raw `orange-N`, no inline hex backgrounds
   in components. Use `ink-*`, `brand-*`, and `white/N` opacities only.
4. **Route template is opacity-only** (`app/template.js`): never add a
   transform on a route-level wrapper (it re-anchors `position:fixed`
   children — HudFrame, boot overlay).
5. **Reduced motion**: every animation must be safe. `Reveal`/`Stagger` now
   handle this globally; bespoke animations must check
   `prefers-reduced-motion` themselves.
6. **One benchmark corpus sitewide**: the June-13 sweep
   (`reports/acc_final_2026_06_13.json`) — 216 benchmarks / 236 matched /
   weighted bias −0.015 s / weighted |Δ| 0.262 s, within ±0.10 s = 62,
   within ±0.20 s = 113 (per docs/validation). Kill every stale "79
   weighted benchmarks", "156-benchmark", "42/81" variant. The landing TOP10
   must equal the docs/validation TOP10.
7. **Mobile first-class**: no horizontal overflow, headers must wrap or
   collapse, tap targets ≥40px. `html,body{overflow-x:clip}` is a safety net,
   not a license.

## 1. Design language (Cockpit v3)

The identity stays **race instrumentation**: seven-segment scoreboards,
staging-lamp signal colors, engine-log microcopy, dark carbon surfaces. v3
raises the *finish*: calmer layouts, one clear primary action per view,
consistent surfaces, and honest live data everywhere.

- **Type**: `font-display` (Space Grotesk) for headings, `font-sans` (Inter)
  for body, `font-mono` (JetBrains Mono) ONLY for data/labels. The label voice
  is `.label-mono` (see §2). Headings: h1 `text-4xl md:text-5xl font-display
  font-bold tracking-tight`; h2 `text-3xl md:text-4xl font-display font-bold`;
  panel titles use `.label-mono`.
- **Surfaces**: page = black; cards = `.card` (ink-2/60 + border-white/10,
  rounded-2xl). Elevated/hover = border-white/20. Never stack more than two
  surface levels.
- **Color roles**: `brand-orange` = primary action + live data accents;
  `brand-green` = success/GO; `brand-amber` = warnings/staging;
  `brand-red` = errors/foul; `brand-accent` (mint) = PRO/meta chips only.
  Body text `text-white/65`, headings `text-white`, hints `text-white/45`.
- **Spacing rhythm**: sections `py-20 md:py-28`; card padding `p-5 md:p-6`;
  grids `gap-4 md:gap-6`. Page containers `max-w-6xl` (content),
  `max-w-[1440px]` (simulator workbench).
- **Motion**: opacity/transform only, ≤0.65 s, `Reveal`/`Stagger` for entrance;
  no infinite animation except the staging lamps and progress sweeps.

## 2. Shared primitives (built in Phase A — USE THESE, do not re-invent)

### CSS component classes (`globals.css`)
- `.card` — standard panel surface.
- `.card-hover` — adds hover border/glow for clickable cards.
- `.btn-primary` / `.btn-ghost` / `.btn-danger` — the ONLY button styles.
  All are `inline-flex items-center justify-center gap-2` with consistent
  height (`h-11` default; add `.btn-sm` for `h-9`).
- `.input-base` — text/number/select fields (ink-3 bg, border-white/10,
  focus ring brand-orange/60).
- `.label-mono` — `font-mono text-[10px] uppercase tracking-[0.25em]
  text-white/45` (the established voice).
- `.skeleton` — shimmer block for loading states.

### `lib/useAsyncTask.js`
```js
const task = useAsyncTask(async (signal, onProgress) => { ...; return result; });
// task.run(...args) → Promise (resolves result | undefined on abort)
// task.stop()  — aborts (AbortError swallowed)
// task.active, task.progress (0..1|null), task.stage, task.error, task.result, task.reset()
```
Standardizes AbortController wiring + progress state + error capture. EVERY
user-triggered async action goes through it.

### `components/ActionButton.js`
```jsx
<ActionButton task={task} onRun={() => task.run()} label="Optimise build"
              runningLabel="Optimising" className="w-full" />
```
Renders `.btn-primary`; while `task.active` it flips to a Stop button showing
`■ Stop — 42%` (real % when determinate) with an integrated edge progress
strip. This is the ONE run/stop pattern sitewide.

### `components/SimProgress.js` (existing — unchanged API)
`active, progress (0..1|null), stage, label, compact, edge, onStop`.
Determinate when progress>0; staged sweep otherwise, self-escalates to the
cold-start caption after 4 s. Pair with ActionButton for panel-level bars.

### `components/Skeleton.js`
`<Skeleton className="h-4 w-32"/>`, `<SkeletonText lines={3}/>`,
`<SkeletonCard rows={4}/>`, `<SkeletonTable rows={6} cols={4}/>`.
Use for EVERY on-mount fetch that blocks meaningful content. Never a blank
"Loading…" text line, never a layout-replacing full-page loader.

### `components/BikePicker.js` (shared)
Accessible combobox (aria-expanded, keyboard ↑↓/Enter/Escape, listbox roles),
debounced `/api/bikes?search=`, optional `popular` chips row, `value/onChange`
= bike object. Replaces the two duplicated pickers + simulator Dropdown where
feasible.

### `lib/api.js` additions
- `simulateJob(body, onProgress, signal)` — runJob('simulate', …) w/ fallback.
- `topspeedJob(body, onProgress, signal)` — runJob('topspeed', …) w/ fallback.
- `compareJob(body, onProgress, signal)` — runJob('compare', …) w/ fallback
  to `/api/simulate/compare` (backend job route added July 2026).
- `saveRun(body, accessToken?)` — POST `/api/simulate/save`, attaches bearer
  when provided so the run lands in the user's Garage.

## 3. Progress doctrine ("functional progress bar everywhere")

| Class of operation | Required feedback |
|---|---|
| Job-backed sims (full sim, top speed, optimize, autotune, **compare**) | Real % via runJob → ActionButton (% in button) + SimProgress panel bar + Stop. |
| Quick sim (~50 ms warm) | Staged edge bar (existing pattern) — no % needed. |
| Plain POST actions (chat, uploads, auth, checkout, save run, suggest bike, license ops, resolve venue) | ActionButton with staged progress (cold-start caption after 4 s) — button is the bar. No dead "Working…" text. |
| On-mount fetches (bikes grid, bike detail, garage, leaderboard, /r/[id], payments config) | Skeletons shaped like the final content. Errors get a `.card` error state WITH a Retry button. |
| Multi-fetch boot (simulator) | Progressive: render the workbench immediately, per-panel skeletons, fetch-count progress in the toolbar, Retry on failure. NO full-page boot loader. |
| Background/silent (telemetry, id-remap) | Stay silent by design. |

Rules: every long-running op gets Stop (abort → server-side cancel where
job-backed); errors are inline, branded, and actionable (Retry) — never
`alert()`/`confirm()`; loading states never collide (one state per op, no
shared `simLoading`).

## 4. Page chrome unification

- **SiteNav everywhere** — including `/simulator` (its bespoke sticky nav is
  retired; its Live/Manual toggle + counts + progress chip move into a
  simulator toolbar `sticky top-16`). Nav links: Simulator, Optimize, Tune,
  Bikes, Leaderboard · Pricing · Resources (Features, Docs, Whitepaper, Blog,
  About) · auth chip · Launch CTA. Mobile drawer lists all.
- **SiteFooter everywhere** (simulator included). Footer Contact →
  `motoquant@gmail.com`.
- **PageHero** on every inner page (privacy/terms included, compact variant).

## 5. Per-page blueprints (Phase B ownership map)

- **S — /simulator**: workbench rebuild per §3/§4. Per-op state separation
  (quick/full/topspeed/compare/uploads each own {loading,progress,error}).
  Compare → compareJob + Stop + in-panel SimProgress. Tabs NEVER auto-run
  physics — empty tab states carry an explicit Run button. Lossless share
  (encode parts/tires/env; read them back). NEW: "Save this run" on results
  (saveRun; signed-out → link to /login?next=). Mobile toolbar wraps.
- **O — /optimize + /autotune**: `max-w-6xl` two-column (controls left,
  results right; stack on mobile). Shared BikePicker + popular chips.
  Validated manual inputs (min/max). Keep job progress (already correct).
- **B — /bikes + /bikes/[id]**: filters become real dropdowns fed from the
  full catalog (one `limit=2000` fetch, cached); grid skeletons on
  filter/page change; detail page gets skeleton + friendly cold-start error +
  differentiated CTAs; drop the client refetch where the layout already has
  data (keep it simple: one clean client fetch + skeleton is acceptable).
- **L — landing**: calmer lg hero (tree + dial stay, but copy column gets
  clear hierarchy; ≤2 pills), stat unification per §0.6 (79→216 fixes,
  aggregate tiles 62/113, TOP10 = docs/validation list), keep all signature
  components, keep STATS const shape (audit).
- **C — pricing/login/account + leaderboard + /r/[id]**: skeletons, branded
  confirm dialogs (no alert/confirm), ActionButton on all submits, garage
  skeleton, checkout staged button, magic-link verifying bar.
- **D — content**: docs mobile nav (collapsible section list), blog index
  featured-post + rubric, features page readouts labeled honestly (or fed
  real constants), about form → working mailto with honest copy, privacy/
  terms on PageHero + stale-claims fixes (terms §2 passwordless claim),
  StructuredData: FAQ rewritten to beta-accurate copy, remove
  aggregateRating, add second founder; robots www→apex; sitemap adds
  /leaderboard /optimize /autotune /terms /privacy.

## 6. Verification gates (Phase C)

1. `next build` green (75+ pages), `ruff`-equivalent grep bans clean.
2. `python3 scripts/audit_headline_stats.py` → "All headline numbers in sync".
3. Playwright vs local uvicorn: every route renders (desktop 1440 + mobile
   390 screenshots), full-sim/optimize/autotune/compare bars MOVE (progress
   assertions), Stop works, share/save flows work.
4. Zero console errors on any page.
