from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.constants import LLM_PROVIDER_COSTS_USD_PER_1K_TOKENS


def estimate_cost(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = LLM_PROVIDER_COSTS_USD_PER_1K_TOKENS.get(provider, LLM_PROVIDER_COSTS_USD_PER_1K_TOKENS["grok"])
    cost = ((prompt_tokens * rates["prompt"]) + (completion_tokens * rates["completion"])) / 1000.0
    return round(cost, 6)


@dataclass
class CostTracker:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        provider: str,
        model: str,
        tier: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> dict[str, Any]:
        cost_usd = estimate_cost(provider, prompt_tokens, completion_tokens)
        record = {
            "provider": provider,
            "model": model,
            "tier": tier,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd,
        }
        self.calls.append(record)
        return record

    def snapshot(self) -> dict[str, Any]:
        return {
            "calls": list(self.calls),
            "total_cost_usd": round(sum(call["cost_usd"] for call in self.calls), 6),
        }

    def reset(self) -> None:
        self.calls.clear()


cost_tracker = CostTracker()
