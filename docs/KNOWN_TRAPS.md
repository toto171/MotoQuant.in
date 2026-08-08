# Known traps — bugs and gotchas that keep coming back

Institutional memory. Every entry here was hit at least once (some several
times) and cost real debugging time. Read this before a large change; it is
cheaper than rediscovering these. New contributor — model or human — this is
the "don't step here" map.

> Rule of thumb from `CLAUDE.md`: *"Fix the same mistake twice, and it is a
> rule. Fix it three times, and it is a section in the docs."*

---

### T1 — Staging with `git add -A` pulls in unrelated WIP
The working tree often holds truncated files, CRLF drift, scratch scripts, and
parallel-session edits. **Always stage explicit paths.** `git status --short`
first and decide file by file.

### T2 — `motoquant.db` shows "modified" but nothing changed
Opening the seeded DB in a test rewrites SQLite internal pages. `git diff` flags
it as binary-modified with **no content change**. Verify row counts against
`HEAD`; if unchanged, `git checkout -- motoquant.db`. Never commit incidental DB
churn — it bloats the repo (the file is ~18 MB).

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

### T8 — `CLAUDE.md` is a fragile single-paragraph changelog
Line ~3 holds the entire nested session history in one paragraph. A `Write` that
"cleans it up" loses the trailing evergreen sections. **Prepend one line;** never
regenerate. Substantive write-ups go in `reports/`. (This repo is intentionally
migrating the durable knowledge *out* of CLAUDE.md into AGENTS.md / INVARIANTS.md
/ ARCHITECTURE.md / this file.)

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
on the single-worker Render deploy, but concurrent **writes** (save-run, suggest,
usage metering, auth session, subscription upsert) can interleave. This is the
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
`scripts/patch_*.py` also updates the reseed chain in `CLAUDE.md` CURRENT
STATE (and anywhere else the chain is written out). The gate: re-prove the
FULL chain idempotent (×2) whenever a script is added.
