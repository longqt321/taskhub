"""Entity task.

Day 1 chưa có project và user nên Task chỉ gồm các field tự thân. Day 4 thêm
project_id, assignee_id, created_by khi có workspace và auth.
"""

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


class TaskStatus(enum.StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"


@dataclass(slots=True)
class Task:
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        # Vừa tạo thì chưa sửa gì, updated_at bằng created_at.
        if self.updated_at is None:
            self.updated_at = self.created_at
