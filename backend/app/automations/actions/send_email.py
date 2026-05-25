from __future__ import annotations

from typing import Any

from app.tools.communication.gmail_tool import run as send_gmail


def run(payload: dict[str, Any]) -> dict[str, Any]:
    email_payload = dict(payload)
    email_payload.setdefault("allow_send", True)
    result = send_gmail(email_payload)
    result["action"] = "send_email"
    return result
