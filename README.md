# MotoQuant

> *The physics of faster.* A free, open-source motorcycle drag-racing simulator.

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![CI](https://github.com/toto171/MotoQuant.in/actions/workflows/ci.yml/badge.svg)](https://github.com/toto171/MotoQuant.in/actions/workflows/ci.yml)
[![Web](https://img.shields.io/badge/web-motoquant.in-orange)](https://www.motoquant.in)

MotoQuant predicts a motorcycle's quarter-mile time, finish-line speed and top
speed from first principles, then answers the questions riders and tuners
ask: what does this sprocket, exhaust or tyre do to my launch, and which
upgrade buys a tenth of a second for the least money?

Use it in the browser at **[motoquant.in](https://www.motoquant.in)**, from
Python or the command line, or run your own copy. It was built for the Indian
drag-racing scene (Aamby Valley, MMRT, BIC, Kari, Hyderabad) and works for any
bike at any strip. Everything here is free under the
[Apache License 2.0](LICENSE).

## What it does

- It simulates the run. Engine torque, clutch slip, tyre grip and heat,
  weight transfer, wheelies, aerodynamics and the density of the air are
  integrated every millisecond (RK4, 15 sub-models, Python and NumPy). An
  optional [Rust core](docs/RUST_CORE.md) gives bit-identical results about
  40 times faster, natively or in the browser through WebAssembly.
- It knows the bikes: 534 bikes, 546 parts, 254 tyres and 20 venues ship
  in a seeded SQLite file (`motoquant.db`). A compatibility engine shows a
  part only for the bikes it fits.
- It gives advice: cost per tenth for every part, a budget-constrained
  upgrade planner, a race-day setup for the day's air (gearing, launch RPM,
  tyre pressure), sensitivity analysis, and a chat assistant that runs the
  simulations for you.
- It checks itself against your data: import a Dragy run, a dyno sheet or
  an ECU log and compare it with the simulation.
- It plugs into other tools: a CLI, a FastAPI backend, the Next.js site and
  an [MCP server](docs/MCP.md) that lets AI assistants call the simulator.

## How accurate it is

The simulator is checked against 250 published quarter-mile tests (magazine
road tests, instrumented GPS runs and timeslips), matched to 263 catalog
bikes. Weighted by how trustworthy each source is, the simulated time is off
by **0.25 s** on average, with a bias of **+0.02 s**; 130 matches land within
0.20 s. The figures come from `reports/acc_final_2026_11_10.json`, and every
benchmark with its source is on
[motoquant.in/validation](https://www.motoquant.in/validation).

Accuracy is uneven, and the project says so. Sport bikes do best (litre bikes
average 0.15–0.17 s). Small bikes are the weakest class, because few instrumented
tests exist for them and their catalog gearing is still inferred. Published
gearing for 53 of them was measured and made the fit worse until the
small-bike settings are re-tuned, so it is recorded but not applied
([`reports/gearing_experiment_2026_11_10.md`](reports/gearing_experiment_2026_11_10.md)).
Top speed is less accurate than quarter-mile time.

Three reference bikes are pinned bit-identical and gated in CI:
GSX-R 1000 K5 **10.0436 s**, YZF-R1 4C8 **10.1092 s** and Hayabusa Gen1
**10.1100 s** at sea level ([docs/INVARIANTS.md](docs/INVARIANTS.md)).

## Quick start

You need Python 3.10 or newer, and Node 18 or newer for the website.

```bash
git clone https://github.com/toto171/MotoQuant.in.git
cd MotoQuant.in
make install      # the package with its runtime and developer dependencies
make check        # lint, format, the reference-time gate and fast tests (about 3 minutes)
```

`make` on its own lists every target. The repository ships the full catalog,
so there is no database to set up.

One simulation from Python:

```python
import motoquant

engine = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5())
print(f"{engine.run().time_quarter:.4f} s")  # 10.0436
```

The command line works on any catalog bike at any venue:

```bash
python -m motoquant.run bikes --search hayabusa              # find a bike id
python -m motoquant.run sim --bike-id 1 --venue-id 1         # GSX-R 1000 K5 at Aamby Valley
python -m motoquant.run parts --bike-id 3 --impact 56        # what one part does
python -m motoquant.run analysis recommend --bike-id 1 --budget 150000
```

The CLI rewrites the database file it opens even when no data changes, so
point it at a copy (`cp motoquant.db /tmp/mq.db`, then `--db /tmp/mq.db`) or
undo the change with `git checkout -- motoquant.db`.

Run the website locally:

```bash
make api          # API on http://localhost:8000 (every route documented at /docs)
make web-install  # once
make web-dev      # site on http://localhost:3000, using the local API
```

To host your own copy, follow [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md).
No setting is required; keys for chat, live weather and error tracking are
optional.

## How you can help

The most useful contribution is data, and none of it needs code:

- [Submit a timeslip](https://github.com/toto171/MotoQuant.in/issues/new?template=submit-timeslip.yml).
  A Dragy run or a timing-light slip for a stock bike is the single best way
  to improve accuracy, above all for bikes under 400 cc.
- [Suggest a bike](https://github.com/toto171/MotoQuant.in/issues/new?template=suggest-bike.yml)
  that is missing, with a link to its specifications.
- [Send a dyno sheet or ECU log](https://github.com/toto171/MotoQuant.in/issues/new?template=calibration_data.yml).

Code is welcome too. Read [AGENTS.md](AGENTS.md) (the working rules, one
page) and [CONTRIBUTING.md](CONTRIBUTING.md), then look for issues labelled
`good first issue`. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md)
and report security problems privately as described in
[SECURITY.md](SECURITY.md).

## Where things are

```
motoquant/              the Python package
  physics.py              RK4 integrator (fixed 1 ms or adaptive step)
  submodels/              the 15 physics sub-models
  category_profiles.py    per-class physics settings
  database/               schema, seed data, repositories
  scraper/                the curated bike catalog and the spec importer
  calibration/            Dragy, dyno and ECU import and comparison
  analysis/               cost per tenth, upgrade planner, race-day setup, sensitivity
  llm/                    the chat assistant
  api.py                  FastAPI backend
  run.py                  command line (python -m motoquant.run)
web/                    the Next.js site (motoquant.in)
rust/                   the optional Rust physics core
tests/                  the test suite
scripts/                sweeps, the reference-time gate, database patches, audits
docs/                   architecture, invariants, decisions, self-hosting
reports/                accuracy sweeps and investigation write-ups
```

[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) answers "where does X live?",
[docs/adr/](docs/adr/) records settled decisions and
[docs/README.md](docs/README.md) indexes the rest.

## License and names

MotoQuant is licensed under the **Apache License, Version 2.0**; see
[LICENSE](LICENSE) and [NOTICE](NOTICE). The licence covers the code and
data, not the MotoQuant name or logo. Motorcycle, tyre and parts names are
trademarks of their owners and are used only to identify the products being
modelled. Benchmark figures are cited facts from their published sources.

Copyright 2026 Hritwik Mudhai and the MotoQuant contributors.
