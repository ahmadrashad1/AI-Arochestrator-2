from __future__ import annotations

from typing import Any

from app.orchestrator.event_bus import event_bus


class Scheduler:
	def schedule_execution(
		self,
		execution_id: str,
		workflow_id: str,
		tenant_id: str,
		input_payload: dict[str, Any],
		idempotency_key: str | None = None,
	) -> str:
		task = event_bus.publish(
			"workflow.execution.requested",
			{
				"execution_id": execution_id,
				"workflow_id": workflow_id,
				"tenant_id": tenant_id,
				"input_payload": input_payload,
				"idempotency_key": idempotency_key,
			},
		)
		return task.id

	def next_execution_task(self):
		return event_bus.claim_ready("workflow.execution.requested")

	def pending_executions(self):
		return [task for task in event_bus.pending() if task.name == "workflow.execution.requested"]


scheduler = Scheduler()


def requeue_stuck_executions(name: str | None = None, timeout_seconds: int = 60) -> int:
	"""Convenience helper: ask the event bus to requeue stuck processing tasks."""
	return event_bus.requeue_stuck(name=name, timeout_seconds=timeout_seconds)