from __future__ import annotations

from typing import Iterable, TypeVar

T = TypeVar("T")


def is_same_tenant(resource_tenant_id: str, tenant_id: str) -> bool:
    return resource_tenant_id == tenant_id


def filter_by_tenant(items: Iterable[T], tenant_id: str, tenant_getter) -> list[T]:
    return [item for item in items if tenant_getter(item) == tenant_id]
