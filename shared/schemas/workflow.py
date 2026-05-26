from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    workflow_type: str = Field(default="automation")
    graph_name: str | None = None
    steps: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowConfigUpdate(BaseModel):
    workflow_type: str | None = None
    graph_name: str | None = None
    steps: list[str] | None = None
    tools: list[str] | None = None
    metadata: dict[str, Any] | None = None


class WorkflowOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None = None
    definition: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowEditorOut(WorkflowOut):
    config: WorkflowConfig = Field(default_factory=WorkflowConfig)