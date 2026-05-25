from __future__ import annotations

from typing import Any


def run(payload: dict[str, Any]) -> dict[str, Any]:
    return {"tool": "crm.hubspot", "synced": True, "payload": payload}
