"""
MotoQuant — physics engine selection
====================================

One place that decides which integrator runs a simulation:

* ``python`` — :class:`motoquant.physics.MotoQuantEngine`, the reference.
* ``native`` — :class:`motoquant.native.NativeEngine`, the Rust core
  (``rust/motoquant-core``). It subclasses the Python engine and only
  replaces ``run()``; results are bit-identical on hosts where the extension
  reproduces the host's NumPy/libm math exactly (``native.host_math()``).

``MOTOQUANT_ENGINE`` selects the mode:

* ``auto`` (default) — native when the extension is importable,
  schema-compatible, NOT stale (built from the Rust sources in this checkout,
  when the checkout has them) AND reproduces the host math exactly;
  otherwise Python.
* ``python`` — always the reference engine (kill switch).
* ``native`` — require the Rust core; raises if it is unavailable or stale.
* anything else (a dashboard typo such as ``rust``) — the Python reference,
  with a one-time WARNING log. ``engine_info()`` (and so ``/api/health``)
  reports ``mode: "invalid"`` plus the error, and that matches what actually
  runs: simulations keep working instead of every route returning 500 while
  the health probe says ``ok``.

The choice is read on every call, so tests and operators can flip the env
var at runtime without re-importing anything.
"""

from __future__ import annotations

import logging
import os

from .constants import QUARTER_MILE_M, ROLLOUT_M
from .models import BikeConfig
from .physics import MotoQuantEngine, SimResult

log = logging.getLogger(__name__)

_VALID_MODES = ("auto", "python", "native")
_warned_invalid: set[str] = set()


def engine_mode() -> str:
    """The configured mode (``MOTOQUANT_ENGINE``), validated (strict: raises
    ``ValueError`` on an unknown value)."""
    mode = os.environ.get("MOTOQUANT_ENGINE", "auto").strip().lower() or "auto"
    if mode not in _VALID_MODES:
        raise ValueError(
            f"MOTOQUANT_ENGINE={mode!r} is invalid; expected one of {_VALID_MODES}"
        )
    return mode


def effective_mode() -> str:
    """The mode simulations actually use: :func:`engine_mode`, except that an
    invalid value degrades to ``python`` (warned once per distinct value)."""
    try:
        return engine_mode()
    except ValueError as exc:
        raw = os.environ.get("MOTOQUANT_ENGINE", "")
        if raw not in _warned_invalid:
            _warned_invalid.add(raw)
            log.warning("%s; using the Python reference engine.", exc)
        return "python"


def fallback_reason() -> str | None:
    """Why ``auto`` would NOT use the Rust core (None = it would)."""
    from . import native

    if not native.available():
        return "unavailable"
    if native.is_stale():
        return "stale"
    if not native.host_math().get("exact"):
        return "host math not reproduced exactly"
    return None


def native_active() -> bool:
    """True when simulations will run on the Rust core."""
    mode = effective_mode()
    if mode == "python":
        return False
    if mode == "native":
        reason = fallback_reason()
        if reason in ("unavailable", "stale"):
            raise RuntimeError(
                f"MOTOQUANT_ENGINE=native but the Rust core is {reason} "
                "(build it with `make native`)."
            )
        return True
    return fallback_reason() is None


def engine_class():
    """The engine class every simulation should construct."""
    if native_active():
        from .native import NativeEngine

        return NativeEngine
    return MotoQuantEngine


def make_engine(config: BikeConfig, dt: float = 0.001) -> MotoQuantEngine:
    """Construct the selected engine for ``config``."""
    return engine_class()(config, dt=dt)


def run_quarter(
    config: BikeConfig,
    distance: float = QUARTER_MILE_M,
    max_time: float = 26.0,
    use_adaptive_dt: bool = False,
    *,
    dt: float = 0.001,
    progress_cb=None,
    rollout_m: float = ROLLOUT_M,
) -> SimResult:
    """Convenience: build the selected engine and run it (splits timed with
    the drag-strip ``rollout_m`` convention; 0.0 = from first motion)."""
    return make_engine(config, dt=dt).run(
        distance=distance,
        max_time=max_time,
        use_adaptive_dt=use_adaptive_dt,
        progress_cb=progress_cb,
        rollout_m=rollout_m,
    )


def engine_info() -> dict:
    """Diagnostics for ``/api/health`` and the CLI."""
    try:
        mode = engine_mode()
    except ValueError as exc:
        # Same fallback the simulations take (effective_mode): the Python
        # reference serves, and the bad value stays visible here.
        effective_mode()  # emit the one-time warning on a health probe too
        return {"engine": "python", "mode": "invalid", "error": str(exc)}
    info: dict = {"mode": mode}
    try:
        from . import native

        info["native"] = native.native_info()
        info["engine"] = "native" if native_active() else "python"
        if mode == "auto" and info["engine"] == "python":
            info["fallback_reason"] = fallback_reason()
    except Exception as exc:  # never let diagnostics break a health probe
        log.warning("engine_info: native probe failed: %s", exc)
        info["engine"] = "python"
        info["native_error"] = str(exc)
    return info
