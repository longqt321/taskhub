"""Entity của resource items.

Day 1 dùng dataclass thuần. Day 2 chuyển sang model SQLAlchemy.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class Item:
    name: str
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        # Vừa tạo thì chưa sửa gì, updated_at bằng created_at.
        if self.updated_at is None:
            self.updated_at = self.created_at
