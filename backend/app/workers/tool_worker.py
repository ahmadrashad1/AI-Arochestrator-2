from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.database.repositories.execution_repository import ExecutionRepository
from app.orchestrator.event_bus import event_bus
from app.orchestrator.retry_manager import retry_manager
from app.orchestrator.workflow_runner import WorkflowRunner
from app.state.execution_state import execution_state
from app.state.shared_state import shared_state
from app.tools.registry import run_tool

def process_tool_jobs(execution_repository: ExecutionRepository | None = None, runner: WorkflowRunner | None = None) -> int:
	processed = 0
	while True:
		task = event_bus.claim_ready("tool.execution.requested")
		if task is None:
			return processed

		payload = task.payload
		execution_id = payload.get("execution_id")
		try:
			if execution_id is not None:
				shared_state.transition(execution_id, "running")
				execution_state.mark_running(execution_id)
				if execution_repository is not None:
					try:
						execution = execution_repository.get_by_id(execution_id)
						if execution is not None:
							execution.status = "running"
							execution.started_at = datetime.now(timezone.utc)
							execution_repository.update(execution)
					except Exception:
						pass

			result: Any
			if runner is not None:
				for method_name in ("run_tool", "execute_tool", "process_tool", "process"):
					method = getattr(runner, method_name, None)
					if callable(method):
						result = method(payload)
						break
				else:
					result = payload.get("input_payload", payload)
			else:
				# try tool registry by tool_name when available
				try:
					tool_name = payload.get("tool_name") if isinstance(payload, dict) else None
					input_payload = payload.get("input_payload") if isinstance(payload, dict) else payload
					if tool_name:
						result = run_tool(tool_name, input_payload)
					else:
						result = input_payload
				except Exception:
					result = payload.get("input_payload", payload)

			if execution_id is not None:
				execution_state.mark_completed(execution_id)
				shared_state.transition(execution_id, "completed")
				if execution_repository is not None:
					try:
						execution = execution_repository.get_by_id(execution_id)
						if execution is not None:
							import json as _json

							execution.status = "completed"
							execution.output_payload_json = _json.dumps(result)
							execution.completed_at = datetime.now(timezone.utc)
							execution_repository.update(execution)
					except Exception:
						pass

			event_bus.ack(task)
			processed += 1
		except Exception as exc:
			attempts = task.attempts + 1
			if execution_id is not None:
				try:
					if execution_repository is not None:
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
				if execution_id is not None:
					shared_state.transition(execution_id, "retrying", attempts=attempts, last_error=str(exc))
			else:
				event_bus.dead_letter(task, str(exc))
				if execution_id is not None:
					shared_state.dead_letter(execution_id, str(exc))
