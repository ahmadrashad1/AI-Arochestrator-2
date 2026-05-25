from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator.event_bus import event_bus
from app.orchestrator.retry_manager import RetryPolicy, RetryManager
from app.orchestrator.retry_manager import retry_manager
from app.workers.workflow_worker import process_next_workflow_job
from app.database.repositories import get_execution_repository


def test_dead_letter_after_retries(monkeypatch):
    # shorten retry policy for test
    monkeypatch.setattr(retry_manager, "policy", RetryPolicy(max_attempts=2, base_delay_seconds=0))
    event_bus.clear()
    client = TestClient(app)

    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    workflow = client.post(
        "/api/v1/workflows",
        json={"name": "Fail flow", "description": "desc", "definition": {"steps": []}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workflow.status_code == 201

    run = client.post(
        f"/api/v1/automations/{workflow.json()['id']}/run",
        json={"input_payload": {"lead": "fail"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run.status_code == 202
    execution = run.json()

    # monkeypatch runner to raise
    class BadRunner:
        def build_execution_plan(self, *args, **kwargs):
            raise RuntimeError("worker failure")

    execution_repo = get_execution_repository()
    # first attempt
    res1 = process_next_workflow_job(execution_repo, runner=BadRunner())
    assert res1 is not None
    # second attempt (requeued)
    res2 = process_next_workflow_job(execution_repo, runner=BadRunner())
    assert res2 is not None

    # after max attempts dead-letter should have the task
    dead = event_bus.dead_letters()
    assert any(task.payload.get("execution_id") == execution["id"] for task in dead)
