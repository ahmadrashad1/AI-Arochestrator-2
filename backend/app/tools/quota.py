from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

try:
    import redis
except Exception:  # pragma: no cover - optional dependency in some envs
    redis = None

from app.database.models.tool_quota import ToolQuota as ToolQuotaModel
from app.database.repositories.tool_quota_repository import ToolQuotaRepository
from app.database.session import SessionLocal


class QuotaExceeded(Exception):
    pass


_memory_lock = threading.Lock()
_memory_quotas: dict[str, ToolQuotaModel] = {}

_redis_client = None
if redis is not None:
    redis_url = os.environ.get("QUOTA_REDIS_URL") or os.environ.get("REDIS_URL")
    if redis_url:
        try:
            _redis_client = redis.from_url(redis_url)
        except Exception:
            _redis_client = None


def _use_database_backend() -> bool:
    return os.environ.get("REPO_BACKEND", "INMEMORY").upper() in ("DB", "SQL", "SQLALCHEMY")


@contextmanager
def _session_scope() -> Iterator[object]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _redis_key(tool_name: str) -> str:
    return f"quotas:{tool_name}"


def _model_to_status(quota: ToolQuotaModel | None) -> dict[str, Optional[float]]:
    if quota is None:
        return {
            "executions_limit": None,
            "used_executions": 0,
            "cpu_seconds_limit": None,
            "used_cpu_seconds": 0.0,
        }
    return {
        "executions_limit": quota.executions_limit,
        "used_executions": quota.used_executions,
        "cpu_seconds_limit": quota.cpu_seconds_limit,
        "used_cpu_seconds": quota.used_cpu_seconds,
    }


def _status_to_model(tool_name: str, status: dict[str, Optional[float]]) -> ToolQuotaModel:
    return ToolQuotaModel(
        tool_name=tool_name,
        executions_limit=status.get("executions_limit"),
        cpu_seconds_limit=status.get("cpu_seconds_limit"),
        used_executions=int(status.get("used_executions") or 0),
        used_cpu_seconds=float(status.get("used_cpu_seconds") or 0.0),
    )


def set_quota(tool_name: str, executions_limit: Optional[int] = None, cpu_seconds_limit: Optional[float] = None) -> None:
    if _use_database_backend():
        with _session_scope() as session:
            repo = ToolQuotaRepository(session=session)
            existing = repo.get_by_tool_name(tool_name)
            if existing is None:
                existing = ToolQuotaModel(tool_name=tool_name, executions_limit=None, cpu_seconds_limit=None, used_executions=0, used_cpu_seconds=0.0)
            if executions_limit is not None:
                existing.executions_limit = executions_limit
            if cpu_seconds_limit is not None:
                existing.cpu_seconds_limit = cpu_seconds_limit
            repo.upsert(existing)
        return

    if _redis_client is not None:
        data = {}
        if executions_limit is not None:
            data["executions_limit"] = json.dumps(executions_limit)
        if cpu_seconds_limit is not None:
            data["cpu_seconds_limit"] = json.dumps(cpu_seconds_limit)
        if data:
            _redis_client.hset(_redis_key(tool_name), mapping=data)
        return

    with _memory_lock:
        existing = _memory_quotas.get(tool_name) or ToolQuotaModel(tool_name=tool_name, executions_limit=None, cpu_seconds_limit=None, used_executions=0, used_cpu_seconds=0.0)
        if executions_limit is not None:
            existing.executions_limit = executions_limit
        if cpu_seconds_limit is not None:
            existing.cpu_seconds_limit = cpu_seconds_limit
        _memory_quotas[tool_name] = existing


def get_quota_status(tool_name: str) -> dict[str, Optional[float]]:
    if _use_database_backend():
        with _session_scope() as session:
            repo = ToolQuotaRepository(session=session)
            return _model_to_status(repo.get_by_tool_name(tool_name))

    if _redis_client is not None:
        raw = _redis_client.hgetall(_redis_key(tool_name))
        if not raw:
            return _model_to_status(None)

        def _decode(value: bytes | str):
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            try:
                return json.loads(value)
            except Exception:
                return value

        return {
            "executions_limit": _decode(raw.get(b"executions_limit") or raw.get("executions_limit")),
            "used_executions": int(_decode(raw.get(b"used_executions") or raw.get("used_executions")) or 0),
            "cpu_seconds_limit": _decode(raw.get(b"cpu_seconds_limit") or raw.get("cpu_seconds_limit")),
            "used_cpu_seconds": float(_decode(raw.get(b"used_cpu_seconds") or raw.get("used_cpu_seconds")) or 0.0),
        }

    with _memory_lock:
        return _model_to_status(_memory_quotas.get(tool_name))


def check_quota(tool_name: str) -> None:
    status = get_quota_status(tool_name)
    if status["executions_limit"] is not None and status["used_executions"] >= status["executions_limit"]:
        raise QuotaExceeded(f"executions quota exceeded for {tool_name}")
    if status["cpu_seconds_limit"] is not None and status["used_cpu_seconds"] >= status["cpu_seconds_limit"]:
        raise QuotaExceeded(f"cpu quota exceeded for {tool_name}")


def record_usage(tool_name: str, executions: int = 1, cpu_seconds: float | None = None) -> None:
    if _use_database_backend():
        with _session_scope() as session:
            repo = ToolQuotaRepository(session=session)
            repo.increment_usage(tool_name, executions=executions, cpu_seconds=cpu_seconds)
        return

    if _redis_client is not None:
        key = _redis_key(tool_name)
        pipe = _redis_client.pipeline()
        pipe.hincrby(key, "used_executions", executions)
        if cpu_seconds is not None:
            cur = _redis_client.hget(key, "used_cpu_seconds")
            cur_value = float(json.loads(cur)) if cur else 0.0
            pipe.hset(key, "used_cpu_seconds", json.dumps(cur_value + float(cpu_seconds)))
        pipe.execute()
        return

    with _memory_lock:
        existing = _memory_quotas.get(tool_name)
        if existing is None:
            existing = ToolQuotaModel(tool_name=tool_name, executions_limit=None, cpu_seconds_limit=None, used_executions=0, used_cpu_seconds=0.0)
            _memory_quotas[tool_name] = existing
        existing.used_executions += executions
        if cpu_seconds is not None:
            existing.used_cpu_seconds += float(cpu_seconds)


def list_quotas() -> dict[str, dict[str, Optional[float]]]:
    if _use_database_backend():
        with _session_scope() as session:
            repo = ToolQuotaRepository(session=session)
            return {quota.tool_name: _model_to_status(quota) for quota in repo.list_all()}

    if _redis_client is not None:
        out: dict[str, dict[str, Optional[float]]] = {}
        for key in _redis_client.keys("quotas:*"):
            tool_name = key.decode().split(":", 1)[1]
            out[tool_name] = get_quota_status(tool_name)
        return out

    with _memory_lock:
        return {tool_name: _model_to_status(quota) for tool_name, quota in _memory_quotas.items()}
