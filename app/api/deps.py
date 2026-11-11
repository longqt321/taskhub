"""Các dependency dùng chung trong router."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query

from app.models.item import Item
from app.repositories.base import BaseRepository
from app.repositories.in_memory import InMemoryRepository
from app.services.item_service import ItemService


@lru_cache
def get_item_repository() -> BaseRepository[Item]:
    # cache để dữ liệu in-memory không bị mất giữa các request
    return InMemoryRepository[Item]()


def get_item_service(
    repository: Annotated[BaseRepository[Item], Depends(get_item_repository)],
) -> ItemService:
    return ItemService(repository)


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


@dataclass(frozen=True, slots=True)
class PaginationParams:
    page: int
    limit: int


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
