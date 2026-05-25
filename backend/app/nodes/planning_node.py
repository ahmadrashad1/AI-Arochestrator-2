from __future__ import annotations

from typing import Any

from app.llm.router import llm_router


def run(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    route = llm_router.select_route(input_payload.get("llm_tier"))
    plan = {
        "objective": input_payload.get("goal") or input_payload.get("intent") or "complete workflow",
        "tier": route.tier,
        "provider": route.provider,
        "model": route.model,
    }
    state["plan"] = plan
    state["llm_route"] = route.to_dict()
    state.setdefault("next_node", "routing")
    return state
