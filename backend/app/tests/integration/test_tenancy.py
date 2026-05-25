from fastapi.testclient import TestClient

from app.main import app


def test_tenant_scoped_workspaces() -> None:
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.ai", "password": "password123"},
    )
    token = login.json()["access_token"]

    tenant_response = client.get("/api/v1/tenants/current", headers={"Authorization": f"Bearer {token}"})
    assert tenant_response.status_code == 200
    assert tenant_response.json()["id"] == "tenant_acme"

    workspaces_response = client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert workspaces_response.status_code == 200
    workspaces = workspaces_response.json()
    assert len(workspaces) == 1
    assert workspaces[0]["tenant_id"] == "tenant_acme"
