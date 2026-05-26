from __future__ import annotations

from app.observability.llm_usage import record_llm_usage, get_usage_for_execution


def test_record_and_retrieve_llm_usage() -> None:
    execution_id = "exec_llm_test"
    # record two calls
    record_llm_usage(execution_id, "tenant_test", "grok", "grok-small", "standard", 10, 20, 123)
    record_llm_usage(execution_id, "tenant_test", "grok", "grok-small", "standard", 5, 10, 50)

    usage = get_usage_for_execution(execution_id)
    assert usage["execution_id"] == execution_id
    assert len(usage["calls"]) >= 2
    assert usage["total_cost_usd"] >= 0
