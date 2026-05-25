from __future__ import annotations

from app.core.security import AuthPrincipal, create_jwt, decode_jwt


def issue_access_token(principal: AuthPrincipal) -> str:
    return create_jwt(
        {
            "sub": principal.user_id,
            "tenant_id": principal.tenant_id,
            "email": principal.email,
            "role": principal.role,
            "request_id": principal.request_id,
        }
    )


def parse_access_token(token: str) -> AuthPrincipal:
    payload = decode_jwt(token)
    return AuthPrincipal(
        user_id=str(payload["sub"]),
        tenant_id=str(payload["tenant_id"]),
        email=str(payload["email"]),
        role=str(payload["role"]),
        request_id=payload.get("request_id"),
    )
