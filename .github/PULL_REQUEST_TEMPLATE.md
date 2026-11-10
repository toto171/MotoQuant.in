<!--
Thanks for contributing. By opening this pull request you agree that your
contribution is licensed under Apache-2.0, like the rest of the project.
First time? Read AGENTS.md (the working rules) and CONTRIBUTING.md.
Delete any section that does not apply.
-->

## What and why

<!-- What changed, and why. The diff shows the what; tell us the why. -->

Closes #

## How I checked it

<!-- Commands you ran and what they printed. `make check` at minimum;
     `make test` before asking for review. -->

## Reference times (physics, sub-models, defaults, category profiles or importer)

<!-- Paste the output of `make baselines`. Any change here needs the full
     accuracy sweep as evidence (docs/adr/0002-pinned-reference-baselines.md). -->

## Data (bikes, parts, tyres, benchmarks)

<!-- One source per value: manual, manufacturer page, magazine test or
     timeslip. Unsourced data is not merged. -->

## Checklist

- [ ] `make check` passes and `make test` is green.
- [ ] Every new function has a test that fails if the function does nothing.
- [ ] Anything that caches the physics is regenerated (`make regen`) if simulated times moved.
- [ ] Web changes build (`make web-build`); changed counts pass `make audit`.
- [ ] No credentials, `.env` files or personal data in the diff.
