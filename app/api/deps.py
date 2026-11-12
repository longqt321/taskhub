"""Các dependency dùng chung trong router."""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT
from app.core.database import get_session
from app.core.pagination import PaginationParams
from app.models.task import TaskModel
from app.repositories.base import BaseRepository
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository
from app.services.task_service import TaskService


def get_task_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BaseRepository[TaskModel]:
    return SqlAlchemyRepository(session, TaskModel, TaskModel.created_at)


def get_task_service(
    repository: Annotated[BaseRepository[TaskModel], Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repository)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Tasks per page")] = DEFAULT_LIMIT,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
