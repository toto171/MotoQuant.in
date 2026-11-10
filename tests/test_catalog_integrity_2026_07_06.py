"""Catalog-integrity regression pins (2026-07-06 audit).

Runs against the shipped ``motoquant.db`` through the PRODUCTION
compatibility path (PartsRepository.list_compatible_for_bike /
enrich_bike_row_for_fitment + is_compatible) and pins the fixes applied by
``scripts/patch_2026_07_06_catalog_integrity.py`` (and folded into the seed
sources):

  A. Belt/shaft/CVT bikes carry no chain pitch, so they match zero
     sprocket/chain parts (and the Aerox 155 CVT scooter matches zero
     quickshifters).
  B. Carbureted 2-strokes match none of the stroke-gated 4T EFI/electronic
     parts; the Zeeltronic YPVS controller only matches powervalve Yamahas.
  C. Model-named parts no longer leak across platforms (Streetfighter V4 vs
     Panigale exhausts, GSX-S1000 vs GSX-R parts, B-King vs Hayabusa
     slip-on, 390 Adventure vs Duke/RC 390 parts, generation-pinned
     flashes/lockups).
  E. No two parts share (brand, model_name) — the global dupe pin.

Fast: one read-only DB connection, no simulations.
"""

import json
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

from motoquant.database.parts_repo import (
    PartsRepository,
    enrich_bike_row_for_fitment,
)
from motoquant.parts.compatibility import is_compatible

# The shipped production catalog — explicitly NOT $MOTOQUANT_DB (test_api.py
# transiently repoints that at a tmp DB during the same pytest session).
_REPO_DB = Path(__file__).resolve().parent.parent / "motoquant.db"


@pytest.fixture(scope="module")
def conn():
    if not _REPO_DB.exists():
        pytest.skip(f"{_REPO_DB} not present")
    c = sqlite3.connect(f"file:{_REPO_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


@pytest.fixture(scope="module")
def repo(conn):
    return PartsRepository(conn)


def _part_id(conn, brand: str, name: str) -> int:
    """Resolve a part id by (brand, model_name), tolerating the brand-prefix
    normalisation difference between prod and fresh-seed DBs."""
    for candidate in (name, f"{brand} {name}"):
        row = conn.execute(
            "SELECT id FROM parts WHERE brand = ? AND model_name = ? ORDER BY id",
            (brand, candidate),
        ).fetchone()
        if row:
            return row["id"]
    raise AssertionError(f"part not found: {brand} / {name}")


def _bike_id(conn, mfr: str, name_frag: str) -> int:
    row = conn.execute(
        """SELECT bm.id FROM bike_models bm
           JOIN manufacturers m ON m.id = bm.manufacturer_id
           WHERE m.name = ? AND bm.model_name LIKE ? ORDER BY bm.id""",
        (mfr, f"%{name_frag}%"),
    ).fetchone()
    assert row, f"bike not found: {mfr} {name_frag}"
    return row["id"]


def _matches(repo, bike_id: int, part_id: int) -> bool:
    return any(p["id"] == part_id for p in repo.list_compatible_for_bike(bike_id))


# ────────────────────────────────────────────────────────────────────
# A. Belt / shaft / CVT final drives
# ────────────────────────────────────────────────────────────────────

# (manufacturer, model_name fragment) — the 15 class-A bikes
SHAFT_BELT_CVT = [
    ("Indian", "Scout (2015"),
    ("Indian", "Scout Bobber"),
    ("Indian", "101 Scout"),
    ("Indian", "Chief Dark Horse"),
    ("Indian", "Chieftain Dark Horse"),
    ("Indian", "Sport Chief"),
    ("Indian", "Challenger"),
    ("Indian", "Chief Bobber Dark Horse"),
    ("Triumph", "Rocket 3 R (2020"),
    ("Triumph", "Rocket 3 Storm R"),
    ("BMW", "R 1300 GS"),
    ("Yamaha", "FJR1300"),
    ("Triumph", "Tiger 1200 GT Pro"),
    ("Moto Guzzi", "V100 Mandello"),
    ("Yamaha", "Aerox 155"),
]


class TestShaftBeltChainParts:
    @pytest.mark.parametrize("mfr,frag", SHAFT_BELT_CVT)
    def test_no_sprocket_or_chain_parts(self, conn, repo, mfr, frag):
        bike = _bike_id(conn, mfr, frag)
        for category in ("sprocket", "chain"):
            hits = repo.list_compatible_for_bike(bike, category=category)
            assert not hits, (
                f"{mfr} {frag} (belt/shaft/CVT) matches {category} parts: "
                f"{[(p['id'], p['model_name']) for p in hits]}"
            )

    @pytest.mark.parametrize("mfr,frag", SHAFT_BELT_CVT)
    def test_chain_pitch_nulled_but_gearing_kept(self, conn, mfr, frag):
        """Physics-neutrality pin: only the pitch string was nulled — the
        final-drive ratio (and any real pulley counts) survive."""
        bike = _bike_id(conn, mfr, frag)
        row = conn.execute(
            "SELECT drivetrain_params FROM bike_configs "
            "WHERE bike_model_id = ? AND is_current = 1",
            (bike,),
        ).fetchone()
        dp = json.loads(row["drivetrain_params"])
        assert dp.get("chain_pitch") is None
        assert dp.get("final_drive_ratio"), "final_drive_ratio must survive"

    def test_aerox_cvt_matches_no_quickshifter(self, conn, repo):
        bike = _bike_id(conn, "Yamaha", "Aerox 155")
        hits = repo.list_compatible_for_bike(bike, category="quickshifter")
        assert not hits, (
            "CVT scooter matches quickshifters: "
            f"{[(p['id'], p['model_name']) for p in hits]}"
        )


# ────────────────────────────────────────────────────────────────────
# B. 4T EFI/electronic parts off carbureted 2-strokes
# ────────────────────────────────────────────────────────────────────

# The stroke-gated part set from the 2026-07-06 patch, as (brand, name).
STROKE_GATED_PARTS = [
    ("Dynojet", "Power Commander PCVI Stage 1 Universal"),
    ("Dynojet", "Power Commander PCVI Stage 2 Universal"),
    ("Bazzaz", "ZFi Fuel Controller Quickshift Unit"),
    ("Rapid Bike", "EVO Fuel Injection Controller"),
    ("HealTech", "iFlash Fuel Controller Autotune"),
    ("HM Quickshifter", "Super Lite Quickshifter"),
    ("Dynojet", "Power Commander Quickshifter Module"),
    ("Bosch", "High-Flow Fuel Pump"),
    ("HealTech", "iFlash Fuel Controller"),
    ("Bazzaz", "Quick Shift Fuel Control"),
    ("Rapid Bike", "EVO EFI Tuning Module"),
    ("Bazzaz", "ZFi Standalone Fuel Management"),
    ("HealTech", "QuickShifter Controller Module"),
    ("Dynojet", "Power Commander Auto-Tune Map"),
    ("AEM", "Infinity Fuel Management"),
    ("Dynojet", "Power Commander QS"),
    ("Dynojet", "Power Commander V Small-Displacement"),
    ("Bazzaz", "BKN Fuel Map Controller"),
    ("Dynojet", "Power Commander 6 (PC6)"),
    ("Rapid Bike", "Evo Piggyback"),
    ("Aracer", "RC Super-2 Piggyback"),
    ("Dynojet", "Power Commander V Entry Twins 300-500"),
    ("Walbro", "450 LPH Fuel Pump"),
    ("Race Dynamics", "PowerTRONIC V4 Piggyback (Indian 200-400cc FI)"),
    ("Healtech", "iQSE Quick Shifter Indian 200-400"),
    ("Aracer", "RC Mini X (SE Asia 150cc FI)"),
    ("Translogic", "Intellishift SE Asia 150cc"),
    ("K&N", "Replacement Air Filter Indian 150-400"),
]

TWO_STROKES = [
    ("Yamaha", "RX100"),
    ("Yamaha", "RX135"),
    ("Yamaha", "RXZ135"),
    ("Aprilia", "RS125"),
    ("Yamaha", "RD350"),
    ("Yamaha", "RD400"),
    ("Suzuki", "GT750"),
]


class TestStrokeGates:
    @pytest.mark.parametrize("mfr,frag", TWO_STROKES)
    def test_two_stroke_matches_no_stroke_gated_part(self, conn, repo, mfr, frag):
        bike = _bike_id(conn, mfr, frag)
        gated_ids = {_part_id(conn, b, n) for b, n in STROKE_GATED_PARTS}
        matched = {p["id"] for p in repo.list_compatible_for_bike(bike)}
        bad = matched & gated_ids
        assert not bad, f"{mfr} {frag} (2T) matches stroke-gated parts: {bad}"

    def test_nsr250r_does_not_match_cbr250rr_slipon(self, conn, repo):
        bike = _bike_id(conn, "Honda", "NSR250R")
        part = _part_id(conn, "Austin Racing", "GP1R Slip-On CBR250RR")
        assert not _matches(repo, bike, part)

    def test_ypvs_controller_only_matches_powervalve_yamahas(self, conn):
        """P444 must match exactly its named platforms (RD500LC / RZV500R /
        TZR250 — all YPVS) and neither air-cooled RD350/RD400."""
        part_id = _part_id(
            conn, "Zeeltronic", "PPV-YZR YPVS Controller RD500LC / TZR250"
        )
        part = dict(
            conn.execute(
                """SELECT p.*, pc.name AS category_name FROM parts p
                   JOIN parts_categories pc ON pc.id = p.category_id
                   WHERE p.id = ?""",
                (part_id,),
            ).fetchone()
        )
        matched = []
        for bike in conn.execute("SELECT * FROM bike_models"):
            row = dict(bike)
            enrich_bike_row_for_fitment(conn, row)
            if is_compatible(part, row)[0]:
                matched.append(row["model_name"])
        assert matched, "YPVS controller lost all fitments"
        for name in matched:
            assert any(tok in name for tok in ("RD500", "RZV500", "TZR250")), (
                f"YPVS controller leaked onto {name!r} (matched: {matched})"
            )

    def test_carb_pulsar_200_does_not_match_ns200_ecu_tune(self, conn, repo):
        bike = _bike_id(conn, "Bajaj", "Pulsar 200 (2007")
        part = _part_id(conn, "Race Dynamics", "RD Pulsar NS200 ECU Tune")
        assert not _matches(repo, bike, part)

    def test_ns200_and_rs200_keep_ecu_tune(self, conn, repo):
        part = _part_id(conn, "Race Dynamics", "RD Pulsar NS200 ECU Tune")
        assert _matches(repo, _bike_id(conn, "Bajaj", "Pulsar NS 200"), part)
        assert _matches(repo, _bike_id(conn, "Bajaj", "Pulsar RS 200"), part)


# ────────────────────────────────────────────────────────────────────
# C. Model-named cross-platform leaks
# ────────────────────────────────────────────────────────────────────


class TestModelNameLeaks:
    def test_streetfighter_v4_no_panigale_exhaust(self, conn, repo):
        bike = _bike_id(conn, "Ducati", "Streetfighter V4 (2020")
        part = _part_id(conn, "Yoshimura", "Panigale V4 R-77")
        assert not _matches(repo, bike, part)

    def test_streetfighter_v4_no_panigale_v4r_parts(self, conn, repo):
        bike = _bike_id(conn, "Ducati", "Streetfighter V4 (2020")
        for brand, name in [
            ("Arrow", "Full System Ducati Panigale V4R (1103cc)"),
            ("Power Commander", "V Ducati Panigale V4R (1103cc)"),
            ("Shorai", "LFX Lithium Battery Ducati Panigale V4R (1103cc)"),
        ]:
            part = _part_id(conn, brand, name)
            assert not _matches(repo, bike, part), f"leak: {brand} {name}"

    def test_gsxs1000_no_gsxr_exhaust(self, conn, repo):
        bike = _bike_id(conn, "Suzuki", "GSX-S1000 (2021")
        part = _part_id(conn, "Arrow", "GSX-R 1000 Pro-Race")
        assert not _matches(repo, bike, part)

    def test_gsxs1000gt_no_k5_flash_or_wheelie_bar(self, conn, repo):
        """The GT is now sport_touring, so sport-gated GSX-R parts drop out."""
        bike = _bike_id(conn, "Suzuki", "GSX-S1000GT")
        for brand, name in [
            ("Woolich Racing", "GSX-R 1000 K5 Stage 1 Flash"),
            ("Schnitz", "RS-3 Wheelie Bar (GSX-R 1000)"),
        ]:
            part = _part_id(conn, brand, name)
            assert not _matches(repo, bike, part), f"leak: {brand} {name}"

    def test_bking_no_hayabusa_slipon(self, conn, repo):
        bike = _bike_id(conn, "Suzuki", "B-King")
        part = _part_id(conn, "Akrapovic", "Evolution Slip-On Hayabusa")
        assert not _matches(repo, bike, part)

    def test_390_adventure_no_duke_rc390_parts(self, conn, repo):
        bike = _bike_id(conn, "KTM", "390 Adventure (2020")
        for brand, name in [
            ("Akrapovic", "Slip-On Line Duke 390 / RC 390"),
            ("Carbonin", "Carbon Fiber Race Fairing KTM RC 390"),
            ("Race Dynamics", "RD Duke 390 ECU Tune"),
        ]:
            part = _part_id(conn, brand, name)
            assert not _matches(repo, bike, part), f"leak: {brand} {name}"

    def test_fz1_and_fzr1000_no_r1_named_parts(self, conn, repo):
        for mfr, frag in [("Yamaha", "FZ1 Fazer"), ("Yamaha", "FZR1000")]:
            bike = _bike_id(conn, mfr, frag)
            for brand, name in [
                ("Yoshimura", "YZF-R1 R-77 Full System"),
                ("Woolich Racing", "YZF-R1 4C8 Stage 1 Flash"),
                ("DNA", "Air Filter Yamaha YZF-R1 (998cc)"),
            ]:
                part = _part_id(conn, brand, name)
                assert not _matches(repo, bike, part), f"{frag} leak: {brand} {name}"

    def test_tuono_v4_no_rsv4_exhaust(self, conn, repo):
        bike = _bike_id(conn, "Aprilia", "Tuono V4 1100")
        part = _part_id(conn, "Akrapovic", "RSV4 Racing Full")
        assert not _matches(repo, bike, part)

    def test_rtr310_no_rr310_parts(self, conn, repo):
        bike = _bike_id(conn, "TVS", "Apache RTR 310")
        for brand, name in [
            ("TFC", "Full System TVS Apache RR 310"),
            ("BMC", "Air Filter TVS Apache RR 310 (312cc)"),
        ]:
            part = _part_id(conn, brand, name)
            assert not _matches(repo, bike, part), f"leak: {brand} {name}"

    def test_yss_adv_shock_pinned_to_re_hero(self, conn, repo):
        part = _part_id(conn, "YSS", "G-Series Rear Shock Himalayan/Scram/Xpulse")
        # named platforms keep it
        assert _matches(repo, _bike_id(conn, "Royal Enfield", "Himalayan 411"), part)
        # foreign ADVs (incl. 2-strokes) lose it
        for mfr, frag in [("BMW", "G310GS"), ("KTM", "300 EXC")]:
            assert not _matches(repo, _bike_id(conn, mfr, frag), part), (
                f"YSS shock leak: {mfr} {frag}"
            )


class TestGenerationPins:
    def test_k5_flash_only_matches_k5_reference(self, conn, repo):
        part = _part_id(conn, "Woolich Racing", "GSX-R 1000 K5 Stage 1 Flash")
        assert _matches(repo, 1, part), "K5 flash must keep the K5 reference bike"
        for frag in ("GSX-R 1000 (2001", "GSX-R 1000 (2007", "GSX-R 1000 (2017"):
            bike = _bike_id(conn, "Suzuki", frag)
            assert not _matches(repo, bike, part), f"K5 flash leaked to {frag}"

    def test_4c8_flash_only_matches_4c8_reference(self, conn, repo):
        part = _part_id(conn, "Woolich Racing", "YZF-R1 4C8 Stage 1 Flash")
        assert _matches(repo, 2, part), "4C8 flash must keep the 4C8 reference bike"

    def test_hayabusa_25th_anniversary_no_gen12_lockup(self, conn, repo):
        part = _part_id(
            conn, "MTC Engineering", "Multistage Lock-Up Clutch — Hayabusa (99-21)"
        )
        bike = _bike_id(conn, "Suzuki", "Hayabusa 25th Anniversary")
        assert not _matches(repo, bike, part)
        # Gen1 (reference bike 3) + Gen2 keep it; Gen3 (2021+, new clutch) not
        assert _matches(repo, 3, part)
        assert _matches(repo, _bike_id(conn, "Suzuki", "Hayabusa (2008"), part)
        assert not _matches(repo, _bike_id(conn, "Suzuki", "Hayabusa (2021"), part)

    def test_gen2_swingarm_only_gen2(self, conn, repo):
        part = _part_id(
            conn, "Schnitz Racing", '10" Extended Swingarm — Hayabusa Gen 2'
        )
        assert _matches(repo, _bike_id(conn, "Suzuki", "Hayabusa (2008"), part)
        assert not _matches(repo, 3, part)  # Gen1 reference
        assert not _matches(repo, _bike_id(conn, "Suzuki", "B-King"), part)
        assert not _matches(repo, _bike_id(conn, "Suzuki", "Hayabusa (2021"), part)


# ────────────────────────────────────────────────────────────────────
# E. Duplicates
# ────────────────────────────────────────────────────────────────────


class TestNoDuplicateParts:
    def test_no_two_parts_share_brand_and_name(self, conn):
        c = Counter(
            (r["brand"], r["model_name"])
            for r in conn.execute("SELECT brand, model_name FROM parts")
        )
        dups = {k: v for k, v in c.items() if v > 1}
        assert not dups, f"duplicate (brand, model_name) parts: {dups}"

    def test_clutchco_kits_banded_not_stacked(self, conn, repo):
        """The 8 banded clutch-kit SKUs must never ALL match one bike — bands
        cap the per-bike overlap at 2 (plus the boundary case).

        July 13, 2026: the fictional 'ClutchCo' brand was renamed to honest
        class names under 'Generic' (scrape honesty triage); the rows keep
        their stable CC-* part numbers, so the banding invariant is tracked
        through those."""
        clutchco_ids = {
            r["id"]
            for r in conn.execute(
                "SELECT p.id FROM parts p JOIN parts_categories c"
                " ON p.category_id = c.id"
                " WHERE p.part_number LIKE 'CC-%' AND c.name = 'clutch_kit'"
            )
        }
        assert len(clutchco_ids) == 8
        for bike_id in (1, 3):  # K5 999cc, Hayabusa 1299cc
            matched = {
                p["id"] for p in repo.list_compatible_for_bike(bike_id)
            } & clutchco_ids
            assert len(matched) <= 2, (
                f"bike {bike_id} matches {len(matched)} banded clutch kits: {matched}"
            )


# ────────────────────────────────────────────────────────────────────
# F. Bike data fixes
# ────────────────────────────────────────────────────────────────────


class TestBikeDataFixes:
    def test_ktm_1390_is_v2(self, conn):
        row = conn.execute(
            "SELECT cylinder_config FROM bike_models WHERE id = 341"
        ).fetchone()
        if row is None:
            pytest.skip("bike 341 not in this DB")
        assert row["cylinder_config"] == "V2"

    def test_gsxs1000gt_is_sport_touring(self, conn):
        bike = _bike_id(conn, "Suzuki", "GSX-S1000GT")
        row = conn.execute(
            "SELECT category FROM bike_models WHERE id = ?", (bike,)
        ).fetchone()
        assert row["category"] == "sport_touring"

    def test_rtr310_is_naked(self, conn):
        bike = _bike_id(conn, "TVS", "Apache RTR 310")
        row = conn.execute(
            "SELECT category FROM bike_models WHERE id = ?", (bike,)
        ).fetchone()
        assert row["category"] == "naked"

    def test_rd500lc_rzv500r_are_v4(self, conn):
        for frag in ("RD500LC", "RZV500R"):
            bike = _bike_id(conn, "Yamaha", frag)
            row = conn.execute(
                "SELECT cylinder_config FROM bike_models WHERE id = ?", (bike,)
            ).fetchone()
            assert row["cylinder_config"] == "V4", f"{frag} must be V4 (2T V4)"
