"""Schema dùng chung: format lỗi và phân trang."""

import math
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


class ErrorDetail(BaseSchema):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseSchema):
    error: ErrorDetail


class Page[T](BaseSchema):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def create(cls, items: list[T], *, total: int, page: int, limit: int) -> Page[T]:
        return cls(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=math.ceil(total / limit),
        )
