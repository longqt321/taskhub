"""Endpoint profile của user đang đăng nhập."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, UserServiceDep
from app.api.responses import UNAUTHORIZED, VALIDATION_ERROR
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    summary="Get current user profile",
    responses=UNAUTHORIZED,
)
async def get_me(user: CurrentUser) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.patch(
    "/me",
    summary="Update current user profile",
    responses={**UNAUTHORIZED, **VALIDATION_ERROR},
)
async def update_me(payload: UserUpdate, user: CurrentUser, service: UserServiceDep) -> UserRead:
    updated = await service.update(user, payload)
    return UserRead(
        id=updated.id,
        email=updated.email,
        full_name=updated.full_name,
        role=updated.role.value,
        is_active=updated.is_active,
        created_at=updated.created_at,
    )
