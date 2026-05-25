from __future__ import annotations

from typing import Any

from app.core.logging import get_logger


def log_llm_call(event: str, **context: Any) -> None:
    get_logger("llm").info("%s %s", event, context)


def log_llm_failure(event: str, **context: Any) -> None:
    get_logger("llm").warning("%s %s", event, context)


def log_execution_trace(event: str, **context: Any) -> None:
    get_logger("trace").info("%s %s", event, context)


def log_tool_call(event: str, **context: Any) -> None:
    get_logger("tools").info("%s %s", event, context)
