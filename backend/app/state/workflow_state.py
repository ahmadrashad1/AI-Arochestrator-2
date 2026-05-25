from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any


@dataclass
class ExecutionLifecycle:
    execution_id: str
    workflow_id: str
    tenant_id: str
    idempotency_key: str | None
    queued_at: datetime
    running_at: datetime
    completed_at: datetime
    output_payload: dict[str, Any]
    history: list[dict[str, Any]] = field(default_factory=list)


class WorkflowState:
    def __init__(self) -> None:
        self._lock = RLock()
        self._lifecycle_by_execution_id: dict[str, ExecutionLifecycle] = {}
        self._execution_by_idempotency_key: dict[tuple[str, str], str] = {}

    def reset(self) -> None:
        with self._lock:
            self._lifecycle_by_execution_id.clear()
            self._execution_by_idempotency_key.clear()

    def create_lifecycle(
        self,
        execution_id: str,
        workflow_id: str,
        tenant_id: str,
        idempotency_key: str | None,
        input_payload: dict[str, Any],
    ) -> ExecutionLifecycle:
        queued_at = datetime.now(timezone.utc)
        lifecycle = ExecutionLifecycle(
            execution_id=execution_id,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            queued_at=queued_at,
            running_at=queued_at + timedelta(milliseconds=75),
            completed_at=queued_at + timedelta(milliseconds=175),
            output_payload={
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "status": "completed",
                "input_payload": input_payload,
            },
            history=[
                {
                    "status": "queued",
                    "progress": 0,
                    "message": "Execution accepted",
                    "recorded_at": queued_at,
                }
            ],
        )
        with self._lock:
            self._lifecycle_by_execution_id[execution_id] = lifecycle
            if idempotency_key:
                self._execution_by_idempotency_key[(tenant_id, idempotency_key)] = execution_id
        return lifecycle

    def get_lifecycle(self, execution_id: str) -> ExecutionLifecycle | None:
        with self._lock:
            return self._lifecycle_by_execution_id.get(execution_id)

    def get_execution_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> str | None:
        with self._lock:
            return self._execution_by_idempotency_key.get((tenant_id, idempotency_key))

    def append_history(self, execution_id: str, status: str, progress: int, message: str) -> None:
        with self._lock:
            lifecycle = self._lifecycle_by_execution_id.get(execution_id)
            if lifecycle is None:
                return
            lifecycle.history.append(
                {
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "recorded_at": datetime.now(timezone.utc),
                }
            )

    def current_history(self, execution_id: str) -> list[dict[str, Any]]:
        with self._lock:
            lifecycle = self._lifecycle_by_execution_id.get(execution_id)
            return [] if lifecycle is None else list(lifecycle.history)

    def snapshot(self, execution_id: str) -> dict[str, Any] | None:
        with self._lock:
            lifecycle = self._lifecycle_by_execution_id.get(execution_id)
            if lifecycle is None:
                return None
            return {
                "execution_id": lifecycle.execution_id,
                "workflow_id": lifecycle.workflow_id,
                "tenant_id": lifecycle.tenant_id,
                "idempotency_key": lifecycle.idempotency_key,
                "queued_at": lifecycle.queued_at,
                "running_at": lifecycle.running_at,
                "completed_at": lifecycle.completed_at,
                "output_payload": lifecycle.output_payload,
                "history": list(lifecycle.history),
            }


workflow_state = WorkflowState()