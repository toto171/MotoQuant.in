# MotoQuant surfaces without the MCP server

Read this when the MCP server is not connected, or when you are working
inside the repo. Base URL for the hosted API:

```
https://motoquant-api.onrender.com
```

It runs on Render's free tier and sleeps after 15 minutes idle — the first
request after a nap can take **~50 s**. That is a cold start, not an outage.
Interactive OpenAPI docs live at `/docs`.

## REST endpoints

### Catalog (GET, no auth)

| Endpoint | Notes |
|---|---|
| `/api/health` | `{status, database, bike_count}`. Also the wake-up call. |
| `/api/bikes` | `?search=&manufacturer=&category=&limit=&offset=`. Returns `{total, bikes:[{id, manufacturer, model, year, category, displacement_cc, peak_power_hp, dry_mass_kg}]}`. `total` respects the filters. |
| `/api/bikes/{id}` | Full spec sheet + config sub-blocks (aero `cd`, sprockets, `redline_rpm`, `tire_mu_peak`) + `tire_fitments`. 404 on an unknown id. |
| `/api/venues` | The 20 seeded strips with `altitude_m` and `surface_type`. |
| `/api/tires` | `?compound=&manufacturer=&limit=` (limit 1–5000). |
| `/api/parts` | `?bike_id=&category=&category_id=&search=&compatible_only=&limit=&fields=id&include_rules=`. **Pass `bike_id`** — each part is then checked against the bike's fitment rules (chain pitch, engine layout, displacement, stroke type). With `compatible_only=false` every part comes back annotated `{compatible, fitment_reason}` instead of filtered. `fields=id` returns just `{part_ids, total, bike_id, compatible_only}` — the cheap way to learn which parts fit a bike. `total` counts matching parts before `limit` slicing; `include_rules=true` adds each part's raw `fitment_rules` / `specifications`. |
| `/api/parts/categories` | Category list. |
| `/api/leaderboard`, `/api/runs/{id}` | Saved public runs / a shareable timeslip. |

### Simulation (POST, JSON body)

Every sim body identifies the bike with `bike_id` **or** `bike_preset`
(`gsxr1000_k5` / `yzfr1_4c8` / `hayabusa_gen1`) and accepts the same
conditions: `rider_mass_kg` (20–250, default 75), `power_boost_pct`
(−50…200), `mass_delta_kg` (−100…200), `part_ids` (at most 30),
`front_tire_id`, `rear_tire_id`, `venue_id`, and the manual overrides
`ambient_temp_c` (−30…60), `track_temp_c` (−30…80), `humidity_pct` (0–100),
`headwind_kmh` (−200…200). Out-of-range values are rejected with 422 rather
than absorbed into a meaningless answer; an unknown bike, preset, venue or
tyre id is a 404, never a silent default. `compare` takes `a_*` / `b_*` copies
of the per-build fields (`a_part_ids`, `b_rear_tire_id`, …) and shared
conditions at the top level.

Every sim result carries an `environment` block — the conditions the engine
actually ran, read back off the config: `{name, is_default, source
("default" | "manual" | "venue"), altitude_m, ambient_temp_c, track_temp_c,
humidity_pct, pressure_hpa, headwind_kmh, track_surface}`. When
`is_default` is true you passed no venue or manual conditions — the answer is
for the server's sea-level defaults, so say so. `parts_applied` lists
`{id, name, brand, price_inr}` for each part that took effect; `parts_skipped`
lists the ids that were ignored (unknown id, or not fitting the bike), and
`build_cost_inr` totals the applied ones.

| Endpoint | Body extras | Returns |
|---|---|---|
| `POST /api/simulate/quick` | — | `{et_quarter_s, trap_speed_kmh, et_60ft_s, et_eighth_s, bike_name, peak_power_hp, total_mass_kg, parts_applied, parts_skipped, build_cost_inr, environment, stock_et_s, et_delta_s}`. ~50 ms. **The workhorse.** `stock_et_s` / `et_delta_s` are null unless parts were applied (`et_delta_s` = with parts − without, negative = quicker). |
| `POST /api/simulate` | `use_adaptive_dt` | `{et_quarter_s, trap_speed_kmh, trap_speed_ms, splits{60ft_s, 330ft_s, 660ft_s, 1000ft_s, 1320ft_s}, environment, parts_applied, parts_skipped, build_cost_inr, bike, config}` plus a `timeseries` block (about 1,000 points: `t_s`, `v_kmh`, `x_m`, `rpm`, `gear`, `accel_g`, `traction_pct`, `tire_temp_c`, `power_kw`, `F_drive_N`, `F_drag_N`). Accepts `part_ids` like every sim route. |
| `POST /api/simulate/top-speed` | `max_time_s` (0.1–120), `include_timeseries` | Terminal velocity in m/s, km/h and mph; time and distance to reach it; `reached_plateau`; terminal gear, RPM, power; LSR splits; `parts_applied`, `parts_skipped`, `build_cost_inr`, `environment`. With `include_timeseries` the series is decimated to at most 2,000 points (first, last and peak kept) and rounded for plotting. |
| `POST /api/simulate/distance` | `distance_m` (>0, ≤20000), `max_time_s` (≤300) | Arbitrary-distance run, for land-speed events: `{distance_m, time_s, trap_speed_*, peak_velocity_kmh, bike_name, parts_skipped, environment}`. |
| `POST /api/simulate/compare` | `a_*` and `b_*` copies of the fields above, shared conditions at the top level | `{a, b, environment, delta:{et_s, trap_kmh, faster, cost_diff_inr}}`; each of `a` / `b` is a build summary with splits, `parts_applied` and `parts_skipped`. `delta` is B − A (negative = B quicker). Runs two sims. |
| `POST /api/chat` | `message`, `messages` | The agentic chat — 15 tools, multi-step. |
| `POST /api/jobs/{simulate\|topspeed\|compare\|optimize\|autotune\|outlaw\|chat}` | same bodies | Returns `{job_id}`; poll `GET /api/jobs/{id}` for `{status, progress, stage, result}` and `POST /api/jobs/{id}/cancel` to stop. Use for anything slow. |

`POST /api/optimize/build` (best parts for a budget), `POST /api/autotune/ecu`
(conditions-aware gearing and setup advisor) and the composed
`POST /api/jobs/outlaw` are open like every other route. They are slow (tens
of seconds), so prefer their `/api/jobs/…` variants. All three accept the
optional conditions block `location` (city or venue text), `venue_id`, `lat` /
`lon`, `altitude_m`, `ambient_temp_c`, `track_temp_c`, `humidity_pct` and
`pressure_hpa`; a resolved location sets the environment first and explicit
values override it. `budget_inr` null / 0 means no limit; the response echoes
the conditions used in `environment` and `environment_source`.

### Deltas and limits

- Public `delta_et_s` / `et_delta_s` is **after − before**: negative = faster.
- `*_gain_s` fields are positive-is-good. Do not mix the two conventions.
- There are no tiers, accounts are optional, and there is no usage quota. Every
  expensive route has a per-IP rate limit; a `429` means back off and retry.

### There is no gearing parameter

No sim route accepts sprocket teeth. Two ways to express a gearing change
over HTTP:

1. **Catalog sprockets** — find parts whose `param_overrides` contain
   `drivetrain.front_sprocket` / `drivetrain.rear_sprocket` at the counts you
   want (`GET /api/parts?bike_id=N&category=sprocket`), then run
   `/api/simulate/compare` with those `part_ids` on each side. The catalog
   covers front 13–18T and rear 38–50T.
2. **Locally** — build the config and set the two fields directly. This is
   what the MCP server's local backend does, and it accepts any tooth count.

## Python / CLI (inside the repo)

```python
import motoquant

et = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5()).run().time_quarter
# → 9.9330563825, pinned bit-identical
```

```bash
python -m motoquant.run bikes --search hayabusa
python -m motoquant.run sim --bike-id 11 --venue-id 3
python -m motoquant.run parts --bike-id 11 --impact 56        # ET delta + ₹/tenth
python -m motoquant.run analysis roi --bike-id 11 --budget 200000 --optimize
python -m motoquant.run analysis recommend --bike-id 11 --profile drag_prep
python -m motoquant.run nl "optimize my Hayabusa for 35C at Aamby Valley"
python -m motoquant.run venues                                # add --detail ID
python -m motoquant.run calibrate import-dragy run.csv --best
```

Running the MCP server itself:

```bash
python -m motoquant.mcp_server --selftest          # handshake check, no network
MOTOQUANT_MCP_LOCAL=1 python -m motoquant.mcp_server
```

## Repo conventions worth knowing

- **`AGENTS.md` first**, then `docs/ARCHITECTURE.md`. `CLAUDE.md` is a long
  session changelog — skim only its top entry.
- **The three pinned baselines are load-bearing.** K5 9.9331 / R1 10.1436 /
  Hayabusa 10.3633, bit-identical. After touching `physics.py`,
  `submodels/*`, `defaults.py`, `category_profiles.py` or
  `scraper/importer.py`, run `make baselines`.
- `make check` (fast gate) → `make test` (full suite) before any PR.
- After a `spec_to_bike_config` or physics change, re-seed the DB blobs or
  `/api/simulate?bike_id=N` silently diverges from the sweep path.
- Never `git add -A`; never commit incidental `motoquant.db` churn.
- Accuracy claims sitewide come from one file — the latest
  `reports/acc_final_*.json`. Quote it, do not estimate.
