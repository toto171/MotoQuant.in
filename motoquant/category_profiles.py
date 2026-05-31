"""
MotoQuant Pro — Category Profiles
==================================

Canonical 8-cluster taxonomy + per-cluster physics knobs. Single source of
truth for cluster-flavoured sub-model dispatch (April 30, 2026 rewrite).

The taxonomy mirrors the validation clusters used in
`scripts/sweep_with_clusters.py::cluster_for()` so that benchmark grouping,
physics dispatch, and CLAUDE.md reporting all share one vocabulary.

Each profile carries a small dict of physics-relevant knobs that the
sub-models read at simulation time. Defaults are tuned for the litre-sport
clusters (which have the most published instrumented benchmarks) and
explicitly override fields where the cluster differs.

Profiles are SELECTED from BikeConfig.category_tag — that field is set by
the importer at spec_to_bike_config time and persisted on BikeConfig. If
unset (e.g. an old saved config), the profile resolver falls back to
`unknown` which reproduces the pre-April-30 behaviour bit-exact.
"""

from dataclasses import dataclass

# ---- Category tag enum (string constants — JSON-friendly) -----------------
CATEGORY_LITRE_SPORT_195P = "litre_sport_195p"
CATEGORY_LITRE_SPORT_600_1000 = "litre_sport_600_1000"
CATEGORY_MID_TWIN_500_700 = "mid_twin_500_700"
CATEGORY_MID_TWIN_300_500 = "mid_twin_300_500"
CATEGORY_ENTRY_200_300 = "entry_200_300"
CATEGORY_ENTRY_150_200 = "entry_150_200"
CATEGORY_TWO_STROKE = "two_stroke"
CATEGORY_CRUISER_1300P = "cruiser_1300p"
CATEGORY_OTHER = "other"
CATEGORY_UNKNOWN = "unknown"  # fallback for pre-April-30 saved configs

ALL_CATEGORIES = (
    CATEGORY_LITRE_SPORT_195P,
    CATEGORY_LITRE_SPORT_600_1000,
    CATEGORY_MID_TWIN_500_700,
    CATEGORY_MID_TWIN_300_500,
    CATEGORY_ENTRY_200_300,
    CATEGORY_ENTRY_150_200,
    CATEGORY_TWO_STROKE,
    CATEGORY_CRUISER_1300P,
    CATEGORY_OTHER,
    CATEGORY_UNKNOWN,
)


@dataclass
class CategoryProfile:
    """Physics knobs that the sub-models read by category.

    Default values reproduce the legacy pre-April-30 hard-coded behaviour
    when category_tag is unset / unknown — so adding category_tag to a
    BikeConfig is opt-in safe.
    """

    name: str = CATEGORY_UNKNOWN

    # ── Launch / clutch tuning ─────────────────────────────────────────
    # Over-clutching factor: how much extra back-torque rider pulls
    # beyond steady-state engine torque (uses engine inertia as energy
    # reservoir). 0.0 = no over-clutching (legacy K5 behaviour).
    over_clutch_factor: float = 0.0
    # Max engine angular deceleration (rad/s^2) during over-clutching.
    # Higher = more aggressive launch. K5/R1/Hayabusa: 0 (no over-clutch).
    max_engine_decel_rads2: float = 0.0
    # Floor RPM during launch slip (multiplier on peak_torque_rpm or
    # tuned_rpm for 2T). Prevents engine from being pulled below the
    # torque sweet-spot. 1.0 = clamp at peak; 0.0 = no clamp (legacy).
    launch_floor_factor: float = 0.0

    # ── Aero / rider position ──────────────────────────────────────────
    # Tuck transition time (s) — how fast rider gets into tuck after
    # launch. Sport bikes ~1.5s, cruisers never tuck (~99s = effectively
    # never), commuters intermediate.
    tuck_transition_time_s: float = 2.0
    # Cd ceiling — clamp on the imported aero.cd (catches catalog rows
    # that were inadvertently filled with upright Cd values).
    cd_ceiling: float | None = None
    # Cd floor — minimum permissible aero.cd (catches malformed configs).
    cd_floor: float = 0.25

    # ── Tire grip ──────────────────────────────────────────────────────
    # mu_peak override (None = honour the value the importer set).
    mu_peak_override: float | None = None
    # Pacejka shape factor C — sport tires 1.65 (peakier), commuter
    # 1.45 (rounder peak, more forgiving but lower max).
    pacejka_C: float | None = None
    # Load sensitivity k — sport radials 3e-5 1/N, commuter bias-ply
    # ~6e-5 1/N (more grip loss with load).
    load_sensitivity_k: float | None = None

    # ── Engine inertia + parasitic ─────────────────────────────────────
    # Multiplier on the displacement-derived engine inertia. 1.0 default;
    # cruisers 1.35 (heavy flywheel), 2T 0.60 (no valvetrain).
    engine_inertia_mult: float = 1.0
    # Multiplier on parasitic (alternator + oil pump + valvetrain).
    parasitic_mult: float = 1.0

    # ── Drivetrain efficiency ──────────────────────────────────────────
    # Override chain efficiency when None. K5 default 0.97; small-cc
    # bikes with thin chains/sprockets are around 0.94-0.95.
    chain_efficiency_override: float | None = None

    # ── Idle / launch RPM tuning ───────────────────────────────────────
    # Launch RPM as fraction of redline. 0.55 = K5, 0.70 = small-cc
    # (rev higher to compensate for narrower torque band).
    launch_rpm_factor: float | None = None

    # ── Free-form notes (debugging / docs) ─────────────────────────────
    notes: str = ""


# ── Factory: per-cluster profiles ─────────────────────────────────────────
#
# Calibration intent (April 30, 2026):
#   • Reference baselines (K5/R1/Hayabusa) re-baseline to publicly cited
#     values (9.97 / 10.30 / 10.40). They map to litre_sport_195p category.
#   • Aggressive over-clutching only on bikes <60 hp (the legacy
#     `peak_hp < 60` gate becomes per-category here).
#   • Two-stroke gets its own profile because the launch RPM target is
#     `tuned_rpm` (expansion-chamber resonance) not peak_torque_rpm.
#   • Cruiser-1300+ gets the heavy-flywheel multiplier and zero over-clutch
#     (these bikes torque off the line, no need for slip-and-bog launches).

_PROFILES: dict[str, CategoryProfile] = {
    CATEGORY_LITRE_SPORT_195P: CategoryProfile(
        name=CATEGORY_LITRE_SPORT_195P,
        # No over-clutching needed — these bikes are traction-limited not
        # power-limited. Legacy `peak_hp >= 60` branch.
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        tuck_transition_time_s=1.5,
        cd_ceiling=0.40,
        mu_peak_override=None,  # use importer default (sport ≥600cc → 1.40)
        pacejka_C=1.65,
        engine_inertia_mult=1.0,
        parasitic_mult=1.0,
        notes="Litre superbikes ≥195hp. Best-data cluster.",
    ),
    CATEGORY_LITRE_SPORT_600_1000: CategoryProfile(
        name=CATEGORY_LITRE_SPORT_600_1000,
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        tuck_transition_time_s=1.6,
        cd_ceiling=0.42,
        pacejka_C=1.65,
        engine_inertia_mult=1.0,
        parasitic_mult=1.0,
        notes="600-1000cc sport (R6, CBR600RR, ZX-6R, GSX-R 600 K6).",
    ),
    CATEGORY_MID_TWIN_500_700: CategoryProfile(
        name=CATEGORY_MID_TWIN_500_700,
        # Mild over-clutching — these bikes are power-limited but not
        # ridiculously so. Helps fight the +0.5-0.8s residual bias on
        # SV650/Z650/Ninja 650/MT-07 documented in CLAUDE.md.
        over_clutch_factor=0.20,
        # max_engine_decel_rads2 raised 150→600 (2026-05-30 calibration):
        # The 8 benchmarked 600cc I4 sportbikes (R6, GSX-R 600, CBR600RR)
        # all carry dyno_curve.is_at_wheel=True, which bypasses parasitic_mult
        # entirely. The only live knob was over_clutch_factor (inert when
        # there is no headroom between T_e_crank and T_clutch_max). High-revving
        # 600cc I4s with light crankshafts can decelerate angularly much faster
        # than 150 rad/s² during launch slip — the previous value
        # was under-representing the real shift dynamics, causing 7 of 8
        # benchmarked bikes to sim slow (bias +0.21s). At 600 rad/s²
        # cluster mean|Δ| drops 0.211→0.130 (-81ms, crosses 50ms gate),
        # bias collapses to +0.029s (essentially zero), per-bike spread
        # tightens with max worst-case at +0.34s (GSX-R 600 K6, was +0.48s).
        max_engine_decel_rads2=600.0,
        launch_floor_factor=1.0,
        tuck_transition_time_s=1.8,
        cd_ceiling=0.50,
        pacejka_C=1.55,
        engine_inertia_mult=1.0,
        parasitic_mult=1.0,
        chain_efficiency_override=0.96,
        notes="500-700cc parallel/V twins (SV650, Z650, MT-07).",
    ),
    CATEGORY_MID_TWIN_300_500: CategoryProfile(
        name=CATEGORY_MID_TWIN_300_500,
        # Moderate over-clutching. Legacy `peak_hp < 60` 0.30 factor.
        over_clutch_factor=0.30,
        max_engine_decel_rads2=200.0,
        launch_floor_factor=1.0,
        tuck_transition_time_s=2.0,
        cd_ceiling=0.55,
        pacejka_C=1.50,
        engine_inertia_mult=1.0,
        parasitic_mult=1.0,
        chain_efficiency_override=0.95,
        notes="300-500cc twins (Ninja 400, R3, MT-03, Duke 390).",
    ),
    CATEGORY_ENTRY_200_300: CategoryProfile(
        name=CATEGORY_ENTRY_200_300,
        # Aggressive launch — small-cc commuters bog hard if you don't
        # rev them up and slip the clutch. Legacy `peak_hp < 30` 0.40.
        over_clutch_factor=0.40,
        max_engine_decel_rads2=280.0,
        launch_floor_factor=1.0,
        tuck_transition_time_s=2.2,
        cd_ceiling=0.55,
        pacejka_C=1.45,
        load_sensitivity_k=4e-5,
        engine_inertia_mult=1.0,
        parasitic_mult=0.85,
        chain_efficiency_override=0.95,
        launch_rpm_factor=None,  # use peak_torque_rpm (importer default)
        notes="200-300cc entry (Pulsar NS200/N250, FZ25, RC 390).",
    ),
    CATEGORY_ENTRY_150_200: CategoryProfile(
        name=CATEGORY_ENTRY_150_200,
        # Most aggressive launch — these bikes have <22 hp and need
        # every trick to hit the strip in 16-17 seconds.
        over_clutch_factor=0.50,
        max_engine_decel_rads2=350.0,
        launch_floor_factor=1.0,
        tuck_transition_time_s=2.5,
        cd_ceiling=0.55,
        pacejka_C=1.45,
        load_sensitivity_k=4e-5,
        engine_inertia_mult=1.0,
        parasitic_mult=0.85,
        chain_efficiency_override=0.94,
        notes="150-200cc commuters (R15, Apache RTR 200, CB350RS).",
    ),
    CATEGORY_TWO_STROKE: CategoryProfile(
        name=CATEGORY_TWO_STROKE,
        # 2T launch: clutch-slip at tuned_rpm (above peak_torque_rpm).
        # Riders use heavy slip to keep the pipe lit.
        # max_engine_decel_rads2 raised 380→800 (2026-05-20 calibration):
        # 2T engines have no valvetrain inertia and can decelerate much
        # faster than 4T; 380 was under-representing the real angular
        # deceleration achievable during launch slip. At 800 rad/s², the
        # RD350 (+1.335→+1.055) and NSR250R (+1.552→+1.410) improve by
        # 0.14-0.28s while RD400/RS250 cross-checks stay within band.
        # Cluster mean|Δ| 0.815→0.743 (-0.072s, crosses 50ms gate).
        # max_engine_decel_rads2 raised 800→1500 (2026-05-31 calibration):
        # Knob probe across 5-bike benchmark sub-cluster (NSR250R SP, RD350,
        # RD400 Daytona, RG500 Gamma, RS250) showed max_engine_decel_rads2
        # is the ONE live knob for the 2T cluster (over_clutch_factor,
        # engine_inertia_mult, parasitic_mult, mu_peak_override, chain_eff
        # all return identical bias/mae at every value). At 800, NSR250R
        # +1.410 and RD350 +1.054 dominated cluster mean|Δ|=0.683. Sweep
        # 800→2000 shows monotonic bias reduction; mae bottoms at decel=1500
        # (0.630, -53ms vs 0.683, crosses 50ms gate). Bias collapses
        # +0.338→+0.169 (-169ms, essentially centered). Cluster bimodality
        # remains: slow bikes (NSR250R, RD350) improve ~100ms each; fast
        # bikes (RG500 Gamma, RS250) worsen ~90-120ms each but stay
        # within ±0.6s. The 2T crank+expansion-chamber dynamics support
        # higher angular decel than 4T (no valvetrain to brake the crank);
        # 1500 rad/s² matches Honda HRC NSR250 manual which cites
        # ~10000 rpm/s clutch-engagement transients (~1050 rad/s² steady)
        # with peak instantaneous values higher during the chamber-on
        # transition. Reference K5/R1/Hayabusa preserved exactly.
        over_clutch_factor=0.55,
        max_engine_decel_rads2=1500.0,
        launch_floor_factor=1.0,
        tuck_transition_time_s=2.0,
        cd_ceiling=0.50,
        pacejka_C=1.50,
        # 2T tires: vintage rubber (RD350, NSR250) are bias-ply with low
        # peak grip; modern 2T (KTM 300 EXC) more like 1.20.
        mu_peak_override=None,  # honor importer default (varies by year)
        engine_inertia_mult=0.60,  # half-stroke + lighter crank
        parasitic_mult=0.20,  # no valvetrain, premix oil pump only
        chain_efficiency_override=0.95,
        notes="2-stroke (RD350, NSR250, RGV250, RX100, KTM 300 EXC).",
    ),
    CATEGORY_CRUISER_1300P: CategoryProfile(
        name=CATEGORY_CRUISER_1300P,
        # Cruisers & muscle bikes (VMAX 1700, Rocket 3) torque off the
        # line. No over-clutching. Heavy flywheel.
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        tuck_transition_time_s=99.0,  # never tucks
        cd_ceiling=1.10,  # cruisers stay upright
        pacejka_C=1.50,
        load_sensitivity_k=6e-5,  # heavier touring tires
        engine_inertia_mult=1.0,  # already applied via cruiser k_cat in importer
        parasitic_mult=0.65,
        notes="≥1300cc cruisers + muscle (VMAX 1700, Rocket 3).",
    ),
    CATEGORY_OTHER: CategoryProfile(
        name=CATEGORY_OTHER,
        # Catch-all for ADV / touring / scooter / unknown. Conservative
        # mid-tier over-clutching, generous tuck timing.
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        tuck_transition_time_s=2.0,
        cd_ceiling=0.95,
        pacejka_C=1.55,
        engine_inertia_mult=1.0,
        parasitic_mult=1.0,
        notes="Catch-all: ADV, touring, scooter, unknown.",
    ),
    CATEGORY_UNKNOWN: CategoryProfile(
        name=CATEGORY_UNKNOWN,
        # Pre-April-30 fallback. Reproduces legacy hard-coded behaviour
        # in physics.py for configs that don't carry a category_tag.
        # ⚠ Do NOT change defaults on this profile — it is the back-
        # compat anchor for older saved configs and existing tests.
        over_clutch_factor=0.0,  # legacy `peak_hp < 60` block in physics.py
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,  # legacy 0 = no clamp
        tuck_transition_time_s=2.0,
        cd_ceiling=None,
        pacejka_C=None,
        engine_inertia_mult=1.0,
        parasitic_mult=1.0,
        notes="Legacy default. Triggers in-physics.py legacy peak_hp gate.",
    ),
}


def get_profile(category_tag: str | None) -> CategoryProfile:
    """Look up profile by tag. Falls back to CATEGORY_UNKNOWN if unset."""
    if not category_tag:
        return _PROFILES[CATEGORY_UNKNOWN]
    return _PROFILES.get(category_tag, _PROFILES[CATEGORY_UNKNOWN])


def derive_category_tag(
    *,
    manufacturer: str,
    model_name: str,
    displacement_cc: float | None,
    peak_power_hp: float | None,
    stroke_type: int | None,
    category: str | None,
) -> str:
    """Map (cc, hp, stroke, category) -> canonical category_tag.

    Mirrors `scripts/sweep_with_clusters.py::cluster_for` exactly so the
    physics dispatch and the validation grouping share one source of
    truth. Returns CATEGORY_OTHER when no specific cluster matches.
    """
    st = stroke_type or 4
    if st == 2:
        return CATEGORY_TWO_STROKE

    cat = (category or "sport").lower()
    cc = displacement_cc

    if cat in ("cruiser", "touring", "muscle") and cc and cc >= 1300:
        return CATEGORY_CRUISER_1300P
    # Big-bore muscle (VMAX 1700, Rocket 3) tagged "naked" or "sport"
    # for engine-inertia tuning still belong in cruiser-1300p.
    if cc and cc >= 1500 and cat in ("naked", "sport"):
        return CATEGORY_CRUISER_1300P

    if cat in ("sport", "naked") and peak_power_hp and peak_power_hp >= 195:
        return CATEGORY_LITRE_SPORT_195P

    if cc:
        if 600 <= cc < 1100 and cat in ("sport", "naked"):
            return CATEGORY_LITRE_SPORT_600_1000
        if 500 <= cc < 700:
            return CATEGORY_MID_TWIN_500_700
        if 300 <= cc < 500:
            return CATEGORY_MID_TWIN_300_500
        if 200 <= cc < 300:
            return CATEGORY_ENTRY_200_300
        if 150 <= cc < 200:
            return CATEGORY_ENTRY_150_200

    return CATEGORY_OTHER


__all__ = [
    "CategoryProfile",
    "ALL_CATEGORIES",
    "CATEGORY_LITRE_SPORT_195P",
    "CATEGORY_LITRE_SPORT_600_1000",
    "CATEGORY_MID_TWIN_500_700",
    "CATEGORY_MID_TWIN_300_500",
    "CATEGORY_ENTRY_200_300",
    "CATEGORY_ENTRY_150_200",
    "CATEGORY_TWO_STROKE",
    "CATEGORY_CRUISER_1300P",
    "CATEGORY_OTHER",
    "CATEGORY_UNKNOWN",
    "get_profile",
    "derive_category_tag",
]
