from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.workflow import Workflow
from app.database.repositories.base import InMemoryStore, store as default_store


class WorkflowRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def get_by_id(self, workflow_id: str) -> Workflow | None:
        session = self._session
        if session is not None:
            return session.get(Workflow, workflow_id)
        return self._store.__dict__.setdefault("workflows", {}).get(workflow_id)

    def list_by_tenant(self, tenant_id: str) -> list[Workflow]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(Workflow).where(Workflow.tenant_id == tenant_id)).all())
        return [workflow for workflow in self._store.__dict__.setdefault("workflows", {}).values() if workflow.tenant_id == tenant_id]

    def create(self, workflow: Workflow) -> Workflow:
        session = self._session
        if session is not None:
            session.add(workflow)
            session.commit()
            session.refresh(workflow)
            return workflow
        self._store.__dict__.setdefault("workflows", {})[workflow.id] = workflow
        return workflow

    def update(self, workflow: Workflow) -> Workflow:
        session = self._session
        if session is not None:
            merged = session.merge(workflow)
            session.commit()
            session.refresh(merged)
            return merged
        self._store.__dict__.setdefault("workflows", {})[workflow.id] = workflow
        return workflow

    def delete(self, workflow_id: str) -> None:
        session = self._session
        if session is not None:
            workflow = session.get(Workflow, workflow_id)
            if workflow is not None:
                session.delete(workflow)
                session.commit()
            return
        self._store.__dict__.setdefault("workflows", {}).pop(workflow_id, None)
