from __future__ import annotations

from typing import Any


class MemoryAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state.setdefault("memory", [])
        state["memory"].append({"summary": "memory updated"})
        return state
