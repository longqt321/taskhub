"""Endpoint comment trên task."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CommentServiceDep, CurrentUser
from app.api.responses import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR, not_found
from app.core.messages import MSG_COMMENT_NOT_FOUND
from app.schemas.comment import CommentCreate, CommentRead

router = APIRouter(tags=["comments"])

_NOT_FOUND = not_found(MSG_COMMENT_NOT_FOUND)


@router.get(
    "/tasks/{task_id}/comments",
    summary="List comments of a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def list_comments(
    task_id: UUID, service: CommentServiceDep, user: CurrentUser
) -> list[CommentRead]:
    comments = await service.list(user, task_id)
    return [CommentRead.model_validate(comment) for comment in comments]


@router.post(
    "/tasks/{task_id}/comments",
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def create_comment(
    task_id: UUID, payload: CommentCreate, service: CommentServiceDep, user: CurrentUser
) -> CommentRead:
    return CommentRead.model_validate(await service.create(user, task_id, payload))


@router.delete(
    "/tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment (author or workspace owner)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def delete_comment(
    task_id: UUID, comment_id: UUID, service: CommentServiceDep, user: CurrentUser
) -> None:
    await service.delete(user, task_id, comment_id)
