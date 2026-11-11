"""Application-level exception hierarchy.

Services and repositories raise these errors instead of HTTP-specific
exceptions, keeping the business layer independent from FastAPI. The API layer
maps them to HTTP responses via the handlers in `app.core.exception_handlers`.
"""

from typing import Any


class AppError(Exception):
    """Base class for expected, domain-level failures."""

    status_code: int = 500
    code: str = "internal_error"
    default_message: str = "Internal server error"

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"
    default_message = "Bad request"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "Resource conflict"
