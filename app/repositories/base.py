"""Repository abstraction: persistence-agnostic data access contract."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Protocol
from uuid import UUID


class HasId(Protocol):
    """Structural requirement for every persisted entity."""

    id: UUID


class BaseRepository[T: HasId](ABC):
    """Generic CRUD contract implemented by concrete repositories.

    Day 1 ships an in-memory implementation; Day 2 adds the SQLAlchemy
    implementation behind the same interface so the service layer is untouched.
    """

    @abstractmethod
    async def get(self, entity_id: UUID) -> T | None:
        """Return the entity with the given id, or None."""

    @abstractmethod
    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[T], int]:
        """Return a page of entities and the total count."""

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Persist a new entity and return it."""

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Persist changes to an existing entity and return it."""

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete the entity by id; return False if it did not exist."""
