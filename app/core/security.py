"""Băm mật khẩu và tạo/giải mã JWT."""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def _encode(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    jti: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": jti,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    return _encode(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        uuid4().hex,
        {"role": role},
    )


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Trả về token, jti và hạn dùng. Service lưu jti vào DB để revoke được."""
    settings = get_settings()
    jti = uuid4().hex
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    token = _encode(subject, "refresh", expires_delta, jti)
    return token, jti, datetime.now(UTC) + expires_delta


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Giải mã token, raise jwt.InvalidTokenError nếu sai chữ ký, hết hạn hoặc sai loại."""
    settings = get_settings()
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected {expected_type} token")
    return payload
