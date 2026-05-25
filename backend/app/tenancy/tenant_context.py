from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    workspace_id: str | None = None


def build_tenant_context(tenant_id: str, workspace_id: str | None = None) -> TenantContext:
    return TenantContext(tenant_id=tenant_id, workspace_id=workspace_id)
