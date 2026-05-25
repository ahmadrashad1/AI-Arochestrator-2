from app.workers.celery import CeleryQueueBackend
from app.workers.celery_worker import celery_app


def test_celery_eager_mode(monkeypatch):
    # run Celery app in eager mode for test
    celery_app.conf.task_always_eager = True
    backend = CeleryQueueBackend(broker_url="memory://")
    # publishing should not raise
    task = backend.publish("workflow.execution.requested", {"execution_id": "ex1"})
    assert task is not None
