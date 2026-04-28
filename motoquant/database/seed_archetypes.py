"""
Pre-built modded archetype seed data.

Famous turbo / nitrous / big-bore / track-only drag-scene builds.  Each
archetype layers deltas + multipliers onto an OEM base bike (resolved by
manufacturer + model_name substring at seed time).

These are NOT separate bike models — they are *modifications* the chat
layer can stack onto a base BikeConfig before running the engine. That
keeps `bike_models` / `known_bikes.py` strictly OEM and lets us model
custom builds (TTS Stage 2, Velocity 5-sec, Bonneville H2 Carbon, etc.)
without polluting the headline catalog.

Sources are best-effort published numbers (workshop dyno sheets, magazine
features, runs documented at Bonneville / Santa Pod / Bandimere).  ETs
quoted in `notes` are real-world reported figures, not sim outputs.
"""

from __future__ import annotations

from typing import Any


# ───────────────────────────────────────────────────────────────────
# Archetype catalog.
#
# Each row keys into bike_archetypes columns.
#   base_bike_match: dict with keys {manufacturer, model_contains}
#                    used to resolve base_bike_model_id at seed time.
#   power_multiplier: applied to peak_power_hp + dyno_curve.torque_nm.
#   peak_power_hp_override: if set, replaces peak_power_hp before mult.
#   mass_delta_kg: + lighter is negative (e.g. carbon track kit), heavier
#                    is positive (turbo plumbing + intercooler).
#   cd_delta / frontal_area_delta_m2: aero changes (track fairings, naked
#                    conversions, large turbo plumbing protruding).
#   sprocket_*_override: hard-coded ratio for drag racing.
#   tire_mu_override: drag slicks (1.85+) vs treaded street DOT-R (1.55).
#   estimated_build_inr: rough INR cost to replicate (turbo kit + tune +
#                    fab + trans build), 2026 prices.
#   is_homologation: 1 if track-only / not road legal.
# ───────────────────────────────────────────────────────────────────

ARCHETYPES: list[dict[str, Any]] = [
    # ── 1. TTS Performance Stage 2 Turbo Hayabusa ──────────────────
    {
        "name": "TTS Stage 2 Turbo Hayabusa",
        "base_bike_match": {"manufacturer": "Suzuki", "model_contains": "Hayabusa"},
        "description": (
            "Big Cheese Racing / TTS Performance Stage 2 turbo kit. "
            "Garrett GT2860RS, IHI tubular manifold, front-mount intercooler, "
            "1.0-bar street boost, ~325 hp at the wheel on pump 95 RON."
        ),
        # Stock Gen-1 Hayabusa: 175 hp wheel. TTS Stage 2: 325 hp wheel.
        # Multiplier on peak_power_hp (which is crank ~197 hp Gen-1) lands ~365 hp crank.
        "power_multiplier": 1.85,
        "peak_power_hp_override": None,
        "peak_torque_nm_override": 220.0,
        "mass_delta_kg": 14.0,  # turbo + intercooler + plumbing + larger battery
        "cd_delta": 0.02,        # plumbing stick-out adds drag
        "frontal_area_delta_m2": 0.015,
        "sprocket_front_override": 18,  # taller for top-end pulls
        "sprocket_rear_override": 40,
        "chain_pitch_override": "530",
        "tire_mu_override": 1.65,  # M&H drag radial street legal
        "notes": (
            "Reported 8.4-8.7s 1/4 mile @ 240+ km/h on street boost with a competent "
            "rider. Peak boost 1.0-1.4 bar; race boost variants exist with built "
            "bottom end and methanol injection."
        ),
        "source_url": "https://www.tts-performance.co.uk/hayabusa-stage-2-turbo",
        "estimated_build_inr": 1_400_000,  # ~£12k kit landed in India incl. duty
        "is_homologation": 0,
    },

    # ── 2. Velocity Racing 5-second Hayabusa ───────────────────────
    {
        "name": "Velocity Racing 5-sec Turbo Hayabusa",
        "base_bike_match": {"manufacturer": "Suzuki", "model_contains": "Hayabusa"},
        "description": (
            "Velocity Racing built bottom-end turbo Hayabusa. PSE turbo, billet "
            "rods + crank, dry-clutch, methanol injection. Pro Street class "
            "drag racer running 5.9s 1/4 mile on a stretched chassis."
        ),
        "power_multiplier": 2.95,    # ~600 hp crank target
        "peak_power_hp_override": None,
        "peak_torque_nm_override": 480.0,
        "mass_delta_kg": -22.0,      # full strip + carbon body, but stretched chassis adds
        "cd_delta": -0.04,           # tight low-slung fairing on long-wheelbase chassis
        "frontal_area_delta_m2": 0.0,
        "sprocket_front_override": 19,
        "sprocket_rear_override": 38,
        "chain_pitch_override": "530",
        "tire_mu_override": 1.95,    # M&H 5.0 slick + chassis air shifter combo
        "notes": (
            "5.9s 1/4 mile @ 380+ km/h reported. Track-only — stretched 60+\" "
            "wheelbase, no headlight, Lexan windscreen, manual shifter or "
            "air-shifter. Not legal for the road in any jurisdiction."
        ),
        "source_url": "https://velocityracing.com/turbo-hayabusa-5-second-package",
        "estimated_build_inr": 4_800_000,
        "is_homologation": 1,
    },

    # ── 3. Bonneville H2 Carbon (track edition) ─────────────────────
    {
        "name": "Bonneville H2 Carbon Track Edition",
        "base_bike_match": {"manufacturer": "Kawasaki", "model_contains": "Ninja H2"},
        "description": (
            "Kawasaki H2 prepared for Bonneville salt-flat top-speed runs. Carbon "
            "fairings, race ECU flash with no rev limiter, low-rolling-resistance "
            "tyres, no mirrors / lights / pillion. ~310 hp crank from H2R-spec "
            "pulleys + open exhaust, weight stripped."
        ),
        "power_multiplier": 1.0,
        "peak_power_hp_override": 310.0,  # H2R-spec supercharger + exhaust
        "peak_torque_nm_override": 165.0,
        "mass_delta_kg": -28.0,           # full carbon, no lights/mirrors/pillion
        "cd_delta": -0.05,                # lower fairing, tail-piece, belly pan
        "frontal_area_delta_m2": -0.03,
        "sprocket_front_override": 18,    # taller gearing for >330 km/h runs
        "sprocket_rear_override": 39,
        "chain_pitch_override": "525",
        "tire_mu_override": 1.45,         # Bonneville-specific low-rolling tires
        "notes": (
            "Track / land-speed only, no street legal kit. Closer to H2R "
            "performance than street H2. Reported 9.2s 1/4 mile in roll-on "
            "configurations and 348 km/h on Bonneville salt."
        ),
        "source_url": "https://www.kawasaki.com/h2-carbon",
        "estimated_build_inr": 2_900_000,
        "is_homologation": 1,
    },

    # ── 4. Schnitz Racing Nitrous Hayabusa ─────────────────────────
    {
        "name": "Schnitz Nitrous Hayabusa",
        "base_bike_match": {"manufacturer": "Suzuki", "model_contains": "Hayabusa"},
        "description": (
            "Schnitz Racing 75-shot wet nitrous kit on a Hayabusa. Stock motor "
            "with Schnitz 2-stage progressive controller, 28-row oil cooler, "
            "Cometic head gasket, Power Commander V tune."
        ),
        # 75-shot adds ~75 hp on peak. Stock crank ~197 -> ~270 hp on the bottle.
        "power_multiplier": 1.36,
        "peak_power_hp_override": None,
        "peak_torque_nm_override": 200.0,
        "mass_delta_kg": 8.0,         # bottle, plumbing, controller
        "cd_delta": 0.0,
        "frontal_area_delta_m2": 0.0,
        "sprocket_front_override": 17,
        "sprocket_rear_override": 42,
        "chain_pitch_override": "530",
        "tire_mu_override": 1.70,     # M&H drag radial 200/55-17
        "notes": (
            "9.0-9.3s 1/4 mile typical. Bottle is hit at 60ft after launch on "
            "the front sprocket sensor — full bottle gives ~6 runs. Less "
            "complex than turbo but engine life shortens."
        ),
        "source_url": "https://www.schnitzracing.com/hayabusa-nitrous-75",
        "estimated_build_inr": 380_000,
        "is_homologation": 0,
    },

    # ── 5. Ron Ayers RAW Racing Turbo Hayabusa ─────────────────────
    {
        "name": "Ron Ayers RAW Turbo Hayabusa",
        "base_bike_match": {"manufacturer": "Suzuki", "model_contains": "Hayabusa"},
        "description": (
            "Ron Ayers / RAW Racing UK Pro-Street turbo build. PT88-67 turbo, "
            "Carrillo rods, JE 9.5:1 pistons, MoTeC M150 ECU. Class-legal Pro "
            "Street drag racer competing in ACU / Santa Pod."
        ),
        "power_multiplier": 2.30,         # ~450 hp crank class limit
        "peak_power_hp_override": None,
        "peak_torque_nm_override": 380.0,
        "mass_delta_kg": -18.0,           # carbon panels, lithium battery, no lights
        "cd_delta": -0.02,
        "frontal_area_delta_m2": 0.0,
        "sprocket_front_override": 19,
        "sprocket_rear_override": 38,
        "chain_pitch_override": "530",
        "tire_mu_override": 1.85,         # Mickey Thompson ET Drag slick
        "notes": (
            "Pro Street class winner at Santa Pod multiple seasons. 6.8-7.1s "
            "1/4 mile typical, 320+ km/h trap. Methanol-fuelled, roll-on starts "
            "from a wheelie bar."
        ),
        "source_url": "https://www.ronayers-racing.co.uk/raw-turbo-hayabusa",
        "estimated_build_inr": 3_200_000,
        "is_homologation": 1,
    },
]


def _resolve_base_bike_id(db: Any, manufacturer: str, model_contains: str) -> int | None:
    """Look up a base bike_models.id by manufacturer + model_name LIKE.

    Picks the first matching row sorted by id (stable insertion order).
    Excludes obvious mismatches: SX = sport-touring, Z H2 = naked.
    """
    cur = db._conn.execute(
        """
        SELECT bm.id
          FROM bike_models bm
          JOIN manufacturers m ON m.id = bm.manufacturer_id
         WHERE m.name = ?
           AND bm.model_name LIKE ?
           AND bm.model_name NOT LIKE '%Mach%'
           AND bm.model_name NOT LIKE '%SX%'
           AND bm.model_name NOT LIKE '%Z H2%'
           AND bm.model_name NOT LIKE '%H2R%'
         ORDER BY bm.id
         LIMIT 1
        """,
        (manufacturer, f"%{model_contains}%"),
    )
    row = cur.fetchone()
    return row[0] if row else None


def seed_archetypes(db: Any) -> int:
    """
    Insert all archetypes into bike_archetypes.

    Idempotent: relies on UNIQUE(name, base_bike_model_id). Returns the
    number of rows inserted (excludes skipped duplicates and unmatched
    bases).
    """
    inserted = 0
    skipped_no_base: list[str] = []

    for arc in ARCHETYPES:
        match = arc["base_bike_match"]
        base_id = _resolve_base_bike_id(
            db, match["manufacturer"], match["model_contains"]
        )
        if base_id is None:
            skipped_no_base.append(arc["name"])
            continue

        cur = db._conn.execute(
            """
            INSERT OR IGNORE INTO bike_archetypes (
                name, base_bike_model_id, description,
                power_multiplier, peak_power_hp_override, peak_torque_nm_override,
                mass_delta_kg, cd_delta, frontal_area_delta_m2,
                sprocket_front_override, sprocket_rear_override, chain_pitch_override,
                tire_mu_override, notes, source_url, estimated_build_inr,
                is_homologation
            ) VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?
            )
            """,
            (
                arc["name"],
                base_id,
                arc.get("description"),
                arc.get("power_multiplier", 1.0),
                arc.get("peak_power_hp_override"),
                arc.get("peak_torque_nm_override"),
                arc.get("mass_delta_kg", 0.0),
                arc.get("cd_delta", 0.0),
                arc.get("frontal_area_delta_m2", 0.0),
                arc.get("sprocket_front_override"),
                arc.get("sprocket_rear_override"),
                arc.get("chain_pitch_override"),
                arc.get("tire_mu_override"),
                arc.get("notes"),
                arc.get("source_url"),
                arc.get("estimated_build_inr"),
                int(bool(arc.get("is_homologation", 0))),
            ),
        )
        if cur.rowcount and cur.rowcount > 0:
            inserted += 1

    db._conn.commit()
    if skipped_no_base:
        print(
            f"seed_archetypes: skipped {len(skipped_no_base)} archetypes "
            f"(no base bike match): {', '.join(skipped_no_base)}"
        )
    return inserted


__all__ = ["ARCHETYPES", "seed_archetypes"]
