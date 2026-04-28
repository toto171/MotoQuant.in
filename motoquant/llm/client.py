"""
LLMClient -- thin wrapper around the Anthropic Messages API.

Why a wrapper:
  - Centralizes model name + retry logic + timeout in one place
  - Lets tests inject mocked responses without touching the anthropic SDK
  - Lazy-imports anthropic so the module loads even when the package is
    not installed (only fails at call time with a typed error)
  - Gracefully degrades when ANTHROPIC_API_KEY is missing

Usage
-----
    from motoquant.llm.client import LLMClient

    client = LLMClient()  # reads ANTHROPIC_API_KEY from env
    resp = client.call_tool(
        system="You parse queries.",
        user="optimize my K5",
        tool_name="submit_query",
        tool_schema={...},
    )
    parsed_dict = resp.tool_input

For tests, pass `_call_override`:
    def fake(kind, kwargs):
        return {"bike_name": "K5", "optimization_goal": "minimize_et"}
    client = LLMClient(_call_override=fake)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

# Pinned model -- bump this in one place when upgrading.
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT_S = 30.0


class LLMNotConfiguredError(RuntimeError):
    """Raised when the Anthropic client is needed but cannot be built.

    Reasons:
      - ANTHROPIC_API_KEY env var is unset and no api_key passed
      - `anthropic` package is not installed
    """


@dataclass
class LLMResponse:
    """Normalized response from a tool-use or text call.

    For tool calls: tool_input is the parsed JSON the model produced.
    For text calls: raw_text is the concatenated text content.
    """

    tool_input: dict[str, Any] | None = None
    raw_text: str | None = None
    stop_reason: str | None = None


class LLMClient:
    """Thin wrapper around the Anthropic Messages API.

    Two main usage modes:
      - call_tool(...) -> LLMResponse with tool_input populated
        Use for structured output (query parsing, build extraction).
      - call_text(...) -> str
        Plain text response. Use for summarization.

    For tests:
      LLMClient(_call_override=lambda kind, kwargs: ...) bypasses the SDK
      entirely. `kind` is "tool" or "text"; `kwargs` are the call args.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        _call_override: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._model = model
        self._max_tokens = max_tokens
        self._timeout_s = timeout_s
        self._call_override = _call_override
        self._sdk_client = None  # lazy

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        """True if a real API call would succeed (key set, SDK importable)."""
        if self._call_override is not None:
            return True
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def _get_sdk(self):
        """Lazy-init the anthropic.Anthropic SDK client."""
        if self._sdk_client is not None:
            return self._sdk_client
        if not self._api_key:
            raise LLMNotConfiguredError(
                "ANTHROPIC_API_KEY env var not set. "
                "Set it (export ANTHROPIC_API_KEY=sk-ant-...) or pass "
                "api_key= to LLMClient(). Get a key at "
                "https://console.anthropic.com/"
            )
        try:
            import anthropic
        except ImportError as e:
            raise LLMNotConfiguredError(
                "anthropic package not installed. Run: "
                "pip install anthropic --break-system-packages"
            ) from e
        self._sdk_client = anthropic.Anthropic(
            api_key=self._api_key, timeout=self._timeout_s
        )
        return self._sdk_client

    # ── public methods ────────────────────────────────────────────────────

    def call_tool(
        self,
        system: str,
        user: str,
        tool_name: str,
        tool_schema: dict[str, Any],
    ) -> LLMResponse:
        """Force the model to invoke `tool_name` with input matching `tool_schema`.

        Returns LLMResponse with tool_input populated.
        Raises RuntimeError if the model refuses to invoke the tool.
        """
        if self._call_override is not None:
            result = self._call_override(
                "tool",
                {
                    "system": system,
                    "user": user,
                    "tool_name": tool_name,
                    "tool_schema": tool_schema,
                },
            )
            if isinstance(result, LLMResponse):
                return result
            if isinstance(result, dict):
                return LLMResponse(tool_input=result, stop_reason="tool_use")
            raise TypeError(
                f"_call_override for 'tool' must return dict or LLMResponse, "
                f"got {type(result).__name__}"
            )

        client = self._get_sdk()
        tools = [
            {
                "name": tool_name,
                "description": (
                    f"Submit the structured parse result. "
                    f"Always invoke {tool_name} -- never reply in plain text."
                ),
                "input_schema": tool_schema,
            }
        ]
        msg = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            tools=tools,
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
        )
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
                return LLMResponse(
                    tool_input=dict(block.input),
                    stop_reason=msg.stop_reason,
                )
        raise RuntimeError(
            f"Model did not invoke {tool_name}; stop_reason={msg.stop_reason}"
        )

    def call_text(self, system: str, user: str) -> str:
        """Plain-text completion. Returns the concatenated text content."""
        if self._call_override is not None:
            result = self._call_override("text", {"system": system, "user": user})
            if isinstance(result, str):
                return result
            raise TypeError(
                f"_call_override for 'text' must return str, "
                f"got {type(result).__name__}"
            )

        client = self._get_sdk()
        msg = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        chunks: list[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                chunks.append(block.text)
        return "".join(chunks).strip()


# ── module singleton ──────────────────────────────────────────────────────

_DEFAULT_CLIENT: LLMClient | None = None


def get_default_client() -> LLMClient:
    """Singleton accessor for the default LLMClient.

    Tests should NOT use this -- pass an explicit
    LLMClient(_call_override=...) into parse_query / summarize_result instead.
    """
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = LLMClient()
    return _DEFAULT_CLIENT


def reset_default_client() -> None:
    """For tests / dev -- drop the singleton so the next call rebuilds it."""
    global _DEFAULT_CLIENT
    _DEFAULT_CLIENT = None
