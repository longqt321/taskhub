"""Endpoint CRUD cho tasks."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import PaginationDep, TaskServiceDep
from app.schemas.common import ErrorResponse, Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

_VALIDATION_ERROR: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": "Validation error"}
}
_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Task not found"}
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    responses=_VALIDATION_ERROR,
)
async def create_task(payload: TaskCreate, service: TaskServiceDep) -> TaskRead:
    return TaskRead.model_validate(await service.create(payload))


@router.get(
    "",
    summary="List tasks",
    responses=_VALIDATION_ERROR,
)
async def list_tasks(service: TaskServiceDep, pagination: PaginationDep) -> Page[TaskRead]:
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
    responses=_NOT_FOUND,
)
async def get_task(task_id: UUID, service: TaskServiceDep) -> TaskRead:
    return TaskRead.model_validate(await service.get(task_id))


@router.patch(
    "/{task_id}",
    summary="Update a task",
    responses={**_NOT_FOUND, **_VALIDATION_ERROR},
)
async def update_task(task_id: UUID, payload: TaskUpdate, service: TaskServiceDep) -> TaskRead:
    return TaskRead.model_validate(await service.update(task_id, payload))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses=_NOT_FOUND,
)
async def delete_task(task_id: UUID, service: TaskServiceDep) -> None:
    await service.delete(task_id)
