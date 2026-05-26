from __future__ import annotations

from typing import Any



def build_plan(input_payload: dict[str, Any], llm_route: dict[str, Any] | None = None) -> dict[str, Any]:
    objective = input_payload.get("goal") or input_payload.get("intent") or "identify and contact promising leads"
    return {
        "objective": objective,
        "graph_name": input_payload.get("graph_name") or "lead_generation",
        "tier": (llm_route or {}).get("tier", "standard"),
        "provider": (llm_route or {}).get("provider", "grok"),
        "model": (llm_route or {}).get("model", ""),
        "next_action": "research_and_outreach",
    }


# Note: lead scoring and personalization now live in the automation layer
