from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    query = input_payload.get("research_query") or input_payload.get("goal") or ""
    state["retrieved_context"] = {"query": query, "notes": [f"Context gathered for {query}".strip()]}
    state["next_node"] = "memory"
    return state
