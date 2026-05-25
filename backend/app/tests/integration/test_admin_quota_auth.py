from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_admin_quota_protected():
    client = TestClient(app)
    # unauthenticated
    r = client.get("/api/v1/admin/quotas")
    assert r.status_code == 401

    # non-admin token from the real login route
    member_login = client.post("/api/v1/auth/login", json={"email": "member@acme.ai", "password": "password123"})
    assert member_login.status_code == 200
    token = member_login.json()["access_token"]
    r = client.get("/api/v1/admin/quotas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

    # admin token from the real login route can set and list quotas
    admin_login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    r = client.post("/api/v1/admin/quotas/foo", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    r = client.get("/api/v1/admin/quotas", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
