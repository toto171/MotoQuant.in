"""
sweep_batched.py
================
Wrapper around scripts/topspeed_sweep.py that lets the caller process the
ALL_KNOWN_BIKES catalog in slices of `--count` bikes starting at index
`--start`. Each slice writes its raw per-bike sim rows to
`reports/sweep_topspeed_partials/slice_NNNN_NNNN.json`.

When `--merge` is passed the script instead reads every partial under that
folder, concatenates the rows, runs the BENCHMARKS scoring step from
topspeed_sweep, and writes the final combined report to
`--out` (JSON) and a sibling `.md` (human-readable).

Why a wrapper rather than editing topspeed_sweep.py: the user's spec said
"write a small wrapper in scripts/sweep_batched.py if neither supports
--start --count". This avoids touching the existing sweep contract.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
logging.getLogger("motoquant").setLevel(logging.ERROR)

# Ensure scripts/ is on sys.path so we can reuse topspeed_sweep helpers.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from topspeed_sweep import BENCHMARKS, _match, _sim_spec  # noqa: E402

from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402


_PARTIAL_DIR = _HERE.parent / "reports" / "sweep_topspeed_partials"


def run_slice(start: int, count: int) -> Path:
    end = min(start + count, len(ALL_KNOWN_BIKES))
    _PARTIAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _PARTIAL_DIR / f"slice_{start:04d}_{end:04d}.json"

    slice_t0 = time.perf_counter()
    rows: list[dict] = []
    fails: list[dict] = []
    for idx in range(start, end):
        spec = ALL_KNOWN_BIKES[idx]
        t0 = time.perf_counter()
        try:
            row = _sim_spec(spec)
            row["_idx"] = idx
            row["_wall_s"] = round(time.perf_counter() - t0, 3)
            rows.append(row)
        except Exception as exc:
            fails.append(
                {
                    "_idx": idx,
                    "manufacturer": spec.manufacturer,
                    "model": spec.model_name,
                    "year": spec.year_from,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    payload = {
        "start": start,
        "end": end,
        "n_ok": len(rows),
        "n_fail": len(fails),
        "wall_s": round(time.perf_counter() - slice_t0, 1),
        "rows": rows,
        "fails": fails,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(
        f"[{start:>3d}..{end:>3d}) ok={len(rows):>3d} fail={len(fails):>2d} "
        f"wall={payload['wall_s']:>5.1f}s -> {out_path.name}"
    )
    return out_path


def merge_all(out_json: Path, out_md: Path) -> None:
    if not _PARTIAL_DIR.is_dir():
        print(f"No partials dir at {_PARTIAL_DIR}", file=sys.stderr)
        sys.exit(2)

    rows: list[dict] = []
    fails: list[dict] = []
    seen_idx: set[int] = set()
    for p in sorted(_PARTIAL_DIR.glob("slice_*.json")):
        data = json.loads(p.read_text())
        for r in data.get("rows", []):
            if r.get("_idx") in seen_idx:
                continue
            seen_idx.add(r["_idx"])
            rows.append(r)
        fails.extend(data.get("fails", []))

    rows.sort(key=lambda r: r.get("_idx", -1))

    # Score against benchmarks (re-uses topspeed_sweep.BENCHMARKS).
    scored = []
    for mfr, mdl, yr, target, src in BENCHMARKS:
        m = _match(mfr, mdl, yr, rows)
        if not m:
            continue
        delta = m["v_max_kmh"] - target
        scored.append(
            {
                "benchmark": f"{mfr} {mdl} ({yr})",
                "target_kmh": target,
                "sim_kmh": m["v_max_kmh"],
                "delta_kmh": delta,
                "source": src,
                "bike_match": f"{m['manufacturer']} {m['model']}",
            }
        )

    abs_d = [abs(x["delta_kmh"]) for x in scored]
    deltas = [x["delta_kmh"] for x in scored]

    # Anomaly flags (per the user's spec)
    flagged: list[dict] = []
    for r in rows:
        flags = []
        if not r.get("reached_plateau", False):
            flags.append("no_plateau")
        t = r.get("time_to_term_s") or 0.0
        if t < 8.0 or t > 60.0:
            flags.append(f"time_{t:.1f}s_outside_8_60")
        plateau_kw = r.get("power_at_term_kw") or 0.0
        crank_kw = (r.get("power_hp") or 0) * 0.7457
        if crank_kw > 0 and plateau_kw == 0:
            flags.append("plateau_power_zero")
        elif crank_kw > 0 and abs(plateau_kw - crank_kw) / crank_kw > 0.10:
            flags.append(
                f"plateau_kw_off_{plateau_kw:.1f}_vs_crank_{crank_kw:.1f}"
            )
        if flags:
            flagged.append(
                {
                    "_idx": r.get("_idx"),
                    "bike": f"{r['manufacturer']} {r['model']}",
                    "v_max_kmh": r["v_max_kmh"],
                    "time_to_term_s": r["time_to_term_s"],
                    "power_hp": r["power_hp"],
                    "plateau_kw": r.get("power_at_term_kw"),
                    "flags": flags,
                }
            )

    # Top-speed deviation > 5 % vs benchmark
    bench_5pct = [
        s for s in scored if s["target_kmh"] and abs(s["delta_kmh"]) / s["target_kmh"] > 0.05
    ]

    summary = {
        "date": _dt.date.today().isoformat(),
        "n_total_bikes": len(ALL_KNOWN_BIKES),
        "n_simmed_ok": len(rows),
        "n_failed_in_sim": len(fails),
        "plateau_count": sum(1 for r in rows if r.get("reached_plateau")),
        "benchmarks_matched": len(scored),
        "mean_abs_delta_kmh": round(sum(abs_d) / len(abs_d), 1) if abs_d else None,
        "median_abs_delta_kmh": round(sorted(abs_d)[len(abs_d) // 2], 1)
        if abs_d
        else None,
        "bias_kmh": round(sum(deltas) / len(deltas), 1) if deltas else None,
        "within_10_kmh": sum(1 for d in abs_d if d <= 10),
        "within_20_kmh": sum(1 for d in abs_d if d <= 20),
        "within_30_kmh": sum(1 for d in abs_d if d <= 30),
        "n_flagged_anomalies": len(flagged),
        "n_benchmarks_off_5pct": len(bench_5pct),
    }
    payload = {
        "summary": summary,
        "sims": rows,
        "scored": scored,
        "fails": fails,
        "flagged": flagged,
        "benchmarks_off_5pct": bench_5pct,
    }
    out_json.write_text(json.dumps(payload, indent=2))

    # Human-readable
    md = []
    md.append(f"# Top-speed sweep — {summary['date']}\n")
    md.append("Generated by `scripts/sweep_batched.py --merge`.\n")
    md.append("## Summary\n")
    for k, v in summary.items():
        md.append(f"- **{k}**: {v}")
    md.append("\n## Anomaly flags (per-bike)\n")
    md.append(
        f"Flagged when: no plateau reached, time-to-plateau outside 8-60s, "
        f"or displayed plateau power deviates >10% from crank rating.\n"
    )
    md.append(f"**Total flagged: {len(flagged)}**\n")
    if flagged:
        md.append(
            "| idx | bike | V_max km/h | t_plateau s | crank hp | plateau kW | flags |"
        )
        md.append(
            "|---:|---|---:|---:|---:|---:|---|"
        )
        for f in flagged:
            md.append(
                f"| {f['_idx']} | {f['bike']} | {f['v_max_kmh']} | {f['time_to_term_s']} | "
                f"{f['power_hp']} | {f['plateau_kw']} | {', '.join(f['flags'])} |"
            )
    md.append("\n## Benchmarks where sim deviates >5% from target\n")
    md.append(f"**Total: {len(bench_5pct)}**\n")
    if bench_5pct:
        md.append("| benchmark | target | sim | Δ km/h | source |")
        md.append("|---|---:|---:|---:|---|")
        for b in bench_5pct:
            md.append(
                f"| {b['benchmark']} | {b['target_kmh']} | {b['sim_kmh']} | "
                f"{b['delta_kmh']:+.1f} | {b['source']} |"
            )
    md.append("\n## Sim failures\n")
    md.append(f"Total: {len(fails)}\n")
    if fails:
        for fl in fails[:20]:
            md.append(
                f"- idx {fl.get('_idx')}: {fl.get('manufacturer')} {fl.get('model')} "
                f"-> {fl.get('error')}"
            )
    md.append("")
    out_md.write_text("\n".join(md))

    print(f"\nMerged {len(rows)} unique bikes into {out_json}")
    print(f"  failures: {len(fails)}   flagged: {len(flagged)}   bench-off-5%: {len(bench_5pct)}")
    if summary["mean_abs_delta_kmh"] is not None:
        print(
            f"  benchmarks: matched={summary['benchmarks_matched']}  "
            f"mean|Δ|={summary['mean_abs_delta_kmh']} km/h  "
            f"bias={summary['bias_kmh']:+}"
        )
    print(f"Markdown: {out_md}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=int, help="Slice start index (0-based) into ALL_KNOWN_BIKES")
    p.add_argument("--count", type=int, default=40, help="How many bikes in this slice")
    p.add_argument("--merge", action="store_true", help="Merge all partials in the partials dir")
    p.add_argument(
        "--out",
        type=Path,
        default=_HERE.parent / "reports" / "sweep_topspeed_2026_05_03.json",
        help="Merged output JSON path",
    )
    args = p.parse_args()

    if args.merge:
        out_md = args.out.with_suffix(".md")
        merge_all(args.out, out_md)
        return

    if args.start is None:
        print("--start is required unless --merge is given", file=sys.stderr)
        sys.exit(2)

    run_slice(args.start, args.count)


if __name__ == "__main__":
    main()
