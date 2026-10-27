"""
test_epoch_physics_intercooler.py
=================================
2026-10 physics epoch, item 6: a turbo with NO intercooler pays the full
charge-temperature penalty (eta_ic = 0).

The penalty ``1 - 0.02·(1 - eta_ic)·bar`` used to sit inside
``if intercooler_type != "none"``, so the non-intercooled turbo made the MOST
torque (audit 2026-10-23: none 1.9928 > a2w 1.9908 > a2a 1.9828 at 1 bar).
"""

from __future__ import annotations

import pytest

import motoquant
from motoquant.defaults import hayabusa_gen1


def _turbo(ic: str, eta: float = 0.75):
    cfg = hayabusa_gen1()
    fi = cfg.forced_induction
    fi.boost_type = "turbo"
    fi.target_boost_bar = 1.0
    fi.intercooler_type = ic
    fi.intercooler_effectiveness = eta
    return cfg


def _mult(cfg, p_boost=1e5):
    return motoquant.MotoQuantEngine(cfg).forced_induction_torque_mult(
        9000.0, 1.0, p_boost
    )


def test_no_intercooler_gets_the_full_penalty():
    eng = motoquant.MotoQuantEngine(_turbo("none", eta=0.95))
    p_atm = eng.rho * 287.058 * (eng.cfg.environment.ambient_temp_c + 273.15)
    expect = (1.0 + 1e5 / p_atm) * max(0.90, 1.0 - 0.02 * 1.0 * 1.0)
    # the configured effectiveness is ignored when there is no intercooler
    assert eng.forced_induction_torque_mult(9000.0, 1.0, 1e5) == pytest.approx(
        expect, abs=1e-12
    )


def test_better_intercooling_never_loses_torque():
    m_none = _mult(_turbo("none"))
    m_a2a_50 = _mult(_turbo("a2a", 0.5))
    m_a2a_75 = _mult(_turbo("a2a", 0.75))
    m_a2w_95 = _mult(_turbo("a2w", 0.95))
    assert m_none < m_a2a_50 < m_a2a_75 < m_a2w_95


def test_no_intercooler_is_slower_on_the_strip():
    et_none = motoquant.MotoQuantEngine(_turbo("none")).run().time_quarter
    et_ic = motoquant.MotoQuantEngine(_turbo("a2w", 0.95)).run().time_quarter
    assert et_none > et_ic
