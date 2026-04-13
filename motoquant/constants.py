"""
MotoQuant Pro — Physical Constants & Unit Conversions
====================================================
Single source of truth for all constants used across sub-models.
"""

import numpy as np

G = 9.80665          # m/s2
RPM_TO_RADS = 2.0 * np.pi / 60.0
RADS_TO_RPM = 60.0 / (2.0 * np.pi)
KMH_TO_MS = 1.0 / 3.6
MS_TO_KMH = 3.6
MS_TO_MPH = 2.23694
QUARTER_MILE_M = 402.336  # 1320 feet
EIGHTH_MILE_M = 201.168   # 660 feet
SIXTY_FOOT_M = 18.288     # 60 feet
THOUSAND_FT_M = 304.8     # 1000 feet
THREE30_FT_M = 100.584    # 330 feet
