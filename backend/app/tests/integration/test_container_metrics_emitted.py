from __future__ import annotations

from fastapi.testclient import TestClient
import shutil
import pytest

from app.main import app


def test_container_invocation_emits_metrics():
    if shutil.which("docker") is None:
        pytest.skip("docker not available in test environment")
    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
    assert login.status_code == 200
    admin_token = login.json()["access_token"]

    # trigger the container-based tool via admin endpoint
    payload = {"tool_name": "echo", "payload": {"ci": "ok"}, "sandbox": "container", "timeout_seconds": 30}
    r = client.post("/api/v1/admin/run_tool", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # scrape metrics and ensure tool_executions_total line exists
    m = client.get("/metrics")
    assert m.status_code == 200
    text = m.text
    assert "tool_executions_total" in text
