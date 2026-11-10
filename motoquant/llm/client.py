"""
LLMClient: the MotoQuant chat layer's only door to a language model.

Claude only. Two assistants, picked per request:

  - "mechanic" (default): claude-sonnet-5-5, effort "medium"
  - "doctor":             claude-opus-5-5,   effort "medium"

Keys
----
The server's own key comes only from the ``ANTHROPIC_API_KEY`` environment
variable. A visitor may bring their own key (the ``X-Anthropic-Key`` header);
the API builds a client for that one request with
``LLMClient(assistant, api_key=key, own_key=True)``. A visitor client never
reads the environment, never falls back to the server key and is never
cached on a module singleton. Every error string this module builds goes
through :func:`redact_secrets`, so a key cannot leak through an error.

Request shape (every call, agent or classic)
--------------------------------------------
``client.beta.messages.create`` with the server-side fallback beta,
``fallbacks="default"``, adaptive thinking, ``output_config.effort``, a
system prompt given as blocks (a frozen block carrying ``cache_control``
plus a small dynamic block), and top-level ``cache_control``. Never sent:
a forced ``tool_choice`` (``any``/``tool``), ``budget_tokens``, disabled
thinking, sampling parameters or an assistant prefill. Forcing a tool is
rejected by both models, so the classic parser uses structured outputs
(``output_config.format``) instead.

For tests, pass ``_call_override``:
    def fake(kind, kwargs):          # kind: "tool" | "tools" | "text"
        return {"bike_name": "K5"}
    client = LLMClient(_call_override=fake)
or inject a fake SDK object as ``client._sdk_client`` to assert on the exact
keyword arguments sent to ``beta.messages.create``.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ─── Assistants ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AssistantSpec:
    id: str
    label: str
    model: str
    model_label: str
    effort: str
    # Units charged against the per-IP daily cap when the server key answers.
    cap_units: int


ASSISTANTS: dict[str, AssistantSpec] = {
    "doctor": AssistantSpec(
        id="doctor",
        label="The doctor",
        model="claude-opus-5-5",
        model_label="Claude Opus 5.5",
        effort="medium",
        cap_units=2,
    ),
    "mechanic": AssistantSpec(
        id="mechanic",
        label="The mechanic",
        model="claude-sonnet-5-5",
        model_label="Claude Sonnet 5.5",
        effort="medium",
        cap_units=1,
    ),
}
DEFAULT_ASSISTANT = "mechanic"
ASSISTANT_ORDER = ("doctor", "mechanic")  # dropdown order: 1. doctor, 2. mechanic

SERVER_KEY_ENV = "ANTHROPIC_API_KEY"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
DEFAULT_MAX_TOKENS = 16_000
# Thinking plus a 16k-token answer can take well over the old 30 s. The SDK
# still retries connection errors, 429 and 5xx (max_retries=2).
DEFAULT_TIMEOUT_S = 180.0
DEFAULT_MODEL = ASSISTANTS[DEFAULT_ASSISTANT].model

# ─── Key handling ─────────────────────────────────────────────────────────

_KEY_PREFIX = "sk-ant-"
_KEY_MIN_LEN = 20
_KEY_MAX_LEN = 300
# Anything that starts like an Anthropic key, up to the next whitespace,
# quote or bracket. Used to scrub every error string and Sentry event.
_SECRET_RE = re.compile(r"sk-ant-[^\s\"'<>\\]*")
REDACTED = "[redacted]"


def looks_like_anthropic_key(value: Any) -> bool:
    """True for a value shaped like an Anthropic API key: the ``sk-ant-``
    prefix, 20-300 printable ASCII characters and no whitespace."""
    if not isinstance(value, str):
        return False
    if not (_KEY_MIN_LEN <= len(value) <= _KEY_MAX_LEN):
        return False
    if not value.startswith(_KEY_PREFIX):
        return False
    return all(33 <= ord(c) <= 126 for c in value)


def redact_secrets(text: Any) -> str:
    """Replace every ``sk-ant-...`` substring with ``[redacted]``."""
    if text is None:
        return ""
    return _SECRET_RE.sub(REDACTED, str(text))


def server_key_configured() -> bool:
    """True when the server has its own key (``ANTHROPIC_API_KEY``)."""
    return bool(os.environ.get(SERVER_KEY_ENV, "").strip())


# When the server key runs out of credit (or hits its spend limit) every
# keyless request would fail the same way. Remember it for a while so the
# site can say so up front and invite visitors to use their own key.
SERVER_REST_S = 600.0
_SERVER_RESTING_UNTIL = 0.0


def note_server_key_resting(now: float | None = None) -> None:
    global _SERVER_RESTING_UNTIL
    _SERVER_RESTING_UNTIL = (time.monotonic() if now is None else now) + SERVER_REST_S


def server_key_resting(now: float | None = None) -> bool:
    return (time.monotonic() if now is None else now) < _SERVER_RESTING_UNTIL


def reset_server_key_resting() -> None:
    global _SERVER_RESTING_UNTIL
    _SERVER_RESTING_UNTIL = 0.0


def free_assistant_available() -> bool:
    """True when a visitor without a key can ask a question right now."""
    return server_key_configured() and not server_key_resting()


# ─── Errors ───────────────────────────────────────────────────────────────


class LLMError(RuntimeError):
    """Base class. ``code`` is the ChatResponse ``error`` value. The message
    is redacted on construction, so ``str(err)`` is always safe to return."""

    code = "agent_failed"

    def __init__(self, message: Any = ""):
        super().__init__(redact_secrets(message))


class LLMNotConfiguredError(LLMError):
    """No usable key: none on the server and none sent by the visitor."""

    code = "assistant_unavailable"


class LLMRateLimitError(LLMError):
    """Anthropic answered 429."""

    code = "rate_limited"


class LLMKeyRejectedError(LLMError):
    """The visitor's own key was refused (401/403, or no credit on it)."""

    code = "key_rejected"


class LLMCreditExhaustedError(LLMError):
    """The server key hit its credit or spend limit."""

    code = "free_assistant_resting"


class LLMRefusalError(LLMError):
    """The model declined (stop_reason "refusal" after server fallbacks)."""

    code = "refused"


_CREDIT_RE = re.compile(
    r"credit balance|billing|spend(?:ing)? limit|usage limit|purchase credits"
    r"|insufficient (?:funds|credit)|out of credit",
    re.IGNORECASE,
)


def _error_text(exc: BaseException) -> str:
    text = getattr(exc, "message", None) or str(exc)
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") if isinstance(body.get("error"), dict) else body
        if isinstance(err, dict) and isinstance(err.get("message"), str):
            text = f"{text} {err['message']}"
    return str(text)


def _error_type(exc: BaseException) -> str | None:
    t = getattr(exc, "type", None)
    if isinstance(t, str):
        return t
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") if isinstance(body.get("error"), dict) else body
        if isinstance(err, dict) and isinstance(err.get("type"), str):
            return err["type"]
    return None


def _status_of(exc: BaseException) -> int | None:
    for attr in ("status_code", "status"):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            return v
    v = getattr(getattr(exc, "response", None), "status_code", None)
    return v if isinstance(v, int) else None


def _is_credit_error(exc: BaseException, status: int | None) -> bool:
    if status == 402 or _error_type(exc) == "billing_error":
        return True
    if status in (400, 403) or status is None:
        return bool(_CREDIT_RE.search(_error_text(exc)))
    return False


# ─── Data types ───────────────────────────────────────────────────────────


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

    ``tool_calls`` non-empty: run them and send back the results.
    ``raw_content`` is the assistant content to echo on the next request
    (thinking blocks included, already filtered by the fallback rule).
    """

    text: str | None = None
    tool_calls: list[ToolCall] = None  # type: ignore[assignment]
    stop_reason: str | None = None
    raw_content: list[Any] | None = None

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


def _btype(block: Any) -> str | None:
    if isinstance(block, dict):
        return block.get("type")
    return getattr(block, "type", None)


def _battr(block: Any, name: str, default: Any = None) -> Any:
    if isinstance(block, dict):
        return block.get(name, default)
    return getattr(block, name, default)


_DROP_BEFORE_FALLBACK = {"thinking", "redacted_thinking", "tool_use"}


def echo_blocks(content: list[Any]) -> list[Any]:
    """Assistant content to send back on the next request.

    Verbatim, except after a mid-output server-side fallback: thinking,
    redacted_thinking and tool_use blocks that come BEFORE the last
    ``fallback`` block are dropped. The fallback block itself stays where
    it appeared, and everything after it is kept.
    """
    blocks = list(content or [])
    last_fb = None
    for i, b in enumerate(blocks):
        if _btype(b) == "fallback":
            last_fb = i
    if last_fb is None:
        return blocks
    return [
        b
        for i, b in enumerate(blocks)
        if i >= last_fb or _btype(b) not in _DROP_BEFORE_FALLBACK
    ]


# ─── JSON schema helpers (strict tools / structured outputs) ──────────────

_UNSUPPORTED_SCHEMA_KEYS = {
    "default",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
    "uniqueItems",
}


def strict_json_schema(
    schema: dict[str, Any], *, all_required: bool = False
) -> dict[str, Any]:
    """Copy of ``schema`` usable with ``strict: true`` / structured outputs:
    every object gets ``additionalProperties: false`` and unsupported
    keywords (defaults, numeric and length limits) are removed. With
    ``all_required`` every property becomes required (nullable fields stay
    nullable, so the model can still say "not mentioned")."""

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(n) for n in node]
        if not isinstance(node, dict):
            return node
        out = {k: walk(v) for k, v in node.items() if k not in _UNSUPPORTED_SCHEMA_KEYS}
        if out.get("type") == "object":
            props = out.get("properties") or {}
            out["properties"] = props
            out["additionalProperties"] = False
            if all_required:
                out["required"] = list(props)
        return out

    return walk(copy.deepcopy(schema))


# ─── Server SDK client cache (server key only, never a visitor key) ──────

_SERVER_SDK: dict[str, Any] = {}
_SERVER_SDK_LOCK = threading.Lock()


def _build_sdk(api_key: str, timeout_s: float):
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover - dependency is pinned
        raise LLMNotConfiguredError(
            "The anthropic package is not installed: pip install -r requirements-api.txt"
        ) from e
    # An explicit api_key stops the SDK from reading any credential from the
    # environment (ANTHROPIC_API_KEY, profiles, federation).
    return anthropic.Anthropic(api_key=api_key, timeout=timeout_s, max_retries=2)


class LLMClient:
    """One assistant, one key. Cheap to build; build one per request."""

    def __init__(
        self,
        assistant: str | None = None,
        *,
        api_key: str | None = None,
        own_key: bool = False,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        _call_override: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        name = (assistant or DEFAULT_ASSISTANT).strip().lower()
        if name not in ASSISTANTS:
            raise ValueError(
                f"Unknown assistant {name!r}. Choose one of {sorted(ASSISTANTS)}."
            )
        self._spec = ASSISTANTS[name]
        self._own_key = bool(own_key)
        if self._own_key:
            # A visitor key is used as given, or not at all: never the env.
            self._api_key = api_key if looks_like_anthropic_key(api_key) else None
        else:
            self._api_key = api_key or os.environ.get(SERVER_KEY_ENV, "").strip() or None
        self._max_tokens = max_tokens
        self._timeout_s = timeout_s
        self._call_override = _call_override
        self._sdk_client = None

    def __repr__(self) -> str:  # never show the key
        return f"LLMClient(assistant={self._spec.id!r}, own_key={self._own_key})"

    # ── properties ────────────────────────────────────────────────────

    @property
    def assistant(self) -> str:
        return self._spec.id

    @property
    def spec(self) -> AssistantSpec:
        return self._spec

    @property
    def model(self) -> str:
        return self._spec.model

    @property
    def effort(self) -> str:
        return self._spec.effort

    @property
    def own_key(self) -> bool:
        return self._own_key

    @property
    def provider(self) -> str:
        return "anthropic"

    @property
    def is_configured(self) -> bool:
        if self._call_override is not None or self._sdk_client is not None:
            return True
        if not self._api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def close(self) -> None:
        """Visitor-key clients only: close the per-request SDK client and
        drop the key. A server-key client is left as it is."""
        if not self._own_key:
            return
        sdk, self._sdk_client, self._api_key = self._sdk_client, None, None
        if sdk is not None:
            try:
                sdk.close()
            except Exception:  # noqa: BLE001
                pass

    def _get_sdk(self):
        if self._sdk_client is not None:
            return self._sdk_client
        if not self._api_key:
            if self._own_key:
                raise LLMKeyRejectedError("The Anthropic key sent with this question is not usable.")
            raise LLMNotConfiguredError(
                "No Anthropic key is set on the server (ANTHROPIC_API_KEY). "
                "Add your own key to ask questions."
            )
        if self._own_key:
            self._sdk_client = _build_sdk(self._api_key, self._timeout_s)
            return self._sdk_client
        with _SERVER_SDK_LOCK:
            sdk = _SERVER_SDK.get(self._api_key)
            if sdk is None:
                _SERVER_SDK.clear()  # the env key changed: drop the old client
                sdk = _build_sdk(self._api_key, self._timeout_s)
                _SERVER_SDK[self._api_key] = sdk
        self._sdk_client = sdk
        return sdk

    # ── error translation ─────────────────────────────────────────────

    def _translate(self, exc: Exception) -> LLMError:
        """Map an SDK exception to a typed, redacted LLMError (most specific
        first: auth, permission, not found, rate limit, bad request, other
        status, connection)."""
        if isinstance(exc, LLMError):
            return exc
        try:
            import anthropic

            auth_cls = (anthropic.AuthenticationError, anthropic.PermissionDeniedError)
            nf_cls = anthropic.NotFoundError
            rl_cls = anthropic.RateLimitError
            bad_cls = anthropic.BadRequestError
            status_cls = anthropic.APIStatusError
            conn_cls = anthropic.APIConnectionError
        except ImportError:  # pragma: no cover
            auth_cls = nf_cls = rl_cls = bad_cls = status_cls = conn_cls = ()
        status = _status_of(exc)
        who = "your" if self._own_key else "the server's"

        if (auth_cls and isinstance(exc, auth_cls)) or status in (401, 403):
            if _is_credit_error(exc, status):
                return self._credit_error()
            if self._own_key:
                return LLMKeyRejectedError(
                    "Anthropic did not accept your API key. Check it in the "
                    "Anthropic console and try again."
                )
            logger.warning("Anthropic rejected the server key (status %s)", status)
            return LLMNotConfiguredError(
                "The server's Anthropic key was not accepted. Add your own key to "
                "ask questions."
            )
        if (nf_cls and isinstance(exc, nf_cls)) or status == 404:
            return LLMError(
                f"The model behind this assistant ({self.model}) is not available to "
                f"{who} Anthropic account."
            )
        if (rl_cls and isinstance(exc, rl_cls)) or status == 429:
            return LLMRateLimitError(
                "Anthropic is rate limiting requests right now. Try again in a minute."
            )
        if (bad_cls and isinstance(exc, bad_cls)) or status == 400:
            if _is_credit_error(exc, status):
                return self._credit_error()
            return LLMError(f"Anthropic rejected the request: {_error_text(exc)[:300]}")
        if (status_cls and isinstance(exc, status_cls)) or status is not None:
            if _is_credit_error(exc, status):
                return self._credit_error()
            return LLMError(f"Anthropic returned an error (status {status}).")
        if conn_cls and isinstance(exc, conn_cls):
            return LLMError("Could not reach Anthropic. Try again shortly.")
        return LLMError(f"{type(exc).__name__}: {exc}")

    def _credit_error(self) -> LLMError:
        if self._own_key:
            return LLMKeyRejectedError(
                "Your Anthropic account has no credit left or reached its spend limit."
            )
        note_server_key_resting()
        logger.warning("The server's Anthropic key hit its credit or spend limit")
        return LLMCreditExhaustedError(
            "The free assistant is resting: today's credit is used up. Add your own "
            "Anthropic key to keep asking."
        )

    def _create(self, **kwargs):
        """Call ``beta.messages.create`` and translate every failure."""
        sdk = self._get_sdk()
        try:
            return sdk.beta.messages.create(**kwargs)
        except Exception as e:  # noqa: BLE001 -- translated below
            raise self._translate(e) from None

    # Kept for callers that pass their own create function (tests, scripts).
    def _sdk_create(self, create_fn, **kwargs):
        try:
            return create_fn(**kwargs)
        except Exception as e:  # noqa: BLE001 -- translated below
            raise self._translate(e) from None

    # ── request shape ─────────────────────────────────────────────────

    @staticmethod
    def system_blocks(system: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """A plain string becomes one frozen block with cache_control."""
        if isinstance(system, str):
            return [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]
        return list(system)

    def request_kwargs(
        self,
        *,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        max_tokens: int | None = None,
        output_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """The exact keyword arguments for ``beta.messages.create``."""
        if tool_choice is not None and tool_choice.get("type") not in ("auto", "none"):
            raise ValueError("forced tool_choice is not supported on these models")
        output_config: dict[str, Any] = {"effort": self.effort}
        if output_format is not None:
            output_config["format"] = output_format
        kw: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens or self._max_tokens,
            "betas": [FALLBACK_BETA],
            "fallbacks": "default",
            "thinking": {"type": "adaptive"},
            "output_config": output_config,
            "system": self.system_blocks(system),
            "messages": messages,
            "cache_control": {"type": "ephemeral"},
        }
        if tools:
            kw["tools"] = tools
        if tool_choice is not None:
            kw["tool_choice"] = tool_choice
        return kw

    # ── classic parser: structured JSON output ────────────────────────

    def call_tool(self, system, user, tool_name, tool_schema):
        """Extract JSON matching ``tool_schema`` from ``user``.

        The name is historical: forcing a tool call returns a 400 on both
        assistants' models, so this uses structured outputs
        (``output_config.format``) and returns the parsed object.
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
                return LLMResponse(tool_input=result, stop_reason="end_turn")
            raise TypeError("_call_override for 'tool' must return dict or LLMResponse")

        fmt = {
            "type": "json_schema",
            "schema": strict_json_schema(tool_schema, all_required=True),
        }
        last_err: str = ""
        for _attempt in range(2):
            msg = self._create(
                **self.request_kwargs(
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    output_format=fmt,
                )
            )
            if msg.stop_reason == "refusal":
                raise LLMRefusalError("The assistant declined to answer this question.")
            text = "".join(
                _battr(b, "text", "") for b in msg.content if _btype(b) == "text"
            ).strip()
            try:
                data = json.loads(text)
            except (TypeError, ValueError):
                last_err = f"stop_reason={msg.stop_reason}"
                continue
            if isinstance(data, dict):
                return LLMResponse(
                    tool_input=data, raw_text=text, stop_reason=msg.stop_reason
                )
            last_err = "not a JSON object"
        raise RuntimeError(f"Model did not return valid {tool_name} JSON ({last_err})")

    # ── agent turns ───────────────────────────────────────────────────
    #
    # Neutral message format (used by llm/agent.py and by test overrides):
    #   {"role": "user",      "content": str}
    #   {"role": "assistant", "content": str | None,
    #    "tool_calls": [{"id", "name", "arguments"}],      # optional
    #    "raw_content": [blocks]}                          # optional, verbatim
    #   {"role": "tool",      "tool_call_id": str, "name": str, "content": str}

    @staticmethod
    def _neutral_to_anthropic(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert neutral agent messages to Messages API format.

        Assistant turns with ``raw_content`` are echoed verbatim (thinking
        blocks included). Tool results and any user text that follows them
        merge into ONE user message, tool results first.
        """
        out: list[dict[str, Any]] = []

        def push_user(blocks: list[dict[str, Any]]) -> None:
            if out and out[-1]["role"] == "user":
                prev = out[-1]["content"]
                if isinstance(prev, str):
                    prev = [{"type": "text", "text": prev}] if prev else []
                out[-1]["content"] = prev + blocks
            else:
                out.append({"role": "user", "content": blocks})

        for m in messages:
            role = m.get("role")
            if role == "user":
                text = m.get("content") or ""
                if out and out[-1]["role"] == "user":
                    push_user([{"type": "text", "text": text}])
                else:
                    out.append({"role": "user", "content": text})
            elif role == "assistant":
                raw = m.get("raw_content")
                if raw:
                    out.append({"role": "assistant", "content": echo_blocks(raw)})
                    continue
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
                push_user(
                    [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.get("tool_call_id") or "",
                            "content": m.get("content") or "",
                        }
                    ]
                )
        return out

    @staticmethod
    def _api_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        keys = ("name", "description", "input_schema", "strict")
        return [{k: t[k] for k in keys if k in t} for t in tools]

    def call_tools(
        self,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        max_tokens: int | None = None,
        tool_choice: dict[str, Any] | None = None,
    ) -> AgentStep:
        """One agent step. The model sees the transcript and the tools and
        either answers or asks for tool calls (``tool_choice`` auto, or
        ``{"type": "none"}`` for a forced final answer)."""
        if self._call_override is not None:
            result = self._call_override(
                "tools",
                {
                    "system": system,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": tool_choice,
                },
            )
            if isinstance(result, AgentStep):
                return result
            if isinstance(result, str):
                return AgentStep(text=result, stop_reason="end_turn")
            if isinstance(result, dict):
                calls = [
                    ToolCall(
                        id=tc.get("id") or f"call_{i}",
                        name=tc["name"],
                        arguments=tc.get("arguments") or {},
                    )
                    for i, tc in enumerate(result.get("tool_calls") or [])
                ]
                return AgentStep(
                    text=result.get("text"),
                    tool_calls=calls,
                    stop_reason=result.get("stop_reason")
                    or ("tool_use" if calls else "end_turn"),
                    raw_content=result.get("raw_content"),
                )
            raise TypeError(
                "_call_override for 'tools' must return AgentStep, str or dict"
            )

        msg = self._create(
            **self.request_kwargs(
                system=system,
                messages=self._neutral_to_anthropic(messages),
                tools=self._api_tools(tools) if tools else None,
                tool_choice=tool_choice,
                max_tokens=max_tokens,
            )
        )
        content = list(msg.content or [])
        if msg.stop_reason == "refusal":
            # Never read or run a refused turn's content.
            return AgentStep(stop_reason="refusal")
        kept = echo_blocks(content)
        text_chunks: list[str] = []
        calls: list[ToolCall] = []
        for block in kept:
            btype = _btype(block)
            if btype == "text":
                text_chunks.append(_battr(block, "text", "") or "")
            elif btype == "tool_use":
                args = _battr(block, "input", None)
                calls.append(
                    ToolCall(
                        id=_battr(block, "id", ""),
                        name=_battr(block, "name", ""),
                        arguments=dict(args) if isinstance(args, dict) else {},
                    )
                )
        return AgentStep(
            text="".join(text_chunks).strip() or None,
            tool_calls=calls,
            stop_reason=msg.stop_reason,
            raw_content=kept,
        )

    def call_text(self, system, user):
        if self._call_override is not None:
            result = self._call_override("text", {"system": system, "user": user})
            if isinstance(result, str):
                return result
            raise TypeError(
                f"_call_override for 'text' must return str, got {type(result).__name__}"
            )
        msg = self._create(
            **self.request_kwargs(
                system=system, messages=[{"role": "user", "content": user}]
            )
        )
        if msg.stop_reason == "refusal":
            raise LLMRefusalError("The assistant declined to answer this question.")
        return "".join(
            _battr(b, "text", "") or "" for b in msg.content if _btype(b) == "text"
        ).strip()


# ─── Process-wide server client (CLI and library use) ─────────────────────

_DEFAULT_CLIENT: LLMClient | None = None


def get_default_client() -> LLMClient:
    """The server-key mechanic. Never used for a visitor's key."""
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = LLMClient()
    return _DEFAULT_CLIENT


def reset_default_client() -> None:
    global _DEFAULT_CLIENT
    _DEFAULT_CLIENT = None
