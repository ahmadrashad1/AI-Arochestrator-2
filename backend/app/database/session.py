from __future__ import annotations

from collections.abc import Generator
from os import environ

from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import get_engine


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    engine = get_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


SessionLocal = create_session_factory()


def _use_database_backend() -> bool:
    return environ.get("REPO_BACKEND", "INMEMORY").upper() in ("DB", "SQL", "SQLALCHEMY")


def get_session() -> Generator[Session | None, None, None]:
    if not _use_database_backend():
        yield None
        return

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
