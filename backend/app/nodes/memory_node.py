from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("memory", [])
    state["memory"].append({"step": state.get("current_node"), "content": state.get("retrieved_context", {})})
    state["next_node"] = "validation"
    return state
