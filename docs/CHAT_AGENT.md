# MotoQuant Chat Agent (July 2026)

The `/api/chat` surface is now a **multi-step tool-calling agent**
(`motoquant/llm/agent.py`) instead of the fixed two-LLM-call pipeline. The
classic pipeline remains available (`mode: "classic"`) and unchanged for the
CLI and older clients.

## What it can do

* **Real conversations** — the client sends prior turns in
  `messages: [{role, content}]`; follow-ups ("what about at Aamby?", "now add
  a full exhaust") keep context. The server stays stateless.
* **Complex questions** — the model freely composes 15 tools across the whole
  product: catalog search, full RK4 sims, top-speed runs, A/B compares,
  fitment-filtered parts and tires, venue/weather resolution, the real
  build-optimizer knapsack, gearing+launch autotune, live catalog stats.
* **Stage 1–4 builds** — industry-standard drag-build tiers are first-class
  (`BUILD_TIERS` in agent.py = the single glossary):
  * stage_1 — bolt-ons (exhaust/filter/ECU), ₹60k default
  * stage_2 — + drivetrain (clutch/QS/sprockets/chain/battery), ₹200k
  * stage_3 — + nitrous/fuel/suspension, ₹500k (engine internals aren't in
    the parts catalog, so stage 3 is honestly approximated)
  * stage_4 / **outlaw / open class** — full drag prep, **no budget limit**
* **Outlaw builds run a composed pipeline** (`motoquant/analysis/outlaw.py`,
  also exposed as `POST /api/jobs/outlaw`):
  drag_prep rubber → full_race parts knapsack (budget resolved to the ₹5M
  internal ceiling — never `inf`, the knapsack DP would overflow) → gearing +
  launch-RPM autotune on the modified bike → combined verification sim.
* **Web lookup** (`motoquant/llm/webtools.py`) — when the model needs facts it
  doesn't know. Providers: `SEARCH_PROVIDER=brave|serper` + `SEARCH_API_KEY`
  env (Render dashboard), else a free DuckDuckGo HTML fallback. SSRF-guarded,
  size-capped, failures degrade to error-as-data. `MOTOQUANT_WEB_TOOLS=0`
  disables entirely.
* **Bikes NOT in the catalog** (`motoquant/llm/estimator.py`) — the model
  gathers real specs (own knowledge or web), then
  `simulate_estimated_bike`: spec dict → `validate_spec` (physical bounds +
  unit auto-correction; hard reject on nonsense) → `spec_to_bike_config`
  (DB-free) → full sim + top speed. Results are always labelled **ESTIMATED**
  with a confidence score and the assumptions made (gearing tier, synthetic
  torque curve, category aero). Misses are logged to `bike_suggestions`.

## Discipline & guardrails

* The system prompt forbids invented numbers; every ET/trap/speed must come
  from a tool result. Estimated sims are always labelled.
* Hard per-message budgets enforced by the **executor** (not the model):
  8 LLM iterations, 20 full sims, 2 heavy ops (optimizer/autotune/outlaw).
* **Pro-tier tools.** `optimize_build` and `autotune_setup` (which includes
  the stage_4 / outlaw pipeline) are the same paid surfaces as
  `POST /api/optimize/build`, `POST /api/autotune/ecu` and
  `POST /api/jobs/outlaw`. The chat executor **inherits the caller's tier**,
  resolved from the bearer token by `get_optional_user` on both chat routes,
  so the two entry points gate identically. Behaviour matches `require_tier`:
  * `MOTOQUANT_BILLING_ENFORCE` **off** (the beta default) → completely
    inert, anonymous callers keep full access;
  * **on** → a caller below `pro` gets a typed
    `{"error": "upgrade_required", required_tier, current_tier, upgrade_url}`
    **tool result** (data, not an exception), so the model relays the upgrade
    path in its own words instead of the request failing. The system prompt
    also tells the model up front, so it does not waste iterations
    discovering the lock.
* Chat sims are **metered** into the free-tier `sim_usage` quota (identity
  captured at route time); when `MOTOQUANT_BILLING_ENFORCE` is on, an
  exhausted quota blocks further sims and the agent explains politely.
  Coverage is now the whole surface, not just agent-mode single sims:
  * agent sim tools — 1 unit each (`compare_bikes` 2, `simulate_estimated_bike`
    2, `rank_bikes` its planned batch);
  * agent heavy ops — a nominal **18 units** (`HEAVY_OP_SIM_COST`, derived
    from autotune's own sweep total: 1 baseline + 9 gearing + 7 launch + 1
    combined), and **36** for the composed outlaw pipeline, which runs both
    an optimizer and an autotune pass;
  * **classic mode** — 1 unit for simulate/explain, 2 for compare, and the
    planned batch for rank (≤15) and choose_bike (≤25). This was the biggest
    hole: classic mode is client-selectable and could burn 25 full RK4 sims
    per request while recording nothing.

  Every path **reserves before it runs**, so the block decision happens
  before the CPU is spent. An exhausted quota surfaces as
  `error: "quota_exceeded"` in classic mode and as tool-result text the agent
  relays in agent mode. `explain` is the one deliberate exception: its sim is
  optional grounding, so it degrades to an ungrounded answer instead of
  failing.
* Rate limit unchanged: 20 chat requests/min/IP. Provider 429s surface as a
  typed `rate_limited` error (both agent and classic modes).

## API

* `POST /api/chat` — body `{query, messages?, mode?}`; returns `ChatResponse`
  with `summary` (the reply), ordered `blocks` (`[{type, payload}]`:
  `sim_result | top_speed | compare_result | build_result | outlaw_result |
  autotune_result | estimated_sim | parts | tires | web_citations |
  bike_details | venues`), `tool_trace`, `sims_run`. `sim_result` mirrors the
  last sim block for older clients. Classic mode now also returns the
  previously-dropped `compare_result / rank_result / recommend_result /
  explain_result / choose_bike_result` payloads + `intent_type`.
* `POST /api/jobs/chat` — same body, 202 + job_id; poll `GET /api/jobs/{id}`
  (live stage text: "Simulating…", "Optimizing stage_4…"), cancellable.
  Use this from UIs — agent turns can take minutes on the 0.5-CPU prod tier.
* `POST /api/jobs/outlaw` — direct access to the composed pipeline
  (`{bike_id, budget_inr?: null=no limit, venue_id?, max_candidates?}`).
* `POST /api/optimize/build` — `budget_inr` is now optional; `null`/`0` =
  no limit (resolved server-side to ₹5M).

## Provider support

All five providers in `motoquant/llm/client.py` support the agent loop
(`LLMClient.call_tools`, `tool_choice` auto): Groq (default,
llama-3.3-70b-versatile), Gemini, Anthropic (native SDK), DeepSeek,
OpenRouter — selected via `LLM_PROVIDER` + per-provider key/model env vars.
Adding another OpenAI-compatible API = one entry in `_PROVIDERS`.

**Groq free-tier note:** an agent turn makes 2–8 LLM calls (vs 2 before). At
30 RPM the 20/min/IP chat limit can exhaust the provider quota under load —
if that bites, set `LLM_PROVIDER=gemini` or add a paid key.

## Testing

Everything is testable offline through the `_call_override("tools", …)` seam:
`tests/test_agent.py` (loop, budgets, metering, estimation, history, API
routes, format conversion) and `tests/test_outlaw.py` (pipeline structure,
physics sanity, unlimited-budget semantics).

`tests/test_chat_gating.py` pins the tier gate and the metering coverage
through the real HTTP routes, in **both** billing modes — the inert-during-beta
half matters as much as the enforcing half, since that is what ships today.
