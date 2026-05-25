from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    jwt_secret: str = "dev-secret-change-me-use-a-longer-secret"
    jwt_issuer: str = "ai-orchestrator-saas"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60
    password_salt: str = "ai-orchestrator-salt"


security_settings = SecuritySettings()


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str
    tenant_id: str
    email: str
    role: str
    request_id: str | None = None


def hash_password(password: str) -> str:
    import hashlib

    digest = hashlib.sha256(f"{security_settings.password_salt}:{password}".encode("utf-8")).hexdigest()
    return digest


def verify_password(password: str, expected_hash: str) -> bool:
    import hmac

    return hmac.compare_digest(hash_password(password), expected_hash)


def create_jwt(payload: Mapping[str, Any], expires_in_minutes: int | None = None) -> str:
    token_payload = dict(payload)
    token_payload.setdefault("iss", security_settings.jwt_issuer)
    token_payload.setdefault("iat", int(time.time()))
    ttl = expires_in_minutes or security_settings.access_token_ttl_minutes
    token_payload.setdefault("exp", int(time.time()) + (ttl * 60))
    return jwt.encode(token_payload, security_settings.jwt_secret, algorithm=security_settings.jwt_algorithm)


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            security_settings.jwt_secret,
            algorithms=[security_settings.jwt_algorithm],
            issuer=security_settings.jwt_issuer,
            options={"require": ["exp", "iat", "iss"]},
        )
        return dict(payload)
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token expired") from exc
    except jwt.InvalidIssuerError as exc:
        raise ValueError("Invalid token issuer") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
