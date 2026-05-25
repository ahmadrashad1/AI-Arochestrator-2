from __future__ import annotations

import time
from typing import Any


def run(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action") or "browse"
    if action == "sleep":
        time.sleep(float(payload.get("seconds", 1)))
    return {
        "tool": "browser.playwright",
        "action": action,
        "status": "ok",
        "payload": payload,
    }
