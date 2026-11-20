"""Endpoint CRUD cho tasks. Yêu cầu đăng nhập và quyền trên project chứa task."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, PaginationDep, TaskFiltersDep, TaskServiceDep
from app.api.responses import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR, not_found
from app.core.messages import MSG_TASK_NOT_FOUND
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

_NOT_FOUND = not_found(MSG_TASK_NOT_FOUND)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def create_task(payload: TaskCreate, service: TaskServiceDep, user: CurrentUser) -> TaskRead:
    return TaskRead.model_validate(await service.create(user, payload))


@router.get(
    "",
    summary="List tasks",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def list_tasks(
    service: TaskServiceDep,
    pagination: PaginationDep,
    filters: TaskFiltersDep,
    user: CurrentUser,
    project_id: Annotated[UUID | None, Query(description="Chỉ lấy task của project này")] = None,
) -> Page[TaskRead]:
    tasks, total = await service.list(user, pagination, filters, project_id)
    return Page[TaskRead].create(
        [TaskRead.model_validate(task) for task in tasks],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{task_id}",
    summary="Get a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def get_task(task_id: UUID, service: TaskServiceDep, user: CurrentUser) -> TaskRead:
    return TaskRead.model_validate(await service.get(user, task_id))


@router.patch(
    "/{task_id}",
    summary="Update a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def update_task(
    task_id: UUID, payload: TaskUpdate, service: TaskServiceDep, user: CurrentUser
) -> TaskRead:
    return TaskRead.model_validate(await service.update(user, task_id, payload))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def delete_task(task_id: UUID, service: TaskServiceDep, user: CurrentUser) -> None:
    await service.delete(user, task_id)
