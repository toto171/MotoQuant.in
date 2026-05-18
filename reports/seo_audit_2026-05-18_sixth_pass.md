# SEO Audit — 2026-05-18 (sixth pass, late-night)

## Scope
Catalog sixth pass shipped 3 bikes (Yamaha XSR900 GP, Kawasaki Ninja
ZX-4R, Bajaj Pulsar N125). Marketing-content shipped the ZX-4R blog. SEO
sixth-pass: mark ZX-4R `done`, add 3 new opportunities (XSR900 GP, Pulsar
N125, XSR900 GP vs MT-09), inject the new entities into surfaces the SEO
agent owns (simulator keywords, StructuredData FAQ, landing-page tile).

## Opportunities (4 new, 1 marked done)

| P | Keyword | Vol (IN) | Target | Action |
|---|---|---|---|---|
| 25 | kawasaki ninja zx-4r quarter mile | med-high | /blog/...zx-4r... | done |
| 26 | yamaha xsr900 gp quarter mile | low IN / med global | /bikes | create-blog-later |
| 27 | bajaj pulsar n125 quarter mile | high | /bikes | create-blog-later |
| 28 | yamaha xsr900 gp vs mt-09 | low IN / med global | /bikes | create-blog-later |

Total in `data/seo_opportunities.json` after pass: **28 opportunities**, 9 escalations.

## On-page edits (3 files)

1. **`web/app/simulator/layout.js`** — keywords array 17 → 20 entries
   (added `kawasaki zx-4r quarter mile`, `yamaha xsr900 gp drag`,
   `pulsar n125 quarter mile`). Description / title / canonical unchanged.

2. **`web/app/StructuredData.js`** — "Which bikes are supported?" FAQ answer
   gained entity mentions for Pulsar N125 / NS400Z, Kawasaki Ninja ZX-4R +
   ZX-4RR (400cc inline-four pair), Yamaha XSR900 GP. Bike count (342)
   preserved; FAQ schema structure unchanged.

3. **`web/app/page.js`** — "Indian Market-First" tile body refreshed to name
   specific high-intent entities (Pulsar N125 / NS200 / NS400Z, Apache RTR,
   R15 V4, Duke 390, RE Interceptor 650) and the Kawasaki ZX-4R/ZX-4RR
   400cc inline-four pair. Tile CTA + href untouched.

## Escalations queued (2 new)

- marketing-content: Yamaha XSR900 GP vs MT-09 platform-pair post.
- marketing-content: Pulsar N125 + 125cc commuter shootout once Raider /
  Splendor / Glamour land in catalog.

## Verification

- JSON syntax valid (`json.load` parse OK).
- "342 bikes" claim preserved on every surface touched. Live db count drift
  (342 web vs db 402) is a separate agent's scope.
- Canonical URLs + schema.org structure unchanged.
- No `/blog/*` or `/sitemap.js` edits — marketing-content owns those.
