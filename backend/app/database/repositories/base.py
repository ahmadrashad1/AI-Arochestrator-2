from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from app.core.security import hash_password
from app.database.models.tenant import Tenant
from app.database.models.user import User
from app.database.models.workspace import Workspace


@dataclass
class InMemoryStore:
    tenants: Dict[str, Tenant] = field(default_factory=dict)
    users: Dict[str, User] = field(default_factory=dict)
    workspaces: Dict[str, Workspace] = field(default_factory=dict)
    workflows: Dict[str, object] = field(default_factory=dict)
    executions: Dict[str, object] = field(default_factory=dict)
    usage_records: Dict[str, object] = field(default_factory=dict)


def _build_store() -> InMemoryStore:
    store = InMemoryStore()
    _seed_store(store)
    return store


def _seed_store(store: InMemoryStore) -> None:

    acme = Tenant(id="tenant_acme", name="Acme Labs", plan="starter")
    orbit = Tenant(id="tenant_orbit", name="Orbit Systems", plan="starter")
    store.tenants[acme.id] = acme
    store.tenants[orbit.id] = orbit

    store.users["user_admin_acme"] = User(
        id="user_admin_acme",
        tenant_id=acme.id,
        email="admin@acme.ai",
        password_hash=hash_password("password123"),
        role="admin",
        full_name="Acme Admin",
    )
    store.users["user_member_acme"] = User(
        id="user_member_acme",
        tenant_id=acme.id,
        email="member@acme.ai",
        password_hash=hash_password("password123"),
        role="member",
        full_name="Acme Member",
    )
    store.users["user_admin_orbit"] = User(
        id="user_admin_orbit",
        tenant_id=orbit.id,
        email="admin@orbit.ai",
        password_hash=hash_password("password123"),
        role="admin",
        full_name="Orbit Admin",
    )

    store.workspaces["workspace_acme_sales"] = Workspace(
        id="workspace_acme_sales",
        tenant_id=acme.id,
        name="Acme Sales",
    )
    store.workspaces["workspace_orbit_sales"] = Workspace(
        id="workspace_orbit_sales",
        tenant_id=orbit.id,
        name="Orbit Sales",
    )


def reset_store() -> None:
    store.tenants.clear()
    store.users.clear()
    store.workspaces.clear()
    store.workflows.clear()
    store.executions.clear()
    store.usage_records.clear()
    _seed_store(store)


store = _build_store()
