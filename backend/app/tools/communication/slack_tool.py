from __future__ import annotations

from typing import Any


def run(payload: dict[str, Any]) -> dict[str, Any]:
    channel = payload.get("channel") or "#general"
    if not payload.get("allow_send", False):
        raise PermissionError("posting to slack not allowed without allow_send=true")
    return {"tool": "communication.slack", "channel": channel, "message": payload.get("message", ""), "status": "queued"}
