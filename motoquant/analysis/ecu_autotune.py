"""
MotoQuant Pro — ECU / Setup Autotune
====================================
Conditions-aware drag setup advisor (Track B).

Given a bike + a *resolved race environment* (temperature, humidity, density
altitude — produced by ``/api/venues/resolve`` and applied onto
``config.environment``), recommend the optimal launch setup:

  • final drive / gearing   — swept and scored on the full physics sim
  • launch RPM              — swept and scored on the full physics sim
  • tyre pressure           — conditions-aware guideline (heuristic, bounded)
  • fuel / timing trim      — air-density-derived guideline (advisory)

…with the atmospheric rationale (density altitude, air density, power
correction) shown alongside.

Why full sim, not the surrogate
-------------------------------
The surrogate's feature vector exposes only ``altitude_m`` from the
environment and has **no** ``launch_rpm`` feature, so it is blind to launch
tuning and to temperature / humidity / pressure effects.  Recommending a
conditions-specific setup through it would be silently wrong, so the gearing
and launch sweeps use the full physics engine (``roi._run_et``), which reads
``config.environment.air_density()`` directly.  Atmospherics are *consumed*
from the environment model here, never re-derived.

Public API
----------
    result = autotune(config_with_environment)
    result.to_dict()        # JSON-ready for the API
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass

from ..models import BikeConfig
from ..submodels.environmental import EnvironmentalModel
from .roi import _run_et

__all__ = ["EcuAutotune", "autotune"]

_RHO_SL_STD = 1.2250  # kg/m³ (matches submodels/environmental)


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


# ─────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class EcuAutotune:
    bike_name: str
    environment: dict
    stock: dict
    gearing: dict
    launch_rpm: dict
    tyre_pressure: dict
    fuel_timing: dict
    combined: dict
    rationale: str
    scoring_method: str = "full_sim"

    def summary(self) -> str:
        e = self.environment
        lines = [
            f"{self.bike_name} — setup for {e.get('location') or 'these conditions'}",
            f"  air: {e['temperature_c']:.0f}°C / {e['humidity_pct']:.0f}% RH / "
            f"{e['altitude_m']:.0f} m  →  DA {e['density_altitude_ft']:.0f} ft "
            f"(ρ {e['air_density_kgm3']:.3f}, power {e['power_correction_pct']:.0f}%)",
            f"  gearing : {self.gearing['recommendation']}  ({self.gearing['delta_et_s']:+.3f}s)",
            f"  launch  : {self.launch_rpm['recommended_rpm']:.0f} rpm  ({self.launch_rpm['delta_et_s']:+.3f}s)",
            f"  tyres   : rear {self.tyre_pressure['rear_psi']:.0f} psi / front {self.tyre_pressure['front_psi']:.0f} psi",
            f"  fuel    : {self.fuel_timing['fuel_trim_pct']:+.1f}% trim, "
            f"{self.fuel_timing['timing_advance_deg']:+.1f}° timing",
            f"  net     : {self.stock['et_s']:.3f}s → {self.combined['et_s']:.3f}s "
            f"({self.combined['delta_et_s']:+.3f}s) with recommended gearing + launch",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────────────────
def _environment_block(config: BikeConfig) -> tuple[dict, float]:
    """Read the resolved atmospherics off config.environment (no re-derivation)."""
    env = config.environment
    model = EnvironmentalModel(config)
    rho = float(model.rho)
    sigma = rho / _RHO_SL_STD  # density ratio ≈ NA power-correction factor
    da_ft = float(model.density_alt_ft)
    block = {
        "location": getattr(env, "venue_name", None),
        "temperature_c": float(getattr(env, "ambient_temp_c", 25.0)),
        "track_temp_c": float(getattr(env, "track_temp_c", 30.0)),
        "humidity_pct": float(getattr(env, "relative_humidity_pct", 50.0)),
        "pressure_hpa": float(getattr(env, "barometric_pressure_hpa", 1013.25)),
        "altitude_m": float(getattr(env, "altitude_m", 0.0)),
        "air_density_kgm3": round(rho, 4),
        "density_altitude_ft": round(da_ft, 0),
        "density_altitude_m": round(da_ft * 0.3048, 0),
        "power_correction_pct": round(float(model.power_correction) * 100.0, 1),
        "power_loss_pct": round(
            float(getattr(model, "da_power_loss_pct", (1.0 - sigma) * 100.0)), 1
        ),
    }
    return block, sigma


# ─────────────────────────────────────────────────────────────────────────
# Sweeps (full physics sim — atmospherics matter)
# ─────────────────────────────────────────────────────────────────────────
def _gearing_recommendation(
    config: BikeConfig, stock_et: float, *, span: int = 3, on_sim=None
) -> dict:
    dt = config.drivetrain
    front = int(getattr(dt, "front_sprocket", 0) or 0)
    rear = int(getattr(dt, "rear_sprocket", 0) or 0)
    chain_adjustable = front > 0 and rear > 0

    candidates: list[dict] = []

    if chain_adjustable:
        lo = max(28, int(round(rear * 0.85)))
        hi = min(56, int(round(rear * 1.20)))
        teeth = sorted({_clamp(rear + d, lo, hi) for d in range(-span, span + 3)})
        for t in teeth:
            cfg = copy.deepcopy(config)
            cfg.drivetrain.rear_sprocket = t
            et, trap = _run_et(cfg)
            if on_sim is not None:
                on_sim()
            candidates.append(
                {
                    "front_sprocket": front,
                    "rear_sprocket": t,
                    "final_drive": round(t / front, 3),
                    "et_s": round(et, 4),
                    "trap_kmh": round(trap * 3.6, 1),
                    "is_stock": t == rear,
                }
            )
        best = min(candidates, key=lambda c: c["et_s"])
        # Public convention (July 6, 2026): delta_et_s = recommended - stock,
        # NEGATIVE = faster — matches /api/simulate/quick's et_delta_s.
        delta = best["et_s"] - stock_et
        if best["rear_sprocket"] == rear:
            rec = f"keep stock {front}/{rear} gearing"
        else:
            direction = (
                "shorter (more acceleration)"
                if best["rear_sprocket"] > rear
                else "taller (more top-end)"
            )
            rec = f"{front}/{best['rear_sprocket']} — {direction}"
        return {
            "adjustable": True,
            "drive": "chain",
            "stock_front": front,
            "stock_rear": rear,
            "recommended_front": best["front_sprocket"],
            "recommended_rear": best["rear_sprocket"],
            "recommended_final_drive": best["final_drive"],
            "et_s": best["et_s"],
            "trap_kmh": best["trap_kmh"],
            "delta_et_s": round(delta, 4) + 0.0,  # +0.0 normalizes -0.0
            "recommendation": rec,
            "candidates": candidates,
        }

    # Shaft / belt drive — final drive is fixed by the OEM.
    fd = float(getattr(dt, "final_drive_ratio", 0.0) or 0.0)
    return {
        "adjustable": False,
        "drive": getattr(dt, "drive_type", "shaft"),
        "recommended_final_drive": round(fd, 3),
        "et_s": round(stock_et, 4),
        "delta_et_s": 0.0,
        "recommendation": "fixed final drive (shaft/belt) — gearing not user-adjustable",
        "candidates": [],
    }


def _launch_recommendation(
    config: BikeConfig, stock_et: float, *, steps: int = 6, on_sim=None
) -> dict:
    eng = config.engine
    redline = float(getattr(eng, "redline_rpm", 12000.0))
    pt = float(getattr(eng, "peak_torque_rpm", redline * 0.7))
    pp = float(getattr(eng, "peak_power_rpm", redline * 0.85))
    idle = float(getattr(eng, "idle_rpm", 1200.0))
    stock_launch = float(
        getattr(config.staging, "launch_rpm", 0.0) or getattr(eng, "launch_rpm", pt)
    )

    lo = _clamp(min(pt, pp) * 0.80, idle * 2.0, redline)
    hi = _clamp(redline * 0.97, lo + 500.0, redline)
    if hi <= lo:
        hi = lo + 500.0

    grid = [round(lo + (hi - lo) * i / (steps - 1), -1) for i in range(steps)]
    grid = sorted(set(grid + [round(stock_launch, -1)]))

    candidates: list[dict] = []
    for rpm in grid:
        cfg = copy.deepcopy(config)
        cfg.staging.launch_rpm = float(rpm)
        et, trap = _run_et(cfg)
        if on_sim is not None:
            on_sim()
        candidates.append(
            {
                "launch_rpm": float(rpm),
                "et_s": round(et, 4),
                "trap_kmh": round(trap * 3.6, 1),
                "is_stock": abs(rpm - stock_launch) < 1.0,
            }
        )
    best = min(candidates, key=lambda c: c["et_s"])
    return {
        "stock_rpm": round(stock_launch, 0),
        "recommended_rpm": best["launch_rpm"],
        "et_s": best["et_s"],
        "trap_kmh": best["trap_kmh"],
        "delta_et_s": round(best["et_s"] - stock_et, 4) + 0.0,  # negative = faster
        "rationale": (
            "higher launch RPM keeps the engine in its powerband off the line"
            if best["launch_rpm"] >= stock_launch
            else "lower launch RPM reduces wheelspin / bog for this traction level"
        ),
        "candidates": candidates,
    }


def _tyre_pressure_recommendation(config: BikeConfig, env: dict) -> dict:
    tires = config.tires
    stock_rear = float(getattr(tires, "rear_pressure_psi", 30.0))
    stock_front = float(getattr(tires, "front_pressure_psi", 33.0))
    track_temp = env.get("track_temp_c", 30.0)

    # Drag launch wants a bigger rear contact patch → drop a few psi; a hotter
    # track builds pressure during the burnout/stage, so start marginally lower
    # when cold and not as low when hot.
    temp_adj = (track_temp - 30.0) * 0.10  # +1 psi per 10°C above 30
    rec_rear = _clamp(round(stock_rear - 4.0 + temp_adj), 18, int(stock_rear))
    rec_front = _clamp(round(stock_front - 1.0), 28, int(stock_front))
    return {
        "stock_rear_psi": round(stock_rear, 0),
        "stock_front_psi": round(stock_front, 0),
        "rear_psi": float(rec_rear),
        "front_psi": float(rec_front),
        "rationale": (
            f"Drop the rear to ~{rec_rear:.0f} psi (from {stock_rear:.0f}) to enlarge the launch "
            f"contact patch; front ~{rec_front:.0f} psi for stability. Track at {track_temp:.0f}°C "
            f"{'builds pressure quickly — start near the upper bound' if track_temp >= 35 else 'is cool — a lower start helps grip'}. "
            "Guideline; verify with a 60-ft pass."
        ),
        "is_guideline": True,
    }


def _fuel_timing_recommendation(config: BikeConfig, env: dict, sigma: float) -> dict:
    induction = (getattr(config.engine, "induction_type", None) or "").lower()
    stroke = int(getattr(config.engine, "stroke_type", 4))

    # Fuel scales ~ with air density: lean out at altitude / heat, richen in
    # dense air.  Timing tolerates a little advance in thinner / more humid air.
    fuel_trim = _clamp(round((sigma - 1.0) * 100.0, 1), -15.0, 15.0)
    timing_adv = _clamp(round(max(0.0, 1.0 - sigma) * 12.0, 1), 0.0, 3.0)

    if induction in ("efi", "tbi", "pgm-fi", "fi"):
        applic = "EFI closed-loop self-corrects partially; apply as a fuel-map trim for wide-open throttle."
    elif induction in ("carb", "carburettor", "carburetor"):
        applic = "Carburettor: rejet to match — leaner main jet at altitude, richer at sea level."
    else:
        applic = "Apply via your fuel controller / ECU map; magnitude scales with air density."
    if stroke == 2:
        applic += " 2-stroke: also re-check premix/oil and main jet conservatively."

    da = env.get("density_altitude_ft", 0.0)
    return {
        "fuel_trim_pct": fuel_trim,
        "timing_advance_deg": timing_adv,
        "density_ratio": round(sigma, 4),
        "applicable": True,
        "rationale": (
            f"Air is {abs(1.0 - sigma) * 100:.0f}% {'thinner' if sigma < 1 else 'denser'} than sea-level "
            f"std (DA {da:.0f} ft). {applic}"
        ),
        "is_guideline": True,
    }


# ─────────────────────────────────────────────────────────────────────────
# Top-level
# ─────────────────────────────────────────────────────────────────────────
def autotune(
    config: BikeConfig,
    *,
    gear_span: int = 3,
    launch_steps: int = 6,
    include_combined: bool = True,
    progress_cb=None,
) -> EcuAutotune:
    """
    Produce a conditions-aware drag setup for ``config``.

    ``config.environment`` is expected to already carry the resolved
    conditions (the API route applies ``/api/venues/resolve`` output onto it).
    """
    env_block, sigma = _environment_block(config)

    # Progress ticker for the website's real progress bar (jobs API).
    # Total full-sim count: stock + gearing sweep + launch sweep (grid can
    # gain the stock-launch slot) + combined verification. Tooth-dedup can
    # only shrink the gearing count, so the bar may finish slightly early —
    # it can never stall short of done.
    _tick = None
    if progress_cb is not None:
        _total = (
            1
            + (2 * gear_span + 3)
            + (launch_steps + 1)
            + (1 if include_combined else 0)
        )
        _done = [0]

        def _tick(stage):
            _done[0] += 1
            progress_cb(min(0.98, _done[0] / _total), stage)

    stock_et, stock_trap = _run_et(config)
    if _tick is not None:
        _tick("Baseline run")
    stock = {
        "et_s": round(stock_et, 4),
        "trap_kmh": round(stock_trap * 3.6, 1),
        "launch_rpm": round(float(getattr(config.staging, "launch_rpm", 0.0)), 0),
        "front_sprocket": int(getattr(config.drivetrain, "front_sprocket", 0) or 0),
        "rear_sprocket": int(getattr(config.drivetrain, "rear_sprocket", 0) or 0),
        "rear_pressure_psi": round(
            float(getattr(config.tires, "rear_pressure_psi", 30.0)), 0
        ),
        "front_pressure_psi": round(
            float(getattr(config.tires, "front_pressure_psi", 33.0)), 0
        ),
    }

    gearing = _gearing_recommendation(
        config,
        stock_et,
        span=gear_span,
        on_sim=(lambda: _tick("Sweeping gearing")) if _tick is not None else None,
    )
    launch = _launch_recommendation(
        config,
        stock_et,
        steps=launch_steps,
        on_sim=(lambda: _tick("Sweeping launch RPM")) if _tick is not None else None,
    )
    tyres = _tyre_pressure_recommendation(config, env_block)
    fuel = _fuel_timing_recommendation(config, env_block, sigma)

    # Net effect of the two simulated knobs applied together.
    combined = {"et_s": stock["et_s"], "trap_kmh": stock["trap_kmh"], "delta_et_s": 0.0}
    if include_combined:
        cfg = copy.deepcopy(config)
        if gearing.get("adjustable") and gearing.get("recommended_rear"):
            cfg.drivetrain.rear_sprocket = int(gearing["recommended_rear"])
        cfg.staging.launch_rpm = float(launch["recommended_rpm"])
        c_et, c_trap = _run_et(cfg)
        if _tick is not None:
            _tick("Verifying combined setup")
        combined = {
            "et_s": round(c_et, 4),
            "trap_kmh": round(c_trap * 3.6, 1),
            "delta_et_s": round(c_et - stock_et, 4) + 0.0,  # negative = faster
        }

    # Overall plain-language rationale tying it to the atmospherics.
    da = env_block["density_altitude_ft"]
    if da >= 3000:
        air_note = (
            f"High density altitude ({da:.0f} ft) — the engine makes "
            f"~{env_block['power_loss_pct']:.0f}% less power, so gear for revs and lean the fuel."
        )
    elif da <= 500:
        air_note = (
            f"Dense, sea-level-like air (DA {da:.0f} ft) — near-peak power; "
            "gear for the extra top-end and richen slightly."
        )
    else:
        air_note = f"Moderate density altitude ({da:.0f} ft) — modest corrections."
    rationale = (
        f"{air_note} Recommended gearing + launch lower the quarter from "
        f"{stock['et_s']:.3f}s to {combined['et_s']:.3f}s ({combined['delta_et_s']:+.3f}s) "
        f"in these conditions."
    )

    return EcuAutotune(
        bike_name=config.name,
        environment=env_block,
        stock=stock,
        gearing=gearing,
        launch_rpm=launch,
        tyre_pressure=tyres,
        fuel_timing=fuel,
        combined=combined,
        rationale=rationale,
        scoring_method="full_sim",
    )
