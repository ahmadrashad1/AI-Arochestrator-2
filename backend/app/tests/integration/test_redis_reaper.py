from datetime import datetime, timezone, timedelta

from app.workers.celery import RedisQueueBackend, QueueTask


class FakeRedis:
    def __init__(self):
        self.storage = {}

    def rpush(self, key, value):
        self.storage.setdefault(key, []).append(value)

    def lpush(self, key, value):
        self.storage.setdefault(key, []).insert(0, value)

    def lrange(self, key, a, b):
        return list(self.storage.get(key, []))

    def lrem(self, key, count, value):
        lst = self.storage.get(key, [])
        try:
            while value in lst and count != 0:
                lst.remove(value)
                if count > 0:
                    count -= 1
        except Exception:
            pass

    def hset(self, key, field, value):
        self.storage.setdefault(key, {})[field] = value

    def hgetall(self, key):
        return dict(self.storage.get(key, {}))

    def hdel(self, key, field):
        self.storage.get(key, {}).pop(field, None)

    def keys(self, pattern):
        # very naive
        return [k for k in self.storage.keys() if k.startswith(pattern.replace("*", ""))]

    def zadd(self, key, mapping):
        self.storage.setdefault(key, {})

    def zrangebyscore(self, key, a, b):
        return []


def test_requeue_stuck_processing():
    fake = FakeRedis()
    backend = RedisQueueBackend(redis_client=fake)

    # prepare a processing item with past visibility
    task = QueueTask(
        id="task_1",
        name="workflow.execution.requested",
        payload={"execution_id": "ex1"},
        available_at=datetime.now(timezone.utc) - timedelta(seconds=120),
    )
    from dataclasses import asdict

    raw = __import__("json").dumps(asdict(task), default=str)
    fake.storage.setdefault("processing:workflow.execution.requested", []).append(raw)
    fake.storage.setdefault("processing:vis:workflow.execution.requested", {})[task.id] = (datetime.now(timezone.utc) - timedelta(seconds=120)).timestamp()

    requeued = backend.requeue_stuck_processing(name=None, timeout_seconds=60)
    assert requeued >= 1
    # ensure it's back in queue list
    assert fake.storage.get("queue:workflow.execution.requested")
