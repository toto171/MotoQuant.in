"""
MotoQuant Pro — Calibration & Validation Pipeline
==================================================
Phase 3: import real run data, overlay with simulation, auto-calibrate physics.

Public surface:
    from motoquant.calibration.dragy      import parse_dragy_file, DragRunData, DragParseError
    from motoquant.calibration.dyno       import parse_dyno_file, DynoResult, DynoParseError
    from motoquant.calibration.ecu        import parse_ecu_file, ECULog, ECURunWindow, ECUParseError
    from motoquant.calibration.overlay    import compare_runs, RunComparison, compute_cost
    from motoquant.calibration.calibrator import calibrate, CalibrationResult, PRESET_AERO_TIRE
"""

from .calibrator import (
    PRESET_AERO_ONLY,
    PRESET_AERO_TIRE,
    PRESET_FULL,
    PRESET_TIRE_ONLY,
    CalibrationError,
    CalibrationResult,
    calibrate,
    calibrate_multi_run,
)
from .dragy import DragParseError, DragRunData, best_run, parse_dragy_file
from .dyno import DynoParseError, DynoResult, parse_dyno_file
from .ecu import ECULog, ECUParseError, ECURunWindow, parse_ecu_file
from .overlay import (
    MultiRunStats,
    OverlayError,
    RunComparison,
    compare_runs,
    compute_cost,
    compute_multi_run_stats,
    print_multi_run_stats,
)

__all__ = [
    "DragRunData",
    "DragParseError",
    "parse_dragy_file",
    "best_run",
    "DynoResult",
    "DynoParseError",
    "parse_dyno_file",
    "ECULog",
    "ECURunWindow",
    "ECUParseError",
    "parse_ecu_file",
    "RunComparison",
    "OverlayError",
    "compare_runs",
    "compute_cost",
    "MultiRunStats",
    "compute_multi_run_stats",
    "print_multi_run_stats",
    "CalibrationResult",
    "CalibrationError",
    "calibrate",
    "calibrate_multi_run",
    "PRESET_AERO_TIRE",
    "PRESET_AERO_ONLY",
    "PRESET_TIRE_ONLY",
    "PRESET_FULL",
]
