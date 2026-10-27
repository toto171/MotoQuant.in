# MCP.md — the MotoQuant MCP server

> *"Ask your AI what 16/45 vs 16/47 does to your 60-foot."*

`motoquant/mcp_server.py` exposes the drag-racing physics engine as
[Model Context Protocol](https://modelcontextprotocol.io) tools, so any MCP
client (Claude Desktop, Claude Code, …) can run real simulations instead of
guessing from memory. It is the P2 "distribution channels" item in
[ROADMAP.md](ROADMAP.md), and it ships with a companion skill at
[`skills/motoquant/SKILL.md`](../skills/motoquant/SKILL.md) that teaches a
model the vocabulary to drive it well.

Nothing here is a new production dependency: the server is **stdlib-only**,
speaks the stdio transport directly, and is not imported by `motoquant.api`.

---

## Quick start

### Claude Code

```bash
claude mcp add motoquant -- python -m motoquant.mcp_server
```

…or commit a `.mcp.json` at the repo root so the whole team gets it:

```json
{
  "mcpServers": {
    "motoquant": {
      "command": "python",
      "args": ["-m", "motoquant.mcp_server"]
    }
  }
}
```

### Claude Desktop

Edit `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`,
Windows: `%APPDATA%\Claude\`) and restart the app:

```json
{
  "mcpServers": {
    "motoquant": {
      "command": "python",
      "args": ["-m", "motoquant.mcp_server"],
      "env": {
        "MOTOQUANT_API_URL": "https://motoquant-api.onrender.com"
      }
    }
  }
}
```

`python` must be a interpreter that can `import motoquant` — either the repo's
virtualenv (`/path/to/.venv/bin/python`) or a checkout installed with
`pip install -e .`. In HTTP mode nothing beyond the stdlib is needed at
runtime, so a bare `pip install -e . --no-deps` is enough.

### Local (no network, full fidelity)

```json
{
  "mcpServers": {
    "motoquant": {
      "command": "/path/to/MotoQuant_v1/.venv/bin/python",
      "args": ["-m", "motoquant.mcp_server", "--local"],
      "env": {
        "MOTOQUANT_DB": "/path/to/MotoQuant_v1/motoquant.db"
      }
    }
  }
}
```

Local mode needs `pip install -r requirements-api.txt` (it imports
`motoquant.api` so the MCP tools and the REST routes cannot drift apart).

### Verify without a client

```bash
python -m motoquant.mcp_server --selftest      # handshake + tools/list, no network
python -m motoquant.mcp_server --local --selftest
```

---

## Backends

| | `http` (default) | `local` (`MOTOQUANT_MCP_LOCAL=1` / `--local`) |
|---|---|---|
| Talks to | hosted API at `MOTOQUANT_API_URL` | this checkout's `motoquant.db` |
| Needs | Python stdlib only | `requirements-api.txt` + the DB |
| Latency | ~0.3 s warm, **up to ~50 s on a cold start** | ~50 ms–2 s |
| `gearing_impact` | catalog sprockets only (see below) | any tooth count |
| Rate limits | the hosted API's per-IP fuses apply (HTTP 429 when tripped) | none |

The hosted backend runs on Render's **free tier**, which sleeps after 15
minutes of inactivity. The first call after a nap can take ~50 s while the
container boots — the client sees a slow tool, not an error (the default
timeout is 90 s, tunable with `MOTOQUANT_MCP_TIMEOUT`). A keep-alive cron
covers 00:00–18:00 UTC, so evening-IST calls are usually warm.

Local mode calls the *same* functions the HTTP routes call
(`_build_config`, `_apply_parts_to_config`, `_compare_impl`, …), so the two
backends cannot silently diverge — that is the whole reason `LocalBackend`
imports `motoquant.api` instead of re-deriving anything.

### Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `MOTOQUANT_API_URL` | `https://motoquant-api.onrender.com` | Hosted API base URL. Point it at `http://localhost:8000` to drive a local `make api`. |
| `MOTOQUANT_MCP_LOCAL` | unset | `1`/`true`/`yes` selects the in-process backend. |
| `MOTOQUANT_MCP_TIMEOUT` | `90` | HTTP timeout in seconds. |
| `MOTOQUANT_DB` | `motoquant.db` | Catalog path (local backend only). |

---

## Tools

Nine tools. Every result is compact JSON with units in the field names
(`et_s`, `trap_kmh`, `price_inr`) — no time-series arrays, because model
context is the scarce resource. **`et_delta_s` is always *after − before*, so
negative means faster**, matching the REST API and the CLI.

| Tool | Arguments | Returns |
|---|---|---|
| `search_bikes` | `query`, `manufacturer`, `category`, `limit` | Catalog ids + headline specs. Start here. |
| `get_bike` | `bike_id` | Full spec sheet, gearing, OEM tires, any published benchmark ET on record. |
| `simulate_quarter_mile` | bike + conditions + `part_ids` | `et_s`, `trap_kmh`, `et_60ft_s`, `et_eighth_s` (+ stock delta when parts are fitted). |
| `simulate_top_speed` | bike + conditions + `part_ids` | Terminal velocity km/h + mph, time/distance to reach it, gear and RPM. |
| `compare_bikes` | `a_*` / `b_*` + shared conditions | Both sides plus the ET/trap delta and a winner. |
| `list_venues` | — | The 20 seeded strips with altitude + surface (feeds density altitude). |
| `search_parts` | `bike_id`, `category`, `query`, `limit` | Catalog parts, fitment-filtered when `bike_id` is given. |
| `part_impact` | bike + `part_id` | Stock vs modified ET, trap delta, cost per tenth in INR. |
| `gearing_impact` | bike + `front_a`/`rear_a`/`front_b`/`rear_b` | Both setups' ET, trap and 60-foot, plus the delta. |

Bike selection is `bike_id` (from `search_bikes`) or `bike_preset`
(`gsxr1000_k5`, `yzfr1_4c8`, `hayabusa_gen1` — the three hand-curated
reference bikes). Shared condition arguments: `rider_mass_kg`,
`power_boost_pct`, `mass_delta_kg`, `venue_id`, `ambient_temp_c`,
`humidity_pct`, `headwind_kmh`.

### `gearing_impact` and the two paths

The REST API has no gearing parameter, so the two backends get there
differently:

* **local** — sets `DrivetrainParams.front_sprocket` / `rear_sprocket` on a
  config built by the production builder and runs two full passes. Any tooth
  count in 8–30 front / 25–80 rear.
* **http** — expresses each tooth count as the catalog sprocket part that
  carries it (`param_overrides: {"drivetrain.front_sprocket": 16}`) and runs
  `/api/simulate/compare`. The catalog covers **front 13–18T, rear 38–50T**;
  anything outside that returns an honest error listing what *is* available
  and pointing at local mode. Pass `bike_id` (not just a preset) so the
  fitment engine checks chain pitch.

The `method` field in the result says which path produced the numbers.

---

## Worked example

> "My R15 V4 runs 14/48. What happens if I go to 52 on the rear?"

`search_bikes(query="R15 V4")` → id 81, then
`gearing_impact(bike_id=81, front_a=14, rear_a=48, front_b=14, rear_b=52)`:

```json
{
  "a": {"final_drive_ratio": 3.4286, "et_s": 18.83,   "et_60ft_s": 3.1323, "trap_kmh": 119.65},
  "b": {"final_drive_ratio": 3.7143, "et_s": 18.7617, "et_60ft_s": 3.0755, "trap_kmh": 119.44},
  "delta": {"et_s": -0.0683, "et_60ft_s": -0.0568, "trap_kmh": -0.21, "faster": "B"}
}
```

Shorter gearing buys 0.057 s of 60-foot and 0.068 s of ET, and costs 0.2 km/h
of trap. **This direction is not universal** — run the same query on the K5
preset and 17/42 → 17/47 *loses* 0.20 s, because a 178 hp litre bike is
grip- and shift-limited off the line, not gearing-limited. That is exactly
why this is a tool and not a rule of thumb.

---

## Protocol details (for maintainers)

* **Transport**: stdio, newline-delimited JSON-RPC 2.0 (MCP's stdio transport
  — *not* the LSP-style `Content-Length` framing). One JSON object per line on
  stdin, one response object per line on stdout. Diagnostics go to **stderr
  only**; anything printed to stdout would corrupt the stream.
* **Protocol versions**: advertises `2025-06-18`, and echoes `2025-03-26` or
  `2024-11-05` back when a client asks for them.
* **Capabilities**: `tools` only (`listChanged: false`). `resources/*` and
  `prompts/*` correctly answer `-32601 method not found`.
* **Methods**: `initialize`, `notifications/initialized`, `ping`,
  `tools/list`, `tools/call`. JSON-RPC batches are supported; notifications
  (no `id`) are never answered.
* **Error split** (the one thing implementers get wrong): protocol faults —
  bad JSON, unknown method, non-object `params` — use the JSON-RPC `error`
  channel. *Tool* failures (unknown bike id, incompatible part, unreachable
  API) come back as a normal `result` with `isError: true` and a human-readable
  message, so the model can read the problem and retry instead of the
  transport blowing up.

### Tests

`tests/test_mcp_server.py` drives the real stdio loop in-process with zero
network: handshake, `tools/list` schema validation, `tools/call` in local mode
against a **temp copy** of `motoquant.db`, both `gearing_impact` paths (the
HTTP one served by a loopback stub), and every malformed-input branch. The
gearing test asserts that setup A at the K5's stock 17/42 reproduces the pinned
`9.9331 s` baseline — proof the sprocket override rides the production config
builder rather than a parallel implementation.

```bash
python -m pytest tests/test_mcp_server.py -q
```

### Adding a tool

1. Write `_t_<name>(backend, args)` returning a compact dict.
2. Append an entry to `TOOLS` with `name`, `description`, `inputSchema`
   (`_schema(props, required)`) and `handler`.
3. Add a `tools/call` test. `tools/list` is validated generically, so a
   malformed schema fails the existing suite automatically.

Keep descriptions honest about limits — a model reads them as ground truth
and will happily over-claim on your behalf.

---

## Honest limits

* Accuracy is **weighted mean |error| ≈ 0.26 s over 276 matched benchmarks**
  (`reports/acc_final_2026_08_08.json`). Good for ranking builds and answering
  what-ifs; not a promise that a given bike will run an exact ET.
* Top-speed predictions are weaker than ET: over 83 matched top-speed
  benchmarks the mean |error| is ~28 km/h and the fleet still carries a
  ~+24 km/h bias after the speed-limiter and gearing passes
  (`reports/sweep_topspeed_2026-08-08.json`).
* The parts catalog is Indian-market priced (INR) and does not cover engine
  internals (cams, big-bore) — "stage 3" is approximated with bolt-on power
  adders.
* Simulations assume a competent launch. There is no rider-skill knob.
* The hosted API is free but rate-limited per IP; heavy interactive or
  batch use should run local mode (or your own self-hosted instance, see
  [SELF_HOSTING.md](SELF_HOSTING.md)).
