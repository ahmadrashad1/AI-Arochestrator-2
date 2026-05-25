from __future__ import annotations

from typing import Any, Sequence

from app.llm.providers.base import BaseLLMProvider, LLMResult


class TestProvider(BaseLLMProvider):
    provider_name = "test"

    def __init__(self, *args, **kwargs) -> None:
        # do not call super() to avoid base URL lookup
        self.api_key = None
        self.base_url = ""
        self.client = None

    def is_configured(self) -> bool:
        return True

    def default_model_for_tier(self, tier: str) -> str:
        return "test-model"

    def complete(self, *, messages: Sequence[dict[str, Any]], model: str | None = None, temperature: float = 0.0, max_tokens: int = 512) -> LLMResult:
        model = model or self.default_model_for_tier("standard")
        content = "This is a test completion."
        return LLMResult(provider=self.provider_name, model=model, content=content, prompt_tokens=1, completion_tokens=1, raw_response={"test": True, "messages": messages})
