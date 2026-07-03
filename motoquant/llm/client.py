"""
LLMClient -- thin provider-agnostic wrapper around chat-completion APIs.

Supported providers (selected via the LLM_PROVIDER env var):
  - "groq"       -- Groq Llama 3.3 70B (free, fastest; OpenAI-compatible) [default]
  - "gemini"     -- Google Gemini (free tier, but free-tier eligibility for
                    individual model IDs varies by project / region)
  - "anthropic"  -- Anthropic Claude (paid, native SDK)
  - "deepseek"   -- DeepSeek API (cheap; OpenAI-compatible)
  - "openrouter" -- OpenRouter (free DeepSeek/Llama via aggregator)

All non-Anthropic providers go through the OpenAI Python SDK pointed at
the provider's OpenAI-compatible endpoint, so the call shape is identical.

Each provider reads its own API key env var:
  - GEMINI_API_KEY     -- get from https://aistudio.google.com/apikey
  - ANTHROPIC_API_KEY  -- get from https://console.anthropic.com/
  - DEEPSEEK_API_KEY   -- get from https://platform.deepseek.com/api_keys
  - GROQ_API_KEY       -- get from https://console.groq.com/keys
  - OPENROUTER_API_KEY -- get from https://openrouter.ai/keys

For tests, pass `_call_override`:
    def fake(kind, kwargs):
        return {"bike_name": "K5"}
    client = LLMClient(_call_override=fake)
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# ─── Provider table ───────────────────────────────────────────────────────
_PROVIDERS: dict[str, dict[str, str | None]] = {
    "gemini": {
        # Free-tier eligibility for specific model IDs varies by project /
        # region (Google sometimes returns "limit: 0" on a model the docs
        # claim is free). Override via GEMINI_MODEL env var if needed —
        # known-good free options: gemini-2.5-flash, gemini-2.5-flash-lite,
        # gemini-2.0-flash, gemini-2.0-flash-lite.
        "model": "gemini-2.5-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
    },
    "anthropic": {
        "model": "claude-sonnet-4-6",
        "base_url": None,
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "groq": {
        # Llama 3.3 70B Versatile — Groq's flagship free model.
        # Free tier: 30 RPM, 14,400 RPD on most accounts (much more
        # generous than Gemini's per-model variability). Override via
        # GROQ_MODEL env var to use llama-3.1-70b / llama-3.1-8b-instant /
        # mixtral-8x7b / etc. without redeploying.
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
    },
    "openrouter": {
        "model": "deepseek/deepseek-chat-v3:free",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

DEFAULT_PROVIDER = "groq"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT_S = 30.0


class LLMNotConfiguredError(RuntimeError):
    """Raised when the LLM client is needed but cannot be built."""


class LLMRateLimitError(RuntimeError):
    """Raised when the provider returns a 429 / quota-exceeded error.

    Distinct from generic errors so the chat pipeline can return a typed
    'rate_limit' marker to the UI instead of bubbling a stack trace.
    """


@dataclass
class LLMResponse:
    tool_input: dict[str, Any] | None = None
    raw_text: str | None = None
    stop_reason: str | None = None


@dataclass
class ToolCall:
    """One tool invocation requested by the model in an agent step."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AgentStep:
    """Result of one :meth:`LLMClient.call_tools` round.

    ``tool_calls`` non-empty → execute them and append tool-result messages;
    empty → ``text`` is the model's final answer for this turn.
    """

    text: str | None = None
    tool_calls: list[ToolCall] = None  # type: ignore[assignment]
    stop_reason: str | None = None

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


class LLMClient:
    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        _call_override: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self._provider = (
            provider or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER
        ).lower()
        if self._provider not in _PROVIDERS:
            raise LLMNotConfiguredError(
                f"Unknown LLM_PROVIDER {self._provider!r}. "
                f"Supported: {sorted(_PROVIDERS.keys())}"
            )
        cfg = _PROVIDERS[self._provider]
        self._api_key = api_key or os.environ.get(cfg["api_key_env"])
        if not self._api_key and self._provider == "anthropic":
            self._api_key = os.environ.get("ANTHROPIC_API_KEY")
        # Allow per-provider model override via env var (e.g. GEMINI_MODEL,
        # ANTHROPIC_MODEL) — handy for swapping on Railway without redeploy.
        env_model = None
        model_env_var = cfg.get("model_env")
        if model_env_var:
            env_model = os.environ.get(model_env_var)
        self._model = model or env_model or cfg["model"]
        self._base_url = cfg["base_url"]
        self._max_tokens = max_tokens
        self._timeout_s = timeout_s
        self._call_override = _call_override
        self._sdk_client = None

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def is_configured(self) -> bool:
        if self._call_override is not None:
            return True
        if not self._api_key:
            return False
        try:
            if self._provider == "anthropic":
                import anthropic  # noqa: F401
            else:
                import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def _get_sdk(self):
        if self._sdk_client is not None:
            return self._sdk_client
        if not self._api_key:
            cfg = _PROVIDERS[self._provider]
            raise LLMNotConfiguredError(
                f"{cfg['api_key_env']} env var not set. "
                f"Provider={self._provider!r}. Set {cfg['api_key_env']}=... "
                f"or set LLM_PROVIDER to a different provider."
            )
        if self._provider == "anthropic":
            try:
                import anthropic
            except ImportError as e:
                raise LLMNotConfiguredError(
                    "anthropic package not installed: pip install anthropic"
                ) from e
            self._sdk_client = anthropic.Anthropic(
                api_key=self._api_key, timeout=self._timeout_s
            )
        else:
            try:
                import openai
            except ImportError as e:
                raise LLMNotConfiguredError(
                    "openai package not installed: pip install openai"
                ) from e
            self._sdk_client = openai.OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout_s,
            )
        return self._sdk_client

    @staticmethod
    def _is_rate_limit(exc: Exception) -> bool:
        """Detect a provider 429 / quota-exceeded error in an SDK-agnostic way.

        Both the anthropic and openai SDKs raise a ``RateLimitError`` (status
        429); other OpenAI-compatible providers surface the same class through
        the openai SDK. We match on HTTP status (most reliable) and fall back to
        the exception class name so a minor SDK refactor cannot silently demote
        a 429 to a generic error.
        """
        for attr in ("status_code", "status"):
            if getattr(exc, attr, None) == 429:
                return True
        resp = getattr(exc, "response", None)
        if getattr(resp, "status_code", None) == 429:
            return True
        return type(exc).__name__ == "RateLimitError"

    def _sdk_create(self, create_fn, **kwargs):
        """Invoke an SDK ``*.create(**kwargs)`` call, translating a provider 429
        into :class:`LLMRateLimitError` so the chat pipeline can return a typed
        'rate_limit' marker instead of a bare stack trace."""
        try:
            return create_fn(**kwargs)
        except LLMRateLimitError:
            raise
        except Exception as e:  # noqa: BLE001 -- re-raised below
            if self._is_rate_limit(e):
                raise LLMRateLimitError(
                    f"{self._provider} rate limit / quota exceeded: {e}"
                ) from e
            raise

    def call_tool(self, system, user, tool_name, tool_schema):
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
            raise TypeError("_call_override for 'tool' must return dict or LLMResponse")

        client = self._get_sdk()

        if self._provider == "anthropic":
            tools = [
                {
                    "name": tool_name,
                    "description": (
                        f"Submit the structured parse result. "
                        f"Always invoke {tool_name}."
                    ),
                    "input_schema": tool_schema,
                }
            ]
            msg = self._sdk_create(
                client.messages.create,
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                tools=tools,
                tool_choice={"type": "tool", "name": tool_name},
                messages=[{"role": "user", "content": user}],
            )
            for block in msg.content:
                if (
                    getattr(block, "type", None) == "tool_use"
                    and block.name == tool_name
                ):
                    return LLMResponse(
                        tool_input=dict(block.input), stop_reason=msg.stop_reason
                    )
            raise RuntimeError(
                f"Model did not invoke {tool_name}; stop_reason={msg.stop_reason}"
            )

        # OpenAI-compatible providers
        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": (
                        f"Submit the structured parse result. "
                        f"Always invoke {tool_name}."
                    ),
                    "parameters": tool_schema,
                },
            }
        ]
        msg = self._sdk_create(
            client.chat.completions.create,
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": tool_name}},
        )
        choice = msg.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", None) or []
        for tc in tool_calls:
            fn = getattr(tc, "function", None)
            if fn is None or fn.name != tool_name:
                continue
            try:
                args = json.loads(fn.arguments)
            except (TypeError, ValueError) as e:
                raise RuntimeError(
                    f"Provider returned malformed JSON for {tool_name}: {fn.arguments!r}"
                ) from e
            return LLMResponse(tool_input=args, stop_reason=choice.finish_reason)
        raise RuntimeError(
            f"Model did not invoke {tool_name}; finish_reason={choice.finish_reason}"
        )

    # ── Multi-turn agentic tool use ───────────────────────────────────
    #
    # Neutral message format (provider-agnostic, used by llm/agent.py):
    #   {"role": "user",      "content": str}
    #   {"role": "assistant", "content": str | None,
    #    "tool_calls": [{"id": str, "name": str, "arguments": dict}]}   # optional
    #   {"role": "tool",      "tool_call_id": str, "name": str, "content": str}
    #
    # Tools are passed as [{"name", "description", "input_schema"}] and the
    # model is FREE to pick any tool or answer in plain text (tool_choice
    # auto) — unlike call_tool, which forces a single named tool.

    @staticmethod
    def _neutral_to_anthropic(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert neutral agent messages to Anthropic messages format."""
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "user":
                out.append({"role": "user", "content": m.get("content") or ""})
            elif role == "assistant":
                blocks: list[dict[str, Any]] = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls") or []:
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc.get("arguments") or {},
                        }
                    )
                out.append({"role": "assistant", "content": blocks or ""})
            elif role == "tool":
                # Anthropic wants tool results inside a user turn. Merge
                # consecutive tool results into one user message.
                block = {
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id") or "",
                    "content": m.get("content") or "",
                }
                if (
                    out
                    and out[-1]["role"] == "user"
                    and isinstance(out[-1]["content"], list)
                    and out[-1]["content"]
                    and out[-1]["content"][0].get("type") == "tool_result"
                ):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
        return out

    @staticmethod
    def _neutral_to_openai(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert neutral agent messages to OpenAI chat format."""
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role")
            if role == "user":
                out.append({"role": "user", "content": m.get("content") or ""})
            elif role == "assistant":
                entry: dict[str, Any] = {
                    "role": "assistant",
                    "content": m.get("content"),
                }
                tcs = m.get("tool_calls") or []
                if tcs:
                    entry["tool_calls"] = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc.get("arguments") or {}),
                            },
                        }
                        for tc in tcs
                    ]
                out.append(entry)
            elif role == "tool":
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": m.get("tool_call_id") or "",
                        "content": m.get("content") or "",
                    }
                )
        return out

    def call_tools(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        max_tokens: int | None = None,
    ) -> AgentStep:
        """One agent step: model sees the transcript + tools, freely answers
        or requests tool calls (``tool_choice`` auto on every provider).

        ``messages`` uses the neutral format documented above. ``tools`` is
        [{"name", "description", "input_schema"}].
        """
        if self._call_override is not None:
            result = self._call_override(
                "tools",
                {"system": system, "messages": messages, "tools": tools},
            )
            if isinstance(result, AgentStep):
                return result
            if isinstance(result, str):
                return AgentStep(text=result, stop_reason="end_turn")
            if isinstance(result, dict):
                return AgentStep(
                    text=result.get("text"),
                    tool_calls=[
                        ToolCall(
                            id=tc.get("id") or f"call_{i}",
                            name=tc["name"],
                            arguments=tc.get("arguments") or {},
                        )
                        for i, tc in enumerate(result.get("tool_calls") or [])
                    ],
                    stop_reason=result.get("stop_reason"),
                )
            raise TypeError(
                "_call_override for 'tools' must return AgentStep, str or dict"
            )

        client = self._get_sdk()
        max_tok = max_tokens or self._max_tokens

        if self._provider == "anthropic":
            a_kwargs: dict[str, Any] = {}
            if tools:
                # Providers reject an empty tools array — omit entirely when
                # the caller wants a plain final-answer turn.
                a_kwargs["tools"] = [
                    {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "input_schema": t["input_schema"],
                    }
                    for t in tools
                ]
            msg = self._sdk_create(
                client.messages.create,
                model=self._model,
                max_tokens=max_tok,
                system=system,
                messages=self._neutral_to_anthropic(messages),
                **a_kwargs,
            )
            text_chunks: list[str] = []
            calls: list[ToolCall] = []
            for block in msg.content:
                btype = getattr(block, "type", None)
                if btype == "text":
                    text_chunks.append(block.text)
                elif btype == "tool_use":
                    calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=dict(block.input or {}),
                        )
                    )
            return AgentStep(
                text="".join(text_chunks).strip() or None,
                tool_calls=calls,
                stop_reason=msg.stop_reason,
            )

        # OpenAI-compatible providers (Groq / Gemini / DeepSeek / OpenRouter)
        o_kwargs: dict[str, Any] = {}
        if tools:
            o_kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ]
            o_kwargs["tool_choice"] = "auto"
        o_messages = [{"role": "system", "content": system}]
        o_messages.extend(self._neutral_to_openai(messages))
        msg = self._sdk_create(
            client.chat.completions.create,
            model=self._model,
            max_tokens=max_tok,
            messages=o_messages,
            **o_kwargs,
        )
        choice = msg.choices[0]
        calls = []
        for tc in getattr(choice.message, "tool_calls", None) or []:
            fn = getattr(tc, "function", None)
            if fn is None:
                continue
            try:
                args = json.loads(fn.arguments) if fn.arguments else {}
            except (TypeError, ValueError):
                # Malformed JSON args: surface as an empty call so the agent
                # loop can report a tool error instead of crashing the turn.
                args = {"__malformed_json__": fn.arguments}
            calls.append(ToolCall(id=tc.id, name=fn.name, arguments=args))
        return AgentStep(
            text=(choice.message.content or "").strip() or None,
            tool_calls=calls,
            stop_reason=choice.finish_reason,
        )

    def call_text(self, system, user):
        if self._call_override is not None:
            result = self._call_override("text", {"system": system, "user": user})
            if isinstance(result, str):
                return result
            raise TypeError(
                f"_call_override for 'text' must return str, got {type(result).__name__}"
            )

        client = self._get_sdk()

        if self._provider == "anthropic":
            msg = self._sdk_create(
                client.messages.create,
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            chunks = []
            for block in msg.content:
                if getattr(block, "type", None) == "text":
                    chunks.append(block.text)
            return "".join(chunks).strip()

        msg = self._sdk_create(
            client.chat.completions.create,
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (msg.choices[0].message.content or "").strip()


_DEFAULT_CLIENT: LLMClient | None = None


def get_default_client() -> LLMClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = LLMClient()
    return _DEFAULT_CLIENT


def reset_default_client() -> None:
    global _DEFAULT_CLIENT
    _DEFAULT_CLIENT = None


DEFAULT_MODEL = _PROVIDERS[DEFAULT_PROVIDER]["model"]
