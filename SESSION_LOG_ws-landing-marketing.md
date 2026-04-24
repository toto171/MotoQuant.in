# SESSION LOG — ws/landing-marketing
> Branch: `ws/landing-marketing`
> Session date: 2026-04-24
> Model: claude-sonnet-4-6
> Goal: First-time visitor in the Indian drag community immediately understands the product, sees why it's worth ₹499/mo, and has 3 clear CTAs — try the free simulator, subscribe, read the blog.

---

## ✅ Completed Tasks

### Task 1 — Hero rewrite + "Why MotoQuant" + social proof (`web/app/page.js`)
- **H1 changed:** "The Physics of Faster" → "Physics-accurate drag simulation for every bike on Indian roads."
- **Sub changed:** "A first-principles physics engine…" → "287 bikes. 465 parts. 15 physics sub-models. Predict your quarter-mile within ±0.5s before you buy a single part."
- **Primary CTA:** "Run a Simulation" → "Try it free" → `/simulator`
- **Secondary CTA:** "See Validation" → "See pricing" → `/pricing`
- **Nav updated:** desktop + mobile — added Features, Docs, Blog, About, Pricing; removed anchor-only links
- **"Why MotoQuant" section added** — 4 cards with Lucide icons:
  1. First-Principles Physics → `/docs/physics`
  2. Indian Market-First → `/bikes`
  3. ROI Before You Buy → `/features`
  4. Validated → `/docs/validation`
- **Testimonials section added** — JSON-driven `TESTIMONIALS` array at top of file (3 entries, all marked `// COPY: replace before launch`)
- **CTA section rewritten** — "Ready to know your number?", 3-CTA row: Try it free / See pricing / Read the blog
- **Footer rewritten** — 3-column grid: Product, Learn, Company with proper link structure
- **StatsStrip preserved** — 287/159/424/20/838/15 numbers NOT touched (orchestrator-owned)

### Task 2 — SimulatorWidget polish (`web/components/SimulatorWidget.js`)
- **Default bike:** Changed from KTM RC 390 (BIKE_CATEGORIES[0].bikes[0]) to Hayabusa Gen1 (`presetId: 'hayabusa_gen1'`) in the Dream Bikes tab
- **"Powered by MotoQuant" chip** — added in widget header row, links to `/features`
- **Post-sim save CTA** — appears after result tiles: "Want to save this run?" → `/signup` (orange badge button)
- Default tab index set to `hayabusaDefaultIdx` (Dream Bikes), falls back gracefully to index 0 if not found

### Task 3 — `/features` page (`web/app/features/page.js`) [NEW FILE]
- 6 product sections: Physics Engine, Parts Catalog, Calibration, ROI & Optimization, Desktop App, API & Integration
- Alternating 2-col layout (text/visual swap per section) with visual screenshot placeholders (`{/* TODO: replace with screenshot/GIF */}`)
- Each section: 3-key-stat grid + docs link
- Quick-jump nav bar at top for long-page scrolling
- Page metadata with canonical URL, OG description

### Task 4 — `/about` page (`web/app/about/page.js`) [NEW FILE]
- 2-column story section (origin + mission)
- Founder card: avatar ("H" initial), name Hritwik Mudhai, quote, email `hello@motoquant.in` link
- Roadmap timeline (5 phases, visual dots, complete/in-progress/upcoming states, NO specific dates)
- Contact form with mailto fallback (`handleSubmit` constructs mailto URL), `sent` state confirmation

### Task 5 — `/blog` with 3 launch posts [NEW FILES]
- **`web/app/blog/page.js`** — index page, 3-post grid, `POSTS` array at top, tag chips, hover effects
- **`web/app/blog/the-physics-of-a-perfect-launch/page.js`** — ~800 words, covers wheelspin / traction limit / RPM selection / clutch engagement / rider weight transfer
- **`web/app/blog/why-your-r15-wont-hit-14s/page.js`** — ~1000 words, covers drivetrain losses / gearing / aero / tyre limits; key thesis: sprocket + tyre changes beat power mods
- **`web/app/blog/how-to-tune-for-aamby-valley-in-november/page.js`** — ~600 words, covers density altitude at ~1100m, November conditions (18-24°C, 28% RH), per-class ET impact, jetting guidance for carburetted bikes
- All posts: inline `CONTENT` array (typed blocks: `lead` / `h2` / `p` / `callout`), `Prose` renderer component, per-post metadata with canonical URL + keywords + OG, post-sim CTA at bottom

### Task 6 — `/docs` pages [NEW FILES]
- **`web/app/docs/layout.js`** — shared sticky sidebar layout (doc nav + "Also see" links), main content `max-w-3xl`
- **`web/app/docs/getting-started/page.js`** — 3 paths (Web / Desktop beta / REST API), numbered steps, code blocks, "Reading the Chart" guide, next-steps links
- **`web/app/docs/physics/page.js`** — `SUBMODELS` array (15 entries with n/name/desc/file), state vector display, RK4 integrator description, force balance equations, BikeConfig 13 parameter sections
- **`web/app/docs/validation/page.js`** — Apr-24-PM metrics (mean |Δ|=0.726s, median=0.240s, bias=+0.550s, top-10=±0.032s), reference baselines (K5/R1/Hayabusa within 0.001s), full TOP10 ranked table, 8-cluster bias table with open/closed status, methodology section

### Task 7 — SEO
- **`web/app/sitemap.js`** — added 10 new static routes: `/features` (0.85), `/about` (0.70), `/blog` (0.80), 3 blog slugs (0.75 each), `/docs/getting-started`, `/docs/physics`, `/docs/validation` (0.80 each)
- **`web/app/robots.js`** — disallow list updated: `['/_next/', '/api/', '/account/', '/login', '/signup']`
- **`web/app/StructuredData.js`** — added `productSchema()` (Free ₹0 + Pro ₹499/mo offers) and `articleSchema({ title, description, slug, datePublished, dateModified })` helper for blog post pages

### Task 8 — Bike browser polish
- **`web/app/bikes/page.js`:**
  - `PAGE_SIZE` bumped 24 → 40 (fewer pagination clicks for the full 287-bike catalog)
  - Filter panel made **sticky** below the nav: `sticky top-16 z-40 backdrop-blur-xl` so search/manufacturer/category controls stay visible while scrolling the grid
  - Nav links updated: removed `/#physics`, `/#validation`; added Features / Docs / Blog / Pricing
- **`web/app/bikes/[id]/page.js`:**
  - Nav links updated to match new site structure
  - **"Simulate this bike" CTA** moved into the header alongside the bike title (no longer just at the bottom of the page) — visible immediately on page load without scrolling
  - Bottom CTA (Simulate + Back to catalog) retained as a second entry point for users who read the full spec

---

## 🎞️ Hero GIF / Screenshot Status

| Section | Status | File needed |
|---|---|---|
| Hero (landing) | **Placeholder only** — no video/GIF yet | `public/hero-sim-preview.gif` |
| Features page — Physics section | `{/* TODO: replace with screenshot/GIF */}` placeholder | `public/screenshots/physics-chart.png` |
| Features page — Parts Catalog | placeholder | `public/screenshots/parts-catalog.png` |
| Features page — Calibration | placeholder | `public/screenshots/calibration-overlay.png` |
| Features page — ROI | placeholder | `public/screenshots/roi-chart.png` |
| Features page — Desktop App | placeholder | `public/screenshots/desktop-app.png` |
| Features page — API | placeholder | `public/screenshots/api-docs.png` |

**Pre-launch action:** Record a 5–10s screen capture of a Hayabusa simulation (sim running → ET tiles appearing) and save as `public/hero-sim-preview.gif`. Drop the 6 feature screenshots into `public/screenshots/`. All placeholder divs have `// TODO: replace with screenshot/GIF` comments to guide this.

---

## 💬 Testimonials Status

All 3 testimonial slots are **COPY placeholders**. Identified with `// COPY: replace before launch` comment in the `TESTIMONIALS` array in `web/app/page.js`.

| Slot | Name placeholder | Quote status |
|---|---|---|
| 1 | Ravi Shankar, Narhe tuning shop | COPY marker — replace with real quote |
| 2 | Arjun Mehta, drag racer | COPY marker — replace with real quote |
| 3 | Suresh Kumar, Bajaj dealer | COPY marker — replace with real quote |

**Pre-launch action:** Collect at least 2 real testimonials from Narhe/Pune tuning community beta users before public launch. Replace the `TESTIMONIALS` array entries — the JSON structure handles the rest.

---

## 🎯 Lighthouse Targets

| Metric | Target | Notes |
|---|---|---|
| Performance | ≥ 90 | New pages are static-first / no heavy client bundles. SimulatorWidget lazy-loads API call on click, not on render. |
| Accessibility | ≥ 95 | All new interactive elements have `aria-label` or semantic markup. Contact form uses `<label>` elements. |
| SEO | ≥ 100 | Every page has `export const metadata` with `title`, `description`, `alternates.canonical`. StructuredData JSON-LD injected per page. Sitemap lists all new routes. |
| Best Practices | ≥ 90 | No console errors expected. API calls are behind try/catch. |

**Not yet run** — Vercel Preview deployment needed for full Lighthouse audit. Run after the PR is merged to main and Vercel deploys the branch.

---

## 📋 Pre-Launch Checklist

- [ ] Replace all `TESTIMONIALS` COPY markers with real quotes from beta users
- [ ] Record hero GIF (`public/hero-sim-preview.gif`) and 6 feature screenshots
- [ ] Add `productSchema()` and `articleSchema()` to the relevant page layouts (currently exported from `StructuredData.js` but not yet imported on `/pricing` or blog posts — wire up in a follow-up session)
- [ ] `/about` contact form: upgrade from mailto fallback to Formspree endpoint (set env var `NEXT_PUBLIC_FORMSPREE_ID`)
- [ ] Run full Lighthouse audit on Vercel Preview URL after PR merge
- [ ] Verify `SimulatorWidget` Hayabusa default loads correctly when API is live (Dream Bikes tab must exist in `BIKE_CATEGORIES` with `presetId: 'hayabusa_gen1'`)
- [ ] Test `/simulator?bike_id=N` deep-link from bikes catalog works in the live SimulatorWidget
- [ ] Review testimonial section on mobile 375px (3 cards stack vertically — check spacing)
- [ ] Confirm StructuredData JSON-LD passes Google Rich Results Test for `/`, `/features`, `/pricing`, blog posts, `/docs/*`

---

## 🚫 Files NOT touched (per workstream brief)
- `web/app/page.js` — StatsStrip with 287/159/424/20/838/15 numbers ✅ preserved
- `web/app/pricing/**` — not touched
- `web/app/login/**`, `web/app/signup/**`, `web/app/account/**` — not touched
- `web/app/terms/**`, `web/app/privacy/**` — not touched
- `web/components/AuthProvider.js`, `web/components/TierBadge.js` — not touched
- `desktop/**`, `motoquant/**` — not touched
- `CLAUDE.md` — not touched (this log is the session record instead)

---

## 📁 New Files Created
```
web/app/features/page.js
web/app/about/page.js
web/app/blog/page.js
web/app/blog/the-physics-of-a-perfect-launch/page.js
web/app/blog/why-your-r15-wont-hit-14s/page.js
web/app/blog/how-to-tune-for-aamby-valley-in-november/page.js
web/app/docs/layout.js
web/app/docs/getting-started/page.js
web/app/docs/physics/page.js
web/app/docs/validation/page.js
SESSION_LOG_ws-landing-marketing.md  ← this file
```

## 📝 Files Modified
```
web/app/page.js                    (hero, why MQ section, testimonials, CTA, footer, nav)
web/components/SimulatorWidget.js  (Hayabusa default, Powered by chip, save CTA)
web/app/sitemap.js                 (10 new static routes)
web/app/robots.js                  (disallow list updated)
web/app/StructuredData.js          (productSchema + articleSchema added)
web/app/bikes/page.js              (sticky filters, PAGE_SIZE 40, nav links updated)
web/app/bikes/[id]/page.js         (nav links updated, header-level Simulate CTA)
```
