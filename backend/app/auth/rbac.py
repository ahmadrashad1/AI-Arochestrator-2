from __future__ import annotations

from dataclasses import dataclass


ADMIN_ROLE = "admin"
MEMBER_ROLE = "member"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    ADMIN_ROLE: {
        "users:read",
        "tenants:read",
        "workspaces:read",
        "workspaces:write",
        "workflows:read",
        "workflows:write",
        "executions:read",
        "executions:write",
        "admin:quotas",
        "auth:login",
    },
    MEMBER_ROLE: {
        "tenants:read",
        "workspaces:read",
        "workflows:read",
        "executions:read",
        "auth:login",
    },
}


@dataclass(frozen=True)
class RoleDecision:
    role: str
    permission: str
    allowed: bool


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def permission_decision(role: str, permission: str) -> RoleDecision:
    return RoleDecision(role=role, permission=permission, allowed=has_permission(role, permission))
