from __future__ import annotations

import os
import json
import base64
import hmac
import hashlib
from typing import Dict, Any


JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")


def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    s2 = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s2.encode("ascii"))


def sign_jwt(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b = _b64u_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b = _b64u_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    to_sign = f"{header_b}.{payload_b}".encode("ascii")
    sig = hmac.new(JWT_SECRET.encode("utf-8"), to_sign, hashlib.sha256).digest()
    sig_b = _b64u_encode(sig)
    return f"{header_b}.{payload_b}.{sig_b}"


def verify_jwt(token: str) -> Dict[str, Any] | None:
    try:
        header_b, payload_b, sig_b = token.split(".")
        to_sign = f"{header_b}.{payload_b}".encode("ascii")
        expected = hmac.new(JWT_SECRET.encode("utf-8"), to_sign, hashlib.sha256).digest()
        actual = _b64u_decode(sig_b)
        if not hmac.compare_digest(expected, actual):
            return None
        payload_json = _b64u_decode(payload_b).decode("utf-8")
        return json.loads(payload_json)
    except Exception:
        return None
