"""Schema request/response của label."""

from uuid import UUID

from pydantic import Field, field_validator

from app.core import messages
from app.core.constants import (
    DEFAULT_LABEL_COLOR,
    LABEL_COLOR_PATTERN,
    MAX_COLOR_LENGTH,
    MAX_LABEL_LENGTH,
)
from app.schemas.base import BaseSchema


class LabelCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)
    color: str = Field(
        default=DEFAULT_LABEL_COLOR, max_length=MAX_COLOR_LENGTH, pattern=LABEL_COLOR_PATTERN
    )


class LabelUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=MAX_LABEL_LENGTH)
    color: str | None = Field(
        default=None, max_length=MAX_COLOR_LENGTH, pattern=LABEL_COLOR_PATTERN
    )

    @field_validator("name")
    @classmethod
    def _reject_null_name(cls, value: str | None) -> str | None:
        # name là NOT NULL, gửi null là lỗi client chứ không phải ý xoá
        if value is None:
            raise ValueError(messages.MSG_NAME_CANNOT_BE_NULL)
        return value

    @field_validator("color")
    @classmethod
    def _reject_null_color(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError(messages.MSG_COLOR_CANNOT_BE_NULL)
        return value


class LabelRead(BaseSchema):
    id: UUID
    project_id: UUID
    name: str
    color: str
