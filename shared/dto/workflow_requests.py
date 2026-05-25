from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateWorkflowRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    definition: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Workflow name cannot be empty")
        return normalized


class RunWorkflowRequest(BaseModel):
    input_payload: dict[str, Any] = Field(default_factory=dict)
