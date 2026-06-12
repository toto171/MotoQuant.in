# Known Prod Issues — caught while merging Phase A+B into origin/main

## 1. Parts catalog has cross-bike leaks via invalid fitment rules

**Symptom:** `tests/test_catalog_integration.py::TestNoLeaks::test_rsv4_no_panigale_leak` fails:

```
RSV4 leaked to Ducati-specific Termignoni:
'termignoni termignoni full system kawasaki zx-10r (998cc)'
```

**Root cause** (visible in test logs):
- Some parts have `tier='family'` with no match constraints → compatibility
  engine's "treat as universal" fallback applies them to every bike.
- Parts 469 and 472 specifically have `tier='model'` which the engine
  doesn't recognize → "Invalid tier: model" warnings, then they fall
  through to universal-match too.

**Status:** **Pre-existing on `origin/main` (= 85b4c63)** — verified by checking
out origin-main and running the same test, which fails identically. NOT
a regression introduced by tonight's merge. Has been live in prod since
PR #84 (the Apr 27 mega-session) shipped the catalog expansion to 555 parts.

**User-visible impact:** On `motoquant.in/simulator`, when a user picks
RSV4 (or other 1000cc sport bikes) and looks at the parts catalog, they
see "Termignoni Full System Kawasaki ZX-10R" as a compatible option.
Click + simulate works (it just applies a generic Termignoni torque
multiplier), but it's clearly the wrong product for that bike.

**Fix outline (not in tonight's deploy):**
1. `motoquant/database/seed.py` (or one of the `seed_catalogs/*.py` modules):
   audit fitment_rules for parts 469, 472 — replace `tier='model'` with
   the correct `tier='exact_model'` or the appropriate level.
2. For all `tier='family'` parts with no constraints: add at least a
   `manufacturers` or `engine_configs` constraint so they don't fall
   through to universal.
3. The compatibility engine in `motoquant/parts/compatibility.py:222` could
   also be hardened — currently it logs a warning then matches everything.
   Stricter behaviour would be to LOG and SKIP (don't attach the part).

## 2. Sobol analysis tests skipped (optional dep)

`tests/test_analysis.py::TestComputeSobolIndices` errors out because
`SALib` isn't installed in the sandbox. This is expected — SALib is
listed as an optional dep for the Sobol global-sensitivity analysis
feature. Production has it (Railway pip install includes SALib via
requirements-api.txt). Sandbox-only issue, no action needed.

## 3. Stale `.git/index.lock` on FUSE-mounted .git

The user's local `.git/index.lock` has been zero-bytes-empty for several
hours, blocking `git push` and other index operations. Sandbox cannot
delete it (Operation not permitted on Windows-created locks). User must
`rm -f .git/index.lock` from their Windows terminal before pushing.

## 4. tokens.md still has live PAT

`.gitignore` was updated in commit 80cb6d5 (and unioned with origin's
gitignore in the merge commit a4b176a) to cover `tokens.md` and friends.
But the file itself still exists on disk with a live fine-grained PAT.
User must revoke the PAT at github.com/settings/tokens.
