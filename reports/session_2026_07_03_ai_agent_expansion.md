# Session Report — July 3, 2026: Agentic Chat AI + International Catalog Expansion + Physics Pass

**Branch:** `claude/motoquant-roadmap-ai-n97val` · **Model:** claude-fable-5 (multi-agent orchestration: 2 workflows + 3 standalone agents, ~3.5M subagent tokens)
**Baselines:** K5 10.0334 / R1 10.2859 / Hayabusa 10.4712 — **Δ+0.0000 (repr-bit-identical) at every checkpoint.**
**Weighted sweep (acceptance gate):** 246 matched / weighted |Δ| **0.2417s** (was 0.2486, −2.8%) / bias −0.026s. New authoritative artifact: `reports/acc_final_2026_07_03.json`.

## 0. Roadmap deliverable

`reports/ROADMAP_2026_07_03.md` — the complete deduplicated inventory of outstanding work
(37 open engineering/data items, prioritized) and manual/operator-only actions (15, by urgency),
compiled from every tracker + a 6-agent code recon.

## 1. Chat AI → multi-step tool-calling agent (the session core)

The `/api/chat` surface is now a real agent (`motoquant/llm/agent.py`, mode `agent` default;
the classic pipeline remains as `mode: "classic"` and for the CLI). Docs: `docs/CHAT_AGENT.md`.

- **`LLMClient.call_tools`** (`llm/client.py`): multi-turn, multi-tool, `tool_choice` auto on
  BOTH provider branches (Anthropic native + OpenAI-compat = Groq/Gemini/DeepSeek/OpenRouter).
  Neutral message format documented in-code; empty tools list omits the param (providers reject
  empty arrays); testable offline via the `_call_override("tools", …)` seam.
- **15 tools:** search_bikes / get_bike_details / run_simulation / run_top_speed / compare_bikes /
  search_parts / list_tires / resolve_venue / list_venues / optimize_build / autotune_setup /
  simulate_estimated_bike / web_search / web_fetch / get_catalog_stats.
- **Multi-turn conversations:** `ChatRequest.messages` (client-held history, server stateless,
  capped 16 msgs/16k chars). Web ChatPanel rebuilt as a transcript UI.
- **Hard budgets enforced by the executor, not the model:** 8 LLM iterations, 20 full sims,
  2 heavy ops per message. Chat sims now METERED into the free-tier `sim_usage` quota
  (identity captured at route time — closes the "choose_bike burns 25 unmetered sims" gap).
- **Stage 1–4 build glossary** (`BUILD_TIERS`, single source of truth) + outlaw/open-class
  aliases; classic pipeline gains matching `stage_3`/`stage_4` recipes + parser enum + prompts,
  with explicit "open class BIKE (choose_bike litre) vs open class BUILD (stage_4)" disambiguation.
- **Outlaw/open-class composed pipeline** (`motoquant/analysis/outlaw.py` + `POST /api/jobs/outlaw`):
  drag_prep rubber (highest-μ rear fitment) → full_race parts knapsack (budget `null` = no limit,
  resolved to the ₹5M cap — never `inf`, the DP would overflow) → gearing+launch autotune on the
  MODIFIED bike → combined verification sim, with compare-style partitioned progress.
  E2E-verified: Hayabusa Gen2 10.223 → **9.211s** (−1.013s; M&H slick + ₹489k build + setup) in 20s
  sandbox wall time. `OptimizeBuildRequest.budget_inr` is now optional (null/0 = no limit).
- **Web lookup** (`llm/webtools.py`): Brave/Serper via `SEARCH_PROVIDER`+`SEARCH_API_KEY` env,
  DuckDuckGo HTML fallback keyless; SSRF guard (private-range refusal), 512KB/8k-char caps,
  errors-as-data. `MOTOQUANT_WEB_TOOLS=0` kill switch. `requests` now pinned in
  requirements-api.txt (was transitive-only). NOTE: unverifiable live from this sandbox
  (proxy 403s external hosts) — prod Render egress is proven by 5 existing paths; the
  degraded-failure path IS verified.
- **Unknown-bike estimation** (`llm/estimator.py`): LLM spec dict → `spec_from_dict`
  (source `llm_estimate`, per-field confidence capped 0.60) → `validate_spec` (bounds + unit
  auto-correct; hard reject) → `spec_to_bike_config` (DB-free) → quarter + top-speed sims.
  Always labelled ESTIMATED with confidence + assumptions; misses logged to `bike_suggestions`.
- **Job-backed chat:** `POST /api/jobs/chat` (progress stages + Stop; ChatPanel uses it via the
  existing `runJob` poller with sync fallback).
- **API contract fixes:** ChatResponse now carries `intent_type` + ALL classic intent payloads
  (compare/rank/recommend/explain/choose_bike were computed then DROPPED — July-2 audit item) +
  agent `blocks`/`tool_trace`/`sims_run`; `sim_result` mirrors the last sim block for old clients.
- **Chat correctness fixes:** typed `rate_limited` error (was generic parse_failed on 429);
  smalltalk live catalog counts (was hardcoded "327 bikes"); GROQ_API_KEY-aware operator banners
  (web + desktop + docstring; was ANTHROPIC_API_KEY); web ChatPanel catch-all error branch
  (rank/recommend/choose_bike failures used to render NOTHING).
- **Kaizen catch:** rider_mass_kg originally wrote a phantom `RiderParams.rider_mass_kg`
  attribute (physics reads `chassis.rider_mass_kg`) — fixed in agent + estimator, pinned by
  `test_sim_modification_knobs_are_live` (every modifier must MOVE the ET).
- **Web UI** (`ChatPanel.js` 263→727 lines): transcript, job progress + Stop, per-block renderers
  (sim tiles / estimated-badge + assumptions / compare table / build + outlaw parts lists /
  autotune setup / citations), refreshed example chips, New-chat reset. BuildOptimizer gains
  "Outlaw — no limit" preset (posts `budget_inr: null`) + slider max 2M.
- **Tests:** `tests/test_agent.py` (34: format conversion, loop, budgets, metering, estimation,
  history clipping, knob liveness, API routes incl. jobs lifecycle) + `tests/test_outlaw.py` (13:
  pipeline structure/physics sanity/unlimited-budget semantics/JSON safety).

## 2. International catalog expansion (+34 bikes → 535; +31 parts → 594; +25 tires → 257)

Three new sibling spec modules (each carrying its own instrumented ET/top-speed benchmark lists,
merged by the sweep scripts):
- **`known_bikes_2026_us.py`** (12): Harley Breakout 117 / Fat Bob 114 / Street Bob 114 /
  Low Rider S 117 / Iron 883 / Forty-Eight; Indian Challenger / 101 Scout / Chief Bobber DH;
  Buell XB12R; EBR 1190RX; Honda CBR1100XX Super Blackbird (+ its CW-1997 10.27s benchmark —
  closes a long-queued carry-forward).
- **`known_bikes_2026_jpeu.py`** (14): ZX-12R, V-Max 1200, GSX-R600/750 L1 (2011-24), ZRX1200R,
  GSX1400, Speed Triple 1050 ×2 gens, Street Triple 675, Ducati 996 / Diavel 1260 S /
  Panigale V2 890 (2025), MV Dragster 800 RR, Bimota Tesi H2 (supercharged 228hp). 6 instrumented
  ET benchmarks + 8 top-speed rows.
- **`known_bikes_2026_world.py`** (8): Kove 450RR, Benda LFC 700, QJ SRK 800 RC, CFMoto 1250TR-G,
  Zontes GK350, Ninja 1100SX (2025), CBR600RR (2024), Suzuki Raider R150 Fi. ET benchmarks
  honestly empty (no instrumented tests exist — reasoning documented in-module).
- Every load-bearing spec web-verified with cited sources; judgment fields (cd/frontal area)
  reasoned in comments; zero fabricated products/benchmarks; 34/34 pass `validate_spec` with 0
  errors; DB-path sanity sims all class-plausible (ZX-12R 10.03 vs 9.87-10.04 tested).
- **Parts** (`seed_catalogs/drag_essentials.py` + `euro_brand_exhausts.py` + fixes):
  **3 NEW categories** — lowering_kit (6), air_shifter (4), lockup_clutch (3) — the three most
  drag-authentic categories the catalog lacked; V2-cruiser nitrous ×4 (NX/DynoTune,
  Harley/Indian); Trask M8 turbo kits ×2 + the existing Trask kit's displacement cap 1750→1950
  (+`Indian` alias — it matched ZERO Indian bikes before); 12 real exhausts for
  Triumph/MV Agusta/Moto Guzzi/CFMoto. Exclusivity wired: roi.py EXCLUSIVE_CATEGORIES + cross-slot
  aliases (lockup↔clutch_kit, air_shifter↔quickshifter) + desktop BuildPage mirror.
- **Tires** (`seed_catalogs/drag_tires_cruiser.py`): 11 drag (Shinko Hook-Up/Stealth/R005 240,
  M&H, Mickey Thompson) + 8 cruiser (Night Dragon/D408/Cruisetec); fitments are QUERY-DRIVEN
  (519 rows planned by category/displacement/OEM-rim rules — works for future bikes too).
- **Data gaps honestly reported, not faked:** sub-500cc wheelie bars (Apr-30 carry-forward remains
  open), QJ exhausts, 240/18 cruiser rears (no bike carries the fitment yet).
- **DB pipeline run:** import_batch (34, idempotent×2) → seeds (idempotent×2) →
  `reseed_configs_from_specs.py` (532 updated; propagates the shaft/belt fix) →
  merge_manufacturers + parts_fitment patches. Parts/bike min 21 / median 107 / max 212;
  0 bikes without exhaust; 0 unreachable parts.

## 3. Physics: safe dead-knob pass + 19% speedup (all bit-identical)

- **Micro-optimizations in `physics.py` run()** — dead `aero_drag` call removed, per-iteration RK4
  closures eliminated, slip-branch engine-torque recomputation cached, loop invariants hoisted:
  K5 wall time 394→319ms (**−19%**), all three baselines repr-bit-identical after every batch.
- **3 CategoryProfile knobs wired** (track_surface pattern; structural no-ops at shipped values):
  mu_peak_override, launch_rpm_factor, cd_floor. Pinned by `tests/test_profile_knobs.py` — each
  knob is proven no-op at defaults AND proven to MOVE ET when set, so none can silently die again.
- **Importer shaft/belt sentinel fix:** `front_sprocket=0` (the documented shaft/belt marker) no
  longer fabricates K5 chain gearing; NEW `_SHAFT_BELT_FINAL_DRIVE` (23 researched entries,
  VERIFIED vs ESTIMATED flagged: R1250GS bevel 2.91, FJR1300 2.698, V-Rod belt 2.571, …).
  Only the R1250GS's spec-path ET moved (11.4357→11.4164s); regression tests added.
- **Sprocket-position hole closed:** 14 positionless DB sprockets stamped (idempotent
  `scripts/patch_2026_07_03_sprocket_position.py`) + name-regex fallback in roi.py; pinned by a
  co-selection test (two front sprockets can no longer stack in the knapsack).
- **Numba REJECTED with rationale** (do not re-litigate): the RK4 loop is object-access-heavy
  scalar Python, not numpy-array-heavy; nopython can't compile it as written; jitting = full
  rewrite + voids the bit-identical pin (LLVM/libm divergence) + ~60-90MB on the 512MB image.
  Sweep speed levers: multiprocessing across bikes, existing adaptive-dt, the surrogate.
- **Epoch-gated (NOT wired, by design):** pacejka_force (needs a wheel-speed ODE state),
  4-branch clutch dispatch (K5 is CLUTCH_LOCKUP — baselines move immediately; also why the new
  lockup_clutch parts are currently ET-neutral), staging dead-time/rollout (shifts all 246
  benchmarks ~0.1-0.35s — calibration has absorbed it), tuck_transition_time_s. Any of these =
  a deliberate re-baselining epoch in a dedicated session.
- **Physics follow-up discovered by the parts work:** the wheelie limit is not the binding launch
  constraint (raising Hayabusa CoG +55mm GAINS 0.113s), so lowering kits currently score
  positive ET. The seeded CoG deltas are physically correct — fix the physics, not the data.

## 4. Surrogate v2.2 + accuracy-content sync

- Surrogate regenerated per the standing contract (34 new bikes + 20 gearing-corrected bikes made
  v2.1 rows stale) — see `artifacts/surrogate/README.md` v2.2 section for metrics.
- Sitewide accuracy claims synced to the new sweep (landing HONEST_CLUSTERS + top-10 slip,
  docs/validation tables, whitepaper, blog) — 223-benchmark corpus / 246 matched / |Δ| 0.2417 /
  bias −0.026.

## 5. Verification summary

- Baselines Δ+0.0000 (repr-equal) after: chat backbone, physics pass, imports, seeds, reseed,
  patches. Full weighted sweep improved. Full pytest suite + ruff clean (see PR).
- Desktop: tsc --noEmit exit 0, vitest 33/33.
- Web: next build 75/75 ×2 (post-ChatPanel, post-content-sync), verify-web 180 files clean.
- Known pre-existing (NOT this session): test_spec_corrections 4 ordering-dependent failures in
  full-suite runs (green in isolation; same env-leak class as the July-2 test_api fix — new test
  modules here use the collection-order-proof setUpModule pattern).

## 6. Operator notes

- **New optional env keys** (Render dashboard): `SEARCH_PROVIDER` + `SEARCH_API_KEY` (upgrades
  chat web-lookup from the keyless DuckDuckGo fallback); `MOTOQUANT_WEB_TOOLS=0` to disable web
  tools. Chat still requires `GROQ_API_KEY` (or `LLM_PROVIDER` + that provider's key).
- **Groq budget:** an agent turn = 2-8 LLM calls (was 2). If the 30 RPM free tier saturates,
  set `LLM_PROVIDER=gemini` or add a paid key. Provider swap needs no code change; any
  OpenAI-compatible API you're scoping = one `_PROVIDERS` entry.
- The full outstanding-work + manual-actions inventory is `reports/ROADMAP_2026_07_03.md`.
