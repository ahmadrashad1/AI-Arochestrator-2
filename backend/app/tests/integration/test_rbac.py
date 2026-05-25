from fastapi.testclient import TestClient

from app.main import app


def test_role_permissions() -> None:
    client = TestClient(app)

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.ai", "password": "password123"},
    )
    admin_token = admin_login.json()["access_token"]

    member_login = client.post(
        "/api/v1/auth/login",
        json={"email": "member@acme.ai", "password": "password123"},
    )
    member_token = member_login.json()["access_token"]

    admin_users = client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_users.status_code == 200
    assert len(admin_users.json()) == 2

    member_users = client.get("/api/v1/users", headers={"Authorization": f"Bearer {member_token}"})
    assert member_users.status_code == 403
