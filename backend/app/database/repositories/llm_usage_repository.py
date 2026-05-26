from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List

from app.database.models.usage import LLMUsage
from app.database.repositories.base import InMemoryStore, store as default_store


class LLMUsageRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def create(self, usage: LLMUsage) -> LLMUsage:
        session = self._session
        if session is not None:
            session.add(usage)
            session.commit()
            session.refresh(usage)
            return usage
        self._store.__dict__.setdefault("llm_usage", {})[usage.id] = usage
        return usage

    def list_by_execution(self, execution_id: str) -> List[LLMUsage]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(LLMUsage).where(LLMUsage.execution_id == execution_id)).all())
        return [u for u in self._store.__dict__.setdefault("llm_usage", {}).values() if u.execution_id == execution_id]
