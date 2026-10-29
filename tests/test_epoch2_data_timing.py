"""2026-10 epoch, round 2 — per-source timing convention of the ET corpus.

A published ET is timed either from the drag-strip start beam (``rollout_1ft``:
the first foot of travel is not timed) or from first detected motion
(``first_motion``: the Racelogic default). ``scripts/sweep_lib`` classifies
every benchmark source and exposes the ``rollout_m`` each row must be simmed
with; these tests pin the classifier, the per-row corpus table (including the
rows whose convention could NOT be established and so carry the default), and
that the value actually reaches ``run()``.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motoquant.constants import ROLLOUT_M  # noqa: E402
from motoquant.engine_select import make_engine  # noqa: E402
from motoquant.scraper.importer import spec_to_bike_config  # noqa: E402
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES  # noqa: E402
from scripts import sweep_lib as SL  # noqa: E402
from scripts.validation_sweep import BENCHMARKS  # noqa: E402

RO, FM = SL.TIMING_ROLLOUT_1FT, SL.TIMING_FIRST_MOTION


def test_rollout_constant_matches_the_engine():
    assert SL.ROLLOUT_1FT_M == ROLLOUT_M == 0.3048
    assert SL.TIMING_ROLLOUT_M == {RO: ROLLOUT_M, FM: 0.0}
    assert SL.SIM_ET_KEY == {RO: "sim_et", FM: "sim_et_first_motion"}


@pytest.mark.parametrize(
    "src,conv,basis",
    [
        # explicit statements in the label win over every outlet rule
        ("Some GPS test (timed from first motion)", FM, "label"),
        ("Racelogic test, Indonesia (1-ft rollout enabled)", RO, "label"),
        ("VBox run, no rollout", FM, "label"),
        # derived / estimated rows: no timed run, default applies (the VBox
        # token inside a DERIVED label must not make it first_motion)
        ("DERIVED (0-100 ~9-10s x1.6 2V VBox, IndianAutosBlog)", RO, "derived"),
        ("Corner Speed 2026 prose estimate (low-12s)", RO, "derived"),
        # drag-strip beam timing
        ("Cycle World 2005 (timing-strip)", RO, "strip_beam"),
        ("HDForums timeslip 2021", RO, "strip_beam"),
        ("Australian Motorcycle News dragstrip test (magazine)", RO, "strip_beam"),
        # Racelogic device default in the Indonesian outlets
        (
            "Otomotif Racelogic instrumented 402m comparo (Indonesia)",
            FM,
            "device_default",
        ),
        (
            "Otomotifnet VBox/Racelogic (instrumented 0-402m 15.5s)",
            FM,
            "device_default",
        ),
        ("Indonesian VBox test 2017 (instrumented)", FM, "device_default"),
        # a Racelogic test with no Indonesian outlet is NOT assumed first motion
        ("Racelogic VBox test (US magazine)", RO, "undocumented"),
        # Dragy (incl. MotoStatz, which tests with Dragy)
        ("MotoStatz 2021 (Dragy, stock instrumented)", RO, "device_default_reported"),
        ("MotoStatz GPS test (instrumented)", RO, "device_default_reported"),
        (
            "Dragy GPS 2021 (Sport mode, stock instrumented)",
            RO,
            "device_default_reported",
        ),
        # North-American magazines
        ("Sport Rider 2009", RO, "na_magazine"),
        ("Motorcycle Consumer News 2012", RO, "na_magazine"),
        ("Cycle magazine 12/1985", RO, "na_magazine"),
        # nothing documented
        ("FastestLaps 2024", RO, "undocumented"),
        ("MCN 2015", RO, "undocumented"),
        ("", RO, "undocumented"),
    ],
)
def test_classifier(src, conv, basis):
    assert SL.timing_convention_meta(src) == (conv, basis)
    assert SL.timing_convention(src) == conv
    assert SL.rollout_m_for_source(src) == SL.TIMING_ROLLOUT_M[conv]


# ── corpus table ──────────────────────────────────────────────────────────

#: every corpus row scored from first motion (Racelogic devices, Indonesian
#: outlets, no documented rollout setting).
FIRST_MOTION_ROWS = {
    ("Bajaj", "Pulsar NS200", 2012),
    ("KTM", "Duke 250", 2017),
    ("TVS", "Apache RTR 200 4V", 2016),
    ("Yamaha", "MT-15", 2019),
    ("Honda", "CBR250RR", 2017),
    ("Yamaha", "YZF-R25", 2015),
    ("Yamaha", "MT-25", 2015),
    ("Kawasaki", "Ninja ZX-25R", 2020),
}

#: rows whose timing convention could NOT be established (aggregators,
#: second-hand citations, UK MCN tests with an undocumented device setting):
#: they carry the default rollout_1ft. Pinned so a change is deliberate.
UNDOCUMENTED_ROWS = {
    ("Kawasaki", "ZZR1400", 2006),
    ("Kawasaki", "Ninja H2", 2015),
    ("Royal Enfield", "Continental GT 650", 2019),
    ("Royal Enfield", "Continental GT 650", 2020),
    ("TVS", "Apache RR 310", 2020),
    ("Honda", "CBR 250R", 2011),
    ("Benelli", "302R", 2017),
    ("Benelli", "TNT 600i", 2014),
    ("Aprilia", "RS 457", 2024),
    ("Ducati", "Diavel V4", 2023),
    ("Suzuki", "V-Strom 1050", 2020),
    ("Kawasaki", "750 H2 Mach IV", 1972),
    ("KTM", "990 RC R", 2025),
    ("Honda", "NS400R", 1985),
    ("Kawasaki", "Versys 650", 2017),
    ("Kawasaki", "W800", 2020),
    ("BMW", "R1200GS", 2014),
    ("KTM", "690 Duke R", 2014),
    ("Husqvarna", "Vitpilen 701", 2019),
    ("Honda", "RC30 (VFR750R)", 1989),
    ("Yamaha", "SR400", 2015),
    ("Suzuki", "V-Strom 800DE", 2023),
    ("Suzuki", "SV650X", 2019),
    ("Indian", "Scout Bobber", 2025),
    ("Husqvarna", "701 Supermoto", 2018),
}


def _keyed(basis=None, conv=None):
    out = set()
    for b in BENCHMARKS:
        c, bs = SL.timing_convention_meta(b[5])
        if (basis is None or bs == basis) and (conv is None or c == conv):
            out.add((b[0], b[1], b[2]))
    return out


def test_first_motion_rows_are_exactly_the_indonesian_racelogic_tests():
    assert _keyed(conv=FM) == FIRST_MOTION_ROWS
    assert _keyed(basis="device_default") == FIRST_MOTION_ROWS


def test_undocumented_rows_are_pinned():
    assert _keyed(basis="undocumented") == UNDOCUMENTED_ROWS


def test_every_row_has_a_known_basis():
    bases = {SL.timing_convention_meta(b[5])[1] for b in BENCHMARKS}
    assert bases <= {
        "label",
        "strip_beam",
        "device_default",
        "device_default_reported",
        "na_magazine",
        "derived",
        "undocumented",
    }


def test_sim_et_for_convention_never_substitutes():
    rec = {"sim_et": 15.0}
    fm_src = "Otomotif Racelogic instrumented 402m comparo (Indonesia)"
    assert SL.sim_et_for_convention(rec, "Sport Rider 2009") == 15.0
    assert SL.sim_et_for_convention(rec, fm_src) is None
    rec["sim_et_first_motion"] = 15.3
    assert SL.sim_et_for_convention(rec, fm_src) == 15.3


# ── the convention reaches the engine ─────────────────────────────────────


def _spec(model):
    hits = [s for s in ALL_KNOWN_BIKES if s.model_name == model]
    assert len(hits) == 1, model
    return hits[0]


def test_first_motion_rollout_reaches_the_run():
    """The per-row ``rollout_m`` changes the timed ET through the production
    engine: from first motion the bike also times its first foot, so the ET
    is longer (and the finish is the same physical distance from the beam)."""
    spec = _spec("Ninja ZX-25R (Indonesia)")
    bm = SL.build_bench_map(BENCHMARKS)
    _, _, src = SL.bind_benchmark_for_record(
        spec.manufacturer, spec.model_name, spec.year_from, spec.year_to, bm
    )
    assert SL.timing_convention(src) == FM
    cfg = spec_to_bike_config(spec)
    et_fm = (
        make_engine(cfg)
        .run(max_time=26.0, rollout_m=SL.rollout_m_for_source(src))
        .time_quarter
    )
    et_ro = make_engine(cfg).run(max_time=26.0).time_quarter
    assert et_fm > et_ro + 0.1


def test_sweep_with_clusters_scores_first_motion_rows_on_their_own_run(
    tmp_path, monkeypatch
):
    """scripts/sweep_with_clusters.py runs a rollout_m=0.0 sim for a row
    bound to a first-motion benchmark and scores it on that run."""
    import json

    from scripts import sweep_with_clusters as swc

    specs = [_spec("Ninja ZX-25R (Indonesia)"), _spec("Ninja 400")]
    monkeypatch.setattr(swc, "ALL_KNOWN_BIKES", specs)
    out = tmp_path / "swc.json"
    assert swc.run_sweep(str(out)) == 0
    rows = {
        r["model"]: r
        for r in json.loads(out.read_text())["results"]
        if r.get("kind") == "catalog"
    }
    zx = rows["Ninja ZX-25R (Indonesia)"]
    assert zx["timing_convention"] == FM
    assert zx["sim_et_first_motion"] > zx["sim_et"]
    assert zx["delta_et"] == pytest.approx(zx["sim_et_first_motion"] - zx["bench_et"])
    n4 = rows["Ninja 400"]
    assert n4["timing_convention"] == RO
    assert "sim_et_first_motion" not in n4
    assert n4["delta_et"] == pytest.approx(n4["sim_et"] - n4["bench_et"])
