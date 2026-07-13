# GitHub Copilot instructions

This repo's working contract is **[../AGENTS.md](../AGENTS.md)** — read it first.
It is model-agnostic and authoritative for every AI tool and human.

The one rule you must never break: the three reference bikes (GSX-R 1000 K5
9.9331 s, YZF-R1 4C8 10.1436 s, Hayabusa Gen1 10.3633 s) are pinned
**bit-identical**. After any change to `motoquant/physics.py`, `submodels/*`,
`defaults.py`, `category_profiles.py`, or `scraper/importer.py`, run
`make baselines`. See `docs/INVARIANTS.md`.

Before opening a PR: `make check` then `make test`. Full details in AGENTS.md,
recurring pitfalls in `docs/KNOWN_TRAPS.md`.
