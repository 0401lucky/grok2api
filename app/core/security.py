"""安全辅助：密码哈希、校验与脱敏。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

HASH_PREFIX = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 310000
SECRET_PLACEHOLDER = "__KEEP_EXISTING__"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    text = str(data or "").strip()
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + padding).encode("utf-8"))


def has_password_hash(value: str | None) -> bool:
    return str(value or "").startswith(f"{HASH_PREFIX}$")


def hash_password(secret: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, int(iterations))
    return f"{HASH_PREFIX}${int(iterations)}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(secret: str, stored_hash: str | None, legacy_plaintext: str | None = None) -> bool:
    hashed = str(stored_hash or "").strip()
    if has_password_hash(hashed):
        try:
            _, iteration_text, salt_text, digest_text = hashed.split("$", 3)
            iterations = int(iteration_text)
            salt = _b64url_decode(salt_text)
            digest = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(_b64url_encode(digest), digest_text)
        except Exception:
            return False
    return hmac.compare_digest(secret, str(legacy_plaintext or ""))


def is_weak_password(stored_hash: str | None, legacy_plaintext: str | None) -> bool:
    if not has_password_hash(stored_hash):
        normalized = str(legacy_plaintext or "").strip().lower()
        return normalized in {"", "admin", "__change_me__", "grok2api"}
    for candidate in ("", "admin", "__CHANGE_ME__", "grok2api"):
        if verify_password(candidate, stored_hash, legacy_plaintext):
            return True
    return False


def redact_secret(value: str | None) -> str:
    return SECRET_PLACEHOLDER if str(value or "").strip() else ""

