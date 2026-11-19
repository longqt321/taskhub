"""Schema request/response của label."""

from uuid import UUID

from pydantic import Field, field_validator

from app.core import messages
from app.core.constants import MAX_COLOR_LENGTH, MAX_LABEL_LENGTH
from app.schemas.base import BaseSchema

# màu dạng #RRGGBB, đúng độ dài cột trong DB
_HEX_CHARS = set("0123456789abcdefABCDEF")


class LabelCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)
    color: str = Field(default="#6B7280", max_length=MAX_COLOR_LENGTH)

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str) -> str:
        if len(value) != MAX_COLOR_LENGTH or not value.startswith("#"):
            raise ValueError("color phải có dạng #RRGGBB")
        if any(char not in _HEX_CHARS for char in value[1:]):
            raise ValueError("color phải có dạng #RRGGBB")
        return value


class LabelUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=MAX_LABEL_LENGTH)
    color: str | None = Field(default=None, max_length=MAX_COLOR_LENGTH)

    @field_validator("name")
    @classmethod
    def _reject_null_name(cls, value: str | None) -> str | None:
        # name là NOT NULL, gửi null là lỗi client chứ không phải ý xoá
        if value is None:
            raise ValueError(messages.MSG_NAME_CANNOT_BE_NULL)
        return value

    @field_validator("color")
    @classmethod
    def _check_color(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("color cannot be null")
        return LabelCreate._check_color(value)


class LabelRead(BaseSchema):
    id: UUID
    project_id: UUID
    name: str
    color: str
