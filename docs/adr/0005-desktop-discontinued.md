# ADR-0005: Desktop app discontinued — the hosted web app is the product

**Status:** Accepted (supersedes [ADR-0001](0001-tauri-python-sidecar.md))
**Date:** 2026-07-06
**Deciders:** Hritwik Mudhai (operator decision)

## Context

ADR-0001 chose a Tauri shell + bundled Python sidecar for a v1.0 desktop app
(Phase 5). The scaffold was built (`desktop/`), typechecks, and has a sidecar
packaging plan — but no binaries were ever cut. Meanwhile the hosted stack
matured into the actual product: FastAPI on Render + Next.js on Vercel
(`motoquant.in`), with the agentic chat, build optimizer, and shareable
timeslips all live and iterating fast.

Shipping and maintaining signed desktop binaries (Apple notarization, Windows EV
cert, an auto-updater, a per-OS build matrix) is real ongoing cost that competes
with the web product for attention, for a delivery channel the audience hasn't
asked for.

## Decision

**Discontinue the desktop app. The hosted web app is the product.** The
`desktop/` scaffold stays in-tree for reference only; its CI typecheck job keeps
the tree healthy, but no binaries are built and no release is cut. All
user-facing surfaces (site, README, FAQ, onboarding) were scrubbed of desktop
references in July 2026; `docs/INSTALL.md` and `docs/RELEASE.md` carry
deprecation banners.

**License keys survive** as a product feature (device-bound seats), independent
of any desktop client.

## Consequences

- **Positive.** One product surface to polish; faster iteration; no
  code-signing/notarization/updater maintenance burden; the IP is protected by
  the hosted model (a copied client is worthless without a live licensed
  session) rather than by shipping the engine to users' machines.
- **Negative.** No offline capability; no "download" conversion path. Accepted —
  the Indian drag community reaches the product fine via the web.
- **Neutral.** The `desktop/` code is not deleted (cheap to keep, useful as a
  reference if a native client is ever revived). Reviving it would need a fresh
  ADR with an fps/UX validation on real hardware.

## References

- ADR-0001 (superseded) · `desktop/` (reference scaffold) ·
  `docs/RELEASE.md` / `docs/INSTALL.md` (deprecation banners) · CLAUDE.md
  (July 6 "DESKTOP APP SCRAPPED" entry).
