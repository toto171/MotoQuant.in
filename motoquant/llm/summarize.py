"""
summarize_result -- render a sim result + parsed query in plain English.

Style target: 2-4 sentences a tuner would actually want to read.
NOT a wall of stats -- those are already in the structured output for the UI.
Highlight: ET, trap, biggest factor that moved the number, what to try next.

Usage
-----
    from motoquant.llm import parse_query, summarize_result

    parsed = parse_query("how fast is my K5?", db=db)
    sim_result = run_simulation(parsed)  # whatever the caller does
    summary = summarize_result(parsed, sim_result)
    print(summary)
    # -> "The K5 ran 10.04 s at 240 km/h on a clean Aamby Valley pull.
    #     Stock launch -- a slipper clutch is the next obvious 0.1 s."
"""

from __future__ import annotations

from typing import Any

from .client import LLMClient, get_default_client
from .parse_query import ParsedSimRequest

__all__ = ["summarize_result", "SUMMARIZE_SYSTEM_PROMPT"]


SUMMARIZE_SYSTEM_PROMPT = """\
You are a knowledgeable motorcycle drag-racing engineer writing a short result \
summary for a tuner. Tone: direct, technical-but-readable, no marketing fluff.

Constraints:
- 2 to 4 sentences total. No headers, no bullet lists, no markdown.
- Lead with the headline numbers (ET in seconds and trap speed in km/h).
- If the input mentions applied parts or unusual environmental conditions \
that meaningfully changed the result, flag that in one sentence.
- If the user had a specific goal (minimize_et / maximize_trap / best_budget), \
end with one concrete suggestion for what to try next.
- Use Indian Rupee (INR) for prices. Use km/h primary, mph in parens optional.
- Never apologize, never disclaim. Speak with calibrated confidence.
"""


def _format_user_message(parsed: ParsedSimRequest, sim: dict[str, Any]) -> str:
    """Render parsed + sim result as the user-turn payload to the LLM."""
    lines = ["The user asked:", f"  > {parsed.raw_query}", ""]

    lines.append(f"Resolved bike: {parsed.bike_name or '<unknown>'}")
    if parsed.venue_name:
        lines.append(f"Venue: {parsed.venue_name}")

    cond = []
    if parsed.ambient_temp_c is not None:
        cond.append(f"{parsed.ambient_temp_c:g}C ambient")
    if parsed.humidity_pct is not None:
        cond.append(f"{parsed.humidity_pct:g}% RH")
    if parsed.altitude_m is not None:
        cond.append(f"{parsed.altitude_m:g} m altitude")
    if parsed.headwind_kmh is not None:
        cond.append(f"{parsed.headwind_kmh:g} km/h headwind")
    if cond:
        lines.append("Conditions: " + ", ".join(cond))

    if parsed.parts_categories:
        lines.append("Parts considered: " + ", ".join(parsed.parts_categories))
    if parsed.budget_inr:
        lines.append(f"Budget: INR {parsed.budget_inr:,}")
    lines.append(f"Optimization goal: {parsed.optimization_goal}")
    if parsed.notes:
        lines.append(f"Parser notes: {parsed.notes}")

    lines.append("")
    lines.append("Simulation result:")
    et = sim.get("et_quarter_s", sim.get("et_s", sim.get("time_quarter")))
    trap_kmh = sim.get("trap_speed_kmh")
    sixty = sim.get("et_60ft_s", sim.get("sixty_foot_s", sim.get("time_60ft")))

    if et is not None:
        lines.append(f"  ET: {float(et):.3f} s")
    if trap_kmh is not None:
        lines.append(f"  Trap: {float(trap_kmh):.1f} km/h")
    if sixty is not None:
        lines.append(f"  60-ft: {float(sixty):.3f} s")
    if sim.get("applied_parts"):
        lines.append(f"  Applied parts: {', '.join(sim['applied_parts'])}")
    if sim.get("build_cost_inr"):
        lines.append(f"  Build cost: INR {int(sim['build_cost_inr']):,}")
    if sim.get("delta_et_s") is not None:
        lines.append(f"  delta-ET vs stock: {float(sim['delta_et_s']):+.3f} s")
    if sim.get("peak_accel_g") is not None:
        lines.append(f"  Peak accel: {float(sim['peak_accel_g']):.2f} g")

    lines.append("")
    lines.append("Write the 2-4 sentence summary now.")
    return "\n".join(lines)


def summarize_result(
    parsed: ParsedSimRequest,
    sim_result: dict[str, Any],
    *,
    client: LLMClient | None = None,
) -> str:
    """Generate a 2-4 sentence plain-English summary of a sim result.

    Args:
      parsed: ParsedSimRequest the run was based on.
      sim_result: dict with keys like et_s, trap_speed_kmh, sixty_foot_s,
                  applied_parts, build_cost_inr, delta_et_s, peak_accel_g.
                  Missing keys are silently skipped.
      client: optional LLMClient. Defaults to module singleton.

    Returns:
      Plain-English summary. Trailing whitespace is stripped.
    """
    cli = client or get_default_client()
    user_msg = _format_user_message(parsed, sim_result)
    return cli.call_text(system=SUMMARIZE_SYSTEM_PROMPT, user=user_msg)
