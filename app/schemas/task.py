"""Schema request/response của resource tasks."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.core.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH
from app.core.messages import (
    MSG_PRIORITY_CANNOT_BE_NULL,
    MSG_STATUS_CANNOT_BE_NULL,
    MSG_TITLE_CANNOT_BE_NULL,
)
from app.models.task import TaskPriority, TaskStatus
from app.schemas.base import BaseSchema


class TaskCreate(BaseSchema):
    project_id: UUID
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: UUID | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    due_date: datetime | None = None

    @model_validator(mode="after")
    def _reject_null_on_required_fields(self) -> TaskUpdate:
        # title, status, priority là NOT NULL, gửi null là lỗi client chứ không phải ý xoá.
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError(MSG_TITLE_CANNOT_BE_NULL)
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError(MSG_STATUS_CANNOT_BE_NULL)
        if "priority" in self.model_fields_set and self.priority is None:
            raise ValueError(MSG_PRIORITY_CANNOT_BE_NULL)
        return self


class TaskRead(BaseSchema):
    id: UUID
    project_id: UUID
    assignee_id: UUID | None
    created_by: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
