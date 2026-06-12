# Team Scaling Playbook

> Honest, cost-aware plan for going from a one-person project to a 2–5-person team.
> Last updated: April 23, 2026.

This doc exists because a generic "2026 startup workflow" recommendation showed up and a lot of it was over-engineered for where MotoQuant actually is. Below is the graded version and what we're doing now vs. later.

---

## Where we are today (evidence, not vibes)

Pulled from `CLAUDE.md` on the date above:

| Signal | State |
|---|---|
| Test suite | 739+ passing, 15 sub-models, ±0.07s accuracy on reference bikes |
| Catalog | 290 bikes, 465 parts, 159 tires, 20 venues |
| Backend | FastAPI + SQLite, calibration pipeline complete |
| Web frontend | Next.js landing + simulator widget, not deployed |
| Desktop app | Tauri + React 19 scaffolded, 2 pages built, not shipped |
| Deployment | Render (API, `render.yaml`) + Vercel (web) — both live |
| Revenue | ₹0 |
| Team size | 1 (founder) + about to add collaborators |

**Bottleneck is not physics.** Physics is the most mature, most-tested part of the stack. The things gating revenue are: shipping the Tauri desktop app, deploying the web surface, collecting real drag-strip runs to calibrate more bikes, and the business side (pricing, first B2B shop conversation in Pune/Narhe).

---

## The plan, graded

| # | Recommendation | Grade | Action |
|---|---|---|---|
| 1 | Create a GitHub Organization (`motoquant-labs`) | ✅ Adopt | Real value for commercial IP + granular permissions. Do within 2 weeks. |
| 2 | Keep all repos private | ✅ Already done | Matches the decision from the collaborator-workflow setup. |
| 3 | `main` + `staging` + `feature/*` branch strategy | ⚠️ Reject for now | Staging branch is cargo-culted from larger orgs. With Vercel preview deploys (already wired in `.github/workflows/deploy.yml`), every PR gets a shareable URL — that's what `staging` is *for*. Adding a staging branch gives every change a second merge gate with no added safety. Revisit at 6+ engineers. Stay trunk-based: `main` + `feature/*`. |
| 4 | Render paid tier for team access | ⚠️ Defer | Real gap, but pay when needed. Keep the founder as sole Render admin until there's a second person actively pushing backend changes. Budget for Pro the month the second dev joins, not before. |
| 5 | Vercel Pro ($20/seat) for commercial use | ⚠️ Defer with trigger | Vercel Hobby ToS forbids commercial use. The moment MotoQuant takes its first rupee of revenue *or* represents itself as a Pvt Ltd publicly, upgrade. Not before. Meanwhile the GitHub Actions deploy workflow (`.github/workflows/deploy.yml`) handles collaborator deploys on Hobby. |
| 6 | Doppler for secrets sync | ❌ Reject | Render env vars + Vercel env vars + a shared 1Password vault for API keys is enough at this scale. Doppler adds a third system to audit; add it at 5+ services or 4+ engineers. |
| 7 | Linear for project management | ⚠️ Defer | Linear is great at 4+ engineers. At 2–3, GitHub Issues + Projects + the issue templates in `.github/ISSUE_TEMPLATE/` are free and co-located with code. Migrate when issue triage genuinely exceeds 15 min/week. |
| 8 | Discord or Slack dev-log channel | ✅ Adopt | Cheap, high-value. Discord for a public community channel (Indian drag-racing scene — the target audience is there), Slack free tier for internal team. GitHub → Slack webhook is 5 min to set up. |
| 9 | Notion/Obsidian "physics bible" | ❌ Reject | `CLAUDE.md` already *is* the physics bible and it's version-controlled with the code. Moving it to Notion guarantees drift between the doc and the code. Keep technical docs in-repo. Use Notion only for business-side artefacts (investor deck narrative, pricing models, meeting notes). |
| 10 | Deployment pipeline (feature → preview → review → main → ship) | ✅ Already implemented | Exactly what `.github/workflows/ci.yml` + `deploy.yml` do. |
| 11 | GitHub for Startups / Vercel for Startups credits | ⚠️ Check eligibility | Both are real programs but generally require either (a) being backed by a partner VC/accelerator or (b) being a registered company. Worth checking once `Motorcycle Research Labs Pvt Ltd` (or whatever the entity ends up being) is incorporated. For now, GitHub Education is the right fit. |

**Net:** adopt the 3 ✅ items this week (Org + Discord/Slack + preview-deploy pipeline, two of which are already done). Put the 4 ⚠️ deferred items behind clear triggers. Ignore the 3 ❌ items.

---

## Concrete 30/60/90 plan

### Next 30 days (pre-commercial)
- [ ] Create `github.com/motoquant-labs` org; transfer the repo.
- [ ] Update remotes, `CODEOWNERS` handles, `CONTRIBUTING.md` URL, any hardcoded refs in workflow files.
- [ ] Invite first collaborator with `Write` access (branch protection will keep them honest).
- [ ] Stand up a MotoQuant Slack workspace free tier; wire `#dev-log` to the GitHub webhook (Actions → new workflow run, PR merged, issue opened).
- [x] Deploy the free-tier stack (Render + Vercel) — live at `motoquant.in` + `motoquant-api.onrender.com`.
- [ ] Pick one good-first-issue from `ONBOARDING.md` §4 and onboard the first collaborator end-to-end on it.

### 60 days (first paying shop or first serious pilot)
- [ ] Trigger upgrade: Vercel Hobby → Pro ($20/mo) the day MotoQuant goes from "prototype" to "commercial offering" publicly or takes first revenue. Non-negotiable — Hobby ToS violation is a takedown risk.
- [ ] Incorporate the entity (if not already). Start the paperwork for GitHub for Startups / Vercel for Startups.
- [ ] Decide: does the desktop app go to closed beta with 2-3 Pune/Narhe shops? If yes, freeze feature work on it and harden.

### 90 days (second engineer onboarded)
- [ ] Render free tier → paid tier the week the second backend engineer joins.
- [ ] Evaluate Linear vs. GitHub Issues honestly — if the current system is fine, stay.
- [ ] Revisit whether a `staging` branch buys anything Vercel previews don't already buy. Almost certainly no, but re-evaluate with the evidence of actual team velocity.

---

## On the "who to hire first" question

**Hire frontend / full-stack first. Not physics.** Evidence:

| Area | Maturity | Current gap |
|---|---|---|
| Physics engine | 15 sub-models, ±0.07s on reference bikes, 739+ tests | Diminishing returns until there's a product to sell |
| Catalog data | 290 bikes, 465 parts | Curated, accurate, tested for leaks |
| Calibration pipeline | Dragy + dyno + ECU, auto-tune via DE + Nelder-Mead | Code-complete |
| **Desktop app (Tauri + React)** | **2 of 5 pages built** | **Main product surface for v1.0 — half-done** |
| **Web deployment** | **Configs ready, nothing live** | **Zero public footprint** |
| **Real Dragy data for more bikes** | **47 benchmarks matched** | **Needs field collection, not engineering** |
| Sales / BD | 0 | Not an engineering hire |

The physics engine does not need a second engineer — it needs customers. The *desktop and web* surfaces are what customers will actually touch, and they're the half-done parts. A mid-level React / TypeScript / Tauri person who can finish the desktop app and polish the Next.js landing page unlocks the commercial launch. A second physics PhD does not.

If/when the physics engine needs a second brain, it'll be because you're building the PPO launch-control work in Phase 6 — that's 2027 territory.

---

## What does not need to change

The collaborator workflow that already landed (strict PR reviews, CODEOWNERS, PR templates, Kaizen checklist, CI with physics benchmark gate, Vercel Actions deploy) covers 90% of what a 2–5 person team needs. The updates above are mostly about *when* to spend money, not *what* code or process to add.
