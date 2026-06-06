# Subagent 7 — Deprecated code & AI slop report
**Scanned:** 2026-06-07
**Files scanned:** 338 (99 Python, 48 blog page.js, 35 desktop TS/TSX, 156 web JS)

---

## Part 1 — Deprecated / legacy

**1a. `nixpacks.toml` — Railway-specific build config, now superseded by `Dockerfile` + `render.yaml`**
- `nixpacks.toml` header reads *"Railway / Nixpacks build configuration"*. Render uses the Dockerfile exclusively; nixpacks.toml is never read in the current deployment path. Safe to delete or keep as dead documentation, but misleads future sessions into thinking it is live config.
- Confidence: HIGH. `render.yaml` points at `dockerfilePath: ./Dockerfile`; no CI job or render.yaml references nixpacks.toml.

**1b. `Procfile` — Heroku/Railway artifact, not used by Render Docker**
- `Procfile` contains `web: uvicorn motoquant.api:app --host 0.0.0.0 --port $PORT`. Render's Docker runtime uses the `CMD` in `Dockerfile`, not Procfile. Only referenced in `.github/CODEOWNERS` as an ownership record. Safe to delete.
- Confidence: HIGH.

**1c. `Dockerfile` line 15 — stale "Railway injects PORT" comment**
- `# Railway injects PORT at runtime` — production is Render; Render also injects `PORT` but the comment names the wrong platform. One-line cosmetic fix: s/Railway/Render/.
- Confidence: HIGH.

**1d. `web/next.config.js` lines 3–11 — comment block still names Railway as the backend**
- The rewrite destination is correctly `motoquant-api.onrender.com` (line 20), but the surrounding comment block refers to `*.up.railway.app` DNS blocking as the architectural rationale. The rationale is still valid (DNS blocks apply to any non-motoquant.in domain), but the specific domain name is wrong. Should read `*.onrender.com`.
- Confidence: MEDIUM (rationale still holds; only the named domain is stale).

**1e. `web/lib/api.js` lines 5–15 — same Railway comment block**
- Same pattern as next.config.js: the proxy rationale cites `*.up.railway.app` wholesale DNS-blocking. Same medium-confidence fix.
- Confidence: MEDIUM.

**1f. `web/app/bikes/[id]/layout.js` lines 20–23, 57 — Railway-specific timeout comments**
- Comment says *"Give the Railway backend a longer rope for SSR: its free tier can cold-start at 10-30s"* and *"most likely the Railway backend is on a cold start"*. Should reference Render. The timeout logic itself (20 s AbortController) is still correct for Render's free tier.
- Confidence: HIGH (user-facing comment is factually wrong about which platform is running).

**1g. `web/app/privacy/page.js` lines 47, 86 — Railway named as current infrastructure provider**
- Line 47: *"stored on servers in us-west2 (Oregon, USA) via Railway (backend)"* — production is now Singapore/Render. Line 86: *"Railway / Vercel — infrastructure providers"*. Both are live legal/privacy disclosures that are factually incorrect post-migration.
- Confidence: HIGH. Privacy page is a legal document; wrong provider name is a material error.

**1h. `motoquant/observability.py` lines 14, 27 — Railway references in docstring**
- *"Set ONE env var on Railway (or wherever the API is deployed)"* and *"different environments (Railway prod, staging…)"*. Minor docstring inaccuracy; low risk but easy to fix.
- Confidence: LOW (docstrings, not live logic).

---

## Part 2A — AI slop: stubs and placeholders

**2A-1. `motoquant/llm/runner.py:774` — inline `# placeholder rows without real pricing`**
- A comment marking pricing data rows as placeholder. Unlike a stub function this is a data-quality note, but it should either be resolved or converted to a structured TODO with a ticket reference.
- Recommended action: check whether real pricing was subsequently seeded; if yes, delete comment; if no, convert to `# TODO(pricing): resolve after vendor query`.

---

## Part 2B — AI slop: narrative comments

**2B-1. `motoquant/defaults.py` lines 222–223, 264–266 — "# was X" inline changelog**
- `band_hi = 0.12  # was 0.16`, `baseline = 0.20  # was 0.30`, `band_lo = 0.25  # was 0.12 (too peaky)`, `band_hi = 0.15  # was 0.08`, `baseline = 0.25  # was 0.12`. Five consecutive edit-history notes inside `_synthetic_2stroke_torque_curve`. Git history records the prior values; these comments add noise without explaining *why* the current value is correct.
- Recommended action: Delete the `# was X` suffixes; keep or expand the explanatory text that follows on the same line (e.g. "powervalve delivers good off-pipe still" is useful; "was 0.30" is not).

**2B-2. `motoquant/scraper/importer.py` lines 405–412 — "Apr-24 experiment" narrative block**
- Eight-line comment block narrates a failed Apr-24 calibration experiment and its reversion. This is session history, not code documentation. The conclusion ("Reverted; logged as a potential follow-up") is the only load-bearing sentence.
- Recommended action: Compress to one line: `# Wheel-loss factor experiment (Apr-24) made all clusters worse; spec.peak_power_hp treated as wheel power throughout.`

**2B-3. `motoquant/category_profiles.py` lines 165–175 — inline calibration narrative**
- Comment block inside `CategoryProfile` definition reads like a session note: *"was under-representing the real shift dynamics, causing 7 of 8 benchmarked bikes to sim slow (bias +0.21s). At 600 rad/s² cluster mean|Δ| drops…"* This is a session report embedded in production code.
- Recommended action: Keep the final conclusion (`max_engine_decel_rads2=600.0` chosen because clutch slip inertia for 600cc I4 ≈ 0.0065 kg·m²), delete the before/after metric table from the comment.

**2B-4. `web/app/blog/600cc-supersport-launch-physics-engine-deceleration/page.js` lines 51, 278 — K5 baseline mislabelled as R1 value (HIGH PRIORITY)**
- Line 51: *"K5 GSX-R 1000, R1 4C8, and Hayabusa Gen 1 — our three load-bearing reference baselines — were nailed to four decimal places (10.2859s / 10.2859s / 10.4712s)."* The first number should be `10.0334s` (K5), not `10.2859s` (R1). The same error recurs at line 278.
- This is the specific drift documented in CLAUDE.md: *"2 pre-existing unrelated drifts remain in a 600cc blog post (mislabels K5 baseline)"*.
- Recommended action: `s/10.2859s \/ 10.2859s/10.0334s \/ 10.2859s/g` at both lines.

---

## Part 2C — AI slop: over-docs

**2C-1. `motoquant/scraper/importer.py:157` — `_fluid_mass_from_spec()` doc=12L body=3L**
- A 12-line docstring on a 3-line function that clips `fluid_mass_kg` between bounds. The docstring includes calibration rationale that is useful but could be trimmed to 3–4 lines.

**2C-2. `motoquant/scraper/importer.py:176` — `_basket_inertia_from_spec()` doc=14L body=3L**
- Same pattern: 14-line docstring on a 3-line clamp function.

**2C-3. `motoquant/llm/summarize.py:100` — `summarize_result()` doc=11L body=3L**
- 11-line docstring on a dispatcher that calls one of three sub-summarizers.

**2C-4. `motoquant/scraper/bulk_scrape.py:61` — `_utcnow_iso()` doc=6L body=1L**
- 6-line docstring on `return datetime.utcnow().isoformat() + "Z"`. The function name is self-documenting; the docstring is pure noise.
- Recommended action: Delete docstring entirely; it adds nothing over the function name.

---

## Part 2D — Defensive over-wrapping

44 bare `except: pass` handlers found across the codebase. The highest-risk cluster:

**2D-1. `motoquant/api.py:652` — telemetry event logging swallows all exceptions silently**
- `except Exception: pass` wrapping the `/api/event` telemetry write. Acceptable for fire-and-forget telemetry; add `log.debug("telemetry write failed", exc_info=True)` so failures are visible in logs without breaking the endpoint.

**2D-2. `motoquant/api.py:831` — bike detail JSON blob enrichment swallows parse errors**
- `except Exception: pass` on the block that enriches bike config JSON for the detail page. A malformed JSON blob silently returns a partially-enriched response with no indication of failure. Recommend `log.warning(...)` at minimum.

**2D-3. `motoquant/api.py:1051` — stock sim baseline silently drops on any error**
- `except Exception: pass` means a stock sim failure causes the compare route to return delta ET of zero with no warning. The subsequent sim may still succeed, producing a silently wrong delta.

**2D-4. `motoquant/database/retail_adapters/__init__.py` lines 156, 297, 500, 535 — four bare-pass scrapers**
- HTTP scraping failures silently return `None`. Acceptable for scraper resilience, but a counter or warning log would help diagnose systematic failures.

---

## Numerical summary

```
{
  "legacy_blocks": 8,
  "stubs": 1,
  "narrative_comments": 4,
  "over_docs": 4,
  "defensive_wraps": 44,
  "ai_slop_phrase_hits_in_blog": 4
}
```

**Notes:**
- The 4 blog AI-slop phrase hits include 1 true slop word ("transformative" in Dominar post) and 3 uses of "leverage" in technically accurate mechanical context (handlebar leverage, mechanical leverage, thermodynamic leverage) — the 3 mechanical uses are NOT slop and should NOT be changed.
- The 44 bare-pass handlers are dominated by `motoquant/scraper/bikez.py` (7) and `motoquant/database/retail_adapters/__init__.py` (4), which are network-scraping paths where swallowing is defensible. The `motoquant/api.py` cluster (8) is higher risk.
- `nixpacks.toml` and `Procfile` are the cleanest deletes: zero downstream references in active code.
