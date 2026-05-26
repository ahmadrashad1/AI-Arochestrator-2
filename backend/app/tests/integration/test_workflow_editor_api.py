from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_workflow_editor_can_read_and_update_config() -> None:
    client = TestClient(app)

    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    workflow = client.post(
        "/api/v1/workflows",
        json={"name": "Editor flow", "description": "configurable", "definition": {"workflow_type": "automation", "steps": ["planner", "validator", "executor"], "tools": ["browser.search"]}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workflow.status_code == 201
    workflow_id = workflow.json()["id"]

    config_response = client.get(f"/api/v1/workflows/{workflow_id}/config", headers={"Authorization": f"Bearer {token}"})
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["config"]["workflow_type"] == "automation"
    assert config_payload["config"]["steps"] == ["planner", "validator", "executor"]

    update_response = client.put(
        f"/api/v1/workflows/{workflow_id}/config",
        json={
            "workflow_type": "support",
            "graph_name": "support",
            "steps": ["planner", "retriever", "validator", "executor"],
            "tools": ["browser.search", "communication.slack"],
            "metadata": {"owner": "ops-team"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["config"]["workflow_type"] == "support"
    assert updated_payload["config"]["graph_name"] == "support"
    assert updated_payload["config"]["steps"] == ["planner", "retriever", "validator", "executor"]
    assert updated_payload["config"]["metadata"]["owner"] == "ops-team"

    run_response = client.post(
        f"/api/v1/automations/{workflow_id}/run",
        json={"input_payload": {"knowledge_query": "refund policy", "graph_name": "support"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run_response.status_code == 202
    assert run_response.json()["workflow_id"] == workflow_id
