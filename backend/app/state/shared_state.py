from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any


@dataclass(slots=True)
class QueueRecord:
	execution_id: str
	workflow_id: str
	tenant_id: str
	status: str
	idempotency_key: str | None
	queued_at: datetime
	updated_at: datetime
	last_error: str | None = None
	attempts: int = 0
	metadata: dict[str, Any] = field(default_factory=dict)


class SharedState:
	def __init__(self) -> None:
		self._lock = RLock()
		self._records: dict[str, QueueRecord] = {}
		self._dead_letter: dict[str, QueueRecord] = {}

	def register(self, execution_id: str, workflow_id: str, tenant_id: str, idempotency_key: str | None) -> QueueRecord:
		now = datetime.now(timezone.utc)
		record = QueueRecord(
			execution_id=execution_id,
			workflow_id=workflow_id,
			tenant_id=tenant_id,
			status="queued",
			idempotency_key=idempotency_key,
			queued_at=now,
			updated_at=now,
		)
		with self._lock:
			self._records[execution_id] = record
		return record

	def transition(self, execution_id: str, status: str, **metadata: Any) -> QueueRecord | None:
		with self._lock:
			record = self._records.get(execution_id)
			if record is None:
				return None
			record.status = status
			record.updated_at = datetime.now(timezone.utc)
			record.metadata.update(metadata)
			if "last_error" in metadata:
				record.last_error = metadata["last_error"]
			if "attempts" in metadata:
				record.attempts = metadata["attempts"]
			return record

	def dead_letter(self, execution_id: str, reason: str) -> QueueRecord | None:
		with self._lock:
			record = self._records.get(execution_id)
			if record is None:
				return None
			record.status = "dead_letter"
			record.last_error = reason
			record.updated_at = datetime.now(timezone.utc)
			self._dead_letter[execution_id] = record
			return record

	def get(self, execution_id: str) -> QueueRecord | None:
		with self._lock:
			return self._records.get(execution_id)

	def dead_letters(self) -> list[QueueRecord]:
		with self._lock:
			return list(self._dead_letter.values())

	def clear(self) -> None:
		with self._lock:
			self._records.clear()
			self._dead_letter.clear()


shared_state = SharedState()