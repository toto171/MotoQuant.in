# Agent A11: growth-experiments

Read CLAUDE.md, then `web/app/page.js` (landing) + `web/components/SimulatorWidget.js`.

## Goal

Propose ONE A/B-able UI/copy variant per session. Implement it as a feature-flagged variant (default off) so user can flip it on after reviewing.

## Today's variant priority

1. CTA copy variants (current "Try it free" → "Predict your bike's ET")
2. Above-the-fold value prop (current physics-first → maybe Indian-first or comparison-first)
3. Pricing-page friction reduction (signup form fields, plan-selector layout)
4. Simulator default bike (currently Hayabusa — try a Pulsar NS200 or RE 650 to localise)
5. Blog-post pull-quote placement / CTA density

## Workflow

1. Pick ONE element. State the hypothesis: "users land and don't try the simulator because <X>."
2. Make the variant. Wrap in a feature flag (`?variant=B` URL param works as a 0-infra A/B).
3. Document the experiment in `data/growth_experiments.json`:
   ```json
   { "id": "EXP-007", "started": "YYYY-MM-DD", "hypothesis": "...", "variant_a": "control", "variant_b": "...", "primary_metric": "simulator_runs/landing_visitor", "min_sample": 200, "status": "live" }
   ```

## Deliverable

- Edit web/app/<page>/page.js with the variant + flag check
- Append to `data/growth_experiments.json`
- `reports/growth_exp_<id>_YYYY-MM-DD.md`

## Don't

- Never test more than one variable per experiment.
- Never start a 2nd experiment on the same page while the first is live.
- Never declare a winner without ≥200 samples.
- Never break SEO on the control. Variant must serve same canonical URL.

Cap ~600 words.
