#!/usr/bin/env python3
"""
Reference-baseline guard — the single load-bearing invariant of this repo.

The three hand-curated reference bikes are pinned **bit-identical**. Any change
to physics/, submodels/, defaults.py, category_profiles.py, or scraper/importer.py
that perturbs them is a regression, no matter how correct it looks. This script
is the one command that proves the pin still holds; it is wired into `make
baselines`, `make check`, the pre-commit hook, and CI so the guard fires the same
way for every contributor — human or model.

Exit 0 = all three within tolerance. Exit 1 = drift (prints the offending delta).

    python scripts/check_baselines.py            # bit-identical (tol 1e-9)
    python scripts/check_baselines.py --tol 0.01 # loose sanity (dev iterations)
"""

from __future__ import annotations

import argparse
import os
import sys

# Make `motoquant` importable when run as `python scripts/check_baselines.py`
# from the repo root even without an editable install (sys.path[0] is scripts/).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The pinned targets (see docs/INVARIANTS.md). These are the exact values the
# current engine produces; the contract is Δ = 0.0000, i.e. bit-identical.
BASELINES = {
    "GSX-R 1000 K5": ("gsxr1000_k5", 9.933056382451884),
    "YZF-R1 4C8": ("yzfr1_4c8", 10.143589715692835),
    "Hayabusa Gen1": ("hayabusa_gen1", 10.363345081274984),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--tol",
        type=float,
        default=1e-9,
        help="max allowed |delta| in seconds (default 1e-9 = bit-identical)",
    )
    args = ap.parse_args()

    try:
        import motoquant as mq
    except Exception as exc:  # pragma: no cover - import failure is a hard stop
        print(f"FAIL: could not import motoquant ({exc})", file=sys.stderr)
        return 2

    worst = 0.0
    failed = []
    for label, (factory_name, target) in BASELINES.items():
        factory = getattr(mq, factory_name)
        et = mq.MotoQuantEngine(factory()).run().time_quarter
        delta = float(et) - target
        worst = max(worst, abs(delta))
        status = "ok" if abs(delta) <= args.tol else "DRIFT"
        if status == "DRIFT":
            failed.append(label)
        print(
            f"  {label:16s} sim={float(et):.10f}  target={target:.10f}  Δ={delta:+.2e}  [{status}]"
        )

    if failed:
        print(
            f"\nFAIL: {len(failed)} baseline(s) drifted beyond tol={args.tol:.1e}: "
            f"{', '.join(failed)}",
            file=sys.stderr,
        )
        print(
            "The reference baselines are a pinned invariant — see docs/INVARIANTS.md. "
            "If this drift is intentional, it needs the full weighted sweep as "
            "justification and a coordinated update of BASELINES + the docs.",
            file=sys.stderr,
        )
        return 1

    print(
        f"\nOK: all baselines bit-identical (worst |Δ| = {worst:.2e} ≤ {args.tol:.1e})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
