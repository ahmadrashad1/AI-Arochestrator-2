from __future__ import annotations

import os

from app.workers.workflow_worker import process_next_workflow_job
from app.database.repositories import get_execution_repository


def _make_fallback_celery():
    class _Fallback:
        def __init__(self, *args, **kwargs):
            self.conf = type("C", (), {"task_always_eager": True})()

        def task(self, *dargs, **dkwargs):
            def _dec(f):
                return f

            return _dec

        def send_task(self, name, args=None, kwargs=None):
            # no-op for fallback
            return None

    return _Fallback()


try:
    from celery import Celery

    CELERY_BROKER = os.environ.get("REDIS_URL") or os.environ.get("BROKER_URL") or "redis://localhost:6379/0"
    celery_app = Celery("ai_orchestrator_worker", broker=CELERY_BROKER)
except Exception:
    celery_app = _make_fallback_celery()


@celery_app.task(name="workflow.execution.requested")
def handle_workflow_execution(payload: dict):
    """Celery task entrypoint for workflow execution requests.

    payload: {execution_id, workflow_id, tenant_id, input_payload}
    """
    # obtain execution repository from factory (request-scoped in HTTP world)
    exec_repo = get_execution_repository()
    # run one job (this task may be invoked with the payload)
    process_next_workflow_job(exec_repo)


@celery_app.task(name="tool.execution.requested")
def handle_tool_execution(payload: dict):
    """Celery task entrypoint for tool execution requests.

    payload: {execution_id, tool_name, input_payload}
    """
    exec_repo = get_execution_repository()
    # process tool job once
    try:
        from app.workers.tool_worker import process_tool_jobs

        process_tool_jobs(exec_repo)
    except Exception:
        # best-effort fallback: ignore errors in worker process
        pass
