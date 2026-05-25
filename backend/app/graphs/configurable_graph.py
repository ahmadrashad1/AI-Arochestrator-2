from __future__ import annotations

from typing import Any

from app.agents.primitives import (
    executor_primitive,
    memory_primitive,
    planner_primitive,
    research_primitive,
    retriever_primitive,
    router_primitive,
    tool_executor_primitive,
    validator_primitive,
)
from app.graphs.base_graph import BaseGraph


STEP_HANDLERS = {
    "planner": planner_primitive,
    "research": research_primitive,
    "retriever": retriever_primitive,
    "router": router_primitive,
    "validator": validator_primitive,
    "memory": memory_primitive,
    "executor": executor_primitive,
    "tool_execution": tool_executor_primitive,
    "approval": validator_primitive,
}


class ConfigurableGraph(BaseGraph):
    def __init__(self, *, name: str, steps: list[str], allowed_tools: list[str] | None = None) -> None:
        normalized_steps = [step for step in steps if step in STEP_HANDLERS]
        if not normalized_steps:
            normalized_steps = ["planner", "router", "validator", "executor"]

        nodes = {step: STEP_HANDLERS[step] for step in normalized_steps}
        transitions = {current: normalized_steps[index + 1] if index + 1 < len(normalized_steps) else None for index, current in enumerate(normalized_steps)}
        self.allowed_tools = allowed_tools or []
        super().__init__(name=name, entry_node=normalized_steps[0], nodes=nodes, transitions=transitions)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        state = dict(state)
        state.setdefault("workflow_definition", {})
        state.setdefault("workflow_config", {})
        if self.allowed_tools:
            state["workflow_config"]["tools"] = list(self.allowed_tools)
        return super().run(state)
