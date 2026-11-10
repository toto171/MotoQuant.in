"""
MotoQuant — Motorcycle Drag Racing Simulation & Optimization Engine
===================================================================
A first-principles physics engine for quarter-mile performance prediction.

15 sub-models, 200+ input parameters, RK4 integration at 1 ms timestep.
Validated against published quarter-mile benchmarks; the measured accuracy is
in the newest reports/acc_final_*.json and on motoquant.in/validation.

Usage:
    from motoquant import MotoQuantEngine, BikeConfig
    from motoquant.defaults import gsxr1000_k5

    config = gsxr1000_k5()
    engine = MotoQuantEngine(config)
    result = engine.run()
    print(f"Quarter-mile: {result.time_quarter:.3f}s @ {result.speed_quarter*3.6:.1f} km/h")
"""

# The one version number of the project. pyproject.toml reads it (setuptools
# dynamic metadata), and the CLI banner, saved-run rows and the Sentry release
# tag all import it from here.
__version__ = "2.0.0"

from .defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from .models import BikeConfig
from .physics import MotoQuantEngine, SimResult
