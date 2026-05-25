from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.workspace import Workspace
from app.database.repositories.base import InMemoryStore, store as default_store


class WorkspaceRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        session = self._session
        if session is not None:
            return session.get(Workspace, workspace_id)
        return self._store.workspaces.get(workspace_id)

    def list_by_tenant(self, tenant_id: str) -> list[Workspace]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(Workspace).where(Workspace.tenant_id == tenant_id)).all())
        return [workspace for workspace in self._store.workspaces.values() if workspace.tenant_id == tenant_id]

    def count_by_tenant(self, tenant_id: str) -> int:
        return len(self.list_by_tenant(tenant_id))

    def create(self, workspace: Workspace) -> Workspace:
        session = self._session
        if session is not None:
            session.add(workspace)
            session.commit()
            session.refresh(workspace)
            return workspace
        self._store.workspaces[workspace.id] = workspace
        return workspace

    def update(self, workspace: Workspace) -> Workspace:
        session = self._session
        if session is not None:
            merged = session.merge(workspace)
            session.commit()
            session.refresh(merged)
            return merged
        self._store.workspaces[workspace.id] = workspace
        return workspace

    def delete(self, workspace_id: str) -> None:
        session = self._session
        if session is not None:
            workspace = session.get(Workspace, workspace_id)
            if workspace is not None:
                session.delete(workspace)
                session.commit()
            return
        self._store.workspaces.pop(workspace_id, None)
