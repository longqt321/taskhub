"""Nghiệp vụ đăng ký, đăng nhập, refresh token, profile và quản lý user."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

import jwt
from sqlalchemy.exc import IntegrityError

from app.core import messages
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
from app.core.pagination import PaginationParams
from app.core.security import (
    DUMMY_HASH,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password_async,
    subject_from_payload,
    verify_password_async,
)
from app.models.user import RefreshToken, User, UserRole
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.schemas.user import LoginRequest, UserAdminUpdate, UserCreate, UserUpdate


def _is_expired(expires_at: datetime) -> bool:
    # Postgres trả datetime có timezone, nhưng vẫn phòng trường hợp driver trả naive
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at < datetime.now(UTC)


def _build_pair(user: User) -> tuple[str, str, RefreshToken]:
    access = create_access_token(str(user.id), user.role.value)
    refresh, jti, expires_at = create_refresh_token(str(user.id))
    return access, refresh, RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at)


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens

    async def register(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=await hash_password_async(data.password),
        )
        try:
            return await self._users.add(user)
        except IntegrityError as exc:
            # hai request cùng email chạy song song thì chỉ unique index chặn được
            await self._users.rollback()
            raise ConflictError(
                messages.MSG_EMAIL_ALREADY_REGISTERED, details={"email": data.email}
            ) from exc

    async def login(self, data: LoginRequest) -> tuple[str, str]:
        user = await self._users.get_by_email(data.email)
        # luôn verify với dummy hash khi không tìm thấy user để tránh lộ email qua timing
        hashed = user.hashed_password if user is not None else DUMMY_HASH
        valid = await verify_password_async(data.password, hashed)
        if user is None or not valid:
            raise UnauthorizedError(messages.MSG_INCORRECT_CREDENTIALS)
        # mật khẩu đúng nhưng tài khoản bị khoá thì báo đúng lý do
        if not user.is_active:
            raise UnauthorizedError(messages.MSG_INACTIVE_USER)
        access, refresh, record = _build_pair(user)
        await self._refresh_tokens.add(record)
        return access, refresh

    async def refresh(self, raw_refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(raw_refresh_token, TokenType.REFRESH)
            user_id = subject_from_payload(payload)
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedError(messages.MSG_INVALID_REFRESH_TOKEN) from exc

        record = await self._refresh_tokens.get_by_jti(payload["jti"])
        if record is None or _is_expired(record.expires_at):
            raise UnauthorizedError(messages.MSG_INVALID_REFRESH_TOKEN)

        user = await self._users.get(user_id)
        if user is None:
            raise UnauthorizedError(messages.MSG_INVALID_REFRESH_TOKEN)
        if not user.is_active:
            raise UnauthorizedError(messages.MSG_INACTIVE_USER)

        access, refresh, new_record = _build_pair(user)
        # Thu hồi token cũ và ghi token mới trong cùng một transaction. Không thu hồi
        # được nghĩa là token đã bị dùng trước đó, coi như bị lộ và cắt hết session.
        if not await self._refresh_tokens.rotate(payload["jti"], new_record):
            # rotate() rollback sẽ expire mọi ORM object, nên dùng user_id đã parse từ token
            await self._refresh_tokens.revoke_all_for_user(user_id, commit=True)
            raise UnauthorizedError(messages.MSG_INVALID_REFRESH_TOKEN)
        return access, refresh

    async def logout(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_token(raw_refresh_token, TokenType.REFRESH)
        except jwt.InvalidTokenError as exc:
            raise UnauthorizedError(messages.MSG_INVALID_REFRESH_TOKEN) from exc
        await self._refresh_tokens.revoke(payload["jti"])


class UserService:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens

    async def get(self, user_id: UUID) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise NotFoundError(messages.MSG_USER_NOT_FOUND)
        return user

    async def list(self, pagination: PaginationParams) -> tuple[Sequence[User], int]:
        return await self._users.list(offset=pagination.offset, limit=pagination.limit)

    async def update(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_unset=True)
        if "password" in changes:
            if not await verify_password_async(changes["current_password"], user.hashed_password):
                raise UnauthorizedError(messages.MSG_INCORRECT_CURRENT_PASSWORD)
            user.hashed_password = await hash_password_async(changes["password"])
        if "full_name" in changes:
            user.full_name = changes["full_name"]
        updated = await self._users.update(user)
        if "password" in changes:
            # đổi mật khẩu xong thì mọi refresh token cũ hết giá trị
            await self._refresh_tokens.revoke_all_for_user(user.id)
        return updated

    async def admin_update(self, actor: User, user_id: UUID, data: UserAdminUpdate) -> User:
        target = await self._get_or_404(user_id)
        changes = data.model_dump(exclude_unset=True)

        deactivating = changes.get("is_active") is False
        losing_admin = changes.get("role") not in (None, UserRole.ADMIN)

        if target.id == actor.id and deactivating:
            raise BadRequestError(messages.MSG_CANNOT_DELETE_SELF)
        if target.id == actor.id and losing_admin:
            raise BadRequestError(messages.MSG_CANNOT_DELETE_SELF)
        if target.role == UserRole.ADMIN and (deactivating or losing_admin):
            await self._ensure_another_admin()

        if "full_name" in changes:
            target.full_name = changes["full_name"]
        if "role" in changes:
            target.role = changes["role"]
        if "is_active" in changes:
            target.is_active = changes["is_active"]
            if not target.is_active:
                # khoá tài khoản thì cắt luôn các session đang mở
                await self._refresh_tokens.revoke_all_for_user(target.id)
        return await self._users.update(target)

    async def admin_delete(self, actor: User, user_id: UUID) -> None:
        target = await self._get_or_404(user_id)
        if target.id == actor.id:
            raise BadRequestError(messages.MSG_CANNOT_DELETE_SELF)
        if target.role == UserRole.ADMIN and target.is_active:
            await self._ensure_another_admin()
        await self._users.delete(user_id)

    async def _get_or_404(self, user_id: UUID) -> User:
        target = await self._users.get(user_id)
        if target is None:
            raise NotFoundError(messages.MSG_USER_NOT_FOUND)
        return target

    async def _ensure_another_admin(self) -> None:
        if await self._users.count_active_admins() <= 1:
            raise BadRequestError(messages.MSG_LAST_ADMIN)
