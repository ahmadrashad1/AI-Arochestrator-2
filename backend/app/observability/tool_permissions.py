from __future__ import annotations

from typing import Any
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger("tool_permissions")


def audit_tool_permission(tenant_id: str | None, workflow_id: str | None, execution_id: str | None, tool: str, allowed: bool, reason: str | None = None) -> dict[str, Any]:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "tool": tool,
        "allowed": bool(allowed),
        "reason": reason,
    }
    logger.info("tool.permission %s", entry)
    return entry
