"""Các dependency dùng chung trong router."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.item import ItemModel
from app.repositories.base import BaseRepository
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository
from app.services.item_service import ItemService


def get_item_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BaseRepository[ItemModel]:
    return SqlAlchemyRepository(session, ItemModel, ItemModel.created_at)


def get_item_service(
    repository: Annotated[BaseRepository[ItemModel], Depends(get_item_repository)],
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
