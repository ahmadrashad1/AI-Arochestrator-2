from __future__ import annotations

import os
import time
import logging
from typing import Optional

from app.workers.workflow_worker import process_next_workflow_job
from app.workers.tool_worker import process_tool_jobs
from app.workers.retry_worker import process_retry_jobs
from app.workers.cleanup_worker import cleanup_dead_letters
from app.database.repositories import get_execution_repository

logger = logging.getLogger("app.workers.runner")


def run_once(exec_repo=None) -> int:
    """Run one pass over available worker queues and return number of tasks processed."""
    count = 0
    exec_repo = exec_repo or get_execution_repository()
    try:
        res = process_next_workflow_job(exec_repo)
        if res is not None:
            count += 1
    except Exception:
        logger.exception("workflow worker error")

    try:
        count += process_tool_jobs(exec_repo)
    except Exception:
        logger.exception("tool worker error")

    try:
        count += process_retry_jobs()
    except Exception:
        logger.exception("retry worker error")

    try:
        # do not purge by default
        cleanup_dead_letters(purge=False)
    except Exception:
        logger.exception("cleanup worker error")

    return count


def run_loop(poll_interval: float = 0.2, max_idle: Optional[int] = None) -> None:
    """Run workers in a tight loop until interrupted.

    poll_interval: seconds to sleep when no tasks processed
    max_idle: optional number of consecutive idle cycles before exit
    """
    idle = 0
    try:
        while True:
            processed = run_once()
            if processed == 0:
                idle += 1
                if max_idle is not None and idle >= max_idle:
                    logger.info("max idle reached, exiting")
                    return
                time.sleep(poll_interval)
            else:
                idle = 0
    except KeyboardInterrupt:
        logger.info("worker runner interrupted")


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("WORKER_LOG_LEVEL", "INFO"))
    run_loop()
