# Daily Improvement — Sunday, May 3, 2026

**Scheduled task:** `motoquant-daily-improvement`
**Today's rotating focus:** Sunday — Documentation & Cleanup Day
**Status:** **COMPLETED** — one push to origin/main (`63d3c0f`); rebaseline forensics; identity audit.
**Operator:** unattended autonomous run, working to a user-supplied playbook from the daily SKILL.md

---

## Summary

The user's playbook called for quarantining a "rebaseline" set of commits
(48561e3 / 6cce194 / 9a64fe7) that supposedly moved the K5/R1/Hayabusa
reference baselines and were hiding on `main`. **Those commits do not exist in
this repo** — `git log -1 <sha>` reports `malformed object name` for all three.
Main is at `3d49cab` (also the same as origin/main pre-push), produces
**K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s exactly**, and contains nothing
that needed reverting.

The substantive cleanup landed today closes one carry-forward item from the
April-24-PM kaizen pass: `tests/test_db_gearing_integrity.py` was reporting
**310 / 334 bike_configs with stale gear ratios** vs the Tier-1 lookup in
`motoquant/scraper/gear_ratios.py`. The repair script
`scripts/refresh_gearing_from_lookup.py` was sitting in the repo unused because
it crashed with `ZeroDivisionError` on the first shaft- / belt-drive bike it
touched (BMW R-series, Indian, HD Sportster S, Moto Guzzi V-twins all return
`front_sprocket=0`). Patched the script with a one-line guard, ran it,
re-verified the test, committed and pushed.

---

## Pre-run gates

| Gate | Result |
|---|---|
| `git fetch origin` + `git log HEAD..origin/main` | OK; main was already at origin's tip after fetch |
| Reference baselines (K5 / R1 / Hayabusa) | **PASS — Δ +0.0000s on all three** (10.0334 / 10.2859 / 10.4712) |
| `scripts/audit_headline_stats.py` | **CLEAN — "All headline numbers in sync. No action needed."** Source-of-truth: 334 bikes / 562 parts / 232 tires / 861 fitments / 20 venues / 79 benchmarks. |
| `pytest tests/test_db_gearing_integrity.py` (pre-fix) | **FAIL — 310 bikes have stale DB gearing.** Three other tests in the same file pass. |
| Production health — Railway `/api/health` | **NOT VERIFIED** — sandbox network egress blocked Railway domain (`cowork-egress-blocked`). The user is asked to confirm `curl https://web-production-de6eb.up.railway.app/api/health` from a real terminal. |
| Production health — Vercel `www.motoquant.in` | **NOT VERIFIED** — same egress restriction. **Side-channel signal:** during this session the user pasted a Vercel screenshot showing "deployment was blocked because the commit author email (kaizen@motoquant.local) is not valid." (See identity audit below.) |

---

## Rebaseline-forensics summary

Per the playbook, looked for commits `48561e3`, `6cce194`, `9a64fe7`, `5f02df7`:

```
48561e3 → fatal: ambiguous argument; malformed object name
6cce194 → fatal: ambiguous argument; malformed object name
9a64fe7 → fatal: ambiguous argument; malformed object name
5f02df7 → 5f02df7 DB: re-seed bike_configs against post-S1 spec_to_bike_config
                 (lives on ws/kaizen only, not on main)
```

**Three of the four don't exist anywhere in this repo.** No reset of `main` was
performed — main was already at `3d49cab` (the legitimate pre-existing tip)
and the playbook explicitly says: *"If main does NOT have those commits: skip
the reset."*

`ws/topspeed-clamp-removal-rfc` was therefore **not created** — there were no
commits to put on it. The "rebaseline" phenomenon described in the playbook
appears to have happened on a different working tree / a parallel session that
never made it to this checkout. The user should verify against any other
machine they were running yesterday.

**Reference baselines re-confirmed exactly to 4 decimals on `main` after
session work:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s.

---

## Branch-sync state

`ls-remote origin` confirms every listed `ws/*` branch is already on origin and
matches the local tip — no pushes were needed for them. The earlier reading of
"`ws/kaizen` is ABSENT on origin" inside the FUSE-mount working copy was a
stale remote-tracking artifact: lock files in `.git/refs/remotes/origin/*.lock`
(owned by sharp-epic-shannon, not removable from inside the sandbox per FUSE
permission tier) blocked the FUSE-side fetch from updating its remote-tracking
refs. Verified via direct `ls-remote` from the `/tmp/mq-push` clean clone.

| Branch | Tip | Origin tip | State |
|---|---|---|---|
| `main` | `63d3c0f` *(pushed today)* | `63d3c0f` | ✓ in sync |
| `ws/physics-smallcc-2t` | `cf0623b` | `cf0623b` | ✓ in sync |
| `ws/gear-topspeed` | `2bdfbcb` | `2bdfbcb` | ✓ in sync |
| `ws/desktop-ux` | `8d5265c` | `8d5265c` | ✓ in sync |
| `ws/backend-surrogate-pricing` | `95cd5d1` | `95cd5d1` | ✓ in sync |
| `ws/subscription-auth` | `42f57ff` | `42f57ff` | ✓ in sync |
| `ws/release-pipeline` | `d13669b` | `d13669b` | ✓ in sync |
| `ws/landing-marketing` | `fc3a540` | `fc3a540` | ✓ in sync |
| `ws/kaizen` | `d114d35` | `d114d35` | ✓ in sync (already) |
| `ws/topspeed-clamp-removal-rfc` | — | — | does not exist; not created |

Local `ws/ws/*` duplicates (6 of them) **could not be deleted** — `git branch
-D` failed with `Operation not permitted` on `.git/packed-refs.lock` and on
`.git/refs/heads/ws/ws/*.lock`. All are FUSE artifacts owned by
sharp-epic-shannon. They do **not** exist on origin (`ls-remote` confirms),
so this is a purely local-only cleanup. **User must run `git branch -D ws/ws/*`
from a real terminal.**

---

## DB re-seed (closes test_db_gearing_integrity)

Commit: **`63d3c0f`** on origin/main, authored by `Hritwik Mudhai
<da25mem5s02@student.nitw.ac.in>`.

**What broke:** the repair script `scripts/refresh_gearing_from_lookup.py`
unconditionally computed `final_drive_ratio = float(rear) / float(front)` —
which divides by zero on every shaft- and belt-drive bike (BMW R 1250 GS, BMW
K-series, Indian Scout/Chief, HD Sportster S 2022+, Moto Guzzi V-twins). The
Tier-1 lookup correctly returns `(0, 0)` for these bikes (no chain), so the
script crashed on the very first such row.

**Fix:** one-line guard — `final_drive_ratio = float(rear) / float(front) if
float(front) > 0 else None`. Final-drive ratio is meaningless for a shaft or
belt anyway, so `None` is the semantically correct value.

**Run output (idempotency-verified):**

```
{'total': 334, 'updated': 310, 'unchanged': 24, 'reference_locked': 3, 'no_tier1': 0}
{'total': 334, 'updated':   0, 'unchanged': 334, 'reference_locked': 3, 'no_tier1': 0}  # 2nd run
```

3 reference bikes (K5 / YZF-R1 4C8 / Hayabusa Gen1) correctly skipped. 310
non-reference rows refreshed in `motoquant.db`. `motoquant.db` MD5
`fc368fcb…` → `65a1ddbf…`.

**Test:** `pytest tests/test_db_gearing_integrity.py -q` →
`4 passed in 0.18s`.

**Reference baselines after re-seed:** K5 10.0334s / R1 10.2859s /
Hayabusa 10.4712s, Δ +0.0000s on all three. Confirmed.

---

## Identity audit (Vercel deployment block)

Mid-session the user pasted a Vercel screenshot showing the deployment was
blocked: *"the commit author email (kaizen@motoquant.local) is not valid."*

`git log` audit across all branches found exactly **5 commits** authored
under the bot identity `MotoQuant Kaizen <kaizen@motoquant.local>`, all on
`ws/kaizen` and only on `ws/kaizen`:

```
d114d35 fix(kaizen): remove None placeholders from 7 Tier-1 gear-ratio entries
88a714f fix(kaizen): close TOCTOU race in consume_magic_link
f00776d fix(kaizen): override get_current_user in test_api.py so Phase-3 tests survive the S5 auth gates
b7c4097 fix(kaizen): add module-level connect() helper to connection.py
d47f49b fix(kaizen): restore truncated tails on roi.py + connection.py
```

`main` (last 20 commits) and all 7 main `ws/*` user branches have student-email
or personal-email tips and contain none of these 5 SHAs. So Vercel will only
reject deployments rooted at `ws/kaizen` (Vercel was apparently watching that
branch for some reason — most likely because `git push origin ws/kaizen` on
April 28 was the last push before today). Deployments rooted at `main` should
be unaffected.

**My commit today (`63d3c0f`)** is authored by `Hritwik Mudhai
<da25mem5s02@student.nitw.ac.in>` — verified via `git log -1 --format='%an
<%ae>' main`.

**Repo-local git config** is correct:
```
user.email = da25mem5s02@student.nitw.ac.in
user.name  = Hritwik Mudhai
```

**Global git config write was blocked** — `/sessions` filesystem is at 100 %
(`/dev/sdc 9.8G 9.3G 0 100%`), so `git config --global …` returned `failed to
write new configuration file /sessions/sharp-epic-shannon/.gitconfig.lock`.
This is the *recurring* sandbox issue noted in the daily SKILL.md fallback
("if /sessions disk is full"). The repo-local config is still correct in both
the FUSE checkout and the `/tmp/mq-push` clean clone, so any commits I author
this session use the right identity. **This is not a regression for the user's
own commits** — it's only a constraint on this autonomous-cron session.

**Resolved mid-session via user-authorized rebase.** GitHub Education student
plan does not allow registering `kaizen@motoquant.local` as a verified email,
so the user explicitly authorized a one-shot history rewrite *only on
`ws/kaizen`* (not on main, not on any other branch). Done via
`GIT_SEQUENCE_EDITOR=true git rebase -i --exec 'git commit --amend --no-edit
--reset-author --allow-empty' 5f02df7` on `ws/kaizen`. Each of the 5 commits
got a fresh author and a new SHA; tree contents unchanged. Force-pushed with
`--force-with-lease`. Original SHAs are unrecoverable on origin and replaced
1:1.

**SHA mapping (ws/kaizen):**

| Old SHA (kaizen@motoquant.local) | New SHA (da25mem5s02@student.nitw.ac.in) | Subject |
|---|---|---|
| `d47f49b` | `366658e` | fix(kaizen): restore truncated tails on roi.py + connection.py |
| `b7c4097` | `9144027` | fix(kaizen): add module-level connect() helper to connection.py |
| `f00776d` | `c8952c6` | fix(kaizen): override get_current_user in test_api.py so Phase-3 tests survive the S5 auth gates |
| `88a714f` | `9e2443d` | fix(kaizen): close TOCTOU race in consume_magic_link |
| `d114d35` | `7f8b93d` | fix(kaizen): remove None placeholders from 7 Tier-1 gear-ratio entries |

**Verified post-rebase:**

* `git log --format='%h %ae' ws/kaizen | head -5` → all 5 tip commits read
  `da25mem5s02@student.nitw.ac.in`. The next 5 commits below are
  `dhisetu@gmail.com` (Hritwik's personal email, pre-existing across
  multiple branches — out of scope for this fix and registered on GitHub).
* `ls-remote origin refs/heads/ws/kaizen` returns `7f8b93d` — origin
  matches local.
* The 5 old SHAs are not on any other branch (verified
  `git branch --contains <sha>` before the rebase). No collateral damage.
* `main` untouched at `63d3c0f`.
* Reference baselines K5 10.0334 / R1 10.2859 / Hayabusa 10.4712, Δ +0.0000s.

Vercel should now accept ws/kaizen-rooted deployments after its next webhook
retry.

---

## Sunday cleanup carry-forward — picked, scoped, deferred

Pulled the May-2 carry-forward list and triaged each item against this
session's risk budget:

| Item | Action |
|---|---|
| (a) Wheelie-bar sub-500cc gap | **Deferred** — needs partnership data from Pune/Narhe drag shops per April-30 entry; no rock-solid public sources. |
| (b) `test_rsv4_no_panigale_leak` pre-existing failure | **Deferred** — touching catalog data without a benchmark sweep risks silent regression. |
| (c) Parts #469/#472 invalid `tier: model` fitment_rules | **N/A — already fixed.** Live DB inspection shows both rows now use `tier: family` with proper manufacturer + displacement + engine_configs + chain_pitch constraints. The May-2 carry-forward was likely written before a later normalisation pass landed. |
| (d) INR pricing on 7 drag-prep specialty parts | **Deferred** — needs vendor query; no Indian-retailer adapter for swingarm extensions / specialty drag chains. |
| (e) 8 deferred parts from May-1 pricing pass | **Deferred** — same. |

Net new cleanup landed: `test_db_gearing_integrity` closure (above).

---

## What was NOT done

- **Production live-health curl:** sandbox egress blocked. User to verify
  `curl -s https://web-production-de6eb.up.railway.app/api/health` and
  `curl -sI https://www.motoquant.in | head -1` from a real terminal.
- **Full 287/334-bike sweep:** SKILL.md says skip (45 s bash cap).
- **`npm install` / `npm test` in `desktop/`:** SKILL.md says skip (`/sessions`
  disk full).
- **Local cleanup of `ws/ws/*` duplicate branches:** blocked by FUSE
  packed-refs lock files. User to run `git branch -D ws/ws/*` from a real
  terminal.
- **Global `git config` write:** blocked by `/sessions` disk-full. Repo-local
  config is correct, so future commits in this session use the right identity.
- *(originally listed; now resolved mid-session — see Identity audit above.)*

---

## Open follow-ups for next daily run

1. *(removed — resolved via the ws/kaizen rebase above; Vercel should accept
   ws/kaizen on its next deploy attempt.)*
2. **`tests/test_rsv4_no_panigale_leak`** still failing — pre-existing, carried
   forward from April 30. Tighten the test brand-only RSV4 ban to allow
   ZX-10R-labelled Termignoni full-system that legitimately fits Aprilia.
3. **Wheelie-bar sub-500cc parts gap** — partnership-data round with
   Pune/Narhe drag shops to seed Indian-fab options for Apache RR 310 / Duke
   390 / RE 650 class.
4. **Pricing refresh on 8 deferred swingarm/chain parts** from May-1 — needs
   direct-vendor query (Schnitz / DME / Brock's / EK 428 / RK 530 PRODR /
   Dynojet PCVI / Akrapovic Panigale full system).
5. **Headline-stats audit hook:** the current
   `scripts/audit_headline_stats.py` reports `tests_collected: ERROR: no count
   line` because pytest can't be invoked in the disk-full sandbox. Cosmetic
   only — switch to a `find tests -name 'test_*.py' | xargs -I{} grep -c
   '^def test_'`-style fallback so the audit is sandbox-resilient.
6. **The `motoquant.db.before-rebuild` file** in the repo root is untracked
   (presumably a backup from a prior session). Ought to be moved to
   `reports/` or deleted.

---

## Final state for Hritwik on return

| Thing | Where |
|---|---|
| New commit on origin/main | `63d3c0f db: re-seed gear ratios from lookup table (closes test_db_gearing_integrity)` |
| Reference baselines | K5 10.0334 / R1 10.2859 / Hayabusa 10.4712 — exact |
| `test_db_gearing_integrity` | green (4/4) |
| Daily report | `reports/daily_session_2026_05_03.md` *(this file)* |
| CLAUDE.md prepend | one-line entry on the chain at line 3 |
| Bot-identity commits | 0 — 5 commits on `ws/kaizen` re-authored via user-authorized rebase to `da25mem5s02@student.nitw.ac.in`; force-pushed |
| Local `ws/ws/*` duplicates | still present (FUSE permission); user to `git branch -D` from real terminal |

---

*Generated 2026-05-03 by autonomous Sunday cleanup run.*
