#!/usr/bin/env python3
"""Run the 287-bike sweep in slices so we stay under the 45s per-shell cap.

Usage:
    python scripts/sweep_chunked.py START END OUT_JSON
e.g.
    python scripts/sweep_chunked.py 0   100 /tmp/sweep_chunk_0.json
    python scripts/sweep_chunked.py 100 200 /tmp/sweep_chunk_1.json
    python scripts/sweep_chunked.py 200 999 /tmp/sweep_chunk_2.json
Then merge the chunk JSONs (each is a plain list of result records).
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motoquant import MotoQuantEngine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


def main():
    if len(sys.argv) != 4:
        print("usage: sweep_chunked.py START END OUT_JSON")
        return 2
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    out = sys.argv[3]

    subset = ALL_KNOWN_BIKES[start:end]
    results = []
    t0 = time.time()
    for i, spec in enumerate(subset):
        try:
            cfg = spec_to_bike_config(spec)
            r = MotoQuantEngine(cfg).run()
            rec = {
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "year_from": spec.year_from,
                "year_to": spec.year_to,
                "disp_cc": spec.displacement_cc,
                "power_hp": spec.peak_power_hp,
                "mass_kg": spec.dry_mass_kg,
                "stroke_type": getattr(spec, "stroke_type", 4) or 4,
                "category": getattr(spec, "category", None),
                "finished": bool(r.finished_quarter),
                "sim_et": float(r.time_quarter) if r.finished_quarter else None,
                "sim_trap_ms": float(r.speed_quarter) if r.finished_quarter else None,
                "max_dist_m": float(r.max_distance_m),
                "elapsed_s": float(r.elapsed_time_s),
            }
        except Exception as exc:
            rec = {
                "manufacturer": spec.manufacturer,
                "model": spec.model_name,
                "error": str(exc)[:200],
            }
        results.append(rec)

    took = time.time() - t0
    with open(out, "w") as f:
        json.dump({"start": start, "end": end, "took_s": took, "results": results}, f)
    print(
        "chunk [%d:%d] %d bikes in %.1fs -> %s" % (start, end, len(results), took, out),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
