# CLAUDE.md

Claude Code reads this file at the start of a session. The rules for working
on MotoQuant are the same for every contributor and every tool, so they live
in **[AGENTS.md](AGENTS.md)**. Read it before your first edit.

The three things that most often go wrong:

1. **The pinned reference times must not move.** After any change to
   `motoquant/physics.py`, `motoquant/submodels/`, `defaults.py`,
   `category_profiles.py` or `scraper/importer.py`, run `make baselines`.
   GSX-R 1000 K5 10.0436 s, YZF-R1 4C8 10.1092 s and Hayabusa Gen1 10.1100 s
   are bit-identical or the change is a regression.
2. **`motoquant.db` is tracked.** Opening it through the CLI or a test can
   rewrite it without changing any data. Work on a copy
   (`--db /tmp/mq.db`) and never commit unintended database changes.
3. **Stage files by name.** Never `git add -A` or `git add .`.

Where things are: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). What must
never break: [docs/INVARIANTS.md](docs/INVARIANTS.md). Bugs that keep coming
back: [docs/KNOWN_TRAPS.md](docs/KNOWN_TRAPS.md). The loop:

```bash
make health   # state of the repository
make check    # lint, format, baselines and fast tests (about 3 minutes)
make test     # the full suite, before you open a pull request
```
