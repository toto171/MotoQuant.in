"""ECU speed-column units (November 2026 port).

The header-unit handling itself came with the Rust-core branch
(``_unit_conversion`` / ``_header_unit``). This file pins what the redesign
branch's audit added on top of it:

* spellings the alias table missed ('GPS Speed', 'Veh Spd', 'SpeedKPH',
  'Speed kph'), so those logs no longer lose their speed channel;
* a speed column whose unit this importer does not convert (knots, ft/s, an
  acceleration unit ...) is REFUSED with a warning instead of being read with
  the km/h default — in the header and in a MoTeC units row alike;
* a name qualifier ('Wheel Speed Rear') is not mistaken for a unit.
"""

import warnings
from pathlib import Path

import numpy as np
import pytest

from motoquant.calibration.ecu import (
    _apply_unit_overrides,
    _map_column,
    parse_ecu_file,
)

_FACTOR = {"kmh": 1 / 3.6, "mph": 0.44704, "ms": 1.0}


@pytest.mark.parametrize(
    "header,unit",
    [
        ("GPS Speed", "kmh"),
        ("GPS Speed (mph)", "mph"),
        ("GPS Speed (km/h)", "kmh"),
        ("SPEED KPH", "kmh"),
        ("SpeedKPH", "kmh"),
        ("SpeedMPH", "mph"),
        ("Speed kph", "kmh"),
        ("Veh Spd", "kmh"),
        ("Veh Spd (mph)", "mph"),
        ("Veh Speed (km/h)", "kmh"),
        ("Speed (kph)", "kmh"),
        ("Speed [mph]", "mph"),
        ("Vehicle Speed [mi/h]", "mph"),
        ("speed_kmh", "kmh"),
        ("Speed [m/s]", "ms"),
        ("VSS (mph)", "mph"),
        # a qualifier after the name is not a unit: alias-table default / its
        # own bracketed unit still apply
        ("Wheel Speed Rear", "kmh"),
        ("Wheel Speed Rear (mph)", "mph"),
    ],
)
def test_speed_header_spellings(header, unit):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a recognised header never warns
        std, conv = _map_column(header)
    assert std == "vehicle_speed_ms", header
    got = 1.0 if conv is None else float(conv)
    assert got == pytest.approx(_FACTOR[unit])


@pytest.mark.parametrize(
    "header",
    [
        "Speed (knots)",
        "Speed (m/s2)",
        "Speed (kt)",
        "Speed knots",
        "Vehicle Speed [ft/s]",
        "Wheel Speed Rear (knots)",
    ],
)
def test_unknown_speed_unit_is_refused_with_a_warning(header):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert _map_column(header) == (None, None)
    assert any("unrecognised speed unit" in str(x.message) for x in w)


@pytest.mark.parametrize(
    "header,std",
    [
        ("Engine Speed", "rpm"),
        ("Speed Limiter", None),
        ("Speedo Error", None),
        ("Front Wheel Speed", None),
    ],
)
def test_non_vehicle_speed_headers_are_not_speed(header, std):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _map_column(header)[0] == std


def test_units_row_with_unknown_speed_unit_drops_the_column():
    col_map = {0: ("time_s", None), 1: ("vehicle_speed_ms", 1 / 3.6)}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        out = _apply_unit_overrides(col_map, ["s", "knots"])
    assert out == {0: ("time_s", None)}
    assert any("unrecognised speed unit" in str(x.message) for x in w)
    # known units and an empty units cell are untouched
    assert _apply_unit_overrides(col_map, ["s", "mph"])[1] == (
        "vehicle_speed_ms",
        0.44704,
    )
    assert _apply_unit_overrides(col_map, ["s", ""]) == col_map


def _write_log(path: Path, speed_header: str, scale: float) -> Path:
    rate = 50.0
    n_idle, n_run = int(3 * rate), int(16 * rate)
    t = np.arange(n_idle + n_run) / rate
    v = np.zeros_like(t)
    v[n_idle:] = np.minimum(58.0, 9.0 * np.arange(n_run) / rate)
    rpm = np.where(v > 0, 6000 + v * 100, 1500.0)
    rows = [f"{a:.2f},{b:.0f},100,{c * scale:.4f}" for a, b, c in zip(t, rpm, v)]
    path.write_text(f"Time,RPM,TPS%,{speed_header}\n" + "\n".join(rows) + "\n")
    return path


def test_knots_log_is_not_timed_as_kmh(tmp_path):
    """End to end: the same run logged in knots must not come back with an ET
    computed as if the numbers were km/h (it used to: 1 kn = 1.852 km/h, so
    the bike 'covered' 402 m far too slowly and the ET read ~1.6x long)."""
    kmh = parse_ecu_file(_write_log(tmp_path / "kmh.csv", "Speed (km/h)", 3.6))
    ref = kmh.best_run()
    assert ref is not None and np.isfinite(ref.et_quarter)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        knots = parse_ecu_file(
            _write_log(tmp_path / "kn.csv", "Speed (knots)", 3.6 / 1.852)
        )
    assert any("unrecognised speed unit" in str(x.message) for x in w)
    assert knots.vehicle_speed_ms is None
    for run in knots.runs:  # RPM-detected windows carry no speed-derived ET
        assert not np.isfinite(run.et_quarter)
