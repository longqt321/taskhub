"""Repository cho task, có thêm truy vấn theo project và theo thành viên workspace."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import TaskModel
from app.models.workspace import WorkspaceMember
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class TaskRepository(SqlAlchemyRepository[TaskModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TaskModel, TaskModel.created_at)

    async def list_in_project(
        self, project_id: UUID, *, offset: int, limit: int
    ) -> tuple[Sequence[TaskModel], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(TaskModel).where(TaskModel.project_id == project_id)
        )
        result = await self._session.scalars(
            select(TaskModel)
            .where(TaskModel.project_id == project_id)
            .order_by(TaskModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        return result.all(), total or 0

    async def list_for_user(
        self, user_id: UUID, *, offset: int, limit: int
    ) -> tuple[Sequence[TaskModel], int]:
        """Task thuộc project trong các workspace mà user là thành viên."""
        condition = TaskModel.project_id.in_(
            select(Project.id)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Project.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
        )
        total = await self._session.scalar(
            select(func.count()).select_from(TaskModel).where(condition)
        )
        result = await self._session.scalars(
            select(TaskModel)
            .where(condition)
            .order_by(TaskModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        return result.all(), total or 0
