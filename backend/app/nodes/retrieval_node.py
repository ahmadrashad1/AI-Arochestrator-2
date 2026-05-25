from __future__ import annotations

from typing import Any

from app.agents.researcher.retrieval import gather_lead_context


def run(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    state["retrieved_context"] = gather_lead_context(input_payload)
    state["next_node"] = "memory"
    return state
