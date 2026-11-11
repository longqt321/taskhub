"""Domain entities.

Day 1 placeholder: entities are plain dataclasses persisted by the in-memory
repository. On Day 2 these are replaced by SQLAlchemy 2.x ORM models.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Item:
    """Scaffolding entity used to exercise the full layered stack on Day 1."""

    name: str
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        # A freshly created entity has not been modified yet.
        if self.updated_at is None:
            self.updated_at = self.created_at
