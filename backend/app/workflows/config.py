from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _normalize_step_name(step_name: str) -> str:
    return step_name.strip().lower().replace("-", "_")


@dataclass(slots=True)
class WorkflowConfig:
    workflow_type: str = "automation"
    graph_name: str | None = None
    steps: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "WorkflowConfig":
        data = payload or {}
        workflow_type = str(data.get("workflow_type") or data.get("kind") or data.get("vertical") or "automation")
        graph_name = data.get("graph_name") or data.get("graph")
        steps = data.get("steps") or []
        tools = data.get("tools") or []
        metadata = {key: value for key, value in data.items() if key not in {"workflow_type", "kind", "vertical", "graph_name", "graph", "steps", "tools"}}
        return cls(
            workflow_type=_normalize_step_name(workflow_type),
            graph_name=_normalize_step_name(graph_name) if isinstance(graph_name, str) and graph_name.strip() else None,
            steps=[_normalize_step_name(step) for step in steps if isinstance(step, str) and step.strip()],
            tools=[str(tool).strip() for tool in tools if str(tool).strip()],
            metadata=metadata,
        )

    def resolved_graph_name(self) -> str:
        return self.graph_name or self.workflow_type or "automation"

    def resolved_steps(self, default_steps: list[str]) -> list[str]:
        return list(self.steps or default_steps)


def resolve_workflow_config(workflow_definition: dict[str, Any] | None, input_payload: dict[str, Any] | None = None) -> WorkflowConfig:
    merged_definition = dict(workflow_definition or {})
    if isinstance(input_payload, dict):
        for key in ("workflow_type", "kind", "vertical", "graph_name", "graph", "steps", "tools"):
            if key not in merged_definition and key in input_payload:
                merged_definition[key] = input_payload[key]
    return WorkflowConfig.from_dict(merged_definition)
