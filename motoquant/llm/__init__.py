"""
MotoQuant Pro -- LLM Interface Layer (Phase A)
==============================================
Wraps the Anthropic API for two jobs:
  1. parse_query: natural-language string -> structured SimulateRequest fields
  2. summarize_result: sim result -> 2-4 sentence English summary

Design notes
------------
- LLM is a translator at the edges (NL -> structure, structure -> NL).
  All physics, optimization, and DB lookup stays deterministic in the
  existing modules. The LLM never touches a number that affects ET.
- The query parser uses Anthropic tool-use (forced JSON output) so we
  never have to parse free-form text. Schema in parse_query.TOOL_SCHEMA.
- Bike resolution is two-stage: LLM extracts a name string, then
  parse_query._resolve_against_db does a fuzzy DB lookup. Keeps the
  prompt tiny (we never dump 290 bike rows into context).
- run_chat_pipeline is the single source of truth shared by the
  `motoquant chat` CLI and POST /api/chat. Pure data in, structured
  data out -- no printing, no HTTP.
- Tests inject a mock by passing LLMClient(_call_override=fn). No live
  API calls in CI -- see tests/test_llm.py.

Public surface re-exported for `from motoquant.llm import ...`.
"""

from .client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_S,
    LLMClient,
    LLMNotConfiguredError,
    LLMResponse,
    get_default_client,
    reset_default_client,
)
from .parse_query import SYSTEM_PROMPT, TOOL_SCHEMA, ParsedSimRequest, parse_query
from .runner import ChatResult, run_chat_pipeline
from .summarize import SUMMARIZE_SYSTEM_PROMPT, summarize_result

__all__ = [
    "ChatResult",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "DEFAULT_TIMEOUT_S",
    "LLMClient",
    "LLMNotConfiguredError",
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
