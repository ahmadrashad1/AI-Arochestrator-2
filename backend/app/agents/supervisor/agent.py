from __future__ import annotations

from typing import Any


class SupervisorAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state["supervisor"] = {"decision": "route"}
        return state
