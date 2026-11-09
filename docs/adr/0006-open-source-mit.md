# ADR-0006: Open source under the MIT license; billing removed

**Status:** Accepted
**Date:** 2026-11-09
**Deciders:** Hritwik Mudhai (operator decision)

## Context

MotoQuant was built as a commercial product: freemium web app with paid tiers,
Razorpay/Stripe checkout, device-bound license keys, and a sim quota
(see the June–August 2026 launch work). Revenue never started — payment
providers were never switched on — while the project's real strengths turned
out to be its validated physics, its curated catalog, and its accuracy
transparency. Those compound faster with outside contributors (sourced bike
specs, instrumented timeslips, parts data) than behind a paywall. The billing
machinery also carried real maintenance and security surface (webhooks,
signature verification, tier gates, quota metering) for no revenue.

## Decision

1. **Release the repository under the MIT license** (`LICENSE`, copyright "The
   MotoQuant Authors"). Contributions are accepted under the same terms; no CLA.
2. **Remove billing entirely**: payment providers, subscriptions, paid tiers,
   license keys, and sim-quota metering. Every feature is free.
3. **Keep optional accounts** (password / magic link) solely so users can save
   runs to a garage and have shareable timeslips attributed. Per-IP rate limits
   stay as abuse protection. A missing `JWT_SECRET` yields a random per-process
   secret with a warning rather than a boot failure.
4. **Keep parts-price data.** INR prices in the parts catalog and the ROI
   cost-per-tenth math are catalog data, not billing.

## Consequences

- **Positive.** Anyone can use, fork, self-host and extend the engine; outside
  contributions (data and code) become the growth path; a much smaller attack
  surface and test matrix; simpler deploy (no payment env vars).
- **Negative.** No revenue path from licensing; hosting is paid for by the
  maintainers (free tiers today). Abuse protection relies on rate limits alone.
- **Neutral.** The honest-data rule and the pinned-baseline contract
  ([ADR-0002](0002-pinned-reference-baselines.md)) are unchanged, and are what
  keep an open contribution model trustworthy. Supersedes the commercial
  framing of [ADR-0005](0005-desktop-discontinued.md) (license keys as a
  product feature); its desktop decision stands.

## References

- `LICENSE` · `CONTRIBUTING.md` · `SECURITY.md` · `CHANGELOG.md` (open-source entry)
