"""
MotoQuant Pro — Motorcycle Drag Racing Simulation & Optimization Engine
=====================================================================
A first-principles physics engine for quarter-mile performance prediction.

15 sub-models, 200+ input parameters, RK4 integration at 1 ms timestep.
Validated within ±0.07s of published quarter-mile benchmarks.

Usage:
    from motoquant import MotoQuantEngine, BikeConfig
    from motoquant.defaults import gsxr1000_k5

    config = gsxr1000_k5()
    engine = MotoQuantEngine(config)
    result = engine.run()
    print(f"Quarter-mile: {result.time_quarter:.3f}s @ {result.speed_quarter*3.6:.1f} km/h")
"""

__version__ = "0.2.0"

from .defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from .models import BikeConfig
from .physics import MotoQuantEngine, SimResult
