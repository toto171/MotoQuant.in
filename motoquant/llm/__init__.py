"""
MotoQuant -- LLM Interface Layer
================================
Claude only. Two assistants ("the doctor" on Claude Opus 5.5, "the mechanic"
on Claude Sonnet 5.5) answer through one client, :class:`LLMClient`.

Design notes
------------
- The LLM is a translator at the edges (natural language to structure,
  structure to natural language). All physics, optimisation and catalog
  lookup stays deterministic in the existing modules. The LLM never touches
  a number that affects ET.
- The chat agent (agent.py) is a bounded tool-calling loop. The classic
  pipeline (runner.py) parses the query with structured JSON output, then
  dispatches on intent and summarises.
- The server key comes only from ANTHROPIC_API_KEY. A visitor's own key is
  used for one request through a per-request client and never stored.
- Tests inject a fake with LLMClient(_call_override=fn), or a fake SDK
  object on ``client._sdk_client``. No live API calls in CI.

Public surface re-exported for `from motoquant.llm import ...`.
"""

from .client import (
    ASSISTANTS,
    DEFAULT_ASSISTANT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_S,
    LLMClient,
    LLMCreditExhaustedError,
    LLMError,
    LLMKeyRejectedError,
    LLMNotConfiguredError,
    LLMRateLimitError,
    LLMRefusalError,
    LLMResponse,
    get_default_client,
    looks_like_anthropic_key,
    redact_secrets,
    reset_default_client,
)
from .parse_query import SYSTEM_PROMPT, TOOL_SCHEMA, ParsedSimRequest, parse_query
from .runner import ChatResult, run_chat_pipeline
from .summarize import SUMMARIZE_SYSTEM_PROMPT, summarize_result

__all__ = [
    "ASSISTANTS",
    "ChatResult",
    "DEFAULT_ASSISTANT",
    "LLMCreditExhaustedError",
    "LLMError",
    "LLMKeyRejectedError",
    "LLMRefusalError",
    "looks_like_anthropic_key",
    "redact_secrets",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "DEFAULT_TIMEOUT_S",
    "LLMClient",
    "LLMNotConfiguredError",
    "LLMRateLimitError",
    "LLMResponse",
    "ParsedSimRequest",
    "SUMMARIZE_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "TOOL_SCHEMA",
    "get_default_client",
    "parse_query",
    "reset_default_client",
    "run_chat_pipeline",
    "summarize_result",
]
