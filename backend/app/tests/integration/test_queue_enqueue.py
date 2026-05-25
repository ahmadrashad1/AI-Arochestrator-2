from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator.event_bus import event_bus


def test_workflow_run_enqueues_queue_job() -> None:
	event_bus.clear()
	client = TestClient(app)

	login = client.post("/api/v1/auth/login", json={"email": "admin@acme.ai", "password": "password123"})
	assert login.status_code == 200
	token = login.json()["access_token"]

	workflow = client.post(
		"/api/v1/workflows",
		json={"name": "Queue flow", "description": "desc", "definition": {"steps": []}},
		headers={"Authorization": f"Bearer {token}"},
	)
	assert workflow.status_code == 201

	run = client.post(
		f"/api/v1/automations/{workflow.json()['id']}/run",
		json={"input_payload": {"lead": "queue"}},
		headers={"Authorization": f"Bearer {token}"},
	)
	assert run.status_code == 202
	assert any(task.name == "workflow.execution.requested" for task in event_bus.pending())