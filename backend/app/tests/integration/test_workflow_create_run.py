from fastapi.testclient import TestClient

from app.main import app
from app.tenancy.usage_meter import reset_usage


def test_create_and_run_workflow():
    client = TestClient(app)
    reset_usage()

    # login as admin
    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    # create workflow
    create = client.post(
        "/api/v1/workflows",
        json={"name": "Test flow", "description": "desc", "definition": {"steps": []}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201
    workflow = create.json()

    # run workflow
    run = client.post(
        f"/api/v1/automations/{workflow['id']}/run",
        json={"input_payload": {"lead": "test"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run.status_code == 202
    execution = run.json()
    assert execution["workflow_id"] == workflow["id"]

    # check status
    status = client.get(f"/api/v1/executions/{execution['id']}", headers={"Authorization": f"Bearer {token}"})
    assert status.status_code == 200
    payload = status.json()
    assert payload["execution"]["id"] == execution["id"]
