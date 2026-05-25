from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    if input_payload.get("approval_required"):
        state["next_node"] = "approval"
    elif input_payload.get("tool_request") or input_payload.get("tool_name"):
        state["next_node"] = "tool_execution"
    elif input_payload.get("research_query"):
        state["next_node"] = "retrieval"
    else:
        state["next_node"] = "validation"
    state["route_decision"] = state["next_node"]
    return state
