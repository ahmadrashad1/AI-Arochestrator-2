from __future__ import annotations

from typing import Any, Sequence

from app.llm.providers.base import BaseLLMProvider, LLMProviderError, LLMResult, _first_text, _response_usage


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

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

            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise LLMProviderError("Missing GEMINI_API_KEY")

        response = self.client.post(
            f"{self.base_url.rstrip('/')}/models/{model_name}:generateContent",
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "role": message.get("role", "user"),
                        "parts": [{"text": str(message.get("content", ""))}],
                    }
                    for message in messages
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        payload = response.json()
        candidates = payload.get("candidates") or []
        content = ""
        if candidates:
            candidate = candidates[0]
            content = _first_text(candidate.get("content") or candidate.get("parts"))
        if not content:
            content = _first_text(payload.get("content"))
        prompt_tokens, completion_tokens = _response_usage(payload)
        return LLMResult(provider=self.provider_name, model=model_name, content=content, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, raw_response=payload)
