from __future__ import annotations

import json
from typing import Any, Iterable

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_tenant, require_permission
from app.orchestrator.dependencies import get_execution_manager
from shared.schemas.execution import ExecutionOut, ExecutionProgressOut, ExecutionStatusOut
from app.observability.llm_usage import get_usage_for_execution

router = APIRouter(tags=["executions"])


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


def _status_out(execution, execution_manager) -> ExecutionStatusOut:
    history = [ExecutionProgressOut(**entry) for entry in execution_manager.get_execution_history(execution.id)]
    latest = history[-1] if history else ExecutionProgressOut(status=execution.status, progress=0, message="Execution queued")
    progress = latest.progress if history else 0
    return ExecutionStatusOut(execution=_execution_out(execution), progress=progress, message=latest.message, history=history)


@router.get("/executions/{execution_id}", response_model=ExecutionStatusOut, dependencies=[Depends(require_permission("executions:read"))])
def get_execution_status(execution_id: str, current_tenant=Depends(get_current_tenant), execution_manager=Depends(get_execution_manager)) -> ExecutionStatusOut:
    execution = execution_manager.get_execution(execution_id)
    if execution is None or execution.tenant_id != current_tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return _status_out(execution, execution_manager)


@router.get("/executions/{execution_id}/trace", dependencies=[Depends(require_permission("executions:read"))])
def get_execution_trace(execution_id: str, current_tenant=Depends(get_current_tenant), execution_manager=Depends(get_execution_manager)) -> dict:
    execution = execution_manager.get_execution(execution_id)
    if execution is None or execution.tenant_id != current_tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    output = json.loads(execution.output_payload_json) if execution.output_payload_json else {}
    return {"execution_id": execution.id, "trace": output.get("trace", [])}


@router.get("/executions/{execution_id}/timeline", dependencies=[Depends(require_permission("executions:read"))])
def get_execution_timeline(execution_id: str, current_tenant=Depends(get_current_tenant), execution_manager=Depends(get_execution_manager)) -> dict:
    execution = execution_manager.get_execution(execution_id)
    if execution is None or execution.tenant_id != current_tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    history = [ExecutionProgressOut(**entry) for entry in execution_manager.get_execution_history(execution.id)]
    output = json.loads(execution.output_payload_json) if execution.output_payload_json else {}
    trace = output.get("trace", [])
    return {"execution": _execution_out(execution), "history": [h.model_dump() for h in history], "trace": trace}


@router.get("/executions/{execution_id}/cost", dependencies=[Depends(require_permission("executions:read"))])
def get_execution_cost(execution_id: str, current_tenant=Depends(get_current_tenant), execution_manager=Depends(get_execution_manager)) -> dict:
    execution = execution_manager.get_execution(execution_id)
    if execution is None or execution.tenant_id != current_tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    # Return cost info from in-memory llm usage tracker and any output payload cost info
    usage = get_usage_for_execution(execution.id)
    output = json.loads(execution.output_payload_json) if execution.output_payload_json else {}
    return {"execution_id": execution.id, "llm_usage": usage, "output_cost_summary": output.get("cost_summary")}


@router.get("/executions/{execution_id}/events", dependencies=[Depends(require_permission("executions:read"))])
def stream_execution_status(execution_id: str, current_tenant=Depends(get_current_tenant), execution_manager=Depends(get_execution_manager)) -> StreamingResponse:
    execution = execution_manager.get_execution(execution_id)
    if execution is None or execution.tenant_id != current_tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    def event_stream() -> Iterable[str]:
        status_payload = _status_out(execution, execution_manager)
        yield f"data: {status_payload.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")