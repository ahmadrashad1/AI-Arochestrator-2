from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.execution import Execution
from app.database.repositories.base import InMemoryStore, store as default_store


class ExecutionRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def get_by_id(self, execution_id: str) -> Execution | None:
        session = self._session
        if session is not None:
            return session.get(Execution, execution_id)
        return self._store.__dict__.setdefault("executions", {}).get(execution_id)

    def list_by_tenant(self, tenant_id: str) -> list[Execution]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(Execution).where(Execution.tenant_id == tenant_id)).all())
        return [execution for execution in self._store.__dict__.setdefault("executions", {}).values() if execution.tenant_id == tenant_id]

    def list_by_workflow(self, workflow_id: str) -> list[Execution]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(Execution).where(Execution.workflow_id == workflow_id)).all())
        return [execution for execution in self._store.__dict__.setdefault("executions", {}).values() if execution.workflow_id == workflow_id]

    def create(self, execution: Execution) -> Execution:
        session = self._session
        if session is not None:
            session.add(execution)
            session.commit()
            session.refresh(execution)
            return execution
        self._store.__dict__.setdefault("executions", {})[execution.id] = execution
        return execution

    def update(self, execution: Execution) -> Execution:
        session = self._session
        if session is not None:
            merged = session.merge(execution)
            session.commit()
            session.refresh(merged)
            return merged
        self._store.__dict__.setdefault("executions", {})[execution.id] = execution
        return execution

    def delete(self, execution_id: str) -> None:
        session = self._session
        if session is not None:
            execution = session.get(Execution, execution_id)
            if execution is not None:
                session.delete(execution)
                session.commit()
            return
        self._store.__dict__.setdefault("executions", {}).pop(execution_id, None)
