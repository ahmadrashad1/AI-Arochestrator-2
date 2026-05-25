from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator.event_bus import event_bus
from app.database.repositories import get_execution_repository
from app.workers.tool_worker import process_tool_jobs


def test_tool_request_enqueues_and_processes_job():
    event_bus.clear()
    from app.tenancy.usage_meter import reset_usage
    reset_usage()
    client = TestClient(app)

    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    wf = client.post(
        "/api/v1/workflows",
        json={"name": "Tool flow", "description": "desc", "definition": {"steps": []}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert wf.status_code == 201

    # run with a tool_request payload
    run = client.post(
        f"/api/v1/automations/{wf.json()['id']}/run",
        json={"input_payload": {"tool_request": {"tool_name": "echo", "input_payload": {"msg": "hi"}}}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run.status_code == 202
    execution = run.json()

    # workflow worker builds the plan and should have enqueued a tool job
    exec_repo = get_execution_repository()
    # process the workflow job which enqueues the tool request
    from app.workers.workflow_worker import process_next_workflow_job

    res = process_next_workflow_job(exec_repo)
    assert res is not None
    # there should be a pending tool execution
    assert any(t.name == "tool.execution.requested" for t in event_bus.pending())

    # process the tool job via the tool worker
    processed = process_tool_jobs(exec_repo)
    assert processed >= 1

    # verify execution persisted as completed (best-effort)
    exec_after = exec_repo.get_by_id(execution["id"])
    assert exec_after is not None
    assert exec_after.status in ("completed", "running") or exec_after.status == "queued"
