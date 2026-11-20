"""Endpoint profile của user đang đăng nhập và các thao tác admin trên user."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentAdmin, CurrentUser, PaginationDep, UserServiceDep
from app.api.responses import (
    UNAUTHORIZED,
    VALIDATION_ERROR,
    bad_request,
    forbidden,
    not_found,
)
from app.core import messages
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import UserAdminUpdate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _to_read(user: User) -> UserRead:
    return UserRead.model_validate(user)


@router.get(
    "/me",
    summary="Get current user profile",
    responses=UNAUTHORIZED,
)
async def get_me(user: CurrentUser) -> UserRead:
    return _to_read(user)


@router.patch(
    "/me",
    summary="Update current user profile",
    responses={**UNAUTHORIZED, **VALIDATION_ERROR},
)
async def update_me(payload: UserUpdate, user: CurrentUser, service: UserServiceDep) -> UserRead:
    return _to_read(await service.update(user, payload))


@router.get(
    "",
    summary="List users",
    responses={**UNAUTHORIZED, **forbidden(messages.MSG_ADMIN_REQUIRED)},
)
async def list_users(
    pagination: PaginationDep, _: CurrentAdmin, service: UserServiceDep
) -> Page[UserRead]:
    users, total = await service.list(pagination)
    return Page[UserRead].create(
        [_to_read(user) for user in users],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{user_id}",
    summary="Get a user by id",
    responses={
        **UNAUTHORIZED,
        **forbidden(messages.MSG_ADMIN_REQUIRED),
        **not_found(messages.MSG_USER_NOT_FOUND),
    },
)
async def get_user(user_id: UUID, _: CurrentAdmin, service: UserServiceDep) -> UserRead:
    return _to_read(await service.get(user_id))


@router.patch(
    "/{user_id}",
    summary="Update a user (change name, role, active state)",
    responses={
        **UNAUTHORIZED,
        **forbidden(messages.MSG_ADMIN_REQUIRED),
        **not_found(messages.MSG_USER_NOT_FOUND),
        **bad_request("Cannot lock yourself or remove the last active admin"),
        **VALIDATION_ERROR,
    },
)
async def admin_update_user(
    user_id: UUID, payload: UserAdminUpdate, admin: CurrentAdmin, service: UserServiceDep
) -> UserRead:
    return _to_read(await service.admin_update(admin, user_id, payload))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        **UNAUTHORIZED,
        **forbidden(messages.MSG_ADMIN_REQUIRED),
        **not_found(messages.MSG_USER_NOT_FOUND),
        **bad_request("Cannot delete yourself or the last active admin"),
    },
)
async def admin_delete_user(user_id: UUID, admin: CurrentAdmin, service: UserServiceDep) -> None:
    await service.admin_delete(admin, user_id)
