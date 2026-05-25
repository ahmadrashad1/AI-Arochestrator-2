from __future__ import annotations

from app.state.shared_state import shared_state


class ExecutionState:
	def queue_execution(self, execution_id: str, workflow_id: str, tenant_id: str, idempotency_key: str | None) -> None:
		shared_state.register(execution_id, workflow_id, tenant_id, idempotency_key)

	def mark_running(self, execution_id: str) -> None:
		shared_state.transition(execution_id, "running")

	def mark_completed(self, execution_id: str, output_payload_json: str | None = None) -> None:
		shared_state.transition(execution_id, "completed", output_payload_json=output_payload_json)

	def mark_failed(self, execution_id: str, reason: str) -> None:
		shared_state.transition(execution_id, "failed", last_error=reason)

	def mark_dead_letter(self, execution_id: str, reason: str) -> None:
		shared_state.dead_letter(execution_id, reason)

	def snapshot(self, execution_id: str):
		return shared_state.get(execution_id)


execution_state = ExecutionState()