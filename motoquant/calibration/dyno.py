"""
MotoQuant — Dyno Curve Import
=============================
Parse dynamometer output files (CSV), apply SAE J1349 atmospheric correction,
and return a DynoCurve ready for injection into BikeConfig.engine.dyno_curve.

Supported formats
-----------------
DynoJet    : RPM, WHP (or HP), TQ (lb-ft)    — most common motorcycle chassis dyno
Generic HP : any CSV with RPM + power in hp/kW/PS or torque in Nm/lb-ft
MoTeC lite : tab-separated channel export with "Engine Speed" + "Engine Power" channels

SAE J1349 Correction
--------------------
The standard correction factor adjusts measured power to what would be produced at
"standard" conditions: 25 °C, 99 kPa dry-air pressure, 0% humidity.

    CF = 1.18 × (99.0 / Pd) × √(Tm / 298.15) − 0.18

where:
    Pd = dry air pressure [kPa]  = total barometric pressure − water vapour pressure
    Tm = inlet air temperature [K]

The 1.18 / −0.18 terms are the standard's mechanical-efficiency allowance
(SAE J1349 JUN90 / AUG2004, and DynoJet's "SAE" mode): friction losses do
not scale with air density, so only ~85% of the deviation in indicated power
is corrected. Without them every deviation from CF = 1 is overstated by 18%.

Power_corrected = Power_measured × CF

Ambient inputs are validated: pressure must be absolute barometric pressure
(kPa, or unambiguously hPa / bar / inHg / psi — auto-converted with a logged
note), temperature −30…60 °C, humidity 0…100 %. Both temperature and pressure
are required for a correction; with neither, the measured power is returned
uncorrected (CF = 1.0); with only one, DynoInputError is raised rather than
silently skipping the correction.

Public API
----------
    from motoquant.calibration.dyno import parse_dyno_file, DynoResult

    result = parse_dyno_file("dynorun.csv", temp_c=28, pressure_kpa=101.3, rh_pct=60)
    curve   = result.curve           # DynoCurve — inject into BikeConfig
    print(result.correction_factor)  # SAE J1349 CF applied
"""

import csv
import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..models import DynoCurve

log = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────

HP_TO_KW: float = 0.745699872
KW_TO_HP: float = 1.0 / HP_TO_KW
PS_TO_KW: float = 0.735499
LBFT_TO_NM: float = 1.35582

# SAE J1349 standard reference conditions
SAE_REF_TEMP_K: float = 298.15  # 25 °C
SAE_REF_PRESSURE_KPA: float = 99.0  # kPa dry air
# SAE J1349 mechanical-efficiency terms: CF = A·(99/Pd)·√(T/298) − B
SAE_CF_SCALE: float = 1.18
SAE_CF_OFFSET: float = 0.18

# Plausible ambient inputs (absolute barometric pressure 60-110 kPa covers
# sea level to ~4,000 m). Values outside are input mistakes, not weather.
PRESSURE_KPA_RANGE: tuple[float, float] = (60.0, 110.0)
TEMP_C_RANGE: tuple[float, float] = (-30.0, 60.0)
RH_PCT_RANGE: tuple[float, float] = (0.0, 100.0)
# J1349's recommended correction window; outside it CF is still applied but
# a note is logged (high-altitude dynos legitimately exceed it).
SAE_CF_ADVISORY_RANGE: tuple[float, float] = (0.85, 1.20)

# Pressure units we auto-convert. Each unit's plausible span (the kPa range
# expressed in that unit) is disjoint from the others, so a value maps to at
# most one unit. DynoJet sheets print barometer in inHg (29.92 = sea level).
_PRESSURE_UNITS: tuple[tuple[str, float], ...] = (
    ("kPa", 1.0),
    ("hPa", 0.1),
    ("bar", 100.0),
    ("inHg", 3.386389),
    ("psi", 6.894757),
)

RPM_MIN: float = 500.0
RPM_MAX: float = 22000.0
PEAK_POWER_KW_MAX: float = 1000.0  # sanity upper bound
PEAK_TORQUE_NM_MAX: float = 5000.0


class DynoParseError(Exception):
    """Raised when a dyno file cannot be parsed or contains invalid data."""


class DynoInputError(DynoParseError, ValueError):
    """Raised when the ambient conditions passed for SAE correction are invalid."""


# ─── Result container ─────────────────────────────────────────────────────


@dataclass
class DynoResult:
    """Parsed and SAE-corrected dyno output."""

    curve: DynoCurve  # Inject into BikeConfig.engine.dyno_curve
    rpm: np.ndarray  # RPM points (same as curve.rpm)
    power_kw: np.ndarray  # Corrected power at wheel [kW]
    torque_nm: np.ndarray  # Corrected torque at wheel [Nm]
    correction_factor: float  # SAE J1349 CF applied (1.0 = uncorrected)
    peak_power_kw: float
    peak_torque_nm: float
    rpm_at_peak_power: float
    rpm_at_peak_torque: float
    is_at_wheel: bool = True  # chassis dyno = True
    source_file: str = ""
    raw_metadata: dict = field(default_factory=dict)

    @property
    def peak_power_hp(self) -> float:
        return self.peak_power_kw * KW_TO_HP

    @property
    def peak_torque_lbft(self) -> float:
        return self.peak_torque_nm / LBFT_TO_NM

    def to_dict(self) -> dict:
        return {
            "peak_power_kw": round(self.peak_power_kw, 2),
            "peak_power_hp": round(self.peak_power_hp, 1),
            "peak_torque_nm": round(self.peak_torque_nm, 2),
            "rpm_at_peak_power": round(self.rpm_at_peak_power, 0),
            "rpm_at_peak_torque": round(self.rpm_at_peak_torque, 0),
            "correction_factor": round(self.correction_factor, 5),
            "is_at_wheel": self.is_at_wheel,
            "source_file": self.source_file,
        }


# ─── SAE J1349 correction ─────────────────────────────────────────────────


def _saturated_vapour_pressure_kpa(temp_c: float) -> float:
    """
    Antoine equation for water saturation pressure [kPa].
    Valid range: 1–100 °C.
    """
    # Constants for Antoine equation (log10, T in °C, P in mmHg)
    A, B, C = 8.07131, 1730.63, 233.426
    p_mmhg = 10 ** (A - B / (temp_c + C))
    return p_mmhg * 0.133322  # mmHg → kPa


def normalize_pressure_kpa(pressure: float) -> tuple[float, str | None]:
    """
    Return (pressure_kpa, note) for a barometric reading in kPa, or in an
    unambiguous other unit (hPa/mbar, bar, inHg, psi) which is converted.

    ``note`` is None when the value was already kPa, else a human-readable
    description of the conversion. Raises DynoInputError when the value fits
    no unit's plausible span (e.g. 50 — neither kPa nor anything else).
    """
    p = float(pressure)
    if not math.isfinite(p):
        raise DynoInputError(f"pressure must be a finite number, got {pressure!r}")
    lo, hi = PRESSURE_KPA_RANGE
    for unit, to_kpa in _PRESSURE_UNITS:
        kpa = p * to_kpa
        if lo <= kpa <= hi:
            if unit == "kPa":
                return kpa, None
            return kpa, f"pressure {p:g} read as {unit} -> {kpa:.2f} kPa"
    raise DynoInputError(
        f"pressure {p:g} is not a plausible absolute barometric pressure: "
        f"expected {lo:g}-{hi:g} kPa (or the same range in hPa, bar, inHg or psi)"
    )


def _validate_ambient(temp_c: float, pressure_kpa: float, rh_pct: float) -> None:
    """Raise DynoInputError unless temp/pressure(kPa)/RH are physically plausible."""
    checks = (
        ("temp_c", temp_c, TEMP_C_RANGE, "°C"),
        ("pressure_kpa", pressure_kpa, PRESSURE_KPA_RANGE, "kPa"),
        ("rh_pct", rh_pct, RH_PCT_RANGE, "%"),
    )
    for name, value, (lo, hi), unit in checks:
        if value is None or not math.isfinite(float(value)):
            raise DynoInputError(f"{name} must be a finite number, got {value!r}")
        if not (lo <= float(value) <= hi):
            raise DynoInputError(
                f"{name}={float(value):g} is outside the plausible range "
                f"{lo:g}-{hi:g} {unit}"
            )


def sae_j1349_correction_factor(
    temp_c: float,
    pressure_kpa: float,
    rh_pct: float = 0.0,
) -> float:
    """
    Compute the SAE J1349 atmospheric correction factor.

        CF = 1.18 × (99 / Pd) × √(T / 298.15) − 0.18

    Pd is the dry-air partial pressure (barometric minus water-vapour
    pressure) and T the inlet air temperature in kelvin. The 1.18 / −0.18
    terms are the standard's mechanical-efficiency allowance; the friction-
    free form ``(99/Pd)·√(T/298)`` (used here until 2026-10-24) overstates
    every deviation from 1.0 by 18% — e.g. 35 °C / 95 kPa / 60% RH gave
    CF 1.098 where J1349 (and DynoJet's SAE mode) gives 1.116.

    Parameters
    ----------
    temp_c       : Inlet air temperature [°C], −30…60
    pressure_kpa : Absolute barometric pressure [kPa], 60…110
    rh_pct       : Relative humidity [%] (0–100)

    Returns
    -------
    float : Correction factor — multiply measured power by this.

    Raises
    ------
    DynoInputError (a ValueError) when an input is outside its plausible
    range. Pressure in inHg/bar/hPa must be converted first — see
    ``normalize_pressure_kpa`` (parse_dyno_file does this automatically).
    """
    _validate_ambient(temp_c, pressure_kpa, rh_pct)
    temp_k = temp_c + 273.15
    p_sat = _saturated_vapour_pressure_kpa(temp_c)
    p_vapour = (rh_pct / 100.0) * p_sat
    p_dry = max(pressure_kpa - p_vapour, 0.1)

    # NOTE the direction of the temperature ratio: sqrt(Tm / Tref), NOT
    # sqrt(Tref / Tm). This shipped inverted until the 2026-07-25 audit, which
    # contradicted BOTH the SAE J1349 standard and this module's own documented
    # formula at the top of the file.
    #
    # Physically: hot air is less dense, so the engine makes LESS power on the
    # dyno, and the correction to standard 25 C must scale it UP -> CF must rise
    # with temperature. The inverted form fell instead, so a 190 hp run measured
    # on a 40 C Pune/Chennai dyno day was reported as 185.4 hp when SAE requires
    # 195.6 hp -- a ~5% error in the wrong direction, growing to ~8% at 0 C.
    density_ratio = (SAE_REF_PRESSURE_KPA / p_dry) * math.sqrt(temp_k / SAE_REF_TEMP_K)
    cf = SAE_CF_SCALE * density_ratio - SAE_CF_OFFSET
    return float(cf)


# ─── Column detection helpers ─────────────────────────────────────────────


def _col_index(header: list[str], candidates: list[str]) -> int:
    """Return index of first matching column (case-insensitive substring). -1 if none."""
    h = [c.strip().lower() for c in header]
    for candidate in candidates:
        c = candidate.lower()
        for i, col in enumerate(h):
            if c == col or c in col or col.startswith(c):
                return i
    return -1


def _detect_power_unit(header: list[str], col_idx: int) -> str:
    """Infer power unit from column header text."""
    if col_idx < 0:
        return "kw"
    label = header[col_idx].lower()
    if "hp" in label or "whp" in label or "bhp" in label or "horsepower" in label:
        return "hp"
    if "ps" in label:
        return "ps"
    return "kw"  # default for unlabelled or "(kw)" headers


def _detect_torque_unit(header: list[str], col_idx: int) -> str | None:
    """Torque unit named by the column header, or None when it names none.

    A bare 'TQ' / 'Torque' label returns None so the caller can infer the
    unit (see _resolve_torque_unit) instead of assuming Nm: DynoJet's own
    'RPM,WHP,TQ' export is lb-ft, and reading it as Nm cut the injected
    torque curve by 26%.
    """
    if col_idx < 0:
        return None
    label = header[col_idx].lower()
    # 'ft' only as a token (lb-ft, ft-lb, '(ft)'), never inside a word: a bare
    # substring test read 'Shaft Torque' as lb-ft.
    if "lb" in label or re.search(r"(?<![a-z])ft(?![a-z])", label):
        return "lbft"
    if re.search(r"(?<![a-z])(nm|n\.m|n-m|newton)", label):
        return "nm"
    return None


def _power_torque_ratio(
    rpm: np.ndarray, power_kw: np.ndarray, torque_raw: np.ndarray
) -> float | None:
    """Median of (torque·ω / power) over rows with real power and torque.

    ≈ 1.0 when the torque column is Nm, ≈ 0.7376 (1 / 1.35582) when it is
    lb-ft. None when there are too few usable rows to judge.
    """
    mask = (power_kw > 1.0) & (torque_raw > 0) & (rpm > 1000)
    if int(mask.sum()) < 3:
        return None
    omega = rpm[mask] * (2 * math.pi / 60)
    return float(np.median(torque_raw[mask] * omega / 1000.0 / power_kw[mask]))


def _resolve_torque_unit(
    labelled_unit: str | None,
    power_unit: str,
    has_power_col: bool,
    rpm: np.ndarray,
    power_kw: np.ndarray,
    torque_raw: np.ndarray,
    metadata: dict,
) -> str:
    """Decide the torque unit, cross-checking against the power channel.

    * Unit named in the header -> use it, but warn (and record in metadata)
      when power and torque disagree by more than 5% under that unit.
    * Unnamed, with a power column -> infer from consistency: torque·ω/P is
      1.0 for Nm and 0.7376 for lb-ft. If the data is too ambiguous, fall
      back to the dyno convention: lb-ft when power is in hp, Nm otherwise.
    * Unnamed, no power column -> Nm (logged, since it is an assumption).
    """
    ratio = _power_torque_ratio(rpm, power_kw, torque_raw) if has_power_col else None
    lbft_ratio = 1.0 / LBFT_TO_NM

    if labelled_unit is not None:
        if ratio is not None:
            expected = 1.0 if labelled_unit == "nm" else lbft_ratio
            mismatch = abs(ratio / expected - 1.0)
            if mismatch > 0.05:
                metadata["power_torque_mismatch_pct"] = round(mismatch * 100, 1)
                log.warning(
                    "Dyno file: power and torque columns disagree by %.1f%% "
                    "(torque labelled %s); the torque column feeds the curve",
                    mismatch * 100,
                    labelled_unit,
                )
        return labelled_unit

    if ratio is not None:
        err_nm = abs(math.log(ratio))
        err_lbft = abs(math.log(ratio / lbft_ratio))
        if min(err_nm, err_lbft) < math.log(1.15):
            unit = "nm" if err_nm < err_lbft else "lbft"
            metadata["torque_unit_inferred"] = unit
            return unit

    unit = "lbft" if (has_power_col and power_unit == "hp") else "nm"
    metadata["torque_unit_assumed"] = unit
    log.warning("Dyno file: torque column names no unit; assuming %s", unit)
    return unit


def _to_kw(values: np.ndarray, unit: str) -> np.ndarray:
    if unit == "hp":
        return values * HP_TO_KW
    if unit == "ps":
        return values * PS_TO_KW
    return values


def _to_nm(values: np.ndarray, unit: str) -> np.ndarray:
    if unit == "lbft":
        return values * LBFT_TO_NM
    return values


def _nm_from_kw_and_rpm(power_kw: np.ndarray, rpm: np.ndarray) -> np.ndarray:
    """Derive torque from power. Avoid division by zero at idle."""
    safe_rpm = np.where(rpm > 50, rpm, 50)
    omega = safe_rpm * (2 * math.pi / 60)
    return power_kw * 1000.0 / omega


# ─── CSV parsing ──────────────────────────────────────────────────────────


def _parse_csv(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict, str]:
    """
    Parse a dyno CSV file.

    Returns (rpm, power_kw_raw, torque_nm_raw, metadata, format_name).
    power_kw_raw or torque_nm_raw may be zeros if that column is absent;
    the caller derives the missing one.
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        all_rows = list(csv.reader(fh))

    metadata: dict = {}
    header_idx = 0

    # Scan for header and extract any key=value metadata above it
    for i, row in enumerate(all_rows):
        if not row or all(c.strip() == "" for c in row):
            continue
        combined = " ".join(row).lower()
        # Header heuristic: contains "rpm" and at least one of power/torque keywords
        if "rpm" in combined and any(
            k in combined for k in ["power", "torque", "hp", "whp", "kw", "nm", "bhp"]
        ):
            header_idx = i
            break
        # Metadata key=value pairs above header
        if len(row) >= 2 and row[1]:
            metadata[row[0].strip()] = row[1].strip()

    header = [c.strip() for c in all_rows[header_idx]]
    data_rows = [
        [c.strip() for c in row]
        for row in all_rows[header_idx + 1 :]
        if row and any(c.strip() for c in row)
    ]

    if len(data_rows) < 5:
        raise DynoParseError(
            f"CSV has fewer than 5 data rows after header at line {header_idx + 1}"
        )

    # Detect columns
    rpm_col = _col_index(header, ["rpm", "engine speed", "speed"])
    pwr_col = _col_index(header, ["whp", "power", "kw", "hp", "bhp", "ps", "wkw"])
    tq_col = _col_index(header, ["torque", "tq", "nm", "lb-ft", "lbft", "ftlb", "wtq"])

    if rpm_col == -1:
        raise DynoParseError(f"Cannot find RPM column in: {header}")
    if pwr_col == -1 and tq_col == -1:
        raise DynoParseError(f"Cannot find power or torque column in: {header}")

    pwr_unit = _detect_power_unit(header, pwr_col)
    tq_label_unit = _detect_torque_unit(header, tq_col)

    rpms, pwrs, torqs = [], [], []
    for row in data_rows:
        try:
            r = float(row[rpm_col])
            if not (RPM_MIN <= r <= RPM_MAX):
                continue
            rpms.append(r)
            pwrs.append(
                float(row[pwr_col]) if pwr_col != -1 and pwr_col < len(row) else 0.0
            )
            torqs.append(
                float(row[tq_col]) if tq_col != -1 and tq_col < len(row) else 0.0
            )
        except (ValueError, IndexError):
            continue

    if len(rpms) < 5:
        raise DynoParseError("Fewer than 5 valid RPM rows after filtering.")

    rpm_arr = np.array(rpms)
    pwr_arr = _to_kw(np.array(pwrs), pwr_unit)
    tq_raw = np.array(torqs)
    tq_unit = (
        _resolve_torque_unit(
            tq_label_unit, pwr_unit, pwr_col != -1, rpm_arr, pwr_arr, tq_raw, metadata
        )
        if tq_col != -1
        else "nm"
    )
    tq_arr = _to_nm(tq_raw, tq_unit)

    # Sort by RPM (some dynos export descending)
    order = np.argsort(rpm_arr)
    return rpm_arr[order], pwr_arr[order], tq_arr[order], metadata, "generic_csv"


# ─── MoTeC tab-delimited (lite) ───────────────────────────────────────────


def _parse_motec_lite(
    path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict, str]:
    """
    Parse a MoTeC i2 tab-separated channel export with Engine Speed + Engine Power.
    Very basic — handles the common single-run export format.
    """
    with open(path, encoding="utf-8-sig") as fh:
        lines = fh.readlines()

    # Find channel labels line and unit line
    channels: list[str] = []
    units: list[str] = []
    data_start = 0
    for i, line in enumerate(lines):
        parts = [p.strip() for p in line.split("\t")]
        if any("engine speed" in p.lower() for p in parts):
            channels = parts
            units = (
                [p.strip() for p in lines[i + 1].split("\t")]
                if i + 1 < len(lines)
                else []
            )
            data_start = i + 2
            break

    if not channels:
        raise DynoParseError("MoTeC format: cannot find 'Engine Speed' channel header.")

    rpm_col = next(
        (i for i, c in enumerate(channels) if "engine speed" in c.lower()), -1
    )
    pwr_col = next(
        (
            i
            for i, c in enumerate(channels)
            if "engine power" in c.lower()
            or ("power" in c.lower() and "brake" not in c.lower())
        ),
        -1,
    )
    tq_col = next(
        (
            i
            for i, c in enumerate(channels)
            if "engine torque" in c.lower() or "torque" in c.lower()
        ),
        -1,
    )

    if rpm_col == -1:
        raise DynoParseError("MoTeC: Engine Speed channel not found.")

    pwr_unit_str = (
        units[pwr_col].lower() if pwr_col != -1 and pwr_col < len(units) else "kw"
    )
    pwr_unit = (
        "kw" if "kw" in pwr_unit_str else ("hp" if "hp" in pwr_unit_str else "kw")
    )

    tq_unit_str = units[tq_col] if tq_col != -1 and tq_col < len(units) else ""
    tq_label_unit = _detect_torque_unit([tq_unit_str], 0) if tq_unit_str else None

    rpms, pwrs, torqs = [], [], []
    for line in lines[data_start:]:
        parts = [p.strip() for p in line.split("\t")]
        try:
            r = float(parts[rpm_col])
            if not (RPM_MIN <= r <= RPM_MAX):
                continue
            rpms.append(r)
            pwrs.append(
                float(parts[pwr_col]) if pwr_col != -1 and pwr_col < len(parts) else 0.0
            )
            torqs.append(
                float(parts[tq_col]) if tq_col != -1 and tq_col < len(parts) else 0.0
            )
        except (ValueError, IndexError):
            continue

    if len(rpms) < 5:
        raise DynoParseError("MoTeC export: fewer than 5 valid rows.")

    rpm_arr = np.array(rpms)
    pwr_arr = _to_kw(np.array(pwrs), pwr_unit)
    tq_raw = np.array(torqs)
    metadata: dict = {}
    tq_unit = (
        _resolve_torque_unit(
            tq_label_unit, pwr_unit, pwr_col != -1, rpm_arr, pwr_arr, tq_raw, metadata
        )
        if tq_col != -1
        else "nm"
    )
    tq_arr = _to_nm(tq_raw, tq_unit)

    order = np.argsort(rpm_arr)
    return rpm_arr[order], pwr_arr[order], tq_arr[order], metadata, "motec_lite"


# ─── Post-processing ──────────────────────────────────────────────────────


def _smooth_and_fill(
    rpm: np.ndarray,
    power_kw: np.ndarray,
    torque_nm: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Given raw arrays (one of power/torque may be all-zero), derive the missing
    channel and apply light smoothing.
    """
    has_power = np.any(power_kw > 0)
    has_torque = np.any(torque_nm > 0)

    if has_power and not has_torque:
        torque_nm = _nm_from_kw_and_rpm(power_kw, rpm)
    elif has_torque and not has_power:
        safe_rpm = np.where(rpm > 50, rpm, 50)
        omega = safe_rpm * (2 * math.pi / 60)
        power_kw = torque_nm * omega / 1000.0
    # if both present: use as-is (sanity check below)

    # Sanity bounds
    power_kw = np.clip(power_kw, 0, PEAK_POWER_KW_MAX)
    torque_nm = np.clip(torque_nm, 0, PEAK_TORQUE_NM_MAX)

    # Light 3-point moving average to reduce noise
    if len(power_kw) >= 5:
        kernel = np.ones(3) / 3
        power_kw_s = np.convolve(power_kw, kernel, mode="same")
        torque_nm_s = np.convolve(torque_nm, kernel, mode="same")
        # Preserve edge values (convolution edge artefacts)
        power_kw_s[0] = power_kw[0]
        power_kw_s[-1] = power_kw[-1]
        torque_nm_s[0] = torque_nm[0]
        torque_nm_s[-1] = torque_nm[-1]
        power_kw, torque_nm = power_kw_s, torque_nm_s

    return rpm, power_kw, torque_nm


# ─── Public API ───────────────────────────────────────────────────────────


def parse_dyno_file(
    path: str | Path,
    temp_c: float | None = None,
    pressure_kpa: float | None = None,
    rh_pct: float = 0.0,
    is_at_wheel: bool = True,
) -> DynoResult:
    """
    Parse a dynamometer CSV export file and return an SAE J1349-corrected DynoCurve.

    Parameters
    ----------
    path         : Path to .csv or .txt dyno file
    temp_c       : Ambient temperature during dyno run [°C], −30…60. Pass with
                   pressure_kpa, or omit both for an uncorrected curve.
    pressure_kpa : Absolute barometric pressure during run [kPa], 60…110. A
                   value that is unambiguously hPa, bar, inHg (DynoJet sheets,
                   e.g. 29.92) or psi is converted, with a note in
                   ``raw_metadata['pressure_input_note']``.
    rh_pct       : Relative humidity [%] (0–100).
    is_at_wheel  : True = chassis (wheel) dyno; False = engine dyno.

    Returns
    -------
    DynoResult with .curve ready for injection into BikeConfig.engine.dyno_curve.

    Raises
    ------
    DynoParseError  : File format unrecognised or data invalid.
    DynoInputError  : Ambient inputs implausible, or only one of temp/pressure
                      given (subclass of DynoParseError and ValueError).
    FileNotFoundError
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dyno file not found: {path}")

    # Try parsers in order
    rpm, power_kw, torque_nm, metadata, fmt = None, None, None, {}, ""
    errors: list[str] = []

    for parser_fn in [_parse_csv, _parse_motec_lite]:
        try:
            rpm, power_kw, torque_nm, metadata, fmt = parser_fn(path)
            break
        except (DynoParseError, UnicodeDecodeError, ValueError) as exc:
            errors.append(f"{parser_fn.__name__}: {exc}")

    if rpm is None:
        raise DynoParseError(
            f"Could not parse {path.name} with any parser. Errors: {'; '.join(errors)}"
        )

    # Fill missing channel, smooth
    rpm, power_kw, torque_nm = _smooth_and_fill(rpm, power_kw, torque_nm)

    # SAE J1349 correction
    if temp_c is not None and pressure_kpa is not None:
        p_kpa, note = normalize_pressure_kpa(pressure_kpa)
        if note:
            log.warning("Dyno SAE correction: %s", note)
            metadata["pressure_input_note"] = note
        if rh_pct is None:
            rh_pct = 0.0
        cf = sae_j1349_correction_factor(temp_c, p_kpa, rh_pct)
        metadata["ambient"] = {
            "temp_c": float(temp_c),
            "pressure_kpa": round(p_kpa, 3),
            "rh_pct": float(rh_pct),
        }
        lo, hi = SAE_CF_ADVISORY_RANGE
        if not (lo <= cf <= hi):
            note = (
                f"SAE CF {cf:.3f} is outside J1349's recommended "
                f"{lo:g}-{hi:g} window — double-check the ambient inputs"
            )
            log.warning("Dyno SAE correction: %s", note)
            metadata["cf_advisory"] = note
    elif temp_c is not None or pressure_kpa is not None:
        missing = "pressure_kpa" if pressure_kpa is None else "temp_c"
        raise DynoInputError(
            f"SAE correction needs both temp_c and pressure_kpa; {missing} is "
            "missing (omit both for an uncorrected curve)"
        )
    else:
        cf = 1.0  # uncorrected

    power_kw_corr = power_kw * cf
    torque_nm_corr = torque_nm * cf

    # Peak values
    peak_pwr_idx = int(np.argmax(power_kw_corr))
    peak_tq_idx = int(np.argmax(torque_nm_corr))

    curve = DynoCurve(
        rpm=rpm,
        torque_nm=torque_nm_corr,
        is_at_wheel=is_at_wheel,
    )

    return DynoResult(
        curve=curve,
        rpm=rpm,
        power_kw=power_kw_corr,
        torque_nm=torque_nm_corr,
        correction_factor=cf,
        peak_power_kw=float(power_kw_corr[peak_pwr_idx]),
        peak_torque_nm=float(torque_nm_corr[peak_tq_idx]),
        rpm_at_peak_power=float(rpm[peak_pwr_idx]),
        rpm_at_peak_torque=float(rpm[peak_tq_idx]),
        is_at_wheel=is_at_wheel,
        source_file=str(path),
        raw_metadata=metadata,
    )
