"""
MotoQuant Pro — Dyno Curve Import
===================================
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
"standard" conditions: 25 °C, 98.9 kPa absolute (14.343 psia), 0% humidity.

    CF = (99.0 / Pd) × √(Tm / 298.15)

where:
    Pd = dry air pressure [kPa]  = total barometric pressure − saturated vapour pressure
    Tm = inlet air temperature [K]

Power_corrected = Power_measured × CF

If no ambient conditions are provided (temp, pressure, humidity), the measured
power is returned uncorrected and the caller is warned.

Public API
----------
    from motoquant.calibration.dyno import parse_dyno_file, DynoResult

    result = parse_dyno_file("dynorun.csv", temp_c=28, pressure_kpa=101.3, rh_pct=60)
    curve   = result.curve           # DynoCurve — inject into BikeConfig
    print(result.correction_factor)  # SAE J1349 CF applied
"""

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..models import DynoCurve

# ─── Constants ────────────────────────────────────────────────────────────

HP_TO_KW: float = 0.745699872
KW_TO_HP: float = 1.0 / HP_TO_KW
PS_TO_KW: float = 0.735499
LBFT_TO_NM: float = 1.35582

# SAE J1349 standard reference conditions
SAE_REF_TEMP_K: float = 298.15  # 25 °C
SAE_REF_PRESSURE_KPA: float = 99.0  # kPa dry air

RPM_MIN: float = 500.0
RPM_MAX: float = 22000.0
PEAK_POWER_KW_MAX: float = 1000.0  # sanity upper bound
PEAK_TORQUE_NM_MAX: float = 5000.0


class DynoParseError(Exception):
    """Raised when a dyno file cannot be parsed or contains invalid data."""


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


def sae_j1349_correction_factor(
    temp_c: float,
    pressure_kpa: float,
    rh_pct: float = 0.0,
) -> float:
    """
    Compute SAE J1349 atmospheric correction factor.

    Parameters
    ----------
    temp_c       : Inlet air temperature [°C]
    pressure_kpa : Absolute barometric pressure [kPa]
    rh_pct       : Relative humidity [%] (0–100)

    Returns
    -------
    float : Correction factor — multiply measured power by this.
    """
    temp_k = temp_c + 273.15
    p_sat = _saturated_vapour_pressure_kpa(temp_c)
    p_vapour = (rh_pct / 100.0) * p_sat
    p_dry = max(pressure_kpa - p_vapour, 0.1)

    cf = (SAE_REF_PRESSURE_KPA / p_dry) * math.sqrt(SAE_REF_TEMP_K / temp_k)
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


def _detect_torque_unit(header: list[str], col_idx: int) -> str:
    """Infer torque unit from column header text."""
    if col_idx < 0:
        return "nm"
    label = header[col_idx].lower()
    if "lb" in label or "ft" in label or "lbft" in label or "ftlb" in label:
        return "lbft"
    return "nm"


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
    tq_unit = _detect_torque_unit(header, tq_col)

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
    tq_arr = _to_nm(np.array(torqs), tq_unit)

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

    tq_unit_str = (
        units[tq_col].lower() if tq_col != -1 and tq_col < len(units) else "nm"
    )
    tq_unit = "lbft" if ("lb" in tq_unit_str or "ft" in tq_unit_str) else "nm"

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
    tq_arr = _to_nm(np.array(torqs), tq_unit)

    order = np.argsort(rpm_arr)
    return rpm_arr[order], pwr_arr[order], tq_arr[order], {}, "motec_lite"


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
    temp_c       : Ambient temperature during dyno run [°C]. If None, no correction applied.
    pressure_kpa : Absolute barometric pressure during run [kPa]. If None, no correction.
    rh_pct       : Relative humidity [%] (0–100).
    is_at_wheel  : True = chassis (wheel) dyno; False = engine dyno.

    Returns
    -------
    DynoResult with .curve ready for injection into BikeConfig.engine.dyno_curve.

    Raises
    ------
    DynoParseError  : File format unrecognised or data invalid.
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
        cf = sae_j1349_correction_factor(temp_c, pressure_kpa, rh_pct)
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
