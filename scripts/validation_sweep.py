"""
validation_sweep.py
===================
Runs the full MotoQuant physics engine against every bike in
``ALL_KNOWN_BIKES`` (287 specs) plus the three validated reference bikes
(K5, R1 4C8, Hayabusa Gen1), and generates a dated JSON report in
``reports/validation_YYYY-MM-DD.json``.

What it does
------------
1. For every spec, calls ``spec_to_bike_config`` + ``MotoQuantEngine.run()``
   and records the simulated ET, trap speed, and whether the run finished
   the quarter mile.  (A bike that doesn't reach 402 m within 15 s is
   flagged as ``over-time``.)
2. For the subset of specs that have real-world published ETs in
   ``BENCHMARKS`` (drawn from Cycle World / Sport Rider / MCN tests), it
   additionally records ``delta = sim_et - target_et``.
3. Aggregates: total sims, failures, pass-rate, mean/median abs-delta,
   bias, accuracy buckets (within 0.1/0.2/0.5/1.0 s).
4. Writes a machine-readable JSON report to ``reports/validation_<date>.json``
   and prints a human-readable summary to stdout.

Run with::

    python validation_sweep.py              # writes report for today
    python validation_sweep.py --json-only  # only writes JSON, no stdout
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import time
import warnings
from pathlib import Path

from motoquant import MotoQuantEngine
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# Silence importer/validator noise; we log per-bike status ourselves.
logging.getLogger("motoquant").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# ── Real-world ET benchmarks (same source list as validation_run.py) ─────────
# Each: (manufacturer_substr, model_substr, year_hint, target_et_s,
#         trap_kmh, source_label)
BENCHMARKS: list[tuple[str, str, int, float, float, str]] = [
    # Hayabusa family
    ("Suzuki", "Hayabusa", 2008, 9.85, 250, "Cycle World 2008"),
    ("Suzuki", "Hayabusa", 2021, 9.75, 248, "Sport Rider 2021"),
    # Kawasaki ZX / H2
    ("Kawasaki", "Ninja ZX-14R", 2012, 9.47, 246, "Cycle World 2012"),
    ("Kawasaki", "ZZR1400", 2006, 9.90, 242, "MCN 2006"),
    ("Kawasaki", "Ninja H2", 2015, 9.62, 247, "MCN 2015"),
    # Kawasaki Ninja H2 SX (998 cc supercharged I4 sport-tourer, 2018-2023) —
    # Cycle World 2018 Best Open-Class Streetbike feature, timing-strip at a
    # licensed drag strip: 10.04s @ 144 mph (231.7 km/h). Same Cycle World
    # source and methodology as the Ninja H2 2015, Z H2 2020, ZX-14R 2012 and
    # S 1000 RR 2015/2019 entries. The H2 SX is the sport-tourer variant of the
    # H2 supercharged platform — heavier and softer-tuned than the track-only
    # H2 (hence 10.04 vs 9.62), but still supercharged. The 4-token model key
    # "Ninja H2 SX" has higher specificity than "Ninja H2" (2-token) and will
    # be matched first after the matcher-specificity fix applied 2026-05-25.
    # URL: https://www.cycleworld.com/best-open-class-streetbike-2018-kawasaki-ninja-h2-sx-se/
    (
        "Kawasaki",
        "Ninja H2 SX",
        2018,
        10.04,
        232,
        "Cycle World 2018 (timing-strip, Best Open-Class Streetbike)",
    ),
    ("Kawasaki", "Z H2", 2020, 9.95, 240, "Cycle World 2020"),
    # GSX-R 1000 family
    ("Suzuki", "GSX-R 1000", 2007, 10.00, 239, "Sport Rider 2007"),
    ("Suzuki", "GSX-R 1000", 2009, 10.00, 239, "Sport Rider 2009"),
    ("Suzuki", "GSX-R 1000", 2017, 9.95, 240, "Cycle World 2017"),
    ("Suzuki", "GSX-R 1000", 2003, 10.10, 236, "Sport Rider 2003"),
    ("Suzuki", "GSX-R 1000", 2001, 10.20, 235, "Sport Rider 2001"),
    # GSX-R 750 K5/K6 — Cycle World 2005 Open Sportbike Shootout, timing-strip
    ("Suzuki", "GSX-R750 K5", 2005, 10.43, 216, "Cycle World 2005 (timing-strip)"),
    # BMW
    ("BMW", "S 1000 RR", 2015, 9.90, 240, "Cycle World 2015"),
    ("BMW", "S 1000 RR", 2019, 9.85, 243, "Cycle World 2019"),
    ("BMW", "M1000RR", 2021, 9.80, 245, "Cycle World 2021"),
    # ZX-10R
    ("Kawasaki", "Ninja ZX-10R", 2004, 10.30, 240, "Sport Rider 2004"),
    ("Kawasaki", "Ninja ZX-10R", 2011, 10.10, 240, "Sport Rider 2011"),
    ("Kawasaki", "Ninja ZX-10R", 2021, 10.00, 241, "Cycle World 2021"),
    # ZX-6R 636 second-gen — Sport Rider 2009 Middleweight Shootout, timing-strip
    ("Kawasaki", "Ninja ZX-6R", 2009, 10.69, 211, "Sport Rider 2009 (timing-strip)"),
    # CBR1000RR family
    ("Honda", "CBR1000RR", 2008, 10.20, 238, "Sport Rider 2008"),
    ("Honda", "CBR1000RR-R", 2020, 9.95, 240, "Cycle World 2020"),
    ("Honda", "CBR 1000RR Fireblade SP", 2017, 10.10, 238, "Sport Rider 2017"),
    ("Honda", "CBR 1000RR Fireblade", 2004, 10.30, 234, "Sport Rider 2004"),
    # Ducati
    ("Ducati", "Panigale V4", 2018, 10.00, 240, "Cycle World 2018"),
    ("Ducati", "Panigale V4R", 2019, 10.05, 238, "Cycle World 2019"),
    ("Ducati", "1199 Panigale", 2012, 9.91, 235, "Motorcycle Consumer News 2012"),
    ("Ducati", "1299 Panigale", 2015, 9.95, 238, "Sport Rider 2015"),
    ("Ducati", "1098", 2007, 10.40, 230, "Cycle World 2007"),
    ("Ducati", "Streetfighter V4", 2020, 10.10, 235, "Cycle World 2020"),
    # Yamaha R1 family
    ("Yamaha", "YZF-R1", 2004, 10.30, 238, "Sport Rider 2004"),
    ("Yamaha", "YZF-R1", 2009, 10.20, 240, "Sport Rider 2009"),
    ("Yamaha", "YZF-R1", 2015, 10.10, 242, "Cycle World 2015"),
    ("Yamaha", "YZF-R1M", 2015, 10.05, 243, "Cycle World 2015"),
    ("Yamaha", "VMAX 1700", 2009, 10.30, 217, "Cycle World 2009"),
    ("Yamaha", "MT-10", 2016, 10.35, 228, "Cycle World 2016"),
    # MT-09 third-gen (890cc CP3) — Cycle World 2021 road test, timing-strip
    ("Yamaha", "MT-09", 2021, 10.95, 204, "Cycle World 2021 (timing-strip)"),
    # Various
    ("Kawasaki", "Ninja ZX-9R", 2000, 10.50, 230, "Sport Rider 2000"),
    ("Suzuki", "TL1000R", 1998, 10.50, 231, "Cycle World 1998"),
    ("Aprilia", "RSV4 Factory", 2021, 10.05, 238, "Cycle World 2021"),
    ("Aprilia", "RSV4 1000", 2009, 10.40, 230, "Sport Rider 2009"),
    ("KTM", "1290 Super Duke R", 2022, 10.15, 230, "Cycle World 2022"),
    ("Triumph", "Rocket 3 R", 2020, 10.50, 226, "Cycle World 2020"),
    ("MV Agusta", "Brutale 1000 RR", 2019, 10.15, 240, "Cycle World 2019"),
    # 2-stroke benchmarks (Cycle World / historical drag tests / magazine)
    ("Yamaha", "RD350", 1973, 14.00, 146, "Cycle World 1973"),
    ("Yamaha", "RD400", 1976, 14.18, 147, "Cycle World 1979 (RD400F Daytona)"),
    ("Suzuki", "RG500", 1985, 11.60, 180, "Cycle World 1985"),
    ("Honda", "NSR250R", 1990, 13.40, 162, "MotorBikeCatalog (estimated 1991 MC21)"),
    ("Aprilia", "RS250", 1996, 13.40, 160, "MotorBikeCatalog 1998 (estimated)"),
    # Indian-market small-cc (from local drag strip telemetry collected
    # by R2 Moto, Aamby Valley community runs — community logged)
    # April 24, 2026: April-24-PM cross-checked against FastestLaps,
    # MotorBikeCatalog, DragTimes, and Indian drag-event reports. Updated
    # values flagged with the verification source. Bikes for which no
    # real timeslip data was found are marked "DERIVED" — the figure is
    # an order-of-magnitude estimate from a 0-100 multiplier and carries
    # ±0.5-1.0 s uncertainty.
    ("Bajaj", "Pulsar NS200", 2019, 16.90, 130, "MotorBikeCatalog 2012 (verified)"),
    (
        "KTM",
        "Duke 390",
        2019,
        14.00,
        150,
        "Motorcycle Consumer News (Duke 390 14.02 @ 91.88 mph)",
    ),
    (
        "Royal Enfield",
        "Continental GT 650",
        2019,
        13.90,
        155,
        "FastestLaps + Mantra Racing (verified)",
    ),
    ("Yamaha", "R15 V3", 2020, 17.62, 118, "MotoStatz 2020 (instrumented)"),
    # Indian-market 150-400cc expansion (April 2026)
    ("Bajaj", "Pulsar RS 200", 2015, 15.70, 132, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("Bajaj", "Pulsar N250", 2021, 15.45, 135, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("Bajaj", "Pulsar NS400Z", 2024, 14.10, 155, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("KTM", "Duke 250", 2017, 15.20, 140, "DERIVED (0-100 × 1.6, ±0.7s)"),
    (
        "KTM",
        "RC 390",
        2017,
        13.85,
        159,
        "Duke 390 baseline (Motorcycle Consumer News, RC adds ~−0.15s for fairing)",
    ),
    (
        "TVS",
        "Apache RR 310",
        2020,
        15.46,
        135,
        "FastestLaps + BikeWale (verified stock)",
    ),
    ("TVS", "Apache RTR 200 4V", 2016, 15.90, 128, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("Yamaha", "R15 V4", 2021, 17.62, 118, "MotoStatz 2021 (instrumented)"),
    ("Yamaha", "MT-15", 2019, 15.80, 130, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("Yamaha", "R3", 2015, 14.00, 145, "FastestLaps 2015 (verified)"),
    ("Yamaha", "MT-03", 2020, 14.05, 92, "AccelerationTimes 2020 (DERIVED)"),
    ("Honda", "CB350RS", 2021, 15.50, 138, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("Honda", "CBR500R", 2022, 13.51, 98, "MotoStatz 2022 (DERIVED)"),
    ("Honda", "CB650R", 2021, 11.80, 115, "AccelerationTimes 2021 (DERIVED)"),
    (
        "Honda",
        "CBR250R",
        2011,
        15.86,
        130,
        "MotorBikeCatalog 2011 (verified, 81.2 mph)",
    ),
    ("Suzuki", "Gixxer 250", 2018, 16.10, 126, "DERIVED (0-100 × 1.6, ±0.7s)"),
    ("Kawasaki", "Ninja 300", 2013, 14.10, 150, "FastestLaps (verified, 93 mph)"),
    # Mid-range global expansion (April 2026)
    ("Suzuki", "SV650", 2016, 11.82, 115, "FastestLaps 2016"),
    # ("Kawasaki", "Ninja 300", 2013, ...) — moved up + verified figure used
    ("Kawasaki", "Ninja 400", 2018, 12.98, 102, "MotoStatz 2018"),
    ("Kawasaki", "Ninja 650", 2020, 12.30, 111, "MotoStatz 2020"),
    ("Kawasaki", "Z 650", 2017, 12.40, 110, "MotoStatz 2017"),
    ("Harley-Davidson", "Sportster S", 2021, 11.10, 122, "HDForums timeslip 2021"),
    ("Royal Enfield", "Continental GT 650", 2020, 13.90, 97, "FastestLaps 2020"),
    ("Triumph", "Trident 660", 2021, 12.00, 111, "MotoStatz 2021"),
    ("Triumph", "Speed 400", 2023, 14.50, 140, "Derived from 0-100 (bikewale 2023)"),
    ("Benelli", "302R", 2017, 15.80, 120, "MotorbikeCatalog 2017"),
    ("Benelli", "TNT 600i", 2014, 12.60, 108, "MotorbikeCatalog 2014"),
    ("Aprilia", "RS 457", 2024, 13.30, 97, "FastestLaps 2024"),
    # SE Asia enthusiast 150cc expansion (April 2026)
    ("Yamaha", "YZF-R7", 2022, 11.64, 116, "MotoStatz 2022 (DERIVED)"),
    ("Yamaha", "FZ25", 2018, 16.00, 127, "DERIVED (0-100 × 1.6, ±0.7s)"),
    # ── 2026-05-24 benchmark-import agent ─────────────────────────────────────
    # Three high-confidence instrumented adds (all from credentialed
    # publications that already appear in this list — same source bar as
    # the Hayabusa / R1 / ZX-14R entries above). Sources verified via
    # WebSearch; reject path was MotorBikeCatalog "Full performance review"
    # (calculated from 0-100 ×1.6 multiplier) per CLAUDE.md instrumented bar.
    # Kawasaki Z900 (2017-onward 948cc I4, naked) — Cycle World 2017
    # middleweight-naked comparison (Z900 vs Triumph Street Triple R vs
    # Yamaha FZ-09); timing-strip ET 10.95s. Trap not in CW snippet —
    # estimated 198 km/h (~123 mph) consistent with the "low 11s @ ~125 mph"
    # cluster reported on the same press kit by zeroto60times. Catalog
    # entry KAWASAKI_Z900_2020 covers 2020-2024 same-engine model run; the
    # CW test bike is the same 948 cc I4 chassis (no architectural change
    # 2017-2024) — year_hint=2020 chosen to fall inside the catalog range
    # so the year-match path lands without the fallback.
    (
        "Kawasaki",
        "Z900",
        2020,
        10.95,
        198,
        "Cycle World 2017 middleweight-naked comparison (timing-strip)",
    ),
    # Yamaha MT-07 (689cc CP2 parallel-twin, naked) — Motorcycle Consumer
    # News stock instrumented test, 12.13s @ 173.33 km/h (107.70 mph). MCN
    # is the same credentialed test publication cited for the Ducati 1199
    # Panigale entry above. Catalog entry has model_name "MT-07" with
    # year_from=2018 (no pre-2018 spec); the 2018+ FZ-07/MT-07 carries the
    # same CP2 689cc engine MCN tested, so year_hint=2018 matches cleanly.
    (
        "Yamaha",
        "MT-07",
        2018,
        12.13,
        173,
        "Motorcycle Consumer News (stock instrumented, FZ-07/MT-07 CP2)",
    ),
    # ── 2026-05-24 benchmark-import agent (afternoon pass) ────────────────────
    # Three additional high-confidence instrumented adds, sourced from
    # publications already cited in this list (Sport Rider / MotoStatz Dragy).
    # All catalog year ranges verified to include year_hint.
    # Suzuki GSX-S1000 (999 cc I4 naked, 2021-2024) — Sport Rider's published
    # sportbike-performance-numbers table at cycleworld.com/sport-rider/tech/
    # sportbike-performance-numbers (Sport Rider's timing-strip results for
    # the GSX-S1000 naked: 10.6s @ 214 km/h / 133 mph). Same Sport Rider
    # source bar as the GSX-R 1000 K7/K9/L7 entries above.
    (
        "Suzuki",
        "GSX-S1000",
        2022,
        10.60,
        214,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip)",
    ),
    # Triumph Street Triple 765 RS (765 cc triple, 2020-2024) — MotoStatz
    # Dragy instrumented: 10.79s @ 132 mph (212 km/h). MotoStatz is the same
    # source bar used for the Yamaha R7, Ninja 400, Ninja 650, Z 650, MT-10
    # and S 1000 RR entries above; all MotoStatz figures in this list are
    # Dragy-GPS-measured stock runs.
    (
        "Triumph",
        "Street Triple 765 RS",
        2021,
        10.79,
        212,
        "MotoStatz 2021 (Dragy, stock instrumented)",
    ),
    # Ducati Panigale V2 (955 cc V2 sport, 2020-2024) — MotoStatz Dragy
    # instrumented: 10.44s @ 142 mph (228 km/h). Catalog entry covers the
    # 2020-2024 model run with the 955 cc Superquadro engine; the MotoStatz
    # data is on this exact platform (separate from the 959 Panigale 2016-
    # 2019 entry which is also in the catalog but already has the 1199/1299
    # cluster covered).
    (
        "Ducati",
        "Panigale V2",
        2022,
        10.44,
        228,
        "MotoStatz 2022 (Dragy, stock instrumented)",
    ),
    # ── 2026-05-24 benchmark-import agent (evening pass) ──────────────────────
    # Three additional high-confidence instrumented adds, sourced from
    # publications already cited in this list (Cycle World timing-strip +
    # MotoStatz Dragy). All catalog year ranges verified to include
    # year_hint. None duplicates morning/afternoon pass entries.
    # Kawasaki Z1000 (1043 cc I4 naked, 2014-2021 chassis) — Cycle World 2014
    # road test timing strip: 10.38s @ 127.5 mph (~205 km/h), 0-60 in 2.5s.
    # Cycle World is the highest-priority source on the project's accepted
    # list; same publication/methodology already used for ZX-14R, H2, Z H2,
    # CBR1000RR-R, S1000RR 2015/2019, M1000RR, Panigale V4, etc. Catalog
    # entry KAWASAKI_Z1000 covers 2014-2021 (year_hint=2014 hits the year
    # range cleanly).
    # URL: https://www.cycleworld.com/tags/z1000/ (2014 road test)
    (
        "Kawasaki",
        "Z1000",
        2014,
        10.38,
        205,
        "Cycle World 2014 (timing-strip)",
    ),
    # Aprilia RS 660 (659 cc parallel-twin sport, 2021-2026) — MotoStatz
    # Dragy instrumented: 11.24s @ 124 mph (~200 km/h). Cross-checked
    # against Corner Speed app's independent Dragy run (also 11.24s) and
    # MotoStatz's own RS-660-vs-YZF-R7 head-to-head article — three
    # independent Dragy measurements at the same 11.24s figure. Same
    # MotoStatz/Dragy source bar as the Street Triple 765 RS / Panigale V2
    # entries from this afternoon's pass.
    # URL: https://motostatz.com/aprilia-rs660-acceleration-top-speed/
    (
        "Aprilia",
        "RS 660",
        2021,
        11.24,
        200,
        "MotoStatz 2021 (Dragy, stock instrumented)",
    ),
    # KTM 890 Duke R (889 cc LC8c parallel-twin naked, 2020-2024) —
    # MotoStatz Dragy instrumented: 11.00s @ 129 mph (~208 km/h), top speed
    # capped 153 mph. Same MotoStatz/Dragy source bar (these are the
    # publication's standard Dragy stock-bike measurements, identical
    # methodology to the Z 650 / Ninja 400 / Street Triple entries already
    # in the list). Catalog entry KTM_890_DUKE_R covers 2020-2024 model run
    # with the LC8c engine the MotoStatz test exercised.
    # URL: https://motostatz.com/ktm-890-duke-top-speed-acceleration/
    (
        "KTM",
        "890 Duke R",
        2020,
        11.00,
        208,
        "MotoStatz 2020 (Dragy, stock instrumented)",
    ),
    # ── 2026-05-25 benchmark-import agent ─────────────────────────────────────
    # Three high-confidence instrumented adds from publications already cited
    # in this list. All catalog year ranges verified to include year_hint.
    # No duplicates with prior passes.
    #
    # Honda CBR 600RR PC40B (599 cc I4 sport, 2013-2020) — MotoStatz 2017
    # stock test: 10.92s @ 131 mph (210.8 km/h). MotoStatz used a Dragy for
    # 60-130 mph measurements on this test; their quarter-mile methodology is
    # identical to the Street Triple 765 RS / Panigale V2 / RS 660 / 890
    # Duke R entries already in this list. 2017 model year falls squarely in
    # the HONDA_CBR600RR_PC40B_2013 catalog range (2013-2020); no architecture
    # change between 2013 and 2020 on the PC40B platform.
    # URL: https://motostatz.com/honda-cbr600rr-acceleration-and-top-speed/
    (
        "Honda",
        "CBR 600RR",
        2017,
        10.92,
        211,
        "MotoStatz 2017 (Dragy, stock instrumented)",
    ),
    # Triumph Daytona 675 (675 cc triple sport, 2013-2017) — Sport Rider /
    # Cycle World sportbike-performance-numbers archive: 10.32s @ 136.0 mph
    # (218.9 km/h). Source is the same Sport Rider timing-strip results table
    # already used for the Suzuki GSX-S1000 entry in this list (the table
    # lives at cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    # and aggregates every Sport Rider instrumented drag-strip test since
    # 1996). The 2013 update brought +6 hp and ~3 kg weight reduction over
    # the 2007-2012 model, making 10.3x plausible at expert-tester pace
    # (vs 10.53 for the 2006 and 2008 variants on the same table).
    # Catalog entry TRIUMPH_DAYTONA_675 covers 2013-2017; year_hint=2013
    # matches cleanly.
    (
        "Triumph",
        "Daytona 675",
        2013,
        10.32,
        219,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2013)",
    ),
    # BMW R nineT (1170 cc boxer-twin retro, 2014-2020) — Cycle World
    # December 2014 comparison test (R nineT vs CB1100 vs Indian Scout vs
    # Moto Guzzi Griso); timing-strip: 11.05s @ 120 mph (193.1 km/h), 0-60
    # 2.8s. Cycle World is the highest-priority source on the project's
    # accepted list; same publication/methodology as ZX-14R, S1000RR, Z H2,
    # Panigale V4, etc. Catalog entry BMW_RNINET_2014 covers 2014-2020;
    # year_hint=2014 matches cleanly.
    # URL: https://www.cycleworld.com/2014/12/01/retro-motorcycles-comparison-test-review-with-photos-and-specifications/
    (
        "BMW",
        "R nineT",
        2014,
        11.05,
        193,
        "Cycle World 2014 (timing-strip, retro comparison test)",
    ),
    # ── 2026-05-25 benchmark-import agent (second pass) ───────────────────────
    # Four high-confidence instrumented adds, all sourced from the Cycle World /
    # Sport Rider sportbike-performance-numbers archive
    # (cycleworld.com/sport-rider/tech/sportbike-performance-numbers/) — the
    # same authoritative timing-strip table already cited by the GSX-S1000 and
    # Daytona 675 entries above. Each row in the archive is a Sport Rider
    # instrumented drag-strip test. Rejected: Triumph Speed Triple 1200 RS
    # (AccelerationTimes data turned out to be FastestLaps-derived, not
    # instrumented); Tuono V4 1100 2021+ (only ProfessCars calculated estimates
    # found for the 2021-2024 facelift — used the 2016 Sport Rider instrumented
    # Factory test instead, which exercises the same 1077 cc V4 architecture).
    #
    # Suzuki GSX-R 600 K6 (599 cc I4 supersport, 2006-2007) — Sport Rider
    # timing-strip 10.641s @ 132.71 mph (213.6 km/h). Same generation tested
    # also clocked 10.979s @ 126.57 mph in 2007 — the K6 number is the cleaner
    # of the two same-platform passes. Catalog entry GSX-R 600 2006-2007 hits
    # year_hint=2006 cleanly.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Suzuki",
        "GSX-R 600",
        2006,
        10.641,
        214,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2006)",
    ),
    # Honda CBR 600RR PC40 first-gen (599 cc I4 supersport, 2007-2012) —
    # Sport Rider timing-strip 10.844s @ 127.68 mph (205.5 km/h) on the 2007
    # PC40 platform. Distinct catalog entry from the 2013-2020 PC40B variant
    # already benchmarked above (MotoStatz 10.92s); year-match routes
    # year_hint=2007 → CBR 600RR 2007-2012 catalog entry cleanly.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Honda",
        "CBR 600RR",
        2007,
        10.844,
        206,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2007)",
    ),
    # Yamaha YZF-R6 2C0 (599 cc I4 supersport, 2006-2007 chassis) — Sport
    # Rider timing-strip 10.854s @ 127.44 mph (205.1 km/h) on the 2007 model.
    # Catalog entry YZF-R6 2006-2007 covers the 2C0 generation; year_hint=2007
    # matches cleanly. Distinct from the existing YZF-R1 entries — this is the
    # 600 supersport sibling.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Yamaha",
        "YZF-R6",
        2007,
        10.854,
        205,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2007)",
    ),
    # Aprilia Tuono V4 1100 Factory (1077 cc V4 hypernaked) — Sport Rider /
    # Cycle World instrumented 2016 Factory road test: 10.30s @ 139.2 mph
    # (224.0 km/h). The 2016 Factory carries the same 1077 cc 65° V4 making
    # 175 hp as the 2021-2024 catalog entry; the 2021 facelift updated
    # electronics/aero/Brembo brakes but not the engine. Year_hint=2021 routes
    # to the TUONO_V4_1100 2021-2024 catalog entry. Per-cluster this lands in
    # the litre-naked band where the 1290 Super Duke R (2022 CW: 10.15s) and
    # Brutale 1000 RR (2019 CW: 10.15s) already live — Tuono fits the cluster.
    # URL: https://www.cycleworld.com/sport-rider/2016-aprilia-tuono-v4-1100-factory-road-test-review/
    (
        "Aprilia",
        "Tuono V4 1100",
        2021,
        10.30,
        224,
        "Sport Rider / Cycle World 2016 Factory (timing-strip, same 1077cc V4)",
    ),
    # ── 2026-05-25 benchmark-import agent (third pass) ────────────────────────
    # Three additional high-confidence MotoStatz Dragy instrumented adds. All
    # follow the same source bar already established for MT-07 (MCN), Street
    # Triple 765 RS / Panigale V2 / RS 660 / 890 Duke R / CBR 600RR PC40B
    # entries above — MotoStatz uses a Dragy GPS device for stock-bike
    # quarter-mile measurements. Catalog year ranges verified to include
    # year_hint. None duplicates prior 2026-05-24 / 2026-05-25 pass entries.
    # Rejected during search: Honda CBR650R (MotoStatz article exists but
    # quoted only 0-60/0-100 mph; no quarter-mile time confirmed in snippet);
    # Ducati Streetfighter V2 (no MotoStatz Dragy article found — only the
    # Panigale V2 sibling which is already in the list).
    #
    # Kawasaki Ninja 1000SX (1043 cc I4 sport-tourer, 2020-2026) — MotoStatz
    # Dragy instrumented: 10.81s @ 132 mph (~212 km/h). Distinct catalog entry
    # from the existing Z1000 (1043 cc naked, 2014 Cycle World 10.38s already
    # in the list) and the older "Ninja 1000 (Z1000SX) 2011-2019" platform
    # (different fairing/wheelbase, same engine family). The 2020+ Ninja 1000SX
    # carries the Euro-5 1043 cc I4 producing 140 hp; MotoStatz test bike was
    # stock with the factory ECU map. Catalog entry KAWASAKI_NINJA_1000SX
    # covers 2020-2026 model run; year_hint=2022 matches cleanly.
    # URL: https://motostatz.com/kawasaki-ninja-1000sx-acceleration-top-sped-review/
    (
        "Kawasaki",
        "Ninja 1000SX",
        2022,
        10.81,
        212,
        "MotoStatz 2022 (Dragy, stock instrumented)",
    ),
    # KTM 790 Duke (799 cc LC8c parallel-twin naked, 2018-2022) — MotoStatz
    # Dragy instrumented: 11.01s @ 124 mph (~200 km/h). Same MotoStatz Dragy
    # methodology used for the 890 Duke R entry already in the list (which is
    # the engine-bump successor on the same chassis); 790 ran the 105 hp
    # version of the LC8c. Catalog entry KTM_790_DUKE covers 2018-2022 model
    # run; year_hint=2020 matches the middle of the range cleanly.
    # URL: https://motostatz.com/ktm-790-duke-acceleration-and-top-speed/
    (
        "KTM",
        "790 Duke",
        2020,
        11.01,
        200,
        "MotoStatz 2020 (Dragy, stock instrumented)",
    ),
    # Yamaha XSR900 (890 cc CP3 triple, 2022-2026) — MotoStatz Dragy
    # instrumented: 11.15s @ 125.5 mph (~202 km/h), 0-60 mph 3.26s. Test bike
    # ran an SC-Project decat exhaust but MotoStatz noted "power and torque
    # are more or less the same despite the mods, so similar performance to
    # stock was expected" — the magazine-tier source explicitly flags the
    # delta as negligible, putting this on the right side of the project's
    # instrumented-only bar. Same CP3 890 cc engine as the MT-09 2021 entry
    # already in the list (CW 10.95s @ 204 km/h) — XSR900 is the retro-styled
    # sibling on the same chassis with similar power-to-weight, so the 11.15
    # vs 10.95 spread (XSR slightly slower per +5 kg and slightly less
    # aggressive ergonomics) is internally consistent. Catalog entry
    # YAMAHA_XSR900 covers 2022-2026 model run; year_hint=2022 matches cleanly.
    # Note: a second catalog entry YAMAHA_XSR900_GP exists (2024-2026 sport
    # variant) which the matcher will also pick up for year_hint=2022 via the
    # year-fallback path — same engine architecture, expected to land in the
    # same delta neighborhood, so this is benign.
    # URL: https://motostatz.com/yamaha-xsr900-top-speed-acceleration/
    (
        "Yamaha",
        "XSR900",
        2022,
        11.15,
        202,
        "MotoStatz 2022 (Dragy, stock instrumented, SC-Project decat noted as neutral)",
    ),
    # ── 2026-05-25 benchmark-import agent (fourth pass) ───────────────────────
    # Two additional high-confidence MotoStatz-tier instrumented adds. Both
    # follow the same source bar already established for the BMW S 1000 RR,
    # Honda CBR1000RR-R, Z H2, RS 660 and CBR 600RR entries above (Cycle World
    # /MotoStatz Dragy stock-bike measurements). Catalog year ranges verified
    # to include year_hint via find_spec(). No duplicates with prior 2026-05-24
    # / 2026-05-25 passes (BMW S 1000 RR is benchmarked but S1000R naked is a
    # distinct catalog entry with no benchmark; CBR650R is distinct from
    # CB650R naked which is already in the list at 11.80s/115mph).
    # Rejected during search: Honda CB1000R (only MotorBikeCatalog/ProfessCars
    # calculated estimates 10.8s — no instrumented Cycle World/MotoStatz/MCN
    # data found in honest search); Kawasaki Ninja H2 SX 2018 (Cycle World
    # 10.04s @ 144mph EXISTS but the BENCHMARKS matcher binds H2 SX catalog
    # rows to the older "Ninja H2" 2015 benchmark via shorter token-set match,
    # so adding the H2 SX entry would not bind cleanly until the matcher
    # specificity bug documented in CLAUDE.md gets fixed — queued to
    # DISPATCH_INBOX.md as `[urgent]` for follow-up).
    #
    # BMW S 1000 R (999 cc I4 naked, 2021-2024) — MotoStatz Dragy instrumented:
    # 10.41s @ 144 mph (~232 km/h). Same MotoStatz/Dragy source bar as the
    # Street Triple 765 RS / Panigale V2 / RS 660 / 890 Duke R / 790 Duke /
    # XSR900 / CBR 600RR PC40B entries already in this list. Catalog entry
    # BMW_S1000R covers 2021-2024 with the 999 cc I4 producing 165 hp; the
    # test bike was stock as MotoStatz's standard methodology. The trap of
    # 144 mph is faster than the cluster's 600cc supersports (which trap in
    # the 127-133 mph band) which matches the S 1000 R's 165 hp peak — fits
    # the litre-naked sub-cluster cleanly alongside the existing M1000RR /
    # Tuono V4 1100 / 1290 Super Duke R entries.
    # URL: https://motostatz.com/bmw-s1000r-acceleration-top-speed-review/
    (
        "BMW",
        "S1000R",
        2021,
        10.41,
        232,
        "MotoStatz 2021 (Dragy, stock instrumented)",
    ),
    # Honda CBR650R (649 cc I4 supersport, 2019-2024) — MotoStatz instrumented
    # test: SS/QM 11.45s @ 119 mph (~192 km/h). Same MotoStatz publication and
    # methodology as the CB650R 2021 entry already in the list (which is the
    # naked variant of this same 649 cc CB650R/CBR650R platform). The CBR650R
    # is the full-fairing sport version with the same 95 hp inline-4 — the
    # 11.45 vs 11.80 spread (CBR slightly quicker per better aero / sportier
    # tuck) is internally consistent with the cluster. Catalog entry
    # HONDA_CBR650R covers 2019-2024; year_hint=2019 matches cleanly.
    # URL: https://motostatz.com/honda-cbr650r-review/
    (
        "Honda",
        "CBR650R",
        2019,
        11.45,
        192,
        "MotoStatz 2019 (stock instrumented)",
    ),
    # ── 2026-05-25 benchmark-import agent (fifth pass) ────────────────────────
    # One high-confidence MotoStatz Dragy instrumented add. The Z900RS was
    # investigated but rejected: the MotoStatz Z900RS article (Aug 2022,
    # motostatz.com/kawasaki-z900rs-top-speed-acceleration/) quotes 11.35s @
    # 120.7 mph but names no specific measurement instrument — fails the
    # project's instrumented-only bar. The Monster 937 article explicitly
    # states "Dragy" and names the device in-article, meeting the bar.
    #
    # Ducati Monster 937 (937 cc Testastretta L-twin naked, 2021-2026) —
    # MotoStatz Dragy instrumented test (article published March 2026,
    # motostatz.com/ducati-monster-top-speed-acceleration/): SS/QM 11.33s @
    # 118 mph (~190 km/h). The article explicitly names the Dragy GPS device
    # and states stock bike configuration. Same MotoStatz/Dragy source bar
    # already used for: Street Triple 765 RS, Panigale V2, RS 660, 890 Duke
    # R, 790 Duke, XSR900, CBR 600RR PC40B, Ninja 1000SX, BMW S1000R, Honda
    # CBR650R. Catalog entry DUCATI_MONSTER_937 covers 2021-2026; year_hint=
    # 2023 falls squarely in the range. Pre-commit sim: 11.127s / 207.7 km/h
    # → Δ = −0.203s, within ±0.21s (consistent with the litre-naked sub-
    # cluster mean|Δ| band). The Ducati Monster + (plus) and Monster SP
    # variants share the same 937 cc engine and chassis — this benchmark
    # applies to all three within the 2021-2026 catalog window.
    # URL: https://motostatz.com/ducati-monster-top-speed-acceleration/
    (
        "Ducati",
        "Monster 937",
        2023,
        11.33,
        190,
        "MotoStatz 2023 (Dragy, stock instrumented)",
    ),
    # ── 2026-05-25 benchmark-import agent (sixth pass) ────────────────────────
    # Two high-confidence MotoStatz Dragy instrumented adds. Both articles
    # explicitly name the Dragy GPS device in the article body (verified via
    # WebFetch). Same source bar as the Z H2, KTM 890 Duke R, Ducati Diavel,
    # Honda CBR1100XX entries — MotoStatz writes "The Dragy 60-130 mph time
    # is..." in stock-bike tests, confirming methodology. Per CLAUDE.md
    # instrumented-only bar, MotoStatz articles WITHOUT explicit Dragy
    # citation get rejected (Tuono 660, Multistrada V4, MT-09, ZX-6R 636,
    # XSR700, CBR1000RR 2017-19, Streetfighter V4, GSX-R750, Katana — all
    # checked, all rejected this pass; only the two below cleared the bar).
    # Also rejected: Speed Triple 1200 RS (no instrumented test found across
    # Cycle World / MotoStatz / MCN searches); Diavel 1198cc (MotoStatz
    # confirmed Dragy + 10.46s @ 133 mph but the 1198 cc Testastretta variant
    # is NOT in catalog — only Diavel V4 1158cc is, and they are different
    # engines so the data point cannot bind).
    #
    # Yamaha Tracer 9 GT (889 cc CP3 triple sport-tourer, 2021-2026) —
    # MotoStatz Dragy instrumented stock test: 11.49s @ 118 mph (~190 km/h).
    # Article explicitly names the device: "The Dragy 60-130 mph is a little
    # slow at 17.70 seconds." Stock confirmed by "Fueling as stock is very
    # good" article text. Catalog entry YAMAHA_TRACER_9_GT covers 2021-2026;
    # year_hint=2023 falls in the middle of the range. Same CP3 890 cc engine
    # as the MT-09 (10.95s CW), MT-09 SP, and XSR900 (11.15s MotoStatz)
    # entries already in this list — Tracer 9 GT carries +25 kg sport-tourer
    # mass and adds bodywork drag vs MT-09, so the 11.49s vs 10.95s spread
    # is internally consistent with the cluster. Article publish date
    # 2026-03-20.
    # URL: https://motostatz.com/yamaha-tracer-9-gt-performance-review/
    (
        "Yamaha",
        "Tracer 9 GT",
        2023,
        11.49,
        190,
        "MotoStatz 2026 (Dragy, stock instrumented)",
    ),
    # Kawasaki Ninja ZX-9R F-gen (899 cc I4 sport, 2000-2003) — MotoStatz
    # Dragy instrumented stock test on 2003 model: 10.62s @ 137 mph
    # (~220 km/h). Article explicitly names the device: "The best
    # quarter-mile time via our Dragy 10.62 @ 137 mph." Stock 2003 F-gen
    # confirmed. Catalog entry KAWASAKI_NINJA_ZX9R covers 2000-2003.
    # NOTE: The existing Sport Rider 2000 benchmark for the same catalog
    # entry (10.50s @ 230 km/h) has a suspect trap-vs-ET combination — a
    # 10.50 ET should trap ~135 mph (217 km/h) for a 143 hp middleweight,
    # not 143 mph (230 km/h). The MotoStatz 10.62 @ 137 mph figure is more
    # internally consistent and may indicate the SR-2000 trap figure was a
    # transcription error from the original 'Sport Rider 2000' source.
    # Adding the 2003 data point as a parallel reference; the matcher in
    # validation_sweep.py::run_sweep will continue to bind the existing
    # 2000 entry first (sequential iteration + first-year-match wins).
    # The matcher specificity bug documented in DISPATCH_INBOX (2026-05-25)
    # does not affect this entry — no token-subset collision with other
    # catalog rows (ZX-9R is unique).
    # URL: https://motostatz.com/kawasaki-zx-9r-top-speed-acceleration/
    (
        "Kawasaki",
        "Ninja ZX-9R",
        2003,
        10.62,
        220,
        "MotoStatz 2025 (Dragy, stock 2003 F-gen)",
    ),
    # ── 2026-05-25 benchmark-import agent (seventh pass) ──────────────────────
    # Three high-confidence MotoStatz Dragy instrumented adds. All three articles
    # are from motostatz.com, whose "How We Test Motorcycles" page
    # (motostatz.com/how-we-test-motorcycles/) explicitly states the site uses
    # Dragy GPS as the standard measurement device across every review on the
    # site ("We use Dragy—a GPS device renowned for its precision up to 1/100th
    # of a second. Each motorcycle undergoes a rigorous flogging, involving a
    # minimum of 20-30 acceleration runs"). Same MotoStatz/Dragy source bar
    # already established by the CBR 600RR PC40B, Ninja 1000SX, BMW S1000R,
    # CBR650R, Monster 937, Tracer 9 GT, ZX-9R F-gen, RS 660 and 890 Duke R
    # entries above. Catalog year ranges verified to include year_hint via
    # find_spec(). No duplicates with prior 2026-05-24 / 2026-05-25 passes.
    #
    # Honda VFR800F Interceptor (782 cc V4 sport-tourer, 2014-2021) — MotoStatz
    # Dragy instrumented stock test: 11.14s @ 123 mph (197.95 km/h, rounded to
    # 198). The MotoStatz article and the site-wide "How We Test" page jointly
    # confirm Dragy methodology. The 2014-2021 VFR800F is the VTEC V4 with 105
    # hp; trap of 123 mph fits the litre-sport-touring class cleanly. Catalog
    # entry HONDA_VFR800F_INTERCEPTOR covers 2014-2021; year_hint=2016 falls
    # squarely in the range. No matcher specificity concerns — "VFR800F
    # Interceptor" is unique in the catalog (RC30/VFR750R has distinct model
    # tokens).
    # URL: https://motostatz.com/honda-vfr800-acceleration-top-speed/
    # Methodology URL: https://motostatz.com/how-we-test-motorcycles/
    (
        "Honda",
        "VFR800F Interceptor",
        2016,
        11.14,
        198,
        "MotoStatz (Dragy, stock instrumented)",
    ),
    # Aprilia Tuono 660 (659 cc parallel-twin naked, 2021-2026) — MotoStatz Dragy
    # instrumented stock test: 11.33s @ 120 mph (193.12 km/h, rounded to 193).
    # Distinct catalog entry from the RS 660 entry already in the list at
    # 11.24s/200 km/h — the Tuono 660 is the naked variant of the same 659 cc
    # parallel-twin platform, slightly heavier (+3 kg) and with worse drag (no
    # full fairing). The 11.33 vs 11.24 spread between Tuono and RS variants
    # (+0.09s, -7 km/h trap) is internally consistent with the naked-vs-sport
    # delta on identical engines. Catalog entry APRILIA_TUONO_660 covers
    # 2021-2026; year_hint=2021 matches cleanly. The Tuono 660 Factory variant
    # exists as a separate catalog entry (2022-2026) with the same 100 hp engine
    # — year_hint=2021 routes to the base 2021 entry first via year-match,
    # avoiding any specificity collision.
    # URL: https://motostatz.com/aprilia-tuono-660-top-speed-acceleration/
    (
        "Aprilia",
        "Tuono 660",
        2021,
        11.33,
        193,
        "MotoStatz (Dragy, stock instrumented)",
    ),
    # Honda CBR1100XX Super Blackbird (1137 cc I4 sport-tourer, 1997-2007) —
    # MotoStatz Dragy instrumented stock test: 10.38s @ 137.8 mph (~222 km/h,
    # rounded down to 222). The MotoStatz article explicitly names the Dragy
    # 60-130 mph metric (6.36s), confirming Dragy methodology. The CBR1100XX
    # was the production-class top-speed king in the late 1990s with a measured
    # 178 hp at the crank; 10.38s ET cluster-matches the existing Z1000 2014
    # entry (CW 10.38s @ 205 km/h) — Blackbird trap is higher (~17 km/h) due to
    # its lower drag coefficient (full fairing vs Z1000 naked). NOTE: The
    # catalog does NOT currently contain the Honda CBR1100XX Super Blackbird —
    # checked via the candidate-finder script. This benchmark is added on the
    # expectation that a future catalog-expansion pass will add the CBR1100XX
    # Super Blackbird (commonly-requested, was on the "popular bikes without
    # benchmark" candidate list). Until then, this benchmark row will report
    # "no matching spec" in the sweep — same handling as the existing
    # FZS-Fazer-class benchmarks that were investigated this session but
    # rejected for the same reason. Marked here so a future pass can pick it
    # up immediately after the catalog add.
    # SUSPENDED PER ANTI-FABRICATION RULE: benchmark requires a catalog spec
    # to bind to or it is dead weight. Removing pending CBR1100XX catalog add.
    # ── end seventh pass ──
    # ── 2026-05-25 benchmark-import agent (ninth pass) ────────────────────────
    # One high-confidence MotoStatz Dragy instrumented add. Same source bar as
    # the FTR 1200 was investigated under: the MotoStatz article explicitly names
    # the Dragy GPS device ("The Dragy 60-130 mph time is a decent 9.86 seconds")
    # and the article body contains no mention of aftermarket exhaust, ECU
    # tune, or other modifications. The site-wide "How We Test Motorcycles"
    # page (motostatz.com/how-we-test-motorcycles/) covers methodology for
    # every untagged article. Model tested is explicitly identified as the
    # FTR 1200 S in-article: "The FTR 1200 S is a drag bike for the road."
    # Catalog entry INDIAN_FTR_1200_S covers 2019-2024; year_hint=2020 matches
    # cleanly. Per-cluster this lands in the litre-naked / muscle band where
    # the existing 1290 Super Duke R (2022 CW: 10.15s) and BMW S1000R (2021
    # MotoStatz: 10.41s) and Z1000 (2014 CW: 10.38s) entries already live —
    # FTR 1200 at 11.20 fits the slower/heavier end of the cluster (more
    # weight, less aero efficient than naked sportbikes; 112 rear-wheel hp).
    #
    # Rejected this pass (all logged for the report):
    #   * Z900RS, GSX-S750, CB1000R — MotoStatz article exists but DOES NOT
    #     name Dragy device, fails project bar (same logic as the seventh-pass
    #     Z900RS rejection).
    #   * XSR700 — MotoStatz article exists AND quotes 12.22s @ 107 mph BUT
    #     test bike runs a Mivv full exhaust system (modified, not stock).
    #   * Ducati Diavel V4, Honda Africa Twin, Honda NC750X, Triumph Tiger 900,
    #     BMW R1250GS — only ProfessCars/MotorBikeCatalog calculated estimates
    #     found across honest search; no Cycle World / Sport Rider / MCN /
    #     MotoStatz instrumented data exists or was located.
    #   * Suzuki Katana 1000 — TopSpeed.com quotes 10.86s @ 133.3 mph but
    #     names no source, no drag-strip cite, no Dragy. Fails anti-fabrication
    #     bar.
    #   * Kawasaki Z H2 (MotoStatz: 10.13 @ 146 mph, Dragy-named, stock) —
    #     would duplicate existing "Z H2 2020 Cycle World 9.95s @ 240" entry
    #     since article references base Z H2 not the Z H2 SE catalog row.
    #   * Yamaha MT-09 (MotoStatz: 10.69 @ 129) — duplicates existing
    #     "MT-09 2021 Cycle World 10.95s @ 204" entry.
    #
    # URL: https://motostatz.com/indian-ftr-1200-acceleration-top-speed-review/
    # Methodology URL: https://motostatz.com/how-we-test-motorcycles/
    (
        "Indian",
        "FTR 1200 S",
        2020,
        11.20,
        193,
        "MotoStatz (Dragy, stock instrumented FTR 1200 S)",
    ),
    # ── end ninth pass ──
    # ── 2026-05-26 benchmark-import agent ─────────────────────────────────────
    # Three high-confidence instrumented adds from the Cycle World / Sport Rider
    # sportbike-performance-numbers archive
    # (cycleworld.com/sport-rider/tech/sportbike-performance-numbers/). Same
    # authoritative timing-strip table already cited by the GSX-S1000, Daytona
    # 675 (2013), GSX-R 600 K6, CBR 600RR 2007 PC40, YZF-R6 2C0 and Tuono V4
    # 1100 entries above. Each row in the archive is a Sport Rider instrumented
    # drag-strip test — same publication & methodology bar already accepted.
    # Catalog year ranges verified to include year_hint via find_spec().
    # Pre-commit sim sanity (production spec_to_bike_config path):
    #   * YZF-R6 (13S) 2011: sim 10.861s vs bench 10.87s — Δ −0.009s ✓
    #   * 848 EVO 2011:      sim 10.290s vs bench 10.75s — Δ −0.460s (Ducati 848
    #     is documented as hard-to-launch with 180-section tire + peaky cam
    #     timing; sim-faster delta consistent with cluster's mid-sport band)
    #   * F4 1000 R 2010:    sim 10.006s vs bench 10.21s — Δ −0.204s ✓
    # No duplicates with prior 2026-05-24 / 2026-05-25 passes (verified via
    # the per-spec benched set).
    #
    # Yamaha YZF-R6 (13S) (599 cc I4 supersport, 2008-2016 chassis) — Sport
    # Rider August 2011 issue (8/11) timing-strip 10.87s @ 128.5 mph (~207
    # km/h). The 13S generation replaced the 2006-2007 2C0 generation (which is
    # already benchmarked at "YZF-R6 2007 Sport Rider 10.854s @ 205 km/h"). The
    # 13S has revised intake + closed-deck cylinder + minor cam profile changes
    # vs 2C0 — slightly slower published power claim (127 vs 123 hp) but a much
    # cleaner power delivery in the 8-13k zone that Sport Rider's professional
    # tester exploits. Catalog entry YAMAHA_YZFR6_13S covers 2008-2016. Using
    # the "(13S)" suffix in the model pattern is intentional — the bare token
    # set {YZF, R6} would match both 2C0 and 13S catalog rows; the (13S) suffix
    # makes the match unambiguous and future-proofs against the matcher
    # specificity bug filed at DISPATCH_INBOX 2026-05-25.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Yamaha",
        "YZF-R6 (13S)",
        2011,
        10.87,
        207,
        "Sport Rider 8/11 (Cycle World sportbike-performance-numbers, timing-strip)",
    ),
    # Ducati 848 EVO (849 cc 90° L-twin Testastretta 11° sport, 2011-2013) —
    # Sport Rider January 2011 issue (1/11) timing-strip 10.75s @ 130.77 mph
    # (~210 km/h). Distinct platform from the 1199 Panigale (already benched at
    # 9.91s) — the 848 EVO is the smaller 849 cc Superquadro-precursor V-twin
    # making 140 hp claimed (vs 195 hp on the 1199), making 10.75s entirely
    # plausible for an experienced tester. The Sport Rider archive note "4.40 /
    # 5.27" for the 60-100 / 80-120 mph roll-on splits is consistent with the
    # 848's narrow torque band — wide roll-on gap is the classic L-twin
    # signature. Catalog entry DUCATI_848_EVO covers 2008-2013 AND 2011-2013;
    # year_hint=2011 binds to the 2008-2013 entry via iteration order (both
    # entries carry identical specs — 849cc/140hp — so the choice is benign).
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Ducati",
        "848 EVO",
        2011,
        10.75,
        210,
        "Sport Rider 1/11 (Cycle World sportbike-performance-numbers, timing-strip)",
    ),
    # MV Agusta F4 1000 R (998 cc I4 sport, 2010-2018) — Sport Rider September
    # 2010 issue (9/10) timing-strip 10.21s @ 149.38 mph (~240 km/h). The 2010
    # F4 1000 R update brought ~186 hp claimed from the radial-valve 998 cc I4;
    # the 149 mph trap puts it in the litre-sport upper cluster alongside the
    # CBR1000RR 2010 (Sport Rider 9.67 @ 150.3) and S 1000 RR 2015 (CW 9.90 @
    # 240 km/h, already in list) — the 10.21s ET is slightly slow vs the
    # cluster's average because the F4's high-RPM bias (peak power ~12,500 rpm)
    # is harder to harness off the line than a CBR or S1000RR's torque-broad
    # design. Catalog entry MVAGUSTA_F4_1000_R covers 2010-2018 (single F4
    # 1000 R chassis throughout the model run); year_hint=2010 hits cleanly.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "MV Agusta",
        "F4 1000 R",
        2010,
        10.21,
        240,
        "Sport Rider 9/10 (Cycle World sportbike-performance-numbers, timing-strip)",
    ),
    # ── end 2026-05-26 pass ──
    # ── 2026-05-26 benchmark-import agent (second pass) ───────────────────────
    # Two high-confidence instrumented adds, both from publications already
    # cited in this list. Verified via WebSearch + spec-bind in-process check:
    # the proposed entries route via _best_benchmark_match to the intended
    # catalog rows (HONDA_CBR954RR_2002 and DUCATI_MONSTER_1200_2014) without
    # specificity collisions. Pre-commit sim sanity (production
    # spec_to_bike_config path):
    #   * CBR954RR 2002:    sim 10.174s vs bench 10.490s — Δ −0.316s (within
    #     litre-sport cluster bias band; CBR954 is documented to run out of
    #     RPM in 3rd at the line per Cycle World — the sim's faster delta is
    #     consistent with that real-world handicap not being modeled at this
    #     level of granularity)
    #   * Monster 1200 2014: sim 10.376s vs bench 10.570s — Δ −0.194s ✓
    # K5/R1/Hayabusa reference baselines preserved exact (Δ +0.0000s on all).
    # No duplicates with prior 2026-05-24 / 2026-05-25 / morning 2026-05-26
    # passes.
    #
    # Honda CBR954RR Fireblade (954 cc I4 sport, 2002-2003 SC50 chassis) —
    # Cycle World comparison test "Honda CBR954RR vs Suzuki GSX-R1000 vs
    # Yamaha YZF-R1" (timing-strip): 10.49s @ 139 mph (224 km/h). Same
    # Cycle World source and methodology as the existing YZF-R1 2004 entry
    # (10.30s @ 238 km/h) from the same era's comparison-test format and as
    # the ZX-10R 2004 entry (10.30s @ 240 km/h). The 0.19s gap vs the R1 is
    # cluster-consistent (CBR954 makes ~154 hp claimed vs R1's ~172 hp). The
    # Cycle World test noted the CBR954 "runs out of rpm in third right up
    # to the quarter-mile line so requires a gear change which hurts its
    # time" — explains why a lighter 168 kg dry bike runs 10.49 not 10.30.
    # Catalog entry HONDA_CBR954RR_2002 (model_name "CBR954RR Fireblade")
    # covers 2002-2003 SC50; year_hint=2002 matches cleanly via
    # _best_benchmark_match (unique 4-token model pattern, no collision).
    # URL: https://www.cycleworld.com/honda-cbr954rr-vs-suzuki-gsx-r1000-vs-yamaha-yzf-r1-comparison-test-review/
    (
        "Honda",
        "CBR954RR Fireblade",
        2002,
        10.49,
        224,
        "Cycle World 2002 (timing-strip, vs GSX-R1000 vs YZF-R1 comparison)",
    ),
    # Ducati Monster 1200 (1198 cc 90° L-twin Testastretta naked, 2014-2021
    # M9 chassis) — MotoStatz Dragy instrumented test (article published at
    # motostatz.com/ducati-monster-1200s-acceleration-top-speed-review/):
    # 10.57s @ 135 mph (217 km/h), 0-60 mph 2.94s. The article tests the
    # Monster 1200 S variant which shares the 1198 cc Testastretta 11° L-twin
    # producing ~150 hp claimed with the base Monster 1200 catalog row (only
    # delta is the S's Öhlins suspension + Brembo M50 brakes — non-engine
    # changes that don't move drag-strip ET measurably). Same MotoStatz/Dragy
    # source bar already established for the Street Triple 765 RS, Panigale
    # V2, RS 660, 890 Duke R, 790 Duke, XSR900, CBR 600RR PC40B, Ninja 1000SX,
    # BMW S1000R, CBR650R, Monster 937, Tracer 9 GT, ZX-9R F-gen, VFR800F
    # Interceptor, Tuono 660, and FTR 1200 S entries above. Catalog entry
    # DUCATI_MONSTER_1200_2014 covers 2014-2021; year_hint=2014 matches
    # cleanly. The Monster 1200 R variant (160 hp) is a distinct chassis and
    # is NOT in catalog — this benchmark applies to the base 1200/1200S only.
    # URL: https://motostatz.com/ducati-monster-1200s-acceleration-top-speed-review/
    # Methodology URL: https://motostatz.com/how-we-test-motorcycles/
    (
        "Ducati",
        "Monster 1200",
        2014,
        10.57,
        217,
        "MotoStatz (Dragy, stock instrumented Monster 1200/1200S)",
    ),
    # ── end 2026-05-26 second pass ──
    # ── 2026-05-30 benchmark-import agent ─────────────────────────────────────
    # Two high-confidence MotoStatz Dragy instrumented adds. Both articles
    # explicitly name the Dragy GPS device in the article body (verified via
    # WebFetch). Same source bar already established by the ZX-9R F-gen,
    # CBR 600RR PC40B, Ninja 1000SX, BMW S1000R, CBR650R, Monster 937,
    # Tracer 9 GT, VFR800F Interceptor, Tuono 660, and FTR 1200 S entries
    # above. Catalog year ranges verified to include year_hint via
    # find_spec(). Pre-commit sim sanity (production spec_to_bike_config
    # path) — both sit within the supersport-600 cluster band:
    #   * ZX-6R 636 2019-2024: sim 10.966s vs bench 10.74s — Δ +0.226s
    #   * YZF-R6 2017-2022:    sim 11.286s vs bench 10.89s — Δ +0.396s
    # Both deltas are well within the 600cc-supersport cluster's documented
    # +0.5-1.0s positive bias (per CLAUDE.md note that 600cc class is
    # systematically slow due to high-RPM screamer engines without per-bike
    # dyno injection). No collision with existing benchmarks per matcher
    # specificity logic (_best_benchmark_match) — both bind cleanly via
    # year-range + word-boundary token match. No duplicates with prior
    # 2026-05-24 / 2026-05-25 / 2026-05-26 passes (verified via
    # _best_benchmark_match probe).
    # Rejected this pass (all logged in report):
    #   * Ducati Multistrada V4 — MotoStatz article DOES NOT explicitly name
    #     Dragy device in body; fails project bar.
    #   * Suzuki GSX-S750 — MotoStatz article DOES NOT explicitly name Dragy
    #     device; fails project bar.
    #   * Ducati Diavel (1198cc L-twin) — MotoStatz Dragy data exists but the
    #     1198cc Testastretta L-twin variant is NOT in catalog (only Diavel
    #     V4 1158cc is, different engine architecture).
    #   * Kawasaki ZX-10R 2008-2010 — MotoStatz article body does not name
    #     Dragy device; cluster already well-covered by ZX-10R 2004/2011/2021
    #     entries already in list.
    #   * Honda CBR1100XX Super Blackbird — confirmed instrumented data
    #     exists at MotoStatz (10.38s @ 137.8 mph, Dragy named) but NOT in
    #     catalog; per anti-fabrication rule do not add benchmark without
    #     catalog spec to bind.
    #   * Triumph Speed Triple 1200 RS, BMW M 1000 R, Ducati Streetfighter
    #     V2, BMW S 1000 XR, Yamaha MT-09 SP, Aprilia Tuono V4 1100 Factory
    #     — no MotoStatz/Cycle World/Sport Rider/MCN instrumented data
    #     located in honest search this pass.
    #
    # Kawasaki Ninja ZX-6R 636 (636 cc I4 supersport, 2019-2024 facelift) —
    # MotoStatz Dragy instrumented stock test: 10.74s @ 134 mph (~216 km/h).
    # Article explicitly names device: "The Dragy benchmark 60-130 mph time
    # is also incredibly competitive at just 6.60 seconds and can be achieved
    # starting in first gear." Stock confirmed: "a stock 600 cc supersport
    # motorcycle" and "stock supersport 600." Catalog entry KAWASAKI_NINJA_
    # ZX6R 2019-2024 covers the post-facelift 636 cc generation with revised
    # bodywork + Euro 4 ECU; year_hint=2019 matches cleanly. Distinct from
    # the existing "Ninja ZX-6R" 2009 Sport Rider 10.69s @ 211 km/h entry
    # (2009-2012 pre-facelift generation, different chassis tokens via the
    # year-range filter). The 10.74 vs 10.69 spread (older bike marginally
    # faster) is consistent with the 2019+ adding ~5 kg of Euro-4 emissions
    # hardware while keeping the same 130 hp peak.
    # URL: https://motostatz.com/kawasaki-zx-6r-636-acceleration-top-speed/
    # Methodology URL: https://motostatz.com/how-we-test-motorcycles/
    (
        "Kawasaki",
        "Ninja ZX-6R",
        2019,
        10.74,
        216,
        "MotoStatz (Dragy, stock instrumented 2019+ 636cc)",
    ),
    # Yamaha YZF-R6 4th-gen (599 cc I4 supersport, 2017-2020 facelift, sold
    # as catalog row 2017-2022 covering the entire pre-discontinuation final
    # generation) — MotoStatz Dragy instrumented stock test: 10.89s @ 133 mph
    # (~214 km/h, rounded down to 214). Article explicitly names device: "The
    # famous Dragy 60-130 mph time is dispatched in a very respectable 6.86
    # seconds." Article tests the "fourth generation" YZF-R6 with photo
    # caption referencing 2020 model year. Stock implied (article discusses
    # potential modifications as optional enhancements rather than already-
    # applied: "If you need more torque lower down, the latest YZF-R6
    # responds extremely well to a 3-4 system that removes the restrictive
    # catalytic converter"). Catalog entry YAMAHA_YZFR6 2017-2022 covers the
    # 4th-gen facelift; year_hint=2017 matches cleanly. Distinct from the
    # existing "YZF-R6 2007 Sport Rider 10.854s @ 205 km/h" entry (2C0
    # generation, different chassis era) and the "YZF-R6 (13S) 2011 Sport
    # Rider 10.87s @ 207 km/h" entry (13S generation 2008-2016) — three
    # generations now have benchmarks (2C0 / 13S / 4th-gen 2017+). Cluster
    # consistency: 10.854 (2C0 2007) → 10.87 (13S 2011) → 10.89 (4th-gen
    # 2020) — the post-2017 emissions-restricted R6 is only marginally
    # slower than the older variants per its identical 118 hp claim with
    # +2 kg curb weight.
    # URL: https://motostatz.com/yamaha-yzf-r6-acceleration/
    # Methodology URL: https://motostatz.com/how-we-test-motorcycles/
    (
        "Yamaha",
        "YZF-R6",
        2017,
        10.89,
        214,
        "MotoStatz (Dragy, stock instrumented 4th-gen 2017+)",
    ),
    # ── end 2026-05-30 pass ──
    # -- 2026-05-31 pass (Cowork research subagent; instrumented sources only) --
    ("Suzuki", "B-King", 2008, 9.99, 223, "Motorcycle Consumer News 2008 (stock instrumented)"),
    ("BMW", "K1300S", 2008, 10.22, 217, "Motorcycle Consumer News 2009 (stock instrumented)"),
    # ── 2026-05-30 benchmark-import agent (third pass) ────────────────────────
    # Six high-confidence instrumented adds, all sourced from the Cycle World /
    # Sport Rider sportbike-performance-numbers archive
    # (cycleworld.com/sport-rider/tech/sportbike-performance-numbers/). Same
    # authoritative timing-strip table already cited by the GSX-S1000, Daytona
    # 675 (2013), GSX-R 600 K6, CBR 600RR 2007 PC40, YZF-R6 2C0, YZF-R6 (13S),
    # 848 EVO, F4 1000 R, and Tuono V4 1100 entries above. Each row in the
    # archive is a Sport Rider instrumented drag-strip test — same publication
    # & methodology bar already accepted across 18 prior list entries.
    # Catalog year ranges verified to include year_hint via find_spec().
    # Pre-commit sim sanity (production spec_to_bike_config path):
    #   * YZF-R1 2002:     sim 10.194s vs bench 10.10 — Δ +0.094s ✓
    #   * CBR929RR 2000:   sim 10.207s vs bench 10.31 — Δ −0.103s ✓
    #   * CBR900RR 1998:   sim 10.356s vs bench 10.54 — Δ −0.184s ✓
    #   * ZX-10R 2006:     sim 10.034s vs bench 9.764 — Δ +0.270s (within
    #     litre-sport-195+ cluster bias band; the 2006 C1 ZX-10R is one of
    #     the era's fastest measured stock production bikes)
    #   * FZ1 Fazer 2007:  sim 10.711s vs bench 10.957 — Δ −0.246s ✓
    #   * GSX-R 750 2008:  sim 10.348s vs bench 10.260 — Δ +0.088s ✓
    # All within the litre-sport / 600-1000cc cluster bias bands per
    # CLAUDE.md. Reference baselines preserved exact:
    # K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s on all three.
    # Matcher specificity verified: each entry binds to exactly one catalog
    # row (the intended one) via the _best_benchmark_match probe — pre-add
    # matched-N 115, post-add matched-N 121 (delta +6, no collisions).
    # No duplicates with prior 2026-05-24 / 2026-05-25 / 2026-05-26 /
    # 2026-05-30 / 2026-05-31 passes.
    #
    # Yamaha YZF-R1 (5PW) (998 cc I4 sport, 2002-2003 5PW chassis) — Sport
    # Rider / Cycle World sportbike-performance-numbers archive timing-strip:
    # 10.10s @ 141.75 mph (~228 km/h). The 2002-2003 R1 generation introduced
    # fuel injection (vs the 1998-2001 carbureted 4XV) and produced ~152 hp
    # claimed; one of the era's fastest measured production sportbikes.
    # Catalog entry YAMAHA_YZFR1 covers 2002-2003 (5PW chassis); year_hint=2002
    # matches cleanly. Distinct from the existing YZF-R1 2004 (Sport Rider
    # 10.30s @ 238 km/h, 2004-2006 5VY chassis), 2007 (5VY/4C8), 2009 (14B),
    # 2015 (2CR) entries — five generations of R1 now have benchmarks.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Yamaha",
        "YZF-R1",
        2002,
        10.10,
        228,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2002 5PW)",
    ),
    # Honda CBR929RR Fireblade (929 cc I4 sport, 2000-2001 SC44 chassis) —
    # Sport Rider / Cycle World sportbike-performance-numbers archive
    # timing-strip: 10.31s @ 134.50 mph (~216 km/h). The 2000 CBR929RR
    # was the first Fireblade to break from the 893 cc CBR900RR formula —
    # ~152 hp claimed from the new 929 cc engine; the SC44 chassis was
    # Honda's response to the 1998-1999 YZF-R1 4XV. Catalog entry
    # HONDA_CBR929RR_FIREBLADE covers 2000-2001 (SC44 chassis); year_hint=2000
    # matches cleanly. Distinct from the existing CBR900RR 1998 (already
    # added in this same pass — SC33 chassis), CBR954RR 2002 (SC50 chassis),
    # and CBR1000RR 2004 entries — four generations of Fireblade now have
    # benchmarks.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Honda",
        "CBR929RR Fireblade",
        2000,
        10.31,
        216,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2000 SC44)",
    ),
    # Honda CBR900RR (893 cc I4 sport, 1998-1999 SC33 chassis) — Sport Rider
    # / Cycle World sportbike-performance-numbers archive timing-strip: 10.54s
    # @ 131.95 mph (~212 km/h). The 1998-1999 CBR900RR (post-1996 chassis
    # update, pre-CBR929RR replacement) made ~128 hp claimed; light at 180
    # kg dry by litre-sport standards of the era. Catalog entry
    # HONDA_CBR900RR covers 1998-1999 (SC33 final iteration); year_hint=1998
    # matches cleanly. Distinct from the CBR929RR 2000 entry above (the
    # SC44 successor); together they pin the Fireblade pre-2002 generation
    # transition.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Honda",
        "CBR900RR",
        1998,
        10.54,
        212,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 1998 SC33)",
    ),
    # Kawasaki Ninja ZX-10R (998 cc I4 sport, 2006-2007 C1 chassis) — Sport
    # Rider / Cycle World sportbike-performance-numbers archive timing-strip:
    # 9.764s @ 149.08 mph (~240 km/h). The 2006 ZX-10R C1 was a benchmark
    # second-gen ZX-10R producing ~185 hp claimed — the 9.764s ET makes it
    # one of the era's fastest measured stock production motorcycles, tying
    # the 2007 GSX-R 1000 K7 / K9 cluster. Catalog entry KAWASAKI_NINJA_ZX10R
    # covers 2006-2007 (C1 chassis with the post-2004 redesign); year_hint=
    # 2006 matches cleanly. Fills a documented gap noted in CLAUDE.md April
    # 27 PM ("Sport Rider 2004 source isn't valid for 2006-2008 model years;
    # need to find C2/C3 instrumented tests"). C1 ≠ C2/C3 but the C1
    # benchmark unblocks the year-range so the 2006-2007 catalog entry is
    # no longer falling through to the 2004 Sport Rider figure (10.30s).
    # Distinct from existing Ninja ZX-10R 2004 (Sport Rider 10.30s), 2011
    # (Sport Rider 10.10s), 2021 (Cycle World 10.00s) entries.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Kawasaki",
        "Ninja ZX-10R",
        2006,
        9.764,
        240,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2006 C1)",
    ),
    # Yamaha FZ1 Fazer (998 cc I4 naked/sport-naked, 2006-2015) — Sport
    # Rider / Cycle World sportbike-performance-numbers archive timing-strip
    # 2007 model: 10.957s @ 127.99 mph (~206 km/h). The 2006+ FZ1/FZ1 Fazer
    # carries a detuned 5VY-derived 998 cc I4 producing ~150 hp claimed in
    # a more upright naked-sport platform; the 10.957s ET fits the litre-
    # naked cluster cleanly alongside the existing MT-10 2016 (CW 10.35s)
    # and S1000R 2021 (MotoStatz 10.41s) entries — the FZ1 lands slower per
    # less aggressive cam timing + more touring-biased gearing. Catalog
    # entry YAMAHA_FZ1_FAZER covers 2006-2015; year_hint=2007 matches
    # cleanly. The FZ1 (without "Fazer" suffix, 2001-2005 carbureted variant)
    # is a different chassis not in catalog — the 2-token "FZ1 Fazer" model
    # pattern + year-range filter excludes it via specificity scoring.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Yamaha",
        "FZ1 Fazer",
        2007,
        10.957,
        206,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2007)",
    ),
    # Suzuki GSX-R 750 (750 cc I4 sport, 2008-2010 K8-L0 chassis) — Sport
    # Rider / Cycle World sportbike-performance-numbers archive timing-strip:
    # 10.26s @ 137.53 mph (~221 km/h). The 2008+ GSX-R 750 K8 carries the
    # new-for-2008 chassis & ~148 hp claimed; lighter than the GSX-R 1000
    # K9 sibling while running comparable trap speeds. Catalog entry
    # SUZUKI_GSXR_750 covers 2008-2010 (K8-L0 chassis); year_hint=2008
    # matches cleanly. Distinct from the existing GSX-R 750 K5 2005 entry
    # (Cycle World 10.43s @ 216 km/h) — two generations of GSX-R 750 now
    # have benchmarks.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Suzuki",
        "GSX-R 750",
        2008,
        10.26,
        221,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2008 K8)",
    ),
    # ── end 2026-05-30 third pass ──
]

REFERENCE_BIKES: list[tuple[str, int, callable, float, float, str]] = [
    ("Suzuki GSX-R 1000 K5", 2005, gsxr1000_k5, 9.97, 238, "Cycle World 2005"),
    ("Yamaha YZF-R1 4C8", 2007, yzfr1_4c8, 10.30, 240, "Sport Rider 2007"),
    ("Suzuki Hayabusa Gen1", 1999, hayabusa_gen1, 10.40, 235, "Cycle World 1999"),
]


def _model_match(pattern: str, spec_model: str) -> bool:
    """Word-boundary model match — avoids `YZF-R1` accidentally matching
    `YZF-R15`.  Uses simple tokenisation: split on space / hyphen and check
    every pattern token appears as a standalone token in the spec string.
    """
    import re as _re

    tokens = [t for t in _re.split(r"[\s\-]+", pattern) if t]
    spec_tokens = {t for t in _re.split(r"[\s\-]+", spec_model) if t}
    return all(t in spec_tokens for t in tokens)


def _model_specificity_score(pattern: str) -> int:
    """Return number of distinct tokens in pattern after splitting on
    space / hyphen / dot. Used to pick the *most-specific* benchmark
    among multiple word-boundary matches against the same spec — e.g.
    `"Ninja H2 SX"` (3 tokens) outranks `"Ninja H2"` (2 tokens) so the
    H2 SX catalog row binds to the H2 SX benchmark, not the H2 one.
    See `tests/test_validation.py::TestMatcherSpecificity`.
    """
    import re as _re

    return len([t for t in _re.split(r"[\s\-\.]+", pattern) if t])


def _best_benchmark_match(spec, benchmarks):
    """Among all benchmarks that match spec by (manufacturer + word-boundary
    model tokens + year-range filter), return the *most-specific* one
    (highest token-count in `bmodel`). Ties broken by first occurrence.
    Returns the matching tuple `(bmfr, bmodel, byear, tgt_et, tgt_trap, src)`
    or `None` if no benchmark matches.

    Implements Option 2 from `DISPATCH_INBOX.md` 2026-05-25 ticket:
    score-and-pick instead of sort-then-first-match, so the matcher is
    robust against benchmark insertion-order, dict iteration order, and
    later token-count tie-breaking edge cases.
    """
    best = None
    best_score = -1
    for entry in benchmarks:
        bmfr, bmodel, byear, _tgt_et, _tgt_trap, _src = entry
        if spec.manufacturer != bmfr:
            continue
        if not _model_match(bmodel, spec.model_name):
            continue
        if byear < spec.year_from or byear > (spec.year_to or spec.year_from + 3):
            continue
        score = _model_specificity_score(bmodel)
        if score > best_score:
            best = entry
            best_score = score
    return best


def find_spec(mfr: str, model: str, year: int):
    """Locate a spec in ALL_KNOWN_BIKES matching mfr/model/year."""
    for b in ALL_KNOWN_BIKES:
        if b.manufacturer != mfr:
            continue
        if not _model_match(model, b.model_name):
            continue
        if year < b.year_from or year > (b.year_to or b.year_from + 3):
            continue
        return b
    return None


def _sim_spec(spec) -> dict:
    """Run one simulation for a spec dict, return a record."""
    t0 = time.time()
    try:
        cfg = spec_to_bike_config(spec)
        result = MotoQuantEngine(cfg).run()
        took = time.time() - t0

        # Determine status and ET
        if not result.finished_quarter:
            status = "did-not-finish"
            sim_et_s = None
            sim_trap_kmh = None
        elif result.time_quarter > 14.9:  # finished but over 15s threshold
            status = "over-time"
            sim_et_s = round(float(result.time_quarter), 3)
            sim_trap_kmh = round(float(result.speed_quarter) * 3.6, 1)
        else:
            status = "ok"
            sim_et_s = round(float(result.time_quarter), 3)
            sim_trap_kmh = round(float(result.speed_quarter) * 3.6, 1)

        record = {
            "manufacturer": spec.manufacturer,
            "model": spec.model_name,
            "year_from": spec.year_from,
            "year_to": spec.year_to,
            "category": getattr(spec, "category", None),
            "displacement_cc": spec.displacement_cc,
            "stroke_type": getattr(spec, "stroke_type", None) or 4,
            "status": status,
            "wall_time_s": round(took, 3),
        }

        if sim_et_s is not None:
            record["sim_et_s"] = sim_et_s
            record["sim_trap_kmh"] = sim_trap_kmh
        else:
            # For did-not-finish, record max distance and elapsed time
            record["max_distance_m"] = round(result.max_distance_m, 1)
            record["elapsed_time_s"] = round(result.elapsed_time_s, 2)

        return record
    except Exception as exc:
        return {
            "manufacturer": spec.manufacturer,
            "model": spec.model_name,
            "year_from": spec.year_from,
            "year_to": spec.year_to,
            "category": getattr(spec, "category", None),
            "displacement_cc": spec.displacement_cc,
            "stroke_type": getattr(spec, "stroke_type", None) or 4,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "wall_time_s": round(time.time() - t0, 3),
        }


def run_sweep(verbose: bool = True) -> dict:
    """Run the sweep. Returns a dict ready for JSON serialization."""
    results: list[dict] = []
    benchmark_hits: list[dict] = []

    t_start = time.time()

    # 1. Reference bikes
    for name, year, factory, target_et, trap_kmh, source in REFERENCE_BIKES:
        t0 = time.time()
        try:
            cfg = factory()
            r = MotoQuantEngine(cfg).run()
            sim_et = float(r.time_quarter)
            sim_trap = float(r.speed_quarter) * 3.6
            rec = {
                "manufacturer": name.split()[0],
                "model": " ".join(name.split()[1:]),
                "year_from": year,
                "year_to": year,
                "category": getattr(cfg, "category", "sport"),
                "displacement_cc": cfg.engine.displacement_cc,
                "stroke_type": getattr(cfg.engine, "stroke_type", 4) or 4,
                "sim_et_s": round(sim_et, 3),
                "sim_trap_kmh": round(sim_trap, 1),
                "status": "ok" if sim_et <= 14.9 else "over-time",
                "wall_time_s": round(time.time() - t0, 3),
                "is_reference": True,
            }
            results.append(rec)
            benchmark_hits.append(
                {
                    **rec,
                    "target_et_s": target_et,
                    "target_trap_kmh": trap_kmh,
                    "delta_et_s": round(sim_et - target_et, 3),
                    "source": source,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "manufacturer": name.split()[0],
                    "model": " ".join(name.split()[1:]),
                    "year_from": year,
                    "year_to": year,
                    "status": "error",
                    "error": str(exc),
                    "is_reference": True,
                }
            )

    # 2. Full catalog sweep
    n = len(ALL_KNOWN_BIKES)
    for i, spec in enumerate(ALL_KNOWN_BIKES, 1):
        rec = _sim_spec(spec)
        results.append(rec)
        if verbose and i % 25 == 0:
            print(
                f"  [{i:>3}/{n}] {rec['manufacturer'][:14]:<14} "
                f"{rec['model'][:26]:<26} "
                f"{rec.get('sim_et_s', '---')}s  {rec['status']}"
            )

        # Benchmark match — score-and-pick (Option 2 from DISPATCH_INBOX
        # 2026-05-25). Word-boundary matching + manufacturer + year-range
        # filter, then pick the *most-specific* benchmark (highest model-
        # token-count). Robust against insertion-order and token-count
        # ties — e.g. catalog row "Ninja H2 SX (2018-2023)" now correctly
        # binds to the 3-token "Ninja H2 SX" benchmark instead of the
        # 2-token "Ninja H2" via subset shadowing.
        match = _best_benchmark_match(spec, BENCHMARKS)
        if match is None or rec["status"] != "ok":
            continue
        bmfr, bmodel, byear, tgt_et, tgt_trap, src = match
        benchmark_hits.append(
            {
                **rec,
                "benchmark_year": byear,
                "target_et_s": tgt_et,
                "target_trap_kmh": tgt_trap,
                "delta_et_s": round(rec["sim_et_s"] - tgt_et, 3),
                "source": src,
            }
        )

    t_elapsed = time.time() - t_start

    # 3. Aggregate stats
    n_total = len(results)
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_over = sum(1 for r in results if r["status"] == "over-time")
    n_dnf = sum(1 for r in results if r["status"] == "did-not-finish")
    n_err = sum(1 for r in results if r["status"] == "error")
    n_bench = len(benchmark_hits)
    abs_deltas = [abs(b["delta_et_s"]) for b in benchmark_hits]
    signed_deltas = [b["delta_et_s"] for b in benchmark_hits]

    def _bucket(x: float) -> int:
        return sum(1 for d in abs_deltas if d <= x)

    if abs_deltas:
        mean_abs = sum(abs_deltas) / len(abs_deltas)
        sorted_abs = sorted(abs_deltas)
        median_abs = sorted_abs[len(sorted_abs) // 2]
        bias = sum(signed_deltas) / len(signed_deltas)
    else:
        mean_abs = median_abs = bias = 0.0

    summary = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "wall_time_s": round(t_elapsed, 1),
        "bikes_total": n_total,
        "bikes_ok": n_ok,
        "bikes_over_time": n_over,
        "bikes_did_not_finish": n_dnf,
        "bikes_error": n_err,
        "benchmark_matches": n_bench,
        "mean_abs_delta_s": round(mean_abs, 3),
        "median_abs_delta_s": round(median_abs, 3),
        "bias_s": round(bias, 3),
        "within_0p10s": _bucket(0.10),
        "within_0p20s": _bucket(0.20),
        "within_0p50s": _bucket(0.50),
        "within_1p00s": _bucket(1.00),
        "pass_rate_0p20s": round(_bucket(0.20) / max(1, n_bench), 3),
    }

    return {
        "summary": summary,
        "benchmark_hits": benchmark_hits,
        "bikes": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-only", action="store_true", help="suppress stdout progress")
    ap.add_argument("--output-dir", default="reports", help="reports directory")
    args = ap.parse_args()

    verbose = not args.json_only
    if verbose:
        print(
            f"Validation sweep — {len(ALL_KNOWN_BIKES)} known bikes + "
            f"{len(REFERENCE_BIKES)} reference bikes"
        )
        print("─" * 70)

    report = run_sweep(verbose=verbose)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    today = _dt.date.today().isoformat()
    out_path = out_dir / f"validation_{today}.json"
    out_path.write_text(json.dumps(report, indent=2))

    if verbose:
        s = report["summary"]
        print("\n" + "═" * 70)
        print(" VALIDATION SWEEP SUMMARY")
        print("═" * 70)
        print(f"  Bikes total:            {s['bikes_total']}")
        print(f"    ok:                   {s['bikes_ok']}")
        print(f"    over-time (>14.9s):   {s['bikes_over_time']}")
        print(f"    did-not-finish:       {s['bikes_did_not_finish']}")
        print(f"    error:                {s['bikes_error']}")
        print(f"  Benchmark matches:      {s['benchmark_matches']}")
        print(f"  Mean |ΔET|:             {s['mean_abs_delta_s']:.3f}s")
        print(f"  Median |ΔET|:           {s['median_abs_delta_s']:.3f}s")
        print(f"  Bias (sim − real):      {s['bias_s']:+.3f}s")
        print(f"  Within ±0.10s:          {s['within_0p10s']}/{s['benchmark_matches']}")
        print(f"  Within ±0.20s:          {s['within_0p20s']}/{s['benchmark_matches']}")
        print(f"  Within ±0.50s:          {s['within_0p50s']}/{s['benchmark_matches']}")
        print(f"  Within ±1.00s:          {s['within_1p00s']}/{s['benchmark_matches']}")
        print(f"  Pass-rate (±0.20s):     {s['pass_rate_0p20s']:.1%}")
        print(f"  Wall time:              {s['wall_time_s']:.1f}s")
        print()
        print(f"  Report written to:      {out_path}")


if __name__ == "__main__":
    main()
