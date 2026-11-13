"""Nghiệp vụ đăng ký, đăng nhập, refresh và logout."""

from datetime import UTC, datetime
from uuid import UUID

import jwt

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.schemas.user import LoginRequest, UserCreate, UserUpdate


def _is_expired(expires_at: datetime) -> bool:
    # Postgres trả datetime có timezone, nhưng vẫn phòng trường hợp driver trả naive
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at < datetime.now(UTC)


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens

    async def register(self, data: UserCreate) -> User:
        if await self._users.get_by_email(data.email) is not None:
            raise ConflictError("Email already registered", details={"email": data.email})
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        return await self._users.add(user)

    async def login(self, data: LoginRequest) -> tuple[str, str]:
        user = await self._users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")
        access = create_access_token(str(user.id), user.role.value)
        refresh, jti, expires_at = create_refresh_token(str(user.id))
        await self._refresh_tokens.add(
            RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at)
        )
        return access, refresh

    async def refresh(self, raw_refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(raw_refresh_token, expected_type="refresh")
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        record = await self._refresh_tokens.get_by_jti(payload["jti"])
        if record is None or record.revoked_at is not None or _is_expired(record.expires_at):
            raise UnauthorizedError("Invalid refresh token")

        user = await self._users.get(UUID(str(payload["sub"])))
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid refresh token")

        # rotate: token cũ bị thu hồi, cấp cặp mới
        await self._refresh_tokens.revoke(payload["jti"])
        access = create_access_token(str(user.id), user.role.value)
        refresh, jti, expires_at = create_refresh_token(str(user.id))
        await self._refresh_tokens.add(
            RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at)
        )
        return access, refresh

    async def logout(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_token(raw_refresh_token, expected_type="refresh")
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc
        await self._refresh_tokens.revoke(payload["jti"])


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def get(self, user_id: UUID) -> User:
        user = await self._users.get(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return user

    async def update(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_unset=True)
        if "password" in changes:
            if not verify_password(changes["current_password"], user.hashed_password):
                raise UnauthorizedError("Incorrect current password")
            user.hashed_password = hash_password(changes["password"])
        if "full_name" in changes:
            user.full_name = changes["full_name"]
        return await self._users.update(user)
