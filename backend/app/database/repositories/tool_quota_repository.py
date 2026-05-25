from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.tool_quota import ToolQuota
from app.database.repositories.base import InMemoryStore, store as default_store


class ToolQuotaRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def get_by_tool_name(self, tool_name: str) -> ToolQuota | None:
        session = self._session
        if session is not None:
            return session.get(ToolQuota, tool_name)
        return self._store.__dict__.setdefault("tool_quotas", {}).get(tool_name)

    def list_all(self) -> list[ToolQuota]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(ToolQuota)).all())
        return list(self._store.__dict__.setdefault("tool_quotas", {}).values())

    def upsert(self, quota: ToolQuota) -> ToolQuota:
        session = self._session
        if session is not None:
            merged = session.merge(quota)
            session.commit()
            session.refresh(merged)
            return merged
        self._store.__dict__.setdefault("tool_quotas", {})[quota.tool_name] = quota
        return quota

    def increment_usage(self, tool_name: str, executions: int = 1, cpu_seconds: float | None = None) -> ToolQuota:
        quota = self.get_by_tool_name(tool_name)
        if quota is None:
            quota = ToolQuota(tool_name=tool_name, executions_limit=None, cpu_seconds_limit=None, used_executions=0, used_cpu_seconds=0.0)
        quota.used_executions += executions
        if cpu_seconds is not None:
            quota.used_cpu_seconds += float(cpu_seconds)
        return self.upsert(quota)
