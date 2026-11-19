"""Repository cho comment của task."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.comment import Comment
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class CommentRepository(SqlAlchemyRepository[Comment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Comment, Comment.created_at)

    async def list_in_task(self, task_id: UUID) -> Sequence[Comment]:
        result = await self._session.scalars(
            select(Comment)
            .where(Comment.task_id == task_id)
            .options(joinedload(Comment.author))
            .order_by(Comment.created_at)
        )
        return result.unique().all()

    async def get_with_author(self, comment_id: UUID) -> Comment | None:
        result = await self._session.scalars(
            select(Comment).where(Comment.id == comment_id).options(joinedload(Comment.author))
        )
        return result.first()
