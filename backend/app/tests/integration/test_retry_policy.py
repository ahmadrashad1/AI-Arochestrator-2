from app.orchestrator.retry_manager import retry_manager


def test_retry_policy_backoff_and_limits():
    # base delay 2s -> sequence 2,4,8 until max or limit
    assert retry_manager.next_delay_seconds(1) == 2
    assert retry_manager.next_delay_seconds(2) == 4
    assert retry_manager.next_delay_seconds(3) == 8 or retry_manager.next_delay_seconds(3) <= retry_manager.policy.max_delay_seconds
    assert retry_manager.can_retry(1) is True
    assert retry_manager.can_retry(retry_manager.policy.max_attempts) is False
