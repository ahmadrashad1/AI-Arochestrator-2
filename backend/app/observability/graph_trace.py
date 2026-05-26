from __future__ import annotations

from typing import Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger("graph_trace")


def record_node_transition(tenant_id: str | None, workflow_id: str | None, execution_id: str | None, node: str, from_node: str | None, to_node: str | None, agent_id: str | None = None, **meta: Any) -> dict[str, Any]:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "execution_id": execution_id,
        "node": node,
        "from": from_node,
        "to": to_node,
        "agent_id": agent_id,
        **meta,
    }
    logger.info("node.transition %s", entry)
    return entry
