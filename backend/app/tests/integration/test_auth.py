from fastapi.testclient import TestClient

from app.main import app


def test_login_and_me() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.ai", "password": "password123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "admin@acme.ai"

    token = payload["access_token"]
    me_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "admin@acme.ai"
