"""Nghiệp vụ của resource items."""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.item import ItemModel
from app.repositories.base import BaseRepository
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, repository: BaseRepository[ItemModel]) -> None:
        self._repository = repository

    async def create(self, data: ItemCreate) -> ItemModel:
        item = ItemModel(name=data.name, description=data.description)
        return await self._repository.add(item)

    async def get(self, item_id: UUID) -> ItemModel:
        item = await self._repository.get(item_id)
        if item is None:
            raise NotFoundError("Item not found", details={"item_id": str(item_id)})
        return item

    async def list(self, *, page: int, limit: int) -> tuple[list[ItemModel], int]:
        offset = (page - 1) * limit
        items, total = await self._repository.list(offset=offset, limit=limit)
        return list(items), total

    async def update(self, item_id: UUID, data: ItemUpdate) -> ItemModel:
        item = await self.get(item_id)
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field_name, value)
        return await self._repository.update(item)

    async def delete(self, item_id: UUID) -> None:
        if not await self._repository.delete(item_id):
            raise NotFoundError("Item not found", details={"item_id": str(item_id)})
