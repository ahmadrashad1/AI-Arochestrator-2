from __future__ import annotations

MAX_WORKSPACES_BY_ROLE = {
    "admin": 10,
    "member": 3,
}


def can_create_workspace(role: str, existing_count: int) -> bool:
    return existing_count < MAX_WORKSPACES_BY_ROLE.get(role, 1)


def workspace_limit_for_role(role: str) -> int:
    return MAX_WORKSPACES_BY_ROLE.get(role, 1)
