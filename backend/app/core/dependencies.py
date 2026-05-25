from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import parse_access_token
from app.auth.rbac import has_permission
from app.database.repositories import get_tenant_repository, get_user_repository, get_workspace_repository
from app.billing.quota_manager import ensure_execution_quota

bearer_scheme = HTTPBearer(auto_error=False)


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def get_idempotency_key(request: Request) -> str | None:
    key = request.headers.get("X-Idempotency-Key")
    if key is None:
        return None
    normalized = key.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Idempotency-Key cannot be empty")
    if len(normalized) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Idempotency-Key is too long")
    return normalized


def get_principal_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return credentials.credentials


def get_current_principal(token: Annotated[str, Depends(get_principal_token)]):
    try:
        return parse_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def get_current_user(principal=Depends(get_current_principal), user_repository=Depends(get_user_repository)):
    user = user_repository.get_by_id(principal.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def get_current_tenant(principal=Depends(get_current_principal), tenant_repository=Depends(get_tenant_repository)):
    tenant = tenant_repository.get_by_id(principal.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant no longer exists")
    return tenant


def get_request_tenant_id(principal=Depends(get_current_principal)) -> str:
    return principal.tenant_id


def require_permission(permission: str) -> Callable:
    def _dependency(principal=Depends(get_current_principal)):
        if not has_permission(principal.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return principal

    return _dependency


def get_tenant_workspaces(principal=Depends(get_current_principal), workspace_repository=Depends(get_workspace_repository)):
    return workspace_repository.list_by_tenant(principal.tenant_id)


def require_execution_quota(current_tenant=Depends(get_current_tenant)):
    ensure_execution_quota(current_tenant.id, current_tenant.plan)
    return current_tenant
