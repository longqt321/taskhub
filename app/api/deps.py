"""Các dependency dùng chung trong router."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.models.item import ItemModel
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.services.auth_service import AuthService, UserService
from app.services.item_service import ItemService

# auto_error=False để tự trả error envelope thay vì HTTPException mặc định
_bearer = HTTPBearer(auto_error=False)


def get_item_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BaseRepository[ItemModel]:
    return SqlAlchemyRepository(session, ItemModel, ItemModel.created_at)


def get_item_service(
    repository: Annotated[BaseRepository[ItemModel], Depends(get_item_repository)],
) -> ItemService:
    return ItemService(repository)


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


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


@dataclass(frozen=True, slots=True)
class PaginationParams:
    page: int
    limit: int


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
