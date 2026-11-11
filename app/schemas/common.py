"""Shared response schemas: error envelope and pagination wrapper."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable error information returned to clients."""

    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Uniform error envelope used by every failing endpoint."""

    error: ErrorDetail


class Page[T](BaseModel):
    """Pagination envelope for list endpoints."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def create(cls, items: list[T], *, total: int, page: int, limit: int) -> Page[T]:
        pages = -(-total // limit) if total else 0
        return cls(items=items, total=total, page=page, limit=limit, pages=pages)
