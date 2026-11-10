# Handoff — 2026-11-05 (branch `claude/happy-bell-uok34d`, PR #126)

The repository moved to **toto171/MotoQuant.in**. The session that did this
work could not push (the Claude GitHub App had no access to the new owner),
so the branch's newest commits exist only where they were made until someone
pushes them. If you are reading this in a fresh clone, they are already
pushed.

## 1. Push

```bash
git push origin claude/happy-bell-uok34d
```

CI on PR #126 should then run green. If a check fails, fix it. Do not
re-pin baselines to hide a failure.

## 2. Close the six superseded PRs (keep #126; leave their branches)

| PR | Reason |
|---|---|
| #88 Sentry visibility | Re-implemented in #114; on main (`observability.is_initialised()`, `/api/debug/sentry-test`). |
| #102 Oracle migration + Local Lab | Stale: the backend stays on Render; client compute is the Rust/wasm core (ADR-0007). |
| #117 chat tool-arg crash | Ported into #126 (commit fc7cdce, `_as_int`, `tests/test_agent_arg_hygiene.py`). |
| #119 audit delta | Still-valid fixes ported into #126 (fc7cdce). OWM redaction, magic-link and `part_ids` caps were already on main. |
| #124 commercialization prep | Monetization scrapped (ADR-0006). |
| #125 OSS release prep | Superseded by #126. Its SIL OFL font notice is ported (ea4274a). Its ODbL data / CC BY docs licences and CITATION.cff were **not** adopted; that is the owner's call. |

End every comment with the Claude Code attribution footer.

## 3. Update the PR #126 description

It still says "partial run". It now contains:
- the open-source pivot (Apache-2.0)
- the Rust physics core (PyO3 + wasm, bit-identical)
- the audit fix wave
- the PR #117/#119/#125 ports
- the repo-link move
- the accuracy epoch

## Accuracy epoch result (shipped)

Sources: `reports/acc_final_2026_11_05.json` and `reports/acc_epoch3_2026_11_03.json`.

| | Pre-epoch (published 2026-08-08) | Shipped |
|---|---|---|
| ET w\|Δ\|, exact published metric | 0.2629 s, bias +0.0073 | 0.2639 s, bias +0.0292 |
| ET w\|Δ\|, epoch rules, per-row timing (n=266) | — | 0.2493 s, bias +0.0225 |
| Trap bias | +13.8 km/h | +3.1 km/h |
| Top-speed mean\|Δ\| (83 matched) | 28.1 km/h | 12.9 km/h |
| Pins (K5 / R1 / Hayabusa) | 9.9331 / 10.1436 / 10.3633 | 10.0436 / 10.1092 / 10.1100 |

ET is now timed from the beam after a 1-ft rollout (`ET = t(D) − t(0.3048 m)`).

Known residuals, accepted by the owner:
- **Mass inversions on two bikes:** HP4 Race (−10 kg is 9.8 ms slower) and Panigale V4R (2.5 ms). This is wheelie-ballast physics: the lighter bike's higher system CoG lowers its wheelie ceiling. More litre bikes invert at sea level.
- **Reference spread is compressed:** the three simulate within 0.07 s of each other (10.0436 / 10.1092 / 10.1100 s) against 0.43 s in the published tests (9.97 / 10.30 / 10.40 s). The order is right; the R1 and Hayabusa come out 0.19 s and 0.29 s quick. *(Corrected 2026-11-10: this line first said the K5 simulates slowest, which the pins contradict.)*
- **Biased classes:** two-strokes, entry 200–300 cc and singles 300–500 cc are biased beyond ±0.25 s.
- **Mass sensitivity:** litre bikes are nearly mass-insensitive at launch, about 1–4 ms/kg.
- **Exhaust gaps:** five 125 cc bikes have no real exhaust part (`KNOWN_EXHAUST_GAPS`).

Next accuracy levers:
- a launch model calibrated on measured 60-ft rows
- per-source rollout evidence
- the two-stroke curve ladder
- measured CoG / weight-distribution data, replacing the 52%-front and 810 mm seat defaults

## Operator items

- Rotate the OpenWeatherMap key; the repo is public now.
- Set `JWT_SECRET` on Render.
- Check that Vercel and Render still deploy from `toto171/MotoQuant.in`. Their GitHub app installations were on the old account.
- The autonomous-session scripts still commit as the university email. Pick a replacement address before it is closed.
- Decide on the data/docs licences proposed in #125.
