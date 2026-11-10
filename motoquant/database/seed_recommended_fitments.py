"""
Recommended and drag_prep tire fitments for MotoQuant (~230 fitments total).

This module defines 230+ additional tire fitments beyond OEM, including popular
sport-touring/track upgrades (recommended) and drag-prep configurations.
"""

import logging

RECOMMENDED_FITMENTS = [
    # Litre superbikes - recommended upgrades (R1, GSX-R 1000, ZX-10R, S1000RR, CBR1000RR, Panigale, RSV4)
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Sport-touring upgrade, OEM alternative",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power GP2"},
        "fitment_type": "recommended",
        "notes": "Race-compound alternative",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 1000"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Racing R11",
        },
        "fitment_type": "recommended",
        "notes": "Track-focused upgrade",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-10R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Sportmax GP-A Pro"},
        "fitment_type": "recommended",
        "notes": "High-performance race tire",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S 1000 RR"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SP V4",
        },
        "fitment_type": "recommended",
        "notes": "Supercorsa race tire",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR1000RR"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Cup 2"},
        "fitment_type": "recommended",
        "notes": "Track-day specific compound",
    },
    {
        "bike_match": {"manufacturer": "Ducati", "model_keywords": ["Panigale V4"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SC2",
        },
        "fitment_type": "recommended",
        "notes": "Race-prepped rear tire",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RSV4"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Hypersport S23",
        },
        "fitment_type": "recommended",
        "notes": "Street-legal race compound",
    },
    # 600cc sport recommended
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["YZF-R6"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Mid-range sport upgrade",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-6R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power 5"},
        "fitment_type": "recommended",
        "notes": "Sport-touring tire",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 600"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Hypersport S22",
        },
        "fitment_type": "recommended",
        "notes": "Street-legal compound",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR600RR"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Sportmax Q4"},
        "fitment_type": "recommended",
        "notes": "Track-focused upgrade",
    },
    # Naked/Streetfighter recommended
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["MT-09"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Streetfighter upgrade",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Z900"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 3"},
        "fitment_type": "recommended",
        "notes": "Middle-ground compound",
    },
    {
        "bike_match": {
            "manufacturer": "Ducati",
            "model_keywords": ["Streetfighter V4"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso II"},
        "fitment_type": "recommended",
        "notes": "Sport-touring compound",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S1000R"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Continental",
            "model_name": "ContiSportAttack 4",
        },
        "fitment_type": "recommended",
        "notes": "All-weather upgrade",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Speed Triple"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 5"},
        "fitment_type": "recommended",
        "notes": "Street-legal sportive tire",
    },
    # Sport-touring recommended
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Hayabusa"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax T32"},
        "fitment_type": "recommended",
        "notes": "Long-distance compound",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-14R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Road 6"},
        "fitment_type": "recommended",
        "notes": "Sport-touring standard",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["FJR1300"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Roadsmart IV"},
        "fitment_type": "recommended",
        "notes": "All-weather all-terrain",
    },
    # Adventure recommended
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["R 1250 GS"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Scorpion Trail 2"},
        "fitment_type": "recommended",
        "notes": "Adventure-specific compound",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["Africa Twin"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Adventurecross AX41S",
        },
        "fitment_type": "recommended",
        "notes": "True dual-sport tire",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Tiger 900"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Anakee Adventure"},
        "fitment_type": "recommended",
        "notes": "Mixed terrain compound",
    },
    # 300-650cc mid-cc recommended
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Ninja 400"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Spirited riding tire",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R3"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 3"},
        "fitment_type": "recommended",
        "notes": "Entry sport upgrade",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["RC 390"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Hypersport S22",
        },
        "fitment_type": "recommended",
        "notes": "Lightweight sport compound",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS 660"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso II"},
        "fitment_type": "recommended",
        "notes": "Mid-sport tier upgrade",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["SV650"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 3"},
        "fitment_type": "recommended",
        "notes": "V-twin classic compound",
    },
    # Indian 150-250cc recommended
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R15"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz FC1"},
        "fitment_type": "recommended",
        "notes": "Indian sport-commuter upgrade",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar NS 200"]},
        "position": "rear",
        "tire_match": {"manufacturer": "CEAT", "model_name": "Zoom Sport"},
        "fitment_type": "recommended",
        "notes": "Indian-market sport option",
    },
    {
        "bike_match": {"manufacturer": "TVS", "model_keywords": ["Apache RR 310"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper"},
        "fitment_type": "recommended",
        "notes": "Entry-level sport upgrade",
    },
    # Indian 250-400cc recommended
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 390"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Sport-enthusiast compound",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Interceptor 650"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "recommended",
        "notes": "Parallel-twin cruiser tire",
    },
    # Cruiser recommended
    {
        "bike_match": {
            "manufacturer": "Harley-Davidson",
            "model_keywords": ["Iron 883"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome AV92"},
        "fitment_type": "recommended",
        "notes": "Cruiser classic compound",
    },
    {
        "bike_match": {"manufacturer": "Indian", "model_keywords": ["Scout"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax"},
        "fitment_type": "recommended",
        "notes": "Modern cruiser compound",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Bonneville"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Night Dragon"},
        "fitment_type": "recommended",
        "notes": "British cruiser heritage",
    },
    # Small-cc commuter recommended
    {
        "bike_match": {"manufacturer": "Hero", "model_keywords": ["Splendor", "Shine"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper"},
        "fitment_type": "recommended",
        "notes": "Commuter standard upgrade",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CB150"]},
        "position": "rear",
        "tire_match": {"manufacturer": "CEAT", "model_name": "Gripp"},
        "fitment_type": "recommended",
        "notes": "Indian commuter utility",
    },
    # SE Asia underbones recommended
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["RS150"]},
        "position": "rear",
        "tire_match": {"manufacturer": "IRC", "model_name": "GP-110"},
        "fitment_type": "recommended",
        "notes": "SE Asia underbone sport",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["Y15ZR"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Street"},
        "fitment_type": "recommended",
        "notes": "Thai commuter-sport tire",
    },
    # ===== DRAG_PREP FITMENTS (80+ entries) =====
    # Litre+ drag_prep
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Slick 2"},
        "fitment_type": "drag_prep",
        "notes": "Dedicated drag slick",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 1000"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Mickey Thompson", "model_name": "ET Drag R"},
        "fitment_type": "drag_prep",
        "notes": "Street-legal drag slick",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-10R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Drag-prepped rubber",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S 1000 RR"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Track slick alternative",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR1000RR"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Dunlop",
            "model_name": "Drag Radial D212 GP Pro",
        },
        "fitment_type": "drag_prep",
        "notes": "Dunlop drag radial",
    },
    {
        "bike_match": {"manufacturer": "Ducati", "model_keywords": ["Panigale V4"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Slick 2"},
        "fitment_type": "drag_prep",
        "notes": "Pure drag compound",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RSV4"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Drag-prepped compound",
    },
    {
        "bike_match": {"manufacturer": "Harley-Davidson", "model_keywords": ["Street"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Mickey Thompson", "model_name": "ET Drag R"},
        "fitment_type": "drag_prep",
        "notes": "Cruiser drag tire",
    },
    # 600cc drag_prep
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["YZF-R6"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Mid-displacement drag tire",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-6R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Sport drag compound",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 600"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Hoosier", "model_name": "Quick Time Pro DOT"},
        "fitment_type": "drag_prep",
        "notes": "Hoosier drag radial",
    },
    # 300-650cc drag_prep
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Ninja 400"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Entry drag tire",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R3"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Lightweight drag compound",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["RC 390"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Sportier 390 slick",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS 660"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Slick 2"},
        "fitment_type": "drag_prep",
        "notes": "600-class drag tire",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["SV650"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Twin drag classic",
    },
    # Indian drag_prep
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R15"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Indian drag spec tire",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar NS 200"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Street-legal drag tire",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 390"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "390 drag upgrade",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Interceptor 650"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Parallel-twin drag prep",
    },
    # 2-stroke & cruiser drag_prep
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RD350", "RX100"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Vintage 2T drag tire",
    },
    {
        "bike_match": {"manufacturer": "Harley-Davidson", "model_keywords": ["Street"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome AV92"},
        "fitment_type": "drag_prep",
        "notes": "Cruiser drag rubber",
    },
    {
        "bike_match": {"manufacturer": "Indian", "model_keywords": ["Scout"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Modern cruiser drag tire",
    },
    # Additional drag_prep for more bikes
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Speed Triple"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Slick 2"},
        "fitment_type": "drag_prep",
        "notes": "Street-legal drag tire",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S1000R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Naked drag option",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CB150"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Entry commuter drag",
    },
    # ═══ EXPANSION (Apr 27, 2026): Front-tire counterparts + new segment depth ═══
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Front sport-touring",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power GP2"},
        "fitment_type": "recommended",
        "notes": "Front race compound",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 1000"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Racing R11",
        },
        "fitment_type": "recommended",
        "notes": "Front track-focused",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-10R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Sportmax GP-A Pro"},
        "fitment_type": "recommended",
        "notes": "Front race tire",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S 1000 RR"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SP V4",
        },
        "fitment_type": "recommended",
        "notes": "Front Supercorsa",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR1000RR"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Cup 2"},
        "fitment_type": "recommended",
        "notes": "Front track-day",
    },
    {
        "bike_match": {"manufacturer": "Ducati", "model_keywords": ["Panigale V4"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SC2",
        },
        "fitment_type": "recommended",
        "notes": "Front race-prepped",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RSV4"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Hypersport S23",
        },
        "fitment_type": "recommended",
        "notes": "Front race-street",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["YZF-R6"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Front mid-sport",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-6R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power 5"},
        "fitment_type": "recommended",
        "notes": "Front sport-touring",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 600"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Hypersport S22",
        },
        "fitment_type": "recommended",
        "notes": "Front street-legal",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR600RR"]},
        "position": "front",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Sportmax Q4"},
        "fitment_type": "recommended",
        "notes": "Front track-focused",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["MT-09"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Front streetfighter",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Z900"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 3"},
        "fitment_type": "recommended",
        "notes": "Front mid-compound",
    },
    {
        "bike_match": {
            "manufacturer": "Ducati",
            "model_keywords": ["Streetfighter V4"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso II"},
        "fitment_type": "recommended",
        "notes": "Front sport-touring",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S1000R"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Continental",
            "model_name": "ContiSportAttack 4",
        },
        "fitment_type": "recommended",
        "notes": "Front all-weather",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Speed Triple"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 5"},
        "fitment_type": "recommended",
        "notes": "Front sportive",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Hayabusa"]},
        "position": "front",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax T32"},
        "fitment_type": "recommended",
        "notes": "Front long-distance",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-14R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Road 6"},
        "fitment_type": "recommended",
        "notes": "Front sport-touring",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["FJR1300"]},
        "position": "front",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Roadsmart IV"},
        "fitment_type": "recommended",
        "notes": "Front all-weather",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["R 1250 GS"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Scorpion Trail 2"},
        "fitment_type": "recommended",
        "notes": "Front adventure",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["Africa Twin"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Adventurecross AX41S",
        },
        "fitment_type": "recommended",
        "notes": "Front dual-sport",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Tiger 900"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Anakee Adventure"},
        "fitment_type": "recommended",
        "notes": "Front mixed-terrain",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Ninja 400"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Front spirited",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R3"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 3"},
        "fitment_type": "recommended",
        "notes": "Front entry-sport",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["RC 390"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Hypersport S22",
        },
        "fitment_type": "recommended",
        "notes": "Front lightweight",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS 660"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso II"},
        "fitment_type": "recommended",
        "notes": "Front mid-sport",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["SV650"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Power 3"},
        "fitment_type": "recommended",
        "notes": "Front V-twin",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R15"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz FC1"},
        "fitment_type": "recommended",
        "notes": "Front Indian-sport",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar NS 200"]},
        "position": "front",
        "tire_match": {"manufacturer": "CEAT", "model_name": "Zoom Sport"},
        "fitment_type": "recommended",
        "notes": "Front Indian-market",
    },
    {
        "bike_match": {"manufacturer": "TVS", "model_keywords": ["Apache RR 310"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper"},
        "fitment_type": "recommended",
        "notes": "Front entry-sport",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 390"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Front sport-enthusiast",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Interceptor 650"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "recommended",
        "notes": "Front parallel-twin",
    },
    {
        "bike_match": {
            "manufacturer": "Harley-Davidson",
            "model_keywords": ["Iron 883"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome AV92"},
        "fitment_type": "recommended",
        "notes": "Front cruiser-classic",
    },
    {
        "bike_match": {"manufacturer": "Indian", "model_keywords": ["Scout"]},
        "position": "front",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax"},
        "fitment_type": "recommended",
        "notes": "Front modern-cruiser",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Bonneville"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Night Dragon"},
        "fitment_type": "recommended",
        "notes": "Front British-heritage",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["RS150"]},
        "position": "front",
        "tire_match": {"manufacturer": "IRC", "model_name": "GP-110"},
        "fitment_type": "recommended",
        "notes": "Front underbone-sport",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["Y15ZR"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Street"},
        "fitment_type": "recommended",
        "notes": "Front Thai-commuter",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Hayabusa"]},
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "AM23A Drag Radial"},
        "fitment_type": "drag_prep",
        "notes": "Front drag-radial",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-14R"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Continental",
            "model_name": "ContiRaceAttack Comp Soft",
        },
        "fitment_type": "drag_prep",
        "notes": "Front street-drag",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["YZF-R6"]},
        "position": "front",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Front mid-displacement",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-6R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Front sport-drag",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 600"]},
        "position": "front",
        "tire_match": {"manufacturer": "Hoosier", "model_name": "Quick Time Pro DOT"},
        "fitment_type": "drag_prep",
        "notes": "Front Hoosier drag",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Ninja 400"]},
        "position": "front",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Front entry-drag",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R3"]},
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Front lightweight-drag",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["RC 390"]},
        "position": "front",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Front 390 slick",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS 660"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power Slick 2"},
        "fitment_type": "drag_prep",
        "notes": "Front 600-class drag",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["SV650"]},
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "Front twin-drag",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R15"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Front Indian-drag",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar NS 200"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz EF1 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Front Indian-drag",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SC1",
        },
        "fitment_type": "drag_prep",
        "notes": "Front race-soft",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S 1000 RR"]},
        "position": "front",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "R11 Race"},
        "fitment_type": "drag_prep",
        "notes": "Front race-spec",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 1000"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Superbike SC1"},
        "fitment_type": "drag_prep",
        "notes": "Front race-soft",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-10R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "KR461 Race"},
        "fitment_type": "drag_prep",
        "notes": "Front race-spec",
    },
    {
        "bike_match": {"manufacturer": "TVS", "model_keywords": ["Apache RTR 200"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Apollo", "model_name": "Alpha H1"},
        "fitment_type": "recommended",
        "notes": "Indian sport-commuter",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar 220"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Indian sport-tourer",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar RS 200"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Angel City"},
        "fitment_type": "recommended",
        "notes": "Indian fairing-sport",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Dominar 400"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "REVZ Y"},
        "fitment_type": "recommended",
        "notes": "Indian sport-tourer",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 200"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "ContiGo"},
        "fitment_type": "recommended",
        "notes": "Indian streetfighter",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 250"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Angel City"},
        "fitment_type": "recommended",
        "notes": "Indian sport-naked",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["FZ 25"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Indian quarter-sport",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR 250R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Revz Y"},
        "fitment_type": "recommended",
        "notes": "Indian entry-fairing",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CB 300R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Angel City"},
        "fitment_type": "recommended",
        "notes": "Indian neo-retro",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Gixxer SF 250"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Indian quarter-fairing",
    },
    {
        "bike_match": {"manufacturer": "Hero", "model_keywords": ["Karizma"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Apollo", "model_name": "Alpha H1"},
        "fitment_type": "recommended",
        "notes": "Indian-classic sport",
    },
    {
        "bike_match": {"manufacturer": "Hero", "model_keywords": ["Xtreme 160"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper FY"},
        "fitment_type": "recommended",
        "notes": "Indian streetfighter",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Classic 350"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Cruiser tourer",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Classic 350"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Night Dragon"},
        "fitment_type": "recommended",
        "notes": "RE-cruiser premium",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Meteor 350"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Nylogrip Plus"},
        "fitment_type": "recommended",
        "notes": "Cruiser-commuter",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Hunter 350"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper FY"},
        "fitment_type": "recommended",
        "notes": "Roadster compact",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Continental GT 650"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Phantom Sportscomp"},
        "fitment_type": "recommended",
        "notes": "Cafe-racer sport",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Himalayan"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Scorpion Rally STR"},
        "fitment_type": "recommended",
        "notes": "Adventure-tourer",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Scram 411"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Crossover dual",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Guerrilla 450"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Roadster modern",
    },
    {
        "bike_match": {
            "manufacturer": "Harley-Davidson",
            "model_keywords": ["Street Bob"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "American Elite"},
        "fitment_type": "recommended",
        "notes": "American cruiser",
    },
    {
        "bike_match": {
            "manufacturer": "Harley-Davidson",
            "model_keywords": ["Road Glide"],
        },
        "position": "rear",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Exedra G852",
        },
        "fitment_type": "recommended",
        "notes": "Bagger touring",
    },
    {
        "bike_match": {
            "manufacturer": "Harley-Davidson",
            "model_keywords": ["Low Rider"],
        },
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome AV92"},
        "fitment_type": "recommended",
        "notes": "Cruiser classic",
    },
    {
        "bike_match": {"manufacturer": "Indian", "model_keywords": ["Pursuit"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "ConmiTour"},
        "fitment_type": "recommended",
        "notes": "Bagger long-haul",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Speed Twin"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Phantom Sportscomp"},
        "fitment_type": "recommended",
        "notes": "Modern-classic",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Rocket 3"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome AV92"},
        "fitment_type": "recommended",
        "notes": "Triple muscle",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Bonneville"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "Conti Twins"},
        "fitment_type": "recommended",
        "notes": "Heritage-classic",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RD350"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "recommended",
        "notes": "Vintage 2T classic",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RX100"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Nylogrip Plus"},
        "fitment_type": "recommended",
        "notes": "Indian vintage 2T",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RX135"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper FY"},
        "fitment_type": "recommended",
        "notes": "Indian vintage 2T",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RD400"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "Conti Twins"},
        "fitment_type": "recommended",
        "notes": "Vintage 2T sport",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["RGV250"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "BT-46"},
        "fitment_type": "recommended",
        "notes": "GP-replica street",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS125"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Activ"},
        "fitment_type": "recommended",
        "notes": "Italian small-2T",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["300 EXC"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Scorpion Rally STR"},
        "fitment_type": "recommended",
        "notes": "Enduro all-terrain",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["Winner X"]},
        "position": "rear",
        "tire_match": {"manufacturer": "IRC", "model_name": "Road Winner"},
        "fitment_type": "recommended",
        "notes": "Vietnamese sport-cub",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["Sonic 150"]},
        "position": "rear",
        "tire_match": {"manufacturer": "FDR", "model_name": "Genzi 2"},
        "fitment_type": "recommended",
        "notes": "Indonesian sport-cub",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR150R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Street Radial"},
        "fitment_type": "recommended",
        "notes": "Thai sport-fairing",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["Exciter 155"]},
        "position": "rear",
        "tire_match": {"manufacturer": "IRC", "model_name": "GP-110"},
        "fitment_type": "recommended",
        "notes": "Thai underbone-sport",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R25"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Street Radial"},
        "fitment_type": "recommended",
        "notes": "Indonesian quarter-sport",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-25R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax S22"},
        "fitment_type": "recommended",
        "notes": "Thai I4 quarter-sport",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Ninja RR Mono"]},
        "position": "rear",
        "tire_match": {"manufacturer": "IRC", "model_name": "GP-110"},
        "fitment_type": "recommended",
        "notes": "Indonesian small-sport",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["390 Adventure"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Mid-adventure crossover",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["G310GS"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Entry-adventure",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["Hornet"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso II"},
        "fitment_type": "recommended",
        "notes": "Streetfighter mid",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["V-Strom 250"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Quarter-adventure",
    },
    {
        "bike_match": {"manufacturer": "Hero", "model_keywords": ["XPulse"]},
        "position": "rear",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip"},
        "fitment_type": "recommended",
        "notes": "Indian dual-sport",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Z650"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power 5"},
        "fitment_type": "recommended",
        "notes": "Mid-naked sport-touring",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["MT-07"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Twin-naked",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CB650R"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Continental",
            "model_name": "ContiSportAttack 4",
        },
        "fitment_type": "recommended",
        "notes": "Mid-classic naked",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-S1000"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "S22"},
        "fitment_type": "recommended",
        "notes": "Liter-naked sport",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Katana"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Modern-classic",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Hayabusa"]},
        "position": "rear",
        "tire_match": {"manufacturer": "M&H", "model_name": "Racemaster 5.5/18"},
        "fitment_type": "drag_prep",
        "notes": "Top-tier drag tire",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-14R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Mickey Thompson", "model_name": "ET Drag"},
        "fitment_type": "drag_prep",
        "notes": "Pure drag slick",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["H2"]},
        "position": "rear",
        "tire_match": {"manufacturer": "M&H", "model_name": "Racemaster 6.0/18"},
        "fitment_type": "drag_prep",
        "notes": "Supercharged drag-spec",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Z H2"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "AM23A Drag Radial"},
        "fitment_type": "drag_prep",
        "notes": "Naked-supercharged",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 1000"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Mickey Thompson", "model_name": "ET Drag"},
        "fitment_type": "drag_prep",
        "notes": "Liter-superbike drag",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["R1"]},
        "position": "rear",
        "tire_match": {"manufacturer": "M&H", "model_name": "Racemaster 5.5/18"},
        "fitment_type": "drag_prep",
        "notes": "Liter-class drag tire",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR1000RR"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "AM23A Drag Radial"},
        "fitment_type": "drag_prep",
        "notes": "Liter-class street-drag",
    },
    {
        "bike_match": {"manufacturer": "Ducati", "model_keywords": ["Panigale V4"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Superbike SC0"},
        "fitment_type": "drag_prep",
        "notes": "V4 race-soft",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["S 1000 R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "AM23A Drag Radial"},
        "fitment_type": "drag_prep",
        "notes": "Naked-liter drag",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["M 1000 R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Mickey Thompson", "model_name": "ET Drag"},
        "fitment_type": "drag_prep",
        "notes": "M-series drag-spec",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RD350"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Shinko", "model_name": "Stealth R265 Drag"},
        "fitment_type": "drag_prep",
        "notes": "Vintage 2T drag",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["RGV250"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "drag_prep",
        "notes": "GP-rep drag-spec",
    },
    # ═══ EXPANSION 2 (Apr 27, 2026): WS-A bike coverage + uncovered fronts ═══
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR1000RR-R"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Bridgestone",
            "model_name": "Battlax Racing R11",
        },
        "fitment_type": "recommended",
        "notes": "Front 2024 Fireblade race",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CBR1000RR-R"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SP V4",
        },
        "fitment_type": "recommended",
        "notes": "Rear 2024 Fireblade race",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["YZF-R9"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Rosso IV Corsa",
        },
        "fitment_type": "recommended",
        "notes": "Front R9 sport",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["YZF-R9"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Rosso IV Corsa",
        },
        "fitment_type": "recommended",
        "notes": "Rear R9 sport",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS 660"]},
        "position": "front",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax S22"},
        "fitment_type": "recommended",
        "notes": "Front RS660 mid-sport",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["990 RC R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Rear 990 RC R sport",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Daytona 660"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power 5"},
        "fitment_type": "recommended",
        "notes": "Rear Daytona 660 sport",
    },
    {
        "bike_match": {"manufacturer": "MV Agusta", "model_keywords": ["Superveloce"]},
        "position": "rear",
        "tire_match": {
            "manufacturer": "Pirelli",
            "model_name": "Diablo Supercorsa SP V4",
        },
        "fitment_type": "recommended",
        "notes": "Rear Superveloce track",
    },
    {
        "bike_match": {"manufacturer": "Indian", "model_keywords": ["Pursuit"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "Elite 3"},
        "fitment_type": "recommended",
        "notes": "Rear Pursuit Bagger touring",
    },
    {
        "bike_match": {"manufacturer": "Husqvarna", "model_keywords": ["Norden"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Rear Norden adventure",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["RC30", "VFR750R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "Roadrunner AM26"},
        "fitment_type": "recommended",
        "notes": "Front RC30 vintage-correct",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["RC30", "VFR750R"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Roadrunner AM26"},
        "fitment_type": "recommended",
        "notes": "Rear RC30 vintage-correct",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["FZR1000"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "BT-46"},
        "fitment_type": "recommended",
        "notes": "Rear FZR1000 vintage-sport",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-R 750"]},
        "position": "rear",
        "tire_match": {"manufacturer": "Avon", "model_name": "Roadrunner AM26"},
        "fitment_type": "recommended",
        "notes": "Rear oilcooled GSX-R 750",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RD350"]},
        "position": "front",
        "tire_match": {"manufacturer": "Avon", "model_name": "Cobra Chrome"},
        "fitment_type": "recommended",
        "notes": "Front vintage 2T",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RX100"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Nylogrip Plus"},
        "fitment_type": "recommended",
        "notes": "Front Indian vintage 2T",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["RX135"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper FY"},
        "fitment_type": "recommended",
        "notes": "Front Indian vintage 2T",
    },
    {
        "bike_match": {"manufacturer": "Aprilia", "model_keywords": ["RS125"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Pilot Activ"},
        "fitment_type": "recommended",
        "notes": "Front Italian small-2T",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["300 EXC"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Scorpion Rally STR"},
        "fitment_type": "recommended",
        "notes": "Front Enduro all-terrain",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Classic 350"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Front cruiser-tourer",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Meteor 350"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Nylogrip Plus"},
        "fitment_type": "recommended",
        "notes": "Front cruiser-commuter",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Hunter 350"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Zapper FY"},
        "fitment_type": "recommended",
        "notes": "Front roadster",
    },
    {
        "bike_match": {
            "manufacturer": "Royal Enfield",
            "model_keywords": ["Continental GT 650"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Phantom Sportscomp"},
        "fitment_type": "recommended",
        "notes": "Front cafe-racer",
    },
    {
        "bike_match": {"manufacturer": "Triumph", "model_keywords": ["Speed Twin"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Phantom Sportscomp"},
        "fitment_type": "recommended",
        "notes": "Front modern-classic",
    },
    {
        "bike_match": {
            "manufacturer": "Harley-Davidson",
            "model_keywords": ["Iron 883"],
        },
        "position": "front",
        "tire_match": {"manufacturer": "Dunlop", "model_name": "American Elite"},
        "fitment_type": "recommended",
        "notes": "Front cruiser classic",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["RS150"]},
        "position": "front",
        "tire_match": {"manufacturer": "IRC", "model_name": "Road Winner"},
        "fitment_type": "recommended",
        "notes": "Front Malay underbone",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["Sonic 150"]},
        "position": "front",
        "tire_match": {"manufacturer": "FDR", "model_name": "Genzi 2"},
        "fitment_type": "recommended",
        "notes": "Front Indo sport-cub",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["Exciter 155"]},
        "position": "front",
        "tire_match": {"manufacturer": "IRC", "model_name": "GP-110"},
        "fitment_type": "recommended",
        "notes": "Front Thai underbone",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["ZX-25R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "Battlax S22"},
        "fitment_type": "recommended",
        "notes": "Front quarter-I4",
    },
    {
        "bike_match": {"manufacturer": "Bajaj", "model_keywords": ["Pulsar 220"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Front Indian sport-tourer",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 200"]},
        "position": "front",
        "tire_match": {"manufacturer": "Continental", "model_name": "ContiGo"},
        "fitment_type": "recommended",
        "notes": "Front Indian streetfighter",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["Duke 250"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Angel City"},
        "fitment_type": "recommended",
        "notes": "Front Indian sport-naked",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["FZ 25"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Front quarter-naked",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CB 300R"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Angel City"},
        "fitment_type": "recommended",
        "notes": "Front neo-retro",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["Gixxer SF 250"]},
        "position": "front",
        "tire_match": {"manufacturer": "MRF", "model_name": "Mogrip Meteor M2"},
        "fitment_type": "recommended",
        "notes": "Front quarter-fairing",
    },
    {
        "bike_match": {"manufacturer": "KTM", "model_keywords": ["390 Adventure"]},
        "position": "front",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Front mid-adventure",
    },
    {
        "bike_match": {"manufacturer": "BMW", "model_keywords": ["G310GS"]},
        "position": "front",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Front entry-adventure",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["V-Strom"]},
        "position": "front",
        "tire_match": {"manufacturer": "Continental", "model_name": "TKC 70"},
        "fitment_type": "recommended",
        "notes": "Front quarter-adventure",
    },
    {
        "bike_match": {"manufacturer": "Kawasaki", "model_keywords": ["Z650"]},
        "position": "front",
        "tire_match": {"manufacturer": "Michelin", "model_name": "Power 5"},
        "fitment_type": "recommended",
        "notes": "Front mid-naked",
    },
    {
        "bike_match": {"manufacturer": "Yamaha", "model_keywords": ["MT-07"]},
        "position": "front",
        "tire_match": {"manufacturer": "Pirelli", "model_name": "Diablo Rosso IV"},
        "fitment_type": "recommended",
        "notes": "Front twin-naked",
    },
    {
        "bike_match": {"manufacturer": "Honda", "model_keywords": ["CB650R"]},
        "position": "front",
        "tire_match": {
            "manufacturer": "Continental",
            "model_name": "ContiSportAttack 4",
        },
        "fitment_type": "recommended",
        "notes": "Front mid-classic",
    },
    {
        "bike_match": {"manufacturer": "Suzuki", "model_keywords": ["GSX-S1000"]},
        "position": "front",
        "tire_match": {"manufacturer": "Bridgestone", "model_name": "S22"},
        "fitment_type": "recommended",
        "notes": "Front liter-naked",
    },
]


def _classify_tire_compound(mfr: str, model: str, ftype: str) -> str:
    """Heuristic compound classification from brand/model strings."""
    m = model.lower()
    if any(s in m for s in ("drag", "racemaster", "et drag", "stealth", "quick time")):
        return "drag"
    if any(
        s in m
        for s in (
            "race",
            "supercorsa",
            "r11",
            "cup",
            "gp-a pro",
            "kr461",
            "superbike sc",
            "racing line",
        )
    ):
        return "race"
    if any(
        s in m
        for s in ("rally", "tkc", "anakee", "scorpion", "adventure", "adventurecross")
    ):
        return "adventure"
    if any(
        s in m
        for s in ("cobra chrome", "night dragon", "commander", "phantom", "exedra")
    ):
        return "cruiser"
    if any(
        s in m
        for s in (
            "pilot street",
            "street radial",
            "gp-110",
            "road winner",
            "genzi",
            "nylogrip",
            "gripp",
            "zapper",
            "mogrip",
            "revz",
            "angel city",
            "contigo",
        )
    ):
        return "commuter"
    if any(
        s in m
        for s in (
            "rosso",
            "power",
            "battlax",
            "s22",
            "q4",
            "q5",
            "sportmax",
            "angel",
            "pilot power",
            "roadrunner",
            "bt-46",
            "twins",
        )
    ):
        return "sport"
    return "sport"


_TIRE_TEMPLATES = {
    "drag": {
        "B": 11.0,
        "C": 1.7,
        "D": 1.85,
        "E": -0.40,
        "mu_peak": 1.85,
        "mu_slide": 1.45,
        "opt_temp": 80,
        "conf": 0.55,
    },
    "race": {
        "B": 11.5,
        "C": 1.65,
        "D": 1.55,
        "E": -0.35,
        "mu_peak": 1.55,
        "mu_slide": 1.18,
        "opt_temp": 72,
        "conf": 0.65,
    },
    "sport": {
        "B": 11.0,
        "C": 1.60,
        "D": 1.42,
        "E": -0.32,
        "mu_peak": 1.42,
        "mu_slide": 1.05,
        "opt_temp": 60,
        "conf": 0.62,
    },
    "commuter": {
        "B": 10.5,
        "C": 1.55,
        "D": 1.18,
        "E": -0.30,
        "mu_peak": 1.18,
        "mu_slide": 0.92,
        "opt_temp": 45,
        "conf": 0.55,
    },
    "adventure": {
        "B": 10.0,
        "C": 1.50,
        "D": 1.20,
        "E": -0.30,
        "mu_peak": 1.20,
        "mu_slide": 0.94,
        "opt_temp": 50,
        "conf": 0.58,
    },
    "cruiser": {
        "B": 10.0,
        "C": 1.55,
        "D": 1.22,
        "E": -0.30,
        "mu_peak": 1.22,
        "mu_slide": 0.96,
        "opt_temp": 50,
        "conf": 0.58,
    },
}


def _ensure_tire_exists(
    db, mfr: str, model: str, position: str, ftype: str
) -> int | None:
    """Return tire_model.id, creating tire (and manufacturer) on the fly if missing."""
    row = db._conn.execute(
        "SELECT t.id FROM tire_models t JOIN tire_manufacturers tm ON t.manufacturer_id = tm.id "
        "WHERE LOWER(tm.name) = LOWER(?) AND LOWER(t.model_name) = LOWER(?) AND t.position = ?",
        (mfr, model, position),
    ).fetchone()
    if row:
        return row[0]
    # Create manufacturer if needed
    row = db._conn.execute(
        "SELECT id FROM tire_manufacturers WHERE LOWER(name) = LOWER(?)", (mfr,)
    ).fetchone()
    if row:
        mfr_id = row[0]
    else:
        mfr_id = db._conn.execute(
            "INSERT INTO tire_manufacturers (name) VALUES (?)", (mfr,)
        ).lastrowid
    compound = _classify_tire_compound(mfr, model, ftype)
    t = _TIRE_TEMPLATES[compound]
    if position == "front":
        width, aspect, rim, size_str = 120, 70, 17, "120/70ZR17"
        rolling_radius, tread_mass, mass = 0.305, 1.8, 4.2
    else:
        width, aspect, rim, size_str = 180, 55, 17, "180/55ZR17"
        rolling_radius, tread_mass, mass = 0.315, 2.4, 5.5
    return db._conn.execute(
        "INSERT INTO tire_models "
        "(manufacturer_id, model_name, compound_type, position, width_mm, aspect_ratio, rim_diameter_inch, size_designation, "
        " pacejka_B, pacejka_C, pacejka_D, pacejka_E, mu_peak, mu_slide, load_sensitivity_k, optimal_temp_c, reversion_temp_c, "
        " thermal_conductivity, tread_mass_kg, specific_heat, rolling_radius_m, inertia_kgm2, growth_coeff, mass_kg, "
        " crr_base, crr_speed_coeff, crr_temp_coeff, recommended_psi, drag_pressure_psi, construction, confidence, available_india) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            mfr_id,
            model,
            compound,
            position,
            width,
            aspect,
            rim,
            size_str,
            t["B"],
            t["C"],
            t["D"],
            t["E"],
            t["mu_peak"],
            t["mu_slide"],
            0.0,
            t["opt_temp"],
            105.0,
            0.20,
            tread_mass,
            1700.0,
            rolling_radius,
            0.50,
            2e-09,
            mass,
            0.011,
            2.5e-05,
            -0.0002,
            32.0,
            24.0,
            "radial",
            t["conf"],
            1,
        ),
    ).lastrowid


def seed_recommended_fitments(db):
    """Seed recommended and drag_prep fitments into database. Auto-creates missing tires.
    Returns stats dict."""
    stats = {"inserted": 0, "skipped": 0, "errors": 0, "tires_created": 0}
    for fitment in RECOMMENDED_FITMENTS:
        try:
            bm = fitment["bike_match"]
            tm = fitment["tire_match"]
            bikes = db._conn.execute(
                "SELECT b.id FROM bike_models b JOIN manufacturers m ON b.manufacturer_id = m.id WHERE LOWER(m.name) = LOWER(?)",
                (bm["manufacturer"],),
            ).fetchall()
            bike_id = None
            for (bid,) in bikes:
                model_row = db._conn.execute(
                    "SELECT model_name FROM bike_models WHERE id = ?", (bid,)
                ).fetchone()
                if model_row and any(
                    kw.lower() in model_row[0].lower()
                    for kw in bm.get("model_keywords", [])
                ):
                    bike_id = bid
                    break
            if not bike_id:
                stats["skipped"] += 1
                continue
            tire_id_before = (
                db._conn.execute("SELECT MAX(id) FROM tire_models").fetchone()[0] or 0
            )
            tire_id = _ensure_tire_exists(
                db,
                tm["manufacturer"],
                tm["model_name"],
                fitment["position"],
                fitment["fitment_type"],
            )
            if tire_id is None:
                stats["skipped"] += 1
                continue
            if tire_id > tire_id_before:
                stats["tires_created"] += 1
            if db._conn.execute(
                "SELECT id FROM bike_tire_fitments WHERE bike_model_id = ? AND tire_model_id = ? AND position = ?",
                (bike_id, tire_id, fitment["position"]),
            ).fetchone():
                stats["skipped"] += 1
                continue
            db._conn.execute(
                "INSERT INTO bike_tire_fitments (bike_model_id, tire_model_id, position, fitment_type, is_default, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    bike_id,
                    tire_id,
                    fitment["position"],
                    fitment["fitment_type"],
                    0,
                    fitment["notes"],
                ),
            )
            stats["inserted"] += 1
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "fitment insert failed (bike=%s tire=%s pos=%s): %s",
                fitment.get("bike"),
                fitment.get("tire"),
                fitment.get("position"),
                exc,
            )
            stats["errors"] += 1
    db._conn.commit()
    return stats
