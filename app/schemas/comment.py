"""Schema request/response của comment."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.constants import MAX_COMMENT_LENGTH
from app.schemas.base import BaseSchema


class CommentCreate(BaseSchema):
    content: str = Field(min_length=1, max_length=MAX_COMMENT_LENGTH)


class CommentAuthor(BaseSchema):
    id: UUID
    full_name: str


class CommentRead(BaseSchema):
    id: UUID
    task_id: UUID
    content: str
    author: CommentAuthor
    created_at: datetime
