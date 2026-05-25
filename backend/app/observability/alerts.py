from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger
from threading import RLock
from typing import Any

import httpx

logger = logging.getLogger("app.alerts")


def _level_for(level: str) -> int:
    match level.lower():
        case "critical":
            return 50
        case "error":
            return 40
        case "warning":
            return 30
        case _:
            return 20


@dataclass(slots=True)
class AlertRecord:
    level: str
    code: str
    message: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class AlertDispatcher:
    def __init__(self) -> None:
        self._logger = getLogger("alerts")
        self._lock = RLock()
        self._alerts: list[AlertRecord] = []

    def notify(self, level: str, code: str, message: str, **metadata: Any) -> AlertRecord:
        record = AlertRecord(level=level, code=code, message=message, created_at=datetime.now(timezone.utc), metadata=metadata)
        with self._lock:
            self._alerts.append(record)
        self._logger.log(_level_for(level), "%s: %s", code, message, extra={"metadata": metadata})
        return record

    def list_alerts(self) -> list[AlertRecord]:
        with self._lock:
            return list(self._alerts)

    def clear(self) -> None:
        with self._lock:
            self._alerts.clear()


alert_dispatcher = AlertDispatcher()


def alert_dead_letter(task: Any, reason: str) -> None:
    """Send a simple alert when a task is dead-lettered. Falls back to logging.

    If `ALERT_WEBHOOK_URL` env var is set, POST a JSON payload.
    """
    payload = {
        "task_id": getattr(task, "id", None) or (task.get("id") if isinstance(task, dict) else None),
        "task_name": getattr(task, "name", None) or (task.get("name") if isinstance(task, dict) else None),
        "reason": reason,
    }
    webhook = os.environ.get("ALERT_WEBHOOK_URL")
    # record internally
    try:
        alert_dispatcher.notify("warning", "dead_letter", "Task moved to dead letter", payload=payload)
    except Exception:
        pass

    if webhook:
        try:
            httpx.post(webhook, json=payload, timeout=5.0)
        except Exception as exc:
            logger.warning("Failed to post alert webhook: %s", exc)
    else:
        logger.warning("Dead-letter alert: %s", payload)

    # If an Alertmanager URL is provided, POST in Alertmanager v1 API format (/api/v1/alerts)
    alertmanager = os.environ.get("ALERTMANAGER_URL")
    if alertmanager:
        try:
            url = alertmanager.rstrip("/")
            if not url.endswith("/api/v1/alerts"):
                url = f"{url}/api/v1/alerts"
            alert = {
                "labels": {
                    "alertname": "DeadLetter",
                    "severity": "warning",
                    "task_name": payload.get("task_name") if isinstance(payload, dict) else None,
                },
                "annotations": {
                    "summary": "Task moved to dead letter",
                    "description": payload.get("reason") if isinstance(payload, dict) else str(payload),
                },
                "startsAt": datetime.now(timezone.utc).isoformat(),
            }
            httpx.post(url, json=[alert], timeout=5.0)
        except Exception as exc:
            logger.warning("Failed to post to Alertmanager: %s", exc)
