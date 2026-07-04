"""
Regression tests pinning the Groq/Llama 'tool_use_failed' salvage path.

Sentry MOTOQUANT-API-1: Groq's llama-3.3-70b sometimes emits a tool call as
its raw '<function=name{json}</function>' text instead of a structured
tool_calls block. Groq rejects that with HTTP 400 code=tool_use_failed but
preserves the intended call verbatim in the error body's 'failed_generation'.
motoquant/llm/client.py salvages that call and returns it as a real ToolCall
(or retries when the payload is unparseable). These tests exercise the REAL
functions so the fix cannot silently regress.

Run with:  python3 -m pytest tests/test_chat_tool_salvage.py -q
"""

from __future__ import annotations

import unittest

from motoquant.llm.client import (
    _TOOL_FLAKE_RETRIES,
    LLMClient,
    _failed_generation_from_error,
    _parse_failed_generation,
)

# The exact string preserved in Groq's failed_generation for the Sentry issue.
_PROD_FAILED_GEN = '<function=search_bikes{"query": "zx14r"}</function>'


# ── _parse_failed_generation ────────────────────────────────────────────────
class TestParseFailedGeneration(unittest.TestCase):
    def test_exact_prod_string(self):
        """(a) The verbatim Sentry payload parses to one call."""
        self.assertEqual(
            _parse_failed_generation(_PROD_FAILED_GEN),
            [("search_bikes", {"query": "zx14r"})],
        )

    def test_missing_closing_tag_is_lenient(self):
        """(b) The regex tolerates a missing </function> closing tag."""
        self.assertEqual(
            _parse_failed_generation('<function=search_bikes{"query": "zx14r"}'),
            [("search_bikes", {"query": "zx14r"})],
        )

    def test_two_chained_calls(self):
        """(c) Two concatenated calls parse to two tuples in order."""
        chained = (
            '<function=search_bikes{"query": "zx14r"}</function>'
            '<function=top_speed{"bike": "busa"}</function>'
        )
        self.assertEqual(
            _parse_failed_generation(chained),
            [("search_bikes", {"query": "zx14r"}), ("top_speed", {"bike": "busa"})],
        )

    def test_no_args_empty_dict(self):
        """(d) A no-arg call yields an empty args dict.

        The code does `json.loads(args_raw) if args_raw else {}`, so all three
        real-world no-arg spellings collapse to ({}).
        """
        for spelling in (
            "<function=live_stats></function>",  # no args group at all
            "<function=live_stats>{}</function>",  # explicit empty JSON
            "<function=live_stats{}</function>",  # no '>' after name
        ):
            with self.subTest(spelling=spelling):
                self.assertEqual(
                    _parse_failed_generation(spelling), [("live_stats", {})]
                )

    def test_unparseable_no_function_tag_returns_empty(self):
        """(f) A string with no <function=...> tag returns []."""
        self.assertEqual(
            _parse_failed_generation("total garbage no function tag"), []
        )

    def test_half_formed_json_returns_empty(self):
        """Invalid JSON args bail to [] (safer to retry than to guess)."""
        self.assertEqual(
            _parse_failed_generation("<function=search_bikes{not valid json}</function>"),
            [],
        )

    def test_empty_input_returns_empty(self):
        self.assertEqual(_parse_failed_generation(""), [])


# ── _failed_generation_from_error ───────────────────────────────────────────
class _FakeGroq400(Exception):
    """Mimics the openai-SDK BadRequestError shape: an error body dict on .body,
    with str(exc) mirroring that body (as the real SDK renders it), so the
    string-fallback branch behaves as it would in prod."""

    def __init__(self, body):
        super().__init__(f"Error code: 400 - {body!r}")
        self.body = body


class TestFailedGenerationFromError(unittest.TestCase):
    def test_body_error_nested(self):
        """(e) .body = {'error': {code, failed_generation}} → extracts the string."""
        exc = _FakeGroq400(
            {
                "error": {
                    "message": "Failed to call a function.",
                    "type": "invalid_request_error",
                    "code": "tool_use_failed",
                    "failed_generation": _PROD_FAILED_GEN,
                }
            }
        )
        self.assertEqual(_failed_generation_from_error(exc), _PROD_FAILED_GEN)

    def test_body_error_flat(self):
        """(e) .body carrying the error fields directly (no 'error' nesting)."""
        exc = _FakeGroq400(
            {"code": "tool_use_failed", "failed_generation": _PROD_FAILED_GEN}
        )
        self.assertEqual(_failed_generation_from_error(exc), _PROD_FAILED_GEN)

    def test_string_in_message_fallback(self):
        """(e) The str(exc) fallback for SDKs that only surface the payload as text."""
        text = (
            "Error code: 400 - {'error': {'message': 'Failed to call a function.', "
            "'type': 'invalid_request_error', 'code': 'tool_use_failed', "
            "'failed_generation': '" + _PROD_FAILED_GEN + "'}}"
        )
        self.assertEqual(_failed_generation_from_error(Exception(text)), _PROD_FAILED_GEN)

    def test_unrelated_exception_returns_none(self):
        """(e) A non-tool_use_failed error is not the flake → returns None → re-raised."""
        self.assertIsNone(_failed_generation_from_error(ValueError("something else")))

    def test_body_wrong_code_falls_through_to_none(self):
        """A 400 with a different code is not salvageable."""
        exc = _FakeGroq400({"error": {"code": "rate_limit_exceeded"}})
        self.assertIsNone(_failed_generation_from_error(exc))


# ── End-to-end salvage/retry inside call_tools (real code path) ──────────────
#
# The _call_override('tools') seam short-circuits BEFORE the SDK call, so it
# cannot exercise the salvage block. Instead we inject a fake SDK client via
# LLMClient._sdk_client (which _get_sdk returns verbatim when set), so the real
# OpenAI-compatible branch — including the try/except salvage/retry loop — runs.
class _FakeCompletions:
    def __init__(self, behaviors):
        # behaviors: list of callables invoked in order per create() call.
        self._behaviors = behaviors
        self.calls = 0

    def create(self, **kwargs):
        idx = min(self.calls, len(self._behaviors) - 1)
        self.calls += 1
        return self._behaviors[idx]()


class _FakeChat:
    def __init__(self, completions):
        self.completions = completions


class _FakeSDK:
    def __init__(self, chat):
        self.chat = chat


def _make_client(behaviors):
    comp = _FakeCompletions(behaviors)
    client = LLMClient(provider="groq", api_key="x")
    client._sdk_client = _FakeSDK(_FakeChat(comp))
    return client, comp


def _raise_tool_use_failed(failed_gen):
    def _raise():
        raise _FakeGroq400(
            {"error": {"code": "tool_use_failed", "failed_generation": failed_gen}}
        )

    return _raise


def _raise_other():
    raise RuntimeError("boom — a real 500, not the flake")


# Minimal duck-typed mirror of an openai ChatCompletion success response.
class _Fn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _RespToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = _Fn(name, arguments)


class _RespMessage:
    def __init__(self, tool_calls, content=None):
        self.tool_calls = tool_calls
        self.content = content


class _RespChoice:
    def __init__(self, message, finish_reason):
        self.message = message
        self.finish_reason = finish_reason


class _Resp:
    def __init__(self, choices):
        self.choices = choices


def _success_with_tool_call():
    return _Resp(
        [
            _RespChoice(
                _RespMessage(
                    [_RespToolCall("call_real", "search_bikes", '{"query": "zx14r"}')]
                ),
                finish_reason="tool_calls",
            )
        ]
    )


_TOOLS = [{"name": "search_bikes", "description": "", "input_schema": {"type": "object"}}]
_MESSAGES = [{"role": "user", "content": "how fast is the zx14r"}]


class TestCallToolsSalvage(unittest.TestCase):
    def test_parseable_flake_is_salvaged_no_400_propagates(self):
        """First (only) attempt 400s with a parseable payload → salvaged call,
        no exception propagates, and no retry is needed."""
        client, comp = _make_client([_raise_tool_use_failed(_PROD_FAILED_GEN)])
        step = client.call_tools(system="s", messages=_MESSAGES, tools=_TOOLS)
        self.assertEqual(step.stop_reason, "tool_use")
        self.assertEqual(len(step.tool_calls), 1)
        tc = step.tool_calls[0]
        self.assertEqual(tc.name, "search_bikes")
        self.assertEqual(tc.arguments, {"query": "zx14r"})
        self.assertEqual(tc.id, "salvaged_0")
        # Salvage returns immediately — the model is not re-hit.
        self.assertEqual(comp.calls, 1)

    def test_unsalvageable_flake_retries_then_succeeds(self):
        """An unparseable 400 triggers a retry; the retry's real tool_calls
        block is used and no 400 propagates."""
        client, comp = _make_client(
            [
                _raise_tool_use_failed("total garbage no function tag"),
                _success_with_tool_call,
            ]
        )
        step = client.call_tools(system="s", messages=_MESSAGES, tools=_TOOLS)
        self.assertEqual(step.stop_reason, "tool_calls")
        self.assertEqual(len(step.tool_calls), 1)
        self.assertEqual(step.tool_calls[0].id, "call_real")
        self.assertEqual(step.tool_calls[0].arguments, {"query": "zx14r"})
        self.assertEqual(comp.calls, 2)

    def test_non_flake_error_propagates(self):
        """A 400 that is NOT tool_use_failed is a real error and must propagate."""
        client, comp = _make_client([_raise_other])
        with self.assertRaises(RuntimeError):
            client.call_tools(system="s", messages=_MESSAGES, tools=_TOOLS)

    def test_retries_exhaust_then_raise(self):
        """When every attempt is an unsalvageable flake, the last one raises."""
        behaviors = [
            _raise_tool_use_failed("total garbage no function tag")
        ] * (_TOOL_FLAKE_RETRIES + 1)
        client, comp = _make_client(behaviors)
        with self.assertRaises(_FakeGroq400):
            client.call_tools(system="s", messages=_MESSAGES, tools=_TOOLS)
        # Initial attempt + _TOOL_FLAKE_RETRIES retries.
        self.assertEqual(comp.calls, _TOOL_FLAKE_RETRIES + 1)


if __name__ == "__main__":
    unittest.main()
