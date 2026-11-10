"""
MotoQuant — Physical Constants & Unit Conversions
=================================================
Single source of truth for all constants used across sub-models.
"""

import numpy as np

G = 9.80665  # m/s2
RPM_TO_RADS = 2.0 * np.pi / 60.0
RADS_TO_RPM = 60.0 / (2.0 * np.pi)
KMH_TO_MS = 1.0 / 3.6
MS_TO_KMH = 3.6
MS_TO_MPH = 2.23694
QUARTER_MILE_M = 402.336  # 1320 feet
EIGHTH_MILE_M = 201.168  # 660 feet
SIXTY_FOOT_M = 18.288  # 60 feet
THOUSAND_FT_M = 304.8  # 1000 feet
THREE30_FT_M = 100.584  # 330 feet

# ═══════════════════════════════════════════
# DRAG-STRIP TIMING CONVENTION (2026-10 physics epoch)
# ═══════════════════════════════════════════
# Real ETs are timed from the moment the front tyre clears the staging beam,
# which happens after ~1 ft of travel from rest ("rollout"). The track
# distance is measured from the start line the bike stages on, so the finish
# line is d from the rest position and the timed run is d - rollout long (the
# strip's beam-to-beam timing; the GPS "subtract the first foot" rule is the
# same thing). MotoQuantEngine.run() integrates from rest and reports every
# split as
#   t(x = d) - t(x = rollout)        (d > rollout)
# with the trap speed taken at the finish line x = d. (Round 1 of the epoch
# put the finish at rollout + d — a third convention, +4.8 ms on the
# references' ET; fixed in round 2.) run(rollout_m=0.0) gives the "from first
# motion" convention instead (what the GPS/ECU log parsers in
# motoquant/calibration measure).
ROLLOUT_M = 0.3048  # 1 ft

# ═══════════════════════════════════════════
# REV LIMITER (2026-10 physics epoch)
# ═══════════════════════════════════════════
# Soft-cut limiter: full torque up to redline, then a linear torque taper that
# reaches a full ignition cut at REV_LIMITER_CUT_FACTOR × redline. The taper
# has the same integrated torque allowance as the legacy hard cut at
# 1.02 × redline (∫ of the ramp over 1.00→1.04 == width of 1.00→1.02) but no
# discontinuity, so (a) a clutch-slip launch whose engine runs to the slip
# clip (1.02 × redline) still transmits torque — the hard cut sat exactly at
# the clip and froze such runs at zero drive force forever — and (b) a bike
# rev-limited in top gear settles smoothly at drive == drag instead of
# chattering at the step rate (run_top_speed plateau detection).
REV_LIMITER_CUT_FACTOR = 1.04

# ═══════════════════════════════════════════
# RIDER ANTHROPOMETRY (2026-10 physics epoch, round 2)
# ═══════════════════════════════════════════
# The wheelie limit and the load transfer act at the COMBINED bike + rider
# centre of mass (submodels/cog.py). ChassisParams.cog_height_mm is the
# bike's own CoG (dry + fluids); the rider is composed on top of it at
#   h_rider = seat_height - static_sag + RIDER_COG_ABOVE_SEAT_PER_STATURE * stature.
#
# Derivation (standard segment mass fractions, Dempster via Winter,
# "Biomechanics and Motor Control of Human Movement", 4th ed., Table 4.1:
# trunk 0.497, head+neck 0.081, both arms 0.100, both thighs 0.200, both
# shanks 0.093, both feet 0.029 of body mass; segment lengths scale with
# stature), for a 1.75 m rider in a sport-bike launch crouch (torso ~45 deg
# forward, hands on clip-ons ~5 cm above the seat, knees at the tank, feet on
# rear-set pegs ~0.40 m below the seat; hip joint ~0.09 m above the seat):
#   trunk  CoG +0.27 m, head +0.54 m, arms +0.25 m, thighs +0.05 m,
#   shanks -0.17 m, feet -0.39 m  (heights above the seat surface)
#   => whole-body CoG = sum(frac * height) = +0.19 m above the seat
# (+0.25 m sitting bolt upright, +0.16 m in a 60 deg race tuck; the legs
# below the seat are why a seated body's CoG is far lower than its torso's).
# Gear (helmet, boots) adds ~+0.01 m. 0.20 m / 1.75 m = 0.114 of stature.
RIDER_COG_ABOVE_SEAT_PER_STATURE = 0.114

# ═══════════════════════════════════════════
# TYRE HEAT BALANCE (2026-10 physics epoch, round 2)
# ═══════════════════════════════════════════
# The friction power F_x * v_slip dissipated in the contact patch is shared
# between the tread and the road. Both surfaces are swept by the contact at
# (essentially) the vehicle speed, so Blok's heat-partition rule (H. Blok,
# 1937; J.C. Jaeger, 1942) gives the tread the share
#   e_tread / (e_tread + e_road),   e = sqrt(k * rho * c)  (thermal effusivity)
# The tread's k and c are the TireParams values (thermal_conductivity,
# specific_heat_rubber); its density is a filled-rubber tread compound's.
# The road is dense-graded asphalt concrete (k ~1.2 W/m/K, rho ~2350 kg/m3,
# c ~920 J/kg/K — typical pavement-engineering values) => e ~1610.
# Default tyre (k 0.2, c 1500): e_tread ~587 => ~27% of the slip heat
# enters the tread. Before round 2 the tread received ALL of it, which (with
# the convection below) ran a top-speed run's tyre to 400-570 C.
TREAD_RUBBER_DENSITY_KGM3 = 1150.0
ROAD_THERMAL_EFFUSIVITY = (1.2 * 2350.0 * 920.0) ** 0.5  # J/(m2 K s^0.5)

# Forced convection from the tread band to the air: the McAdams (Heat
# Transmission, 3rd ed., 1954) wind correlation in SI form,
#   h = 7.2 v^0.78   W/(m2 K)   (v > ~4.9 m/s; stated range to ~30 m/s,
#                                extrapolated above it), v = road speed (m/s)
# floored at its still-air value 5.7 W/(m2 K): h = max(5.7, 7.2 v^0.78).
# (McAdams' low-speed branch 5.7 + 3.8 v crosses the power law twice, at ~3.3
# and ~9 m/s, so neither max() nor min() of the two branches is the
# correlation; the floored power law stays within 7% of the linear branch
# below 4.9 m/s, where a drag run spends < 0.5 s.) The cooled area is the
# tread band, 2 pi r_rear * section width. The old fixed h = 10 + 0.5 v over
# 0.15 m2 under-cooled a 190-section tyre ~15x at 300 km/h.
CONV_H_STILL_AIR = 5.7
CONV_H_COEFF = 7.2
CONV_H_EXP = 0.78
# Section width (m) assumed when a tyre size string cannot be parsed.
DEFAULT_TREAD_WIDTH_M = 0.18

# ═══════════════════════════════════════════
# LAND SPEED RECORD / TOP SPEED CONSTANTS
# ═══════════════════════════════════════════
ONE_MILE_M = 1609.344  # 1 statute mile — Texas Mile, Ohio Mile, Elvington
ONE_KM_M = 1000.0  # standing kilometre — Nardo, ECTA
HALF_MILE_M = 804.672  # Wilmington / ECTA half-mile shootouts
TWO_MILE_M = 3218.688  # Loring AFB, Bonneville short course
THREE_MILE_M = 4828.032  # Bonneville long course / Black Rock measured mile
FIVE_MILE_M = 8046.72  # Bonneville 5-mile long course

# Standard measured-mile flying start: vehicle accelerates then enters the
# timed mile at steady-state. We model this by running past the measured
# distance with a long run-up and extracting the mile segment velocity.
FLYING_MILE_RUNUP_M = 2500.0  # typical pre-trap acceleration zone

# Top-speed plateau detection: terminal velocity is declared when
# |dv/dt| < TOPSPEED_PLATEAU_ACCEL for TOPSPEED_PLATEAU_WINDOW_S seconds.
TOPSPEED_PLATEAU_ACCEL = 0.05  # m/s^2 (about 0.005g — effectively coasting at terminal)
TOPSPEED_PLATEAU_WINDOW_S = 1.5  # seconds of sustained low-accel
TOPSPEED_MAX_TIME_S = 120.0  # hard cap — any bike terminals under 2 min
TOPSPEED_MAX_DISTANCE_M = 20000.0  # 20 km upper bound for integration
