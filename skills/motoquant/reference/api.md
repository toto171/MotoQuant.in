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
| `/api/tires` | `?compound=&manufacturer=&limit=`. |
| `/api/parts` | `?bike_id=&category=&search=&compatible_only=&limit=`. **Pass `bike_id`** — each part is then checked against the bike's fitment rules (chain pitch, engine layout, displacement, stroke type). With `compatible_only=false` every part comes back annotated `{compatible, fitment_reason}` instead of filtered. |
| `/api/parts/categories` | Category list. |
| `/api/leaderboard`, `/api/runs/{id}` | Saved public runs / a shareable timeslip. |

### Simulation (POST, JSON body)

Every sim body identifies the bike with `bike_id` **or** `bike_preset`
(`gsxr1000_k5` / `yzfr1_4c8` / `hayabusa_gen1`) and accepts the same
conditions: `rider_mass_kg` (20–250, default 75), `power_boost_pct`
(−50…200), `mass_delta_kg` (−100…200), `venue_id`, `ambient_temp_c`,
`track_temp_c`, `humidity_pct`, `headwind_kmh`, `rear_tire_id`. Out-of-range
values are rejected with 422 rather than absorbed into a meaningless answer.

| Endpoint | Body extras | Returns |
|---|---|---|
| `POST /api/simulate/quick` | `part_ids: [int]` | `{et_quarter_s, trap_speed_kmh, et_60ft_s, et_eighth_s, bike_name, peak_power_hp, total_mass_kg, parts_applied, build_cost_inr, stock_et_s, et_delta_s}`. ~50 ms. **The workhorse.** |
| `POST /api/simulate` | `use_adaptive_dt` | Everything above plus all five splits and 100 Hz time-series arrays (`v_kmh`, `rpm`, `gear`, `accel_g`, `traction_pct`, …). No `part_ids` on this route. |
| `POST /api/simulate/top-speed` | `part_ids`, `max_time_s` (0.1–300), `include_timeseries` | Terminal velocity in m/s, km/h and mph; time and distance to reach it; terminal gear, RPM, power; LSR splits. |
| `POST /api/simulate/distance` | `distance_m` | Arbitrary-distance run, for land-speed events. |
| `POST /api/simulate/compare` | `a_*` and `b_*` copies of the fields above, shared conditions at the top level | `{a, b, delta:{et_s, trap_kmh, faster, cost_diff_inr}}`. Metered as two sims. |
| `POST /api/chat` | `message`, `messages` | The agentic chat — 15 tools, multi-step. |
| `POST /api/jobs/{simulate\|topspeed\|compare\|optimize\|autotune\|outlaw\|chat}` | same bodies | Returns `{job_id}`; poll `GET /api/jobs/{id}` for `{status, progress, stage, result}` and `POST /api/jobs/{id}/cancel` to stop. Use for anything slow. |

`POST /api/optimize/build` (knapsack build optimizer under a budget) and
`POST /api/autotune/ecu` (conditions-aware gearing + launch-RPM advisor) exist
but are **Pro-tier gated**. Do not present them as freely available.

### Deltas and metering

- Public `delta_et_s` / `et_delta_s` is **after − before**: negative = faster.
- `*_gain_s` fields are positive-is-good. Do not mix the two conventions.
- Anonymous sims are metered on the free tier (`X-Sims-Remaining` header).
  `/api/simulate/quick` is deliberately unmetered so slider UIs work.

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
