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
# Taxonomy v2 (July 6, 2026): cylinder-aware sub-clusters. The July-4 246-row
# weighted residual table showed engine character, not displacement, is the
# dominant systematic: twins simmed fast (bias -0.20 within the 600-1100
# sport cluster, w=28.3), 300-500cc singles simmed fast (bias -0.33), and
# sub-500cc I4 screamers (ZX-4RR/ZX-25R) simmed +1.1..+1.3s slow because they
# shared the commuter-twin launch profile. I4s >=600cc and triples were
# already centered (bias +0.005 / +0.017) so their routing is unchanged.
CATEGORY_SPORT_TWIN_600_1300 = "sport_twin_600_1300"
CATEGORY_SMALL_I4_SCREAMER = "small_i4_screamer"
CATEGORY_SINGLE_300_500 = "single_300_500"
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
    CATEGORY_SPORT_TWIN_600_1300,
    CATEGORY_SMALL_I4_SCREAMER,
    CATEGORY_SINGLE_300_500,
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

    Tombstone (2026-07-17): six dead knobs DELETED — tuck_transition_time_s,
    cd_ceiling, pacejka_C, load_sensitivity_k, engine_inertia_mult,
    chain_efficiency_override. Zero consumers anywhere; profiles ASSIGNED
    non-default values that nothing read (KNOWN_TRAPS T11 pattern). The
    intended per-cluster values are recorded in
    reports/session_2026_07_10_physics_foundations_review.md; wiring any of
    them back is epoch-gated (ADR-0002). The same-named TireParams /
    RiderDynamicsParams fields are LIVE and unrelated — do not confuse them.
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

    # ── Aero ───────────────────────────────────────────────────────────
    # Cd floor — minimum permissible aero.cd (catches malformed configs).
    # WIRED July 3, 2026: physics.run() clamps the rider-dynamic Cd*A at
    # cd_floor × frontal_area each step. 0.25 is below every catalog Cd
    # (min ≈ 0.31 × 0.92 race-crouch), so the default is a no-op guard.
    cd_floor: float = 0.25

    # ── Tire grip ──────────────────────────────────────────────────────
    # mu_peak override (None = honour the value the importer set).
    # WIRED July 3, 2026: when set, physics builds TireModel against a
    # config copy whose tires.mu_peak is replaced by this value (launch
    # traction + thermal grip path). None in every profile today.
    mu_peak_override: float | None = None
    # Multiplicative launch-grip recalibration, applied AFTER the override
    # (tires.mu_peak × scale). WIRED July 13, 2026 for the traction-cap
    # epoch: the iterated weight-transfer→traction fix removed the
    # inflated rear-load feed the old per-cluster grip calibration was
    # implicitly tuned against, so clusters re-center with a scale that
    # PRESERVES each bike's relative rubber (unlike the hard override).
    # 1.0 = bit-identical no-op.
    mu_peak_scale: float = 1.0

    # ── Parasitic losses ───────────────────────────────────────────────
    # Multiplier on parasitic (alternator + oil pump + valvetrain).
    parasitic_mult: float = 1.0

    # ── Idle / launch RPM tuning ───────────────────────────────────────
    # Launch RPM as fraction of redline. 0.55 = K5, 0.70 = small-cc
    # (rev higher to compensate for narrower torque band).
    # WIRED July 3, 2026: when set, physics.run() overrides the
    # StagingModel initial engine speed with
    # clamp(redline × factor, idle, redline). None in every profile today.
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
        mu_peak_override=None,  # use importer default (sport ≥600cc → 1.40)
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.08,
        parasitic_mult=1.0,
        notes="Litre superbikes ≥195hp. Best-data cluster.",
    ),
    CATEGORY_LITRE_SPORT_600_1000: CategoryProfile(
        name=CATEGORY_LITRE_SPORT_600_1000,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.07,
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,
        notes="600-1000cc sport (R6, CBR600RR, ZX-6R, GSX-R 600 K6).",
    ),
    CATEGORY_SPORT_TWIN_600_1300: CategoryProfile(
        name=CATEGORY_SPORT_TWIN_600_1300,
        # Sport/naked twins 600-1300cc (Ducati V2 848/959/1098/1199, RS 660,
        # MT-07, RE 650 twins, Buell 1125R, RC8 R, Monster 1200). Split out
        # of litre_sport_600_1000 + "other" July 6, 2026: the 40-row twin
        # sub-population simmed uniformly FAST (w_bias -0.20) while I4s and
        # triples in the same displacement band were centered. Real twins
        # give up launch performance to lumpy power delivery — testers short-
        # shift and launch conservatively vs I4 screamers.
        # Knob values below are the July-6 full-corpus calibration (see
        # scripts/tune_cluster_knobs.py); non-launch knobs inherit the
        # litre_sport_600_1000 parent values.
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        # July 6, 2026 calibration: mu_peak_override is the ONE live knob on
        # this cluster (parasitic_mult bit-identical — the benchmarked twins
        # carry at-wheel dyno curves; cd_floor near-dead; launch_rpm_factor
        # centers bias but degrades spread). Twins cannot use full sport-
        # radial grip off the line — 270-degree/90-degree V-twin torque
        # pulses break traction earlier than an I4's smooth delivery, so
        # the effective launch mu sits below the compound's peak. Grid
        # 1.20-1.35: w|d| 0.2622 -> 0.1871, w_bias -0.1778 -> +0.0019 at 1.31.
        mu_peak_override=1.31,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.085,
        parasitic_mult=1.0,
        notes="Sport/naked twins 600-1300cc (848 EVO, RS 660, MT-07, 1125R).",
    ),
    CATEGORY_SMALL_I4_SCREAMER: CategoryProfile(
        name=CATEGORY_SMALL_I4_SCREAMER,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        # (n=2 cluster — ZX-25R/ZX-4RR; the pre-epoch fit used the
        # decel=2800 over-clutch fudge for the same reason. Effective
        # launch mu ~1.8 is the single-knob fit, honest about thinness.)
        # 2026-08-08 crank-semantics retune: the July-17 honest-data batch
        # (ZX-25R Racelogic 14.1 replacing its DERIVED fit) showed this
        # cluster sim-FAST by -0.95 weighted — the 1.30 grip fudge plus the
        # 2800 decel fudge were both fit to the optimistic pre-instrumented
        # rows. Grid mu{1.30..1.00} x decel{2800,1400}: w|d| 1.184 -> 0.962
        # at mu 1.00 / decel 1400. The residual is the documented n=2
        # conflict (ZX-25R vs ZX-4RR pull opposite) — knob-unfixable.
        mu_peak_scale=1.00,
        # Sub-500cc inline-fours (ZX-4RR 399, ZX-25R 249, CB400SF class).
        # Split out of mid_twin_300_500 July 6, 2026: these 15-17k rpm
        # screamers launch like 600 supersports (high slip, hard clutch
        # work), not like 40hp commuter twins — the shared profile's gentle
        # decel=50 launch left them +1.1..+1.3s slow vs Cycle World data.
        # July 6, 2026 calibration: launch knobs seeded from the
        # mid_twin_500_700 600-I4 values (decel 600) still left the pair
        # +0.63 slow; the sub-500 I4 crank carries a fraction of a 600's
        # rotating mass, so the achievable angular deceleration during
        # launch slip is far higher. Grid 600->2800: w_bias +0.776 -> +0.091,
        # w|d| 0.794 -> 0.351 at 2800 rad/s^2 (~27k rpm/s transient on a
        # near-massless crank; the extra back-torque is still headroom- and
        # inertia-bounded to ~20 Nm). Single-knob fit on n=2 by design —
        # a second knob would be pure overfit.
        over_clutch_factor=0.30,
        max_engine_decel_rads2=1400.0,
        launch_floor_factor=1.0,
        parasitic_mult=1.0,
        notes="Sub-500cc I4 screamers (ZX-4RR, ZX-25R).",
    ),
    CATEGORY_SINGLE_300_500: CategoryProfile(
        name=CATEGORY_SINGLE_300_500,
        # 300-500cc singles (KTM 390 family, RE 350 J-platform, G310,
        # Himalayan, Speed 400). Split out of mid_twin_300_500 July 6, 2026:
        # the single-cylinder sub-population simmed FAST (w_bias -0.33,
        # dominated by the instrumented Duke 390 rows) while the twins in
        # the same band simmed slightly slow (+0.20) — a single shared
        # launch profile could not center both. Values below start from the
        # mid_twin_300_500 parent and are retuned on the singles corpus.
        over_clutch_factor=0.30,
        max_engine_decel_rads2=50.0,
        launch_floor_factor=1.0,
        # July 6, 2026 calibration: after the cylinder-aware synthetic-curve
        # tail fix (singles 30-60hp keep 1.00, twins keep 1.05 — defaults.py)
        # the cluster bias sat at -0.132. Launch knobs are near-dead on these
        # power-limited bikes; effective launch grip is the one live lever.
        # Indian-market OEM rubber (MRF Steel Braces, Metzeler M5 on the 390
        # family) grips well below the sport-radial 1.30 the importer
        # assigns 300-600cc sport bikes. Grid 1.08-1.12: w|d| 0.488 -> 0.484,
        # w_bias -0.132 -> -0.046 at 1.10.
        mu_peak_override=1.18,
        parasitic_mult=1.0,
        notes="300-500cc singles (Duke 390, RC 390, Classic 350, G310).",
    ),
    CATEGORY_MID_TWIN_500_700: CategoryProfile(
        name=CATEGORY_MID_TWIN_500_700,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.14,
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
        parasitic_mult=1.0,
        notes="500-700cc parallel/V twins (SV650, Z650, MT-07).",
    ),
    CATEGORY_MID_TWIN_300_500: CategoryProfile(
        name=CATEGORY_MID_TWIN_300_500,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        # 2026-08-08 crank-semantics retune: under crank curves + the
        # global recal the twins drifted +0.19 slow; grid mu{1.12,1.16,
        # 1.20} x decel{150,400}: w|d| 0.407 -> 0.361 at 1.20/400.
        mu_peak_scale=1.20,
        # Moderate over-clutching. Legacy `peak_hp < 60` 0.30 factor.
        over_clutch_factor=0.30,
        # max_engine_decel_rads2 lowered 200 -> 50 (2026-06-11 calibration):
        # cluster was sim-fast (weighted bias -0.116; Apache RR 310 -0.98 and
        # Benelli 302R -0.93 at w=0.5 vs Ninja 400 +0.49 at w=1.0). Grid
        # probe 50/120/200: weighted bias centers at 50 (-0.011) with w|D|
        # 0.466 -> 0.450. Baselines exact at every point.
        # Raised 50 -> 150 (2026-07-06, taxonomy v2): the singles that
        # dragged this cluster fast now live in single_300_500, leaving a
        # twins-only population (Ninja 400, Z400, R3, MT-03, RS 457) that
        # simmed +0.20 slow. Grid 50/150/300/500: w|d| 0.409 -> 0.393 at
        # 150 with bias +0.196 -> +0.124.
        # Raised 150 -> 400 in the 2026-08-08 retune (see mu note above).
        max_engine_decel_rads2=400.0,
        launch_floor_factor=1.0,
        parasitic_mult=1.0,
        notes="300-500cc twins (Ninja 400, R3, MT-03, Duke 390).",
    ),
    CATEGORY_ENTRY_200_300: CategoryProfile(
        name=CATEGORY_ENTRY_200_300,
        # Aggressive launch — small-cc commuters bog hard if you don't
        # rev them up and slip the clutch. Legacy `peak_hp < 30` 0.40.
        over_clutch_factor=0.40,
        # max_engine_decel_rads2 lowered 280 -> 40 (2026-06-11 calibration):
        # this cluster was sim-FAST (weighted bias -0.22 driven by CBR300R
        # -0.87 w=0.7 and the recovered CBR 250R 2011 row). Grid probe
        # 0/40/80/160/220/280/500/800: w|D| bottoms at 0-40 (0.433-0.434)
        # vs 0.543 at 280; 40 keeps the over-clutch mechanism armed instead
        # of dead. Weighted bias lands -0.015.
        # 2026-08-08 crank-semantics retune: with crank curves + the global
        # recal + the now-live parasitic path (par 0.85), the cluster sat
        # +0.23 slow. Grid mu{1.00,1.06,1.12} x decel{40,200} x par{0.85,
        # 0.50}: w|d| 0.300 -> 0.231 at mu 1.12 / decel 200 / par 0.85.
        max_engine_decel_rads2=200.0,
        launch_floor_factor=1.0,
        mu_peak_scale=1.12,  # 2026-08-08 retune, see decel note above
        parasitic_mult=0.85,
        launch_rpm_factor=None,  # use peak_torque_rpm (importer default)
        notes="200-300cc entry (Pulsar NS200/N250, FZ25, RC 390).",
    ),
    CATEGORY_ENTRY_150_200: CategoryProfile(
        name=CATEGORY_ENTRY_150_200,
        # Most aggressive launch — these bikes have <22 hp and need
        # every trick to hit the strip in 16-17 seconds.
        over_clutch_factor=0.50,
        # max_engine_decel_rads2 raised 350 -> 900 (2026-06-11 calibration):
        # after the R155 gearing fix (primary 1.609/2.1 franken-values ->
        # real 3.042) and the measured-wheel-curve extension to the V3
        # generation, the whole R15/MT-15 quartet simmed consistently slow
        # (+0.49/+0.55 on the two w=1.0 MotoStatz rows). Grid probe 350/600/
        # 900/1300 on the 6-bike weighted sub-cluster: w|D| 0.673 -> 0.542 at
        # 900 with the R15 V3/V4 pair landing +0.20/+0.31; 1300 over-speeds
        # the NS200 (-1.14) for no pair gain. Baselines exact at every point.
        # Lowered 900 -> 150 (2026-08-08 crank-semantics retune): the
        # July-17 honest-data batch (five Indonesian Racelogic-instrumented
        # rows: MT-15 19.6, Apache RTR 200 4V 18.1, ...) exposed the 900
        # value as fit to optimistic DERIVED rows — the cluster simmed
        # -0.37 weighted FAST. The <22hp power rung is nearly inert here
        # (these bikes are launch-limited: rung sweep 1.13 -> 0.96 moved
        # bias only -0.37 -> -0.33), so the honest lever is launch
        # aggression. Grid 900/500/250/200/150/100/50: bias centers at 150
        # (-0.01) with w|d| 0.749 -> 0.701. over_clutch_factor is inert in
        # this regime (decel binds first in the over-clutch min()).
        max_engine_decel_rads2=150.0,
        launch_floor_factor=1.0,
        parasitic_mult=0.85,
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
        # parasitic_mult, mu_peak_override and the since-deleted inertia/
        # chain-eff knobs all return identical bias/mae at every value). At 800, NSR250R
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
        # Raised 1500 -> 1800 (2026-07-06 full-corpus retune): cluster bias
        # +0.153 -> +0.096 with w|d| flat (0.584 -> 0.587); the documented
        # bimodality (NSR250R/RD350 slow vs RG500/RS250 fast) persists and
        # is benchmark-quality-limited, not knob-limited.
        over_clutch_factor=0.55,
        # Raised 1800 -> 2400 (2026-08-08 crank-semantics retune, with
        # parasitic_mult 0.20 -> 0.10 below): under crank curves the 2T
        # parasitic path went live for the first time; grid par{0.20,0.10}
        # x decel{1800,2400}: w|d| 0.669 -> 0.642, bias +0.132 -> +0.077.
        # The documented NSR/RD-vs-RG/RS bimodality persists (data-limited).
        max_engine_decel_rads2=2400.0,
        launch_floor_factor=1.0,
        # 2T tires: vintage rubber (RD350, NSR250) are bias-ply with low
        # peak grip; modern 2T (KTM 300 EXC) more like 1.20.
        mu_peak_override=None,  # honor importer default (varies by year)
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.15,
        parasitic_mult=0.10,  # no valvetrain, premix oil pump only (2026-08-08: 0.20->0.10, see decel note)
        notes="2-stroke (RD350, NSR250, RGV250, RX100, KTM 300 EXC).",
    ),
    CATEGORY_CRUISER_1300P: CategoryProfile(
        name=CATEGORY_CRUISER_1300P,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.20,
        # Cruisers & muscle bikes (VMAX 1700, Rocket 3) torque off the
        # line. Heavy flywheel.
        # 2026-06-11 calibration: both benchmarked rows (VMAX 1700 +0.477,
        # Rocket 3 R +0.276, Cycle World w=0.7 each) simmed slow — same
        # heavy-torquey under-launch as the "other" cluster. oc 0.30 /
        # decel 800 / floor 1.0 lands +0.318/+0.164 (w|D| 0.377 -> 0.241).
        # N=2 is thin; kept identical to the "other" treatment rather than
        # fitting the pair harder.
        # 2026-06-13: 3rd benchmark (Rocket 3 Storm R) joined the cluster;
        # all 3 rows sim uniformly slow (cluster w_bias +0.355). Modest
        # bump oc 0.30->0.45 / decel 800->900 (muscle bikes slip-launch
        # harder than the shared "other" default) trims the uniform bias
        # without chasing the thin set to target. Same-direction N=3 so
        # low regression risk; references are litre_sport so untouched.
        # 2026-07-06 (3-bike-pin retired, full-corpus retune): all 3 rows
        # still simmed uniformly slow (+0.255). Grid oc 0.45-0.75 x decel
        # 900-1400: knob saturates (headroom-bounded) — oc 0.60 / decel 1100
        # trims w_bias to +0.231; pushing to 0.75/1400 buys only 0.02 more
        # on an n=3 cluster and was rejected as overfit. Residual +0.23 is
        # not launch-reachable (likely aero/mass modelling on VMAX-class).
        over_clutch_factor=0.60,
        max_engine_decel_rads2=1100.0,
        launch_floor_factor=1.0,
        parasitic_mult=0.65,
        notes="≥1300cc cruisers + muscle (VMAX 1700, Rocket 3).",
    ),
    CATEGORY_OTHER: CategoryProfile(
        name=CATEGORY_OTHER,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.15,
        # Catch-all for ADV / touring / scooter / unknown. Conservative
        # mid-tier over-clutching, generous tuck timing.
        # 2026-06-11 calibration: the 15 benchmarked "other" bikes (heavy
        # standards/muscle: CB1100, GSF1250 Bandit, Rebel 1100, B-King,
        # K1300S, R nineT, Hayabusa Gen3...) simmed slow (weighted bias
        # +0.234, w|D| 0.355). Real riders launch these torquey bikes with
        # meaningful clutch slip; the zero-over-clutch legacy behaviour
        # under-launched them. Grid probe (floor 1.0 fixed): oc 0.15/0.30/
        # 0.45 x decel 250/500/800/1100 -> best w|D| 0.296 at oc 0.30 /
        # decel 800 (bias +0.036); decel 1100 centers bias but degrades the
        # sporty-naked fast side (Buell 1125R, RC8 R). launch_floor_factor
        # 1.0 alone is a no-op on this cluster (verified: bit-identical
        # weighted stats) — it only guards the over-clutch bog documented
        # Apr 27. Sacred baselines verified exact at every grid point
        # (references carry explicit litre_sport_195p tags).
        # 2026-07-06 (taxonomy v2): the sporty big twins (1125R, RC8 R,
        # Monster 1200) that used to drag this cluster fast moved to
        # sport_twin_600_1300, leaving the remainder slightly slow
        # (+0.084). Grid oc 0.30-0.40 x decel 800-1000: oc 0.40 / decel
        # 1000 re-centers (w_bias +0.045, w|d| 0.281 -> 0.277).
        over_clutch_factor=0.40,
        max_engine_decel_rads2=1000.0,
        launch_floor_factor=1.0,
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
    cylinders: int | None = None,
) -> str:
    """Map (cc, hp, stroke, category, cylinders) -> canonical category_tag.

    This is the SINGLE source of truth for the taxonomy —
    `scripts/sweep_with_clusters.py::cluster_for` delegates here so the
    physics dispatch and the validation grouping can never diverge.
    Returns CATEGORY_OTHER when no specific cluster matches.

    ``cylinders`` is optional for backward compatibility: when None (old
    saved configs, callers that predate taxonomy v2) the cylinder-aware
    branches are skipped and the July-3 taxonomy is reproduced exactly.
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

    # ── Taxonomy v2 (July 6, 2026): cylinder-aware branches ────────────
    # Placed before the hp>=195 gate on purpose: a 195hp Panigale 1199 V2
    # launches like a big twin, not like an I4 superbike — the twins-fast
    # systematic held across the hp boundary in the July-4 residuals.
    if cylinders == 2 and cc and 600 <= cc < 1300 and cat in ("sport", "naked"):
        return CATEGORY_SPORT_TWIN_600_1300
    if cylinders and cylinders >= 4 and cc and cc < 500 and cat in ("sport", "naked"):
        return CATEGORY_SMALL_I4_SCREAMER
    if cylinders == 1 and cc and 300 <= cc < 500:
        return CATEGORY_SINGLE_300_500

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
    "CATEGORY_SPORT_TWIN_600_1300",
    "CATEGORY_SMALL_I4_SCREAMER",
    "CATEGORY_SINGLE_300_500",
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
