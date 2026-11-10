# MotoQuant web: the CLARITY design system (v6, November 2026)

> This file is the authority for the web app. It replaces v5 "IGNITION",
> which is kept in git history. Where old page code disagrees with this
> file, this file wins. Every agent working in `web/` reads it first.

## 0. Why v6 exists

People could not understand the product. v1–v5 spoke fluent drag-strip and
fluent engineer: "STAGING · CONFIGURE THE RUN", "TELEMETRY · LIVE RESULTS
FEED", "knapsack", "ET", "density altitude", seven-segment digits that read
`54|` instead of `541`, and tool pages that opened with a full-screen
marketing hero before the tool. Newcomers left.

MotoQuant is now open source (Apache-2.0). The site is the free public
instance of a community project. It has no pricing, no tiers and no upsell,
and it asks visitors to *use it*, *understand it* and *contribute to it*.

The aim is a calculator a first-timer can use in 10 seconds, with the full
workbench one click away. Every feature stays. The default view answers one
question in plain words, and the depth is opt-in.

The audience has not changed: Indian riders on R15s, Dukes, Pulsars and
Hayabusas, mostly on phones and often outdoors at a strip. The site has to
be readable in sunlight, which is why it has a real light theme.

## 1. The seven rules (apply to every screen)

1. Plain words first, jargon second. Lead with what a rider would say, and
   put the technical term in a `<Term>` tooltip or in brackets once.
   "Quarter-mile time" not "ET". "Finish-line speed" not "trap speed".
   "First 60 ft (launch)" not "60 ft". "Air & altitude" not "density
   altitude". "Best parts for your budget" not "knapsack optimizer".
   §6 has the canonical vocabulary; use it verbatim everywhere.
2. Sentence case. No ALL-CAPS tracking-wide micro-labels on controls, form
   labels, tabs, buttons or card titles. The only uppercase allowed is the
   small section eyebrow (`.eyebrow`), at most one per section.
3. Tool first. On tool routes (`/simulator`, `/optimize`, `/autotune`,
   `/bikes`, `/leaderboard`) the working UI starts in the first viewport on a
   390×844 phone. Page headers are compact: a title and one plain sentence.
   No stat counters and no marketing hero on tool pages.
4. One primary action per screen. One `.btn-primary`; everything else is
   ghost or text. Tell the user what happens: "Calculate my time", "Find the
   best parts", "Get my setup", never a bare "Run".
5. Results explain themselves. Every result leads with a plain sentence
   ("A stock Hayabusa with a 75 kg rider runs the quarter mile in about
   10.36 s, crossing the line at 228 km/h."), then the numbers, then a
   "What next?" list of the obvious next steps.
6. Progressive disclosure. Defaults cover the common case. Advanced controls
   sit behind an explicit, remembered "Advanced" switch or a "More options"
   disclosure. They are never deleted and never the default.
7. Never show a wrong or empty number. No count-up from 0, no `—` rows in a
   result shown as final, and no content that stays invisible until a
   scroll animation fires. Content is visible in the server HTML; motion is
   added on top.

## 2. Hard constraints (inherited, still binding)

1. `next build` must pass. Client `useSearchParams()` sits inside
   `<Suspense>`.
2. Stat-audit token shapes survive (`scripts/audit_headline_stats.py` and
   `web/scripts/gen_bike_ids.py --check` must stay clean). Do not invent or
   change counts. Reuse the existing constants and phrasing shapes, and run
   the audit after touching any page that shows a number.
3. `web/scripts/verify-web.mjs` must pass (it runs as `prebuild`).
4. The same-origin `/api` rewrite is architectural. Design work does not
   modify `lib/api.js` job polling (fallback, restart recovery, backoff,
   abort) or `lib/surrogate.js` (bit-parity with the server surrogate).
5. `delta_et_s` sign: negative = quicker = good (green); positive = slower =
   bad (red). Trap-speed deltas: positive = faster = good.
6. Reduced motion is respected everywhere. The route template stays
   opacity-only.
7. Mobile is first-class: no horizontal overflow at 360px, tap targets
   ≥ 44px, form inputs ≥ 16px font-size (this prevents iOS zoom).
8. Existing routes keep their URLs (`/optimize`, `/autotune`, …). Rename
   labels, never paths. Share links and `/timeslip` links keep working.
9. Accessibility: every input has a visible label wired with
   `htmlFor`/`id` or `aria-label`; every clickable is a `<button>` or `<a>`;
   the focus ring is visible; colour is never the only signal; text contrast
   is ≥ 4.5:1 in both themes.

## 3. Tokens: themable, light and dark

All colour goes through CSS variables defined in `app/globals.css` and
exposed by `tailwind.config.js` as `rgb(var(--x) / <alpha-value>)`. The
existing class names keep working, which is how ~80 content/blog pages
re-skin with zero edits:

| Tailwind name | Variable | Dark (default identity) | Light |
|---|---|---|---|
| `white` (= foreground) | `--fg` | `255 255 255` | `17 18 22` |
| `black` (= deepest background) | `--bg-deep` | `0 0 0` | `255 255 255` |
| `asphalt-0` (page) | `--surface-0` | `9 9 11` | `250 250 249` |
| `asphalt-1` | `--surface-1` | `14 14 17` | `255 255 255` |
| `asphalt-2` (card) | `--surface-2` | `21 21 25` | `255 255 255` |
| `asphalt-3` (raised/input) | `--surface-3` | `30 30 35` | `244 244 242` |
| `asphalt-4` (border-strong) | `--surface-4` | `46 46 52` | `226 226 222` |
| `accent` | `--accent` | `255 94 31` | `214 69 8` |
| `accent-bright` | `--accent-bright` | `255 143 87` | `234 88 12` |
| `accent-deep` | `--accent-deep` | `204 64 0` | `174 52 4` |
| `signal-go` | `--go` | `52 211 120` | `21 128 61` |
| `signal-stage` | `--stage` | `245 178 40` | `161 98 7` |
| `signal-foul` | `--foul` | `248 96 96` | `200 30 30` |
| `on-accent` (text on accent fills) | `--on-accent` | `12 10 9` | `255 255 255` |

`white` means "foreground ink" and `black` means "deep background"; in the
light theme they invert. So `text-white/70` is secondary text in both themes
and `bg-white/[0.04]` is a subtle tint in both. New code may keep using these
names. The one thing that must not invert with the theme is text on an
accent or solid colour fill: use `text-on-accent` (in place of `text-black`
on `bg-accent`/`.btn-primary`).

Theme selection: `<html data-theme="light|dark">`. On first visit the theme
follows the OS (`prefers-color-scheme`). The nav `ThemeToggle` writes
`localStorage['mq-theme']`, and a tiny inline script in the `<head>` of
`app/layout.js` applies it before paint, so there is no flash.
`color-scheme` is set per theme so native controls match. `mint`, legacy
`ink-*` and `brand-*` aliases still resolve, mapped onto the same
variables. `mint` is no longer a tier colour; treat it as an alias of
`signal-go`.

Anything that cannot use Tailwind classes (SVG, canvas and recharts props,
inline `style`) reads the variables: `rgb(var(--fg) / 0.6)`, or the helper
`cssVar('--fg', 0.6)` from `lib/theme.js`. Components use no raw hex and no
`rgba(255,255,255,…)`/`rgba(0,0,0,…)` literals, because those break the
light theme. Shadows may use `rgb(0 0 0 / α)`; glows use
`rgb(var(--accent) / α)`.

### Type

- `font-display`: Space Grotesk, for headings, big numbers and buttons.
- `font-sans`: Inter, for everything else, including form labels and tabs.
- `font-mono`: JetBrains Mono, only for numeric data in tables and rows
  (`tabular-nums`) and for code. Never for labels or body copy.
- Scale: page title `text-3xl md:text-4xl font-display font-bold`; section
  title `text-xl md:text-2xl font-display font-semibold`; body `text-base`
  (`text-white/75`); secondary `text-sm text-white/60`. Nothing goes below
  `text-xs`, and `text-xs` never goes below `text-white/55`.
- Seven-segment digits are retired. `ScoreboardDigits`/`ScoreboardCounter`
  keep their exports and props but render clean `font-display font-bold
  tabular-nums` text, with the final value in server HTML (no count-up from
  zero). The hero result number is `text-6xl md:text-7xl`, accent-coloured.

### Component classes (`globals.css`, names stable)

- `.card`: `rounded-2xl border border-white/10 bg-asphalt-2` plus a soft
  shadow in the light theme. `.card-pad` = `p-5 md:p-6`.
- `.btn-primary` (accent fill, `text-on-accent`, h-12 on tool pages),
  `.btn-ghost`, `.btn-danger`, `.btn-running`, `.btn-sm`: names unchanged.
- `.input-base`: h-12, `text-base`, `bg-asphalt-3`, `border-white/12`, a
  clear focus ring in accent.
- `.field-label` (new): `block text-sm font-medium text-white/80 mb-1.5`,
  sentence case. `.field-hint`: `text-xs text-white/55 mt-1`.
- `.eyebrow` (new, replaces `.label-mono` usage): `text-xs font-semibold
  uppercase tracking-wider text-accent`. `.label-mono` stays defined as an
  alias to a calmer style (sentence-case-friendly `text-xs font-medium
  text-white/60`, no wide tracking, not mono), so untouched pages calm down.
- `.step-badge` (new): a 24px circle with the step number and an accent
  outline.
- `.stat-row`: label on the left (sans, `text-white/70`), value on the right
  (mono, tabular, `text-white`), divider `border-white/8`.
- `.seg-control` (new): the Simple/Advanced style two-option switch
  (`role="tablist"`), 44px tall.

Removed decoration: tri-dot eyebrow lamps on every header (`StageDots` may
stay only in the landing hero), dashed rulers under headers, mono all-caps
chips and "standing by" empty-state theatre.

## 4. Shared components (contracts)

- `components/Term.js`: `<Term k="et">quarter-mile time</Term>`. It renders
  its children with a dotted underline as a `<button type="button">`. Hover,
  focus or tap opens a small popover with the plain definition from
  `lib/glossary.js` and a "Glossary" link. It uses `aria-describedby`;
  Escape and an outside click close it; on mobile the popover is clamped
  inside the viewport. With no children it renders the glossary entry's
  `label`.
- `lib/glossary.js`: the single source, `{ key: { label, short, long } }`.
  `short` is ≤ 140 chars, and a definition contains no jargon. It powers
  `<Term>` and the `/docs/glossary` page. Keys at minimum: `et`, `trap`,
  `sixty`, `eighth`, `launch_rpm`, `two_step`, `gearing`, `sprockets`, `da`
  (air & altitude), `traction`, `wheelie`, `cost_per_tenth`,
  `instant_estimate`, `full_sim`, `power_boost`, `mass_delta`, `cd_a`,
  `redline`, `slip`, `build_profile`, `stage_tiers`, `outlaw`, `dyno`,
  `dragy`, `top_speed`, `splits`.
- `components/PageHeader.js`: the compact tool-page header, with an optional
  eyebrow, an `<h1>`, a one-sentence lede and an optional right-side slot.
  It replaces `PageHero` on tool routes. `PageHero` stays for content pages,
  slimmed down (no counters).
- `components/ThemeToggle.js`: a sun/moon button, 44px, `aria-pressed`.
- `components/ResultSentence.js`: builds the plain-language sentence from
  `{bikeName, riderKg, et, trapKmh, venueName?, estimated?}`.
- `components/NextSteps.js`: the "What next?" list. Items are
  `{icon, title, hint, href|onClick}`.
- `SiteNav` labels (paths unchanged): `Simulator` (/simulator) ·
  `Upgrades` (/optimize) · `Race-day setup` (/autotune) · `Bikes` ·
  `Leaderboard` · `Learn ▾` (Getting started, Glossary, How the physics
  works, Accuracy, Blog, About) · GitHub icon link · ThemeToggle · Your runs ·
  primary `Open simulator`. Each Learn item has a one-line description.
  `MobileToolBar`: Simulate / Upgrades / Setup / Bikes / Board.
  `CommandPalette`: the same labels and descriptions. Searching "optimize",
  "tune", "ET", "knapsack" and so on still finds the renamed entries (keep
  the old words as hidden keywords).
- `Reveal` / `Stagger`: content is rendered visible. The animation is a
  short fade/translate that starts from visible-on-SSR when JS is slow or
  absent (use a `.js` class gate, or `whileInView` with an `initial={false}`
  fallback). A full-page screenshot taken without scrolling must show all
  content.

## 5. Page blueprints

### `/simulator` — Simple ⇄ Advanced
Header: `PageHeader` with the title "Quarter-mile simulator" and the lede
"Pick a bike and see how fast it runs the quarter mile." Right slot: a
`.seg-control` **Simple | Advanced** (persisted in
`localStorage['mq-sim-mode']`; default Simple). A share link that carries
parts, tires, environment or compare opens Advanced automatically.

Simple mode has 2 columns at lg and up and is stacked on mobile. The result
card is sticky on lg and sits directly under the bike picker on mobile.
- Step 1 "Choose your bike": `BikePicker` plus popular chips.
- Step 2 "You and the conditions": a "Rider weight with gear" slider
  (kg, shows the value) · "Where are you racing? (optional)" `LocationPicker`
  with the hint "Adjusts for altitude and weather."
- Result card "Your result": big number and unit, `ResultSentence`, then
  `.stat-row`s: "First 60 ft (launch)", "Halfway (⅛ mile)",
  "Finish-line speed", "Power", "Total weight with rider". Each label is a
  `<Term>`. If the number is the instant estimate, show a calm inline note:
  "Instant estimate. **Run the full simulation** for exact splits and
  charts." (button). Rows the estimate cannot fill are hidden, not shown
  as `—`.
- `NextSteps`: "Add parts and mods" (→ Advanced, parts panel focused) ·
  "Find the best parts for my budget" (→ `/optimize?bike_id=`) · "Get a
  race-day setup" (→ `/autotune?bike_id=`) · "Compare with another bike"
  (→ Advanced, Compare tab) · "See charts and splits" · "Save and share
  this run".
- "Ask in plain English": the chat, collapsed to one input row under the
  header ("Ask anything, e.g. 'How fast is a Duke 390 at Aamby Valley?'").
  It expands in place when used.

Advanced mode is the full existing workbench with every feature intact,
relabelled: "Setup" (was Staging · Configure the run) and "Results" (was
Telemetry · Live results feed). Sliders: "Rider weight", "Engine power
change", "Weight added or removed". Sections: "Air and altitude"
(environment), "Tyres", "Parts and mods" (with a search field above the
category list, and the selected-parts summary and total cost pinned at the
top). Tabs: "Quarter mile", "Top speed", "Charts", "Splits", "Compare",
"My data" (was Upload), "Specs". The Live/Manual toggle becomes a labelled
checkbox, "Update as I change things". Share, Save and Reset stay.

### `/optimize` — "Best parts for your budget"
Lede: "Tell us your bike and how much you want to spend. We test every
compatible part and show the combination that makes it quickest."
Steps: 1 bike · 2 budget (preset chips ₹25,000 / ₹50,000 / ₹1,00,000 /
₹2,00,000 / No limit, plus a slider) · 3 "What kind of build?", radio cards
with a one-line description each (Street legal / Drag-strip prep / Full
race / Anything goes). A "More options" disclosure holds the goal (quickest
time vs highest finish speed), location and rider weight. Button: "Find the
best parts".
Result: a sentence ("Spend ₹92,400 on 6 parts: 10.36 s → 9.98 s, 0.38 s
quicker."), before/after tiles, and the parts list sorted best-value-first
with price, gain and a `<Term k="cost_per_tenth">` column. Then warnings in
plain words, "What to buy next if you have more budget", and NextSteps
(open in the simulator with these parts, share).

### `/autotune` — "Race-day setup"
Lede: "Pick your bike and where you're racing. Get the gearing, launch RPM
and tyre pressure that suit today's air, with how much time each one is
worth." Steps: 1 bike · 2 where (LocationPicker, with a "Set conditions by
hand" disclosure) · 3 rider weight. Button: "Get my setup". Result: a
sentence, then one card per recommendation with what to change, from → to,
the time gained and a one-line reason in plain words.

### `/` — landing
1. Hero: H1 "Know your quarter-mile time before you race." Sub: "Pick your
   bike, see how fast it should run, and find out what actually makes it
   quicker. Free and open source." The existing `SimulatorWidget` sits on
   the right (relabelled per §6). Primary CTA "Open the simulator",
   secondary "Browse 534 bikes". A trust line in plain words.
2. "What do you want to do?": 4 task cards → simulator / optimize /
   autotune / compare.
3. "How it works": 3 steps, plain words, one line each.
4. "Can I trust the numbers?": a plain accuracy statement, the existing
   accuracy stats and table (constants unchanged) and a link to
   `/validation`.
5. "Open source": Apache-2.0, GitHub link, "Add your bike", "Send us your
   timeslip", "Read the physics".
6. FAQ (plain questions), then the footer.

Everything is visible without scroll-triggered reveals (rule 7).

### `/bikes`, `/bikes/[id]`
A compact header ("Bikes", "534 motorcycles you can simulate. Pick one to see
its predicted time."), then search and filters. Cards show name, cc, hp,
predicted time when known, and one clear action, "Simulate this bike".
Remove the SEO keyword paragraph from the visible header (keep the keywords
in metadata). The detail page leads with the predicted time, a sentence and
"Open in simulator".

### `/leaderboard`, `/runs`, `/timeslip`
Compact headers, plain labels, v6 components. Timeslip print styles keep
working. There are no accounts: `/runs` lists the runs saved in this browser,
and `/timeslip` re-runs a shared link through the physics. The old `/login`,
`/signup`, `/account` and `/r/[id]` paths redirect (`next.config.js`).

### `/docs/*`, `/features`, `/about`, `/validation`, `/whitepaper`, blog
Content pages keep their content and inherit the theme through tokens.
Add `/docs/glossary` ("Drag-racing terms in plain English") and rewrite
`/docs/getting-started` as a 5-minute walkthrough of Simple mode →
Advanced → Upgrades → Race-day setup. Fix any hard-coded colour that breaks
the light theme.

## 6. Canonical vocabulary (use verbatim)

| Say | Not | Term key |
|---|---|---|
| Quarter-mile time | ET, elapsed time | `et` |
| Finish-line speed | Trap speed | `trap` |
| First 60 ft (launch) | 60 ft, sixty-foot | `sixty` |
| Halfway (⅛ mile) | 1/8 mile, eighth | `eighth` |
| Air and altitude | Density altitude, DA, environment | `da` |
| Rider weight with gear | Rider mass | — |
| Engine power change | Power boost % | `power_boost` |
| Weight added or removed | Mass delta | `mass_delta` |
| Parts and mods | Parts catalog | — |
| Best parts for your budget | Build optimizer, knapsack | — |
| Race-day setup | ECU autotune, setup sheet | — |
| Gearing (sprockets) | Final drive ratio | `gearing` |
| Launch RPM | Staging RPM | `launch_rpm` |
| Cost per tenth of a second | Cost-per-tenth, ROI | `cost_per_tenth` |
| Instant estimate | Surrogate, client-surrogate | `instant_estimate` |
| Full simulation | RK4 sim, server sim | `full_sim` |
| Quicker / slower (for time) | Faster ET, negative delta | — |
| Compare two bikes | A vs B | — |
| Your saved runs | Garage | — |
| Calculate my time | Run, Run sim | — |

Engineering depth (RK4, 1 ms timestep, 15 sub-models, SAE J1349) belongs on
`/docs/physics`, `/whitepaper`, `/validation` and in tooltips. Control
labels leave it out.

## 7. Verification (every web change)

`cd web && node scripts/verify-web.mjs && npx next build`, then from the
repo root `python3 scripts/audit_headline_stats.py` and
`python3 web/scripts/gen_bike_ids.py --check`. Screenshot the changed pages
at 1440×900 and 390×844 in both themes. Expect zero console errors and zero
horizontal overflow, and a full-page screenshot that shows all content
without scrolling first.
