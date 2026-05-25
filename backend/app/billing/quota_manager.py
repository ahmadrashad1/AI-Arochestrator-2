from __future__ import annotations

from fastapi import HTTPException, status

from app.tenancy.usage_meter import get_usage_snapshot

EXECUTION_LIMITS = {
    "starter": 2,
    "pro": 10,
    "enterprise": 100,
}


def execution_limit_for_plan(plan: str) -> int:
    return EXECUTION_LIMITS.get(plan, EXECUTION_LIMITS["starter"])


def ensure_execution_quota(tenant_id: str, plan: str) -> None:
    current_usage = get_usage_snapshot(tenant_id).get("executions", 0)
    limit = execution_limit_for_plan(plan)
    if current_usage >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Execution quota reached for plan {plan} ({current_usage}/{limit})",
        )