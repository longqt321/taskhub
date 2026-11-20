"""Endpoint label trong project và gán/bỏ label cho task."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, LabelServiceDep
from app.api.responses import (
    CONFLICT,
    FORBIDDEN,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    not_found,
)
from app.core.messages import MSG_LABEL_NOT_FOUND
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate

router = APIRouter(tags=["labels"])

_NOT_FOUND = not_found(MSG_LABEL_NOT_FOUND)
_WRITE_ERRORS = {**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR}


@router.post(
    "/projects/{project_id}/labels",
    status_code=status.HTTP_201_CREATED,
    summary="Create a label in a project",
    responses={**UNAUTHORIZED, **FORBIDDEN, **CONFLICT, **VALIDATION_ERROR},
)
async def create_label(
    project_id: UUID, payload: LabelCreate, service: LabelServiceDep, user: CurrentUser
) -> LabelRead:
    return LabelRead.model_validate(await service.create(user, project_id, payload))


@router.get(
    "/projects/{project_id}/labels",
    summary="List labels of a project",
    responses={**UNAUTHORIZED, **FORBIDDEN, **VALIDATION_ERROR},
)
async def list_labels(
    project_id: UUID, service: LabelServiceDep, user: CurrentUser
) -> list[LabelRead]:
    labels = await service.list(user, project_id)
    return [LabelRead.model_validate(label) for label in labels]


@router.patch(
    "/labels/{label_id}",
    summary="Update a label",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **CONFLICT, **VALIDATION_ERROR},
)
async def update_label(
    label_id: UUID, payload: LabelUpdate, service: LabelServiceDep, user: CurrentUser
) -> LabelRead:
    return LabelRead.model_validate(await service.update(user, label_id, payload))


@router.delete(
    "/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a label",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def delete_label(label_id: UUID, service: LabelServiceDep, user: CurrentUser) -> None:
    await service.delete(user, label_id)


@router.get(
    "/tasks/{task_id}/labels",
    summary="List labels attached to a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def list_task_labels(
    task_id: UUID, service: LabelServiceDep, user: CurrentUser
) -> list[LabelRead]:
    labels = await service.list_for_task(user, task_id)
    return [LabelRead.model_validate(label) for label in labels]


@router.put(
    "/tasks/{task_id}/labels/{label_id}",
    summary="Attach a label to a task",
    responses=_WRITE_ERRORS,
)
async def attach_label(
    task_id: UUID, label_id: UUID, service: LabelServiceDep, user: CurrentUser
) -> list[LabelRead]:
    labels = await service.attach(user, task_id, label_id)
    return [LabelRead.model_validate(label) for label in labels]


@router.delete(
    "/tasks/{task_id}/labels/{label_id}",
    summary="Detach a label from a task",
    responses=_WRITE_ERRORS,
)
async def detach_label(
    task_id: UUID, label_id: UUID, service: LabelServiceDep, user: CurrentUser
) -> list[LabelRead]:
    labels = await service.detach(user, task_id, label_id)
    return [LabelRead.model_validate(label) for label in labels]
