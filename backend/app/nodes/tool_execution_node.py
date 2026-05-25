from __future__ import annotations

from typing import Any

from app.automations.lead_generation.execution_engine import execute_lead_generation
from app.tools.registry import run_tool


def run(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("graph_name") == "lead_generation":
        result = execute_lead_generation(state)
        state.update(result)
        state["status"] = result.get("status", "completed")
        state["next_node"] = None
        return state

    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    tool_request = input_payload.get("tool_request") if isinstance(input_payload.get("tool_request"), dict) else None
    tool_name = input_payload.get("tool_name") or (tool_request.get("tool_name") if tool_request else None)
    tool_input = input_payload.get("tool_input") or (tool_request.get("input_payload") if tool_request else input_payload)
    if not tool_name:
        state["next_node"] = None
        state["status"] = "completed"
        return state

    result = run_tool(tool_name, tool_input)
    state["tool_result"] = result
    state["output_payload"] = {
        "workflow_id": state.get("workflow_id"),
        "execution_id": state.get("execution_id"),
        "status": "completed",
        "tool_name": tool_name,
        "tool_result": result,
        "llm_route": state.get("llm_route"),
    }
    state["status"] = "completed"
    state["next_node"] = None
    return state
