from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from app.core.constants import LLM_PROVIDER_FALLBACKS, LLM_PROVIDER_PRIORITY, LLM_TIERS, LLM_TIER_MODEL_MAP
from app.llm.cost_tracker import CostTracker, cost_tracker
from app.llm.prompt_manager import PromptManager, prompt_manager
from app.llm.token_tracker import TokenTracker, token_tracker
import os
from time import perf_counter

from app.llm.providers import AnthropicProvider, BaseLLMProvider, GeminiProvider, GrokProvider, LLMProviderError, LLMResult, OpenAIProvider
from app.llm.providers.base import NoopProvider
from app.llm.providers.test_provider import TestProvider
from app.observability import metrics
from app.observability.logging import log_llm_call, log_llm_failure


@dataclass(frozen=True)
class LLMRoute:
    tier: str
    provider: str
    model: str
    fallbacks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "provider": self.provider,
            "model": self.model,
            "fallbacks": list(self.fallbacks),
        }


class LLMRouter:
    def __init__(
        self,
        providers: Sequence[BaseLLMProvider] | None = None,
        *,
        prompt_manager: PromptManager | None = None,
        token_tracker: TokenTracker | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self.prompt_manager = prompt_manager or globals()["prompt_manager"]
        self.token_tracker = token_tracker or globals()["token_tracker"]
        self.cost_tracker = cost_tracker or globals()["cost_tracker"]
        self._providers = list(providers) if providers is not None else [GrokProvider(), OpenAIProvider(), AnthropicProvider(), GeminiProvider()]
        self._explicit_providers = providers is not None
        self._provider_by_name = {provider.provider_name: provider for provider in self._providers}

    def _normalize_tier(self, tier: str | None) -> str:
        normalized = (tier or "standard").strip().lower().replace("-", "_")
        if normalized in ("high", "high_confidence", "highconfidence", "expensive"):
            normalized = "high_confidence"
        if normalized not in LLM_TIERS:
            return "standard"
        return normalized

    def select_route(self, tier: str | None = None) -> LLMRoute:
        normalized_tier = self._normalize_tier(tier)
        primary_provider = "grok"
        provider = self._pick_available_provider(primary_provider)
        model = provider.default_model_for_tier(normalized_tier)
        return LLMRoute(
            tier=normalized_tier,
            provider=provider.provider_name,
            model=model,
            fallbacks=self._fallback_chain(provider.provider_name),
        )

    def _fallback_chain(self, provider_name: str) -> tuple[str, ...]:
        return LLM_PROVIDER_FALLBACKS.get(provider_name, ())

    def _pick_available_provider(self, preferred_provider: str) -> BaseLLMProvider:
        # If test mode is explicitly enabled, return the TestProvider
        if os.environ.get("LLM_TEST_MODE") in ("1", "true", "yes"):
            return TestProvider()
        if self._explicit_providers and preferred_provider in self._provider_by_name:
            return self._provider_by_name[preferred_provider]

        candidates = [preferred_provider, *LLM_PROVIDER_FALLBACKS.get(preferred_provider, ())]
        for provider_name in candidates:
            provider = self._provider_by_name.get(provider_name)
            if provider is not None and provider.is_configured():
                return provider

        for provider_name in LLM_PROVIDER_PRIORITY:
            provider = self._provider_by_name.get(provider_name)
            if provider is not None and (self._explicit_providers or provider.is_configured()):
                return provider

        # Return a NoopProvider to allow the runtime and tests to operate without API keys.
        return NoopProvider()

    def _message_list(self, prompt: str | None = None, messages: Sequence[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        if messages is not None:
            return list(messages)
        if prompt is None:
            return []
        return [{"role": "user", "content": prompt}]

    def complete(
        self,
        *,
        prompt: str | None = None,
        messages: Sequence[dict[str, Any]] | None = None,
        tier: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        preferred_provider: str | None = None,
        execution_id: str | None = None,
        tenant_id: str | None = None,
        workflow_id: str | None = None,
        agent: str | None = None,
    ) -> LLMResult:
        normalized_tier = self._normalize_tier(tier)
        message_list = self._message_list(prompt=prompt, messages=messages)
        primary = preferred_provider or "grok"
        provider_names = [primary, *LLM_PROVIDER_FALLBACKS.get(primary, ())]
        if primary != "grok":
            provider_names.extend(name for name in LLM_PROVIDER_PRIORITY if name not in provider_names)

        last_error: Exception | None = None
        for provider_name in provider_names:
            provider = self._provider_by_name.get(provider_name)
            if provider is None:
                continue
            if not self._explicit_providers and not provider.is_configured():
                continue

            model = provider.default_model_for_tier(normalized_tier)
            route = LLMRoute(
                tier=normalized_tier,
                provider=provider.provider_name,
                model=model,
                fallbacks=self._fallback_chain(provider.provider_name),
            )
            try:
                start = perf_counter()
                result = provider.complete(messages=message_list, model=model, temperature=temperature, max_tokens=max_tokens)
                latency_ms = int((perf_counter() - start) * 1000)
                prompt_tokens = result.prompt_tokens
                completion_tokens = result.completion_tokens
                if prompt_tokens is None or completion_tokens is None:
                    prompt_tokens, completion_tokens = self.token_tracker.estimate(prompt=prompt, messages=message_list, completion=result.content)

                self.token_tracker.record(provider.provider_name, result.model, normalized_tier, prompt_tokens, completion_tokens)
                self.cost_tracker.record(provider.provider_name, result.model, normalized_tier, prompt_tokens, completion_tokens)
                try:
                    metrics.record_llm_call(provider.provider_name, result.model, normalized_tier, True, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
                except Exception:
                    pass
                # Record per-execution LLM usage if execution context provided
                try:
                    from app.observability.llm_usage import record_llm_usage

                    record_llm_usage(execution_id or "", tenant_id, provider.provider_name, result.model, normalized_tier, prompt_tokens, completion_tokens, latency_ms)
                except Exception:
                    pass
                log_llm_call(
                    "llm.complete",
                    provider=provider.provider_name,
                    model=result.model,
                    tier=normalized_tier,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    route=route.to_dict(),
                )
                return result
            except Exception as exc:
                last_error = exc
                try:
                    metrics.record_llm_call(provider.provider_name, model, normalized_tier, False)
                except Exception:
                    pass
                log_llm_failure(
                    "llm.complete.failed",
                    provider=provider.provider_name,
                    model=model,
                    tier=normalized_tier,
                    error=str(exc),
                )

        if last_error is not None:
            raise last_error
        raise LLMProviderError("No LLM provider could satisfy the request")


llm_router = LLMRouter()
