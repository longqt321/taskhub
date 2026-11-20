"""Lỗi nghiệp vụ.

Service raise mấy lỗi này thay vì HTTPException, để tầng service không phải
import FastAPI. Tầng API đổi chúng sang HTTP response trong exception_handlers.
"""

from typing import Any

from app.core import messages


class AppError(Exception):
    status_code: int = 500
    code: str = messages.CODE_INTERNAL_ERROR
    default_message: str = messages.MSG_INTERNAL_ERROR

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = messages.CODE_BAD_REQUEST
    default_message = messages.MSG_DEFAULT_BAD_REQUEST


class NotFoundError(AppError):
    status_code = 404
    code = messages.CODE_NOT_FOUND
    default_message = messages.MSG_DEFAULT_NOT_FOUND


class ConflictError(AppError):
    status_code = 409
    code = messages.CODE_CONFLICT
    default_message = messages.MSG_DEFAULT_CONFLICT


class UnauthorizedError(AppError):
    status_code = 401
    code = messages.CODE_UNAUTHORIZED
    default_message = messages.MSG_NOT_AUTHENTICATED


class ForbiddenError(AppError):
    status_code = 403
    code = messages.CODE_FORBIDDEN
    default_message = messages.MSG_INSUFFICIENT_PERMISSIONS
