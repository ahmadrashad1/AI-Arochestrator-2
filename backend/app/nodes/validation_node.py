from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload")
    if not isinstance(input_payload, dict):
        state["status"] = "failed"
        state["error"] = "input_payload must be a mapping"
        state["next_node"] = "fallback"
        return state

    if state.get("plan") is None:
        state["plan"] = {"objective": input_payload.get("goal") or "complete workflow"}

    state["validation"] = {"ok": True}
    if state.get("graph_name") == "lead_generation":
        state["next_node"] = "tool_execution"
    else:
        state["next_node"] = "tool_execution" if (input_payload.get("tool_request") or input_payload.get("tool_name")) else None
    if state["next_node"] is None:
        state["status"] = "completed"
    return state
