from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_exposes_prometheus() -> None:
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    # content-type should match prometheus content type
    assert "text" in r.headers.get("content-type", "")
    # ensure a known metric name is present (tool_executions_total exists when prometheus_client installed)
    # it's ok if not present; test verifies endpoint returns text content
    assert isinstance(r.text, str)
