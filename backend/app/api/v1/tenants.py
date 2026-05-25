from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_tenant

router = APIRouter(tags=["tenants"])


class TenantOut(BaseModel):
    id: str
    name: str
    plan: str


@router.get("/tenants/current", response_model=TenantOut)
def current_tenant(tenant=Depends(get_current_tenant)) -> TenantOut:
    return TenantOut(id=tenant.id, name=tenant.name, plan=tenant.plan)
