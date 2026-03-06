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
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_config


SESSION_TOKEN_PREFIX = "g2a"
DEFAULT_SESSION_HOURS = 8
ADMIN_SESSION_COOKIE = "g2a_admin_session"
REVOCATION_FILE = Path(__file__).parent.parent.parent / "data" / "admin_session_revocations.json"

_revoked_jti_cache: dict[str, int] | None = None
_revoked_jti_mtime: float | None = None
_revoked_jti_lock = threading.Lock()

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
    app_key_hash = str(get_config("app.app_key_hash", "") or "").strip()
    app_key = str(get_config("app.app_key", "") or "").strip()
    material = app_key_hash or app_key
    if not material:
        return b""
    extra_secret = str(os.getenv("ADMIN_SESSION_SECRET", "") or "").strip()
    material = f"{material}:{extra_secret}" if extra_secret else material
    return hashlib.sha256(material.encode("utf-8")).digest()


def _sign(payload_b64: str, secret: bytes) -> str:
    digest = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def _read_revocations_file_unlocked() -> dict[str, int]:
    if not REVOCATION_FILE.exists():
        return {}
    try:
        raw = REVOCATION_FILE.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in data.items():
        key = str(k or "").strip()
        if not key:
            continue
        try:
            exp = int(v)
        except Exception:
            continue
        out[key] = exp
    return out


def _write_revocations_file_unlocked(data: dict[str, int]) -> None:
    REVOCATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = REVOCATION_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(tmp, REVOCATION_FILE)


def _load_revocations() -> dict[str, int]:
    global _revoked_jti_cache, _revoked_jti_mtime

    try:
        mtime = REVOCATION_FILE.stat().st_mtime if REVOCATION_FILE.exists() else None
    except Exception:
        mtime = None

    if _revoked_jti_cache is not None and _revoked_jti_mtime == mtime:
        return _revoked_jti_cache

    with _revoked_jti_lock:
        try:
            mtime = REVOCATION_FILE.stat().st_mtime if REVOCATION_FILE.exists() else None
        except Exception:
            mtime = None
        if _revoked_jti_cache is not None and _revoked_jti_mtime == mtime:
            return _revoked_jti_cache

        data = _read_revocations_file_unlocked()
        now = int(time.time())
        filtered = {k: exp for k, exp in data.items() if exp > now}

        if filtered != data:
            try:
                _write_revocations_file_unlocked(filtered)
                mtime = REVOCATION_FILE.stat().st_mtime if REVOCATION_FILE.exists() else None
            except Exception:
                pass

        _revoked_jti_cache = filtered
        _revoked_jti_mtime = mtime
        return filtered


def _is_revoked_jti(jti: str, now: int | None = None) -> bool:
    token_id = str(jti or "").strip()
    if not token_id:
        return False
    if now is None:
        now = int(time.time())
    revoked = _load_revocations()
    exp = revoked.get(token_id)
    return bool(exp and exp > now)


def _decode_session_payload(raw: str) -> dict | None:
    token = str(raw or "").strip()
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != SESSION_TOKEN_PREFIX:
        return None
    payload_b64 = parts[1]
    signature = parts[2]
    secret = _session_secret()
    if not secret:
        return None
    expected_signature = _sign(payload_b64, secret)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        payload_raw = _b64url_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def create_admin_session_token(username: str, ttl_hours: int = DEFAULT_SESSION_HOURS) -> str:
    """签发后台会话令牌。"""
    ttl = max(1, int(ttl_hours or DEFAULT_SESSION_HOURS))
    now = int(time.time())
    payload = {
        "v": 1,
        "u": str(username or "admin"),
        "iat": now,
        "exp": now + ttl * 3600,
        "jti": secrets.token_urlsafe(16),
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
    payload = _decode_session_payload(token)
    if not payload:
        return False

    try:
        exp = int(payload.get("exp") or 0)
    except Exception:
        return False

    now = int(time.time())
    if exp <= now:
        return False

    jti = str(payload.get("jti") or "").strip()
    if jti and _is_revoked_jti(jti, now=now):
        return False
    return True


def revoke_admin_session_token(token: str) -> bool:
    payload = _decode_session_payload(token)
    if not payload:
        return False

    jti = str(payload.get("jti") or "").strip()
    if not jti:
        return False
    try:
        exp = int(payload.get("exp") or 0)
    except Exception:
        exp = 0
    if exp <= 0:
        return False

    global _revoked_jti_cache, _revoked_jti_mtime
    with _revoked_jti_lock:
        now = int(time.time())
        data = _read_revocations_file_unlocked()
        data = {k: v for k, v in data.items() if v > now}
        data[jti] = exp
        _write_revocations_file_unlocked(data)
        try:
            mtime = REVOCATION_FILE.stat().st_mtime if REVOCATION_FILE.exists() else None
        except Exception:
            mtime = None
        _revoked_jti_cache = data
        _revoked_jti_mtime = mtime
    return True


async def verify_admin_session(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> str:
    """FastAPI 依赖：验证后台会话令牌。"""
    token = str(auth.credentials or "").strip() if auth else ""
    if not token:
        token = str(request.cookies.get(ADMIN_SESSION_COOKIE, "") or "").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin session",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    "revoke_admin_session_token",
]
