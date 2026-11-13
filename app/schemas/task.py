"""Schema request/response của resource tasks."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.core.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH
from app.models.task import TaskStatus
from app.schemas.base import BaseSchema


class TaskCreate(BaseSchema):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    status: TaskStatus = TaskStatus.TODO


class TaskUpdate(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def _reject_null_on_required_fields(self) -> TaskUpdate:
        # title và status là NOT NULL, gửi null là lỗi client chứ không phải ý xoá.
        for field_name in ("title", "status"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class TaskRead(BaseSchema):
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
