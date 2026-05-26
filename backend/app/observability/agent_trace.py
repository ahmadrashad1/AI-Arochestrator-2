from __future__ import annotations

from typing import Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger("agent_trace")


def record_agent_decision(tenant_id: str | None, workflow_id: str | None, execution_id: str | None, agent: str, decision: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "agent": agent,
        "decision": decision,
        "details": details or {},
    }
    logger.info("agent.decision %s", entry)
    return entry
