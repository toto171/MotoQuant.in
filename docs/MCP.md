# The MotoQuant MCP server

`motoquant/mcp_server.py` exposes the drag-racing physics engine as
[Model Context Protocol](https://modelcontextprotocol.io) tools, so any MCP
client (Claude Desktop, Claude Code, …) can run simulations instead of
guessing from memory. A companion skill at
[`skills/motoquant/SKILL.md`](../skills/motoquant/SKILL.md) teaches a model
the terms it needs to use the tools well. The server is the P2 "distribution
channels" item in [ROADMAP.md](ROADMAP.md).

The server adds no production dependency. It is **stdlib-only**, speaks the
stdio transport directly and is not imported by `motoquant.api`.

---

## Quick start

### Claude Code

```bash
claude mcp add motoquant -- python -m motoquant.mcp_server
```

Or commit a `.mcp.json` at the repo root so everyone on the team gets it:

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

`python` must be an interpreter that can `import motoquant`: either the
repo's virtualenv (`/path/to/.venv/bin/python`) or a checkout installed with
`pip install -e .` (which also installs the runtime dependencies). HTTP mode
needs only the stdlib at runtime, so `pip install -e . --no-deps` is enough.

### Local (no network, full fidelity)

```json
{
  "mcpServers": {
    "motoquant": {
      "command": "/path/to/MotoQuant.in/.venv/bin/python",
      "args": ["-m", "motoquant.mcp_server", "--local"],
      "env": {
        "MOTOQUANT_DB": "/path/to/MotoQuant.in/motoquant.db"
      }
    }
  }
}
```

Local mode needs the runtime dependencies (`pip install -e .`, or
`pip install -r requirements-api.txt`), because it imports `motoquant.api`.

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
minutes of inactivity. The first call after it sleeps can take ~50 s while
the container boots. The client sees a slow tool, not an error: the default
timeout is 90 s, and `MOTOQUANT_MCP_TIMEOUT` changes it. A keep-alive cron
covers 00:00–18:00 UTC, so evening-IST calls are usually warm.

Local mode calls the *same* functions the HTTP routes call
(`_build_config`, `_apply_parts_to_config`, `_compare_impl`, …), so the two
backends cannot silently diverge. That is why `LocalBackend` imports
`motoquant.api` instead of re-deriving anything.

### Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `MOTOQUANT_API_URL` | `https://motoquant-api.onrender.com` | Hosted API base URL. Point it at `http://localhost:8000` to drive a local `make api`. |
| `MOTOQUANT_MCP_LOCAL` | unset | `1`/`true`/`yes` selects the in-process backend. |
| `MOTOQUANT_MCP_TIMEOUT` | `90` | HTTP timeout in seconds. |
| `MOTOQUANT_DB` | `motoquant.db` | Catalog path (local backend only). |

---

## Tools

There are nine tools. Each returns compact JSON with units in the field names
(`et_s`, `trap_kmh`, `price_inr`) and no time-series arrays, because model
context is scarce. `et_delta_s` is always *after − before*, so **negative
means faster**, as in the REST API and the CLI.

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
(`gsxr1000_k5`, `yzfr1_4c8` or `hayabusa_gen1`, the three hand-curated
reference bikes). Shared condition arguments: `rider_mass_kg`,
`power_boost_pct`, `mass_delta_kg`, `venue_id`, `ambient_temp_c`,
`humidity_pct`, `headwind_kmh`.

### `gearing_impact` and the two paths

The REST API has no gearing parameter, so the two backends get there
differently:

* The local backend sets `DrivetrainParams.front_sprocket` / `rear_sprocket`
  on a config built by the production builder and runs two full passes. It
  takes any tooth count in 8–30 front / 25–80 rear.
* The http backend expresses each tooth count as the catalog sprocket part
  that carries it (`param_overrides: {"drivetrain.front_sprocket": 16}`) and
  runs `/api/simulate/compare`. The catalog covers **front 13–18T, rear
  38–50T**. Anything outside that returns an error that lists what *is*
  available and points to local mode. Pass `bike_id` (not just a preset) so
  the fitment engine checks chain pitch.

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

Shorter gearing gains 0.057 s in the 60-foot and 0.068 s in ET, and costs
0.2 km/h of trap speed. It does not always help: run the same query on
the K5 preset and 17/42 → 17/47 *loses* 0.20 s, because a 178 hp
litre bike is limited by grip and shifting off the line, not by gearing.

---

## Protocol details (for maintainers)

* Transport: stdio, newline-delimited JSON-RPC 2.0 (MCP's stdio transport,
  *not* the LSP-style `Content-Length` framing). One JSON object per line on
  stdin, one response object per line on stdout. Diagnostics go to **stderr
  only**, because anything printed to stdout would corrupt the stream.
* Protocol versions: advertises `2025-06-18`, and echoes `2025-03-26` or
  `2024-11-05` back when a client asks for them.
* Capabilities: `tools` only (`listChanged: false`). `resources/*` and
  `prompts/*` answer `-32601 method not found`.
* Methods: `initialize`, `notifications/initialized`, `ping`, `tools/list`,
  `tools/call`. JSON-RPC batches are supported; notifications (no `id`) are
  never answered.

Implementers most often get the error split wrong. Protocol faults (bad
JSON, unknown method, non-object `params`) use the JSON-RPC `error` channel.
*Tool* failures (unknown bike id, incompatible part, unreachable API) come
back as a normal `result` with `isError: true` and a human-readable message, so the
model can read the problem and retry instead of the transport failing.

### Tests

`tests/test_mcp_server.py` drives the real stdio loop in-process with no
network: handshake, `tools/list` schema validation, `tools/call` in local mode
against a temp copy of `motoquant.db`, both `gearing_impact` paths (the HTTP
one served by a loopback stub), and every malformed-input branch. The gearing
test asserts that setup A at the K5's stock 17/42 reproduces the pinned
`10.0436 s` baseline. That proves the sprocket override goes through the
production config builder, not a parallel implementation.

```bash
python -m pytest tests/test_mcp_server.py -q
```

### Adding a tool

1. Write `_t_<name>(backend, args)` returning a compact dict.
2. Append an entry to `TOOLS` with `name`, `description`, `inputSchema`
   (`_schema(props, required)`) and `handler`.
3. Add a `tools/call` test. `tools/list` is validated generically, so a
   malformed schema fails the existing suite automatically.

State each tool's limits in its description. A model reads descriptions as
ground truth and will over-claim on your behalf.

---

## Limits

* Accuracy is **weighted mean |error| ≈ 0.25 s over 263 matched benchmarks**
  (`reports/acc_final_2026_11_10.json`). That is good enough to rank builds
  and answer what-if questions. It does not promise that a given bike will
  run an exact ET.
* Top-speed predictions are weaker than ET: over 83 matched top-speed
  benchmarks the mean |error| is ~13 km/h with a ~+7 km/h (sim fast) bias
  (`reports/acc_final_2026_11_10.json` `topspeed`).
* The parts catalog is Indian-market priced (INR) and does not cover engine
  internals (cams, big-bore). "Stage 3" is approximated with bolt-on power
  adders.
* Simulations assume a competent launch. There is no rider-skill knob.
* The hosted API is free but rate-limited per IP; heavy interactive or
  batch use should run local mode (or your own self-hosted instance, see
  [SELF_HOSTING.md](SELF_HOSTING.md)).
