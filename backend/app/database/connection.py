from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./ai_orchestrator.db"


database_settings = DatabaseSettings()


def _normalize_database_url(database_url: str | None) -> str:
    if database_url:
        return database_url
    return database_settings.database_url


@lru_cache(maxsize=8)
def get_engine(database_url: str | None = None) -> Engine:
    normalized_url = _normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if normalized_url.startswith("sqlite") else {}
    return create_engine(normalized_url, future=True, connect_args=connect_args)


def create_engine_from_settings() -> Engine:
    return get_engine()


def ensure_sqlite_database(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
