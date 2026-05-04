# dhisetu@gmail.com Authorship Audit — May 3, 2026

## Question
Will future Vercel/GitHub-integration deploys reject commits authored as
`dhisetu@gmail.com`, and which addresses are verified on the GitHub account
`da25mem5s02-debug`?

## Findings on `main` (HEAD `3d49cab`)

`git log --format='%h %ae %ad %s' --date=short main | grep dhisetu@gmail.com` returns **5 commits**:

```
882c3af dhisetu@gmail.com 2026-05-02 test(physics): Hypothesis property tests for ET monotonicity invariants
31efba9 dhisetu@gmail.com 2026-04-30 feat(catalog): drag-prep specialty parts + daily-run cleanup
066fc0e dhisetu@gmail.com 2026-04-22 Silent-failure hardening + gear-ratio fixes + 4-cluster physics tuning
2c1a0f3 dhisetu@gmail.com 2026-04-22 Silent-failure hardening + gear-ratio fixes + 4-cluster physics tuning
ff970db dhisetu@gmail.com 2026-04-13 Initial commit: MotoQuant Pro physics engine + landing page
```

For comparison, **266 commits** are authored as the desired
`da25mem5s02@student.nitw.ac.in`. The author set on `main` is exactly those
two addresses, no others.

`066fc0e` and `2c1a0f3` look like a duplicate / orphan-pair from the April-22
PM session.

## Verified-emails check on `da25mem5s02-debug`

**Blocked.** The sandbox egress allowlist permits `github.com`
(used for `git fetch`/`git push`) but **not** `api.github.com`. Both
`curl` and the workspace `web_fetch` failed with:

- `curl`: `HTTP code 403 from proxy after CONNECT`
- `web_fetch`: `Host "api.github.com" is not on the network allowlist`

The endpoints needed for forensic verification — `GET /user/emails` (PAT-auth)
and `GET /users/da25mem5s02-debug/public_events` — are therefore not reachable
from this run. Adding `api.github.com` to the egress allowlist (Settings →
Capabilities) would unblock future automated audits.

## What we can infer indirectly

1. The 5 `dhisetu@gmail.com` commits **are present in `origin/main`** —
   `git log origin/main` shows the same five SHAs. So at the moment those
   commits landed, neither GitHub nor Vercel rejected them.
2. The most recent `dhisetu@gmail.com` commit (`882c3af`, May 2) was made
   *after* the standing git-auth note in CLAUDE.md instructed all
   autonomous runs to use `da25mem5s02@student.nitw.ac.in`. That note was
   only added the same day in `3d49cab`, so `882c3af` predates the rule —
   not a violation, just a pre-rule artefact.
3. The repo-local `git config user.email` is now correctly set to
   `da25mem5s02@student.nitw.ac.in` (verified at the start of this session),
   so any new commits this run author correctly.

## Recommendation (no action taken — forensic only per spec)

If a future Vercel push from `main` is rejected on author-email grounds,
two safe remediation paths exist:

- **Cosmetic:** rewrite the 5 commits with `git filter-branch` /
  `git filter-repo` to update `GIT_COMMITTER_EMAIL` +
  `GIT_AUTHOR_EMAIL` to the verified address. Force-push required.
- **Pragmatic:** add `dhisetu@gmail.com` as a secondary verified address
  to `da25mem5s02-debug` on github.com → Settings → Emails. Zero history
  rewrite, idempotent, and leaves the historical record honest.

The pragmatic path is preferred unless the user has a reason to scrub
that address from the git log.

## What this run did NOT do

- Did not modify any commit history
- Did not force-push
- Did not rewrite refs
- Did not rotate the PAT
