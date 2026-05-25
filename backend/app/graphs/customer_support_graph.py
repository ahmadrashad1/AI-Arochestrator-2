from __future__ import annotations

from app.graphs.base_graph import BaseGraph
from app.nodes.approval_node import run as approval_node
from app.nodes.fallback_node import run as fallback_node
from app.nodes.memory_node import run as memory_node
from app.nodes.planning_node import run as planning_node
from app.nodes.routing_node import run as routing_node
from app.nodes.tool_execution_node import run as tool_execution_node
from app.nodes.validation_node import run as validation_node


class CustomerSupportGraph(BaseGraph):
    def __init__(self) -> None:
        super().__init__(
            name="customer_support",
            entry_node="planning",
            nodes={
                "planning": planning_node,
                "routing": routing_node,
                "approval": approval_node,
                "memory": memory_node,
                "validation": validation_node,
                "tool_execution": tool_execution_node,
                "fallback": fallback_node,
            },
            transitions={
                "planning": "routing",
                "routing": "approval",
                "approval": "validation",
                "validation": "tool_execution",
                "tool_execution": None,
                "memory": "validation",
                "fallback": None,
            },
        )


def create_graph() -> CustomerSupportGraph:
    return CustomerSupportGraph()
