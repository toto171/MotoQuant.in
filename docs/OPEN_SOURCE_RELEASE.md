# Open-source release runbook

> Written 2026-09-15 alongside the market study that recommended opening the
> project. This is the ordered checklist for taking `MotoQuant_v1` from a
> private repository to a public Apache-2.0 / ODbL project. Everything in
> §1 is already done on the branch that added this file; §2 and §3 are the
> operator's steps, because a repository's visibility can only be changed by
> its owner in the GitHub UI.

## 1. What the release branch changed (done)

| Area | Change |
|---|---|
| Licences | `LICENSE` (Apache-2.0, code) · `LICENSE-DATA` (ODbL 1.0, catalog + benchmark corpus + DB) · `LICENSE-DOCS` (CC BY 4.0, docs/whitepaper/blog) · `NOTICE` · `web/scripts/fonts/OFL.txt` (the Barlow font files were shipped without the SIL notice the OFL requires) · `license` fields in `pyproject.toml` and `web/package.json` · `CITATION.cff` · `SECURITY.md`. |
| Removed | The autonomous-operations scaffold (`scripts/START.sh`, scheduler, session pre/postflight, agent and subagent prompt templates, `AUTONOMOUS_PAUSED`), the operator message queue (`DISPATCH_*.md`, `STATUS.md`, `NEXT_SESSION.md`), the unsent sales drafts (`outreach/`), the internal business papers (`docs/papers/`), the workstream prompts (`prompts/`), the scaffold's output data (`data/*.json`), the internal planning docs (`TEAM_SCALING`, `TASKS_MASTER_LIST`, `phase_plan`, `SCHEDULING`, `DISPATCH_PROTOCOL`, `AUTONOMOUS_OPERATIONS_PLAYBOOK`), the two tests that only exercised the scaffold, and every prose report under `reports/` (the JSON sweep artefacts and the July-2026 provenance scrape stay — code reads them). All of it remains in git history. |
| Honesty | The "no curve-fitting, every coefficient traceable to a physical measurement" line (features page, whitepaper) now describes the cluster calibration and templated coefficients as they are. The Terms' intellectual-property section names the open licences. New `docs/DATA_PROVENANCE.md` states, table by table, what is measured, what is estimated and what is a placeholder. |
| Verification | Full reachable git history (204 commits) and the working tree were scanned for token-shaped strings (GitHub, Groq, Anthropic, Razorpay, AWS, Resend, Stripe webhook, private keys): clean. `ruff`, the pinned-baseline guard and the fast test tier were run on the branch. |

## 2. Before you flip visibility (operator, ~30 minutes)

1. **Confirm the copyright holder.** `NOTICE` and `CITATION.cff` say
   "Hritwik Mudhai and the MotoQuant Pro contributors" (the `pyproject.toml`
   author). The repo also carries commits and site copy under other names
   (Arya Desai, Ritwik Singh, Sahil Shetye). Put the legal name(s) you want
   on the record in `NOTICE`, `CITATION.cff` and `pyproject.toml` before the
   flip; it is awkward to change afterwards.
2. **Rotate anything that was ever pasted into a chat or a local file.**
   The tracked tree and reachable history are clean, but the project's own
   notes describe PATs, a Groq key and a Gemini key living in local
   `tokens.md` files and in chat transcripts. Rotate them anyway. Set a real
   `JWT_SECRET` on Render (production still runs on the default).
3. **Decide what to do with `CLAUDE.md`.** It is a 290 KB session diary. It
   contains no secrets, but it does describe sandbox paths, token-file names
   and personal workflow. Options: keep it (it is the project's memory and
   `AGENTS.md` rule 7 forbids rewriting it), move it to a private wiki, or
   trim it to the structural sections below the dated chain. This branch
   kept it and prepended a release entry.
4. **Optional: publish without history.** If you would rather the public
   repository not carry the private history at all (reports, dispatch logs,
   the valuation target), publish a fresh copy instead of flipping this one:
   ```bash
   git checkout -b public-release <this branch>
   git checkout --orphan public-main && git add -A && git commit -m "MotoQuant Pro — open-source release"
   git remote add public git@github.com:<owner>/motoquant.git && git push public public-main:main
   ```
   Then archive `MotoQuant_v1` or keep it private. Update the Vercel and
   Render integrations to the new repository if you do this.
5. **Reconcile the pricing page with the licence.** The site still shows
   Pro ₹499/mo and Studio ₹1,999/mo tiers that have never been enforced.
   Open-core (open engine, paid hosted extras) is a legitimate shape, but
   decide it deliberately: the market study recommended dropping the
   subscription plan and keeping the hosted site as a free showcase.
6. **Vercel Hobby** forbids commercial use. A free, open-source showcase is
   fine on Hobby; the moment money is taken, upgrade.

## 3. The flip (operator, 5 minutes)

1. GitHub → repository **Settings → General → Danger Zone → Change
   visibility → Make public**. Type the repository name to confirm.
2. Same page: set the description ("Physics-based motorcycle quarter-mile
   simulator, 541-bike catalog, validated against 250 published runs") and
   the website (`https://motoquant.in`); add topics
   (`motorcycle`, `drag-racing`, `vehicle-dynamics`, `physics-simulation`,
   `python`, `nextjs`, `mcp-server`).
3. Settings → **Features**: enable Discussions (cheaper than issues for a
   hobby audience), keep Issues on, leave Wiki off (docs live in `docs/`).
4. Settings → **Branches**: protect `main` (require the CI workflow).
5. Merge the release PR, then check the README renders the licence badges
   and that `https://github.com/<owner>/MotoQuant_v1/blob/main/LICENSE` shows
   "Apache License 2.0" in GitHub's licence detector.

## 4. After the flip

- Run `make health`; CI's secret scan continues to guard every push.
- Announce once, where the users are, not where developers are: an
  xBhp/Team-BHP thread and the Valley Run WhatsApp/Instagram community, with
  a shared timeslip page as the hook. Ask for Dragy exports — they are the
  instrumented Indian small-cc benchmarks the corpus lacks.
- Add the repository link to the whitepaper and `/validation` page so the
  "auditable" claim resolves to something a reader can open.
- Do not expect stars to arrive by themselves; the entire drag-simulator
  niche on GitHub tops out at ~50 stars. The point of opening the code is
  credibility, portfolio value and honesty, not distribution.

## 5. Licence summary for contributors

| What | Licence | Why |
|---|---|---|
| Source code (`motoquant/`, `web/`, `scripts/`, `tests/`, `e2e/`, `desktop/`) | Apache-2.0 | Explicit patent grant, corporate-friendly, embeddable in MCP clients and hosted services. |
| Data (spec catalog, benchmark corpus, parts/tires/fitments/venues, `motoquant.db`, `reports/*.json`) | ODbL 1.0 | Facts are not copyrightable in India or the US; ODbL binds the database as a contract and requires attribution + share-alike on derived databases. |
| Documentation, whitepaper, blog | CC BY 4.0 | Standard for written material; attribution only. |
| Barlow Condensed font subsets | SIL OFL 1.1 | Upstream licence; notice now travels with the files. |

Contributions are accepted under the same licences (inbound = outbound). No
CLA.
