from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.workers.celery import QueueTask, queue_backend
from app.observability import metrics
from app.observability import alerts


class EventBus:
	def publish(self, name: str, payload: dict[str, Any], available_at: datetime | None = None, max_attempts: int = 3) -> QueueTask:
		return queue_backend.publish(name=name, payload=payload, available_at=available_at, max_attempts=max_attempts)

	def claim_ready(self, name: str | None = None) -> QueueTask | None:
		return queue_backend.claim_ready(now=datetime.now(timezone.utc), name=name)

	def requeue(self, task: QueueTask, delay_seconds: int) -> QueueTask:
		return queue_backend.requeue(task, delay_seconds)

	def dead_letter(self, task: QueueTask, reason: str) -> QueueTask:
		res = queue_backend.dead_letter(task, reason)
		# observability
		try:
			if hasattr(metrics, "dead_letter_total"):
				metrics.dead_letter_total.inc()  # type: ignore
		except Exception:
			pass
		try:
			alerts.alert_dead_letter(task, reason)
		except Exception:
			pass
		return res

	def pending(self) -> list[QueueTask]:
		return queue_backend.pending()

	def dead_letters(self) -> list[QueueTask]:
		return queue_backend.dead_letters()

	def clear_dead_letters(self) -> int:
		if hasattr(queue_backend, "clear_dead_letters"):
			try:
				return queue_backend.clear_dead_letters()
			except Exception:
				return 0
		return 0

	def clear(self) -> None:
		queue_backend.clear()

	def ack(self, task: QueueTask) -> None:
		# acknowledge successful processing
		if hasattr(queue_backend, "ack"):
			try:
				queue_backend.ack(task)
			except Exception:
				pass

	def requeue_stuck(self, name: str | None = None, timeout_seconds: int = 60) -> int:
		if hasattr(queue_backend, "requeue_stuck_processing"):
			try:
				return queue_backend.requeue_stuck_processing(name=name, timeout_seconds=timeout_seconds)
			except Exception:
				return 0
		return 0


event_bus = EventBus()