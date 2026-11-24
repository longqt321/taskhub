"""Repository SQLAlchemy, cài đặt BaseRepository bằng async session."""

from collections.abc import Sequence
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.repositories.base import BaseRepository


class SqlAlchemyRepository[T](BaseRepository[T]):
    """Làm việc với một loại model duy nhất qua session được cấp."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[T],
        *order_by: InstrumentedAttribute[Any],
    ) -> None:
        self._session = session
        self._model = model
        self._order_by = order_by

    async def get(self, entity_id: UUID) -> T | None:
        return await self._session.get(self._model, entity_id)

    async def _paginate(
        self,
        stmt: Select[Any],
        *,
        offset: int,
        limit: int,
        order_by: Sequence[Any] | None = None,
    ) -> tuple[Sequence[T], int]:
        """Đếm tổng bản ghi và lấy một trang dữ liệu theo stmt."""
        total = await self._session.scalar(select(func.count()).select_from(stmt.subquery()))
        clauses = order_by if order_by is not None else self._order_by
        if clauses:
            stmt = stmt.order_by(*clauses)
        result = await self._session.scalars(stmt.offset(offset).limit(limit))
        return cast(Sequence[T], result.all()), total or 0

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[T], int]:
        return await self._paginate(select(self._model), offset=offset, limit=limit)

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        entity = await self.get(entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.flush()
        return True

    async def rollback(self) -> None:
        """Bỏ transaction đang dở, dùng khi ghi bị vi phạm ràng buộc."""
        await self._session.rollback()
