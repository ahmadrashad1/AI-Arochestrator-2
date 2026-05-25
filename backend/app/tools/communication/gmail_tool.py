from __future__ import annotations

from typing import Any


def run(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("allow_send", False):
        raise PermissionError("sending email not allowed without allow_send=true")
    recipient = payload.get("to") or payload.get("recipient")
    if not recipient:
        raise ValueError("recipient is required")
    return {
        "tool": "communication.gmail",
        "to": recipient,
        "subject": payload.get("subject", ""),
        "body": payload.get("body", ""),
        "status": "queued",
    }
