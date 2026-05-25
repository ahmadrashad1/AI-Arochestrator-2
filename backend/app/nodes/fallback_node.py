from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    error = state.get("error") or state.get("pause_reason") or "fallback triggered"
    state["fallback"] = {"reason": error}
    if state.get("allow_fallback", True):
        state["status"] = "completed"
        state["output_payload"] = {
            "workflow_id": state.get("workflow_id"),
            "execution_id": state.get("execution_id"),
            "status": "completed",
            "fallback": True,
            "reason": error,
            "llm_route": state.get("llm_route"),
        }
    else:
        state["status"] = "failed"
    state["next_node"] = None
    return state
