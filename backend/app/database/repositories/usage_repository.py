from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.usage import Usage
from app.database.repositories.base import InMemoryStore, store as default_store


class UsageRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def create(self, usage: Usage) -> Usage:
        session = self._session
        if session is not None:
            session.add(usage)
            session.commit()
            session.refresh(usage)
            return usage
        self._store.__dict__.setdefault("usage_records", {})[usage.id] = usage
        return usage

    def list_by_tenant(self, tenant_id: str) -> list[Usage]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(Usage).where(Usage.tenant_id == tenant_id)).all())
        return [usage for usage in self._store.__dict__.setdefault("usage_records", {}).values() if usage.tenant_id == tenant_id]
