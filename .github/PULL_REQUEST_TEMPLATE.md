<!--
Thanks for contributing to MotoQuant Pro.
First time here? Read AGENTS.md (the working contract) and docs/INVARIANTS.md (what must never break).
Fill every section. Delete sections that don't apply (e.g. "Physics benchmark deltas" for a docs-only PR), but don't delete the Kaizen checklist.
Run `make check` (fast gate) and `make test` (full suite) before opening this PR.
-->

## What changed

<!-- One paragraph. What did you change and why? The diff shows the "what" — tell us the "why". -->

## Linked issue

Closes #

## Type

- [ ] Bugfix
- [ ] New feature
- [ ] Physics / sub-model change
- [ ] Database schema change
- [ ] Bike / parts / tire data
- [ ] Calibration data (Dragy / dyno / ECU log)
- [ ] Desktop (Tauri + React) or Web (Next.js) frontend
- [ ] Docs / tooling / CI

## Test plan

<!-- How did you verify the change? Paste commands + relevant output. -->

```
python -m pytest tests/ -q
```

## Physics benchmark deltas (required if you touched `motoquant/physics.py`, any `submodels/*`, or `defaults.py`)

<!-- Paste output from the benchmark sanity check. All three must stay in tolerance:
     K5 = 10.034s ± 0.07   R1 = 10.286s ± 0.10   Hayabusa = 10.472s ± 0.30
-->

| Bike | Target | This PR | Δ |
|---|---|---|---|
| K5 | 10.034 s |  |  |
| R1 | 10.286 s |  |  |
| Hayabusa | 10.472 s |  |  |

## Kaizen checklist (from CLAUDE.md)

- [ ] No silent failure modes (no swallowed exceptions, no helpers that accept invalid paths silently).
- [ ] Data ↔ model paths match (seed / DB / config keys hit real dataclass fields — no `UserWarning` from `bridge.apply_part_to_config`).
- [ ] No bypass paths — modifications flow through every active code path (e.g. if you scaled a dyno curve, `peak_power_hp` is also updated).
- [ ] Every new public function has at least one test that would fail if the function did nothing.
- [ ] Numerical sanity checked — simulation deltas are physically plausible.
- [ ] No dead DB columns / dataclass fields / config keys introduced.
- [ ] Backwards-compatible for renamed fields (grepped all uses, updated, full suite green).

## Collaborator checklist

- [ ] `python -m pytest tests/ -q` is green locally.
- [ ] `ruff check .` and `ruff format --check .` are clean.
- [ ] If this is a desktop / web PR: `npx tsc --noEmit` green in `desktop/` and `npm run build` green in `web/`.
- [ ] Updated `CLAUDE.md` → "Current State" and the relevant phase checklist if this was substantive.
- [ ] No secrets, API keys, or `.env` files in the diff.
- [ ] Commit messages are imperative-mood ("Add …", "Fix …"), subject ≤ 72 chars.
