"""Repository cho task, có thêm truy vấn theo project, theo thành viên workspace và bộ lọc."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import TaskModel, TaskPriority, TaskStatus
from app.models.workspace import WorkspaceMember
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class TaskFilters:
    """Bộ lọc dùng cho danh sách task. None nghĩa là không lọc theo tiêu chí đó."""

    assignee_id: UUID | None = None
    status: list[TaskStatus] | None = None
    priority: list[TaskPriority] | None = None
    due_before: datetime | None = None
    due_after: datetime | None = None
    search: str | None = None

    def conditions(self) -> list[ColumnElement[bool]]:
        clauses: list[ColumnElement[bool]] = []
        if self.assignee_id is not None:
            clauses.append(TaskModel.assignee_id == self.assignee_id)
        if self.status:
            clauses.append(TaskModel.status.in_(self.status))
        if self.priority:
            clauses.append(TaskModel.priority.in_(self.priority))
        if self.due_before is not None:
            clauses.append(TaskModel.due_date <= self.due_before)
        if self.due_after is not None:
            clauses.append(TaskModel.due_date >= self.due_after)
        if self.search:
            escaped = self.search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clauses.append(TaskModel.title.ilike(f"%{escaped}%", escape="\\"))
        return clauses


class TaskRepository(SqlAlchemyRepository[TaskModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TaskModel, TaskModel.created_at, TaskModel.id)

    async def list_in_project(
        self, project_id: UUID, *, filters: TaskFilters, offset: int, limit: int
    ) -> tuple[Sequence[TaskModel], int]:
        stmt = select(TaskModel).where(TaskModel.project_id == project_id, *filters.conditions())
        return await self._paginate(stmt, offset=offset, limit=limit)

    def _member_projects(self, user_id: UUID) -> Select[Any]:
        return (
            select(Project.id)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Project.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
        )

    async def list_for_user(
        self, user_id: UUID, *, filters: TaskFilters, offset: int, limit: int
    ) -> tuple[Sequence[TaskModel], int]:
        """Task thuộc project trong các workspace mà user là thành viên."""
        stmt = select(TaskModel).where(
            TaskModel.project_id.in_(self._member_projects(user_id)), *filters.conditions()
        )
        return await self._paginate(stmt, offset=offset, limit=limit)

    async def list_all(
        self, *, filters: TaskFilters, offset: int, limit: int
    ) -> tuple[Sequence[TaskModel], int]:
        stmt = select(TaskModel).where(*filters.conditions())
        return await self._paginate(stmt, offset=offset, limit=limit)
