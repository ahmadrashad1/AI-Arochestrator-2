from __future__ import annotations

from typing import Any


def _score_lead(input_payload: dict[str, Any]) -> int:
    score = 40
    if input_payload.get("email") or input_payload.get("prospect_email"):
        score += 20
    if input_payload.get("company"):
        score += 15
    if input_payload.get("role"):
        score += 10
    if input_payload.get("research_query") or input_payload.get("goal"):
        score += 10
    return min(score, 100)


def build_plan(input_payload: dict[str, Any], llm_route: dict[str, Any] | None = None) -> dict[str, Any]:
    objective = input_payload.get("goal") or input_payload.get("intent") or "identify and contact promising leads"
    lead_score = _score_lead(input_payload)
    return {
        "objective": objective,
        "graph_name": input_payload.get("graph_name") or "lead_generation",
        "tier": (llm_route or {}).get("tier", "standard"),
        "provider": (llm_route or {}).get("provider", "grok"),
        "model": (llm_route or {}).get("model", ""),
        "lead_score": lead_score,
        "next_action": "research_and_outreach",
    }


def personalize_message(input_payload: dict[str, Any], plan: dict[str, Any], research: dict[str, Any]) -> str:
    name = input_payload.get("name") or input_payload.get("prospect_name") or "there"
    company = input_payload.get("company") or research.get("company") or "your team"
    return (
        f"Hi {name},\n\n"
        f"I reviewed {company} and put together a short note based on {plan['objective']}. "
        f"Your lead score is {plan['lead_score']} out of 100, which makes this a good fit for outreach.\n\n"
        "If you’d like, I can share the rest of the workflow details."
    )
