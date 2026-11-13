"""Các dependency dùng chung trong router."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT
from app.core.database import get_session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.pagination import PaginationParams
from app.core.security import decode_token
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
) -> UserService:
    return UserService(users)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    if credentials is None:
        raise UnauthorizedError()
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    user = await users.get(UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


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
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Tasks per page")] = DEFAULT_LIMIT,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
