from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    return max(1, len(text.split()))


def estimate_message_tokens(messages: list[dict[str, Any]] | None) -> int:
    total = 0
    for message in messages or []:
        total += 4 + _estimate_tokens(str(message.get("content", "")))
    return total


@dataclass
class TokenTracker:
    calls: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        provider: str,
        model: str,
        tier: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> dict[str, Any]:
        total_tokens = prompt_tokens + completion_tokens
        record = {
            "provider": provider,
            "model": model,
            "tier": tier,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        self.calls.append(record)
        return record

    def estimate(self, prompt: str | None = None, messages: list[dict[str, Any]] | None = None, completion: str | None = None) -> tuple[int, int]:
        prompt_tokens = _estimate_tokens(prompt) if prompt is not None else estimate_message_tokens(messages)
        completion_tokens = _estimate_tokens(completion)
        return prompt_tokens, completion_tokens

    def snapshot(self) -> dict[str, Any]:
        return {
            "calls": list(self.calls),
            "prompt_tokens": sum(call["prompt_tokens"] for call in self.calls),
            "completion_tokens": sum(call["completion_tokens"] for call in self.calls),
            "total_tokens": sum(call["total_tokens"] for call in self.calls),
        }

    def reset(self) -> None:
        self.calls.clear()


token_tracker = TokenTracker()
