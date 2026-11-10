# Known traps — bugs and gotchas that keep coming back

Institutional memory. Every entry here was hit at least once (some several
times) and cost real debugging time. Read this before a large change; it is
cheaper than rediscovering these. New contributor — model or human — this is
the "don't step here" map.

> Rule of thumb: *"Fix the same mistake twice, and it is a rule. Fix it three
> times, and it is a section in the docs."*

---

### T1 — Staging with `git add -A` pulls in unrelated WIP
The working tree often holds truncated files, CRLF drift, scratch scripts, and
parallel-session edits. **Always stage explicit paths.** `git status --short`
first and decide file by file.

### T2 — `motoquant.db` shows "modified" but nothing changed
Opening the seeded DB through the CLI or a test rewrites it. `git diff` flags
it as binary-modified with **no content change**. Verify row counts against
`HEAD`; if unchanged, `git checkout -- motoquant.db`. Never commit incidental DB
churn — it bloats the repo (the file is ~18 MB).

The mechanism (measured 2026-11-10): `MotoQuantDB.initialize()` re-runs its
`INSERT OR IGNORE` seed rows for venues, seasonal weather and part categories
on every open, and an ignored insert into an `AUTOINCREMENT` table still
consumes sequence numbers. So **every** CLI command on the default path, even
a read-only `bikes --search` or `sim`, moves three counters in
`sqlite_sequence` and nothing else. When you only want to look, point the CLI
at a copy: `cp motoquant.db /tmp/mq.db && python -m motoquant.run --db /tmp/mq.db …`.

### T3 — Physics/importer change without a reseed → silent DB-path drift
`/api/simulate?bike_id=N` reads stored `bike_configs` blobs, not live specs.
Change `spec_to_bike_config` / physics and skip
`scripts/reseed_configs_from_specs.py`, and the DB path diverges from the sweep
by seconds — invisible until a DB-vs-spec diff. See invariant I2.

### T4 — "Optimising" the ROI double-fetch breaks the repo seam
`compute_parts_roi` deliberately routes part application through
`parts_repo.apply_to_config` so test stubs / alternate repos stay in control.
Calling the concrete `bridge.apply_part_to_config` directly *looks* like a free
perf win (avoids one indexed `get`) but bypasses the seam and returns an empty
build for `FakeRepo`-style tests. It broke `test_parts_integrity` in PR #99 and
was reverted. Don't redo it. See invariant I4.

### T5 — `ruff check` clean ≠ `ruff format --check` clean
CI runs **both**. `ruff check` ignores line length (E501); `ruff format` still
re-wraps long lines. A PR that only ran `ruff check` can still fail the format
gate (it did in PR #99). Run `make fmt-check` (or just `make check`).

### T6 — pytest under `-n` (xdist) flakes ~15 DB-backed "Live" tests
`test_chat_resolver.py` "Live" resolver tests and a couple of route tests share
the seeded DB and env across xdist workers, so parallel runs show spurious
failures. **They all pass serially.** The authoritative run (and CI) is serial
(`make test`). Don't chase these as real bugs after a parallel run — re-run the
failing file serially to confirm.

### T7 — File-write tools can truncate large files
A `Write`/`Edit` on a big file can silently cut the tail (historically ~5–6 KB).
After any large write, `wc -l` the file and eyeball the last lines. If truncated,
rewrite via `cat > file <<'EOF'` (no size limit) or restore from
`git show HEAD:path`.

### T8 — Durable knowledge belongs in the docs, not in a session log
`CLAUDE.md` once held a nested, ever-growing session history, and every
"clean-up" lost part of it. It is now a short pointer to `AGENTS.md`. Put rules
in `AGENTS.md` / `INVARIANTS.md`, recurring bugs here, history in
`CHANGELOG.md`, and investigation write-ups in `reports/`.

### T9 — Vercel rejects unknown committer emails
A deploy fails with "commit author email is not valid" if the author email
isn't registered with a provider account. Commit with a real registered email
(the repo convention) — a bot/no-reply address can break the preview deploy.

### T10 — Headline counts drift across ~30 files on any catalog change
Changing the bike/part/tire/fitment/benchmark counts leaves stale numbers in
web pages, README, blog posts, docs, and the OG image. Run
`scripts/audit_headline_stats.py` (`make audit`) and patch every drift before
pushing. See invariant I6.

### T11 — Dead knobs: a config field written but never read
A parameter can be plumbed through config and appear "wired" while nothing in
the sim reads it (e.g. `power_boost_pct` was once a no-op on the small-cc path;
six inert `CategoryProfile` knobs were deleted on 2026-07-17). Before trusting a
knob, prove it moves ET with a quick sweep. When adding one, add a liveness test
that fails if the knob does nothing.

The 2026-07-25 audit's canonical example — `CategoryProfile.parasitic_mult`
wired but unreachable because every catalog config shipped
`dyno_curve.is_at_wheel=True` — was RESOLVED 2026-08-08 (synthetic catalog
curves now declare crank semantics, so the parasitic path is live). The
lesson stands: treat the "live knob" inventory as necessary but not
sufficient — a knob can be wired and still be unreachable for the data the
catalog actually carries. When auditing a knob, check reachability against
the real catalog rows, not just against a hand-built config.

### T12 — SQLite `LIMIT -1` is unbounded
A `limit` query param with only an upper bound (`le=100`, no `ge=1`) lets
`limit=-1` become `LIMIT -1` = dump the whole table. Every list route needs
`ge=1`. (Fixed on the two that were missed in PR #99; keep it that way for new
routes.)

### T13 — `cur.lastrowid == 0` misreads an ignored INSERT
After `INSERT OR IGNORE`, a fresh sqlite3 cursor's `lastrowid` is not reliably
`0` when the row was ignored — prefer `cur.rowcount == 0` as the "was ignored"
signal. This is import/seed-path code; change it carefully, it's guarded by
idempotency tests. (Fixed everywhere: `tire_repo` July 6, `bike_repo`/`venue_repo`
in the July-17 run. Kept as a trap because the misreading is easy to reintroduce.)

### T14 — One shared SQLite connection across request + job threads
`api.py` keeps a module-level `sqlite3` connection (`check_same_thread=False`)
reused by FastAPI request threads *and* `jobs.py` daemon workers. Reads are fine
on the single-worker Render deploy. No visitor request writes today, but any
future write route (or a job that writes) can interleave with another thread. This is the
#1 thing to fix before scaling to multiple workers — a per-thread/pooled
connection. (Deferred; documented in the roadmap.)

### T15 — Every config serialization path must round-trip `category_tag` (and any new top-level `BikeConfig` field)
Hit TWICE. July 2: the DB bridge dropped `category_tag` on the round-trip, so
44 bikes silently ran a different cluster profile on `/api/simulate` than the
sweep. July 13: `config_io` save/load dropped it AGAIN in the file-based twin
of the same bug — loaded bikes silently ran the `unknown` profile. The rule: a
new top-level `BikeConfig` field is not "wired" until EVERY serializer (DB
bridge, `config_io`, API DTOs) carries it. The gate: a round-trip test that
recursively diffs the full config (including the new field) on every path —
add it in the same session the field lands.

### T16 — Enum-ish string fields validate at construction or silently take a wrong branch
`boost_type` accepted any unknown string until July 13: the forced-induction
torque multiplier fell through to ×1.0 (zero boost) while the model still
applied the ×0.97 boosted-DA floor — a pure penalty masquerading as a turbo,
with no warning anywhere. The rule: any string field that selects a physics
or logic branch must raise at construction on unknown values, and the API must
return a 422 naming the offending part/field — never default silently. The
gate: a test that constructs with a bogus value and asserts the raise.

### T17 — Every new idempotent DB patch script joins the documented reseed chain the same session
Third occurrence July 13: `patch_2026_07_13_scrape_data.py` (282 reprices,
discontinued flags, tire-availability flags) was written, run, and proven
idempotent — but NOT appended to the documented reseed chain, so a fresh
reseed would silently drop all of it (real data loss, invisible until a
price/tire diff). Same shape as the seed-source resurrection closed July 4
(A3-15) and the July-6 patch trio. The rule: the session that lands a
`scripts/patch_*.py` also appends it to `RESEED_CHAIN` in the `Makefile`
(`make reseed` is the one written-out chain). The gate: re-prove the
FULL chain idempotent (×2) whenever a script is added.

### T18 — A catalog bike and a reference preset do not run in the same air
`/api/simulate` with `bike_id=1` and `python -m motoquant.run sim --bike-id 1`
answer about 0.1 s slower than the pinned 10.0436 s for the same K5. Nothing
is broken: a config loaded from the DB gets the default environment (Aamby
Valley, 679 m, 22 °C; see the `motoquant/database/bridge.py` docstring), while
`motoquant.gsxr1000_k5()` and the other two presets run at sea level, which is
what `scripts/check_baselines.py` pins. Before reporting a "baseline drift",
compare like with like: read the conditions the result states (the
`environment` block of an API result, the "Environment" section of the CLI
output), or use `make baselines`.

### T19 — ETs from before and after November 2026 are not the same quantity
Since the 2026-10/11 epoch every split is clocked from the 1-ft stage beam
(ET = t(402.336 m) − t(0.3048 m)); before it, from first motion. The same run
reads a few tenths quicker under the new convention with no change in the
bike (0.29 s on the reference K5). Do not compare a pre-epoch figure (an old
report, a blog table, a saved run) with a current sim, and do not score a
benchmark row without checking which convention its source used: the sweep
scores each row under its own convention for exactly this reason (the
`"timing": "row"` mode recorded in `reports/acc_final_2026_11_05.json`).

### T20 — "Obviously wrong data" is not a licence to change it without a sweep
The November 2026 audit confirmed that many small bikes carry implausibly tall
gearing (a litre-bike primary ratio used as a fallback). The obvious fix, an
inferred primary ratio, was built and swept: it made the weighted accuracy
*worse*, no physically plausible retune recovered it, and it was reverted
(`reports/session_2026_11_10_epoch.md`). The per-class knobs had been fitted
around the wrong gearing, so correcting one input alone un-centres the class.
The rule: a catalog-wide data rule ships only with the full weighted sweep as
evidence, and inferred values never replace missing sourced ones. Add
service-manual ratios bike by bike instead.

### T21 — The site build must not fetch anything from the network
The fonts are files in `web/app/fonts/`, loaded with `next/font/local`.
`next/font/google` downloads at build time, and that fetch failed CI twice.
Do not reintroduce it (or any other build-time download); `web-verify.yml`
runs `npm ci` + `next build` and should pass with no access beyond the npm
registry.

### T22 — In the web theme, `white` and `black` are not colours
`web/tailwind.config.js` maps `white` to the foreground ink and `black` to the
deepest background, so both **invert** in the light theme. `text-white` on a
coloured button turns dark-on-dark there. On an accent or solid colour fill
use the `on-accent` token; see `web/DESIGN.md`.

### T23 — Two web builds in one checkout clobber each other's `.next`
Parallel builds (a CI matrix, two contributors or agents on one tree) that
share `web/.next` fail in confusing ways. Give each its own output directory:
`NEXT_DIST_DIR=.next-<name> npm run build` (`web/next.config.js` reads it;
`.next-*/` is git-ignored). Unset, the build uses `.next`, which is what
Vercel expects.

### T24 — A redirected `pytest -q` log lags far behind the run
With stdout redirected to a file, `pytest -q` output is block-buffered: a log
that shows "2 %" can belong to a run that is 75 % done, and a silent log does
not mean a hung run. Check the process and its CPU time, or run with
`python -u -m pytest` / `-p no:cacheprovider -rfE` and read the summary at the
end, before concluding anything from a partial log.

### T25 — Docs drift silently; the docs-truth test is the gate
The docs have promised things the tree did not have: a `make` target that did
not exist, a CODEOWNERS path with no file behind it, a setup recipe that
installed no dependencies, a licence the repository does not use.
`tests/test_docs_truth_2026_11.py` now checks relative links, `make` targets,
CLI subcommands, CODEOWNERS patterns, packaging metadata, the licence and the
retired product wording across the live docs. When you rename a target, a
subcommand or a file, run it; when you add a doc that others will rely on,
add it to the test's list.
