"""Schema request/response của comment."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.core import messages
from app.core.constants import MAX_COMMENT_LENGTH
from app.schemas.base import BaseSchema


class CommentCreate(BaseSchema):
    content: str = Field(min_length=1, max_length=MAX_COMMENT_LENGTH)

    @field_validator("content")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        # BaseSchema strip khoảng trắng trước, nên "   " thành rỗng
        if not value:
            raise ValueError(messages.MSG_COMMENT_CANNOT_BE_EMPTY)
        return value


class CommentAuthor(BaseSchema):
    id: UUID
    full_name: str


class CommentRead(BaseSchema):
    id: UUID
    task_id: UUID
    content: str
    author: CommentAuthor
    created_at: datetime
