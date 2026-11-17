"""Endpoint đăng ký, đăng nhập, refresh, logout."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.api.responses import VALIDATION_ERROR, conflict, unauthorized
from app.schemas.user import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={**conflict("Email already registered"), **VALIDATION_ERROR},
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
    responses={**unauthorized("Incorrect email or password"), **VALIDATION_ERROR},
)
async def login(payload: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    access, refresh = await service.login(payload)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    summary="Exchange a refresh token for a new token pair",
    responses={**unauthorized("Invalid refresh token"), **VALIDATION_ERROR},
)
async def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    access, refresh = await service.refresh(payload.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/logout",
    summary="Revoke a refresh token",
    responses=unauthorized("Invalid refresh token"),
)
async def logout(payload: RefreshRequest, service: AuthServiceDep) -> dict[str, str]:
    await service.logout(payload.refresh_token)
    return {"status": "logged_out"}
