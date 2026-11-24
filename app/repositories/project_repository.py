"""Repository cho project."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class ProjectRepository(SqlAlchemyRepository[Project]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project, Project.created_at, Project.id)

    async def list_in_workspace(
        self, workspace_id: UUID, *, offset: int, limit: int
    ) -> tuple[Sequence[Project], int]:
        stmt = select(Project).where(Project.workspace_id == workspace_id)
        return await self._paginate(stmt, offset=offset, limit=limit)
