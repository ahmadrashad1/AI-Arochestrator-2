from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, require_permission
from app.database.repositories import get_user_repository

router = APIRouter(tags=["users"])


class UserOut(BaseModel):
    id: str
    tenant_id: str
    email: str
    role: str
    full_name: str


@router.get("/users/me", response_model=UserOut)
def read_me(current_user=Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        role=current_user.role,
        full_name=current_user.full_name,
    )


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_permission("users:read"))])
def list_users(current_user=Depends(get_current_user), user_repository=Depends(get_user_repository)) -> list[UserOut]:
    users = user_repository.list_by_tenant(current_user.tenant_id)
    return [
        UserOut(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        )
        for user in users
    ]
