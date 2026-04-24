#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────
# MotoQuant — seed GitHub Issues + Labels (v2, phase-aligned)
#
# This script now reflects both:
#   (a) Launch-ops issues for immediate subscription rollout (P0)
#   (b) Arya's 28-week phased engineering roadmap (Phase 1 → Phase 5)
#
# Run from repo root (after installing + authenticating gh CLI):
#   bash scripts/seed_github_issues.sh
#
# What this does:
#   1. Creates labels (priority, effort, area, phase) — idempotent.
#   2. Creates 5 phase-milestone issues (long-arc tracking).
#   3. Creates ~32 concrete sub-task issues under the phases + launch ops.
#   4. Does NOT assign anyone — do that in the UI after running.
#   5. Does NOT create the Project board — use the UI to board-ify.
# ─────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO="da25mem5s02-debug/MotoQuant_v1"

# ─── Preflight ────────────────────────────────────────────────────────
command -v gh >/dev/null 2>&1 || { echo "✗ gh CLI not found. Install from https://cli.github.com/"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "✗ Not authenticated. Run: gh auth login"; exit 1; }

echo "=== Seeding GitHub Issues for $REPO ==="
echo

# ─── Labels ───────────────────────────────────────────────────────────
label() {
  gh label create "$1" --color "$2" --description "$3" --repo "$REPO" --force >/dev/null 2>&1 || true
  echo "  label: $1"
}

echo "--- Labels ---"
# Priority
label "P0"              "B60205" "Blocker / launch-prereq"
label "P1"              "D93F0B" "Current-phase core work"
label "P2"              "FBCA04" "Stretch / nice-to-have"
label "P3-deferred"     "C2E0C6" "Later-phase or stretch"

# Effort
label "S"               "BFDADC" "<4 hours"
label "M"               "6EBEDE" "~1 day"
label "L"               "1D76DB" "2-3 days"
label "XL"              "0052CC" "Full week+"
label "epic"            "3E4B9E" "Multi-week milestone"

# Phase
label "phase-1"         "0366D6" "Wk 1–4: Surrogate → production grade"
label "phase-2"         "0E8A16" "Wk 5–12: Cornering + lateral dynamics"
label "phase-3"         "1D76DB" "Wk 13–16: Weather + surface + time-of-day"
label "phase-4"         "6F42C1" "Wk 17–22: AI tuning intelligence"
label "phase-5"         "E99695" "Wk 23–28: Frontend + platform hardening"
label "launch-ops"      "D4C5F9" "Subscription launch, orthogonal to phases"

# Area
label "physics"         "F9D0C4" "Physics engine / calibration"
label "backend"         "C5DEF5" "FastAPI + motoquant/ Python"
label "web"             "FEF2C0" "Next.js web frontend"
label "desktop"         "D4C5F9" "Tauri desktop app"
label "infra"           "BFE5BF" "Vercel / Railway / GitHub / DNS / CI"
label "payments"        "5319E7" "Razorpay / Stripe / PayPal"
label "ai"              "E99695" "ML / LLM / surrogate"
label "db"              "FBCA04" "Bike / parts / tires catalog"
label "research"        "0E8A16" "Investigation before code"
label "content"         "D4C5F9" "Copy, screenshots, GIFs"
label "blocked"         "E11D21" "Cannot proceed"
label "needs-review"    "5319E7" "Awaiting co-founder review"

echo

# ─── Issue creator ────────────────────────────────────────────────────
issue() {
  local title="$1" labels="$2"
  shift 2
  local body_file
  body_file=$(mktemp)
  printf '%s\n' "$@" > "$body_file"
  local url
  url=$(gh issue create --repo "$REPO" --title "$title" --label "$labels" --body-file "$body_file")
  rm -f "$body_file"
  echo "  ✓ $url"
  echo "    → $title"
}

# ─── Launch-ops (P0) — subscription rollout prereqs ───────────────────
echo "--- P0 launch-ops (subscription rollout) ---"

issue "Razorpay production launch" "P0,M,payments,backend,launch-ops" \
  "Create 4 plans in Razorpay dashboard:" \
  "- Pro monthly ₹499" \
  "- Pro yearly ₹4999" \
  "- Studio monthly ₹2999" \
  "- Studio yearly ₹29999" \
  "" \
  "Set env vars on Railway: \`RAZORPAY_KEY_ID/SECRET/WEBHOOK_SECRET\`, \`JWT_SECRET\` (32 random bytes), SMTP or Resend." \
  "Integration-test webhook in Razorpay test mode. Flip to live keys." \
  "" \
  "**Effort:** 1 day"

issue "Wire AuthProvider into production layout" "P0,S,web,backend,launch-ops" \
  "Wrap Next.js \`layout.js\` children with \`<AuthProvider>\`." \
  "Drop \`<TierBadge>\` + \`<UpgradeCTA>\` into SimulatorWidget + BuildPage." \
  "" \
  "**Effort:** 0.5 day"

issue "Free-tier sim counter (3/day)" "P0,S,backend,launch-ops" \
  "Add \`sim_usage\` table. Wrap \`/api/simulate\` + \`/api/simulate/quick\` with a counter." \
  "Free tier: HTTP 429 past 3 sims/day. Surface \"N of 3 today\" on SimulatorWidget." \
  "" \
  "**Effort:** 0.5 day"

issue "Vercel Pro upgrade" "P0,S,infra,launch-ops" \
  "Upgrade to Vercel Pro (\$20/mo). Removes the single-author gate, adds analytics, more build minutes." \
  "" \
  "**Effort:** 15 min"

issue "Railway Pro upgrade + project rename" "P0,S,infra,launch-ops" \
  "Upgrade Railway to Pro before trial runs out. Rename project \`proactive-adventure\` → \`motoquant-api\`." \
  "" \
  "**Effort:** 15 min"

issue "GitHub plan decision (Pro vs Team)" "P0,S,infra,launch-ops" \
  "Pick Pro (\$4/user/mo) or Team (\$4/user/mo + protected branches + required reviews)." \
  "Recommend Team for two-person code-review hygiene." \
  "" \
  "**Effort:** 15 min"

issue "Stripe integration (non-INR gateway)" "P0,L,payments,backend,launch-ops" \
  "Mirror Razorpay architecture. New \`motoquant/subscriptions_stripe.py\`. Reuse existing tables." \
  "Auto-detect currency on \`/pricing\` — INR → Razorpay, everything else → Stripe." \
  "Stripe webhook handler with signature verification." \
  "" \
  "**Effort:** 1.5 days"

issue "PayPal integration (third gateway)" "P1,M,payments,backend,launch-ops" \
  "One-time annual-license checkout links (no recurring). Good for SEA markets." \
  "New \`motoquant/subscriptions_paypal.py\`." \
  "" \
  "**Effort:** 0.5 day"

issue "Hero GIF + 6 feature screenshots" "P1,S,content,web,launch-ops" \
  "Record 10-second Hayabusa-sim loop → \`web/public/hero-sim-preview.gif\`." \
  "6 feature screenshots into \`web/public/screenshots/\` (physics-chart, parts-catalog, calibration-overlay, roi-chart, desktop-app, api-docs)." \
  "" \
  "**Effort:** 0.5 day"

issue "Collect 2 real testimonials" "P1,S,content,research,launch-ops" \
  "Replace the \`TESTIMONIALS\` COPY placeholders in \`web/app/page.js\`." \
  "Target Narhe/Pune beta users, Bangalore drag racers, tuning-shop owners." \
  "" \
  "**Effort:** 0.5 day + response-wait time"

echo

# ─── Phase 1: Surrogate model → production grade (Weeks 1–4) ──────────
echo "--- Phase 1: Surrogate → production grade (Wk 1–4) ---"

issue "Phase 1 milestone: Surrogate model → production grade" "P0,XL,epic,phase-1,ai,backend" \
  "**Duration:** Weeks 1–4" \
  "**Priority:** Highest — unblocks all downstream AI features" \
  "" \
  "Current state: XGBoost surrogate at R²=0.95, MAE 535ms, trained on 1.5k Sobol samples." \
  "Target: MAE <50ms on ET, <1.5 km/h on trap speed, <5ms inference, served via \`/api/surrogate/predict\`." \
  "" \
  "**Sub-tasks (track in separate issues):**" \
  "- [ ] 1.1 Training data sweep: 1.5k → 50k Sobol samples" \
  "- [ ] 1.2 XGBoost retrain + Optuna hyperparam search" \
  "- [ ] 1.3 DNN ensemble member (retrain + XGB+DNN averaging)" \
  "- [ ] 1.4 Deploy \`/api/surrogate/predict\` + \`/sensitivity\` routes" \
  "" \
  "**Critical:** Every physics change must run \`scripts/reseed_configs_from_specs.py\` (the reseed trap)." \
  "" \
  "Sub-task prompts for Claude Code are in \`docs/phase_plan.md\`."

issue "1.1 Training data sweep: 1.5k → 50k Sobol samples" "P0,L,phase-1,ai,backend" \
  "Use existing \`surrogate_data.py\` Sobol sampler. Expand to 50,000 parameter sets in the 47-d feature vector." \
  "Run via \`sweep_chunked.py\` for parallelism. Save to Parquet (not npz — better handling for large tabular data)." \
  "" \
  "**Expected compute:** ~5.5 hours at 400 ms / sim on a modern machine." \
  "**Deliverable:** \`artifacts/surrogate/samples_50k.parquet\`." \
  "" \
  "Add \`pyarrow\` to requirements if not present."

issue "1.2 XGBoost retrain with Optuna hyperparam search" "P0,L,phase-1,ai" \
  "Retrain on 50k samples. Optuna hyperparam search, 100 trials, objective: minimize ET MAE on 5k holdout." \
  "Tune: \`n_estimators\`, \`max_depth\`, \`learning_rate\`, \`subsample\`, \`colsample_bytree\`, \`reg_alpha\`, \`reg_lambda\`." \
  "" \
  "**Target:** MAE <50ms for ET, <1.5 km/h for trap." \
  "**Deliverable:** \`artifacts/surrogate/xgb_50k_tuned.pkl\` + \`docs/surrogate_v3_report.md\`." \
  "" \
  "Add \`optuna\` to requirements."

issue "1.3 DNN ensemble member" "P1,M,phase-1,ai" \
  "Retrain \`motoquant/analysis/surrogate_dnn.py\` on the same 50k dataset." \
  "Create an ensemble predictor that averages XGBoost + DNN predictions." \
  "DNN handles interaction effects XGBoost might miss in high-dim tyre-weather space." \
  "" \
  "**Deliverable:** \`artifacts/surrogate/ensemble_predictor.py\` with \`EnsembleSurrogate.predict()\`."

issue "1.4 Deploy /api/surrogate/predict + /sensitivity routes" "P0,M,phase-1,backend,ai" \
  "Create \`motoquant/api/surrogate_routes.py\`:" \
  "- POST \`/api/surrogate/predict\` — accepts bike_config + weather overrides, returns ET/60ft/trap + confidence bounds" \
  "- GET \`/api/surrogate/sensitivity\` — returns SHAP feature importance for a given config" \
  "" \
  "Load ensemble at FastAPI startup (app.state). Target inference latency: <5 ms." \
  "Gate behind \`require_tier(\"pro\")\`." \
  "Hook BuildPage sliders to this endpoint — drops slider lag from ~50 ms to ~1 ms." \
  "" \
  "Add routes to main \`api.py\` router. Validate predictions against 287-bike sweep baseline."

echo

# ─── Phase 2: Cornering + lateral dynamics (Weeks 5–12) ───────────────
echo "--- Phase 2: Cornering + lateral dynamics (Wk 5–12) ---"

issue "Phase 2 milestone: Cornering + lateral dynamics (greenfield)" "P1,XL,epic,phase-2,physics" \
  "**Duration:** Weeks 5–12" \
  "**Priority:** Highest — biggest engineering lift, product-expanding" \
  "" \
  "Codebase audit confirmed: zero cornering code exists. No lateral velocity, no yaw, no combined-slip, no lean model." \
  "Existing Pacejka only evaluates longitudinal slip (κ). 69-tyre coefficient library, weight-transfer math, validation harness all reusable." \
  "" \
  "**Sub-tasks:**" \
  "- [ ] 2.1 State vector expansion (8 → 13 states)" \
  "- [ ] 2.2a Lateral Pacejka branch (F_y(α))" \
  "- [ ] 2.2b Combined-slip friction ellipse" \
  "- [ ] 2.2c Rider lean + steering model" \
  "- [ ] 2.2d Braking + corner-entry model" \
  "- [ ] 2.3 Track geometry schema + JSON layouts" \
  "" \
  "**Hard constraint:** 287-bike drag validation baseline must still pass within ±0.001 s after Phase 2 lands. Drag-only mode = 8-state RK4; full-track mode = 13-state RK4."

issue "2.1 State vector expansion to 13 states" "P1,M,phase-2,physics" \
  "Current (8-state): \`[x, v, ω_e, T_tire, T_clutch, P_boost, gear, clutch_locked]\`" \
  "New (13-state): add \`[y, v_lat, ψ (yaw), ψ̇ (yaw_rate), φ (lean_angle)]\`" \
  "" \
  "The RK4 integrator in \`physics.py\` already handles arbitrary state vectors — extend the derivative function, don't replace the solver." \
  "Add a \`mode\` flag to \`MotoQuantEngine\` — 'drag' (8-state) vs 'track' (13-state)." \
  "" \
  "Drag regression suite must pass unchanged."

issue "2.2a Lateral Pacejka branch" "P1,L,phase-2,physics" \
  "New submodel: \`motoquant/submodels/lateral_tire.py\`." \
  "\`F_y = D·sin(C·arctan(B·α − E·(B·α − arctan(B·α))))\`" \
  "" \
  "Initially derive lateral B/C/D/E from longitudinal coefficients with standard motorcycle ratios (F_y_peak ≈ 0.85 × F_x_peak)." \
  "Long-term: fit from actual tyre test data." \
  "" \
  "Add lateral_coefficients field to each of 69 tyres in the catalog."

issue "2.2b Combined-slip friction ellipse" "P1,M,phase-2,physics" \
  "Couple F_x and F_y via the friction ellipse: \`(F_x/F_x_max)² + (F_y/F_y_max)² ≤ 1\`." \
  "Use Milliken's approach or the Sakai combined-slip model." \
  "" \
  "This is the core of realistic track simulation — when braking hard into a corner, you can't also use full lateral grip." \
  "" \
  "Integrate with \`lateral_tire.py\` output and the existing Fx computation."

issue "2.2c Rider lean + steering model" "P1,L,phase-2,physics" \
  "New submodel: \`motoquant/submodels/lean_model.py\`." \
  "Counter-steering torque → roll rate → steady lean angle." \
  "Include rider CG offset from bike CG. Simplified gyroscopic precession for stability at speed." \
  "" \
  "Motorcycle-specific — replaces a car-like yaw model. Lean angle φ determines lateral force capacity."

issue "2.2d Braking + corner-entry model" "P1,M,phase-2,physics" \
  "New submodel: \`motoquant/submodels/corner_entry.py\`." \
  "Trail braking: progressive brake release as lean angle increases." \
  "Couple with existing longitudinal weight transfer + new lateral weight transfer." \
  "Fork dive changes trail → changes steering feel." \
  "" \
  "Existing \`braking.py\` handles force; add the corner-entry logic on top."

issue "2.3 Track geometry schema + JSON layouts" "P1,L,phase-2,physics,db" \
  "Create \`motoquant/track_geometry.py\`: \`TrackSegment\` and \`TrackLayout\` dataclasses." \
  "Extend venue schema with a segment list. Each segment: \`type\` (straight/corner), \`length_m\`, \`radius_m\`, \`banking_deg\`, \`elevation_change_m\`, \`surface_type\`, \`grip_modifier\`." \
  "" \
  "Backward-compatible: drag strips are single-segment layouts." \
  "" \
  "**Deliverables:**" \
  "- 5–10 real circuits pre-built: Phillip Island, Sachsenring, a kart track for testing, 2–3 Indian tracks" \
  "- \`test_data/tracks/*.json\` files" \
  "- \`tests/test_lateral.py\` with constant-radius cornering validation"

echo

# ─── Phase 3: Weather + surface + time-of-day (Weeks 13–16) ───────────
echo "--- Phase 3: Weather + surface + time-of-day (Wk 13–16) ---"

issue "Phase 3 milestone: Weather + surface + time-of-day realism" "P2,L,epic,phase-3,physics,backend" \
  "**Duration:** Weeks 13–16" \
  "**Priority:** Medium — builds on existing \`environmental.py\` + tyre thermal model" \
  "" \
  "Foundations already exist (\`environmental.py\`, VHT/PJ1 track prep, weather CLI, seasonal venue data). This phase adds depth." \
  "" \
  "**Sub-tasks:**" \
  "- [ ] 3.1 Surface evolution over passes" \
  "- [ ] 3.2 Track temp → tyre temp coupling" \
  "- [ ] 3.3 Humidity-dependent grip" \
  "- [ ] 3.4 Wind gust model" \
  "- [ ] 3.5 Real-time weather API (Open-Meteo)"

issue "3.1 Surface evolution over sessions" "P2,M,phase-3,physics" \
  "VHT/PJ1 multiplier is currently static. Make it dynamic: grip increases with pass count as rubber is laid down." \
  "Model: \`μ_surface(n) = μ_base + Δμ_rubber × (1 − exp(−k·n))\`." \
  "" \
  "Wire into existing \`track_prep\` multiplier in \`tire.py\`." \
  "Matters for drag — first run of the day vs pass #50 is measurably different."

issue "3.2 Track temp → tyre temp coupling" "P2,M,phase-3,physics" \
  "Tyre thermal model has Gaussian peak at ~65°C." \
  "Add track surface temperature as initial tyre condition and heat source during warm-up." \
  "" \
  "New function in \`environmental.py\`: \`solar_track_temp(time_of_day, ambient_temp, cloud_cover)\`." \
  "50°C afternoon track warms tyres faster than 20°C morning track."

issue "3.3 Humidity-dependent grip" "P2,S,phase-3,physics" \
  "Add to \`environmental.py\`:" \
  "- \`dew_point_grip_penalty(humidity, ambient_temp)\` → μ modifier near dew point" \
  "- Aquaplaning threshold for wet conditions" \
  "- Grip-degradation curve for damp surfaces"

issue "3.4 Wind gust model" "P2,S,phase-3,physics" \
  "\`aero.py\` already accepts a wind vector. Add stochastic gusts — Gaussian noise on steady-state wind." \
  "Configurable variance. For drag: head/tailwind affects trap speed. For track: crosswind as lateral disturbance."

issue "3.5 Real-time weather API integration" "P2,M,phase-3,backend" \
  "Create \`motoquant/weather_api.py\`: \`fetch_weather(lat, lon)\` using Open-Meteo (free, no key)." \
  "Cache 30 minutes per location. Auto-populate venue temp/humidity/wind/baro."

echo
echo "--- Phase 4: AI tuning intelligence (Wk 17–22) ---"

issue "Phase 4 milestone: AI tuning intelligence layer" "P1,XL,epic,phase-4,ai,backend" \
  "**Duration:** Weeks 17–22" \
  "**Priority:** High — product differentiator vs a simple physics simulator" \
  "" \
  "Three pillars: Bayesian optimization, local LLM reasoning, semantic search." \
  "" \
  "**Sub-tasks:**" \
  "- [ ] 4.1 Bayesian tuning optimizer (Optuna + surrogate)" \
  "- [ ] 4.2 Ollama integration (deepseek-r1:14b, llama3.2:3b, codellama:13b, nomic-embed-text)" \
  "- [ ] 4.3 Session vector DB (ChromaDB)" \
  "- [ ] 4.4 SHAP explainability" \
  "" \
  "All AI features degrade gracefully without Ollama."

issue "4.1 Bayesian tuning optimizer" "P1,L,phase-4,ai,backend" \
  "Create \`motoquant/ai/optimizer.py\` → \`BayesianTuner\` using Optuna." \
  "Param ranges: sprockets, tyre_pressure, launch_rpm, clutch_type, suspension_preload, aero_config." \
  "Objective: minimize ET via \`surrogate.predict()\`. Returns top-5 configs + confidence bounds." \
  "Supports constraints: \"only change gearing\" / \"NHRA Pro Stock rules\"."

issue "4.2 Ollama local-model integration" "P1,L,phase-4,ai,backend" \
  "Create \`motoquant/ai/advisor.py\` → \`OllamaAdvisor\` using \`httpx\` → \`localhost:11434\`." \
  "" \
  "Models:" \
  "- \`deepseek-r1:14b\` (~9 GB) — tuning advisor, chain-of-thought" \
  "- \`llama3.2:3b\` (~2 GB) — fast chat" \
  "- \`codellama:13b\` (~7 GB) — spec auto-generation" \
  "- \`nomic-embed-text\` (~274 MB) — embeddings" \
  "" \
  "Methods: \`explain_change\`, \`quick_answer\`. Fall back gracefully if Ollama isn't running."

issue "4.3 Session vector database (ChromaDB)" "P1,L,phase-4,ai,backend" \
  "Create \`motoquant/ai/session_search.py\`." \
  "Store every sim run as: config + weather + result + delta from previous." \
  "Embed into ChromaDB using nomic-embed-text." \
  "Query example: \"show configs where 60ft improved but trap didn't drop\" → similarity + metadata filter."

issue "4.4 SHAP explainability for surrogate" "P1,M,phase-4,ai,backend" \
  "Create \`motoquant/ai/explainer.py\` — SHAP wrapper for XGBoost surrogate." \
  "- \`feature_importance(config)\` → sorted (param, shap_value, direction)" \
  "- \`sensitivity_sweep(config, param_name, range)\` → ET curve as one param varies" \
  "" \
  "Expose as API routes. Tornado-chart UI in Phase 5." \
  "Add \`shap\` to requirements."

echo
echo "--- Phase 5: Frontend + platform hardening (Wk 23–28) ---"

issue "Phase 5 milestone: Frontend + platform hardening" "P2,XL,epic,phase-5,web,desktop,infra" \
  "**Duration:** Weeks 23–28" \
  "**Priority:** Medium — polish + production reliability" \
  "" \
  "**Sub-tasks:**" \
  "- [ ] 5.1a \`/build\` instant surrogate feedback" \
  "- [ ] 5.1b \`/simulator\` live telemetry (WebSocket)" \
  "- [ ] 5.2a \`/tuner\` AI command center (new)" \
  "- [ ] 5.2b \`/compare\` run analysis (new)" \
  "- [ ] 5.2c \`/track\` geometry editor (new, needs Phase 2)" \
  "- [ ] 5.3 Desktop Tauri ↔ Python handshake verified" \
  "- [ ] 5.4 CI/CD reseed-trap automation" \
  "- [ ] 5.5 First desktop release v0.1.0"

issue "5.1a /build instant surrogate feedback" "P2,M,phase-5,web" \
  "Wire BuildPage to \`/api/surrogate/predict\` (from Phase 1). Every slider change shows predicted ET <5 ms." \
  "Add diff vs current config, confidence bar, \"Optimize this\" button triggering Bayesian tuner (Phase 4)."

issue "5.1b /simulator live telemetry stream" "P2,L,phase-5,web,backend" \
  "Add WebSocket stream from sim engine. Real-time velocity, RPM, slip, tyre temp charts as sim runs." \
  "Side-by-side overlay with previous best. Add \`websockets\` to requirements."

issue "5.2a /tuner — AI command center (new page)" "P1,L,phase-5,web,ai" \
  "Depends on Phase 4:" \
  "- Chat panel (Ollama)" \
  "- Optimizer top-5 results" \
  "- SHAP tornado chart" \
  "- Sensitivity sweep charts" \
  "- Natural-language tuning advice"

issue "5.2b /compare — run analysis (new page)" "P2,L,phase-5,web" \
  "Side-by-side A-vs-B overlay: velocity, RPM, slip traces. Delta table. Session-history timeline with ChromaDB-powered search."

issue "5.2c /track — geometry editor (new page)" "P2,L,phase-5,web" \
  "Depends on Phase 2. Visual drag-drop track layout. Segments: radius, banking, surface. Minimap preview."

issue "5.3 Desktop Tauri ↔ Python handshake verification" "P1,M,phase-5,desktop" \
  "Audit flagged handshake as unverified. Verify + fix: Tauri shell plugin spawns \`python -m motoquant.run\`, IPC or local HTTP." \
  "Desktop needs offline mode — bundle surrogate + Ollama for local-only operation." \
  "End-to-end test macOS/Windows/Linux."

issue "5.4 CI/CD reseed-trap automation" "P1,M,phase-5,infra" \
  "Every PR touching \`motoquant/submodels/\` or \`known_bikes.py\` triggers:" \
  "- \`scripts/reseed_configs_from_specs.py\`" \
  "- \`scripts/validation_sweep.py\`" \
  "" \
  "Fail PR if any bike >0.001 s deviation from baseline. Add real-data import pipeline (timeslip OCR, Dynojet CSV, GPS overlay)."

issue "5.5 Cut first desktop release v0.1.0" "P1,L,phase-5,desktop,infra" \
  "1. Generate Ed25519 updater keypair" \
  "2. Paste pubkey into \`tauri.conf.json\`, privkey to GitHub Secrets" \
  "3. Replace placeholder icons with Fiverr designer asset" \
  "4. \`git tag v0.1.0 && git push --tags\`" \
  "" \
  "See \`docs/RELEASE.md\`."

echo
echo "--- Ongoing / deferred ---"

issue "Drop the phase plan doc into the repo" "P0,S,content" \
  "Commit \`docs/phase_plan.md\` as source of truth for the 28-week roadmap." \
  "Every phase-milestone issue links to the corresponding section."

issue "Reseed trap — document + PR checklist" "P0,S,infra,physics" \
  "Every physics change must run \`scripts/reseed_configs_from_specs.py\` afterwards." \
  "Add PR template checkbox: \"[ ] Ran reseed_configs_from_specs.py after physics changes\"." \
  "Automate in CI (see Phase 5.4)."

issue "Windows EV + Apple Developer signing certs" "P3-deferred,infra,desktop,launch-ops" \
  "Only after v0.1.0 produces a working unsigned binary." \
  "Windows EV ~\$400/yr (Sectigo) + Apple Developer ID \$99/yr."

issue "Pricing-page A/B test: ₹499 vs ₹799 monthly" "P3-deferred,web,launch-ops" \
  "After ≥50 weekly signups. Vercel Edge Config or 50/50 cookie split."

issue "Migrate motoquant.db to Railway persistent volume" "P3-deferred,infra" \
  "Move from git-tracked to volume + seed script. Removes repo bloat."

issue "Real cofounder avatars on /about" "P3-deferred,content,web" \
  "Replace \"A\"/\"H\" monograms with real 400×400 photos."

issue "Blog post: How the MotoQuant physics engine works" "P2,M,content" \
  "~1500 words, technical but accessible. Source from Arya's NIT-W CFD work + submodel docs."

issue "5 user-research calls with Pune/Narhe tuning shops" "P2,S,research" \
  "Script + Notion writeup. Feeds Phase 5 UX decisions."

issue "Validation spot-check: 10 Indian bikes vs real Dragy" "P2,S,physics,research" \
  "Real-user validation complementing the 78 published benchmarks."

echo
echo "=== Done. Issues created for launch-ops + 5 phases. ==="
echo
echo "Next steps:"
echo "  1. Go to https://github.com/$REPO/projects — 'New project' → 'Board'"
echo "  2. Add column per phase + 'Launch Ops' + 'In Progress' + 'Review' + 'Done'"
echo "  3. Bulk-filter by label (phase-1, phase-2, ...) → add items to matching columns"
echo "  4. Assign via gh or in the UI"
echo "  5. Share board URL with Arya"
echo
