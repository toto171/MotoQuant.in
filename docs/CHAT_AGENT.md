# MotoQuant chat agent

`/api/chat` is a multi-step tool-calling agent (`motoquant/llm/agent.py`)
that runs on Anthropic's Claude. The classic pipeline is still available
(`mode: "classic"`) for the CLI and older clients.

## Two assistants

The chat panel has an Assistant dropdown. The browser sends only the id, and
the server maps it to a model, so a client can never pick an arbitrary model.

| Dropdown | `assistant` | Model | Effort | Daily cost |
|---|---|---|---|---|
| 1. The doctor | `doctor` | Claude Opus 5.5 (`claude-opus-5-5`) | medium | 2 units |
| 2. The mechanic | `mechanic` | Claude Sonnet 5.5 (`claude-sonnet-5-5`) | medium | 1 unit |

The mechanic is the default. The browser keeps the choice in local storage
(`mq.assistant.v1`).

## Who pays: the server key and visitor keys

* The server key comes only from the `ANTHROPIC_API_KEY` environment
  variable (on the public instance, the Render dashboard). It is never in a
  file. With neither a server key nor a visitor key, chat answers
  `assistant_unavailable`.
* A visitor's own key is optional. In the chat panel, "Use your own key"
  takes an Anthropic API key and keeps it in the browser: in session storage
  by default, or in local storage (`mq.anthropic-key.v1`) when "Remember on
  this device" is ticked. It is sent as the `X-Anthropic-Key` request header
  on the request that starts a chat (`POST /api/jobs/chat`, or the
  `POST /api/chat` fallback), never on job polls, never in the body or a
  query string.
* The server accepts only values that look like an Anthropic key (prefix
  `sk-ant-`, 20 to 300 characters, no whitespace); anything else gets
  `invalid_key_format`. A valid visitor key is used for that one request
  through its own client: there is no fallback to the server key, and the key
  is never stored, logged, put in a job result or error, or returned. Error
  text is scrubbed of `sk-ant-` strings, and the Sentry scrubber drops the
  `X-Anthropic-Key`, `Authorization` and `X-Api-Key` headers.
* `GET /api/assistant` tells the browser whether the free assistant is on:
  `{free_available, assistants: [{id, label, model}], default, daily_free_limit}`.
  When `free_available` is false, the panel opens the key form with a short
  explanation.

## What it can do

* Hold a conversation. The client sends earlier turns in
  `messages: [{role, content}]`, so follow-ups ("what about at Aamby?", "now
  add a full exhaust") keep their context. The server stays stateless.
* Answer complex questions. The model combines 15 tools across the whole
  product as it needs them: catalog search, full RK4 sims, top-speed runs, A/B
  compares, fitment-filtered parts and tires, venue and weather resolution,
  the real build-optimizer knapsack, gearing and launch autotune, and live
  catalog stats.
* Plan Stage 1–4 builds. The industry-standard drag-build tiers are built in
  (`BUILD_TIERS` in agent.py is the single glossary):
  * stage_1: bolt-ons (exhaust/filter/ECU), ₹60k default
  * stage_2: adds drivetrain (clutch/QS/sprockets/chain/battery), ₹200k
  * stage_3: adds nitrous/fuel/suspension, ₹500k. Engine internals are not
    in the parts catalog, so stage 3 is an approximation.
  * stage_4, also called outlaw or open class: full drag prep with no budget
    limit.
* Run outlaw builds through a composed pipeline
  (`motoquant/analysis/outlaw.py`, also exposed as `POST /api/jobs/outlaw`):
  drag_prep rubber → full_race parts knapsack (budget resolved to the ₹5M
  internal ceiling, never `inf`, because the knapsack DP would overflow) →
  gearing and launch-RPM autotune on the modified bike → combined
  verification sim.
* Look things up on the web (`motoquant/llm/webtools.py`) when the model
  needs facts it does not know. Providers: `SEARCH_PROVIDER=brave|serper` plus
  `SEARCH_API_KEY` in the environment (Render dashboard), or else a free
  DuckDuckGo HTML fallback. Fetches are SSRF-guarded and size-capped, and a
  failure comes back to the model as an error in the data.
  `MOTOQUANT_WEB_TOOLS=0` turns lookup off.
* Simulate bikes that are not in the catalog (`motoquant/llm/estimator.py`).
  The model gathers real specs, from its own knowledge or the web, then calls
  `simulate_estimated_bike`: spec dict → `validate_spec` (physical bounds and
  unit auto-correction; nonsense is rejected outright) →
  `spec_to_bike_config` (no DB) → full sim and top speed. Results are always
  labelled ESTIMATED, with a confidence score and the assumptions made
  (gearing tier, synthetic torque curve, category aero). Nothing is stored
  for a missing bike (`log_suggestion=False`); riders suggest bikes through
  the GitHub form.

## Guardrails

* The system prompt forbids invented numbers: every ET, trap or speed figure
  must come from a tool result. Estimated sims are always labelled.
* The executor, not the model, enforces hard per-message budgets: 8 LLM
  iterations, 20 full sims, 2 heavy ops (optimizer, autotune, outlaw).
* Every tool is free. `optimize_build` and `autotune_setup` (including the
  stage_4 / outlaw pipeline) are open to every caller, signed in or not,
  exactly like `POST /api/optimize/build`, `POST /api/autotune/ecu` and
  `POST /api/jobs/outlaw`. There are no tiers, quotas or upgrade paths
  (ADR-0006). The per-turn budgets above are the CPU fuse.
* Heavy tools share the direct routes' rate bucket. Each `optimize_build` or
  `autotune_setup` call consults a per-IP gate (`heavy_gate_for` in
  `motoquant/ratelimit.py`) that counts against the same bucket as
  `POST /api/optimize/build` (6 per minute per IP), so asking the chat agent
  for the heavy tools cannot out-run calling the routes directly. A refused
  call comes back as a plain tool-result message, which the model relays in
  its own words; the request does not fail.
* `sims_run` on the response is a report, not a charge. Sim tools count 1
  each (`compare_bikes` 2, `simulate_estimated_bike` 2, `rank_bikes` its
  planned batch). Heavy ops add a nominal 18 (`HEAVY_OP_SIM_COST`, from
  autotune's own sweep total: 1 baseline + 9 gearing + 7 launch + 1
  combined), and the composed outlaw pipeline adds 36.
* Per-IP fuses apply to everyone: 20 chat requests per minute per IP.
  `mode: "classic"`, which can run up to 25 sims per request outside the
  agent's budgets, has a tighter bucket of 4 per minute. The limit protects
  the CPU, because tools run simulations. The heavy-op gate above also
  applies to everyone.
* The daily cap counts only requests the server's key answers.
  `MOTOQUANT_CHAT_DAILY_LIMIT` is 200 units per IP per rolling 24 h by
  default, and `0` turns it off. A mechanic question costs 1 unit and a
  doctor question 2. Requests with a visitor key skip the daily cap.
  `/api/chat` and `/api/jobs/chat` share both buckets, and tripping either
  answers HTTP 429 with `Retry-After`. When the daily cap is hit, the panel
  offers the visitor's own key.

## API

* `POST /api/chat`: body `{query, messages?, mode?, assistant?}`
  (`assistant` is `"mechanic"` or `"doctor"`, default `"mechanic"`), optional
  header `X-Anthropic-Key`. Returns `ChatResponse` with `summary` (the reply),
  `assistant` (who answered), `own_key` (true when the visitor's key was
  used), ordered `blocks` (`[{type, payload}]`:
  `sim_result | top_speed | compare_result | build_result | rank_result |
  outlaw_result | autotune_result | estimated_sim | parts | tires |
  web_citations | bike_details | venues`), `tool_trace` and `sims_run`.
  `sim_result` mirrors the last sim block for older clients. Classic mode
  also returns `intent_type` and the `compare_result / rank_result /
  recommend_result / explain_result / choose_bike_result` payloads it used
  to drop.
* Errors come back as HTTP 200 with `error` set:

  | `error` | Meaning | What the panel says |
  |---|---|---|
  | `assistant_unavailable` | No server key and no visitor key | Add your own key |
  | `free_assistant_resting` | The server key hit its credit or spend limit | Add your own key, or try later |
  | `key_rejected` | Anthropic refused the visitor's key (401/403) | Check or change the key |
  | `invalid_key_format` | The header does not look like an Anthropic key | Keys start with `sk-ant-` |
  | `rate_limited` | Anthropic answered 429 | Try again in a minute |
  | `refused` | The model declined to answer | Ask about a bike, part or run |
  | `agent_failed` | Anything else; `error_detail` never contains a key | Try again |

* `GET /api/assistant`: whether the free assistant is on, the two
  assistants and the daily limit (see above).
* `POST /api/jobs/chat`: same body and header; returns 202 and a job_id. Poll
  `GET /api/jobs/{id}` for live stage text ("Simulating…", "Optimizing
  stage_4…"). The job can be cancelled. Use this route from UIs, because an
  agent turn can take minutes on the 0.5-CPU production tier.
* `POST /api/jobs/outlaw`: direct access to the composed pipeline
  (`{bike_id, budget_inr?: null=no limit, max_candidates?}` plus the optional
  conditions every simulation route takes: `venue_id`, `location`, `lat`/`lon`,
  `altitude_m`, temperatures, humidity, pressure). The result echoes the
  conditions used in `environment`.
* `POST /api/optimize/build`: `budget_inr` is optional; `null` or `0` means
  no limit (resolved server-side to ₹5M).

## Provider

Claude is the only provider. Set `ANTHROPIC_API_KEY` on the server; there is
no provider switch and no other provider's key to set. An agent turn makes
several Claude calls, so size `MOTOQUANT_CHAT_DAILY_LIMIT` to your monthly
Anthropic budget, or set a spend limit in the Anthropic Console. When that
limit is reached, the panel shows `free_assistant_resting` and visitors can
carry on with their own key.

## Build planner

Give the chat a budget and a goal in plain words ("1.5 lakh", "₹80k", "under
50 thousand"; "quickest ET", "max speed") and it calls `optimize_build`. It
then explains each pick in one line (what it does, the time saved and the
rupees per tenth), followed by the total and what the next rupee should buy.
The panel's build card shows the parts, the warnings ("Things to check") and
the next upgrade ("If you have more to spend"). `rank_bikes` results show as
a "Quickest bikes" table.

## Testing

Everything can be tested offline through the `_call_override("tools", …)`
seam: `tests/test_agent.py` (loop, budgets, estimation, history, API routes,
format conversion) and `tests/test_outlaw.py` (pipeline structure, physics
sanity, unlimited-budget semantics).

`tests/test_open_source_pivot.py` pins, through the real HTTP routes, that no
paywall exists (`TestMonetizationIsGone`) and that the daily chat cap trips,
is per-IP, is shared by both chat routes and can be disabled
(`TestChatDailyCap`). `tests/test_chat_fuses.py` pins the heavy-tool gate,
the per-message budgets and the chat route rate limits, also through the real
routes. The old `tests/test_chat_gating.py` (tier gate and metering in both
billing modes) was deleted along with monetization.
