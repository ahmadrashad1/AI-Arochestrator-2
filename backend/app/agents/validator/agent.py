from __future__ import annotations

from typing import Any


class ValidatorAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state["validator"] = {"summary": "validated"}
        return state
