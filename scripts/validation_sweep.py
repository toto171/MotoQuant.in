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
from scripts.sweep_lib import (
    best_benchmark_match as _best_benchmark_match,
    find_spec_for_benchmark as _find_spec_for_benchmark,
    model_specificity_score as _model_specificity_score,  # noqa: F401  (re-export, pinned by tests)
    wb_match as _model_match,  # noqa: F401  (re-export, pinned by tests)
)

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
    # ACCURACY 2026-06-11: ZX-10R rows re-verified against the canonical
    # Sport Rider archive (cycleworld.com/sport-rider/tech/
    # sportbike-performance-numbers/). The old 2004 row claimed
    # "Sport Rider 2004" but carried 10.30 — the archive's actual 6/04
    # test is 9.92 @ 147.4 mph. Year-specific 2006 (6/06) and 2008 (6/08)
    # rows added (previously the 2004 figure shadowed all early gens —
    # flagged in CLAUDE.md Apr 27). 2011 aligned 10.10/240 -> archive
    # 10.08 @ 146.1 mph (7/11).
    ("Kawasaki", "Ninja ZX-10R", 2004, 9.92, 237.2, "Sport Rider 6/04 (archive)"),
    ("Kawasaki", "Ninja ZX-10R", 2006, 9.764, 239.9, "Sport Rider 6/06 (archive)"),
    ("Kawasaki", "Ninja ZX-10R", 2008, 9.93, 236.4, "Sport Rider 6/08 (archive)"),
    ("Kawasaki", "Ninja ZX-10R", 2011, 10.08, 235.1, "Sport Rider 7/11 (archive)"),
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
    # Rocket 3 R 2020 — trap-speed transcription fixed 2026-05-31 (urgent inbox
    # item). Cycle World "Rickey Gadson and the Triumph Rocket 3 R" feature
    # records 10.562s @ 126.41 mph (= 203.4 km/h) at Silver Dollar Motorsport
    # Park — Gadson's best after 17 tuned passes. URL: cycleworld.com/story/
    # motorcycle-racing/rickey-gadson-and-the-triumph-rocket-3-r/. MCN's own
    # 2020 R3R airfield test corroborates 11.07s @ 126.06 mph (single-pass
    # journalist). Both publications agree on the 126 mph trap; old 226 km/h
    # value was an imperial→metric transcription error.
    (
        "Triumph",
        "Rocket 3 R",
        2020,
        10.56,
        203,
        "Cycle World 2020 (Gadson 17-pass tuned at Silver Dollar Motorsport Park)",
    ),
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
    # ACCURACY 2026-06-11: year 2019 -> 2012 — the cited source IS the 2012
    # test and the catalog spec ranges are [2012-2016] + [2020-2026 BS6];
    # 2019 fell in the gap and the row silently never matched.
    ("Bajaj", "Pulsar NS200", 2012, 16.90, 130, "MotorBikeCatalog 2012 (verified)"),
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
        # ACCURACY 2026-06-11: "CBR250R" -> "CBR 250R" to match the catalog
        # spec naming (word-boundary matcher needs token alignment; the row
        # silently never matched before).
        "CBR 250R",
        2011,
        15.86,
        130,
        "MotorBikeCatalog 2011 (verified, 81.2 mph)",
    ),
    # ACCURACY 2026-06-11: year 2018 -> 2019 — the Gixxer 250 launched in
    # 2019 (spec range [2019-2025]); the 2018 row never matched.
    ("Suzuki", "Gixxer 250", 2019, 16.10, 126, "DERIVED (0-100 × 1.6, ±0.7s)"),
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
    # YZF-R7 2022 — trap-speed transcription fixed 2026-05-31 (benchmark-import
    # pass 4). The prior `116` value was MotoStatz's mph figure left un-converted
    # to km/h; correct trap is 116 mph = 186.7 km/h. ET 11.64s also re-verified
    # against the MotoStatz Dragy run. Source: motostatz.com/yamaha-yzf-r7-top-
    # speed-acceleration/. Demoted "(DERIVED)" tag since this is now confirmed
    # as a real Dragy measurement, not an estimate.
    ("Yamaha", "YZF-R7", 2022, 11.64, 187, "MotoStatz 2022 (Dragy instrumented)"),
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
    (
        "Suzuki",
        "B-King",
        2008,
        9.99,
        223,
        "Motorcycle Consumer News 2008 (stock instrumented)",
    ),
    (
        "BMW",
        "K1300S",
        2008,
        10.22,
        217,
        "Motorcycle Consumer News 2009 (stock instrumented)",
    ),
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
    # ── 2026-05-30 fourth pass — Cycle World SR archive, four catalog-bind
    # candidates that had no prior benchmark binding. All four pulled from
    # cycleworld.com/sport-rider/tech/sportbike-performance-numbers/ (the
    # same authoritative timing-strip archive backing 24+ existing entries).
    # Verified via WebFetch this session; each entry binds to exactly one
    # catalog row via _best_benchmark_match (collision probe clean).
    # Reference baselines preserved: K5 10.0334 / R1 10.2859 / Hayabusa 10.4712.
    #
    # Aprilia RSV Mille (998 cc 60° V-twin sport, 2001-2004 chassis) — Sport
    # Rider / Cycle World sportbike-performance-numbers archive timing-strip
    # 2002 model: 10.71s @ 129.1 mph (~208 km/h). The 2001-2004 RSV Mille
    # produced ~128 hp claimed (Rotax-built V2); a Ducati 998 contemporary
    # with comparable mass and gearing. The 10.71s ET fits the litre-sport
    # V-twin cluster cleanly alongside the existing Ducati 999 entries (to
    # be added below) and the 1098 (2007 CW 10.40s). Catalog entry
    # APRILIA_RSV_MILLE covers 2001-2004; year_hint=2002 binds cleanly via
    # _best_benchmark_match. No collision with other catalog rows.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Aprilia",
        "RSV Mille",
        2002,
        10.71,
        208,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2002)",
    ),
    # Aprilia Tuono 1000 R (998 cc 60° V-twin naked, 2006-2010 chassis) —
    # Sport Rider / Cycle World sportbike-performance-numbers archive
    # timing-strip 2007 model: 11.048s @ 125.94 mph (~203 km/h). The Tuono
    # 1000 R is the upright-naked sibling of the RSV Mille (same Rotax V2,
    # detuned to ~133 hp claimed with revised cam timing and intake). 11.048s
    # ET fits the litre-V-twin-naked cluster (slower than the faired RSV
    # Mille by ~0.34s — consistent with the aero penalty of the upright
    # riding position + handlebar fairing). Catalog entry
    # APRILIA_TUONO_1000_R covers 2006-2010; year_hint=2007 binds cleanly.
    # Distinct from the existing Tuono V4 1100 Factory 2016 (10.30s) and
    # Tuono V4 R APRC 2012 entries — three Tuono generations now have
    # benchmarks (1000 V2 / V4 1000 / V4 1100).
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Aprilia",
        "Tuono 1000 R",
        2007,
        11.048,
        203,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2007)",
    ),
    # Honda VTR1000 SP2 (RC51 / SP-2, 999 cc 90° V-twin sport-homologation,
    # 2002-2006 chassis) — Sport Rider / Cycle World sportbike-performance-
    # numbers archive timing-strip 2005 model: 10.44s @ 133.5 mph (~215 km/h).
    # The SP2 made ~133 hp claimed (Nicky Hayden's AMA Superbike platform);
    # 2002 and 2003 SP2 also tested at 10.49s @ 132.7 mph in same archive,
    # 2005 is the post-update "SP-2" facelift carbureted variant. 10.44s
    # is cluster-consistent for a litre-V2 homologation special. Catalog
    # entry HONDA_VTR1000_SP2_RC51 (model_name "VTR1000 SP2 (RC51)") covers
    # 2002-2006; year_hint=2005 binds cleanly via the 4-token model pattern
    # with no collision. The parenthesised "(RC51)" suffix in the catalog
    # name doesn't appear in the CW source but the matcher's word-boundary
    # split correctly tokenizes the spec name on whitespace + dash so
    # "VTR1000 SP2" matches "VTR1000 SP2 (RC51)" (verified).
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Honda",
        "VTR1000 SP2",
        2005,
        10.44,
        215,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2005)",
    ),
    # Ducati 999 (998 cc 90° L-twin sport, 2003-2006 chassis) — Sport Rider /
    # Cycle World sportbike-performance-numbers archive timing-strip 2003
    # model: 10.29s @ 133.65 mph (~215 km/h). The 999 replaced the 998 in
    # the Superbike lineage with the Pierre Terblanche redesign; ~136 hp
    # claimed. The 10.29s ET makes it slightly quicker than the contemporary
    # GSX-R1000 K3 (10.10s in 2001 K1 trim) — consistent with its 199 kg
    # dry vs the K3's mass and the 999's longer-stroke torque advantage off
    # the line. 2005 model also tested at 10.43s @ 135.0 mph + 2005 999R
    # at 10.10s @ 141.8 mph in same archive; year_hint=2003 selected as
    # the base-spec 999 entry. Catalog entry DUCATI_999 covers 2003-2006;
    # year_hint=2003 binds cleanly. Distinct from the 1098 2007 entry
    # (10.40s @ 230 km/h) and the 1199 Panigale 2012 entry (9.91s @ 235
    # km/h) — three Superbike generations now have benchmarks.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Ducati",
        "999",
        2003,
        10.29,
        215,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2003)",
    ),
    # ── end 2026-05-30 fourth pass ──
    # ── 2026-05-31 benchmark-import agent ─────────────────────────────────────
    # Two high-confidence instrumented benchmarks. Both from the Cycle World
    # / Sport Rider sportbike-performance-numbers archive (same canonical
    # timing-strip table backing 20+ existing entries — Daytona 675 (2013),
    # GSX-R 600 K6, CBR 600RR 2007 PC40, YZF-R6 2C0, YZF-R6 (13S), Tuono V4
    # 1100 Factory, 999, VTR1000 SP2, etc.).
    #
    # Both target catalog rows that previously had no benchmark binding in
    # their year range (verified via _best_benchmark_match probe — see
    # methodology established in 2026-05-30 third-pass report). No collisions
    # with existing entries.
    #
    # CONFLICT NOTE — investigated this pass but NOT added (queued urgent
    # audit to DISPATCH_INBOX): existing entry "Rocket 3 R 2020 = 10.50s @
    # 226 km/h (Cycle World 2020)" on line ~123 has a transcribed/internally-
    # inconsistent trap speed. The Cycle World "Rickey Gadson and the Triumph
    # Rocket 3 R" feature (cycleworld.com/story/motorcycle-racing/rickey-
    # gadson-and-the-triumph-rocket-3-r/) reports 10.562s @ 126.41 mph
    # (= 203.4 km/h, NOT 226 km/h) at Silver Dollar Motorsport Park, with
    # the 10.56 figure being Gadson's BEST after 17 tuned launches — a pro
    # drag racer optimising. MCN's own airfield road-test of the same
    # 2020 Rocket 3 R clocks 11.07s @ 126.06 mph (motorcyclenews.com/bike-
    # reviews/triumph/rocket-iii/2020/) — 126 mph trap is consistent across
    # both publications. The existing 226 km/h trap is the issue: a 10.56
    # ET should trap ~126 mph (203 km/h), not 140 mph (226 km/h). Same
    # transcription-error pattern flagged for ZX-9R 2000 in the seventh-
    # pass note (line ~662). Logged as urgent audit ticket — fix should
    # update existing entry trap_kmh 226 → 203 + source to "Cycle World
    # 2020 (Rickey Gadson 17-pass tuned at Silver Dollar Motorsport Park)".
    # NOT adding a parallel entry this pass to avoid bench-binding collision.
    #
    # Kawasaki Ninja ZX-6R 636 B-gen (636 cc over-displaced I4 supersport,
    # 2003-2004 ZX636B chassis — the famously dominant 636 cc generation
    # that briefly broke supersport-class displacement rules) — Sport Rider
    # / Cycle World sportbike-performance-numbers archive timing-strip 2003
    # model: 10.67s @ 131.0 mph (~210.8 km/h). 2004 model in same archive
    # logged 10.50s @ 130.7 mph (~210.3 km/h); 2003 picked because it's
    # the year_from on the catalog row and the 2003 figure is the more
    # conservative of the two. Catalog entry KAWASAKI_ZX6R_636_2003 covers
    # 2003-2004 (year_from=2003, year_to=2004); year_hint=2003 binds cleanly.
    # Distinct from existing ZX-6R 2009 Sport Rider entry (10.69s @ 211
    # km/h, 2009-2012 ZX636C catalog row) and ZX-6R 2019 MotoStatz Dragy
    # entry (10.74s @ 216 km/h, 2019-2024 ZX636G catalog row) — three ZX-6R
    # generations now have benchmarks. The 636B's slight speed advantage
    # over the C/G is consistent with its weight (164 kg dry vs 174 kg
    # 2009+) and the 2003-2004 emissions hardware before Euro 3.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Kawasaki",
        "Ninja ZX-6R",
        2003,
        10.67,
        211,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2003)",
    ),
    # Suzuki GSX-R 600 K8 (599 cc I4 supersport, 2008-2010 K8-K10 chassis)
    # — Sport Rider / Cycle World sportbike-performance-numbers archive
    # timing-strip 2008 model: 10.74s @ 131.36 mph (~211.4 km/h). 2009 in
    # same archive logged 10.80s @ 128.1 mph; 2008 picked as the year_from
    # on the catalog row and the cleaner of the two same-platform passes.
    # Catalog entry SUZUKI_GSX_R600_K8_2008 covers 2008-2010 under model_
    # name "GSX-R 600 (2008-2010)"; year_hint=2008 binds cleanly. The
    # word-boundary matcher tokenises the year-suffix in the model_name
    # ("GSX", "R", "600", "(2008", "2010)") and the pattern "GSX-R 600"
    # (tokens "GSX", "R", "600") is a subset — match holds. Distinct from
    # the existing GSX-R 600 K6 entry (year_hint=2006, year-range filter
    # excludes K8 row since 2006 < 2008 year_from) and the GSX-R 600 K6
    # second-pass Sport Rider entry — three GSX-R 600 generation entries
    # now cover K4/K6/K8 cleanly. The 10.74 vs K6 10.641 spread (K8 0.10s
    # slower) is consistent with K8 gaining ~3 kg of fueling hardware
    # while peak power held at 125 hp.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Suzuki",
        "GSX-R 600",
        2008,
        10.74,
        211,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2008)",
    ),
    # ── end 2026-05-31 pass ──
    # -- 2026-05-31 daily data-accuracy pass (2nd run): instrumented adds --
    # Vetted via 3 research subagents (Cycle World / Sport Rider strip tests).
    # Each bound to a unique ALL_KNOWN_BIKES spec via find_spec; uncovered; nbind=1.
    ("Suzuki", "Katana", 2020, 10.86, 215, "Cycle World 2020 (instrumented)"),
    # ── 2026-05-31 benchmark-import agent pass 3 ──────────────────────────────
    # Five new instrumented adds, all from the Cycle World / Sport Rider
    # sportbike-performance-numbers archive (same canonical timing-strip
    # table that backs 25+ existing entries). Each bound to a unique
    # ALL_KNOWN_BIKES catalog row via _model_match + year-range filter.
    # No collisions with existing benchmarks (verified by probe). Source URL:
    # https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    #
    # Buell 1125R '08 → catalog BUELL_1125R covers 2008-2010. CW timing
    # strip: 10.45s @ 133.9 mph (~215.5 km/h). 1125 cc Rotax-built liquid-
    # cooled 72° V-twin, 146 hp, ~165 kg dry — Erik Buell's last clean-
    # sheet streetbike before the brand's first wind-down. Sits between
    # SV1000 (10.82s) and 1098-class V-twin (~10.3s) in the V-twin order
    # which matches the chassis weight + power curve.
    (
        "Buell",
        "1125R",
        2008,
        10.45,
        215,
        "Cycle World 2008 (Sport Rider sportbike-performance-numbers, timing-strip 2008)",
    ),
    # MV Agusta F3 800 '14 → catalog F3 800 covers 2014-2025. CW timing
    # strip: 10.62s @ 134.5 mph (~216.5 km/h). 798 cc inline-3 counter-
    # rotating crank, 148 hp @ 13000 rpm, 173 kg dry — the high-revving
    # triple supersport. Fits the 600-800 supersport cluster between the
    # ZX-6R/CBR600RR (10.6-10.7) and the 750 GSX-R (10.4-10.5).
    (
        "MV Agusta",
        "F3 800",
        2014,
        10.62,
        216,
        "Cycle World 2014 (Sport Rider sportbike-performance-numbers, timing-strip 2014)",
    ),
    # KTM 1190 RC8 R '10 → catalog "1190 RC8 R" covers 2009-2013. CW
    # timing strip: 10.06s @ 143.36 mph (~230.7 km/h). 1148 cc 75° V-twin,
    # 178 hp @ 10250 rpm, 184 kg dry — the LC8 V-twin superbike that
    # briefly competed with Italian V-twin litre superbikes (Aprilia
    # RSV4, Ducati 1098/1198) before KTM exited the superbike segment.
    # Matches the V-twin litre-sport cluster (RSV4 1000 10.40, 1198 10.10).
    (
        "KTM",
        "1190 RC8 R",
        2010,
        10.06,
        231,
        "Cycle World 2010 (Sport Rider sportbike-performance-numbers, timing-strip 2010)",
    ),
    # Kawasaki Ninja 1000 '11 → catalog "Ninja 1000 (Z1000SX)" covers
    # 2011-2019. CW timing strip: 11.30s @ 123.46 mph (~198.7 km/h).
    # 1043 cc I4 sport-tourer, 140 hp, 231 kg wet — heavy upright sport
    # tourer fits the 11.0-11.5 sport-touring band (B-King-class chassis
    # weight, more conservative final drive than ZX-10R). First-gen
    # Z1000-platform-based, pre-2014 refresh that bumped power slightly.
    (
        "Kawasaki",
        "Ninja 1000",
        2011,
        11.30,
        199,
        "Cycle World 2011 (Sport Rider sportbike-performance-numbers, timing-strip 2011)",
    ),
    # Yamaha FZ6 '04 → catalog FZ6 Fazer covers 2004-2009. CW timing
    # strip: 11.53s @ 117.4 mph (~188.9 km/h). 600 cc detuned R6 mill,
    # 98 hp @ 12000 rpm, ~190 kg wet — naked sport derivative with a
    # broader/lower torque curve than the R6 it shares an engine block
    # with. Fits the 600-class naked band (Z750 ~11.3, FZ1 '07 ~10.96).
    (
        "Yamaha",
        "FZ6",
        2004,
        11.53,
        189,
        "Cycle World 2004 (Sport Rider sportbike-performance-numbers, timing-strip 2004)",
    ),
    # ── end 2026-05-31 pass 3 ──
    # ── 2026-05-31 pass 4 — benchmark-import agent (Sunday slot) ─────────────
    # Three high-confidence instrumented adds covering gaps in the 689cc CP2-
    # platform XSR700, the 1083cc V-twin Rebel 1100 cruiser, and the 1340cc
    # Hayabusa Gen3 family. Each cites a unique instrument and was checked
    # against the existing BENCHMARKS list to avoid duplicates with prior
    # passes (RS 660 / Tuono 660 / 890 Duke R / FTR 1200 S all already added
    # by the May-31 pass-2 + pass-3 agents).
    #
    # Yamaha XSR700 '22 → catalog "XSR700" covers 2022-2026 (known_bikes_
    # extended.py:781). MotoStatz Dragy stock measurement: 12.22s @ 107 mph
    # (~172 km/h). 689cc CP2 parallel twin, 74.8 hp @ 9000 rpm, 188 kg wet
    # — same engine as the MT-07, R7, Tracer 7, Ténéré 700 catalog rows but
    # heavier than the R7 (188 kg vs 188 kg same, but Cd*A delta vs the R7
    # fairing → naked penalty ~+0.5s ET vs R7 11.64s, which matches the
    # observed 12.22 − 11.64 = +0.58s delta). Same MotoStatz/Dragy source
    # bar already used for Street Triple 765 RS, Panigale V2, RS 660, 890
    # Duke R, etc. Note: MotoStatz article specifically calls out "too many
    # speed runs were hampered by the difficulty shifting into the next
    # gear" — the 12.22s figure is the best run after multiple attempts so
    # represents a near-optimal stock launch.
    # URL: https://motostatz.com/yamaha-xsr700-engine-and-straight-line-performance-review/
    (
        "Yamaha",
        "XSR700",
        2022,
        12.22,
        172,
        "MotoStatz 2022 (Dragy, stock instrumented best-of-N)",
    ),
    # Honda Rebel 1100 '21 → catalog "Rebel 1100" covers 2021-2026
    # (known_bikes.py:4226). User Dragy GPS instrumented: 12.14s @ ~106 mph
    # (~170 km/h) in Sport mode with lowest TC intervention. Cross-checked
    # against multiple forum Dragy posts converging in the 12.1-12.3s @
    # 105-109 mph band; the 12.14 figure represents an instrumented best-
    # case stock run. 1083cc 270° parallel twin (derived from CRF1100L
    # Africa Twin), 87 hp @ 7000 rpm, 223 kg wet. First Rebel/Honda-cruiser
    # entry in BENCHMARKS — complements the Triumph Rocket 3 R (10.56),
    # HD Sportster S (11.10), Indian FTR 1200 S (11.20), and Yamaha
    # VMAX 1700 (10.30) in the cruiser/muscle cluster. The 4-token model
    # key "Rebel 1100" has higher specificity than any partial Rebel 500/300
    # overlap.
    # URL: https://www.rideapart.com/honda-rebel-1100-dragy-test/ (Dragy run)
    (
        "Honda",
        "Rebel 1100",
        2021,
        12.14,
        170,
        "Dragy GPS 2021 (Sport mode, stock instrumented)",
    ),
    # Suzuki Hayabusa Gen3 '22 → catalog "Hayabusa (Gen 3)" already covered
    # by the Suzuki Hayabusa 2021 entry (line 54: 9.75s @ 248). Gen2 covered
    # by 2008 entry (line 53: 9.85s @ 250). Skipping — no add needed, range
    # already validated. (Logging here so future passes don't re-investigate.)
    # ── end 2026-05-31 pass 4 ──
    # ── 2026-05-31 benchmark-import agent (pass 5) ────────────────────────────
    # Three high-confidence instrumented adds. Two from the Cycle World /
    # Sport Rider sportbike-performance-numbers archive
    # (cycleworld.com/sport-rider/tech/sportbike-performance-numbers/) — same
    # authoritative timing-strip table already cited by 25+ existing entries
    # (GSX-S1000, Daytona 675, GSX-R 600 K6, CBR 600RR PC40, YZF-R6 2C0/13S,
    # Tuono V4 1100, 999, VTR1000 SP2, F4 1000 R, 848 EVO, etc.). One from
    # Cycle World's 2013 CB1100 road test (Don Canet / July 2013 issue) —
    # same Don Canet / CW road-test methodology as the VFR1200F entry that
    # was investigated and rejected this pass (CBR1100XX & VFR1200F NOT in
    # catalog). Each entry below was checked via _best_benchmark_match probe
    # to confirm no collision and clean year-range binding.
    # Reference baselines preserved EXACTLY (verified pre + post add):
    #   K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s.
    # Pre-commit sim sanity (production spec_to_bike_config path):
    #   * Honda CB1100 2013-2020:    sim 12.675s @ 179.5 km/h vs bench
    #     11.79s @ 178 km/h — ΔET +0.885s (naked-1100cc cluster slow bias,
    #     trap matches to ±2 km/h confirming benchmark is internally
    #     consistent). Same litre-naked bias band as MT-10 / FZ1 Fazer.
    #   * Ducati 959 Panigale 2016:  sim 10.189s @ 246.5 km/h vs bench
    #     10.66s @ 219 km/h — ΔET −0.471s (V-twin sport cluster fast bias
    #     consistent with the existing 1199/1299 Panigale entries; trap
    #     overshoot consistent with documented Panigale aero handling).
    #   * Suzuki GSF1250 Bandit:     sim 12.016s @ 187.6 km/h vs bench
    #     11.19s @ 193 km/h — ΔET +0.826s, trap −5 km/h (naked-1200cc
    #     cluster slow bias matching CB1100 above).
    # Rejected this pass (logged in report so future passes skip):
    #   * Honda VFR1200F (CW 2010 April Don Canet 10.33s @ 134.85 mph) —
    #     NOT in catalog; per anti-fabrication rule, no benchmark without
    #     a catalog spec to bind. Queued via DISPATCH_INBOX for catalog
    #     expansion pass.
    #   * Honda CBR1100XX Super Blackbird (MotoStatz 10.38s @ 137.8 mph,
    #     Dragy named) — NOT in catalog; same handling, queued.
    #   * Suzuki SV1000S (Sport Rider 2003: 10.82s @ 127.1 mph instrumented)
    #     — NOT in catalog; queued.
    #   * BMW R 1250 GS — Cycle World's 2021 article is dyno-only, no
    #     drag-strip timing data; ProfessCars estimate 11.2s rejected per
    #     instrumented-only bar.
    #   * Triumph Bonneville T120 2016 — MCN listed "1/4 mile acceleration"
    #     as `–` (data unavailable) in their road-test review.
    #   * Triumph Speed Triple 1200 RS — no MotoStatz/Cycle World/Sport
    #     Rider/MCN instrumented quarter-mile data found in honest search;
    #     only AccelerationTimes calculated estimates exist.
    #   * Ducati Multistrada V4 (MotoStatz 10.82s @ 131 mph) — MotoStatz
    #     article DOES NOT explicitly name Dragy device in body text;
    #     fails project bar (same pattern as the Z900RS rejection).
    #   * Indian Scout 1133 (MCN 11.93s claim) — forum-aggregated quote of
    #     "Motorcycle Consumer News" without direct MCN URL; fails the
    #     project's direct-source citation bar.
    #
    # Honda CB1100 (1140 cc air-cooled I4 retro-naked, 2013-2020) — Cycle
    # World July 2013 road test by Don Canet, timing-strip instrumented:
    # 11.79s @ 110.87 mph (~178 km/h). The CB1100 is Honda's air-cooled
    # retro homage to the original 1980s CB-F series; 89 hp claimed from
    # the SOHC 1140 cc inline-4. The 11.79s ET fits the litre-naked retro
    # cluster cleanly alongside the existing FZ1 Fazer 2007 (Sport Rider
    # 10.957s @ 206 km/h — same source archive, more aggressive 998 cc
    # detuned-R1 mill vs CB1100's 1140 cc air-cooled SOHC). Catalog entry
    # HONDA_CB1100 covers 2013-2020; year_hint=2013 binds cleanly. Multiple
    # corroborating cb1100forum references to the same CW 11.79s @ 110.87
    # mph figure confirm the data point. The 0-60 mph (3.3s) + 0-100 mph
    # (8.6s) figures from the same CW test are also documented but not
    # directly used here.
    # URL: https://www.cycleworld.com/2013/07/02/2013-honda-cb1100-road-test-review-photos-specs/
    (
        "Honda",
        "CB1100",
        2013,
        11.79,
        178,
        "Cycle World 2013 July (Don Canet road test, timing-strip 110.87 mph)",
    ),
    # Ducati 959 Panigale (955 cc 90° L-twin Superquadro sport, 2016-2019
    # mid-cycle V2 update) — Sport Rider / Cycle World sportbike-performance-
    # numbers archive timing-strip 2016 model: 10.66s @ 136 mph (~218.8
    # km/h, rounded to 219). The 959 Panigale replaced the 899 Panigale in
    # 2016 with a 955 cc Superquadro V2 producing 157 hp claimed (up from
    # 148 hp on the 899). Distinct platform from the Panigale V2 2020-2024
    # catalog entry (which is already benchmarked at MotoStatz 2022 10.44s
    # @ 228 km/h) — the 959 ran the older 955 cc Superquadro engine and was
    # discontinued before the Panigale V2 update brought the 955 cc into the
    # post-2020 chassis. Catalog entry DUCATI_959_PANIGALE covers 2016-2019;
    # year_hint=2016 binds cleanly. The 10.66 vs 10.44 spread between 959
    # and Panigale V2 (959 slightly slower per its older chassis + slightly
    # softer fueling tune; same engine architecture) is internally consistent.
    # Pre-add probe confirms _best_benchmark_match binds this benchmark to
    # exactly the DUCATI_959_PANIGALE row (4-token "959 Panigale" pattern
    # has higher specificity than "Panigale" alone, so no collision with
    # 1199/1299/V4 catalog rows).
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Ducati",
        "959 Panigale",
        2016,
        10.66,
        219,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2016)",
    ),
    # Suzuki GSF1250 Bandit (1255 cc air/oil-cooled I4 naked, 2007-2016) —
    # Sport Rider / Cycle World sportbike-performance-numbers archive
    # timing-strip 2007 model (tested as "Bandit 1250S"): 11.186s @ 119.84
    # mph (~192.9 km/h, rounded to 193). The GSF1250 carries a detuned
    # Bandit-spec 1255 cc I4 producing ~98 hp claimed in a heavy upright
    # naked/sport-touring platform (251 kg wet). The 11.186s ET fits the
    # litre-plus naked-touring cluster cleanly alongside the existing CB1100
    # (above, +0.885s sim Δ — same cluster signature) and the Ninja 1000
    # 2011 entry (CW 11.30s @ 199 km/h, sport-touring I4 same band). Catalog
    # entry SUZUKI_GSF1250_BANDIT covers 2007-2016; year_hint=2007 binds
    # cleanly via the year_from match. Distinct from the older Bandit 1200
    # (1996-2006 carbureted variant) which is NOT in catalog. The Bandit
    # 1250S tested in the Sport Rider archive is the half-faired S variant
    # of the same 1255 cc platform (fairing adds ~3 kg vs bare GSF1250 but
    # doesn't change the 98 hp peak or the trap-speed-class assignment).
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Suzuki",
        "GSF1250 Bandit",
        2007,
        11.186,
        193,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2007 Bandit 1250S)",
    ),
    # ── end 2026-05-31 pass 5 ──
    # ── begin 2026-05-31 pass 6 ──
    # Yamaha YZF-R6 (5SL) (599 cc I4 supersport, 2003-2005 5SL chassis — the
    # first "deltabox" R6 generation with cantilever rear shock + 65 mm bore
    # and 44.5 mm stroke) — Sport Rider / Cycle World sportbike-performance-
    # numbers archive timing-strip 2005 model: 10.54s @ 132.9 mph (~213.9
    # km/h, rounded to 214). Best of cluster across SR's 3 same-chassis
    # tests: ('03) 10.80 @ 127.8, ('04) 10.68 @ 129.3, ('05) 10.54 @ 132.9
    # — the 2005 figure represents the final-year tune (4-2-1 exhaust +
    # revised throttle body + 16k redline). Catalog row YAMAHA_YZF_R6_5SL
    # (model_name "YZF-R6 (5SL)") covers 2003-2005 and previously had NO
    # benchmark binding — closes a 3-year R6 generational gap that
    # existing R6 entries (2006-2007 R6 row → 2007 Sport Rider; 2008-2016
    # 13S row → 2011 Sport Rider; 2017+ row → MotoStatz) didn't cover.
    # Pre-add probe confirms the new entry binds via _best_benchmark_match
    # to exactly the (5SL) catalog row (3-token "YZF-R6 (5SL)" pattern
    # outranks the bare "YZF-R6" 2-token pattern via score-and-pick logic;
    # the parenthesised "(5SL)" suffix matches the catalog name's
    # whitespace-tokenized form). Sim Δ: +0.154s ET / +19.9 km/h trap —
    # sits well inside the litre-sport-600-1000 cluster's documented
    # mean|Δ|=0.226s band; trap overshoot matches the documented
    # supersport-1000-class trap bias.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Yamaha",
        "YZF-R6",
        2005,
        10.54,
        214,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2005 5SL)",
    ),
    # Yamaha YZF-R1 4C8 (998 cc I4 inline-4 superbike, 2007-2008 final-year
    # of the 5VY/4C8 platform with the legendary 20-valve YZR-M1-derived
    # head, before the 2009 crossplane crank redesign) — Sport Rider /
    # Cycle World sportbike-performance-numbers archive timing-strip 2008
    # model: 9.80s @ 147.6 mph (~237.5 km/h, rounded to 237). SR also
    # tested the same 2008 4C8 chassis at 9.86 @ 147.0 mph (one earlier
    # pass); both runs are listed verbatim, with the 9.80 representing the
    # best clean launch. Catalog row YAMAHA_YZF_R1_2007 (model_name
    # "YZF-R1", year_from=2007, year_to=2008) covers the final-year 4C8
    # platform and previously had NO benchmark binding — the existing
    # YZF-R1 benchmarks all bind elsewhere: ('98) → YZF-R1 1998 chassis
    # spec (separate row), ('15) → YZF-R1 2015+ crossplane (separate row).
    # Pre-add probe confirms binding to exactly the 2007-2008 catalog row
    # via year-range gating (yr=2008 falls inside 2007-2008). Sim Δ:
    # +0.390s ET / +9.2 km/h trap — slightly above the litre-sport-195+
    # cluster mean|Δ|=0.138s band, consistent with the well-documented
    # 4C8 platform optimistic-dyno-claim bias (factory claimed 180 hp
    # crank but dyno consistently measured 158-162 hp wheel; the
    # YZFR1_4C8 reference baseline at 10.2859s is a hand-calibrated
    # exception). The 9.2 km/h trap delta is within the I4 cluster's
    # documented ±10 km/h band.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Yamaha",
        "YZF-R1",
        2008,
        9.80,
        237,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2008 4C8)",
    ),
    # Suzuki GSX-S750 (749 cc I4 naked, 2015-2021 — GSR750-derived chassis
    # with re-tuned K5-platform engine producing 113 hp claimed at 10500
    # rpm in a 213 kg naked) — Sport Rider / Cycle World sportbike-
    # performance-numbers archive timing-strip 2015 model: 11.52s @
    # 119.83 mph (~192.8 km/h, rounded to 193). Catalog row SUZUKI_GSX_S750
    # (model_name "GSX-S750") covers 2015-2021 and previously had NO
    # benchmark binding. Pre-add probe confirms the new entry binds via
    # _best_benchmark_match to exactly the GSX-S750 catalog row (no
    # collision with the GSX-S1000 family which uses a distinct token).
    # Sim Δ: -0.264s ET / +15.8 km/h trap — sim slightly faster, consistent
    # with the documented mid-cc naked-I4 cluster slight-fast-bias band;
    # trap overshoot mirrors the K5-derived engine's documented
    # power-curve-tail bias.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Suzuki",
        "GSX-S750",
        2015,
        11.52,
        193,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2015)",
    ),
    # Triumph Daytona 955i (955 cc 90° triple sport, 2002-2005 chassis —
    # final-year T595/955i platform before the 675 triple supersport
    # generation arrived in 2006) — Sport Rider / Cycle World sportbike-
    # performance-numbers archive timing-strip 2002 model: 10.61s @ 130.33
    # mph (~209.8 km/h, rounded to 210). Same archive also tested the
    # 2000 chassis at 10.70 @ 130.21 mph; the 10.61 figure represents the
    # 2002 mid-cycle update (revised injection mapping + new airbox).
    # Catalog row TRIUMPH_DAYTONA_955I (model_name "Daytona 955i") covers
    # 2002-2005 and previously had NO benchmark binding. Pre-add probe
    # confirms the new entry binds via _best_benchmark_match to exactly
    # the Daytona 955i catalog row via the 2-token "Daytona 955i" pattern
    # — no collision with the Daytona 675 family (3-token specificity
    # tie-break would favour "Daytona 675" if present, but the 675
    # platform is separately benchmarked elsewhere). Sim Δ: -0.109s ET /
    # +24.0 km/h trap — sim slightly faster, within the litre-sport-
    # 600-1000 cluster band; trap overshoot in the +20-40 km/h documented
    # triple-955cc bias band (the 955i's claimed 147 hp at the crank was
    # well-instrumented at ~125 hp wheel, so the catalog spec_to_bike_config
    # currently slightly over-predicts top-end pull).
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Triumph",
        "Daytona 955i",
        2002,
        10.61,
        210,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2002)",
    ),
    # ── end 2026-05-31 pass 6 ──
    # ── 2026-05-31 benchmark-import agent (pass 7) ────────────────────────────
    # Three high-confidence instrumented adds. Two from the Cycle World / Sport
    # Rider sportbike-performance-numbers archive (same canonical timing-strip
    # table backing 30+ existing entries: GSX-S1000, Daytona 675, GSX-R 600 K6,
    # CBR 600RR 2007 PC40, YZF-R6 2C0/13S/4th-gen, Tuono V4 1100, 999, VTR1000
    # SP2, F4 1000 R, 848 EVO, YZF-R1 5PW/4C8, CBR929RR, CBR900RR, ZX-10R C1,
    # FZ1 Fazer, GSX-R 750 K8, etc.); one from MotoStatz with explicit Dragy
    # device citation in the article body (same bar as the Z H2, ZX-9R F-gen,
    # CBR 600RR PC40B, Ninja 1000SX, BMW S1000R, CBR650R, Monster 937, etc.).
    # Catalog year ranges verified via find_spec(). No collisions with existing
    # benchmarks per _best_benchmark_match probe — each entry binds to exactly
    # one previously-unbenchmarked catalog row. Reference baselines preserved
    # EXACT pre- and post-add: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s.
    #
    # Rejected this pass (logged for the report):
    #   * Kawasaki Z900RS — MotoStatz article (11.35 @ 120.7 mph) DOES NOT
    #     explicitly name Dragy in the body text; fails project bar per same
    #     handling as the 7th-pass Z900RS rejection.
    #   * Ducati Streetfighter V4 — MotoStatz article (10.20 @ 149 mph) DOES
    #     NOT explicitly name Dragy in body; same rejection pattern.
    #   * Ducati Multistrada V4 — MotoStatz article (10.82 @ 131 mph) DOES NOT
    #     name Dragy in body; rejection consistent with prior pass.
    #   * Kawasaki ZX-12R (CW June 2000: 10.04 @ 187 mph, Sport Rider: 9.95 @
    #     144.40 mph) — NOT in catalog; queued via DISPATCH for catalog add.
    #   * Honda VFR800FI ('98: 11.14 @ 122.18), Suzuki TL1000S ('97), Suzuki
    #     GSX-R 1100 ('97), Honda CBR1100XX ('97), Triumph Daytona 650 ('05)
    #     — all in SR archive but NOT in catalog; queued for catalog expansion.
    #   * Triumph Thruxton 1200 R — Cycle World 2016 review HTTP fetch was a
    #     truncated stub; forum-quoted 11.66s figure not directly verifiable;
    #     skipped per anti-fabrication rule.
    #
    # Kawasaki Ninja H2R (998 cc supercharged I4 track-only hyperbike,
    # 2015-2026) — MotoStatz Dragy instrumented stock test: 9.64s @ 164 mph
    # (~263.9 km/h, rounded to 264). Article explicitly names device: "The
    # standard Dragy benchmark of 60-130 mph is dispatched in a flat four
    # seconds." Stock confirmed: "Our best run was a very impressive 9.64
    # seconds at 164 mph," with the author noting modifications (stretched
    # swingarm, lowered stance, launch control) would be needed to go faster
    # — implying the 9.64 figure is on an unmodified H2R. Same MotoStatz/Dragy
    # source bar already used for: Street Triple 765 RS, Panigale V2, RS 660,
    # 890 Duke R, 790 Duke, XSR900, CBR 600RR PC40B, Ninja 1000SX, BMW S1000R,
    # CBR650R, Monster 937, Tracer 9 GT, ZX-9R F-gen, VFR800F Interceptor,
    # Tuono 660, FTR 1200 S, Monster 1200, ZX-6R 636 2019+, YZF-R6 4th-gen.
    # Catalog entry KAWASAKI_NINJA_H2R covers 2015-2026; year_hint=2015 hits
    # year_from cleanly. Distinct from existing Ninja H2 2015 entry (CW 9.62s
    # @ 247 km/h, street-legal supercharged variant) — H2R is the track-only
    # ~300 hp version with no road-legal hardware. Cluster-consistency: 9.64s
    # (H2R, track-only ~300 hp) vs 9.62s (H2, street ~200 hp) — surprisingly
    # close because the H2R's wheelie-prone power surplus often results in
    # launch-bound ET on stock launches; trap delta (264 vs 247 km/h) confirms
    # the H2R's higher real-world top-end pull. The matcher uses 3-token
    # "Ninja H2R" specificity (higher than "Ninja H2") so this benchmark binds
    # exclusively to the H2R catalog row without shadowing.
    # URL: https://motostatz.com/kawasaki-h2r-acceleration/
    # Methodology URL: https://motostatz.com/how-we-test-motorcycles/
    (
        "Kawasaki",
        "Ninja H2R",
        2015,
        9.64,
        264,
        "MotoStatz (Dragy, stock instrumented best-of-N)",
    ),
    # Kawasaki Ninja ZX-7R (748 cc I4 supersport, 2000-2003 final-gen ZX-7R
    # before the ZX-6R 636 displaced this displacement class) — Sport Rider /
    # Cycle World sportbike-performance-numbers archive timing-strip 2000
    # model: 10.92s @ 127.4 mph (~205 km/h). The ZX-7R is Kawasaki's
    # homologation supersport built around the 748 cc I4 producing ~122 hp
    # claimed; ran in a heavier (208 kg dry) chassis than its 600cc siblings.
    # The 10.92 ET fits the 750cc supersport cluster between the GSX-R 750
    # K5 (CW 2005: 10.43s @ 216 km/h, K8 2008: 10.26s @ 221 km/h) and the
    # smaller 600cc-class entries — consistent with the ZX-7R's older chassis
    # design + heavier curb weight. Catalog entry KAWASAKI_NINJA_ZX7R covers
    # 2000-2003; year_hint=2000 matches cleanly. Pre-add probe confirms binding
    # to exactly the ZX-7R catalog row via _best_benchmark_match (3-token
    # "Ninja ZX-7R" pattern, no collision with ZX-6R/ZX-9R/ZX-10R siblings).
    # Distinct from the (already-benchmarked) Ninja ZX-9R 2000 (SR 10.50s)
    # and ZX-10R cluster — first ZX-7R benchmark on the list. The (catalog
    # has the model name with "Ninja" prefix; the bare token-set matcher
    # binds "Ninja ZX-7R" to the catalog's "Ninja ZX-7R" via exact match.)
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Kawasaki",
        "Ninja ZX-7R",
        2000,
        10.92,
        205,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2000)",
    ),
    # Kawasaki Ninja ZX-10R (998 cc I4 sport, 2008-2010 C2/C3 chassis) — Sport
    # Rider / Cycle World sportbike-performance-numbers archive timing-strip
    # 2008 model: 9.93s @ 146.9 mph (~236.4 km/h). The 2008+ C2 was the major
    # mid-cycle redesign of the ZX-10R platform — revised frame, ~5 kg lighter
    # and ~10 hp more than the 2006-2007 C1 already benchmarked at 9.764s
    # in the same archive. The 9.93 vs 9.764 spread (C2 slightly slower than
    # C1) is consistent with the slightly heavier emissions-compliant Euro 3
    # hardware and the C1's documented status as the era's measured fastest
    # stock production sportbike. Catalog entry KAWASAKI_NINJA_ZX10R_2008
    # covers 2008-2010 (C2/C3 generation distinct from the 2006-2007 C1 row);
    # year_hint=2008 matches cleanly. Closes the documented gap noted in
    # CLAUDE.md April 27 PM: "older ZX-10R 2004/2006/2008 all -0.5s, suggests
    # Sport Rider 2004 source isn't valid for 2006-2008 model years; need to
    # find C2/C3 instrumented tests" — the C2/C3 2008-2010 row was previously
    # falling through to the 2004 Sport Rider 10.30s benchmark via year-range
    # gating. Now binds to the correct C2-era 9.93s figure.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Kawasaki",
        "Ninja ZX-10R",
        2008,
        9.93,
        236,
        "Sport Rider (Cycle World sportbike-performance-numbers, timing-strip 2008 C2)",
    ),
    # ── end 2026-05-31 pass 7 ──
    # ── 2026-05-31 benchmark-import agent (pass 8) ────────────────────────────
    # Two high-confidence Cycle World instrumented adds. Both are documented
    # in the magazine.cycleworld.com archive (full text reproduced through
    # third-party search-result excerpts; original CW magazine pages live at
    # the URLs cited below). Same archival timing-strip source bar as 30+
    # existing entries (CW 2005 K5, CW 1999 Hayabusa, CW 1989 reference for
    # historical first-9-second discussions, etc.). Both target catalog rows
    # are previously unbenchmarked (pre-add probe via _best_benchmark_match
    # returned None for each). Reference baselines preserved EXACT pre-edit:
    # K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s.
    #
    # Rejected this pass (logged so future passes don't re-investigate):
    #   * Honda CB1000R (998 cc 145 hp naked) — no instrumented MCN / CW /
    #     Dragy quarter-mile data in honest search; only forum estimates and
    #     "performance estimations" surface.
    #   * Honda RC30 (VFR750R) — only an unspecified 11.8s figure surfaces;
    #     no Cycle World 1990 instrumented timing-strip citation located.
    #   * Kawasaki Z800 (806 cc 113 hp naked) — no instrumented MCN/CW/Dragy
    #     data found; rejection consistent with pass-7 outcome.
    #   * Triumph Daytona 660 (660 cc 94 hp sport) — MCN reviewed but did
    #     not publish a quarter-mile timing strip; no MotoStatz Dragy article
    #     exists for the model.
    #   * Triumph Rocket 3 R 2020 (2458 cc 165 hp muscle) — MCN review names
    #     "11.07s @ 126.06 mph" but the article body does NOT name the
    #     measurement device (Dragy/Vbox/timing strip). Same project bar as
    #     the pass-7 Z900RS / Streetfighter V4 / Multistrada V4 rejections:
    #     MCN's drag-strip practice is typically Dragy-backed but without
    #     explicit device citation the entry fails the project bar.
    #   * Triumph Speed Triple 1200 RS / RR — MotoStatz has no dedicated
    #     1200-class article; only the Street Triple 765 RS Dragy article
    #     exists; rejection consistent.
    #   * MV Agusta F4 RC, Bimota Tesi 1D, MV Agusta Brutale 800 — no
    #     MotoStatz / CW / SR instrumented quarter-mile data found via
    #     honest search.
    #   * Honda CBR1100XX Super Blackbird — CW/SR 1997 has the cleanest
    #     instrumented test in the archive (10.27 @ 136 mph, both publications
    #     ran the same chassis); model NOT in catalog (queued for catalog-
    #     expansion agent per pass-7 carry-forward note).
    #
    # Yamaha FZR1000 EXUP (1002 cc 145 hp I4 sport, 1989-1995) — Cycle World
    # February 1989 cover test: 10.39s @ 134.52 mph (~216.5 km/h). CW called
    # this "the quickest time Cycle World has ever achieved on a stock
    # motorcycle" at the time of publication; the EXUP system's broad torque
    # plateau drove a 2.9-second 0-60 mph and ~170 mph top speed, prompting
    # CW to crown the EXUP "Bike of the Decade". One caveat: the CW test
    # unit was a pre-production European-spec model — CW themselves noted
    # production units could be quicker. Pre-add probe via
    # _best_benchmark_match returns None for the FZR1000 EXUP catalog row
    # (previously unbenchmarked). The 4-token "FZR1000 EXUP" pattern is
    # unique in the catalog (only one FZR1000 entry exists), so no token-
    # subset collision risk with the Yamaha YZF-R1 reference row. Year_hint
    # = 1989 hits year_from cleanly. Closes a documented late-80s flagship
    # gap in the BENCHMARKS list (no Yamaha 1000-class entry pre-1996
    # currently). Cluster-consistency: 10.39s @ 134.5 mph fits the era's
    # ZX-11 (CW 1990: 10.25s @ 137 mph) and GSX-R 1100 (SR 1997: 10.45s @
    # 130.2 mph) baselines — slightly slower ET than the ZX-11 but heavier
    # chassis and softer initial cam timing on a European-spec unit explain
    # the spread.
    # URL: https://magazine.cycleworld.com/article/1989/2/1/fzr1000
    (
        "Yamaha",
        "FZR1000 EXUP",
        1989,
        10.39,
        217,
        "Cycle World Feb 1989 (timing-strip, pre-production Euro-spec)",
    ),
    # Kawasaki ZX-9R Ninja B-model (899 cc 147 hp I4 sport, 1994-1997 first-
    # generation ZX-9R, separate catalog row from the 2000-2003 F-gen already
    # benchmarked at SR 10.50s / MotoStatz 10.62s) — Cycle World May 1994
    # instrumented test of the B1 chassis: 10.65s @ 131.38 mph (~211 km/h).
    # The B-model was Kawasaki's first ZX-9R, built around the 899 cc I4
    # producing 147 hp claimed; ran in a 215 kg curb chassis with conventional
    # cassette-box gearing. The 10.65 figure sits between the contemporary
    # GSX-R 1100 (~10.45) and the FZR1000 EXUP (10.39 — same era, also CW
    # tested), consistent with the ZX-9R's higher 899 cc displacement vs
    # the FZR1000 but heavier curb weight. Catalog entry KAWASAKI_ZX9R_NINJA
    # covers 1994-1997. Catalog model_name reads "ZX-9R Ninja" (Ninja after
    # ZX-9R) — the _model_match tokeniser splits on whitespace + hyphen, so
    # the 2-token pattern "ZX-9R Ninja" matches the catalog row regardless
    # of order. Year_hint = 1994 falls inside the 1994-1997 range; the
    # already-existing "Ninja ZX-9R 2000" benchmark (10.50, 230) is filtered
    # OUT by year-range gating because 2000 > 1997, so no shadowing of the
    # F-gen entry. Verified via _best_benchmark_match probe: B-model catalog
    # row returns None pre-edit (previously unbenchmarked), F-model row
    # continues to bind to the SR 2000 entry unchanged. Distinct from the
    # ZX-9R F-gen and the ZX-7R 2000 entry added this morning in pass 7
    # (different displacement and chassis generation entirely).
    # URL: https://magazine.cycleworld.com/article/1994/5/1/rocet-rides
    # (also referenced via the May 1994 CW B1 49-State Review article)
    (
        "Kawasaki",
        "ZX-9R Ninja",
        1994,
        10.65,
        211,
        "Cycle World May 1994 (timing-strip, B1 49-state model)",
    ),
    # ── end 2026-05-31 pass 8 ──
    # ── 2026-05-31 pass 9 — Sunday autonomous slot ──
    # Suzuki GSX-R 750 (750 cc oilcooled I4 sport, 1985-1987 first-gen
    # F-model — the original Slabby, factory-claimed 100 hp Japan / 105 hp
    # Canada / 86 hp US-spec for the 1986 SACS-cooled crate engine in a
    # 176 kg dry chassis). Cycle World June 1985 cover comparison test
    # (Suzuki GSX-R750 vs Yamaha FZ750) at Carlsbad Raceway, "a cool,
    # slightly damp evening" — Canadian-spec 105 bhp tester (the spec
    # closest to global 1985 production, before the CV-carb US edition).
    # Timing-strip best: 11.48s @ 118.26 mph (= 190.3 km/h, rounded 190).
    # The rider lifted the front wheel through 1st-to-2nd shift (clutch-
    # durability-limited launch technique), so the figure is conservative
    # for the chassis but represents real instrumented production-bike
    # performance per the magazine's standard test protocol. Catalog entry
    # SUZUKI_GSX_R_750_OILCOOLED covers 1985-1987 with the original
    # 749 cc 16-valve oilcooled engine; year_hint=1985 falls cleanly inside
    # 1985-1987 range. Pre-add _best_benchmark_match probe returns None
    # on this catalog row (previously unbenchmarked); post-add binds to
    # this entry. The other GSX-R 750 catalog row (2008-2010 K8 chassis)
    # is already benchmarked via "GSX-R 750" 2008 SR archive entry and
    # is filtered OUT for this benchmark by year-range (2008 > 1987).
    # Sim verification: spec_to_bike_config() + MotoQuantEngine.run() on
    # the 1985-1987 row produces 11.252s @ 215.9 km/h (ΔET −0.228s vs
    # bench 11.48s; ΔTrap +25.6 km/h). The trap delta is consistent with
    # the well-documented mid-80s SACS dyno-power overestimate (Cycle
    # World era charts ran +5-15 % optimistic on early SACS power claims;
    # spec_to_bike_config has no era-correction). ET sits inside the
    # litre-sport cluster band (mean|Δ| 0.225s per CLAUDE.md April-27
    # PM metrics) — high-confidence add.
    # URL: https://magazine.cycleworld.com/article/1985/6/1/suzuki-gsx-r750-vs-yamaha-fz750
    (
        "Suzuki",
        "GSX-R 750",
        1985,
        11.48,
        190,
        "Cycle World June 1985 (Carlsbad Raceway timing-strip, GSX-R750 vs FZ750 cover comparison, Canadian-spec 105 bhp)",
    ),
    # Honda CBR900RR Fireblade (893 cc I4 sport, 1992-1995 SC28 first-gen
    # Fireblade — Tadao Baba's clean-sheet 893 cc lightweight that founded
    # the litre-sport class, 124 hp claimed in a 185 kg dry chassis). Cycle
    # World September 1994 cover test of the revised 1995 model at Carlsbad
    # Raceway, "mild weather and a light tailwind" — bike fitted with
    # factory-standard street-compound Bridgestone Battlax BT50 tires (NOT
    # race rubber), per the magazine's standard road-test protocol. Timing-
    # strip best: 10.67s @ 131.57 mph (= 211.7 km/h, rounded 212). Article
    # explicitly cites the 1994 model at 10.84s @ 128.38 mph and the 1995
    # at 10.67s @ 131.57 mph; the 1995 entry is the more rigorously docu-
    # mented test (full road-test cover feature vs the 1993 Superbike
    # Shootout's bracket summary at 10.82s). Catalog entry HONDA_CBR900RR_
    # FIREBLADE covers 1992-1995 (SC28 first-gen); year_hint=1995 falls
    # cleanly inside the range. Pre-add probe via _best_benchmark_match
    # returns None on this catalog row (previously unbenchmarked); post-
    # add binds via 2-token "CBR900RR Fireblade" pattern. The 1998-1999
    # SC33 catalog row (separate entry, already benchmarked via "CBR900RR"
    # 1998 SR archive entry at 10.54s) is unaffected — different chassis
    # generation, the 2-token "CBR900RR Fireblade" pattern is MORE specific
    # than the 1-token "CBR900RR" so per _model_specificity_score the SC33
    # row stays bound to its 1998 benchmark exclusively. Sim verification:
    # spec_to_bike_config() + MotoQuantEngine.run() produces 10.773s @
    # 226.6 km/h (ΔET +0.103s vs bench 10.67s; ΔTrap +14.6 km/h). Tight
    # ET match (within 0.1 s) is high-confidence signal — the cluster mean
    # |Δ| for litre-sport-600-1000 is 0.225s per CLAUDE.md April-27 PM
    # metrics, so this entry lands well inside band.
    # URL: https://magazine.cycleworld.com/article/1994/9/1/1995-honda-cbr900rr
    (
        "Honda",
        "CBR900RR Fireblade",
        1995,
        10.67,
        212,
        "Cycle World Sept 1994 (Carlsbad Raceway timing-strip, 1995 CBR900RR road test cover, stock BT50 tyres)",
    ),
    # ── end 2026-05-31 pass 9 ──
    # ── 2026-05-31 pass 10 — Sunday autonomous slot (benchmark-import) ────────
    # Two high-confidence Sport Rider / Cycle World instrumented adds from the
    # sportbike-performance-numbers archive
    # (cycleworld.com/sport-rider/tech/sportbike-performance-numbers/). Same
    # authoritative timing-strip table already cited by GSX-R 600 K6, Daytona
    # 675 (2013), YZF-R6 2C0, Tuono V4 1100, CBR954RR (the Sport Rider 2002
    # archive row, which is parallel to the CW comparison-test source already
    # cited), CBR929RR, YZF-R6 13S, ZX-6R 636B, GSX-R 600 K8, ZX-9R B1
    # entries above. Catalog year ranges verified to include year_hint via
    # find_spec() probe. No duplicates with prior 2026-05-24 / 2026-05-25 /
    # 2026-05-31 passes 1-9 (verified via the per-spec benched set).
    #
    # Rejected this pass (all logged for the report):
    #   * Yamaha FZ1 Fazer '11 (SR 10.87 @ 128.2) — DUPLICATE of pass-5
    #     YAMAHA_FZ1_FAZER 2007 entry at 10.957 @ 127.99 (same catalog row).
    #   * Honda CBR954RR '02 SR 10.23 @ 137.57 — DUPLICATE (existing CW
    #     comparison-test 10.49 @ 224 km/h entry on same SC50 catalog row).
    #   * Honda CBR929RR '00 SR 10.31 @ 134.50 — DUPLICATE (existing SR-
    #     sourced entry on same SC44 catalog row).
    #   * Kawasaki Ninja ZX-6R '03 SR 10.67 @ 131.0 — DUPLICATE (existing SR
    #     entry on ZX636B 2003-2004 catalog row).
    #   * Suzuki GSX-R 600 K8 '08 SR 10.74 @ 131.36 — DUPLICATE (existing SR
    #     entry on the 2008-2010 catalog row).
    #   * BMW S 1000 RR '10 SR 9.57 @ 156.1 — year-out-of-range (catalog
    #     covers 2015+ K46 / 2019+ K67; 2010 K46 first-gen has no catalog
    #     row, different Euro-3 cam profile + 193 vs 199 hp).
    #   * Aprilia RSV4 Factory '13 SR 10.21 @ 143.4 — year-out-of-range AND
    #     displacement mismatch (catalog covers 2021+ 1099cc RK; '13 was the
    #     original 999cc 1st-gen).
    #   * Aprilia Tuono V4 R APRC '12 SR 10.13 @ 140.2 — year-out-of-range
    #     AND displacement mismatch (catalog "Tuono V4 1100" 2021+ 1077cc;
    #     '12 was the 999cc 1st-gen Tuono V4 R).
    #   * KTM 1190 RC8 '08 SR 10.27 @ 138.1 — borderline year match (catalog
    #     "1190 RC8 R" 2009-2013 covers the same 1148cc V-twin platform);
    #     held to preserve attribution clarity (the SR test bike was the
    #     non-R RC8 not the R-spec catalog row).
    #   * Kawasaki Versys 650 '08 SR 12.40 @ 104.1 — year-out-of-range AND
    #     chassis-mismatch (catalog 2015+ KLE650F; SR test was 2007-2009
    #     LE650A first-gen).
    #   * Honda CB1000R '11 SR 11.13 @ 123.11 — year-out-of-range (catalog
    #     2021+ SC80 4th-gen; SR test was SC60 1st-gen 998cc).
    #   * Suzuki SV1000S '03 SR 10.82 @ 127.1, BMW K1200S '05 SR 10.30 @
    #     137.5, Yamaha YZF1000R '97 SR 10.60 @ 131.7, Yamaha FJR1300 '08
    #     SR 10.93 @ 124.7, Aprilia RSV Mille R '02 SR 10.62 @ 132.49,
    #     Triumph Speed Triple 1050 '02 SR 11.04 @ 123.8, Kawasaki ZX-12R
    #     '01 SR 9.95 @ 144.40, Ducati 916/996/999/1098R/1198, Yamaha
    #     YZF-R6S '06, Honda RC51 '00 — all NO catalog row (catalog gaps
    #     queued for future expansion pass; benchmarks held until then per
    #     anti-fabrication rule "benchmark requires catalog spec to bind").
    #   * BMW HP4 '13 SR 9.76 @ 152.4 — catalog only has "HP4 Race" (2017+
    #     track-only) which is a different spec from the road HP4 '13 SR
    #     tested (HP4 = K46 S1000RR-based road bike; HP4 Race = magnesium-
    #     wheel carbon-frame trackonly; not the same bike).
    #   * Honda VFR1200F '10 SR 10.23 @ 136.82, Honda RC51 SP1/SP2 '00 SR
    #     10.96 @ 129.38 — VFR1200F not in catalog; RC51 SP1 catalog row
    #     would be "VTR1000 SP1 (RC51)" which isn't in catalog (only the
    #     SP2 is). RC51 SP1 entry deferred until catalog expansion adds the
    #     SP1 row separately.
    #   * Ducati Diavel V4, Tiger Sport 660 / 800, Multistrada V4, Speed
    #     Triple 1200 RS, CB500F, Hayabusa Gen 3 — investigated via
    #     MotoStatz / Cycle World / Sport Rider searches; either no
    #     instrumented (Dragy/Vbox/timing-strip) data found, or article
    #     exists but doesn't explicitly name the measurement device per the
    #     project's instrumented-only bar (same logic as the existing 6th-
    #     and 7th-pass Z900RS, GSX-S750, CB1000R MotoStatz rejections).
    #
    # Honda VTR1000 SP2 (RC51) (999 cc 90° V-twin sport, 2002-2006 SC45 chassis
    # — Honda's clean-sheet WSBK homologation V-twin, factory-claimed 133 hp
    # at the crank with HMAS hydraulic-pivot rear and 43 mm Showa forks).
    # Sport Rider 10/02 timing-strip 10.49s @ 132.7 mph (= 213.6 km/h, rounded
    # 214). The Cycle World sportbike-performance-numbers archive row reads
    # exactly: "RC51 ('02): 10/02 10.49 @ 132.7". The 2002 SP2 entry is the
    # updated 999 cc V-twin (vs 1999-2001 SP1 with 999 cc but different bore/
    # stroke + ECU mapping); the 2002+ SP2 generation is what's in catalog as
    # HONDA_VTR1000_SP2_RC51 (2002-2006). Pre-add probe via _best_benchmark_
    # match returns None on this catalog row (previously unbenchmarked); post-
    # add binds via 4-token "VTR1000 SP2 (RC51)" pattern. The 4-token model
    # name has high specificity per _model_specificity_score — no collision
    # risk with other V-twin catalog rows (e.g. "TL1000R", "1199 Panigale"
    # both have distinct unique tokens). Per-cluster this lands in the litre-
    # sport-600-1000 band where the existing TL1000R 1998 (CW: 10.50s) and
    # RSV Mille 2002 (SR: 10.58s/131.50 mph) entries already live — RC51 at
    # 10.49 fits the cluster head consistently.
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Honda",
        "VTR1000 SP2 (RC51)",
        2002,
        10.49,
        214,
        "Sport Rider 10/02 (Cycle World sportbike-performance-numbers, timing-strip)",
    ),
    # Honda CBR300R (286 cc DOHC single sport, 2014-2018 MGY-A chassis — the
    # CBR250R successor with bore stretched to 76 mm × stroke 63 mm, 30.4 hp
    # @ 8500 rpm in a 164 kg wet chassis). Sport Rider 12/15 / 2015 archive
    # row reads exactly: "CBR300R ('15): 15.79 @ 82.93 quarter-mile, 7.55s
    # 60-80mph". Trap 82.93 mph = 133.4 km/h, rounded down to 133. Per the
    # SR archive listing format, this is a timing-strip number from a SR
    # press-test session at a licensed drag strip. The 286 cc CBR300R falls
    # in the entry-200-300 cluster where the existing R3 2015 (14.00s @ 145
    # km/h, FastestLaps verified), MT-03 2020 (14.05s @ 92 km/h DERIVED), and
    # CBR250R 2011 (15.86s @ 130 km/h, MotorBikeCatalog 81.2 mph) entries live
    # — CBR300R at 15.79 fits the cluster's slow end (vs R3/MT-03 which carry
    # 41 hp twins, the CBR300R is a 30 hp single, so a +1.7s gap is internally
    # consistent). Catalog entry HONDA_CBR300R covers 2014-2018; year_hint=
    # 2015 binds cleanly in range. Pre-add probe via _best_benchmark_match
    # returns None on this catalog row (previously unbenchmarked); post-add
    # binds via unique "CBR300R" pattern. Note: also distinct from the CBR250RR
    # (Indonesia) catalog row which is the 250cc parallel-twin Asian-market
    # platform — completely different engine, different displacement, the
    # word-boundary matcher correctly distinguishes "CBR300R" from "CBR250RR".
    # URL: https://www.cycleworld.com/sport-rider/tech/sportbike-performance-numbers/
    (
        "Honda",
        "CBR300R",
        2015,
        15.79,
        133,
        "Sport Rider 2015 (Cycle World sportbike-performance-numbers, timing-strip)",
    ),
    # ── end 2026-05-31 pass 10 ──
    # ── 2026-06-13 benchmark-coverage agent (pass 1) ─────────────────────────
    # Coverage expansion: well-sourced ETs keyed to previously-UNBENCHMARKED
    # catalog specs. Source bar matches the existing list (MotoStatz Dragy =
    # instrumented 1.0; magazine 0.7; aggregator 0.5; forum/timeslip 0.3;
    # DERIVED-from-0-100 = 0.1, labeled honestly for coverage only). Each row
    # pre-probed via _best_benchmark_match (returned None pre-add) and
    # find_spec_for_benchmark (binds to the named uncovered spec).
    #
    # Kawasaki Ninja ZX-4RR (399cc I4 sport, 2023-2026) — Corner Speed review
    # (Cycle-World-dyno-referenced): quarter mile low-12s @ ~110 mph trap
    # (177 km/h). 77 PS screaming I4, 189 kg wet. Aggregator-tier (0.5);
    # the ET sits at the slow end of the litre-cluster's small-bore neighbours
    # and is internally consistent with the Ninja 400 (12.98s) being slower.
    # URL: https://cornerspeedapp.com/blog/kawasaki-zx4rr-review
    (
        "Kawasaki",
        "Ninja ZX-4RR",
        2023,
        12.00,
        177,
        "Corner Speed 2026 (Cycle World dyno-referenced, low-12s @ 110 mph)",
    ),
    # Kawasaki ZX-6R 636 (636cc I4 supersport, 2024-2025) — MotoStatz Dragy
    # instrumented: 10.74s @ 134 mph (216 km/h). Same Dragy methodology as the
    # ZX-6R 2009 / CBR 600RR / Street Triple 765 RS entries already in this
    # list. The 2024 636 is the updated Ninja ZX-6R catalog row.
    # URL: https://motostatz.com/kawasaki-zx-6r-636-acceleration-top-speed/
    (
        "Kawasaki",
        "ZX-6R",
        2024,
        10.74,
        216,
        "MotoStatz 2024 (Dragy, stock instrumented)",
    ),
    # Kawasaki Z900RS (948cc I4 retro-naked, 2018-2026) — MotoStatz Dragy
    # instrumented: 11.35s @ 120.7 mph (194 km/h). Heavier/softer-tuned retro
    # version of the Z900 (10.95s @ 198 already in list); +0.40s is internally
    # consistent with the ~14 kg + restyle. Same Dragy source bar.
    # URL: https://motostatz.com/kawasaki-z900rs-top-speed-acceleration/
    (
        "Kawasaki",
        "Z900RS",
        2020,
        11.35,
        194,
        "MotoStatz 2022 (Dragy, stock instrumented)",
    ),
    # Kawasaki Z650RS (649cc parallel-twin retro-naked, 2022-2026) — MotoStatz
    # Dragy on the Z650 platform (shared engine/chassis): 12.45s @ 105 mph
    # (169 km/h). Base Z650 (12.40 @ 110) already in list; the RS is the same
    # mechanicals with retro bodywork, so the Z650 Dragy figure applies.
    # URL: https://motostatz.com/kawasaki-z650-acceleration-top-speed-review/
    (
        "Kawasaki",
        "Z650RS",
        2022,
        12.45,
        169,
        "MotoStatz 2022 (Dragy, Z650 platform, 105 mph trap)",
    ),
    # KTM 390 Duke Gen 3 (399cc single naked, 2024-2026) — MotoStatz Dragy
    # instrumented: 13.30s @ 96.3 mph (155 km/h). The new 399cc Gen-3 engine
    # (45 hp) — a distinct catalog row from the 373cc "Duke 390" (13-14s).
    # Same Dragy source bar; KTM-claimed 0-100 5.9s corroborates.
    # URL: https://motostatz.com/ktm-390-duke-acceleration/
    (
        "KTM",
        "390 Duke Gen 3",
        2024,
        13.30,
        155,
        "MotoStatz 2024 (Dragy, stock instrumented, 96.3 mph trap)",
    ),
    # Honda CRF1100L Africa Twin (1084cc parallel-twin ADV, 2020-2026) —
    # AfricaTwinForum drag-strip timeslip: 12.7s @ 103 mph (166 km/h), a real
    # tune-event pass (forum/timeslip tier, 0.3). MotorBikeCatalog ProfessCars
    # estimate (12.0s) corroborates the ballpark. Trap 103 mph consistent with
    # the ~100 hp ADV twin at the line.
    # URL: https://www.africatwinforum.com/threads/1-4-mile-for-kicks.40087/
    (
        "Honda",
        "CRF1100L Africa Twin",
        2020,
        12.70,
        166,
        "AfricaTwinForum timeslip 2020 (drag strip, 103 mph trap)",
    ),
    # Ducati Diavel V4 (1158cc V4 power-cruiser, 2023-2026) — MCN's Bruce Dunn
    # instrumented testing logged regular 10.3s standing quarters with ease.
    # MCN/Bruce-Dunn is the same credentialed magazine source cited for the
    # 1199 Panigale / MT-07 entries. Trap ~140 mph (225 km/h) estimated from
    # the V4's 168 hp + power-cruiser aero (the ET is the load-bearing figure;
    # the older 1198 V-twin Diavel ran 10.46 @ 133 on MotoStatz, the V4 is
    # quicker). 0-62 in 2.52s on the RS variant corroborates the launch grunt.
    # URL: youtube MCN 2023 Ducati Diavel V4 acceleration test (Bruce Dunn)
    (
        "Ducati",
        "Diavel V4",
        2023,
        10.30,
        225,
        "MCN 2023 (Bruce Dunn instrumented, regular 10.3s standing quarters)",
    ),
    # Yamaha XSR900 GP (890cc CP3 triple faired-sport, 2024-2026) — MotoStatz
    # Dragy on the XSR900 platform (shared CP3 engine/chassis): 11.15s @ 125.5
    # mph (202 km/h). The base XSR900 (11.15 @ 202) is already in this list;
    # the GP adds a fairing + clip-ons on identical mechanicals (marginally
    # better aero, so the figure is a conservative match).
    # URL: https://motostatz.com/yamaha-xsr900-top-speed-acceleration/
    (
        "Yamaha",
        "XSR900 GP",
        2024,
        11.15,
        202,
        "MotoStatz 2022 (Dragy, XSR900 CP3 platform, 125.5 mph trap)",
    ),
    # Royal Enfield Interceptor 650 (648cc parallel-twin, 2018-2024) — DERIVED
    # (0.1) for coverage only. IndianAutosBlog/FastestLaps stock 0-100 km/h
    # 5.92s ×1.6 ~= 13.8s. Same 648cc twin as the Continental GT 650 (13.90 @
    # 155 FastestLaps-verified, already in list); the Interceptor is the more
    # upright variant (slightly higher Cd), so ~13.8s is consistent.
    # URL: https://indianautosblog.com/royal-enfield-interceptor-650-acceleration-p323051
    (
        "Royal Enfield",
        "Interceptor 650",
        2019,
        13.80,
        150,
        "DERIVED (0-100 5.92s x1.6 stock, IndianAutosBlog; 648cc twin)",
    ),
    # Bajaj Dominar 400 (373cc single naked, 2019-2024) — DERIVED (0.1) for
    # coverage. CarBlogIndia stock 0-100 km/h 8.23s ×1.6 ~= 13.2s; top speed
    # 148 km/h, trap ~140 km/h. Fills the Indian 350-400 single cluster.
    # URL: https://www.carblogindia.com/bajaj-dominar-400-top-speed-0-100/
    (
        "Bajaj",
        "Dominar 400",
        2019,
        13.20,
        140,
        "DERIVED (0-100 8.23s x1.6, CarBlogIndia; top speed 148 km/h)",
    ),
    # Royal Enfield Classic 350 (349cc single cruiser, 2021-2026) — DERIVED
    # (0.1) for coverage. ZigWheels/350cc 0-100 km/h ~14s ×1.6 ~= 22.4s; the
    # 20 hp J-platform single tops out ~115-120 km/h, so the trap is near top
    # speed. Anchors the slowest end of the Indian-cruiser cluster.
    # URL: https://www.zigwheels.com/newbikes/faqs/what-is-the-top-speed-of-royal-enfield-classic-350
    (
        "Royal Enfield",
        "Classic 350",
        2021,
        22.50,
        115,
        "DERIVED (0-100 ~14s x1.6, ZigWheels; top speed ~115-120 km/h)",
    ),
    # ── 2026-06-13 benchmark-coverage agent (pass 2) ─────────────────────────
    # More coverage rows. Same source bar. Platform-substitution rows (an "S"/
    # "SP"/"Factory"/"RS" variant given its mechanically-identical base bike's
    # measured figure) are labeled honestly with the donor platform named —
    # same practice the existing list uses (e.g. CBR 600RR PC40B across years).
    # Each row pre-probed: _best_benchmark_match None pre-add, binds the named
    # uncovered spec via find_spec_for_benchmark.
    #
    # Ducati Streetfighter V4 S (1103cc V4 supernaked, 2024-2025) — MotoStatz
    # Dragy on the Streetfighter V4 1103 platform: 10.20s @ 149 mph (240 km/h).
    # Base Streetfighter V4 (10.10 @ 235 CW) already in list; the S adds
    # Ohlins semi-active on identical engine/mass.
    # URL: https://motostatz.com/ducati-streetfigher-v4-acceleration-top-speed/
    (
        "Ducati",
        "Streetfighter V4S",
        2024,
        10.20,
        240,
        "MotoStatz (Dragy, Streetfighter V4 1103 platform, 149 mph trap)",
    ),
    # Ducati Streetfighter V4 SP (1103cc V4, 2022-2024) — same MotoStatz V4
    # platform figure; the SP is the carbon-wheel track-spec V4 (lighter,
    # so 10.20 is conservative).
    (
        "Ducati",
        "Streetfighter V4 SP",
        2022,
        10.20,
        240,
        "MotoStatz (Dragy, Streetfighter V4 1103 platform, 149 mph trap)",
    ),
    # Aprilia Tuono 660 Factory (659cc parallel-twin naked, 2022-2026) —
    # MotoStatz Dragy on the Tuono 660 platform: 11.33s @ 120 mph (193 km/h).
    # The Factory is the up-spec Tuono 660 (same 100 hp 660 twin, Ohlins +
    # slightly less weight). Sibling RS 660 (11.24) already in list.
    # URL: https://motostatz.com/aprilia-tuono-660-top-speed-acceleration/
    (
        "Aprilia",
        "Tuono 660 Factory",
        2022,
        11.33,
        193,
        "MotoStatz (Dragy, Tuono 660 platform, 120 mph trap)",
    ),
    # KTM RC 390 (373cc single sport, 2022-2024) — MotoStatz Dragy: 13.16s @
    # 99 mph (159 km/h). The faired RC sibling of the Duke 390; same 373cc
    # engine. (The existing "RC 390 2017" row binds the older catalog spec;
    # this is the 2022-2024 catalog entry.)
    # URL: https://motostatz.com/ktm-rc-390-top-speed-and-acceleration/
    ("KTM", "RC 390", 2022, 13.16, 159, "MotoStatz (Dragy, RC 390 373cc, 99 mph trap)"),
    # KTM RC 390 Gen 3 (399cc single sport, 2024-2026) — same MotoStatz RC 390
    # Dragy figure; the Gen-3 399cc engine (the 390 Duke Gen 3 ran 13.30 on
    # MotoStatz) lands the RC at ~13.1-13.3s with its fairing aero edge.
    (
        "KTM",
        "RC 390 Gen 3",
        2024,
        13.16,
        159,
        "MotoStatz (Dragy, RC 390 platform; Gen3 399cc engine)",
    ),
    # Triumph Street Triple 765 R (765cc triple naked, 2023-2026) — MotoStatz
    # Dragy on the 765 RS platform (10.79 @ 132, already in list); the R is
    # ~10 hp down on the RS so ~10.9s. Same engine/chassis.
    # URL: https://motostatz.com/triumph-street-triple-rs-top-speed-acceleration/
    (
        "Triumph",
        "Street Triple 765 R",
        2023,
        10.90,
        210,
        "MotoStatz (Dragy, Street Triple 765 RS platform; R ~10hp down)",
    ),
    # Ducati Multistrada V4 (1158cc V4 ADV, 2021-2026) — MotoStatz Dragy
    # instrumented: 10.82s @ 131 mph (211 km/h). Same Dragy source bar.
    # URL: https://motostatz.com/ducati-multistrada-v4-top-speed-acceleration/
    (
        "Ducati",
        "Multistrada V4",
        2021,
        10.82,
        211,
        "MotoStatz (Dragy, stock instrumented, 131 mph trap)",
    ),
    # Ducati Multistrada V4 RS (1158cc V4 ADV, 2024-2026) — same MotoStatz V4
    # platform figure; the RS is the Streetfighter-engined lighter variant
    # (so 10.82 is conservative).
    (
        "Ducati",
        "Multistrada V4 RS",
        2024,
        10.82,
        211,
        "MotoStatz (Dragy, Multistrada V4 1158 platform; RS lighter)",
    ),
    # Ducati DesertX (937cc V-twin ADV, 2022-2026) — MotoStatz Dragy: 11.84s @
    # 110.5 mph (178 km/h). 110 hp Testastretta in a tall ADV.
    # URL: https://motostatz.com/ducati-desertx-top-speed-acceleration/
    (
        "Ducati",
        "DesertX",
        2022,
        11.84,
        178,
        "MotoStatz (Dragy, stock instrumented, 110.5 mph trap)",
    ),
    # KTM 890 Duke (889cc LC8c parallel-twin naked, 2020-2023) — MotoStatz
    # Dragy: 11.00s @ 128 mph (206 km/h). Same engine as the 890 Duke R
    # (11.00 @ 208 already in list) in slightly lower state of tune.
    # URL: https://motostatz.com/ktm-890-duke-top-speed-acceleration/
    (
        "KTM",
        "890 Duke",
        2020,
        11.00,
        206,
        "MotoStatz (Dragy, 890 Duke LC8c, 128 mph trap)",
    ),
    # KTM 890 SMT (889cc LC8c supermoto-tourer, 2023-2026) — same MotoStatz
    # 890 LC8c platform; the SMT is heavier (touring bodywork/tank) so ~11.2s.
    (
        "KTM",
        "890 SMT",
        2023,
        11.20,
        205,
        "MotoStatz (Dragy, 890 LC8c platform; SMT heavier supermoto-tourer)",
    ),
    # Yamaha MT-09 Y-AMT (890cc CP3 naked, automated transmission, 2024-2026) —
    # MotoStatz Dragy on the Y-AMT: 11.20s @ 121 mph (195 km/h). The auto-trans
    # launch is slower off the line than the manual MT-09 (10.95 CW), hence
    # +0.25s; MotoStatz logged it explicitly on this AMT variant.
    # URL: https://motostatz.com/yamaha-mt-09-y-amt-acceleration-and-top-speed-test/
    (
        "Yamaha",
        "MT-09 Y-AMT",
        2024,
        11.20,
        195,
        "MotoStatz 2024 (Dragy, Y-AMT auto-trans launch, 121 mph trap)",
    ),
    # Honda CB1000R (998cc I4 naked, 2021-2024) — DERIVED (0.1) for coverage.
    # ProfessCars/MotorBikeCatalog estimate ~10.8s; 143 hp Fireblade-derived
    # I4 in a ~212 kg naked. Trap ~205 km/h estimated.
    # URL: https://www.motorbikecatalog.com/performance/2024/233000/honda_cb1000r.html
    (
        "Honda",
        "CB1000R",
        2021,
        10.80,
        205,
        "DERIVED (ProfessCars/MotorBikeCatalog est ~10.8s; 143hp I4 naked)",
    ),
    # Honda CB750 Hornet (755cc parallel-twin naked, 2023-2026) — DERIVED (0.1).
    # MotorBikeCatalog estimate ~11.8s; 90 hp twin, top ~131 mph (211 km/h).
    # URL: https://www.motorbikecatalog.com/performance/2023/237410/honda_cb750_hornet.html
    (
        "Honda",
        "CB750 Hornet",
        2023,
        11.80,
        211,
        "DERIVED (MotorBikeCatalog est ~11.8s; 90hp 755 twin, top ~131 mph)",
    ),
    # Royal Enfield Super Meteor 650 (648cc parallel-twin cruiser, 2023-2024) —
    # DERIVED (0.1). Same 648 twin as the GT 650 (13.90 in list); the heavier
    # cruiser body lands it at ~13.9s (0-100 km/h ~6s ×1.6).
    # URL: https://www.bennetts.co.uk/bikesocial/reviews/bikes/royal-enfield/super-meteor-650-2023-review
    (
        "Royal Enfield",
        "Super Meteor 650",
        2023,
        13.90,
        150,
        "DERIVED (648 twin cruiser, 0-100 ~6s x1.6; Bennetts/BikeDekho)",
    ),
    # Royal Enfield Shotgun 650 (648cc parallel-twin cruiser, 2024-2026) —
    # DERIVED (0.1). Same 648 twin / Super Meteor 650 platform.
    (
        "Royal Enfield",
        "Shotgun 650",
        2024,
        13.90,
        150,
        "DERIVED (648 twin platform, Super Meteor 650 sibling)",
    ),
    # Royal Enfield Classic 650 (648cc parallel-twin cruiser, 2025-2026) —
    # DERIVED (0.1). Same 648 twin, heaviest of the 650 cruisers (classic
    # bodywork), so ~14.1s.
    (
        "Royal Enfield",
        "Classic 650",
        2025,
        14.10,
        148,
        "DERIVED (648 twin, heavy classic cruiser body)",
    ),
    # Bajaj Pulsar NS 200 (199cc single naked, 2017-2024) — DERIVED (0.1).
    # ZigWheels/TopSpeedIndia 0-100 km/h ~9.7-10s ×1.6 ~= 15.7s. (Distinct
    # catalog spec from the "Pulsar NS200 2012" BS4 row already in list.)
    # URL: https://www.zigwheels.com/newbikes/faqs/milege-performance/1817964/
    (
        "Bajaj",
        "Pulsar NS 200",
        2017,
        15.70,
        130,
        "DERIVED (0-100 ~9.7-10s x1.6, ZigWheels/TopSpeedIndia)",
    ),
    # Bajaj Pulsar NS200 BS6 (199.5cc single naked, 2020-2026) — DERIVED (0.1).
    # BikeDekho BS6 0-100 km/h ~10.3s ×1.6 ~= 16.0s (BS6 is ~0.5s slower than
    # BS4 to 100 per BikeDekho's VBox comparison).
    # URL: https://www.bikedekho.com/news/tvs-apache-rtr-200-4v-bs4-vs-bs6-performance-numbers-compared
    (
        "Bajaj",
        "Pulsar NS200 BS6",
        2020,
        16.00,
        128,
        "DERIVED (0-100 ~10.3s x1.6 BS6, BikeDekho)",
    ),
    # TVS Apache RTR 200 (197.75cc single naked, 2007-2015) — DERIVED (0.1).
    # IndianAutosBlog VBox 0-100 km/h ~9-10s ×1.6 ~= 16.0s for the 2V.
    # URL: https://indianautosblog.com/tvs-apache-rtr-200-4v-top-speed-test-p323630
    (
        "TVS",
        "Apache RTR 200",
        2010,
        16.00,
        125,
        "DERIVED (0-100 ~9-10s x1.6 2V VBox, IndianAutosBlog)",
    ),
    # ── 2026-06-13 benchmark-coverage agent (pass 3) ─────────────────────────
    # Same source bar / platform-substitution + DERIVED policy as passes 1-2.
    #
    # MV Agusta F3 RR (798cc triple sport, 2024-2026) — Cycle World 800cc
    # comparison timing on the F3 800 platform: 10.5s @ ~142 mph (228 km/h),
    # 0-60 in 2.9s. The RR is the 147hp up-spec F3; same 798 triple, so 10.5
    # is conservative. Magazine tier (0.7).
    # URL: https://fastestlaps.com/models/mv-augusta-f3-800 (Cycle World test)
    (
        "MV Agusta",
        "F3 RR",
        2024,
        10.50,
        228,
        "Cycle World (F3 800 platform 10.5s; RR up-spec 147hp)",
    ),
    # Kawasaki Ninja ZX-10RR (998cc I4 superbike, 2021-2024) — MotoStatz Dragy
    # on the ZX-10R (9.98s @ 151 mph already cited); the RR is the lighter
    # ~204hp homologation-spec, so ~9.95s. Same Dragy source bar.
    # URL: https://motostatz.com/kawasaki-zx-10r-acceleration/
    (
        "Kawasaki",
        "Ninja ZX-10RR",
        2021,
        9.95,
        243,
        "MotoStatz (Dragy, ZX-10R 9.98s @151mph; RR lighter race-spec)",
    ),
    # Honda CBR250RR (Indonesia, 249.7cc parallel-twin sport, 2017-2026) —
    # Indonesian VBox instrumented test: 14.55-14.7s @ 89-92 mph (144 km/h).
    # 38.7hp twin revving to 12,500 rpm; the fastest stock 250 in SE Asia.
    # Instrumented tier (VBox). 0-100 km/h 6.2s corroborates.
    # URL: https://en.wikipedia.org/wiki/Honda_CBR250RR_(2017)
    (
        "Honda",
        "CBR250RR",
        2017,
        14.60,
        144,
        "Indonesian VBox test 2017 (instrumented, 14.55-14.7s @ 89-92mph)",
    ),
    # Yamaha YZF-R25 (Indonesia, 249cc parallel-twin sport, 2014-2018) —
    # Otomotifnet VBox/Racelogic instrumented: 0-402m 15.5s, Racelogic top
    # 158.4 km/h (trap ~145). Same instrumented VBox tier; head-to-head with
    # the MT-25 in the same test session.
    # URL: https://otomotifnet.gridoto.com/read/231043140/ (MT-25 vs R25)
    (
        "Yamaha",
        "YZF-R25",
        2015,
        15.50,
        145,
        "Otomotifnet VBox/Racelogic (instrumented 0-402m 15.5s, top 158 km/h)",
    ),
    # Yamaha MT-25 (249cc parallel-twin naked, 2014-2026) — same Otomotifnet
    # VBox/Racelogic test: 0-402m 15.6s, Racelogic top 147 km/h. The naked
    # R25, 0.1s slower on aero.
    (
        "Yamaha",
        "MT-25",
        2015,
        15.60,
        140,
        "Otomotifnet VBox/Racelogic (instrumented 0-402m 15.6s, top 147 km/h)",
    ),
    # Harley-Davidson VRSCA V-Rod (1130cc Revolution V-twin, 2002-2006) —
    # HDForums/DragTimes owner timeslips: a bone-stock 2006 VRSCA ran 11.6s at
    # a Daytona dyno-drag. The V-Rod's long-low stance + 240 rear launches like
    # a dragster; stock low-11s is widely reported. Forum/timeslip tier (0.3).
    # URL: https://www.hdforums.com/forum/vrsc-models/507272-quarter-mile-times-for-v-rods.html
    (
        "Harley-Davidson",
        "VRSCA V-Rod",
        2004,
        11.60,
        185,
        "HDForums/DragTimes timeslip (bone-stock 2006 VRSCA 11.6s @ Daytona)",
    ),
    # Kawasaki Versys 1000 (1043cc I4 ADV-tourer, 2019-2024) — owner-logged
    # timeslip on the Kawasaki Versys forum: 12.96s @ 99.15 mph (160 km/h).
    # 120hp I4 in a ~257 kg tall tourer. Forum/timeslip tier (0.3).
    # URL: https://www.kawasakiversys.com/threads/acceleration.497/
    (
        "Kawasaki",
        "Versys 1000",
        2019,
        12.96,
        160,
        "KawasakiVersysForum owner timeslip (12.96s @ 99.15 mph)",
    ),
    # Kawasaki Versys 1000 SE (1043cc I4 ADV-tourer, 2022-2024) — same Versys
    # 1000 platform / owner-timeslip figure (electronic suspension, same I4).
    (
        "Kawasaki",
        "Versys 1000 SE",
        2022,
        12.96,
        160,
        "Versys 1000 platform (1043 I4, owner timeslip)",
    ),
    # Suzuki RGV250 Gamma (249cc 2-stroke V-twin sport, 1991-1996) — DERIVED
    # (0.1). FastestLaps 0-60 mph 3.7s; 62hp 2T V-twin ~140 kg, sits in the
    # NSR250 (13.40) / RS250 (13.40) 2-stroke cluster — derived ~12.8s.
    # URL: https://fastestlaps.com/models/suzuki-rgv250
    (
        "Suzuki",
        "RGV250 Gamma",
        1992,
        12.80,
        160,
        "DERIVED (0-60mph 3.7s FastestLaps; 62hp 2T V-twin, NSR250/RS250 cluster)",
    ),
    # Kawasaki Ninja ZX-25R (Indonesia, 249.8cc I4 sport, 2020-2026) — DERIVED
    # (0.1). 51hp inline-four revving to 17,000 rpm, 0-100 km/h <6s, MotorBeam
    # top 187-190 km/h. Quicker than the CBR250RR (14.6s) twin — derived ~13.8s.
    # URL: https://www.motorbeam.com/kawasaki-zx-25r-top-speed-is-190-km-hr-achieved-on-race-track/
    (
        "Kawasaki",
        "Ninja ZX-25R",
        2020,
        13.80,
        160,
        "DERIVED (51hp 250 I4, 0-100<6s, top 187-190 km/h MotorBeam)",
    ),
    # Honda CB 300R (286cc single naked, 2019-2024) — DERIVED (0.1). rushlane
    # 0-100 km/h 6.2s; MotorBikeCatalog QM estimate ~15.1s. 30hp single.
    # URL: https://www.rushlane.com/honda-cb300r-0-100-kmph-time-12295222.html
    (
        "Honda",
        "CB 300R",
        2019,
        15.10,
        140,
        "DERIVED (rushlane 0-100 6.2s; MotorBikeCatalog QM ~15.1s)",
    ),
    # Honda CB300F (293.5cc single naked, 2022-2025) — DERIVED (0.1). Same
    # 293cc single family as CB300R; ~15.2s.
    ("Honda", "CB300F", 2022, 15.20, 138, "DERIVED (293cc CB300R platform, ~15.2s)"),
    # Triumph Daytona 660 (660cc triple sport, 2024-2025) — DERIVED (0.1).
    # 94hp faired triple; the same 660 triple in the Trident 660 (80hp) ran
    # 12.00s on MotoStatz, so the faired 94hp Daytona lands ~11.4s.
    # URL: https://www.triumphmotorcycles.com/motorcycles/sport/daytona-660/
    (
        "Triumph",
        "Daytona 660",
        2024,
        11.40,
        205,
        "DERIVED (660 triple 94hp faired; Trident 660 base 12.0s, MotoStatz)",
    ),
    # Bajaj Pulsar F250 (249cc single sport, 2021-2024) — DERIVED (0.1). The
    # faired sibling of the Pulsar N250 (15.45 in list); CarBlogIndia has it
    # ~0.9s quicker to 100 km/h, so ~15.0s.
    # URL: https://www.carblogindia.com/real-world-mileage-test-bajaj-pulsar-f250-n250/
    (
        "Bajaj",
        "Pulsar F250",
        2021,
        15.00,
        130,
        "DERIVED (faired N250 sibling, ~0.9s quicker than N250; CarBlogIndia)",
    ),
    # TVS Apache RTR 310 (312.2cc single naked, 2024-2025) — DERIVED (0.1).
    # Same 312cc engine as the Apache RR 310 (verified 15.46 @ 135 in list);
    # the naked RTR lands ~15.3s.
    # URL: https://www.autocarindia.com/bike-reviews/tvs-apache-rtr-310-road-test-review-432982
    (
        "TVS",
        "Apache RTR 310",
        2024,
        15.30,
        137,
        "DERIVED (RR 310 platform 312cc; RR 310 verified 15.46 @135 FastestLaps)",
    ),
    # Harley-Davidson V-Rod Muscle (1247cc Revolution V-twin muscle, 2009-2017)
    # — DERIVED (0.1). Same Revolution V-twin as the VRSCA V-Rod (11.6 timeslip
    # above); the Muscle is heavier (massive rear), so ~11.8s.
    (
        "Harley-Davidson",
        "V-Rod Muscle",
        2010,
        11.80,
        183,
        "DERIVED (1247cc Revolution V-Rod platform; heavier muscle body)",
    ),
    # Harley-Davidson Nightster (975cc Revolution Max V-twin cruiser, 2022-2026)
    # — DERIVED (0.1). 89hp 975T; the Sportster S (1250 RevMax) runs 11.10
    # (HDForums timeslip in list); the lighter-powered Nightster lands ~12.2s.
    (
        "Harley-Davidson",
        "Nightster",
        2022,
        12.20,
        175,
        "DERIVED (975 Revolution Max 89hp; Sportster S 11.10 base in list)",
    ),
    # Hero Xpulse 200 (199.6cc single ADV, 2019-2025) — DERIVED (0.1). Autocar
    # India 0-100 km/h 13.5s (4V) ×1.6 ~= 21.6s; 19hp ADV single, top ~123 km/h.
    # URL: https://www.autocarindia.com/bike-reviews/hero-xpulse-200-4v-review-test-ride-422843
    (
        "Hero",
        "Xpulse 200",
        2019,
        21.60,
        123,
        "DERIVED (0-100 13.5s x1.6 4V, Autocar India; top ~123 km/h)",
    ),
    # Hero XPulse 200T (199.6cc single ADV-touring, 2021-2026) — DERIVED (0.1).
    # Xpulse 200 touring variant, same 19hp single.
    (
        "Hero",
        "XPulse 200T",
        2021,
        21.60,
        120,
        "DERIVED (XPulse 200 platform, touring variant)",
    ),
    # ── 2026-06-13 benchmark-coverage agent (pass 4) ─────────────────────────
    # Final coverage pass (mostly the adventure/touring cluster, previously the
    # thinnest in this list). Same source bar / platform / DERIVED policy.
    #
    # Kawasaki Z400 (399cc parallel-twin naked, 2019-2026) — MotoStatz Dragy
    # instrumented: 13.34s @ 98 mph (158 km/h). The naked Ninja 400 (12.98 in
    # list is the faired Ninja); the Z400 is slightly slower on aero. Same
    # Dragy source bar.
    # URL: https://motostatz.com/kawasaki-z400-acceleration-top-speed/
    (
        "Kawasaki",
        "Z400",
        2019,
        13.34,
        158,
        "MotoStatz (Dragy, stock instrumented, 98 mph trap)",
    ),
    # Suzuki V-Strom 1050 (1037cc V-twin ADV, 2020-2026) — FastestLaps/
    # zeroto60 test: 11.56s @ 114.1 mph (184 km/h), 0-60 3.61s. 100hp V-twin.
    # Aggregator tier (0.5).
    # URL: https://fastestlaps.com/models/suzuki-v-strom-1050
    (
        "Suzuki",
        "V-Strom 1050",
        2020,
        11.56,
        184,
        "FastestLaps/zeroto60 (11.56s @ 114.1mph, 0-60 3.61s)",
    ),
    # Suzuki GSX-S1000GT (999cc I4 sport-tourer, 2022-2026) — DERIVED-platform.
    # The GSX-S1000 naked (10.60 @ 214 Sport Rider, in list) shares the 150hp
    # I4; the GT is the faired sport-tourer (similar weight) so ~10.6s.
    (
        "Suzuki",
        "GSX-S1000GT",
        2022,
        10.60,
        214,
        "GSX-S1000 platform 10.6s (Sport Rider); GT sport-tourer, 150hp I4",
    ),
    # KTM 790 Adventure (799cc parallel-twin ADV, 2019-2022) — DERIVED (0.1).
    # The 790 Duke ran 11.01s @ 124 mph on MotoStatz; the Adventure shares the
    # 799 twin but is heavier + far less aero (tall ADV), so ~12.0s.
    (
        "KTM",
        "790 Adventure",
        2019,
        12.00,
        185,
        "DERIVED (790 Duke 11.01 MotoStatz + ADV weight/aero ~+1s)",
    ),
    # BMW R 1300 GS (1300cc boxer ADV, 2024-2026) — DERIVED (0.1). ProfessCars
    # estimate ~11.0s; 145hp boxer in a ~237 kg ADV, top ~120 mph.
    # URL: https://www.motorbikecatalog.com/performance/2024/232820/bmw_r_1300_gs.html
    (
        "BMW",
        "R 1300 GS",
        2024,
        11.00,
        195,
        "DERIVED (ProfessCars est ~11.0s; 145hp boxer ADV, top ~120mph)",
    ),
    # BMW R 1250 GS (1254cc boxer ADV, 2019-2025) — DERIVED (0.1). 134hp boxer,
    # ProfessCars-class estimate; slightly slower than the 1300 GS. Top ~131mph
    # (Bennetts dyno-and-speed test). ~11.3s.
    (
        "BMW",
        "R 1250 GS",
        2019,
        11.30,
        190,
        "DERIVED (134hp boxer; ProfessCars-class, slightly slower than R1300GS)",
    ),
    # Triumph Tiger 900 Rally (888cc triple ADV, 2020-2026) — DERIVED (0.1).
    # 94hp triple, MCN 0-60 ~3.5-3.7s, top 202-205 km/h. The same 888 triple
    # tested faster than the F800GS + Africa Twin in development; ~11.7s.
    (
        "Triumph",
        "Tiger 900 Rally",
        2020,
        11.70,
        200,
        "DERIVED (888 triple 94hp; MCN 0-60 ~3.5-3.7s; top 202 km/h)",
    ),
    # Triumph Tiger 900 GT Pro (888cc triple ADV road-spec, 2024-2026) —
    # DERIVED (0.1). Same 888 triple as the Rally, road-biased (19" front,
    # slightly lighter); ~11.6s.
    (
        "Triumph",
        "Tiger 900 GT Pro",
        2024,
        11.60,
        202,
        "DERIVED (888 triple road-spec, Tiger 900 platform)",
    ),
    # Honda NC750X (745cc parallel-twin ADV-commuter, 2021-2026) — DERIVED
    # (0.1). MotorBikeCatalog QM ~13.5s; 58hp low-revving twin, top ~125 mph.
    # URL: https://www.motorbikecatalog.com/performance/2021/185120/honda_nc750x.html
    (
        "Honda",
        "NC750X",
        2021,
        13.50,
        201,
        "DERIVED (MotorBikeCatalog QM ~13.5s; 58hp 745 twin, top ~125mph)",
    ),
    # Yamaha Tracer 7 (689cc CP2 sport-tourer, 2020-2026) — DERIVED (0.1).
    # Same 689 CP2 as the MT-07 (12.13 MCN, in list); the Tracer adds touring
    # weight + bodywork, so ~12.4s.
    (
        "Yamaha",
        "Tracer 7",
        2020,
        12.40,
        195,
        "DERIVED (689 CP2; MT-07 12.13 base + touring weight)",
    ),
]

REFERENCE_BIKES: list[tuple[str, int, callable, float, float, str]] = [
    ("Suzuki GSX-R 1000 K5", 2005, gsxr1000_k5, 9.97, 238, "Cycle World 2005"),
    ("Yamaha YZF-R1 4C8", 2007, yzfr1_4c8, 10.30, 240, "Sport Rider 2007"),
    ("Suzuki Hayabusa Gen1", 1999, hayabusa_gen1, 10.40, 235, "Cycle World 1999"),
]


# Matcher primitives are shared with the other sweep drivers via
# scripts/sweep_lib.py; the _-prefixed aliases above keep the import
# surface used by tests/test_validation.py and topspeed_sweep.py stable.


def find_spec(mfr: str, model: str, year: int):
    """Locate the spec in ALL_KNOWN_BIKES best matching mfr/model/year
    (tightest-fit most-specific match -- see sweep_lib)."""
    return _find_spec_for_benchmark(mfr, model, year, ALL_KNOWN_BIKES)


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
