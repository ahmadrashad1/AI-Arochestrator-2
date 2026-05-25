from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.database.models.execution import Execution
from app.database.repositories.execution_repository import ExecutionRepository
from app.database.repositories.workflow_repository import WorkflowRepository
from app.orchestrator.scheduler import scheduler
from app.orchestrator.workflow_runner import WorkflowRunner
from app.state.execution_state import execution_state
from app.state.workflow_state import workflow_state
from app.tenancy.usage_meter import record_usage


class ExecutionManager:
    def __init__(
        self,
        execution_repository: ExecutionRepository,
        workflow_repository: WorkflowRepository,
        runner: WorkflowRunner | None = None,
    ):
        self.execution_repository = execution_repository
        self.workflow_repository = workflow_repository
        self.runner = runner or WorkflowRunner()

    def submit_execution(
        self,
        tenant_id: str,
        workflow_id: str,
        input_payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> Execution:
        if idempotency_key:
            existing_execution_id = workflow_state.get_execution_by_idempotency_key(tenant_id, idempotency_key)
            if existing_execution_id:
                existing_execution = self.execution_repository.get_by_id(existing_execution_id)
                if existing_execution is not None:
                    return existing_execution

        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None or workflow.tenant_id != tenant_id:
            raise LookupError("Workflow not found")

        execution = Execution(
            id=f"execution_{uuid4().hex[:12]}",
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            status="queued",
            input_payload_json=json.dumps(input_payload, separators=(",", ":")),
            retry_count=0,
            started_at=datetime.now(timezone.utc),
        )
        self.execution_repository.create(execution)
        workflow_state.create_lifecycle(execution.id, workflow_id, tenant_id, idempotency_key, input_payload)
        scheduler.schedule_execution(execution.id, workflow_id, tenant_id, input_payload, idempotency_key)
        execution_state.queue_execution(execution.id, workflow_id, tenant_id, idempotency_key)
        record_usage(tenant_id, "executions", 1)
        return execution

    def refresh_execution(self, execution_id: str) -> Execution | None:
        execution = self.execution_repository.get_by_id(execution_id)
        lifecycle = workflow_state.get_lifecycle(execution_id)
        if execution is None or lifecycle is None:
            return execution

        now = datetime.now(timezone.utc)
        if now >= lifecycle.completed_at and execution.status != "completed":
            execution.status = "completed"
            execution.output_payload_json = json.dumps(lifecycle.output_payload, separators=(",", ":"))
            execution.completed_at = now
            workflow_state.append_history(execution_id, "completed", 100, "Execution completed")
            self.execution_repository.update(execution)
            return execution

        if now >= lifecycle.running_at and execution.status == "queued":
            execution.status = "running"
            workflow_state.append_history(execution_id, "running", 50, "Execution running")
            self.execution_repository.update(execution)
            return execution

        return execution

    def get_execution_history(self, execution_id: str) -> list[dict[str, Any]]:
        self.refresh_execution(execution_id)
        return workflow_state.current_history(execution_id)

    def get_execution(self, execution_id: str) -> Execution | None:
        return self.refresh_execution(execution_id)

