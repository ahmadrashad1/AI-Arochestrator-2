from fastapi.testclient import TestClient

from app.main import app


def test_workspace_limit_enforced() -> None:
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.ai", "password": "password123"},
    )
    token = login.json()["access_token"]

    for index in range(9):
        response = client.post(
            "/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"Workspace {index}"},
        )
        assert response.status_code == 200

    blocked = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Workspace 10"},
    )
    assert blocked.status_code == 403
