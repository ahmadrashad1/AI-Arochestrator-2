from __future__ import annotations

from typing import Any


def score_lead(input_payload: dict[str, Any], research: dict[str, Any] | None = None, plan: dict[str, Any] | None = None) -> int:
    """Score a lead using simple, configurable heuristics.

    This lives in the lead_generation automation layer so generic agents remain agnostic.
    """
    score = 40
    if input_payload.get("email") or input_payload.get("prospect_email"):
        score += 20
    if input_payload.get("company") or (research or {}).get("company"):
        score += 15
    if input_payload.get("role"):
        score += 10
    if input_payload.get("research_query") or input_payload.get("goal"):
        score += 10
    return min(score, 100)
