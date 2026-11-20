"""Các dependency dùng chung trong router."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.cache import TaskCache
from app.core.config import get_settings
from app.core.constants import (
    DEFAULT_LIMIT,
    DEFAULT_PAGE,
    MAX_LIMIT,
    MAX_SEARCH_LENGTH,
    MIN_LIMIT,
    MIN_PAGE,
)
from app.core.database import get_session
from app.core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError
from app.core.pagination import PaginationParams
from app.core.security import TokenType, decode_token, subject_from_payload
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User, UserRole
from app.repositories.comment_repository import CommentRepository
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskFilters, TaskRepository
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.auth_service import AuthService, UserService
from app.services.comment_service import CommentService
from app.services.label_service import LabelService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.workspace_service import WorkspaceService

# auto_error=False để tự trả error envelope thay vì HTTPException mặc định
_bearer = HTTPBearer(auto_error=False)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    return UserRepository(session)


def get_refresh_token_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def get_workspace_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceRepository:
    return WorkspaceRepository(session)


def get_project_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectRepository:
    return ProjectRepository(session)


def get_task_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskRepository:
    return TaskRepository(session)


def get_label_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LabelRepository:
    return LabelRepository(session)


def get_comment_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CommentRepository:
    return CommentRepository(session)


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


def get_workspace_service(
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> WorkspaceService:
    return WorkspaceService(workspaces, users)


WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]


def get_project_service(
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
) -> ProjectService:
    return ProjectService(projects, workspaces)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def get_task_cache(request: Request) -> TaskCache:
    redis_client: Redis | None = getattr(request.app.state, "redis", None)
    return TaskCache(redis_client, ttl_seconds=get_settings().cache_ttl_seconds)


TaskCacheDep = Annotated[TaskCache, Depends(get_task_cache)]


def get_task_service(
    tasks: Annotated[TaskRepository, Depends(get_task_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    cache: TaskCacheDep,
) -> TaskService:
    return TaskService(tasks, projects, workspaces, users, cache)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_label_service(
    labels: Annotated[LabelRepository, Depends(get_label_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    tasks: Annotated[TaskRepository, Depends(get_task_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    cache: TaskCacheDep,
) -> LabelService:
    return LabelService(labels, projects, tasks, workspaces, cache)


LabelServiceDep = Annotated[LabelService, Depends(get_label_service)]


def get_comment_service(
    comments: Annotated[CommentRepository, Depends(get_comment_repository)],
    tasks: Annotated[TaskRepository, Depends(get_task_repository)],
    projects: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspaces: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
) -> CommentService:
    return CommentService(comments, tasks, projects, workspaces)


CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]


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
    """Dependency kiểm tra role hệ thống. ADMIN luôn được đi qua."""

    def __init__(self, *roles: UserRole) -> None:
        self.roles = roles

    async def __call__(self, user: CurrentUser) -> User:
        if user.role != UserRole.ADMIN and user.role not in self.roles:
            raise ForbiddenError()
        return user


def get_task_filters(
    assignee_id: Annotated[UUID | None, Query(description="Lọc theo người được giao")] = None,
    status: Annotated[list[TaskStatus] | None, Query(description="Lọc theo trạng thái")] = None,
    priority: Annotated[list[TaskPriority] | None, Query(description="Lọc theo độ ưu tiên")] = None,
    due_before: Annotated[datetime | None, Query(description="Hạn chót trước mốc này")] = None,
    due_after: Annotated[datetime | None, Query(description="Hạn chót sau mốc này")] = None,
    search: Annotated[
        str | None, Query(max_length=MAX_SEARCH_LENGTH, description="Tìm trong tiêu đề")
    ] = None,
) -> TaskFilters:
    if due_after is not None and due_before is not None and due_after > due_before:
        raise BadRequestError(messages.MSG_INVALID_DUE_RANGE)
    return TaskFilters(
        assignee_id=assignee_id,
        status=status,
        priority=priority,
        due_before=due_before,
        due_after=due_after,
        search=search,
    )


TaskFiltersDep = Annotated[TaskFilters, Depends(get_task_filters)]


def get_pagination_params(
    page: Annotated[int, Query(ge=MIN_PAGE, description="1-based page number")] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=MIN_LIMIT, le=MAX_LIMIT, description="Items per page")] = (
        DEFAULT_LIMIT
    ),
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
