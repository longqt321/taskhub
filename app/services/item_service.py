"""Business logic for the items resource."""

from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.item import Item
from app.repositories.base import BaseRepository
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """Coordinates item use cases on top of a repository."""

    def __init__(self, repository: BaseRepository[Item]) -> None:
        self._repository = repository

    async def create(self, data: ItemCreate) -> Item:
        item = Item(name=data.name, description=data.description)
        return await self._repository.add(item)

    async def get(self, item_id: UUID) -> Item:
        item = await self._repository.get(item_id)
        if item is None:
            raise NotFoundError("Item not found", details={"item_id": str(item_id)})
        return item

    async def list(self, *, page: int, limit: int) -> tuple[list[Item], int]:
        offset = (page - 1) * limit
        items, total = await self._repository.list(offset=offset, limit=limit)
        return list(items), total

    async def update(self, item_id: UUID, data: ItemUpdate) -> Item:
        item = await self.get(item_id)
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field_name, value)
        item.updated_at = datetime.now(UTC)
        return await self._repository.update(item)

    async def delete(self, item_id: UUID) -> None:
        if not await self._repository.delete(item_id):
            raise NotFoundError("Item not found", details={"item_id": str(item_id)})
