"""
Tests for motoquant.mcp_server -- the stdio MCP server.

Zero network. Everything runs against a TEMP COPY of the tracked
``motoquant.db`` (the tracked file is never opened for writing), driving the
server exactly the way an MCP client does: newline-delimited JSON-RPC 2.0
messages in, JSON-RPC responses out.

Covered:
  * initialize / notifications/initialized / ping handshake
  * tools/list shape (every tool has a name, description, object schema)
  * tools/call in LOCAL mode for search_bikes + simulate_quarter_mile
    (the production path -- LocalBackend dispatches into motoquant.api)
  * gearing_impact on both backends: direct sprocket override (local) and the
    catalog-sprocket fallback (HTTP framing, served by a loopback stub)
  * malformed input: bad JSON, unknown method, unknown tool, missing args
"""

import io
import json
import os
import sqlite3
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Isolated DB: back up the tracked catalog into a tmp file BEFORE motoquant.api
# is imported/connected. sqlite3's backup API reads through a read-only handle
# and merges any WAL, so the tracked motoquant.db is never written.
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_DB = os.path.join(_REPO_ROOT, "motoquant.db")

_tmp = tempfile.NamedTemporaryFile(prefix="motoquant_mcp_", suffix=".db", delete=False)
_tmp.close()
_TMP_DB_PATH = _tmp.name
_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MCP_LOCAL = os.environ.get("MOTOQUANT_MCP_LOCAL")

if not os.path.exists(_SRC_DB):  # pragma: no cover
    raise FileNotFoundError(
        f"{_SRC_DB} missing — these tests need the shipped catalog DB"
    )
_src = sqlite3.connect(f"file:{_SRC_DB}?mode=ro", uri=True)
_dst = sqlite3.connect(_TMP_DB_PATH)
try:
    _src.backup(_dst)
finally:
    _dst.close()
    _src.close()

os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH

from motoquant import mcp_server  # noqa: E402
from motoquant.mcp_server import (  # noqa: E402
    TOOLS,
    HttpBackend,
    LocalBackend,
    MCPServer,
    serve,
)


def setUpModule():
    """Re-assert this module's tmp DB (sibling modules also set MOTOQUANT_DB at
    import time, which is collection time -- ordering must not matter)."""
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
    try:
        import motoquant.api as api_mod

        api_mod._db_conn = None
    except ImportError:  # pragma: no cover - fastapi absent
        pass


def tearDownModule():
    try:
        import motoquant.api as api_mod

        if api_mod._db_conn is not None:
            try:
                api_mod._db_conn.close()
            except Exception:
                pass
            api_mod._db_conn = None
    except ImportError:  # pragma: no cover
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB
    if _PRIOR_MCP_LOCAL is None:
        os.environ.pop("MOTOQUANT_MCP_LOCAL", None)
    else:
        os.environ["MOTOQUANT_MCP_LOCAL"] = _PRIOR_MCP_LOCAL
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:  # pragma: no cover
        pass


# ─── Helpers ──────────────────────────────────────────────────────────────


def _drive(messages, backend=None):
    """Feed JSON-RPC messages through the real stdio loop; return responses."""
    stdin = io.StringIO(
        "\n".join(m if isinstance(m, str) else json.dumps(m) for m in messages) + "\n"
    )
    stdout = io.StringIO()
    server = MCPServer(backend=backend if backend is not None else LocalBackend())
    serve(server, stdin, stdout)
    lines = [ln for ln in stdout.getvalue().splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines], server


def _call(name, arguments=None, backend=None):
    """tools/call one tool; return (is_error, parsed_payload_or_text)."""
    responses, _ = _drive(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }
        ],
        backend=backend,
    )
    result = responses[0]["result"]
    text = result["content"][0]["text"]
    if result.get("isError"):
        return True, text
    return False, json.loads(text)


class _LoopbackHttpBackend(HttpBackend):
    """HttpBackend with the socket swapped for the local API.

    Exercises the real HTTP-mode code paths (URL/param building, response
    shapes, the catalog-sprocket gearing fallback) without any network.
    """

    def __init__(self):
        super().__init__("http://loopback.test", timeout=5.0)
        self._local = LocalBackend()
        self.calls = []

    def _request(self, method, path, params=None, payload=None):
        self.calls.append((method, path))
        if method == "GET" and path == "/api/parts":
            p = dict(params or {})
            if isinstance(p.get("compatible_only"), str):
                p["compatible_only"] = p["compatible_only"] == "true"
            return self._local.list_parts(**p)
        if method == "GET" and path == "/api/bikes":
            return self._local.list_bikes(**(params or {}))
        if method == "POST" and path == "/api/simulate/compare":
            return self._local.compare(payload or {})
        if method == "POST" and path == "/api/simulate/quick":
            return self._local.simulate_quick(payload or {})
        raise AssertionError(f"unexpected request {method} {path}")


# ─── Protocol ─────────────────────────────────────────────────────────────


class TestHandshake(unittest.TestCase):
    def test_initialize_returns_capabilities_and_server_info(self):
        responses, server = _drive(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "pytest", "version": "1"},
                    },
                },
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "ping"},
            ]
        )
        # The notification must NOT get a response -- 3 messages in, 2 out.
        self.assertEqual(len(responses), 2)
        init = responses[0]
        self.assertEqual(init["jsonrpc"], "2.0")
        self.assertEqual(init["id"], 1)
        result = init["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "motoquant")
        self.assertTrue(result["instructions"])
        self.assertTrue(server.initialized)
        self.assertEqual(responses[1]["result"], {})

    def test_unknown_protocol_version_falls_back_to_ours(self):
        responses, _ = _drive(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "1999-01-01"},
                }
            ]
        )
        self.assertIn(
            responses[0]["result"]["protocolVersion"],
            mcp_server.SUPPORTED_PROTOCOL_VERSIONS,
        )


class TestToolsList(unittest.TestCase):
    def test_every_tool_is_listed_with_a_valid_schema(self):
        responses, _ = _drive([{"jsonrpc": "2.0", "id": 7, "method": "tools/list"}])
        tools = responses[0]["result"]["tools"]
        self.assertEqual(len(tools), len(TOOLS))

        names = {t["name"] for t in tools}
        for expected in (
            "search_bikes",
            "get_bike",
            "simulate_quarter_mile",
            "simulate_top_speed",
            "compare_bikes",
            "list_venues",
            "search_parts",
            "part_impact",
            "gearing_impact",
        ):
            self.assertIn(expected, names)

        for tool in tools:
            with self.subTest(tool=tool["name"]):
                self.assertRegex(tool["name"], r"^[a-z][a-z0-9_]*$")
                self.assertGreater(len(tool["description"]), 30)
                schema = tool["inputSchema"]
                self.assertEqual(schema["type"], "object")
                self.assertIsInstance(schema["properties"], dict)
                self.assertIsInstance(schema["required"], list)
                # Required keys must actually exist in properties.
                for req in schema["required"]:
                    self.assertIn(req, schema["properties"])
                # Every property must declare a type (clients validate on this).
                for prop_name, prop in schema["properties"].items():
                    self.assertIn("type", prop, f"{tool['name']}.{prop_name}")
                # Schema must be JSON-serialisable as-is.
                json.dumps(schema)

    def test_handlers_are_not_leaked_over_the_wire(self):
        responses, _ = _drive([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}])
        for tool in responses[0]["result"]["tools"]:
            self.assertNotIn("handler", tool)


# ─── Tool calls (LOCAL backend, production code path) ─────────────────────


class TestToolCallsLocal(unittest.TestCase):
    def test_search_bikes_returns_catalog_ids(self):
        is_error, payload = _call("search_bikes", {"query": "hayabusa", "limit": 5})
        self.assertFalse(is_error, payload)
        self.assertGreater(payload["total_matching"], 0)
        self.assertGreaterEqual(len(payload["bikes"]), 1)
        first = payload["bikes"][0]
        self.assertIsInstance(first["id"], int)
        self.assertIn("Hayabusa", first["model"])
        self.assertEqual(first["manufacturer"], "Suzuki")

    def test_search_bikes_limit_is_capped(self):
        is_error, payload = _call("search_bikes", {"limit": 5000})
        self.assertFalse(is_error, payload)
        self.assertLessEqual(len(payload["bikes"]), 50)

    def test_simulate_quarter_mile_preset_matches_pinned_baseline(self):
        """The K5 reference is pinned bit-identical (AGENTS.md prime directive);
        the MCP surface must report that same number, not a copy of it."""
        is_error, payload = _call(
            "simulate_quarter_mile", {"bike_preset": "gsxr1000_k5"}
        )
        self.assertFalse(is_error, payload)
        self.assertAlmostEqual(payload["et_s"], 10.0436, places=4)
        self.assertGreater(payload["trap_kmh"], 200)
        self.assertLess(payload["et_60ft_s"], payload["et_eighth_s"])
        self.assertLess(payload["et_eighth_s"], payload["et_s"])

    def test_simulate_quarter_mile_by_bike_id(self):
        _, found = _call("search_bikes", {"query": "hayabusa", "limit": 1})
        bike_id = found["bikes"][0]["id"]
        is_error, payload = _call("simulate_quarter_mile", {"bike_id": bike_id})
        self.assertFalse(is_error, payload)
        self.assertGreater(payload["et_s"], 7.0)
        self.assertLess(payload["et_s"], 16.0)
        self.assertIn("Hayabusa", payload["bike"])

    def test_simulate_requires_a_bike(self):
        is_error, text = _call("simulate_quarter_mile", {"rider_mass_kg": 80})
        self.assertTrue(is_error)
        self.assertIn("bike_id", text)

    def test_unknown_bike_id_is_a_tool_error_not_a_crash(self):
        is_error, text = _call("simulate_quarter_mile", {"bike_id": 999999})
        self.assertTrue(is_error)
        self.assertIn("404", text)

    def test_list_venues(self):
        is_error, payload = _call("list_venues")
        self.assertFalse(is_error, payload)
        self.assertGreater(len(payload["venues"]), 0)
        self.assertIn("altitude_m", payload["venues"][0])

    def test_gearing_impact_local_uses_direct_override(self):
        is_error, payload = _call(
            "gearing_impact",
            {
                "bike_preset": "gsxr1000_k5",
                "front_a": 17,
                "rear_a": 42,
                "front_b": 17,
                "rear_b": 47,
            },
        )
        self.assertFalse(is_error, payload)
        self.assertIn("local", payload["method"])
        self.assertEqual(payload["a"]["rear_sprocket"], 42)
        self.assertEqual(payload["b"]["rear_sprocket"], 47)
        self.assertGreater(
            payload["b"]["final_drive_ratio"], payload["a"]["final_drive_ratio"]
        )
        # Setup A IS the K5's stock 17/42, so this path must reproduce the
        # pinned baseline exactly -- proof the sprocket override rides the real
        # config builder rather than a parallel re-implementation.
        self.assertAlmostEqual(payload["a"]["et_s"], 10.0436, places=4)
        # The swap must actually move the physics at BOTH the launch and the
        # stripe. Which way it moves is bike-specific (a grip-limited litre
        # bike loses to shorter gearing, a power-limited 150 gains), so the
        # direction is deliberately not asserted here.
        self.assertNotEqual(payload["a"]["et_s"], payload["b"]["et_s"])
        self.assertNotEqual(payload["a"]["et_60ft_s"], payload["b"]["et_60ft_s"])
        self.assertAlmostEqual(
            payload["delta"]["et_s"],
            round(payload["b"]["et_s"] - payload["a"]["et_s"], 4),
            places=4,
        )
        self.assertIn(payload["delta"]["faster"], ("A", "B", "tie"))

    def test_gearing_impact_rejects_absurd_teeth(self):
        is_error, text = _call(
            "gearing_impact",
            {
                "bike_preset": "gsxr1000_k5",
                "front_a": 17,
                "rear_a": 42,
                "front_b": 400,
                "rear_b": 42,
            },
        )
        self.assertTrue(is_error)
        self.assertIn("outside", text)


# ─── HTTP-mode paths (loopback stub -- no sockets) ────────────────────────


class TestHttpBackendPaths(unittest.TestCase):
    def test_gearing_impact_falls_back_to_catalog_sprockets(self):
        backend = _LoopbackHttpBackend()
        is_error, payload = _call(
            "gearing_impact",
            {
                "bike_preset": "gsxr1000_k5",
                "front_a": 17,
                "rear_a": 42,
                "front_b": 16,
                "rear_b": 45,
            },
            backend=backend,
        )
        self.assertFalse(is_error, payload)
        self.assertIn("hosted API", payload["method"])
        self.assertEqual(payload["a"]["front_sprocket"], 17)
        self.assertEqual(payload["b"]["rear_sprocket"], 45)
        self.assertNotEqual(payload["a"]["et_s"], payload["b"]["et_s"])
        # One catalog fetch for both setups, then a single compare call.
        self.assertEqual(backend.calls.count(("GET", "/api/parts")), 1)
        self.assertIn(("POST", "/api/simulate/compare"), backend.calls)

    def test_gearing_impact_reports_unavailable_tooth_counts_honestly(self):
        is_error, text = _call(
            "gearing_impact",
            {
                "bike_preset": "gsxr1000_k5",
                "front_a": 17,
                "rear_a": 42,
                "front_b": 17,
                "rear_b": 79,  # in-range, but no such sprocket in the catalog
            },
            backend=_LoopbackHttpBackend(),
        )
        self.assertTrue(is_error)
        self.assertIn("rear 79T", text)
        self.assertIn("MOTOQUANT_MCP_LOCAL", text)

    def test_query_params_drop_none_values(self):
        backend = _LoopbackHttpBackend()
        is_error, payload = _call(
            "search_bikes", {"query": "ninja", "limit": 3}, backend=backend
        )
        self.assertFalse(is_error, payload)
        self.assertEqual(backend.calls, [("GET", "/api/bikes")])

    def test_http_backend_reports_unreachable_api_as_a_tool_error(self):
        backend = HttpBackend("http://127.0.0.1:1", timeout=1.0)
        is_error, text = _call("list_venues", backend=backend)
        self.assertTrue(is_error)
        self.assertIn("Could not reach", text)


# ─── Conditions and skipped parts reach the MCP result ────────────────────

_ENV = {
    "name": "Test Strip",
    "is_default": False,
    "source": "venue",
    "altitude_m": 679.0,
    "ambient_temp_c": 22.0,
    "track_surface": "asphalt",
}


_SKIP = {"id": 999, "reason": "does_not_fit", "detail": "Part 999 does not fit."}


def _api_side(name, et, **extra):
    return {
        "bike_name": name,
        "et_quarter_s": et,
        "trap_speed_kmh": 230.0,
        "et_60ft_s": 1.8,
        "et_eighth_s": 6.5,
        "peak_power_hp": 170.0,
        "total_mass_kg": 270.0,
        **extra,
    }


class _CannedBackend:
    """Answers each backend call with an API-shaped response that carries the
    ``environment`` block and ``parts_skipped`` (set ``with_extras=False`` for
    an older API that has neither)."""

    kind = "http"

    def __init__(self, with_extras=True, skip_in_compare=False):
        self.skip_in_compare = skip_in_compare
        self.extras = (
            {
                "environment": dict(_ENV),
                "parts_skipped": [999],
                "parts_skipped_detail": [dict(_SKIP)],
            }
            if with_extras
            else {}
        )

    def simulate_quick(self, payload):
        out = _api_side("Test Bike", 10.0 if not payload.get("part_ids") else 9.9)
        if payload.get("part_ids"):
            out.update(
                parts_applied=[{"id": 7, "brand": "Acme", "name": "Pipe"}],
                build_cost_inr=10_000.0,
                stock_et_s=10.0,
                et_delta_s=-0.1,
            )
        return {**out, **self.extras}

    def top_speed(self, payload):
        return {
            "bike_name": "Test Bike",
            "terminal_velocity_kmh": 290.0,
            "terminal_velocity_mph": 180.2,
            "reached_plateau": True,
            **self.extras,
        }

    def compare(self, payload):
        skipped = (
            {"parts_skipped": [999], "parts_skipped_detail": [dict(_SKIP)]}
            if self.skip_in_compare
            else {}
        )
        out = {
            "a": _api_side("Bike A", 10.0, **skipped),
            "b": _api_side("Bike B", 10.2),
            "delta": {"et_s": 0.2, "trap_kmh": -3.0, "faster": "A"},
        }
        if self.extras:
            out["environment"] = dict(_ENV)
        return out

    def list_parts(self, **kw):
        return {
            "parts": [
                {"id": 1, "param_overrides": {"drivetrain.front_sprocket": 17}},
                {"id": 2, "param_overrides": {"drivetrain.rear_sprocket": 42}},
                {"id": 3, "param_overrides": {"drivetrain.rear_sprocket": 45}},
            ]
        }


class TestConditionsAndSkippedPartsArePassedThrough(unittest.TestCase):
    """A result without its conditions cannot be compared with anything, and
    a part that silently did not fit looks applied: every result shaper must
    carry both through when the API supplies them."""

    GEARING = {
        "bike_id": 1,
        "front_a": 17,
        "rear_a": 42,
        "front_b": 17,
        "rear_b": 45,
    }

    def _calls(self, backend):
        return {
            "simulate_quarter_mile": _call(
                "simulate_quarter_mile", {"bike_id": 1, "part_ids": [7]}, backend
            ),
            "simulate_top_speed": _call("simulate_top_speed", {"bike_id": 1}, backend),
            "compare_bikes": _call(
                "compare_bikes", {"a_bike_id": 1, "b_bike_id": 2}, backend
            ),
            "part_impact": _call("part_impact", {"bike_id": 1, "part_id": 7}, backend),
            "gearing_impact": _call("gearing_impact", dict(self.GEARING), backend),
        }

    def test_every_simulation_tool_reports_its_conditions(self):
        for tool, (is_error, payload) in self._calls(_CannedBackend()).items():
            self.assertFalse(is_error, (tool, payload))
            self.assertEqual(payload.get("environment"), _ENV, tool)

    def test_skipped_parts_are_reported_where_parts_can_be_requested(self):
        got = self._calls(_CannedBackend(skip_in_compare=True))
        for tool in ("simulate_quarter_mile", "simulate_top_speed", "part_impact"):
            payload = got[tool][1]
            self.assertEqual(payload["parts_skipped"], [999], tool)
            self.assertEqual(payload["parts_skipped_detail"], [_SKIP], tool)
        # compare: per side, only on the side that skipped
        payload = got["compare_bikes"][1]
        self.assertEqual(payload["a"]["parts_skipped"], [999])
        self.assertEqual(payload["a"]["parts_skipped_detail"], [_SKIP])
        self.assertNotIn("parts_skipped", payload["b"])

    def test_gearing_comparison_is_refused_when_a_sprocket_was_not_fitted(self):
        """Over the hosted API a tooth count is a catalog sprocket. If the API
        skipped one, that side ran on other gearing: no result, the reason."""
        is_error, text = self._calls(_CannedBackend(skip_in_compare=True))[
            "gearing_impact"
        ]
        self.assertTrue(is_error, text)
        self.assertIn("setup A", text)
        self.assertIn("999", text)
        self.assertIn("does not fit", text)

    def test_part_impact_says_why_a_part_was_not_applied(self):
        class _Unfitted(_CannedBackend):
            def simulate_quick(self, payload):
                out = _api_side("Test Bike", 10.0)
                if payload.get("part_ids"):
                    out.update(parts_applied=[], **self.extras)
                return out

        is_error, text = _call(
            "part_impact", {"bike_id": 1, "part_id": 999}, _Unfitted()
        )
        self.assertTrue(is_error, text)
        self.assertIn("Part 999 does not fit.", text)

    def test_absent_fields_are_not_invented(self):
        for tool, (is_error, payload) in self._calls(_CannedBackend(False)).items():
            self.assertFalse(is_error, (tool, payload))
            self.assertNotIn("environment", payload, tool)
            self.assertNotIn("parts_skipped", payload, tool)
            self.assertNotIn("parts_skipped_detail", payload, tool)

    def test_slim_sim_keeps_both_fields(self):
        slim = mcp_server._slim_sim(
            {"bike_name": "X", "environment": _ENV, "parts_skipped": [4, 5]}
        )
        self.assertEqual(slim["environment"], _ENV)
        self.assertEqual(slim["parts_skipped"], [4, 5])
        self.assertNotIn("parts_skipped", mcp_server._slim_sim({"parts_skipped": []}))

    def test_local_backend_passes_every_route_parameter_explicitly(self):
        """The GET routes declare Query(...) defaults that only the request
        layer resolves. Called as functions, every parameter must be given a
        plain value — including ones a newer API adds."""
        from fastapi import Query

        seen = {}

        def route(
            category: str | None = Query(None),
            bike_id: int | None = Query(None, ge=1),
            bike_preset: str | None = Query(None, max_length=64),
            compatible_only: bool = Query(True),
            limit: int = Query(500, ge=1),
            fields: str | None = Query(None),
            include_rules: bool = Query(False),
            request=None,
        ):
            seen.update(locals())
            return {"parts": []}

        kwargs = LocalBackend._route_kwargs(
            route,
            {"category": "sprocket", "bike_preset": "gsxr1000_k5", "not_a_param": 1},
        )
        route(**kwargs)
        self.assertEqual(seen["category"], "sprocket")
        self.assertEqual(seen["bike_preset"], "gsxr1000_k5")
        self.assertIsNone(seen["bike_id"])
        self.assertIs(seen["compatible_only"], True)
        self.assertEqual(seen["limit"], 500)
        self.assertIsNone(seen["fields"])
        self.assertIs(seen["include_rules"], False)
        self.assertNotIn("not_a_param", kwargs)

    def test_local_results_carry_what_the_api_returns(self):
        """LOCAL mode (the production code path): the MCP result shows exactly
        the conditions block the API function returned for the same request."""
        args = {"bike_preset": "gsxr1000_k5"}
        api_res = LocalBackend().simulate_quick(dict(args))
        is_error, payload = _call("simulate_quarter_mile", args)
        self.assertFalse(is_error, payload)
        self.assertEqual(payload.get("environment"), api_res.get("environment"))
        is_error, top = _call("simulate_top_speed", args)
        self.assertFalse(is_error, top)
        self.assertEqual(top.get("environment"), api_res.get("environment"))
        is_error, gearing = _call(
            "gearing_impact",
            {**args, "front_a": 17, "rear_a": 42, "front_b": 17, "rear_b": 45},
        )
        self.assertFalse(is_error, gearing)
        self.assertEqual(gearing.get("environment"), api_res.get("environment"))
        # the conditions are reported once, not repeated inside each setup
        self.assertNotIn("environment", gearing["a"])
        self.assertNotIn("environment", gearing["b"])


# ─── Malformed input ──────────────────────────────────────────────────────


class TestErrorHandling(unittest.TestCase):
    def test_invalid_json_line_gets_a_parse_error(self):
        responses, _ = _drive(["{not json at all"])
        self.assertEqual(responses[0]["error"]["code"], mcp_server.PARSE_ERROR)
        self.assertIsNone(responses[0]["id"])

    def test_blank_lines_are_ignored(self):
        responses, _ = _drive(
            ["", "   ", {"jsonrpc": "2.0", "id": 3, "method": "ping"}]
        )
        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0]["id"], 3)

    def test_unknown_method_is_method_not_found(self):
        responses, _ = _drive([{"jsonrpc": "2.0", "id": 4, "method": "resources/list"}])
        self.assertEqual(responses[0]["error"]["code"], mcp_server.METHOD_NOT_FOUND)

    def test_missing_method_is_invalid_request(self):
        responses, _ = _drive([{"jsonrpc": "2.0", "id": 5}])
        self.assertEqual(responses[0]["error"]["code"], mcp_server.INVALID_REQUEST)

    def test_non_object_params_is_invalid_params(self):
        responses, _ = _drive(
            [{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": [1, 2]}]
        )
        self.assertEqual(responses[0]["error"]["code"], mcp_server.INVALID_PARAMS)

    def test_unknown_tool_is_an_iserror_result_not_a_transport_error(self):
        """MCP spec: tool failures ride back in the result so the model can
        recover; only protocol faults use the JSON-RPC error channel."""
        responses, _ = _drive(
            [
                {
                    "jsonrpc": "2.0",
                    "id": 8,
                    "method": "tools/call",
                    "params": {"name": "definitely_not_a_tool", "arguments": {}},
                }
            ]
        )
        self.assertNotIn("error", responses[0])
        self.assertTrue(responses[0]["result"]["isError"])
        self.assertIn("Unknown tool", responses[0]["result"]["content"][0]["text"])

    def test_missing_required_argument_is_reported_by_name(self):
        is_error, text = _call("get_bike", {})
        self.assertTrue(is_error)
        self.assertIn("bike_id", text)

    def test_non_integer_id_is_rejected_cleanly(self):
        is_error, text = _call("get_bike", {"bike_id": "not-a-number"})
        self.assertTrue(is_error)
        self.assertIn("integer", text)

    def test_batch_requests_are_answered_in_order(self):
        stdin = io.StringIO(
            json.dumps(
                [
                    {"jsonrpc": "2.0", "id": 1, "method": "ping"},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                ]
            )
            + "\n"
        )
        stdout = io.StringIO()
        serve(MCPServer(backend=LocalBackend()), stdin, stdout)
        responses = [json.loads(ln) for ln in stdout.getvalue().splitlines() if ln]
        self.assertEqual([r["id"] for r in responses], [1, 2])


# ─── Wiring ───────────────────────────────────────────────────────────────


class TestBackendSelection(unittest.TestCase):
    def test_env_flag_selects_the_local_backend(self):
        prior = os.environ.get("MOTOQUANT_MCP_LOCAL")
        try:
            os.environ["MOTOQUANT_MCP_LOCAL"] = "1"
            self.assertIsInstance(mcp_server.make_backend(), LocalBackend)
            os.environ["MOTOQUANT_MCP_LOCAL"] = "0"
            self.assertIsInstance(mcp_server.make_backend(), HttpBackend)
        finally:
            if prior is None:
                os.environ.pop("MOTOQUANT_MCP_LOCAL", None)
            else:
                os.environ["MOTOQUANT_MCP_LOCAL"] = prior

    def test_default_http_backend_points_at_the_hosted_api(self):
        prior_local = os.environ.pop("MOTOQUANT_MCP_LOCAL", None)
        prior_url = os.environ.pop("MOTOQUANT_API_URL", None)
        try:
            backend = mcp_server.make_backend()
            self.assertIsInstance(backend, HttpBackend)
            self.assertEqual(backend.base_url, "https://api.motoquant.in")
        finally:
            if prior_local is not None:
                os.environ["MOTOQUANT_MCP_LOCAL"] = prior_local
            if prior_url is not None:
                os.environ["MOTOQUANT_API_URL"] = prior_url

    def test_selftest_entrypoint_passes_without_network(self):
        prior = os.environ.get("MOTOQUANT_MCP_LOCAL")
        try:
            os.environ["MOTOQUANT_MCP_LOCAL"] = "1"
            self.assertEqual(mcp_server.main(["--selftest"]), 0)
        finally:
            if prior is None:
                os.environ.pop("MOTOQUANT_MCP_LOCAL", None)
            else:
                os.environ["MOTOQUANT_MCP_LOCAL"] = prior


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
