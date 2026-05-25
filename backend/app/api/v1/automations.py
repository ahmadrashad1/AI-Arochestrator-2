from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import get_current_tenant, get_idempotency_key, require_execution_quota, require_permission
from app.orchestrator.dependencies import get_workflow_engine
from shared.dto.workflow_requests import RunWorkflowRequest
from shared.schemas.execution import ExecutionOut

router = APIRouter(tags=["automations"])


def _execution_out(execution) -> ExecutionOut:
    return ExecutionOut(
        id=execution.id,
        tenant_id=execution.tenant_id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        input_payload=json.loads(execution.input_payload_json or "{}"),
        output_payload=json.loads(execution.output_payload_json) if execution.output_payload_json else None,
        error_message=execution.error_message,
        retry_count=execution.retry_count,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
    )


@router.post(
    "/automations/{workflow_id}/run",
    response_model=ExecutionOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission("executions:write")), Depends(require_execution_quota)],
)
def run_workflow(
    workflow_id: str,
    payload: RunWorkflowRequest,
    request: Request,
    current_tenant=Depends(get_current_tenant),
    idempotency_key: str | None = Depends(get_idempotency_key),
    workflow_engine=Depends(get_workflow_engine),
) -> ExecutionOut:
    execution = workflow_engine.run_workflow(current_tenant.id, workflow_id, payload, idempotency_key=idempotency_key)
    return _execution_out(execution)