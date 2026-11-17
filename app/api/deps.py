"""Các dependency dùng chung trong router."""

from typing import Annotated

import jwt
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT
from app.core.database import get_session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.pagination import PaginationParams
from app.core.security import TokenType, decode_token, subject_from_payload
from app.models.task import TaskModel
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.services.auth_service import AuthService, UserService
from app.services.task_service import TaskService

# auto_error=False để tự trả error envelope thay vì HTTPException mặc định
_bearer = HTTPBearer(auto_error=False)


def get_task_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BaseRepository[TaskModel]:
    return SqlAlchemyRepository(session, TaskModel, TaskModel.created_at)


def get_task_service(
    repository: Annotated[BaseRepository[TaskModel], Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repository)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    return UserRepository(session)


def get_refresh_token_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_tokens: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> AuthService:
    return AuthService(users, refresh_tokens)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_tokens: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> UserService:
    return UserService(users, refresh_tokens)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Giải mã access token rồi lấy user. Chỗ duy nhất làm việc này."""
    if credentials is None:
        raise UnauthorizedError(messages.MSG_NOT_AUTHENTICATED)
    try:
        payload = decode_token(credentials.credentials, TokenType.ACCESS)
        user_id = subject_from_payload(payload)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError(messages.MSG_INVALID_TOKEN) from exc

    user = await users.get(user_id)
    if user is None:
        raise UnauthorizedError(messages.MSG_USER_NOT_FOUND)
    if not user.is_active:
        raise UnauthorizedError(messages.MSG_INACTIVE_USER)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError(messages.MSG_ADMIN_REQUIRED)
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]


class RequireRoles:
    """Dependency kiểm tra role. ADMIN luôn được đi qua."""

    def __init__(self, *roles: UserRole) -> None:
        self.roles = roles

    async def __call__(self, user: CurrentUser) -> User:
        if user.role != UserRole.ADMIN and user.role not in self.roles:
            raise ForbiddenError()
        return user


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Items per page")] = DEFAULT_LIMIT,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
