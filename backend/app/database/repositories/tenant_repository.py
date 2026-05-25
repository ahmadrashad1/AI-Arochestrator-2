from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.tenant import Tenant
from app.database.repositories.base import InMemoryStore, store as default_store


class TenantRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def get_by_id(self, tenant_id: str) -> Tenant | None:
        session = self._session
        if session is not None:
            return session.get(Tenant, tenant_id)
        return self._store.tenants.get(tenant_id)

    def list_all(self) -> list[Tenant]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(Tenant)).all())
        return list(self._store.tenants.values())

    def create(self, tenant: Tenant) -> Tenant:
        session = self._session
        if session is not None:
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            return tenant
        self._store.tenants[tenant.id] = tenant
        return tenant

    def update(self, tenant: Tenant) -> Tenant:
        session = self._session
        if session is not None:
            merged = session.merge(tenant)
            session.commit()
            session.refresh(merged)
            return merged
        self._store.tenants[tenant.id] = tenant
        return tenant

    def delete(self, tenant_id: str) -> None:
        session = self._session
        if session is not None:
            tenant = session.get(Tenant, tenant_id)
            if tenant is not None:
                session.delete(tenant)
                session.commit()
            return
        self._store.tenants.pop(tenant_id, None)
