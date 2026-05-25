from __future__ import annotations

from app.database.repositories import get_execution_repository
from app.orchestrator.event_bus import event_bus
from app.orchestrator.retry_manager import retry_manager
from app.workers.workflow_worker import process_next_workflow_job


def next_retry_delay(attempt_number: int) -> int:
	return retry_manager.next_delay_seconds(attempt_number)


def process_retry_jobs() -> int:
	"""Process any workflow jobs that became ready after a retry delay."""
	processed = 0
	execution_repository = get_execution_repository()
	while True:
		task = event_bus.claim_ready("workflow.execution.requested")
		if task is None:
			return processed
		event_bus.requeue(task, 0)
		if process_next_workflow_job(execution_repository) is not None:
			processed += 1