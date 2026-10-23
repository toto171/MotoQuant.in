> **Archived 2026-10-23: internal ops** — a session-handoff note from June 2026, superseded by [docs/ROADMAP.md](../ROADMAP.md) and the open-source pivot (ADR-0006).

# NEXT_SESSION.md — briefing for the next long session

> Written 2026-06-12 at the close of the overnight rehaul + cleanup, operator-reviewed scope.
> Read together with `reports/rehaul_2026_06_12.md` (what shipped) and `reports/cleanup_2026_06_12.md` (what was removed/queued).
> State you can trust without re-litigating: origin = `main` only (+17 `archive/*` tags) · baselines K5 10.0334 / R1 10.2859 / Hayabusa 10.4712 exact · the 156-row weighted sweep (`reports/acc_final_2026_06_11.json`) is the accuracy truth · DB regen order is reseed → parts-patch · **regenerate the surrogate after ANY reseed/retune, same session** · autotune is full-sim BY DESIGN (surrogate is launch-RPM-blind) · payments untouched BY DESIGN (beta on, providers unconfigured).

---

## P0 — Desktop app pass (the committed headline of the next session)

Deferred from the rehaul night to avoid parallel-push collisions. The web/API moved a lot underneath it:

1. **Known bug:** `desktop/src/pages/BuildPage.tsx` hardcodes `EXCLUSIVE_PREFIXES` missing `swingarm` vs backend `roi.py EXCLUSIVE_CATEGORIES` (grown June 11: chain, boost_kit, nitrous, wheelie_bar, swingarm_ext) — desktop users can stack two swingarm extensions. Prefer deriving exclusivity from the API over patching the hardcoded list.
2. **Contract sync (verify each, then adopt):** jobs API (`POST /api/jobs/* + poll + cancel`) — desktop appears to still call the sync routes (no progress bars, no stop); unknown-`bike_id` now 404s (desktop error handling must not treat it as a crash); `/api/tires` + `/api/parts` now return honest `total` fields; `/api/surrogate/predict` returns `source: numpy` + envelope info (desktop BuildPage surrogate preview wiring predates all of this).
3. **Identity port:** bring the cockpit token set (ink surfaces, brand-orange, mono label voice, seven-segment numerals where natural) to the desktop UI so it stops looking like a different product.
4. **Small web companion:** `?bike_id=` preselect handoff from `/bikes/[id]` → `/optimize` (the detail-page CTA currently links plain).
5. **Phase-5 carry-forwards still unproven:** PyInstaller sidecar binaries never built on any target OS, `cargo tauri dev` handshake never confirmed, icons are placeholders, the `v*`-tag CI release matrix has never run. If the session has runway, push a `v1.0.0-beta.x` tag and watch the matrix.

## P0 — Paid-launch blocker: account durability (NOT optional before enforcement)

Prod SQLite is baked into the Docker image (Render free tier, no disk): **every deploy wipes users, saved runs, and subscriptions.** Fine for the open beta; a hard blocker before `MOTOQUANT_BILLING_ENFORCE=true`. Fix = Render persistent disk + `MOTOQUANT_DB=/data/…` (+ one-time copy on boot), or Supabase Postgres for the auth/subscription tables. Documented as Step 0 in `docs/PAYMENTS_SETUP.md`. Decide and ship it the session before any real-money work.

## P1 — Accuracy floor: small-cc DERIVED benchmarks need real data

The worst residuals (RTR 200 +2.77s, MT-15 V1 +2.63s, CB350RS +1.57…) are all weight-0.1 DERIVED rows — the 0-100×1.6 formula is demonstrably optimistic below ~25 hp (real MT-15 runs ~17.5-18s, not 15.8). No knob fixes this; only instrumented data does (Phase-3 calibrator path). **Recommendation:** start a Dragy collection program — the `/api/calibrate/dragy` upload already works; add a "submit your timeslip" CTA on small-cc bike pages + a WhatsApp/community ask through the Pune/Narhe contacts. Even ~10 verified Indian-commuter runs would replace the worst rows and visibly move the published numbers.

## P1 — next.js 15/16 migration

14.2.35 cleared the critical pile; **2 advisories remain with no 14.x fix** (RSC deserialization DoS, self-hosted image-optimizer DoS — both partially mitigated on Vercel managed infra). Breaking migration (async request APIs, config changes): dedicated session, full `next build` + route-table pin + live walkthrough. Don't piggyback it on feature work.

## P1 — Content refresh: dated accuracy claims

`/whitepaper`, `/docs/validation`, and the physics-engine blog still present the April 74-row sweep (internally consistent, deliberately relabeled "weighted benchmarks", flagged in code comments). One content pass: regenerate their tables/metrics from `reports/acc_final_2026_06_11.json` (156 rows, ±0.010s top-10) so the marketing surface matches the landing page. Same pass: **og-image regeneration** — the auditor flags it stale and no generator script exists; either write `scripts/generate_og_image.py` (auditable forever) or regenerate manually once. Also fix the auditor's `tests_collected ERROR` (it can't count tests in-sandbox; make it read a committed count or skip gracefully).

## P2 — Code-health queue (verified findings, deliberately not auto-applied)

- `scrape --bulk`: flag advertised in `run.py` but `cmd_scrape_bulk` is unreachable — wire it or remove the flag (75 dead lines either way).
- Pricing DTOs half-wired (`api.py` ~2777): `PricingEntryOut`/`BikePricingSummaryItem` unused while sibling responses carry untyped lists + dishonest `float = Field(None)` defaults — completing this changes response validation; needs its own tested pass.
- `_infer_cylinder_config` wrong for bikes 199/333 (V2/V4 inferred as I2/I4) — the parts patch script guards the DB rows; fix the root inference so future reseeds stop regressing it.
- "Indian" + "Indian Motorcycle" duplicate manufacturer rows — merge + re-point FKs (small migration script).
- ~25 stale constraint VALUES remain in seed catalog sources (DB itself is patched) — **sync the sources before ANY fresh-seed**, or a new DB resurrects the leaks.
- 21/23 vintage-2T bikes lack OEM tire fitments — needs honest period data (no fabrication); period catalogs or punt permanently.
- `LLMRateLimitError` declared, never raised — implement 429 detection in `llm/client.py` or delete the class.
- 48 magic `×3.6` conversion sites + inline ₹ formatting in 14 files — consolidate only with regression cover (`/3.6 → *KMH_TO_MS` is NOT bit-identical; baseline risk).
- 52 unread dataclass fields in `models.py` (suspension damping, brake specs…) — per-field decision: implement in physics or remove; removal breaks config round-trips, so do it with the reseed machinery in hand.
- `app.py` (Streamlit) retirement decision — README/CONTRIBUTING/ONBOARDING still tell users to run it; web + desktop supersede it. Operator call, then docs follow.
- Minor: redundant explicit `styled-jsx` dep in web; `DISPATCH_2026-04-24*.md` + `prompts/` are archive candidates.

## P2 — Tooling investments (my ranked recommendations, all still undone from the toolkit shortlist)

1. **pytest-regressions snapshot over the full 501-bike sweep** — formalizes the implicit baseline contract; the single highest-ROI guard for every future physics change (tonight's R15-primary-ratio bug would have been caught the day it shipped).
2. **Sentry on Render + Vercel** — we are currently blind to prod 500s and JS errors; free tier suffices; `observability.init_sentry()` already no-ops on a missing DSN, so this is mostly an env-var + verify session.
3. **Numba `@njit` on the RK4 inner loop** — sweeps, optimizer fallback sims, and autotune (full-sim by design) all get faster; biggest UX lever left for autotune's 30-90s prod jobs.
4. **Playwright smoke in CI** — landing boot → quick sim → optimizer happy-path against a preview URL; catches the rewrite/Suspense class of regression before deploy.
5. **Coverage signal** — 1,376 test functions but zero branch-coverage truth; one CI artifact answers "which physics branches are actually exercised".
6. **MotoQuant MCP server** — weekend-scale wrap of the existing OpenAPI surface; Phase-6 distribution + a demo that writes its own marketing.

## Operator-only actions (sessions can't do these)

- **Rotate the PAT** — overdue since 2026-06-03 (still works). `scripts/secrets_bootstrap.sh`; grant `workflow` scope this time so sessions can edit `.github/workflows/*` when needed.
- **Finish the local-folder sync** (fetch already done from the sandbox): `cd "…\Vehicle Dynamics" && git merge --ff-only origin/main` from a real terminal. Working tree verified phantom-dirty only.
- **Real-phone pass** on the redesign (sandbox can't truly verify mobile; code-level responsive checks passed).
- **When ready for money:** `docs/PAYMENTS_SETUP.md` — but Step 0 (account durability above) first, then Razorpay KYC/plans → Stripe prices → JWT_SECRET/SMTP → flip enforce.
- Optional hygiene: merge `TOKENS_UPDATE_2026-05-04.md` into `tokens.md` and delete it (its own instruction says so); delete the QA accounts note — they vanish on next image deploy anyway.

## Explicitly NOT to-do (so nobody "fixes" them)

- Autotune on the surrogate — it would be silently wrong (launch-RPM-blind); the progress bar + cancel button are the intended UX.
- `vercel.json` ×2 + `next.config.js` duplicated rewrite/cron blocks — intentional (root-directory setting unknown; one copy is inert).
- `CategoryProfile` reserved knobs, `payments._paypal_configured`, `users_repo.get_session_by_jti` — reserved/planned surface, documented.
- The two historical Railway mentions left in `web/lib/api.js` + `next.config.js` comments — they record the incident that justifies the same-origin proxy.
