from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from app.observability import metrics
from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.database.models.usage import LLMUsage

logger = get_logger("llm_usage")


@dataclass
class ExecutionLLMUsage:
    execution_id: str
    tenant_id: str | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def record(self, provider: str, model: str, tier: str, prompt_tokens: int | None, completion_tokens: int | None, cost_usd: float | None = None, latency_ms: int | None = None) -> dict[str, Any]:
        rec = {
            "provider": provider,
            "model": model,
            "tier": tier,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
        }
        self.calls.append(rec)
        try:
            metrics.record_llm_call(provider, model, tier, True, prompt_tokens=prompt_tokens or 0, completion_tokens=completion_tokens or 0, cost_usd=cost_usd)
        except Exception:
            pass
        logger.info("llm.usage %s %s", self.execution_id, rec)
        return rec


# in-memory map of execution_id -> usage (sufficient for debugging & tests)
_USAGE_CACHE: dict[str, ExecutionLLMUsage] = {}


def record_llm_usage(execution_id: str, tenant_id: str | None, provider: str, model: str, tier: str, prompt_tokens: int | None, completion_tokens: int | None, latency_ms: int | None = None) -> dict[str, Any]:
    key = execution_id
    if key not in _USAGE_CACHE:
        _USAGE_CACHE[key] = ExecutionLLMUsage(execution_id=execution_id, tenant_id=tenant_id)
    cost_rec = None
    try:
        from app.llm.cost_tracker import cost_tracker

        cost = cost_tracker.record(provider, model, tier, prompt_tokens or 0, completion_tokens or 0)
        cost_rec = cost
    except Exception:
        cost_rec = None
    rec = _USAGE_CACHE[key].record(provider, model, tier, prompt_tokens, completion_tokens, cost_usd=(cost_rec or {}).get("cost_usd") if cost_rec else None, latency_ms=latency_ms)

    # Persist to database if DB backend is enabled
    try:
        # create a session directly so this function can be called from background workers
        session = SessionLocal()
        try:
            db_obj = LLMUsage(
                id=f"llm_{execution_id}_{len(_USAGE_CACHE.get(key).calls)}",
                tenant_id=tenant_id,
                execution_id=execution_id,
                workflow_id=None,
                provider=provider,
                model=model,
                tier=tier,
                prompt_tokens=prompt_tokens or 0,
                completion_tokens=completion_tokens or 0,
                cost_usd=(cost_rec or {}).get("cost_usd") if cost_rec else None,
                latency_ms=latency_ms,
            )
            session.add(db_obj)
            session.commit()
        finally:
            session.close()
    except Exception:
        # If DB not available or error occurs, we still keep in-memory record for debugging
        pass

    return rec


def get_usage_for_execution(execution_id: str) -> dict[str, Any]:
    usage = _USAGE_CACHE.get(execution_id)
    if not usage:
        return {"execution_id": execution_id, "calls": [], "total_cost_usd": 0.0}
    total = sum(call.get("cost_usd") or 0.0 for call in usage.calls)
    return {"execution_id": execution_id, "calls": list(usage.calls), "total_cost_usd": round(total, 6)}
