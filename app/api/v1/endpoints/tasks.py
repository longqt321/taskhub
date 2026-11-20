"""Endpoint CRUD cho tasks. Yêu cầu đăng nhập."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, PaginationDep, TaskServiceDep
from app.api.responses import UNAUTHORIZED, VALIDATION_ERROR, not_found
from app.core.messages import MSG_TASK_NOT_FOUND
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

NOT_FOUND = {**UNAUTHORIZED, **not_found(MSG_TASK_NOT_FOUND)}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    responses={**UNAUTHORIZED, **VALIDATION_ERROR},
)
async def create_task(payload: TaskCreate, service: TaskServiceDep, user: CurrentUser) -> TaskRead:
    return TaskRead.model_validate(await service.create(payload))


@router.get(
    "",
    summary="List tasks",
    responses={**UNAUTHORIZED, **VALIDATION_ERROR},
)
async def list_tasks(
    service: TaskServiceDep, pagination: PaginationDep, user: CurrentUser
) -> Page[TaskRead]:
    tasks, total = await service.list(pagination)
    return Page[TaskRead].create(
        [TaskRead.model_validate(task) for task in tasks],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{task_id}",
    summary="Get a task",
    responses=NOT_FOUND,
)
async def get_task(task_id: UUID, service: TaskServiceDep, user: CurrentUser) -> TaskRead:
    return TaskRead.model_validate(await service.get(task_id))


@router.patch(
    "/{task_id}",
    summary="Update a task",
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
async def update_task(
    task_id: UUID, payload: TaskUpdate, service: TaskServiceDep, user: CurrentUser
) -> TaskRead:
    return TaskRead.model_validate(await service.update(task_id, payload))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses=NOT_FOUND,
)
async def delete_task(task_id: UUID, service: TaskServiceDep, user: CurrentUser) -> None:
    await service.delete(task_id)
