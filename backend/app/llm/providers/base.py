from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

import httpx

from app.core.constants import LLM_PROVIDER_BASE_URLS, LLM_PROVIDER_ENV_VARS, LLM_PROVIDER_PRIORITY, LLM_TIER_MODEL_MAP


@dataclass(frozen=True)
class LLMResult:
    provider: str
    model: str
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    raw_response: dict[str, Any] | None = None

    @property
    def total_tokens(self) -> int | None:
        if self.prompt_tokens is None and self.completion_tokens is None:
            return None
        return (self.prompt_tokens or 0) + (self.completion_tokens or 0)


class LLMProviderError(RuntimeError):
    pass


class BaseLLMProvider(ABC):
    provider_name: str

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url or LLM_PROVIDER_BASE_URLS[self.provider_name]
        self.client = client or httpx.Client(timeout=30.0)

    def default_model_for_tier(self, tier: str) -> str:
        tier_map = LLM_TIER_MODEL_MAP.get(tier, {})
        if not tier_map:
            return ""
        return tier_map.get(self.provider_name, next(iter(tier_map.values())))

    def is_configured(self) -> bool:
        if self.api_key:
            return True
        env_name = LLM_PROVIDER_ENV_VARS.get(self.provider_name)
        if env_name is None:
            return False
        import os

        return bool(os.environ.get(env_name))

    @abstractmethod
    def complete(
        self,
        *,
        messages: Sequence[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> LLMResult:
        raise NotImplementedError


class NoopProvider(BaseLLMProvider):
    provider_name = "none"

    def __init__(self, *args, **kwargs) -> None:
        # avoid calling BaseLLMProvider init which expects a known provider base URL
        self.api_key = None
        self.base_url = ""
        self.client = None

    def is_configured(self) -> bool:
        return True

    def complete(self, *, messages: Sequence[dict[str, Any]], model: str | None = None, temperature: float = 0.0, max_tokens: int = 512) -> LLMResult:
        raise LLMProviderError("No LLM provider configured; cannot perform completion")


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("content", "text", "message"):
            if key in value:
                result = _first_text(value[key])
                if result:
                    return result
        return ""
    if isinstance(value, list):
        for item in value:
            text = _first_text(item)
            if text:
                return text
        return ""
    return str(value) if value is not None else ""


def _response_usage(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    usage = payload.get("usage") or payload.get("usageMetadata") or {}
    prompt_tokens = usage.get("prompt_tokens") or usage.get("promptTokenCount") or usage.get("promptTokens")
    completion_tokens = usage.get("completion_tokens") or usage.get("candidatesTokenCount") or usage.get("completionTokenCount") or usage.get("output_tokens") or usage.get("outputTokenCount")
    if prompt_tokens is not None:
        prompt_tokens = int(prompt_tokens)
    if completion_tokens is not None:
        completion_tokens = int(completion_tokens)
    return prompt_tokens, completion_tokens


def _openai_style_payload(messages: Sequence[dict[str, Any]], model: str, temperature: float, max_tokens: int) -> dict[str, Any]:
    return {
        "model": model,
        "messages": list(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
