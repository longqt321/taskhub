"""Endpoint đăng ký, đăng nhập, refresh, logout."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.api.responses import VALIDATION_ERROR, conflict, unauthorized
from app.core import messages
from app.schemas.user import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={**conflict(messages.MSG_EMAIL_ALREADY_REGISTERED), **VALIDATION_ERROR},
)
async def register(payload: UserCreate, service: AuthServiceDep) -> UserRead:
    return UserRead.model_validate(await service.register(payload))


@router.post(
    "/login",
    summary="Login with email and password",
    responses={**unauthorized(messages.MSG_INCORRECT_CREDENTIALS), **VALIDATION_ERROR},
)
async def login(payload: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    access, refresh = await service.login(payload)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    summary="Exchange a refresh token for a new token pair",
    responses={**unauthorized(messages.MSG_INVALID_REFRESH_TOKEN), **VALIDATION_ERROR},
)
async def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    access, refresh = await service.refresh(payload.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
    responses=unauthorized(messages.MSG_INVALID_REFRESH_TOKEN),
)
async def logout(payload: RefreshRequest, service: AuthServiceDep) -> None:
    await service.logout(payload.refresh_token)
