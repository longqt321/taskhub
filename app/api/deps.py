"""Các dependency dùng chung trong router."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query

from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT
from app.core.pagination import PaginationParams
from app.models.task import Task
from app.repositories.base import BaseRepository
from app.repositories.in_memory import InMemoryRepository
from app.services.task_service import TaskService


@lru_cache
def get_task_repository() -> BaseRepository[Task]:
    # cache để dữ liệu in-memory không bị mất giữa các request
    return InMemoryRepository[Task]()


def get_task_service(
    repository: Annotated[BaseRepository[Task], Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repository)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Items per page")] = DEFAULT_LIMIT,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
