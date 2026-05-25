from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.database.models.user import User
from app.database.repositories.base import InMemoryStore, store as default_store


class UserRepository:
    def __init__(self, store: InMemoryStore | None = None, session: Session | None = None):
        self._store = store or default_store
        self._session = session

    def get_by_id(self, user_id: str) -> User | None:
        session = self._session
        if session is not None:
            return session.get(User, user_id)
        return self._store.users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.casefold()
        session = self._session
        if session is not None:
            statement = select(User).where(func.lower(User.email) == normalized_email)
            return session.scalars(statement).first()
        return next((user for user in self._store.users.values() if user.email.casefold() == normalized_email), None)

    def list_by_tenant(self, tenant_id: str) -> list[User]:
        session = self._session
        if session is not None:
            return list(session.scalars(select(User).where(User.tenant_id == tenant_id)).all())
        return [user for user in self._store.users.values() if user.tenant_id == tenant_id]

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create(self, user: User) -> User:
        session = self._session
        if session is not None:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        self._store.users[user.id] = user
        return user

    def update(self, user: User) -> User:
        session = self._session
        if session is not None:
            merged = session.merge(user)
            session.commit()
            session.refresh(merged)
            return merged
        self._store.users[user.id] = user
        return user

    def delete(self, user_id: str) -> None:
        session = self._session
        if session is not None:
            user = session.get(User, user_id)
            if user is not None:
                session.delete(user)
                session.commit()
            return
        self._store.users.pop(user_id, None)
