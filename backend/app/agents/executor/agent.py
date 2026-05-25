from __future__ import annotations

from typing import Any


class ExecutorAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state["executor"] = {"summary": "executed"}
        return state
