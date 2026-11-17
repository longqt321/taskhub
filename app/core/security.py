"""Băm mật khẩu và tạo/giải mã JWT."""

import enum
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


class TokenType(enum.StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


# claim bắt buộc phải có, thiếu cái nào cũng coi là token hỏng
REQUIRED_CLAIMS = ("sub", "jti", "exp", "type")


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
        "type": token_type.value,
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
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        uuid4().hex,
        {"role": role},
    )


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Trả về token, jti và hạn dùng. Service lưu jti vào DB để revoke được."""
    settings = get_settings()
    jti = uuid4().hex
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    token = _encode(subject, TokenType.REFRESH, expires_delta, jti)
    return token, jti, datetime.now(UTC) + expires_delta


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Giải mã token, raise jwt.InvalidTokenError nếu sai chữ ký, hết hạn hoặc sai loại."""
    settings = get_settings()
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type.value:
        raise jwt.InvalidTokenError(f"Expected {expected_type.value} token")
    for claim in REQUIRED_CLAIMS:
        if claim not in payload:
            raise jwt.InvalidTokenError(f"Token is missing {claim} claim")
    return payload


def subject_from_payload(payload: dict[str, Any]) -> UUID:
    """Đọc sub từ payload. Token ký đúng nhưng sub rác vẫn là token không hợp lệ."""
    try:
        return UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Token subject is not a valid UUID") from exc
