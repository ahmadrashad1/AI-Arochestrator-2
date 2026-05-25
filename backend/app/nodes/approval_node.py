from __future__ import annotations

from typing import Any


def run(state: dict[str, Any]) -> dict[str, Any]:
    input_payload = state.get("input_payload", {}) if isinstance(state.get("input_payload"), dict) else {}
    approved = bool(input_payload.get("approved") or state.get("approved"))
    if not approved:
        state["status"] = "paused"
        state["pause_reason"] = "approval required"
        state["next_node"] = None
        return state

    state["approved"] = True
    state["next_node"] = "validation"
    return state
