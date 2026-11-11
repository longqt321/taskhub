"""Repository in-memory, dùng tạm khi chưa có DB."""

from collections.abc import Sequence
from uuid import UUID

from app.repositories.base import BaseRepository, HasId


class InMemoryRepository[T: HasId](BaseRepository[T]):
    def __init__(self) -> None:
        self._items: dict[UUID, T] = {}

    async def get(self, entity_id: UUID) -> T | None:
        return self._items.get(entity_id)

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[T], int]:
        entities = list(self._items.values())
        return entities[offset : offset + limit], len(entities)

    async def add(self, entity: T) -> T:
        self._items[entity.id] = entity
        return entity

    async def update(self, entity: T) -> T:
        self._items[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        return self._items.pop(entity_id, None) is not None
