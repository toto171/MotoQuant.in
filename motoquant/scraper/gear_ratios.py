"""
MotoQuant Pro — Gear Ratio Lookup Library
==========================================
Bikez.com does NOT publish gear ratios. This module provides a two-tier
fallback so every bike in the DB gets a usable drivetrain even without
service-manual data:

Tier 1 — Model-family lookup  (GEAR_RATIO_DB)
  Keyed by (manufacturer_lower, model_pattern, year_range).
  Patterns are matched with simple substring matching on the model name.
  Source: compiled from service manuals, owners forums, and dyno databases.
  Confidence: 0.75

Tier 2 — Category + displacement class defaults  (category_default_ratios)
  When Tier 1 misses, pick a typical 6-speed/5-speed set based on
  engine size and body style.
  Confidence: 0.45

Gear ratios are listed as [1st, 2nd, 3rd, ...] in descending order
(1st gear is always the highest ratio = lowest speed).

Primary ratio and sprocket defaults are in a separate lookup because they
compound with gear ratios to give overall reduction.
"""

from typing import Optional, List, Dict, Tuple


# ══════════════════════════════════════════════════════════════════
# TIER 1: NAMED MODEL FAMILIES
# Key: (manufacturer_slug, model_substring_lower)
#      manufacturer_slug: manufacturer name in lowercase, spaces→underscores
#      model_substring_lower: if this string appears anywhere in the
#                             lowercased model name, this entry matches.
# Value: dict with gear_ratios, front_sprocket, rear_sprocket (optional),
#        primary_ratio (optional), confidence (0–1).
# When multiple patterns match, the longest model_substring wins.
# ══════════════════════════════════════════════════════════════════

_DB: List[Dict] = [

    # ── Suzuki ────────────────────────────────────────────────────────────────
    {"mfr": "suzuki", "model": "gsx-r 600",   "year": (2001, 2026),
     "ratios": [2.571, 1.944, 1.619, 1.380, 1.238, 1.130],
     "front": 15, "rear": 43, "primary": 1.795},

    {"mfr": "suzuki", "model": "gsx-r 750",   "year": (2000, 2026),
     "ratios": [2.600, 1.944, 1.619, 1.380, 1.238, 1.130],
     "front": 15, "rear": 42, "primary": 1.795},

    {"mfr": "suzuki", "model": "gsx-r 1000",  "year": (2001, 2011),
     "ratios": [2.600, 2.105, 1.750, 1.500, 1.333, 1.200],
     "front": 17, "rear": 42, "primary": 1.522},

    {"mfr": "suzuki", "model": "gsx-r 1000",  "year": (2012, 2026),
     "ratios": [2.571, 1.894, 1.571, 1.381, 1.238, 1.130],
     "front": 17, "rear": 45, "primary": 1.590},

    {"mfr": "suzuki", "model": "hayabusa",     "year": (1999, 2012),
     "ratios": [2.615, 2.062, 1.714, 1.500, 1.333, 1.200],
     "front": 17, "rear": 40, "primary": 1.543},

    {"mfr": "suzuki", "model": "hayabusa",     "year": (2021, 2026),
     "ratios": [2.615, 2.062, 1.714, 1.500, 1.333, 1.200],
     "front": 18, "rear": 40, "primary": 1.543},

    {"mfr": "suzuki", "model": "katana",       "year": (2019, 2026),
     "ratios": [2.571, 1.894, 1.571, 1.381, 1.238, 1.130],
     "front": 17, "rear": 45, "primary": 1.590},

    {"mfr": "suzuki", "model": "gsx-s 1000",   "year": (2015, 2026),
     "ratios": [2.571, 1.894, 1.571, 1.381, 1.238, 1.130],
     "front": 17, "rear": 45, "primary": 1.590},

    {"mfr": "suzuki", "model": "gsx-s 750",    "year": (2017, 2026),
     "ratios": [2.600, 1.944, 1.619, 1.380, 1.238, 1.130],
     "front": 16, "rear": 43, "primary": 1.795},

    {"mfr": "suzuki", "model": "sv 650",       "year": (1999, 2026),
     "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
     "front": 15, "rear": 44, "primary": 1.901},

    {"mfr": "suzuki", "model": "bandit 1200",  "year": (2001, 2006),
     "ratios": [2.500, 1.857, 1.529, 1.333, 1.190, 1.095],
     "front": 17, "rear": 44, "primary": 1.543},

    {"mfr": "suzuki", "model": "bandit 1250",  "year": (2007, 2016),
     "ratios": [2.500, 1.857, 1.529, 1.333, 1.190, 1.095],
     "front": 17, "rear": 44, "primary": 1.543},

    # ── Yamaha ────────────────────────────────────────────────────────────────
    {"mfr": "yamaha", "model": "yzf-r1",       "year": (1998, 2003),
     "ratios": [2.684, 1.947, 1.565, 1.350, 1.208, 1.125],
     "front": 17, "rear": 45, "primary": 1.609},

    {"mfr": "yamaha", "model": "yzf-r1",       "year": (2004, 2014),
     "ratios": [2.643, 1.947, 1.619, 1.380, 1.238, 1.130],
     "front": 17, "rear": 45, "primary": 1.609},

    {"mfr": "yamaha", "model": "yzf-r1",       "year": (2015, 2026),
     "ratios": [2.600, 1.947, 1.619, 1.380, 1.238, 1.130],
     "front": 17, "rear": 45, "primary": 1.609},

    {"mfr": "yamaha", "model": "yzf-r6",       "year": (1999, 2016),
     "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
     "front": 16, "rear": 45, "primary": 1.854},

    {"mfr": "yamaha", "model": "yzf-r6",       "year": (2017, 2022),
     "ratios": [2.714, 2.000, 1.667, 1.444, 1.304, 1.208],
     "front": 16, "rear": 45, "primary": 1.854},

    {"mfr": "yamaha", "model": "yzf-r7",       "year": (2021, 2026),
     "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
     "front": 15, "rear": 45, "primary": 1.866},

    {"mfr": "yamaha", "model": "mt-10",        "year": (2016, 2026),
     "ratios": [2.600, 1.947, 1.619, 1.380, 1.238, 1.130],
     "front": 17, "rear": 44, "primary": 1.609},

    {"mfr": "yamaha", "model": "mt-09",        "year": (2013, 2026),
     "ratios": [2.714, 2.000, 1.619, 1.360, 1.200, 1.080],
     "front": 16, "rear": 45, "primary": 1.861},

    {"mfr": "yamaha", "model": "mt-07",        "year": (2014, 2026),
     "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
     "front": 15, "rear": 45, "primary": 1.866},

    {"mfr": "yamaha", "model": "fz1",          "year": (2001, 2015),
     "ratios": [2.600, 1.947, 1.619, 1.380, 1.238, 1.130],
     "front": 17, "rear": 45, "primary": 1.609},

    {"mfr": "yamaha", "model": "vmax",         "year": (2009, 2020),
     "ratios": [2.500, 1.714, 1.333, 1.095, 0.967, 0.864],
     "front": 18, "rear": 36, "primary": 2.000},

    {"mfr": "yamaha", "model": "xsr900",       "year": (2016, 2026),
     "ratios": [2.714, 2.000, 1.619, 1.360, 1.200, 1.080],
     "front": 16, "rear": 43, "primary": 1.861},

    # ── Honda ────────────────────────────────────────────────────────────────
    {"mfr": "honda", "model": "cbr 1000rr",    "year": (2004, 2016),
     "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
     "front": 16, "rear": 43, "primary": 1.733},

    {"mfr": "honda", "model": "cbr 1000rr",    "year": (2017, 2026),
     "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
     "front": 16, "rear": 41, "primary": 1.733},

    {"mfr": "honda", "model": "cbr 600rr",     "year": (2003, 2020),
     "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
     "front": 16, "rear": 43, "primary": 2.117},

    {"mfr": "honda", "model": "cbr 900rr",     "year": (1992, 2003),
     "ratios": [2.750, 2.056, 1.706, 1.478, 1.304, 1.190],
     "front": 16, "rear": 43, "primary": 1.739},

    {"mfr": "honda", "model": "cbr 954rr",     "year": (2002, 2003),
     "ratios": [2.750, 2.056, 1.706, 1.478, 1.304, 1.190],
     "front": 16, "rear": 43, "primary": 1.739},

    {"mfr": "honda", "model": "cb 1000r",      "year": (2008, 2026),
     "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
     "front": 17, "rear": 42, "primary": 1.733},

    {"mfr": "honda", "model": "cb 650r",       "year": (2019, 2026),
     "ratios": [3.000, 2.117, 1.667, 1.348, 1.161, 1.038],
     "front": 15, "rear": 41, "primary": 2.176},

    {"mfr": "honda", "model": "cb 650f",       "year": (2014, 2018),
     "ratios": [3.000, 2.117, 1.667, 1.348, 1.161, 1.038],
     "front": 15, "rear": 41, "primary": 2.176},

    {"mfr": "honda", "model": "hornet",        "year": (1998, 2013),
     "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
     "front": 16, "rear": 43, "primary": 1.733},

    {"mfr": "honda", "model": "vtr 1000",      "year": (1997, 2005),
     "ratios": [2.462, 1.823, 1.500, 1.310, 1.166, 1.053],
     "front": 15, "rear": 41, "primary": 1.807},

    # ── Kawasaki ─────────────────────────────────────────────────────────────
    {"mfr": "kawasaki", "model": "zx-10r",     "year": (2004, 2015),
     "ratios": [2.642, 2.000, 1.652, 1.436, 1.296, 1.185],
     "front": 17, "rear": 41, "primary": 1.612},

    {"mfr": "kawasaki", "model": "zx-10r",     "year": (2016, 2026),
     "ratios": [2.567, 1.933, 1.619, 1.400, 1.259, 1.148],
     "front": 17, "rear": 41, "primary": 1.612},

    {"mfr": "kawasaki", "model": "zx-6r",      "year": (2003, 2006),
     "ratios": [2.933, 2.133, 1.785, 1.545, 1.380, 1.259],
     "front": 16, "rear": 43, "primary": 2.071},

    {"mfr": "kawasaki", "model": "zx-6r",      "year": (2007, 2026),
     "ratios": [2.933, 2.133, 1.785, 1.545, 1.380, 1.259],
     "front": 16, "rear": 43, "primary": 2.071},

    {"mfr": "kawasaki", "model": "zx-14r",     "year": (2006, 2021),
     "ratios": [2.294, 1.714, 1.379, 1.138, 0.958, 0.857],
     "front": 17, "rear": 37, "primary": 1.545},

    {"mfr": "kawasaki", "model": "ninja h2",   "year": (2015, 2026),
     "ratios": [2.294, 1.714, 1.379, 1.138, 0.958, 0.857],
     "front": 17, "rear": 37, "primary": 1.545},

    {"mfr": "kawasaki", "model": "z1000",      "year": (2003, 2020),
     "ratios": [2.642, 2.000, 1.652, 1.436, 1.296, 1.185],
     "front": 17, "rear": 40, "primary": 1.612},

    {"mfr": "kawasaki", "model": "z900",       "year": (2017, 2026),
     "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
     "front": 15, "rear": 41, "primary": 1.795},

    {"mfr": "kawasaki", "model": "z650",       "year": (2017, 2026),
     "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
     "front": 14, "rear": 42, "primary": 1.795},

    {"mfr": "kawasaki", "model": "er-6",       "year": (2006, 2016),
     "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
     "front": 15, "rear": 46, "primary": 1.795},

    # ── Aprilia ───────────────────────────────────────────────────────────────
    {"mfr": "aprilia", "model": "rsv4",        "year": (2009, 2026),
     "ratios": [2.615, 2.000, 1.667, 1.444, 1.286, 1.148],
     "front": 15, "rear": 38, "primary": 1.872},

    {"mfr": "aprilia", "model": "rs 660",      "year": (2020, 2026),
     "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
     "front": 14, "rear": 39, "primary": 2.056},

    {"mfr": "aprilia", "model": "tuono v4",    "year": (2011, 2026),
     "ratios": [2.615, 2.000, 1.667, 1.444, 1.286, 1.148],
     "front": 15, "rear": 39, "primary": 1.872},

    {"mfr": "aprilia", "model": "tuono 660",   "year": (2021, 2026),
     "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
     "front": 14, "rear": 40, "primary": 2.056},

    {"mfr": "aprilia", "model": "rsv 1000",    "year": (2004, 2009),
     "ratios": [2.769, 2.091, 1.667, 1.391, 1.214, 1.095],
     "front": 15, "rear": 38, "primary": 1.800},

    {"mfr": "aprilia", "model": "shiver 900",  "year": (2017, 2021),
     "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
     "front": 16, "rear": 46, "primary": 1.850},

    # ── Ducati ────────────────────────────────────────────────────────────────
    {"mfr": "ducati", "model": "panigale v4",  "year": (2018, 2026),
     "ratios": [2.462, 1.842, 1.500, 1.308, 1.160, 1.043],
     "front": 15, "rear": 39, "primary": 1.840},

    {"mfr": "ducati", "model": "panigale v2",  "year": (2020, 2026),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 38, "primary": 1.840},

    {"mfr": "ducati", "model": "1098",         "year": (2007, 2009),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 38, "primary": 1.840},

    {"mfr": "ducati", "model": "1198",         "year": (2009, 2011),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 38, "primary": 1.840},

    {"mfr": "ducati", "model": "999",          "year": (2003, 2006),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 38, "primary": 1.840},

    {"mfr": "ducati", "model": "749",          "year": (2003, 2006),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 38, "primary": 1.840},

    {"mfr": "ducati", "model": "streetfighter v4", "year": (2020, 2026),
     "ratios": [2.462, 1.842, 1.500, 1.308, 1.160, 1.043],
     "front": 15, "rear": 42, "primary": 1.840},

    {"mfr": "ducati", "model": "monster",      "year": (2003, 2016),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 43, "primary": 1.840},

    {"mfr": "ducati", "model": "monster",      "year": (2017, 2026),
     "ratios": [2.462, 1.842, 1.500, 1.308, 1.160, 1.043],
     "front": 15, "rear": 43, "primary": 1.840},

    {"mfr": "ducati", "model": "hypermotard",  "year": (2007, 2026),
     "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
     "front": 15, "rear": 43, "primary": 1.840},

    # ── MV Agusta ─────────────────────────────────────────────────────────────
    {"mfr": "mv_agusta", "model": "f4",        "year": (1999, 2018),
     "ratios": [2.667, 2.000, 1.615, 1.348, 1.174, 1.040],
     "front": 16, "rear": 41, "primary": 1.840},

    {"mfr": "mv_agusta", "model": "f3 675",    "year": (2012, 2016),
     "ratios": [2.769, 2.125, 1.706, 1.462, 1.300, 1.174],
     "front": 15, "rear": 40, "primary": 1.960},

    {"mfr": "mv_agusta", "model": "f3 800",    "year": (2013, 2026),
     "ratios": [2.769, 2.125, 1.706, 1.462, 1.300, 1.174],
     "front": 15, "rear": 39, "primary": 1.960},

    {"mfr": "mv_agusta", "model": "brutale",   "year": (2001, 2026),
     "ratios": [2.667, 2.000, 1.615, 1.348, 1.174, 1.040],
     "front": 16, "rear": 44, "primary": 1.840},

    {"mfr": "mv_agusta", "model": "dragster",  "year": (2014, 2026),
     "ratios": [2.769, 2.125, 1.706, 1.462, 1.300, 1.174],
     "front": 15, "rear": 43, "primary": 1.960},

    # ── BMW ───────────────────────────────────────────────────────────────────
    {"mfr": "bmw", "model": "s 1000 rr",       "year": (2009, 2026),
     "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
     "front": 17, "rear": 44, "primary": 1.565},

    {"mfr": "bmw", "model": "s 1000 r",        "year": (2014, 2026),
     "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
     "front": 17, "rear": 45, "primary": 1.565},

    {"mfr": "bmw", "model": "s 1000 xr",       "year": (2015, 2026),
     "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
     "front": 17, "rear": 46, "primary": 1.565},

    {"mfr": "bmw", "model": "m 1000 rr",       "year": (2021, 2026),
     "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
     "front": 17, "rear": 44, "primary": 1.565},

    {"mfr": "bmw", "model": "f 900 r",         "year": (2020, 2026),
     "ratios": [2.769, 2.000, 1.579, 1.310, 1.125, 0.966],
     "front": 15, "rear": 45, "primary": 1.700},

    # ── KTM ───────────────────────────────────────────────────────────────────
    {"mfr": "ktm", "model": "super duke 1290", "year": (2014, 2026),
     "ratios": [2.308, 1.722, 1.411, 1.204, 1.060, 0.957],
     "front": 17, "rear": 41, "primary": 1.700},

    {"mfr": "ktm", "model": "super duke 990",  "year": (2005, 2013),
     "ratios": [2.462, 1.857, 1.529, 1.294, 1.125, 1.000],
     "front": 16, "rear": 42, "primary": 1.700},

    {"mfr": "ktm", "model": "duke 890",        "year": (2020, 2026),
     "ratios": [2.625, 1.941, 1.580, 1.346, 1.185, 1.071],
     "front": 15, "rear": 42, "primary": 1.783},

    {"mfr": "ktm", "model": "duke 790",        "year": (2018, 2022),
     "ratios": [2.625, 1.941, 1.580, 1.346, 1.185, 1.071],
     "front": 15, "rear": 42, "primary": 1.783},

    {"mfr": "ktm", "model": "rc 390",          "year": (2014, 2026),
     "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
     "front": 14, "rear": 45, "primary": 2.200},

    # ── Triumph ───────────────────────────────────────────────────────────────
    {"mfr": "triumph", "model": "daytona 675", "year": (2006, 2016),
     "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
     "front": 17, "rear": 43, "primary": 1.952},

    {"mfr": "triumph", "model": "daytona 765", "year": (2020, 2026),
     "ratios": [2.684, 1.947, 1.619, 1.395, 1.250, 1.143],
     "front": 16, "rear": 43, "primary": 1.952},

    {"mfr": "triumph", "model": "speed triple", "year": (2005, 2026),
     "ratios": [2.684, 1.947, 1.619, 1.395, 1.250, 1.143],
     "front": 17, "rear": 43, "primary": 1.952},

    {"mfr": "triumph", "model": "street triple", "year": (2007, 2026),
     "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
     "front": 16, "rear": 43, "primary": 1.952},

    {"mfr": "triumph", "model": "speed twin",  "year": (2019, 2026),
     "ratios": [2.937, 2.187, 1.666, 1.375, 1.164, 0.991],
     "front": 17, "rear": 43, "primary": 1.780},

    # ── Royal Enfield ─────────────────────────────────────────────────────────
    {"mfr": "royal_enfield", "model": "interceptor 650", "year": (2018, 2026),
     "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
     "front": 14, "rear": 43, "primary": 2.000},

    {"mfr": "royal_enfield", "model": "int 650", "year": (2018, 2026),
     "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
     "front": 14, "rear": 43, "primary": 2.000},

    {"mfr": "royal_enfield", "model": "super meteor 650", "year": (2023, 2026),
     "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
     "front": 15, "rear": 43, "primary": 2.000},

    {"mfr": "royal_enfield", "model": "shotgun 650", "year": (2024, 2026),
     "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
     "front": 15, "rear": 43, "primary": 2.000},

    # ── Harley-Davidson ───────────────────────────────────────────────────────
    {"mfr": "harley-davidson", "model": "v-rod", "year": (2002, 2017),
     "ratios": [2.214, 1.607, 1.225, 1.000, 0.824, 0.714],
     "front": 29, "rear": 70, "primary": 1.905},

    {"mfr": "harley-davidson", "model": "vrsca", "year": (2002, 2006),
     "ratios": [2.214, 1.607, 1.225, 1.000, 0.824, 0.714],
     "front": 29, "rear": 70, "primary": 1.905},
]


# ══════════════════════════════════════════════════════════════════
# TIER 2: CATEGORY + DISPLACEMENT DEFAULTS
# ══════════════════════════════════════════════════════════════════

_DEFAULTS: Dict[str, Dict] = {
    # Super-sport 600cc class (inline-4, 6-speed, wide ratios)
    "sport_600": {
        "ratios":  [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front":   16,  "rear": 43,  "primary": 1.900,
        "confidence": 0.40,
    },
    # Super-sport 1000cc class (inline-4, 6-speed, close-ratio)
    "sport_1000": {
        "ratios":  [2.600, 2.000, 1.667, 1.444, 1.296, 1.185],
        "front":   17,  "rear": 42,  "primary": 1.600,
        "confidence": 0.40,
    },
    # Naked middleweight 650-900cc (parallel twin or inline-3)
    "naked_mw": {
        "ratios":  [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front":   15,  "rear": 43,  "primary": 1.850,
        "confidence": 0.38,
    },
    # Naked litre+ (inline-4 or V4)
    "naked_1000": {
        "ratios":  [2.600, 2.000, 1.619, 1.400, 1.250, 1.143],
        "front":   17,  "rear": 43,  "primary": 1.600,
        "confidence": 0.38,
    },
    # Sport-cruiser (V-twin 1000+cc, belt or shaft drive)
    "cruiser_vt": {
        "ratios":  [2.200, 1.600, 1.222, 1.000, 0.833, 0.722],
        "front":   29,  "rear": 68,  "primary": 1.920,
        "confidence": 0.35,
    },
    # Generic 5-speed fallback
    "generic_5": {
        "ratios":  [2.600, 2.000, 1.650, 1.400, 1.250],
        "front":   16,  "rear": 43,  "primary": 1.700,
        "confidence": 0.30,
    },
    # Generic 6-speed fallback
    "generic_6": {
        "ratios":  [2.600, 1.947, 1.619, 1.400, 1.250, 1.148],
        "front":   16,  "rear": 43,  "primary": 1.700,
        "confidence": 0.30,
    },
}


# ══════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════

def lookup_gear_ratios(
    manufacturer: str,
    model_name: str,
    year: Optional[int] = None,
    category: str = "sport",
    displacement_cc: Optional[float] = None,
    gears: Optional[int] = None,
) -> Tuple[List[float], int, int, float, float]:
    """
    Look up gear ratios and sprocket sizes for a given bike.

    Returns (gear_ratios, front_sprocket, rear_sprocket, primary_ratio, confidence)

    The function tries Tier 1 first (named model-family match), then falls back
    to Tier 2 (category + displacement class defaults).

    Parameters
    ----------
    manufacturer   : Manufacturer display name (case-insensitive)
    model_name     : Model name string (case-insensitive; partial match supported)
    year           : Model year (None = any)
    category       : "sport" / "naked" / "cruiser"
    displacement_cc: Engine displacement in cc (used for Tier 2)
    gears          : Number of gears (used for Tier 2 fallback selection)
    """
    # Normalise manufacturer to slug form used in _DB
    mfr_slug = manufacturer.lower().strip().replace(" ", "_")

    # ── Tier 1: named model match ─────────────────────────────────────────────
    model_lower = model_name.lower()

    # Collect all matching entries, prefer longest pattern match
    candidates = []
    for entry in _DB:
        if entry["mfr"] != mfr_slug:
            continue
        pattern = entry["model"].lower()
        if pattern not in model_lower:
            continue
        # Check year range
        if year is not None:
            y_from, y_to = entry["year"]
            if not (y_from <= year <= y_to):
                continue
        candidates.append((len(pattern), entry))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]
        return (
            best["ratios"],
            best.get("front", 16),
            best.get("rear", 43),
            best.get("primary", 1.700),
            0.75,
        )

    # ── Tier 2: category + displacement defaults ──────────────────────────────
    cc = displacement_cc or 0
    key = _pick_default_key(category, cc, gears)
    d = _DEFAULTS[key]
    return (
        d["ratios"],
        d["front"],
        d["rear"],
        d["primary"],
        d["confidence"],
    )


def _pick_default_key(category: str, cc: float, gears: Optional[int]) -> str:
    """Select the best Tier 2 default bucket."""
    if gears == 5:
        return "generic_5"
    if category == "cruiser":
        return "cruiser_vt"
    if category in ("sport", "naked"):
        if cc >= 900:
            return "sport_1000" if category == "sport" else "naked_1000"
        if cc >= 700:
            return "naked_mw"
        if category == "sport":
            return "sport_600"
        return "naked_mw"
    return "generic_6"
