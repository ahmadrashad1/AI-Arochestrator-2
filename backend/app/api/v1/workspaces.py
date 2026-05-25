from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.logging import audit_log
from app.core.dependencies import get_current_user, require_permission
from app.database.models.workspace import Workspace
from app.database.repositories import get_workspace_repository
from app.tenancy.tenant_limits import can_create_workspace, workspace_limit_for_role

router = APIRouter(tags=["workspaces"])


class WorkspaceOut(BaseModel):
    id: str
    tenant_id: str
    name: str


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.get("/workspaces", response_model=list[WorkspaceOut], dependencies=[Depends(require_permission("workspaces:read"))])
def list_workspaces(current_user=Depends(get_current_user), workspace_repository=Depends(get_workspace_repository)) -> list[WorkspaceOut]:
    workspaces = workspace_repository.list_by_tenant(current_user.tenant_id)
    return [WorkspaceOut(id=workspace.id, tenant_id=workspace.tenant_id, name=workspace.name) for workspace in workspaces]


@router.post("/workspaces", response_model=WorkspaceOut, dependencies=[Depends(require_permission("workspaces:write"))])
def create_workspace(
    payload: CreateWorkspaceRequest,
    request: Request,
    current_user=Depends(get_current_user),
    workspace_repository=Depends(get_workspace_repository),
) -> WorkspaceOut:
    existing_count = workspace_repository.count_by_tenant(current_user.tenant_id)
    limit = workspace_limit_for_role(current_user.role)
    if not can_create_workspace(current_user.role, existing_count):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Workspace limit reached for role {current_user.role} ({existing_count}/{limit})",
        )

    workspace = Workspace(
        id=f"workspace_{uuid4().hex[:12]}",
        tenant_id=current_user.tenant_id,
        name=payload.name,
    )
    workspace_repository.create(workspace)
    audit_log(
        "workspace.create",
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        workspace_id=workspace.id,
        request_id=getattr(request.state, "request_id", None),
    )
    return WorkspaceOut(id=workspace.id, tenant_id=workspace.tenant_id, name=workspace.name)
