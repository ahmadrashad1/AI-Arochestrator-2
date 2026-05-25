from __future__ import annotations

from typing import Any


class PlannerAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state["planner"] = {"summary": "planned"}
        return state
