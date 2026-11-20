"""Interface repository, để service không cần biết dữ liệu lưu ở đâu."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID


class BaseRepository[T](ABC):
    @abstractmethod
    async def get(self, entity_id: UUID) -> T | None: ...

    @abstractmethod
    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[T], int]:
        """Trả về một trang entity kèm tổng số bản ghi."""

    @abstractmethod
    async def add(self, entity: T) -> T: ...

    @abstractmethod
    async def update(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Trả về False nếu không tìm thấy."""
