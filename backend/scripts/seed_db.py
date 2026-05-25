from __future__ import annotations

import sys
from pathlib import Path


# Ensure local backend package is importable when running this script directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database.connection import get_engine
from app.database.models.base import Base
from app.database.session import create_session_factory
from app.database.repositories.tenant_repository import TenantRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.workspace_repository import WorkspaceRepository
from app.core.security import hash_password
from app.database.models.tenant import Tenant
from app.database.models.user import User
from app.database.models.workspace import Workspace


def seed():
    engine = get_engine()
    Base.metadata.create_all(engine)

    SessionLocal = create_session_factory()
    session = SessionLocal()

    tenant_repo = TenantRepository(session=session)
    user_repo = UserRepository(session=session)
    workspace_repo = WorkspaceRepository(session=session)

    if tenant_repo.get_by_id("tenant_acme") is None:
        acme = Tenant(id="tenant_acme", name="Acme Labs", plan="starter")
        tenant_repo.create(acme)

    if user_repo.get_by_email("admin@acme.ai") is None:
        admin = User(
            id="user_admin_acme",
            tenant_id="tenant_acme",
            email="admin@acme.ai",
            password_hash=hash_password("password123"),
            role="admin",
            full_name="Acme Admin",
        )
        user_repo.create(admin)

    if workspace_repo.get_by_id("workspace_acme_sales") is None:
        ws = Workspace(id="workspace_acme_sales", tenant_id="tenant_acme", name="Acme Sales")
        workspace_repo.create(ws)

    session.close()


if __name__ == "__main__":
    seed()
    print("DB seeded")
