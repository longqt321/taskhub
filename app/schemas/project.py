"""Schema request/response của project."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.core.constants import MAX_DESCRIPTION_LENGTH, MAX_NAME_LENGTH
from app.core.messages import MSG_NAME_CANNOT_BE_NULL, MSG_STATUS_CANNOT_BE_NULL
from app.models.project import ProjectStatus
from app.schemas.base import BaseSchema


class ProjectCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)


class ProjectUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    status: ProjectStatus | None = None

    @model_validator(mode="after")
    def _reject_null_on_required_fields(self) -> ProjectUpdate:
        # name và status là NOT NULL, gửi null là lỗi client chứ không phải ý xoá.
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError(MSG_NAME_CANNOT_BE_NULL)
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError(MSG_STATUS_CANNOT_BE_NULL)
        return self


class ProjectRead(BaseSchema):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
