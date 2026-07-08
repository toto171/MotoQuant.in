"""MotoQuant Local Lab — self-contained local engine + UI package.

Operator stress-test tool (July 2026): bundles the full physics engine,
the seeded catalog DB, the numpy surrogate, and the desktop UI's static
build into one PyInstaller executable so the real engine can be exercised
at native CPU speed with no hosted-tier CPU cap, cold starts, or LB
timeouts. NOT a public product — the hosted web app remains the product
(desktop app scrapped July 6, 2026); do not distribute the binary.

See local_lab/README.md for build + usage.
"""
