"""The chat agent's unknown-bike estimator must build its engine through
``engine_select`` (Rust core when available), like every other sim call
site, instead of constructing the Python ``MotoQuantEngine`` directly."""

from __future__ import annotations

from motoquant import engine_select
from motoquant.llm.estimator import simulate_estimated_bike

SPEC = {
    "manufacturer": "Testmoto",
    "model_name": "Estimator 600",
    "displacement_cc": 599,
    "peak_power_hp": 118,
    "peak_power_rpm": 13000,
    "peak_torque_nm": 66,
    "peak_torque_rpm": 11000,
    "dry_mass_kg": 167,
    "cylinders": 4,
    "category": "sport",
}


def test_estimator_uses_engine_select(monkeypatch):
    calls = []
    real = engine_select.make_engine

    def spy(config, dt=0.001):
        engine = real(config, dt=dt)
        calls.append(type(engine))
        return engine

    monkeypatch.setattr(engine_select, "make_engine", spy)
    out = simulate_estimated_bike(SPEC, include_top_speed=False, log_suggestion=False)
    assert "error" not in out, out
    assert out["estimated"] is True
    assert calls == [engine_select.engine_class()]
    assert 9.0 < out["et_quarter_s"] < 14.0
