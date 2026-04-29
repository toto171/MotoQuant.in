# MotoQuant Pro — Legacy website snapshot

This directory is a frozen copy of the marketing site as it existed at commit
**`1a18652`** (April 30, 2026), immediately before the **Direction A** scroll-driven
rework.

It mirrors what was in `web/` at that time: all `app/*` routes, components,
config, scripts, and public assets. It is checked into git so that anyone
exploring the repo can read the previous version of any page without
needing a `git checkout`.

## Why this exists

The current `web/` ships the post-April-30 Direction A rework: cinematic
motorsport hero, sticky christmas tree, pinned telemetry HUD with an
MV-F4-style superbike silhouette, filtered cluster bias chart, and a
new `/whitepaper` page. If anything regresses on the live site, this
snapshot is the immediate fallback.

## How to roll back

There are three ways to restore the previous site, in order of safety:

### 1. Per-file rollback (most common)

```bash
# Restore a single page from the snapshot:
cp -r web-legacy/app/<route>/page.js web/app/<route>/page.js

# Or, equivalently, from git history:
git checkout 1a18652 -- web/app/<route>/page.js
```

### 2. Whole-site rollback to the legacy snapshot

```bash
# Replace every file under web/ with its web-legacy/ counterpart
rsync -a --delete web-legacy/ web/

# Or, equivalently, from git:
git checkout 1a18652 -- web/
```

### 3. Deploy the legacy site standalone

If you want the legacy site live alongside the new one (e.g. on a
`legacy.motoquant.in` subdomain), rename `web-legacy` to its own
project root and point a new Vercel project at it:

```bash
mv web-legacy web-legacy-deploy
cd web-legacy-deploy
# package.json, next.config.js, tailwind.config.js etc. are all already here
npm install
npm run build
# then connect this directory as a separate Vercel project
```

## What changed in the rework (high level)

- **Shared `<SiteNav>` and `<SiteFooter>`** components introduced — every
  page now renders the same nav/footer instead of each page carrying
  a duplicated copy.
- **Realistic MV-Agusta-F4-style superbike SVG silhouette**
  (`components/BikeSilhouette.js`) replaces the abstract glow-orb hero.
- **Christmas tree** (`components/ChristmasTree.js`) drives off scroll
  progress with NHRA-accurate signal positions: pre-stage pair, stage
  pair, three ambers, green, red.
- **Pinned telemetry HUD** (`components/TelemetryHUD.js`) plays a real
  GSX-R K5 quarter-mile run as you scroll through the section.
- **Cluster bias chart** on the landing page now shows only the
  source-quality-clean clusters (litre 195+, litre 600-1000, mid-twin
  300-500, overall). The 2T / small-cc / cruiser clusters with
  benchmark-data-bounded residuals are documented in
  `/docs/validation` and `/whitepaper` instead.
- **New `/whitepaper` route** with a peer-review-style technical
  writeup of the physics engine, the 8-cluster taxonomy, and the
  validation methodology.
- **Pricing, login, account** — converted from light gray-* theme
  to the unified Direction A black + brand-orange palette.
- **All other routes** (features, about, blog, blog articles, docs,
  bikes catalog, terms, privacy) — nav/footer swapped to shared
  components, content preserved.

## Compatibility notes

The legacy snapshot uses the older `bg-ink-0` background variant in
several places and per-page nav blocks. If you re-deploy this snapshot
as-is:

- The `tailwind.config.js` in `web-legacy/` is the original (no
  `brand-green` / `brand-amber` / `brand-red` tokens). Direction A
  components will not render correctly if mixed across the two trees;
  always pull from the same snapshot.
- Razorpay subscription flows, AuthProvider, the SimulatorWidget, and
  the FastAPI `lib/api.js` rewrite are all preserved. No backend
  contract changed in the rework.

— last updated April 30, 2026
