from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExecutionProgressOut(BaseModel):
    status: str
    progress: int
    message: str
    recorded_at: datetime | None = None


class ExecutionOut(BaseModel):
    id: str
    tenant_id: str
    workflow_id: str
    status: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExecutionStatusOut(BaseModel):
    execution: ExecutionOut
    progress: int
    message: str
    history: list[ExecutionProgressOut] = Field(default_factory=list)