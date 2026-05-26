from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from dataclasses import asdict, is_dataclass

from app.core.dependencies import get_current_tenant, require_permission
from app.orchestrator.dependencies import get_workflow_engine
from app.workflows.config import resolve_workflow_config
from shared.dto.workflow_requests import CreateWorkflowRequest
from shared.schemas.workflow import WorkflowConfig as WorkflowConfigOutModel, WorkflowConfigUpdate, WorkflowEditorOut, WorkflowOut

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


def _workflow_editor_out(workflow) -> WorkflowEditorOut:
    config = resolve_workflow_config(json.loads(workflow.definition_json or "{}"))

    def _to_dict(obj):
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return dict(obj.__dict__)

    base = _to_dict(_workflow_out(workflow))
    cfg_dict = _to_dict(config)

    # Validate into the API output model; support multiple pydantic versions
    try:
        cfg_model = WorkflowConfigOutModel.model_validate(cfg_dict)
    except Exception:
        try:
            cfg_model = WorkflowConfigOutModel.parse_obj(cfg_dict)  # type: ignore[attr-defined]
        except Exception:
            cfg_model = WorkflowConfigOutModel(**cfg_dict)  # type: ignore[arg-type]

    return WorkflowEditorOut(**base, config=cfg_model)


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


@router.get(
    "/workflows/{workflow_id}/config",
    response_model=WorkflowEditorOut,
    dependencies=[Depends(require_permission("workflows:read"))],
)
def read_workflow_config(workflow_id: str, current_tenant=Depends(get_current_tenant), workflow_engine=Depends(get_workflow_engine)) -> WorkflowEditorOut:
    workflow = workflow_engine.get_workflow(current_tenant.id, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return _workflow_editor_out(workflow)


@router.put(
    "/workflows/{workflow_id}/config",
    response_model=WorkflowEditorOut,
    dependencies=[Depends(require_permission("workflows:write"))],
)
def update_workflow_config(
    workflow_id: str,
    payload: WorkflowConfigUpdate,
    current_tenant=Depends(get_current_tenant),
    workflow_engine=Depends(get_workflow_engine),
) -> WorkflowEditorOut:
    workflow = workflow_engine.update_workflow_config(current_tenant.id, workflow_id, payload)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return _workflow_editor_out(workflow)