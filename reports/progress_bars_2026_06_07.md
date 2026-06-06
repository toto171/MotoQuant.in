# Real progress bars for all website simulations — 2026-06-07

Operator request: replace the rotating spinner animations on the website with
real progress bars for quick sim, full sim, top speed, autotune, and the build
optimiser ("it looks cheap"). Follow-up request mid-session: a way to run the
quick sim manually instead of automatically → Live/Manual toggle (default Live).

## Backend
- `motoquant/jobs.py` (new): in-memory job registry. Daemon-thread execution,
  `progress(frac, stage)` callback, monotonic clamped progress, TTL 15 min,
  MAX_JOBS 200, MAX_RUNNING 6 (429 on overflow), error strings bounded to 500
  chars (a full-timeseries "Config error" once produced a 75 KB payload).
- `api.py`: sync route bodies extracted into `_simulate_impl/_topspeed_impl/
  _optimize_impl/_autotune_impl(req, progress=None)`; sync routes unchanged in
  behaviour. New: POST `/api/jobs/{simulate|topspeed|autotune|optimize}` (202 +
  job_id), GET `/api/jobs/{id}` → {status, progress, stage, result|error}.
- `physics.py`: `run(progress_cb=None, progress_every_steps=250)` reports
  `max(x/distance, t/max_time)`; `run_top_speed` passes it through. Pure
  observer — ET bit-identical with/without callback; K5/R1/Hayabusa Δ+0.0000.
- `ecu_autotune.py`: `on_sim` hooks on the gearing/launch sweep helpers +
  stage-labelled ticker in `autotune(progress_cb=)`.
- `build_optimizer.py`: `SurrogatePredictor.on_predict` hook (exception-proof)
  + per-candidate ticker in `optimize_build(progress_cb=)`.

## Web
- `components/SimProgress.js` (new): determinate % bar / staged sweep with an
  honest "waking the simulation engine" cold-start message after 4 s; compact
  (nav chip) and edge (card top) variants; ARIA + prefers-reduced-motion.
- `lib/api.js`: `startJob/getJob/runJob` (350 ms poll; 404/405 → sync-route
  fallback for deploy skew + the desktop sidecar) + `autotuneEcuJob`/
  `optimizeBuildJob`; sync helpers refactored onto shared body builders.
- Simulator page: full sim + top speed run as jobs with live % (nav chip, run
  buttons, top-speed panel); boot screen counts the 5 data fetches as real
  progress; upload spinner → bar; **Live/Manual toggle** for the auto quick-sim
  (Manual shows a "Run quick sim" button). Quick sim itself stays synchronous
  (~50 ms warm — a job round-trip would slow it down).
- Landing SimulatorWidget: top-speed via job (real %), quick sim staged; the
  rotating conic-gradient overlay is now a slim top-edge progress bar.
- EcuAutotune + BuildOptimizer: job-backed bars with backend stage text
  ("Sweeping gearing", "Scoring candidate parts", …) + live % in the button.

## Verification
- `tests/test_jobs_api.py` (new, 9 tests): registry lifecycle / clamp /
  truncation / capacity, engine-callback monotonicity + bit-identical ET on the
  K5 baseline, jobs routes end-to-end incl. stages and 404.
- test_validation 57 + jobs 9 green in-sandbox; test_api / test_build_optimizer
  / test_ecu_autotune green except 2 PRE-EXISTING surrogate failures that fail
  identically on the pristine origin tree (sandbox lacks sklearn/xgboost).
- Baselines: K5 10.0334 / R1 10.2859 / Hayabusa 10.4712, Δ+0.0000 ×3.
- `cd web && next build`: ✓ Compiled, 74/74 static pages (run twice, second
  including the Live toggle). ruff check + format clean on all touched py.
- Headline audit: unchanged (only the 2 documented 600cc-blog drifts remain).

## Notes
- FUSE working tree had api.py / physics.py / ecu_autotune.py /
  build_optimizer.py TRUNCATED (documented Cowork file-write bug, leftover from
  the earlier Jun-7 session); restored from origin before patching.
- Render free tier keeps jobs in a single process — registry is in-memory by
  design; a restart mid-job surfaces as a clear "run again" error client-side.
