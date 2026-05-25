from __future__ import annotations

LLM_TIERS = ("cheap", "standard", "high_confidence")

LLM_TIER_MODEL_MAP: dict[str, dict[str, str]] = {
    "cheap": {
        "grok": "grok-2-mini",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "gemini": "gemini-1.5-flash",
    },
    "standard": {
        "grok": "grok-2",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20240620",
        "gemini": "gemini-1.5-pro",
    },
    "high_confidence": {
        "grok": "grok-3",
        "openai": "gpt-4.1",
        "anthropic": "claude-3-7-sonnet-20250219",
        "gemini": "gemini-2.0-pro",
    },
}

LLM_PROVIDER_PRIORITY = ("grok", "openai", "anthropic", "gemini")

LLM_PROVIDER_FALLBACKS: dict[str, tuple[str, ...]] = {
    "grok": ("openai", "anthropic", "gemini"),
    "openai": ("anthropic", "gemini"),
    "anthropic": ("gemini",),
    "gemini": (),
}

LLM_PROVIDER_ENV_VARS: dict[str, str] = {
    "grok": "XAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

LLM_PROVIDER_BASE_URLS: dict[str, str] = {
    "grok": "https://api.x.ai/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
}

LLM_PROVIDER_COSTS_USD_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "grok": {"prompt": 0.0003, "completion": 0.0006},
    "openai": {"prompt": 0.0005, "completion": 0.0010},
    "anthropic": {"prompt": 0.0008, "completion": 0.0024},
    "gemini": {"prompt": 0.0002, "completion": 0.0004},
}
