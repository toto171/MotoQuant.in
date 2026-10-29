"""
MotoQuant — Category Profiles
=============================

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
# Frozen reference profile (2026-10 physics epoch). The three hand-curated
# reference bikes in defaults.py (K5 / R1 4C8 / Hayabusa Gen1) used to share
# litre_sport_195p with ~30 catalog bikes, so ANY catalog retune of that
# cluster silently moved the pinned baselines (ADR-0002). They now carry this
# dedicated tag, cloned from litre_sport_195p's knob values as of the epoch
# start; catalog tuning of litre_sport_195p is therefore pin-safe, and this
# profile is tuned ONLY against the references' own published figures
# (K5 9.97 s Sport Rider; R1 4C8 / Hayabusa Gen1 per tests/test_validation.py).
# derive_category_tag() never returns it — it is assigned explicitly.
CATEGORY_REFERENCE_LITRE_195P = "reference_litre_195p"

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
    CATEGORY_REFERENCE_LITRE_195P,
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
#
# 2026-10 PHYSICS EPOCH RETUNE (ADR-0002; reports/acc_epoch_2026_10_24.json,
# scripts/tune_epoch_2026_10_24.py): every value below was re-selected from
# NEUTRAL (rated rubber, modelled parasitics, no over-clutch, no floor,
# default launch rpm) against a joint objective w|d|_ET + 0.01 s/(km/h) x
# w|d|_trap with grouped 5-fold cross-validation and a one-standard-error
# rule toward the simplest knob set; clusters with < 8 benchmark-bound bikes
# or < 6 distinct benchmark rows are not fitted (neutral, or a documented
# donor's knobs). Since the epoch's energy-consistent launch floor the
# over-clutch / floor knobs only act when launch rpm sits above the floor,
# and no cluster's CV supported them — they are 0 everywhere (still wired,
# liveness-tested). The older per-cluster comments below are the history
# of the PRE-epoch physics. The three pinned references carry their own
# frozen profile (reference_litre_195p), fitted only to their published
# figures, so catalog retunes never move the pins.
#
# 2026-10 EPOCH, ROUND 2 (reports/acc_epoch2_2026_10_29.json,
# scripts/tune_epoch2_2026_10_29.py). Round 1 was rejected: its sub-1 grip
# scales left litre bikes traction-limited up to ~230 km/h, where a heavier
# bike runs FASTER. Round 2's physics makes every litre launch WHEELIE-limited
# (combined bike + rider CoG) and power-limited from 2nd gear, and scores
# each benchmark row under its own timing convention (1-ft rollout vs first
# motion). Every value below was re-selected from NEUTRAL inside PHYSICAL
# bounds — mu_peak_scale 0.95-1.15, launch_rpm_factor None or 0.45-0.75 x
# redline (4T clutch-dump rpm; 2T launches on its pipe = None) — with the
# same joint objective / grouped 5-fold CV / one-standard-error rule, and a
# HARD mass-monotonicity gate: a selected knob set must leave every catalog
# bike of its cluster with ET(-10 kg) <= ET(0) <= ET(+10 kg)
# (scripts/check_mass_monotonicity.py). No class rubber override, no
# over-clutch / floor / parasitic knob is used. Values marked "round 1" in
# the comments below are history.

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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json; scripts/tune_epoch_2026_10_24.py, joint ET+trap
        # objective, grouped 5-fold CV, 1-SE rule): the epoch removed the
        # double-counted slip inertia and added the 1-ft rollout, so the
        # cluster launched ~0.27 s FAST at rated rubber. Selected family
        # 'grip+lr' (CV J 0.197 vs grip-only 0.222, beyond 1 SE):
        # mu 0.94 = effective launch grip 6 % under the rated 1.40 sport
        # compound (a test rider modulating wheelie/clutch — the sim's
        # wheelie limit does not bind), launch at 0.80 x redline = the
        # high side of the torque plateau (~11.5k on a 14.5k I4; the
        # V4s / Hayabusa / Z H2 whose rated peak-torque rpm sits at
        # 0.62-0.70 x redline are the bikes it moves). Upper bound of the
        # a-priori plausible 0.45-0.80 band; J is flat within 0.02 over
        # 0.60-0.80 (profile in the report). Litre 60 ft now ~1.78 s.
        # (round 1 above: mu 0.94 / launch 0.80 — rejected, mass inversions.)
        # 2026-10 epoch ROUND 2 (reports/acc_epoch2_2026_10_29.json): the
        # unconstrained CV choice (grip+lr 0.95 / 0.525) left the BMW HP4
        # Race mass-inverted (+10 kg faster AND -10 kg slower: 215 hp on
        # 146 kg wheelies in 2nd gear when lighter, and mu 0.95 makes it
        # traction-limited in 2nd) — as does every other family, neutral
        # included. Re-selected by CV + 1-SE over the 6 gate-FEASIBLE grid
        # points only (all at launch 0.45-0.475): launch at 0.475 x redline
        # (~6.6k on a 14k I4: the magazine-test clutch-slip launch that
        # keeps the front down) with mu 1.05 (rubber 5 % over rated keeps
        # the HP4 out of the 2nd-gear traction limit). Cluster w|d| 0.45 /
        # bias -0.02 (neutral 0.54 / -0.54); mean 60 ft 1.77 s (1-ft
        # rollout; neutral 1.59). The unconstrained choice would have
        # scored w|d| 0.33 but leaves the HP4 inverted and traction-limited
        # above 2nd gear (report 'conservative_alternatives').
        mu_peak_scale=1.05,
        parasitic_mult=1.0,
        launch_rpm_factor=0.475,  # 2026-10 epoch round 2, see mu note
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): selected 'grip' (CV J 0.217; grip+lr 0.211 is
        # within 1 SE, so the simpler set wins). mu 0.93 = effective
        # launch grip 7 % under rated (rider-limited launch; see
        # litre_sport_195p). 60 ft ~1.79 s.
        # 2026-10 epoch ROUND 2: now also hosts the 599 cc I4 supersports
        # (R6 / GSX-R 600 / CBR600RR / 599 ZX-6R, re-routed from
        # mid_twin_500_700). Selected 'grip+lr' (CV J 0.303 +- 0.030; launch
        # only 0.348, beyond 1 SE): clutch-dump at 0.50 x redline (~6.5-8k
        # on 13-16k I3/I4s) and grip 0.95 x rated (the lower bound: street
        # sport radials on an unprepped test surface; 1st-gear launches
        # traction-limited, no bike traction-limited above 2nd gear). Every
        # catalog bike of the cluster mass-monotone (min +-10 kg step
        # +8.8 ms). Cluster w|d| 0.25 / bias -0.09 (neutral 0.46 / -0.45);
        # mean 60 ft 1.75 s (neutral 1.64).
        mu_peak_scale=0.95,
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,
        launch_rpm_factor=0.50,  # 2026-10 epoch round 2
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): override retired — the CV prefers the per-bike
        # rated rubber scaled (grip, CV J 0.280) over a class override
        # (rubber 1.27, CV J 0.284). The 1.31/1.085 pair below was fit
        # to the pre-epoch physics.
        mu_peak_override=None,
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        # 2026-10 epoch ROUND 2: selected 'grip+lr' (CV J 0.347 +- 0.020;
        # launch only 0.369, just outside 1 SE): clutch-dump at 0.475 x
        # redline (~5.5k on an 11.5k Ducati V2 — big twins launch low and
        # short-shift; their torque pulses break traction early) with grip
        # 0.95 x rated (lower bound). The low launch also removes the
        # neutral-knob mass inversion of the 1199 Panigale (2nd-gear
        # wheelie threshold). Cluster w|d| 0.26 / bias -0.04 (neutral
        # 0.45 / -0.40); mean 60 ft 1.83 s (neutral 1.68).
        mu_peak_scale=0.95,  # 2026-10 epoch round 2 (round 1: 0.91)
        parasitic_mult=1.0,
        launch_rpm_factor=0.475,  # 2026-10 epoch round 2
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): THIN cluster (n=2) — not fitted; neutral knobs.
        # Every knob is inert on its power-limited launch (bias moves
        # < 0.11 s across mu 0.80-1.05 and launch rpm 0.6-0.9); the
        # residual (+0.76 s, ZX-25R Racelogic row) is model/data-limited.
        # 2026-10 epoch ROUND 2: still THIN (n=2) — neutral. With the
        # corrected ZX-25R gearing/mass and its Racelogic row scored from
        # first motion the cluster sits at bias -0.19 s.
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): launch knobs neutral. Since the epoch's
        # energy-consistent launch floor, over-clutching only acts when
        # the launch rpm sits above the floor, and the CV found no knob
        # set that beats neutral by more than 1 SE on this cluster
        # (values below the line are the pre-epoch history).
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        # July 6, 2026 calibration: after the cylinder-aware synthetic-curve
        # tail fix (singles 30-60hp keep 1.00, twins keep 1.05 — defaults.py)
        # the cluster bias sat at -0.132. Launch knobs are near-dead on these
        # power-limited bikes; effective launch grip is the one live lever.
        # Indian-market OEM rubber (MRF Steel Braces, Metzeler M5 on the 390
        # family) grips well below the sport-radial 1.30 the importer
        # assigns 300-600cc sport bikes. Grid 1.08-1.12: w|d| 0.488 -> 0.484,
        # w_bias -0.132 -> -0.046 at 1.10.
        # 2026-10 epoch retune: override retired. Best CV family was a class override
        # (1.12, CV J 0.555) but the fold spread is huge (SE 0.21, DERIVED
        # rows with multi-second residuals), so neutral (0.677) is within
        # 1 SE and the simpler set wins. Now also hosts the 650-700 cc
        # singles (690 Duke R, 701 Supermoto, Vitpilen 701, ...).
        # 2026-10 epoch ROUND 2: neutral (best CV, J 0.653 +- 0.197 — fold
        # spread dominated by DERIVED / aggregator rows; no family within
        # reach). Residual bias -0.27 s is data-limited (see the report).
        mu_peak_override=None,
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): selected 'rubber' — a class-level effective grip
        # 1.26 (CV J 0.175) beats scaling the per-bike rated rubber
        # (grip 0.97, CV J 0.203) beyond 1 SE. The cluster mixes 599 cc
        # I4 supersports (rated 1.30) with 650 cc cruiser / ADV twins
        # (rated 1.20 / 1.15): the corpus says the importer's category
        # grip spread is too wide in this class (the road-biased OE
        # rubber on V-Strom / Versys / Vulcan S is not knobby/touring
        # grade), and one class value fits both. Supersports barely move
        # (1.30 x 0.97 = 1.26).
        # 2026-10 epoch ROUND 2: override RETIRED (None). The 599 cc I4
        # supersports it was mostly fitted to now route to
        # litre_sport_600_1000; the remaining population (650-700 cc cruiser
        # / ADV twins + the Tiger Sport 660 / 703F / LFC 700 multis) has 7
        # benchmark-bound bikes — below the fit threshold — so the cluster
        # runs at neutral, rated rubber (bias +0.14 s).
        mu_peak_scale=1.0,
        mu_peak_override=None,
        # Mild over-clutching — these bikes are power-limited but not
        # ridiculously so. Helps fight the +0.5-0.8s residual bias on
        # SV650/Z650/Ninja 650/MT-07 documented in CLAUDE.md.
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): launch knobs neutral. Since the epoch's
        # energy-consistent launch floor, over-clutching only acts when
        # the launch rpm sits above the floor, and the CV found no knob
        # set that beats neutral by more than 1 SE on this cluster
        # (values below the line are the pre-epoch history).
        over_clutch_factor=0.0,
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
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,
        notes="500-700cc twins (cruiser / ADV: Vulcan S, V-Strom 650, Bear 650).",
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
        # 2026-10 epoch retune: neutral (selected; best CV). Residual +0.31 s slow is
        # not knob-reachable (grip inert, launch knobs inert at the
        # energy-consistent floor).
        # ROUND 2: neutral again (best CV, J 0.409); bias +0.19 s.
        mu_peak_scale=1.0,
        # Moderate over-clutching. Legacy `peak_hp < 60` 0.30 factor.
        over_clutch_factor=0.0,
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
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,
        notes="300-500cc twins (Ninja 400, R3, MT-03, Duke 390).",
    ),
    CATEGORY_ENTRY_200_300: CategoryProfile(
        name=CATEGORY_ENTRY_200_300,
        # Aggressive launch — small-cc commuters bog hard if you don't
        # rev them up and slip the clutch. Legacy `peak_hp < 30` 0.40.
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): launch knobs neutral. Since the epoch's
        # energy-consistent launch floor, over-clutching only acts when
        # the launch rpm sits above the floor, and the CV found no knob
        # set that beats neutral by more than 1 SE on this cluster
        # (values below the line are the pre-epoch history).
        over_clutch_factor=0.0,
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
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        mu_peak_scale=1.0,  # 2026-10 epoch retune: neutral (grip inert)
        parasitic_mult=1.0,  # 2026-10 epoch retune: modelled parasitics
        # ROUND 2: neutral (best CV, J 0.379 +- 0.219; grip inert, every
        # set launch rpm worse). Bias +0.27 s slow is not knob-reachable.
        launch_rpm_factor=None,  # use peak_torque_rpm (importer default)
        notes="200-300cc entry (Pulsar NS200/N250, FZ25, RC 390).",
    ),
    CATEGORY_ENTRY_150_200: CategoryProfile(
        name=CATEGORY_ENTRY_150_200,
        # Most aggressive launch — these bikes have <22 hp and need
        # every trick to hit the strip in 16-17 seconds.
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): launch knobs neutral. Since the epoch's
        # energy-consistent launch floor, over-clutching only acts when
        # the launch rpm sits above the floor, and the CV found no knob
        # set that beats neutral by more than 1 SE on this cluster
        # (values below the line are the pre-epoch history).
        # The cluster's w|d| (~0.72) is dominated by the documented
        # R15-vs-MT-15 conflict on the same 155 cc engine (4 instrumented
        # rows of opposite sign); grip is inert (launch-limited).
        # ROUND 2: neutral (best CV, J 0.691 +- 0.619 — the same conflict).
        over_clutch_factor=0.0,
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
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,  # 2026-10 epoch retune: modelled parasitics
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): launch knobs neutral. Since the epoch's
        # energy-consistent launch floor, over-clutching only acts when
        # the launch rpm sits above the floor, and the CV found no knob
        # set that beats neutral by more than 1 SE on this cluster
        # (values below the line are the pre-epoch history).
        # The cluster stays ~+0.6 s slow: the residual is curve/data-
        # limited (2T ladder; RD500LC synthetic curve too weak — data
        # agent report), not launch-knob reachable.
        # ROUND 2: neutral (grip 0.95 has the best CV J 0.531, but neutral
        # 0.566 is within 1 SE 0.065; a 2T launches on its pipe, so no set
        # launch rpm is searched). Bias -0.05 s after the RD350 / RD500LC
        # gearing fixes.
        over_clutch_factor=0.0,
        # Raised 1800 -> 2400 (2026-08-08 crank-semantics retune, with
        # parasitic_mult 0.20 -> 0.10 below): under crank curves the 2T
        # parasitic path went live for the first time; grid par{0.20,0.10}
        # x decel{1800,2400}: w|d| 0.669 -> 0.642, bias +0.132 -> +0.077.
        # The documented NSR/RD-vs-RG/RS bimodality persists (data-limited).
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        # 2T tires: vintage rubber (RD350, NSR250) are bias-ply with low
        # peak grip; modern 2T (KTM 300 EXC) more like 1.20.
        mu_peak_override=None,  # honor importer default (varies by year)
        # July 13, 2026 epoch recalibration: the iterated weight-
        # transfer→traction-cap fix removed the inflated rear-load feed
        # the previous grip calibration was implicitly tuned against;
        # mu_peak_scale re-centers the cluster on the 277-match weighted
        # corpus while preserving each bike's relative rubber
        # (scripts/tune_cluster_knobs.py grids, session 2026-07-13).
        mu_peak_scale=1.0,  # 2026-10 epoch retune: neutral
        # 2026-10 epoch retune: 1.0 — the importer already zeroes the 2T
        # valvetrain loss and sets the premix oil pump; a further x0.10
        # was a fudge (ET effect ~0.02 s).
        parasitic_mult=1.0,
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): THIN cluster (n=4) — not fitted; shares the
        # SELECTED knobs of its documented donor 'other' (heavy, torque-
        # rich road bikes launch alike; the 2026-06-11 calibration kept
        # the two identical for the same reason) — neutral this epoch.
        # ROUND 2: still THIN (n=4) — neutral. The pre-registered donor's
        # knobs ('other': grip 0.95) were evaluated and REJECTED: they make
        # the cluster's own rows worse than neutral (in-sample J 0.398 vs
        # 0.283; bias +0.23 vs +0.03 s), and a donor is a prior, not a licence
        # to degrade a cluster. (Round 1's donor knobs were neutral too.)
        mu_peak_scale=1.0,
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
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,
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
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json): neutral selected (best CV, J 0.377; every fitted
        # family is within noise of it). Donor for cruiser_1300p.
        # ROUND 2: selected 'grip' (CV J 0.396 +- 0.053; neutral 0.456 is
        # outside 1 SE): 0.95 x rated rubber (lower bound) — the heavy ADV /
        # touring / big-standard bikes do not wheelie, their 1st-gear launch
        # is traction-limited on road rubber. Mass gate passed on all 114
        # catalog bikes. Cluster w|d| 0.33 / bias +0.01 (neutral 0.39 /
        # -0.16). Pre-registered donor for cruiser_1300p (rejected there —
        # see that profile).
        mu_peak_scale=0.95,
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
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        parasitic_mult=1.0,
        notes="Catch-all: ADV, touring, scooter, unknown.",
    ),
    CATEGORY_REFERENCE_LITRE_195P: CategoryProfile(
        name=CATEGORY_REFERENCE_LITRE_195P,
        # Clone of litre_sport_195p as of the 2026-10 epoch start (every knob
        # value identical, so this step is bit-identical for the references).
        # Tune ONLY against the references' published figures — never as part
        # of a catalog cluster grid (scripts/tune_cluster_knobs.py has no
        # cluster mapped to this tag).
        over_clutch_factor=0.0,
        max_engine_decel_rads2=0.0,
        launch_floor_factor=0.0,
        mu_peak_override=None,
        # 2026-10 epoch retune (reports/acc_epoch_2026_10_24.json 'reference_fit'): fit ONLY to the three
        # references' published figures — minimax of |ET - pub| / tol
        # with the tests/test_validation.py bands (K5 9.97 +/-0.10, R1
        # 10.30 +/-0.20, Hayabusa 10.1-10.7). mu 0.906 puts all three
        # inside their bands (K5 10.044, R1 10.155, Hayabusa 10.248);
        # launch_rpm_factor stays None (the curated 0.615 = 8000/13000
        # is within the flat band, so the neutral launch wins). Known
        # miss: K5 60 ft 1.69 s vs the 1.8-2.1 s band — no grip/launch
        # setting meets both 60 ft and ET (the references' top end is
        # too strong; physics/data-limited).
        # ROUND 2 (reports/acc_epoch2_2026_10_29.json 'reference_fit'): the
        # references are now wheelie-limited at launch, so grip is inert at
        # the curated launch (neutral K5 9.54 s, 0.43 s quicker than 9.97).
        # Same minimax fit inside the physical bounds: the optimum sits on
        # BOTH lower bounds — clutch-dump at 0.45 x redline (5850 rpm on the
        # K5) and grip 0.95 — K5 9.831 (still 0.04 s under its 9.87-10.07
        # band: physics/data-limited), R1 10.159, Hayabusa 10.446 (inside
        # their bands); traps 238.5 / 230.8 / 230.7 km/h; K5 60 ft 1.724 s
        # (1-ft rollout) / 1.998 s from first motion. All three references
        # mass-monotone over -20..+20 kg.
        mu_peak_scale=0.95,
        parasitic_mult=1.0,
        launch_rpm_factor=0.45,  # 2026-10 epoch round 2
        notes="Frozen profile for the 3 pinned reference bikes (defaults.py).",
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
    # 2026-10 epoch: ALL 4T singles >=300 cc route here (was 300-500 only).
    # The 650-700 cc singles (KTM 690 Duke R / 690 SMC R, Husqvarna 701
    # Supermoto / Vitpilen 701, Ducati Hypermotard 698 Mono, BSA Gold Star
    # 650, KLR 650) used to fall through to litre_sport_600_1000 (an I4
    # supersport launch profile) or mid_twin_500_700 — a single's launch is
    # a single's launch whatever its displacement (one big torque pulse per
    # two revs, short wheelbase, power-limited not traction-limited). The
    # cluster name is kept for DB/tag compatibility.
    if cylinders == 1 and cc and cc >= 300:
        return CATEGORY_SINGLE_300_500
    # 2026-10 epoch, round 2: the 599 cc inline-4 supersports (YZF-R6,
    # GSX-R 600, CBR600RR, 599 cc ZX-6R) sat 1 cc under the 600 cc boundary
    # and fell into mid_twin_500_700 — a cruiser / ADV twin population whose
    # class grip override the round-1 retune fitted mostly to THEM. They share
    # engine character with the 636 cc ZX-6R and the 675 cc triples already in
    # litre_sport_600_1000 (13-16k rpm I3/I4, 115-130 PS, 160-190 kg, sport
    # radials) — the cluster this profile's own notes name them in. Inline-3
    # and inline-4 sport/naked bikes from 500 cc route there; touring / ADV /
    # cruiser multis (Tiger Sport 660, 703F, LFC 700) keep their routing.
    # cylinders=None (old saved configs) never fires this branch.
    if (
        cylinders
        and cylinders >= 3
        and cc
        and 500 <= cc < 600
        and cat in ("sport", "naked")
    ):
        return CATEGORY_LITRE_SPORT_600_1000

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
    "CATEGORY_REFERENCE_LITRE_195P",
    "get_profile",
    "derive_category_tag",
]
