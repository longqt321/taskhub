"""Tham số phân trang dùng chung cho các endpoint list."""

from dataclasses import dataclass

from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT


@dataclass(frozen=True, slots=True)
class PaginationParams:
    page: int = DEFAULT_PAGE
    limit: int = DEFAULT_LIMIT

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


# dùng trong Query(ge=..., le=...)
MIN_PAGE = 1
MIN_LIMIT = 1
MAX_PAGE_LIMIT = MAX_LIMIT
