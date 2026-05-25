from __future__ import annotations

from typing import Any, Sequence

from app.llm.providers.base import BaseLLMProvider, LLMProviderError, LLMResult, _first_text, _response_usage


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def complete(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> LLMResult:
        model_name = model or self.default_model_for_tier("standard")
        api_key = self.api_key
        if api_key is None:
            import os

            api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMProviderError("Missing ANTHROPIC_API_KEY")

        response = self.client.post(
            f"{self.base_url.rstrip('/')}/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model_name,
                "messages": list(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        payload = response.json()
        content = _first_text(payload.get("content"))
        prompt_tokens, completion_tokens = _response_usage(payload)
        return LLMResult(provider=self.provider_name, model=model_name, content=content, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, raw_response=payload)
