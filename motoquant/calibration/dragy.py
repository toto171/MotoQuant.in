"""
MotoQuant Pro — Dragy GPS Import
=================================
Parse Dragy GPS timer CSV and JSON exports, detect run boundaries, and
produce DragRunData for the calibration pipeline.

Supported formats
-----------------
CSV A  — classic Dragy 2/3 export (imperial): time_s, speed_mph, dist_ft
CSV B  — Dragy 4+ export (metric):  Time (s), Speed (km/h), Distance (m)
CSV C  — Dragy app export with GPS: Time, Speed, Distance, Lat, Lon [any units]
JSON   — Dragy app JSON: {"meta": {...}, "runs": [{"samples": [...]}]}
AUTO   — unit and format auto-detected from column headers

Run-boundary detection
----------------------
Dragy records continuously. A raw file contains:
  * idle period before staging (v ≈ 0)
  * rollout / staged window (v < 0.5 m/s)
  * the run itself (launch → 1/4 mile + brief coasting)
  * optional cooldown

The detector:
  1. Converts everything to SI (m, m/s, s).
  2. Finds the *last* consecutive window of at least MIN_STAGE_FRAMES frames
     where v < LAUNCH_VEL_THRESHOLD_MS.
  3. The "launch frame" is the first frame *after* that window where velocity
     climbs above LAUNCH_VEL_THRESHOLD_MS AND the slope is positive.
  4. Integrates v(t) forward from launch to find cumulative distance.
  5. Interpolates the exact timestamp when distance crosses 402.336 m.
  6. Returns DragRunData trimmed from launch to (quarter + POST_TRAP_MARGIN_S).

Multiple-run files
------------------
parse_dragy_file() returns a list[DragRunData].  The file may contain one or
more staged runs; each separated by a new idle window.  Callers typically take
the best run (lowest ET) or the most recent.
"""

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ─── Physical constants ────────────────────────────────────────────────────
from ..constants import QUARTER_MILE_M  # single source of truth (402.336 m)

EIGHTH_MILE_M: float = 201.168  # 1/8 mile in metres

# Unit conversion factors
MPH_TO_MS: float = 0.44704
KMH_TO_MS: float = 1.0 / 3.6
FT_TO_M: float = 0.3048

# ─── Boundary-detection tuning knobs ──────────────────────────────────────

LAUNCH_VEL_THRESHOLD_MS: float = 0.8  # m/s  — below = "staged/idle"
MIN_STAGE_FRAMES: int = 5  # consecutive below-threshold frames = valid stage
MIN_RUN_DURATION_S: float = 5.0  # discard anything shorter
MAX_RUN_DURATION_S: float = 30.0  # discard implausibly slow runs
POST_TRAP_MARGIN_S: float = 1.0  # keep this many seconds past 1/4 mile
MIN_PEAK_SPEED_MS: float = 20.0  # ≥ 72 km/h peak — rejects noise runs

# Standard split distances in metres  (60 ft, 330 ft, 660 ft, 1000 ft, 1320 ft)
SPLIT_DISTANCES_M: dict[str, float] = {
    "60ft": 18.288,
    "330ft": 100.584,
    "660ft": 201.168,
    "1000ft": 304.800,
    "1320ft": 402.336,
}


# ─── Errors ───────────────────────────────────────────────────────────────


class DragParseError(Exception):
    """Raised when a Dragy file cannot be parsed or contains no valid run."""


# ─── Data model ───────────────────────────────────────────────────────────


@dataclass
class DragRunData:
    """
    One detected quarter-mile run extracted from a Dragy GPS file.

    All time-series arrays are the same length and share the same index.
    ``timestamps[0] == 0.0`` (launch is the time origin).
    """

    # ── Time-series (numpy arrays, SI units) ──────────────────────────────
    timestamps: np.ndarray  # seconds, t=0 at launch
    velocity_ms: np.ndarray  # m/s
    distance_m: np.ndarray  # cumulative metres from launch
    acceleration_ms2: np.ndarray  # dv/dt (central differences, m/s²)

    # ── Scalar results ─────────────────────────────────────────────────────
    et_quarter: float  # ET at 402.336 m (seconds)
    trap_speed_ms: float  # speed at 1/4 mile (m/s)

    # ── Metadata ───────────────────────────────────────────────────────────
    sample_rate_hz: float
    source_file: str
    run_index: int = 0  # 0-based index within the source file
    raw_metadata: dict = field(default_factory=dict)

    # ── Derived properties ─────────────────────────────────────────────────

    @property
    def trap_speed_kmh(self) -> float:
        return self.trap_speed_ms * 3.6

    @property
    def trap_speed_mph(self) -> float:
        return self.trap_speed_ms * 2.23694

    @property
    def duration_s(self) -> float:
        return float(self.timestamps[-1]) if len(self.timestamps) else 0.0

    @property
    def peak_speed_ms(self) -> float:
        return float(np.max(self.velocity_ms)) if len(self.velocity_ms) else 0.0

    def splits(self) -> dict[str, float]:
        """
        Return split ETs as {name: seconds} for all standard marks that fall
        within the recorded distance.  Linearly interpolated.
        """
        result: dict[str, float] = {}
        for name, target_m in SPLIT_DISTANCES_M.items():
            if target_m > self.distance_m[-1]:
                continue  # run didn't reach this mark
            # Find surrounding indices
            idx = int(np.searchsorted(self.distance_m, target_m))
            if idx == 0:
                result[name] = float(self.timestamps[0])
            elif idx >= len(self.distance_m):
                result[name] = float(self.timestamps[-1])
            else:
                # Linear interpolation between idx-1 and idx
                d0, d1 = self.distance_m[idx - 1], self.distance_m[idx]
                t0, t1 = self.timestamps[idx - 1], self.timestamps[idx]
                frac = (target_m - d0) / (d1 - d0) if (d1 - d0) > 0 else 0.0
                result[name] = float(t0 + frac * (t1 - t0))
        return result

    def to_dict(self) -> dict:
        """Serialisable summary (no arrays)."""
        return {
            "et_quarter": round(self.et_quarter, 4),
            "trap_speed_kmh": round(self.trap_speed_kmh, 2),
            "trap_speed_mph": round(self.trap_speed_mph, 2),
            "sample_rate_hz": self.sample_rate_hz,
            "duration_s": round(self.duration_s, 3),
            "peak_speed_kmh": round(self.peak_speed_ms * 3.6, 2),
            "splits": {k: round(v, 4) for k, v in self.splits().items()},
            "source_file": self.source_file,
            "run_index": self.run_index,
        }


# ─── Internal helpers ─────────────────────────────────────────────────────


def _detect_csv_units(header: list[str]) -> tuple[str, str, str]:
    """
    Infer speed and distance units from column headers.

    Returns (speed_unit, dist_unit, time_unit) where each is one of:
        speed_unit : 'mph' | 'kmh' | 'ms'
        dist_unit  : 'ft'  | 'm'
        time_unit  : 's'
    """
    header_lower = [h.lower() for h in header]
    combined = " ".join(header_lower)

    speed_unit = "mph"  # default (older Dragy is imperial)
    dist_unit = "ft"

    if "km/h" in combined or "kmh" in combined or "km_h" in combined:
        speed_unit = "kmh"
    elif "m/s" in combined:
        speed_unit = "ms"

    if any(tok in combined for tok in ["(m)", "dist_m", "distance_m", " m,", "meters"]):
        dist_unit = "m"
    elif any(
        tok in combined for tok in ["(ft)", "dist_ft", "distance_ft", " ft,", "feet"]
    ):
        dist_unit = "ft"

    return speed_unit, dist_unit, "s"


def _col_index(header: list[str], candidates: list[str]) -> int:
    """Return index of first matching column name (case-insensitive). -1 if none."""
    h = [c.strip().lower() for c in header]
    for candidate in candidates:
        c = candidate.lower()
        for i, col in enumerate(h):
            if c == col or col.startswith(c) or c in col:
                return i
    return -1


def _to_si_velocity(values: np.ndarray, unit: str) -> np.ndarray:
    if unit == "mph":
        return values * MPH_TO_MS
    if unit == "kmh":
        return values * KMH_TO_MS
    return values  # already m/s


def _to_si_distance(values: np.ndarray, unit: str) -> np.ndarray:
    if unit == "ft":
        return values * FT_TO_M
    return values  # already metres


def _compute_acceleration(t: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Central-difference first derivative dv/dt.  Forward/backward at ends."""
    if len(t) < 2:
        return np.zeros_like(v)
    a = np.empty_like(v)
    a[0] = (v[1] - v[0]) / (t[1] - t[0]) if (t[1] - t[0]) > 0 else 0.0
    a[-1] = (v[-1] - v[-2]) / (t[-1] - t[-2]) if (t[-1] - t[-2]) > 0 else 0.0
    dt_mid = t[2:] - t[:-2]
    safe = dt_mid > 0
    a[1:-1] = np.where(safe, (v[2:] - v[:-2]) / np.where(safe, dt_mid, 1.0), 0.0)
    return a


def _integrate_distance(t: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Trapezoidal integration of v(t) → cumulative distance."""
    dt = np.diff(t)
    v_avg = (v[:-1] + v[1:]) * 0.5
    increments = dt * v_avg
    return np.concatenate([[0.0], np.cumsum(increments)])


def _interpolate_et(t: np.ndarray, d: np.ndarray, target_m: float) -> float | None:
    """
    Return the time (seconds) when cumulative distance first crosses target_m.
    Linear interpolation between samples.  Returns None if never reached.
    """
    idx = int(np.searchsorted(d, target_m))
    if idx == 0 and d[0] >= target_m:
        return float(t[0])
    if idx >= len(d):
        return None  # never reached
    d0, d1 = d[idx - 1], d[idx]
    t0, t1 = t[idx - 1], t[idx]
    frac = (target_m - d0) / (d1 - d0) if (d1 - d0) > 0 else 0.0
    return float(t0 + frac * (t1 - t0))


def _interpolate_speed_at_distance(
    v: np.ndarray, d: np.ndarray, target_m: float
) -> float | None:
    """Speed (m/s) when distance first crosses target_m. Linear interpolation."""
    idx = int(np.searchsorted(d, target_m))
    if idx == 0:
        return float(v[0])
    if idx >= len(d):
        return None
    d0, d1 = d[idx - 1], d[idx]
    v0, v1 = v[idx - 1], v[idx]
    frac = (target_m - d0) / (d1 - d0) if (d1 - d0) > 0 else 0.0
    return float(v0 + frac * (v1 - v0))


def _detect_sample_rate(t: np.ndarray) -> float:
    """Compute sample rate from median inter-frame delta-t."""
    if len(t) < 2:
        return 10.0
    dt = np.median(np.diff(t))
    return float(1.0 / dt) if dt > 0 else 10.0


# ─── Run-boundary detection ───────────────────────────────────────────────


def _find_staged_windows(v_ms: np.ndarray) -> list[tuple[int, int]]:
    """
    Return list of (start_idx, end_idx) for every consecutive window where
    v < LAUNCH_VEL_THRESHOLD_MS for at least MIN_STAGE_FRAMES frames.
    end_idx is inclusive.
    """
    below = v_ms < LAUNCH_VEL_THRESHOLD_MS
    windows = []
    start = None
    for i, b in enumerate(below):
        if b and start is None:
            start = i
        elif not b and start is not None:
            length = i - start
            if length >= MIN_STAGE_FRAMES:
                windows.append((start, i - 1))
            start = None
    if start is not None:
        length = len(below) - start
        if length >= MIN_STAGE_FRAMES:
            windows.append((start, len(below) - 1))
    return windows


def _detect_runs(
    t: np.ndarray,
    v_ms: np.ndarray,
    d_m: np.ndarray,
) -> list[tuple[int, int, float, float]]:
    """
    Find all drag runs in continuous telemetry.

    Returns list of (launch_idx, trap_idx, et_quarter, trap_speed_ms).
    Each run begins immediately after a staged window and ends when the bike
    crosses or exceeds QUARTER_MILE_M from that launch point.
    """
    staged_windows = _find_staged_windows(v_ms)
    if not staged_windows:
        return []

    runs = []

    for win_start, win_end in staged_windows:
        # Launch = first frame after staged window where v > threshold
        launch_idx = win_end + 1
        while launch_idx < len(v_ms) and v_ms[launch_idx] < LAUNCH_VEL_THRESHOLD_MS:
            launch_idx += 1
        if launch_idx >= len(v_ms):
            continue

        # Check there are enough frames after launch
        remaining = len(v_ms) - launch_idx
        if remaining < int(_detect_sample_rate(t) * MIN_RUN_DURATION_S):
            continue

        # Slice from launch
        t_run = t[launch_idx:] - t[launch_idx]  # re-zero time
        v_run = v_ms[launch_idx:]
        d_run = _integrate_distance(t_run, v_run)

        # Must reach 1/4 mile
        et = _interpolate_et(t_run, d_run, QUARTER_MILE_M)
        if et is None:
            continue

        # Sanity checks
        if et < MIN_RUN_DURATION_S or et > MAX_RUN_DURATION_S:
            continue
        if float(np.max(v_run)) < MIN_PEAK_SPEED_MS:
            continue

        # Speed at trap
        trap_speed = _interpolate_speed_at_distance(v_run, d_run, QUARTER_MILE_M)
        if trap_speed is None:
            trap_speed = float(v_run[int(np.searchsorted(d_run, QUARTER_MILE_M))])

        # Find trap index (how many samples past launch to keep)
        trap_raw_idx = int(np.searchsorted(d_run, QUARTER_MILE_M))
        post_samples = int(_detect_sample_rate(t) * POST_TRAP_MARGIN_S)
        end_idx_local = min(trap_raw_idx + post_samples, len(v_run) - 1)

        runs.append((launch_idx, launch_idx + end_idx_local, et, trap_speed))

    return runs


# ─── CSV parsing ──────────────────────────────────────────────────────────


def _parse_csv_body(
    rows: list[list[str]],
    header: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Parse CSV rows into (t_s, v_ms, d_m_or_None) numpy arrays.
    d_m is None when there is no distance column (we integrate from v later).
    """
    speed_unit, dist_unit, _ = _detect_csv_units(header)

    t_col = _col_index(header, ["time (s)", "time_s", "time", "t", "elapsed"])
    v_col = _col_index(
        header,
        [
            "speed (mph)",
            "speed_mph",
            "speed (km/h)",
            "speed_kmh",
            "speed (m/s)",
            "speed_ms",
            "speed",
            "v",
            "velocity",
        ],
    )
    d_col = _col_index(
        header,
        [
            "distance (ft)",
            "dist_ft",
            "distance_ft",
            "distance (m)",
            "distance_m",
            "dist_m",
            "distance",
            "dist",
            "d",
        ],
    )

    if t_col == -1:
        raise DragParseError(f"Cannot find time column in CSV header: {header}")
    if v_col == -1:
        raise DragParseError(f"Cannot find speed column in CSV header: {header}")

    ts, vs, ds = [], [], []
    for row in rows:
        try:
            ts.append(float(row[t_col]))
            vs.append(float(row[v_col]))
            if d_col != -1 and d_col < len(row):
                ds.append(float(row[d_col]))
        except (ValueError, IndexError):
            continue  # skip malformed rows

    if len(ts) < 10:
        raise DragParseError("CSV contains fewer than 10 valid data rows.")

    t_arr = np.array(ts)
    v_arr = _to_si_velocity(np.array(vs), speed_unit)
    d_arr = _to_si_distance(np.array(ds), dist_unit) if ds else None

    return t_arr, v_arr, d_arr


def _parse_csv(path: Path) -> list[DragRunData]:
    """Parse a Dragy-format CSV file. Returns list of DragRunData."""
    metadata: dict = {}

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        all_rows = list(reader)

    # Skip blank/comment lines at top; find header
    header_idx = 0
    for i, row in enumerate(all_rows):
        if not row or all(c.strip() == "" for c in row):
            continue
        # Heuristic: header has at least one of these words
        combined = " ".join(row).lower()
        if any(
            kw in combined for kw in ["time", "speed", "velocity", "distance", "dist"]
        ):
            header_idx = i
            break
        # Otherwise treat as metadata key=value
        if "=" in " ".join(row) or (len(row) >= 2 and row[1] == ""):
            metadata[row[0].strip()] = row[1].strip() if len(row) > 1 else ""

    header = [c.strip() for c in all_rows[header_idx]]
    data_rows = [
        [c.strip() for c in row]
        for row in all_rows[header_idx + 1 :]
        if row and any(c.strip() for c in row)
    ]

    t_arr, v_arr, d_arr_raw = _parse_csv_body(data_rows, header)

    # Use provided distance only if monotonically non-decreasing from launch
    if d_arr_raw is not None and np.all(np.diff(d_arr_raw) >= -0.01):
        d_arr = d_arr_raw
    else:
        d_arr = None  # will integrate from velocity

    return _build_run_list(t_arr, v_arr, d_arr, str(path), metadata)


# ─── JSON parsing ─────────────────────────────────────────────────────────


def _parse_json(path: Path) -> list[DragRunData]:
    """Parse a Dragy-app JSON file. Returns list of DragRunData."""
    with open(path, encoding="utf-8-sig") as fh:
        payload = json.load(fh)

    metadata = payload.get("meta", {})
    runs_raw = payload.get("runs", [payload])  # single-run files omit "runs" key

    results: list[DragRunData] = []

    for run_idx, run_obj in enumerate(runs_raw):
        samples = run_obj.get("samples", run_obj.get("data", []))
        if not samples:
            continue

        # Auto-detect speed/distance keys
        first = samples[0]
        t_key = next((k for k in ["t", "time", "time_s"] if k in first), None)
        v_keys_mph = [k for k in first if "mph" in k.lower() or k in ("v", "speed")]
        v_keys_kmh = [k for k in first if "km" in k.lower() or "kmh" in k.lower()]
        v_keys_ms = [
            k
            for k in first
            if "m/s" in k.lower() or k.lower() == "ms" or k.lower().endswith("_ms")
        ]

        if t_key is None:
            raise DragParseError(f"JSON run {run_idx}: no time key found in samples.")

        # Pick speed key and unit
        if v_keys_ms:
            v_key, v_unit = v_keys_ms[0], "ms"
        elif v_keys_kmh:
            v_key, v_unit = v_keys_kmh[0], "kmh"
        elif v_keys_mph:
            v_key, v_unit = v_keys_mph[0], "mph"
        else:
            raise DragParseError(f"JSON run {run_idx}: no recognisable speed key.")

        # Distance key (optional)
        d_keys_m = [
            k for k in first if "dist_m" in k or "distance_m" in k or k == "d_m"
        ]
        d_keys_ft = [
            k for k in first if "dist_ft" in k or "distance_ft" in k or k == "d_ft"
        ]
        d_key: str | None = None
        d_unit = "m"
        if d_keys_m:
            d_key, d_unit = d_keys_m[0], "m"
        elif d_keys_ft:
            d_key, d_unit = d_keys_ft[0], "ft"

        ts, vs, ds = [], [], []
        for s in samples:
            try:
                ts.append(float(s[t_key]))
                vs.append(float(s[v_key]))
                if d_key and d_key in s:
                    ds.append(float(s[d_key]))
            except (KeyError, ValueError, TypeError):
                continue

        if len(ts) < 10:
            continue

        t_arr = np.array(ts)
        v_arr = _to_si_velocity(np.array(vs), v_unit)
        d_arr = _to_si_distance(np.array(ds), d_unit) if ds else None

        run_meta = {**metadata, **{k: run_obj[k] for k in run_obj if k != "samples"}}
        partial = _build_run_list(t_arr, v_arr, d_arr, str(path), run_meta)
        for r in partial:
            r.run_index = run_idx + len(results)
        results.extend(partial)

    return results


# ─── Run assembly ─────────────────────────────────────────────────────────


def _build_run_list(
    t_arr: np.ndarray,
    v_arr: np.ndarray,
    d_arr: np.ndarray | None,
    source: str,
    metadata: dict,
) -> list[DragRunData]:
    """
    Given full-file SI arrays, detect run boundaries and return DragRunData
    objects (one per valid run).
    """
    sample_rate = _detect_sample_rate(t_arr)

    # Use provided distance for boundary checks only if it's plausible;
    # we always re-integrate from v within each detected run to stay
    # independent of GPS drift accumulation.
    d_for_detection = d_arr if d_arr is not None else _integrate_distance(t_arr, v_arr)

    detected = _detect_runs(t_arr, v_arr, d_for_detection)
    if not detected:
        return []

    results = []
    for run_num, (launch_idx, end_idx, et_quarter, trap_speed) in enumerate(detected):
        t_slice = t_arr[launch_idx : end_idx + 1].copy()
        v_slice = v_arr[launch_idx : end_idx + 1].copy()

        # Re-zero time and re-integrate distance within this slice
        t_slice -= t_slice[0]
        d_slice = _integrate_distance(t_slice, v_slice)
        a_slice = _compute_acceleration(t_slice, v_slice)

        results.append(
            DragRunData(
                timestamps=t_slice,
                velocity_ms=v_slice,
                distance_m=d_slice,
                acceleration_ms2=a_slice,
                et_quarter=et_quarter,
                trap_speed_ms=trap_speed,
                sample_rate_hz=sample_rate,
                source_file=source,
                run_index=run_num,
                raw_metadata=metadata,
            )
        )

    return results


# ─── Public API ───────────────────────────────────────────────────────────


def parse_dragy_file(path: str | Path) -> list[DragRunData]:
    """
    Parse a Dragy GPS timer file and return all detected quarter-mile runs.

    Parameters
    ----------
    path : str or Path
        Path to a .csv or .json Dragy export file.

    Returns
    -------
    list[DragRunData]
        One entry per detected valid run.  Empty list if no valid run found.

    Raises
    ------
    DragParseError
        If the file format is unrecognised or the file is malformed.
    FileNotFoundError
        If the path does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dragy file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        return _parse_json(path)
    elif suffix in {".csv", ".txt", ""}:
        return _parse_csv(path)
    else:
        # Try CSV first, then JSON
        try:
            return _parse_csv(path)
        except (DragParseError, UnicodeDecodeError):
            try:
                return _parse_json(path)
            except (DragParseError, json.JSONDecodeError, KeyError) as exc:
                raise DragParseError(
                    f"Unrecognised file format for {path.name}: {exc}"
                ) from exc


def best_run(runs: list[DragRunData]) -> DragRunData | None:
    """Return the run with the lowest ET. Returns None if list is empty."""
    if not runs:
        return None
    return min(runs, key=lambda r: r.et_quarter)
