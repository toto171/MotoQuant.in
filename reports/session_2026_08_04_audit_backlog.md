# 2026-08-04 — codebase audit (delta over July-25) + deferred-work backlog

> **PARTIALLY SUPERSEDED — read this first (added 2026-08-10).** PR #120
> ("full-night run", merged to main 2026-08-09) independently closed a large
> share of the §2 backlog below. **Do NOT re-scope these — they are DONE on
> main:** the `is_at_wheel`/parasitic decision (shipped as the crank-semantics
> epoch + retune), the gearing fix for the four speed-limiter heavies (+9 new
> annotations), catalog de-duplication (regen made deterministic), the
> Next.js 14→15 migration (27 advisories → 0), the chat tier-gate decision
> (settled: the executor inherits the caller's tier), production dependency
> pinning (lockfile + CVE floors), the Scrapling safety gates (now fail
> closed), the 8 inert quickshifter SKUs (armed), the OEM drag-tire fitment
> defaults, and three previously-vacuous test gates. The MCP server + skill
> also shipped. `tests/test_llm_runner.py`'s env leak was fixed on main too,
> more thoroughly than here (it also stops metering rows writing into the
> shipped catalog) — main's version is the one in the tree.
>
> **Still open and still valid** (verified absent from main at 270074e): the
> three HIGHs this PR fixes — the DNF-sentinel ranking bug, the OWM API-key
> leak, and the magic-link token reaching production logs — plus the
> `part_ids` caps, the chat-agent duplicate-part/budget clamps, and the
> `stroke_type`/`gear_ratios` gap behind the 2-stroke structured data.
>
> **Accuracy figures quoted below are superseded.** The authoritative sweep is
> now `reports/acc_final_2026_08_08.json`: **276 matched / weighted |Δ|
> 0.2629 s / bias +0.0073 s**. The three pinned references are unchanged.

**Branch:** `claude/codebase-audit-backlog-fdqcnb`
**Method:** four parallel finder agents (physics/analysis/LLM · API/security/DB ·
web frontend · tests/CI/scripts/docs), each briefed on
`reports/session_2026_07_25_weekly_audit.md` and instructed to report only the
**delta** over its known-open list. Findings acted on here were re-verified
inline by this session — not taken from an agent summary (AGENTS.md rule 3).

**Verification state of the tree at HEAD before any edit:**

- `scripts/check_baselines.py` — K5 9.9330563825 / R1 10.1435897157 /
  Hayabusa 10.3633450813, **Δ +0.00e+00 ×3**.
- 4,532 tests collected, 0 collection errors.
- `next build` — 178 files clean, 76/76 static pages.
- `audit_headline_stats.py --fail-on-drift` — rc 0.

---

## 1. What this session fixed

Every fix below was proven **revert-sensitive** where it is testable, ran
against the real production path, and left the three pinned baselines
bit-identical.

### 1.1 A did-not-finish run was ranked as the fastest ET `[HIGH]` — fixed

`SimResult.time_quarter` stays at its `0.0` default when a run never reaches the
quarter-mile (`finished_quarter` exists precisely to flag this). Every
argmin/sort consumer read `time_quarter` raw, so a DNF was interpreted as an ET
of **0.0 s — the global minimum**:

- `ecu_autotune._gearing_recommendation` / `_launch_recommendation`
  (`min(candidates, key=…["et_s"])`) recommended whichever candidate *failed to
  finish*;
- `agent._exec_compare_bikes` picked `winner` on raw ET;
- `agent._exec_rank_bikes` sorted DNFs to the top of the "fastest" list.

Reproduced by the finder agent with **fully API-legal inputs**: `/api/autotune/ecu`
on the Yamaha RX100 at `altitude_m=2400, ambient_temp_c=45, rider_weight_kg=150`
(all inside `AutotuneRequest`'s own `Field` bounds) recommended "14/47 — taller
(more top-end)" with `delta_et_s = −25.691` and a combined net ET of `0.0 s`,
because the 47-tooth candidate DNF'd. At 5000 m *every* candidate DNF'd and the
whole recommendation collapsed to `0.0 s`.

**Fix:** new `physics.effective_et(sim)` + `DNF_ET_SENTINEL_S = 999.0` — a
finite sentinel above the 26 s ceiling (`inf` breaks `a − b` arithmetic).
Threaded through `roi._run_et` (which feeds both autotune sweeps and ROI
deltas), `agent._sim_to_dict` and `agent._exec_rank_bikes`; the agent payloads
now also carry `finished_quarter` so a client can render the DNF honestly.
A finished run passes through **bit-identically** (asserted).

New `tests/test_dnf_sentinel.py` (4 tests). **Revert-proof:** reverting
`effective_et` to a raw pass-through turns 3 of the 4 red
(`AssertionError: 0.0 != 999.0`).

### 1.2 The full serial test suite was red — fixed at the root `[HIGH]`

`tests/test_llm_runner.py` set `MOTOQUANT_DB` to an **empty** tmp DB at *module
import* (collection) time with no restore and no unlink. In a full
`pytest tests/` run that left the env pointing at an empty DB when the run phase
began, so `test_chat_resolver`'s Live resolver tests — which read
`$MOTOQUANT_DB` — resolved against an empty catalog:

```
pytest tests/ -k "TestResolveBikeLive or TestResolveVenueLive"
    before:  14 failed,  2 passed
    after:   16 passed
```

Both modules pass standalone, which is exactly why this survived: the July-25
audit ran the 63 modules **individually**, and CI has had no runners since
July 13 (operator item O1). **Every "full suite green" claim since PR #114
traces to per-module runs that could not see this.** When O1 is restored, the
first main-push CI run would have failed here and looked like a chat-resolver
regression.

**Fix, two layers** (either alone is insufficient — the leak simply migrates to
the next alphabetically-last import-time setter, which is `test_jobs_api`):

1. `test_llm_runner.py` now sets the env in `setUpModule` (run time) and
   restores + unlinks in `tearDownModule` — the established `test_agent.py`
   pattern. It also no longer leaks a `/tmp/mq_chat_test_*.db` per invocation.
2. `test_chat_resolver._live_db_path()` now **prefers the repo `motoquant.db`**
   and demotes `$MOTOQUANT_DB` to a fallback. These tests exist to resolve real
   names against the real catalog, so pinning is the correct semantics and makes
   them ordering-independent regardless of who leaks next.

`docs/KNOWN_TRAPS.md` T6 claimed "**They all pass serially.**" — false on the
tree as found. T6 is rewritten with both rules and the repro command.

### 1.3 `/api/venues/resolve` leaked the OpenWeatherMap API key `[HIGH]` — fixed

`_fetch_owm_for_location` passes `appid` as a query param, then returns
`str(exc)` to the caller. A `requests.HTTPError` string embeds the **fully
resolved URL**, so the 502 detail contained the operator's key. OWM returns
**404 for an unknown city**, making this a single anonymous request:

```
POST /api/venues/resolve {"location":"zzqx_nonexistent_city"}
→ 502 "...for url: https://api.openweathermap.org/...?appid=<REAL_KEY>&..."
```

The July-25 rate-limit fuse does not mitigate it — one request suffices; and it
also fires on 401 (rotated/unactivated key → *every* call leaks).

**Fix:** redact the key from the exception string before it is logged or
returned. Verified against a real `requests.HTTPError`: the client now sees
`appid=***` and the message stays diagnostically useful.

### 1.4 Unbounded `part_ids` → unbounded serial queries on the shared connection `[HIGH]` — fixed

The July-25 fix de-duplicated `part_ids` but never bounded the list. `/api/simulate/quick`
is (correctly, for the slider UI) **unmetered and unthrottled**, and
`_apply_parts_to_config` runs one `SELECT` per id against the module-singleton
connection. `{"part_ids":[0…1_000_000]}` monopolises `_db_conn` in a GIL-holding
loop; every other DB-touching request — **including `/api/health`** — serialises
behind it, so Render can mark the instance unhealthy. A new variant of
KNOWN_TRAPS T14.

**Fix:** `max_length=50` on all five `part_ids` fields (quick, top-speed,
distance, compare `a`/`b`). Verified through the real routes: 51 ids → **422**,
normal request → **200**.

### 1.5 Chat agent: duplicate parts and an unbounded knapsack budget `[MEDIUM]` — fixed

Both are agent-path twins of API-path fixes that never reached `llm/agent.py`:

- **Duplicate `part_ids`** — `_build_config_for` called `apply_multiple` on the
  raw list. Measured: `part_ids=[56]` → ET 10.11 s / ₹238,000;
  `[56,56,56]` → ET **9.956 s / ₹714,000** — a fabricated 0.154 s gain and 3×
  cost from one repeated integer, returned as a normal success block.
- **Unbounded `budget_inr`** — the tool schema has no `maximum`, and
  `roi._grouped_knapsack` allocates `budget // 100` DP buckets. The API caps this
  at ₹5M (`Field(le=5_000_000)`); the agent bypassed that model entirely. A
  "₹10 billion build" asks for **100 million buckets** (measured 153 MB at 1e8;
  linear ⇒ ~15 GB at 1e10) — an OOM kill on a 512 MB instance, reachable
  **unauthenticated** since `/api/chat` has no tier gate.

**Fix:** de-duplicate preserving order; clamp the LLM-supplied budget to the same
₹5M ceiling the API enforces (`None` stays `None` so stage_4/outlaw resolves its
own no-limit cap). Verified: ₹10bn → 50,000 buckets; `[56,56,56,12]` → `[56,12]`.

### 1.6 Magic-link tokens printed to production logs `[MEDIUM]` — fixed

`_send_magic_link_email` falls back to stdout when SMTP is unconfigured — the
current beta state — so the deployed Render instance printed a live,
single-use, 10-minute **account-takeover credential** to its log stream on every
request. The response-echo of the same token is correctly gated on
`not IN_DEPLOYED_ENV`; this sibling path was not.

**Fix:** gate the stdout branch on `IN_DEPLOYED_ENV` too, logging an honest
"no email backend configured; link not delivered" warning instead. Verified both
directions: deployed → token absent from stdout; dev → still prints (no local
workflow regression).

### 1.7 Every 2-stroke bike page published "4-stroke" structured data `[MEDIUM]` — fixed

`web/app/bikes/[id]/layout.js` reads `bike.stroke_type` and `bike.gear_ratios`
to emit JSON-LD, but `/api/bikes/{id}` never returned either field (they live
inside the `engine_params` / `drivetrain_params` blobs and were not merged to
the top level). `stroke_type === 2` was therefore *always* false: the ~30
two-stroke bikes (RD350, RX100, NSR250R, RG500…) publish
`fuelType: Gasoline` and "4-stroke" to search engines — on exactly the pages
whose content emphasises 2T physics. `numberOfForwardGears` was dead for all 541.

**Fix:** merge both fields in the `get_bike` route (the client was right; the API
was incomplete).

### 1.8 Content and doc truth

- **`/whitepaper` per-cluster table was the July-13 sweep** while its own
  attribution line, the aggregate row and the surrounding prose all cite
  July-17. Seven rows understated reality — worst: Entry 150–200 bias
  **−0.030 → −0.402 s** (13×) and small-cc I4 **+0.032 → −0.976 s**. Synced to
  `reports/acc_final_2026_07_17.json`, plus an added paragraph that states the
  two large negative biases honestly (they *worsened* when optimistic DERIVED
  rows were replaced with instrumented truth — the cluster constants had been
  fitted to the optimistic data) and notes an N=2 cluster is not a meaningful
  bias estimate.
- **`CLAUDE.md` CURRENT STATE** quoted the superseded 0.2533 / +0.0166 pair as
  current. Now 0.2721 / −0.0047 with an explicit "do NOT quote the July-13 pair"
  note. This is the file every session reads first, and the stat audit does not
  scan it.
- **`CHANGELOG.md`** had no PR #118 entry (the same "one merge behind" class
  #118 itself fixed for #114/#116). Added.
- **`docs/ARCHITECTURE.md`** named a GitHub Actions cron as the live cold-start
  guard; its schedule has been commented out since 2026-07-14 and Actions has no
  runners. Now names the layers that actually run (Vercel `/api/wake` crons +
  in-app `keepwarm.py`).
- **`docs/ONBOARDING.md`** stated two different accuracy headlines sixteen lines
  apart (221 benchmarks / ≈0.22 s vs the correct 250/277 / 0.272 s), and offered
  "add coverage.py + a CI artifact" as a good-first-issue for something CI has
  done since July 4. Both corrected; the task is now the real one (ratchet a
  floor).
- **`accuracy_data.json`** carried `generated: 2026-07-04` over July-17 data
  (a stale `--stamp` arg). Corrected — cosmetic, but it would mislead the next
  auditor into thinking the viz data is pre-epoch.
- **`web/lib/telemetry.js`** commented that it skips previews but only checked
  localhost, so `*.vercel.app` preview clicks landed in the prod funnel. Guard
  now matches the comment.

### 1.9 A staleness guard that never tested the shipped artifact `[MEDIUM]` — fixed

`test_power_boost_regression.TestDbMatchesSpec` — whose docstring says "the whole
point is catching future stale-DB drift" — called `live_db_copy()` with no
argument, and that helper prefers `$MOTOQUANT_DB`. In CI that is the freshly
seeded `/tmp/ci.db`; in a local full run it is a sibling's tmp DB. Either way it
validated a DB that matches `spec_to_bike_config` **by construction** rather than
the tracked `motoquant.db` that ships to Render. Now pins the repo DB, matching
`test_regression_snapshot.py` and `test_db_gearing_integrity.py`.

---

## 2. Found and NOT fixed — deliberately

Each of these moves pinned baselines, published numbers, the catalog, or is a
product decision. They do not belong in an audit PR. **Ordered by what I would
do first.**

1. **Settle the chat tier-gate** *(carried from July-25 §3.5 — still open, now
   more urgent given 1.5)*. Build Optimizer, ECU Autotune and the Outlaw
   pipeline are all `require_tier("pro")` yet fully reachable unauthenticated
   through `/api/chat`. Must be decided **before** `MOTOQUANT_BILLING_ENFORCE`
   is flipped or the conversion lever is void on day one. Product decision.
2. **`bayesian_opt.power_delta_hp` is a dead knob for every bike with a stored
   dyno curve `[MEDIUM]`.** `_apply_params_to_config` mutates
   `engine.peak_power_hp` but never scales `dyno_curve.torque_nm`, so physics
   ignores it — the exact April-24 dead-knob mechanism. Every sibling path
   (`sobol`, `api._apply_power_boost`, `agent._apply_power_boost`) scales the
   curve; this one forgot. Measured on the Hayabusa: `power_delta_hp` of **+50
   and −30 both give ET 10.2253 s**, while `mass_delta_kg=−15` moves it. The
   optimizer's largest lever (−30…+50 hp) is inert for the 25 curve-carrying
   bikes and all three references, so the GP surrogate learns "power doesn't
   matter". CLI-only (`analysis optimize`), not on the FastAPI surface — hence
   not shipped here, but it is a one-line-shaped fix that wants its own
   verification pass.
3. **Multipart uploads still fill disk during parse `[MEDIUM]`.** The July-25
   25 MB cap runs in the handler body, but Starlette parses the body **first**
   and skips `max_part_size` for *file* parts, spooling the whole upload to
   `/tmp`. The commit message named "an OOM kill plus a disk fill"; only the OOM
   half is closed. Both calibrate routes are anonymous in beta and unrate-limited.
   Needs a size guard at the ASGI/middleware layer.
4. **Payments: the idempotency ledger commits before entitlement `[MEDIUM]`.**
   `record_payment_event` commits in its own transaction, *then* the handler
   grants the tier. If the grant raises (a locked DB under T14 contention,
   disk-full), the provider's retry is dropped as a duplicate and the customer
   has **paid but is never upgraded** — silently and permanently. Record and
   grant in one transaction, or record only after success. Inert until billing
   is enforced, which is exactly why it should be fixed before then.
5. Everything in the July-25 §3 list that remains open — `is_at_wheel` /
   `parasitic_mult` (blocks the cluster retune), the four speed-limiter heavies'
   gearing, catalog duplicates, the 29 inert priced SKUs, `has_vht`,
   Next.js 14 EOL, dependency pinning, Scrapling safety gates.

Lower-severity items recorded for the next pass: two anonymous unrate-limited DB
writers (`/api/bikes/suggest`, `/api/specs/correct`); full-sim routes metered but
unthrottled; chat `rank_result` blocks silently dropped by the transcript UI
(`ChatPanel` has renderers for the other 12 block types); the two `vercel.json`
files diverged on security headers and cache policy, and which one production
reads is indeterminate from the repo; landing/about "4,393 tests" stale since
July 6 (4,536 collect today — the audit script's tests gate skips when pytest
can't be invoked, so nothing enforced it); the KTM 890 blog's present-tense
"+0.18 s cluster bias" / "90-benchmark" claims; `test_profile_knobs`' docstring
promising per-knob liveness tests for 8 knobs when only 4 have them; Makefile ⟷
CI parity gaps (`make check` omits the two guards CI's PR tier runs;
`test_catalog_snapshot_no_drift_full` is reachable from no make target and no
workflow).

---

## 3. Verification of this session's changes

| Gate | Result |
|---|---|
| `scripts/check_baselines.py` | **Δ +0.00e+00 ×3** — bit-identical |
| `tests/test_dnf_sentinel.py` (new) | 4 passed; **3 fail on revert** |
| `pytest tests/ -k "TestResolve*Live"` | **16 passed** (was 14 failed / 2 passed) |
| Affected modules (12) | agent · llm_runner · chat_resolver · api · auth · api_input_integrity · dnf_sentinel · ecu_autotune · analysis · build_optimizer · outlaw · power_boost_regression — all green |
| Drift guards | regression_snapshot · physics_invariants · profile_knobs · validation — green |
| Collection | 4,536 tests, 0 errors |
| `ruff check` / `format --check` | clean / 254 files formatted |
| `next build` | 178 files clean, **76/76** static pages |
| `audit_headline_stats.py --fail-on-drift` | rc 0 |

`motoquant.db` is **untouched** by this session — no catalog, physics-data or
seed change. The `sim_usage` rows the finder agents incidentally wrote while
running sims were reverted (`git restore`).

---

## 4. Operator backlog

The deferred-work list this session was also asked to produce is delivered in
chat; the durable version of what blocks revenue lives in `docs/ROADMAP.md`
(P0-1…P0-4) and the operator table in the July-25 report §5, both still
accurate. The single highest-leverage item is unchanged and is now
load-bearing for this report: **O1, GitHub Actions billing.** CI has had no
runner since 2026-07-13, PRs #114/#116/#118 all merged unverified, and finding
1.2 above is precisely the class of defect that a working CI would have caught
the day it landed.
