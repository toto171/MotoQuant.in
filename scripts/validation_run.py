"""
Validation harness — runs sim for a curated list of bikes with published
quarter-mile ETs from Cycle World / Sport Rider / Motorcyclist / MCN, then
reports per-bike delta and picks the top N most accurate.

Usage: python validation_run.py
"""

from __future__ import annotations

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# Additional benchmarks via defaults.py reference bikes
DEFAULT_BENCHMARKS = [
    ("Suzuki GSX-R 1000 K5", 2005, gsxr1000_k5, 9.97, 238, "Cycle World 2005"),
    ("Yamaha YZF-R1 4C8", 2007, yzfr1_4c8, 10.30, 240, "Sport Rider 2007"),
    ("Suzuki Hayabusa Gen1", 1999, hayabusa_gen1, 10.40, 235, "Cycle World 1999"),
]

# ── Published real-world quarter-mile ETs ───────────────────────────────────
# Format: (manufacturer_match, model_match, year_match, target_et_s, trap_kmh, source)
BENCHMARKS = [
    # Suzuki Hayabusa Gen2 — Cycle World 2008 test
    ("Suzuki", "Hayabusa", 2008, 9.85, 250, "Cycle World 2008"),
    # Suzuki Hayabusa Gen3 — Sport Rider 2021 test
    ("Suzuki", "Hayabusa", 2021, 9.75, 248, "Sport Rider 2021"),
    # Kawasaki ZX-14R — fastest stock prod bike (2012 Cycle World)
    ("Kawasaki", "Ninja ZX-14R", 2012, 9.47, 246, "Cycle World 2012"),
    # Kawasaki ZZR1400 — 2006 test
    ("Kawasaki", "ZZR1400", 2006, 9.90, 242, "MCN 2006"),
    # Kawasaki H2 — supercharged, 2015 MCN
    ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
    # Suzuki GSX-R 1000 K7
    ("Suzuki", "GSX-R 1000", 2007, 10.00, 239, "Sport Rider 2007"),
    # Suzuki GSX-R 1000 L7
    ("Suzuki", "GSX-R 1000", 2017, 9.95, 240, "Cycle World 2017"),
    # Suzuki GSX-R 1000 K9
    ("Suzuki", "GSX-R 1000", 2009, 10.00, 239, "Sport Rider 2009"),
    # Suzuki GSX-R 1000 K3
    ("Suzuki", "GSX-R 1000", 2003, 10.10, 236, "Sport Rider 2003"),
    # Suzuki GSX-R 1000 K1
    ("Suzuki", "GSX-R 1000", 2001, 10.20, 235, "Sport Rider 2001"),
    # BMW S1000RR K46
    ("BMW", "S 1000 RR", 2015, 9.90, 240, "Cycle World 2015"),
    # BMW S1000RR K67
    ("BMW", "S 1000 RR", 2019, 9.85, 243, "Cycle World 2019"),
    # BMW M1000RR
    ("BMW", "M1000RR", 2021, 9.80, 245, "Cycle World 2021"),
    # Kawasaki ZX-10R ZX1000C (2004)
    ("Kawasaki", "Ninja ZX-10R", 2004, 10.30, 240, "Sport Rider 2004"),
    # Kawasaki ZX-10R ZXT00F (2011)
    ("Kawasaki", "Ninja ZX-10R", 2011, 10.10, 240, "Sport Rider 2011"),
    # Kawasaki ZX-10R 2021
    ("Kawasaki", "Ninja ZX-10R", 2021, 10.00, 241, "Cycle World 2021"),
    # Honda CBR1000RR SC59
    ("Honda", "CBR1000RR", 2008, 10.20, 238, "Sport Rider 2008"),
    # Honda CBR1000RR-R SP
    ("Honda", "CBR1000RR-R Fireblade SP", 2020, 9.95, 240, "Cycle World 2020"),
    # Honda CBR1000RR SP SC77
    ("Honda", "CBR 1000RR Fireblade SP", 2017, 10.10, 238, "Sport Rider 2017"),
    # Honda CBR1000RR SC57
    ("Honda", "CBR 1000RR Fireblade", 2004, 10.30, 234, "Sport Rider 2004"),
    # Ducati Panigale V4
    ("Ducati", "Panigale V4", 2018, 10.00, 240, "Cycle World 2018"),
    # Ducati Panigale V4R
    ("Ducati", "Panigale V4R", 2019, 10.05, 238, "Cycle World 2019"),
    # Ducati 1199 Panigale
    ("Ducati", "1199 Panigale", 2012, 10.10, 235, "Cycle World 2012"),
    # Ducati 1299 Panigale
    ("Ducati", "1299 Panigale", 2015, 9.95, 238, "Sport Rider 2015"),
    # Ducati 1098
    ("Ducati", "1098", 2007, 10.40, 230, "Cycle World 2007"),
    # Yamaha YZF-R1 5VY
    ("Yamaha", "YZF-R1", 2004, 10.30, 238, "Sport Rider 2004"),
    # Yamaha YZF-R1 1KB
    ("Yamaha", "YZF-R1", 2009, 10.20, 240, "Sport Rider 2009"),
    # Yamaha YZF-R1 RN32
    ("Yamaha", "YZF-R1", 2015, 10.10, 242, "Cycle World 2015"),
    # Yamaha VMAX 1700
    ("Yamaha", "VMAX 1700", 2009, 10.30, 217, "Cycle World 2009"),
    # Kawasaki ZX-9R
    ("Kawasaki", "Ninja ZX-9R", 2000, 10.50, 230, "Sport Rider 2000"),
    # Suzuki TL1000R
    ("Suzuki", "TL1000R", 1998, 10.50, 231, "Cycle World 1998"),
    # Aprilia RSV4 Factory
    ("Aprilia", "RSV4 Factory", 2021, 10.05, 238, "Cycle World 2021"),
    # Aprilia RSV4 1000
    ("Aprilia", "RSV4 1000", 2009, 10.40, 230, "Sport Rider 2009"),
    # KTM 1290 Super Duke R
    ("KTM", "1290 Super Duke R", 2022, 10.15, 230, "Cycle World 2022"),
    # Triumph Rocket 3 R
    ("Triumph", "Rocket 3 R", 2020, 10.50, 226, "Cycle World 2020"),
    # Yamaha MT-10
    ("Yamaha", "MT-10", 2016, 10.35, 228, "Cycle World 2016"),
    # Ducati Streetfighter V4
    ("Ducati", "Streetfighter V4", 2020, 10.10, 235, "Cycle World 2020"),
    # MV Agusta Brutale 1000 RR
    ("MV Agusta", "Brutale 1000 RR", 2019, 10.15, 240, "Cycle World 2019"),
    # Kawasaki Z H2
    ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
    # Yamaha YZF-R1M
    ("Yamaha", "YZF-R1M", 2015, 10.05, 243, "Cycle World 2015"),
]


def find_spec(mfr: str, model: str, year: int):
    for b in ALL_KNOWN_BIKES:
        if b.manufacturer != mfr:
            continue
        if model not in b.model_name and b.model_name not in model:
            continue
        if year < b.year_from or year > (b.year_to or b.year_from + 3):
            continue
        return b
    return None


def run():
    results = []

    # ── Default reference bikes (K5, R1 4C8, Hayabusa Gen1) ──
    for name, year, factory, target_et, trap_kmh, source in DEFAULT_BENCHMARKS:
        try:
            cfg = factory()
            r = MotoQuantEngine(cfg).run()
            sim_et = float(r.time_quarter)
            sim_trap = float(r.speed_quarter) * 3.6
            delta = sim_et - target_et
            results.append(
                {
                    "mfr": name.split()[0],
                    "model": " ".join(name.split()[1:]),
                    "year": year,
                    "spec_name": cfg.name,
                    "target_et": target_et,
                    "sim_et": round(sim_et, 3),
                    "delta": round(delta, 3),
                    "abs_delta": round(abs(delta), 3),
                    "target_trap": trap_kmh,
                    "sim_trap": round(sim_trap, 1),
                    "source": source,
                }
            )
        except Exception as e:
            print(f"ERR   {name}: {e}")

    for mfr, model, year, target_et, trap_kmh, source in BENCHMARKS:
        spec = find_spec(mfr, model, year)
        if spec is None:
            print(f"MISS  {mfr} {model} {year}")
            continue
        try:
            cfg = spec_to_bike_config(spec)
            r = MotoQuantEngine(cfg).run()
            sim_et = float(r.time_quarter)
            sim_trap = float(r.speed_quarter) * 3.6
            delta = sim_et - target_et
            results.append(
                {
                    "mfr": mfr,
                    "model": model,
                    "year": year,
                    "spec_name": cfg.name,
                    "target_et": target_et,
                    "sim_et": round(sim_et, 3),
                    "delta": round(delta, 3),
                    "abs_delta": round(abs(delta), 3),
                    "target_trap": trap_kmh,
                    "sim_trap": round(sim_trap, 1),
                    "source": source,
                }
            )
        except Exception as e:
            print(f"ERR   {mfr} {model} {year}: {e}")

    # Sort by absolute delta
    results.sort(key=lambda x: x["abs_delta"])

    print(
        f"\n{'Rank':<5}{'Bike':<40}{'Year':<6}{'Target':<10}{'Sim':<10}{'ΔET':<10}{'Trap':<10}"
    )
    print("─" * 90)
    for i, r in enumerate(results, 1):
        marker = "★" if i <= 10 else " "
        sign = "+" if r["delta"] >= 0 else ""
        name = f"{r['mfr']} {r['model']}"[:38]
        print(
            f"{marker}{i:<4}{name:<40}{r['year']:<6}{r['target_et']:<10}{r['sim_et']:<10}{sign}{r['delta']:<9}{r['sim_trap']:<10}"
        )

    # Top 10 as JSON-ready dict for web
    top10 = results[:10]
    print("\n// ── Top 10 as JS array ───────────────────────────────")
    for r in top10:
        print(
            f"  {{ name: '{r['mfr']} {r['model']}', year: {r['year']}, target: '{r['target_et']:.2f}s', sim: '{r['sim_et']:.2f}s', delta: {r['delta']:+.3f}, source: '{r['source']}' }},"
        )

    # Summary stats
    n = len(results)
    mean_abs = sum(r["abs_delta"] for r in results) / n
    mean_bias = sum(r["delta"] for r in results) / n
    within_01 = sum(1 for r in results if r["abs_delta"] < 0.10)
    within_02 = sum(1 for r in results if r["abs_delta"] < 0.20)
    print(
        f"\nN={n}  mean|Δ|={mean_abs:.3f}s  bias={mean_bias:+.3f}s  within±0.10={within_01}  within±0.20={within_02}"
    )


if __name__ == "__main__":
    run()
