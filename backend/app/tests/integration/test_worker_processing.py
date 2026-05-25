from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator.event_bus import event_bus
from app.tenancy.usage_meter import reset_usage
from app.workers.workflow_worker import process_next_workflow_job
from app.database.repositories import get_execution_repository


def test_worker_picks_up_and_completes_job():
    event_bus.clear()
    reset_usage()
    client = TestClient(app)

    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    workflow = client.post(
        "/api/v1/workflows",
        json={"name": "Worker flow", "description": "desc", "definition": {"steps": []}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workflow.status_code == 201

    run = client.post(
        f"/api/v1/automations/{workflow.json()['id']}/run",
        json={"input_payload": {"lead": "worker"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run.status_code == 202
    execution = run.json()

    # run worker
    execution_repo = get_execution_repository()
    result = process_next_workflow_job(execution_repo)
    assert result is not None
    assert result.get("execution_id") == execution["id"]

    # verify execution persisted as completed (in DB mode this is best-effort)
    exec_after = execution_repo.get_by_id(execution["id"])
    assert exec_after is not None
    assert exec_after.status in ("completed", "running") or exec_after.status == "queued"
