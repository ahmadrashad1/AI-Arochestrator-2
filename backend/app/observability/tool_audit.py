from __future__ import annotations

from typing import Any
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger("tool_audit")


def record_tool_call(tenant_id: str | None, workflow_id: str | None, execution_id: str | None, tool_name: str, status: str, duration_ms: int | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "tool": tool_name,
        "status": status,
        "duration_ms": duration_ms,
        "extra": extra or {},
    }
    logger.info("tool.call %s", entry)
    return entry
