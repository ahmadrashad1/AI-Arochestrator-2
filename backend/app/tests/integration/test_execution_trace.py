from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.database.repositories import get_execution_repository
from app.main import app
from app.orchestrator.event_bus import event_bus
from app.tenancy.usage_meter import reset_usage
from app.workers.workflow_worker import process_next_workflow_job


def test_execution_trace_is_persisted_with_vertical_output() -> None:
    event_bus.clear()
    reset_usage()
    client = TestClient(app)

    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    workflow = client.post(
        "/api/v1/workflows",
        json={"name": "Lead gen trace", "description": "trace", "definition": {"graph_name": "lead_generation"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workflow.status_code == 201

    run = client.post(
        f"/api/v1/automations/{workflow.json()['id']}/run",
        json={
            "input_payload": {
                "graph_name": "lead_generation",
                "goal": "identify and contact qualified leads",
                "company": "Acme Labs",
                "prospect_name": "Taylor",
                "email": "taylor@example.com",
                "research_query": "Acme Labs B2B growth",
                "website": "https://example.com/acme",
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run.status_code == 202

    execution_repo = get_execution_repository()
    process_next_workflow_job(execution_repo)

    execution_record = execution_repo.get_by_id(run.json()["id"])
    assert execution_record is not None
    output = json.loads(execution_record.output_payload_json or "{}")
    assert output["trace"]
    assert any(entry.get("node") == "planning" for entry in output["trace"])
    assert output["lead_score"] >= 70
    assert output["email_result"]["status"] == "queued"
