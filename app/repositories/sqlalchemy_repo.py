"""Repository SQLAlchemy, cài đặt BaseRepository bằng async session."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.models.item import ItemModel
from app.repositories.base import BaseRepository


class SqlAlchemyRepository[T](BaseRepository[T]):
    """Làm việc với một loại model duy nhất qua session được cấp."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[T],
        order_by: InstrumentedAttribute[Any] | None = None,
    ) -> None:
        self._session = session
        self._model = model
        self._order_by = order_by

    async def get(self, entity_id: UUID) -> T | None:
        return await self._session.get(self._model, entity_id)

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[T], int]:
        total = await self._session.scalar(select(func.count()).select_from(self._model))
        stmt = select(self._model)
        if self._order_by is not None:
            stmt = stmt.order_by(self._order_by)
        result = await self._session.scalars(stmt.offset(offset).limit(limit))
        return result.all(), total or 0

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        entity = await self.get(entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.commit()
        return True


ItemRepository = SqlAlchemyRepository[ItemModel]
