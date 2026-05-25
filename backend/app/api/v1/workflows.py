from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_tenant, require_permission
from app.orchestrator.dependencies import get_workflow_engine
from shared.dto.workflow_requests import CreateWorkflowRequest
from shared.schemas.workflow import WorkflowOut

router = APIRouter(tags=["workflows"])


def _workflow_out(workflow) -> WorkflowOut:
    return WorkflowOut(
        id=workflow.id,
        tenant_id=workflow.tenant_id,
        name=workflow.name,
        description=workflow.description,
        definition=json.loads(workflow.definition_json or "{}"),
        status=workflow.status,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.get("/workflows", response_model=list[WorkflowOut], dependencies=[Depends(require_permission("workflows:read"))])
def list_workflows(current_tenant=Depends(get_current_tenant), workflow_engine=Depends(get_workflow_engine)) -> list[WorkflowOut]:
    return [_workflow_out(workflow) for workflow in workflow_engine.list_workflows(current_tenant.id)]


@router.post(
    "/workflows",
    response_model=WorkflowOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("workflows:write"))],
)
def create_workflow(payload: CreateWorkflowRequest, current_tenant=Depends(get_current_tenant), workflow_engine=Depends(get_workflow_engine)) -> WorkflowOut:
    workflow = workflow_engine.create_workflow(current_tenant.id, payload)
    return _workflow_out(workflow)


@router.get("/workflows/{workflow_id}", response_model=WorkflowOut, dependencies=[Depends(require_permission("workflows:read"))])
def read_workflow(workflow_id: str, current_tenant=Depends(get_current_tenant), workflow_engine=Depends(get_workflow_engine)) -> WorkflowOut:
    workflow = workflow_engine.get_workflow(current_tenant.id, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return _workflow_out(workflow)