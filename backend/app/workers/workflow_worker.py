from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from app.orchestrator.scheduler import scheduler
from app.orchestrator.retry_manager import retry_manager
from app.orchestrator.workflow_runner import WorkflowRunner
from app.orchestrator.event_bus import event_bus
from app.state.execution_state import execution_state
from app.state.shared_state import shared_state
from app.database.repositories.execution_repository import ExecutionRepository


def process_next_workflow_job(execution_repository: ExecutionRepository, runner: WorkflowRunner | None = None) -> dict[str, Any] | None:
	task = scheduler.next_execution_task()
	if task is None:
		return None

	payload = task.payload
	execution_id = payload.get("execution_id")
	try:
		# mark running in shared state and persist started_at if possible
		shared_state.transition(execution_id, "running")
		execution_state.mark_running(execution_id)
		try:
			execution = execution_repository.get_by_id(execution_id)
			if execution is not None:
				execution.status = "running"
				execution.started_at = datetime.now(timezone.utc)
				execution_repository.update(execution)
		except Exception:
			execution = None

		# perform the work
		runner = runner or WorkflowRunner()
		plan = runner.build_execution_plan(
			payload.get("workflow_id"),
			execution_id,
			payload.get("input_payload"),
			payload.get("workflow_definition"),
		)
		output = plan.get("output_payload")
		status = output.get("status") if isinstance(output, dict) else "completed"

		# mark state based on the graph result and persist outputs
		if status == "paused":
			execution_state.mark_running(execution_id)
			shared_state.transition(execution_id, "paused")
		elif status == "failed":
			execution_state.mark_failed(execution_id, str(output.get("error") if isinstance(output, dict) else "graph failed"))
			shared_state.transition(execution_id, "failed")
		else:
			execution_state.mark_completed(execution_id)
			shared_state.transition(execution_id, "completed")
		try:
			if execution is None:
				execution = execution_repository.get_by_id(execution_id)
			if execution is not None:
				import json as _json

				execution.status = status if status in {"paused", "failed", "completed"} else "completed"
				execution.output_payload_json = _json.dumps(output)
				execution.completed_at = datetime.now(timezone.utc)
				execution_repository.update(execution)
		except Exception:
			# best-effort; do not crash worker on persistence failures
			pass
		# acknowledge the task so it is removed from processing set
		try:
			event_bus.ack(task)
		except Exception:
			pass

		return {"task_id": task.id, "execution_id": execution_id}
	except Exception as exc:
		# handle retries and persist error + retry count
		attempts = task.attempts + 1
		try:
			execution = execution_repository.get_by_id(execution_id)
			if execution is not None:
				execution.retry_count = (execution.retry_count or 0) + 1
				execution.error_message = str(exc)
				execution_repository.update(execution)
		except Exception:
			pass

		if retry_manager.can_retry(attempts):
			delay = retry_manager.next_delay_seconds(attempts)
			event_bus.requeue(task, delay)
			shared_state.transition(execution_id, "retrying", attempts=attempts, last_error=str(exc))
		else:
			event_bus.dead_letter(task, str(exc))
			shared_state.dead_letter(execution_id, str(exc))

		return {"task_id": task.id, "error": str(exc)}