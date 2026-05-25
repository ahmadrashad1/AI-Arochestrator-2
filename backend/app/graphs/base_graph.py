from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

try:
    from langgraph.graph import StateGraph  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    StateGraph = None


GraphState = dict[str, Any]
NodeHandler = Callable[[GraphState], GraphState]


@dataclass(slots=True)
class BaseGraph:
    name: str
    entry_node: str
    nodes: dict[str, NodeHandler]
    transitions: dict[str, str | None] = field(default_factory=dict)

    def compile(self) -> Any:
        if StateGraph is None:
            return self

        graph = StateGraph(GraphState)
        for node_name, handler in self.nodes.items():
            graph.add_node(node_name, handler)
        graph.set_entry_point(self.entry_node)
        for source, target in self.transitions.items():
            if target is not None:
                graph.add_edge(source, target)
        return graph.compile()

    def _next_node(self, state: GraphState, current_node: str) -> str | None:
        explicit_next = state.pop("next_node", None)
        if explicit_next is not None:
            return explicit_next
        return self.transitions.get(current_node)

    def run(self, state: GraphState) -> GraphState:
        current_state = dict(state)
        current_state.setdefault("graph_name", self.name)
        current_state.setdefault("status", "running")
        current_state.setdefault("history", [])
        current_state.setdefault("visited_nodes", [])

        current_node = current_state.pop("current_node", None) or current_state.pop("next_node", None) or self.entry_node
        while current_node:
            current_state["current_node"] = current_node
            current_state["visited_nodes"].append(current_node)
            current_state["history"].append({"node": current_node, "status": current_state.get("status", "running")})
            handler = self.nodes[current_node]
            current_state = handler(current_state)
            if current_state.get("status") in {"paused", "failed", "completed"} and current_state.get("next_node") is None:
                break
            current_node = self._next_node(current_state, current_node)

        current_state.setdefault("output_payload", {
            "graph_name": self.name,
            "status": current_state.get("status", "completed"),
            "visited_nodes": list(current_state.get("visited_nodes", [])),
        })
        return current_state
