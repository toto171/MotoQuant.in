"""
MotoQuant — ECU / Setup Autotune
================================
Conditions-aware drag setup advisor (Track B).

Given a bike + a *resolved race environment* (temperature, humidity, density
altitude — produced by ``/api/venues/resolve`` and applied onto
``config.environment``), recommend the optimal launch setup:

  • final drive / gearing   — swept and scored on the full physics sim
  • launch RPM              — swept and scored on the full physics sim (with a
                              two-step holding each candidate RPM), only where
                              the sim responds to it; where it does not, the
                              result says so (``adjustable: False``, no RPM)
  • tyre pressure           — general guidance, not simulated
  • fuel / timing trim      — air-density guidance, not simulated

…with the atmospheric rationale (density altitude, air density, power
correction) shown alongside.

Why full sim, not the surrogate
-------------------------------
The surrogate's feature vector exposes only ``altitude_m`` from the
environment and has **no** ``launch_rpm`` feature, so it is blind to launch
tuning and to temperature / humidity / pressure effects.  Recommending a
conditions-specific setup through it would be silently wrong, so the gearing
and launch sweeps use the full physics engine (``roi._run_et`` through one
``roi.SimMemo`` per call, so no config is simulated twice), which reads
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

from .. import engine_select
from ..constants import RPM_TO_RADS
from ..models import DRIVE_BELT, DRIVE_SHAFT, BikeConfig
from ..submodels.environmental import EnvironmentalModel
from .roi import SimMemo

__all__ = ["EcuAutotune", "autotune"]

_RHO_SL_STD = 1.2250  # kg/m³ (matches submodels/environmental)

# Launch-RPM probe runs whose ETs all agree within this many seconds mean the
# sim is not responding to the knob at all (e.g. the bike's category profile
# fixes the launch RPM).
_LAUNCH_LIVENESS_TOL_S = 1e-3

_LAUNCH_NOT_MODELLED = (
    "Launch RPM is not modelled for this bike, so no recommendation is made."
)


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
    engine: str = "python"  # which physics engine ran the sweeps (python | native)

    def summary(self) -> str:
        e = self.environment
        lines = [
            f"{self.bike_name} — setup for {e.get('location') or 'these conditions'}",
            f"  air: {e['temperature_c']:.0f}°C / {e['humidity_pct']:.0f}% RH / "
            f"{e['altitude_m']:.0f} m  →  DA {e['density_altitude_ft']:.0f} ft "
            f"(ρ {e['air_density_kgm3']:.3f}, power {e['power_correction_pct']:.0f}%)",
            f"  gearing : {self.gearing['recommendation']}  ({self.gearing['delta_et_s']:+.3f}s)",
            f"  launch  : {self._launch_line()}",
            f"  tyres   : rear {self.tyre_pressure['rear_psi']:.0f} psi / front {self.tyre_pressure['front_psi']:.0f} psi",
            f"  fuel    : {self.fuel_timing['fuel_trim_pct']:+.1f}% trim, "
            f"{self.fuel_timing['timing_advance_deg']:+.1f}° timing",
            f"  net     : {self.stock['et_s']:.3f}s → {self.combined['et_s']:.3f}s "
            f"({self.combined['delta_et_s']:+.3f}s) with the simulated setup",
        ]
        return "\n".join(lines)

    def _launch_line(self) -> str:
        lr = self.launch_rpm
        if lr.get("adjustable") and lr.get("recommended_rpm") is not None:
            return f"{lr['recommended_rpm']:.0f} rpm  ({lr['delta_et_s']:+.3f}s)"
        if lr.get("reason") and lr.get("reason") != _LAUNCH_NOT_MODELLED:
            return f"no change — {lr['reason']}"
        return "not modelled for this bike — no recommendation"

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
    sigma = rho / _RHO_SL_STD  # air-density ratio (fuel/timing guidance only)
    power_corr = float(model.power_correction)  # exactly what the sim applies
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
        "power_correction_pct": round(power_corr * 100.0, 1),
        "power_loss_pct": round(max(0.0, 1.0 - power_corr) * 100.0, 1),
    }
    return block, sigma


# ─────────────────────────────────────────────────────────────────────────
# Sweeps (full physics sim — atmospherics matter)
# ─────────────────────────────────────────────────────────────────────────
def _gearing_adjustable(config: BikeConfig) -> tuple[bool, str]:
    """(user-adjustable chain gearing?, drive label)."""
    dt = config.drivetrain
    front = int(getattr(dt, "front_sprocket", 0) or 0)
    rear = int(getattr(dt, "rear_sprocket", 0) or 0)
    drive = str(getattr(dt, "drive_type", "chain") or "chain").lower()
    if drive in (DRIVE_BELT, DRIVE_SHAFT):
        return False, drive
    if front <= 0 or rear <= 0:
        return False, "shaft/belt"
    if getattr(dt, "chain_pitch", None) is None:
        # The catalog stamps a chain pitch on every chain-drive bike; None is
        # how belt and shaft bikes are recorded (their stored "sprockets" are
        # belt pulleys or a synthetic ratio — e.g. a Street Bob's 32/66
        # pulleys, which the old 28-56T clamp collapsed to a single
        # never-stock 56T candidate and recommended as a 10-tooth change).
        return False, "belt/shaft (no chain pitch on record)"
    return True, "chain"


def _gearing_recommendation(
    config: BikeConfig,
    stock_et: float,
    *,
    span: int = 3,
    on_sim=None,
    stock_trap: float | None = None,
    sim=None,
) -> dict:
    sim = sim if sim is not None else SimMemo()
    dt = config.drivetrain
    front = int(getattr(dt, "front_sprocket", 0) or 0)
    rear = int(getattr(dt, "rear_sprocket", 0) or 0)
    adjustable, drive = _gearing_adjustable(config)

    candidates: list[dict] = []

    if adjustable:
        # Sweep window derived from the STOCK sprocket (no absolute tooth
        # cap), and the stock count is always a candidate.
        lo = max(1, int(round(rear * 0.85)))
        hi = max(lo, int(round(rear * 1.20)))
        teeth = sorted(
            {_clamp(rear + d, lo, hi) for d in range(-span, span + 3)} | {rear}
        )
        for t in teeth:
            if t == rear and stock_trap is not None:
                et, trap = stock_et, stock_trap
            else:
                cfg = copy.deepcopy(config)
                cfg.drivetrain.rear_sprocket = t
                et, trap = sim(cfg)
                if on_sim is not None:
                    on_sim()
            candidates.append(
                {
                    "front_sprocket": front,
                    "rear_sprocket": t,
                    "final_drive": round(t / front, 3),
                    "et_s": round(float(et), 4),
                    "trap_kmh": round(float(trap) * 3.6, 1),
                    "is_stock": t == rear,
                }
            )
        # Stock wins ties: only recommend a change that measurably helps.
        best = min(candidates, key=lambda c: (c["et_s"], 0 if c["is_stock"] else 1))
        # Public convention (July 6, 2026): delta_et_s = recommended - stock,
        # NEGATIVE = faster — matches /api/simulate/quick's et_delta_s.
        delta = best["et_s"] - round(float(stock_et), 4)
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
            "drive": drive,
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
    fd = float(getattr(dt, "final_ratio", 0.0) or 0.0)
    return {
        "adjustable": False,
        "drive": drive,
        "recommended_final_drive": round(fd, 3),
        "et_s": round(float(stock_et), 4),
        "delta_et_s": 0.0,
        "recommendation": "fixed final drive (shaft/belt) — gearing not user-adjustable",
        "candidates": [],
    }


def _actual_launch_rpm(config: BikeConfig) -> float:
    """The RPM the engine REALLY launches at in the sim.

    Without a two-step the staging model holds peak-torque RPM (the stored
    staging.launch_rpm is then an unused dataclass default — 8000 rpm, above
    a Street Bob's redline); a category profile's launch_rpm_factor
    overrides both.
    """
    eng = engine_select.make_engine(config)
    rpm = float(eng.staging_initial_omega_e()) / RPM_TO_RADS
    factor = getattr(getattr(eng, "_profile", None), "launch_rpm_factor", None)
    if factor is not None:
        e = config.engine
        rpm = max(e.idle_rpm, min(e.redline_rpm * factor, e.redline_rpm))
    return rpm


def _launch_recommendation(
    config: BikeConfig,
    stock_et: float,
    *,
    steps: int = 6,
    on_sim=None,
    stock_trap: float | None = None,
    sim=None,
) -> dict:
    """Sweep the launch RPM with a two-step holding it — where the sim responds.

    staging.launch_rpm is only honoured when a two-step is active (otherwise
    the engine launches at peak-torque RPM), so the old sweep — which never
    set two_step — simulated 7 identical runs on 520 of 541 bikes and then
    recommended the lowest grid point (min() tie-break) with a made-up
    "reduces wheelspin" rationale. Every candidate now runs with
    ``staging.two_step = True`` at that RPM; the stock candidate is the bike
    exactly as configured.

    Liveness probe: the two most separated candidates are simulated first. If
    neither moves the ET off stock, the sim is not responding to the knob (a
    category profile that fixes the launch RPM overrides staging entirely) and
    the answer is ``adjustable: False`` with ``recommended_rpm: None`` and a
    ``reason`` — no further launch sims are run and no RPM is invented.
    """
    sim = sim if sim is not None else SimMemo()
    eng = config.engine
    redline = float(getattr(eng, "redline_rpm", 12000.0))
    pt = float(getattr(eng, "peak_torque_rpm", redline * 0.7))
    pp = float(getattr(eng, "peak_power_rpm", redline * 0.85))
    idle = float(getattr(eng, "idle_rpm", 1200.0))
    two_step_fitted = bool(getattr(config.staging, "two_step", False))
    stock_launch = _actual_launch_rpm(config)

    lo = _clamp(min(pt, pp) * 0.80, idle * 2.0, redline)
    hi = _clamp(redline * 0.97, lo + 500.0, redline)
    if hi <= lo:
        hi = lo + 500.0

    grid = sorted({round(lo + (hi - lo) * i / (steps - 1), -1) for i in range(steps)})

    if stock_trap is None:
        stock_et, stock_trap = sim(config)
    stock_et_r = round(float(stock_et), 4)
    stock_cand = {
        "launch_rpm": round(stock_launch, 0),
        "et_s": stock_et_r,
        "trap_kmh": round(float(stock_trap) * 3.6, 1),
        "is_stock": True,
    }

    def _is_stock_point(rpm: float) -> bool:
        return abs(rpm - stock_launch) < 1.0 and two_step_fitted

    def _candidate(rpm: float) -> dict:
        cfg = copy.deepcopy(config)
        cfg.staging.two_step = True
        cfg.staging.launch_rpm = float(rpm)
        et, trap = sim(cfg)
        if on_sim is not None:
            on_sim()
        return {
            "launch_rpm": float(rpm),
            "et_s": round(float(et), 4),
            "trap_kmh": round(float(trap) * 3.6, 1),
            "is_stock": False,
        }

    swept: dict[float, dict] = {}
    for rpm in (grid[0], grid[-1]):
        if rpm not in swept and not _is_stock_point(rpm):
            swept[rpm] = _candidate(rpm)
    if swept and all(
        abs(c["et_s"] - stock_et_r) < _LAUNCH_LIVENESS_TOL_S for c in swept.values()
    ):
        return {
            "adjustable": False,
            "stock_rpm": round(stock_launch, 0),
            "recommended_rpm": None,
            "changed": False,
            "two_step_fitted": two_step_fitted,
            "requires_two_step": False,
            "et_s": stock_et_r,
            "trap_kmh": stock_cand["trap_kmh"],
            "delta_et_s": 0.0,
            "reason": _LAUNCH_NOT_MODELLED,
            "rationale": _LAUNCH_NOT_MODELLED,
            "candidates": [stock_cand] + [swept[r] for r in sorted(swept)],
        }
    for rpm in grid:
        if rpm not in swept and not _is_stock_point(rpm):
            swept[rpm] = _candidate(rpm)
    candidates = [stock_cand] + [swept[r] for r in grid if r in swept]

    # Stock wins ties: a sweep where every RPM gives the same ET recommends
    # "no change", never an arbitrary grid point.
    best = min(candidates, key=lambda c: (c["et_s"], 0 if c["is_stock"] else 1))
    changed = not best["is_stock"]
    if not changed:
        rationale = (
            "no change — no launch RPM beat the stock launch in these conditions"
        )
    elif best["launch_rpm"] >= stock_launch:
        rationale = "higher launch RPM keeps the engine in its powerband off the line"
    else:
        rationale = (
            "a lower launch RPM gives the quickest simulated quarter for this "
            "traction level"
        )
    if changed and not two_step_fitted:
        rationale += " (needs a two-step / launch control to hold this RPM)"
    return {
        "adjustable": True,
        "stock_rpm": round(stock_launch, 0),
        "recommended_rpm": best["launch_rpm"],
        "changed": changed,
        "two_step_fitted": two_step_fitted,
        "requires_two_step": changed and not two_step_fitted,
        "et_s": best["et_s"],
        "trap_kmh": best["trap_kmh"],
        "delta_et_s": round(best["et_s"] - stock_et_r, 4) + 0.0,  # negative = faster
        "reason": (
            "Launch RPM changes the simulated ET for this bike."
            if changed
            else "No launch RPM beat the stock launch in these conditions."
        ),
        "rationale": rationale,
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
            f"General guidance — not simulated. A common drag starting point is a rear around "
            f"{rec_rear:.0f} psi (stock {stock_rear:.0f}) and a front around {rec_front:.0f} psi; "
            f"the track is at {track_temp:.0f}°C. Tyre pressure has no effect in the "
            "MotoQuant simulation, so treat this as a starting point and verify it on the track."
        ),
        "simulated": False,
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
            f"General guidance — not simulated. Air is {abs(1.0 - sigma) * 100:.0f}% "
            f"{'thinner' if sigma < 1 else 'denser'} than sea-level std (DA {da:.0f} ft). "
            f"{applic} Fuel and timing are not modelled, so this shows no ET change."
        ),
        "is_guideline": True,
        "simulated": False,
    }


def _drop_gearing(gearing: dict, stock: dict) -> None:
    """Withdraw the gearing change: the quickest verified setup does not use it."""
    gearing.update(
        recommended_front=gearing["stock_front"],
        recommended_rear=gearing["stock_rear"],
        recommended_final_drive=round(
            gearing["stock_rear"] / max(1, gearing["stock_front"]), 3
        ),
        et_s=stock["et_s"],
        trap_kmh=stock["trap_kmh"],
        delta_et_s=0.0,
        recommendation=(
            f"keep stock {gearing['stock_front']}/{gearing['stock_rear']} gearing "
            "(no gain beyond the launch-RPM change)"
        ),
    )


def _drop_launch(launch: dict, stock: dict) -> None:
    """Withdraw the launch-RPM change: the quickest verified setup does not use it."""
    reason = (
        "No gain beyond the gearing change, so no launch-RPM change is recommended."
    )
    launch.update(
        adjustable=False,
        recommended_rpm=None,
        changed=False,
        requires_two_step=False,
        et_s=stock["et_s"],
        trap_kmh=stock["trap_kmh"],
        delta_et_s=0.0,
        reason=reason,
        rationale=reason,
    )


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

    # One memo for the whole call: the stock run, both sweeps and the combined
    # verification never simulate the same config twice.
    sim = SimMemo()
    stock_et, stock_trap = sim(config)
    if _tick is not None:
        _tick("Baseline run")
    stock = {
        "et_s": round(float(stock_et), 4),
        "trap_kmh": round(float(stock_trap) * 3.6, 1),
        "launch_rpm": round(_actual_launch_rpm(config), 0),
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
        stock_trap=stock_trap,
        sim=sim,
    )
    launch = _launch_recommendation(
        config,
        stock_et,
        steps=launch_steps,
        on_sim=(lambda: _tick("Sweeping launch RPM")) if _tick is not None else None,
        stock_trap=stock_trap,
        sim=sim,
    )
    tyres = _tyre_pressure_recommendation(config, env_block)
    fuel = _fuel_timing_recommendation(config, env_block, sigma)

    # Headline setup = whichever verified configuration is actually quickest:
    # gearing alone, launch RPM alone, or both together. The two sweeps each
    # ran at the OTHER knob's stock value, so their joint effect is not simply
    # additive and can be slower than one knob by itself. A knob that does not
    # earn its place is dropped from the recommendation, so the combined run
    # is always the sim of exactly what is recommended.
    combined = {
        "et_s": stock["et_s"],
        "trap_kmh": stock["trap_kmh"],
        "delta_et_s": 0.0,
        "knobs": [],
    }
    if include_combined:
        g_change = bool(
            gearing.get("adjustable")
            and gearing.get("recommended_rear")
            and gearing["recommended_rear"] != gearing.get("stock_rear")
        )
        l_change = bool(launch.get("changed"))
        options: list[tuple[float, float, tuple[str, ...]]] = []
        if g_change:
            options.append((gearing["et_s"], gearing["trap_kmh"], ("gearing",)))
        if l_change:
            options.append((launch["et_s"], launch["trap_kmh"], ("launch_rpm",)))
        if g_change and l_change:
            cfg = copy.deepcopy(config)
            cfg.drivetrain.rear_sprocket = int(gearing["recommended_rear"])
            cfg.staging.two_step = True
            cfg.staging.launch_rpm = float(launch["recommended_rpm"])
            c_et, c_trap = sim(cfg)
            if _tick is not None:
                _tick("Verifying combined setup")
            options.append(
                (
                    round(float(c_et), 4),
                    round(float(c_trap) * 3.6, 1),
                    ("gearing", "launch_rpm"),
                )
            )
        # Only a setup that beats stock is worth recommending; on a tie the
        # one with fewer changes wins (min() keeps the first, singles come first).
        best = min(options, key=lambda o: o[0], default=None)
        if best is not None and best[0] < stock["et_s"]:
            c_et_r, c_trap_kmh, knobs = best
            combined = {
                "et_s": float(c_et_r),
                "trap_kmh": float(c_trap_kmh),
                "delta_et_s": round(float(c_et_r) - stock["et_s"], 4)
                + 0.0,  # negative = faster
                "knobs": list(knobs),
            }
        if "gearing" not in combined["knobs"] and g_change:
            _drop_gearing(gearing, stock)
        if "launch_rpm" not in combined["knobs"] and l_change:
            _drop_launch(launch, stock)

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
        f"{air_note} The simulated setup change takes the quarter from "
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
        engine="native" if engine_select.native_active() else "python",
    )
