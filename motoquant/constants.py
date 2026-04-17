"""
MotoQuant Pro — Physical Constants & Unit Conversions
====================================================
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
