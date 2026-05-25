from __future__ import annotations

from typing import Any


class ResearcherAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state["researcher"] = {"summary": "researched"}
        return state
