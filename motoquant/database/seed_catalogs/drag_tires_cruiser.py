"""
MotoQuant — Drag Rubber + Cruiser Tire Pack (July 2026)
=======================================================
Two tire families following the seed_recommended_fitments auto-create
pattern (_ensure_tire_exists + honest Pacejka templates), plus
DB-QUERY-DRIVEN fitment seeding — fitments are derived from each bike's
category / displacement / OEM rim+width at seed time, NOT from hardcoded
model-name lists, so bikes added later pick them up on the next seed.

DRAG PACK (11 tires — all real, live-listed July 2026):
  Shinko Hook-Up Drag Radial   180/55ZR17, 190/50ZR17, 200/50ZR17 ($137 verified)
  Shinko Hook-Up Pro           200/50ZR17 (competition carcass)
  Shinko 003 Stealth Ultra-Soft 180/55ZR17, 190/50ZR17, 200/50ZR17 ($125-130 verified)
  Shinko Advance R005          240/40R18 (fat-tire kit radial)
  Mickey Thompson ET Drag Moto 26.0/7.0-17 slick (M/T moto line current)
  M&H Racemaster moto slick    7.5/23.0-15 rear ($341 verified)
  M&H Racemaster DOT FrontRunner 4.5/27-16 front ($233 verified)

CRUISER PACK (8 tires — all real):
  Pirelli Night Dragon    130/60B19 F, 180/65B16 R
  Dunlop D408F / D407     130/60B19 F, 180/65B16 R (Harley OEM line)
  Metzeler Cruisetec      130/60B19 F, 180/65B16 R, 200/55R17 R, 160/70B17 R

  (Night Dragon 240/40R18 and Cruisetec 240/40VR18 exist in the real
  catalogs but NO bike in the DB carries an OEM 240/18 fitment, so they
  are deliberately not seeded — orphan rows help nobody.)

FITMENT RULES (query-driven, applied by plan_tire_fitments):
  R1 sport/naked/muscle >=550cc with 17in OEM rear rim -> drag_prep rows
     for the closest-width Hook-Up + closest-width Stealth Ultra-Soft.
  R2 cruiser/touring/muscle >=1100cc with 17in OEM rear rim -> drag_prep
     row for the closest-width Hook-Up (strip-day rubber for Diavel-class).
  R3 sport/naked/muscle/cruiser >=1300cc with 18in OEM rear rim ->
     drag_prep row for the Advance R005 240 (fat-tire/extended-swingarm kit).
  R4 sport/naked/muscle >=1000cc with 17in OEM rear rim -> drag_prep row
     for the M/T ET Drag slick (competition, strip only).
  R4b sport/naked/muscle >=1200cc with 17in OEM rear rim -> drag_prep row
     for the Hook-Up Pro (the competition carcass the class actually runs).
  R5 sport/naked/muscle I4 >=1280cc (Hayabusa/ZX-14/VMAX pro-street
     class; I4-only so single-sided-swingarm V-twins are excluded) ->
     drag_prep rows for the M&H rear slick + DOT front runner (both need
     drag wheel conversions — noted on the fitment).
  R6 cruiser/touring/muscle (any cc): 'recommended' rows for cruiser-pack
     tires whose rim matches the bike's OEM rim per position and whose
     width is within 25 mm of OEM; capped at 3 per bike/position.

Pacejka numbers are honest template estimates (confidence 0.55-0.62)
anchored to the existing _TIRE_TEMPLATES ranges in
seed_recommended_fitments.py. Prices: landed INR via the documented
import formula (usd * 84 * 1.30 * 1.18 + 1500), +/-15%.
"""

import logging

logger = logging.getLogger(__name__)

# key -> tire spec. "usd" retained in specs for auditability.
DRAG_TIRES = [
    {
        "key": "hookup_180",
        "mfr": "Shinko",
        "model": "Hook-Up Drag Radial",
        "position": "rear",
        "size": "180/55ZR17",
        "width": 180,
        "aspect": 55,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.0,
        "C": 1.70,
        "mu_peak": 1.78,
        "mu_slide": 1.40,
        "E": -0.40,
        "opt_temp": 75,
        "rec_psi": 30.0,
        "drag_psi": 17.0,
        "mass": 5.8,
        "tread_mass": 2.6,
        "usd": 137,
        "price_inr": 19200,
        "conf": 0.60,
    },
    {
        "key": "hookup_190",
        "mfr": "Shinko",
        "model": "Hook-Up Drag Radial",
        "position": "rear",
        "size": "190/50ZR17",
        "width": 190,
        "aspect": 50,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.0,
        "C": 1.70,
        "mu_peak": 1.78,
        "mu_slide": 1.40,
        "E": -0.40,
        "opt_temp": 75,
        "rec_psi": 30.0,
        "drag_psi": 17.0,
        "mass": 6.0,
        "tread_mass": 2.7,
        "usd": 137,
        "price_inr": 19200,
        "conf": 0.60,
    },
    {
        "key": "hookup_200",
        "mfr": "Shinko",
        "model": "Hook-Up Drag Radial",
        "position": "rear",
        "size": "200/50ZR17",
        "width": 200,
        "aspect": 50,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.0,
        "C": 1.70,
        "mu_peak": 1.78,
        "mu_slide": 1.40,
        "E": -0.40,
        "opt_temp": 75,
        "rec_psi": 30.0,
        "drag_psi": 17.0,
        "mass": 6.3,
        "tread_mass": 2.9,
        "usd": 145,
        "price_inr": 20200,
        "conf": 0.60,
    },
    {
        "key": "hookup_pro_200",
        "mfr": "Shinko",
        "model": "Hook-Up Pro Drag Radial",
        "position": "rear",
        "size": "200/50ZR17",
        "width": 200,
        "aspect": 50,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.2,
        "C": 1.72,
        "mu_peak": 1.85,
        "mu_slide": 1.45,
        "E": -0.40,
        "opt_temp": 80,
        "rec_psi": 28.0,
        "drag_psi": 16.0,
        "mass": 5.9,  # lighter aramid-belted competition carcass
        "tread_mass": 2.8,
        "usd": 180,
        "price_inr": 24700,
        "conf": 0.55,
        "price_estimated": True,
    },
    {
        "key": "stealth_180",
        "mfr": "Shinko",
        "model": "003 Stealth Ultra-Soft",
        "position": "rear",
        "size": "180/55ZR17",
        "width": 180,
        "aspect": 55,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.2,
        "C": 1.65,
        "mu_peak": 1.68,
        "mu_slide": 1.30,
        "E": -0.38,
        "opt_temp": 68,
        "rec_psi": 32.0,
        "drag_psi": 20.0,
        "mass": 6.0,
        "tread_mass": 2.6,
        "usd": 125,
        "price_inr": 17600,
        "conf": 0.60,
    },
    {
        "key": "stealth_190",
        "mfr": "Shinko",
        "model": "003 Stealth Ultra-Soft",
        "position": "rear",
        "size": "190/50ZR17",
        "width": 190,
        "aspect": 50,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.2,
        "C": 1.65,
        "mu_peak": 1.68,
        "mu_slide": 1.30,
        "E": -0.38,
        "opt_temp": 68,
        "rec_psi": 32.0,
        "drag_psi": 20.0,
        "mass": 6.2,
        "tread_mass": 2.7,
        "usd": 130,
        "price_inr": 18300,
        "conf": 0.60,
    },
    {
        "key": "stealth_200",
        "mfr": "Shinko",
        "model": "003 Stealth Ultra-Soft",
        "position": "rear",
        "size": "200/50ZR17",
        "width": 200,
        "aspect": 50,
        "rim": 17,
        "compound": "drag_dot",
        "B": 11.2,
        "C": 1.65,
        "mu_peak": 1.68,
        "mu_slide": 1.30,
        "E": -0.38,
        "opt_temp": 68,
        "rec_psi": 32.0,
        "drag_psi": 20.0,
        "mass": 6.5,
        "tread_mass": 2.9,
        "usd": 135,
        "price_inr": 18900,
        "conf": 0.60,
    },
    {
        "key": "r005_240",
        "mfr": "Shinko",
        "model": "Advance R005",
        "position": "rear",
        "size": "240/40R18",
        "width": 240,
        "aspect": 40,
        "rim": 18,
        "compound": "drag_dot",
        "B": 10.5,
        "C": 1.60,
        "mu_peak": 1.50,
        "mu_slide": 1.15,
        "E": -0.35,
        "opt_temp": 60,
        "rec_psi": 32.0,
        "drag_psi": 22.0,
        "mass": 8.5,
        "tread_mass": 3.6,
        "usd": 190,
        "price_inr": 26000,
        "conf": 0.55,
        "price_estimated": True,
    },
    {
        "key": "mt_slick_17",
        "mfr": "Mickey Thompson",
        "model": "ET Drag Motorcycle Slick",
        "position": "rear",
        "size": "26.0/7.0-17",
        "width": 178,
        "aspect": 64,
        "rim": 17,
        "compound": "drag_slick",
        "B": 10.5,
        "C": 1.75,
        "mu_peak": 1.92,
        "mu_slide": 1.55,
        "E": -0.42,
        "opt_temp": 85,
        "rec_psi": 14.0,
        "drag_psi": 12.0,
        "mass": 5.5,
        "tread_mass": 2.8,
        "rolling_radius": 0.330,  # 26.0 in overall diameter
        "usd": 310,
        "price_inr": 41400,
        "conf": 0.55,
        "price_estimated": True,
    },
    {
        "key": "mh_slick_15",
        "mfr": "M&H",
        "model": "Racemaster Motorcycle Drag Slick",
        "position": "rear",
        "size": "7.5/23.0-15",
        "width": 190,
        "aspect": 53,
        "rim": 15,
        "compound": "drag_slick",
        "B": 10.5,
        "C": 1.75,
        "mu_peak": 1.90,
        "mu_slide": 1.52,
        "E": -0.42,
        "opt_temp": 85,
        "rec_psi": 13.0,
        "drag_psi": 11.0,
        "mass": 5.8,
        "tread_mass": 2.9,
        "rolling_radius": 0.292,  # 23.0 in overall diameter
        "usd": 341,
        "price_inr": 45400,
        "conf": 0.60,
    },
    {
        "key": "mh_frontrunner_16",
        "mfr": "M&H",
        "model": "Racemaster DOT Front Runner",
        "position": "front",
        "size": "4.5/27-16",
        "width": 114,
        "aspect": 120,
        "rim": 16,
        "compound": "drag_dot",
        "B": 10.0,
        "C": 1.55,
        "mu_peak": 1.35,
        "mu_slide": 1.05,
        "E": -0.32,
        "opt_temp": 55,
        "rec_psi": 30.0,
        "drag_psi": 28.0,
        "mass": 3.4,
        "tread_mass": 1.5,
        "rolling_radius": 0.343,  # 27 in overall diameter
        "crr_base": 0.009,  # tall narrow low-drag front runner
        "usd": 233,
        "price_inr": 31500,
        "conf": 0.60,
    },
]

CRUISER_TIRES = [
    {
        "key": "nightdragon_f19",
        "mfr": "Pirelli",
        "model": "Night Dragon",
        "position": "front",
        "size": "130/60B19",
        "width": 130,
        "aspect": 60,
        "rim": 19,
        "compound": "cruiser",
        "B": 10.0,
        "C": 1.55,
        "mu_peak": 1.25,
        "mu_slide": 0.98,
        "E": -0.30,
        "opt_temp": 50,
        "rec_psi": 36.0,
        "drag_psi": 30.0,
        "mass": 5.0,
        "tread_mass": 2.2,
        "usd": 180,
        "price_inr": 24700,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "nightdragon_r16",
        "mfr": "Pirelli",
        "model": "Night Dragon",
        "position": "rear",
        "size": "180/65B16",
        "width": 180,
        "aspect": 65,
        "rim": 16,
        "compound": "cruiser",
        "B": 10.0,
        "C": 1.55,
        "mu_peak": 1.25,
        "mu_slide": 0.98,
        "E": -0.30,
        "opt_temp": 50,
        "rec_psi": 40.0,
        "drag_psi": 32.0,
        "mass": 8.2,
        "tread_mass": 3.4,
        "usd": 220,
        "price_inr": 29800,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "d408f_19",
        "mfr": "Dunlop",
        "model": "D408F Harley-Davidson",
        "position": "front",
        "size": "130/60B19",
        "width": 130,
        "aspect": 60,
        "rim": 19,
        "compound": "cruiser",
        "B": 9.8,
        "C": 1.55,
        "mu_peak": 1.18,
        "mu_slide": 0.92,
        "E": -0.30,
        "opt_temp": 48,
        "rec_psi": 36.0,
        "drag_psi": 32.0,
        "mass": 5.2,
        "tread_mass": 2.3,
        "usd": 190,
        "price_inr": 26000,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "d407_r16",
        "mfr": "Dunlop",
        "model": "D407 Harley-Davidson",
        "position": "rear",
        "size": "180/65B16",
        "width": 180,
        "aspect": 65,
        "rim": 16,
        "compound": "cruiser",
        "B": 9.8,
        "C": 1.55,
        "mu_peak": 1.18,
        "mu_slide": 0.92,
        "E": -0.30,
        "opt_temp": 48,
        "rec_psi": 40.0,
        "drag_psi": 34.0,
        "mass": 8.5,
        "tread_mass": 3.5,
        "usd": 210,
        "price_inr": 28600,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "cruisetec_f19",
        "mfr": "Metzeler",
        "model": "Cruisetec",
        "position": "front",
        "size": "130/60B19",
        "width": 130,
        "aspect": 60,
        "rim": 19,
        "compound": "cruiser",
        "B": 10.2,
        "C": 1.56,
        "mu_peak": 1.28,
        "mu_slide": 1.00,
        "E": -0.30,
        "opt_temp": 52,
        "rec_psi": 36.0,
        "drag_psi": 30.0,
        "mass": 5.0,
        "tread_mass": 2.2,
        "usd": 200,
        "price_inr": 27300,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "cruisetec_r16",
        "mfr": "Metzeler",
        "model": "Cruisetec",
        "position": "rear",
        "size": "180/65B16",
        "width": 180,
        "aspect": 65,
        "rim": 16,
        "compound": "cruiser",
        "B": 10.2,
        "C": 1.56,
        "mu_peak": 1.28,
        "mu_slide": 1.00,
        "E": -0.30,
        "opt_temp": 52,
        "rec_psi": 40.0,
        "drag_psi": 32.0,
        "mass": 8.3,
        "tread_mass": 3.4,
        "usd": 230,
        "price_inr": 31100,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "cruisetec_r17_200",
        "mfr": "Metzeler",
        "model": "Cruisetec",
        "position": "rear",
        "size": "200/55R17",
        "width": 200,
        "aspect": 55,
        "rim": 17,
        "compound": "cruiser",
        "B": 10.2,
        "C": 1.56,
        "mu_peak": 1.28,
        "mu_slide": 1.00,
        "E": -0.30,
        "opt_temp": 52,
        "rec_psi": 38.0,
        "drag_psi": 30.0,
        "mass": 7.8,
        "tread_mass": 3.2,
        "usd": 240,
        "price_inr": 32400,
        "conf": 0.58,
        "price_estimated": True,
    },
    {
        "key": "cruisetec_r17_160",
        "mfr": "Metzeler",
        "model": "Cruisetec",
        "position": "rear",
        "size": "160/70B17",
        "width": 160,
        "aspect": 70,
        "rim": 17,
        "compound": "cruiser",
        "B": 10.2,
        "C": 1.56,
        "mu_peak": 1.28,
        "mu_slide": 1.00,
        "E": -0.30,
        "opt_temp": 52,
        "rec_psi": 38.0,
        "drag_psi": 30.0,
        "mass": 7.2,
        "tread_mass": 3.0,
        "usd": 210,
        "price_inr": 28600,
        "conf": 0.58,
        "price_estimated": True,
    },
]

_ALL_TIRES = DRAG_TIRES + CRUISER_TIRES

# Hook-Up family + Stealth family keys used by the width-closest picker.
_HOOKUP_KEYS = ["hookup_180", "hookup_190", "hookup_200"]
_STEALTH_KEYS = ["stealth_180", "stealth_190", "stealth_200"]


def _tire_by_key(key: str) -> dict:
    for t in _ALL_TIRES:
        if t["key"] == key:
            return t
    raise KeyError(key)


def _ensure_tire(db, spec: dict) -> tuple[int, bool]:
    """Return (tire_model_id, created). Idempotent on
    (manufacturer, model_name, position, NORMALIZED size).

    July 6, 2026: the size comparison goes through
    TireRepository.normalize_size_designation so notation variants of the
    same physical size ('150/80B16' vs '150/80R16') match the existing row
    instead of minting a duplicate — the source of the duplicate-title rows
    merged by scripts/patch_2026_07_06_tire_dedup.py.
    """
    from ..tire_repo import TireRepository

    norm = TireRepository.normalize_size_designation
    for cand in db._conn.execute(
        "SELECT t.id, t.size_designation FROM tire_models t "
        "JOIN tire_manufacturers tm ON t.manufacturer_id = tm.id "
        "WHERE LOWER(tm.name) = LOWER(?) AND LOWER(t.model_name) = LOWER(?) "
        "AND t.position = ?",
        (spec["mfr"], spec["model"], spec["position"]),
    ).fetchall():
        if norm(cand[1]) == norm(spec["size"]):
            return cand[0], False
    row = db._conn.execute(
        "SELECT id FROM tire_manufacturers WHERE LOWER(name) = LOWER(?)",
        (spec["mfr"],),
    ).fetchone()
    if row:
        mfr_id = row[0]
    else:
        mfr_id = db._conn.execute(
            "INSERT INTO tire_manufacturers (name) VALUES (?)", (spec["mfr"],)
        ).lastrowid
    rolling_radius = spec.get("rolling_radius") or round(
        (spec["rim"] * 25.4 / 2 + spec["width"] * spec["aspect"] / 100) / 1000.0, 4
    )
    inertia = 0.42 if spec["position"] == "front" else 0.55
    if spec["width"] >= 220:
        inertia = 0.62
    source_note = "seed:drag_tires_cruiser Jul 2026" + (
        " (price estimated)" if spec.get("price_estimated") else " (verified listing)"
    )
    tire_id = db._conn.execute(
        "INSERT INTO tire_models "
        "(manufacturer_id, model_name, compound_type, position, width_mm, "
        " aspect_ratio, rim_diameter_inch, size_designation, "
        " pacejka_B, pacejka_C, pacejka_D, pacejka_E, mu_peak, mu_slide, "
        " load_sensitivity_k, optimal_temp_c, reversion_temp_c, "
        " thermal_conductivity, tread_mass_kg, specific_heat, rolling_radius_m, "
        " inertia_kgm2, growth_coeff, mass_kg, crr_base, crr_speed_coeff, "
        " crr_temp_coeff, recommended_psi, drag_pressure_psi, construction, "
        " data_source, confidence, price_inr, price_usd, available_india) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            mfr_id,
            spec["model"],
            spec["compound"],
            spec["position"],
            spec["width"],
            spec["aspect"],
            spec["rim"],
            spec["size"],
            spec["B"],
            spec["C"],
            spec["mu_peak"],  # pacejka_D = peak coefficient
            spec["E"],
            spec["mu_peak"],
            spec["mu_slide"],
            0.0,
            spec["opt_temp"],
            105.0,
            0.20,
            spec["tread_mass"],
            1700.0,
            rolling_radius,
            inertia,
            2e-09,
            spec["mass"],
            spec.get("crr_base", 0.013),
            2.5e-05,
            -0.0002,
            spec["rec_psi"],
            spec["drag_psi"],
            "bias" if spec["compound"] == "drag_slick" else "radial",
            source_note,
            spec["conf"],
            spec["price_inr"],
            spec["usd"],
            0,  # import-only; no Indian distributor stocks these yet
        ),
    ).lastrowid
    return tire_id, True


def _oem_rims(db, position: str) -> dict[int, tuple[int, int]]:
    """bike_id -> (rim_inch, widest OEM width_mm) for the given position."""
    rows = db._conn.execute(
        "SELECT f.bike_model_id, t.rim_diameter_inch, t.width_mm "
        "FROM bike_tire_fitments f JOIN tire_models t ON t.id = f.tire_model_id "
        "WHERE f.position = ? AND f.fitment_type = 'oem' "
        "AND t.rim_diameter_inch IS NOT NULL AND t.width_mm IS NOT NULL",
        (position,),
    ).fetchall()
    out: dict[int, tuple[int, int]] = {}
    for bike_id, rim, width in rows:
        cur = out.get(bike_id)
        if cur is None or width > cur[1]:
            out[bike_id] = (int(rim), int(width))
    return out


def _bikes(db) -> list[dict]:
    rows = db._conn.execute(
        "SELECT b.id, b.model_name, b.category, b.displacement_cc, m.name, "
        "b.cylinder_config "
        "FROM bike_models b JOIN manufacturers m ON b.manufacturer_id = m.id"
    ).fetchall()
    return [
        {
            "id": r[0],
            "model": r[1],
            "category": r[2] or "",
            "cc": r[3] or 0.0,
            "mfr": r[4],
            "cyl": r[5] or "",
        }
        for r in rows
    ]


def _closest_width(keys: list[str], oem_width: int, max_diff: int = 30) -> str | None:
    best_key, best_diff = None, None
    for key in keys:
        diff = abs(_tire_by_key(key)["width"] - oem_width)
        if best_diff is None or diff < best_diff:
            best_key, best_diff = key, diff
    if best_diff is not None and best_diff <= max_diff:
        return best_key
    return None


def plan_tire_fitments(db) -> list[dict]:
    """READ-ONLY planner: derive the fitment rows this module would insert.

    Returns dicts: {bike_id, tire_key, position, fitment_type, notes}.
    Pure SELECTs — safe to run as a dry-run against a read-only DB.
    """
    plans: list[dict] = []
    rear_rims = _oem_rims(db, "rear")
    front_rims = _oem_rims(db, "front")
    sportish = {"sport", "naked", "muscle"}
    cruiserish = {"cruiser", "touring", "muscle"}

    for bike in _bikes(db):
        bid, cat, cc = bike["id"], bike["category"], bike["cc"]
        rim_width = rear_rims.get(bid)

        # R1: 17in drag radials for sport/naked/muscle >= 550cc
        if cat in sportish and cc >= 550 and rim_width and rim_width[0] == 17:
            for family, label in (
                (_HOOKUP_KEYS, "Shinko Hook-Up DOT drag radial"),
                (_STEALTH_KEYS, "Shinko 003 Stealth Ultra-Soft"),
            ):
                key = _closest_width(family, rim_width[1])
                if key:
                    plans.append(
                        {
                            "bike_id": bid,
                            "tire_key": key,
                            "position": "rear",
                            "fitment_type": "drag_prep",
                            "notes": f"{label}, width-matched to OEM",
                        }
                    )

        # R2: 17in-rim big cruisers get the Hook-Up as strip-day rubber
        if cat in {"cruiser", "touring"} and cc >= 1100 and rim_width:
            if rim_width[0] == 17:
                key = _closest_width(_HOOKUP_KEYS, rim_width[1])
                if key:
                    plans.append(
                        {
                            "bike_id": bid,
                            "tire_key": key,
                            "position": "rear",
                            "fitment_type": "drag_prep",
                            "notes": "DOT drag radial — strip use on big V-twins",
                        }
                    )

        # R3: 18in-rim >=1300cc muscle class -> 240 fat-tire radial
        if (
            cat in (sportish | {"cruiser"})
            and cc >= 1300
            and rim_width
            and rim_width[0] == 18
        ):
            plans.append(
                {
                    "bike_id": bid,
                    "tire_key": "r005_240",
                    "position": "rear",
                    "fitment_type": "drag_prep",
                    "notes": "240 kit tire — requires fat-tire/extended swingarm kit",
                }
            )

        # R4: competition slick for litre+ 17in-rim sport bikes
        if cat in sportish and cc >= 1000 and rim_width and rim_width[0] == 17:
            plans.append(
                {
                    "bike_id": bid,
                    "tire_key": "mt_slick_17",
                    "position": "rear",
                    "fitment_type": "drag_prep",
                    "notes": "Competition slick — strip only, no DOT",
                }
            )

        # R4b: Hook-Up Pro competition carcass for the 1200+ 17in class
        if cat in sportish and cc >= 1200 and rim_width and rim_width[0] == 17:
            plans.append(
                {
                    "bike_id": bid,
                    "tire_key": "hookup_pro_200",
                    "position": "rear",
                    "fitment_type": "drag_prep",
                    "notes": "Hook-Up Pro competition carcass — DOT drag",
                }
            )

        # R5: Pro-street wheel-conversion package (I4 1300 class only —
        # excludes single-sided-swingarm V-twins where a 15in conversion
        # is not a real-world option)
        if cat in sportish and cc >= 1280 and bike["cyl"] == "I4":
            plans.append(
                {
                    "bike_id": bid,
                    "tire_key": "mh_slick_15",
                    "position": "rear",
                    "fitment_type": "drag_prep",
                    "notes": "Requires 15in drag wheel conversion",
                }
            )
            plans.append(
                {
                    "bike_id": bid,
                    "tire_key": "mh_frontrunner_16",
                    "position": "front",
                    "fitment_type": "drag_prep",
                    "notes": "Requires 16in drag front wheel",
                }
            )

        # R6: cruiser pack — rim + width matched recommended rows
        if cat in cruiserish:
            for position in ("front", "rear"):
                oem = front_rims.get(bid) if position == "front" else rim_width
                if not oem:
                    continue
                added = 0
                for spec in CRUISER_TIRES:
                    if added >= 3:
                        break
                    if spec["position"] != position:
                        continue
                    if spec["rim"] != oem[0] or abs(spec["width"] - oem[1]) > 25:
                        continue
                    plans.append(
                        {
                            "bike_id": bid,
                            "tire_key": spec["key"],
                            "position": position,
                            "fitment_type": "recommended",
                            "notes": "Modern V-twin cruiser rubber, OEM rim match",
                        }
                    )
                    added += 1

    return plans


def seed_drag_tires_cruiser(db) -> dict:
    """Seed the drag + cruiser tire packs and their query-driven fitments.
    Idempotent. Returns stats dict."""
    stats = {"tires_created": 0, "fitments_inserted": 0, "skipped": 0, "errors": 0}

    key_to_id: dict[str, int] = {}
    for spec in _ALL_TIRES:
        try:
            tire_id, created = _ensure_tire(db, spec)
            key_to_id[spec["key"]] = tire_id
            if created:
                stats["tires_created"] += 1
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "tire create failed (%s %s): %s", spec["mfr"], spec["model"], exc
            )
            stats["errors"] += 1

    for plan in plan_tire_fitments(db):
        tire_id = key_to_id.get(plan["tire_key"])
        if tire_id is None:
            stats["skipped"] += 1
            continue
        try:
            exists = db._conn.execute(
                "SELECT id FROM bike_tire_fitments "
                "WHERE bike_model_id = ? AND tire_model_id = ? AND position = ?",
                (plan["bike_id"], tire_id, plan["position"]),
            ).fetchone()
            if exists:
                stats["skipped"] += 1
                continue
            db._conn.execute(
                "INSERT INTO bike_tire_fitments "
                "(bike_model_id, tire_model_id, position, fitment_type, "
                " is_default, notes) VALUES (?, ?, ?, ?, 0, ?)",
                (
                    plan["bike_id"],
                    tire_id,
                    plan["position"],
                    plan["fitment_type"],
                    plan["notes"],
                ),
            )
            stats["fitments_inserted"] += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "fitment insert failed (bike=%s tire=%s): %s",
                plan["bike_id"],
                plan["tire_key"],
                exc,
            )
            stats["errors"] += 1

    db._conn.commit()
    logger.info("Drag/cruiser tire pack: %s", stats)
    return stats
