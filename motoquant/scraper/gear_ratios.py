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

_DB: list[dict] = [
    # ── Suzuki ────────────────────────────────────────────────────────────────
    {
        "mfr": "suzuki",
        "model": "gsx-r 600",
        "year": (2001, 2026),
        "ratios": [2.571, 1.944, 1.619, 1.380, 1.238, 1.130],
        "front": 15,
        "rear": 43,
        "primary": 1.795,
    },
    {
        "mfr": "suzuki",
        "model": "gsx-r 750",
        "year": (2000, 2026),
        "ratios": [2.600, 1.944, 1.619, 1.380, 1.238, 1.130],
        "front": 15,
        "rear": 42,
        "primary": 1.795,
    },
    {
        "mfr": "suzuki",
        "model": "gsx-r 1000",
        "year": (2001, 2011),
        "ratios": [2.600, 2.105, 1.750, 1.500, 1.333, 1.200],
        "front": 17,
        "rear": 42,
        "primary": 1.522,
    },
    {
        "mfr": "suzuki",
        "model": "gsx-r 1000",
        "year": (2012, 2026),
        "ratios": [2.571, 1.894, 1.571, 1.381, 1.238, 1.130],
        "front": 17,
        "rear": 45,
        "primary": 1.590,
    },
    {
        "mfr": "suzuki",
        "model": "hayabusa",
        "year": (1999, 2012),
        "ratios": [2.615, 2.062, 1.714, 1.500, 1.333, 1.200],
        "front": 17,
        "rear": 40,
        "primary": 1.543,
    },
    {
        "mfr": "suzuki",
        "model": "hayabusa",
        "year": (2021, 2026),
        "ratios": [2.615, 2.062, 1.714, 1.500, 1.333, 1.200],
        "front": 18,
        "rear": 40,
        "primary": 1.543,
    },
    {
        "mfr": "suzuki",
        "model": "katana",
        "year": (2019, 2026),
        "ratios": [2.571, 1.894, 1.571, 1.381, 1.238, 1.130],
        "front": 17,
        "rear": 45,
        "primary": 1.590,
    },
    {
        "mfr": "suzuki",
        "model": "gsx-s 1000",
        "year": (2015, 2026),
        "ratios": [2.571, 1.894, 1.571, 1.381, 1.238, 1.130],
        "front": 17,
        "rear": 45,
        "primary": 1.590,
    },
    {
        "mfr": "suzuki",
        "model": "gsx-s 750",
        "year": (2017, 2026),
        "ratios": [2.600, 1.944, 1.619, 1.380, 1.238, 1.130],
        "front": 16,
        "rear": 43,
        "primary": 1.795,
    },
    {
        "mfr": "suzuki",
        "model": "sv 650",
        "year": (1999, 2026),
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 15,
        "rear": 44,
        "primary": 1.901,
    },
    {
        "mfr": "suzuki",
        "model": "bandit 1200",
        "year": (2001, 2006),
        "ratios": [2.500, 1.857, 1.529, 1.333, 1.190, 1.095],
        "front": 17,
        "rear": 44,
        "primary": 1.543,
    },
    {
        "mfr": "suzuki",
        "model": "bandit 1250",
        "year": (2007, 2016),
        "ratios": [2.500, 1.857, 1.529, 1.333, 1.190, 1.095],
        "front": 17,
        "rear": 44,
        "primary": 1.543,
    },
    # ── Yamaha ────────────────────────────────────────────────────────────────
    {
        "mfr": "yamaha",
        "model": "yzf-r1",
        "year": (1998, 2003),
        "ratios": [2.684, 1.947, 1.565, 1.350, 1.208, 1.125],
        "front": 17,
        "rear": 45,
        "primary": 1.609,
    },
    {
        "mfr": "yamaha",
        "model": "yzf-r1",
        "year": (2004, 2014),
        "ratios": [2.643, 1.947, 1.619, 1.380, 1.238, 1.130],
        "front": 17,
        "rear": 45,
        "primary": 1.609,
    },
    {
        "mfr": "yamaha",
        "model": "r15 v4",
        "year": (2021, 2026),
        "ratios": [3.533, 2.333, 1.722, 1.357, 1.129, 0.966],
        "front": 17,
        "rear": 42,
        "primary": 1.800,
    },
    {
        "mfr": "yamaha",
        "model": "mt-15 v2",
        "year": (2021, 2026),
        "ratios": [3.533, 2.333, 1.722, 1.357, 1.129, 0.966],
        "front": 17,
        "rear": 42,
        "primary": 1.800,
    },
    {
        "mfr": "yamaha",
        "model": "fz-x",
        "year": (2021, 2026),
        "ratios": [3.500, 1.846, 1.227, 0.923, 0.734, None],
        "front": 16,
        "rear": 48,
        "primary": 2.000,
    },
    {
        "mfr": "yamaha",
        "model": "yzf-r1",
        "year": (2015, 2026),
        "ratios": [2.600, 1.947, 1.619, 1.380, 1.238, 1.130],
        "front": 17,
        "rear": 45,
        "primary": 1.609,
    },
    {
        "mfr": "yamaha",
        "model": "yzf-r6",
        "year": (1999, 2016),
        "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front": 16,
        "rear": 45,
        "primary": 1.854,
    },
    {
        "mfr": "yamaha",
        "model": "yzf-r6",
        "year": (2017, 2022),
        "ratios": [2.714, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front": 16,
        "rear": 45,
        "primary": 1.854,
    },
    {
        "mfr": "yamaha",
        "model": "yzf-r7",
        "year": (2021, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
        "front": 15,
        "rear": 45,
        "primary": 1.866,
    },
    {
        "mfr": "yamaha",
        "model": "mt-10",
        "year": (2016, 2026),
        "ratios": [2.600, 1.947, 1.619, 1.380, 1.238, 1.130],
        "front": 17,
        "rear": 44,
        "primary": 1.609,
    },
    {
        "mfr": "yamaha",
        "model": "mt-09",
        "year": (2013, 2026),
        "ratios": [2.714, 2.000, 1.619, 1.360, 1.200, 1.080],
        "front": 16,
        "rear": 45,
        "primary": 1.861,
    },
    {
        "mfr": "yamaha",
        "model": "mt-07",
        "year": (2014, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
        "front": 15,
        "rear": 45,
        "primary": 1.866,
    },
    {
        "mfr": "yamaha",
        "model": "fz1",
        "year": (2001, 2015),
        "ratios": [2.600, 1.947, 1.619, 1.380, 1.238, 1.130],
        "front": 17,
        "rear": 45,
        "primary": 1.609,
    },
    {
        "mfr": "yamaha",
        "model": "vmax",
        "year": (2009, 2020),
        "ratios": [2.500, 1.714, 1.333, 1.095, 0.967, 0.864],
        "front": 18,
        "rear": 36,
        "primary": 2.000,
    },
    {
        "mfr": "yamaha",
        "model": "xsr900",
        "year": (2016, 2026),
        "ratios": [2.714, 2.000, 1.619, 1.360, 1.200, 1.080],
        "front": 16,
        "rear": 43,
        "primary": 1.861,
    },
    # ── Honda ────────────────────────────────────────────────────────────────
    {
        "mfr": "honda",
        "model": "cbr 1000rr",
        "year": (2004, 2016),
        "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
        "front": 16,
        "rear": 43,
        "primary": 1.733,
    },
    {
        "mfr": "honda",
        "model": "cbr 1000rr",
        "year": (2017, 2026),
        "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
        "front": 16,
        "rear": 41,
        "primary": 1.733,
    },
    {
        "mfr": "honda",
        "model": "cbr 600rr",
        "year": (2003, 2020),
        "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front": 16,
        "rear": 43,
        "primary": 2.117,
    },
    {
        "mfr": "honda",
        "model": "cbr 900rr",
        "year": (1992, 2003),
        "ratios": [2.750, 2.056, 1.706, 1.478, 1.304, 1.190],
        "front": 16,
        "rear": 43,
        "primary": 1.739,
    },
    {
        "mfr": "honda",
        "model": "cbr 954rr",
        "year": (2002, 2003),
        "ratios": [2.750, 2.056, 1.706, 1.478, 1.304, 1.190],
        "front": 16,
        "rear": 43,
        "primary": 1.739,
    },
    {
        "mfr": "honda",
        "model": "cb 1000r",
        "year": (2008, 2026),
        "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
        "front": 17,
        "rear": 42,
        "primary": 1.733,
    },
    {
        "mfr": "honda",
        "model": "cb 650r",
        "year": (2019, 2026),
        "ratios": [3.000, 2.117, 1.667, 1.348, 1.161, 1.038],
        "front": 15,
        "rear": 41,
        "primary": 2.176,
    },
    {
        "mfr": "honda",
        "model": "cb 650f",
        "year": (2014, 2018),
        "ratios": [3.000, 2.117, 1.667, 1.348, 1.161, 1.038],
        "front": 15,
        "rear": 41,
        "primary": 2.176,
    },
    {
        "mfr": "honda",
        "model": "hornet",
        "year": (1998, 2013),
        "ratios": [2.600, 2.052, 1.714, 1.500, 1.333, 1.200],
        "front": 16,
        "rear": 43,
        "primary": 1.733,
    },
    {
        "mfr": "honda",
        "model": "vtr 1000",
        "year": (1997, 2005),
        "ratios": [2.462, 1.823, 1.500, 1.310, 1.166, 1.053],
        "front": 15,
        "rear": 41,
        "primary": 1.807,
    },
    {
        "mfr": "honda",
        "model": "cbr 250r",
        "year": (2011, 2019),
        "ratios": [3.083, 1.947, 1.435, 1.143, 0.971, 0.857],
        "front": 17,
        "rear": 43,
        "primary": 1.900,
    },
    {
        "mfr": "honda",
        "model": "cb 300r",
        "year": (2019, 2026),
        "ratios": [3.133, 1.882, 1.357, 1.037, 0.842, 0.710],
        "front": 17,
        "rear": 41,
        "primary": 1.900,
    },
    {
        "mfr": "honda",
        "model": "hornet 2.0",
        "year": (2020, 2026),
        "ratios": [3.313, 1.842, 1.157, 0.862, 0.688, None],
        "front": 16,
        "rear": 46,
        "primary": 2.000,
    },
    # ── Kawasaki ─────────────────────────────────────────────────────────────
    {
        "mfr": "kawasaki",
        "model": "zx-10r",
        "year": (2004, 2015),
        "ratios": [2.642, 2.000, 1.652, 1.436, 1.296, 1.185],
        "front": 17,
        "rear": 41,
        "primary": 1.612,
    },
    {
        "mfr": "kawasaki",
        "model": "zx-10r",
        "year": (2016, 2026),
        "ratios": [2.567, 1.933, 1.619, 1.400, 1.259, 1.148],
        "front": 17,
        "rear": 41,
        "primary": 1.612,
    },
    {
        "mfr": "kawasaki",
        "model": "zx-6r",
        "year": (2003, 2006),
        "ratios": [2.933, 2.133, 1.785, 1.545, 1.380, 1.259],
        "front": 16,
        "rear": 43,
        "primary": 2.071,
    },
    {
        "mfr": "kawasaki",
        "model": "zx-6r",
        "year": (2007, 2026),
        "ratios": [2.933, 2.133, 1.785, 1.545, 1.380, 1.259],
        "front": 16,
        "rear": 43,
        "primary": 2.071,
    },
    {
        "mfr": "kawasaki",
        "model": "zx-14r",
        "year": (2006, 2021),
        "ratios": [2.294, 1.714, 1.379, 1.138, 0.958, 0.857],
        "front": 17,
        "rear": 37,
        "primary": 1.545,
    },
    {
        "mfr": "kawasaki",
        "model": "ninja h2",
        "year": (2015, 2026),
        "ratios": [2.294, 1.714, 1.379, 1.138, 0.958, 0.857],
        "front": 17,
        "rear": 37,
        "primary": 1.545,
    },
    {
        "mfr": "kawasaki",
        "model": "z1000",
        "year": (2003, 2020),
        "ratios": [2.642, 2.000, 1.652, 1.436, 1.296, 1.185],
        "front": 17,
        "rear": 40,
        "primary": 1.612,
    },
    {
        "mfr": "kawasaki",
        "model": "z900",
        "year": (2017, 2026),
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 15,
        "rear": 41,
        "primary": 1.795,
    },
    {
        "mfr": "kawasaki",
        "model": "z650",
        "year": (2017, 2026),
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 14,
        "rear": 42,
        "primary": 1.795,
    },
    {
        "mfr": "kawasaki",
        "model": "er-6",
        "year": (2006, 2016),
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 15,
        "rear": 46,
        "primary": 1.795,
    },
    {
        "mfr": "kawasaki",
        "model": "ninja 300",
        "year": (2013, 2026),
        "ratios": [3.360, 2.111, 1.542, 1.188, 0.966, 0.811],
        "front": 17,
        "rear": 43,
        "primary": 1.900,
    },
    {
        "mfr": "kawasaki",
        "model": "ninja 400",
        "year": (2018, 2026),
        # Kawasaki Ninja 400 2018 service manual (p. 3-33)
        # Fixed: was erroneously copy-pasted from Ninja 300 entry
        "ratios": [2.846, 2.071, 1.700, 1.441, 1.241, 1.107],
        "front": 15,
        "rear": 46,
        "primary": 3.082,
    },
    # ── Aprilia ───────────────────────────────────────────────────────────────
    {
        "mfr": "aprilia",
        "model": "rsv4",
        "year": (2009, 2026),
        "ratios": [2.615, 2.000, 1.667, 1.444, 1.286, 1.148],
        "front": 15,
        "rear": 38,
        "primary": 1.872,
    },
    {
        "mfr": "aprilia",
        "model": "rs 660",
        "year": (2020, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
        "front": 14,
        "rear": 39,
        "primary": 2.056,
    },
    {
        "mfr": "aprilia",
        "model": "tuono v4",
        "year": (2011, 2026),
        "ratios": [2.615, 2.000, 1.667, 1.444, 1.286, 1.148],
        "front": 15,
        "rear": 39,
        "primary": 1.872,
    },
    {
        "mfr": "aprilia",
        "model": "tuono 660",
        "year": (2021, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.333, 1.167, 1.043],
        "front": 14,
        "rear": 40,
        "primary": 2.056,
    },
    {
        "mfr": "aprilia",
        "model": "rsv 1000",
        "year": (2004, 2009),
        "ratios": [2.769, 2.091, 1.667, 1.391, 1.214, 1.095],
        "front": 15,
        "rear": 38,
        "primary": 1.800,
    },
    {
        "mfr": "aprilia",
        "model": "shiver 900",
        "year": (2017, 2021),
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 16,
        "rear": 46,
        "primary": 1.850,
    },
    # ── Ducati ────────────────────────────────────────────────────────────────
    {
        "mfr": "ducati",
        "model": "panigale v4",
        "year": (2018, 2026),
        "ratios": [2.462, 1.842, 1.500, 1.308, 1.160, 1.043],
        "front": 15,
        "rear": 39,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "panigale v2",
        "year": (2020, 2026),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 38,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "1098",
        "year": (2007, 2009),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 38,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "1198",
        "year": (2009, 2011),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 38,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "999",
        "year": (2003, 2006),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 38,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "749",
        "year": (2003, 2006),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 38,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "streetfighter v4",
        "year": (2020, 2026),
        "ratios": [2.462, 1.842, 1.500, 1.308, 1.160, 1.043],
        "front": 15,
        "rear": 42,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "monster",
        "year": (2003, 2016),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 43,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "monster",
        "year": (2017, 2026),
        "ratios": [2.462, 1.842, 1.500, 1.308, 1.160, 1.043],
        "front": 15,
        "rear": 43,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "hypermotard",
        "year": (2007, 2026),
        "ratios": [2.467, 1.778, 1.444, 1.222, 1.062, 0.951],
        "front": 15,
        "rear": 43,
        "primary": 1.840,
    },
    # ── MV Agusta ─────────────────────────────────────────────────────────────
    {
        "mfr": "mv_agusta",
        "model": "f4",
        "year": (1999, 2018),
        "ratios": [2.667, 2.000, 1.615, 1.348, 1.174, 1.040],
        "front": 16,
        "rear": 41,
        "primary": 1.840,
    },
    {
        "mfr": "mv_agusta",
        "model": "f3 675",
        "year": (2012, 2016),
        "ratios": [2.769, 2.125, 1.706, 1.462, 1.300, 1.174],
        "front": 15,
        "rear": 40,
        "primary": 1.960,
    },
    {
        "mfr": "mv_agusta",
        "model": "f3 800",
        "year": (2013, 2026),
        "ratios": [2.769, 2.125, 1.706, 1.462, 1.300, 1.174],
        "front": 15,
        "rear": 39,
        "primary": 1.960,
    },
    {
        "mfr": "mv_agusta",
        "model": "brutale",
        "year": (2001, 2026),
        "ratios": [2.667, 2.000, 1.615, 1.348, 1.174, 1.040],
        "front": 16,
        "rear": 44,
        "primary": 1.840,
    },
    {
        "mfr": "mv_agusta",
        "model": "dragster",
        "year": (2014, 2026),
        "ratios": [2.769, 2.125, 1.706, 1.462, 1.300, 1.174],
        "front": 15,
        "rear": 43,
        "primary": 1.960,
    },
    # ── BMW ───────────────────────────────────────────────────────────────────
    {
        "mfr": "bmw",
        "model": "s 1000 rr",
        "year": (2009, 2026),
        "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
        "front": 17,
        "rear": 44,
        "primary": 1.565,
    },
    {
        "mfr": "bmw",
        "model": "s 1000 r",
        "year": (2014, 2026),
        "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
        "front": 17,
        "rear": 45,
        "primary": 1.565,
    },
    {
        "mfr": "bmw",
        "model": "s 1000 xr",
        "year": (2015, 2026),
        "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
        "front": 17,
        "rear": 46,
        "primary": 1.565,
    },
    {
        "mfr": "bmw",
        "model": "m 1000 rr",
        "year": (2021, 2026),
        "ratios": [2.640, 1.947, 1.619, 1.395, 1.250, 1.143],
        "front": 17,
        "rear": 44,
        "primary": 1.565,
    },
    {
        "mfr": "bmw",
        "model": "f 900 r",
        "year": (2020, 2026),
        "ratios": [2.769, 2.000, 1.579, 1.310, 1.125, 0.966],
        "front": 15,
        "rear": 45,
        "primary": 1.700,
    },
    # ── KTM ───────────────────────────────────────────────────────────────────
    {
        "mfr": "ktm",
        "model": "super duke 1290",
        "year": (2014, 2026),
        "ratios": [2.308, 1.722, 1.411, 1.204, 1.060, 0.957],
        "front": 17,
        "rear": 41,
        "primary": 1.700,
    },
    {
        "mfr": "ktm",
        "model": "super duke 990",
        "year": (2005, 2013),
        "ratios": [2.462, 1.857, 1.529, 1.294, 1.125, 1.000],
        "front": 16,
        "rear": 42,
        "primary": 1.700,
    },
    {
        "mfr": "ktm",
        "model": "duke 890",
        "year": (2020, 2026),
        "ratios": [2.625, 1.941, 1.580, 1.346, 1.185, 1.071],
        "front": 15,
        "rear": 42,
        "primary": 1.783,
    },
    {
        "mfr": "ktm",
        "model": "duke 790",
        "year": (2018, 2022),
        "ratios": [2.625, 1.941, 1.580, 1.346, 1.185, 1.071],
        "front": 15,
        "rear": 42,
        "primary": 1.783,
    },
    {
        "mfr": "ktm",
        "model": "rc 390",
        "year": (2014, 2026),
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 14,
        "rear": 45,
        "primary": 2.200,
    },
    {
        "mfr": "ktm",
        "model": "duke 390",
        "year": (2017, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 15,
        "rear": 45,
        "primary": 2.200,
    },
    {
        "mfr": "ktm",
        "model": "duke 250",
        "year": (2017, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 14,
        "rear": 45,
        "primary": 2.200,
    },
    {
        "mfr": "ktm",
        "model": "duke 200",
        "year": (2017, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 14,
        "rear": 49,
        "primary": 2.200,
    },
    {
        "mfr": "ktm",
        "model": "rc 200",
        "year": (2022, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 14,
        "rear": 49,
        "primary": 2.200,
    },
    # ── Bajaj ────────────────────────────────────────────────────────────────
    {
        "mfr": "bajaj",
        "model": "pulsar ns 200",
        "year": (2017, 2026),
        "ratios": [2.909, 1.882, 1.350, 1.040, 0.862, 0.774],
        "front": 15,
        "rear": 43,
        "primary": 2.100,
    },
    {
        "mfr": "bajaj",
        "model": "pulsar rs 200",
        "year": (2015, 2026),
        "ratios": [2.909, 1.882, 1.350, 1.040, 0.862, 0.774],
        "front": 15,
        "rear": 43,
        "primary": 2.100,
    },
    {
        "mfr": "bajaj",
        "model": "pulsar 220f",
        "year": (2007, 2026),
        "ratios": [3.500, 1.846, 1.227, 0.923, 0.734, None],
        "front": 16,
        "rear": 50,
        "primary": 2.100,
    },
    {
        "mfr": "bajaj",
        "model": "dominar 400",
        "year": (2019, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 16,
        "rear": 46,
        "primary": 2.100,
    },
    {
        "mfr": "bajaj",
        "model": "dominar 250",
        "year": (2020, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 16,
        "rear": 48,
        "primary": 2.100,
    },
    # ── TVS ──────────────────────────────────────────────────────────────────
    {
        "mfr": "tvs",
        "model": "apache rr 310",
        "year": (2018, 2026),
        "ratios": [3.384, 2.333, 1.769, 1.400, 1.160, 0.961],
        "front": 16,
        "rear": 47,
        "primary": 2.000,
    },
    {
        "mfr": "tvs",
        "model": "apache rtr 200",
        "year": (2016, 2026),
        "ratios": [3.214, 1.947, 1.333, 1.000, 0.800, None],
        "front": 16,
        "rear": 48,
        "primary": 2.000,
    },
    {
        "mfr": "tvs",
        "model": "apache rtr 160",
        "year": (2018, 2026),
        "ratios": [3.182, 1.909, 1.313, 0.987, 0.789, None],
        "front": 16,
        "rear": 48,
        "primary": 2.000,
    },
    # ── Royal Enfield ─────────────────────────────────────────────────────────
    {
        "mfr": "royal_enfield",
        "model": "himalayan 450",
        "year": (2024, 2026),
        "ratios": [3.692, 2.105, 1.526, 1.179, 0.966, 0.814],
        "front": 17,
        "rear": 47,
        "primary": 1.800,
    },
    {
        "mfr": "royal_enfield",
        "model": "continental gt 650",
        "year": (2018, 2026),
        "ratios": [2.531, 1.693, 1.289, 1.054, 0.892, 0.780],
        "front": 14,
        "rear": 37,
        "primary": 2.000,
    },
    # ── Triumph ───────────────────────────────────────────────────────────────
    {
        "mfr": "triumph",
        "model": "daytona 675",
        "year": (2006, 2016),
        "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front": 17,
        "rear": 43,
        "primary": 1.952,
    },
    {
        "mfr": "triumph",
        "model": "daytona 765",
        "year": (2020, 2026),
        "ratios": [2.684, 1.947, 1.619, 1.395, 1.250, 1.143],
        "front": 16,
        "rear": 43,
        "primary": 1.952,
    },
    {
        "mfr": "triumph",
        "model": "speed triple",
        "year": (2005, 2026),
        "ratios": [2.684, 1.947, 1.619, 1.395, 1.250, 1.143],
        "front": 17,
        "rear": 43,
        "primary": 1.952,
    },
    {
        "mfr": "triumph",
        "model": "street triple",
        "year": (2007, 2026),
        "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front": 16,
        "rear": 43,
        "primary": 1.952,
    },
    {
        "mfr": "triumph",
        "model": "speed twin",
        "year": (2019, 2026),
        "ratios": [2.937, 2.187, 1.666, 1.375, 1.164, 0.991],
        "front": 17,
        "rear": 43,
        "primary": 1.780,
    },
    {
        "mfr": "triumph",
        "model": "speed 400",
        "year": (2023, 2026),
        "ratios": [2.900, 2.067, 1.562, 1.240, 1.043, None],
        "front": 14,
        "rear": 41,
        "primary": 1.900,
    },
    # ── Husqvarna ─────────────────────────────────────────────────────────────
    {
        "mfr": "husqvarna",
        "model": "svartpilen 401",
        "year": (2020, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 15,
        "rear": 45,
        "primary": 2.200,
    },
    {
        "mfr": "husqvarna",
        "model": "vitpilen 401",
        "year": (2020, 2026),
        "ratios": [2.846, 2.105, 1.625, 1.300, 1.095, 0.962],
        "front": 15,
        "rear": 45,
        "primary": 2.200,
    },
    # ── Hero ──────────────────────────────────────────────────────────────────
    {
        "mfr": "hero",
        "model": "xtreme 160r",
        "year": (2020, 2026),
        "ratios": [3.500, 1.846, 1.227, 0.923, 0.734, None],
        "front": 16,
        "rear": 50,
        "primary": 2.100,
    },
    # ── Royal Enfield ─────────────────────────────────────────────────────────
    {
        "mfr": "royal_enfield",
        "model": "interceptor 650",
        "year": (2018, 2026),
        "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
        "front": 14,
        "rear": 43,
        "primary": 2.000,
    },
    {
        "mfr": "royal_enfield",
        "model": "int 650",
        "year": (2018, 2026),
        "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
        "front": 14,
        "rear": 43,
        "primary": 2.000,
    },
    {
        "mfr": "royal_enfield",
        "model": "super meteor 650",
        "year": (2023, 2026),
        "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
        "front": 15,
        "rear": 43,
        "primary": 2.000,
    },
    {
        "mfr": "royal_enfield",
        "model": "shotgun 650",
        "year": (2024, 2026),
        "ratios": [2.923, 2.058, 1.605, 1.333, 1.158, 1.000],
        "front": 15,
        "rear": 43,
        "primary": 2.000,
    },
    # ── Harley-Davidson ───────────────────────────────────────────────────────
    {
        "mfr": "harley-davidson",
        "model": "v-rod",
        "year": (2002, 2017),
        "ratios": [2.214, 1.607, 1.225, 1.000, 0.824, 0.714],
        "front": 29,
        "rear": 70,
        "primary": 1.905,
    },
    {
        "mfr": "harley-davidson",
        "model": "vrsca",
        "year": (2002, 2006),
        "ratios": [2.214, 1.607, 1.225, 1.000, 0.824, 0.714],
        "front": 29,
        "rear": 70,
        "primary": 1.905,
    },
    # ── International Expansion (April 2026) ─────────────────────────────────
    # Yamaha
    {
        "mfr": "yamaha",
        "model": "yzf-r7",
        "year": (2022, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.300, 1.090, 0.964],
        "front": 16,
        "rear": 43,
        "primary": 1.955,
    },
    {
        "mfr": "yamaha",
        "model": "xsr900",
        "year": (2022, 2026),
        "ratios": [2.666, 2.000, 1.619, 1.333, 1.111, 0.966],
        "front": 16,
        "rear": 45,
        "primary": 1.680,
    },
    {
        "mfr": "yamaha",
        "model": "vmax",
        "year": (2009, 2020),
        "ratios": [2.294, 1.555, 1.217, 1.000, 0.806],
        "front": 18,
        "rear": 46,
        "primary": 1.680,
    },
    # Honda
    {
        "mfr": "honda",
        "model": "cb650r",
        "year": (2019, 2025),
        "ratios": [2.571, 1.944, 1.590, 1.333, 1.153, 1.035],
        "front": 15,
        "rear": 42,
        "primary": 1.822,
    },
    {
        "mfr": "honda",
        "model": "cbr500r",
        "year": (2013, 2026),
        "ratios": [3.285, 2.105, 1.600, 1.300, 1.090, 0.967],
        "front": 15,
        "rear": 41,
        "primary": 2.029,
    },
    {
        "mfr": "honda",
        "model": "rebel 1100",
        "year": (2021, 2026),
        "ratios": [2.562, 1.894, 1.454, 1.181, 0.969, 0.827],
        "front": 16,
        "rear": 40,
        "primary": 1.730,
    },
    # Kawasaki
    {
        "mfr": "kawasaki",
        "model": "zx-4r",
        "year": (2023, 2026),
        "ratios": [3.090, 2.437, 1.904, 1.560, 1.347, 1.208],
        "front": 14,
        "rear": 46,
        "primary": 2.045,
    },
    {
        "mfr": "kawasaki",
        "model": "z h2",
        "year": (2020, 2025),
        "ratios": [2.600, 2.000, 1.667, 1.444, 1.296, 1.185],
        "front": 16,
        "rear": 42,
        "primary": 1.590,
    },
    {
        "mfr": "kawasaki",
        "model": "vulcan s",
        "year": (2015, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.300, 1.090, 0.964],
        "front": 15,
        "rear": 46,
        "primary": 1.858,
    },
    # Suzuki
    {
        "mfr": "suzuki",
        "model": "sv650",
        "year": (2016, 2026),
        "ratios": [2.562, 1.894, 1.454, 1.181, 0.969, 0.827],
        "front": 15,
        "rear": 46,
        "primary": 2.088,
    },
    {
        "mfr": "suzuki",
        "model": "gsx-8s",
        "year": (2023, 2026),
        "ratios": [2.416, 1.764, 1.380, 1.125, 0.961, 0.851],
        "front": 14,
        "rear": 46,
        "primary": 2.029,
    },
    {
        "mfr": "suzuki",
        "model": "katana",
        "year": (2019, 2024),
        "ratios": [2.562, 1.947, 1.636, 1.416, 1.260, 1.136],
        "front": 17,
        "rear": 44,
        "primary": 1.553,
    },
    # Ducati
    {
        "mfr": "ducati",
        "model": "panigale v4r",
        "year": (2019, 2025),
        "ratios": [2.466, 2.066, 1.762, 1.545, 1.380, 1.260],
        "front": 16,
        "rear": 39,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "diavel v4",
        "year": (2023, 2026),
        "ratios": [2.466, 1.944, 1.545, 1.333, 1.178, 1.062],
        "front": 17,
        "rear": 44,
        "primary": 1.840,
    },
    {
        "mfr": "ducati",
        "model": "scrambler 1100",
        "year": (2018, 2024),
        "ratios": [2.466, 1.764, 1.353, 1.100, 0.952, 0.846],
        "front": 15,
        "rear": 45,
        "primary": 1.840,
    },
    # Triumph
    {
        "mfr": "triumph",
        "model": "rocket 3",
        "year": (2020, 2026),
        "ratios": [2.352, 1.750, 1.368, 1.130, 0.974, 0.843],
        "front": 18,
        "rear": 47,
        "primary": 1.640,
    },
    {
        "mfr": "triumph",
        "model": "trident 660",
        "year": (2021, 2026),
        "ratios": [2.615, 2.000, 1.590, 1.318, 1.128, 1.000],
        "front": 14,
        "rear": 45,
        "primary": 1.740,
    },
    {
        "mfr": "triumph",
        "model": "tiger 900",
        "year": (2020, 2026),
        "ratios": [2.615, 1.952, 1.555, 1.285, 1.096, 0.952],
        "front": 16,
        "rear": 44,
        "primary": 1.740,
    },
    # BMW
    {
        "mfr": "bmw",
        "model": "r 1250 gs",
        "year": (2019, 2025),
        "ratios": [2.438, 1.714, 1.296, 1.059, 0.909, 0.811],
        "front": 0,
        "rear": 0,
        "primary": 1.588,
    },
    {
        "mfr": "bmw",
        "model": "m 1000 r",
        "year": (2023, 2026),
        "ratios": [2.529, 2.058, 1.714, 1.476, 1.304, 1.173],
        "front": 17,
        "rear": 45,
        "primary": 1.524,
    },
    # Aprilia
    {
        "mfr": "aprilia",
        "model": "rs 660",
        "year": (2021, 2026),
        "ratios": [2.687, 2.062, 1.647, 1.368, 1.173, 1.037],
        "front": 15,
        "rear": 43,
        "primary": 1.750,
    },
    {
        "mfr": "aprilia",
        "model": "tuono 660",
        "year": (2021, 2026),
        "ratios": [2.687, 2.062, 1.647, 1.368, 1.173, 1.037],
        "front": 15,
        "rear": 43,
        "primary": 1.750,
    },
    # MV Agusta
    {
        "mfr": "mv agusta",
        "model": "f3 800",
        "year": (2014, 2025),
        "ratios": [2.583, 2.000, 1.666, 1.400, 1.230, 1.100],
        "front": 16,
        "rear": 41,
        "primary": 1.815,
    },
    # Harley-Davidson (Milwaukee-Eight 117ci / belt drive)
    {
        "mfr": "harley-davidson",
        "model": "low rider",
        "year": (2022, 2026),
        "ratios": [3.627, 2.279, 1.585, 1.250, 1.000, 0.840],
        "front": 34,
        "rear": 66,
        "primary": 1.000,
    },
    {
        "mfr": "harley-davidson",
        "model": "road glide",
        "year": (2023, 2026),
        "ratios": [3.627, 2.279, 1.585, 1.250, 1.000, 0.840],
        "front": 34,
        "rear": 66,
        "primary": 1.000,
    },
    # CFMoto
    {
        "mfr": "cfmoto",
        "model": "700cl-x",
        "year": (2022, 2026),
        "ratios": [2.846, 2.125, 1.631, 1.300, 1.090, 0.964],
        "front": 16,
        "rear": 43,
        "primary": 1.750,
    },
    # Benelli
    {
        "mfr": "benelli",
        "model": "tnt 600",
        "year": (2014, 2024),
        "ratios": [2.750, 2.062, 1.647, 1.380, 1.178, 1.045],
        "front": 16,
        "rear": 46,
        "primary": 1.850,
    },
    {
        "mfr": "benelli",
        "model": "leoncino 500",
        "year": (2018, 2026),
        "ratios": [2.833, 2.062, 1.550, 1.272, 1.083, 0.967],
        "front": 14,
        "rear": 44,
        "primary": 1.950,
    },
    # QJ Motor
    {
        "mfr": "qj motor",
        "model": "srk 400",
        "year": (2022, 2026),
        "ratios": [2.833, 2.062, 1.550, 1.272, 1.083, 0.967],
        "front": 14,
        "rear": 45,
        "primary": 1.950,
    },
]


# ══════════════════════════════════════════════════════════════════
# TIER 2: CATEGORY + DISPLACEMENT DEFAULTS
# ══════════════════════════════════════════════════════════════════

_DEFAULTS: dict[str, dict] = {
    # Super-sport 600cc class (inline-4, 6-speed, wide ratios)
    "sport_600": {
        "ratios": [2.750, 2.000, 1.667, 1.444, 1.304, 1.208],
        "front": 16,
        "rear": 43,
        "primary": 1.900,
        "confidence": 0.40,
    },
    # Super-sport 1000cc class (inline-4, 6-speed, close-ratio)
    "sport_1000": {
        "ratios": [2.600, 2.000, 1.667, 1.444, 1.296, 1.185],
        "front": 17,
        "rear": 42,
        "primary": 1.600,
        "confidence": 0.40,
    },
    # Naked middleweight 650-900cc (parallel twin or inline-3)
    "naked_mw": {
        "ratios": [2.600, 1.882, 1.562, 1.333, 1.192, 1.095],
        "front": 15,
        "rear": 43,
        "primary": 1.850,
        "confidence": 0.38,
    },
    # Naked litre+ (inline-4 or V4)
    "naked_1000": {
        "ratios": [2.600, 2.000, 1.619, 1.400, 1.250, 1.143],
        "front": 17,
        "rear": 43,
        "primary": 1.600,
        "confidence": 0.38,
    },
    # Sport-cruiser (V-twin 1000+cc, belt or shaft drive)
    "cruiser_vt": {
        "ratios": [2.200, 1.600, 1.222, 1.000, 0.833, 0.722],
        "front": 29,
        "rear": 68,
        "primary": 1.920,
        "confidence": 0.35,
    },
    # Adventure / ADV 800-1250cc (parallel twin or boxer, wide ratios for off-road)
    "adventure": {
        "ratios": [2.538, 1.833, 1.428, 1.172, 1.000, 0.882],
        "front": 16,
        "rear": 44,
        "primary": 1.640,
        "confidence": 0.35,
    },
    # Touring 1600-2000cc (V-twin, long legs, overdrive top gear)
    "touring": {
        "ratios": [3.627, 2.279, 1.585, 1.250, 1.000, 0.840],
        "front": 34,
        "rear": 66,
        "primary": 1.000,
        "confidence": 0.30,
    },
    # Generic 5-speed fallback
    "generic_5": {
        "ratios": [2.600, 2.000, 1.650, 1.400, 1.250],
        "front": 16,
        "rear": 43,
        "primary": 1.700,
        "confidence": 0.30,
    },
    # Generic 6-speed fallback
    "generic_6": {
        "ratios": [2.600, 1.947, 1.619, 1.400, 1.250, 1.148],
        "front": 16,
        "rear": 43,
        "primary": 1.700,
        "confidence": 0.30,
    },
}


# ══════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════


def lookup_gear_ratios(
    manufacturer: str,
    model_name: str,
    year: int | None = None,
    category: str = "sport",
    displacement_cc: float | None = None,
    gears: int | None = None,
) -> tuple[list[float], int, int, float, float]:
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


def _pick_default_key(
    category: str, displacement_cc: float, gears: int | None
) -> str:
    """
    Pick the appropriate Tier-2 default key based on category and displacement.

    Returns a key into _DEFAULTS that best matches the bike characteristics.
    """
    category_lower = (category or "sport").lower()

    # Defaults by category
    if category_lower in ("sport", "supersport", "hypersport"):
        if displacement_cc >= 900:
            return "sport_1000"
        else:
            return "sport_600"
    elif category_lower in ("cruiser", "touring_cruiser", "harley"):
        return "cruiser_vt"
    elif category_lower in ("naked", "streetfighter", "standard", "urban", "adventure"):
        if displacement_cc >= 800:
            return "naked_1000"
        else:
            return "naked_mw"
    elif category_lower in ("scrambler", "cafe_racer", "retro"):
        return "naked_mw"
    else:
        # Fallback based on gears
        if gears == 5:
            return "generic_5"
        else:
            return "generic_6"
