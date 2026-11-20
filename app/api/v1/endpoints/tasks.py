"""Endpoint CRUD cho tasks. Yêu cầu đăng nhập và quyền trên project chứa task."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query, status
from pydantic import ValidationError

from app.api.deps import (
    CurrentUser,
    PaginationDep,
    TaskCacheDep,
    TaskFiltersDep,
    TaskServiceDep,
)
from app.api.responses import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR, not_found
from app.core.cache import build_project_tasks_key
from app.core.messages import MSG_TASK_NOT_FOUND
from app.core.notifications import send_task_assigned_email
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import AssignCallback

router = APIRouter(prefix="/tasks", tags=["tasks"])

_NOT_FOUND = not_found(MSG_TASK_NOT_FOUND)


def _assign_notifier(background_tasks: BackgroundTasks) -> AssignCallback:
    def notify(email: str, title: str, task_id: UUID) -> None:
        background_tasks.add_task(send_task_assigned_email, email, title, task_id)

    return notify


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def create_task(
    payload: TaskCreate,
    service: TaskServiceDep,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> TaskRead:
    task = await service.create(user, payload, on_assigned=_assign_notifier(background_tasks))
    return TaskRead.model_validate(task)


@router.get(
    "",
    summary="List tasks",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def list_tasks(
    service: TaskServiceDep,
    pagination: PaginationDep,
    filters: TaskFiltersDep,
    cache: TaskCacheDep,
    user: CurrentUser,
    project_id: Annotated[UUID | None, Query(description="Chỉ lấy task của project này")] = None,
) -> Page[TaskRead]:
    if project_id is not None:
        # kiểm tra quyền trước khi đọc cache, tránh user ngoài lấy được dữ liệu đã cache
        await service.ensure_can_read_project(user, project_id)
        version = await cache.get_version(project_id)
        cache_key = build_project_tasks_key(project_id, version, pagination, filters)
        cached = await cache.get(cache_key, project_id)
        if cached is not None:
            try:
                return Page[TaskRead].model_validate_json(cached)
            except ValidationError:
                # payload cache lệch schema sau khi deploy thì bỏ qua, query lại DB
                pass

        tasks, total = await service.list(user, pagination, filters, project_id)
        page = Page[TaskRead].create(
            [TaskRead.model_validate(task) for task in tasks],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )
        await cache.set(cache_key, page.model_dump_json(), project_id)
        return page

    tasks, total = await service.list(user, pagination, filters, None)
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
    task_id: UUID,
    payload: TaskUpdate,
    service: TaskServiceDep,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> TaskRead:
    task = await service.update(
        user, task_id, payload, on_assigned=_assign_notifier(background_tasks)
    )
    return TaskRead.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def delete_task(task_id: UUID, service: TaskServiceDep, user: CurrentUser) -> None:
    await service.delete(user, task_id)
