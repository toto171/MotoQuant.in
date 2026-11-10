"""
MotoQuant — Dragy GPS Import
============================
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
import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ─── Physical constants ────────────────────────────────────────────────────
from ..constants import QUARTER_MILE_M  # single source of truth (402.336 m)

log = logging.getLogger(__name__)

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

# Hard cap on samples per file. Dragy logs at 10-25 Hz, so 400k samples is
# 4.4 h of continuous recording at 25 Hz — far beyond any real session. The
# cap bounds parse memory/CPU for anonymous uploads (/api/calibrate/dragy).
MAX_SAMPLES: int = 400_000

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


def _speed_unit_from_label(label: str) -> str | None:
    """Speed unit named by ONE column label, or None when it names none."""
    lab = label.strip().lower()
    if any(tok in lab for tok in ("km/h", "kmh", "km_h", "kph", "km/hr")):
        return "kmh"
    if "mph" in lab or "mi/h" in lab:
        return "mph"
    if "m/s" in lab or "mps" in lab or re.search(r"(^|[\s_(\[])ms[)\]]?$", lab):
        return "ms"
    return None


def _dist_unit_from_label(label: str) -> str | None:
    """Distance unit named by ONE column label, or None when it names none."""
    lab = label.strip().lower()
    if any(tok in lab for tok in ("(ft)", "[ft]", "_ft", "feet", "foot")) or (
        re.search(r"\sft$", lab)
    ):
        return "ft"
    if any(tok in lab for tok in ("(m)", "[m]", "_m", "meter", "metre")) or (
        re.search(r"\sm$", lab)
    ):
        return "m"
    return None


def _detect_csv_units(
    header: list[str], speed_col: int = -1, dist_col: int = -1
) -> tuple[str, str, str]:
    """
    Infer speed and distance units from the SELECTED columns' own labels.

    Returns (speed_unit, dist_unit, time_unit) where each is one of:
        speed_unit : 'mph' | 'kmh' | 'ms'
        dist_unit  : 'ft'  | 'm'
        time_unit  : 's'

    Units are read from the speed / distance column label only — never from
    the joined header. A joined-header scan let an unrelated column flip the
    speed unit: 'Accel (m/s2)' next to 'Speed (mph)' made every mph value be
    read as m/s (ET 7.05 s / 357 km/h for an 11.3 s run). With no unit in the
    speed label the historical imperial default (mph) is kept and a warning
    is logged so the assumption is never silent.
    """
    speed_unit = None
    if 0 <= speed_col < len(header):
        speed_unit = _speed_unit_from_label(header[speed_col])
    if speed_unit is None:
        speed_unit = "mph"  # default (older Dragy is imperial)
        if 0 <= speed_col < len(header):
            log.warning(
                "Dragy CSV: speed column %r names no unit; assuming mph",
                header[speed_col],
            )

    dist_unit = None
    if 0 <= dist_col < len(header):
        dist_unit = _dist_unit_from_label(header[dist_col])
    if dist_unit is None:
        dist_unit = "ft"

    return speed_unit, dist_unit, "s"


def _col_index(
    header: list[str], candidates: list[str], exclude: tuple[int, ...] = ()
) -> int:
    """Return index of first matching column name (case-insensitive). -1 if none.

    Candidates of one or two characters ('t', 'v', 'd') must match a column
    label EXACTLY (optionally followed by a parenthesised unit). As substrings
    they matched almost anything: 't' found the 'Distance' column before the
    'elapsed' candidate was ever tried, and 'd' matched 'Speed'. Columns in
    ``exclude`` (already assigned to another channel) are never returned.
    """
    h = [c.strip().lower() for c in header]
    bare = [re.sub(r"\s*[(\[][^)\]]*[)\]]\s*$", "", c).strip() for c in h]
    for candidate in candidates:
        c = candidate.lower()
        for i, col in enumerate(h):
            if i in exclude:
                continue
            if len(c) <= 2:
                if c == col or c == bare[i]:
                    return i
            elif c == col or col.startswith(c) or c in col:
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
    end_idx is inclusive.  Vectorised: one numpy pass over the file.
    """
    below = np.asarray(v_ms) < LAUNCH_VEL_THRESHOLD_MS
    if not below.any():
        return []
    edges = np.diff(np.concatenate(([0], below.astype(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)  # exclusive
    keep = (ends - starts) >= MIN_STAGE_FRAMES
    return list(zip(starts[keep].tolist(), (ends[keep] - 1).tolist()))


def _detect_runs(
    t: np.ndarray,
    v_ms: np.ndarray,
    d_m: np.ndarray | None = None,
    *,
    sample_rate: float | None = None,
) -> list[tuple[int, int, float, float]]:
    """
    Find all drag runs in continuous telemetry.

    Returns list of (launch_idx, trap_idx, et_quarter, trap_speed_ms).
    Each run begins immediately after a staged window and ends when the bike
    crosses or exceeds QUARTER_MILE_M from that launch point.

    ``d_m`` is accepted for backward compatibility and ignored: detection
    always integrates v(t) so GPS distance drift never moves the boundary.
    ``sample_rate`` (Hz) is computed from ``t`` when not given.

    Cost is O(N log N) in the file length, whatever the number of staged
    windows. The previous version re-integrated the WHOLE remainder of the
    file (and re-took the median sample rate) for every staged window —
    O(windows x N) — so a ~1 MB crafted upload of "5 idle rows + 1 fast row"
    repeated pinned the API CPU for tens of seconds, and the 25 MB upload cap
    for hours. Now one cumulative-distance prefix sum answers "where does
    this launch reach 402 m" by binary search, and only ACCEPTED runs are
    re-integrated locally (over their own <= 30 s + 1 s slice). Accepted runs
    report exactly the ET / trap the old per-window integration produced
    (same prefix of the same cumulative sum).

    A launch whose bike re-stages (the next staged window begins) before it
    has covered 402 m is an aborted run and is rejected. Previously such a
    launch "reached the quarter" by integrating straight through the stop
    and the relaunch, producing a bogus extra run (e.g. ET 21.3 s with a
    5.9 m/s trap) overlapping the real one.
    """
    v_ms = np.asarray(v_ms, dtype=float)
    t = np.asarray(t, dtype=float)
    n = len(v_ms)
    if n < 2:
        return []
    staged_windows = _find_staged_windows(v_ms)
    if not staged_windows:
        return []

    if sample_rate is None:
        sample_rate = _detect_sample_rate(t)
    min_frames = int(sample_rate * MIN_RUN_DURATION_S)
    post_samples = int(sample_rate * POST_TRAP_MARGIN_S)

    # One pass each, shared by every candidate launch below.
    cum = _integrate_distance(t, v_ms)  # distance from file start
    suffix_peak = np.maximum.accumulate(v_ms[::-1])[::-1]  # max(v[i:])

    runs = []

    for w, (_win_start, win_end) in enumerate(staged_windows):
        # Launch = first frame after the (maximal) staged window, which is
        # above threshold by construction.
        launch_idx = win_end + 1
        if launch_idx >= n:
            continue

        # Check there are enough frames after launch
        if n - launch_idx < min_frames:
            continue
        # Peak-speed sanity check over the rest of the file (same span the
        # per-window version tested), in O(1).
        if float(suffix_peak[launch_idx]) < MIN_PEAK_SPEED_MS:
            continue

        # Must reach 1/4 mile: binary search the prefix sum.
        base = cum[launch_idx]
        k = launch_idx + int(np.searchsorted(cum[launch_idx:], base + QUARTER_MILE_M))
        if k >= n:
            continue
        # Aborted run: the bike re-staged (next staged window) before 402 m.
        if w + 1 < len(staged_windows) and staged_windows[w + 1][0] < k:
            continue
        d0, d1 = cum[k - 1] - base, cum[k] - base
        t0, t1 = t[k - 1] - t[launch_idx], t[k] - t[launch_idx]
        frac = (QUARTER_MILE_M - d0) / (d1 - d0) if (d1 - d0) > 0 else 0.0
        et = float(t0 + frac * (t1 - t0))
        trap_speed = float(v_ms[k - 1] + frac * (v_ms[k] - v_ms[k - 1]))

        # Sanity checks
        if et < MIN_RUN_DURATION_S or et > MAX_RUN_DURATION_S:
            continue

        # Accepted. Re-integrate locally from the launch frame to just past
        # the crossing, so the reported ET / trap are bit-identical to the
        # old per-window integration (the local cumsum is a prefix of the
        # old whole-remainder cumsum). The +3 margin absorbs rounding
        # between the global and local sums.
        hi = min(k + 3, n)
        t_run = t[launch_idx:hi] - t[launch_idx]  # re-zero time
        v_run = v_ms[launch_idx:hi]
        d_run = _integrate_distance(t_run, v_run)
        et_local = _interpolate_et(t_run, d_run, QUARTER_MILE_M)
        trap_raw_idx = int(np.searchsorted(d_run, QUARTER_MILE_M))
        if et_local is not None and trap_raw_idx < len(d_run):
            et = et_local
            trap_speed = _interpolate_speed_at_distance(v_run, d_run, QUARTER_MILE_M)
        else:
            trap_raw_idx = k - launch_idx

        # Find trap index (how many samples past launch to keep): the
        # POST_TRAP_MARGIN_S worth of frames at the file's median rate, but
        # never more than 1.5x that margin in TIME. The time cap only bites
        # on files whose local sample density differs from the median (it
        # stops crafted dense/sparse mixes from making every accepted run's
        # slice — and the arrays _build_run_list copies — span most of the
        # file); on uniform-rate files the frame count is always tighter.
        trap_idx = launch_idx + trap_raw_idx
        end_by_frames = launch_idx + min(
            trap_raw_idx + post_samples, n - launch_idx - 1
        )
        end_by_time = trap_idx + max(
            int(
                np.searchsorted(
                    t[trap_idx:],
                    t[trap_idx] + 1.5 * POST_TRAP_MARGIN_S,
                    side="right",
                )
            )
            - 1,
            0,
        )
        end_idx = min(end_by_frames, end_by_time)

        runs.append((launch_idx, end_idx, et, trap_speed))

    return runs


# ─── CSV parsing ──────────────────────────────────────────────────────────


_T_CANDIDATES = ["time (s)", "time_s", "time", "elapsed", "t"]
_V_CANDIDATES = [
    "speed (mph)",
    "speed_mph",
    "speed (km/h)",
    "speed_kmh",
    "speed (m/s)",
    "speed_ms",
    "speed",
    "velocity",
    "v",
]
_D_CANDIDATES = [
    "distance (ft)",
    "dist_ft",
    "distance_ft",
    "distance (m)",
    "distance_m",
    "dist_m",
    "distance",
    "dist",
    "d",
]


def _resolve_csv_columns(header: list[str]) -> tuple[int, int, int]:
    """(t_col, v_col, d_col) for a CSV header; each channel gets its own column."""
    t_col = _col_index(header, _T_CANDIDATES)
    v_col = _col_index(header, _V_CANDIDATES, exclude=(t_col,))
    d_col = _col_index(header, _D_CANDIDATES, exclude=(t_col, v_col))
    if t_col == -1:
        raise DragParseError(f"Cannot find time column in CSV header: {header}")
    if v_col == -1:
        raise DragParseError(f"Cannot find speed column in CSV header: {header}")
    return t_col, v_col, d_col


def _parse_float(cell) -> float | None:
    """float(cell) when it is a finite number, else None (blank/null/text/nan)."""
    try:
        x = float(cell)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _check_sample_cap(n: int) -> None:
    if n > MAX_SAMPLES:
        raise DragParseError(
            f"File has more than {MAX_SAMPLES:,} samples — too long for a "
            "Dragy session export. Trim it to the runs you want to analyse."
        )


def _parse_csv_body(
    rows,
    header: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Parse CSV rows into (t_s, v_ms, d_m_or_None) numpy arrays.
    d_m is None when there is no distance column (we integrate from v later).

    A row is kept only when BOTH its time and speed cells are finite numbers;
    the cells are parsed into locals and appended together, so a blank or
    non-numeric cell skips the whole row. (Appending field by field left the
    time list one longer than the speed list after a blank speed cell, and
    the parse died on a numpy broadcast error instead of skipping the row.)
    The optional distance column is parsed best-effort: one bad distance cell
    discards the distance channel, never a time/speed row.
    """
    t_col, v_col, d_col = _resolve_csv_columns(header)
    speed_unit, dist_unit, _ = _detect_csv_units(header, v_col, d_col)

    ts, vs, ds = [], [], []
    d_ok = d_col != -1
    for row in rows:
        if not row or not any(str(c).strip() for c in row):
            continue
        tv = _parse_float(row[t_col]) if t_col < len(row) else None
        vv = _parse_float(row[v_col]) if v_col < len(row) else None
        if tv is None or vv is None:
            continue  # skip malformed rows
        ts.append(tv)
        vs.append(vv)
        _check_sample_cap(len(ts))
        if d_ok:
            dv = _parse_float(row[d_col]) if d_col < len(row) else None
            if dv is None:
                d_ok = False
            else:
                ds.append(dv)

    if len(ts) < 10:
        raise DragParseError("CSV contains fewer than 10 valid data rows.")

    t_arr = np.array(ts)
    v_arr = _to_si_velocity(np.array(vs), speed_unit)
    d_arr = _to_si_distance(np.array(ds), dist_unit) if d_ok and ds else None

    return t_arr, v_arr, d_arr


def _parse_csv(path: Path) -> list[DragRunData]:
    """Parse a Dragy-format CSV file. Returns list of DragRunData.

    Streams the file (never holds every row in memory) and stops with a
    DragParseError past MAX_SAMPLES data rows.
    """
    metadata: dict = {}

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)

        # Skip blank/comment lines at top; find header
        header = None
        for row in reader:
            if not row or all(c.strip() == "" for c in row):
                continue
            # Heuristic: header has at least one of these words
            combined = " ".join(row).lower()
            if any(
                kw in combined
                for kw in ["time", "speed", "velocity", "distance", "dist"]
            ):
                header = [c.strip() for c in row]
                break
            # Otherwise treat as metadata key=value
            if "=" in " ".join(row) or (len(row) >= 2 and row[1] == ""):
                metadata[row[0].strip()] = row[1].strip() if len(row) > 1 else ""

        if header is None:
            raise DragParseError("CSV has no recognisable header row.")

        data_rows = ([c.strip() for c in row] for row in reader)
        t_arr, v_arr, d_arr_raw = _parse_csv_body(data_rows, header)

    # Use provided distance only if monotonically non-decreasing from launch
    if d_arr_raw is not None and np.all(np.diff(d_arr_raw) >= -0.01):
        d_arr = d_arr_raw
    else:
        d_arr = None  # will integrate from velocity

    return _build_run_list(t_arr, v_arr, d_arr, str(path), metadata)


# ─── JSON parsing ─────────────────────────────────────────────────────────


def _parse_json(path: Path) -> list[DragRunData]:
    """Parse a Dragy-app JSON file. Returns list of DragRunData.

    Expected shape: an object, optionally with "meta" (object) and "runs"
    (array of objects, each with a "samples" or "data" array of sample
    objects). A single-run file may omit "runs". Anything else raises a
    DragParseError — never an AttributeError/TypeError from deep inside.
    """
    with open(path, encoding="utf-8-sig") as fh:
        payload = json.load(fh)

    if not isinstance(payload, dict):
        raise DragParseError(
            "Dragy JSON must be an object with a 'runs' list "
            f"(got a top-level {type(payload).__name__})."
        )

    metadata = payload.get("meta", {})
    if not isinstance(metadata, dict):
        metadata = {}
    runs_raw = payload.get("runs", [payload])  # single-run files omit "runs" key
    if not isinstance(runs_raw, list):
        raise DragParseError("Dragy JSON 'runs' must be a list of run objects.")

    results: list[DragRunData] = []
    total_samples = 0

    for run_idx, run_obj in enumerate(runs_raw):
        if not isinstance(run_obj, dict):
            raise DragParseError(f"JSON run {run_idx}: expected an object.")
        samples = run_obj.get("samples", run_obj.get("data", []))
        if not isinstance(samples, list):
            raise DragParseError(f"JSON run {run_idx}: 'samples' must be a list.")
        if not samples:
            continue
        total_samples += len(samples)
        _check_sample_cap(total_samples)

        # Auto-detect speed/distance keys
        first = samples[0]
        if not isinstance(first, dict):
            raise DragParseError(
                f"JSON run {run_idx}: samples must be objects, "
                f"got {type(first).__name__}."
            )
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

        # Same row-atomic rule as the CSV path: a sample is kept only when
        # both t and speed are finite numbers (a null speed used to append
        # t but not v, desyncing the arrays).
        ts, vs, ds = [], [], []
        d_ok = d_key is not None
        for s in samples:
            if not isinstance(s, dict):
                continue
            tv = _parse_float(s.get(t_key))
            vv = _parse_float(s.get(v_key))
            if tv is None or vv is None:
                continue
            ts.append(tv)
            vs.append(vv)
            if d_ok:
                dv = _parse_float(s.get(d_key))
                if dv is None:
                    d_ok = False
                else:
                    ds.append(dv)

        if len(ts) < 10:
            continue

        t_arr = np.array(ts)
        v_arr = _to_si_velocity(np.array(vs), v_unit)
        d_arr = _to_si_distance(np.array(ds), d_unit) if d_ok and ds else None

        run_meta = {**metadata, **{k: run_obj[k] for k in run_obj if k != "samples"}}
        partial = _build_run_list(t_arr, v_arr, d_arr, str(path), run_meta)
        # 0-based index across the whole file. (Was run_idx + len(results),
        # which double-counted and numbered three runs 0, 2, 4.)
        for k, r in enumerate(partial):
            r.run_index = len(results) + k
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
    _check_sample_cap(len(t_arr))
    sample_rate = _detect_sample_rate(t_arr)

    # A provided GPS distance column is never used for detection: we always
    # integrate v(t) from each launch to stay independent of GPS drift
    # accumulation. The sample rate is computed once per file (it used to be
    # recomputed — a full-file median — for every staged window).
    detected = _detect_runs(t_arr, v_arr, sample_rate=sample_rate)
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
