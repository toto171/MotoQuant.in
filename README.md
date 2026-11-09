# MotoQuant

> *The physics of faster.*

[![CI](https://github.com/toto171/MotoQuant.in/actions/workflows/ci.yml/badge.svg)](https://github.com/toto171/MotoQuant.in/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Web](https://img.shields.io/badge/web-motoquant.in-orange)](https://motoquant.in)

MotoQuant is an open-source, first-principles physics engine for motorcycle
quarter-mile drag racing: predict elapsed time and trap speed from a bike's
specs, test modifications (power, gearing, tires, weight, parts) before you
spend money, and rank parts by seconds gained per rupee. It started in the
Indian drag-racing community (Aamby Valley, MMRT, BIC, Kari, Hyderabad) and
models 541 bikes, 254 tires, 593 parts, and 20 venues. Predictions are
validated against 250 published benchmarks (weighted mean |Δ| 0.263 s, bias
+0.007 s across 276 matched runs) by a ~4,400-test pytest suite.

MotoQuant is free software released under the [MIT license](LICENSE).

## What you can do with it

- **Use the hosted site** — [motoquant.in](https://motoquant.in): simulator,
  build optimizer, ECU autotune, AI chat, shareable timeslips, accuracy
  explorer. No payment, no quota; accounts are optional and only used to save
  runs to your garage.
- **Use the Python package / CLI** — `python -m motoquant.run …`: simulate,
  search the catalog, rank parts, run sensitivity analysis, import Dragy /
  dyno / ECU logs.
- **Run the FastAPI backend** — every capability of the site is an HTTP
  endpoint (OpenAPI docs at `/docs`).
- **Plug it into your AI** — a stdio MCP server (`python -m motoquant.mcp_server`,
  see [docs/MCP.md](docs/MCP.md)) and a Claude skill under `skills/motoquant/`.

## Quickstart

Requires Python 3.10+ (and Node 18+ only if you want the web app).

```bash
git clone https://github.com/toto171/MotoQuant.in.git
cd MotoQuant.in

make install          # runtime + dev deps, editable package
make baselines        # confirm the three pinned reference bikes are bit-identical
make                  # list every target
```

The repo ships a seeded `motoquant.db`, so everything below works immediately.

Run one simulation from Python (stock GSX-R 1000 K5, sea-level defaults):

```python
import motoquant

engine = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5())
result = engine.run()
print(f"{result.time_quarter:.4f} s")  # 9.9331
```

…or from the CLI, for a catalog bike at a venue:

```bash
python -m motoquant.run bikes --search hayabusa        # find a bike id
python -m motoquant.run sim --bike-id 1 --venue-id 1   # K5 at Aamby Valley
python -m motoquant.run --help                         # all subcommands
```

Start the API and the website locally:

```bash
make api              # FastAPI on :8000  (docs at http://localhost:8000/docs)
make web-install      # once
make web-dev          # Next.js on :3000, pointed at the local API
```

Optional: the AI chat needs an LLM provider key (see
[docs/CHAT_AGENT.md](docs/CHAT_AGENT.md)); `python -m motoquant.run nl "…"` is the
keyless regex fallback.

## Accuracy

The three hand-curated reference bikes are pinned **bit-identical** and gated
in CI ([docs/INVARIANTS.md](docs/INVARIANTS.md) I1):

| Bike | Pinned ET |
|---|---|
| Suzuki GSX-R 1000 K5 | **9.9331 s** |
| Yamaha YZF-R1 4C8 | **10.1436 s** |
| Suzuki Hayabusa Gen1 | **10.3633 s** |

Across the full benchmark corpus the weighted mean |Δ| is 0.263 s (bias
+0.007 s, 276 matched runs); the 10 cleanest validated runs agree within
about ±0.007 s. Small-displacement bikes are data-limited rather than
model-limited — real instrumented timeslips are the most valuable thing you can
contribute (see [CONTRIBUTING.md](CONTRIBUTING.md)). The site's
[/validation](https://motoquant.in/validation) page shows every comparison.

## Project layout

```
motoquant/    Python package: physics engine, submodels, DB layer, calibration,
              analysis, scraper/importer, LLM agent, MCP server, FastAPI app, CLI
web/          Next.js site (motoquant.in)
tests/        pytest suite
scripts/      validation sweeps, DB patches, health/baseline checks
docs/         architecture, invariants, known traps, ADRs, runbooks
```

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (module map and
data-flow — *where does X live?*). The deploy shape is documented in
[docs/RENDER_MIGRATION.md](docs/RENDER_MIGRATION.md): API on Render
(`render.yaml`, Docker), frontend on Vercel with a `/api/*` rewrite.

A few root files (`DISPATCH_*.md`, `STATUS.md`, `NEXT_SESSION.md`,
`AUTONOMOUS_PAUSED`, `CLAUDE.md`) are session-handoff notes from the
AI-assisted development workflow; you can ignore them when contributing.

## Contributing

Contributions are welcome — code, bike specs, benchmark timeslips, parts data,
docs. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) (the
one-page working contract), then [docs/ONBOARDING.md](docs/ONBOARDING.md). The
fast gate is `make check`; the full suite is `make test`. Please follow the
[Code of Conduct](CODE_OF_CONDUCT.md); report vulnerabilities privately per
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 The MotoQuant Authors.
