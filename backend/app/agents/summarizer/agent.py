from __future__ import annotations

from typing import Any


class SummarizerAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state["summary"] = f"Workflow {state.get('workflow_id')} processed"
        return state
