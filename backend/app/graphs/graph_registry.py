from __future__ import annotations

from typing import Any

from app.graphs.automation_graph import create_graph as create_automation_graph
from app.graphs.configurable_graph import ConfigurableGraph
from app.graphs.customer_support_graph import create_graph as create_customer_support_graph
from app.graphs.lead_generation_graph import create_graph as create_lead_generation_graph
from app.workflows.template_registry import workflow_template_registry


class GraphRegistry:
    def __init__(self) -> None:
        self._factories = {
            "automation": create_automation_graph,
            "lead_generation": create_lead_generation_graph,
            "customer_support": create_customer_support_graph,
        }

    def select_name(self, workflow_definition: dict[str, Any] | None, input_payload: dict[str, Any] | None = None) -> str:
        workflow_definition = workflow_definition or {}
        input_payload = input_payload or {}
        for key in ("graph_name", "graph", "workflow_type", "kind", "vertical"):
            value = workflow_definition.get(key) or input_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower().replace("-", "_")
        return "automation"

    def resolve(self, workflow_definition: dict[str, Any] | None, input_payload: dict[str, Any] | None = None):
        config, template = workflow_template_registry.resolve(workflow_definition, input_payload)
        name = config.resolved_graph_name()

        # Preserve the specialized sales/support vertical graphs when tenants explicitly select them.
        if name in self._factories and not config.steps:
            return self._factories[name]()

        if config.steps or config.workflow_type in workflow_template_registry.available():
            return ConfigurableGraph(name=name, steps=config.resolved_steps(template.default_steps), allowed_tools=template.allowed_tools)

        factory = self._factories.get(name) or self._factories["automation"]
        return factory()

    def available(self) -> list[str]:
        return sorted(self._factories)


graph_registry = GraphRegistry()
