from __future__ import annotations

from app.graphs.base_graph import BaseGraph
from app.nodes.fallback_node import run as fallback_node
from app.nodes.memory_node import run as memory_node
from app.nodes.planning_node import run as planning_node
from app.nodes.retrieval_node import run as retrieval_node
from app.nodes.routing_node import run as routing_node
from app.nodes.tool_execution_node import run as tool_execution_node
from app.nodes.validation_node import run as validation_node


class LeadGenerationGraph(BaseGraph):
    def __init__(self) -> None:
        super().__init__(
            name="lead_generation",
            entry_node="planning",
            nodes={
                "planning": planning_node,
                "routing": routing_node,
                "retrieval": retrieval_node,
                "memory": memory_node,
                "validation": validation_node,
                "tool_execution": tool_execution_node,
                "fallback": fallback_node,
            },
            transitions={
                "planning": "routing",
                "routing": "retrieval",
                "retrieval": "memory",
                "memory": "validation",
                "validation": None,
                "tool_execution": None,
                "fallback": None,
            },
        )


def create_graph() -> LeadGenerationGraph:
    return LeadGenerationGraph()
