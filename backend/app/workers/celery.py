from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4
import os
import json


@dataclass(slots=True)
class QueueTask:
	id: str
	name: str
	payload: dict[str, Any]
	available_at: datetime
	attempts: int = 0
	max_attempts: int = 3
	enqueued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
	dead_letter_reason: str | None = None


def _deserialize_queue_task(raw: str) -> QueueTask:
	data = json.loads(raw)
	for key in ("available_at", "enqueued_at"):
		value = data.get(key)
		if isinstance(value, str):
			try:
				data[key] = datetime.fromisoformat(value)
			except ValueError:
				data[key] = datetime.now(timezone.utc)
	return QueueTask(**data)


class InMemoryQueueBackend:
	def __init__(self) -> None:
		self._lock = RLock()
		self._tasks: list[QueueTask] = []
		self._dead_letter: list[QueueTask] = []

	def publish(self, name: str, payload: dict[str, Any], available_at: datetime | None = None, max_attempts: int = 3) -> QueueTask:
		task = QueueTask(
			id=f"task_{uuid4().hex[:12]}",
			name=name,
			payload=payload,
			available_at=available_at or datetime.now(timezone.utc),
			max_attempts=max_attempts,
		)
		with self._lock:
			self._tasks.append(task)
		return task

	def claim_ready(self, now: datetime | None = None, name: str | None = None) -> QueueTask | None:
		current_time = now or datetime.now(timezone.utc)
		with self._lock:
			for index, task in enumerate(self._tasks):
				if task.available_at > current_time:
					continue
				if name is not None and task.name != name:
					continue
				return self._tasks.pop(index)
		return None

	def requeue(self, task: QueueTask, delay_seconds: int) -> QueueTask:
		requeued = QueueTask(
			id=task.id,
			name=task.name,
			payload=task.payload,
			available_at=datetime.now(timezone.utc) + timedelta(seconds=delay_seconds),
			attempts=task.attempts + 1,
			max_attempts=task.max_attempts,
			enqueued_at=task.enqueued_at,
		)
		with self._lock:
			self._tasks.append(requeued)
		return requeued

	def dead_letter(self, task: QueueTask, reason: str) -> QueueTask:
		dead_task = QueueTask(
			id=task.id,
			name=task.name,
			payload=task.payload,
			available_at=task.available_at,
			attempts=task.attempts,
			max_attempts=task.max_attempts,
			enqueued_at=task.enqueued_at,
			dead_letter_reason=reason,
		)
		with self._lock:
			self._dead_letter.append(dead_task)
		return dead_task

	def pending(self) -> list[QueueTask]:
		with self._lock:
			return list(self._tasks)

	def dead_letters(self) -> list[QueueTask]:
		with self._lock:
			return list(self._dead_letter)

	def clear_dead_letters(self) -> int:
		with self._lock:
			count = len(self._dead_letter)
			self._dead_letter.clear()
			return count

	def clear(self) -> None:
		with self._lock:
			self._tasks.clear()
			self._dead_letter.clear()
class RedisQueueBackend:
	def __init__(self, redis_url: str | None = None, redis_client: object | None = None):
		try:
			if redis_client is not None:
				self._redis = redis_client
			else:
				import redis

				if redis_url is None:
					raise RuntimeError("redis_url required when no client provided")
				self._redis = redis.from_url(redis_url, decode_responses=True)
		except Exception:
			raise

	def publish(self, name: str, payload: dict[str, Any], available_at: datetime | None = None, max_attempts: int = 3) -> QueueTask:
		task = QueueTask(
			id=f"task_{uuid4().hex[:12]}",
			name=name,
			payload=payload,
			available_at=available_at or datetime.now(timezone.utc),
			max_attempts=max_attempts,
		)
		key = f"queue:{name}"
		self._redis.rpush(key, json.dumps(task.__dict__, default=str))
		return task

	def claim_ready(self, now: datetime | None = None, name: str | None = None) -> QueueTask | None:
		current_time = (now or datetime.now(timezone.utc)).timestamp()
		# move ready delayed tasks into the list
		if name is None:
			return None
		delayed_key = f"queue:delayed:{name}"
		ready = self._redis.zrangebyscore(delayed_key, 0, current_time)
		if ready:
			pipe = self._redis.pipeline()
			for member in ready:
				pipe.lpush(f"queue:{name}", member)
				pipe.zrem(delayed_key, member)
			pipe.execute()
		# atomically move from queue to processing list using Lua when available
		raw = None
		try:
			# prefer atomic rpoplpush if available
			raw = self._redis.rpoplpush(f"queue:{name}", f"processing:{name}")
		except Exception:
			# fallback to a simple pop/push (may not be atomic)
			try:
				val = self._redis.rpop(f"queue:{name}")
				if val:
					self._redis.lpush(f"processing:{name}", val)
					raw = val
			except Exception:
				raw = None
		if not raw:
			return None
		data = json.loads(raw)
		# convert available_at back to datetime
		data["available_at"] = datetime.fromisoformat(data["available_at"]) if isinstance(data["available_at"], str) else datetime.now(timezone.utc)
		# record visibility deadline
		vis_key = f"processing:vis:{name}"
		try:
			self._redis.hset(vis_key, data["id"], (datetime.now(timezone.utc) + timedelta(seconds=60)).timestamp())
		except Exception:
			pass
		return QueueTask(**data)

	def requeue(self, task: QueueTask, delay_seconds: int) -> QueueTask:
		# remove from processing list and schedule in delayed set
		processing_list = f"processing:{task.name}"
		try:
			self._redis.lrem(processing_list, 0, json.dumps(task.__dict__, default=str))
		except Exception:
			pass
		delayed_key = f"queue:delayed:{task.name}"
		member = json.dumps(task.__dict__, default=str)
		score = (datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)).timestamp()
		self._redis.zadd(delayed_key, {member: score})
		return task

	def dead_letter(self, task: QueueTask, reason: str) -> QueueTask:
		processing_list = f"processing:{task.name}"
		try:
			self._redis.lrem(processing_list, 0, json.dumps(task.__dict__, default=str))
		except Exception:
			pass
		key = f"queue:dead:{task.name}"
		task.dead_letter_reason = reason
		self._redis.rpush(key, json.dumps(task.__dict__, default=str))
		return task

	def ack(self, task: QueueTask) -> None:
		# remove from processing list and processing visibility map
		processing_list = f"processing:{task.name}"
		vis_key = f"processing:vis:{task.name}"
		try:
			self._redis.lrem(processing_list, 0, json.dumps(task.__dict__, default=str))
			self._redis.hdel(vis_key, task.id)
		except Exception:
			pass

	def requeue_stuck_processing(self, name: str | None = None, timeout_seconds: int = 60) -> int:
		"""Scan processing visibility map and requeue tasks whose visibility deadline has passed.

		Returns the number of tasks requeued.
		"""
		requeued = 0
		now_ts = datetime.now(timezone.utc).timestamp()
		if name is None:
			# scan keys matching pattern
			try:
				keys = self._redis.keys("processing:vis:*")
			except Exception:
				keys = []
		else:
			keys = [f"processing:vis:{name}"]

		for vis_key in keys:
			try:
				entries = self._redis.hgetall(vis_key)
			except Exception:
				continue
			for task_id, deadline in entries.items():
				try:
					if float(deadline) < now_ts:
						# find the task in processing list
						pname = vis_key.split(":", 2)[-1]
						processing_list = f"processing:{pname}"
						raw_list = self._redis.lrange(processing_list, 0, -1)
						for raw in raw_list:
							try:
								data = json.loads(raw)
							except Exception:
								continue
							if data.get("id") == task_id:
								# remove from processing and push back to queue
								try:
									self._redis.lrem(processing_list, 0, raw)
									self._redis.hdel(vis_key, task_id)
									self._redis.lpush(f"queue:{pname}", raw)
									requeued += 1
								except Exception:
									pass
								break
				except Exception:
					continue
		return requeued

	def pending(self) -> list[QueueTask]:
		tasks: list[QueueTask] = []
		for key in self._redis.keys("queue:*"):
			if ":delayed:" in key or ":dead:" in key:
				continue
			try:
				for raw in self._redis.lrange(key, 0, -1):
					tasks.append(_deserialize_queue_task(raw))
			except Exception:
				continue
		for key in self._redis.keys("queue:delayed:*"):
			try:
				for raw, score in self._redis.zrange(key, 0, -1, withscores=True):
					task = _deserialize_queue_task(raw)
					task.available_at = datetime.fromtimestamp(float(score), timezone.utc)
					tasks.append(task)
			except Exception:
				continue
		return tasks

	def dead_letters(self) -> list[QueueTask]:
		tasks: list[QueueTask] = []
		for key in self._redis.keys("queue:dead:*"):
			try:
				for raw in self._redis.lrange(key, 0, -1):
					tasks.append(_deserialize_queue_task(raw))
			except Exception:
				continue
		return tasks

	def clear_dead_letters(self) -> int:
		count = 0
		for key in self._redis.keys("queue:dead:*"):
			try:
				count += int(self._redis.llen(key))
				self._redis.delete(key)
			except Exception:
				continue
		return count

	def clear(self) -> None:
		for key in self._redis.keys("queue:*"):
			try:
				self._redis.delete(key)
			except Exception:
				continue
		for key in self._redis.keys("processing:*"):
			try:
				self._redis.delete(key)
			except Exception:
				continue


# select backend based on REDIS_URL
_redis_url = os.environ.get("REDIS_URL")
_broker_url = os.environ.get("BROKER_URL")
if _redis_url:
	try:
		queue_backend = RedisQueueBackend(_redis_url)
	except Exception:
		queue_backend = InMemoryQueueBackend()
elif _broker_url:
	# do not auto-configure Celery here; defer to CeleryQueueBackend if present
	queue_backend = InMemoryQueueBackend()
else:
	queue_backend = InMemoryQueueBackend()


class CeleryQueueBackend:
	def __init__(self, broker_url: str):
		try:
			from celery import Celery

			self.app = Celery(broker=broker_url)
		except Exception:
			# fallback stub
			class _Stub:
				def send_task(self, *args, **kwargs):
					return None

			self.app = _Stub()

	def publish(self, name: str, payload: dict[str, Any], available_at: datetime | None = None, max_attempts: int = 3) -> QueueTask:
		# Use send_task to allow external worker to pick up
		task = QueueTask(
			id=f"task_{uuid4().hex[:12]}",
			name=name,
			payload=payload,
			available_at=available_at or datetime.now(timezone.utc),
			max_attempts=max_attempts,
		)
		# send as generic task
		try:
			self.app.send_task(name, args=[payload], kwargs={})
		except Exception:
			pass
		return task

	# Celery-backed claim/requeue/dead-letter are not applicable locally; raise NotImplementedError
	def claim_ready(self, now: datetime | None = None, name: str | None = None) -> QueueTask | None:
		raise NotImplementedError()

	def requeue(self, task: QueueTask, delay_seconds: int) -> QueueTask:
		raise NotImplementedError()

	def dead_letter(self, task: QueueTask, reason: str) -> QueueTask:
		raise NotImplementedError()

	def pending(self) -> list[QueueTask]:
		return []

	def dead_letters(self) -> list[QueueTask]:
		return []

	def clear(self) -> None:
		return