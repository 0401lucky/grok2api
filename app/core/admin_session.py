"""
后台会话令牌工具

使用 `app.app_key` 派生签名密钥，生成短期 Bearer 会话令牌。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_config


SESSION_TOKEN_PREFIX = "g2a"
DEFAULT_SESSION_HOURS = 8

security = HTTPBearer(
    auto_error=False,
    scheme_name="Admin Session",
    description="Enter admin session token in the format: Bearer <token>",
)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    s = str(data or "").strip()
    if not s:
        raise ValueError("empty base64url data")
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("utf-8"))


def _session_secret() -> bytes:
    app_key = str(get_config("app.app_key", "") or "").strip()
    if not app_key:
        return b""
    extra_secret = str(os.getenv("ADMIN_SESSION_SECRET", "") or "").strip()
    material = f"{app_key}:{extra_secret}" if extra_secret else app_key
    return hashlib.sha256(material.encode("utf-8")).digest()


def _sign(payload_b64: str, secret: bytes) -> str:
    digest = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_admin_session_token(username: str, ttl_hours: int = DEFAULT_SESSION_HOURS) -> str:
    """签发后台会话令牌。"""
    ttl = max(1, int(ttl_hours or DEFAULT_SESSION_HOURS))
    now = int(time.time())
    payload = {
        "v": 1,
        "u": str(username or "admin"),
        "iat": now,
        "exp": now + ttl * 3600,
        "n": secrets.token_urlsafe(12),
    }
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    secret = _session_secret()
    if not secret:
        raise RuntimeError("Admin session secret is unavailable")
    signature = _sign(payload_b64, secret)
    return f"{SESSION_TOKEN_PREFIX}.{payload_b64}.{signature}"


def verify_admin_session_token(token: str) -> bool:
    """校验后台会话令牌。"""
    raw = str(token or "").strip()
    if not raw:
        return False
    parts = raw.split(".")
    if len(parts) != 3 or parts[0] != SESSION_TOKEN_PREFIX:
        return False

    payload_b64 = parts[1]
    signature = parts[2]
    secret = _session_secret()
    if not secret:
        return False

    expected_signature = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected_signature):
        return False

    try:
        payload_raw = _b64url_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return False

    if not isinstance(payload, dict):
        return False

    try:
        exp = int(payload.get("exp") or 0)
    except Exception:
        return False

    now = int(time.time())
    return exp > now


async def verify_admin_session(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> str:
    """FastAPI 依赖：验证后台会话令牌。"""
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = str(auth.credentials or "").strip()
    if not verify_admin_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


__all__ = [
    "create_admin_session_token",
    "verify_admin_session_token",
    "verify_admin_session",
]
