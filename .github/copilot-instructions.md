# GitHub Copilot instructions

This repo's working contract is **[../AGENTS.md](../AGENTS.md)**. Read it first.
It is model-agnostic and authoritative for every AI tool and human.

The one rule you must never break: the three reference bikes (GSX-R 1000 K5
10.0436 s, YZF-R1 4C8 10.1092 s, Hayabusa Gen1 10.1100 s) are pinned
**bit-identical**. After any change to `motoquant/physics.py`, `submodels/*`,
`defaults.py`, `category_profiles.py`, or `scraper/importer.py`, run
`make baselines`. See `docs/INVARIANTS.md`.

Before opening a PR, run `make check` then `make test`. AGENTS.md has the full
details and `docs/KNOWN_TRAPS.md` lists recurring pitfalls.

MotoQuant is free and open source (Apache-2.0, `docs/adr/0006-open-source-pivot.md`):
never add paywalls, tier gates, usage quotas or licence keys. Protect
expensive routes with a per-IP `rate_limit(...)` fuse instead.
