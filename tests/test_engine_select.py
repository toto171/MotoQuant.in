"""
Engine selection — ``motoquant/engine_select.py`` and every production call
site that runs a simulation through it.

What is pinned here:

* ``MOTOQUANT_ENGINE`` parsing (auto / python / native, case + whitespace,
  invalid values) and the fallback rules: ``auto`` uses the Rust core only
  when it is available, NOT stale and reproduces the host math exactly;
  ``python`` is a kill switch; ``native`` raises when the core is missing or
  stale.
* ``/api/health`` reports the engine (and stays under the 1 KB gzip floor).
* PRODUCTION-PATH parity: the API routes (quick sim incl. its stock baseline,
  full sim, top speed, distance, compare), the chat agent, the NL runner and
  the MCP local backend return IDENTICAL numbers under
  ``MOTOQUANT_ENGINE=python`` and ``auto`` — and under ``auto`` they really
  ran on the Rust core (counted through a spy on ``NativeEngine.run``). The
  native halves skip when the extension is not built.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest

pytest.importorskip("fastapi")

import motoquant as mq  # noqa: E402
from motoquant import engine_select, native  # noqa: E402
from motoquant.physics import MotoQuantEngine  # noqa: E402

needs_native = pytest.mark.skipif(
    not native.available() and os.environ.get("MOTOQUANT_REQUIRE_NATIVE") != "1",
    reason="motoquant_core not built (make native)",
)

# ── Isolated DB copy (the tracked motoquant.db is never written) ─────────────
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_DB = os.path.join(_REPO_ROOT, "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(
    prefix="mq_engine_select_", suffix=".db", delete=False
)
_tmp.close()
_TMP_DB = _tmp.name
_PRIOR_DB = os.environ.get("MOTOQUANT_DB")
_src = sqlite3.connect(f"file:{_SRC_DB}?mode=ro", uri=True)
_dst = sqlite3.connect(_TMP_DB)
try:
    _src.backup(_dst)
finally:
    _dst.close()
    _src.close()


def setup_module():
    os.environ["MOTOQUANT_DB"] = _TMP_DB
    import motoquant.api as api_mod

    api_mod._db_conn = None


def teardown_module():
    import motoquant.api as api_mod

    if api_mod._db_conn is not None:
        try:
            api_mod._db_conn.close()
        except Exception:
            pass
        api_mod._db_conn = None
    if _PRIOR_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_DB
    try:
        os.unlink(_TMP_DB)
    except OSError:
        pass


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    import motoquant.api as api_mod

    os.environ["MOTOQUANT_DB"] = _TMP_DB
    api_mod._db_conn = None
    return TestClient(api_mod.app)


@pytest.fixture
def native_calls(monkeypatch):
    """Count NativeEngine.run invocations (the real method still runs)."""
    calls = {"n": 0}
    orig = native.NativeEngine.run

    def spy(self, *a, **kw):
        calls["n"] += 1
        return orig(self, *a, **kw)

    monkeypatch.setattr(native.NativeEngine, "run", spy)
    return calls


# ── mode parsing ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,mode",
    [(None, "auto"), ("", "auto"), ("  ", "auto"), ("AUTO", "auto"),
     (" Python ", "python"), ("native", "native")],
)  # fmt: skip
def test_mode_parsing(monkeypatch, raw, mode):
    if raw is None:
        monkeypatch.delenv("MOTOQUANT_ENGINE", raising=False)
    else:
        monkeypatch.setenv("MOTOQUANT_ENGINE", raw)
    assert engine_select.engine_mode() == mode


def test_invalid_mode_raises_but_health_info_survives(monkeypatch):
    monkeypatch.setenv("MOTOQUANT_ENGINE", "rust-please")
    with pytest.raises(ValueError, match="MOTOQUANT_ENGINE"):
        engine_select.engine_mode()
    with pytest.raises(ValueError):
        engine_select.make_engine(mq.gsxr1000_k5())
    info = engine_select.engine_info()
    assert info["mode"] == "invalid" and info["engine"] == "python"


def test_kill_switch_forces_the_python_reference(monkeypatch):
    monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
    eng = engine_select.make_engine(mq.gsxr1000_k5())
    assert type(eng) is MotoQuantEngine
    assert engine_select.engine_class() is MotoQuantEngine
    assert engine_select.engine_info()["engine"] == "python"


def test_native_mode_raises_when_unavailable(monkeypatch):
    monkeypatch.setenv("MOTOQUANT_ENGINE", "native")
    monkeypatch.setattr(native, "available", lambda: False)
    with pytest.raises(RuntimeError, match="unavailable"):
        engine_select.make_engine(mq.gsxr1000_k5())
    # auto silently falls back instead, and says why
    monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
    assert type(engine_select.make_engine(mq.gsxr1000_k5())) is MotoQuantEngine
    assert engine_select.fallback_reason() == "unavailable"


def test_stale_build_is_refused(monkeypatch):
    monkeypatch.setattr(native, "available", lambda: True)
    monkeypatch.setattr(native, "is_stale", lambda: True)
    monkeypatch.setenv("MOTOQUANT_ENGINE", "native")
    with pytest.raises(RuntimeError, match="stale"):
        engine_select.make_engine(mq.gsxr1000_k5())
    monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
    assert engine_select.fallback_reason() == "stale"
    assert type(engine_select.make_engine(mq.gsxr1000_k5())) is MotoQuantEngine


def test_auto_requires_exact_host_math(monkeypatch):
    monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
    monkeypatch.setattr(native, "available", lambda: True)
    monkeypatch.setattr(native, "is_stale", lambda: False)
    monkeypatch.setattr(native, "host_math", lambda: {"exact": False})
    assert engine_select.fallback_reason() == "host math not reproduced exactly"
    assert engine_select.engine_class() is MotoQuantEngine


@needs_native
def test_auto_and_native_modes_pick_the_rust_core(monkeypatch):
    for mode in ("auto", "native"):
        monkeypatch.setenv("MOTOQUANT_ENGINE", mode)
        eng = engine_select.make_engine(mq.gsxr1000_k5())
        assert type(eng) is native.NativeEngine
        assert isinstance(eng, MotoQuantEngine)  # drop-in subclass
    r = engine_select.run_quarter(mq.gsxr1000_k5())
    assert r.time_quarter == MotoQuantEngine(mq.gsxr1000_k5()).run().time_quarter


# ── /api/health ──────────────────────────────────────────────────────────────


def test_health_reports_engine(client, monkeypatch):
    monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
    r = client.get("/api/health")
    assert r.status_code == 200
    eng = r.json()["engine"]
    assert eng["mode"] == "python" and eng["engine"] == "python"
    assert "native" in eng and eng["native"]["schema"] == native.SCHEMA_VERSION
    monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
    body = client.get("/api/health")
    expected = "native" if engine_select.native_active() else "python"
    assert body.json()["engine"]["engine"] == expected
    # Must stay below GZipMiddleware's minimum_size (tests/test_fuses_*).
    assert len(body.content) < 1024


# ── production-path parity: python vs auto ───────────────────────────────────

_BIKE_IDS = (3, 11, 120, 300)
_QUICK_FIELDS = (
    "et_quarter_s",
    "trap_speed_kmh",
    "et_60ft_s",
    "et_eighth_s",
    "stock_et_s",
)


def _post(client, path, body):
    r = client.post(path, json=body)
    assert r.status_code == 200, (path, r.status_code, r.text[:300])
    return r.json()


def _both(client, monkeypatch, native_calls, path, body, *, sims):
    """POST under python then auto; under auto EVERY one of the route's
    ``sims`` simulations must have run on the Rust core (so a single call
    site left on MotoQuantEngine fails the count)."""
    monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
    before = native_calls["n"]
    py = _post(client, path, body)
    assert native_calls["n"] == before, f"{path}: python mode ran the Rust core"
    monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
    na = _post(client, path, body)
    ran = native_calls["n"] - before
    assert ran == sims, f"{path}: {ran}/{sims} simulations ran on the Rust core"
    return py, na


@needs_native
@pytest.mark.parametrize("bike_id", _BIKE_IDS)
def test_quick_sim_identical_python_vs_auto(client, monkeypatch, native_calls, bike_id):
    # A part forces the stock-baseline sim too (both construction sites).
    py, na = _both(
        client,
        monkeypatch,
        native_calls,
        "/api/simulate/quick",
        {"bike_id": bike_id, "venue_id": 1, "part_ids": [1]},
        sims=2,  # modified build + stock baseline
    )
    assert py == na and py["stock_et_s"] is not None


@needs_native
def test_full_sim_and_compare_identical_python_vs_auto(
    client, monkeypatch, native_calls
):
    body = {"bike_id": 11, "venue_id": 2, "use_adaptive_dt": True}
    py, na = _both(client, monkeypatch, native_calls, "/api/simulate", body, sims=1)
    assert py == na
    cmp_body = {"a_bike_id": 11, "b_bike_id": 3}
    py, na = _both(
        client, monkeypatch, native_calls, "/api/simulate/compare", cmp_body, sims=2
    )
    assert py == na


@needs_native
def test_topspeed_and_distance_identical_python_vs_auto(
    client, monkeypatch, native_calls
):
    py, na = _both(
        client,
        monkeypatch,
        native_calls,
        "/api/simulate/top-speed",
        {"bike_id": 11},
        sims=1,
    )
    assert py == na
    py, na = _both(
        client,
        monkeypatch,
        native_calls,
        "/api/simulate/distance",
        {"bike_id": 11, "distance_m": 1000.0},
        sims=1,
    )
    assert py == na


def _db():
    from motoquant.database.connection import MotoQuantDB

    return MotoQuantDB(_TMP_DB)


@needs_native
def test_agent_runner_and_mcp_route_through_engine_select(monkeypatch, native_calls):
    from motoquant.llm.agent import AgentChatResult, AgentContext, _exec_run_simulation
    from motoquant.llm.parse_query import ParsedSimRequest
    from motoquant.llm.runner import _run_one_sim
    from motoquant.mcp_server import LocalBackend

    db = _db()

    def agent():
        ctx = AgentContext(db=db, result=AgentChatResult(raw_query=""))
        return _exec_run_simulation(ctx, {"bike_id": 11})

    def runner():
        return _run_one_sim(11, ParsedSimRequest(raw_query="", bike_name="x"), db)

    def mcp():
        os.environ["MOTOQUANT_DB"] = _TMP_DB
        return LocalBackend().simulate_gearing({"bike_id": 11}, 17, 42)

    for label, fn in (("agent", agent), ("runner", runner), ("mcp", mcp)):
        monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
        before = native_calls["n"]
        py = fn()
        assert native_calls["n"] == before, label
        monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
        na = fn()
        assert native_calls["n"] == before + 1, f"{label} did not use the Rust core"
        assert py == na, label
        assert "error" not in str(py)[:200].lower(), (label, py)


def test_quick_response_carries_the_compared_numbers(client, monkeypatch):
    """Guard the parity tests above: the quick-sim response (with a part, so
    the stock-baseline sim runs too) really carries the numbers compared — a
    payload that silently lost them would make ``py == na`` vacuous."""
    monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
    body = _post(
        client, "/api/simulate/quick", {"bike_id": 11, "venue_id": 1, "part_ids": [1]}
    )
    for k in _QUICK_FIELDS:
        assert isinstance(body.get(k), float) and body[k] > 0, (k, body.get(k))


def _dragy_csv() -> bytes:
    """Minimal imperial Dragy CSV: 20 staged frames, then a launch ramp."""
    dt, lines, dist_ft = 0.03, ["Time (s),Speed (mph),Distance (ft)"], 0.0
    lines += [f"{i * dt:.3f},0.0000,0.0000" for i in range(20)]
    for i in range(400):
        v_mph = 160.0 * (i / 400) ** 0.7
        dist_ft += v_mph * 0.44704 * dt / 0.3048
        lines.append(f"{(20 + i) * dt:.3f},{v_mph:.4f},{dist_ft:.4f}")
    return "\n".join(lines).encode()


@needs_native
def test_dragy_overlay_sim_routes_through_engine_select(
    client, monkeypatch, native_calls
):
    import io

    def upload():
        r = client.post(
            "/api/calibrate/dragy",
            files={"file": ("run.csv", io.BytesIO(_dragy_csv()), "text/csv")},
            data={"bike_preset": "hayabusa_gen1"},
        )
        assert r.status_code == 200, r.text[:300]
        return r.json()["overlay"]

    monkeypatch.setenv("MOTOQUANT_ENGINE", "python")
    before = native_calls["n"]
    py = upload()
    assert native_calls["n"] == before
    monkeypatch.setenv("MOTOQUANT_ENGINE", "auto")
    na = upload()
    assert native_calls["n"] == before + 1, "overlay sim did not use the Rust core"
    assert py == na and py["sim_et_s"] > 0
