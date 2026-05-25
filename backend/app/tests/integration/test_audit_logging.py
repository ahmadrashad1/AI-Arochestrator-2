from fastapi.testclient import TestClient

from app.main import app


def test_audit_logs_and_request_id(caplog) -> None:
    client = TestClient(app)

    with caplog.at_level("INFO", logger="audit"):
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@acme.ai", "password": "password123"},
        )
        assert login.status_code == 200
        assert login.headers["x-request-id"]
        assert any("auth.login" in record.message for record in caplog.records)

        token = login.json()["access_token"]
        workspace = client.post(
            "/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Audit Workspace"},
        )
        assert workspace.status_code == 200
        assert workspace.headers["x-request-id"]
        assert any("workspace.create" in record.message for record in caplog.records)
