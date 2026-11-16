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
    default_message = "Bad request"


class NotFoundError(AppError):
    status_code = 404
    code = messages.CODE_NOT_FOUND
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    code = messages.CODE_CONFLICT
    default_message = "Resource conflict"
