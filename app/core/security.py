from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    return str(_pwd_ctx.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bool(_pwd_ctx.verify(plain, hashed))
    except Exception:
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.jwt_access_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Returns (plain_token, token_hash, expires_at)."""
    settings = get_settings()
    raw = secrets.token_urlsafe(48)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_ttl_seconds)
    return raw, digest, expires_at


def hash_refresh_token(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_tokens_match(cookie_value: str, header_value: str) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value, header_value)
