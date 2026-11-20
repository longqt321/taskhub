"""Repository cho project."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class ProjectRepository(SqlAlchemyRepository[Project]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project, Project.created_at)

    async def list_in_workspace(
        self, workspace_id: UUID, *, offset: int, limit: int
    ) -> tuple[Sequence[Project], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(Project).where(Project.workspace_id == workspace_id)
        )
        result = await self._session.scalars(
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.created_at, Project.id)
            .offset(offset)
            .limit(limit)
        )
        return result.all(), total or 0
