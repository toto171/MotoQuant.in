# Known traps

Bugs and gotchas that keep coming back. Each one has been hit at least once,
some several times, and each cost real debugging time. Read this before a
large change; it is cheaper than finding them again.

### T1: Staging with `git add -A` pulls in unrelated work in progress
The working tree often holds truncated files, CRLF drift, scratch scripts and
edits from parallel sessions. Stage explicit paths: run `git status --short`
first and decide file by file.

### T2: `motoquant.db` shows "modified" but nothing changed
Opening the seeded DB through the CLI or a test rewrites it. `git diff` flags
it as a modified binary with no change to its content. Compare row counts
with `HEAD`; if they match, `git checkout -- motoquant.db`. Never commit
incidental DB churn: the file is about 18 MB, and it bloats the repo.

The cause (measured 2026-11-10): `MotoQuantDB.initialize()` re-runs its
`INSERT OR IGNORE` seed rows for venues, seasonal weather and part categories
on every open, and an ignored insert into an `AUTOINCREMENT` table still
consumes sequence numbers. So every CLI command on the default path, even a
read-only `bikes --search` or `sim`, moves three counters in
`sqlite_sequence` and nothing else. When you only want to look, point the CLI
at a copy: `cp motoquant.db /tmp/mq.db && python -m motoquant.run --db /tmp/mq.db …`.

### T3: A physics or importer change without a reseed makes the DB path drift
`/api/simulate?bike_id=N` reads stored `bike_configs` blobs, not live specs.
Change `spec_to_bike_config` or the physics without running
`scripts/reseed_configs_from_specs.py`, and the DB path drifts from the sweep
by seconds. Nothing shows it until someone diffs the DB against the specs.
See invariant I2.

### T4: "Optimising" the ROI double fetch breaks the repo seam
`compute_parts_roi` routes part application through
`parts_repo.apply_to_config` on purpose, so test stubs and alternate repos
stay in control. Calling the concrete `bridge.apply_part_to_config` directly
looks like a free speed-up (it saves one indexed `get`), but it bypasses the
seam and returns an empty build for `FakeRepo`-style tests. It broke
`test_parts_integrity` in PR #99 and was reverted. Don't redo it. See
invariant I4.

### T5: Passing `ruff check` does not mean passing `ruff format --check`
CI runs both. `ruff check` ignores line length (E501), but `ruff format`
still re-wraps long lines, so a PR that ran only `ruff check` can fail the
format gate. PR #99 did. Run `make fmt-check`, or `make check`.

### T6: Under pytest `-n` (xdist), about 15 DB-backed "Live" tests flake
The "Live" resolver tests in `test_chat_resolver.py` and a couple of route
tests share the seeded DB and environment across xdist workers, so parallel
runs show spurious failures. They all pass serially. The authoritative run
is serial (`make test`), and so is CI. After a parallel run, re-run the failing file
serially before you treat a failure as a real bug.

### T7: File-write tools can truncate large files
A `Write` or `Edit` on a big file can silently cut the tail (historically
around 5–6 KB). After any large write, run `wc -l` on the file and read the
last lines. If it was truncated, rewrite it with `cat > file <<'EOF'` (no
size limit) or restore it from `git show HEAD:path`.

### T8: Durable knowledge belongs in the docs, not in a session log
`CLAUDE.md` once held a nested session history that kept growing, and every
clean-up lost part of it. It is now a short pointer to `AGENTS.md`. Put rules
in `AGENTS.md` or `INVARIANTS.md`, recurring bugs here, history in
`CHANGELOG.md`, and investigation write-ups in `reports/`.

### T9: Vercel rejects unknown committer emails
A deploy fails with "commit author email is not valid" when the author email
is not registered with a provider account. Commit with a real registered
email (the repo convention). A bot or no-reply address can break the preview
deploy.

### T10: A catalog change leaves stale headline counts in about 30 files
A change to the bike, part, tire, fitment or benchmark counts leaves old
numbers in web pages, README, blog posts, docs and the OG image. Run
`scripts/audit_headline_stats.py` (`make audit`) and fix every drift before
you push. See invariant I6.

### T11: Dead knobs, written to the config but never read
A parameter can be plumbed through config and look wired while nothing in
the sim reads it. `power_boost_pct` was once a no-op on the small-cc path,
and six inert `CategoryProfile` knobs were deleted on 2026-07-17. Before you
trust a knob, prove with a quick sweep that it moves ET. When you add one,
add a liveness test that fails if the knob does nothing.

A knob can also be wired and still unreachable for the data the catalog
carries. The 2026-07-25 audit found `CategoryProfile.parasitic_mult` wired
but unreachable, because every catalog config shipped
`dyno_curve.is_at_wheel=True`. That was fixed on 2026-08-08: synthetic
catalog curves now declare crank semantics, so the parasitic path is live. A
"live knob" inventory is necessary but not sufficient. When you audit a knob,
check reachability against the real catalog rows, not only against a
hand-built config.

### T12: SQLite `LIMIT -1` is unbounded
A `limit` query parameter with only an upper bound (`le=100`, no `ge=1`) lets
`limit=-1` become `LIMIT -1`, which dumps the whole table. Every list route
needs `ge=1`. The two routes missed in PR #99 are fixed; keep it that way for
new routes.

### T13: `cur.lastrowid == 0` misreads an ignored INSERT
After `INSERT OR IGNORE`, a fresh sqlite3 cursor's `lastrowid` is not
reliably `0` when the row was ignored. Use `cur.rowcount == 0` to detect an
ignored row. This is import and seed code, guarded by idempotency tests, so
change it carefully. It is fixed everywhere (`tire_repo` on July 6,
`bike_repo` and `venue_repo` in the July 17 run) and stays listed because the
misreading is easy to bring back.

### T14: One SQLite connection is shared by request and job threads
`api.py` keeps a module-level `sqlite3` connection (`check_same_thread=False`)
that FastAPI request threads and the `jobs.py` daemon workers both use. Reads
are fine on the single-worker Render deploy. No visitor request writes today,
but a future write route, or a job that writes, can interleave with another
thread. Moving to a per-thread or pooled connection is the first job before
scaling to more than one worker. It is deferred and listed in the roadmap.

### T15: Every config serialization path must round-trip `category_tag` (and any new top-level `BikeConfig` field)
This has been hit twice. On July 2 the DB bridge dropped `category_tag` on the
round-trip, so 44 bikes silently ran a different cluster profile on
`/api/simulate` than in the sweep. On July 13 `config_io` save and load
dropped it again, the file-based twin of the same bug, and loaded bikes
silently ran the `unknown` profile.

Rule: a new top-level `BikeConfig` field is not wired until every serializer
(DB bridge, `config_io`, API DTOs) carries it. Gate: a round-trip test that
recursively diffs the full config, new field included, on every path. Add it
in the same change as the field.

### T16: An enum-like string field validates at construction, or it silently takes the wrong branch
Until July 13, `boost_type` accepted any unknown string. The forced-induction
torque multiplier fell through to ×1.0 (no boost) while the model still
applied the ×0.97 boosted-DA floor: a pure penalty that looked like a turbo,
with no warning anywhere.

Rule: a string field that selects a physics or logic branch must raise at
construction on an unknown value, and the API must return a 422 that names
the offending part or field. It never falls back to a default silently. Gate:
a test that constructs with a bogus value and asserts the raise.

### T17: A new idempotent DB patch script joins the documented reseed chain in the same change
Third occurrence, July 13: `patch_2026_07_13_scrape_data.py` (282 reprices,
discontinued flags, tire-availability flags) was written, run and proven
idempotent, but not added to the documented reseed chain. A fresh reseed would
silently drop all of it, a real data loss that nothing shows until a price or
tire diff. The seed-source resurrection closed on July 4 (A3-15) and the July
6 patch trio had the same shape.

Rule: the change that adds a `scripts/patch_*.py` also appends it to
`RESEED_CHAIN` in the `Makefile` (`make reseed` is the one written-out chain).
Gate: whenever a script is added, prove the full chain idempotent again by
running it twice.

### T18: A catalog bike and a reference preset do not run in the same air
`/api/simulate` with `bike_id=1` and `python -m motoquant.run sim --bike-id 1`
answer about 0.1 s slower than the pinned 10.0436 s for the same K5. Nothing
is broken. A config loaded from the DB gets the default environment (Aamby
Valley, 679 m, 22 °C; see the `motoquant/database/bridge.py` docstring),
while `motoquant.gsxr1000_k5()` and the other two presets run at sea level,
which is what `scripts/check_baselines.py` pins. Before you report a
"baseline drift", compare like with like: read the conditions the result
states (the `environment` block of an API result, the "Environment" section
of the CLI output), or use `make baselines`.

### T19: ETs from before and after November 2026 are not the same quantity
Since the 2026-10/11 epoch every split is clocked from the 1-ft stage beam
(ET = t(402.336 m) − t(0.3048 m)); before it, splits ran from first motion.
The same run reads a few tenths quicker under the new convention with no
change to the bike (0.29 s on the reference K5). Do not compare a pre-epoch
figure (an old report, a blog table, a saved run) with a current sim. Do not
score a benchmark row without checking which convention its source used. The
sweep scores each row under its own convention for this reason (the
`"timing": "row"` mode recorded in `reports/acc_final_2026_11_05.json`).

### T20: "Obviously wrong data" is not a licence to change it without a sweep
The November 2026 audit confirmed that many small bikes carry implausibly tall
gearing (a litre-bike primary ratio used as a fallback). The obvious fix, an
inferred primary ratio, was built and swept. It made the weighted accuracy
worse, no physically plausible retune recovered it, and it was reverted
(`reports/session_2026_11_10_epoch.md`). The per-class knobs had been fitted
around the wrong gearing, so correcting one input alone un-centres the class.
Rule: a catalog-wide data rule ships only with the full weighted sweep as
evidence, and inferred values never replace missing sourced ones. Add
service-manual ratios bike by bike instead.

### T21: The site build must not fetch anything from the network
The fonts are files in `web/app/fonts/`, loaded with `next/font/local`.
`next/font/google` downloads at build time, and that fetch failed CI twice.
Do not bring it back, or any other build-time download. `web-verify.yml` runs
`npm ci` and `next build`, and should pass with no network access beyond the
npm registry.

### T22: In the web theme, `white` and `black` are not colours
`web/tailwind.config.js` maps `white` to the foreground ink and `black` to the
deepest background, so both invert in the light theme. `text-white` on a
coloured button turns dark-on-dark there. On an accent or solid colour fill,
use the `on-accent` token; see `web/DESIGN.md`.

### T23: Two web builds in one checkout clobber each other's `.next`
Parallel builds (a CI matrix, or two contributors or agents on one tree) that
share `web/.next` fail in confusing ways. Give each build its own output
directory: `NEXT_DIST_DIR=.next-<name> npm run build` (`web/next.config.js`
reads it; `.next-*/` is git-ignored). Unset, the build uses `.next`, which is
what Vercel expects.

### T24: A redirected `pytest -q` log lags far behind the run
With stdout redirected to a file, `pytest -q` output is block-buffered. A log
that shows "2 %" can belong to a run that is 75 % done, and a silent log does
not mean a hung run. Check the process and its CPU time, or run with
`python -u -m pytest` / `-p no:cacheprovider -rfE` and read the summary at the
end, before you conclude anything from a partial log.

### T25: Docs drift silently, and the docs-truth test is the gate
The docs have promised things the tree did not have: a `make` target that did
not exist, a CODEOWNERS path with no file behind it, a setup recipe that
installed no dependencies, a licence the repository does not use.
`tests/test_docs_truth_2026_11.py` now checks relative links, `make` targets,
CLI subcommands, CODEOWNERS patterns, packaging metadata, the licence and the
retired product wording across the live docs. Run it when you rename a
target, a subcommand or a file. When you add a doc that others will rely on,
add it to the test's list.

### T26: No Python callback may run on the shared SQLite connection
The API shares one SQLite connection across its request and job threads. An
authorizer callback on it deadlocked the server under a handful of concurrent
requests: SQLite calls the callback while holding the connection mutex, the
callback needs the GIL, and another thread holds the GIL while it waits for
that mutex (binding parameters or reading columns). Production showed it as a
hung API that Render restarted, with a minute or two of 502s each time. Do not
add `set_authorizer`, `set_trace_callback`, `set_progress_handler` or
`create_function` to that connection; do the work in Python before the
statement reaches SQLite, as `CatalogTrackingConnection` does. Keep
`cached_statements=0` on it, because threads must not share a prepared
statement. `tests/test_launch_hardening_2026_11_11.py` runs eight threads
against the connection and fails on a hang.

### T27: Weather lookups from the server fail on a shared IP address
Open-Meteo's no-key API limits calls per IP address (600 a minute, 10,000
a day). A free Render service shares its outbound address with many other apps,
so the API's own lookups failed with HTTP 429 and the site showed "Live weather
isn't available right now" for any place that is not a known track
(2026-11-11). The website now fetches the reading in the visitor's browser
(`web/lib/openMeteo.js`, the same query as
`motoquant/api.py::_fetch_open_meteo_uncached`) and sends it to
`/api/venues/resolve` as `observed`; the simulation routes skip the lookup when
a request carries altitude, temperature, humidity and pressure. Do not move the
fetch back to the server, and keep the two lookups in step.
`tests/test_browser_weather_2026_11_11.py` fails if those paths call out.
