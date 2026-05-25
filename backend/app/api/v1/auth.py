from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.auth.jwt import issue_access_token
from app.core.logging import audit_log
from app.core.security import AuthPrincipal
from app.database.repositories import get_tenant_repository, get_user_repository

router = APIRouter(tags=["auth"])
class UserOut(BaseModel):
    id: str
    tenant_id: str
    email: str
    role: str
    full_name: str


class TenantOut(BaseModel):
    id: str
    name: str
    plan: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    tenant: TenantOut


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: dict[str, str] = Body(...),
    user_repository=Depends(get_user_repository),
    tenant_repository=Depends(get_tenant_repository),
) -> LoginResponse:
    email = payload.get("email", "")
    password = payload.get("password", "")
    user = user_repository.authenticate(email, password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tenant = tenant_repository.get_by_id(user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant not found")

    principal = AuthPrincipal(user_id=user.id, tenant_id=user.tenant_id, email=user.email, role=user.role)
    token = issue_access_token(principal)
    audit_log("auth.login", user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        ),
        tenant=TenantOut(id=tenant.id, name=tenant.name, plan=tenant.plan),
    )
