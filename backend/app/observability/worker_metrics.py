from __future__ import annotations

from typing import Any
from app.observability import metrics
from app.core.logging import get_logger

logger = get_logger("worker_metrics")


def record_queue_wait(queue_name: str, wait_seconds: float) -> None:
    try:
        metrics.processing_tasks.set(0)  # placeholder
    except Exception:
        pass
    logger.info("worker.queue_wait %s %s", queue_name, wait_seconds)


def record_job_duration(workflow_id: str | None, execution_id: str | None, duration_seconds: float) -> None:
    logger.info("worker.job_duration %s %s %s", workflow_id, execution_id, duration_seconds)


def record_worker_busy(count: int) -> None:
    try:
        metrics.processing_tasks.set(count)
    except Exception:
        pass
