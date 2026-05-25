from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.workflows.config import WorkflowConfig, resolve_workflow_config


@dataclass(slots=True)
class WorkflowTemplate:
    name: str
    default_steps: list[str]
    description: str
    allowed_tools: list[str] = field(default_factory=list)


class WorkflowTemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, WorkflowTemplate] = {
            "automation": WorkflowTemplate(
                name="automation",
                default_steps=["planner", "routing", "validation"],
                description="Generic automation workflow",
                allowed_tools=["browser.search", "browser.scraper", "communication.gmail", "communication.slack"],
            ),
            "sales": WorkflowTemplate(
                name="sales",
                default_steps=["planner", "research", "validator", "executor"],
                description="Lead generation and outreach workflow",
                allowed_tools=["browser.search", "browser.scraper", "communication.gmail", "crm.hubspot", "crm.salesforce"],
            ),
            "lead_generation": WorkflowTemplate(
                name="lead_generation",
                default_steps=["planner", "research", "memory", "validator", "executor"],
                description="Lead generation workflow",
                allowed_tools=["browser.search", "browser.scraper", "communication.gmail", "crm.hubspot", "crm.salesforce"],
            ),
            "support": WorkflowTemplate(
                name="support",
                default_steps=["planner", "retriever", "validator", "executor"],
                description="Customer support workflow",
                allowed_tools=["browser.search", "communication.slack"],
            ),
        }

    def resolve(self, workflow_definition: dict[str, Any] | None, input_payload: dict[str, Any] | None = None) -> tuple[WorkflowConfig, WorkflowTemplate]:
        config = resolve_workflow_config(workflow_definition, input_payload)
        template = self._templates.get(config.resolved_graph_name())
        if template is None:
            template = self._templates[config.workflow_type] if config.workflow_type in self._templates else self._templates["automation"]
        return config, template

    def get(self, template_name: str) -> WorkflowTemplate:
        return self._templates[template_name]

    def available(self) -> list[str]:
        return sorted(self._templates)


workflow_template_registry = WorkflowTemplateRegistry()
