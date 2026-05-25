from __future__ import annotations

from typing import Callable

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
except Exception:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"  # type: ignore
    Counter = None  # type: ignore
    Gauge = None  # type: ignore
    generate_latest = None  # type: ignore


def noop(*args, **kwargs):
    return None


if Counter is not None:
    reaper_requeued_total = Counter("reaper_requeued_total", "Number of tasks requeued by reaper")
    dead_letter_total = Counter("dead_letter_total", "Number of tasks sent to dead-letter")
    processing_tasks = Gauge("processing_tasks", "Number of tasks currently in processing lists")
    llm_requests_total = Counter("llm_requests_total", "Number of LLM requests", ["provider", "model", "tier", "status"])
    llm_tokens_total = Counter("llm_tokens_total", "Total LLM tokens processed", ["provider", "model", "tier", "kind"])
    llm_cost_usd_total = Counter("llm_cost_usd_total", "Total estimated LLM cost in USD", ["provider", "model", "tier"])
    # Tool execution metrics
    tool_executions_total = Counter(
        "tool_executions_total",
        "Number of tool executions",
        ["tool_name", "status"],
    )
    try:
        from prometheus_client import Histogram  # type: ignore

        tool_execution_duration_seconds = Histogram(
            "tool_execution_duration_seconds",
            "Tool execution duration in seconds",
            ["tool_name"],
        )
    except Exception:
        tool_execution_duration_seconds = None
    tool_execution_cpu_seconds = Gauge(
        "tool_execution_cpu_seconds",
        "User+system CPU seconds used by last tool execution",
        ["tool_name"],
    )
    tool_execution_memory_bytes = Gauge(
        "tool_execution_memory_bytes",
        "Peak memory (bytes) used by last tool execution",
        ["tool_name"],
    )
else:
    reaper_requeued_total = noop
    dead_letter_total = noop
    processing_tasks = noop
    llm_requests_total = noop
    llm_tokens_total = noop
    llm_cost_usd_total = noop


def record_tool_execution(tool_name: str, success: bool, duration_seconds: float | None = None, cpu_seconds: float | None = None, memory_bytes: int | None = None) -> None:
    if Counter is None:
        return
    status = "success" if success else "failure"
    try:
        tool_executions_total.labels(tool_name=tool_name, status=status).inc()
    except Exception:
        pass


def record_llm_call(
    provider: str,
    model: str,
    tier: str,
    success: bool,
    *,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    cost_usd: float | None = None,
) -> None:
    if Counter is None:
        return
    status = "success" if success else "failure"
    try:
        llm_requests_total.labels(provider=provider, model=model, tier=tier, status=status).inc()
    except Exception:
        pass
    try:
        if prompt_tokens is not None:
            llm_tokens_total.labels(provider=provider, model=model, tier=tier, kind="prompt").inc(prompt_tokens)
        if completion_tokens is not None:
            llm_tokens_total.labels(provider=provider, model=model, tier=tier, kind="completion").inc(completion_tokens)
    except Exception:
        pass
    try:
        if cost_usd is not None:
            llm_cost_usd_total.labels(provider=provider, model=model, tier=tier).inc(cost_usd)
    except Exception:
        pass

    try:
        if duration_seconds is not None and tool_execution_duration_seconds is not None:
            tool_execution_duration_seconds.labels(tool_name=tool_name).observe(duration_seconds)
    except Exception:
        pass

    try:
        if cpu_seconds is not None:
            tool_execution_cpu_seconds.labels(tool_name=tool_name).set(cpu_seconds)
    except Exception:
        pass

    try:
        if memory_bytes is not None:
            tool_execution_memory_bytes.labels(tool_name=tool_name).set(memory_bytes)
    except Exception:
        pass


def get_metrics_app():
    # the main FastAPI app imports `app.observability.metrics` and exposes `/metrics` elsewhere
    return None
