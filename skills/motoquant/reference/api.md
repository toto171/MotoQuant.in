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
| `/api/health` | `{status, database, bike_count, engine}`. `engine` says which integrator is live (the Rust core or the Python reference; same numbers) and why. Also the wake-up call. |
| `/api/bikes` | `?search=&manufacturer=&category=&limit=&offset=`. Returns `{total, bikes:[{id, manufacturer, model, year, category, displacement_cc, peak_power_hp, dry_mass_kg}]}`. `total` respects the filters. |
| `/api/bikes/{id}` | Full spec sheet + config sub-blocks (aero `cd`, sprockets, `redline_rpm`, `tire_mu_peak`) + `tire_fitments`. 404 on an unknown id. |
| `/api/venues` | The 20 seeded strips with `altitude_m` and `surface_type`. |
| `/api/tires` | `?compound=&manufacturer=&limit=` (limit 1–5000). |
| `/api/parts` | `?bike_id=&category=&category_id=&search=&compatible_only=&limit=&fields=id&include_rules=`. **Pass `bike_id`** — each part is then checked against the bike's fitment rules (chain pitch, engine layout, displacement, stroke type). With `compatible_only=false` every part comes back annotated `{compatible, fitment_reason}` instead of filtered. `fields=id` returns just `{part_ids, total, bike_id, compatible_only}`: the cheap way to learn which parts fit a bike. `total` counts matching parts before `limit` slicing; `include_rules=true` adds each part's raw `fitment_rules` / `specifications`. |
| `/api/parts/categories` | Category list. |

### Simulation (POST, JSON body)

Every sim body identifies the bike with `bike_id` **or** `bike_preset`
(`gsxr1000_k5` / `yzfr1_4c8` / `hayabusa_gen1`; with neither, the K5 preset is
simulated, so always send one) and accepts the same build fields: `rider_mass_kg` (20–250, default 75), `power_boost_pct` (−50…200),
`mass_delta_kg` (−100…200), `part_ids` (at most 30), `front_tire_id`,
`rear_tire_id`. Out-of-range values are rejected with 422 instead of being
absorbed into a meaningless answer; an unknown bike, preset, venue or tire id
is a 404, never a silent default. `compare` takes `a_*` / `b_*` copies of the
build fields (`a_part_ids`, `b_rear_tire_id`, …) and shared conditions at the
top level.

#### Conditions

Every simulation, compare, optimizer, autotune and outlaw body (and their
`/api/jobs/*` variants) accepts the same optional conditions. All may be
omitted.

| Field | Range | Meaning |
|---|---|---|
| `venue_id` | a seeded venue id | Sets altitude and track surface from the venue (`GET /api/venues`). |
| `location` | text, ≤ 200 chars | A city or venue name ("Pune, IN"); resolved server-side. |
| `lat`, `lon` | −90…90, −180…180 | A point to resolve instead of a name. |
| `altitude_m` | −500…8000 | Explicit altitude. |
| `ambient_temp_c` | −30…60 | Air temperature. |
| `track_temp_c` | −30…80 | Track surface temperature. |
| `humidity_pct` | 0…100 | Relative humidity. |
| `pressure_hpa` | 800…1100 | Barometric pressure. |
| `headwind_kmh` | −200…200 | Sim, top-speed, distance and compare routes only; negative = tailwind. |

Precedence: `venue_id` sets altitude and surface first; a resolved `location`
or `lat` + `lon` then sets the environment; explicit values override both.

#### The `environment` block

Every result carries the conditions the engine actually ran, read back off the
config:

```json
{
  "name": "Default conditions",
  "is_default": true,
  "source": "default",
  "altitude_m": 679.0,
  "ambient_temp_c": 22.0,
  "track_temp_c": 30.0,
  "humidity_pct": 40.0,
  "pressure_hpa": 1013.25,
  "headwind_kmh": 0.0,
  "track_surface": "asphalt"
}
```

`source` is `"default"` (you passed no conditions), `"manual"` (you passed
explicit values; `name` is "Custom conditions") or `"venue"` (`name` is the
venue's). **Always read the values, not just the flag: "default" is not one
place.** A catalog bike (`bike_id`) defaults to the conditions stored with the
catalog (Aamby Valley: 679 m, 22 °C, 40 % humidity), while the three presets
default to sea level (0 m, 25 °C, 50 %). The same K5 therefore answers about
0.1 s apart as `bike_id: 1` and as `bike_preset: "gsxr1000_k5"`. When you
report a number, say which conditions it is for. The optimizer, autotune and
outlaw results also carry `environment_source`, saying how the conditions were
chosen.

`parts_applied` lists `{id, name, brand, price_inr}` for each part that took
effect; `parts_skipped` lists the requested ids that were ignored because they
are not in the catalog (or failed to apply), and `build_cost_inr` totals the
applied ones. A non-empty `parts_skipped` means the answer is not for the
build you asked about: say so.

**The simulation routes do not check fitment.** A part id that exists but does
not fit the bike is applied as if it did (a Hayabusa exhaust on a GSX-R1000
returns a quicker time and no warning). Get the fitting ids first with
`GET /api/parts?bike_id=N&fields=id` and only send those. (The optimizer and
outlaw routes choose from fitting parts themselves.)

#### Routes

All times are clocked from the 1-ft stage beam (see "Rollout" in
`glossary.md`).

| Endpoint | Body extras | Returns |
|---|---|---|
| `POST /api/simulate/quick` | — | `{et_quarter_s, trap_speed_kmh, et_60ft_s, et_eighth_s, bike_name, peak_power_hp, total_mass_kg, parts_applied, parts_skipped, build_cost_inr, environment, stock_et_s, et_delta_s}`. **The workhorse.** `stock_et_s` / `et_delta_s` are null unless parts were applied (`et_delta_s` = with parts − without; negative = quicker). |
| `POST /api/simulate` | `use_adaptive_dt` | `{et_quarter_s, trap_speed_kmh, trap_speed_ms, splits{60ft_s, 330ft_s, 660ft_s, 1000ft_s, 1320ft_s}, environment, parts_applied, parts_skipped, build_cost_inr, bike, config}` plus a `timeseries` block of about 1,000 points (`t_s`, `v_kmh`, `x_m`, `rpm`, `gear`, `accel_g`, `traction_pct`, `tire_temp_c`, `power_kw`, `F_drive_N`, `F_drag_N`). Accepts `part_ids` like every sim route. |
| `POST /api/simulate/top-speed` | `max_time_s` (0.1–120), `include_timeseries` | Terminal velocity in m/s, km/h and mph; time and distance to reach it; `reached_plateau`; terminal gear, RPM, power; LSR splits; `parts_applied`, `parts_skipped`, `build_cost_inr`, `environment`. |
| `POST /api/simulate/distance` | `distance_m` (longer than the 0.3048 m rollout, ≤ 20000), `max_time_s` (0.1–300) | Arbitrary-distance run, for land-speed events: `{distance_m, time_s, trap_speed_ms, trap_speed_kmh, trap_speed_mph, peak_velocity_kmh, bike_name, peak_power_hp, total_mass_kg, parts_skipped, environment}`. |
| `POST /api/simulate/compare` | `a_*` and `b_*` copies of the build fields, shared conditions at the top level | `{a, b, environment, delta:{et_s, trap_kmh, faster, cost_diff_inr}}`. Each of `a` / `b` is a build summary (`et_quarter_s`, `trap_speed_kmh`, `et_60ft_s`, `et_eighth_s`, `parts_applied`, `parts_skipped`, `build_cost_inr`, `timeseries`). `delta` is B − A (negative `et_s` = B quicker). Runs two sims. |
| `POST /api/chat` | `query`, `messages`, `mode` | The agentic chat — 15 tools, multi-step. |
| `POST /api/jobs/{simulate\|topspeed\|compare\|optimize\|autotune\|outlaw\|chat}` | same bodies | Returns `{job_id}`; poll `GET /api/jobs/{id}` for `{status, progress, stage, result}` and `POST /api/jobs/{id}/cancel` to stop. Use for anything slow. |

`POST /api/optimize/build` (best parts for a budget: `budget_inr`, `goal`
`min_et` | `max_trap`, `profile` `all` | `street_legal` | `drag_prep` |
`full_race`, `rider_weight_kg`), `POST /api/autotune/ecu` (conditions-aware
gearing and setup advisor: `rider_weight_kg`, `gear_span`, `launch_steps`) and
the composed `POST /api/jobs/outlaw` are free like everything else. They are
slow (tens of seconds), so prefer their `/api/jobs/*` variants. `budget_inr`
null or 0 means no limit. All three take the conditions above and echo what
they used in `environment` and `environment_source`.

### Deltas and rate limits

- Public `delta_et_s` / `et_delta_s` is **after − before**: negative = faster.
- `*_gain_s` fields are positive-is-good. Do not mix the two conventions.
- Everything is free and anonymous; there is no quota. Compute-heavy routes
  carry per-IP rate limits and answer **HTTP 429** with `Retry-After` when
  tripped (chat also has a daily per-IP cap). Back off and retry later rather
  than looping.

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
# → 10.0436008056, pinned bit-identical
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

- **`AGENTS.md` first**, then `docs/ARCHITECTURE.md`.
- **The three pinned baselines are load-bearing.** K5 10.0436 / R1 10.1092 /
  Hayabusa 10.1100, bit-identical. After touching `physics.py`,
  `submodels/*`, `defaults.py`, `category_profiles.py` or
  `scraper/importer.py`, run `make baselines`.
- `make check` (fast gate) → `make test` (full suite) before any PR.
- After a `spec_to_bike_config` or physics change, re-seed the DB blobs or
  `/api/simulate?bike_id=N` silently diverges from the sweep path.
- Never `git add -A`; never commit incidental `motoquant.db` churn.
- Accuracy claims sitewide come from one file — the latest
  `reports/acc_final_*.json`. Quote it, do not estimate.
