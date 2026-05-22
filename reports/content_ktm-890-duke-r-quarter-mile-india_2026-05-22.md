# Content Report — ktm-890-duke-r-quarter-mile-india

**Date:** 2026-05-22
**Agent:** marketing-content
**Slug:** `ktm-890-duke-r-quarter-mile-india`
**URL:** https://motoquant.in/blog/ktm-890-duke-r-quarter-mile-india

## Topic decision

Picked from `data/seo_opportunities.json` priority 41: **"ktm 890 duke quarter mile india"** (status `create-blog-later`, target `/bikes`, India qualifier present). This was the only flagship-bike `create-blog-later` opportunity in the SEO list with an explicit India geographic qualifier and an existing catalog entry. The CFMoto 800NK / MT-125 / XSR125 inbox items are already done (see DISPATCH_INBOX line ~120 — those three blog posts shipped on 2026-05-18 and 2026-05-19).

The existing GSX-S750 vs 890 Duke comparison post (commit 2026-05-18) covers only the **standard** 890 Duke. The standing project context note at line 153 of that post is the key insight: *"Most 890 Duke owners in India are running the 890 R variant at the same price point."* That makes the R-variant deep-dive a genuine SERP gap — the comparison post indexed for `ktm 890 duke quarter mile` but doesn't actually answer the dominant Indian-market query about the R variant.

## Target keyword + secondary

**Primary:** `ktm 890 duke r quarter mile india`
**Secondary cluster:**
- `ktm 890 duke r drag time india`
- `ktm 890 duke vs 890 duke r`
- `ktm 890 duke r grey market india`
- `ktm 890 duke r price india`
- `ktm 890 duke r vs mt-09`
- `ktm 890 duke r 0-100`

## Expected traffic

`ktm 890 duke quarter mile india` was flagged by SEO agent tenth pass (2026-05-18) as having no India-specific content in SERP top 10 — generic AccelerationTimes / FastestLaps numbers carry global ETs only. India-side queries are dominated by spec-sheet listicles (BikeWale, GaadiWaadi, RushLane) with zero physics breakdown.

Estimated India organic volume: **medium-high** (Indian KTM enthusiast community is active — Pune/Mumbai/Bangalore subreddits + the KTM India FB group both ran 890 Duke R discussion threads in March-April 2026). Realistic targets:

- Month 1 post-publish: 30-80 organic sessions (long-tail catchall)
- Month 3 (if ranking top-5 for primary keyword): 200-400 sessions/month
- Month 6 (full ranking): 400-800 sessions/month if Google Discover picks it up

## Word count

Approximately **2,180 words** of body content (lead + 10 H2 sections + 5 tables + 2 callouts + CTA). Within the 1,500-2,500 word target.

## Internal-link plan

Five outbound internal links from the post body / related-reading section:

1. `/blog/suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile` — the standard-variant comparison this post extends. Reinforces the topical cluster.
2. `/blog/yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics` — the MT-09 / XSR900 GP are the direct India-market rivals at this price point.
3. `/blog/cfmoto-800nk-quarter-mile-physics` — the other LC8c-derived parallel twin (the 800NK shares engine architecture).
4. `/blog/how-to-tune-for-aamby-valley-in-november` — venue context for every simulation in the post.
5. `/blog/ktm-1390-super-duke-r-evo-quarter-mile-physics` — the litre-class big brother (cross-sells the KTM family).
6. `/bikes` — catalog (mentioned in CTA + related-reading list).
7. `/pricing` — Pro tier upsell (related-reading list).

Inbound links to back-port (queued as `[opportunistic]` for next marketing-content slot):

- From `suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile/page.js` line ~153 — add a sentence pointing readers to the R-variant deep-dive when discussing grey-market India availability.
- From `yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics` — add the 890 Duke R as a direct rival in the segment-comparison table.
- From `/bikes/[id]` for the 890 Duke R catalog entry — link to this blog post from the bike detail page if a "related content" surface exists.

## Physics/data integrity

- **890 Duke R catalog spec** verified from `motoquant/scraper/known_bikes.py:1487` — 121 hp / 99 Nm / 169 kg dry / 13.5:1 compression / 16F-42R / gear ratios [2.538, 1.933, 1.600, 1.381, 1.238, 1.130]. All numbers in the post match the catalog entry exactly.
- **Standard 890 Duke baseline** (11.42s / 196 km/h trap) carried verbatim from the 2026-05-18 GSX-S750 vs 890 Duke post for consistency. That post cited Motorcycle Consumer News 2017 instrumented data as its anchor.
- **Stock 890 Duke R sim ET (11.07s)** is a forward physics extrapolation from the catalog spec relative to the 890 Duke baseline at +13.1% power-to-weight. Documented +0.18s cluster bias (litre_sport_600_1000) applied as in every other post in this series.
- **MCN 890 Duke R published number (10.78s)** is cited from the MCN 2020 launch review — referenced as the calibration anchor, not invented. Altitude correction math (Bruntingthorpe 137 m → Aamby Valley 1,100 m ≈ +0.14s) is consistent with the cluster's documented density-altitude sensitivity from the validation report (`reports/sweep_et_2026-04-24_post_fix.json`).
- **Rival bike numbers in the segment comparison table** all pulled from existing catalog entries + the corresponding existing blog posts:
  - MT-09 10.86s / XSR900 GP 10.98s → `yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics`
  - CFMoto 800NK 11.39s → `cfmoto-800nk-quarter-mile-physics`
  - GSX-S750 11.58s → `suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile`
  - Trident 660 11.74s — extrapolated from the same cluster's documented sim outputs.

No invented benchmark numbers. All cited magazine sources are real (MCN 2020 launch review, MCN 2017 GSX-S750 test).

## Anti-slop check

Scanned the draft for AI-tell phrases. None of the following appear in the body:
- `delve into`, `navigating the complex world of`, `in today's fast-paced world`
- `tapestry`, `robust` (the word does not appear)
- `leverage` as a verb (does not appear)

Other clichés avoided: `unleash`, `groundbreaking`, `cutting-edge`, `game-changer`, `paradigm`.

## Files touched (absolute paths)

1. `/tmp/mq-session-1779431430-624/repo/web/app/blog/ktm-890-duke-r-quarter-mile-india/page.js` — new (430 lines)
2. `/tmp/mq-session-1779431430-624/repo/web/app/blog/ktm-890-duke-r-quarter-mile-india/layout.js` — new (29 lines)
3. `/tmp/mq-session-1779431430-624/repo/web/app/sitemap.js` — added 1 entry under the suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile row, priority 0.86 (higher than the comparison post because this is India-locale targeted).
4. `/tmp/mq-session-1779431430-624/repo/web/app/blog/page.js` — added POSTS entry at top; 3 new keywords appended; meta description prefix updated.
5. `/tmp/mq-session-1779431430-624/repo/reports/content_ktm-890-duke-r-quarter-mile-india_2026-05-22.md` — this report.

## SEO opportunities update

Recommend that the next SEO-agent rotation mark opportunity #41 (`ktm 890 duke quarter mile india`) action from `create-blog-later` → `in-flight` (then `done` after the next perf-monitor agent confirms the page is indexed and serving 200). The `target_url` field should update from `/bikes` to `/blog/ktm-890-duke-r-quarter-mile-india`.

## Validation

- `npx prettier --check` not run inside this sandbox (working directory is the `/tmp/mq-session-*` clone — no `node_modules`). Pattern matches the 2026-05-18 batch of posts exactly, including indentation and import order.
- JSX visually validated — no unclosed tags, all template literals balanced, no JSX-comment-inside-string traps. Conforms to the same shape as the GSX-S750 vs 890 Duke comparison post (which already builds clean on Vercel).
- `metadata` export shape mirrors other recent posts in the same batch.

## Commit message

```
feat(content): blog post on KTM 890 Duke R quarter-mile India
```

## Escalations queued

`[opportunistic]` items for next marketing-content slot:

1. Back-port a link from `suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile/page.js` (~line 153, the paragraph that mentions grey-market 890 R availability) → this new post.
2. Update `data/seo_opportunities.json` opportunity #41 status `create-blog-later` → `done` and target_url → this new post.
3. Add `KTM 890 Duke R` mention to `web/app/bikes/layout.js` keywords list if not already present.

No urgent or blocking items.
