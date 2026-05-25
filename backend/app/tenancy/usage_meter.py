from __future__ import annotations

from collections import defaultdict


_USAGE: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))


def reset_usage() -> None:
    _USAGE.clear()


def record_usage(tenant_id: str, metric: str, amount: int = 1) -> None:
    _USAGE[tenant_id][metric] += amount


def get_usage_snapshot(tenant_id: str) -> dict[str, int]:
    return dict(_USAGE.get(tenant_id, {}))
