"""
MotoQuant — ECU Log Import
==========================
Parse motorcycle ECU data logger exports and extract physics-relevant
channels for simulation overlay and calibration.

Supported formats
-----------------
Woolich Racing  : TuneEdit CSV export (100 Hz, 50+ channels)
                  Header: "Time,RPM,TPS%,AFR,Coolant Temp,Air Temp,Speed,Gear,..."
Power Commander : PC-Link CSV (variable Hz, lambda/AFR, VSS in km/h)
                  Header: "Time (s),RPM,TP%,Lambda,ECT(°C),IAT(°C),VSS(km/h),Gear,..."
MoTeC i2        : Full channel tab-delimited export with metadata preamble
                  Starts with "Segment" header block, then channel + unit rows

All formats are auto-detected from the header row.

Output
------
Returns an ECULog dataclass containing:
  - time_s        : time axis [s], starting at 0 for the entire file
  - Per-channel arrays (RPM, TPS, speed, gear, AFR, temps, etc.)
  - A list of ECURunWindow objects extracted from launch-point detection
  - Metadata dict with logger type, sample rate, channel list

Run-window detection
--------------------
A "run" is detected by finding windows where:
  1. Vehicle speed is near-zero for ≥ MIN_STAGED_FRAMES consecutive samples
  2. Followed by speed increasing steadily (launch)
  3. Run ends when distance ≥ QUARTER_MILE_M or speed drops below LAUNCH_VEL_THRESHOLD

Public API
----------
    from motoquant.calibration.ecu import parse_ecu_file, ECULog, ECURunWindow

    log     = parse_ecu_file("woolich_log.csv")
    runs    = log.runs          # list[ECURunWindow]
    best    = log.best_run()    # lowest ET run
    rpm_t   = log.rpm           # full RPM channel [rpm]
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from .dragy import LAUNCH_VEL_THRESHOLD_MS, MIN_STAGE_FRAMES, QUARTER_MILE_M

# ─── Constants ────────────────────────────────────────────────────────────

KMH_TO_MS: float = 1.0 / 3.6
MPH_TO_MS: float = 0.44704

# Minimum TPS during a run (to confirm throttle was applied, not a coast)
MIN_LAUNCH_TPS: float = 20.0  # %

# Minimum speed increase rate to confirm acceleration (m/s per second)
MIN_ACCEL_MS2: float = 0.5

# Maximum believable ECU sample rate (Hz) — sanity bound
MAX_SAMPLE_RATE_HZ: float = 2000.0

# Minimum run duration for QM detection
MIN_RUN_DURATION_S: float = 5.0


class ECUParseError(Exception):
    """Raised when an ECU log file cannot be parsed."""


# ─── Channel name aliases ─────────────────────────────────────────────────
# Map ECU-specific column names → standard channel names.
# Each entry: (standard_name, conversion_fn_or_factor)
# conversion can be: float (multiply), callable, or None (identity)

_CHANNEL_ALIASES: list[tuple[str, str, object | None]] = [
    # (regex pattern matching header col, standard_name, conversion)
    # Time
    (r"^time[_ (s)]*$", "time_s", None),
    (r"^time\s*\(s\)$", "time_s", None),
    (r"^timestamp", "time_s", None),
    # RPM
    (r"^rpm$", "rpm", None),
    (r"^engine.?speed", "rpm", None),
    (r"^engine rpm", "rpm", None),
    # Throttle position
    (r"^tps[%_]?$", "tps_pct", None),
    (r"^tp[%_]?$", "tps_pct", None),
    (r"^throttle.?pos", "tps_pct", None),
    (r"^throttle.?(%|pct|percent)", "tps_pct", None),
    # Vehicle speed — km/h → m/s
    (r"^speed[_ (km/h)]*$", "vehicle_speed_ms", KMH_TO_MS),
    (r"^vss.*(km.?h)?$", "vehicle_speed_ms", KMH_TO_MS),
    (r"^vehicle.?speed.*(km.?h)?$", "vehicle_speed_ms", KMH_TO_MS),
    (r"^wheel.?speed.*(km.?h)?$", "vehicle_speed_ms", KMH_TO_MS),
    (r"^ground.?speed.*(km.?h)?$", "vehicle_speed_ms", KMH_TO_MS),
    # m/s already
    (r"^vehicle.?speed.*(m/?s)?$", "vehicle_speed_ms", None),
    # mph → m/s
    (r"^speed.*(mph|mi.?h)$", "vehicle_speed_ms", MPH_TO_MS),
    (r"^vss.*(mph|mi.?h)$", "vehicle_speed_ms", MPH_TO_MS),
    # Gear
    (r"^gear[_ ]?(position|pos)?$", "gear", None),
    (r"^current.?gear", "gear", None),
    # AFR / Lambda
    (r"^afr$", "afr", None),
    (r"^air.?fuel.?(ratio)?$", "afr", None),
    # Lambda → AFR (multiply by 14.7 for gasoline stoich)
    (r"^lambda[_ 1]?$", "afr", 14.7),
    (r"^o2.*(lambda)?$", "afr", 14.7),
    # Coolant temperature
    (r"^coolant.?temp", "coolant_temp_c", None),
    (r"^ect[_ (°c)]*$", "coolant_temp_c", None),
    (r"^engine.?temp", "coolant_temp_c", None),
    (r"^water.?temp", "coolant_temp_c", None),
    # °F → °C
    (r"^coolant.*(f|°f)$", "coolant_temp_c", lambda v: (v - 32) * 5 / 9),
    (r"^ect.*(f|°f)$", "coolant_temp_c", lambda v: (v - 32) * 5 / 9),
    # Inlet air temperature
    (r"^air.?temp", "air_temp_c", None),
    (r"^iat[_ (°c)]*$", "air_temp_c", None),
    (r"^inlet.?temp", "air_temp_c", None),
    (r"^intake.?temp", "air_temp_c", None),
    (r"^air.*(f|°f)$", "air_temp_c", lambda v: (v - 32) * 5 / 9),
    (r"^iat.*(f|°f)$", "air_temp_c", lambda v: (v - 32) * 5 / 9),
    # Ignition advance
    (r"^ign.*adv", "ignition_adv_deg", None),
    (r"^ignition.*timing", "ignition_adv_deg", None),
    (r"^spark.*adv", "ignition_adv_deg", None),
    (r"^timing", "ignition_adv_deg", None),
    # Fuel trim / injection
    (r"^fuel.?trim", "fuel_trim_pct", None),
    (r"^stft", "fuel_trim_pct", None),
    (r"^ltft", "fuel_trim_pct", None),
    (r"^inj.?pulse", "inj_pulse_ms", None),
    (r"^injection.?time", "inj_pulse_ms", None),
    (r"^pw[_ ]?(ms)?$", "inj_pulse_ms", None),
    # MAP / boost
    (r"^map[_ (kpa)]*$", "map_kpa", None),
    (r"^manifold.?(abs|pressure)", "map_kpa", None),
    (r"^boost[_ ]?(kpa|bar)?$", "map_kpa", None),
    # psi → kPa
    (r"^map.*(psi)$", "map_kpa", 6.89476),
    (r"^boost.*(psi)$", "map_kpa", 6.89476),
    # Battery voltage
    (r"^battery.?(voltage|volt|v)?$", "battery_v", None),
    (r"^batt.?v", "battery_v", None),
    (r"^supply.?v", "battery_v", None),
]

# Compiled patterns for speed
_COMPILED_ALIASES: list[tuple[re.Pattern, str, object | None]] = [
    (re.compile(pat, re.IGNORECASE), std, conv) for pat, std, conv in _CHANNEL_ALIASES
]


# ─── Data models ──────────────────────────────────────────────────────────


@dataclass
class ECURunWindow:
    """
    A single drag run extracted from an ECU log.

    Timestamps start at 0 (launch point). All channels present in the
    parent ECULog are available here sliced to the run window.
    """

    time_s: np.ndarray  # seconds, 0 = launch
    rpm: np.ndarray | None
    tps_pct: np.ndarray | None
    vehicle_speed_ms: np.ndarray | None
    gear: np.ndarray | None
    afr: np.ndarray | None
    coolant_temp_c: np.ndarray | None
    air_temp_c: np.ndarray | None
    ignition_adv_deg: np.ndarray | None
    fuel_trim_pct: np.ndarray | None
    map_kpa: np.ndarray | None
    inj_pulse_ms: np.ndarray | None
    battery_v: np.ndarray | None

    et_quarter: float  # ET at 402.336 m [s]; NaN if not reached
    trap_speed_ms: float  # speed at QM [m/s]; NaN if not reached
    peak_rpm: float  # max RPM during run
    peak_speed_ms: float  # max speed during run [m/s]
    launch_rpm: float  # RPM at launch (t=0)
    sample_rate_hz: float
    run_index: int = 0
    source_file: str = ""

    @property
    def trap_speed_kmh(self) -> float:
        return (
            self.trap_speed_ms * 3.6
            if not np.isnan(self.trap_speed_ms)
            else float("nan")
        )

    @property
    def duration_s(self) -> float:
        return float(self.time_s[-1]) if len(self.time_s) > 0 else 0.0

    def splits(self) -> dict[str, float]:
        """Return split times at standard drag strip distances."""
        if self.vehicle_speed_ms is None or len(self.vehicle_speed_ms) == 0:
            return {}
        dist = _integrate_distance(self.time_s, self.vehicle_speed_ms)
        marks = {
            "60ft": 18.288,
            "330ft": 100.584,
            "660ft": 201.168,
            "1000ft": 304.8,
            "1320ft": QUARTER_MILE_M,
        }
        out = {}
        for name, m in marks.items():
            t = _interpolate_et(self.time_s, dist, m)
            if t is not None:
                out[name] = round(t, 4)
        return out

    def to_dict(self) -> dict:
        return {
            "run_index": self.run_index,
            "et_quarter_s": round(self.et_quarter, 4)
            if not np.isnan(self.et_quarter)
            else None,
            "trap_speed_kmh": round(self.trap_speed_kmh, 2)
            if not np.isnan(self.trap_speed_ms)
            else None,
            "peak_rpm": round(self.peak_rpm, 0),
            "peak_speed_kmh": round(self.peak_speed_ms * 3.6, 2),
            "launch_rpm": round(self.launch_rpm, 0),
            "sample_rate_hz": self.sample_rate_hz,
            "duration_s": round(self.duration_s, 3),
            "source_file": self.source_file,
            "splits": self.splits(),
        }


@dataclass
class ECULog:
    """
    Full parsed ECU log file.

    Contains the complete time-series for all recognised channels,
    plus a list of detected drag runs.
    """

    # Complete file arrays (may be long — several minutes of logging)
    time_s: np.ndarray
    rpm: np.ndarray | None = None
    tps_pct: np.ndarray | None = None
    vehicle_speed_ms: np.ndarray | None = None
    gear: np.ndarray | None = None
    afr: np.ndarray | None = None
    coolant_temp_c: np.ndarray | None = None
    air_temp_c: np.ndarray | None = None
    ignition_adv_deg: np.ndarray | None = None
    fuel_trim_pct: np.ndarray | None = None
    map_kpa: np.ndarray | None = None
    inj_pulse_ms: np.ndarray | None = None
    battery_v: np.ndarray | None = None

    # Extra channels not mapped to standard names
    extra_channels: dict[str, np.ndarray] = field(default_factory=dict)

    # Detected runs
    runs: list[ECURunWindow] = field(default_factory=list)

    # Metadata
    source_file: str = ""
    logger_type: str = "unknown"  # woolich | pclink | motec | generic
    sample_rate_hz: float = 0.0
    n_samples: int = 0
    channel_names: list[str] = field(default_factory=list)

    def best_run(self) -> ECURunWindow | None:
        """Return the run with the lowest ET (fastest quarter mile)."""
        valid = [r for r in self.runs if not np.isnan(r.et_quarter)]
        if not valid:
            return self.runs[0] if self.runs else None
        return min(valid, key=lambda r: r.et_quarter)

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "logger_type": self.logger_type,
            "sample_rate_hz": self.sample_rate_hz,
            "n_samples": self.n_samples,
            "n_runs": len(self.runs),
            "channel_names": self.channel_names,
            "runs": [r.to_dict() for r in self.runs],
        }


# ─── Public API ───────────────────────────────────────────────────────────


def parse_ecu_file(
    path: str | Path,
    min_speed_ms: float = LAUNCH_VEL_THRESHOLD_MS,
    staged_frames: int = MIN_STAGE_FRAMES,
) -> ECULog:
    """
    Parse a motorcycle ECU log file and extract drag runs.

    Parameters
    ----------
    path           : Path to the ECU log file (.csv or .tsv or .txt)
    min_speed_ms   : Speed threshold [m/s] to detect staged position (default 0.8)
    staged_frames  : Consecutive sub-threshold frames needed to confirm staging

    Returns
    -------
    ECULog  — with .runs populated by detected drag run windows

    Raises
    ------
    ECUParseError  : if the file cannot be parsed or has no usable channels
    FileNotFoundError : if path does not exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"ECU log not found: {path}")

    raw_text = path.read_text(errors="replace")

    # Detect format
    logger_type, delimiter, header_row, data_start_row, units_row_idx = _detect_format(
        raw_text, path
    )

    # Parse all rows
    lines = raw_text.splitlines()
    header_cols = _split_row(lines[header_row], delimiter)

    # Build column → standard channel mapping
    col_map: dict[int, tuple[str, object | None]] = {}
    for i, col in enumerate(header_cols):
        std, conv = _map_column(col.strip())
        if std:
            # Don't overwrite an earlier mapping (prefer first match)
            if std not in {v[0] for v in col_map.values()}:
                col_map[i] = (std, conv)

    if not col_map:
        raise ECUParseError(
            f"No recognised channels found in {path.name}. Columns: {header_cols[:10]}"
        )

    # For MoTeC: read units row and override conversions based on physical units
    if units_row_idx is not None and units_row_idx < len(lines):
        unit_cols = _split_row(lines[units_row_idx], delimiter)
        col_map = _apply_unit_overrides(col_map, unit_cols)

    # Gather units row for MoTeC (row after header is units) — skip when parsing data
    skip_units = logger_type == "motec"

    # Parse data rows into per-column float arrays
    raw_cols: dict[int, list[float]] = {i: [] for i in col_map}

    # For extra channels not in col_map
    all_std_names = {v[0] for v in col_map.values()}
    extra_col_map: dict[int, str] = {}
    for i, col in enumerate(header_cols):
        if i not in col_map:
            clean = re.sub(r"[^a-z0-9_]", "_", col.strip().lower())
            if clean and clean not in all_std_names and len(clean) > 1:
                extra_col_map[i] = clean
    extra_cols: dict[int, list[float]] = {i: [] for i in extra_col_map}

    units_skipped = False
    for line_no, line in enumerate(lines[data_start_row:], start=data_start_row):
        line = line.strip()
        if not line:
            continue
        if skip_units and not units_skipped:
            units_skipped = True
            continue
        parts = _split_row(line, delimiter)
        if len(parts) < max(col_map.keys(), default=0) + 1:
            continue
        # Try to parse numeric
        row_ok = True
        row_vals: dict[int, float] = {}
        for i in list(col_map.keys()) + list(extra_col_map.keys()):
            if i >= len(parts):
                row_ok = False
                break
            try:
                row_vals[i] = float(parts[i])
            except (ValueError, IndexError):
                row_ok = False
                break
        if not row_ok:
            continue
        for i in col_map:
            raw_cols[i].append(row_vals[i])
        for i in extra_col_map:
            if i in row_vals:
                extra_cols[i].append(row_vals[i])

    if not raw_cols or all(len(v) == 0 for v in raw_cols.values()):
        raise ECUParseError(f"No numeric data rows found in {path.name}")

    n_rows = min(len(v) for v in raw_cols.values() if v)

    # Build standard channel arrays with conversion applied
    std_arrays: dict[str, np.ndarray] = {}
    for i, (std_name, conv) in col_map.items():
        arr = np.array(raw_cols[i][:n_rows], dtype=float)
        if conv is not None:
            if callable(conv):
                arr = np.vectorize(conv)(arr)
            else:
                arr = arr * float(conv)
        # If multiple columns map to same standard name, keep first
        if std_name not in std_arrays:
            std_arrays[std_name] = arr

    # Build extra channel arrays
    extra_arrays: dict[str, np.ndarray] = {}
    for i, name in extra_col_map.items():
        arr = np.array(extra_cols[i][:n_rows], dtype=float)
        if len(arr) == n_rows:
            extra_arrays[name] = arr

    # Time axis
    if "time_s" in std_arrays:
        t = std_arrays.pop("time_s")
        # Some loggers give time in ms
        if len(t) > 1 and (t[1] - t[0]) > 0.5:  # likely ms if step > 0.5
            t = t / 1000.0
        t = t - t[0]  # normalise to start at 0
    else:
        # Infer time from sample index — use median dt
        t = np.arange(n_rows, dtype=float) / max(n_rows - 1, 1)

    # Compute sample rate
    if len(t) > 1:
        dts = np.diff(t)
        median_dt = float(np.median(dts[dts > 0])) if np.any(dts > 0) else 0.01
        sample_rate = (
            min(1.0 / median_dt, MAX_SAMPLE_RATE_HZ) if median_dt > 0 else 100.0
        )
    else:
        sample_rate = 100.0

    # Build channel name list (what we found)
    found_channels = list(std_arrays.keys()) + list(extra_arrays.keys())

    log = ECULog(
        time_s=t,
        rpm=std_arrays.get("rpm"),
        tps_pct=std_arrays.get("tps_pct"),
        vehicle_speed_ms=std_arrays.get("vehicle_speed_ms"),
        gear=std_arrays.get("gear"),
        afr=std_arrays.get("afr"),
        coolant_temp_c=std_arrays.get("coolant_temp_c"),
        air_temp_c=std_arrays.get("air_temp_c"),
        ignition_adv_deg=std_arrays.get("ignition_adv_deg"),
        fuel_trim_pct=std_arrays.get("fuel_trim_pct"),
        map_kpa=std_arrays.get("map_kpa"),
        inj_pulse_ms=std_arrays.get("inj_pulse_ms"),
        battery_v=std_arrays.get("battery_v"),
        extra_channels=extra_arrays,
        source_file=str(path),
        logger_type=logger_type,
        sample_rate_hz=round(sample_rate, 1),
        n_samples=n_rows,
        channel_names=found_channels,
    )

    # Extract drag runs
    log.runs = _extract_runs(log, min_speed_ms, staged_frames)

    return log


# ─── Format detection ──────────────────────────────────────────────────────


def _detect_format(text: str, path: Path) -> tuple[str, str, int, int, int | None]:
    """
    Detect ECU log format from file content.

    Returns (logger_type, delimiter, header_row_index, data_start_row_index, units_row_idx).
    units_row_idx is None if no units row is present.
    """
    lines = text.splitlines()

    # MoTeC i2: starts with "Segment" or "Format" metadata block
    for i, line in enumerate(lines[:20]):
        if re.match(
            r"^\s*(Segment|Format|Venue|Vehicle|Driver|Event|Session)", line, re.I
        ):
            # Find the row that looks like channel names (has RPM or Engine Speed)
            for j in range(i, min(i + 30, len(lines))):
                if re.search(r"rpm|engine.?speed|time", lines[j], re.I):
                    return ("motec", "\t", j, j + 2, j + 1)  # j+1 is units, j+2 is data
            break

    # Try tab-separated (MoTeC generic, some PC-Link exports)
    first_data = next((line for line in lines if line.strip()), "")
    if "\t" in first_data:
        for i, line in enumerate(lines[:10]):
            if re.search(r"rpm|time|speed", line, re.I):
                return ("motec", "\t", i, i + 1, None)

    # Woolich Racing: "Time,RPM,TPS%,..." — comma, first line is header
    # Power Commander PC-Link: "Time (s),RPM,TP%,Lambda,..."
    # Both are comma-delimited with header on first non-empty, non-comment row
    for i, line in enumerate(lines[:15]):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        cols = [c.strip() for c in line_stripped.split(",")]
        if len(cols) < 3:
            continue
        if re.search(r"rpm|time|speed|tps|tp%", line_stripped, re.I):
            # Distinguish Woolich vs PC-Link by column names
            joined = ",".join(cols).lower()
            if "tp%" in joined or "lambda" in joined or "ect" in joined:
                logger_type = "pclink"
            elif "tps%" in joined or "woolich" in joined:
                logger_type = "woolich"
            else:
                logger_type = "generic"
            return (logger_type, ",", i, i + 1, None)

    # Final fallback: try semicolon-delimited
    for i, line in enumerate(lines[:15]):
        if ";" in line and re.search(r"rpm|time|speed", line, re.I):
            return ("generic", ";", i, i + 1, None)

    raise ECUParseError(
        f"Unrecognised ECU log format in {path.name}. "
        "Expected Woolich, Power Commander PC-Link, or MoTeC i2 CSV/TSV."
    )


def _apply_unit_overrides(
    col_map: dict[int, tuple[str, object | None]],
    unit_cols: list[str],
) -> dict[int, tuple[str, object | None]]:
    """
    For MoTeC (and similar) logs where units appear in a separate row,
    override the column conversion based on the physical unit string.

    Supported unit overrides:
      m/s   → speed channel: no conversion (identity)
      km/h  → speed channel: KMH_TO_MS
      mph   → speed channel: MPH_TO_MS
      °f/f  → temp channel: Fahrenheit → Celsius
      psi   → pressure: psi → kPa
    """
    new_map = dict(col_map)
    for i, (std_name, conv) in col_map.items():
        if i >= len(unit_cols):
            continue
        unit = unit_cols[i].strip().lower()
        if not unit:
            continue

        if std_name == "vehicle_speed_ms":
            if unit in ("m/s", "ms", "meters/s"):
                new_map[i] = (std_name, None)  # already m/s
            elif unit in ("km/h", "kmh", "kph", "km/hr"):
                new_map[i] = (std_name, KMH_TO_MS)
            elif unit in ("mph", "mi/h"):
                new_map[i] = (std_name, MPH_TO_MS)

        elif std_name in ("coolant_temp_c", "air_temp_c"):
            if unit in ("°f", "f", "fahrenheit", "degf"):
                new_map[i] = (std_name, lambda v: (v - 32) * 5.0 / 9.0)
            elif unit in ("°c", "c", "celsius", "degc"):
                new_map[i] = (std_name, None)

        elif std_name == "map_kpa":
            if unit in ("psi",):
                new_map[i] = (std_name, 6.89476)
            elif unit in ("kpa", "bar"):
                if unit == "bar":
                    new_map[i] = (std_name, 100.0)  # bar → kPa
                else:
                    new_map[i] = (std_name, None)

    return new_map


# ─── Column mapping ────────────────────────────────────────────────────────


def _map_column(col_name: str) -> tuple[str | None, object | None]:
    """Map a raw column name to a standard channel name + conversion."""
    col_lower = col_name.lower().strip()
    # Strip units in parentheses for matching: "Speed (km/h)" → "Speed"
    col_clean = re.sub(r"\s*\([^)]*\)", "", col_lower).strip()

    for pattern, std, conv in _COMPILED_ALIASES:
        if pattern.match(col_clean) or pattern.match(col_lower):
            return std, conv
    return None, None


def _split_row(line: str, delimiter: str) -> list[str]:
    """Split a CSV/TSV row, handling quoted fields."""
    if delimiter == ",":
        reader = csv.reader([line])
        return next(reader, [])
    return line.split(delimiter)


# ─── Run extraction ────────────────────────────────────────────────────────


def _extract_runs(
    log: ECULog,
    min_speed_ms: float,
    staged_frames: int,
) -> list[ECURunWindow]:
    """
    Extract individual drag runs from a full ECU log.

    Strategy:
    1. Use vehicle_speed_ms if available (preferred — most accurate)
    2. Fall back to RPM-only detection (detect engine rev-up from idle)
    """
    if log.vehicle_speed_ms is not None and len(log.vehicle_speed_ms) > 0:
        return _extract_runs_from_speed(log, min_speed_ms, staged_frames)
    elif log.rpm is not None and len(log.rpm) > 0:
        return _extract_runs_from_rpm(log)
    return []


def _extract_runs_from_speed(
    log: ECULog,
    min_speed_ms: float,
    staged_frames: int,
) -> list[ECURunWindow]:
    """Extract runs using vehicle speed channel."""
    speed = log.vehicle_speed_ms
    t = log.time_s
    n = len(speed)
    runs: list[ECURunWindow] = []
    run_index = 0

    i = 0
    while i < n - staged_frames:
        # Find staged window: consecutive frames with speed < threshold
        if speed[i] < min_speed_ms:
            stage_end = i
            count = 0
            while stage_end < n and speed[stage_end] < min_speed_ms:
                count += 1
                stage_end += 1

            if count >= staged_frames and stage_end < n:
                # launch_idx = first frame where speed rises above threshold
                launch_idx = stage_end
                while launch_idx < n and speed[launch_idx] < min_speed_ms:
                    launch_idx += 1

                if launch_idx >= n:
                    break

                # Verify it's a genuine launch: speed must keep increasing
                # (check average acceleration over next 0.5 s)
                half_s_frames = max(1, int(0.5 * log.sample_rate_hz))
                end_check = min(launch_idx + half_s_frames, n - 1)
                if end_check > launch_idx:
                    avg_accel = (speed[end_check] - speed[launch_idx]) / (
                        t[end_check] - t[launch_idx] + 1e-9
                    )
                    if avg_accel < MIN_ACCEL_MS2:
                        i = launch_idx + 1
                        continue

                # Scan forward to find run end
                run_end = _find_run_end_speed(speed, t, launch_idx)

                # Extract window
                window = slice(launch_idx, run_end)
                run = _build_run_window(log, window, run_index, t[launch_idx])
                if run is not None:
                    runs.append(run)
                    run_index += 1

                i = run_end
                continue

        i += 1

    return runs


def _find_run_end_speed(speed: np.ndarray, t: np.ndarray, launch_idx: int) -> int:
    """Find end of a drag run: QM reached, or speed drops >20 m/s from peak."""
    n = len(speed)
    peak_speed = speed[launch_idx]
    peak_idx = launch_idx
    cum_dist = 0.0
    prev_i = launch_idx

    for i in range(launch_idx + 1, n):
        dt = float(t[i] - t[prev_i])
        cum_dist += float(speed[i]) * dt
        if speed[i] > peak_speed:
            peak_speed = speed[i]
            peak_idx = i
        prev_i = i

        # Run is done if we've clearly gone past QM distance
        if cum_dist >= QUARTER_MILE_M * 1.05:
            return i + 1

        # Run is done if speed dropped 20 m/s from peak (braking / ran off)
        if (
            i > peak_idx + 5
            and speed[i] < peak_speed - 20.0
            and cum_dist > QUARTER_MILE_M * 0.5
        ):
            return i

        # Maximum run window: 30 seconds of data
        if float(t[i] - t[launch_idx]) > 30.0:
            return i

    return n


def _extract_runs_from_rpm(log: ECULog) -> list[ECURunWindow]:
    """
    Fallback run detection using RPM channel alone.
    Detect runs as RPM going from idle (< 2000) to high (> 6000) + sustained.
    """
    rpm = log.rpm
    t = log.time_s
    n = len(rpm)
    runs: list[ECURunWindow] = []
    run_index = 0
    i = 0

    IDLE_RPM = 2500.0
    LAUNCH_RPM = 4000.0

    while i < n - 10:
        if rpm[i] < IDLE_RPM:
            # Scan for RPM rise
            j = i
            while j < n and rpm[j] < IDLE_RPM:
                j += 1
            if j < n and j - i >= MIN_STAGE_FRAMES:
                # Find where RPM sustains > LAUNCH_RPM
                k = j
                while k < n and rpm[k] < LAUNCH_RPM:
                    k += 1
                if k < n:
                    # Run end: RPM drops back below LAUNCH_RPM
                    end = k
                    while end < n and rpm[end] > LAUNCH_RPM:
                        end += 1
                    duration = float(t[min(end, n - 1)] - t[k])
                    if duration >= MIN_RUN_DURATION_S:
                        window = slice(j, min(end + 20, n))
                        run = _build_run_window(log, window, run_index, t[j])
                        if run is not None:
                            runs.append(run)
                            run_index += 1
                    i = end
                    continue
        i += 1

    return runs


def _build_run_window(
    log: ECULog,
    window: slice,
    run_index: int,
    t_launch: float,
) -> Optional["ECURunWindow"]:
    """Slice all channels to the window and build an ECURunWindow."""
    t_win = log.time_s[window] - t_launch

    if len(t_win) < 5:
        return None

    speed_win = _slice_or_none(log.vehicle_speed_ms, window)

    # Compute ET and trap speed from speed channel
    if speed_win is not None and len(speed_win) > 3:
        dist = _integrate_distance(t_win, speed_win)
        et = _interpolate_et(t_win, dist, QUARTER_MILE_M)
        trap = _interpolate_speed(t_win, speed_win, dist, QUARTER_MILE_M)
        et_q = et if et is not None else float("nan")
        trap_s = trap if trap is not None else float("nan")
        peak_speed = float(np.max(speed_win))
    else:
        et_q = trap_s = float("nan")
        peak_speed = 0.0

    rpm_win = _slice_or_none(log.rpm, window)
    peak_rpm = float(np.max(rpm_win)) if rpm_win is not None else 0.0
    launch_rpm = float(rpm_win[0]) if rpm_win is not None else 0.0

    return ECURunWindow(
        time_s=t_win,
        rpm=rpm_win,
        tps_pct=_slice_or_none(log.tps_pct, window),
        vehicle_speed_ms=speed_win,
        gear=_slice_or_none(log.gear, window),
        afr=_slice_or_none(log.afr, window),
        coolant_temp_c=_slice_or_none(log.coolant_temp_c, window),
        air_temp_c=_slice_or_none(log.air_temp_c, window),
        ignition_adv_deg=_slice_or_none(log.ignition_adv_deg, window),
        fuel_trim_pct=_slice_or_none(log.fuel_trim_pct, window),
        map_kpa=_slice_or_none(log.map_kpa, window),
        inj_pulse_ms=_slice_or_none(log.inj_pulse_ms, window),
        battery_v=_slice_or_none(log.battery_v, window),
        et_quarter=et_q,
        trap_speed_ms=trap_s,
        peak_rpm=peak_rpm,
        peak_speed_ms=peak_speed,
        launch_rpm=launch_rpm,
        sample_rate_hz=log.sample_rate_hz,
        run_index=run_index,
        source_file=log.source_file,
    )


def _slice_or_none(arr: np.ndarray | None, window: slice) -> np.ndarray | None:
    if arr is None:
        return None
    sliced = arr[window]
    return sliced if len(sliced) > 0 else None


# ─── Maths helpers ────────────────────────────────────────────────────────


def _integrate_distance(t: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Trapezoidal integration of v(t) → cumulative distance [m]."""
    dt = np.diff(t)
    v_mid = 0.5 * (v[:-1] + v[1:])
    return np.concatenate([[0.0], np.cumsum(v_mid * dt)])


def _interpolate_et(t: np.ndarray, dist: np.ndarray, target_m: float) -> float | None:
    """Linear interpolation: time when cumulative distance hits target_m."""
    idx = np.searchsorted(dist, target_m)
    if idx == 0 or idx >= len(dist):
        return None
    d0, d1 = dist[idx - 1], dist[idx]
    t0, t1 = t[idx - 1], t[idx]
    if d1 == d0:
        return None
    frac = (target_m - d0) / (d1 - d0)
    return float(t0 + frac * (t1 - t0))


def _interpolate_speed(
    t: np.ndarray, v: np.ndarray, dist: np.ndarray, target_m: float
) -> float | None:
    """Speed at the moment cumulative distance hits target_m."""
    idx = np.searchsorted(dist, target_m)
    if idx == 0 or idx >= len(dist):
        return None
    d0, d1 = dist[idx - 1], dist[idx]
    if d1 == d0:
        return None
    frac = (target_m - d0) / (d1 - d0)
    return float(v[idx - 1] + frac * (v[idx] - v[idx - 1]))
