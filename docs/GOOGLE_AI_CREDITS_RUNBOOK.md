# Google AI Studio / $300 Credit Runbook — Cowork Handoff

> **Audience:** a Cowork (desktop) session with the Chrome extension + the
> operator. Everything account-side happens in the operator's logged-in Chrome
> window; everything repo-side is either already done (PR from
> `claude/google-ai-studio-motoquant-wt2vv7`) or explicitly queued at the
> bottom for a Claude Code session. **Cowork: do NOT hand-edit Python via the
> FUSE mount** (documented truncation trap — CLAUDE.md "SESSION HYGIENE").
>
> **Prepared:** July 19, 2026, by a Claude Code remote session. Facts below
> were verified against live web sources on that date via a multi-agent
> research + adversarial-verification pass (the sandbox could not fetch
> ai.google.dev directly — egress-blocked — so figures were cross-checked via
> search-indexed copies of Google's own pages plus a direct fetch of
> cloud.google.com/vertex-ai/generative-ai/pricing). **Cowork has a real
> browser: re-confirm the load-bearing numbers on the live pages as you go.**

---

## Cowork session setup (model + effort + kickoff)

- **Model: Opus 4.8** (or Fable 5 if it's in the picker). This run mixes
  browser operation with real-money billing decisions and a route fork that
  hinges on correctly reading Google's live billing pages — worth a strong
  model. **Sonnet 5 is acceptable** if usage limits are tight (the runbook
  pre-decides everything hard); do **not** use Haiku for the billing steps.
- **Reasoning effort: medium.** The thinking is already done in this doc —
  the session executes and verifies. Bump to high only if the account turns
  out to be an edge case (Prepay forced, credit not drawing down, express-mode
  ambiguity in Route B).
- **Don't re-research pricing/policy** — §1 was multi-agent verified on
  2026-07-19; only re-confirm numbers by *reading the live pages already
  linked*, in the browser, at the moment of use.
- **Kickoff prompt (paste into the Cowork chat):**
  > Read docs/GOOGLE_AI_CREDITS_RUNBOOK.md in the MotoQuant repo and execute
  > it with me. Use the Chrome window (I'm logged into Google + Render).
  > Start with §2 Step 1 (identify the credit + pick Route A or B), create
  > the budget alerts before anything else, then walk the route's steps,
  > §5 env wiring, and the §7 verification checklist. Ask me before every
  > billing-state change (upgrade, prepay purchase, plan link). Do not edit
  > any repo code — code tasks are queued in §8 for a Claude Code session.

## 0. TL;DR

The "$300 free usage credits" is (almost certainly) the **Google Cloud Free
Trial welcome credit**: it lives in a Cloud Billing account, expires **90 days
after signup**, and never auto-charges (trial billing auto-closes; the card
check at signup is an authorization hold, not a charge).

**The catch that decides everything:** since **March 2, 2026**, welcome
credits granted to *new* accounts **cannot pay for Gemini API / AI Studio
usage**. They still pay for other Google Cloud products — including the *same
Gemini models served through Vertex AI*. Credits granted *before* that date
are grandfathered and DO work with an AI Studio Gemini API key until expiry.
Source: https://ai.google.dev/gemini-api/docs/billing (verified 2026-07-19).

So the flow is: **Step 1 — find out which side of March 2, 2026 the credit
falls on. Then follow Route A (grandfathered) or Route B (new account).**

Regardless of route, going paid on Gemini is worth doing for MotoQuant even at
$0 spent, because of two things the free tier does not give:

1. **Data terms:** on the free tier Google uses prompts + responses to improve
   its products (incl. possible human review). On paid, it does not. MotoQuant
   `/api/chat` carries real user data — a SaaS should be on the paid terms.
   Source: https://ai.google.dev/gemini-api/docs/terms
2. **Rate limits:** free tier is ~10–15 RPM on Flash models; paid Tier 1 is
   ~150–300 RPM. The chat agent burns 2–8 LLM calls per user turn, so free-tier
   RPM is a real ceiling under any traffic.

---

## 1. Verified facts (as of July 19, 2026)

Confidence: items marked ✅ were confirmed by an adversarial verify pass
against Google's own pages; items marked ⚠️ had conflicting secondary sources
— check the live page in Chrome before relying on the exact number.

### Credit mechanics
- ✅ $300 welcome credit, 90-day validity, visible at **Cloud Console →
  Billing → Credits** (shows balance + expiry date). No auto-charge; billing
  starts only if you manually upgrade the billing account to paid.
- ✅ Accounts opened **after March 2, 2026**: credit is NOT spendable on
  Gemini API / AI Studio. It IS spendable on Vertex AI (same Gemini models).
- ✅ Accounts opened **before March 2, 2026**: credit works on the Gemini API
  until it expires.
- ✅ **Prepay wrinkle:** new AI Studio billing setups (policy effective
  ~Mar 23, 2026; announced Apr 15, 2026) may be *required* to prepay —
  minimum $10, max $5,000 balance, prepaid credits expire after 12 months,
  non-refundable except when switching to postpay. If forced onto Prepay,
  eligible (grandfathered) Cloud credits apply only after the first prepaid
  purchase. Source: https://blog.google/innovation-and-ai/technology/developers-tools/prepay-gemini-api/
- ✅ India billing: Google Cloud India Pvt Ltd, **18% GST** on top of
  USD-denominated prices; add the GSTIN in payments-profile tax settings for
  input-tax credit.

### Models + pricing (paid tier, per 1M tokens, standard interactive)
Verified directly on https://cloud.google.com/vertex-ai/generative-ai/pricing
(2026-07-19); Gemini API (AI Studio) rates align.

| Model | Input | Output | Notes |
|---|---|---|---|
| `gemini-3.1-pro-preview` | $2.00 (≤200K ctx) / $4.00 | $12.00 / $18.00 | Flagship reasoning. **No free tier** (3.x Pro went paid-only Apr 2026). `-customtools` variant exists for tool-heavy agents. |
| `gemini-3.5-flash` | $1.50 | $9.00 | GA workhorse (May 2026). Has a free tier. |
| `gemini-3-flash-preview` | $0.50 | $3.00 | Superseded by 3.5 Flash but still served; free tier. |
| `gemini-3.1-flash-lite` | $0.25 | $1.50 | GA, cheapest current-gen; "optimized for high-volume agentic tasks"; free tier (~15 RPM). **New repo default.** |
| `gemini-2.5-*` | — | — | **Deprecated 2026-06-17, shutdown Oct 2026; 404s reported from ~July 9.** Do not use. |

- ✅ Batch API = **50% off** (text models, embeddings, Nano-Banana image
  models; NOT Imagen/Veo/Lyria). ~24h turnaround, JSONL in/out.
- ⚠️ Context caching ≈ 10% of input price + storage ~$1.00/1M tok/hr on
  Flash-class, ~$4.50 on Pro-class. Thinking tokens bill as OUTPUT.
- ✅ OpenAI-compatible endpoint
  `https://generativelanguage.googleapis.com/v1beta/openai/` supports tool
  calling + structured output on Gemini 3.x — which is exactly how
  `motoquant/llm/client.py` already talks to Gemini (no code change to switch
  models; it's all env vars).
- ⚠️ Free-tier limits are per-project and shift silently; read them live in
  AI Studio's rate-limit view, not from blogs.

### Beyond-chat capabilities relevant to MotoQuant
- ✅ **Grounding with Google Search:** Gemini 3 models get **5,000 free search
  queries/month**, then $14/1,000 queries (one request can issue several
  queries). Responses carry `groundingMetadata` with per-span source URLs —
  exactly what the benchmark corpus needs for citations.
- ✅ **URL context tool:** model reads up to 20 public URLs/request (34 MB
  each); no per-call fee, pages bill as normal input tokens. Pairs with
  grounding: search finds the magazine test, url_context reads it in full.
- ✅ **Embeddings:** `gemini-embedding-001` $0.15/1M tokens ($0.075 batch);
  multimodal `gemini-embedding-2` (preview) $0.20/1M text. **File Search**
  (managed RAG): storage free, query-time embeddings free, pay only one-time
  indexing — MotoQuant's whole 541-bike/593-part/254-tire catalog indexes for
  **well under $1**.
- ✅ **Image gen ("Nano Banana" family):** Gemini 3 Pro Image ≈ $0.134/img
  (1–2K), Gemini 3.1 Flash Image ≈ $0.067, Gemini 2.5 Flash Image ≈ $0.039.
  Batch halves those. 541 bike-page hero/OG images ≈ **$18–36 total**.
- ✅ **Deep Research agents** (`deep-research-preview-04-2026`, `-max-`):
  Google's autonomous research agent as an API, via the async **Interactions
  API** (not generateContent), available on free AND paid tiers (free tier has
  a small quota). Billed at 3.1 Pro token rates ≈ **$1–3 per research task**
  + grounding queries. This is effectively MotoQuant's instrumented-quarter-
  mile-hunting session as an API call.
- ✅ **Code execution tool:** free Python sandbox, only tokens billed.
- Veo 3.1 video: $0.40/s standard, $0.15/s fast (⚠️ per-second rates read via
  search index only). An 8s clip ≈ $1.20–3.20. Marketing-only, no batch.

### What $300 actually buys (at ~3K in + 500 out tokens per LLM call)
- `gemini-3.1-flash-lite`: ~**200,000 calls** (~25K–100K chat-agent user turns)
- `gemini-3.5-flash`: ~33,000 calls
- `gemini-3.1-pro-preview`: ~25,000 calls nominal; realistically 8–20K once
  thinking tokens count
- Honest framing: at current beta traffic MotoQuant cannot organically spend
  $300 in 90 days on chat alone. The credit's real value = (a) paid-tier data
  terms + rate limits at $0 if grandfathered, (b) one-off bulk jobs (Deep
  Research corpus sweep, embeddings index, imagery) we'd otherwise skip.

---

## 2. STEP 1 — Chrome: identify the credit + pick the route

1. Open **https://console.cloud.google.com/billing** → select the billing
   account → **Credits** (left nav). Record: credit name, **remaining
   balance**, **grant date**, **expiry date**. Screenshot it.
2. Determine the account-open / credit-grant date vs **March 2, 2026**:
   - Granted **before** → **Route A** (credit pays for the Gemini API).
   - Granted **on/after** → **Route B** (credit only pays via Vertex AI).
3. While there: **Billing → Budgets & alerts → Create budget** on this billing
   account: amount $300, threshold alerts at 25% / 50% / 90% / 100%, email to
   dhisetu@gmail.com. Do this in BOTH routes before anything else — once the
   billing account is upgraded to paid, spend past the credit is real money.
4. Also check **https://aistudio.google.com** → API keys page: note which
   Google Cloud project the existing `GEMINI_API_KEY` (in local `tokens.md`)
   belongs to, and what the "Billing Tier" column says (should currently read
   free tier).

## 3. Route A — credit is grandfathered (pre-Mar-2 account)

1. In AI Studio (API keys / usage & billing page) click **"Set up billing"**
   on the key's project → link the billing account holding the $300. Tier 1
   activates immediately. If the UI forces the **Prepay** plan, buy the $10
   minimum (real money) — grandfathered Cloud credits then apply to usage.
2. Confirm on the AI Studio rate-limits view that the project now shows
   Tier 1 limits, and that Cloud Console → Billing → Reports attributes
   subsequent Gemini API spend against the credit (run a couple of playground
   calls, wait a few hours, check the report shows $0.0x offset by credit).
   **If usage bypasses the credit and hits the card, STOP — the account is
   not actually grandfathered; fall back to Route B.**
3. Proceed to §5 (wire it into MotoQuant).

## 4. Route B — new account (credit is Vertex-only)

The $300 cannot fund the AI Studio key. Two-track approach:

**Track 1 — chat stays on the AI Studio key (env-only, costs ~$0):**
- Keep the free tier for now (data-terms caveat noted), or optionally go paid
  via Prepay $10–25 of real money — that alone funds months of beta chat at
  flash-lite rates AND flips the data terms to no-training. Operator's call;
  it is cheap either way.

**Track 2 — burn the $300 on Vertex AI (same Gemini models):**
- In Chrome, open **https://console.cloud.google.com/vertex-ai** on the same
  project, enable the Vertex AI API.
- Check whether **Vertex AI express mode / API-key auth** is offered for this
  account (Google has been expanding API-key access to Vertex; the console
  and https://cloud.google.com/vertex-ai/generative-ai/docs will say). If an
  API key works against Vertex's OpenAI-compatible chat-completions endpoint,
  a Claude Code session can add a `vertex` provider entry to
  `motoquant/llm/client.py` in ~20 lines (queued below).
- If only service-account (OAuth) auth is available: that's still fine for
  **offline/bulk jobs** (Deep-Research-style corpus hunting, batch
  enrichment, embeddings, Imagen) run from scripts with `gcloud` auth — it
  just shouldn't gate the prod chat path. Queue the code task; don't force it.
- Vertex, being a Cloud service, also does not train on customer data — so
  Track 2 work gets the good data terms automatically.

## 5. Wire it into MotoQuant (env-only — no deploy of new code needed)

The repo already speaks Gemini through the OpenAI-compat endpoint. The PR from
this session updates the stale default model (`gemini-2.5-flash` →
`gemini-3.1-flash-lite`); setting `GEMINI_MODEL` in the environment overrides
the default either way, so these env steps work before or after that PR lands.

**Render dashboard** (https://dashboard.render.com → `motoquant-api` →
Environment) — set/confirm:

| Env var | Value | Why |
|---|---|---|
| `GEMINI_API_KEY` | the (now paid-tier, Route A) AI Studio key | provider credential |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` (start here; try `gemini-3.5-flash` if chat quality feels thin) | pins a current model; the old default `gemini-2.5-flash` is deprecated/dying |
| `LLM_PROVIDER` | `gemini` to make Gemini primary, or leave as `groq` to keep Gemini as the manual fallback | operator's call — see the check below first |

⚠️ **Check the CURRENT value of `LLM_PROVIDER` + `GEMINI_MODEL` on Render
first.** STATUS.md and the ops playbook say prod `/api/chat` runs "Gemini
Flash 2.5", while `client.py`'s default provider is Groq — the dashboard is
the truth. **If prod is already `LLM_PROVIDER=gemini` with no `GEMINI_MODEL`
set (or set to a 2.5 model), prod chat is running on a deprecated model that
has started 404ing for others — fix `GEMINI_MODEL` immediately regardless of
everything else in this doc.**

Any env change on Render triggers a service restart (in-flight jobs registry
is wiped — pick a quiet moment).

**Key storage:** Render dashboard env var (prod) + local `tokens.md` (already
gitignored). Never in git, never in this doc.

## 6. Spending menu (ranked; prices from §1)

1. **Prod chat on paid Gemini** — env-only (§5). Fixes data terms + the RPM
   ceiling (Groq free = 30 RPM; agent turns = 2–8 calls each). Cost:
   single-digit dollars per month at beta traffic.
2. **Deep Research pilot on the benchmark queue** — run 2–3 tasks first in
   the AI Studio UI (free) before any API wiring: "Find instrumented
   quarter-mile tests (Racelogic/VBOX/Dragy/magazine dragstrip) for <bike>;
   report figure, source, instrumentation type, URL." Targets from the
   next-session queue: the 11 honestly-not-found bikes, the Apache RTR 200
   18.1-vs-18.3 primary-source verify, the ~9 suspect mph-vs-kmh trap rows.
   Full queue via API ≈ $25–35. This is the highest-leverage novel use — it
   automates what currently costs whole agent sessions.
3. **Grounded search + URL context** for research sessions — 5,000 free
   queries/month likely covers the entire corpus pipeline ($0). Production
   wiring into `llm/webtools.py` is a queued code task; until then it's
   available in AI Studio / ad-hoc scripts.
4. **Embed the catalog via File Search** — <$1 one-time; enables "which
   slip-on fits my 2019 Street Triple RS" semantic lookup for the chat agent
   and site search. Queued code task.
5. **Nano Banana hero/OG imagery experiment** — generate 10–20 samples for
   operator review before committing to the 541-page run (~$18–36 batched).
   Brand-consistency is the risk; the current scripted OG generator stays the
   default until samples beat it.
6. **Veo hero clip** — 1–2 experiments max ($1.20–3.20 per 8s clip); nice for
   the landing page, not a pipeline.

Do NOT manufacture spend to "use up" the credit — unspent credit costs
nothing; bad data or off-brand imagery does.

## 7. Verification checklist (Cowork, after §5)

- [ ] Credits page screenshot recorded (balance, expiry date) + budget alerts
      created (§2).
- [ ] AI Studio shows the project at Tier 1 (Route A) / express-mode status
      recorded (Route B).
- [ ] Render env updated; service restarted clean (`/api/health` 200,
      `bike_count` 541).
- [ ] Prod chat smoke on https://motoquant.in — ask "quarter mile for a stock
      Hayabusa at Aamby Valley?" → tool-driven answer with sim numbers, no
      `rate_limited`/provider error. Check Render logs show the expected
      provider/model string.
- [ ] Billing report (next day): Gemini API usage drawing down the credit
      (Route A) — NOT the card. If the card is charged, revisit §3.2.
- [ ] Note the credit **expiry date** in DISPATCH_INBOX for the operator +
      future sessions (bulk jobs must run before it).

## 8. Queued code tasks (for a Claude Code session — NOT Cowork/FUSE)

1. **`vertex` provider entry** in `motoquant/llm/client.py` (Route B only,
   if express-mode/API-key auth confirmed) — one `_PROVIDERS` entry pointing
   at Vertex's OpenAI-compat endpoint.
2. **Gemini-grounded `web_search` provider** in `motoquant/llm/webtools.py`
   (`SEARCH_PROVIDER=gemini`) using Google Search grounding +
   `groundingMetadata` URLs, alongside brave/serper/DDG.
3. **Deep Research corpus harness** — script the §6.2 queue through the
   Interactions API, emitting candidate benchmark rows with citations into
   `reports/` for the normal verify-then-adjudicate pipeline (LLM output is
   NEVER committed to the corpus without the existing source-verification
   rules).
4. **File Search catalog index + chat-agent retrieval tool** (§6.4).
5. **Batch-API enrichment harness** for future 541-bike classification/
   enrichment passes at 50% rates.

Each is small, independent, and none blocks the env-only win in §5.
