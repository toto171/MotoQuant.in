# MotoQuant Domain LLM — Build & Continuous-Upgrade Plan (Engineering Hand-off)

**Date:** 2026-07-04
**Audience:** the solo/contract ML engineer who will execute this, and the founder who approves each gate.
**Status:** plan of record. **Read §0 and §1 before you touch a GPU.**

> **What this document is.** The founder wants a "MotoQuant AI LLM" built on top of an open-source model and kept current as the AI space moves. This is the exact, phased way to do that *without* wasting months — grounded in the code that already exists (`motoquant/llm/agent.py`, the 5-provider `LLMClient`, the 16-tool agent, the deterministic physics engine). It is written to be handed to one engineer and executed gate by gate.

---

## 0. Read this first — the one paragraph that governs everything

The obvious plan — "rent a GPU and fine-tune a model" — is the trap. If you start there you will spend 6–10 weeks building a training/serving/MLOps platform to solve a **$0/month cost problem** and a **30-RPM rate-limit problem that a one-line env change already fixes**, while there is **near-zero real chat traffic to learn from**. The two durable assets are the **evaluation harness** and the **captured dataset**. The model weights are a disposable casting you re-mint from those assets whenever a better open base ships. **Build the assets first; build the model last, behind a measured trigger; ship something useful at every phase.** Do not start at "fine-tune the model."

---

## 1. Executive recommendation

**Thesis.** MotoQuant's moat is the deterministic physics engine (`MotoQuantEngine.run()`), the validated-benchmark corpus (±0.006s headline), and the 535-bike catalog. The LLM is a **commodity router + narrator** sitting in front of that moat. Its only jobs are: (1) pick the right one of ~16 tools, (2) emit valid JSON arguments, (3) faithfully narrate whatever the tool returned — **never invent a number.** All three are cheap to teach by imitation and cheap to *check*, because the engine is a deterministic oracle you can re-run to verify any numeric claim. **That oracle is the rarest asset in this plan and it should be the spine of everything you build.**

**Durable vs. disposable.** The **dataset** (synthetic-from-engine + curated production traces) and the **eval harness** (oracle-checked regression suite) are permanent, compounding assets that improve the *hosted* product today and make any future fine-tune portable across base models. The **model weights** are disposable — re-minted on each new open base by a config edit and a GPU-hour. You protect the mold, not the casting. This is literally what "keep upgrading as the AI space moves ahead" means in practice: you don't chase models, you keep a dataset + eval that lets you re-cast onto whatever is best this quarter in an afternoon.

**The on-ramp is distillation from your own strong hosted agent — but only after real traffic exists.** Your production agent, running against the deterministic engine, is a label factory: log real `user → tool_calls → tool_results → faithful_summary` trajectories, filter them by re-running the oracle, and train a small open model to imitate them. Until traffic exists there is nothing to distill; **synthetic-from-engine data carries v1** (perfect labels, free, uncopyable).

**Do not self-host a GPU, and do not fine-tune, until data + traffic justify it.** At launch volume the fine-tune is a *future* cost optimization contingent on volume you do not have. A managed fine-tune *adds* ~$20–30/mo; a reliable dedicated GPU adds $500–1,600/mo. Break-even vs. cheap hosted models is ~2.5B tokens/mo (~5k chats/day sustained) — years away, if ever. The one legitimate reason to *own* an open fine-tune is **offline desktop**, and that **contradicts your current hosted-only IP-protection decision** — treat it as an explicit founder decision, not an engineering default.

> **One-line verdict a founder can act on:** *Build the physics-oracle eval harness and consent-gated trace capture now (they improve the live product regardless); keep the 5-provider hosted setup as the production brain; fine-tune the narrowest slice on a small open model only after a measured trigger fires — and keep a frontier model as the live fallback forever.*

---

## 2. What fine-tuning genuinely buys you — and what it does not

| Fine-tuning a small open model **buys** | Fine-tuning **does NOT buy** |
|---|---|
| **Lower $/token at high, steady volume** — a fine-tuned 4–8B (served per-token ~$0.18–0.20/1M or self-hosted) beats a frontier model *only when token volume is large and sustained*. | **Better physics or better numbers.** ETs come from the engine. A model that "knows" ETs is *worse* — it hallucinates instead of calling the sim. Never fine-tune the answer, only the routing/narration. |
| **Format / tool-call reliability on a *small* model** — reliably emit valid tool JSON, use your glossary, pick the right one of 16 tools. | **A moat.** Anyone can fine-tune Qwen on bike chat. The weights are not defensible; the engine + benchmark corpus + catalog are. |
| **A latency/throughput floor you control** — no shared 30-RPM ceiling. | **Reasoning / planning.** Small fine-tunes are *worse* at novel multi-step tool orchestration than frontier models. Your 8-iteration outlaw pipeline can degrade. |
| **Independence / IP** from a provider's price hikes, deprecations, ToS. | **Lower maintenance.** It *adds* ops: GPU hosting, retrain cadence, drift monitoring, eval gates — a second thing that breaks at 2am for a one-person team. |
| **On-device / privacy** — a model that runs in the desktop app or inside a B2B customer boundary (both currently hypothetical). | **A fix for the 30-RPM pinch.** That is a *provider-tier* problem: `LLM_PROVIDER=gemini`, a paid Groq tier, or round-robin across the 5 providers already wired. Not a fine-tune problem. |

**The one-sentence version:** for a tool-calling agent in front of a deterministic engine, the realistic upside is **cost + latency + small-model format-reliability — not capability, not correctness, not defensibility.**

### The gating brand risk (bold, at the top of every review)

A frontier model's most valuable property for MotoQuant is *knowing when NOT to answer from memory* — it reliably calls the sim instead of guessing. **A fine-tuned 4–8B is materially worse at exactly this.** When a tool call fails, times out (Render cold starts), or the model skips it, a 4B pattern-completes a plausible-but-wrong ET far more often than Claude/Gemini. You would introduce that failure mode to save ~$0 today / ~$30/mo at launch. One viral screenshot of MotoQuant confidently quoting a hallucinated 9.8s Hayabusa does more brand damage than a year of fine-tune savings. **The fine-tune ships only if it matches frontier faithfulness at *literally zero* hallucinated numbers on the golden set — not "within noise" — and the frontier model stays a live fallback for the hot path indefinitely.**

---

## 3. Target architecture (drop-in)

The whole point of the existing design is that a fine-tune is **one `_PROVIDERS` entry + env vars, zero code changes.** Preserve that.

```
                        ┌─────────────────────────────────────────────┐
   POST /api/chat  ───► │  _chat_impl → run_agent_chat (agent.py)      │
   POST /api/jobs/chat  │  16 tools · budgets 8 iter / 20 sim / 2 heavy│
                        └───────────────┬─────────────────────────────┘
                                        │ LLMClient.call_tools(system, messages, tools)
                                        │ neutral message format (provider-agnostic)
                        ┌───────────────▼─────────────────────────────┐
                        │  LLMClient._PROVIDERS  (env: LLM_PROVIDER)   │
                        ├──────────────────────────────────────────────┤
                        │  groq*  gemini  anthropic  deepseek  openrouter│ ← keep as production brain
                        │  ★ selfhost / motoquant-ft  (NEW, OpenAI-compat)│ ← fine-tune drops in here
                        └───────────────┬──────────────────────────────┘
                     OpenAI SDK path ◄──┴──► Anthropic SDK path
                                        │
                    ┌───────────────────┼────────────────────────────┐
                    │ CLOUD serve        │ DESKTOP serve (if approved)│
                    │ base + LoRA adapter│ merged GGUF Q4_K_M          │
                    │ vLLM / SGLang      │ llama.cpp llama-server      │
                    │ or Together/Fire-  │ localhost:8080/v1           │
                    │ works multi-LoRA   │                             │
                    └────────────────────┴────────────────────────────┘
```

**The drop-in contract — the fine-tuned endpoint MUST satisfy all of these** (verified against `motoquant/llm/client.py`):

1. Reachable via `openai.OpenAI(base_url=<url>/v1)` at `POST /chat/completions` (the OpenAI-compat path already serves 4 of 5 providers, so this is genuinely one `_PROVIDERS` dict entry).
2. Accepts `model`, `max_tokens` (agent sends `AGENT_MAX_TOKENS=2048`), neutral-converted `messages` incl. `role:"tool"` with `tool_call_id`, `tools:[{"type":"function","function":{name,description,parameters}}]`, `tool_choice:"auto"`.
3. Emits **native** `choices[0].message.tool_calls[]` with `.id`, `.function.name`, `.function.arguments` as a **JSON string** that `json.loads` parses. Supports multiple tool calls per turn.
4. Accepts the assistant/tool round-trip (assistant `tool_calls` → `role:"tool"` keyed by `tool_call_id`).
5. Honors `tool_choice:"auto"` (may return plain text = final answer).
6. Surfaces `finish_reason` (metadata only).
7. 429s surface as an OpenAI `RateLimitError` → `LLMRateLimitError` → `"rate_limited"` UI error.
8. Obeys the discipline rules (only the `AGENT_TOOLS`, valid arg shapes, never invent physics numbers, `search_bikes` before simulating, `simulate_estimated_bike` for non-catalog bikes, respect budgets).

**Two non-negotiables the hand-off engineer must not break:**

- **The `_call_override` test seam.** `tests/test_agent.py` drives the entire agent loop offline through `_call_override("tools")`; it sits *above* the SDK layer, so a new provider preserves it automatically — but do not "optimize" it away.
- **Statelessness.** History is client-held via `ChatRequest.messages`. Do not add server-side session state to accommodate a fine-tune.

**Adapter, not merge, for cloud.** Serve base + LoRA adapter and select by `model` name; this lets you host `motoquant-chat` and (later) `motoquant-outlaw` / `motoquant-summarizer` adapters off one base and roll back by deleting an adapter. Merge only for the desktop GGUF.

---

## 4. Phase-gated roadmap

Every phase ships something useful even if the next never happens. Gates are hard; the founder approves each one.

### Phase 0 — Eval harness + oracle (NOW · ~1–2 weeks · zero-regret)
The only sanctioned model-related work until there is a live API **and** real chat traffic.

- **Build `eval/oracles/physics_oracle.py`** (~40 lines) wrapping `MotoQuantEngine` — re-runs the sim for a resolved `BikeConfig`, returns `time_quarter`, trap, splits. This is the crown jewel.
- **Author 30–50 golden cases** (grow to ~150 later, *not* 800 up front) from existing `tests/test_agent.py` scenarios + `scripts/validate_chat_corpus.py`. Store as `{msg, expected_tools, forbidden_tools, arg_assertions, oracle:{bike_id,venue_id,env,mods}}`. **Golden expected values reference the LIVE engine, never frozen numbers** (physics reseeds move ETs).
- **Write the deterministic metrics** as first-party pytest (see §7): faithfulness (Layer A tool-vs-engine, Layer B prose-vs-payload), tool-selection (required/forbidden sets), arg-correctness, budget discipline.
- **Score the CURRENT hosted agent.** Emit a per-dimension scorecard + $ cost + p50/p95 latency.
- **Exit criteria:** a reproducible number for how good today's hosted agent is, running in CI in minutes, with a **zero-hallucination gate live on day one.** Ship the scorecard to the founder. **Reassess before Phase 1.**

> Keep the harness in **first-party pytest + the oracle.** DeepEval / promptfoo / Braintrust are optional dashboards you can bolt on later and drop at will — do not hard-wire your eval ratchet to a third-party platform (promptfoo was acquired by OpenAI; you are a provider-independence company).

### Phase 1 — Consent-gated trace capture (AFTER live traffic · weeks · zero-regret)
- **Gate:** requires (a) live API returning healthy, (b) real chat traffic, (c) ToS/privacy updated with a model-improvement clause + opt-out, (d) PII scrub implemented. **No trace capture before the consent + scrub layer exists** — capturing bike/rider details, account IDs, and web-fetched copyrighted article bodies without consent is a legal landmine.
- **Hook the logger** where `_call_override("tools")` already lives; serialize the *actual* message array `LLMClient` produces (incl. the `TOOL_RESULT_MAX_CHARS` truncation + `json.dumps(default=str)` quirks) to a `chat_traces` table or append-only JSONL. Log model/provider version, budgets used, latency, terminal status, and any user signal (thumbs, Save-this-run, Stop-button).
- **Auto-triage with the oracle:** re-run Layer-B faithfulness on every captured trace; auto-flag any answer whose prose numbers don't reconcile with its tool results.
- **Exit criteria:** a growing, PII-scrubbed, oracle-flagged corpus that tells you where the *hosted* product is weak — valuable whether or not you ever fine-tune.

### Phase 2 — Optimize the cheap hosted path (weeks · zero-regret)
- Use the Phase-0 eval to find the **cheapest hosted model that PASSES** (Gemini 2.5 Flash-Lite / Llama-8B-class). Tighten the system prompt, tool schemas, few-shot exemplars.
- **Fix the 30-RPM pinch with fallback + paid tier + provider round-robin — not a GPU.** Wire `LLM_PROVIDER` failover so a 429 on Groq spills to Gemini.
- **Exit criteria (Gate 2):** lower cost + higher reliability for $0 of training. **This is very likely a stable end state.** Proceed only if a measured trigger fires (§9). **A tie or a hunch is a NO.**

### Phase 3 — Prove the fine-tune on the narrowest slice (1–2 week time-boxed spike · reversible)
- Only after a measured trigger. **Pick ONE bounded slice, not "the agent":**
  - **Summarizer** (recommended first) — highest hallucination-risk surface, cheapest to gate with the oracle. Input = tool payloads, output = faithful prose.
  - **or Router** — intent + tool + args; correctness is cheap to verify against gold trajectories.
- LoRA a **4B** open model on captured + synthetic traces (tens of $). Score on the *same* Phase-0 eval.
- **Exit criteria:** the slice **matches frontier faithfulness at zero hallucination** AND wins materially on cost or latency. **If it fails → kill it.** The eval + data remain permanent wins; no months lost.

### Phase 4 — Deploy scoped, with a live fallback (only after a trigger + a Phase-3 win)
- Serve the proven slice on **managed multi-LoRA per-token (Together/Fireworks)** first — no fixed GPU cost, no cold start.
- **Keep the frontier model as a live fallback** for hard/novel queries and for any oracle-flagged live faithfulness regression (router-to-two-models).
- Add the model to `_PROVIDERS`, canary via a `MODEL_ROUTING` weight (95/5), watch live oracle-faithfulness for 24–72h.
- **Dedicated GPU + SGLang only when steady volume clears ~2.5B tokens/mo (~5k chats/day).** Never scale-to-zero serverless GPU for interactive chat.
- **Exit criteria:** a served fine-tune that is cheaper/faster on its slice with zero brand regression and instant rollback.

### Phase 5 — Continuous-upgrade CI (only once a model exists to manage)
Registry + swap-the-base workflow + quarterly cadence (§9). **Capped, not perpetual** — re-run eval quarterly, change nothing unless it fails.

---

## 5. Data pipeline

Two corpora, versioned separately (DVC pointers in git; optional private HF mirror). **Strict wall:** golden eval inputs never enter training (CI checksum-membership test).

### 5A. Synthetic-from-engine (the bulk, perfect labels, uncopyable)
```
sample scenario → compute CORRECT tool call(s) → ACTUALLY run the engine/tool
   → real result JSON → render NL question → render faithful summary → emit example
```
Because you execute the real tool, `arguments` and results are correct and mutually consistent by construction — zero hallucinated labels.

- **Scenario sampler:** grid + random over 535 bikes × 20 venues × 594 parts × 257 tires × rider mass × conditions × build tiers (stage_1..stage_4/outlaw). Stratify so every bike, tool, venue, and glossary term appears ≥N times; bias toward popular bikes (Hayabusa, K5, R1, Duke 390, RC 390, Classic 350) to match traffic; keep tail coverage.
- **One generator per tool** (all 16) + **multi-tool compositions** mirroring the real `outlaw.py` order (`get_bike_details → search_parts/optimize_build → autotune_setup → run_simulation verify → summary`). Compositions are where small models fail and are easy to under-sample — over-weight them.
- **NL question rendering, two-stage:** (1) templates with heavy slot variation incl. misspellings/aliases ("busa","gsxr","r15v4"), unit systems, Hinglish code-switching, terse vs verbose; (2) an LLM paraphrase pass, with a regex entity re-extraction check that discards any paraphrase that dropped/altered a bike/venue/number.
- **Summary rendering, faithful by construction:** fill ET/trap/60ft/splits/prices from the *actual* JSON; optional single LLM style pass **re-validated against the JSON, reject on mismatch.**

> **CRITICAL data-design rule (the single most important sentence in the pipeline).** For every question template, generate **many examples with different tool results** — vary venue/temp/mods so the ET actually moves. If every "Hayabusa quarter mile" example carries `10.4712`, the model **memorizes 10.4712 and emits it even when the tool returns something else.** That is the hallucination failure mode baked in at training time. The number in the summary must be a **verbatim copy of the immediately-preceding tool payload**, and the training distribution must make the number a *function of the tool output*, not of the question.

> **Train/serve-skew rule.** Generate training tool-result payloads by capturing the **actual serialized messages `LLMClient` produces** (with the char truncation and `default=str` serialization), not hand-built clean approximations. Otherwise the model trains on inputs it never sees in production.

### 5B. Distillation from production traces (real distribution — Phase 1+ only)
- Capture the full message array exactly as the strong model saw/produced it. **Quality filter before promotion:** terminal status = completed & within budget; every `tool_call` valid JSON matching a real schema; **summary numbers reconcile with tool results** (the oracle filter — highest-value gate); prefer positive user signal; down-weight abandoned/re-asked conversations.
- **PII scrub + provenance + consent column** on every row (`source ∈ {hand, synthetic, production}`, `license`, `captured_at`, `curated_by`). Keep web-tool result payloads short/factual so the model learns the *pattern* (call → cite → summarize), not scraped prose.

### 5C. Hard / negative cases (15–25% of the set — the difference between a demo and a product)
Refusals (out-of-scope car/weather/poetry → branded decline; scoped `web_search` when it's a legit bike fact); unknown-bike → `simulate_estimated_bike` with ESTIMATED badge + 0.60-confidence caveat, *and* cases where estimation should fail → clarifying question not a fabricated sim; clarifying questions for underspecified asks; tool-error/cold-start recovery → honest "couldn't compute" not a hallucinated ET; budget-exhaustion explanation; **anti-hallucination pins** ("roughly what's the ¼-mile of a Panigale V4?" → must call the sim, labeled with a tool call not prose); multi-turn coreference ("compare it to the R1").

### Glossary coverage (first-class axis)
Require each term to appear as a user phrasing and a correctly-narrated concept, with **contrastive disambiguation pairs**: `60-foot, ET, trap, ⅛/1000ft/¼ splits, two-step, launch RPM, anti-squat, slipper, lockup clutch, quickshifter/air shifter, expansion chamber, knapsack/ROI, autotune, drag_prep, full_race, stage_1..4, outlaw/open class (=stage_4, no-limit budget) vs open-class (litre), DA, wheelie limit, final drive 16/45, lowering kit, Cd·A, kerb vs dry mass, nitrous/boost.`

### Sizes & versioning
| Milestone | Total | Mix | Note |
|---|---|---|---|
| **v1 (first useful)** | **2–4k** | ~70% synthetic + ~15% distilled (once it exists) + ~15% hard/negative | Trains in 1–3h on one H100. Don't chase bigger before traffic proves the distribution. |
| **v2 (strong)** | **12–30k** | ~55% synthetic (deep grid, rare bikes, long compositions) + ~25% distilled + ~20% hard/negative | Diminishing returns past ~30k for a LoRA of this scope; quality/coverage/dedup > raw count. |
| **Ongoing** | +500–2k/mo | new distilled + newly-failing evals | Kaizen for the model. |

**Rules:** balance the tail (every tool ≥ a few hundred; compositions hardest), dedup aggressively, hold out a real-traffic eval set the model never trains on. DVC-tag each batch (`dataset-vN`); pin the exact dataset version to every eval run. **Do not build the 12–30k v2 set before real traffic validates the distribution** — start at 2–4k.

---

## 6. Fine-tuning recipe

**Base models — mid-2026 landscape (all clean licenses; do NOT touch Llama's Community License — no capability edge for this task and it drags attribution + train-a-competitor strings).** Verified via BFCL-V4 / BenchLM tool-use leaderboards (June–July 2026).

| Target | Model | License | Why |
|---|---|---|---|
| **Cloud v1** | **`Qwen3-4B-Instruct-2507`** | Apache 2.0 | **Start at 4B.** Narrow task + engine-as-oracle means a well-tuned 4B very likely matches a 30B on *your* workload. Top open family on BFCL-V4; Unsloth first-class; whole size ladder in one family. |
| **Cloud v2 (only if 4B measurably plateaus)** | `Qwen3-8B` or `Qwen3-30B-A3B` (MoE, ~3B active) | Apache 2.0 | Size up **on evidence only.** The 30B-A3B serves at ~3B cost; reach for it only after a measured 8B failure on hard compositions. **Never rent H100s for 30B on a hunch.** |
| **Desktop (if approved)** | `Qwen3-4B-Instruct-2507` / `Qwen3-1.7B` → GGUF Q4_K_M | Apache 2.0 | Same family as cloud = one recipe, one template, one dataset across targets. ~2.5–3 GB; runs on an 8 GB laptop. |
| **Cross-family sanity check** | `Gemma 4 27B` / `Gemma 4 E4B` (Apache 2.0 as of Apr 2026) | Apache 2.0 | Confirm you're not overfitting to Qwen; genuine co-favorite. `GLM-5.2` (MIT) only if the agent grows into genuinely complex multi-step planning. |

**Pin the base by exact HF revision hash.** A silent base bump invalidates eval baselines the way a physics reseed invalidates ET baselines. **Do not commit to a base from this table blind — run the Phase-0 eval bake-off (Qwen3-4B vs 8B vs Gemma 4 E4B) on YOUR golden set and let the numbers pick.**

**Method: QLoRA** (4-bit base, LoRA adapter). Not full FT (overkill, catastrophic-forgetting risk, un-hot-swappable), not RAG-as-substitute (RAG feeds tools facts; fine-tuning teaches *when/how* to call — do both).

**Stack: Unsloth** (solo-engineer default — single GPU, ~2× faster, ~70% less VRAM, `train_on_responses_only`). **Axolotl** YAML when you want reproducible CI recipes / multi-GPU. Managed alternative for zero-infra distillation: **OpenPipe / Together / Fireworks fine-tuning**.

**Tool-calling chat-template format — train in the format you infer in.** Store provider-neutral OpenAI-style `{messages, tools}` JSONL; render with `tokenizer.apply_chat_template(messages, tools=tools)` at *both* train and inference. Do not hand-format special tokens.

```jsonc
{"tools":[{"type":"function","function":{"name":"run_simulation",
  "description":"Full RK4 quarter-mile sim ...","parameters":{"type":"object",
  "properties":{"bike_id":{"type":"integer"},"venue_id":{"type":"integer"},
  "power_boost_pct":{"type":"number"},"part_ids":{"type":"array","items":{"type":"integer"}}},
  "required":["bike_id"]}}}],
 "messages":[
  {"role":"system","content":"You are MotoQuant's race engineer. Use tools for every number; never invent an ET. Glossary: stage_4/outlaw = full_race + no-limit budget ..."},
  {"role":"user","content":"what's the busa run at aamby valley?"},
  {"role":"assistant","content":"","tool_calls":[{"id":"c1","type":"function","function":{"name":"search_bikes","arguments":"{\"query\":\"Hayabusa\"}"}}]},
  {"role":"tool","tool_call_id":"c1","content":"{\"best_match\":{\"bike_id\":12,\"name\":\"Suzuki Hayabusa Gen1\"}}"},
  {"role":"assistant","content":"","tool_calls":[{"id":"c2","type":"function","function":{"name":"run_simulation","arguments":"{\"bike_id\":12,\"venue_id\":1}"}}]},
  {"role":"tool","tool_call_id":"c2","content":"{\"et_quarter_s\":10.4712,\"trap_speed_kmh\":233.9,\"et_60ft_s\":1.71}"},
  {"role":"assistant","content":"Your Hayabusa runs **10.471 s** at Aamby Valley, trapping 233.9 km/h with a 1.71 s sixty-foot. Want an outlaw build?"}
 ]}
```

**Training config sketch (Unsloth QLoRA, Qwen3-4B — pin the revision hash in prod):**
```python
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

model, tok = FastLanguageModel.from_pretrained(
    "unsloth/Qwen3-4B-Instruct-2507",  # PIN the revision hash in prod
    max_seq_length=8192,  # 16 tool schemas + multi-turn are large
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0.0,  # r=32 for 8B / heavy compositions
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

ds = load_dataset("json", data_files="data/agent_sft.jsonl", split="train").map(
    lambda ex: {
        "text": tok.apply_chat_template(
            ex["messages"],
            tools=ex["tools"],
            tokenize=False,
            add_generation_prompt=False,
        )
    }
)
tr = SFTTrainer(
    model=model,
    tokenizer=tok,
    train_dataset=ds,
    args=SFTConfig(
        per_device_train_batch_size=8,
        gradient_accumulation_steps=2,
        num_train_epochs=2,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        optim="adamw_8bit",
        weight_decay=0.01,
        bf16=True,
        packing=False,  # OFF: preserve turn boundaries (packing drifts tool format)
        max_seq_length=8192,
        seed=42,
        output_dir="out/motoquant-agent-v1",
    ),
)
tr = train_on_responses_only(
    tr,  # loss on assistant turns only; mask system/user/tool
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)
tr.train()
model.save_pretrained("out/motoquant-agent-v1-lora")  # ~50–200 MB
```

**Serve command:**
```bash
vllm serve unsloth/Qwen3-4B-Instruct-2507 --enable-lora \
  --lora-modules motoquant-agent-v1=out/motoquant-agent-v1-lora \
  --max-lora-rank 32 --guided-decoding-backend outlines --port 8001
```
**Reliability belt-and-suspenders:** serve with **guided/grammar-constrained JSON decoding** (vLLM guided-JSON / llama.cpp GBNF) so a rare malformed emission is structurally impossible. Keep the client's existing `<function=...>` salvage + `__malformed_json__` fallback as the final net — harmless if never triggered.

---

## 7. Eval harness

The ratchet that makes upgrades safe. Score the **trajectory**, not just the final string. Keep it **first-party pytest + oracle**; third-party frameworks are optional dashboards.

**Five dimensions, priority order:**

| # | Dimension | Catches | Check |
|---|---|---|---|
| 1 | **Faithful summary** | Hallucinated ET/trap/hp/price; prose contradicting the payload | **Deterministic** (oracle) |
| 2 | **Tool selection** | Wrong tool; `web_search` on in-catalog bike; skips knapsack on budget ask | Deterministic (trajectory set) |
| 3 | **Argument correctness** | Wrong `bike_id`/venue; `budget_inr` null-vs-0; `build_tier=stage_4` for "outlaw" | Deterministic (schema+value) |
| 4 | **Refusal / scope** | Answers car questions; ignores `MOTOQUANT_WEB_TOOLS=0` | Hybrid (guard + judge) |
| 5 | **Multi-turn coherence** | Loses turn-1 bike; re-runs a heavy sim; self-contradicts | Hybrid |

**Faithfulness = two deterministic layers (the oracle in action):**
- **Layer A — tool vs engine:** re-invoke `MotoQuantEngine` with the same resolved config; assert `abs(tool.et_quarter_s − engine.time_quarter) < 1e-3`. Catches a model that emits a number without calling the tool.
- **Layer B — prose vs payload:** regex every number out of the answer (`\d+\.\d{2,3}\s*s`, `km/h`, `₹`, `hp`) and match each against a tool payload the model actually received. Any unsupported number → **hard fail.**

**Two real holes in Layer B — the engineer must handle both or it's useless:**
- **False positives on derived values:** the model legitimately converts km/h→mph (×0.621) and rounds ("about 10.5s"). Whitelist unit conversions + a rounding tolerance, or you train the model to never convert units.
- **False negatives on attribution:** right number, wrong bike; or a coincidental match to a different tool result. Layer B does not catch these — document the limit, don't oversell the oracle as total coverage; the LLM-judge residue + multi-turn consistency checks partially cover it.

**LLM-judge = last resort, advisory only.** Use it only for the subjective residue (unsupported causal claims, tone, ESTIMATED-bike over-specification). A judge failure blocks promotion **only** if a human has confirmed the failure class before. Never sits on the critical gate alone.

**Trajectory metrics** as set/order relations (many valid paths): required-tool recall, forbidden-tool rate, arg-value asserts (`build_tier=="stage_4"`, `budget_inr is None` for "no limit" — the DP-overflow bug), budget discipline (`sims<=20 and heavy<=2 and iters<=8`).

**Promotion gates — `eval/thresholds.yaml` (versioned in git):**
```yaml
faithful_summary:  {hallucinated_number_rate: 0.000, three_decimal_contract: 0.98}  # HARD: literally zero
tool_selection:    {required_tool_recall: 0.97, forbidden_tool_rate: 0.02}
arg_correctness:   0.98
refusal:           {out_of_scope_refuse: 0.98, in_scope_false_refuse: 0.03}          # over-refusal is a regression too
budget_discipline: 1.00
multiturn_consistency: 0.99
```
**Separation of concerns (important):** the engine baseline-pin tests (K5 10.0334 / R1 10.2859 / Hayabusa 10.4712 bit-identity) stay in the **physics** suite, **NOT** the model eval suite. Mixing them means an engine reseed fails a model gate and vice versa. The model eval references the *live* engine per case; it does not assert frozen ETs.

**Public leaderboards (BFCL/IFEval/MMLU) are a coarse go/no-go pre-filter ONLY, never an optimization target.** Use them once, to decide whether a raw base is worth fine-tuning. BFCL ≠ your 16 tools.

---

## 8. Serving + cost

**Workload reality (from your own architecture):** agentic chat = 2–8 LLM calls/message, the same 16-tool schema prefix re-sent each iteration ⇒ **~16k tokens/chat, ~90% input.** This makes **prompt/prefix caching** worth more to you than to a normal chatbot.

**Managed-first, real numbers:**

| Scenario | Chats/day | Tokens/mo | Managed per-token (Together/Fireworks 8B ~$0.18–0.20/1M) | Self-host 24/7 |
|---|---|---|---|---|
| **Launch** | 300 | ~0.14B | **~$26–29/mo** (→ ~$15–20 cached) | reliable GPU **$500–1,600/mo** |
| **Growth** | 5,000 | ~2.4B | ~$430–480/mo (→ ~$300 cached) | one L40S/4090 carries it |
| **Scale** | 50,000 | ~24B | ~$4.3–4.8k/mo | 1–2 GPUs ~$600–1,200/mo + eng |

**Corrections you must honor:**
- **You have NO per-token bill today.** A managed fine-tune *adds* ~$20–30/mo at launch — it is a future optimization, not a saving.
- **Self-host break-even is ~1.3–2.5B tokens/mo (~3–5k chats/day sustained).** Out of scope until traffic demonstrably clears that line.
- **The "$248/mo 4090 community" number is a trap** — community-tier GPUs are flaky hosts unfit for interactive production. Honest always-on reliable serving is **$500–1,600/mo** (L40S/H100). Budget the reliable number.
- **Do not assume self-host = lower latency.** Groq's LPU is among the fastest tokens/s available; a 4B on a commodity GPU may be *slower* first-token. Agent latency is usually dominated by tool round-trips (Render cold starts, sim time), which a fine-tune does not speed up. **Measure before claiming a latency win.**
- **Never scale-to-zero serverless GPU for interactive chat** (15–30s cold starts, worse than Render). Fine for batch (surrogate regen).

**Recommendation:** launch on **Together Serverless Multi-LoRA** (fallback Fireworks) — upload the LoRA, pay base per-token, **no cold start**, add as one `_PROVIDERS` entry (`base_url=api.together.xyz/v1`), keep Gemini/Groq as the live fallback tier. Migrate to a **dedicated L40S (FP8) / 24GB card (AWQ int4) + SGLang** (RadixAttention prefix-cache is tailor-made for your repeated tool-schema prefix) only past ~2.5B tokens/mo.

**Server quant:** AWQ int4 on a 24GB card (8B weights ~5–6GB → ~18GB for KV cache, which your long agentic contexts need); FP8 on L40S/H100 if quality-critical. Stay at 8B unless eval proves 30B is required.

**Desktop (only if the founder approves — see §12 risk #3):** merge LoRA→base, quantize to **GGUF Q4_K_M** (~2.5–3 GB for a 3–4B build), bundle **llama.cpp `llama-server`** exposing `/v1` on `localhost:8080` (zero client change; the sidecar-spawn pattern the desktop app already used pre-hosted-only). Runs on ≥8 GB-RAM laptops (CPU) or ≥6 GB VRAM. Trim the desktop tool set + keep context 2–4k to hold KV down.

---

## 9. The "keep upgrading" loop — capped, not perpetual

This is the part that satisfies "keep upgrading as the AI space moves ahead" **without** turning it into a permanent tax.

**Registry:** MLflow aliases (`@champion`/`@challenger`/`@canary`) — **defer until a model actually exists to manage** (do not build DVC+MLflow+Braintrust+canary at zero traffic). A registered version pins the tuple; the **only field that changes on a base swap is `base` (+ resulting adapter)**:
```
{base:"Qwen3.6-27B", adapter:"s3://…/lora-abc", train_data:"dataset-v37",
 train_config:"configs/ft_v12.yaml", prompt:"prompt-v9", eval_run:"mlflow://…/def456"}
```

**Swap-the-base CI (`remint-model.yml --base <hf_repo>`), when it exists:**
`Step 0` cheap pre-screen (lm-eval BFCL+IFEval; STOP if worse than incumbent's base) → `Step 1` fine-tune (same data/config, swap `base_model`+template) → `Step 2` deterministic eval gate (§7 hard thresholds) → `Step 3` adversarial gate (injection/PII on `web_fetch`, kill-switch) → `Step 4` compare vs `@champion` → `Step 5` human GO/NO-GO (minutes) → `Step 6` canary via `MODEL_ROUTING` weight → promote/rollback.

**Cadence (the anti-treadmill rule):**
- **Weekly:** curate the flywheel (~2–4h), run the golden eval against the *current champion* on a cron (catches provider drift behind `LLM_PROVIDER`), skim the release wire → backlog only.
- **When a new base lands — three conditions, ALL required to even fine-tune:** (1) beats/matches incumbent base on BFCL+IFEval; (2) servable in budget within the RPM/latency envelope; (3) **the champion is NOT already saturating the golden eval** — if it scores ~99% everywhere, a new base moves only noise, so **don't.**
- **Quarterly:** re-mint the champion on its own base to fold in accumulated flywheel data; prune the golden set.

**When to upgrade vs. ignore:** promote **iff** all HARD gates pass, no metric regresses beyond noise, ≥1 metric wins beyond noise, and the 24–72h canary's live oracle-faithfulness ≥ champion. **A tie is a NO — the incumbent wins ties** (churn costs re-validation + canary risk). For a physics-moat company, **once a hosted/fine-tuned model passes eval, the correct default is "re-run eval quarterly, change nothing unless it fails."** Do not run the "fresh base every 6–8 weeks, chase it" treadmill — the "durable asset" framing is not a license for perpetual model work.

**Rollback:** one alias move (previous base+adapter+config still pinned). Keep the last 3 champions warm-deployable. Pre-define the trigger: live oracle-faithfulness below champion, or error/latency SLO breach → auto-rollback, no meeting.

---

## 10. Cost & timeline (solo mid-level ML engineer)

| Phase | Wall-clock | Eng time | $ spend | Ships |
|---|---|---|---|---|
| **0 — Eval + oracle** | 1–2 wk | ~1.5 wk | **$0** (uses hosted agent you already pay $0 for) | A number for today's agent + day-one hallucination gate |
| **1 — Trace capture** | 1–2 wk (after live traffic + consent) | ~1 wk | ~$0 | PII-scrubbed, oracle-flagged corpus |
| **2 — Optimize hosted** | 1–2 wk | ~1 wk | $0 training; maybe a paid Groq/Gemini tier | Cheaper, more reliable hosted path (likely end state) |
| **3 — Fine-tune spike** | 1–2 wk time-boxed | ~1.5 wk | **~$20–80** (rented H100 hours + a few managed train runs) | Pass/fail verdict on the narrowest slice |
| **4 — Scoped deploy** | 1 wk | ~1 wk | **~$20–30/mo** managed multi-LoRA at launch | Served fine-tune on its slice + frontier fallback |
| **5 — Upgrade CI** | 1–2 wk (only once a model exists) | ~1.5 wk | registry/eval infra ~$0–50/mo | Reproducible remint-on-new-base pipeline |

**Realistic path to first served fine-tune (if a trigger fires):** ~6–8 engineer-weeks spread across gates, **~$100 one-time + ~$30/mo.** Most likely outcome given current state: **you stop at Phase 2** and bank the eval + data as permanent wins.

---

## 11. Skills / profile for the hand-off engineer

**Must-have:** Python + PyTorch fluency; hands-on LoRA/QLoRA (Unsloth or Axolotl) — has actually shipped a fine-tune, not just read about it; understands **chat templates + tool-calling serialization** deeply (train/serve skew is the #1 silent killer here); comfortable in the existing FastAPI/pytest codebase (must extend the `_call_override`-driven tests, not rewrite them); **eval-first mindset** — treats the golden set + oracle as the deliverable, not the model.

**Strongly preferred:** vLLM/SGLang serving + quantization (AWQ/FP8/GGUF); data-pipeline engineering (synthetic generation, dedup, PII scrub); MLflow/DVC familiarity (for Phase 5, later).

**Red flags when hiring/contracting:** anyone who wants to "start by fine-tuning Qwen-30B"; anyone who conflates BFCL score with product quality; anyone who can't explain why the summary number must be a verbatim copy of the tool payload; anyone who proposes shipping model weights offline without flagging the IP contradiction. **The right hire is skeptical of the fine-tune and excited about the eval harness** — that ordering is the whole job.

---

## 12. Risks & mitigations (biggest brand risk first)

1. **★ Hallucinated physics numbers (existential brand risk).** A fine-tuned 4B pattern-completes plausible-but-wrong ETs when tools fail/time out/are skipped. **Mitigations:** zero-hallucination hard gate (Layer-B, literally 0.000); training distribution where the number is a *function of the tool output* (§5A critical rule); guided-JSON decoding; frontier model kept as **live fallback forever**; the fine-tune ships only if it *matches* frontier faithfulness. **If in doubt, don't ship the fine-tune on the hot path.**
2. **Premature build burns 6–10 weeks solving a $0 problem.** Mitigation: Phase 0 is the *only* sanctioned model work until a live API + real traffic exist; production/API health + analytics outrank this entire initiative.
3. **Offline-desktop contradicts the hosted-only IP decision.** Bundling a merged GGUF hands weights to anyone who unzips the app — and the model without the engine is a degraded toy. Mitigation: **explicit founder decision, not an engineering default.** The offline justification is weaker than it looks.
4. **Distillation with no traffic → synthetic-only model that aces synthetic eval and dies on the first Hinglish typo'd bike name.** Mitigation: no v2-scale synthetic build-out until real captured queries anchor the distribution; 15–25% hard/negative cases from day one.
5. **Legal landmine from ungoverned trace capture** (personal bike/rider data, copyrighted web-fetch bodies, account IDs). Mitigation: consent/opt-out + PII scrub live *before* any capture; provenance column; short/factual web-tool payloads in training.
6. **Vendor lock-in in the eval stack** (promptfoo→OpenAI). Mitigation: eval logic in first-party pytest + oracle; frameworks are droppable dashboards.
7. **Train/serve skew from message serialization** (char truncation, `default=str`). Mitigation: generate training payloads from the *actual* `LLMClient` output.
8. **Golden cases with frozen ET break on every physics reseed.** Mitigation: reference the live engine per case; keep baseline-pin tests out of the model eval suite.
9. **Perpetual upgrade treadmill as an engineer tax.** Mitigation: capped cadence — quarterly eval, change only on a real above-threshold win; ties go to the incumbent.
10. **Misdiagnosing 30-RPM as a fine-tune trigger.** Mitigation: fix with `LLM_PROVIDER` fallback / paid tier / round-robin; RPM is explicitly *not* a trigger.

---

## 13. Phase 0 kickoff checklist — the first two weeks, task by task

**Week 1 — the oracle + the gate**
- [ ] **Day 1:** Read `motoquant/llm/agent.py`, `client.py`, and `tests/test_agent.py` end-to-end. Confirm the `_call_override("tools")` seam and how tests drive the loop offline.
- [ ] **Day 1–2:** Write `eval/oracles/physics_oracle.py` (~40 lines) — resolve a case's `{bike_id, venue_id, env, mods}` into a `BikeConfig`, run `MotoQuantEngine`, return `time_quarter`/trap/60ft/splits. Unit-test it against K5/R1/Hayabusa (must reproduce 10.0334/10.2859/10.4712).
- [ ] **Day 2–3:** Write `eval/metrics/faithful_summary.py` — Layer A (tool-vs-engine, `<1e-3`) + Layer B (regex numbers from prose vs received payloads), **with the unit-conversion whitelist + rounding tolerance** so km/h→mph and "about 10.5s" don't false-fail.
- [ ] **Day 3–4:** Author **30–50 golden cases** in `eval/datasets/golden_v/` covering: 8 faithfulness (incl. anti-hallucination "roughly what's the ¼-mile of X?" pins), 8 tool-selection (incl. in-catalog-bike-must-not-web_search, budget-ask-must-use-knapsack), 6 arg-correctness (incl. `budget_inr:null` for "no limit", `build_tier:stage_4` for "outlaw"), 6 refusal (out-of-scope + `MOTOQUANT_WEB_TOOLS=0` kill-switch), 4 multi-turn coreference. Expected values reference the **live** oracle, never frozen numbers.
- [ ] **Day 4–5:** Write `eval/metrics/{tool_trajectory,arg_correctness,budget_discipline}.py` as pytest assertions.

**Week 2 — score, report, decide**
- [ ] **Day 6–7:** Wire `eval/runners/run_eval.py` to run all golden cases against the **current hosted agent** (via the real `LLMClient`, pinned provider). Capture per-dimension pass rates + $ cost + p50/p95 latency per case.
- [ ] **Day 7–8:** Create `eval/thresholds.yaml` (§7). Make the runner emit a green/red scorecard and exit non-zero on any HARD-gate failure. Add it to CI as a non-blocking job first.
- [ ] **Day 8–9:** `dvc init`; add `eval/datasets/`; commit pointers; tag `golden-v1`. Add the checksum membership test scaffold (golden never enters training) even though no training set exists yet.
- [ ] **Day 9–10:** Write the **founder-facing scorecard**: "here is exactly how good today's hosted agent is, per dimension, at $X/query and Yms p95." Include the hallucination rate — this is the headline.
- [ ] **STOP and reassess with the founder.** Do not open Phase 1 until (a) the API is live, (b) real chat traffic exists, (c) ToS/opt-out + PII scrub are scheduled. If the current agent already passes the bar, **you have no model problem** — invest the engineer in the moat (benchmarks, catalog, physics, surrogate) and re-run this eval quarterly.

**Definition of done for Phase 0:** a reproducible, CI-runnable, oracle-checked scorecard for the live hosted agent, with a zero-hallucination gate active — 100% non-wasteable whether you ever fine-tune, switch providers, or never touch a model again.

---

## Appendix A — How this plan was produced

Synthesized 2026-07-04 from a multi-agent research pass over: (1) code recon of the existing `motoquant/llm/` agent stack; (2) the mid-2026 open-weight model landscape (BFCL-V4 / BenchLM leaderboards, June–July 2026); (3) fine-tuning/distillation methods; (4) serving & cost economics; (5) the MLOps continuous-upgrade loop; and (6) an adversarial "should you even do this" strategy review. Model names and licenses were verified against primary sources as of the date above; **re-verify the base-model table before committing to a base — the landscape moves monthly, which is exactly why the durable asset is the eval + dataset, not the weights.**
