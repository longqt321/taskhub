"""Đổi lỗi của app sang HTTP response, mọi lỗi trả cùng một format."""

from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import messages
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.common import ErrorDetail, ErrorResponse

logger = get_logger(__name__)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=headers,
    )


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # cast thay vì assert: assert bị bỏ khi chạy python -O
    error = cast(AppError, exc)
    if error.status_code >= 500:
        logger.error("Application error: %s", error.message, exc_info=error)
    return _error_response(error.status_code, error.code, error.message, error.details)


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = cast(RequestValidationError, exc)
    details = [
        {"loc": [str(part) for part in error["loc"]], "msg": error["msg"], "type": error["type"]}
        for error in validation_error.errors()
    ]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        messages.CODE_VALIDATION_ERROR,
        messages.MSG_VALIDATION_FAILED,
        details,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    http_error = cast(StarletteHTTPException, exc)
    return _error_response(
        http_error.status_code,
        messages.CODE_HTTP_ERROR,
        str(http_error.detail),
        headers=getattr(http_error, "headers", None),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while handling %s %s", request.method, request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        messages.CODE_INTERNAL_ERROR,
        messages.MSG_INTERNAL_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
