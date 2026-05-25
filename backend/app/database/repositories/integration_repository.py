from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.integration import Integration
from app.database.repositories.base import InMemoryStore, store as default_store


class IntegrationRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def create(self, integration: Integration) -> Integration:
        if self._session is not None:
            self._session.add(integration)
            self._session.commit()
            self._session.refresh(integration)
            return integration
        self._store.__dict__.setdefault("integrations", {})[integration.id] = integration
        return integration

    def list_by_tenant(self, tenant_id: str) -> list[Integration]:
        if self._session is not None:
            return list(self._session.scalars(select(Integration).where(Integration.tenant_id == tenant_id)).all())
        return [integration for integration in self._store.__dict__.setdefault("integrations", {}).values() if integration.tenant_id == tenant_id]
