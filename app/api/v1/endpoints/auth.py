"""Endpoint đăng ký, đăng nhập, refresh, logout."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.user import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def register(payload: UserCreate, service: AuthServiceDep) -> UserRead:
    user = await service.register(payload)
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    summary="Login with email and password",
    responses={
        401: {"model": ErrorResponse, "description": "Incorrect email or password"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def login(payload: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    access, refresh = await service.login(payload)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    summary="Exchange a refresh token for a new token pair",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    access, refresh = await service.refresh(payload.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/logout",
    summary="Revoke a refresh token",
    responses={401: {"model": ErrorResponse, "description": "Invalid refresh token"}},
)
async def logout(payload: RefreshRequest, service: AuthServiceDep) -> dict[str, str]:
    await service.logout(payload.refresh_token)
    return {"status": "logged_out"}
