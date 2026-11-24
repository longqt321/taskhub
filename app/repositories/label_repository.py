"""Repository cho label và bảng nối task_labels."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label, TaskLabel
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class LabelRepository(SqlAlchemyRepository[Label]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Label, Label.name)

    async def list_in_project(self, project_id: UUID) -> Sequence[Label]:
        result = await self._session.scalars(
            select(Label).where(Label.project_id == project_id).order_by(Label.name)
        )
        return result.all()

    async def get_by_name(self, project_id: UUID, name: str) -> Label | None:
        result = await self._session.scalars(
            select(Label).where(Label.project_id == project_id, Label.name == name)
        )
        return result.first()

    async def list_for_task(self, task_id: UUID) -> Sequence[Label]:
        result = await self._session.scalars(
            select(Label)
            .join(TaskLabel, TaskLabel.label_id == Label.id)
            .where(TaskLabel.task_id == task_id)
            .order_by(Label.name)
        )
        return result.all()

    async def is_attached(self, task_id: UUID, label_id: UUID) -> bool:
        total = await self._session.scalar(
            select(func.count())
            .select_from(TaskLabel)
            .where(TaskLabel.task_id == task_id, TaskLabel.label_id == label_id)
        )
        return bool(total)

    async def attach(self, task_id: UUID, label_id: UUID) -> None:
        self._session.add(TaskLabel(task_id=task_id, label_id=label_id))
        await self._session.flush()

    async def detach(self, task_id: UUID, label_id: UUID) -> None:
        await self._session.execute(
            delete(TaskLabel).where(TaskLabel.task_id == task_id, TaskLabel.label_id == label_id)
        )
        await self._session.flush()
