from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None = None
    definition: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None