from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetryPolicy:
	max_attempts: int = 3
	base_delay_seconds: int = 2
	max_delay_seconds: int = 60


class RetryManager:
	def __init__(self, policy: RetryPolicy | None = None) -> None:
		self.policy = policy or RetryPolicy()

	def next_delay_seconds(self, attempt_number: int) -> int:
		delay = self.policy.base_delay_seconds * (2 ** max(attempt_number - 1, 0))
		return min(delay, self.policy.max_delay_seconds)

	def can_retry(self, attempt_number: int) -> bool:
		return attempt_number < self.policy.max_attempts


retry_manager = RetryManager()